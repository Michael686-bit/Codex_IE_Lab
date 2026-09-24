# 输入 TCP 预抓取位，移动 S1 单臂

2026-09-11：本地实验脚本，未部署、未在真机运行。使用已检查生产源码的 SDK
IK/FK/碰撞辅助函数；运行时兼容性、路径净空和运动效果均待验证。

`move_to_pregrasp.py` 输入指定侧 GE103v1 TCP 在 **base_link** 下的位置（米）和
RPY（度，`Rz(yaw) Ry(pitch) Rx(roll)`）。RPY 必须明确提供。`0 0 0` 表示
TCP 坐标轴与 base_link 对齐，不代表七个关节回零。不自动应用 ±50 mm/−35 mm
标定偏移，也不自动抓取、合爪、提升、返回或切换控制器。

仅支持空载单臂；另一臂、夹爪、腰、头、底盘不接收运动命令。目标是 TCP
端点，过程中使用七关节五次插值，TCP 路径不保证直线。与 one-click 的原生
IMC PTP/LIN 路线不同。模型峰值关节速度默认 0.05 rad/s、上限 0.1 rad/s；
解析峰值加速度不超过 0.1 rad/s²，但 SDK 插值和实机速度仍需验证。

## 依赖与执行位置

把脚本单独复制至 S1 的独立实验目录，在 **S1 宿主机** 使用
`/home/galbot/ie_lab/bin/s1-python`。脚本依赖 NumPy、SDK，以及既有文件：

`/home/galbot/ie_lab/projects/dual_arm_v5/workspace/s1_sjtu_0806/tools/host_mode00_pregrasp_sdk_runner.py`

只导入其中辅助函数，不调用其 main/run_pregrasp。输出记录 helper 和 URDF
哈希。共享宿主机 `/home/galbot/ie_lab/control.lock`；容器运行被拒绝。
不得与其他控制任务并行。已有工具挂载时仍拒绝覆盖。
2026-09-11 用户要求简化后：移除持箱标记读取和 map 定位依赖，不初始化
GalbotNavigation，不再使用定位位移门限。自碰撞查询仅使用机器人里程计
快照提供基座姿态；不使用该快照判断地图漂移或环境避障。底盘静止、空载和
净空由执行前的一次现场确认覆盖。IK、关节限位、自碰撞、起点一致性保留。

## 使用

假设脚本已放在 `/home/galbot/Lsy03/direct_pregrasp/move_to_pregrasp.py`。
先在机器人静止时规划（**这会连接 SDK，并临时 attach/detach GE103 碰撞模型，
但不发送运动命令，不是纯离线或纯 getter 操作**）：

```bash
/home/galbot/ie_lab/bin/s1-python /home/galbot/Lsy03/direct_pregrasp/move_to_pregrasp.py \
  --arm right --xyz 0.924421 -0.350638 0.603564 --rpy-deg 0 0 0 \
  --output /home/galbot/Lsy03/direct_pregrasp/right_plan_01.json
```

数字仅演示参数写法，来自 9/11 FDP 原始几何候选；不是当前有效目标或安全运动
推荐。该示例显式选择生产预抓取的 RPY=0，不保留原几何报告中的姿态。
用户应填写当前经过核对的目标和姿态，不要使用陈旧感知坐标。

检查 JSON 的 `plan.goal_joint_rad`、`plan.tcp_preview` 和 `plan.waypoints_rad`。
现场核对完整工作区（包括肘部、另一臂、箱体、邻箱及线缆）与物理急停后，使用
同一输入及一个新的输出文件，附加：

```text
--execute
```

执行模式重新基于实时状态求解；显示本次具体计划后，要求输入绑定该计划的
`MOVE RIGHT <哈希>`（左臂为 LEFT）。先前计划或确认不会自动批准新计划。
确认后再次检查起点和整条离散路径，再非阻塞提交一次单臂轨迹；反馈超时、
异常、Ctrl+C/SIGTERM 尝试停止，失败不自动恢复。停止 API 的作用域可能涉及
所有活动关节轨迹，因此必须独占控制；SDK RPC 卡住时软件停止无保证，使用物理急停。

碰撞检查复用生产 helper，覆盖双臂和 GE103 **自碰撞离散样本**；没有自动加入
箱体/环境障碍，不能证明连续路径或环境避障。仿真/规划审阅和现场确认是必要的。
单次任一关节变化超过 2 rad 会拒绝；已接近目标（最大关节差 <=0.03 rad）时
执行被拒绝，以免将旧 COMPLETED 状态误判为本次动作完成。

## 本地验证

```bash
python3 -m unittest discover -s experiments/20260911_direct_pregrasp -v
python3 experiments/20260911_direct_pregrasp/move_to_pregrasp.py --help
```

九项本地测试通过。测试使用假 SDK 检查单臂命令范围、执行前拒绝、提交异常/超时/中断/反馈失败的
停止行为，同时验证位姿旋转、米制输入和插值速度/加速度。它不构成真机验证。
旧的三个 `--confirm-workcell-clear`、`--confirm-empty-gripper`、
`--ignore-stale-carried-marker` 参数仅为旧命令兼容而保留，不再需要。

前序说明修正：FDP 左 TCP `[0.973265,0.317579,0.603564]` 加
`[-0.035,-0.05,0]` 后应是 `[0.938265,0.267579,0.603564]`。