# S1 导航 SDK 容器调查报告

调查日期：2026-08-27
调查对象：S1 `galbot-echo` 上的 `s1_sjtu_0806_slim` 容器
调查方式：通过用户授权的 SSH 复用连接执行只读命令

## 1. 安全与证据边界

本次没有修改 S1 宿主机、容器或项目文件，没有实例化
`GalbotNavigation`/`GalbotRobot`/`GalbotMotion`，没有调用 `init()`，
没有读取大体量传感器数据，没有发送导航、速度、重定位或其他运动命令。

证据主要来自：

- 当前容器中的 `/opt/galbot/sdk/galbot_sdk/s1/__init__.pyi`；
- 当前容器中的 `/opt/galbot/sdk/galbot_sdk/s1/__init__.py`；
- 当前容器中的 `/opt/s1-sjtu` 项目源码；
- `docker inspect`、文件列表和安装环境的只读检查。

2026-08-28 保存的 ESDF/碰撞球解释性侧边对话见
[`history/navigation_esdf_side_chat_20260828.md`](history/navigation_esdf_side_chat_20260828.md)。
该文件用于保留历史上下文，不构成独立于本报告日志证据之外的新验证。

## 2. 当前运行架构

```text
容器内 Galbot SDK / S1 项目客户端
        │  host network + host IPC
        ▼
S1 宿主机的厂家服务
  - service_navigation_plan
  - service_motion_plan
  - localization_server
  - robot_state_publish
  - 雷达、相机、融合感知等服务
        │
        ▼
S1 硬件
```

当前容器信息：

| 项目 | 已验证值 |
| --- | --- |
| 容器名 | `s1_sjtu_0806_slim` |
| 镜像 | `s1-sjtu-0806-slim:latest` |
| 镜像 ID | `sha256:6359272ddc5c520c60dd61a2293672d826e5312046c3986170bbdd0849c71697` |
| 镜像创建时间 | 2026-08-06 01:37:49 UTC |
| 入口 | `/ros_entrypoint.sh` + `sleep infinity` |
| 网络 / IPC | `host` / `host` |
| 默认工作目录 | `/opt/s1-sjtu` |
| Python | 3.8.10, aarch64 |
| Galbot SDK | 1.9.0 |

容器不是完整的 S1 底层控制系统；它是一个长期存活的 SDK/项目运行
环境，通过宿主网络和 IPC 访问宿主机厂家服务。

### 2.1 宿主机受管 SDK 环境（后续核查更正）

S1 宿主机也已配置一套不经 Docker 的正式受管 SDK 环境。早先检查
`/usr/bin/python3` 时 `find_spec("galbot_sdk")` 返回 `None`，只能说默认系统
Python 不能导入 SDK，不能推导为“宿主机没有 SDK”。

已验证的宿主机入口：

| 项目 | 路径/值 |
| --- | --- |
| 环境激活 | `/home/galbot/ie_lab/bin/s1-env` |
| 直接 Python 包装器 | `/home/galbot/ie_lab/bin/s1-python` |
| 被动环境检查 | `/home/galbot/ie_lab/bin/s1-env-check` |
| 受管 Python | `/home/galbot/ie_lab/envs/s1-sdk-1.9.0-py38/bin/python` |
| SDK 运行时 | `/data/galbot/lib` |
| Python / SDK | 3.8.20 / 1.9.0 |

2026-08-27 实际运行 `s1-env-check` 通过：NumPy 1.24.4、SciPy 1.10.1、
OpenCV 4.10.0、Open3D 0.18.0 和 `GalbotRobot`/`GalbotNavigation` 导入均成功，
且检查程序明确输出 `motion_init=not_run`。

因此 SDK 学习和单文件官方示例可以直接在宿主机上用：

```bash
/home/galbot/ie_lab/bin/s1-python your_example.py
```

或先 `source /home/galbot/ie_lab/bin/s1-env` 再使用 `python`。不应使用
`/usr/bin/python3`，也不应把 `/data/galbot/lib` 全局写入 `.bashrc`。

`/home/galbot/ie_lab/projects/chassis_env/build/sdk_runtime` 是另一份项目构建/容器
打包快照；`chassis_env/Dockerfile` 会将其复制为容器内 `/opt/galbot/sdk`。
日常宿主机执行应使用上述 `s1-python`，不要手工指向该 build 快照。

