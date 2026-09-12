# S1 `add_bounding_box` runtime analysis and live-ESDF validation plan

Date: 2026-08-31
Target runtime: S1 host, Galbot SDK 1.9.0, `galbot_fusion_main` PID 4966,
`service_navigation_plan` PID 4599

## Safety and evidence boundary

The investigation used authorized read-only SSH inspection of current type
stubs, process file descriptors, logs, binary strings, ELF symbols, and
disassembly. It did not initialize the SDK, create a DDS reader, publish a
message, call a service, change a box, clear a map, signal a process, or send a
robot command.

The deployed C++ source file `nvblox_embosa_node.cpp` was not present. Function
names and control-flow conclusions below are therefore based on the current
unstripped production binary plus runtime logs, not source-level review.

## Verified API-to-fusion chain

The current SDK 1.9.0 stub documents:

```text
GalbotNavigation.add_bounding_box(box_info)
  box_size: [lx, ly, lz]
  box_pose: [x, y, z, qx, qy, qz, qw] relative to parent_link_name
  box_tag: converted internally to an SDK-marked box name
  parent_link_name
```

The current fusion binary registers these distinct services:

```text
galbot_fusion_add_box
galbot_fusion_get_box
galbot_fusion_remove_box
galbot_fusion_clear_esdf
```

For the user-run tag `4317`, the runtime sequence was:

```text
SDK box_tag 4317
  -> object name sdk_box_4317
  -> galbot_fusion_add_box
  -> NvbloxEmbosaNode::AddBoxInfoServerCallback
  -> validate and deserialize box
  -> store active BoxInfo keyed by name
  -> transform the box from parent_link_name using current TF
  -> NvbloxEmbosaNode::SetPointsFilterBoxs
  -> nvblox projective integrator point filtering
  -> TSDF / occupancy / color integration
  -> ESDF update and publication
```

At `14:05:03.266`, fusion logged one received SDK box, size
`0.60 x 0.50 x 0.375 m`, parent `base_link`, and then reported two active
boxes: the built-in `galbot_fusion_robot_bbox` and `sdk_box_4317`.

## What the box filter does

The production ELF exposes all of the following symbols:

- `NvbloxEmbosaNode::SetPointsFilterBoxs()`
- `ProjectiveTsdfIntegrator::filterPointsWithBoxes(...)`
- `ProjectiveOccupancyIntegrator::filterPointsWithBoxes(...)`
- `ProjectiveColorIntegrator::filterPointsWithBoxes(...)`
- corresponding `filterPointsWithMeshAndBoxes(...)` functions
- CUDA `filter_points_with_boxes_kernel` and
  `filter_points_with_mesh_and_box_kernel`

This is strong direct evidence that active boxes filter incoming sensor points
before those points are integrated into the nvblox TSDF, occupancy, and color
layers. The box is transformed using TF rather than treated as a fixed map-axis
box; the filter therefore follows `base_link` while the recorded pose remains
valid.

## What the box filter does not do

Map clearing is a separate path in the same binary:

- service `galbot_fusion_clear_esdf`
- `NvbloxEmbosaNode::ClearESDFServerCallback(...)`
- log messages `Clearing ESDF...` and `Clear ESDF Done`
- nvblox `Mapper::clearTsdfInsideShapes(...)` and other clear kernels

`AddBoxInfoServerCallback`, `RemoveBoxInfoServerCallback`, and
`ClearESDFServerCallback` are distinct functions and services. The inspected
`AddBoxInfoServerCallback` disassembly contains box deserialization,
validation, map insertion, logging, locking, and response handling; it does not
call the clear callback or TSDF/ESDF clear functions. Runtime logs for the 4317
addition likewise show only box registration followed by continued TSDF/ESDF
publication.

Therefore `add_bounding_box()` is an input-point filter for subsequent
integration. It has no verified retrospective deletion semantics for points or
voxels already fused before registration. `remove_bounding_box()` removes the
future input filter and likewise must not be interpreted as a voxel clear.

The existence of `galbot_fusion_clear_esdf` does not make it safe to call. Its
request schema, scope (whole map versus region), effects on localization/PNS,
and recovery behavior remain unverified.

## Exact live-ESDF validation method

The most authoritative observable is `esdf_pointcloud_serialized`, because it
is the `galbot.perception_proto.EsdfGrid` stream consumed by PNS. Raw LiDAR
alone would show sensor returns but not the final field queried for collision.

The repository already contains a previously validated passive reader:

`experiments/20260828_s1_esdf_rviz/capture_current_pose_esdf.py`

It uses the vendor embosa runtime with the required `LARGE_DATA_TRANSPORT`,
best-effort, keep-last depth 3, volatile QoS and synchronizes the ESDF header to
`/galbot/mes/global_pose`.

For the current hypothesis, extend it from one frame to a bounded window:

1. Passively capture 3--5 seconds of `EsdfGrid` and global-pose frames; do not
   import or initialize Galbot SDK in the capture process.
2. While the capture window is active, run one query-only
   `probe-relative --direction forward --distances 1.0 --checks 1` in a separate
   terminal.
3. Read the corresponding PNS query timestamp and sphere-11 position from the
   existing PNS log; do not modify PNS.
4. Select the ESDF frame nearest that timestamp and verify the measured time
   delta.
5. Decode the exact voxel array and sample:
   - the PNS-reported target sphere-11 center;
   - a small 3x3x3 or 5x5x5 voxel neighborhood around it;
   - the current 4317 physical box volume and the larger filter volume;
   - an adjacent control region outside the box.
6. Compare the sampled ESDF distance against the PNS-reported distance. With
   0.05 m voxels, agreement within one voxel plus interpolation convention is a
   strong same-field check.
7. Visualize the decoded near-obstacle voxels in RViz together with:
   - current S1 pose;
   - current physical box OBB and filter OBB;
   - hypothetical +1 m base pose;
   - target sphere 11 with radius 0.20 m;
   - nearest low-distance voxel cluster.

The existing probe geometry predicts that the target sphere center will lie
inside the current physical box volume. If the synchronized live frame shows a
low-distance/occupied surface in that same current box region and reproduces
the PNS distance, the “pre-filter crate voxels remain in nvblox” hypothesis is
strongly confirmed.

## Stronger causal test

A true A/B causal test would compare the synchronized ESDF and reachability
result before and after a vendor-supported, spatially bounded clear of only the
old crate region while the filter remains active. That operation would change
the live collision map and must not be attempted until the clear-service schema,
scope, rollback, localization impact, and emergency procedure are understood.

Do not use a whole-map clear, fusion restart, attachment removal, enlarged
filter, disabled collision checking, or robot motion as a shortcut.

## Authorization needed for the next step

Running the passive window capture creates a DDS participant, shared-memory
reader, temporary files under `/tmp`, and bounded CPU/memory/bandwidth load. It
does not publish or control the robot, but it is more than pure file inspection
and requires explicit authorization before execution.