import argparse

import cv2


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera-id", type=int, default=0)
    parser.add_argument("--dshow", action="store_true", help="Use DirectShow camera backend on Windows.")
    return parser.parse_args()


def main():
    args = parse_args()
    backend = cv2.CAP_DSHOW if args.dshow else cv2.CAP_ANY
    cap = cv2.VideoCapture(args.camera_id, backend)

    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera id {args.camera_id}")

    print("Camera opened. Press q to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Could not read a camera frame. Try another --camera-id or add --dshow.")
            break

        cv2.imshow("Camera check", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
