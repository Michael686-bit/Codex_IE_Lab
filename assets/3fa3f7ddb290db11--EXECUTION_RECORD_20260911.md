# Orin Docker 感知计算迁移执行记录

日期：2026-09-11 至 2026-09-12。范围：阶段 1～4 的无运动部分。所有远端操作均使用用户当前
授权的短时 SSH；本记录不含凭据。

## 最终镜像

- 镜像：`s1-box-pose-compute:v5_2_v5_3b_20260911_03`
- Image ID：`sha256:651bcf7087b9ba1ee2702a4b58ef488936c45251e2a661db8b41d547042bae89`
- 架构：`arm64`
- 基础镜像：`s1-sjtu-0806-slim:latest`
- 基础镜像 ID：`sha256:6359272ddc5c520c60dd61a2293672d826e5312046c3986170bbdd0849c71697`
- 镜像大小：约 5.41 GB（包含基础镜像和本次复制的计算源码/模型）
- Dockerfile 入口：`/usr/bin/python3 /opt/box-pose/app/compute_observation.py`
- 构建：Orin 本地 Docker daemon，`--network=none --pull=false`；没有 apt/pip
  安装。依赖清单见 `runtime_versions.txt`，运行时 Python 3.8.10、NumPy
  1.23.5、SciPy 1.10.0、OpenCV 4.12.0。

## GPU 验证

在上述最终镜像内，使用 NVIDIA runtime、断网、只读根文件系统、非 root、
cap-drop ALL、no-new-privileges 运行 CUDA Driver API smoke test：

```json
{"status":"passed","device":"Orin","device_count":1,"cuda_driver_api_version":11040,"kernel_output":42,"expected":42,"robot_sdk_called":false}
```

这证明容器能访问 GPU 驱动并执行 CUDA 核函数；V5 当前仍使用 CPU NumPy/SciPy
计算，不应把该结果解释为 V5 已经 GPU 加速。

## 同输入回归

两个 bundle 均由宿主机文件导出后只读挂载；容器不导入 SDK、不调用网络。

| 输入 | `_03` 状态 | 拒绝原因 | 算法耗时 |
|---|---|---|---:|
| `s1_observation_bundle_right_01` | `accepted` | 无 | 14.829 s |
| `s1_observation_bundle_left_01` | `rejected` | `ambiguous_inner_outer_surface_hypotheses` | 50.557 s |

右腕中心：

```text
[1.3863633760476675, 0.2493339463832932, 0.4943560250186494] m
```

与 `_02` 同输入比较，右腕三个坐标轴最大差为 `0`、欧氏差为 `0`；左右腕
状态和拒绝原因也完全一致。输入校验、输出位姿/矩阵一致性由容器入口执行。
右腕统计回归记录了 Docker 的 8 GiB 内存上限和 CPU/PID 限额；采样峰值约
`271.9 MiB / 8 GiB`（3.32%，`docker stats` 采样），容器状态
`exit_code=0, oom_killed=false`。左腕采样峰值约 `286.5 MiB / 8 GiB`
（3.50%），状态 `exit_code=3, oom_killed=false`，符合预期 rejected 路径。
这些是周期采样值，不是 GPU 显存上限或 cgroup 历史峰值证明。

## 回退检查

停止容器后，使用未切换的旧 `current` 入口对同一冻结右腕案例回放：

```text
/home/galbot/Lsy03/box_pose_pipeline/runs/rollback_check_20260911_01
status=accepted
center=[1.3863633760476675, 0.2493339463832932, 0.4943560250186494] m
```

与 `_03` 容器结果的三个坐标轴最大差和欧氏差均为 `0`。这证明单次旧入口
回退回放可用；每侧 5 次冻结重复已另行完成，实时链路仍未开始。

## 重复运行

在相同 bundle、镜像和资源限制下，每侧独立运行 5 次：

- 右腕：`5/5 accepted`，五次中心完全相同；算法耗时
  `14.686–14.928 s`，均值 `14.783 s`。
- 左腕：`5/5 rejected`，五次均为
  `ambiguous_inner_outer_surface_hypotheses`；算法耗时
  `40.379–52.611 s`，均值 `43.247 s`。

这些是冻结输入的计算重复性，不能替代实时采集重复性、绝对精度或抓取验证。

## 远端路径和安全边界

最终 release：

```text
/home/galbot/Lsy03/box_pose_pipeline_docker/releases/v5_2_v5_3b_container_20260911_03/
```

其中保存构建上下文、逐文件 SHA-256、两个冻结 bundle、两个有效回归目录和
先前一次中断的左腕目录（保留，不作为结果）。旧流水线指针仍为：

```text
/home/galbot/Lsy03/box_pose_pipeline/current
 -> releases/v5_2_v5_3b_live_20260910_01
```

本次容器均使用 `--runtime nvidia`、非 root、断网、只读根、只读输入、独立输出、
cap-drop ALL、no-new-privileges、8 GiB 内存、6 CPU、256 PIDs；没有使用
`--privileged`、host 网络、宿主机 home、SDK、控制锁或 Docker socket。
没有发送机械臂、夹爪、升降或底盘命令。最终检查时发现一个不同镜像的
`s1-destack-controller` 容器正在运行；本任务没有启动、停止或修改它。

## 阶段结论

- 阶段 1：完成。
- 阶段 2：完成；bundle 导出/加载和纯文件计算入口已加入本地代码，17 项测试通过。
- 阶段 3：完成首个可用 `_03` 镜像及 GPU 接入验证；后续增加 PyTorch/CuPy
  仍需新镜像和兼容性测试。
- 阶段 4：状态、位姿和拒绝路径回归完成；左右腕均有资源采样且未发生 OOM。
- 阶段 5：已完成 2026-09-12 右腕一次实时采集、感知、人工确认和 `_03`
  容器计算；左腕、重复采集和完整服务级回退仍待执行。
- 阶段 6：每侧 5 次冻结重复和一次旧入口回退回放已完成；实时服务级回退
  和现场运行演练仍待执行。

## 2026-09-12 右腕在线 Docker 单次

在用户明确授权右腕 RGB-D/状态数据发送和保存后，机器人保持 FDP 观测位，
执行 `online_docker_20260912_right_03`：宿主机采集 → SAM3/LingBot → 用户
确认 `roi_index=0`（“最高最近的料箱”）→ 宿主机 V5 → 冻结 bundle → `_03`
断网容器。前两次 401 失败（入口变量未注入）保留在 `right_01`、`right_02`。

宿主机和 `_03` 均为 `accepted`，base_link 中心均为
`[0.9272119309,-0.0255310572,0.5314192737] m`；中心和 4×4 矩阵最大差均为
`0`。同输入 V5 后端时间分别为 `17.5951 s` 和 `34.3402 s`，容器本次约慢
`95.17%`。资源采样运行算法时间 `32.3750 s`，周期内存峰值约
`290.9 MiB / 8 GiB`，CPU 峰值约 `615.52%`，退出码 0、未 OOM。

容器记录断网、无 SDK/机器人访问、无运动命令；旧 `current` 未切换。该结果
只完成右腕一次新采集，不能代表实时重复性、绝对精度或抓取可用性。完整
逐项记录见 `docs/s1_orin_docker_online_test_20260912.md`。