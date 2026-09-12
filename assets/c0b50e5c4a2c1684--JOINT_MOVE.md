# 通用关节位置控制 v1

入口为 `run_g1_joint_move.sh`，实现为 `g1_joint_move.py`，依赖同目录的 `g1_arm_smoke_test.py`。沿用原双臂脚本的 SDK 初始化、限位交集、3°余量、反馈检查、非阻塞运动、到位监测和信号停止。旧脚本保留。

## 常用姿态 Hanging_down

`poses/Hanging_down.json` 保存左右臂各七个角度，单位 rad，顺序 joint1 到 joint7。按用户最新纠正，右臂逐项取左臂的相反数：

```text
left_arm:  [1.153, -1.295, -0.615, -0.433, -0.268, 0.0, 0.258]
right_arm: [-1.153, 1.295, 0.615, 0.433, 0.268, 0.0, -0.258]
```

名称是用户指定的标签，尚未在真机验证该姿态或运动路径。默认速度上限 0.03 rad/s；可通过命令行覆盖。

在脚本所在目录运行：

```bash
# PC 离线检查参数，无 SDK、无真机限位检查
./run_g1_joint_move.sh --pose Hanging_down --offline

# G1 本机预检：初始化 SDK 并读取当前状态，不下发运动
./run_g1_joint_move.sh --pose Hanging_down

# G1 只读查看左右臂当前状态
./run_g1_joint_move.sh --status

# 每 1 秒连续查看状态；Ctrl+C 只退出查看
./run_g1_joint_move.sh --status --watch 1

# 只查看左臂
./run_g1_joint_move.sh --status --arm left

# G1 交互 SSH 终端执行，预检通过后直接运动，无需输入确认字符
./run_g1_joint_move.sh --pose Hanging_down --speed-rad-s 0.03 --execute

# 单关节绝对目标角度，默认预检
./run_g1_joint_move.sh --joint left_arm_joint7=10 --unit deg --speed-rad-s 0.03

# 多关节
./run_g1_joint_move.sh --joint left_arm_joint1=20 --joint right_arm_joint7=5 --unit deg

# 整臂；双臂可同时传 --left-arm 和 --right-arm
./run_g1_joint_move.sh --left-arm 10 -20 0 -30 0 0 5 --unit deg

# 自定义姿态文件
./run_g1_joint_move.sh --pose-file poses/Hanging_down.json --speed-rad-s 0.02
```

默认只预检；`--execute` 才进入实际执行。`--offline` 与 `--execute` 互斥。直接输入必须指定 `--unit deg|rad`。未指定关节不发送目标，不补零。目标是绝对角度，不支持相对增量。`--timeout-s` 默认 180 秒，超时会请求停止，必要时可显式增大。

`--status` 是独立只读模式，默认分左右臂读取 14 个关节，输出位置（rad/deg）、速度、反馈年龄、轴间时间戳跨度、活动控制器、运动/静止判断和限位状态。SDK 初始化后的短暂空反馈会在 5 秒窗口内自动重试，避免一次空帧导致状态命令误报失败。它不调用 `set_joint_positions()` 或 `stop_trajectory_execution()`；`--status` 与目标参数、`--execute`、`--offline` 互斥。`--watch SECONDS` 只能和 `--status` 一起使用。G1 当前 SDK 的 `wait_for_shutdown()` 在只读客户端可能无限等待，因此只读模式输出快照后直接结束专用进程，依靠操作系统释放本地 SDK 客户端，不等待该 SDK 清理屏障；这不会影响机器人端持续运行的服务，也不会发送运动命令。

姿态文件不能与命令行角度混用，速度可覆盖。文件字段为 `version: 1`、`unit`、可选 `speed_rad_s`、`targets`；targets 支持 left_arm/right_arm 的七元素数组或完整关节名与数值。拒绝重复关节、未知字段、非有限数值和非正速度。内置 JSON 无新增依赖；外部 YAML 使用相同结构，需要 PyYAML，重复键会报错。

执行输出当前角度、目标和角度差，周期输出目标误差与反馈速度。到位要求误差不超过 0.2°、速度不超过 0.002 rad/s，持续 0.5 秒。成功保持目标位置；错误不自动重试或返回原位。Ctrl+C、SIGTERM、SIGHUP 会请求停止已提交的轨迹。网络断线未必立即传递信号，停止请求也不能替代物理急停。位置接口不做环境碰撞规划。

已部署目录：G1 `/home/galbot/g1_joint_move_20260910`。启动器沿用已验证的 G1 SDK 环境路径。

## 中断与退出修复

现场已确认旧版 Ctrl+C 后机械臂停住，但 SDK 清理卡住。SDK 的 `wait_for_shutdown()` 没有超时参数；旧版第二次 Ctrl+C 只设置标志，不能打断清理。

新版在停止命令成功后读取所选关节的新鲜反馈，检查速度和位置稳定性，通过才输出“所选关节已静止”。观察窗口为 5 秒；底层 SDK 读取若自身阻塞，窗口不能保证硬实时退出。该验证仅覆盖本次指定关节。

清理逐项打印进入和完成的 SDK 方法，仍按 `request_shutdown()` → `wait_for_shutdown()` → `destroy()` 顺序执行。独立子进程监督清理，总计 10 秒超时后仅强制结束本次脚本（通常 shell 退出码 137），即使原生 SDK 持有 Python GIL 也能执行超时。正常退出时监督子进程自动结束。清理阶段的信号会交给该超时保护处理，因为已安装的 G1 SDK 可能在 `request_shutdown()` 内部产生 SIGINT/SIGTERM；运动阶段 Ctrl+C 仍会先请求停止并验证反馈。强制结束脚本不等于机器人急停，也不表示 SDK 已正常销毁。

新代码不改变已运行的旧进程。修复部署本身不触发运动。

## 离线验证

```bash
python3 -m unittest discover -s g1_arm_smoke_test/tests -v
```

测试覆盖姿态数值、单位转换、关节顺序、参数冲突、失效反馈及命令提交失败时的停止请求。模拟测试不能替代真机 SDK 验证。