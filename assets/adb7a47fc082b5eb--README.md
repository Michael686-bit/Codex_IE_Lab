# S1 local ESDF RViz investigation

This experiment prepares a passive one-frame Fast DDS capture of the local
ESDF consumed by PNS. It does not import or initialize `galbot_sdk`, publish any
DDS message, change localization/navigation state, or control any robot device.

Verified 2026-08-28 inputs:

- serialized channel: `esdf_pointcloud_serialized`;
- protobuf: `galbot.perception_proto.EsdfGrid`;
- expected resolution and dimensions: `0.05 m`, `200 x 200 x 42`;
- capture runtime: the managed S1 Python 3.8 environment, because the installed
  generated protobuf files are incompatible with the host system Python's
  newer protobuf package. The capture script uses the managed Python 3.8
  interpreter while explicitly adding the image's compatible system
  `protobuf 3.6.1` package path.

The installed generated protobuf needs a version between the managed
environment (missing protobuf) and the host package (protobuf 3.6.1, too old).
No package is installed or replaced. `capture_one_esdf_frame.py` instead uses
the vendor's low-level embosa reader and saves the exact serialized protobuf
payload as `.pb`; decoding happens locally.

The reader explicitly matches the live topic QoS reported by the vendor tool:
`LARGE_DATA_TRANSPORT`, best-effort reliability, keep-last depth 3, volatile
durability, and intra-core pub/sub. The default reader is not sufficient for
the roughly 6.7 MB ESDF payload.

The script accepts only the reviewed channel, limits runtime to 30 seconds, and
restricts output to a direct child of `/tmp`. The reader and embosa runtime are
explicitly shut down. Running it still creates a temporary DDS participant,
shared-memory resources, and a local raw frame file; therefore it requires
separate authorization from file-only inspection.

## 2026-08-28 captured frame

The user authorized one passive reader on the S1 host. The first two attempts
failed before producing a frame: the high-level binding had an incompatible
protobuf runtime, and the default low-level reader used an insufficient shared
memory transport. The vendor `embosa_topic_tool` then verified the exact live
QoS: `LARGE_DATA_TRANSPORT`, best effort, keep-last depth 3, and volatile
durability. With that QoS, the third reader captured one frame successfully.

- remote temporary source: `/tmp/s1_esdf_frame_20260828_once.pb`;
- local evidence copy: `data/s1_esdf_frame_20260828_once.pb`;
- payload bytes: `6,720,121`;
- SHA-256: `0ab948b68968544990b7cc7c39fcca8abe06ee8adaf06eb20fa1b94cfe858f22`;
- no protobuf or Galbot SDK was imported by the successful reader;
- no publisher, motion, localization, navigation, or configuration command was
  created or sent.

`decode_esdf_frame.py` decodes the protobuf wire format locally and creates the
NPZ replay artifact. Verified frame values are `0.05 m`, `200 x 200 x 42`,
1,680,000 finite distances, `frame_id=base_link`, and distance range
`0..3.7195 m`. Spatial-continuity checks identify the flat layout as
`x + nx*(y + ny*z)`; this inference should still be compared with authoritative
fusion source if exact half-voxel conventions become safety-critical.

At this later capture time, sampled ESDF distances at sphere 9 projected to
current/forward 0.7/forward 0.8/forward 1.0 m were approximately
`0.814/0.925/0.967/1.075 m`. The earlier `0.126 m` forward collision was not
present in this captured frame. This is evidence that the runtime field changed
or cleared; it does not by itself identify which sensor or transform produced
the earlier anomaly.

The offline ROS 2 publisher is installed into the existing `s1_rviz_demo`
package. It publishes `/s1/esdf/near_obstacle`, `/s1/esdf/slice`, and
`/s1/esdf/diagnostic_markers` without connecting to S1.

As of 2026-08-31, that `s1_rviz_demo` package is the project's sole canonical
RViz implementation for new navigation/ESDF diagnostics. The separate
`s1_room0804_rviz` package in the external SDK-learning workspace is retained
only as a static-map/historical reference and must not receive parallel viewer
features.

Decode/rebuild once:

```bash
cd '/home/lsy03/文档/ChatGPT/S1'
python3 experiments/20260828_s1_esdf_rviz/decode_esdf_frame.py \
  experiments/20260828_s1_esdf_rviz/data/s1_esdf_frame_20260828_once.pb \
  --npz experiments/20260828_s1_esdf_rviz/data/s1_esdf_frame_20260828_once.npz

cd experiments/20260822_s1_rviz_demo/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select s1_rviz_demo
source install/setup.bash
ros2 launch s1_rviz_demo view_captured_esdf.launch.py
```

Useful launch overrides are `near_threshold_m:=0.17`, `slice_z_m:=0.40`, and
`max_near_points:=180000`. This launch is offline even though its source frame
was captured from the real S1.

The revised viewer intentionally uses a time-composed robot state:

- near-obstacle voxels use a fixed red color;
- the 0.40 m distance slice uses fixed 0--1 m intensity bounds and is enabled
  by default at the user's request;
- `map -> base_link` uses the earlier complete `pose_readonly` result;
- the fourteen arm joints use the later user-provided state read;
- lift, head, wheels and grippers remain at URDF defaults;
- an in-scene warning states that ESDF, base pose and arms were not captured at
  the same time and that the display is not live.

Continuous real-time streaming is deliberately deferred. A full ESDF message
is about 6.7 MB and uses the vendor's large-data DDS transport. Before keeping a
persistent bridge running, the ESDF frame, base pose, joint state and PNS query
must be timestamped together; otherwise a visually convincing display could
still combine different robot states and give a false collision interpretation.

## Timestamp-synchronized base pose + ESDF frame

At the user's request, `capture_current_pose_esdf.py` passively subscribed to
`esdf_pointcloud_serialized` and `/galbot/mes/global_pose` in one embosa node.
It observed 45 pose frames and selected the pose nearest the ESDF header stamp.
Both selected messages had exactly `1787910212000000000 ns`, for a measured
delta of `0.0 ms`.

The synchronized map pose is approximately
`[0.413935,-0.101069,-0.016797,0.003628,-0.000234,-0.710142,0.704049]`.
The captured frame again contained `200 x 200 x 42` voxels at `0.05 m`. Sphere
9 samples at current/forward 0.7/0.8/1.0 m were approximately
`0.806/0.921/0.963/1.071 m`, so this synchronized frame still does not reproduce
the historical `0.126 m` anomaly. The RViz launch now uses this NPZ by default
for both the ESDF and `map -> base_link`; arm joints remain the older snapshot
and are explicitly excluded from the synchronization claim.