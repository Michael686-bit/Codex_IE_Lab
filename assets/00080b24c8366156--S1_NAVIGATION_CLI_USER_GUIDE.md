# S1 导航 CLI 同事使用手册

本文档说明如何使用 `s1_navigation_cli.py` 完成 S1 导航状态检查、可达性探测、地图坐标导航、相对导航，以及 4317 箱体的导航注册和取消注册。

> 适用代码：`s1_navigation_cli.py`（本文编写时 SHA-256：`053a4818e12b7f57374a36d509d8a63ee2a23e909c978ab1d0064cee6a46c2bb`）
> 适用环境：S1 主机受管 Galbot SDK 1.9.0 Python 环境
> 重要边界：脚本中的 `navigate` 和 `relative` 会驱动真实移动底盘；箱体注册/取消注册不产生物理运动，但会修改 fusion/PNS 的导航状态。

## 阅读依据与版本边界

本文优先按用户提供的银河通用官方开发者站点《Python API 参考 - S1 机器》整理。该页面标记为 `latest (1.9.1)`；当前 S1 主机受管运行环境已核验为 SDK 1.9.0。因此本文按以下证据顺序描述：

1. **官方 API 语义（1.9.1 文档）**：说明各接口的设计用途、参数单位、坐标系和返回状态；
2. **当前 CLI 源码**：说明这份代码实际采用的默认值、保护顺序和成功/失败判据；
3. **SDK 1.9.0 当前 stub 与现场记录**：用于补充 1.9.0 的实测返回形式和运行注意事项。

如果三者有差异，运行时应以 S1 主机实际安装的 1.9.0 stub/行为为准，并把差异记录下来，不能直接假设 1.9.1 文档在 1.9.0 上完全相同。

### S1 实际部署版本核对（2026-09-02）

本次经用户授权，通过既有 SSH 复用连接对 S1 主机 `galbot-echo` 做了只读静态核对。没有初始化 `GalbotRobot`/`GalbotNavigation`，没有读取或修改机器人运行状态，也没有调用导航、定位、箱体或控制器接口。

| 核对项 | S1 主机实际结果 | 与本文匹配情况 |
| --- | --- | --- |
| 部署脚本 | `/home/galbot/Lsy03/navigation_tests/s1_navigation_cli.py` | 匹配 |
| 文件大小 | `70,247 bytes` | 与本地源文件一致 |
| 文件修改时间 | `2026-09-02 14:50:22 +08:00` | 记录项 |
| SHA-256 | `053a4818e12b7f57374a36d509d8a63ee2a23e909c978ab1d0064cee6a46c2bb` | **与本文标注及本地源文件完全一致** |
| 受管启动器 | `/home/galbot/ie_lab/bin/s1-python` | 匹配 |
| SDK 环境 | `/home/galbot/ie_lab/envs/s1-sdk-1.9.0-py38`，`S1_SDK_VERSION=1.9.0` | 匹配 |
| CLI 子命令 | 9 个子命令及 `--execute`、`--omni-plan`、成对箱体开关 | `--help` 静态解析结果匹配 |
| SDK 1.9.0 stub | 核心导航/箱体方法、`(success, status_string)` 返回形式、任务状态枚举、底盘姿态控制器常量 | 与当前源码调用和本文主要描述匹配 |

结论：**本文对应的代码就是 2026-09-02 核对时 S1 主机上的实际部署版本，不是旧备份。** 由于 SHA-256 完全相同，本地 23 项伪 SDK 测试所覆盖的也是这份部署代码本身；这不等于已在真机上执行或验证所有导航、停止和箱体状态变化路径。

本次只证明“部署文件、参数界面和已安装 stub 与手册匹配”，没有检查当前定位、PNS/fusion 服务就绪度、控制锁占用、当前箱体登记状态或物理导航效果。执行现场命令前仍必须重新完成第 2、3 节的运行前检查。

### 官方 API 与当前 CLI 的对应关系