## 3. SDK 形态和生命周期

S1 Python 包是“Python 包装层 + aarch64 二进制扩展 + `.pyi` 类型桩”。
`galbot_sdk.s1.GalbotNavigation` 是单例包装器，内部取得
`MachineType.S1` 对应的底层实例。

公开说明要求：

1. 创建包装对象；
2. 调用 `init()` 后才能使用导航 API；
3. SDK 在同一进程中是单例；
4. `GalbotRobot.init()` 只有首次调用生效，`destroy()` 后要重新启动
   Python 进程才能再初始化；
5. 当前公开类型桩没有独立的 Navigation/Motion 销毁 API，项目注释认为
   `GalbotRobot` 的 shutdown/wait/destroy 生命周期负责整体清理。

因此不应在同一容器中随意并发启动多个 SDK 控制客户端。

## 4. `GalbotNavigation` 接口说明

### 4.1 初始化和只读状态

| API | 返回 | 含义 | 状态影响 |
| --- | --- | --- | --- |
| `init()` | `bool` | 初始化导航子系统 | 会初始化通信，不应与其他客户端并发 |
| `is_localized()` | `bool` | 判断地图定位是否有效 | 只读 |
| `get_current_pose()` | 7 维列表 | `map` 坐标系下底盘位姿 `[x,y,z,qx,qy,qz,qw]` | 只读，仅在已定位时有效 |
| `get_navigation_status()` | `NavigationTaskStatus` | 最近导航任务状态 | 只读 |
| `get_navigation_target_status(task_id)` | `NavigationTaskSnapshot` | 按任务 ID 查询异步任务 | 只读 |
| `check_goal_arrival()` | `bool` | 检查当前目标是否到达 | 只读 |
| `check_path_reachability(goal,start)` | `bool` | 检查静态地图上是否有无碰路径 | 规划查询，类型桩声明仅考虑静态障碍 |
| `get_bounding_box()` | `list[dict]` | 查询导航障碍物过滤框 | 只读 |
| `dump_navigation_configs()` | `(bool,str)` | 将动态导航配置输出到 SDK 日志 | 不运动，但会产生日志 |

### 4.2 导航和速度控制（会使底盘运动）

| API | 关键参数 | 说明 |
| --- | --- | --- |
| `move_straight_to(goal_pose, is_blocking=True, timeout=8)` | 相对 `base_link` 的 7D 位姿 | 基于里程计直达，无全局路径规划 |
| `navigate_to_goal(...)` | `map` 下 7D 位姿 | v1 导航；默认非阻塞；SDK 监视超时后会自动 `stop_navigation()` |
| `navigate_to_goal_v2(...)` | 7D 位姿、`[vx,vy,vyaw]`、`map/base_link` | v2 导航；超时参数传给 PNS 服务 |
| `navigate_with_velocity(vx,vy,vyaw,duration_s=3)` | 底盘速度和持续时间 | 非阻塞；返回仅表示命令被接受 |
| `navigate_along_trajectory(...)` | `Pose` 列表 | 轨迹会被平滑/优化，仅最终位姿保证为目标 |
| `navigate_through_waypoints(...)` | `Waypoint` 列表 | 按顺序执行多航点 |
| `set_navigation_target(...)` | 可变动态目标 | 异步、可抢占前目标；高频更新会导致规划抖动 |
| `stop_navigation()` | 无 | 停止当前导航并使底盘停下 |

所有上述运动 API 都必须在真机步骤级确认后才能调用。特别是
`is_blocking=False` 不代表不运动，只代表调用者不等待运动结束。

### 4.3 改变导航状态/配置的 API

| API | 作用 | 风险 |
| --- | --- | --- |
| `relocalize(init_pose)` | 在 `map` 下重设初始位姿 | 改变定位状态，不是只读 |
| `set_navigation_arrival_threshold([x,y,yaw])` | 设置到达阈值 | 影响任务成功判定 |
| `set_navigation_velocity_limit([vx,vy,vyaw])` | 速度上限 | 影响实机运动 |
| `set_navigation_kinematics_limits(vel,acc,jerk)` | 速度/加速度/加加速度上限 | 影响实机运动 |
| `set_navigation_timeout(timeout_s)` | 导航运动时限 | `<=0` 会禁用运动时限 |

### 4.4 箱体、碰撞和融合障碍点

