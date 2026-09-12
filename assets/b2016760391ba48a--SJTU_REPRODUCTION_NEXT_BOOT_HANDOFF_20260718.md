# Codex 自用接续记录：SJTU 单入口流程（2026-07-18 关机前）

本文件是下次机器人开机后的第一读取入口。不要根据旧 PID、旧 ROS 图或“上次能跑”直接发送运动命令；先按本文重新确认实际环境。

## 1. 本轮已经完成

- 已建立单入口 `scripts/robot_sjtu_reproduction_pipeline.py`，当前真实执行边界为 `first_draw`。
- 自动上层选择支持 `00/01/10`，固定要求 H4，H4 间距按实测 `0.165 m`。
- SAM 后底盘精接近使用所选料箱的原始几何中心，不再把抓取补偿混入导航参考点。
- FDP 采用跨视角三维目标身份锁：共同 `odom` 坐标、同型号、同 H4、默认 `0.15 m` 硬门限；严格区分 `source_roi_index` 与目标优先重排后的 `mask_index`。
- `fdp-low` 已改为只移动拍照臂：`10 -> 左臂`，`01/00 -> 右臂`。
- 三种首抓 adapter 已接入：
  - `10`: 右臂，保留高度 `+15 mm`、深度 `+20 mm`，终点 `right_draw`；
  - `01`: 左臂，使用 FAR1/FAR2，不继承 mode10 补偿，终点 `left_draw`；
  - `00`: 双臂，高度 `+20 mm`，锁定 `object_in_left_base`，终点映射为 `dual_near`。
- 已实现一个 Driver 内的 SDK/PNS 全局导航与局部 `cmd_vel_odom` 仲裁补丁。局部通道只接受 `/sdk_target_pos_pro_navigation_bridge`，带限速、非有限数拒绝、陈旧命令重复清零和互斥所有权。
- 已预留但未实现/未验证：`second_fdp -> handoff -> carry_ready -> nav_unload -> place -> return_to_stack -> side_change -> cycle_complete`。
- 固定卸货地图位已经写入计划但不能执行：`map (-0.4, -2.3, yaw=-0.7 rad)`。
- 本地完整测试：`44 passed`；主脚本、Driver patch 和 shell 均通过语法检查，包括 runtime launcher heredoc 内层脚本。

注意：H4 层间有效高度使用 `0.165 m`，抓取几何/mesh 的箱体高度仍沿用已验证的 `0.175 m`。下次不要未经实验把两者统一成一个数。

## 2. 关机前最后状态（只用于审计，不可直接复用）

最后一次确认时间约为 2026-07-18 16:08：

- `roscore`: PID `21425`。
- SDK-hybrid Driver: PID `517345`，`_nav_mode:=sdk`，`_sdk_nav_enable_motion:=true`。
- 局部桥: PID `517905`，`_backend:=cmd_vel_odom`，`_enable_motion:=true`。
- Driver 启动后状态为 `SDK ready; localized=True; motion=True`。
- `/sjtu/nav/local_direct_state` 最后为 `idle`。
- 本轮从未向新 Driver 发布全局目标或局部 Twist；没有做新混合通道的物理小步验证。
- 双臂在无运动健康门时读取到接近 SAM 的关节位，随后只重启了 Driver，没有发机械臂命令。
- 相机 RGB/Depth、双臂关节、LiDAR、IMU、`/wheel_odom`、`/hand_camera_transform` 均采样成功。
- Workbin bridge 已重启到新源码，health 的 `source_sha256` 为 `c550c377...60696327`；配置为 `4317`、H4 单位 `0.165`、nearest-depth、crop `0.25/0.20`、面积比例 `0.08680555555555557`。
- FDP 服务 health 正常并已调用 `/warmup`，tracker 已存在。

用户随后要求停止并将机器人关机。不要假设上述进程、PID、定位状态或话题关系能跨关机保持。

## 3. 尚未部署的最后一处修正

本地 `scripts/run_robot_sjtu_reproduction.sh` 已新增：

- `source /opt/ros/noetic/setup.bash`；
- `ROS_MASTER_URI=http://10.34.216.132:11311`；
- `ROS_IP=10.34.216.132`；
- 清理代理并设置 `NO_PROXY`。

这次修正发生在用户要求停止之后，**尚未重新部署到机器人**。因此下次开机第一轮脚本部署必须重新执行：

```bash
cd /home/c/workspace/260611_sjtu_workbin_movement/migrate_back/g1_workbin_perception
scripts/deploy_robot_sjtu_reproduction_runtime.sh
```

部署脚本只复制、编译并做 dry-run，不启动 Driver、不发运动目标。

## 4. DriverNode 与源码备份

本地快照目录：

