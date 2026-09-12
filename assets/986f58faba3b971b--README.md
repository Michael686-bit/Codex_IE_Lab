# S1 TSDF offline and bounded live RViz bridge

Date: 2026-09-02

## Verified live source

The current S1 `galbot_fusion_main` publishes:

```text
topic: tsdf_pointcloud_serialized
type: galbot.perception_proto.TsdfGrid
publisher: galbot_fusion|galbot_fusion_main
QoS: LARGE_DATA_TRANSPORT, best effort, keep-last depth 3, volatile
observed source rate: approximately 7.1--7.8 Hz
```

The source is a vendor TSDF debug point representation, not a complete dense
regular voxel array. The captured protobuf has these top-level fields:

```text
1 header
2 voxel_size_m
3 packed repeated float voxel_data
4 current_pose
```

`voxel_data` is grouped in five float32 values. Runtime inspection of the
current security manager verifies it reads `std::array<float, 5>` and keeps
records whose fourth value is `<= 0` as obstacle points. The first three values
are XYZ and the fourth is therefore exported as `tsdf_distance`. The exact
semantics of the fifth value are not established by an installed source/schema;
it is deliberately named `auxiliary`, not `weight`.

## Authorized passive capture

One TSDF frame and the nearest `/galbot/mes/global_pose` were captured with
exactly matching header timestamps. No Galbot SDK, DDS publisher, service,
navigation/localization/configuration call, or robot command was used.

```text
timestamp: 1788311956000000000 ns
pose delta: 0.0 ms
raw TSDF bytes: 934,839
voxel size: 0.05 m
debug points: 46,736
source frame: base_link
local bounds: x [-4.974, 5.000], y [-4.998, 3.838], z [0.015, 2.100] m
map bounds: x [-2.425, 7.925], y [-4.775, 4.275], z [0.025, 2.075] m
fourth value range: exactly 0 in this captured frame
fifth values: 0 for 668 records, 3 for 46,068 records
```

Raw `.pb` and generated `.npz` files stay local and are ignored by Git. Their
hashes are recorded in `data/ASSET_MANIFEST.sha256`.

## Offline decode and RViz

Decode the captured frame:

```bash
cd '/home/lsy03/文档/ChatGPT/S1'
python3 experiments/20260902_s1_tsdf_rviz/decode_tsdf_frame.py \
  experiments/20260902_s1_tsdf_rviz/data/s1_tsdf_20260902_0920_tsdf.pb \
  --pose experiments/20260902_s1_tsdf_rviz/data/s1_tsdf_20260902_0920_pose.pb \
  --npz experiments/20260902_s1_tsdf_rviz/data/s1_tsdf_20260902_0920.npz
```

Build and start the offline viewer:

```bash
cd '/home/lsy03/文档/ChatGPT/S1/experiments/20260822_s1_rviz_demo/ros2_ws'
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select s1_rviz_demo
source install/setup.bash
export ROS_LOCALHOST_ONLY=1
ros2 launch s1_rviz_demo view_captured_tsdf.launch.py
```

It publishes reliable, transient-local topics:

```text
/s1/tsdf/surface             sensor_msgs/PointCloud2
/s1/tsdf/slice               sensor_msgs/PointCloud2
/s1/tsdf/diagnostic_markers  visualization_msgs/MarkerArray
```

The verified default capture publishes 46,736 surface points and 726 points in
the `z=0.40 m` slice. Both clouds are pre-transformed to `map` using the pose
embedded in the same TsdfGrid. The room0804 2D map and downsampled global PCD
are available as context. The robot arms remain an older snapshot and are
explicitly outside the TSDF/base synchronization claim.

## Optional bounded live bridge

Upload the reviewed S1-side reader after each S1 restart or `/tmp` cleanup:

```bash
cd '/home/lsy03/文档/ChatGPT/S1'
scp -o ControlPath=/tmp/s1_codex_mux_20260831_lidar \
  experiments/20260902_s1_tsdf_rviz/s1_tsdf_stream.py \
  galbot@10.34.216.17:/tmp/s1_tsdf_stream_20260902.py
```

Then enable the normally disabled bridge in the existing live viewer:

```bash
ros2 launch s1_rviz_demo view_live_lidars.launch.py publish_live_tsdf:=true
```

The bridge samples the latest vendor stream at 1 Hz, transforms each selected
frame to `map` with the pose embedded in that message, enforces point limits,
and publishes volatile/reliable ROS 2 clouds. The remote script imports no
Galbot SDK and creates no publisher or service client.

### Important runtime cost

The end-to-end bridge was verified with approximately 48,000 surface points
and 3,200 slice points per frame. However, the vendor Python/embosa
`LARGE_DATA_TRANSPORT` reader consumed about 59--64% of one CPU core and
approximately 410--450 MB RSS in steady-state sampling on the 12-core S1 host.
Reducing Python polling and copying did not remove this cost, showing that the
dominant load is inside the vendor large-message reader path.

Therefore `publish_live_tsdf` remains `false` by default. Use the live bridge
only for short, supervised diagnostics; stop it after use. A low-load always-on
bridge requires vendor C++ headers/source or an official already-filtered ROS/
network output, neither of which is installed on the inspected S1 image.

## Safety boundary

Neither offline nor live code moves the base, arms, grippers, or lift. It does
not clear TSDF/ESDF, add/remove a bounding box, restart fusion, modify
localization/navigation, publish S1 DDS messages, or call Galbot SDK. The live
reader still creates a DDS participant and has the documented CPU/RSS cost, so
it requires explicit authorization and supervision whenever run.