# Galbot S1 Project Knowledge Base

## V0–V5-5 版本谱系复核 — 2026-09-12

用户要求按 V0 FDP、V1 箱口、V2 整体箱壁、V3 多平面、V4 三阶段及 V5-0 至
V5-5 回顾。该回顾编号与代码 method 后缀不同。源码确认 V5-3 初值实际来自
V4 joint，完整 B/C/mesh 多来源初值在 V5-2 补齐；V5-3/3b 分别使用单向/双向
欧氏最近点拟合，V5-4 为显式 point-to-plane ICP；V5-5 使用独立观测初值和
6DoF 拟合，不能画成继承 V5-4 输出。详细关系、报告状态冲突及证据见
[版本谱系回顾](s1_pose_version_lineage_20260912.md)。本次仅本地核对，没有重跑实验。

Last synchronized from the ChatGPT project **“银河通用s1 项目 代码”**, the local OpenCode history for `galbot_s1_SDK_learning`, and preserved Codex side-chat context: 2026-09-08. Local experiment review and user scope/update: 2026-09-10.

## FDP 后端阶段范围确认 — 2026-09-09

用户在 ICP/其他算法替代 FDP 实验回顾中明确“暂时只先优化 FDP”。当前阶段
聚焦位姿后端替代与优化，保留 SAM3、LingBot 和人工确认 mask；整链端侧化
另列后续阶段。V5-4 首轮 ICP A/B 已执行，但受约束 ICP 没有显示有意义的整体
收益，且 z 轴观测不足；9/11 仍仅为实验拟合门限通过，没有独立抓取精度验证。
汇总、已执行/未执行边界、分阶段计划与待补信息见
[9 月 9 日阶段总结](s1_fdp_replacement_review_20260909.md)。

## Orin 可插拔位姿流程范围确认 — 2026-09-10

2026-09-11 后续用户授权 GPU Docker 接入，实机确认已有 Docker 26.1.3 和
NVIDIA runtime 注册；无需安装或重启。以非 root、断网、只读容器通过 CUDA
Driver API 执行 PTX 核函数并验证输出 42，设备 Orin，driver API 11040。
复验入口已部署于 `/home/galbot/Lsy03/box_pose_pipeline_docker/gpu_check_20260911/`。
默认 runtime 仍 runc，旧流水线保留；没有 SDK 调用或运动。证据与后续
PyTorch/算法镜像待完成边界见
[GPU 容器验证记录](../experiments/20260911_orin_gpu_container/README.md)。

2026-09-11 用户确定后续 Orin 新增算法实验默认使用 Docker 隔离，首期采用
“宿主机 SDK 采集 → 冻结文件 → Docker 感知计算 → 输出位姿”；SAM3/LingBot
继续远端推理，容器运行客户端、ROI、人工确认及 V5。原厂服务和 SDK 环境
留在宿主机，保留当前可用流水线作为回退。阶段步骤、隔离配置与验收标准见
[Docker 迁移计划](s1_orin_docker_migration_plan_20260911.md)。同日已完成基线
检查、Observation bundle 文件边界、ARM64 `_03` 计算镜像重建、镜像内 GPU
smoke test，以及右腕 accepted/左腕 rejected 两个 Orin 离线回归；失败的
`_01` 和对照的 `_02` release 均保留。当前已完成阶段 1～3，阶段 4 的状态、
位姿和拒绝路径通过但峰值内存待测；旧 current 对同一冻结案例已成功回退回放
且位姿差为 0。实时 Docker 全链路、重复性、完整回退演练和算法 GPU 加速仍待
执行。完整证据见
[Docker 执行记录](../experiments/20260911_orin_docker_deployment/EXECUTION_RECORD_20260911.md)。

2026-09-11 双腕同箱体单帧实验：用户确认左3/右8，右腕 V5 accepted，
左腕因截边/内外表面歧义 rejected。各自同帧 FDP 对照中心差为左诊断
2.76 mm、右正式 6.82 mm；FDP 左右视角中心差 24.22 mm，V5 左诊断/右正式
差 22.64 mm。仅各一帧，不是重复性或绝对精度验证；详见
[双腕 V5/FDP 对照](s1_orin_bilateral_fdp_comparison_20260911.md)。

同日已将 Orin `runs/` 下 9 个实时/回放目录（约 72 MB、302 个文件）只读归档到
`experiments/20260910_orin_pose_pipeline/archives/20260911_live_runs/remote_runs/`，
并生成 `SHA256SUMS`；归档包含成功、V5 拒绝、采集时间同步失败和 SAM3 401 失败
记录。双腕/第二观测位的本地 FDP 对照、投影和 TCP 派生结果在该归档同级
`outputs/` 下。首轮右腕的旧 FDP 对照以本地报告/文档保存，远端旧运行目录没有
同名 `fdp_compare_01/` 子目录；该缺口已写入归档 README。

2026-09-11 第二观测位左腕 `live_left_20260911_04`：ROI 2 的 V5 因
mask 截边和内外表面歧义拒绝；同帧 FDP HTTP 200。FDP 与被拒绝的 V5
诊断候选中心差 3.76 mm、yaw 差 1.38°，不是真值误差。尚未进行五次重复性
测试；优先解决完整入镜。认证注入遗漏及 FDP 发布包缺 client.py 已查明，
具体证据、输入合同和人工确认时序修正见
[第二观测位对照记录](s1_orin_second_view_fdp_comparison_20260911.md)。

用户确定 Orin 负责采集、调度和本地位姿后端，SAM3/LingBot 继续调用现有
远端服务；手动单次触发，主输出为 base_link 下箱体几何中心。算法接口可插拔，
首版后端 `v5_2_v5_3b`，左右腕参数化，默认左腕可切换，每次单侧采集。
用户说明实物可能倾斜；现有 V5 仅估计 x/y/z/yaw，roll/pitch 为直立先验，
因此倾斜适用性不能随接口部署而被视为已验证。首版聚焦工程闭环、回放及
诊断，倾斜后端另设阶段；当前已完成本地接口/回放封装，但未据此部署或访问机器人。
接口合同、交付顺序、验收边界见
[Orin 可插拔位姿计划](s1_orin_pluggable_pose_plan_20260910.md)。

后续用户授权只读检查 S1 `Lsy03/fdp_baseline`：现有工作区约 356 MB，
所在盘可用约 1.4 TB。采集和 SAM3/LingBot 客户端与本地对应文件哈希相同，
但远端 fresh_case 仍拒绝左腕、case 缺少新增人工确认校验、geometry 固定
右腕帧名，不能认为整套已更新。建议新部署到同级 `Lsy03/box_pose_pipeline`
并通过适配器只读复用旧数据；该目录已于同日部署版本
`v5_2_v5_3b_20260910_01`，具体回放证据见
[Orin 部署记录](s1_orin_box_pose_deployment_20260910.md)。

本地实现位于
`experiments/20260910_orin_pose_pipeline/`：`Observation`/`BackendResult`、
`ObservationSource`/`ResultSink` 协议、后端注册表、`v5_2_v5_3b` 适配器和单次
冻结案例回放 CLI 已实现。10 项专用测试、既有 V5 相关 68 项测试及 baseline
21 项测试通过；一次右腕人工确认案例回放结果与矩阵中心一致，算法耗时约 4.17 s
（本机 x86）。这些结果是本地工程验证，不是 Orin 性能或实机精度验证。

2026-09-10 已按用户授权将独立发布包部署到 S1
`/home/galbot/Lsy03/box_pose_pipeline/releases/v5_2_v5_3b_20260910_01`，
`current` 指向该版本；Jetson AGX Orin Developer Kit、`s1-python` 依赖和
一次冻结案例回放均已核对。Orin 与本地同输入中心最大绝对差约
`2.26e-12 m`、矩阵最大差同量级；算法耗时约 16.91 s（本地 x86 约 4.12 s）。
旧 `fdp_baseline` 部署清单哈希未改变。此次未采集实时图像、未调用远端服务、
未发送运动命令。完整证据和回退目录见
[Orin 部署记录](s1_orin_box_pose_deployment_20260910.md)。

2026-09-11 已在该独立版本中加入实时
`LiveWristCaptureSource`、SAM3/LingBot 适配器、ROI 候选和人工确认入口，
并完成 Orin 导入检查；`run_pose_once.py` 仍要求显式只读采集确认，确认目标后
才运行 V5。真实相机/远端服务尚未调用，详情见
[实时感知实现记录](s1_orin_live_perception_implementation_20260911.md)。

同日首轮真实实时实验已完成：左腕采集/服务成功但 V5 因
`ambiguous_inner_outer_surface_hypotheses` 正确拒绝；右腕同一静止场景、人工确认
H4 目标后 V5 接受，输出中心约
`[0.9450306242,-0.0219308933,0.5364676366] m`、yaw `87.4822°`。两次均未发送
运动命令；右腕一次接受仍不构成绝对精度或抓取验证。详见
[首轮实时实验记录](s1_orin_live_experiment_20260911.md)。

右腕同一实时 RGB、LingBot 深度、人工确认 mask、K、TF 和 mesh 的 V5/FDP 对照
已完成：中心差 `12.10 mm`、180° 对称 yaw 差 `1.66°`、箱口中心差
`13.23 mm`、两条短边中点差约 `19.66/7.84 mm`。这些是后端差异，不是真值
误差；完整输入合同和解释边界见
[实时 V5/FDP 对照](s1_orin_live_fdp_comparison_20260911.md)。

## Purpose and authority

### 单臂 TCP 输入实验脚本 — 2026-09-11

用户要求输入预抓取位并移动指定机械臂，新增
[`move_to_pregrasp.py`](../experiments/20260911_direct_pregrasp/move_to_pregrasp.py)
和[使用说明](../experiments/20260911_direct_pregrasp/README.md)。输入为显式
左右臂、base_link 下 TCP XYZ（米）和 RPY（度），不叠加生产偏移。使用既有
生产 helper 的 SDK 多初值 IK/FK、自碰撞检查及反馈验证，配合新五次关节插值；
不是 one-click 原生 IMC PTP/LIN 路线。默认只规划，但规划会临时挂载/卸载
GE103 碰撞工具模型，不是纯 getter。执行须现场确认当前具体计划；只提交单臂
轨迹，默认模型峰值关节速度 0.05 rad/s。真实环境/箱体避障不自动建立。

`LOCAL TESTED; NOT DEPLOYED`: 七项本地测试及 CLI help 通过，包括位姿/单位、
插值速度加速度、单臂命令范围、错误确认、执行前拒绝和执行异常停止。脚本尚未
部署或运行于 S1；当前 SDK/helper 兼容性与实际运动效果待验证。前序只读 SSH
源码检查不代表执行过该脚本，保存历史关节数组也不构成新目标的运动授权。

前序对话数值笔误修正：FDP 原始左预抓取 `[0.973265,0.317579,0.603564]`
加生产标定 `[-0.035,-0.05,0]` 后为 `[0.938265,0.267579,0.603564]`，
不是 Y=0.367579。新脚本只使用用户输入，不自动套用这个偏移。

用户运行脚本被既有持箱标记拦截，随后明确确认双臂空载并授权忽略。
新增本次显式 `--ignore-stale-carried-marker`，必须同时提供
`--confirm-empty-gripper`；保留标记文件并将内容/覆盖原因记入报告，
其余运动门禁不变。新增覆盖开关测试后共八项本地测试通过；本次仅修改本地文件。

后续用户运行因 map 位姿差超过 1 cm/1° 被拒绝；该日志本身不能证明物理底盘
移动，也没有运动提交。用户要求删除无关检查，已在本地移除 Navigation 初始化、
map 稳定/漂移检查和持箱标记读取。自碰撞查询改用 odom 位姿快照；底盘静止、
空载与净空合并入一次现场确认，旧三个额外标志仅兼容解析。保留机械臂 IK、
限位、自碰撞、模型起点和执行反馈/停止保护。九项本地测试通过；未部署/实机执行
此修订，不应将先前“残留标记可选忽略”的实现说明当作当前行为。

This file is the durable bridge between historical ChatGPT discussions and local Codex work. Chat-derived claims are context, not ground truth. Verify them against the checked-out source, official documentation, simulation, or the real system before relying on them for implementation or motion.

Detailed OpenCode session findings, conflicts, and the real-robot safety incident are recorded in `docs/opencode_session_knowledge.md`.

The current beginner-to-project roadmap is recorded in
`docs/depalletizing_learning_project_plan.md`.

The model-matched S1 left-arm zero/axis/limit reference is recorded in
`docs/s1_left_arm_joint_reference.md`.

The user-provided Galbot developer-site snapshot for the S1 Python API,
labelled SDK 1.9.1, is summarized in
`docs/s1_sdk_python_api_1_9_1_notes.md`. It is a documented reference rather
than proof that every API is present or behaves identically in the currently
verified S1 SDK 1.9.0 runtime.

The preserved explanatory side chat about the 2026-08-27 static ESDF goal
collision, collision spheres, RPC/PNS/CLI, and the three repeated reachability
checks is recorded in
`docs/history/navigation_esdf_side_chat_20260828.md`. It is historical context;
the verified result remains the log-backed 2026-08-27 entry below. It must not
be reused as the explanation for the different 2026-08-28 post-relocalization
target; later evidence for that target superseded the early "purely the saved
static ESDF" interpretation.

The 2026-09-03 assessment of S1 head stereo RGB, LiDAR point-cloud projection,
dense depth, and wrist RGB-D task boundaries is recorded in
`docs/s1_head_rgb_depth_fusion_assessment_20260903.md`.

## Project scope

The long-term goal is to understand and build an S1 system spanning:

- robot state, sensors, and basic control;
- single-arm and dual-arm manipulation;
- kinematics, inverse kinematics, planning, collision checking, trajectories, and execution;
- RGB-D perception, segmentation, depth, point clouds, and 6D object pose;
- localization, SLAM, navigation, and mobile-base control;
- an integrated task loop from instruction to perception, planning, execution, and feedback.

## Working architecture — 待验证

```text
Task / behavior layer
        ↓
Upper perception
        ↓
Object pose and environment state
        ↓
Dual-arm planning and control (IRMV_DUAL_ARM)
        ↓
IMC
        ↓
Galbot SDK
        ↓
S1 hardware
```

The historical discussion treats Galbot SDK as the hardware-facing state/control layer, IMC as a planning/control framework, and IRMV_DUAL_ARM as a dual-arm planning-to-execution wrapper. Exact package boundaries and APIs remain **待验证** from source.

## Perception pipeline — 待验证

```text
RGB + depth
    ↓
SAM-family segmentation
    ↓
mask
    ↓
dense/refined depth
    ↓
point cloud and object geometry
    ↓
FoundationPose or equivalent
    ↓
object 6D pose
```

Historical project materials mention SAM3, LingBotDepth, FoundationPose, and a work-bin perception flow. Their exact versions, licenses, interfaces, and deployment status must be checked locally.

## Lightweight context: work-bin pose and mask terminology — 2026-09-07

The following is a compact summary of a user-provided explanatory discussion;
it is context rather than independent implementation evidence:

- “Old pose” and “new pose” mean two pose-estimation results. A comparison must
  identify the same object, data frame, and coordinate frame; robot motion can
  change an object's coordinates in `base_link` even when the object itself did
  not move.
- SAM3 produces candidate 2D masks. LingBot provides dense/completed depth, not
  segmentation masks. ROI geometry uses masks and depth to produce ROI objects
  containing geometry plus a processed/final mask. Target selection chooses one
  ROI, and FoundationPose++ receives that final mask together with RGB, depth,
  camera intrinsics, and the matching mesh, then outputs a 4x4 pose matrix.
- A mask answers “which image pixels belong to the selected target”; a depth
  image answers “how far is each pixel”; an ROI is a richer object and is not
  synonymous with a mask. The final ROI mask may differ from the original SAM3
  mask after geometric projection and morphology.
- Selecting the target instance happens before FoundationPose++; specifying the
  object type/mesh is separate from specifying which visible instance to
  estimate. Exact source behavior remains **待验证** against the local
  implementation.

## Recommended learning path

Current user focus (2026-08-20): prioritize arm manipulation for the grasping
role.  Learn state reading, joint-space control concepts, FK/IK, Cartesian
targets, planning, trajectory review, gripper control, and dual-arm grasp
staging before returning to navigation.  Do not begin with a whole-body SDK
tutorial or an unreviewed real-robot motion.

### Phase 1 — SDK foundation

Establish the smallest closed loop:

1. Initialize/connect safely.
2. Read robot and joint state.
3. Read sensor data.
4. In simulation first, issue one minimal arm or base target.
5. Read state again and verify the result.

Focus on startup/lifecycle, state APIs, manipulators, mobile base, grippers, lift, cameras, blocking versus non-blocking calls, error handling, and safety limits.

### Phase 2 — planning and dual-arm control

Trace one target pose through FK/IK, motion planning, collision checking, trajectory generation, and SDK execution. Map the actual relationship among IRMV_DUAL_ARM, IMC, Galbot SDK, and S1 instead of assuming the chat-derived diagram is exact.

### Phase 3 — upper perception

Run one offline sample before reading every implementation detail. Follow RGB/depth through mask, depth processing, point-cloud generation, geometry estimation, and 6D pose output. Record coordinate frames, camera calibration, transforms, units, and confidence/failure cases.

### Phase 4 — navigation

Study localization, maps, SLAM, path planning, obstacle handling, and base control. Verify the ROS/ROS 2 distribution and message interfaces from the actual environment.

### Phase 5 — integration

Connect task instruction → perception → target pose → manipulation planning → base/arm execution → state feedback. Add explicit recovery behavior and real-robot safety gates.

## Historical project/component references

The ChatGPT project mentioned the following names. Presence and paths in the current repository are **待验证**:

- `GalbotSDK`
- `IMC`
- `IRMV_DUAL_ARM`
- `g1_workbin_perception`
- `DualMobManip_S1_migration`
- `S1_nav_experiment_ws`
- `AI_SERVICES_API.md`
- `UPPER_PERCEPTION_FLOW.md`
- `run_perception_once.py`
- `map_assets`