| 当前 CLI 功能 | 主要官方 API | 官方定义的核心语义 | 当前代码的使用方式 |
| --- | --- | --- | --- |
| 初始化和清理 | `GalbotRobot.init()`、`GalbotNavigation.init()`、`request_shutdown()`、`wait_for_shutdown()`、`destroy()` | 导航 API 必须先初始化；机器人关闭遵循规定顺序 | 每个子命令建立一次 SDK 会话，结束时统一清理 |
| 定位检查 | `is_localized()`、`get_current_pose()` | 只有 `is_localized()==true` 时地图位姿有效 | 导航和可达性查询前强制检查；位姿必须为有限、归一化的 7D 数据 |
| 任务状态 | `get_navigation_status()`、`check_goal_arrival()` | 前者返回任务状态；后者表示是否在内部位置/方向容差内到达，且无活动目标时也为 `false` | 非阻塞导航中每 0.2 秒同时轮询两者和当前位姿 |
| 路径预检查 | `check_path_reachability(goal_pose, start_pose)` | 查询地图中是否有静态无碰撞路径；`true` 不保证最终导航成功 | 同一目标连续检查三次，必须全为 `true` |
| 绝对/相对导航 | `navigate_to_goal_v2()` | `pose_frame` 支持 `map` 和 `base_link`；非阻塞返回只表示请求是否被接受 | `navigate` 用 `map`；`relative` 用 `base_link`；碰撞检查固定开启 |
| 停止 | `stop_navigation()` | 取消当前导航并按运动学约束减速停止；停止后不保证回到原位置 | 超时、SIGINT/SIGTERM 和未完成清理时调用；实体急停仍是最终保障 |
| fusion 箱体过滤 | `add_bounding_box()`、`get_bounding_box()`、`remove_bounding_box()` | 让融合服务忽略指定箱体区域的障碍点；用同一 `box_tag` 查询/移除 | 固定 tag 4317，添加后完整回读 profile，取消时回查 tag 消失 |
| PNS 附着碰撞物 | `attach_box_to_link()`、`detach_box_from_link()` | 把箱体作为父 link 下的附着碰撞物；可指定与箱体忽略碰撞的机器人 links | 固定 tag 4317 和左臂末端父 link；`WAIT_INITIALIZED` 最长重试 5 秒 |
| 重定位 | `relocalize()` | 用地图初值重置定位；机器人应静止，调用后必须再用 `is_localized()` 验证 | 只调用一次，再做有界定位采样，不把 RPC 成功当作定位成功 |

官方 API 文档中 `navigate_to_goal_v2()` 的默认值是 `timeout=5.0`、`omni_plan=false`；当前 CLI 明确覆盖为 `timeout=30.0`、`omni_plan=true`。同事使用时应以命令行打印的实际值为准，而不是依赖 SDK 默认值。

## 1. 这份代码能做什么

| 子命令 | 功能 | 是否运动 | 是否修改系统状态 | 是否需要 `--execute` |
| --- | --- | --- | --- | --- |
| `pose` | 读取定位、地图位姿、导航状态和过滤框 | 否 | 否 | 否 |
| `diagnose-localization` | 持续采样定位状态 | 否 | 否 | 否 |
| `probe-relative` | 查询相对方向上不同距离是否可达 | 否 | 否，只发查询 | 否 |
| `payload-status-4317` | 查询 4317 fusion 过滤框 | 否 | 否 | 否 |
| `payload-register-4317` | 注册 4317 fusion 过滤框并附着 PNS 碰撞箱 | 否 | 是 | 是 |
| `payload-remove-4317` | 解除 PNS 碰撞箱并删除 fusion 过滤框 | 否 | 是 | 是 |
| `navigate` | 导航到 `map` 坐标系中的绝对目标 | **底盘运动** | 是 | 是 |
| `relative` | 按当前 `base_link` 坐标系中的偏移量导航 | **底盘运动** | 是 | 是 |
| `relocalize` | 重设地图初始位姿并观察是否收敛 | 否 | 是，修改定位状态 | 是 |

