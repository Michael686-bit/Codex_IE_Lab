# 第二观测位左腕 V5/FDP 同帧对照

2026-09-11，运行 `live_left_20260911_04`。用户已授权腕部采集、内网推理及指定安全文件的服务密钥使用，并在聊天中明确提交目标 `2`。未发送运动命令。

## 结果

| 项目 | V5-2＋V5-3b 诊断候选 | FDP |
|---|---:|---:|
| 中心 X（base_link，m） | 0.9823092834 | 0.9846614701 |
| 中心 Y（m） | -0.0392901978 | -0.0397602165 |
| 中心 Z（m） | 0.5165563016 | 0.5194484276 |
| yaw（度） | 88.9462053 | 87.5654609 |
| 后端耗时（s） | 23.4121 | 0.9364 |

中心距离 3.7574 mm，180° 对称 yaw 差 1.3807°，使用相同模型高度推导的箱口中心距离 3.3092 mm。计时是 Orin 本地 V5 与外部 FDP HTTP 请求，各自边界和硬件不同。

V5 正式状态是 **rejected**，原因是 `mask_touches_image_border` 和
`ambiguous_inner_outer_surface_hypotheses`；正式中心和矩阵均为 null。
表内数值只来自 `candidate_diagnostic`，不能当作已接受位姿或抓取目标。
FDP 返回 HTTP 200 和合法矩阵，并不证明绝对精度。投影落在选定上层右侧箱体，
两后端投影接近；目标 mask 触及图像边界，截边问题未消失。

未进行五次静止重复性测试：首帧已暴露截边，当前应先取得完整入镜的视角，
再确认目标并统计重复性。实物倾斜情况未知；V5 仍采用直立先验。

## 输入与复现

严格复用同一 RGB、已保存 LingBot 深度、最终 ROI 2 mask、K、同期 TF。
请求前校验采集文件哈希、感知清单哈希、确认 mask 哈希及 LingBot 深度哈希。
FDP 网络编码将米制浮点深度转换为 uint16 毫米 PNG，因此存在毫米量化。
服务端 mesh 路径沿用 `/opt/s1-sjtu/assets/mesh/EU4322_midcut_target175mm.obj`。

远端产物：`/home/galbot/Lsy03/box_pose_pipeline/runs/live_left_20260911_04/fdp_compare_01`。
本地完整镜像位于 `experiments/20260910_orin_pose_pipeline/outputs/live_left_20260911_04/`；
包括原图、原始/补全深度、mask、确认记录、V5 结果、FDP 请求/响应、归一化矩阵、
`comparison.json` 和 `same_frame_projection.jpg`。执行脚本保存为 `executed_comparison.py`。

实时发布包缺少 `fdp_baseline/client.py`。本次复用旧基线目录的客户端（哈希与
本地一致），但使用新发布包支持左腕的 geometry/io_utils；未修改旧基线代码。

## 前序失败与证据边界

- `_02`：RGB/深度时间差超过 50 ms，采集拒绝。
- `_03`：采集成功，但 `credential_used=false`，SAM3 HTTP 401。
- `_04`：显式授权安全文件后加载认证，SAM3/LingBot 成功，V5 拒绝如上。
- 初次 FDP 对照因发布包缺客户端而未发送；本次已完成请求。

上次成功的具体密钥注入来源仍未核实；不能把本次可用的安全文件称为上次来源。
当前代码确认文件中的中文说明由助手在用户聊天确认前填入，用户随后明确提交 `2`；
因此该文件的时间戳不能被解读为用户最初提交时间。本次 FDP 在用户确认后执行。
后续必须展示候选图并等待用户确认再提交，助手视觉判断不能代替人工确认。