One historical source tree was described as `/home/lsy03/GalbotS1文件/260611_sjtu_workbin_movement`. It should not be assumed available or authoritative without inspection.

## Related local learning repository

The directory `/home/lsy03/Lsy03_document/galbot_s1_SDK_learning` was confirmed readable on 2026-08-20. At that time it contained, among other items:

- `README.md`, `AGENTS.md`, and `docs/`
- `sdk_examples/`, `ros_examples/`, and `experiments/`
- `imc_learning/`, `dual_arm/`, `perception/`, and `navigation/`
- `third_party/`, `scripts/`, and `archive/`
- a Git repository and a `GalbotSDK-main.zip` archive

Use it as a reference source when explicitly relevant. Do not edit it from this project unless the user specifically asks.

## Environment and access notes

- `LOCAL CONFIGURATION (2026-09-09)`: 用户要求将 S1 SSH 连接方式保存为个人
  skill，已安装 `/home/lsy03/.codex/skills/galbot-s1-ssh/SKILL.md`。
  凭据单独存于仓库外 `/home/lsy03/.config/galbot-s1/ssh-password`，目录权限
  `700`、文件权限 `600`（本地明文文件，不是加密钥匙串）；仓库不保存密码。
  skill 格式校验通过，本次未连接机器人，当前认证有效性/可达性待验证。
  保存凭据不构成未来自动连接或运动授权，仍遵守当前请求范围及逐步运动确认。
- Historical discussion identifies an Ubuntu 22.04 laboratory environment connected to an S1 robot; confirm the actual host OS and ROS distribution before setup work.
- S1 SSH endpoint supplied by the user on 2026-08-20: `ssh galbot@10.34.216.17` (**待验证** until a successful connection). Credentials are intentionally omitted from this repository; obtain them from a secure local store when access is required.
- Local workstation helper `/home/lsy03/bin/codex-desktop-proxy` was installed on 2026-08-20. It launches Codex Desktop through the user-supplied mobile Clash endpoint `192.168.211.229:7890`, while bypassing `10.34.216.0/24`, `192.168.211.0/24`, and localhost. Script installation and shell syntax are verified; proxy reachability and S1 connectivity remain **待验证**.
- One discussion referred to GalbotSDK release/main version `V1.9.1`; treat this as **待验证** because repository state may have changed.

## Read-only S1 inspection — 2026-08-20

The user authorized read-only SSH inspection of `/home/galbot/ie_lab` on
`10.34.216.17`.  Access was made through a user-created temporary SSH control
socket; no remote file was modified and no project, container, ROS, SDK, or
motion command was run.

- `VERIFIED (current S1 files)`: the current handoff document is
  `/home/galbot/ie_lab/S1_DEVELOPMENT_HANDOFF.md`, dated 2026-08-14.
- `VERIFIED (current S1 files)`: the production-oriented source tree is
  `/home/galbot/ie_lab/projects/dual_arm_v5/workspace/s1_sjtu_0806`.
- `VERIFIED (current S1 files)`: that tree contains Galbot SDK adapters,
  perception and pipeline gates, IMC planning/execution helpers, Mode 00/10
  orchestration, GE103 gripper helpers, navigation helpers, and 4317/H4
  configuration.
- `DOCUMENTED WITH HISTORICAL RUN EVIDENCE`: the handoff records a real chain
  `RGB-D -> Thor SAM3 -> LingBot-Depth -> ROI/H4 -> FoundationPose++ -> dual-arm
  targets -> IMC execution`. FoundationPose++ is called remotely at
  `10.34.216.13:7876`; SAM3 and LingBot-Depth are external Thor services at
  `10.34.216.11`.
- `DOCUMENTED WITH HISTORICAL RUN EVIDENCE`: grasp approach, gripper close,
  100 mm lift, carried-crate navigation, release, and return have succeeded in
  separate real-robot experiments.  The inspected result
  `rerun_shifted_unload_20260814_1458_retry2/RESULT.txt` ended with the crate
  held at unload and explicitly recorded `put_executed=false`.
- `VERIFIED (current S1 source/docs)`: the current Mode 00 one-click route
  deliberately skips unverified `put/down`; the source contains a disabled
  fixed-put stage and separates `--dry-run` from `--execute`.
- `VERIFIED (current S1 config)`: the 4317/H4 profile uses a 0.4 x 0.3 x
  0.175 m crate, stack level 4, 0.165 m layer pitch, and requires fresh
  perception rather than silently reusing an absolute target.
- `UNRESOLVED`: GE103 feedback/force semantics are not calibrated.  The
  current TODO warns not to interpret returned `effort=1000` as 1000 N.
- `ENGINEERING RISK`: the handoff says the production source tree and per-run
  source snapshots are not yet tied to one reliable, resolvable Git revision.

## Real-robot safety lessons from OpenCode history

## `chassis_env` test-script inspection — 2026-08-22

The user authorized read-only SSH inspection of
`/home/galbot/ie_lab/projects/chassis_env`; no robot program, container,
service, SDK initialization, controller operation, or motion command was run,
and no remote file was modified.

- `VERIFIED (current S1 files)`: the version-controlled project contains
  `tools/check_env.py`, `controller_status.py`, `relocalize_report.py`, and
  `navigate_relative_v2.py`.  Only the first two are offline/read-only;
  relocalization changes localization state, and relative navigation commands
  the mobile base.
- `VERIFIED (current S1 files)`: the Python files directly under `workspace/`
  have no Git history in the enclosing repository and appear to be field
  experiments rather than maintained, versioned tools.
- `VERIFIED (source and historical SDK log)`: `workspace/test_move_wrist.py`
  can read state, command either arm with `set_joint_positions`, and command
  either gripper.  The SDK log at 2026-08-13 14:24:45 records a right-arm
  `set_joint_positions success` with final position error norm about
  `0.000318666`, which is evidence that one right-arm invocation reached its
  numeric target.  The exact command line, target semantics, collision safety,
  and repeatability are not recorded, so the script as a whole is not an
  approved general-purpose motion test.
- `VERIFIED (historical SDK logs)`: the temporary left-arm experiments around
  13:46--13:58 on 2026-08-13 did not reach their 0.2 rad target.  The direct
  command retained about `0.19988` final error; the GalbotMotion/
  `set_joint_positions` attempt timed out; and the
  `execute_joint_trajectory` attempt timed out.  The `request_target` log shows
  controller switching but no positive target-completion evidence.
- `VERIFIED (historical SDK logs)`: several 2026-07-31 chassis navigation
  attempts successfully submitted `navigate_to_goal_v2` but finished
  `FAILED`; therefore command submission must not be reported as successful
  navigation.

Do not run any of these robot-facing scripts without the user's explicit,
step-specific direction and the real-robot safety gate in `AGENTS.md`.

## S1 本地模型与可视化 — 2026-08-22

- `VERIFIED (local official repository snapshot)`: 本地目录
  `/home/lsy03/Lsy03_document/galbot_s1_SDK_learning/third_party/galbot_s1_description`
  的 Git remote 是银河通用官方组织
  `GalaxyGeneralRobotics/galbot_s1_description`；本地提交为
  `cb758e557a880c70260c7883207334aed2aa3c65`。
- `VERIFIED (local files)`: 该仓库同时提供 URDF、MJCF 和 USD 三种 S1
  模型资产。URDF 是 `galbot_s1-v2_1_0-A21-ge103in`，包含视觉 mesh、碰撞
  mesh、关节轴和限位；MJCF 可作为 MuJoCo 入口，USD 可作为 Isaac Sim/
  Omniverse 入口。
- `VERIFIED (local files and current official repository page)`: 官方描述仓库
  本身没有 ROS package manifest、RViz 配置、launch 文件、Gazebo world/plugin
  或一键仿真脚本。因此可把 URDF 接到 `robot_state_publisher`、
  `joint_state_publisher_gui` 和 RViz2，但这属于通用 ROS 接入，不应描述为官方
  已提供的 S1 RViz 仿真套件。
- `ENVIRONMENT CHECK`: 当前本机没有发现 ROS、RViz、MuJoCo 或 Isaac Sim
  可执行环境；离线关节演示应保持为纯本地几何/运动学显示，不能被表述为
  物理仿真或真机控制验证。

### 后续本机环境与 RViz2 演示

- `VERIFIED (local environment, later on 2026-08-22)`: 已安装 ROS 2 Humble
  和 RViz2；`ROS_DISTRO=humble`、`ROS_VERSION=2`，RViz2 窗口可正常打开。
- `VERIFIED (local environment)`: RTX 4090 已由 NVIDIA 595.84 驱动接管，
  OpenGL 4.6 硬件直接渲染正常；这取代了上文“未发现 ROS/RViz”的早期环境
  检查结果。
- `IMPLEMENTED AND STATICALLY VERIFIED`: 离线演示位于
  `experiments/20260822_s1_rviz_demo`。它在内存中把官方 URDF 的 82 个相对
  mesh 路径转换为本地 `file://` URI，不修改官方模型；模型树有 54 个 link、
  53 个 joint，唯一根 link 是 `base_link`，且引用的 mesh 文件全部存在。
- `VERIFIED (user runtime and screenshot)`: “RViz2 + RobotModel +
  joint_state_publisher_gui”已联合启动，完整 S1 模型可见，关节滑块可改变离线
  模型姿态；没有连接真机。
- `VERIFIED (local assets and RViz observation)`: 官方 GLB 的部分主体外观依赖
  内嵌 PBR 纹理，RViz2 未完整还原时会使机身、底盘和立柱整体偏黑。演示包
  因此提供 `color_mode:=clear|original`；默认 `clear` 用高对比的每-link URDF
  材质辅助关节学习，`original` 保留 GLB 内嵌材质。高保真官方外观更适合在
  后续 USD/Isaac Sim 中验证。
- `VERIFIED (local MJCF inspection)`: 官方本地 MJCF 含 54 个 body、52 个
  joint、314 个 geom（其中 235 个 collision、75 个 visual）、19 个位置执行器、
  3 个底盘速度执行器、22 个 joint-velocity sensor 和 4 个 equality constraint；
  双臂、头部、升降柱和底盘已有控制范围、力范围、质量/惯量与碰撞数据。
  但它没有预配置 camera、contact pair 或 keyframe，53 个 inertial 中有 15 个
  使用 `1e-6 kg` 级占位质量，因此可用于离线重力/接触/基础控制实验，但不能
  未经验证就称为与实机动力学一致的高保真数字孪生。
- `VERIFIED (local USD inspection)`: 官方 USD 含 1 个 articulation root、32 个
  rigid body/mass API、30 个 revolute joint、1 个 prismatic joint、54 个 drive
  API、30 个 collision API，以及独立 PBR 材质和纹理资产。它适合在 Isaac Sim
  中做高质量外观、场景、物理和后续传感器配置；现有资产本身不证明相机、
  RGB-D 或其他传感器已经按当前实机完成标定。

- `VERIFIED (historical session output)`: Read-only state access and several small head/left-arm experiments were reported successful on 2026-08-15.
- `VERIFIED (historical session output)`: A recovery script later moved the torso lift downward because an unmeasured prior torso position was guessed as `0`. This violated the evidence and safety rules.
- `VERIFIED (historical session output)`: The torso was subsequently moved from approximately `0.4331` to `0.74` with a reported `ControlStatus.SUCCESS`.
- `OBSERVATION`: The arm vectors recorded before `example2` reproduce the pose first observed by OpenCode, but the user later questioned whether that pose was actually the correct natural/initial pose. Those vectors are not an approved recovery pose.
- `USER CONSTRAINT`: Do not automatically connect to or control the robot. Each real motion requires fresh, step-specific confirmation.

## S1 导航 SDK 容器只读调查 — 2026-08-27

详细报告见 [`docs/s1_navigation_sdk_report_20260827.md`](s1_navigation_sdk_report_20260827.md)。

- `VERIFIED (current S1 container)`: `s1_sjtu_0806_slim` 使用
  `s1-sjtu-0806-slim:latest`，默认仅运行 `sleep infinity`，并以 host
  network/IPC 访问宿主机上的导航、运动规划、定位和传感器服务。
- `VERIFIED (current S1 container)`: 容器内 Galbot SDK 版本为 1.9.0，
  Python 为 3.8.10/aarch64。
- `VERIFIED (current S1 host)`: 宿主机同时提供不经 Docker 的受管 SDK
  环境：`/home/galbot/ie_lab/bin/s1-python` 使用
  `/home/galbot/ie_lab/envs/s1-sdk-1.9.0-py38` 和 `/data/galbot/lib`。
  2026-08-27 的 `s1-env-check` 实际通过，确认 Python 3.8.20、SDK
  1.9.0、NumPy/SciPy/OpenCV/Open3D 和 SDK 符号导入；该检查未初始化机器人。
  默认 `/usr/bin/python3` 仍无法找到 `galbot_sdk`，因此宿主机 SDK
  示例应用 `s1-python` 或先 source `s1-env`，不应写全局 `.bashrc`。
- `VERIFIED (current SDK stubs)`: `GalbotNavigation` 暴露定位/位姿/任务
  状态、直达/目标/航点/速度导航、重定位、运动学限制，以及
  `add_bounding_box`/`attach_box_to_link` 等携带物建模接口。
- `VERIFIED (current S1 container)`: slim 容器声明 ROS 1 Noetic 环境，但没有
  `rosnode`/`rostopic`/RViz/ROS 2/Nav2 可执行环境；不应直接把 Nav2 安装进
  该真机运行容器。
- `VERIFIED (current SDK stubs)`: SDK 提供 LiDAR 点云二进制数据、PointField、
  TF/外参和 odometry 读取，可用于在独立 ROS 2 环境实现 PointCloud2/TF/
  Odometry 桥接。
- `HIGH-PRIORITY HYPOTHESIS`: 抓箱后的导航碰撞报警可能同时需要
  “将箱体附着到机器人碰撞模型”和“从融合障碍点中过滤机器人自己携带的箱体”。
  当前 `/opt/s1-sjtu` 没有调用导航箱体 API，但该假设还需日志和静态真机状态验证。
- `VERIFIED (non-motion S1 host SDK run, 2026-08-27)`: 在确认无其他 SDK
  客户端、取得 `/home/galbot/ie_lab/control.lock` 后，使用宿主机
  `s1-python` 运行受限状态脚本成功。SDK 报告 `localized=true`，
  `map` 位姿约为 `[2.7946, 0.2979, -0.0019, 0.0022, -0.0015,
  -0.0007, 1.0000]`，导航状态 `UNKNOWN (0)`，bounding-box 列表为空。
  本次未发送运动、控制器切换、重定位或 stop-navigation 调用，SDK
  生命周期清理成功。详见 `experiments/20260827_s1_navigation/`。
- `VERIFIED (user-run S1 base navigation, 2026-08-27)`: 用户在宿主机受管
  SDK 环境中执行了 `base_link` 前进 `0.5 m` 的
  `navigate_to_goal_v2` 测试，三次静态可达性检查均为 true，v2 碰撞检测
  开启。后续位姿回读换算为起始 `base_link` 约前进 `0.4730 m`、
  横向偏差 `-0.0026 m`，距离请求目标少约 `0.0270 m`。SDK/PNS 返回
  `SUCCESS`，但 `check_goal_arrival()` 为 false、任务状态回读为 `UNKNOWN`，
  因此守护 CLI 正确地报告 `terminal_result_not_arrived`，不将服务成功等同于
  严格到达验证。
- `VERIFIED (S1 navigation fail-closed precheck, 2026-08-27)`: 在地图位姿约
  `(1.008, -0.076)` 处请求沿 `base_link` 前进 `1.0 m` 时，守护 CLI
  在控制器切换和运动提交前拒绝。PNS 服务端三次均记录目标位姿在
  静态 ESDF 中碰撞：`goal available=0`、`path_collision=0`、
  `has_solution=0`，碰撞为 `omni_chassis_base_link` sphere 9，距离约
  `0.145–0.163 m` 而球半径为 `0.17 m`。日志同时明确
  `evaluate at dyn map: 0`，因此该次拒绝源于静态 3D 地图目标净空，
  不是动态点云障碍。
- `IMPLEMENTED AND LOCALLY TESTED (2026-08-28)`: 导航守护 CLI 增加
  `diagnose-localization` 纯只读子命令，在同一 SDK 会话内有界采样
  `is_localized()`、地图位姿和导航状态，并分开报告 `query_ok`
  与 `navigation_ready`。本地伪 SDK 测试已覆盖“延迟后恢复定位”和
  “持续未定位”两种情况；未连接或运行于真机，真机结果仍待验证。
- `VERIFIED (user-run S1 localization diagnostic, 2026-08-28)`: 用户在 S1
  宿主机运行 `diagnose-localization --timeout 10 --interval 1`，11 次采样
  全部为 `localized=false`、地图位姿为空，导航状态为 `UNKNOWN`；
  `localized_ever=false`且 `navigation_ready=false`。SDK 会话和查询成功，
  因此该次现象不是短暂的客户端初始化同步延迟；定位服务、地图加载、
  传感器输入或定位置信度中的具体原因仍待只读调查。本次未切换控制器、
  未重定位、未停止导航，也未发送运动命令。
- `VERIFIED (user-run S1 host inspection, 2026-08-28)`: 当前地图仍为
  `/var/maps/room0804`，80 MB 的 `global_cloud_cleaned.esdf` 存在；
  `service_navigation_plan`、三路 LiDAR capture、`robot_state_publish` 和
  `localization_server` 均在运行，且进程启动时间集中在 08:32:13--14。
  `map.yaml`/`map.pgm` 也在 08:32 更新。因此可排除“定位进程根本未运行”；
  “宿主机或导航栈重启后定位状态未重新建立”是当前待验证假设。
- `IMPLEMENTED AND LOCALLY TESTED (2026-08-28)`: 导航 CLI 新增受保护的
  `relocalize` 子命令。它会预览完整 map 初始位姿、要求与数值绑定的
  精确交互确认、只调用一次 `relocalize()`，然后进行有界只读观测；
  若导航状态为 `RUNNING`/`OCCUPIED` 则拒绝执行。本地伪 SDK 的 4 项测试
  已通过，包括精确确认后单次调用和错误确认时零状态变更；尚未在真机执行。
