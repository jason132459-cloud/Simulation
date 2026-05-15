import argparse
from pathlib import Path

import cv2


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", type=int, default=0)
    parser.add_argument("--size", type=int, default=600)
    parser.add_argument("--output", type=Path, default=Path("data/marker_0.png"))
    return parser.parse_args()


def main():
    args = parse_args()
    # DICT_4X4_50은 4x4 비트 패턴 50개를 가진 ArUco dictionary다.
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    marker = cv2.aruco.generateImageMarker(aruco_dict, args.id, args.size)

    # 출력한 마커를 카메라가 잘 볼 수 있게 충분히 크게 인쇄하면 pose가 안정적이다.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(args.output), marker)
    print(f"saved: {args.output}")


if __name__ == "__main__":
    main()
