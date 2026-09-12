# S1 Orin 实时 RGB-D → SAM3/LingBot → V5 入口

日期：2026-09-11。状态：代码已实现并部署；首轮左右腕真实采集和远端推理已执行。

## 已实现组件

新版本位于 Orin：

```text
/home/galbot/Lsy03/box_pose_pipeline/current
 -> releases/v5_2_v5_3b_live_20260910_01
```

该发布包本地 SHA-256 为
`f0923cc01a251d19cd8f0201b2ddee45ba5bc792ebaa54c595b25d9e29e591f3`。

`app/pose_pipeline/live.py` 提供：

- `LiveWristCaptureSource`：调用现有
  `fdp_baseline.live_capture.capture_wrist_once()`，支持 left/right，使用
  `/home/galbot/ie_lab/control.lock` 非阻塞锁，并校验 RGB/depth/K/TF、帧名、
  哈希和只读安全字段；只允许 getter/lifecycle SDK 调用。
- `RemoteSAM3Adapter`：复用现有 SAM3 HTTP 客户端，保存原始响应，凭据只从
  环境变量传入，结果只记录 `credential_used`。
- `RemoteLingBotAdapter`：复用现有 LingBot-Depth HTTP 客户端，保存原始响应和
  米制深度数组。
- `ROIFrontendAdapter`：加载 Orin 已存在的
  `g1_workbin_perception`，生成所有 ROI 候选及最终 mask，不自动绑定目标。
- `ConsoleTargetConfirmer` / `confirm_live_target.py`：要求人工输入一个
  `4317/H4` 候选索引和非空说明；确认文件绑定感知清单及最终 mask 哈希。
- `LiveObservationSource`：组合采集、前处理和确认，生成统一 `Observation`。

一次性流程入口为 `app/scripts/run_pose_once.py`。后端仅在确认完成后调用，
不包含机械臂、夹爪、升降或底盘动作。

## Orin 使用命令

在机器人已经由现场人员遥控到观测位并保持静止后，入口为：

```bash
OPENBLAS_NUM_THREADS=1 /home/galbot/ie_lab/bin/s1-python \
  /home/galbot/Lsy03/box_pose_pipeline/current/app/scripts/run_pose_once.py \
  --pipeline-config /home/galbot/Lsy03/box_pose_pipeline/current/app/configs/live_v5_2_v5_3b.json \
  --run-dir /home/galbot/Lsy03/box_pose_pipeline/runs/live_$(date +%Y%m%d_%H%M%S) \
  --acknowledge-readonly-live-s1
```

流程会先采集，再调用 SAM3/LingBot，打印候选，等待输入 `roi_index` 和人工
说明，确认后才运行 `v5_2_v5_3b`。也可以把
`--selected-index N --operator-statement "..."` 作为命令行参数传入。
API key 使用配置中的 `S1_PERCEPTION_API_KEY` 环境变量名；不能把 key 写进
命令行、配置或输出目录。

每次运行目录保存 capture、SAM3/LingBot 响应、候选 mask、感知清单、目标确认、
Observation 清单、V5 结果、耗时及失败记录。已有目录拒绝覆盖。

## 已完成的非实时验证

- 本地 mock/接口测试：15 项通过。
- Orin 新版本 Python 编译和适配器导入：通过。
- Orin 随包冻结案例回放：`accepted`，说明新版本实时组件没有破坏 V5 回放。
- 旧版本 `v5_2_v5_3b_20260910_01` 保留，`current` 可通过版本指针回退。
- 首轮真实运行结果为左腕拒绝、右腕接受，详细数据见
  [首轮实时实验记录](s1_orin_live_experiment_20260911.md)。

以上结果没有证明目标绝对精度或抓取可用性；后续重复运行仍需记录相机侧别、
候选图、服务耗时、目标确认内容和 V5 拒绝/接受状态。
V5 当前仍是 `x/y/z/yaw`，roll/pitch 使用直立先验；倾斜箱体的结果只作为基线
诊断，不能直接进入抓取。

## 安全边界

本入口的设备读取是左/右腕 RGB-D 相机，预期动作是获取一帧图像和只读状态；
不移动机械臂、夹爪、升降或移动底盘。采集时仍需确认工作区无遮挡、控制锁可用、
现场急停可用；本入口不发送运动命令。