| API | SDK 声明的语义 |
| --- | --- |
| `add_bounding_box(box_info)` | 添加过滤框，使导航忽略框内对应的融合障碍点 |
| `remove_bounding_box(box_tag)` | 移除指定过滤框 |
| `attach_box_to_link(box_info, ignore_collision_links=[])` | 把箱形碰撞体附着到某机器人 link |
| `detach_box_from_link(box_tag)` | 解除附着箱体 |

`box_info` 的公开字段为：

- `box_size`: `[length_x, length_y, length_z]`，单位米；
- `box_pose`: `[x,y,z,qx,qy,qz,qw]`，相对 `parent_link_name`；
- `box_tag`: SDK 箱体标签；
- `parent_link_name`: 箱体位姿的父 link；
- `ignore_collision_links`: 仅 `attach_box_to_link` 提供，用于指定附着箱体与哪些机器人
  link 忽略碰撞检查。

当前 `/opt/s1-sjtu` 中没有搜到这四个导航箱体 API 的调用。
项目已有的 `tool_collision_probe.py` 只会：

- 临时把官方 `GE103v1` 工具模型附着到左右臂；
- 用当前 17 维全身关节状态和 `map` 下底盘位姿执行一次静态碰撞检查；
- 回滚工具模型；
- 明确禁止导航目标、重定位和运动。

因此该 probe 不能单独解决“抓箱后导航把箱子视为碰撞物”。

## 5. 导航任务状态

`NavigationTaskStatus` 当前公开值：

| 值 | 含义 |
| --- | --- |
| `UNKNOWN` (0) | 未知 |
| `RUNNING` (1) | 执行中 |
| `SUCCESS` (2) | 成功 |
| `FAILED` (3) | 失败 |
| `INTERRUPTED` (4) | 被中断 |
| `OCCUPIED` (5) | 导航系统已被占用 |
| `COLLISION` (6) | 碰撞 |
| `CLOSE_TO_OBSTACLE` (7) | 靠近障碍物 |

`TaskHandle` 包含 `task_id`、`request_sent` 和 `msg`；
`NavigationTaskSnapshot` 包含 `task_id`、`status` 和 `msg`。
因此异步导航不能只根据“请求已发送”判断成功，必须按任务 ID 跟踪到
终态。

## 6. 点云、TF 和 RViz 可行性

### 6.1 SDK 已暴露的数据

`GalbotRobot` 类型桩提供：

- `get_lidar_data(sensor_id)`：返回点云字段和二进制点数据；
- `get_frame_names()`：返回可用坐标系；
- `get_transform(target_frame, source_frame, timestamp_ns=0, timeout_ms=100)`：查询 TF；
- `get_sensor_extrinsic(sensor_id, reference_frame="base_link")`：查询传感器外参；
- `get_odom()`：返回时间戳、位置和四元数；
- RGB、深度、内参和时间同步观测 API。

公开 LiDAR 枚举包括 `HEAD_LIDAR`、`BACK_LIDAR`、`CHASSIS_LIDAR`和
`BASE_LIDAR`。`LidarData` 结构与 ROS `sensor_msgs/PointCloud2` 高度对应：
包含 header、height、width、fields、endianness、point_step、row_step、dense 标志
和二进制 data。

### 6.2 当前容器的限制

已验证：

- 环境变量标识 `ROS_DISTRO=noetic`；
- 但 slim 容器内没有 `rosnode`、`rostopic`、`ros2`、`rviz` 或 `rviz2`
  可执行文件；
- 没有检出 Nav2/RViz 安装包；
- 宿主机底层服务以 `/data/galbot/bin/*` 和厂家 proto/中间件运行，
  不能因为存在 `ROS_DISTRO` 就假定它们发布标准 ROS topic。

结论：**当前容器不能直接打开 RViz，但 SDK 提供了构建点云/TF/里程计
桥接的必要数据。**

推荐在本地 ROS 2 Humble 工作站或专用开发容器中构建桥接：

```text
S1 SDK 读取进程
  ├─ get_lidar_data() -> sensor_msgs/PointCloud2
  ├─ get_transform() / get_sensor_extrinsic() -> tf2
  ├─ get_odom() -> nav_msgs/Odometry
  └─ get_current_pose() -> geometry_msgs/PoseStamped
                                  │
                                  ▼
                               RViz2
```

### 6.3 厂家局部 ESDF 的内部可视化入口（2026-08-28 后续只读核查）

