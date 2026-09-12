# S1 three-LiDAR live RViz bridge

Date: 2026-08-31

## Purpose

Display the three raw S1 LiDAR streams in local ROS 2 Humble/RViz without
initializing Galbot SDK or publishing anything back to S1.

```text
S1 raw Fast DDS PointCloud2 topics
  -> passive embosa readers on S1
  -> current /embosa_tf + /embosa_tf_static transform to base_link
  -> finite/range/point-count bounds
  -> compact float32 XYZ stream over an existing SSH ControlMaster
  -> local ROS 2 PointCloud2 topics
  -> RViz2
```

## Safety boundary

The bridge:

- imports no Galbot SDK;
- creates no S1 DDS publisher;
- sends no navigation, localization, controller, arm, gripper, lift, or base
  command;
- changes no fusion/PNS configuration;
- creates three LiDAR readers plus dynamic/static TF readers;
- uses bounded S1 CPU/shared-memory/network load and cleans up on termination.

The local robot model uses the official URDF for meshes and fixed joints. S1
`/embosa_tf` is forwarded at a bounded rate for the live `map -> base_link` and
moving-joint transforms; the old arm snapshot publisher is not used. The model
and point clouds therefore share the live S1 TF tree. Their individual message
timestamps remain asynchronous sensor samples rather than one atomic
whole-body observation.

## Verified S1 inputs

| Sensor | Topic | Frame |
| --- | --- | --- |
| chassis | `/lidar_chassis_f/lidar/data_raw` | `chassis_lidar_base_link` |
| head | `/lidar_head_f/lidar/data_raw` | `head_lidar_base_link` |
| back | `/lidar_body_b/lidar/data_raw` | `back_lidar_base_link` |

All three use `galbot.sensor_proto.PointCloud2` with:

- approximately 10 Hz input;
- `LARGE_DATA_TRANSPORT`, best effort, keep-last depth 3, volatile QoS;
- 19,968 points per observed frame;
- little-endian, point step 26 bytes;
- scalar float32 `x/y/z` at offsets `0/4/8`;
- one serialized frame about 519 KB.

The bridge also passively reads `galbot.tf2_proto.TF2Message` from
`/embosa_tf_static` and `/embosa_tf`. Verified transform chains are:

- chassis LiDAR -> `base_link`;
- back LiDAR -> `base_link`;
- head LiDAR -> head joints -> torso/lift/column/chassis -> `base_link`.

## Implemented files

- `s1_lidar_stream.py`: S1-side passive reader, protobuf wire decoder, TF tree,
  range/point limit, and compact binary stream.
- `test_s1_lidar_stream.py`: local parser, TF, validation, and downsampling tests.
- existing ROS package `s1_rviz_demo`:
  - `scripts/live_lidar_ssh_bridge.py`
  - `scripts/carried_box_markers.py`
  - `scripts/room0804_map_publisher.py`
  - `scripts/room0804_pcd_publisher.py`
  - `launch/view_live_lidars.launch.py`
  - `rviz/live_lidars.rviz`

## Current conservative live settings

- requested output: 2 Hz per sensor;
- requested dynamic TF output: 10 Hz;
- observed local ROS rate: approximately 1.65--1.73 Hz per sensor;
- maximum transmitted points: 20,000 per frame;
- range bound: 10 m;
- local topics:
  - `/s1/lidar/chassis_raw` (green)
  - `/s1/lidar/head_raw` (orange)
  - `/s1/lidar/back_raw` (cyan)
- point-cloud output frame: `base_link`;
- RViz fixed frame: `map`.

## Verified room0804 global-map overlay — 2026-09-01

The same live launch now reads the verified local `room0804` assets and, by
default, publishes both forms of the global map without sending them to S1:

| Display | Local topic | Type | Frame | QoS |
| --- | --- | --- | --- | --- |
| 2D navigation map | `/map` | `nav_msgs/OccupancyGrid` | `map` | reliable, transient local |
| 3D cleaned map | `/s1/map/global_cloud` | `sensor_msgs/PointCloud2` | `map` | reliable, transient local |