- `VERIFIED (user-run guarded relocalization, 2026-08-28)`: 用户明确确认后，
  以人工估计的 map 位姿 `(x=0.2 m, y=-0.2 m, yaw=-0.5 rad)` 发送了一次
  `relocalize()`。RPC 返回 `(true, "SUCCESS")`，但后续 10 秒 11 次采样全部仍为
  `localized=false`、无地图位姿；CLI 正确报告 `relocalization_not_verified`。
  本次未发送任何运动、控制器切换或导航命令。这证明重定位 RPC 成功
  不等于定位收敛成功；在核查日志、传感器输入和初始位姿误差前不应盲目重试。
- `VERIFIED (read-only S1 localization root-cause inspection, 2026-08-28)`:
  经用户明确授权，Codex 通过用户创建的 SSH 复用连接完成只读调查，未启动
  SDK 客户端或改变机器人状态。宿主机于 08:31:44 启动，导航/定位/LiDAR
  栈在 08:32 启动；room0804 地图、106 个 key pose、约 246 万个全局点及
  PCD/ESDF 均加载/存在。底盘 LiDAR、IMU 和 TF 已被检测，前端里程计也收到
  点云/IMU；但本次启动后已观测的 8,953 次 score 全为 `-1`，并出现
  89,799 次 `lidar pose empty`。LIO 6 Hz 低于默认 10 Hz 的警告在前一天
  定位正常时也大量存在，不足以单独解释本次失败。
- `VERIFIED (last complete trusted pre-reboot pose)`: 2026-08-27 20:23:38 的最后完整
  高分定位样本为 score `0.978842`，位置
  `(1.01397,-0.0760396,-0.00384747)`，四元数
  `(0.00145588,0.00159162,-0.0799555,0.996796)`，平面 yaw 约 `-0.160 rad`。
  用户本次估计 `(0.2,-0.2,-0.5)` 与之相差约 0.82 m 和 0.34 rad，初值超出
  匹配收敛范围是当前首要假设。但只有在用户确认该时刻后机器人未被物理移动时，
  该完整快照才可作为下一次重定位依据。
- `VERIFIED (successful user-run relocalization, 2026-08-28)`: 确认机器人已被
  物理移动后，用户以估计位姿 `(x=1.0 m,y=0.0 m,yaw=-pi/2)` 执行受保护
  重定位。约 2.0 秒后 `localized=true`，且直到 15 秒观测结束始终保持；
  最终位姿约为
  `[0.41497,-0.09932,-0.02023,0.00401,-0.00035,-0.71047,0.70371]`，
  `navigation_ready=true`。定位引擎将初值平移修正了约 0.594 m，方向仅修正
  约 0.0125 rad。这已验证定位状态成功恢复，但在运动前仍需用现场几何核对
  最终 map 位置，以排除对相似场景的错误匹配。本次未发送运动命令或切换控制器。
- `VERIFIED (post-relocalization static precheck refusal, 2026-08-28)`: 定位稳定在
  约 `(0.4148,-0.0978,yaw=-1.58)` 后，用户请求沿 `base_link` 前进 1.0 m；
  CLI 在三次静态 `check_path_reachability()` 阶段 fail closed，未切换控制器或
  发送运动。该目标换算到 map 约为 `(0.4056,-1.0977)`。对保存的 room0804
  `map.pgm` 离线检查表明：起点、沿线每 0.1 m、目标和目标周围约 0.2 m 邻域
  均为像素值 254 的自由区。因此该次拒绝不是 2D 栅格占据可以解释的，三维
  ESDF/底盘碰撞球或地图-ESDF 对齐问题是主要方向。这一新目标的具体碰撞 link、
  sphere 和距离仍需 PNS 日志确认，不能直接沿用前一天不同目标的 sphere 9 结论。

### 2026-08-27 与 2026-08-28 ESDF 事件分离及证据修正

以下是两个不同起点、目标和时间的实验，不得混用数值：

| 事件 | 起点/目标 | PNS 距离证据 | 当前解释 |
| --- | --- | --- | --- |
| 2026-08-27 前进 1.0 m 预检查 | 起点约 `(1.0076,-0.0764)`，目标约 `(1.9949,-0.2353)` | sphere 9 半径 `0.17 m`，距离约 `0.145–0.163 m`，日志含 `evaluate at dyn map: 0` | 对该历史目标，日志支持“目标姿态被 PNS 的静态评估拒绝”；底盘未运动 |
| 2026-08-28 重定位后前方边界 | 起点约 `(0.4148,-0.0978,yaw=-1.58)`，1.0 m 目标约 `(0.4056,-1.0977)` | 后续任务记录的 PNS sphere 9 距离约 `0.126–0.127 m`；同一查询位置的磁盘 ESDF/PCD 离线距离却约 `1.29/1.30 m` | 已排除“磁盘 `global_cloud_cleaned.esdf` 本身即可解释当前拒绝”；运行时融合场、缓存或坐标/时序问题仍待同步复现 |

- `SUPERSEDED INTERPRETATION (2026-08-28)`: 早期侧边解释把第二个事件也直接
  归因于保存的纯静态 ESDF。后续 PNS 数值与磁盘 ESDF/PCD 对照不一致，故该
  解释不再有效。`evaluate at dyn map: 0` 的厂家内部精确语义仍为 **待验证**，
  不能自行等同于“只读取磁盘 `.esdf` 文件”。
- `DOCUMENTED WITH 2026-08-28 TASK LOG EVIDENCE`: 第二个事件的具体 PNS
  数值来自当日任务中读取的厂家日志；原始日志尚未作为版本化文件保存，因此
  后续同步实验应把原始日志片段与时间戳纳入证据包。
- `VERIFIED (later passive captures)`: 后续真实 `EsdfGrid` 单帧和同步帧在
  前方 0.8 m 的 sphere 9 投影采样约为 `0.967 m` 和 `0.963 m`，均未复现
  `0.126–0.127 m`。这说明异常会随运行状态出现或清除，而不是磁盘地图中的
  固定永久障碍；其传感器/TF/过滤来源仍未知。

## S1 SDK 1.9.1 Python API 文档快照 — 2026-08-28

详细摘要见 [`docs/s1_sdk_python_api_1_9_1_notes.md`](s1_sdk_python_api_1_9_1_notes.md)。

- `DOCUMENTED (user-provided official-page snapshot)`: 用户粘贴的 Galbot
  开发者站点页面标记为 `latest (1.9.1)`，并把 S1 Python API
  分为 `GalbotRobot`、`GalbotMotion`、`GalbotNavigation`、
  `GalbotPerception` 和公用类型/枚举。当前实机受管环境已核验为
  SDK 1.9.0，因此 1.9.1 符号和语义在调用前仍需用当前 stub
  或最小静态调用确认。
- `DOCUMENTED`: `GalbotRobot` 的正常关闭顺序是
  `request_shutdown()` → `wait_for_shutdown()` → `destroy()`；`destroy()`
  后当前进程不能重新初始化。传感器必须在 `init()` 时显式启用，
  同步观测还需 `enable_sync_mode=True`。
- `DOCUMENTED`: S1 空参数关节状态顺序为
  `torso -> head -> left_arm -> right_arm`；但轨迹与控制应显式携带
  `joint_names` 或 `joint_groups`，并保证每个轨迹点与展开顺序一致。
- `DOCUMENTED`: `set_joint_positions()` 用于低频关键帧；
  `set_joint_commands()` 是高频流式接口且不会从当前状态插值到首帧，
  大跳变会导致过快运动。非阻塞接口立即返回不表示运动停止或完成。
- `DOCUMENTED`: `GalbotMotion` 不自动订阅或同步导航系统的
  点云地图；操作规划需通过 `add_obstacle()` 等接口显式建立障碍物场景。
  抓取物用 `attach_target_object()` 附着，工具用 `attach_tool()` 加入模型。
- `DOCUMENTED`: 导航命令的“请求成功/接受”不等于“严格到达”；
  应分开检查定位、静态可达性、任务终态、`check_goal_arrival()` 和
  最终位姿。`move_straight_to()` 不提供动态避障或全局规划。
- `DOCUMENTED`: `navigate_to_goal_v2()` 的 `max_vel=[vx, vy, vyaw]` 是 x/y/偏航速度通道的上限（通常按底盘本体坐标解释，具体 frame 语义以当前 SDK/PNS 版本为准），不是导航方向；方向来自 `goal_pose` 在 `pose_frame` 中的位置差分，`omni_plan=True` 只是允许全向规划。如需直接发送正负侧向速度，是 `navigate_with_velocity()` 的职责，但它不等于全局避障。
- `DOCUMENTED`: 携带箱体导航有两类互补接口：
  `add_bounding_box()` 让融合服务过滤箱体区域内的自观测障碍点，
  `attach_box_to_link()` 让 PNS 把箱体作为附着碰撞物。这支持本项目
  “抓箱后导航可能同时需要携带物碰撞建模和自点云过滤”的高优先级假设，
  但 1.9.0 实机运行时仍待验证。
- `VERIFIED (current PNS model/config, 2026-08-28)`: 本次碰撞的 sphere 9 是
  `omni_chassis_base_link` 原生碰撞球，在底盘局部坐标中心约为
  `(-0.235,0.107,0.382)`、半径 `0.17 m`；变换到本次目标后与 PNS 日志一致。
  三次任务日志的左/右工具均为 `None`。PNS 配置明确
  `use_esdf_filter=false`，其预置机器人周围过滤范围为
  `[-0.5,-0.5,-0.5]` 到 `[0.5,0.5,2.0]`。`attach_box_to_link()` 用于增加
  携带物碰撞几何，不是消除本体 sphere 假碰撞的手段；当前不调用它或
  `add_bounding_box()`。
- `IMPLEMENTED AND LOCALLY TESTED (2026-08-28)`: 导航 CLI 新增纯只读
  `probe-relative`。默认在同一 SDK 会话中对 `base_link` 前方
  `0.10,0.20,0.30,0.40,0.50,0.60,0.80,1.00,1.20 m` 各执行三次
  `check_path_reachability()`，并分类为稳定可达、稳定不可达或混合。
  本地伪 SDK 的 5 项测试全部通过；该命令不切换控制器、不发送导航、
  不重定位，也不修改 bounding box 或 attachment。真机扫描结果待执行。
- `VERIFIED (local ESDF generation chain, read-only S1 inspection, 2026-08-28)`:
  局部 ESDF 由 `/data/galbot/bin/galbot_fusion_main` 使用 NVIDIA nvblox 生成。输入为
  底盘、头部和后部三路 Livox 点云，约 10 Hz；当前关闭深度相机和 OCC
  融合，同时加载 `global_cloud_cleaned.pcd`。nvblox 依次维护 TSDF/颜色/
  freespace/occupancy/ESDF 层，体素 0.05 m，输出 `base_link` 周围
  `x,y=[-5,5] m`、`z=[0,2.1] m` 的 `200x200x42` 局部块。ESDF 调试消息约
  6.5--7 Hz，TSDF 调试点云目标 2 Hz；系统存在
  `galbot.perception_proto.EsdfGrid`/`TsdfGrid` protobuf 以及
  `esdf_debug_pointcloud` channel。
- `VERIFIED (current binaries/schema/logs, read-only S1 inspection, 2026-08-28)`:
  fusion 与 PNS 之间还有序列化 DDS channel `esdf_pointcloud_serialized`；PNS
  二进制包含对应的 `EsdfGrid` reader 和 `esdf_map_callback`，当前日志持续记录
  `recv esdf map topic` 及 `updateEsdfMap ... size: 200, 200, 42`。安装的
  `perception_esdf_pb2.py` 表明 `EsdfGrid` 字段包括 header、`voxel_size_m`、
  三轴 voxel count、`origin_point`、重复 float `voxel_distances`、
  `current_pose` 和 `offset_per_voxel`。当前约 `(-4.56,-5.07,0)` 的日志
  “pose”与 `base_link` 周围 `x/y=[-5,5] m` 输出窗口的地图原点吻合，不应误读
  为机器人当前底盘位姿。
- `VERIFIED (installed passive-reader capability, 2026-08-28)`: 宿主机安装了
  Fast DDS、多个 `libembosa` 版本，以及 Python 3.8/3.10 embosa binding；
  `Node.CreateSerializationReader(message_type, channel_name, callback, ...)` 可用于
  被动订阅 `EsdfGrid`。当前生成的 protobuf 与系统 Python 的 protobuf 版本不兼容，
  因此捕获器应使用与厂家运行时匹配的受管 Python 3.8 环境。真正创建 reader
  会新增 DDS participant、共享内存和少量日志/CPU负载，不能归类为纯文件只读
  检查，需单独授权；下述捕获是在用户随后明确授权后执行。
- `VERIFIED (authorized passive ESDF capture, 2026-08-28)`: 厂家
  `embosa_topic_tool` 验证 `esdf_pointcloud_serialized` 的 publisher 为
  `galbot_fusion_main`，subscriber 为 PNS 与 motion-plan，消息类型为
  `galbot.perception_proto.EsdfGrid`；精确 QoS 是 `LARGE_DATA_TRANSPORT`、
  best-effort、keep-last depth 3、volatile、auto callback。使用相同 QoS 的临时
  被动 reader 成功捕获一帧 6,720,121-byte payload，SHA-256 为
  `0ab948b68968544990b7cc7c39fcca8abe06ee8adaf06eb20fa1b94cfe858f22`。
  成功 reader 未导入 protobuf/Galbot SDK、未创建 publisher，也未发送运动、
  定位、导航或配置命令。
- `VERIFIED (captured frame and offline RViz replay, 2026-08-28)`: 本地解析确认
  该帧含 `200x200x42=1,680,000` 个有限 float 距离，voxel size `0.05 m`，
  `frame_id=base_link`，距离范围约 `0--3.7195 m`。空间连续性验证扁平索引为
  `x + nx*(y + ny*z)`（精确半体素约定仍待厂家源码确认）。同一帧中 sphere 9
  在当前、前方 0.7/0.8/1.0 m 投影位置的采样距离约为
  `0.814/0.925/0.967/1.075 m`，此前的 `0.126 m` 前向异常在本次捕获时已不
  存在，说明运行时场可能已变化或清除。现有 ROS 2 demo 已增加离线 ESDF
  近障碍点云、0.40 m高度切片和 sphere 9投影标记；无 GUI测试实际发布
  113,250 个阈值点和 40,000 个切片点，全程未连接 S1。
- `PROJECT DECISION (2026-08-31)`: 后续导航/ESDF RViz 主实现统一为
  `experiments/20260822_s1_rviz_demo/ros2_ws/src/s1_rviz_demo`。它承载机器人
  模型、历史失败回放和厂家 `EsdfGrid` 离线回放。外部学习仓库的
  `navigation/ros2_ws/src/s1_room0804_rviz` 仅保留为静态地图/历史场景参考，
  不再并行增加诊断功能。
- `IMPLEMENTED AND LOCALLY VERIFIED (2026-08-28)`: 离线 ESDF查看器已改为
  近障碍固定红色、0.40 m切片固定 `0--1 m` 色标；切片按用户后续要求默认
  开启。查看器加入此前完整
  `pose_readonly` 的 `map -> base_link`，以及用户实读的双臂 14 关节快照。
  头部、升降柱、轮组和夹爪继续使用 URDF默认值。画面内明确标注
  “真实单帧 ESDF + 较早底盘位姿 + 较晚双臂状态”的分时组合边界，不能称为
  实时全身状态。持续实时桥暂缓，直到 ESDF、定位、关节状态和 PNS查询能按
  同一时间基准同步记录。
- `VERIFIED (timestamp-synchronized passive capture, 2026-08-28)`: 在同一
  embosa node中被动订阅 `esdf_pointcloud_serialized` 与
  `/galbot/mes/global_pose`，捕获窗口观察到45个位姿帧；选中的ESDF和地图
  位姿 header 时间戳均为 `1787910212000000000 ns`，差值 `0.0 ms`。同步底盘
  位姿约为 `[0.413935,-0.101069,-0.016797,0.003628,-0.000234,-0.710142,
  0.704049]`。新 ESDF帧中 sphere 9 当前/前方0.7/0.8/1.0 m采样距离约为
  `0.806/0.921/0.963/1.071 m`，仍未重现历史 `0.126 m`异常。RViz默认已切换
  到这组同步ESDF+底盘位姿；双臂仍为旧快照，不能纳入同步结论。
- `VERIFIED (fusion filters and TF dependency, 2026-08-28)`: fusion 已启用三层自体/
  噪声过滤：`1x1x3 m` 的 `galbot_fusion_robot_bbox`（中心 z=1.5 m）、
  S1 URDF convex-hull mesh 过滤（`ego_point_threshold=0.08 m`）、以及 0.5 s 时窗内
  至少 3 次命中的时序体素过滤；单帧离群过滤半径 0.10 m。但
  `clear_blind_before_pub_esdf=false`。fusion 严格依赖坐标变换：2026-08-28
  13:45:27--15:06:36 持续没有 `map -> base_link`，直到 15:06:38 才首次
  处理三路 LiDAR 并发布 ESDF；之后仍偶发无法获得
  `base_link -> head_link1`，并跳过对应 LiDAR 帧。因此 TF 时序/完整性和
  `clear_blind_before_pub_esdf=false` 是当前前方运行时假障碍的高优先级调查方向。
- `VERIFIED (live ESDF channel/schema, 2026-08-28)`: fusion 以约 6.6--7.5 Hz
  发布 `esdf_pointcloud_serialized`，类型为
  `galbot.perception_proto.EsdfGrid`；订阅者是
  `service_navigation_plan` 和 `service_motion_plan`。消息字段已从当前 protobuf
  核实为 `header`、`voxel_size_m`、`voxel_count_x/y/z`、`origin_point`、
  repeated float `voxel_distances`、`current_pose`和 `offset_per_voxel`。另有
  `esdf_debug_pointcloud` (`TsdfGrid`)、`tsdf_pointcloud_serialized`和零拷贝
  `esdf_pointcloud` 出口。系统自带 `embosa_topic_tool`，因此可以不修改
  fusion/PNS 服务，通过新的只读订阅者将 `EsdfGrid` 桥接到 RViz2。
