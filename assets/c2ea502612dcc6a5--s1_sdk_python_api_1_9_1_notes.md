# Galbot S1 SDK Python API 1.9.1 使用笔记

Recorded: 2026-08-28
Source: 用户粘贴的 Galbot 开发者站点「Python API 参考 - S1 机器」页面文本
Page label: `latest (1.9.1)`
Evidence level: `DOCUMENTED (user-provided official-page snapshot)`

## 证据边界

- 本文是对用户粘贴文档的可检索摘要，不是对当前机器人运行时的完整验证。
- 粘贴页面标记为 SDK `1.9.1`，而 2026-08-27 实机容器和宿主机受管环境已核验为 `1.9.0`。新增符号、参数、默认值和返回语义在实机上均应先用当前 stub/`help()`/最小静态调用确认。
- 本文不替代完整 API 页面。复杂配置类、全部字段和枚举值仍应查阅版本匹配的官方文档或本地 stub。
- 任何控制器切换、关节/夹爪/升降/底盘命令、导航或重定位都会读取或改变实机状态。真机运动必须遵守 `AGENTS.md` 的分步确认规则。

## 模块划分

Python API 按四个单例模块组织，都以 `MachineType.S1` 获取 S1 实例：

| 模块 | 职责 |
| --- | --- |
| `GalbotRobot` | 机器人连接与生命周期、关节/夹爪/底盘底层控制、传感器、TF、控制器管理 |
| `GalbotMotion` | FK/IK、雅可比、轨迹规划与执行、碰撞检查、障碍物/工具/抓取物管理 |
| `GalbotNavigation` | 定位、重定位、目标/轨迹/路点/速度导航、到达判定、携带物建模 |
| `GalbotPerception` | 端侧感知模型加载、单次推理和结果读取 |

通用约定：角度为弧度，线性长度为米，时间戳通常为纳秒；位姿向量通常是
`[x, y, z, qx, qy, qz, qw]`，四元数顺序为 `xyzw` 且必须归一化。

## `GalbotRobot` 基础用法

### 生命周期

1. 获取 S1 单例。
2. 调用 `init(enable_sensor_set=..., enable_sync_mode=False)`。
3. 检查 `init()` 的布尔返回值，再使用其他 API。
4. 运行期可用 `is_running()` 检查关闭信号。
5. 正常关闭顺序是 `request_shutdown()` → `wait_for_shutdown()` → `destroy()`。

`destroy()` 后 SDK 在当前进程进入终态，不能重新 `init()`；如需重连，应退出并新建进程。未 `destroy()` 时重复 `init()` 只有第一次生效。

### 传感器初始化与读取

- 只有在 `enable_sensor_set` 中启用的传感器才会初始化；按需启用可降低启动时间和资源占用。
- RGB、深度、红外、相机内参、IMU、LiDAR 和传感器外参都依赖对应传感器已启用。
- 红外数据还要求相机参数中 `ir_enabled=true`。
- `enable_sync_mode=True` 才启用同步缓冲区。`get_synced_observation(cameras, with_joint_state=True)` 以第一个相机最新帧为锚，对其他相机和关节状态做最近时间戳匹配。

主要读取接口：

- 设备/模型：`get_device_information()`、`get_joint_group_names()`、`get_joint_names()`、`get_frame_names()`
- 本体状态：`get_joint_positions()`、`get_joint_states()`、`get_gripper_state()`、`get_odom()`
- 传感器：`get_rgb_data()`、`get_depth_data()`、`get_ir_data()`、`get_imu_data()`、`get_lidar_data()`、`get_camera_intrinsic()`
- 坐标变换：`get_sensor_extrinsic()`、`get_transform(target_frame, source_frame, ...)`
- 诊断：`get_log_information()`、`get_active_controller()`、`check_trajectory_execution_status()`

### 关节顺序是强约束

- 显式传 `joint_names` 时，返回值或命令按该列表的精确顺序。
- 只传 `joint_groups` 时，按组定义顺序展开。
- 两者均为空的状态读取中，S1 默认顺序是 `torso` → `head` → `left_arm` → `right_arm`。
- 对 `Trajectory`、`execute_joint_trajectory()`、`set_joint_commands_batch()`，`joint_groups` 和 `joint_names` 不能同时为空；每个轨迹点的 `joint_command_vec` 必须与它们规定的顺序一致。
- 不要硬编码单关节名和顺序；先用 `get_joint_names(True, [group])` 在运行时查询。

