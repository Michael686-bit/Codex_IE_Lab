# G1 原生碰撞检查接入验证（2026-09-11）

当前状态：只读探针已运行，尚未接入 j7_follow.py 的运动放行条件。
本次没有发送运动、规划执行指令，也没有添加、删除障碍物或工具。

## 实测

- 本机 PC SDK 的 GalbotRobot、GalbotMotion 均可初始化，全身21关节状态通过名称、数值和时间戳检查。
- 官方示例的基础 RobotStates（whole_body_joint + base_state）在本机返回 INVALID_INPUT；默认 Parameter 也一样。
- JointStates 指定 left_arm、七关节位置，同时携带21关节 whole_body_joint 后返回 SUCCESS。
- 十次查询全部返回 True（碰撞）；已有障碍物清单为 ground。
- 十次耗时16.45～77.66ms，平均70.40ms；首帧后约75～78ms。不是批量轨迹检查的性能结论。
- 复测零位和 SDK 官方示例姿态仍返回 True；把假设底盘 z 改为1 m或10 m也仍返回 True，尚未能把结果归因于 ground。
- `enable_collision_check=False` 复测仍返回 True，说明当前 SDK/部署对该参数或返回值还需进一步核对，不能把这次结果直接当作可放行依据。
- base_state 暂用单位位姿，仅用于接口/模型诊断，尚未验证与世界坐标、ground 的关系。
- 不能据此确定真实发生接触，也不能认定是误报；接口未提供本次碰撞对。
- 尚未核对真机服务版本、碰撞模型、夹爪工具和实际底盘位姿；未验证桌面或墙壁。

日志：collision_probe_20260911.jsonl。

## 复现

```bash
bash teleoperation/run_collision_probe.sh --samples 10
# 零位、官方示例姿态仅用于诊断，不会发送运动
bash teleoperation/run_collision_probe.sh --samples 3 --pose zero
bash teleoperation/run_collision_probe.sh --samples 3 --pose sample
```

独立 Docker 只读挂载项目，无 GP001 设备依赖，外层25秒超时。
成功退出只表示查询成功，不表示状态无碰撞；检查 collision_count。
两项状态校验单元测试及启动脚本语法检查通过。

## 接入次序

1. 核对真机版本、模型、base/world变换、ground及工具模型，解释当前True结果。不能删除ground或忽略碰撞来绕过。
2. 确认桌面尺寸和其在已验证坐标系中的位姿，以独立ID添加box、安全余量；只清理本次自己创建的对象，禁止clear_obstacle全清场景。
3. 在独立进程运行查询，测量批量候选轨迹的延迟；检查全身实测、从实测到待发起点及目标段的采样状态。
4. 执行端仅放行绑定到相同目标、全身状态和场景版本且未过期的成功无碰撞结果。错误、碰撞、超时、状态变化或工作进程退出都停止/禁止发送，不使用上一条结果默认放行。
5. 规划前视时域要覆盖查询延迟、通信延迟和实测停止距离；候选轨迹离散采样不是连续碰撞证明。
6. 先只读影子检查，再验证故障与停止行为，再接入运动。保持J7 0.3rad/s和绝对[-45°,45°]基线。

motion_plan/motion_plan_multi_waypoints适合初始化和明确路径规划，不应未经时延验证就逐帧重规划。
attach_tool/attach_target_object必须来自实际工具和抓取物几何；safe_margin是几何余量，不能代替停止距离。

本地依据：.vendor/galbot-pc-sdk/examples/g1/python/galbot_motion/check_collision.py、add_obstacle.py及g1/__init__.pyi。
官方参考：https://developer.galbot.com/docs/SDK/1.9.1/g1/en/api_python_reference/