The 2D map is `800 x 220` at `0.05 m/cell`, with origin
`[-3.70319, -6.71105, 0]`. The binary PCD contains 2,177,227 source points;
the default `map_point_stride:=10` publishes 217,723 finite XYZ points. The
RViz config enables both displays and uses a purple flat color for the global
PCD so it remains distinct from the green/orange/cyan live LiDAR streams.

The local 2D map files were SHA-256-identical to the files under the S1's
current `/var/maps/cur -> /var/maps/room0804`. Current S1 startup logs also
recorded successful loading of 106 localization key poses, the 2,177,227-point
global PCD, and `global_cloud_cleaned.esdf`. This confirms the selected static
assets and the live `map` TF refer to room0804; it does not claim that static
PCD alone represents current dynamic obstacles.

The publishers fail explicitly on missing/malformed assets. The large PCD is
not copied into the ROS package or Git. Useful controls are:

```text
publish_2d_map:=true|false
publish_3d_map:=true|false
map_point_stride:=10
map_yaml_path:=/absolute/path/to/map.yaml
map_pcd_path:=/absolute/path/to/global_cloud_cleaned.pcd
```

Local build, unit tests, and isolated ROS topic verification passed. The topic
check confirmed one publisher per topic, the expected message types and sizes,
and reliable/transient-local endpoint QoS.

The live view also publishes `/visualization_marker_array` with frame-locked
markers sourced from the exact navigation CLI 4317 profile:

- yellow translucent cube + wireframe: fusion filter
  `0.60 x 0.50 x 0.375 m`;
- cyan translucent cube + wireframe: physical/PNS collision box
  `0.40 x 0.30 x 0.175 m`;
- red translucent cube + wireframe: official axis-aligned example
  `0.40 x 0.30 x 0.28 m` at `[0.45, 0, 0.25]`.

The 4317 physical and filter boxes use profile
`4317_left_mount_20260831_193312_191` and share this pose relative to
`left_arm_end_effector_mount_link`:

```text
[0.088464546,-0.209262727,-0.158900000,
 0.011116385,-0.000386121,0.697301150,0.716691972]
```

Because the markers use the left arm mount and `frame_locked=true`, they follow
the live base, torso, and arm TF chain in the RViz `map` fixed frame.  A
repository test asserts that the YAML marker profile matches the size, pose,
tag, and parent constants in `s1_navigation_cli.py` exactly.

One verified chassis output frame contained 19,684 points after the 10 m range
bound and had `frame_id=base_link`.

Live TF verification with local `tf2_echo` showed continuously updating
`map -> base_link`, `map -> left_arm_link7`, and
`map -> left_arm_end_effector_mount_link` chains.  The left-mount marker profile
therefore resolves in the live RViz scene rather than remaining an orphan frame.

## Failure and recovery record — 2026-09-01

### Observed failure

The user-provided runtime log reported:

```text
FileNotFoundError:
SSH ControlPath does not exist:
/tmp/s1_codex_mux_20260831_lidar
```

This matches the bridge startup guard in
`s1_rviz_demo/scripts/live_lidar_ssh_bridge.py`: it checks that the local SSH
ControlPath exists before starting the SSH subprocess.  The ControlMaster had
therefore expired or its socket had been cleaned up, so
`live_lidar_ssh_bridge.py` exited immediately.  The launch could leave RViz and
the other local nodes visible, but there was no remote LiDAR stream and no
forwarded live S1 TF.

The resulting symptoms were:

- no three live LiDAR point-cloud topics;
- no live `map -> base_link` or arm TF update from S1;
- an incomplete `map -> base_link -> left_arm_end_effector_mount_link` chain;
- the left-end-effector yellow/cyan carried-box markers could not resolve in
  RViz;
- RViz showed only the RobotModel without live state.

The `unrealistic inertia` warnings were recorded as unrelated warnings, not as
the cause of this stream/TF failure.

