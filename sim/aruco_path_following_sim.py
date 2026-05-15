import math
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "tools"))

from cv_geometry import load_homography, load_path, pixel_to_world, world_to_pixel


CAMERA_ID = 0
ROBOT_MARKER_ID = 0
HOMOGRAPHY_FILE = ROOT / "data/homography.npz"
PATH_FILE = ROOT / "data/path.json"

# True: use the physical marker pose as the current robot state.
# False: use the marker only to initialize/reset the simulated robot.
USE_MARKER_AS_STATE = False
YAW_OFFSET_RAD = 0.0


def normalize_angle(angle):
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


def distance_xy(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def make_aruco_detector():
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

    try:
        params = cv2.aruco.DetectorParameters()
    except AttributeError:
        params = cv2.aruco.DetectorParameters_create()

    if hasattr(cv2.aruco, "ArucoDetector"):
        detector = cv2.aruco.ArucoDetector(aruco_dict, params)
    else:
        detector = None

    return aruco_dict, params, detector


def detect_markers(frame, aruco_dict, params, detector):
    if detector is not None:
        corners, ids, _ = detector.detectMarkers(frame)
    else:
        corners, ids, _ = cv2.aruco.detectMarkers(frame, aruco_dict, parameters=params)
    return corners, ids


def get_robot_pose_from_aruco(corners, ids, H, marker_id):
    if ids is None:
        return None

    for i, detected_id in enumerate(ids.flatten()):
        if int(detected_id) != marker_id:
            continue

        corner_px = corners[i].reshape(4, 2)
        corner_world = pixel_to_world(corner_px, H)

        p0, p1, p2, p3 = corner_world
        center = (p0 + p1 + p2 + p3) / 4.0
        front = (p0 + p1) / 2.0

        dx = front[0] - center[0]
        dy = front[1] - center[1]
        theta = normalize_angle(math.atan2(dy, dx) + YAW_OFFSET_RAD)

        return {"x": float(center[0]), "y": float(center[1]), "theta": float(theta)}

    return None


def compute_control(robot_pose, target_point):
    x = robot_pose["x"]
    y = robot_pose["y"]
    theta = robot_pose["theta"]
    tx, ty = target_point

    dx = tx - x
    dy = ty - y
    target_angle = math.atan2(dy, dx)
    angle_error = normalize_angle(target_angle - theta)
    dist_error = math.hypot(dx, dy)

    v = 0.0 if abs(angle_error) > 0.6 else 0.6 * dist_error
    w = 1.8 * angle_error

    return max(min(v, 0.35), 0.0), max(min(w, 1.8), -1.8)


def update_sim_pose(robot_pose, v, w, dt):
    theta = robot_pose["theta"]
    robot_pose["x"] += v * math.cos(theta) * dt
    robot_pose["y"] += v * math.sin(theta) * dt
    robot_pose["theta"] = normalize_angle(theta + w * dt)
    return robot_pose


def draw_world_path(frame, H, path, color=(255, 0, 0)):
    if len(path) < 1:
        return

    path_px = world_to_pixel(path, H)

    for i in range(len(path_px) - 1):
        p1 = tuple(path_px[i].astype(int))
        p2 = tuple(path_px[i + 1].astype(int))
        cv2.line(frame, p1, p2, color, 2)

    for i, p in enumerate(path_px):
        point = tuple(p.astype(int))
        cv2.circle(frame, point, 5, color, -1)
        cv2.putText(frame, str(i), (point[0] + 6, point[1] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)


def draw_pose(frame, H, pose, color=(0, 255, 0), label="robot"):
    x = pose["x"]
    y = pose["y"]
    theta = pose["theta"]
    length = 0.18

    center_world = np.array([[x, y]], dtype=np.float32)
    front_world = np.array([[x + length * math.cos(theta), y + length * math.sin(theta)]], dtype=np.float32)

    center_px = world_to_pixel(center_world, H)[0]
    front_px = world_to_pixel(front_world, H)[0]
    c = tuple(center_px.astype(int))
    f = tuple(front_px.astype(int))

    cv2.circle(frame, c, 6, color, -1)
    cv2.arrowedLine(frame, c, f, color, 3)
    cv2.putText(frame, label, (c[0] + 8, c[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


def main():
    H = load_homography(HOMOGRAPHY_FILE)
    path = load_path(PATH_FILE)
    if not path:
        raise RuntimeError(f"No path found. Run: python tools/click_path.py")

    aruco_dict, params, detector = make_aruco_detector()
    cap = cv2.VideoCapture(CAMERA_ID)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera id {CAMERA_ID}")

    sim_pose = None
    waypoint_index = 0
    last_time = time.time()

    print("q: quit")
    print("r: reset simulated robot from current ArUco pose")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        now = time.time()
        dt = min(now - last_time, 0.1)
        last_time = now

        corners, ids = detect_markers(frame, aruco_dict, params, detector)
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        marker_pose = get_robot_pose_from_aruco(corners, ids, H, ROBOT_MARKER_ID)
        if sim_pose is None and marker_pose is not None:
            sim_pose = marker_pose.copy()
            print(f"sim initialized: {sim_pose}")

        current_pose = marker_pose if USE_MARKER_AS_STATE else sim_pose
        v = 0.0
        w = 0.0

        if current_pose is not None and waypoint_index < len(path):
            target = path[waypoint_index]
            if distance_xy((current_pose["x"], current_pose["y"]), target) < 0.10:
                waypoint_index += 1

            if waypoint_index < len(path):
                target = path[waypoint_index]
                v, w = compute_control(current_pose, target)

                if sim_pose is not None and not USE_MARKER_AS_STATE:
                    sim_pose = update_sim_pose(sim_pose, v, w, dt)

        draw_world_path(frame, H, path, color=(255, 0, 0))

        if marker_pose is not None:
            draw_pose(frame, H, marker_pose, color=(0, 255, 255), label="aruco")

        if sim_pose is not None:
            draw_pose(frame, H, sim_pose, color=(0, 255, 0), label="sim")

        if waypoint_index < len(path):
            target_px = world_to_pixel([path[waypoint_index]], H)[0]
            cv2.circle(frame, tuple(target_px.astype(int)), 8, (0, 0, 255), -1)

        info = f"wp:{waypoint_index}/{len(path)} v:{v:.2f} w:{w:.2f}"
        cv2.putText(frame, info, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.imshow("ArUco path following simulation", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("r"):
            if marker_pose is None:
                print("Cannot reset: marker is not visible.")
                continue
            sim_pose = marker_pose.copy()
            waypoint_index = 0
            print(f"reset sim: {sim_pose}")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