- `VERIFIED/DOCUMENTED (navigation box API boundaries, 2026-08-28)`: 官方 SDK
  changelog 和当前 fusion 服务表明，`add_bounding_box()` 通过
  `galbot_fusion_add_box` 进入 `galbot_fusion_main` 的 points-filter-box 链，在点云
  融入 nvblox TSDF/occupancy/ESDF 之前过滤与携带箱体区域对应的融合点；
  因此会影响之后同时供 PNS 和 Motion 订阅的 `EsdfGrid`，但不增大机器人
  碰撞外形。`attach_box_to_link()` 不改变 LiDAR、fusion、nvblox 或 ESDF；它在
  导航/PNS 碰撞场中向指定 link 附着一个会随 link 运动的箱体几何，
  使其与环境 ESDF 参与碰撞判定。携箱时两者互补：前者防止箱体自观测点
  被当成外界障碍，后者保留携带物的真实碰撞外形。当前空载前方异常不是
  “必须先 attach 箱体”的问题，不应在尚未定位异常体素前用任意
  bounding box 遮蔽现象。新增/删除过滤框对已融合体素的追溯清理时序仍待实机对照验证。
- `VERIFIED (user-run forward reachability probe, 2026-08-28)`: 定位稳定在
  约 `(0.4157,-0.0996,yaw=-1.58)` 时，前向 `0.10--0.60 m` 的 6 个目标各三次
  检查全部可达（18/18 true）；`0.80,1.00,1.20 m` 各三次全部不可达
  （9/9 false），无混合结果。稳定边界位于 `0.60--0.80 m`。这排除了该次
  是偶发查询/启动故障，并证明存在可重复的运行时可达边界。本次未运动，
  也未修改 bounding box 或 attachment。
- `VERIFIED (user-run four-direction probe, 2026-08-28)`: 前方 0.60/0.70 m
  稳定可达、0.80 m 稳定不可达；后方和左侧 0.60/0.70/0.80 m 全部稳定
  可达；右侧三个距离全部稳定不可达，无混合结果。对 20 个底盘原生碰撞球
  进行离线静态 ESDF 对照：前方 0.80 m 目标最小静态余量仍约 `0.76 m`，
  无法解释拒绝；右侧 0.60/0.70/0.80 m 的最小静态余量约为
  `+0.029/-0.060/-0.128 m`，与靠近静态墙体一致。因此当前证据显示至少两种
  效应叠加：机器人右侧的真实静态边界，以及前方仅出现于运行时/局部 ESDF
  的额外边界。
- `OBSERVED (user output and later read-only SSH check, 2026-08-31)`: 用户一次
  `relative --x 1.0` 尝试在 SDK 初始化、可达性检查和导航提交之前即因
  `/home/galbot/ie_lab/control.lock` 被占用而 fail closed；该输出不能作为
  “携箱导致导航失败”的证据。随后只读检查时锁文件已为空、`lslocks` 未显示
  持有者，也没有运行中的 `s1_navigation_cli.py`，说明占用已释放；未结束进程或
  删除锁文件。
- `IMPLEMENTED AND LOCALLY TESTED; DEPLOYED BUT NOT RUN ON S1 (2026-08-31)`:
  导航 CLI 新增 `payload-status-4317`、`payload-register-4317` 和
  `payload-remove-4317`。固定配置来自当前生产工具
  `host_s1_navigate_unload_v2.py`：4317 实体碰撞箱 `0.40 x 0.30 x 0.175 m`、
  融合过滤箱 `0.60 x 0.50 x 0.375 m`、父坐标系 `base_link`、标签 `4317`，
  并复用其完整 7D 位姿和四个末端忽略碰撞 link。该配置只适用于生产脚本注明的
  “抓取后上抬 100 mm、底盘沿自身 X 方向后退 50 mm”姿态；姿态不同时必须
  重新测量，不能复用。
- `IMPLEMENTATION SAFETY (2026-08-31)`: 登记命令先精确确认，再调用
  `add_bounding_box()`、通过 `get_bounding_box()` 验证 tag，随后调用
  `attach_box_to_link()`；附着失败会尝试回滚融合过滤框。登记会保留到显式
  `payload-remove-4317`，后者同时调用 detach/remove 并验证过滤框消失。
  三个命令均不切换控制器或发送底盘、机械臂、夹爪、升降运动，但会改变
  fusion/PNS 导航状态。9 项本地伪 SDK 测试通过；修改后的远端脚本 SHA-256
  为 `928dc9147af86dd7cb660d003c6f9c7a912cb51c1df08a8cd0aaa39840cd32c4`，
  原版备份为
  `/home/galbot/Lsy03/navigation_tests/s1_navigation_cli.py.before_payload_4317_20260831`。
  尚未在真机调用三个新子命令，也未验证 SDK 1.9.0 的持久化/清理运行时语义。
- `VERIFIED (user-run S1 payload registration, 2026-08-31)`: 用户确认当前 4317
  箱体处于记录的“抓取后上抬 100 mm、底盘沿自身 X 方向后退 50 mm”姿态，
  随后运行 `payload-register-4317` 并输入数值绑定的确认口令。
  `add_bounding_box()` 返回 `(true, "SUCCESS")`，`get_bounding_box()` 随即
  回读到 tag `4317`、父坐标系 `base_link` 和预期过滤框；
  `attach_box_to_link()` 也返回 `(true, "SUCCESS")`。CLI 报告
  `ok=true`、`outcome=payload_registered`，且没有发送控制器切换或任何
  底盘、机械臂、夹爪、升降运动命令。登记前定位有效，地图位姿约为
  `(0.5780,0.3887,yaw=-0.0443 rad)`，导航状态为 `UNKNOWN`。融合回读中的
  末位差异符合 float32 精度转换。下一步仍需在新的 SDK 会话中用
  `payload-status-4317` 验证过滤框跨会话保持；公开 API 仍不能查询 PNS
  attachment 列表，因此 attachment 的跨会话持久性只能由登记返回、后续
  PNS 行为和最终 detach 结果共同验证。
- `VERIFIED (user-run cross-session filter query, 2026-08-31)`: 用户随后在新的
  SDK 会话运行 `payload-status-4317`，回读 `filter_registered=true`，列表中
  tag `4317`、`base_link` 父坐标系、`0.60 x 0.50 x 0.375 m` 过滤尺寸和完整
  7D 位姿均与登记结果一致，确认 fusion 过滤框至少跨本次 SDK 客户端退出保持。
  本次查询没有发送运动、控制器切换、bounding-box 变更或 attachment 变更。
  PNS attachment 仍因公开 API 缺少 getter 而无法独立查询。
- `VERIFIED (user-run carried-payload forward probe, 2026-08-31)`: 在 fusion
  已跨会话回读 tag `4317` 过滤框之后，用户从地图位姿约
  `(0.5736,0.3928,yaw=-0.0447 rad)` 对 `base_link` 正前方 1.0 m 目标执行
  三次只读 `check_path_reachability()`。目标换算到 map 约为
  `(1.5726,0.3481)`，三次均返回 false（每次约 0.101 s），分类为
  `stably_unreachable`。本次未切换控制器、未提交导航、未改变过滤框或
  attachment，也未产生运动。该结果证明当前 PNS 仍拒绝此目标，但不单独证明
  拒绝来自箱体自点云；过滤框已存在，而 attach 后扩大的碰撞几何、底盘原生
  碰撞球、静态/运行时 ESDF、地图/TF 或目标有效性条件仍需用同一时刻 PNS
  日志区分。在查明原因前不得绕过预检查或关闭碰撞检测。
- `VERIFIED (authorized read-only PNS/fusion log inspection, 2026-08-31)`:
  对上述三次查询的同一时刻日志核查表明，PNS 已成功附着
  `sdk_box_4317`，三轮均记录 `has object 1: sdk_box_4317`；但直接报碰撞的
  是底盘原生 `omni_chassis_base_link` sphere 11，而非箱体对象。该球半径
  `0.20 m`，三次 ESDF 距离分别约为 `0.164164/0.163081/0.191371 m`，均在
  目标姿态碰撞。三次判定均为 `start=1, goal=0, path_collision=0,
  has_solution=1`。
- `VERIFIED/INFERRED (same logs and geometry, 2026-08-31)`: PNS 在每次查询中
  使用约 120 ms 前的新 ESDF 帧并记录 `cache esdf`，同时反复报告
  `global esdf map is nullptr`。因此碰撞值高度确定来自
  `galbot_fusion_main`/NVIDIA nvblox 持续发布的运行时局部 ESDF，而不是磁盘
  全局 ESDF。内部字段 `evaluate at dyn map: 0` 不能再解释为“使用磁盘静态
  ESDF”；其精确厂家语义仍待验证。
- `HIGH-CONFIDENCE ROOT-CAUSE INFERENCE (2026-08-31)`: 目标 sphere 11 中心
  约为 `(1.34808,0.34652,0.68720)`；将当前登记箱体中心从 `base_link`
  换算到 map 得约 `(1.30258,0.36794,0.64111)`，两者仅相距约 `0.0682 m`。
  sphere 中心在箱体局部轴下的偏移约
  `(-0.0182,-0.0459,0.0471) m`，位于实体箱半尺寸
  `(0.20,0.15,0.0875) m` 内。fusion 日志只记录 14:05 新增过滤框，没有
  记录追溯清除已有 TSDF/ESDF 体素。因此最符合证据的根因是：登记过滤框前
  已融合的当前箱体体素仍残留在运行时 nvblox 场中；PNS 假设底盘前进 1 m
  后，原生 sphere 11 落入这块旧世界坐标箱体区域而拒绝目标。详见
  `experiments/20260827_s1_navigation/pns_payload_probe_20260831.md`。在没有
  经审查的清理机制前，不得通过关闭碰撞、解除携带物模型或任意清图绕过。
- `VERIFIED (current fusion ELF/stub/log inspection, 2026-08-31)`:
  SDK 1.9.0 stub 将 `box_tag` 转为 SDK 标记名称；fusion 二进制注册了独立的
  `galbot_fusion_add_box/get_box/remove_box/clear_esdf` 服务。
  `AddBoxInfoServerCallback` 将 box 反序列化、校验并存入活动 BoxInfo；
  `TransformBoxInfoToBaseLink` 使用 TF，`SetPointsFilterBoxs` 把 box 传入
  TSDF/occupancy/color projective integrator。ELF 明确包含三类
  `filterPointsWithBoxes`、`filterPointsWithMeshAndBoxes` 和对应 CUDA kernel，
  证明 box 是在点云进入 nvblox 集成前过滤输入点。
- `VERIFIED IMPLEMENTATION BOUNDARY (2026-08-31)`: 清理路径是独立的
  `galbot_fusion_clear_esdf`、`ClearESDFServerCallback` 及 nvblox clear 函数。
  AddBox 回调的运行日志和反汇编均未显示调用清理路径。因此
  `add_bounding_box()` 不能解释为追溯删除已有 TSDF/ESDF 体素；它只对登记后
  的输入点过滤。clear 服务的请求 schema、全局/局部作用域和恢复语义尚未
  核实，不得调用。详细链路和同步验证方案见
  `docs/s1_add_bounding_box_runtime_analysis_20260831.md`。
- `IMPLEMENTED AND LIVE-VERIFIED (2026-08-31)`: 三路原始 LiDAR 实时RViz桥已在
  `experiments/20260831_s1_lidar_live_rviz/` 和现有 `s1_rviz_demo` 包中实现。
  S1端使用低层 embosa 被动订阅三路
  `galbot.sensor_proto.PointCloud2` 以及 `/embosa_tf_static`、`/embosa_tf`，
  不导入Galbot SDK、不创建S1 publisher；实时TF把三路XYZ变换到
  `base_link`，再进行10 m限距、最多2万点和约2 Hz限频，通过SSH紧凑二进制流
  送至本机ROS 2。三路输入均约10 Hz、每帧19,968点和约519 KB；本机实际输出
  约1.65--1.73 Hz/路，底盘一帧限距后19,684点。
- `VERIFIED (local live RViz, 2026-08-31)`: 本机隔离 `ROS_DOMAIN_ID=84` 下已
  同时发布 `/s1/lidar/chassis_raw`、`/s1/lidar/head_raw` 和
  `/s1/lidar/back_raw`，frame均为 `base_link`。RViz以绿色/橙色/青色分别显示
  底盘/头部/后部原始点云；QoS已改为本机reliable以匹配RViz。此前无GUI验证
  停止后确认远端临时进程消失且厂家LiDAR订阅者列表恢复，无reader遗留。
  后续已删除旧关节快照发布器，并把S1 `/embosa_tf` 动态TF以10 Hz上限同步
  转发到本机；官方URDF仅提供mesh与固定关节。RViz固定坐标改为 `map`，
  `tf2_echo` 实际验证 `map -> base_link` 和 `map -> left_arm_link7` 连续更新。
  一组底盘样本约为 `(2.25,0.60,yaw=-2.48 rad)`，连续样本随实时定位轻微变化。
  因此当前窗口中的底盘全局位姿、升降柱、头部、双臂和轮组动态TF来自S1实时
  数据；但各LiDAR帧和不同TF消息仍是异步采样，不构成原子级全身同步快照。
- `IMPLEMENTED AND LIVE-VERIFIED (2026-08-31)`: 实时RViz增加
  `/visualization_marker_array` 的4317携带物标记。黄色半透明体/线框是
  `add_bounding_box()` 的 `0.60 x 0.50 x 0.375 m` fusion过滤框；青色是
  `0.40 x 0.30 x 0.175 m` 实体/PNS碰撞箱；红色是用户提供的官方示例
  `0.40 x 0.30 x 0.28 m`、中心 `[0.45,0,0.25]`、单位四元数。4317两个框
  严格复用CLI记录的完整7D位姿，仓库测试已断言YAML与CLI常量完全相同。
  marker的frame是 `base_link` 且 `frame_locked=true`，因此在RViz的 `map`
  固定坐标下随实时 `map -> base_link` 一起运动。实际DDS检查确认marker发布者1、
  RViz订阅者1。
- `IMPLEMENTED AND LIVE-CHAIN VERIFIED (2026-09-01)`: 导航CLI的4317配置已从
  固定 `base_link` 旧姿态改为相对
  `left_arm_end_effector_mount_link` 的刚性携箱姿态，profile为
  `4317_left_mount_20260831_193312_191`。相对7D位姿来自该次已成功执行的
  `dual_lift_up_100mm_target.json` 与当前S1 GE103v1 mount/TCP几何，矩阵往返
  误差约 `1e-17`；过滤框仍为 `0.60 x 0.50 x 0.375 m`，实体/PNS碰撞箱仍为
  `0.40 x 0.30 x 0.175 m`。登记前新增父frame列表与
  `base_link <- left_arm_end_effector_mount_link` TF检查，添加后按tag、尺寸、
  位置、四元数和父link完整回读验证；确认口令改为
  `REGISTER_NAV_PAYLOAD_4317_LEFT_MOUNT`。
- `VERIFIED (isolated local ROS and passive live S1 stream, 2026-09-01)`:
  RViz MarkerArray与CLI使用同一YAML/profile；黄色过滤框和青色实体箱消息均为
  `frame_id=left_arm_end_effector_mount_link`、`frame_locked=true`。隔离
  `ROS_DOMAIN_ID=86` 的无GUI集成检查同时收到三路LiDAR帧，并连续解析
  `map -> left_arm_end_effector_mount_link`。测试节点与本次1 Hz远端reader均正常
  退出；S1上另有一个10:10启动、参数为2 Hz/20000点的既有reader，早于本次测试，
  未被结束或修改。该profile仅在箱体相对左末端保持记录的刚性变换时有效；滑移、
  释放、重新抓取或抓取几何变化后必须移除或重算。
- `IMPLEMENTED AND LOCALLY TESTED (2026-09-01)`: 导航CLI已移除全部运行时
  `input()`字符确认。所有会改变fusion/PNS/定位状态或产生真实底盘运动的命令
  改为在原始命令行中显式要求 `--execute`，未提供时在SDK初始化前fail closed；
  只读命令不需要该标志。`navigate`和`relative`新增
  `--omni-plan true|false`，默认保持 `true`，该布尔值同时写入结果记录并原样传给
  `navigate_to_goal_v2()`；碰撞检测仍固定开启且没有关闭选项。16项本地伪SDK/
  参数解析测试通过。该修改不构成任何真机运动授权，具体运动仍需命令级的新鲜确认、
  现场净空、低速和物理急停条件。
- `IMPLEMENTED AND LOCALLY FAULT-INJECTION TESTED (2026-09-01)`: 针对一次
  `navigate_to_goal_v2(is_blocking=True, timeout=300)` 期间终端已显示多个`^C`但
  Python进程仍阻塞的问题，`navigate`与`relative`均已改为
  `is_blocking=False`提交，并在Python中每0.20 s轮询位姿、导航状态和到位标志；
  约每秒输出一次进度。SIGINT/SIGTERM首次到达后立即调用`stop_navigation()`，
  在停止RPC和最多5 s状态确认期间忽略重复信号；超时走同一停止路径，若未确认停止，
  SDK会话清理仍会二次尝试stop。伪SDK故障注入验证了运行中Ctrl+C返回130且只发送
  一次stop，以及超时自动stop；源码中已无阻塞导航调用。尚未用真实底盘运动验证该
  新停止路径，实体急停仍是运动异常时的最高优先级措施。
- `IMPLEMENTED AND LOCALLY TESTED (2026-09-01)`: `navigate`与`relative`新增
  两个默认关闭、必须成对出现的显式开关：`--add-bounding-box`和
  `--attach-box-to-link`。只传一个会在SDK初始化前fail closed；两者都不传保持
  既有导航行为。两者都传时要求起始tag 4317完全不存在，在同一control.lock和
  SDK会话中依次完成导航空闲/定位/左末端TF检查、add、完整profile回读、attach、
  三次可达性检查和非阻塞导航。即使已有tag配置正确也拒绝自动模式，因为公开API
  无法证明PNS attachment仍存在；登记后状态保留到显式remove。19项伪SDK测试覆盖
  参数成对约束、成功链、重复tag拒绝、attach失败回滚、外部omni_plan、Ctrl+C和
  超时stop。尚未运行真机自动登记导航链。
