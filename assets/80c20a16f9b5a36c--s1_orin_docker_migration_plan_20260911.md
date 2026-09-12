# S1 Orin 感知计算 Docker 迁移计划

日期：2026-09-11。状态：P1/P2 已执行，P4/P5 待执行；本文同时记录实施结果。

后续更新：同日用户授权接通 GPU Docker，已确认现有 runtime 可用并完成非 root
容器 CUDA 核函数验证，见[实测记录](../experiments/20260911_orin_gpu_container/README.md)。
GPU 接入已完成；本文的文件拆分、首个计算镜像和一例 Orin 离线回归也已完成，
实时 Docker 全链路、重复性和算法 GPU 加速仍待实施。

## 目标与完成定义

后续 Orin 新增算法实验默认使用 Docker 隔离依赖。首期完成：

```text
宿主机现有 SDK 单侧腕部采集
  → 冻结 RGB / raw depth / K / 同帧 TF / 时间戳 / 哈希
  → Docker：SAM3/LingBot 远端调用 → ROI → 人工确认 → V5
  → 宿主机独立结果目录：base_link 箱体几何中心、姿态、诊断及回放记录
```

SAM3/LingBot 模型仍在现有远端服务运行，容器只运行客户端。
人工确认发生在候选生成之后，绑定本次 mask 与清单哈希。
保留既有宿主机流水线作为回退；验收前不切换现有 current。
首期不迁移原厂服务、驱动、SDK 采集环境或运动控制，不升级 JetPack/CUDA，
不同时更换 V5 算法、参数、模型或放宽接受门限。

完成意味着：同输入回放一致、实时单次流程可用、隔离配置经验证、失败可诊断、
旧入口可回退。容器迁移不构成定位精度、倾斜适用性或抓取安全性验证。

## 当前依据与待验证信息

- 9 月 10 日部署记录并于本轮只读复核：AGX Orin 64 GB、aarch64、Ubuntu 20.04.6、
  JetPack 5.1.4 / L4T 35.6.0；本轮确认 `galbot-echo`、aarch64 和 L4T R35.6.0。
- 既有算法环境：Python 3.8.20、NumPy 1.24.4、SciPy 1.10.1、
  OpenCV 4.10.0、Requests 2.32.3。先尝试复现这些依赖；ARM64 wheel
  可获得性、传递依赖与实际构建结果待验证，不为构建便利升级宿主机。
- 现有 live.py 已分出采集、服务、ROI、确认适配器，但当前实时入口仍串联
  SDK 采集；需新增纯文件输入的计算入口，不能直接把整条入口搬进容器。
- Docker/runtime 已在 Orin 只读核对：Docker 26.1.3、NVIDIA runtime 3.9.0-1、
  toolkit 1.11.0~rc.1-1，默认 runtime 仍为 runc；GPU Driver API smoke test
  已通过。首个计算镜像复用已有 ARM64 基础镜像；容器依赖为 Python 3.8.10、
  NumPy 1.23.5、SciPy 1.10.0、OpenCV 4.12.0，V5 本身仍为 CPU 路径。

## 实施步骤与阶段验收