```text
robot_runtime_backups/20260718_pre_shutdown/
```

包含：

- `galbot_driver_node_candidate.py`，SHA-256 `4d070c7ed438192be7ddc5e405209fb327da218d4cc0fb757eecc50d26edae5d`；
- 已安装的 hybrid `nav_driver.py`，SHA-256 `829ff46981cd34daf9ffd9a31a11be736c272487887043cf935ec556090f49ad`；
- 安装前原版 `nav_driver.py.pre_sdk_hybrid_20260718.20260718_155651.bak`，SHA-256 `147e9303569932a43b52c13a37c054aaafae68fd148f7e4f7aaf44fb6073bcf9`；
- motion-enabled Driver 与局部桥的启动日志快照。

机器人上也保留原版备份：

```text
/home/galbot/workspace/galbot_bringup/src/galbot_bringup/
  nav_driver.py.pre_sdk_hybrid_20260718.20260718_155651.bak
```

下次先运行只读检查：

```bash
robot_runtime_patches/sdk_hybrid_nav_20260718/install_on_robot.sh --check
```

处理规则：

1. 远端 `nav_driver.py` 是 patched SHA：继续审计进程配置，不重复覆盖。
2. 是 known base SHA：确认没有队友新改动后才 `--deploy`。
3. 两者都不是：立即停止部署，先把未知版本和 candidate driver 复制到新的日期快照，做 diff；禁止覆盖。
4. candidate driver SHA 只要不等于上面记录值，同样先备份和检查其 NavDriver 构造、SDK 初始化与 topic 参数接口。

## 5. 下次开机必须假定会变化的环境

SDK/GBS 版本按用户说明可视为不变，但以下全部视为未知：

- 是否已有 DriverNode 自动启动、由谁启动、`nav_mode` 是 `ros` 还是 `sdk`；
- DriverNode 源码是否被开机脚本、队友或同步操作替换；
- 是否出现多个 roscore、多个 candidate Driver 或多个局部桥；
- ROS master/IP、机器人局域网连接和实际主机名；
- HPU 当前是否仍为 `WORKING_MODE`，充电枪、即停、关键硬件服务是否恢复完毕；
- SDK 是否仍显示 localized，当前地图是否仍为这次固定点使用的地图；
- `/wheel_odom` 是否重新归零（允许归零，但每次跨视角锁定必须在同一轮内使用一致 odom）；
- 工作站 8040 Workbin 与 7876 FDP 是否仍在运行、是否加载了相同源码和参数；
- 机器人 `/home/galbot/workspace/hmy`、`DualMobManip`、`codex_robot_ops` 中部署文件是否被改动。

## 6. 下次开机恢复顺序（先无运动）

### A. 网络、HPU 与进程审计

1. 检查机器人 `10.34.216.132`、Thor `10.34.216.11`、工作站服务地址 `10.34.216.13`。
2. 查最新 HPU launcher 日志，必须看到当前 `Cur mode:WORKING_MODE`。
3. 确认关键服务：motion plan、robot state、左右腕相机、头相机、LiDAR/data backflow。
4. 精确列出 roscore、DriverNode、局部桥；不要用旧 PID。
5. 如果已有不匹配 Driver：保存 `ps` 命令行、ROS params、源码 SHA 和日志；只有机器人静止且用户知情后，才对唯一确认 PID 发 SIGINT。不得 `kill -9`，不得并行启动第二个 Driver。

### B. 源码与服务

1. 执行上面的 Driver `--check` 与 candidate SHA 审计。
2. 执行 `scripts/deploy_robot_sjtu_reproduction_runtime.sh`，部署尚缺的 ROS wrapper 修正。
3. 用明确环境变量启动/复用 Workbin bridge；health 必须匹配源码 SHA、`4317`、H4=`0.165`、mask 顺序契约和请求 profile。
4. 启动/复用 FDP，检查 `/health` 并调用 `/warmup`。

### C. motion-disabled 健康门

在没有 Driver/桥或已受控结束旧进程后：

```bash
scripts/start_robot_sjtu_sdk_nav_runtime.sh --motion-disabled
```

必须确认：

- 恰好一个 candidate Driver；
- `nav_mode=sdk`、`sdk_nav_enable_motion=false`；
- `local_direct_state=motion_disabled`；
- SDK localized；
- RGB/Depth、关节、LiDAR、IMU、odom、外参话题都有新数据；
- 双臂实际姿态与反馈一致；
- 日志没有 sensor readiness、WBC、相机或 SDK navigation 初始化错误。

完成后受控 SIGINT 结束这个唯一 Driver 和局部桥，再启动正式配置：

```bash
scripts/start_robot_sjtu_sdk_nav_runtime.sh
```