### Recovery procedure

First stop the incomplete launch in the RViz terminal with `Ctrl+C`.  In the
recorded run, the residual processes were Launch PID `634077` and RViz PID
`634084`.  If the original terminal cannot be found, the documented fallback
is:

```bash
kill -INT 634077
```

Only after the old launch has stopped, recreate the SSH ControlMaster:

```bash
umask 077
ssh -fN -M \
  -S /tmp/s1_codex_mux_20260831_lidar \
  -o ControlPersist=2h \
  galbot@10.34.216.17
```

Check that the master is alive:

```bash
ssh -S /tmp/s1_codex_mux_20260831_lidar \
  -O check \
  galbot@10.34.216.17
```

Expected output includes `Master running`.

Upload the S1-side temporary reader again, because an S1 restart or `/tmp`
cleanup may have removed it:

```bash
cd '/home/lsy03/文档/ChatGPT/S1'

scp -o ControlPath=/tmp/s1_codex_mux_20260831_lidar \
  experiments/20260831_s1_lidar_live_rviz/s1_lidar_stream.py \
  galbot@10.34.216.17:/tmp/s1_lidar_stream_20260831.py
```

Then start one fresh local launch:

```bash
cd '/home/lsy03/文档/ChatGPT/S1/experiments/20260822_s1_rviz_demo/ros2_ws'

source /opt/ros/humble/setup.bash
source install/setup.bash

mkdir -p /tmp/s1_live_lidar_ros_logs
export ROS_LOG_DIR=/tmp/s1_live_lidar_ros_logs
export ROS_DOMAIN_ID=84

ros2 launch s1_rviz_demo view_live_lidars.launch.py
```

Successful startup should again show `Starting passive S1 LiDAR stream`, one
`first_frame` line for each of `chassis`, `head`, and `back`, and recurring
`Received LiDAR frames: chassis=..., head=..., back=...` output.  The live TF
chain and the left-mounted markers should then resolve in RViz.

Do not start the fresh launch before the old one is stopped.  Otherwise two
`carried_box_markers.py` instances publish the same `/visualization_marker_array`,
which can make the yellow/cyan boxes appear to jump between publishers.

The SSH master is intentionally temporary (`ControlPersist=2h`).  When it
expires or `/tmp` is cleaned, repeat the ControlMaster creation, health check,
S1 script upload, and single-launch sequence above.  This recovery record is
based on the user-provided runtime log and procedure; no SSH connection or
robot command was executed while documenting it.

## Reproduce

Establish an SSH master:

```bash
umask 077
ssh -fN -M \
  -S /tmp/s1_codex_mux_20260831_lidar \
  -o ControlPersist=2h \
  galbot@10.34.216.17
```

Upload the reviewed S1 reader:

```bash
cd '/home/lsy03/文档/ChatGPT/S1'
scp -o ControlPath=/tmp/s1_codex_mux_20260831_lidar \
  experiments/20260831_s1_lidar_live_rviz/s1_lidar_stream.py \
  galbot@10.34.216.17:/tmp/s1_lidar_stream_20260831.py
```

Build and launch locally:

```bash
cd '/home/lsy03/文档/ChatGPT/S1/experiments/20260822_s1_rviz_demo/ros2_ws'
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select s1_rviz_demo
source install/setup.bash
export ROS_LOG_DIR=/tmp/s1_live_lidar_ros_logs
export ROS_DOMAIN_ID=84
ros2 launch s1_rviz_demo view_live_lidars.launch.py
```

Useful launch bounds:

```text
output_hz:=1.0 max_points:=10000 max_range_m:=8.0
```

Press `Ctrl+C` in the launch terminal to stop RViz, local publishers, SSH
stream, and remote readers. Verify no remote reader remains with:

```bash
ssh -S /tmp/s1_codex_mux_20260831_lidar galbot@10.34.216.17 \
  pgrep -af s1_lidar_stream_20260831.py
```

An empty result is expected.