- `IMPLEMENTED AND LOCALLY FAULT-INJECTION TESTED; NOT DEPLOYED (2026-09-02)`:
  用户运行当前CLI时，fusion add及完整回读成功，但
  `attach_box_to_link()`返回`WAIT_INITIALIZED`，随后过滤框按设计回滚；官方
  SDK将该状态明确解释为PNS服务尚未准备。旧字符确认版成功、无交互版失败以及
  同一当前版后续偶发成功共同支持“移除人工确认后暴露PNS就绪竞态”的高置信度
  判断，而不是箱体profile或父link失效。新本地版本仅对`WAIT_INITIALIZED`每
  0.25 s重试、最长5 s；其他错误立即回滚。超时或失败后会再次查询过滤框并明确
  报告回滚是否验证成功，错误JSON保留全部attach尝试。map目标距离门禁也已提前到
  自动add/attach之前；携带物可达性检查仍保留在登记之后。23项伪SDK测试通过，
  覆盖延迟后成功、持续等待超时、非瞬态错误、回滚不可验证及距离门禁顺序。修改前
  CLI已备份为
  `experiments/20260827_s1_navigation/s1_navigation_cli.py.before_pns_attach_ready_retry_20260902`，
  SHA-256为`7bc3cc5631955c2977a747eb219baceb495d7504e22bdce879917d977d07e4fa`。
  本次未连接或部署到S1，未调用真实SDK、改变fusion/PNS状态或发送运动。
- `VERIFIED (read-only S1 deployment audit, 2026-09-02)`: 经用户明确授权，
  通过既有 SSH 复用连接只读核对
  `/home/galbot/Lsy03/navigation_tests/s1_navigation_cli.py`。远端文件大小为
  `70,247 bytes`，修改时间为 `2026-09-02 14:50:22 +08:00`，SHA-256 为
  `053a4818e12b7f57374a36d509d8a63ee2a23e909c978ab1d0064cee6a46c2bb`，
  与当前仓库脚本及同事使用手册标注完全一致。远端只运行了 argparse
  `--help`，确认 9 个子命令、`--execute`、`--omni-plan` 和成对箱体开关；
  没有进入任何 handler 或初始化 SDK。受管启动器仍指向
  `s1-sdk-1.9.0-py38` 并设置 `S1_SDK_VERSION=1.9.0`。当前 1.9.0
  `__init__.pyi` 中核心导航/箱体签名、`(success,status_string)` 返回形式、
  `NavigationTaskStatus` 枚举和 `SWERVE_CHASSIS_POSE_CTRL` 与 CLI 调用匹配。
  本次未查询定位/箱体运行状态，未调用控制器、导航、重定位、注册、取消注册
  或 stop，也未产生任何物理运动。
- `RECOVERY RECORD (user-provided runtime log and procedure, 2026-09-01)`:
  实时桥启动时会先检查本机 SSH ControlPath；日志
  `FileNotFoundError: SSH ControlPath does not exist:
  /tmp/s1_codex_mux_20260831_lidar` 表明复用主连接已过期或 socket 已被清理，
  因而 `live_lidar_ssh_bridge.py` 直接退出。其直接后果是三路点云、S1实时TF
  和 `map -> base_link -> 左臂末端` 链缺失，左末端黄色/青色框无法解析，RViz
  只剩无实时状态的 RobotModel。恢复顺序固定为：停止残缺旧 Launch，重新建立
  `ControlPersist=2h` SSH Master 并用 `-O check` 确认 `Master running`，重新上传
  `/tmp/s1_lidar_stream_20260831.py`，再以 `ROS_DOMAIN_ID=84` 启动单个
  `view_live_lidars.launch.py`；完整命令见
  `experiments/20260831_s1_lidar_live_rviz/README.md`。不得保留旧 Launch 后直接
  重启，否则会出现两个 MarkerArray 发布者，导致黄色/青色框横跳。S1 重启或
  `/tmp` 清理后还必须重新上传临时脚本。`unrealistic inertia` 警告在本次日志
  诊断中不是该故障原因。此条是恢复流程记录，不代表本次文档更新实际建立了
  SSH 或执行了机器人命令。
- `IMPLEMENTED AND LOCALLY ROS-VERIFIED (2026-09-01)`: 规范
  `s1_rviz_demo/view_live_lidars.launch.py` 已默认叠加当前
  `room0804` 的二维占据地图和三维静态 PCD。本机发布器从
  `experiments/20260827_s1_navigation/s1_room0804` 读取资产，分别在
  `/map` 发布 `800 x 220`、`0.05 m/cell` 的
  `nav_msgs/OccupancyGrid`，以及在 `/s1/map/global_cloud` 发布默认
  stride 10 的 `sensor_msgs/PointCloud2`（217,723 个有限 XYZ）。两者
  `frame_id=map`、QoS 均为 reliable + transient-local，RViz 默认启用
  `room0804 2D Map` 和紫色 `room0804 Global PCD`。话题类型、尺寸与
  QoS 已在隔离 `ROS_DOMAIN_ID=184` 中实测；`colcon build` 和 4 项
  发布器测试通过。发布器仅读本地资产，不修改 S1 地图/定位，
  不导入 Galbot SDK 且不发送任何运动或控制指令。
- `VERIFIED (authorized passive S1 TSDF inspection/capture, 2026-09-02)`:
  当前 `galbot_fusion_main` 以约 7.1--7.8 Hz 发布
  `tsdf_pointcloud_serialized`，类型为
  `galbot.perception_proto.TsdfGrid`，QoS为 `LARGE_DATA_TRANSPORT`、best effort、
  keep-last depth 3、volatile；当前 `service_security_manager` 也是订阅者。
  一帧TSDF与 `/galbot/mes/global_pose` 在同一被动embosa node中捕获，header时间戳
  均为 `1788311956000000000 ns`、差值0.0 ms。原始TSDF为934,839 bytes、
  SHA-256 `402ec2ac27353e52a501444768597bf3203ecc1095de5b9ec6e2c4b0407e2901`；
  未导入/初始化Galbot SDK，未创建publisher、调用服务、改变配置或发送运动。
- `VERIFIED (current TsdfGrid schema/runtime consumer, 2026-09-02)`:
  当前消息顶层字段为header、`voxel_size_m`、packed repeated float
  `voxel_data`和`current_pose`，不是完整稠密规则体素数组。当前安全服务二进制
  明确按 `std::array<float,5>` 读取，并保留第4项 `<=0` 的记录作为障碍点；
  前3项为XYZ，第4项据此作为 `tsdf_distance` 发布。第5项精确厂家语义没有
  已安装source/schema支撑，当前只标记为 `auxiliary`，不得称为权重。捕获帧
  voxel size为0.05 m、46,736点、source frame为`base_link`；使用同消息内嵌
  current pose变换后，map范围约为x `[-2.425,7.925]`、y `[-4.775,4.275]`、
  z `[0.025,2.075]` m。
- `IMPLEMENTED AND OFFLINE ROS-VERIFIED (2026-09-02)`: 规范 `s1_rviz_demo`
  已加入 `view_captured_tsdf.launch.py`、`tsdf_frame_publisher.py` 和
  `captured_tsdf.rviz`。默认在map frame发布可靠/transient-local的
  `/s1/tsdf/surface`（46,736点）、`/s1/tsdf/slice`（726点）及诊断Marker，
  并叠加room0804二维地图、静态PCD和同步底盘位姿。无GUI隔离ROS检查确认消息
  类型、QoS和点数，ROS包累计9项测试通过；离线launch不连接S1。
- `IMPLEMENTED AND BOUNDED LIVE-CHAIN VERIFIED; DEFAULT OFF (2026-09-02)`:
  新增S1端 `s1_tsdf_stream.py` 和本机 `live_tsdf_ssh_bridge.py`，可在现有
  `view_live_lidars.launch.py` 中以 `publish_live_tsdf:=true` 显式开启1 Hz
  map-frame TSDF表面/0.40 m切片和stale诊断。端到端实测连续输出约48,000个
  表面点和3,200个切片点，停止后远端reader消失。但厂家Python/embosa
  large-message reader稳态占约59--64%单核和410--450 MB RSS；降低轮询与只在
  1 Hz复制消息未消除该成本，且当前镜像没有可用embosa/TsdfGrid C++头文件。
  因此该桥只允许短时受监督诊断，保持默认关闭，不能宣称为低负载常驻实时桥。
  详细命令、证据边界与哈希见 `experiments/20260902_s1_tsdf_rviz/README.md`。
- `SAFETY BOUNDARY`: 文档中的 `move_whole_body_joint_zero()`、
  `zero_whole_body_and_base()` 和“零/home”描述不构成现场安全恢复位。
  不得在没有完整运动前快照、型号/版本匹配依据和新鲜分步确认时调用。

## Mode 00 一键拆垛当前部署只读审计 — 2026-09-03

用户明确授权后，Codex 通过用户建立的 SSH 复用连接只读查看
`/home/galbot/ie_lab/projects/dual_arm_v5/workspace/s1_sjtu_0806`。未运行
任何项目 Python、Docker、SDK、规划、定位、导航或运动命令；远端未修改。

- `VERIFIED (current S1 source)`: 当前入口
  `scripts/run_s1_mode00_one_click.py` 不带参数时默认调用主流水线
  `--execute --unattended`，即默认真实运动并自动跳过每阶段人工口令。
  只有显式 `--dry-run` 才是无动作路径；该 dry-run 仅核验文件、
  SHA-256 批准清单和流程定义，不检验当前服务或机器人状态。
- `VERIFIED (current S1 source)`: 主链是
  `配置/镜像预检 -> 定位 -> 腰部 H4 0.420 m -> 双臂 SAM 姿态 ->`
  `右腕 RGB-D -> SAM3/LingBot 粗选 4317/H4 -> 底盘到 0.80 m 观察位 ->`
  `FDP 双臂观察姿态 -> 右腕 RGB-D -> SAM3/LingBot/ROI/FoundationPose++ ->`
  `双臂目标 -> 开爪 -> 预抓 -> 双侧内收 100 mm -> 合爪 -> 手臂上抬 100 mm ->`
  `腰部同时从 0.420 m 升到 0.520 m 并持箱导航 -> 高位张爪释放 ->`
  `双臂回 SAM -> 底盘回 SAM`。不执行 `put/down` 或释放后外撤。
- `VERIFIED (current S1 source)`: 感知使用右腕对齐 RGB-D；粗选和精感知均用
  Thor 上的 SAM3 与 LingBot-Depth，精感知再调用工作站的
  FoundationPose++。捕获门禁检查 RGB/深度时间差、有效深度、内参、
  `base_link <- camera` 时刻锁定变换和变换一致性。精感知必须输出真实
  FoundationPose 的 4x4 物体位姿，且目标为 4317/H4。
- `VERIFIED (current S1 source)`: 抓取目标不是纯 FDP 输出。它先将 FDP mesh 坐标
  转为 4317 语义长/宽/高轴，固定 180° 对称符号，然后叠加
  2026-08-06/13 操作员标定：左 TCP `[-35,-50,0] mm`、右 TCP
  `[-35,+50,0] mm`，两侧 TCP RPY 强制为零。抓取点由预抓点沿物体
  接近轴对向内收 100 mm，提升点再沿 `base_link +Z` 加 100 mm。
- `VERIFIED (current S1 source)`: IMC 的 `solve_ptp/solve_lin` 以
  `check_collision=false` 生成单臂路径，之后将左右路径时间对齐，并使用
  SDK 临时挂载两个 GE103v1 对所有离散样本做机器人本体/自碰检查。
  这一检查明确没有把实体箱体或现场环境加入 Motion 场景，因此不能
  证明夹爪/手臂与货垛和环境的净空。
- `VERIFIED (current S1 source)`: 带载运输以左右提箱 TCP 中点和历史操作员
  教导的卸货箱体 map 位姿反算当次底盘目标。腰部上升与底盘导航
  并发，速度配置为 `[0.2,0.2,0.2]`、`omni_plan=false`。当前活跃链路
  没有调用 `add_bounding_box()` 或 `attach_box_to_link()`，而是显式传入
  `enable_collision_check=false`。释放后底盘回 SAM 时恢复导航碰撞检查。
- `VERIFIED (current S1 source)`: 顶层有全局 `control.lock`、固定 Docker image ID、
  批准源文件哈希、每次 run 的源码/配置快照、冻结计划 SHA 绑定、当前
  关节状态偏差、限位、夹爪接触和导航到达门禁。但当前
  `prepare_runtime()` 已刻意改为“警告后忽略已有持箱状态标记”，而不是拒绝新任务。
- `VERIFIED (current S1 repository boundary)`: 这一部署树整体被上层
  `/home/galbot/ie_lab/projects/dual_arm_v5/.gitignore` 的 `workspace/` 规则忽略。
  当前 Git HEAD `1735aacee360be12b67b68a6f3aa460058c8b4e7` 不包含这些入口、
  主流水线或批准清单；运行时 SHA 清单可以检测现场漂移，但不等于
  可解析的 Git 版本追溯。
- `VERIFIED (current run artifacts)`: 最新完整 `RESULT.txt` 为
  `s1_mode00_sam_to_sam_20260901_110253_413`，记录于 2026-09-01 11:07:54
  成功高位释放并返回 SAM，`put_executed=false`。之后的
  `s1_mode00_sam_to_sam_20260901_163430_580` 已完成抓取与提升并进入
  带载运输，但在运输早期生成软件停止产物且无 `RESULT.txt`；仅从
  当前只读产物不能确认触发停止的外部原因。

`HIGH-RISK CURRENT LIMITATIONS`: 默认实机且 `unattended`、带载导航关闭碰撞、
启动时忽略未清理的持箱标记、高位直接张爪、未标定的 GE103 `effort`
语义、机械臂规划没有环境/箱体碰撞场景，以及部署源码未纳入 Git，都是
当前不能将该入口当作普适、无人监督生产系统的核心原因。

## SJTU 料箱几何位姿与 ICP 可用性只读核查 — 2026-09-03

用户明确授权后，Codex 通过用户建立的 SSH 复用连接只读检查
`/home/galbot/ie_lab/projects/dual_arm_v5/workspace/s1_sjtu_0806`。本次只使用
`find`/`grep`/`sed`/`nl`/`sha256sum`/`jq`/`awk` 查看源码与历史产物；
未运行任何项目 Python、Docker、SDK、ROS、规划、定位、导航或运动命令，
远端未修改。

- `VERIFIED (current S1 source)`: 对当前部署树中的 Python/C++/配置/文档
  搜索未找到 ICP、Open3D/PCL registration、FPFH、点到平面或其他物体点云
  配准实现/调用。IMC 中的 point-cloud provider 用于规划碰撞几何，
  `getNearestIK` 用于逆解，都不是 ICP。
- `VERIFIED (current S1 source)`: 当前粗感知是
  `SAM3 mask + LingBot depth -> mask 内点云 -> XY 俯视栅格 -> 最大轮廓 ->`
  `cv2.minAreaRect -> 最近尺寸模板 -> 4317 角点吸附`。它输出中心、
  yaw、顶面角点和 H4，当前只用于选箱和生成 0.80 m 观察位。
- `VERIFIED (current S1 source)`: 最近模板函数没有“不匹配”距离门限；
  只要 ROI 能拟合出矩形，它就会选择配置中最近的箱型。当前 vendor 感知包
  未包含单元测试、真值集、精度阈值或离线回归报告。
- `VERIFIED (current S1 source)`: 精感知门禁要求
  `foundationpose_real=true` 和 4x4 物体位姿。后续目标生成器又要求
  `source=fdp`、捕获时变换锁定且 `non_fdp_geometry_not_used=true`。因此 ICP
  现在不是可在配置中切换的后端；替换 FDP 必须新建位姿来源 schema、
  置信门禁、坐标轴语义转换、批准哈希和离线/规划验证。
- `VERIFIED (historical local SJTU source)`: 2026-06 本地交付源码
  `irmv_nd_workbin/workbin_detector_gal.py` 有一个更接近“模型对观测搜索”的
  `_chamfer_matching`/矩形边缘模板路线：它在 BEV 中对多箱型和
  `[-90, 90)` 内的 5° 角度网格用膨胀边缘与 `cv2.matchTemplate(TM_CCORR)`
  计数匹配。函数名称虽写 Chamfer，当前代码并未使用 distance transform，
  也不是 3D ICP；该空间/旋转遍历实现不在当前 S1 部署包中。
- `DOCUMENTED (historical SJTU slides)`: 《宁德-上层感知-讲解》第 1/4/6 页也描述了
  BEV 平面最大轮廓、外接矩形及二值边缘模板遍历位置/旋转打分；
  《宁德-位姿估计-讲解》第 1/3 页的抓取位姿主路仍是 FoundationPose/
  FoundationPose++，后者追踪使用前帧位姿、2D Cutie、深度和卡尔曼滤波，
  不是 ICP。
- `VERIFIED (current historical run artifacts)`: 对 8 个存在 `status=SUCCESS`、
  完整精感知产物的历史 run，在同一次 FDP 观测中将粗几何 ROI 与
  FDP 语义箱体位姿对比：XY 中心差平均约 `19.5 mm`、最大约
  `26.5 mm`；扣除 4317 半高 `87.5 mm` 后的 Z 中心残差平均约
  `-2.8 mm`；按 180° 对称归一后 yaw 绝对差平均约 `1.93°`、
  最大约 `4.71°`。这支持“几何初值可用”，但不证明“几何单独抓取已验证”，
  因为这些成功 run 的最终抓取目标仍来自 FDP。