只启动不代表允许马上移动。先要求 `local_direct_state=idle`，并运行单入口到 preflight：

```bash
ssh galbot@10.34.216.132 \
  '/home/galbot/workspace/hmy/run_sjtu_reproduction.sh \
    --run-dir /home/galbot/workspace/hmy/output/<NEW_STAMP>_preflight \
    --execute --i-know-this-moves-the-robot \
    --mode auto --stop-after preflight'
```

上次这个命令已通过 ROS ownership 和感知服务检查，但旧 wrapper 未 source ROS，最终报 `No module named rospy`；本地 wrapper 已修，尚待部署并重跑。

## 7. 物理验证顺序（必须重新取得用户现场确认）

在任何物理动作前明确确认：充电已拔、即停已松、用户在机器人旁并准备即停、底盘周围净空、料垛未进入机械臂/相机危险区。

1. **局部直控最小验证**：只动底盘，不动手臂。当前局部终点容差是 `0.04 m`，所以不要发送 `0.02 m` 目标（会直接判到位）。建议发送 `0.06 m` 的 `base_link` 目标，预计实际移动约 `0.02 m` 后进入 4 cm 容差；监控 `/moving_state_pro`、`/galbot/status_text_pro`、`/sjtu/nav/local_direct_state` 和 odom，确认完成后重复零速、所有权回到 `idle`。
2. **SDK 全局导航验证**：确认局部所有权 `idle` 后，再测试固定 SAM 地图点 `map (0.31,-0.60,0.023)`。保留 0.7 m 安全半径和静态路径检查；被拒绝就停止分析，不改半径。
3. **只到 FDP 身份锁**：首次完整链建议先 `--stop-after fdp_target_lock`，验证选中 mode、底盘终姿、单臂 FDP-low、三维候选距离和 mask 可视化，不进入预抓取。
4. **两次首抓完整实验**：上一步人工确认后再执行到 `first_draw`。每次都由用户准备即停，并在两轮之间恢复料垛/机器人起点。

正式命令模板：

```bash
/home/galbot/workspace/hmy/run_sjtu_reproduction.sh \
  --execute \
  --i-know-this-moves-the-robot \
  --mode auto \
  --stop-after first_draw
```

## 8. 仍需重点审查的风险

- 新 SDK-hybrid Driver 已完成 fake 回归和无运动初始化，但尚未在真机验证“GalbotNavigation 已 init 且 idle 时，shared GalbotRobot 接受局部 set_base_velocity”。这是下次最高优先级实验，不可被完整抓取掩盖。
- 跨视角锁依赖两次采图期间底盘静止和 odom 连续；若 Driver 重启发生在两帧之间，必须整轮作废并从 SAM 重来。
- mode00/01/10 的首抓 adapter 来自各自成功实验，不得互相镜像补偿。
- Workbin `source_sha256` 写死在当前单入口默认参数；只要桥源码改变，必须审查后同步更新默认 SHA，而不是用命令行绕过。
- 卸货、放置、返回和换边只是 schema 预留，没有现场验证，不可把状态名当作已实现功能。

## 9. 核心本地文件校验值

```text
0119ec9f...944b6  scripts/robot_sjtu_reproduction_pipeline.py
0b1001f8...b0e4  scripts/robot_sjtu_mode10_full_pipeline.py
9fcc3f11...450d  scripts/run_robot_sjtu_reproduction.sh
3529ef9f...7c1  scripts/deploy_robot_sjtu_reproduction_runtime.sh
d277237a...96d7  scripts/start_robot_sjtu_sdk_nav_runtime.sh
c550c377...6327  scripts/serve_workbin_sam3_lingbot_bridge.py
b1f5ba33...83e7  src/g1_workbin_perception/fdp_identity_lock.py
693f80e9...17b2  src/g1_workbin_perception/navigation_geometry.py
829ff469...f49ad  robot_runtime_patches/sdk_hybrid_nav_20260718/nav_driver.py
```

恢复工作时先重新计算完整 SHA，不要只比较本文省略显示的前后缀。

## 10. 2026-07-22 本地流程更新（尚未部署、尚未真机验证）

当前完整流程入口改为
`scripts/robot_sjtu_sdk_no_collision_full_cycle.py`。机器人在上一次放置动作异常后已由现场即停；本节变更只写入本地工作区，未解除即停、未写机器人文件、未发送运动命令。

标准搬运参考关节位姿记录如下：

```text
left_arm  [1.531224, -1.191664, -0.373357, -2.065983, -1.866879, -0.309768, 0.066513]
right_arm [-1.531153, 1.191590, 0.373404, 2.066032, 1.866904, 0.309770, -0.066658]
```

