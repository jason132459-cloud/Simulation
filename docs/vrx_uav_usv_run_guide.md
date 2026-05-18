# VRX UAV-USV ArUco Simulator Run Guide

This guide summarizes how to run the current Gazebo / ROS 2 Jazzy simulator setup for the UAV camera and USV ArUco target workflow.

## Current Simulation Flow

```text
Parrot Bebop 2 downward camera
  -> /parrot_bebop_2/downward_camera/image
  -> aruco_detector_node
  -> /target_pose
  -> waypoint_generator_node
  -> /usv1/goal_pose
  -> /usv2/goal_pose
```

The UAV is currently a static Parrot Bebop 2 model hovering above the `my_roboboat` model. The ArUco marker is attached to the top of `my_roboboat` and is treated as the target object.

## Local Workspace Paths

```bash
~/vrx_ws
~/vrx_ws/src/uav_usv_aruco
~/gazebo_maritime/models/parrot_bebop_2
~/gazebo_maritime/models/my_roboboat
```

Important files:

```bash
~/vrx_ws/src/uav_usv_aruco/uav_usv_aruco/aruco_detector_node.py
~/vrx_ws/src/uav_usv_aruco/uav_usv_aruco/waypoint_generator_node.py
~/vrx_ws/src/uav_usv_aruco/launch/aruco_pipeline.launch.py
~/vrx_ws/src/uav_usv_aruco/launch/nbpark_aruco_demo.launch.py
~/vrx_ws/src/vrx/vrx_gz/worlds/nbpark.sdf
~/gazebo_maritime/models/my_roboboat/model.sdf
~/gazebo_maritime/models/parrot_bebop_2/model.sdf
```

## Environment Setup

Use ROS 2 Jazzy. Humble is not installed in the current WSL environment.

```bash
source /opt/ros/jazzy/setup.bash
cd ~/vrx_ws
source install/setup.bash
```

If the terminal starts with `(base)`, disable or leave conda first:

```bash
conda deactivate
```

Optional one-time setting to stop conda base from auto-starting:

```bash
conda config --set auto_activate_base false
```

Check that ROS is available:

```bash
which ros2
```

Expected:

```text
/opt/ros/jazzy/bin/ros2
```

## Build

After changing the ROS package or VRX world file:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/vrx_ws
colcon build --merge-install --packages-select vrx_gz uav_usv_aruco
source install/setup.bash
```

If only the Python ROS package changed:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/vrx_ws
colcon build --merge-install --packages-select uav_usv_aruco
source install/setup.bash
```

To rebuild the whole workspace:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/vrx_ws
colcon build --merge-install
source install/setup.bash
```

## VRX Base Run Commands

Use these commands when you want to run VRX itself before running the UAV/ArUco pipeline.

### 1. Start a clean terminal

Do not type setup or ROS commands into a terminal that is already running Gazebo logs. Open a new WSL terminal.

```bash
conda deactivate
source /opt/ros/jazzy/setup.bash
cd ~/vrx_ws
source install/setup.bash
export GZ_SIM_RESOURCE_PATH=:$HOME/gazebo_maritime/models:$GZ_SIM_RESOURCE_PATH
```

Check the environment:

```bash
which ros2
echo $GZ_SIM_RESOURCE_PATH
```

### 2. Run the customized `nbpark` world

This is the main world used for the Parrot Bebop 2 + ArUco marker test.

```bash
ros2 launch vrx_gz vrx_environment.launch.py world:=nbpark
```

The customized `nbpark` world includes:

```text
parrot_bebop_2 at (-175, 1120, 8)
my_roboboat at (-175, 1120, 0)
ArUco marker on my_roboboat
```

### 3. Run VRX without GUI

Use this when you only need topics and want less graphics load.

```bash
ros2 launch vrx_gz vrx_environment.launch.py world:=nbpark headless:=True
```

### 4. Start paused

Use this for debugging world loading before physics starts.

```bash
ros2 launch vrx_gz vrx_environment.launch.py world:=nbpark paused:=True
```

### 5. Run the original VRX competition launch

Use this when following the standard VRX competition launch flow.

```bash
ros2 launch vrx_gz competition.launch.py world:=nbpark
```

If a specific competition launch requires extra arguments, inspect available arguments with:

```bash
ros2 launch vrx_gz competition.launch.py --show-args
```

### 6. Show available VRX launch arguments

```bash
ros2 launch vrx_gz vrx_environment.launch.py --show-args
```

Common arguments include:

```text
world
sim_mode
bridge_competition_topics
config_file
robot
headless
paused
competition_mode
extra_gz_args
```

### 7. Check Gazebo / VRX topics

In a second terminal:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/vrx_ws
source install/setup.bash

ros2 topic list | head
ros2 topic list | grep -E "clock|vrx|parrot|camera|wamv|goal|target"
```

Check Gazebo-native topics:

```bash
gz topic -l | grep -E "parrot|camera|image|nbpark|world"
```