脚本不会控制机械臂、夹爪或升降柱，也不会自动抓取或释放箱体。

## 2. 运行前准备

### 2.1 在哪里运行

必须在 S1 主机上用受管 SDK Python 运行，不要使用系统默认的 `/usr/bin/python3`。

仓库中的源文件位于：

```text
experiments/20260827_s1_navigation/s1_navigation_cli.py
```

S1 主机上常用的部署位置是：

```text
/home/galbot/Lsy03/navigation_tests/s1_navigation_cli.py
```

本文后续命令使用以下变量；如果实际部署位置不同，只修改 `S1_CLI`：

```bash
S1_PY=/home/galbot/ie_lab/bin/s1-python
S1_CLI=/home/galbot/Lsy03/navigation_tests/s1_navigation_cli.py
```

可先确认文件版本：

```bash
sha256sum "$S1_CLI"
```

如果校验值和本文开头不同，先查看该版本的 `--help` 和变更记录，不要默认参数与本文完全一致。

### 2.2 每次运行前必须确认

- 现场有人看护机器人，物理急停可立即触达。
- 底盘四周、目标点、规划路径和箱体外廓均有足够净空。
- 地面平整，没有人员、线缆、推车或临时障碍进入路径。
- 没有其他 SDK 客户端或导航程序正在控制机器人。
- 定位地图与现场一致，机器人地图位姿可信。
- 携箱时，箱体确实处于本文第 5 节规定的 4317 抓持几何中，且没有滑移或重新抓取。

脚本会自行独占 `/home/galbot/ie_lab/control.lock`。不要再在命令外套同一个 `flock`。如果报告锁被占用，应先确认占用者，不要删除锁文件或强行结束未知进程。

## 3. 建议先做的只读检查

### 3.1 查看当前定位和导航状态

```bash
"$S1_PY" "$S1_CLI" pose
```

重点看：

- `localized`：必须为 `true` 才能导航或探测可达性；
- `current_pose_map`：当前地图 7D 位姿 `[x,y,z,qx,qy,qz,qw]`；
- `navigation_status`：开始注册、取消注册或重定位前不能是 `RUNNING`/`OCCUPIED`；
- `bounding_boxes`：当前 fusion 过滤框列表。

按官方 API，`get_current_pose()` 表示地图坐标系中的底盘接地轮廓中心位姿，并且只有在 `is_localized()` 为 `true` 时有效。

如果定位状态不稳定，可连续观察 10 秒：

```bash
"$S1_PY" "$S1_CLI" diagnose-localization --timeout 10 --interval 1
```

只有最终 `navigation_ready=true` 才表示最后一次采样同时具备定位和有效地图位姿。

### 3.2 导航前只读探路

前方默认距离扫描：

```bash
"$S1_PY" "$S1_CLI" probe-relative --direction forward --checks 3
```

指定四个方向和距离：

```bash
"$S1_PY" "$S1_CLI" probe-relative \
  --direction all --distances 0.3 0.5 0.8 --checks 3
```

方向采用 `base_link`：

- `forward`：前方，`+x`；
- `backward`：后方，`-x`；
- `left`：左侧，`+y`；
- `right`：右侧，`-y`。

结果分类：

- `stably_reachable`：同一目标的所有检查都可达；
- `stably_unreachable`：所有检查都不可达；
- `mixed`：结果不稳定，应停止运动并调查，不要反复尝试碰运气。

探测可达不等于现场绝对安全，只说明当前 PNS 查询通过。

官方 API 特别注明：`check_path_reachability()` 只检查地图中的静态障碍，而且返回 `true` 不保证实际导航成功。动态障碍、运行时状态、定位变化和控制执行仍可能导致导航失败。

## 4. 空载导航

### 4.1 相对导航：适合短距离现场操作

例：沿机器人当前朝向前进 0.5 m，不改变朝向：

```bash
"$S1_PY" "$S1_CLI" relative \
  --x 0.5 --y 0.0 --yaw 0.0 \
  --max-vx 0.10 --max-vy 0.10 --max-vyaw 0.15 \
  --timeout 30 --max-distance 0.6 \
  --omni-plan true --execute
```

