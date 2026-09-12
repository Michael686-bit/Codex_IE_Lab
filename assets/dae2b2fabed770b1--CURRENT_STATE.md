# 当前状态（CURRENT_STATE）

> 只记录"现在真正做到哪里"。未知内容写 NEEDS_CONFIRMATION，不要猜测。
> 本文件每次有实质进展时更新。

更新于：2026-08-15

## 完成情况

- [x] Workspace 目录结构初始化
- [x] 文件化知识库初始化（docs/ 核心文档）
- [x] AGENTS.md / opencode.json / .opencode/commands 初始化
- [x] Git 仓库初始化（git 2.34.1 已安装，首次提交 57fe774，身份 Michael686）
- [x] Galbot SDK 参考代码入库（third_party/GalbotSDK，取自交大工作目录 sdk_reference，含 pyi 存根 + 官方示例，来源说明见 SOURCE.md）
- [x] 第一个只读状态获取实验（sdk_examples/read_robot_state.py，语法检查通过，未实机运行）
- [x] 真机只读验证成功（SSH galbot@10.34.216.17 运行 read_robot_state.py，VERIFIED）
- [x] head 关节微动验证成功（sdk_examples/test_head_micro_move.py，+0.05 rad 前移并回原位，最终误差 0.0025 rad，VERIFIED）
- [x] 单臂小幅运动验证成功（sdk_examples/test_left_arm_micro_move.py，left_arm_joint1 +0.1 rad 回原位，误差 0.00017 rad，VERIFIED）
- [x] head 明显摆动验证成功（sdk_examples/test_head_visible_move.py，±0.4 rad≈23° 前后摆动回位，误差 0.00005 rad，VERIFIED）

## 当前具备条件

| 项目 | 状态 |
|---|---|
| Galbot SDK 代码 / 示例 | ✅ `third_party/GalbotSDK`（pyi 存根 + 官方示例，仅参考；运行时库 `.so` 缺失 `NEEDS_CONFIRMATION`） |
| IMC 代码 | 本地存在：`~/GalbotS1文件/260611_sjtu_workbin_movement/`（imc.zip / imc-master-*.zip），未入库 |
| IRMV_DUAL_ARM 代码 | 本地存在：`~/GalbotS1文件/260611_sjtu_workbin_movement/`（IRMV_DUAL_ARM-galbot-develop-real-*.zip），未入库 |
| 真机访问 | ✅ SSH `galbot@10.34.216.17`（VERIFIED，SDK 1.9.0 可导入，只读验证成功） |
| ROS 环境 | `NEEDS_CONFIRMATION` |
| 本地开发机环境（CPU/GPU/OS） | Ubuntu 22.04，`NEEDS_CONFIRMATION`（CPU/GPU 待确认） |
| 感知依赖（SAM3 / FoundationPose 等） | 无，`NEEDS_CONFIRMATION` |

## 当前学习阶段

Stage 0：系统总览（未开始）

## 下一步任务

1. 单臂小幅运动已通过 ✅，下一步：完整机械臂运动 / 多关节轨迹（可基于官方 tutorials）
2. 梳理 SDK API 结构（GalbotRobot / GalbotMotion / GalbotNavigation / GalbotPerception）写入 ARCHITECTURE 或学习笔记
3. 入库 IMC / IRMV_DUAL_ARM（本地已有 zip）

## 未解决疑问

- Galbot S1 SDK 的官方获取渠道与文档位置
- IMC 与 Galbot SDK 的关系（`NEEDS_CONFIRMATION`）
- IRMV_DUAL_ARM 是否为交大二次开发框架（`NEEDS_CONFIRMATION`）