# G1 只读状态适配

本目录当前只提供左臂状态读取，不提供运动入口。

读取内容包括：7 个关节名、位置、速度、反馈时间戳、活动控制器，以及活动 URDF 和标定 URDF 的保守限位交集。状态必须新鲜、顺序正确且持续静止，否则失败退出。

在 G1 上把项目的 `robot_g1/`、`teleoperation/` 和 `g1_arm_smoke_test/` 放到同一个工作目录后运行：

```bash
bash robot_g1/run_read_g1_state.sh
```

输出是 `galbot.g1.read_only_snapshot` JSON。脚本只初始化 SDK、调用状态读取接口，然后执行 `request_shutdown → wait_for_shutdown → destroy`；不会调用关节、夹爪、底盘或轨迹运动接口。

构造第 7 关节接收策略预览：

```bash
source /opt/galbot/galbot_sdk/linux-aarch64-gcc940/setup.sh
export PYTHONPATH="/data/galbot/lib:${PYTHONPATH:-}"
/usr/bin/python3 -B -m teleoperation.g1_sdk_policy_preview
```

这仍然不是网络接收器或真机运动程序。策略预览完成后 SDK 会被清理；若机器人状态随后发生变化，该快照立即视为过期，不能用于真机运动。

2026-09-07 的 G1 实测结果见 [READ_ONLY_VALIDATION.md](READ_ONLY_VALIDATION.md)。