相对目标参数：

- `--x`：前后偏移，正数向前，单位 m；
- `--y`：左右偏移，正数向左，单位 m；
- `--yaw`：相对旋转角，单位 rad；
- `--max-distance`：允许的最大平移距离，超过即拒绝；
- `--omni-plan true|false`：是否允许全向规划，默认 `true`。

官方 API 规定 `max_vel=[vx,vy,vyaw]`，两个线速度单位为 m/s，偏航速度单位为 rad/s，三个分量都必须在 `[0.05,1.5]`。`omni_plan=true` 表示启用全向规划；`false` 表示使用基于航向的规划。它不是碰撞检测开关。

### 4.2 地图绝对坐标导航

例：前往 `map` 中的 `(x=1.0 m, y=-1.0 m, yaw=-1.0 rad)`：

```bash
"$S1_PY" "$S1_CLI" navigate \
  --x 1.0 --y -1.0 --yaw -1.0 \
  --max-vx 0.10 --max-vy 0.10 --max-vyaw 0.15 \
  --timeout 30 --max-distance 2.0 \
  --omni-plan true --execute
```

`navigate` 中的 `x/y/yaw` 是地图绝对目标，不是相对位移。使用前必须从可信地图和现场标志物核对目标，不能把上一次运行的坐标直接套到已经移动过的机器人或不同地图中。

### 4.3 导航命令内部的保护

当前代码会依次执行：

1. 要求命令行显式携带 `--execute`；
2. 获取独占控制锁；
3. 检查定位有效；
4. 检查目标距离不超过 `--max-distance`；
5. 对同一目标做三次静态可达性检查，必须三次全为 `true`；
6. 打印起点、目标、速度、超时、碰撞检测和箱体状态；
7. 切换到 `SWERVE_CHASSIS_POSE_CTRL`；
8. 用 `navigate_to_goal_v2()` 非阻塞提交，碰撞检测固定开启；
9. 每 0.2 秒监控位姿、导航状态和到位标志，约每秒输出一次进度；
10. 超时或收到一次 `Ctrl+C`/SIGTERM 时调用 `stop_navigation()`，最多等待 5 秒确认退出 `RUNNING`。

代码没有关闭 v2 碰撞检测的选项，但这不等于已覆盖所有现场风险。脚本本身还会警告：PNS 全身碰撞检查不能由该 CLI 保证。

根据官方 API，非阻塞 `navigate_to_goal_v2()` 的返回只表示请求是否被接受，并不表示机器人已经到达；其 `timeout` 还会被发送给 PNS，可能改变后续底盘导航配置。当前 CLI 因此继续轮询终态，并在本次命令自身的超时点主动执行停止流程。

## 5. 4317 箱体注册

### 5.1 “注册”实际包含两个互补动作

| 动作 | 作用 | 不会做什么 |
| --- | --- | --- |
| `add_bounding_box()` | 在 fusion 中过滤箱体区域后续采集到的自身点云，减少把手持箱体识别成外界障碍 | 不会增大机器人的碰撞外形；不会追溯清除已经融合的旧体素 |
| `attach_box_to_link()` | 在 PNS 中把实体箱作为随机器人运动的附着碰撞物，用于环境碰撞检查 | 不会过滤 LiDAR 点，也不会修改/清除 ESDF |

携箱导航需要两者配套。只做过滤会丢失箱体外廓碰撞保护，只做附着又可能让箱体自身点云进入环境地图。

上述两类用途来自官方 API。关于“过滤只作用于后续输入、不会追溯清除已有 TSDF/ESDF 体素”的结论，则来自当前 S1 fusion 二进制/日志分析，不是官方 API 页面给出的清图保证。

### 5.2 当前固定的 4317 配置

此命令不是通用箱体注册器，只适用于固定 profile：

