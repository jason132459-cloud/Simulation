import json
from pathlib import Path

import cv2
import numpy as np


def load_homography(path):
    data = np.load(path)
    return data["H"]


def pixel_to_world(points_px, H):
    # 카메라 이미지의 pixel 좌표를 경기장 world 좌표(meter)로 변환한다.
    pts = np.array(points_px, dtype=np.float32).reshape(-1, 1, 2)
    world = cv2.perspectiveTransform(pts, H)
    return world.reshape(-1, 2)


def world_to_pixel(points_world, H):
    # world 좌표를 다시 화면에 그리기 위해 inverse homography로 pixel 좌표를 구한다.
    H_inv = np.linalg.inv(H)
    pts = np.array(points_world, dtype=np.float32).reshape(-1, 1, 2)
    pixel = cv2.perspectiveTransform(pts, H_inv)
    return pixel.reshape(-1, 2)


def load_path(path):
    path = Path(path)
    if not path.exists():
        return []

    # path.json에는 pixel이 아니라 world 좌표가 저장되어 있어야 제어기에 바로 쓸 수 있다.
    with path.open("r", encoding="utf-8") as f:
        raw_points = json.load(f)

    return [(float(p["x"]), float(p["y"])) for p in raw_points]


def save_path(path, points_world):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # 사람이 클릭한 목표점을 meter 단위 좌표로 저장한다.
    payload = [{"x": float(x), "y": float(y)} for x, y in points_world]
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