宿主机的 `galbot_fusion_main` 已经使用 nvblox 生成 PNS 实际消费的局部
ESDF，因此不必先用三路 LiDAR 重新实现一套近似 ESDF。当前配置和日志验证：

- 三路输入为 `/lidar_chassis_f/lidar/data_raw`、
  `/lidar_head_f/lidar/data_raw`、`/lidar_body_b/lidar/data_raw`；
- ESDF voxel size 为 `0.05 m`，输出窗口相对 `base_link` 为
  `x/y=[-5,5] m`、`z=[0,2.1] m`，即 `200 x 200 x 42`；
- fusion 开启 `publish_esdf_pointcloud`，PNS 日志持续收到相同尺寸的更新；
- 序列化 DDS channel 为 `esdf_pointcloud_serialized`，另有
  `esdf_debug_pointcloud` debug/zero-copy 入口；
- 消息为 `galbot.perception_proto.EsdfGrid`，携带 voxel size/count、地图原点、
  距离数组、当前位姿和每体素偏移信息；
- 厂家 embosa Python binding 提供 `CreateSerializationReader()`，可构造被动
  一帧订阅器。

这把 RViz 路线收敛为：受管 Python 3.8 一帧订阅
`esdf_pointcloud_serialized` -> 保存最小、带元数据的本地样本 -> 工作站 ROS 2
节点按距离阈值/切片转换成 `PointCloud2` 或 `OccupancyGrid` -> RViz2。创建
DDS reader 虽然不控制机器人或修改 PNS，但会新增 participant、共享内存、日志和
少量 CPU/带宽负载，因此应与纯文件只读调查分开授权和记录。

后续经用户明确授权完成了一次单帧捕获。官方 topic工具确认该 channel 必须使用
`LARGE_DATA_TRANSPORT`、best-effort、keep-last depth 3 与 volatile QoS；默认
reader 因共享内存段不足无法接收。匹配 QoS 后获得 6,720,121-byte 原始 protobuf，
并在本地解析为完整 `200 x 200 x 42` 距离场。该捕获时刻前方 0.8 m的 sphere 9
采样距离约 `0.967 m`，没有重现此前 `0.126 m` 异常。因此后续实时桥必须同步记录
PNS查询时间和 ESDF帧时间，不能用任意较晚帧解释较早碰撞。

在实现前需先用一次经确认的只读 SDK 初始化检查实际返回字典的 key、
PointField 排列、时间戳单位和 frame name。

### 6.4 两次 1 m 拒绝不得混用（2026-08-31 修正）

2026-08-27 与 2026-08-28 的前进 1 m 请求是不同实验：

- 2026-08-27：起点约 `(1.0076,-0.0764)`、目标约
  `(1.9949,-0.2353)`；PNS 报告 sphere 9 距离约 `0.145–0.163 m`，球半径
  `0.17 m`。本文和历史侧边对话中的“静态目标碰撞”只对应这次事件。
- 2026-08-28：重定位后起点约 `(0.4148,-0.0978,yaw=-1.58)`；任务中读取的
  PNS 日志记录 sphere 9 距离约 `0.126–0.127 m`，但磁盘静态 ESDF/PCD
  在同一位置的离线距离约 `1.29/1.30 m`，后捕获的运行时 ESDF 又约为
  `0.963–0.967 m`。

因此，后一个事件不能再解释为“磁盘 `global_cloud_cleaned.esdf` 中存在固定
障碍”。高优先级方向是运行时融合场、PNS 内部缓存以及 TF/坐标时序；但
`evaluate at dyn map: 0` 的精确厂家语义尚未解码，以上仍不是最终根因。

## 7. 地图与 Nav2 仿真

当前挂载地图 `/var/maps/cur` 已验证包含：

- `map.yaml` + `map.pgm`：可能可转入 ROS/Nav2 的 2D 地图资产；
- `global_cloud.pcd` 和 `global_cloud_cleaned.pcd`：全局点云；
- `global_cloud_cleaned.esdf`：ESDF 资产；
- `map_topo.osm`：拓扑地图；
- 轨迹/帧数据 `poses.txt`、`times.txt`、`000000.bin...`。

当前容器没有 Nav2，且是 ROS 1 Noetic 风格的 slim SDK 环境。Nav2 应在
独立 ROS 2 Humble 仿真环境中建立，不应直接安装进这个真机运行容器。