```text
profile: 4317_left_mount_20260831_193312_191
tag: 4317
parent link: left_arm_end_effector_mount_link
fusion 过滤框: 0.60 x 0.50 x 0.375 m
PNS 实体碰撞箱: 0.40 x 0.30 x 0.175 m
```

PNS 碰撞箱还配置了以下 `ignore_collision_links`，其官方含义是：在碰撞检测时，忽略附着箱体与这些机器人 link 之间的碰撞；并不是忽略箱体与外部环境的碰撞。

```text
left_arm_end_effector_mount_link
right_arm_end_effector_mount_link
left_fingertip_end_effector_mount_link
right_fingertip_end_effector_mount_link
```

两种箱体使用相同的左臂末端相对位姿：

```text
[0.088464545899, -0.209262726967, -0.158900000000,
 0.011116385395, -0.000386121234, 0.697301150147, 0.716691972112]
```

该 profile 来源于记录的 4317 抓取后抬升姿态及当前 GE103v1 安装几何。只有箱体相对 `left_arm_end_effector_mount_link` 保持这一刚性关系时才有效。发生滑移、释放、重新抓取、换箱、换夹具或抓持位姿变化后，必须先取消旧注册，并重新测量/生成 profile，不能继续复用。

### 5.3 推荐注册步骤

1. 确认导航已经停止，箱体已被稳定抓持在上述固定姿态，现场急停可用。
2. 查询当前状态，确认 tag 4317 不存在：

```bash
"$S1_PY" "$S1_CLI" payload-status-4317
```

3. 注册 fusion 过滤框和 PNS 碰撞箱：

```bash
"$S1_PY" "$S1_CLI" payload-register-4317 --execute
```

4. 成功后再次查询：

```bash
"$S1_PY" "$S1_CLI" payload-status-4317
```

期望看到：

```text
filter_registered: true
filter_profile_matches: true
```

注意：当前公开 SDK 只能回查 fusion 过滤框，不能查询 PNS attachment 列表。因此 `payload-status-4317` 不能独立证明碰撞箱仍附着；注册时的 `attach_box_to_link_return`、后续 PNS 行为以及最终 detach 结果需要共同留档。

官方 1.9.1 API 页面规定：`get_bounding_box()` 在“当前没有箱体”或“通信失败”时都可能返回空列表；S1 当前安装的 1.9.0 stub 只写明返回当前箱体列表，没有写出这一歧义。为兼容更保守的官方语义，意外得到空列表时不能只凭 `filter_registered=false` 断言取消注册成功；应重复查询并检查 SDK/fusion 通信日志。当前 CLI 的 `query_ok=true` 仅表示本次 Python 调用没有抛出异常。

### 5.4 注册命令内部顺序

注册命令会：

1. 拒绝在导航状态为 `RUNNING`/`OCCUPIED` 时操作；
2. 要求 tag 4317 在 fusion 中完全不存在；
3. 检查父 frame 存在，并读取有限有效的 `base_link <- left_arm_end_effector_mount_link` TF；
4. 添加 fusion 过滤框；
5. 按 tag、尺寸、位置、四元数和父 link 完整回读校验；
6. 添加 PNS 碰撞箱；如果 PNS 返回 `WAIT_INITIALIZED`，每 0.25 秒重试，最长 5 秒；
7. 附着失败时尝试删除刚添加的 fusion 过滤框，并回查回滚是否成功。

成功结果应包含：

```text
ok: true
outcome: payload_registered
registration_retained_until_explicit_remove: true
```

注册状态不会随这次 CLI 进程退出自动删除，会一直保留到显式取消注册。

官方列出的箱体接口返回状态包括：

- `add_bounding_box()`：`SUCCESS`、`INVALID_INPUT`、`COMM_ERR`；
- `attach_box_to_link()`：`SUCCESS`、`INVALID_INPUT`、`WAIT_INITIALIZED`、`COMM_ERR`；
- `detach_box_from_link()`：`SUCCESS`、`WAIT_INITIALIZED`、`COMM_ERR`；
- `remove_bounding_box()`：`SUCCESS`、`COMM_ERR`。