| 阶段 | 工作 | 交付及通过条件 |
|---|---|---|
| 1 环境与回退基线 | 获得当次机器人访问授权后，只读核对 Docker、runtime、系统版本、磁盘、现有服务和发布指针；保存代码/配置/依赖清单及哈希，不导出凭据 | 环境报告、明确旧入口和版本、缺项清单；若需安装或调整 Docker，另列宿主机变更清单，不能当作容器内部操作 |
| 2 拆分文件边界 | 复用已有 SDK getter 采集；新增从冻结 capture 目录开始的计算 CLI；沿用 Observation/Result 合同 | 采集无需新增算法依赖；计算可在无 SDK 环境导入运行；不完整、哈希错误、左右腕不匹配输入被拒绝 |
| 3 构建隔离运行包 | 编写 Dockerfile、依赖锁定清单、构建与运行脚本；代码和依赖固定进镜像，模型和数据按固定版本提供 | ARM64 镜像可启动；记录镜像 ID/digest、源码/模型/配置哈希；无凭据进入构建上下文、层或日志 |
| 4 冻结数据回归 | 在 Orin 上比较旧环境与容器，使用完全相同的已确认 Observation，关闭网络回放 V5 | 接受/拒绝和原因一致；中心、矩阵、诊断候选在预设数值容差内一致；同时记录耗时和内存 |
| 5 单次实时闭环 | 宿主机先采集并封存，容器调用服务、产出候选，用户确认本次目标后计算并存档 | 左右腕分别完成一次链路验证；结果可合法接受或拒绝，工程成功与定位接受分开记录；无运动命令，失败不复用旧结果 |
| 6 运行验证与回退演练 | 固定现场条件建议每侧独立触发 5 次；检查资源、日志、失败状态；停止容器后用旧入口回放同一冻结数据 | 报告成功/拒绝/异常次数、分阶段耗时、资源峰值；回退后旧入口正常；通过后新实验默认走容器入口 |

阶段 4 建议预设迁移数值容差为中心欧氏差 ≤ 1e-6 m、4×4 矩阵元素最大差
≤ 1e-6（仅作软件回归容差，不是实物精度指标）。若超差，定位浮点、依赖或
输入变化原因后复审，不事后直接放宽门限。历史 accepted 与 rejected 案例均覆盖；
异常输入和服务超时/认证失败使用离线 fixture 或 mock 验证，不刻意干扰服务。
再次请求远端推理可能改变深度或 mask，不能用它作为严格同输入回归证据。

## 已执行记录（2026-09-11）

- **基线检查**：Orin 为 `galbot-echo`、aarch64、L4T R35.6.0；Docker 26.1.3
  和 NVIDIA runtime 已存在，默认 runtime 未改。旧发布指针仍为
  `/home/galbot/Lsy03/box_pose_pipeline/current -> releases/v5_2_v5_3b_live_20260910_01`；
  未改动 `fdp_baseline`、SDK、服务或任何运动接口。
- **文件边界**：新增 `pose_pipeline.bundle`、`export_observation_bundle.py`
  和 `compute_observation.py`。bundle 强制校验 RGB/depth/mask/K/TF 哈希、
  左右腕帧名、base_link、米制光学 Z 和 `motion_commands_sent=false`；
  容器计算入口不导入 SDK、不调用网络。
- **镜像**：在 Orin 离线构建
  `s1-box-pose-compute:v5_2_v5_3b_20260911_03`，使用既有
  `s1-sjtu-0806-slim:latest`（base image ID 已锁定）。首版构建缺少 baseline
  导入依赖，保留 `_01` 失败 release；补齐依赖的 `_02` 也保留作对照。最终
  当前源码和依赖锁定文件已在 `_03` 重新构建，镜像 ID 为
  `sha256:651bcf7087b9ba1ee2702a4b58ef488936c45251e2a661db8b41d547042bae89`，
  构建上下文、哈希和运行脚本位于
  `/home/galbot/Lsy03/box_pose_pipeline_docker/releases/v5_2_v5_3b_container_20260911_03/`。
- **Orin 回归**：右腕确认冻结 bundle 在 `_03` 容器中 `accepted`，中心为
  `[1.3863633760476675, 0.2493339463832932, 0.4943560250186494] m`，
  与 `_02` 同输入回放三个坐标轴最大差 `0`；容器输出记录
  `robot_accessed=false`、`network_services_called=false`。左腕归档 bundle
  在 `_03` 中 `rejected / ambiguous_inner_outer_surface_hypotheses`，与
  `_02` 状态和原因一致。右腕算法耗时约 `14.829 s`，左腕约 `50.557 s`。
