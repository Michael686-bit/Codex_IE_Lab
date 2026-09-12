# 知识导航入口（KNOWLEDGE INDEX）

> 本文件只负责导航：告诉 Agent 某类知识应该去哪里读取。
> 不要在本文件堆砌内容；详情请进入对应文档。

## 核心上下文（每个 Session 必读 / 自动加载）

| 内容 | 位置 |
|---|---|
| 当前项目状态（现在做到哪） | `CURRENT_STATE.md` |
| 项目背景（长期稳定） | `PROJECT_CONTEXT.md` |
| 学习路线 | `LEARNING_ROADMAP.md` |

## 稳定知识

| 内容 | 位置 |
|---|---|
| 系统架构认知（当前版本） | `ARCHITECTURE.md` |
| 硬件与软件环境 | `HARDWARE_SOFTWARE.md` |
| 重要技术决策 | `DECISIONS.md` |
| 术语表 | `GLOSSARY.md` |

## 过程记录

| 内容 | 位置 |
|---|---|
| 历史 Debug / 排错经验 | `DEBUG_HISTORY.md` |
| 知识结构变化记录 | `CHANGELOG.md` |
| 阶段性 handoff / session 总结 | `sessions/` |
| 实验记录 | `experiments/` |

## 代码（按模块）

| 内容 | 位置 |
|---|---|
| Galbot SDK 学习 / 验证代码 | `sdk_examples/` |
| IMC（FK/IK/trajectory/planning） | `imc_learning/` |
| 双臂 / IRMV_DUAL_ARM | `dual_arm/` |
| 感知（RGBD/SAM3/PointCloud/FoundationPose） | `perception/` |
| 导航 / SLAM / 底盘 | `navigation/` |
| ROS / ROS2 最小实验 | `ros_examples/` |
| 临时实验 | `experiments/` |
| 辅助脚本 | `scripts/` |
| 参考原始代码（只读） | `third_party/` |
| 废弃但有价值 | `archive/` |

## 读取规则

- 按需加载，不要默认读取整个 `docs/` 或 `third_party/`
- 大代码库定向检索：关键词 → 模块 → 调用链
- 信息可信度标注见 `AGENTS.md`