# s1_room0804_rviz

Offline ROS 2 Humble package for replaying the recorded room0804 navigation
reachability failure in RViz2.

The package will publish only local visualization data:

- `map.yaml` and `map.pgm` as `nav_msgs/OccupancyGrid`;
- a downsampled `global_cloud_cleaned.pcd` as `sensor_msgs/PointCloud2`;
- recorded start, goal, path line, and collision sphere as visualization
  markers;
- the local S1 URDF through `robot_state_publisher`.

No component in this package may publish robot commands or initialize the
Galbot SDK.

## Current implemented step

The minimal `map_publisher` node reads a local map-server-style YAML/PGM pair
and publishes `nav_msgs/OccupancyGrid` on `/map` using reliable,
transient-local QoS.  It does not read the PCD yet.

```bash
source /opt/ros/humble/setup.bash
source navigation/ros2_ws/install/setup.bash
export ROS_LOCALHOST_ONLY=1
ros2 run s1_room0804_rviz map_publisher --ros-args \
  -p yaml_path:=/absolute/path/to/map.yaml
```

## Map-only RViz2 launch

Build and launch from the repository root:

```bash
source /opt/ros/humble/setup.bash
cd navigation/ros2_ws
colcon build --symlink-install
source install/setup.bash
export ROS_LOCALHOST_ONLY=1
ros2 launch s1_room0804_rviz map_only.launch.py
```

The launch starts only the local map publisher and RViz2.  The fixed frame is
`map`, the view is top-down, and the Map display subscribes to `/map` with
transient-local durability.

## Map and static cloud launch

```bash
source /opt/ros/humble/setup.bash
cd navigation/ros2_ws
colcon build --symlink-install
source install/setup.bash
export ROS_LOCALHOST_ONLY=1
ros2 launch s1_room0804_rviz map_cloud.launch.py
```

The point-cloud node reads only the local binary PCD, extracts XYZ, publishes
every tenth source point by default, and retains the message on
`/static_cloud`.  Override the sampling stride when needed:

```bash
ros2 launch s1_room0804_rviz map_cloud.launch.py point_stride:=20
```

## Recorded forward-1.0-m failure replay

```bash
ros2 launch s1_room0804_rviz failure_replay.launch.py
```

The replay adds ten markers from the recorded PNS evidence: start, goal, their
connecting line, collision sphere 9 and its center, labels, a true-radius red
outline, and a red locator arrow.  The arrow is only a visual locator; the
0.17 m sphere and outline carry the recorded collision size.  The start heading
is deliberately not rendered because the preserved result only contains the
start XY coordinates, not the full orientation.

All launch files publish a local identity transform from `world` to `map` so
RViz2 can resolve the fixed frame without a live robot TF tree.  This transform
defines only the offline visualization root and does not alter map coordinates.

## Pose snapshot preview — separate from the historical failure

```bash
ros2 launch s1_room0804_rviz pose_snapshot_preview.launch.py
```

This is a separate, non-collision scenario using the user-provided read-only
pose snapshot at approximately `(0.419, -0.099)` with yaw `-90.55 deg`.  It
derives the geometry of a relative `base_link +1.0 m` preview but does not run
reachability, does not display sphere 9, and does not claim the target is safe
or reachable.

The scene also loads the local official S1 URDF.  Its `map -> base_link`
transform uses the earlier full pose snapshot.  The 14 arm joints use a later
user-provided `test_move_wrist.py state` read.  Lift, head, wheel and gripper
joints remain at URDF defaults.  The reported gripper width is preserved in the
snapshot YAML but is not applied because the SDK-width-to-URDF-angle mapping is
not verified.  This is a time-composed visualization, not a synchronized
whole-body state snapshot and not collision-clearance evidence.