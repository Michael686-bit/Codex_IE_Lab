# S1 IE Lab Project

This repository is the local, versionable knowledge and engineering workspace for the Galbot S1 project. It connects code work in Codex with the historical context held in the ChatGPT project **“银河通用s1 项目 代码”**.

Start with [docs/knowledge_base.md](docs/knowledge_base.md). Historical OpenCode work from the SDK learning workspace is summarized in [docs/opencode_session_knowledge.md](docs/opencode_session_knowledge.md). Durable conclusions from future discussions and experiments should be written back into repository documentation so that a new agent session can recover context without relying on chat memory.

Current high-level learning order:

1. Galbot SDK and minimal state/control examples
2. IMC and IRMV_DUAL_ARM planning/execution
3. RGB-D perception, segmentation, depth, point clouds, and 6D pose
4. Localization, SLAM, navigation, and base control
5. Integrated perception-planning-control execution

All real-robot operations follow the safety rules in `AGENTS.md`.

## Canonical navigation visualization

The canonical RViz implementation for ongoing S1 navigation/ESDF diagnosis is
`experiments/20260822_s1_rviz_demo/ros2_ws/src/s1_rviz_demo`. It contains the
robot-only viewer, the preserved 2026-08-27 failure replay, and the offline
publisher for captured vendor `EsdfGrid` frames.

The separate
`/home/lsy03/Lsy03_document/galbot_s1_SDK_learning/navigation/ros2_ws/src/s1_room0804_rviz`
package remains a read-only historical/static-map reference. Do not add new
diagnostic features there; new RViz work belongs in the canonical package
above so the two implementations do not diverge.

Generated ROS `build/`, `install/`, and `log/` trees, Python caches, large map
point clouds, raw ESDF files, and captured binary frames are intentionally not
versioned. Their adjacent README and `ASSET_MANIFEST.sha256` files preserve
source, size, checksum, evidence boundary, and local reconstruction steps.