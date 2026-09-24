# `_03` 右腕在线 Docker 计算测试记录

日期：2026-09-12。范围：FDP 观测位右腕单次在线采集、宿主机 V5 对照、
`s1-box-pose-compute:v5_2_v5_3b_20260911_03` 容器计算和资源采样。
本记录不含机械臂、夹爪、升降或底盘运动。

## 授权与执行边界

用户明确授权本次右腕 RGB-D/状态数据按既定路径发送并保存，用于在线测试。
数据由 S1 `galbot-echo` 采集，SAM3/LingBot 服务地址为 `10.34.216.11:7861`
和 `10.34.216.11:7865`；运行目录为：

```text
/home/galbot/Lsy03/box_pose_pipeline/runs/online_docker_20260912_right_03
```

现场未改变机器人姿态。采集入口只读取右腕相机、TF 和状态，旧宿主机 V5
只计算位姿；容器使用断网、非 root、只读根和只读 bundle。清场时流水线进程为
0、控制锁占用为 0，旧 `current` 仍指向
`releases/v5_2_v5_3b_live_20260910_01`。

## 过程

前两次尝试保留在远端运行目录：

- `online_docker_20260912_right_01`：采集完成，但非交互 SSH 未注入
  `S1_PERCEPTION_API_KEY`，SAM3 返回 HTTP 401。
- `online_docker_20260912_right_02`：加载了既有安全文件，但文件定义的是
  `AI_SERVICE_API_KEY`，入口变量仍为空，SAM3 返回 HTTP 401。

未重新采集的最终尝试 `right_03` 在当前进程内将已授权安全文件中的变量映射为
入口所需名称；密钥未写入文件、命令参数、镜像或输出。

1. 右腕新鲜采集 RGB、原始深度、K、同期 TF。
2. SAM3/LingBot 成功，生成 9 个候选。
3. 用户确认 `roi_index=0`，说明“最高最近的料箱”；确认清单绑定本帧最终 mask。
4. 宿主机旧环境 V5 计算接受。
5. 从同一确认结果导出哈希校验 bundle，交给 `_03` 断网容器计算。
6. 使用同一 bundle 进行第二次容器运行，采集内存/CPU周期样本。
7. 使用同一 bundle 调用 FDP `/first_frame_track`，保存原始响应并归一化到 `base_link`。

## 结果

固定镜像：`s1-box-pose-compute:v5_2_v5_3b_20260911_03`；实际 Image ID：

```text
sha256:651bcf7087b9ba1ee2702a4b58ef488936c45251e2a661db8b41d547042bae89
```

| 项目 | 宿主机旧 V5 | `_03` 容器 V5 |
|---|---:|---:|
| 状态 | `accepted` | `accepted` |
| 中心 base_link（m） | `[0.9272119309, -0.0255310572, 0.5314192737]` | `[0.9272119309, -0.0255310572, 0.5314192737]` |
| 中心最大轴差 | 基准 | `0 m` |
| 中心欧氏差 | 基准 | `0 m` |
| 4×4 矩阵最大元素差 | 基准 | `0` |
| V5 后端计算时间 | `17.5951 s` | `34.3402 s` |

同一冻结 Observation 的后端计算时间差为 `16.7450 s`，容器时间约为宿主机的
`1.9517×`，即在这一次配对运行中慢约 `95.17%`。该比较只覆盖 V5 后端计时；
容器镜像启动、挂载和输出写入没有单独取得外部墙钟时间，不能把这个数字解释
为完整端到端 Docker 延迟，也不能归因于纯 Docker 开销。宿主机与容器使用
同一 Orin，但运行时负载和进程边界不完全相同。

现场流程计时（宿主机入口）：采集 `6.1931 s`，SAM3/LingBot/ROI
`6.5160 s`，人工确认等待 `1678.9808 s`，Observation 生成 `0.0156 s`，
宿主机 V5 `17.5951 s`，总计 `1709.3104 s`。人工等待单独列出，不能视作算法
耗时。

容器资源采样运行：算法时间 `32.3750 s`；周期采样 13 次，内存峰值约
`290.9 MiB / 8 GiB`，CPU 峰值约 `615.52%`（6 CPU 限额），退出码 `0`，
`oom_killed=false`。这些是周期采样值，不是 cgroup 历史峰值证明。

容器输出合同记录 `network_services_called=false`、`robot_accessed=false`、
`robot_sdk_called=false`、`motion_commands_sent=false`；`accuracy_validated`
和 `grasp_ready` 均保持 `false`。V5 输出为 xyz/yaw，roll/pitch 仍使用直立先验。

## 同帧 FDP 对照

FDP 返回 HTTP 200，服务客户端耗时 `1.2299 s`（服务响应内部报告 `0.502 s`）。
将 FDP 原始 mesh 位姿按既有右腕几何变换归一化为同一 `base_link`/4317 语义后：

