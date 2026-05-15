import argparse
from pathlib import Path

import cv2

from cv_geometry import load_homography, load_path, pixel_to_world, save_path, world_to_pixel


DEFAULT_CAMERA_ID = 0
DEFAULT_HOMOGRAPHY = Path("data/homography.npz")
DEFAULT_PATH = Path("data/path.json")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera-id", type=int, default=DEFAULT_CAMERA_ID)
    parser.add_argument("--homography", type=Path, default=DEFAULT_HOMOGRAPHY)
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH)
    return parser.parse_args()


def draw_path(frame, H, path_world):
    if not path_world:
        return

    # 저장된 목표점은 world 좌표이므로, 카메라 화면에 보이려면 pixel 좌표로 되돌린다.
    path_px = world_to_pixel(path_world, H)

    for i, point in enumerate(path_px):
        p = tuple(point.astype(int))
        cv2.circle(frame, p, 6, (0, 0, 255), -1)
        cv2.putText(
            frame,
            str(i),
            (p[0] + 8, p[1] - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 255),
            2,
        )

    for i in range(len(path_px) - 1):
        p1 = tuple(path_px[i].astype(int))
        p2 = tuple(path_px[i + 1].astype(int))
        cv2.line(frame, p1, p2, (255, 0, 0), 2)


def main():
    args = parse_args()
    if not args.homography.exists():
        raise FileNotFoundError(
            f"{args.homography} not found. Run `python aruco/calibrate_homography.py` first, "
            "click four arena corners, then press `s` to save."
        )

    H = load_homography(args.homography)
    path_world = load_path(args.path)

    cap = cv2.VideoCapture(args.camera_id)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera id {args.camera_id}")

    window_name = "Click path waypoints"

    def on_mouse(event, x, y, flags, userdata):
        if event != cv2.EVENT_LBUTTONDOWN:
            return

        # 클릭한 위치는 pixel 좌표다. 제어기에서 쓰기 위해 world 좌표(meter)로 변환한다.
        world = pixel_to_world([(x, y)], H)[0]
        waypoint = (float(world[0]), float(world[1]))
        path_world.append(waypoint)
        print(f"added pixel=({x}, {y}) -> world=({waypoint[0]:.3f}, {waypoint[1]:.3f})")

    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, on_mouse)

    print("Left click: add waypoint")
    print("keys: u=undo, c=clear, s=save, q=quit")

    while True:
        # 현재 카메라 화면 위에 지금까지 만든 path를 계속 덧그린다.
        ret, frame = cap.read()
        if not ret:
            break

        draw_path(frame, H, path_world)
        cv2.putText(
            frame,
            f"waypoints: {len(path_world)}",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )
        cv2.imshow(window_name, frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("u") and path_world:
            removed = path_world.pop()
            print(f"removed world=({removed[0]:.3f}, {removed[1]:.3f})")
        if key == ord("c"):
            path_world.clear()
            print("cleared path")
        if key == ord("s"):
            # 저장되는 값은 pixel이 아니라 homography를 통과한 world 좌표다.
            save_path(args.path, path_world)
            print(f"saved: {args.path}")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