### 控制接口层级

| 用途 | 接口 | 重要语义 |
| --- | --- | --- |
| 低频关键帧/姿态转换 | `set_joint_positions()` | 带速度限制的平滑轨迹；不适合高频逐帧控制 |
| 高频指令流 | `set_joint_commands()` | 不从当前位置插值到第一个目标，首帧跳变尤其危险 |
| 批量高频轨迹 | `set_joint_commands_batch()` | 非阻塞提交，立即返回 |
| 完整关节轨迹 | `execute_joint_trajectory()` | 可阻塞/非阻塞；必须明确关节顺序 |
| 夹爪 | `set_gripper_command()` | 目标宽度以米为单位，另有速度与 effort 限制 |
| 底盘位姿/速度 | `set_base_pose()` / `set_base_velocity()` | 直接底层控制，不等于导航规划 |
| WBC 任务位姿 | `set_end_effector_command()` | 每行为 7D 位姿，默认参考系为 `world` |

标准关节在当前文档版本中主要使用 `JointCommand.position`；速度、加速度和 effort 在相关接口中可能被忽略。夹爪的位置表示宽度，速度和 effort 有效。

文档给出 S1 夹爪宽度范围：长行程 `0.007–0.11 m`，短行程 `0.007–0.076 m`。具体末端执行器型号、标定和 effort 语义仍须在当前实机上验证；特别是 GE103 的力反馈尚未标定。

### 控制器与停止

- 管理接口：`acquire_controller()`、`switch_controller()`、`start_controller()`、`stop_controller()`、`release_controller()`、`reload_controller()`。
- `stop_controller()` 停止执行但保留权限；`release_controller()` 释放权限且会隐式停止运行中的执行。
- `stop_trajectory_execution()` 停止所有活动关节轨迹，文档称关节保持当前位置。
- `stop_base()` 是底盘立即停止命令，不替代物理急停。

`move_whole_body_joint_zero()`、`zero_whole_body_and_base()` 和文档中的“零（home）”描述不能被当作自然姿态、上次姿态或现场安全恢复点。本项目已有因把未测量的 `torso=0` 当成恢复值而导致升降柱意外下降的历史教训；禁止未经完整快照与现场审核直接使用这类全身接口。

## `GalbotMotion` 规划与执行

### 安全的学习顺序

1. `init()`，失败则停止。
2. 查询 `get_supported_chains()`、`get_supported_frames()`、`get_supported_links()`、`get_supported_ee_frames()`。
3. 用 `get_robot_states()`、`get_chain_joint_state()`、`get_end_effector_pose()` 读当前状态。
4. 先做 `forward_kinematics()`/`inverse_kinematics()` 和 `check_collision()` 的静态计算。
5. 用 `motion_plan()` 或 `motion_plan_multi_waypoints()` 规划，检查返回状态和轨迹。
6. 只有在仿真/离线验证和真机分步安全确认后才执行。

高级 `set_end_effector_pose()` 会内部做 IK、轨迹规划和执行。`is_blocking=False` 只表示 API 立即返回，机器人仍会在后台继续运动。

### 碰撞场景不会自动同步

- `add_obstacle()` 显式添加 box/sphere/cylinder/mesh/point_cloud/depth_image 等障碍物；对象持续存在直到 `remove_obstacle()` 或 `clear_obstacle()`。
- `attach_target_object()` 用于抓取后把物体附着到机器人，释放后用 `detach_target_object()`。`clear_obstacle()` 不会清除已附着对象。
- `attach_tool()`/`detach_tool()` 会更新运动学和碰撞几何，前提是工具已在机器人描述中配置。
- `GalbotMotion` 不会自动订阅或同步 `GalbotNavigation` 的点云/地图。要在操作规划中考虑环境，必须通过 Motion API 显式加载障碍物。
- 对 `safe_margin`、忽略碰撞 link、安全边界和禁用自碰/环境碰撞检查的任何配置，都应视为高风险变更。

### 已记录的限制