执行策略不是分别把两臂做关节插值。流程先对上述关节做 FK，再读取实时
`Tleft2ee`、`Tright2ee` 和 `Tleft2right`，保持当前夹爪间相对变换不变，生成成对的
`DualArm moveByLin` 小段轨迹。标准右臂参考与刚性保持结果若相差超过 `0.03 m`
或 `5 deg`，在发臂命令前失败退出，避免挤压或拉脱料箱。

卸货处不再升降腰：`carry_raise_waist` 和 `place_lower_waist` 已从状态机删除，放置
下移阶段为 `place_lower_arms`，由双臂保持夹持几何向下移动。松爪后的左右各
`0.10 m` 外扩改为从实时末端位姿计算，不再复用抓取阶段旧目标。

下一次真机运行默认 `--stop-after sdk_nav_to_unload`，到达卸货地图位后必须停住，
由现场检查新搬运姿态的高度和水平位置；本轮不自动下放、松爪或外扩。只有明确
指定更晚的 `--stop-after` 才会进入放置阶段。

## 11. 2026-07-23 即停后的搬运策略修正（仅本地）

右臂高度补偿已由 `0.015m` 改为 `0.025m`。最近一轮两爪闭合后，旧流程单独
上提左臂有效 `0.06m`，导致实时夹持几何与记录标准位姿不兼容；刚性门测得
`0.0538m / 1.73deg` 后拒绝执行标准位姿。后续底盘通道出现
`ControlStatus.FAULT`，现场已即停。

本地入口现已改为参考 SJTU mode 00 的实时双臂回收：

- 左爪闭合后不再单独移动左臂；
- 从实时双末端姿态生成保持夹爪相对变换的共同上提 `0.10m`；
- 再沿实时抓取局部 `-X` 共同回收 `0.05m`；
- 记录的标准关节位不再执行，只保留作诊断；
- 卸货处仍由双臂共同下放 `0.08m`，腰不动。

主脚本、FK helper 编译通过，单测 `10 passed`，完整 dry-run 通过。以上修改尚未
部署到机器人；下次必须先确认即停恢复、`WORKING_MODE`、Driver 速度通道不再
返回 `ControlStatus.FAULT`，再从 SAM 新开 run-dir，禁止续用本次持箱中途状态。

## 12. 2026-07-24 底盘 transport 切换

SDK/local-direct 临时底盘方案停止作为后续实验入口。完整流程的标准入口改为：

```text
scripts/robot_sjtu_target_pos_full_cycle.py
```

`robot_sjtu_sdk_no_collision_full_cycle.py` 只作为 targetpos 版本复用的感知、抓取、
双臂搬运和释放实现保留，不再直接执行其底盘路线。完整归档说明见：

```text
docs/archive/SDK_LOCAL_DIRECT_BASE_TRANSPORT_ARCHIVED_20260724.md
```

真机已验证 SLAM/local-planner 的 `/target_pos` 路线可到达
`(-0.3, -2.4, -30deg)` 和 `(0.2, 0.5, 2deg)`。注意 `/target_pos` 当前同时被
`/local_planner_node` 和 `/galbot_driver_node` 订阅；后者会直接调用 SDK
`navigate_to_goal_v2`，与 local planner 发布的 `/waypoints` 竞争。不能杀掉整个
driver，因为它仍是 `/waypoints` 的执行端。需要在明确允许重启 driver 后，仅把
driver 的 direct target topic 隔离，保留 `/waypoints`。

## 13. 2026-07-25 当前 local-planner 拓扑的 maunal_ver

当前拓扑已变为
`/target_pos -> /local_planner_node -> /waypoints -> /galbot_driver_node`，且
`/local_planner_node/robot/get_local_pose=false`。当前 planner callback 不使用
消息的 `header.frame_id`，因此原 targetpos 脚本发布的 SAM→FDP、抓取后后撤这两类
`base_link` 相对目标会被误当作地图绝对坐标。

保留原入口不动，另增当前环境专用入口：

```text
scripts/robot_sjtu_target_pos_full_cycle_maunal_ver.py
scripts/run_robot_sjtu_targetpos_full_cycle_maunal_ver.sh
```

该版本仅在发布相对底盘段前读取 `/Odometry_robot`，同时采用
`/local_planner_node/robot/odom_yaw_offset_rad`，把相对 XY/yaw 转为地图绝对目标；
卸货点和 SAM 点仍直接使用原地图坐标。每次换算会写入
`plans/*_maunal_ver_frame_conversion.json`。预检要求 `/target_pos` 只有一个订阅者，
并要求 `get_local_pose=false`；如果环境恢复为 planner 自己换算相对目标，该版本会
拒绝运行，以避免重复变换。