当前 SDK 1.9.0 现场返回通常表现为 `(bool, status)` 元组，CLI 同时检查元组首项并记录完整返回值。

### 5.5 注册后不要立刻假设旧障碍已经消失

`add_bounding_box()` 只过滤注册以后进入 fusion 的输入点，没有经过验证的“追溯删除旧 TSDF/ESDF 体素”能力。如果箱体在注册前已被传感器融合，原位置可能仍残留障碍体素。

因此注册后应先运行只读 `probe-relative`。如果携箱目标仍是 `stably_unreachable`，应检查 PNS/ESDF/TF 和现场几何；不要关闭碰撞检测、删除碰撞箱或清空地图来绕过预检查。

## 6. 携箱导航的两种用法

### 6.1 推荐：先显式注册，再导航

这种方式便于每一步检查和留档：

```bash
"$S1_PY" "$S1_CLI" payload-status-4317

"$S1_PY" "$S1_CLI" payload-register-4317 --execute

"$S1_PY" "$S1_CLI" probe-relative \
  --direction forward --distances 0.3 0.5 --checks 3

"$S1_PY" "$S1_CLI" relative \
  --x 0.5 --y 0.0 --yaw 0.0 \
  --max-vx 0.10 --max-vy 0.10 --max-vyaw 0.15 \
  --timeout 30 --max-distance 0.6 \
  --omni-plan true --execute
```

箱体已经显式注册后，导航命令中**不要**再带 `--add-bounding-box --attach-box-to-link`；否则代码会因为 tag 4317 已存在而拒绝。

### 6.2 一条命令自动注册后导航

只有确认 tag 4317 完全不存在时，才可使用成对开关：

```bash
"$S1_PY" "$S1_CLI" relative \
  --x 0.5 --y 0.0 --yaw 0.0 \
  --max-vx 0.10 --max-vy 0.10 --max-vyaw 0.15 \
  --timeout 30 --max-distance 0.6 \
  --omni-plan true \
  --add-bounding-box --attach-box-to-link --execute
```

两个开关必须同时出现，只写一个会在 SDK 初始化前直接失败。自动模式会在同一个锁和 SDK 会话中完成“检查距离 → 注册 → 三次可达性检查 → 导航”。无论导航成功、失败、超时或被操作员停止，注册都不会自动移除。

## 7. 4317 箱体取消注册

取消注册只修改导航建模状态：它不会放下箱体、不会张开夹爪，也不会移动机械臂或底盘。

### 7.1 什么时候执行

- 导航已完全停止；
- 后续不再需要把该箱体作为当前携带物进行导航建模；
- 箱体已经释放，或者机器人将停留原地进入释放/重新抓取流程；
- 取消后绝不再以“仍持有这个固定 profile”的假设继续导航。

### 7.2 命令

```bash
"$S1_PY" "$S1_CLI" payload-remove-4317 --execute
```

命令会先调用 `detach_box_from_link(4317)`，再调用 `remove_bounding_box(4317)`，最后回查 fusion 列表。成功结果应为：

```text
ok: true
outcome: payload_removed
filter_removed: true
```

再做一次只读确认：

```bash
"$S1_PY" "$S1_CLI" payload-status-4317
```

期望：

```text
filter_registered: false
```

`remove_bounding_box()` 同样不代表旧 ESDF 体素被清除；它只是删除后续输入点过滤规则。

## 8. 如何判断命令结果

脚本最终输出 JSON，并使用以下退出码：

- `0`：命令按当前代码判据成功；
- `1`：失败并保持关闭状态，或结果未被充分验证；
- `130`：运行中收到操作员中断信号。

常见 `outcome`：