- `ENGINEERING ASSESSMENT`: 若引入 ICP，当前最合理的方式不是“全 6D ICP
  单独替掉 FDP”，而是使用现有 ROI/矩形或历史边缘模板提供粗初值，
  对站立料箱约束 roll/pitch，对 0°/180° 对称候选分别做鲁棒、裁剪的
  point-to-plane ICP，只使用可见外壁/顶缘而排除箱内货物，并输出残差、内点率、
  覆盖率和两个对称解的差距门禁。它应先作为 FDP 的离线 A/B 对照或交叉校验，
  不应直接接入实机执行链。当前 `pyproject.toml` 只声明 NumPy/OpenCV/
  Requests/PyYAML，没有 Open3D/PCL 配准依赖。

## FoundationPose++ 无运动参考基线 — 2026-09-03

- `IMPLEMENTED AND OFFLINE-VERIFIED`: 新增
  `experiments/20260903_fdp_baseline`，并部署到 S1
  `/home/galbot/Lsy03/fdp_baseline`。该工具不导入 Galbot SDK、ROS、IMC、
  规划器、执行器或运动接口；默认只准备 FDP 请求，只有显式
  `--call-service` 才允许网络推理。
- `VERIFIED (current S1 source contract)`: 当前远程 FDP 首帧接口为
  `POST /first_frame_track`，载荷包含服务端 mesh 路径、PNG/base64 RGB、
  uint16 毫米 PNG/base64 深度、二值 PNG/base64 mask、3x3 `K`、
  `depth_scale=1000.0` 和 `return_vis`。返回要求 `ok=true`、有限 4x4
  `pose` 和可选 `vis_png_base64`；生产链将原始矩阵解释为
  `T_camera_from_fdp_mesh`。
- `VERIFIED (current S1 source contract)`: 4317 语义位姿由原始 FDP mesh
  位姿右乘固定 `T_fdp_mesh_from_4317_semantic` 得到，语义 +X/+Y/+Z 分别
  表示箱体长/宽/高；180° 对称规范使用“水平语义 +X 在 `base_link` 的 Y
  分量非负”。基准结果明确保存 raw camera、raw base、semantic camera、
  symmetry 前后 semantic base 和 canonical raw mesh 各矩阵，不包含 TCP
  人工偏移、预抓、内收、提升或任何执行目标。
- `VERIFIED (historical artifact limitation)`: 现有成功 run 保存了原始 RGB-D、
  内参、捕获时刻 `T_base_link_from_camera`、最终 ROI mask 和 FDP 位姿，
  但没有保存实际输入 FDP 的 LingBot 稠密深度或完整 HTTP 请求/响应。因此首个
  `mode00_20260901_110253_413_legacy_partial` 案例只能精确复核坐标规范化，
  不能声称逐字节复现历史 FDP 调用；工具对此默认拒绝服务推理。
- `OFFLINE VERIFICATION`: 本机和 S1 端 7 项单元测试通过。首个案例所有输入
  SHA-256 验证通过；规范化结果与原生产 `fdp_pose_lock.json` 的平移差约
  `3.93e-8 m`、旋转差约 `2.09e-6 deg`、矩阵最大元素差约 `3.13e-8`。
  请求归档已在不发送网络请求的情况下生成；非精确历史深度的默认拒绝门禁
  已验证，且拒绝时不创建输出目录。
- `SUPERSEDED ON 2026-09-04`: 上述等待 LingBot 数据发送授权的状态已由用户
  后续明确授权取代；2026-09-04 已完成一次新的实时只读采集和 SAM3/LingBot
  A/B，但尚未调用 FDP，结果也未冒充历史 FDP 复现。

## 右腕实时 RGB-D、SAM3 与 raw/LingBot ROI 基准 — 2026-09-04

- `IMPLEMENTED AND LIVE READ-ONLY VERIFIED`: 在
  `/home/galbot/Lsy03/fdp_baseline` 新增受共享 `control.lock` 保护的右腕单帧
  RGB-D 采集，以及 `--depth-mode raw|lingbot|both` 感知工具。实时采集只调用
  `GalbotRobot.init/get_rgb_data/get_depth_data/get_camera_intrinsic/
  get_sensor_extrinsic/get_transform/destroy` 和
  `GalbotMotion.init/get_robot_states`；未调用控制、规划或执行接口，产物明确
  `motion_commands_sent=false`。
- `VERIFIED (fresh capture)`: `right_wrist_20260904_01` 为 1280x720，RGB/深度
  时间差和捕获 TF 时间差均为 0 ns，原始深度有效率约 85.2151%；静态外参与
  捕获时刻 TF 的平移差约 0.002 mm、旋转差约 0.00266 deg。采集后共享锁可用，
  生产容器仍停止，未发现匹配的一键/控制进程。
- `VERIFIED (fresh Thor inference)`: 同一冻结 RGB 仅调用一次 SAM3，返回 12 个
  mask；同一冻结 RGB-D 仅调用一次 LingBot，报告 920,116 个有效点。凭据从
  既有生产配置在内存中读取，未打印或写入案例。首次 SAM3 解析因当前响应把
  整数数量放在 `masks`、实际 PNG 放在 `mask_png_base64` 而失败；失败目录保留，
  修正与回归测试后在 `retry1` 新目录成功，未覆盖失败证据。
- `VERIFIED (raw/LingBot A/B)`: 两条分支均按当前生产兼容排序选择 SAM index 3，
  均判断为 4317/H4。raw 与 LingBot 的选中中心相差约 55.7 mm、180° 对称 yaw
  相差约 12.69°、最终 mask IoU 约 0.8918；原始/补全深度有效率分别约
  85.22%/99.84%。这次实测说明 LingBot 不仅填补空洞，还会显著改变 ROI
  三维中心与 yaw，不能把启用/禁用 LingBot 当作无影响的部署开关。
- `FAIL-CLOSED TARGET GATE`: raw 分支有 4 个、LingBot 分支有 2 个 4317/H4
  候选。当前生产兼容理由仍是“无参考点，使用 ROI 排序第一项”；视觉检查显示
  index 3 为画面最右侧开口箱，但目标身份并不唯一。因此两个不可变 case 均
  标记 `human_review_required=true`、`ready_for_fdp=false`，本轮未调用 FDP。
- `OFFLINE REPLAY VERIFIED`: raw 和 LingBot 两个冻结 case 均在不访问机器人、
  不调用网络服务的情况下复算出同一 ROI index、中心、yaw 和二值 mask；中心/
  yaw 差为 0，mask IoU 为 1.0。本地与 S1 两套 Python 环境 12 项测试通过。
  完整命令、产物哈希与结果见
  `experiments/20260903_fdp_baseline/RUN_20260904_LIVE_RGBD_SAM_LINGBOT.md`。

## FDP 解耦实验对话衔接 — 2026-09-07

本次读取了以下任务记录，并与本地 baseline 文档和实现核对；未连接机器人，
未采集新数据或调用推理服务。

- `9_3 分析箱体6D位姿流程输入输出`
  （`01a06a1a-6375-7013-b78d-2c64d17861ca`）。
- `9_5 继续分析箱体6D位姿流程`
  （`01a06f1a-06fd-70d3-b3ed-abf9d282cf2b`）。
- `9_5 分析ICP替代箱体6D流程`
  （`01a06fc9-65d2-7c01-b8e4-3d26b3aa4f09`）。

- `SCOPE CONFIRMED (user diagram and local baseline)`: “FDP 剥离/解耦”指将
  近距离右腕 RGB-D → SAM3/深度/ROI → FDP → 4317 语义位姿从 Mode 00
  运动链中独立出来，保存可回放输入和中间产物。输出止于
  `T_base_link_from_4317_semantic`；图中的 FDP 双臂拍摄姿态是生产前置动作，
  不属于 baseline 自动执行范围；预抓目标和后续运动在实验边界之外。
- `STATUS RECONCILIATION`: 9 月 3 日对话图中的“尚未新鲜采集/SAM3/LingBot”
  已由上述 9 月 4 日记录取代。当前最新已记录实验已完成实时只读采集和
  raw/LingBot ROI 离线回放，但两分支目标不唯一，仍为 `ready_for_fdp=false`，
  未调用新帧 FDP。历史位姿坐标归一化复现不等于重新运行了 FDP 推理。
- `HISTORICAL SOURCE-AUDIT CONCLUSION; remote current state 待验证`:
  9 月 5 日续聊记录称，9 月 3 日部署快照的两次目标选择分别按
  `(-center_world[2], center_world[1])` 排序并取首项，未将粗选实例 ID
  传给精感知；同系代码存在 identity lock，但该一键链未接入。
  这属于已读取的历史审计结论，本次未重新核验远端源码。
  baseline 的严格唯一性门禁可在本地 `fdp_baseline/fresh_case.py` 核对，
  不应把它描述为原生产链已有的保证。
- `HISTORICAL DESIGN PROPOSAL; effectiveness 待验证`: 9 月 5 日 ICP
  讨论提出保留采集、分割、深度和 ROI，以约束几何/ICP 替换 FDP 位姿后端，
  或先作 FDP 的独立对照。它是后续方案，不代表 ICP 已实现、完成精度验证或
  接入生产。跨帧目标关联与位姿求解是两个不同问题；更换位姿后端本身不建立
  目标身份关联。

## 新帧 FDP 基线与人工目标确认 — 2026-09-07

- `VERIFIED (current live read-only capture)`: 用户确认 S1 人工摆位完成并静止后，
  getter-only 脚本保存 `right_wrist_20260907_01`，RGB-D 1280×720，
  RGB/深度与 TF/深度时间差均为 0 ns，原始深度有效率 86.5964%。
  未发送双臂、腰部、夹爪或底盘运动命令。
- `VERIFIED (explicitly authorized service calls and frozen replay)`: SAM3 和
  LingBot 各调用一次；10 个 SAM mask 中，raw/LingBot 均有 H4 候选 `[1,2]`，
  默认选择 index 1，原案例继续保留 `ready_for_fdp=false`。两分支中心差
  37.2254 mm、yaw 差 0°、mask IoU 0.936768；分别离线回放后中心/yaw 差为
  0、mask IoU 为 1。
- `USER-CONFIRMED FROZEN TARGET; locally implemented`: 用户看过本帧 ROI 图，
  明确选择原图右侧绿色开口箱 index 1。新增
  `right_wrist_20260907_01_lingbot_operator1` 案例，绑定用户原话、RGB、
  depth、mask、K、TF、mesh、ROI 报告及父 manifest 哈希。人工确认策略与
  自动严格唯一性分开，后者仍为 false；没有修改原多候选案例或生产逻辑。
  确认仅适用于该冻结帧，不授权后续帧、目标追踪或运动。新增确认工具与
  case 校验代码只在本机，未部署至 S1；15 项离线测试通过。
- `VERIFIED (one new FDP response)`: 用户单独授权后，本机向既有
  `10.34.216.13:7876/first_frame_track` 调用一次 FDP，HTTP 200，
  客户端耗时约 1.145 s，完整请求/响应和叠加图已保存。归一化语义中心为
  `[1.392452018, 0.255328013, 0.505903426] m`，yaw 约 91.288512°；
  刚体与高度轴门禁通过，未执行 180° 翻转。保存响应离线重算的全部矩阵
  逐元素一致。这取代“新帧 FDP 尚未调用”的最新实验停点；历史记录不改写。
- `UNRESOLVED ACCURACY`: FDP 与 LingBot ROI 顶面中心的 XY 差约
  **137.311 mm**，明显大于历史对照差异；用语义高度轴补偿半高后的顶面
  Z 差约 -6.116 mm。差异来源 **待验证**，ROI 不是测量真值，不能将其直接
  称为 FDP 误差。当前验证的是独立链路和回放合同，不是抓取精度、跨帧
  自动选箱、服务端 mesh/权重版本一致性或重复推理稳定性。

- `VERIFIED (FDP network diagnosis and retry)`: 首次本机 FDP 调用返回空 body
  的 HTTP 502；案例输入和哈希门禁均已通过。默认网络路径受本机
  `HTTP_PROXY/HTTPS_PROXY=192.168.42.129:7890` 影响；绕过代理访问
  `10.34.216.13:7876/health` 返回 HTTP 200，服务为 `local_fdp_4090`，
  RTX 4090，`import_error=null`。同一确认案例显式移除代理后重试成功，
  与此前成功归一化位姿的平移、旋转和矩阵差均为 0。FDP 与 Thor/S1 内网
  地址应直连，不需要代理；手册中的 FDP 命令已加入显式代理清除环境变量。

完整命令、结果、限制和产物哈希见
[`RUN_20260907_FDP_OPERATOR_TARGET.md`](../experiments/20260903_fdp_baseline/RUN_20260907_FDP_OPERATOR_TARGET.md)。

## FDP reproduction guide — 2026-09-07

完整使用手册为
[`FDP_DECOUPLING_USER_GUIDE.md`](../experiments/20260903_fdp_baseline/FDP_DECOUPLING_USER_GUIDE.md)，
第 5 节覆盖固定 RGB-D 整段重跑 SAM3/LingBot/ROI/FDP、第 6 节说明新帧采集。
手册明确 S1/本机的执行边界、独立 batch case-root、产物拷贝、人工确认只能
使用已物化的默认目标 mask，以及新批次需重新核对候选的限制。
文档中的 23 个 Bash 代码块通过语法检查；编写手册未新增实机或服务调用。
已有基线快捷复现说明保留在 `experiments/20260903_fdp_baseline/REPRODUCE.md`。
新增 `scripts/replay_saved_fdp_result.py`，校验冻结案例和请求/响应哈希，
重建请求内容并从已保存的 FDP 位姿重算语义坐标，无网络请求或 SDK 初始化。
当前帧全部矩阵逐元素一致，平移/旋转差为 0。此脚本是坐标后处理回放，
不重新运行 FDP 模型。手册分别提供纯离线、重新调用 FDP 和新帧采集命令，
并明确本机与 S1 路径、产物索引以及数据不随 Git 提交的边界。

本机 vendor 四项源码哈希与冻结案例一致；LingBot ROI 回放完全一致。
raw ROI 本机回放中心差为 `1.1920928955078125e-7 m`（约 0.000119 mm），
index/yaw/mask 一致，但超过脚本 `1e-9 m` 严格阈值，因此返回 false。
该值与 float32 舍入量级一致，具体来源待验证；未修改阈值或掩盖失败。
这不推翻此前 S1 原环境中两分支完全一致的结果。

## FDP 轻量替代与端侧化目标 — 2026-09-07

- `USER-STATED DIRECTION`: 用户明确希望使用 ICP 或其他轻量算法替代 FDP，
  使程序可在端侧 OrinX 运行。具体板卡、内存和软件运行时仍 **待验证**。
- `USER-CLARIFIED TASK OUTPUT`: 用户更关心箱体中心/方位或上沿平面/范围，
  用于计算两条短边上的夹爪抓取点，并要求先比较技术方案后自行选型。
  当前尚未选型；箱沿几何直接估计、ICP 精修、关键点和贴标路线的比较已补入
  下方方案文档。几何参考点不等于可直接执行的 TCP 位姿。
- `DESIGN ADVICE; NOT IMPLEMENTED`: 建议优先比较约束箱体几何与几何初值加
  ICP；固定输入后逐步验证 raw depth 和轻量分割，分别消除 FDP、LingBot、
  SAM3 的外部依赖。不能将仅替掉 FDP 称为整链已端侧化。
- 本次已读取 `9_7 分析FDP剥离解耦实验` 并核对 baseline 本地合同；未新增
  服务或实机调用。方案、精度边界、评估顺序和官方资料见
  [端侧轻量位姿建议](s1_lightweight_pose_replacement_advice_20260907.md)。

## 4317 箱口矩形与箱体中心离线实验 — 2026-09-07

- `USER-AUTHORIZED SCOPE`: 用户已选 B 方案，授权新建独立实验
  `experiments/20260907_bin_rim_pose`，仅复用本机人工确认冻结案例；随后允许
  使用直接箱体几何中心估计作同帧对照。此前“尚未选型”是较早讨论状态。
  当前仍禁止机器人访问、外部感知服务、生产抓取规则修改与 ICP；不进入
  多帧采集、抓取目标接入或真机执行。
- `IMPLEMENTED AND OFFLINE TESTED`: RGB 边缘加候选平面/固定尺寸矩形的 B
  后端、局部法向筛选箱壁的几何中心分支、4317 语义输出、拒绝门禁与诊断已实现。
  复用 baseline 纯文件加载和几何检查接口；20 项测试通过。源输入与对照哈希
  在运行前后相同，原案例/生产代码未改，未连接 S1 或调用任何服务。
- `REJECTED REAL-FRAME HYPOTHESIS`: B 候选箱口中心约
  `[1.397253,0.255183,0.573685] m`，yaw 93.183°；存在两个能通过四边检查的
  竞争平面，故 `ok=false / ambiguous_rim_planes`。箱壁分支候选箱体中心约
  `[1.390316,0.238961,0.505199] m`、yaw 91.614°，因缺边、内点比例不足和
  高度跨度与直立模型不相容而拒绝。两个正式位姿矩阵均为 null；数值候选
  只保留用于诊断，不能生成抓取目标。
- `ACCURACY UNVERIFIED`: B 与 FDP 的箱体中心三维差约 20.114 mm，箱壁
  分支约 16.520 mm；ROI/FDP 均非真值，差异更小不等于精度更高。当前算法
  本机单次约 1.808 s / 0.463 s，不代表 Orin 性能或已实现加速。
- `LOCAL SOURCE AUDIT; CURRENT SERVER UNVERIFIED`: 冻结 OBJ 原始轴/原点
  不能直接视为接口语义坐标；本地历史 FDP helper 使用 oriented bounding box
  居中变换后返回 pose。本轮按已冻结的 baseline 长宽高语义合同直接输出，
  不重复应用 mesh 轴转换；未核验当前服务端实现/mesh 是否与历史版本一致。

复现命令、诊断图、失败原因、输入/源码哈希和下一步建议见
[实验 README](../experiments/20260907_bin_rim_pose/README.md) 与
[第一轮报告](../experiments/20260907_bin_rim_pose/ROUND1_REPORT.md)。

### 原始 SAM index 1 / 最终 ROI mask 单变量消融

- `OFFLINE VERIFIED`: 在相同 RGB、LingBot 深度、K、捕获 TF、SAM index、
  尺寸、源码与配置下，只切换分析 mask。原 SAM 为 30,512 像素；最终 ROI
  为 31,948 像素，后者增加 1,436、删除 0，IoU 0.955052。