### 8. Stop VRX

In the terminal running Gazebo / VRX:

```text
Ctrl+C
```

Wait until the shell prompt returns before running another launch command.

### 9. Common VRX startup problems

If `ros2: command not found` appears:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/vrx_ws
source install/setup.bash
```

If custom models are missing, re-export the Gazebo model path:

```bash
export GZ_SIM_RESOURCE_PATH=:$HOME/gazebo_maritime/models:$GZ_SIM_RESOURCE_PATH
```

If Gazebo opens but the screen is black, wait a little, move the camera, or try software rendering:

```bash
export LIBGL_ALWAYS_SOFTWARE=1
ros2 launch vrx_gz vrx_environment.launch.py world:=nbpark
```

If a world edit is not reflected, rebuild and restart Gazebo:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/vrx_ws
colcon build --merge-install --packages-select vrx_gz
source install/setup.bash
ros2 launch vrx_gz vrx_environment.launch.py world:=nbpark
```

## Run Everything

This launches the VRX `nbpark` world, the Parrot Bebop 2 camera bridge, ArUco detector, and waypoint generator.

```bash
conda deactivate
source /opt/ros/jazzy/setup.bash
cd ~/vrx_ws
source install/setup.bash
ros2 launch uav_usv_aruco nbpark_aruco_demo.launch.py
```

## Run Only the ArUco Pipeline

Use this when Gazebo is already running.

```bash
conda deactivate
source /opt/ros/jazzy/setup.bash
cd ~/vrx_ws
source install/setup.bash
ros2 launch uav_usv_aruco aruco_pipeline.launch.py
```

## Expected Topics

```bash
ros2 topic list | grep -E "parrot_bebop_2|target_pose|goal_pose"
```

Expected topics:

```text
/parrot_bebop_2/downward_camera/image
/target_pose
/usv1/goal_pose
/usv2/goal_pose
```

## Check Camera Image Publishing

```bash
ros2 topic hz /parrot_bebop_2/downward_camera/image
```

A rate around several Hz means the Gazebo camera and bridge are working.

## Check ArUco Detection

```bash
ros2 topic echo /target_pose
```

When the detector sees marker ID 0, `/target_pose` should publish a pose near the boat position, for example:

```text
position:
  x: -174.96
  y: 1119.99
  z: 0.405
```

The detector log should show messages like:

```text
image received: 1280x720, encoding=rgb8, frame_id=parrot_bebop_2/body/downward_camera
Detected ArUco ids: [0]
marker 0 -> /target_pose x=-174.96, y=1119.99
```

## Check Generated USV Goals

```bash
ros2 topic echo /usv1/goal_pose
ros2 topic echo /usv2/goal_pose
```

These are generated by `waypoint_generator_node` from `/target_pose`. They are the left/right cooperative approach points for the two USVs.

## Manual Target Test

This bypasses vision and manually publishes a target pose. Use it to test the waypoint generator.

```bash
ros2 topic pub --once /target_pose geometry_msgs/msg/PoseStamped "{header: {frame_id: 'map'}, pose: {position: {x: -175.0, y: 1120.0, z: 0.0}, orientation: {w: 1.0}}}"
```

Then check:

```bash
ros2 topic echo /usv1/goal_pose
ros2 topic echo /usv2/goal_pose
```

## Current Model Details

Parrot Bebop 2 include in `nbpark.sdf`:

```xml
<include>
  <name>parrot_bebop_2</name>
  <pose>-175 1120 8 0 0 3.14</pose>
  <uri>parrot_bebop_2</uri>
</include>
```

The Parrot model has a custom downward camera added:

```xml
<sensor name="downward_camera" type="camera">
  <pose>0.08 0 -0.09 0 1.5708 0</pose>
  <always_on>1</always_on>
  <update_rate>30</update_rate>
  <topic>/parrot_bebop_2/downward_camera/image</topic>
</sensor>
```

The ArUco marker is on `my_roboboat` and currently uses the original size:

```xml
<size>0.28 0.28</size>
```

## Troubleshooting

If `ros2: command not found` appears, source Jazzy first:

```bash
source /opt/ros/jazzy/setup.bash
source ~/vrx_ws/install/setup.bash
```

If `/target_pose` does not publish:

```bash
ros2 node list | grep aruco
ros2 node info /aruco_detector_node
ros2 topic info -v /target_pose
ros2 topic hz /parrot_bebop_2/downward_camera/image
```

Interpretation:

```text
No /aruco_detector_node
  -> detector launch failed or was not started.

Camera topic has no Hz
  -> Gazebo camera or ros_gz_bridge issue.

Camera topic has Hz but /target_pose is empty
  -> image is arriving, but ArUco marker is not detected.
```

The current `aruco_detector_node.py` avoids `cv_bridge` for image conversion because `cv_bridge` caused a segmentation fault in this environment. It directly converts `sensor_msgs/Image` data into a NumPy/OpenCV image.
