# 2026-09-04 right-wrist RGB-D, SAM3, and raw/LingBot ROI run

## Objective

Establish a fresh, replayable FDP input bundle from one live right-wrist RGB-D
capture, while comparing the production-compatible LingBot depth path with an
explicit raw-depth path.  Stop before FDP, planning, or execution.

## Safety level and physical boundary

- Level: live read-only sensor/state inspection.
- Device read: right-wrist RGB-D camera.
- State read: 17 whole-body joints solely to bind capture-time provenance.
- Arm, gripper, torso, and mobile base motion: none.
- Planning/execution/FDP: not called.
- The capture held `/home/galbot/ie_lab/control.lock` non-blockingly.
- After completion the lock was available, the production container remained
  stopped, and zero matching control processes were present.

## Source and runtime

- S1 SDK Python: `/home/galbot/ie_lab/bin/s1-python`, SDK environment labelled
  1.9.0.  The runtime printed that 1.9.1 was available; no upgrade was made.
- Baseline root: `/home/galbot/Lsy03/fdp_baseline`.
- Production ROI modules:
  `/home/galbot/ie_lab/projects/dual_arm_v5/workspace/s1_sjtu_0806/vendor/g1_workbin_perception`.
- Thor SAM3: `10.34.216.11:7861`.
- Thor LingBot-Depth: `10.34.216.11:7865`.
- Credentials were read from the existing production site file in memory and
  were neither printed nor copied into any artifact.

## Commands

Live capture (the only robot-connected step):

```bash
/home/galbot/ie_lab/bin/s1-python scripts/capture_right_wrist_rgbd_once.py \
  --output-dir captures/right_wrist_20260904_01 \
  --settle-s 3 \
  --timeout-s 15 \
  --acknowledge-readonly-live-s1
```

Frozen-file perception A/B (no robot access):

```bash
python3 scripts/build_fresh_fdp_case.py \
  --capture-dir captures/right_wrist_20260904_01 \
  --output-dir outputs/live_perception_20260904_01_retry1 \
  --case-root cases \
  --depth-mode both \
  --site-config /home/galbot/ie_lab/projects/dual_arm_v5/workspace/s1_sjtu_0806/config/site.production.yaml \
  --perception-root /home/galbot/ie_lab/projects/dual_arm_v5/workspace/s1_sjtu_0806/vendor/g1_workbin_perception \
  --mesh /home/galbot/ie_lab/projects/dual_arm_v5/workspace/s1_sjtu_0806/assets/mesh/EU4322_midcut_target175mm.obj \
  --timeout-s 180
```

Both frozen cases were then replayed with `scripts/replay_roi_case.py`; these
replays called neither the robot nor any network service.

## Capture result

- RGB: 1280 x 720.
- Aligned depth: 1280 x 720.
- RGB/depth timestamp skew: 0 ns.
- Capture-time TF timestamp skew: 0 ns.
- Raw depth valid ratio: 0.8521506076388888.
- Static-vs-capture TF delta: about 0.000001996 m and 0.002658 deg.
- Recorded SDK calls were limited to `init`, RGB/depth/intrinsic/state/extrinsic/
  transform getters, and `GalbotRobot.destroy`.
- `motion_commands_sent=false`.

## SAM3 result and preserved failure

SAM3 returned 12 masks with scores from 0.54296875 to 0.953125.  The first
attempt was preserved at `outputs/live_perception_20260904_01`: the current Thor
response stores integer mask count in `masks` and PNG payloads in
`mask_png_base64`; the new client initially treated the integer as mask data.
The decoder was corrected to match the existing production compatibility rule,
covered by a regression test, and the successful result was written to the new
`retry1` directory rather than overwriting the failed experiment.

## Raw versus LingBot result

Both branches selected SAM index 3, visually the right-most open blue crate in
the captured image.

| Metric | Raw depth | LingBot depth |
|---|---:|---:|
| Valid depth ratio | 0.852151 | 0.998390 |
| Selected center in base_link (m) | [0.873561, 0.354580, 0.643720] | [0.819408, 0.367405, 0.644471] |
| Selected yaw (deg) | 79.7800 | -87.5283 |
| Final mask pixels | 96,418 | 87,025 |
| 4317/H4 candidate indices | [3, 9, 5, 8] | [3, 9] |

Cross-branch metrics:

- selected center delta: 0.0556559 m;
- 180-degree-symmetric yaw delta: 12.6917 deg;
- final mask IoU: 0.891789;
- same selected SAM index: true.

The production-compatible target is 4317/H4 in both branches, but neither
branch is strictly unique.  Both case manifests therefore set
`human_review_required=true` and `ready_for_fdp=false`.  No FDP request was
made.

## Offline replay result

For both raw and LingBot cases:

- selected ROI index matched;
- center delta was 0 m;
- symmetric yaw delta was 0 deg;
- final mask IoU was 1.0;
- network services called: none;
- robot SDK imported: false;
- motion commands sent: false.

## Primary artifacts and SHA-256

```text
3fff347b346d558163571b93fbf05205754da90335e39e9dc535233d016145de  captures/right_wrist_20260904_01/capture_result.json
adbabeebb5be8bd187a78cc55a4bedd86202b3ee3c8aaf7215bc6a705ecb49d0  outputs/live_perception_20260904_01_retry1/common/sam3_response.json
80093373231987080f02dc990867f4a04505ad1fbd67e2d735cd4c5e68aee966  outputs/live_perception_20260904_01_retry1/common/lingbot_response.json
9890f866f9f38bb503641fa2a2ed6ad5227380f5c6dd1b5b040ed31a21a0b8b4  outputs/live_perception_20260904_01_retry1/raw/roi_mask_final.png
e72f725c7be046253776cfd0dbf1e214b7c4be326543b00b5383027e17d0804a  outputs/live_perception_20260904_01_retry1/lingbot/roi_mask_final.png
696df977a7cd167474364e1873e743941fca05b50056d80af9031eb6dde226e0  outputs/live_perception_20260904_01_retry1/raw_vs_lingbot.json
9e5c154341ba3e967b61267948aaaf8d7fbcd4c74a6c6b92917daad792cc1d35  cases/right_wrist_20260904_01_raw/manifest.json
da9975f25c6b84b44fe2b2448f08d57d80c9e1e0ea0ce3c904d6328684aa4d49  cases/right_wrist_20260904_01_lingbot/manifest.json
```

## Conclusion and next gate

The requested live RGB-D, live SAM3 masks, switchable raw/LingBot processing,
final binary ROI masks, immutable cases, and offline replay are implemented and
verified.  LingBot materially changes this capture's fitted geometry.  FDP must
remain blocked until the operator confirms the intended crate and a target
identity/uniqueness rule replaces the current "first ROI after sorting" policy.