- `VERIFIED SOURCE CAUSE`: 本地 `roi_estimator.py` 哈希与冻结案例记录的生产
  源码哈希一致；其默认 `augment_mask=true`，会把尺寸模板四角投影后用
  `fillPoly` 并入 SAM mask。图中的锐利三角扩张来自该 ROI 后处理，不是原始
  SAM index 1。`sam_candidates_overlay.png` 本身还叠加所有候选、检测框和标签。
- `RESULT`: 箱沿候选的箱体中心仅相差 0.744 mm、yaw 相差 0.366°；最终 ROI
  让一条边的覆盖率从 41.7% 升至 58.3%，但两者仍因多平面歧义拒绝。箱壁
  分支候选中心相差 1.540 mm、yaw 相差 0.166°，拒绝原因完全相同。
  因此扩张影响门禁，但现有证据不支持把它认定为核心失败来源。
- `DIRECTION`: 后续轻量几何可用原 SAM mask 限定搜索范围；模板补全部分应
  标为先验并做深度一致性检查，不能作为直接观测。ROI/FDP 均非真值。

命令、两分支数值与诊断图见
[mask 消融报告](../experiments/20260907_bin_rim_pose/MASK_ABLATION_REPORT.md)。

## Documentation workflow

### FDP 轻量替代首批数据计划 — 2026-09-07

结合任务 `9_7 建议用轻量算法替代FDP`
（`01a07a67-a824-78c3-ac14-2ac2c473a3a8`）和当前本地产物盘点，现有多次
FDP/感知输出均源于同一 `right_wrist_20260907_01`，因此只有 **1 个独立
RGB-D 帧**，不能按输出目录数量计算数据集规模。

首批目标设为 15 个独立采集：12 个有效姿态样本和 3 个拒绝样本，其中前
10 个作为开发/调试集、后 5 个作为初版算法的留出集。覆盖静止重复、距离、
横向/斜视、另一物理目标，以及截边、遮挡、多目标歧义。该规模用于实现和
调试几何/ICP、解释 ROI/FDP 差异及初步留出检查；不足以证明生产成功率、
抓取精度或训练泛化网络。没有独立参考测量时，FDP 仅是参考后端，不是真值。
详细矩阵、每套必存产物和安全边界见
[`DATASET_COLLECTION_PLAN_20260907.md`](../experiments/20260903_fdp_baseline/DATASET_COLLECTION_PLAN_20260907.md)。

### D01～D12 原始冻结采集与第二轮侧壁分解 — 2026-09-07

- `READ-ONLY COPY VERIFIED`: 用户明确授权只读 SSH 检查和复制 D01～D12。
  D01 对应早先的 `right_wrist_20260907_01`，D02～D12 使用带编号目录；12 套
  均为 `ok=true`、`motion_commands_sent=false`，六个必需文件齐全，实际
  SHA-256 与各自采集结果一致，RGB/深度为 1280×720，帧同步差为 0。
  审计索引见 [批次索引](../experiments/20260903_fdp_baseline/CAPTURE_BATCH_D01_D12_20260907.json)。
- `DATA BOUNDARY`: D02～D12 目前只有原始 RGB-D、K、捕获 TF 和采集元数据；
  未运行/冻结 SAM3、LingBot、ROI、人工确认或 FDP。D11/D12 的场景分组未记录，
  不根据 RGB 猜测。不能跨帧沿用 D01 的 SAM index。
- `ROUND 2 OFFLINE RESULT`: 新增多平面侧壁分支，在 D01 已确认案例中分解
  7 个平面，找到三面且包含一组相对面的固定尺寸候选。诊断中心约
  `[1.398724, 0.236702, 0.494088] m`，yaw 约 `89.359°`；因三个匹配面的
  中心 Z 区间存在约 2.50 mm 空隙，正式结果拒绝为
  `multiplane_wall_heights_inconsistent_with_model`。FDP 仍非真值。
  详见 [第二轮报告](../experiments/20260907_bin_rim_pose/ROUND2_REPORT.md)。
- `D01 DEPTH ABLATION`: 固定人工确认 mask/K/TF，仅将 LingBot 深度换成 raw
  深度时，raw 分解出 10 个平面但无法形成三面且含相对面的尺寸一致候选，
  拒绝为 `no_dimension_consistent_three_face_hypothesis`。这说明当前 D01 不能
  直接删除 LingBot，但不证明 LingBot 是几何真值；需在其余确认帧复核。
- `PERCEPTION BATCH VERIFIED`: 用户授权后，D02～D12 已在 S1 完成 SAM3、
  LingBot 和 raw/LingBot ROI 批处理并复制回本机。11/11 服务级完成，0/11
  调用 FDP，0/11 运动命令；LingBot 均有 H4 候选，D06、D07、D10、D11 达到
  `ready_for_fdp=true`，但全部仍需逐帧人工确认。D06/D07/D11 的 raw 与
  LingBot 选择了不同实例，D12 也有显著分支差异。不能跨帧继承 SAM index，
  也不能把 `ready_for_fdp` 当作物理身份确认。详情见
  [D02–D12 感知批处理记录](../experiments/20260903_fdp_baseline/PERCEPTION_BATCH_ROUND2_D02_D12_20260907.md)。

### D02–D12 用户确认与 v3 多平面批量评估 — 2026-09-08

- `OPERATOR CONFIRMATION MATERIALIZED`: 用户原话“全部确认”绑定 D02=3、D03=6、
  D04=0、D05=1、D06=10、D07=5、D08=1、D09=0、D10=0、D11=6、D12=3 的
  LingBot 默认目标。11 个独立确认案例均通过 `load_case()`；253 个源文件
  哈希未变。任务上下文、审阅图和输入哈希见
  [确认索引](../experiments/20260903_fdp_baseline/OPERATOR_CONFIRMED_D02_D12_20260908.json)。
  此状态取代上文“仍待人工确认”；未确认 raw 分支的其他默认实例。
- `IMPLEMENTATION CORRECTIONS`: v3 修正了平面偏移投影混用导致的坐标原点
  依赖、细化后未复核三面支持、拒绝路径绘图缺字段和面符号不一致的问题。
  新批入口无需 FDP 参照，并绑定帧编号/捕获来源/确认输入；38 项测试通过。
  旧 v2/D01 文件保留，不能把“存在三面候选”解释为真实 XY/yaw 精度已验证。
- `FIXED-CONFIG BATCH VERIFIED`: D02–D12 用同一冻结 LingBot 深度、各自确认
  最终 ROI mask 和未更改的参数完成 11 帧本地估计；运行错误 0，几何接受 0。
  D02/D03/D08 当前搜索未找到三面候选；D04/D05/D06/D07/D09/D10 有竞争
  解释；D11/D12 仅高度冲突。按非互斥原因统计，共 7 帧有高度冲突。
  11 个正式矩阵均为 null；两次批量几何 JSON 逐字节一致。88 个产物、145 个
  输入路径、17 个源码路径哈希复核通过。本轮无网络、机器人或 FDP 调用。
- `DIAGNOSED LIMITATIONS`: D02 的两面贴合初值可能漏掉联合可行的三面组合，
  因此“未找到”不是“现场缺第三面”的证明。D05 有两个几乎等分的解释，XY
  相差约 31.085 mm，外/内壁归属待验证。D11 高度统计使用整片平面，范围外
  点使 P0/P2 跨度达 199.134/255.882 mm；仅统计匹配有限面内点后降为
  171.105/158.089 mm。这是下一步应修复的统计范围问题，尚未改为新正式算法。
- `DIRECTION`: 下一阶段优先统一有限面匹配点与高度统计，再检查联合初值和
  内外壁身份。暂不据本批加入 ICP 或抓取；同 mask 的 raw/LingBot 对照及新帧
  FDP 参照尚未执行。D11/D12 场景分组、跨帧物理身份和独立真值仍待补齐。
  当前 x86 单线程 11 帧算法计时 p50/p95 约 1.311/1.427 s，非 OrinX 性能。

详细逐帧结果、复现命令及证据边界见
[9 月 8 日批量报告](../experiments/20260907_bin_rim_pose/ROUND2_BATCH_REPORT_20260908.md)。

### 有限面高度、联合初值和内外表面复核 v4 — 2026-09-08

- `IMPLEMENTED AND STAGED EVALUATION`: 用户授权继续修正并评估。新增独立
  `multiplane_refined.py`，保留 v3；同一 D02–D12 确认输入、相同数值阈值下，
  有限面高度修正使原 7 帧高度冲突全部消失，D11/D12 中间几何通过；联合
  相对面/第三面初值补回 D02/D03 候选，中间通过变为 D03/D09/D11/D12 共4帧。
  D02 仍有竞争解释和 Z 区间 25.374 mm 欠约束，D08 仍未找到候选。
- `SURFACE MODEL LIMITATION`: 按捕获相机视线与平面法向做内外朝向假设复核，
  有候选的10帧均包含腔内朝向表面，却被原模型直接约束到外形尺寸。
  最终 `surface` 分支 0/11 通过，11 个正式矩阵为空。此为几何一致性复核，
  不是经过独立标签验证的内外壁检测器，尚未实现可靠内壁尺寸补偿；不能把
  三面外尺寸模型的不相容解释为全部采集数据损坏。
- `VERIFIED FROZEN MESH GEOMETRY`: 对冻结 OBJ（SHA-256
  `adb0d1cf4ee3cc885641ce5e473efb31de4d80323e7665ec50fa5aaabbcc991b`）
  做中央射线截面：最大外形约402.119×300.248×175 mm；距顶50 mm时宽向
  首/末交点对跨度约268.492/273.447 mm，长向约370.246/375.049 mm，且随
  高度变化。简单截面单壁首末交点间距约2.4–2.5 mm，不能把约30 mm矩形
  跨度差解释为每边15 mm壁厚。这是CAD局部几何，不是现场实测或全表面模型。
- `VALIDATION`: 43项离线测试通过；三阶段各11帧均无运行错误；33组复跑
  候选/接受状态一致。四阶段对照核验361个归档产物和相同输入清单。
  高度分支不改XY/yaw，表面分支不改联合分支中心。没有FDP/ICP/机器人或
  网络调用。联合/表面分支本机算法p50约1.536/1.577 s，非OrinX实测。
- `NEXT DIRECTION`: 优先把最大外形矩形模型改为随高度变化的内/外壳截面，
  区分箱沿法兰、箱身内外壁和筋条；校验模型与实物及坐标合同后再拟合。
  当前尚不能替代FDP或用于抓取，不宜以放宽门限解决模型尺寸不匹配。

详细结果与复现见
[v4 评估报告](../experiments/20260907_bin_rim_pose/ROUND2_V4_REPORT_20260908.md)。

### 相关侧边对话归档 — 2026-09-08

用户粘贴的 B/C/D 方案解释、D01 箱口矩形示例、中心与箱口派生关系、D02–D12
接受率/准确率边界及 FDP 对照已归档至
[箱体位姿侧边对话](history/bin_rim_pose_side_chat_20260908.md)。归档明确：

- 当前核心估计量是 T_base_link_from_4317_semantic 的箱体中心与 yaw；箱口中心、
  四角和短边中点含有 175 mm 高度与尺寸模型先验，不是独立测量结果。
- 0/11 是最终严格接受率，不是识别准确率；没有独立真值时，FDP 差异不能替代
  中心/yaw/抓取接触点误差。
- B、C 都是 RGB-D 几何视觉方案，D 才是明确的观测点云与模型点云配准；ICP 应在
  壳体模型和多初值之后做受约束精修/对照。

其中侧聊数字仍服从本文件的证据边界；需要对外报告或进入抓取门禁时，优先引用
实验报告和机器可读产物。

### 型号、mesh 与法兰侧边对话归档 — 2026-09-08

关于 4317/H4、EU4322_midcut_target175mm.obj、400×300×175 mm 尺寸语义、
法兰/箱身截面差异、中央裁切接缝和 V5 方向的侧聊已归档至
[型号与 mesh/法兰对话](history/bin_mesh_dimensions_flange_side_chat_20260908.md)。
当前可复核的核心边界是：

- 感知合同使用 4317/H4，但冻结 mesh 文件名为 EU4322_midcut_target175mm；
  两者是否同一实物型号仍待厂家或实物确认。
- 算法标称尺寸是 400×300×175 mm；冻结 OBJ 最大包围范围约
  402.119×300.248×175 mm，中央截面随高度变化且明显小于最大外形。
- 法兰很可能解释了“最大外形尺寸”和“箱身/内壁截面”之间的差异，但尚不能
  单独解释所有位姿偏差；当前 mesh 是中央裁切的派生模型。
- 后续应先建立带表面语义的高度相关内外壳截面模型，再使用可见表面受约束 ICP，
  不应直接把完整 mesh 交给普通 ICP。

### V5 Mesh 壳体模型计划 — 2026-09-08

- `USER-REQUESTED PLAN`: 用户询问 V5 是否应利用箱体 mesh 改善 V4-c，并要求
  先给出计划和后续实验方案。当前决定是使用 mesh 生成随高度变化、带内外表面
  和可见性角色的轻量壳体模型；不直接把完整 mesh ICP 当主方案。
- `V5-0/V5-1 IMPLEMENTED`: 已完成 mesh 合同审计和随高度变化截面预计算，输出
  [V5-0/V5-1 报告](../experiments/20260907_bin_rim_pose/V5_0_V5_1_REPORT_20260908.md)
  及 `v5_mesh_shell_model_20260908_01`。当前已记录 raw/semantic 轴变换、
  36 个高度层、内外层跨度、法兰/筋条/central_cut_seam 启发式角色；尚未把
  这些角色当作厂家标签，尚未发布姿态或运行 ICP。
- `REMAINING PLAN`: 后续预计算壳体截面，融合 B 箱口与 C 侧壁候选，建立纯壳体
  拟合基线，随后对相同初值增加受约束 4DoF ICP，并保留直接全 mesh ICP 作为
  对照。当前 mesh 是 central-height cut 派生文件，实物/服务端版本对应仍待确认。
- `V5-3 COMPLETED BEFORE ICP`: 已完成纯壳体拟合批量实验
  `v5_shell_fit_D02_D12_20260908_03`：11 帧运行无错误，9 帧通过实验拟合门限，
  D08 无初始化、D12 残差/覆盖率不足。候选 p90 残差多数约 14–21 mm；D01
  同帧与保存 FDP 的平移差约 6.5 mm、旋转差约 4.0°，FDP 仍非真值。所有
  候选均标记 `grasp_ready=false`、`outer_surface_identity_verified=false`，
  随后进入了独立 V5-4 ICP A/B；V5-3 本身仍未接入抓取。
- `V5-3 INTERPRETATION`: D01 与保存 FDP 的候选平移差约 6.5 mm、旋转差约
  4.0°，仅作后端差异观察，不是真值误差。V5-3 的 9/11 通过是几何拟合门限，
  不能称为准确率；对应报告见
  [V5-3 报告](../experiments/20260907_bin_rim_pose/V5_3_REPORT_20260908.md)。
- `V5-2/V5-3B EXECUTED`: 已将 B 箱口、C 多平面和 mesh 粗投影统一成候选初值，
  并加入图像边界、z-buffer 自遮挡和双向最近点可见性拟合。D02–D12 运行 0
  错误，9/11 通过实验门限；D08 从无 shell 初值变为有 12 个融合种子并产生
  候选，D12 因触边及残差/覆盖不足拒绝，D03 因内外表面解释接近拒绝。候选
  仍标记不可抓取、外壁身份未验证，不能把 9/11 称为准确率。
- `V5-2/FDP`: 与新 FDP 参考比较的 11 帧中心差 p50/p95 约 10.08/15.14 mm，
  yaw 对称差约 1.20/1.86°，短边两侧 p50 约 15.80/6.20 mm；这些是后端差异，
  不是绝对误差。V5-2 相比 V5-3 主要改善初始化覆盖和 D12 拒绝解释，整体
  精度没有被独立真值证明提高。详情见
  [V5-2/V5-3b 报告](../experiments/20260907_bin_rim_pose/V5_2_V5_3B_REPORT_20260908.md)。
- `V5-4 ICP A/B EXECUTED (2026-09-09)`: 在相同确认 LingBot 输入、最终 ROI
  mask、K、TF 和冻结 mesh 上，首次运行不依赖 Open3D 的多尺度受约束
  point-to-plane ICP，并保留直接全 mesh ICP 负面对照。11/11 帧运行无错误；
  受约束 ICP 相对 shell-fit 的模型 p90 中位数仅变化 −0.02 mm（6/11 改善、
  5/11 变差），直接全 mesh ICP 中位数恶化 +65.38 mm。受约束分支 0/11 帧
  具有足够 z 法向支持，z 主要继承初值/直立先验；合成回归验证加入水平面
  才能约束 z。结果见 [V5-4 报告](../experiments/20260907_bin_rim_pose/V5_4_ICP_AB_REPORT_20260909.md)
  和批次 [SUMMARY](../experiments/20260907_bin_rim_pose/outputs/v5_4_icp_ab_20260909_03/SUMMARY.json)。
  该轮不代表绝对准确率、FDP 真值或抓取可用性。
- `V5-3/FDP COMPARISON`: D01 的 V5-3 与保存 FDP 对照细化为箱体中心差
  6.497 mm、箱口中心差 10.380 mm、180° 对称 yaw 差 1.961°、完整旋转差
  4.026°；两条短边中点差分别 18.536 mm 与 3.398 mm。该条记录当时仅覆盖
  D01；随后已对 D02–D12 逐帧新调用 FDP，不能把任何 FDP 差异当作准确率。完整对照见
  [V5-3/FDP 报告](../experiments/20260907_bin_rim_pose/outputs/v5_shell_fit_fdp_compare_D01_20260908_01/REPORT.md)。
