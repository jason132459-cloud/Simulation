import argparse
from pathlib import Path

import cv2
import numpy as np


DEFAULT_CAMERA_ID = 0
DEFAULT_OUTPUT = Path("data/homography.npz")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera-id", type=int, default=DEFAULT_CAMERA_ID)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--width-m", type=float, default=2.4)
    parser.add_argument("--height-m", type=float, default=1.4)
    parser.add_argument("--dshow", action="store_true", help="Use DirectShow camera backend on Windows.")
    return parser.parse_args()


def main():
    args = parse_args()
    clicked = []
    latest_frame = None

    # 카메라 화면에서 경기장 네 모서리를 클릭해서 pixel 좌표를 수집한다.
    backend = cv2.CAP_DSHOW if args.dshow else cv2.CAP_ANY
    cap = cv2.VideoCapture(args.camera_id, backend)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera id {args.camera_id}")

    window_name = "Calibrate homography"

    def on_mouse(event, x, y, flags, userdata):
        if event == cv2.EVENT_LBUTTONDOWN and len(clicked) < 4:
            clicked.append((x, y))
            print(f"corner {len(clicked)}: pixel=({x}, {y})")

    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, on_mouse)

    print("Click arena corners in order: bottom-left, bottom-right, top-right, top-left")
    print("keys: u=undo, s=save after 4 clicks, q=quit")

    while True:
        # 매 프레임마다 현재 클릭된 점을 화면 위에 표시한다.
        ret, frame = cap.read()
        if not ret:
            print("Could not read a camera frame. Try --camera-id 1 or --dshow.")
            break

        latest_frame = frame.copy()

        for i, point in enumerate(clicked):
            cv2.circle(frame, point, 6, (0, 255, 255), -1)
            cv2.putText(
                frame,
                str(i + 1),
                (point[0] + 8, point[1] - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2,
            )

        cv2.putText(
            frame,
            f"clicked: {len(clicked)}/4",
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
        if key == ord("u") and clicked:
            removed = clicked.pop()
            print(f"removed: {removed}")
        if key == ord("s"):
            if len(clicked) != 4:
                print("Need exactly 4 clicked corners before saving.")
                continue

            # pixel_points는 카메라 이미지 좌표, world_points는 실제 경기장 좌표(meter)다.
            # 이 둘의 대응 관계로 homography H를 계산한다.
            pixel_points = np.array(clicked, dtype=np.float32)
            world_points = np.array(
                [
                    [0.0, 0.0],
                    [args.width_m, 0.0],
                    [args.width_m, args.height_m],
                    [0.0, args.height_m],
                ],
                dtype=np.float32,
            )
            H, _ = cv2.findHomography(pixel_points, world_points)
            if H is None:
                print("Failed to compute homography.")
                continue

            # 이후 모든 클릭 지점과 ArUco 위치는 이 H를 통해 world 좌표로 변환된다.
            args.output.parent.mkdir(parents=True, exist_ok=True)
            np.savez(
                args.output,
                H=H,
                pixel_points=pixel_points,
                world_points=world_points,
                width_m=args.width_m,
                height_m=args.height_m,
            )
            print(f"saved: {args.output}")
            break

    cap.release()
    cv2.destroyAllWindows()

    if latest_frame is None:
        raise RuntimeError("No camera frame was captured.")


if __name__ == "__main__":
    main()