- 四元数必须归一化。
- FK 的 `target_frame` 必须是有效 URDF link。
- 雅可比接口不支持 `target_frame="Tool"` TCP；应使用有效 link 或 `EndEffector`。
- IK 不保证有解，种子状态会影响收敛和解的选择。
- `motion_plan()` 的 `target` 必须是 `PoseState` 或 `JointStates`，不能只传基类 `RobotStates`。
- `params.is_direct_execute=true` 会直接下发规划结果；不应把它当成纯规划调用。

## `GalbotNavigation` 导航语义

### 发送前的基本门禁

1. `init()` 成功。
2. `is_localized()` 为 true，再使用 `get_current_pose()`。
3. 用 `check_path_reachability(goal, start)` 做静态可达性预检。
4. 预检 true 只表示规划器认为有静态无碰路径，不保证导航成功。
5. 非阻塞调用的返回值通常只是“请求已接受”；必须继续查询 `get_navigation_status()`/任务快照和 `check_goal_arrival()`，并设置有界超时。

这与本项目的实机经验一致：SDK/PNS 返回 `SUCCESS` 不足以单独证明严格到达；必须再看到达判定与位姿反馈。

### 导航接口选择

| 接口 | 坐标/用途 | 关键风险 |
| --- | --- | --- |
| `navigate_to_goal()` | map 中的全局目标 | 非阻塞默认；需独立验证终态与到达 |
| `navigate_to_goal_v2()` | `map` 或 `base_link`，显式 `max_vel` | 会修改导航速度/超时等运行参数；实机 1.9.0 已使用，仍需守护式验证 |
| `navigate_through_waypoints()` | 必须按顺序经过多个路点 | 中间和最终状态都需监控 |
| `navigate_along_trajectory()` | 轨迹参考 | 中间点可被平滑/优化，不保证精确通过 |
| `set_navigation_target()` | 可频繁更新的动态目标 | 新目标可抢占旧目标，不宜高频调用 |
| `navigate_with_velocity()` | v2 平面速度+持续时间 | 非阻塞；“接受”不是“持续时间已完成” |
| `move_straight_to()` | odom/相对的短距离精调 | **不做动态避障或全局路径规划**，长距离有里程计漂移 |

### `max_vel` 不是导航方向

`navigate_to_goal_v2()` 的 `max_vel=[vx_max, vy_max, vyaw_max]` 是速度上限，不是带方向的速度向量：

- `goal_pose` 的位置差分决定目标方向。在 `pose_frame="base_link"` 下，`x` 是前后方向，`y` 是横向方向；例如纯横移目标可表示为 `[0, ±d, 0, qx, qy, qz, qw]`，正负号应以当前底盘 TF 坐标约定为准。
- `pose_frame="map"` 时，目标位置在地图坐标系中指定；如需从当前位姿横移 `d`，应先用当前 yaw 把本体坐标的横移向量转换到 map。
- `max_vel` 只限制规划轨迹中的 x/y/偏航速度通道（通常按底盘本体坐标解释，具体 frame 语义仍以当前 SDK/PNS 版本为准）；数值越大不会将目标改成该方向。文档要求各速度限制在 `[0.05, 1.5]` 范围内。
- `omni_plan=True` 表示允许全向底盘沿 x/y 任意方向并可独立旋转；它是可行运动方式的开关，不是“向左/向右”指令。规划器仍会根据目标和碰撞约束选择实际路径，因此不保证全程保持纯横移。

如果需要直接规定瞬时速度和正负方向，可用 `navigate_with_velocity(vx, vy, vyaw, ...)`，但它是非阻塞速度指令，不提供完整的全局避障规划。因此“侧移并自动规划避障”应优先用目标导航：`goal_pose` 指方向，`max_vel` 限速度，`omni_plan=True` 允许全向规划，`enable_collision_check=True` 启用对应碰撞检查。

**实机证据边界：**本项目于 2026-08-27 已用 `navigate_to_goal_v2(..., pose_frame="map", omni_plan=True)` 完成前向目标测试，但尚未对当前 S1 实机完成“纯横移目标 + 避障”的特定验证。

`relocalize(init_pose)` 的 RPC 成功只代表请求被接受，必须继续有界观测 `is_localized()` 和地图位姿。重定位时机器人应保持静止。

### 携带物在导航中的两类建模