| `outcome` | 含义 | 建议 |
| --- | --- | --- |
| `payload_registered` | 两种箱体注册调用完成，fusion profile 已回查 | 继续做状态查询和只读可达性探测 |
| `payload_removed` | detach/remove 返回成功，且过滤框已消失 | 再运行一次 `payload-status-4317` 留档 |
| `payload_removal_not_fully_verified` | detach、remove 或回查至少一项不完整 | 不要直接重新注册；保留完整 JSON 并调查 |
| `completed` | 到位标志为真，或导航状态报告 `SUCCESS` | 同时检查最终位姿误差和现场实际位置 |
| `navigation_failed` | 导航状态报告 `FAILED` | 保持停止，检查 PNS/ESDF/现场障碍和日志 |
| `navigation_timeout_stopped` | 超时后已进入停止流程 | 确认底盘实际静止和 `stop_confirmed` |
| `interrupted_and_stopped` | `Ctrl+C` 后停止得到确认 | 现场确认静止，再决定下一步 |
| `interrupted_stop_not_verified` | 中断后未确认停止 | **立即以实体急停和现场状态为准** |
| `failed_closed` | 参数、锁、定位、TF、距离、可达性或 SDK 调用不满足要求 | 阅读 `error.message` 和 `details`，不要盲目重试 |

SDK 返回 `SUCCESS` 只说明 SDK/PNS 的相应成功判据成立，不等于现场语义一定正确。导航后必须一起检查：

- `final_pose`/`final_pose_map`；
- `position_error_m`；
- `orientation_error_rad`；
- `goal_arrival`；
- `navigation_status`；
- 机器人现场实际位置和朝向。

官方 `NavigationTaskStatus` 还定义了 `UNKNOWN`、`RUNNING`、`SUCCESS`、`FAILED`、`INTERRUPTED`、`OCCUPIED`、`COLLISION` 和 `CLOSE_TO_OBSTACLE`。当前 CLI 立即终止的显式分支主要是 `SUCCESS`、`FAILED`、到位、超时和操作员信号；如果进度输出持续出现 `COLLISION`、`CLOSE_TO_OBSTACLE`、`INTERRUPTED` 或异常 `OCCUPIED`，不要等待软件自行恢复，应现场确认机器人状态，必要时使用物理急停，并保留完整输出供代码维护者分析。

## 9. 常见问题与处理

### `robot control lock is already held`

说明另一个进程持有控制锁。确认当前 SDK/导航程序及其操作员，不要删锁文件，不要强杀未知进程。

### `navigation is not localized`

停止导航流程，运行 `diagnose-localization`。不要为了“试一下”而编造坐标执行 `relocalize`。

### `static path was not reachable in all three checks`

脚本尚未切换控制器或提交导航。官方文档把该 API 定义为静态地图无碰撞路径查询；当前 S1 现场记录还显示其结果可能受 PNS 当前使用的运行时 ESDF 影响，二者存在版本/实现语义差异。应检查现场障碍、目标几何、PNS 日志、实时 ESDF 和 TF；不要关闭碰撞检测或扩大过滤框来绕过。

### tag 4317 已存在

先运行 `payload-status-4317`。如果箱体确实仍按正确 profile 被持有，可在人工确认既有 attachment 可信后使用不带自动注册开关的导航命令；如果状态来源不明，先停止导航并按异常状态处理，不要直接覆盖或重复注册。

### `WAIT_INITIALIZED`

代码会自动重试最多 5 秒。最终仍失败时会尝试回滚 fusion 过滤框。检查输出中的 `attach_box_to_link_attempts`、`rollback_attempted` 和 `filter_rollback_verified`。

### `filter_rollback_verified: false`

fusion 状态未知。不要导航，不要再次注册；保留完整输出并人工核查 `get_bounding_box()` 和 PNS 状态。

### 取消注册返回 `payload_removal_not_fully_verified`

保持机器人停止。分别查看 `detach_box_from_link_return`、`remove_bounding_box_return` 和 `filter_removed`。因为公开 API 无法列出 attachment，不能只凭过滤框消失就断言 PNS 已成功解除附着。

### `Ctrl+C` 后机器人仍有动作

软件停止不是实体安全保证。立即使用现场物理急停，并在确认底盘、机械臂、夹爪和升降柱全部静止后再检查日志。不要连续反复按 `Ctrl+C` 代替急停。