| 项目 | 宿主机 V5 | `_03` 容器 V5 | FDP |
|---|---:|---:|---:|
| 中心 X/Y/Z（m） | `0.927212 / -0.025531 / 0.531419` | 同宿主机 | `0.933132 / -0.024928 / 0.544688` |
| yaw（°） | `87.5991` | `87.5991` | `86.3618` |
| 后端/服务耗时（s） | `17.5951` | `34.3402` | `1.2299` |

中心差：宿主机 V5–容器为 `0 mm`；宿主机 V5–FDP 和容器 V5–FDP 均为
`14.5418 mm`。按同一 V5 模型顶面中心 `[0,0,height/2]` 定义箱口中心，
两套 V5 与 FDP 的箱口中心差均为 `14.7219 mm`。180° 对称 yaw 差均为
`1.2373°`。FDP 与 V5 的耗时边界和实现不同，不能据此作硬件速度排名。

这个 FDP 对照只说明同一输入下两个后端的输出差异；FDP 不是独立真值，差值
不能直接称为 V5 的绝对误差。FDP 结果的完整请求、响应、归一化矩阵、可视化
和比较 JSON 保存在本地归档的 `fdp_compare_01/`。

## V5 容器慢速诊断

同一镜像、同一 bundle 的无网络 A/B 运行显示，基线容器（`--cpus 6`、未设置
BLAS/OpenMP 线程变量）算法时间为 `34.3402 s`。只在容器进程环境中加入
`OPENBLAS_NUM_THREADS=1`、`OMP_NUM_THREADS=1`、`MKL_NUM_THREADS=1`、
`NUMEXPR_NUM_THREADS=1`，仍保持 6 CPU 限额，时间降为 `15.5938 s`，下降
`54.59%`，比宿主机本次 `17.5951 s` 还快约 `11.37%`。相反，保持默认线程、
把 CPU 限额放宽到 12，时间为 `43.2306 s`，未得到加速。

宿主机本次入口显式设置了 `OPENBLAS_NUM_THREADS=1`，容器启动脚本没有设置；
宿主机 CPU cgroup quota 为无限制，容器 `--cpus 6` 对应 `600000/100000`。
因此本次慢速的首要证据是容器默认线程/BLAS 调度造成的竞争或超配额，CPU
限额是次要约束；容器 NumPy `1.23.5`/SciPy `1.10.0` 的 OpenBLAS ILP64
构建与宿主机 NumPy `1.24.4`/SciPy `1.10.1` 的 `blas/cblas` 构建差异，
可能解释单线程下剩余差异。V5 源码本身使用 NumPy、SciPy `cKDTree` 和
`least_squares`，当前没有 GPU 后端；CUDA smoke test 只证明驱动可访问，
没有执行 V5 GPU 计算。因此“没有启动 GPU”不能解释这次宿主机与容器的
差距，只能说明两者都没有享受 GPU 加速。

本诊断只运行计算容器，不访问相机、服务、SDK 或控制接口；两组结果均
`accepted` 且中心不变。A/B 输出和计算值见
[`v5_runtime_diagnosis.json`](../experiments/20260910_orin_pose_pipeline/outputs/online_docker_20260912_right_03/v5_runtime_diagnosis.json)。
尚未修改 `_03` 镜像或启动脚本；是否将单线程环境固化到后续发布，需要先在
左右腕和多次新采集上复验，并单独评估 CPU 资源策略。GPU 优化仍按计划留到
下一轮。

## 产物

本地归档位于
[`online_docker_20260912_right_03`](../experiments/20260910_orin_pose_pipeline/outputs/online_docker_20260912_right_03/)，
包含原始采集/感知/确认文件、哈希校验 bundle、宿主机结果、容器结果、FDP
请求/响应、资源采样和 [`online_test_comparison.json`](../experiments/20260910_orin_pose_pipeline/outputs/online_docker_20260912_right_03/online_test_comparison.json)。
三方数值见 [`fdp_compare_01/comparison.json`](../experiments/20260910_orin_pose_pipeline/outputs/online_docker_20260912_right_03/fdp_compare_01/comparison.json)，
FDP 可视化见 [`foundationpose_vis.png`](../experiments/20260910_orin_pose_pipeline/outputs/online_docker_20260912_right_03/fdp_compare_01/foundationpose_vis.png)。

## 阶段结论

右腕单次“现场采集 → 感知 → 人工确认 → `_03` 计算”工程链路通过；同帧
宿主机与容器迁移一致性通过，并已完成该帧的 FDP 三方对照。当前只完成右腕 1 次新采集，不能代表左右腕
重复性、绝对定位精度、倾斜箱体适用性或抓取安全性。左腕和每侧 5 次独立
新采集仍待用户另行授权后执行。GPU 优化不在本轮范围，继续使用 `_03` CPU
基线；后续 GPU 方案应新建镜像并重新做同输入回归。