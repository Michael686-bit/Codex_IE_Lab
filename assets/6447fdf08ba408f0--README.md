# Orin 箱体位姿实时实验归档

归档日期：2026-09-11。来源：S1 Orin `galbot-echo` 的
`/home/galbot/Lsy03/box_pose_pipeline/runs/`，以及本地由这些运行产物生成的
同帧 FDP/V5 对照文件。

## 归档内容

`remote_runs/` 是从 S1 只读复制的完整运行目录，包含 RGB、原始深度、K、同期
TF、SAM3/LingBot 响应、候选 mask、人工确认、V5 原生结果、耗时和失败记录。
共保存以下 9 个目录：

- `replay_v5_2_v5_3b_20260910_01`：冻结案例 Orin V5 回放，accepted。
- `replay_v5_2_v5_3b_live_20260910_02`：冻结案例实时发布版回放，accepted。
- `live_left_20260911_01`：首轮左腕，V5 rejected。
- `live_right_20260911_01`：首轮右腕，V5 accepted。
- `live_left_20260911_02`：RGB/depth 时间差超过 50 ms，采集拒绝。
- `live_left_20260911_03`：采集成功但 SAM3 HTTP 401，密钥未注入。
- `live_left_20260911_04`：第二观测位左腕，ROI 2，V5 rejected；同帧 FDP 已完成。
- `bilateral_20260911_01_left`：双腕实验左腕 ROI 3，V5 rejected；同帧 FDP 已完成。
- `bilateral_20260911_01_right`：双腕实验右腕 ROI 8，V5 accepted；同帧 FDP 已完成。

本地派生结果仍保留在同级项目目录：

- `../../outputs/live_left_20260911_04/`：第二观测位 V5/FDP 输入、矩阵、投影和 TCP 对照。
- `../../outputs/bilateral_20260911_01/`：左右腕完整派生结果、FDP 请求/响应、投影图、
  `summary.json`、V5/FDP TCP 对照和复现脚本。
- `../../reports/live_right_20260911_01_{v5,fdp}_mode00_targets.json`：首轮右腕
  V5/FDP 的 mode-00 TCP 几何报告。
- `../../reports/live_right_20260911_01_*_mode00_targets.svg`：首轮 TCP 可视化。

## 数据完整性和边界

`SHA256SUMS` 覆盖 `remote_runs/` 中的全部文件；重新计算后应无差异。运行目录
中的 `live_run_manifest.json` 和 `capture_result.json` 记录了采集哈希及
`motion_commands_sent=false`。本归档不包含任何 API key；运行清单只记录
`credential_used`。FDP 请求归档含图像/深度/mask 编码数据，但不含服务密钥。

首轮右腕的 FDP 对照曾写入本地报告和文档，旧远端运行目录本身没有
`fdp_compare_01/` 子目录；本归档通过本地报告和后续双腕对照保留其分析结果，
不把缺失的远端子目录伪装成已保存。

后续离线分析应优先读取 `remote_runs/` 的原始输入和本地派生的 `comparison.json`。
FDP 不是独立真值；V5 rejected 运行的中心只能作为诊断候选。所有运行均没有发送
机器人运动命令。交接前不要删除 S1 上的 `runs/`；确认本机归档可读后再按现场
存储策略处理空间。