## 10. 关于 `relocalize`

`relocalize` 不产生物理运动，但会改变定位状态，并直接影响后续导航安全。只有在操作员能从当前地图和现场可靠估计完整 `x/y/yaw` 时才使用：

```bash
"$S1_PY" "$S1_CLI" relocalize \
  --x 1.0 --y 0.0 --yaw -1.5708 \
  --observe 15 --interval 1 --execute
```

RPC 返回成功不代表定位已经收敛。只有输出 `navigation_ready=true`，并且最终地图位姿与现场标志物一致，才可进入后续导航检查。绝不能把“零点”“home”或旧日志中的不完整位姿当成当前恢复目标。

## 11. 推荐的完整携箱作业清单

```text
[ ] 现场人员、急停、路径和箱体外廓净空已确认
[ ] 无其他 SDK/导航客户端占用机器人
[ ] pose：localized=true，导航不在 RUNNING/OCCUPIED
[ ] 当前箱体与 4317 固定 profile 完全一致且无滑移
[ ] payload-status-4317：登记前 tag 不存在
[ ] payload-register-4317 --execute：outcome=payload_registered
[ ] payload-status-4317：filter_registered/profile_matches 均为 true
[ ] probe-relative：计划方向和距离稳定可达
[ ] 用低速、短距离和收紧的 max-distance 执行 navigate/relative
[ ] 检查最终位姿、状态和现场结果，不只看 RPC 返回值
[ ] 导航完全停止后再进入释放/取消注册流程
[ ] payload-remove-4317 --execute：outcome=payload_removed
[ ] payload-status-4317：filter_registered=false
```

## 12. 官方 API 签名速查

以下签名摘取自用户提供的官方 S1 Python API 1.9.1 页面；在 SDK 1.9.0 主机上调用前仍应以当前 stub 为准。

```python
# 定位与状态
GalbotNavigation.is_localized() -> bool
GalbotNavigation.get_current_pose() -> list[float]
GalbotNavigation.get_navigation_status() -> NavigationTaskStatus
GalbotNavigation.check_goal_arrival() -> bool

# 路径和导航
GalbotNavigation.check_path_reachability(goal_pose, start_pose) -> bool
GalbotNavigation.navigate_to_goal_v2(
    goal_pose,
    max_vel,
    pose_frame="map",
    enable_collision_check=True,
    is_blocking=False,
    timeout=5.0,
    omni_plan=False,
) -> tuple
GalbotNavigation.stop_navigation() -> tuple

# 定位状态修改
GalbotNavigation.relocalize(init_pose) -> tuple

# fusion 过滤框
GalbotNavigation.add_bounding_box(box_info) -> tuple
GalbotNavigation.get_bounding_box() -> list
GalbotNavigation.remove_bounding_box(box_tag) -> tuple

# PNS 附着碰撞箱
GalbotNavigation.attach_box_to_link(
    box_info,
    ignore_collision_links=[],
) -> tuple
GalbotNavigation.detach_box_from_link(box_tag) -> tuple

# 底盘控制器切换
GalbotRobot.switch_controller(controller_name) -> ControlStatus
```

箱体 `box_info` 的官方字段结构为：

```python
{
    "box_size": [length_x, length_y, length_z],          # m
    "box_pose": [x, y, z, qx, qy, qz, qw],              # 相对 parent link
    "box_tag": 4317,                                     # 唯一标记
    "parent_link_name": "left_arm_end_effector_mount_link",
}
```

## 13. 维护约定

- 修改 `s1_navigation_cli.py` 的命令、默认值、4317 profile、退出判据或保护逻辑后，要同步更新本文。
- 新箱体不要直接复制 tag 4317；应建立新的可追溯 profile、父 frame、实体尺寸、过滤尺寸和独立测试。
- 每次现场运行应保存原始命令、完整 JSON 输出、时间、地图、箱体状态、操作员观察和异常日志。
- 失败实验应保留用于诊断，不要只留下“成功/失败”的口头结论。