- `add_bounding_box(box_info)`：向融合服务登记箱体区域，过滤该区域内的融合障碍点，避免把自己携带的箱子当成障碍物。
- `attach_box_to_link(box_info, ignore_collision_links)`：向 PNS 发送附着碰撞物，使箱子作为机器人几何的一部分参与碰撞检查。

两者语义不同且可能需要配合使用；对应删除接口分别是 `remove_bounding_box(box_tag)` 和 `detach_box_from_link(box_tag)`。这为“抓箱后导航需同时建模携带物并过滤自观测点”提供了 1.9.1 文档依据，但当前 1.9.0 实机服务的详细行为仍待验证。

## `GalbotPerception` 最小流程

1. `init({PerceptionModule...})` 加载所需模型。
2. 文档建议初始化后等待约 10 s 再调用 `run_once(module)`。
3. 用 `wait_for_new_result(module, timeout_s)` 有界等待新结果。
4. 用 `get_latest_result(module)` 非阻塞获取最新缓存结果。

文档列出 `FOUNDATION_STEREO` 为高精度立体深度，`LIGHT_STEREO` 在该版本不支持。这里的端侧 `GalbotPerception` 不应与项目现有的 Thor SAM3、LingBot-Depth 和远程 FoundationPose++ 流水线混为一谈；它们的部署位置和接口不同。

## 状态与结果判定

常见 `ControlStatus`/`MotionStatus` 包括：`SUCCESS`、`IN_PROGRESS`、`INVALID_INPUT`、`TIMEOUT`、`STOPPED_UNREACHED`、`DATA_FETCH_FAILED`、`COMM_DISCONNECTED`、`FAULT`、`INIT_FAILED`、`PUBLISH_FAIL`。

导航任务状态包括：`UNKNOWN`、`RUNNING`、`SUCCESS`、`FAILED`、`INTERRUPTED`、`OCCUPIED`、`COLLISION`、`CLOSE_TO_OBSTACLE`。

守护式客户端不应只判断一个返回码；应同时记录：

- 初始化和通信是否成功；
- 请求是否只被接受，还是已返回终态；
- 是否超时、中断或未到达；
- 位姿/关节/夹爪的二次状态回读；
- 碰撞检查和其它安全门禁是否真正启用。

## S1 平台枚举速查

### 关节组

`torso`、`head`、`left_arm`、`right_arm`、`left_gripper`、`right_gripper`、`left_camera`、`right_camera`、`swerve_chassis`。

文档称左/右臂各 7 自由度。`swerve_chassis` 在关节位置控制中是被动组。

### 控制器名称常量

`ELEVATOR_CTRL`、`HEAD_PVT_CTRL`、`LEFT_ARM_PVT_CTRL`、`RIGHT_ARM_PVT_CTRL`、`LEFT_GRIPPER_CTRL`、`RIGHT_GRIPPER_CTRL`、`LEFT_CAMERA_CTRL`、`RIGHT_CAMERA_CTRL`、`SWERVE_CHASSIS_POSE_CTRL`、`SWERVE_CHASSIS_TWIST_CTRL`。

### 传感器

- 相机：`HEAD_LEFT_CAMERA`、`HEAD_RIGHT_CAMERA`、`LEFT_ARM_CAMERA`、`RIGHT_ARM_CAMERA`
- 深度：`LEFT_ARM_DEPTH_CAMERA`、`RIGHT_ARM_DEPTH_CAMERA`
- 红外：左/右臂 `INFRA_CAMERA_1/2`
- LiDAR：`CHASSIS_LIDAR`、`HEAD_LIDAR`、`BACK_LIDAR`
- IMU：`CHASSIS_IMU`、`HEAD_IMU`、`BACK_IMU`

## 对当前项目的直接结论

- 新代码要把“命令接受”、“任务终态”、“严格到达/姿态误差”分开记录。
- 操作规划的障碍物场景和导航的障碍物场景是两套独立语义，不能假设自动同步。
- 抓箱后导航应分别考虑 PNS 附着碰撞物和融合点过滤箱体；只做其中一个可能不完整。
- 所有关节向量在读取、规划和执行之间都要保留显式名称/顺序，不依赖版本可变的隐式默认顺序。
- 真机上首先做版本和符号存在性检查，再做只读状态检查，然后才能考虑经审查的单设备低速运动。