- **资源与权限**：运行脚本使用 `--runtime nvidia`、非 root、断网、只读根、
  cap-drop ALL、no-new-privileges、只读输入和独立输出；未使用 privileged、
  host 网络、SDK、控制锁或 Docker socket。旧版本 `current` 未切换。

因此阶段 1、2、3 已完成；阶段 4 的状态/位姿回归已完成但峰值内存仍待测量。
阶段 5 实时 Docker 全链路尚未开始，阶段 6 已完成一次旧入口回退回放，但
重复运行和完整回退演练仍是后续工作。完整
命令、哈希、输出和边界见[执行记录](../experiments/20260911_orin_docker_deployment/EXECUTION_RECORD_20260911.md)。

## 文件交换与权限设计

拟新增独立部署根 `/home/galbot/Lsy03/box_pose_pipeline_docker/`，具体位置在
阶段 1 核对；目录包含部署文件、captures、runs 和版本清单。现有
`box_pose_pipeline` 与 `fdp_baseline` 保留。

- 宿主机采集先写临时目录，校验完成后在同一文件系统内原子改名发布；
  容器只接收完成的指定 run ID，不扫描并误用“最新”旧数据。
- 原始 capture、模型及固定配置只读挂载；仅本次输出目录可写。
  不挂载整个 home、系统环境、控制锁或 Docker socket。
- 非 root 运行并匹配结果目录 UID/GID；只读根文件系统，临时计算使用 tmpfs，
  丢弃不必要 capabilities、禁用提权；不使用 privileged 或设备直通。
- 离线回放无网络；在线计算先用 bridge 网络访问必要服务，不默认 host 网络。
  bridge 本身不等于目的地址白名单；如需强制限制目的地址，单列网络策略验证，
  不擅自修改机器人全局防火墙。
- 凭据运行时注入；优先受限只读 secret 文件并由入口加载，兼容现有客户端。
  不写入源码、镜像、提交、结果或命令参数。
- CPU、内存、PIDs、临时空间和日志轮转显式配置；初始限额根据阶段 1
  可用资源及阶段 4 峰值确定，验证不会挤压现有服务。镜像/结果占盘单独监测。
- SDK 锁只由宿主机采集使用；容器不初始化 SDK。控制访问不应仅依靠
  “没有安装 SDK”作安全保证，仍需审查网络与入口的实际能力。

## 输出合同与回退

每次输出保留 center_base_m、T_base_link_from_box、后端/自由度/先验、
accepted/rejected/error、拒绝原因、输入/模型/配置/镜像标识、服务响应、
人工确认及各阶段耗时。中心与矩阵平移一致；拒绝时正式位姿为空，诊断候选单列。
V5 仍为 x/y/z/yaw、roll/pitch 直立先验；accuracy_validated 与 grasp_ready
保持 false。

回退通过停止新容器并显式调用阶段 1 记录的旧版本入口完成。保留失败运行、
旧镜像及日志，不删除数据或改装宿主机依赖。演练用冻结数据验证旧入口可用，
无需运动。Docker 如涉及宿主机安装/网络变更，其回退另行记录，停止容器本身
不能撤销这些变更。

实时验证仅读取所选左/右腕相机及 TF/状态，不涉及机械臂、夹爪、升降或底盘
运动。由现场人员保持静止及工作区净空、确认急停可用；机器人访问需当前请求
授权，任何后续物理运动仍需逐步明确确认。本文不授权自动执行远端部署或采集。

## 参考

- [现有 Orin 部署与版本证据](s1_orin_box_pose_deployment_20260910.md)
- [实时接口与确认流程](s1_orin_live_perception_implementation_20260911.md)
- [既有可插拔流程计划](s1_orin_pluggable_pose_plan_20260910.md)
- [Docker 资源限制](https://docs.docker.com/engine/containers/resource_constraints/)
- [Docker 运行权限和挂载](https://docs.docker.com/engine/containers/run/)
- [NVIDIA Jetson 容器说明](https://nvidia.github.io/container-wiki/toolkit/jetson.html)