仿真对接需分开验证：

1. `map.yaml` 的 resolution/origin/image 是否符合 Nav2 map server；
2. S1 全向底盘的 `cmd_vel` 和里程计语义；
3. `map -> odom -> base_link` TF 链；
4. 雷达点云投影或 2D scan 来源；
5. 机器人常态 footprint 与携箱 footprint；
6. Nav2 代价地图和厂家 PNS 规划器的行为差异。

Nav2 仿真可以用来验证地图、TF、footprint 和携箱几何，但不能直接证明
厂家真机导航服务的等价性。

## 8. “抓箱后碰撞报警”的当前判断

最值得优先验证的机制是：

1. 箱子被夹起后仍出现在融合点云中；
2. 导航将这些随机器人移动的点当成近距离外部障碍；
3. 返回 `CLOSE_TO_OBSTACLE` 或 `COLLISION`；
4. 项目目前又没有调用 `add_bounding_box()` 去过滤这些自带点。

同时，仅过滤点云也不够：规划器还应知道携带箱体后的实际外形，
否则可能规划出底盘能过、箱子过不去的路径。因此正确方向可能是：

```text
抓取成功
  -> 确认箱体尺寸和相对机器人位姿
  -> attach_box_to_link（建模携带物的碰撞体）
  -> add_bounding_box（忽略箱体自身在融合感知中的点）
  -> 携箱导航
  -> 放置完成
  -> remove_bounding_box + detach_box_from_link
```

这是根据当前 SDK 文档语义得出的**高优先级假设**，尚不是经过真机实验的
定论。下一步必须确认：

- 报警究竟是 `COLLISION` 还是 `CLOSE_TO_OBSTACLE`；
- 报警来自导航 PNS、运动规划、安全管理器还是其他服务；
- 箱体尺寸、父 link、相对位姿和 `box_tag` 生命周期；
- 哪些与夹爪/手臂的预期接触需列入 `ignore_collision_links`；
- 过滤框是否会误滤除箱体外的真实障碍。

不应将 `enable_collision_check=False` 作为解决方案。

## 9. 建议的后续步骤

### A. 非运动读取（需单独确认 SDK 初始化）

1. 确认没有其他 SDK 客户端占用。
2. 优先通过宿主机 `/home/galbot/ie_lab/bin/s1-python` 运行经审查的学习脚本；
   容器仅在脚本依赖 ROS Noetic 或容器项目库时必需。
3. 仅初始化必要的 LiDAR/状态传感器。
4. 读取 `get_frame_names()`、`get_bounding_box()`、定位状态和一帧 LiDAR
   数据元信息；不保存整帧原始点云也能先确认格式。
5. 做完整 SDK 生命周期清理。

### B. 离线 RViz2 桥接

1. 用保存的一帧 LiDAR 样本实现 PointCloud2 转换；
2. 不连真机验证 fields、endianness、point_step、row_step 和 frame_id；
3. 在本地 RViz2 显示点云和 S1 模型；
4. 再加入在线只读传输。

### C. Nav2 仿真

1. 在独立 ROS 2 Humble 容器/工作区中启动；
2. 转换并验证当前 2D 地图；
3. 配置全向底盘模型、TF、odom 和激光数据；
4. 对比无箱与携箱 footprint/代价地图；
5. 不将 Nav2 成功直接外推为厂家 PNS 真机成功。

### D. 真机携箱问题诊断

先做静态、无运动对比：抓取前/抓取后的导航状态、箱体过滤框、融合点云和
安全日志。任何附着/解除箱体 API 都会改变规划场景，应设计可验证的回滚；
任何底盘运动都需新的步骤级确认。

## 10. 待验证项

- 当前 S1 GBS/机器人系统版本；本次已验证 SDK 1.9.0，但未从
  `system.cfg` 得到 `CUR_VERSION`。
- `get_lidar_data()` 在当前机型上的实际字典 key 和 PointField 格式。
- 当前可用 frame 名称和完整 TF 链。
- 厂家导航服务是否有未暴露为 ROS topic 的内部点云/代价地图可视化接口。
- `attach_box_to_link()` 和 `add_bounding_box()` 在 S1 1.9.0 + 当前 GBS 上的具体生命
  周期、持久性和回滚语义。
- 抓箱后实际报警源和状态码。