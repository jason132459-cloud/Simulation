# ArUco-in-the-loop 2D Path Following Simulation

Camera-in-the-loop starter repo for testing ArUco pose estimation, clickable goal/path setup, and simple 2D path following without a physical robot.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Workflow

1. Print an ArUco marker.

```bash
python tools/generate_aruco_marker.py --id 0 --output data/marker_0.png
```

2. Calibrate the tabletop/arena homography.

```bash
python aruco/calibrate_homography.py
```

Click the four arena corners in this order:

```text
bottom-left, bottom-right, top-right, top-left
```

The script saves `data/homography.npz`.

3. Click target waypoints on the camera image.

```bash
python tools/click_path.py
```

Left click to add waypoints. Press `u` to undo, `s` to save, and `q` to quit.

The clicked pixels are converted into world coordinates through the homography and saved to `data/path.json`.

4. Run the simulation.

```bash
python sim/aruco_path_following_sim.py
```

Press `r` to reset the simulated robot from the current ArUco pose. Press `q` to quit.

## How Targets Are Set

The camera gives pixel coordinates such as `(512, 280)`. The controller should not use those directly.

Instead:

```text
camera pixel click
  -> homography transform
  -> world coordinate in meters
  -> saved as path waypoint
```

That means your path file contains stable arena coordinates:

```json
[
  {"x": 0.30, "y": 0.25},
  {"x": 0.80, "y": 0.40},
  {"x": 1.20, "y": 0.80}
]
```

The simulator draws those world points back onto the camera image using the inverse homography.