- `V5-3/FDP BATCH COMPARISON`: 随后用户明确授权本机直连
  `10.34.216.13:7876/first_frame_track`，D02–D12 逐帧新调用全部 HTTP 200，
  输入为各自确认的 LingBot case，结果标记为
  `new_result_from_frozen_exact_input`。与 V5-3 比较时，12 帧 FDP 成功、V5-3
  有 11 个候选（D08 无候选），11 帧可比较；中心差 p50/p95 为 8.22/15.30 mm，
  180° 对称 yaw 差 p50/p95 为 0.82/2.44°，短边两侧差异的 p50 约14.11/9.38 mm。
  FDP 仍不是独立真值，不能把这些差异写成 V5-3 准确率。全过程未访问机器人、
  未发送运动命令。逐帧证据见
  [V5-3/FDP 批量报告](../experiments/20260907_bin_rim_pose/outputs/v5_shell_fit_fdp_compare_D02_D12_20260908_01/REPORT.md)。
- `V5-3 INTERPRETATION`: 9/11 仅说明 mesh primary-role 点集可被观测壁点
  近邻拟合，不能证明拟合的是正确外壁、中心绝对误差或生产成功率。观察到
  内外 shell 角色同时参与，下一步若恢复应先增加表面对应门禁，再比较受约束 ICP。
- 当前 D01～D12 都已用于开发/诊断，不是未见留出集；V5 冻结后需新采
  H01/H02/R01～R03。没有独立参考前不能报告绝对准确率。建议 10 mm 中心/
  短边点和 2° yaw 仅作为设计目标，需由抓取误差预算修订。
- 详细模型审计、E1～E5 实验、准确度参考、门禁和停止条件见
  [V5 计划](s1_v5_mesh_shell_plan_20260908.md)。

For every meaningful experiment, record:

- date and objective;
- source files/components used;
- input data and assumptions;
- exact commands;
- output and observed result;
- safety conditions;
- verified conclusions;
- unresolved questions and next step.

When new evidence contradicts this file, preserve the useful historical note, clearly mark it superseded, and add the verified replacement with its source.


## 左右腕冻结 RGB-D 采集参数化 — 2026-09-09

- `IMPLEMENTED AND OFFLINE-VERIFIED`: 原采集脚本增加
  `scripts/capture_left_wrist_rgbd_once.py` 左腕入口；右腕入口仍为
  `scripts/capture_right_wrist_rgbd_once.py`（默认 right，并保留
  `--camera-arm left|right` 兼容参数）。两者共用实现选择 RGB/depth/K/TF，
  fresh_case 加载器同步支持左腕并校验侧别与帧名一致，案例来源使用实际侧别。
- `VERIFIED (local source)`: 旧脚本已保存 `base_from_camera.npy`，语义为按
  depth 时间戳查询的 `T_base_link_from_camera`；关节状态在取图后读取，并非
  严格同步。RGB/depth 与 TF/depth 门限分别 50/100 ms；没有图像最大年龄门禁。
  点云在相机坐标系由深度/K 生成，在 base_link 下另乘该帧 TF；移动基座跨帧
  地图融合还需可靠的公共坐标变换。
- `LOCAL ONLY; LIVE LEFT WRIST 待验证`: 19 项离线测试通过；本次未连接或部署
  S1，也没有实时采集或运动。详见
  [左右腕采集说明](../experiments/20260903_fdp_baseline/WRIST_CAPTURE_GUIDE_20260909.md)。

## H03L 左腕冻结采集检查 — 2026-09-09

- `VERIFIED (authorized read-only SSH inspection)`: S1 目录
  `/home/galbot/Lsy03/fdp_baseline/captures/left_wrist_H03L_20260909_102639_767663149`
  的 `capture_result.json` 为 `ok=true`，五个必需数据文件齐全，逐项 SHA-256
  与结果清单一致；本次检查使用了本地临时副本，未修改 S1。
- `VERIFIED`: 侧别为 `left`，传感器帧为
  `left_arm_camera_color_optical_frame`；RGB/深度均为 1280×720，帧时间差为
  0 ns，深度有效率约 84.7724%，深度 p50/p95 为 1.072/2.513 m。
- `VERIFIED`: 静态外参与捕获 TF 的刚体质量均有效，TF 与深度时间差为 0 ns；
  两者交叉差约 0.0188 mm、0.00318°。采集时保存 17 个全身关节值，关节读取
  相对深度时间约 73.7 ms，因此可作为采集时状态参考，但不是严格同步关节快照。
- `VERIFIED`: API 调用仅包含初始化、RGB-D/K/TF/状态读取和销毁，
  `robot_sdk_read_only=true`、`motion_commands_sent=false`。RGB 与深度预览显示
  目标箱体完整入镜，原始数据可用于离线点云和后续 SAM3/LingBot/ROI 处理。
- `UNRESOLVED`: 尚未对 H03L 运行目标人工确认、FDP 或轻量位姿评估；因此当前
  结论是“原始采集可用”，不是“目标位姿结果已验证”。

## H01L–H03L 左腕批量检查 — 2026-09-09

- `VERIFIED (authorized read-only SSH inspection)`: H01L、H02L、H03L 三个目录
  均为 `ok=true`，五个采集文件的 SHA-256 均与各自结果清单一致，RGB/深度
  均为 1280×720，侧别和 optical frame 均为左腕。
- `VERIFIED`: 三帧深度有效率分别约 85.8040%、85.0423%、84.7724%；
  RGB/depth 时间差和 TF/depth 时间差均为 0 ns，静态外参与捕获 TF 的刚体
  质量均有效。K 三帧完全一致，捕获 TF 之间最大相对位移约 0.012 mm、
  最大相对旋转约 0.0033°。
- `VERIFIED`: 三帧均只调用 getter/lifecycle 接口并记录
  `motion_commands_sent=false`。RGB/深度预览没有发现整体截断或明显编码错误，
  三帧可作为原始点云和后续感知输入。
- `LIMITATION`: H01L/H02L/H03L 的关节状态是在取图后读取，距深度时间约
  127/114/74 ms；它们适合作为状态参考，不应当当作严格同步的关节快照。点云
  变换应优先使用各帧保存的 `base_from_camera.npy`。
- `UNRESOLVED`: 三帧尚未完成逐帧目标确认、FDP 和轻量位姿评估；批次目前确认
  为“原始数据可用”，不等于目标身份或位姿精度已验证。

### H01L–H03L 后端对照方案 — 仅计划

2026-09-09 用户要求先制定现有算法与 FDP 对比方案，尚未启动推理实验。
计划固定输入比较 V3、V4 finite_height/joint/surface、V5-3、
V5-2+V5-3b 与 FDP，共最多 21 组主结果，再作 9 组 raw 深度消融。
执行前需逐帧确认目标和实物/mesh 合同。补充前述预览结论的边界：H01L 左前箱
外轮廓贴近/接触画面左边，完整性需按目标 mask 核对；图中 EU4316 字样与
4317/H4 模型的对应仍待验证。相机相对 base_link 的 TF 稳定不能证明基座在
世界中固定。详见
[本轮对照方案](../experiments/20260907_bin_rim_pose/H01L_H03L_COMPARISON_PLAN_20260909.md)。

### H01L–H03L SAM3/LingBot/ROI 预处理 — 2026-09-09

- `VERIFIED (authorized service execution)`: 三帧 SAM3 候选数为 10/11/10，
  每帧 SAM3 与 LingBot 各调用一次；六个 raw/LingBot 案例均通过哈希和输入门禁。
- `TARGET REVIEW REQUIRED`: 每帧均有两个 4317/H4 候选，默认选择的画面右前箱
  分别为 index 3/4/4，画面左前箱分别为 index 8/3/3；所有分支均正确停在
  `ready_for_fdp=false`。尚未调用 FDP 或运行轻量算法对照。
- raw/LingBot 默认目标的中心差为 22.97/27.48/35.69 mm，180° 对称 yaw 差为
  0.66/1.78/1.52°，mask IoU 为 0.9560/0.9538/0.9442。它们是深度分支差异，
  不是绝对误差。
- 详见[预处理记录](../experiments/20260903_fdp_baseline/H01L_H03L_PERCEPTION_RUN_20260909.md)。

### H01L–H03L 轻量后端、FDP 与倾斜验证 — 2026-09-10

- `SUPERSEDES PREVIOUS PLAN STATUS`: 用户确认三帧均以绿色覆盖的画面右前箱为目标，
  已物化 operator-confirmed case。V3、V4 finite_height、V4 joint、V4 surface、
  V5-3 shell、V5-2+V5-3b、V5-4 受约束/直接 mesh ICP 均已在同一批确认 LingBot
  输入上运行；FDP 修正版结果来自同一帧冻结请求。机器人未连接控制接口，运动命令为 0。
- `VERIFIED`: V3/V4 四个分支均 0/3 正式接受；V5-3 shell 3/3 通过当前拟合门限；
  V5-2+V5-3b 1/3 正式接受（H02L），H01L/H03L 因内外表面竞争解释拒绝。
  V5-4 受约束 ICP 三帧优化完成，模型 p90 相对 shell-fit 中位数变化约 -0.05 mm，
  仍无独立发布/精度门禁；直接全 mesh ICP 中位数恶化约 +72.22 mm。
- `VERIFIED`: 与 FDP 的候选中心差中位数依次为 V3 21.65 mm、V4-joint/surface
  21.54 mm、V5-3 13.65 mm、V5-2+V5-3b 10.76 mm、受约束 ICP 10.66 mm；
  这些是后端差异，不是绝对准确率。受约束 ICP 的小幅变化不足以证明整体收益。
- `TILT EVIDENCE`: 近水平顶部点云平面独立拟合的 LingBot 倾斜中位数为
  5.47°/5.91°/4.89°，raw 为 5.61°/7.14°/5.56°；FDP 高度轴为
  7.50°/8.61°/7.28°。观测法向与 FDP 高度轴夹角约 1.81～2.75°，raw 与
  LingBot 法向差约 0.81～1.57°，支持“箱体存在非零倾斜”的方向性证据。
- `LIMITATION`: 点云平面可能混入内壁、法兰、筋条或 mask 区域，分位阈值带来
  倾角范围；没有独立重力/标定板/测量真值，不能把观测 5～7° 或 FDP 7～9°
  当作真实角度。当前 V5 仍为 4DoF 直立先验，后续若扩展 roll/pitch 必须增加
  表面身份、可观测性和独立参考门禁。
- 完整算法表见[后端对照报告](../experiments/20260907_bin_rim_pose/outputs/h01l_h03l_all_backends_fdp_compare_20260909_02_status_fixed/REPORT.md)，
  倾斜细节见[倾斜验证报告](../experiments/20260907_bin_rim_pose/outputs/h01l_h03l_tilt_validation_20260910_01/REPORT.md)。

### 倾斜估计器合成与投影复核 — 2026-09-10

- `VERIFIED (synthetic)`: 已知 0°、5°、8° 平面，加入 1～2 mm 噪声、40%～
  30% 随机缺失点和较低水平干扰平面；独立法向估计误差分别约 0.01°、0.36°、
  0.81°，三种场景均通过 1° 合成门限。合成结果只验证数值实现，不验证实物
  表面身份或相机标定。
- `VISUAL CHECK`: H01L～H03L 的独立近水平平面支持点已投影回 RGB；黄色点
  主要落在确认的右前箱上缘区域，未见支持点整体落到背景的情况。该图仍是
  可见性诊断，不能将启发式平面认作实物真值。
- 脚本和结果见
  [合成验证报告](../experiments/20260907_bin_rim_pose/outputs/synthetic_tilt_validation_20260910_01/REPORT.md)、
  [真实倾斜投影接触表](../experiments/20260907_bin_rim_pose/outputs/h01l_h03l_tilt_projection_20260910_03/REPORT.md)。

## V5-5 A 阶段：倾斜证据工具修复 — 2026-09-10

- `A STAGE COMPLETE`: 按 [Luna 交接文件](../experiments/20260907_bin_rim_pose/V5_5_LUNA_HANDOFF_20260910.md)
  仅修复证据/验证工具；没有实现 V5-5 主算法，没有调用外部服务或连接机器人。
- `VERIFIED`: 新倾斜验证器保存体素选择顺序、像素与点坐标、RANSAC/TLS 前后
  支持集合、原点/法向、阈值、种子及按点数归一的 PCA 标准差；原始 SVD 奇异
  值明确标为审计量，不再当作与点数无关的空间跨度。
- `VERIFIED`: 投影渲染器直接读取保存的 post-TLS 支持像素/点，不重新拟合；
  raw 与 LingBot 使用同一个确认 mask；六组投影的像素/K/TF 重建最大误差均为
  0.0 m，mask 哈希按帧一致。
- `VERIFIED`: 合成覆盖 7 个常规倾斜/直立场景、随机/连续缺失和 XYZ 噪声，
  以及窄条带、单线和竞争平面；常规法向误差均 <=1°，退化被拒绝，竞争平面
  保留为歧义，全部通过固定测试。
- `VERIFIED`: bin_rim_pose 62 项测试、fdp_baseline 21 项测试和新增脚本编译
  均通过。A 阶段归档、输入/源码快照和资产哈希见
  [A 阶段输出](../experiments/20260907_bin_rim_pose/outputs/v5_5_A_stage_20260910_02/)。
- `A ARTIFACT UPDATE`: 最新合成报告加入真值/估计法向叠加图，扩展为 7 个常规、
  2 个退化和 1 个竞争平面场景；倾斜数值/投影分别见
  [A3 倾斜结果](../experiments/20260907_bin_rim_pose/outputs/h01l_h03l_tilt_validation_20260910_A3/REPORT.md)、
  [A5 投影](../experiments/20260907_bin_rim_pose/outputs/h01l_h03l_tilt_projection_20260910_A5/REPORT.md)、
  [A2 合成图](../experiments/20260907_bin_rim_pose/outputs/synthetic_tilt_validation_20260910_A2/REPORT.md)。
- `UNRESOLVED`: 真实平面身份、实物/mesh 对应、重力真值和 6DoF 箱体位姿仍未
  验证；下一步 B 阶段需单独授权，不能把 A 阶段结果当作 V5-5 已实现。

## V5-5 B 阶段：倾斜感知 6DoF 原型 — 2026-09-10

- `IMPLEMENTED; DESIGN GATE FAILED`: 新增独立 `v5_5_tilt.py`、
  `run_v5_5_batch.py`、`config/v5_5.json` 和合成 mesh 观测生成器；采用
  `Rz(yaw) Ry(pitch) Rx(roll)`，不读取 FDP pose，保留完整候选、局部边界、
  总倾角、可见性和尺度归一 Jacobian 诊断。C 阶段真实 H01L～H03L 对照未开始。
- `VERIFIED`: 7/7 合成场景运行无错误；包含直立、正负 roll/pitch、组合噪声/缺失
  和连续遮挡。算法内部门禁接受 4/7；连续遮挡被安全拒绝。truth 设计门槛（理想
  中心 <=2 mm、完整旋转 <=1°；噪声中心 <=5 mm、旋转 <=2°）仅 1/7 通过，
  因而不能标记 B 阶段通过或进入 C。
- `FAILURE EVIDENCE`: 当前模型点采样、像素 z-buffer 和双向最近点对应仍造成
  理想姿态中心/旋转超限；部分场景虽 `ok=true`，truth 误差仍超门槛，说明内部
  拟合门禁不能替代真值评估。合成矩阵也尚未覆盖全部 yaw×roll/pitch 组合，且
  还不是完整三角面光栅化渲染。
- `VERIFIED`: V5-5 相关 68 项测试、baseline 21 项测试和新增脚本编译均通过；
  真值/估计叠加图、源码/输入哈希、失败输出和固定配置见
  [B 阶段归档](../experiments/20260907_bin_rim_pose/outputs/v5_5_B_stage_20260910_02/)。
- `NEXT STOP`: 先修复合成观测/模型对应、补齐姿态矩阵和增强误接受门禁，再重跑
  B。未达标前不把 V5-5 接入真实 H 数据、FDP 或抓取链，也不放宽固定验收阈值。

`B FINAL STOP`: 最新 B14 批次仍为 7/7 无运行错误、4/7 算法门禁接受、truth
设计门槛 1/7（连续遮挡安全拒绝）。S01～S05 中心/完整旋转仍有超限，S06
组合噪声超限；故 B 未通过，C 未开始。详见
[B v2 报告](../experiments/20260907_bin_rim_pose/V5_5_B_STAGE_REPORT_20260910_v2.md)。

## V5-5 与 FDP 同帧对照 — 2026-09-10

- VERIFIED (local offline comparison): 按用户要求，V5-5 已在同一批
  H01L/H02L/H03L operator-confirmed LingBot 输入上与修正过 camera_frame
  标签的 FDP 输出完成对照；V5-5 未读取 FDP 位姿，也没有连接机器人或调用
  外部服务。
- VERIFIED: V5-5 三帧运行完成 3/3、正式接受 0/3。拒绝时正式矩阵为
  null，仅保留诊断候选；候选相对 FDP 的中心距离为 H01L 622.22 mm、
  H02L 666.61 mm、H03L 622.30 mm，中位数 622.30 mm。完整旋转差为
  116.03°/30.60°/45.91°；逐轴 RzRyRx 差值见专门报告。
- VERIFIED: 三帧均出现双向残差和内点率门禁失败及倾斜假设歧义；
  H01L/H02L 还超过 15° 总倾角范围。Jacobian 虽为数值满秩，不能证明
  候选语义对应正确。
- REFERENCE ONLY: 同一对照中的 V5-2+V5-3b 中心差为 10.76/11.71/8.79 mm
  （中位数 10.76 mm），只有 H02L 门禁通过；这些仍是与 FDP 的后端差异，
  FDP 不是独立真值。
- STOP: 本结果不支持 V5-5 已优于现有基线；B 阶段仍未通过，C 阶段不开始。
  下一次工作前必须先修复语义模型/观测对应和可见性生成，再重跑固定合成
  truth 门槛，不放宽阈值。详见
  [V5-5/FDP 对照报告](../experiments/20260907_bin_rim_pose/V5_5_FDP_H01L_H03L_COMPARISON_20260910.md) 和
  [统一对照机器结果](../experiments/20260907_bin_rim_pose/outputs/h01l_h03l_all_backends_fdp_compare_20260910_v5_5/REPORT.md)。