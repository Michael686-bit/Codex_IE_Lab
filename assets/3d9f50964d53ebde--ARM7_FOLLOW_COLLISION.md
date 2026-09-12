# 左臂七关节碰撞拒绝遥操作（第一版）

新入口是 `run_arm7_follow_collision.sh`，对应程序 `arm7_follow_collision.py`。
它读取 GP001 左臂七个位置，生成 G1 左臂七关节的连续短轨迹；每个候选目标在发送前都必须通过 GalbotMotion `check_collision()`。

当前版本的安全策略是 fail-closed：碰撞、服务失败、返回格式异常、场景为空、G1/GP001反馈过期、非左臂关节移动或时间戳回退，都会拒绝目标；已有运动则请求停止并确认七个关节静止。

## 当前配置和限制

- 映射配置：`arm7_collision_profile.json`。
- 七个关节暂用弧度制、方向 `+1`、比例 `1`、零偏 `0`，这是待标定的显式候选，不是七关节真机验收结论。
- 每个关节目标速度候选为 `0.3 rad/s`；碰撞查询实测约75 ms，因此轨迹段先用 `100 ms`。
- J7 固定绝对范围为 `[-45°, +45°]`；J1～J6 使用 URDF 限位向内保留3°。
- 七个关节启动时都必须与 GP001 相差不超过10°，G1全身静止至少0.5秒；这只放宽启动条件，不放宽机械限位或运行中的跟随保护。
- GP001 设备 `timestamp` 单位未知，只记录并检查有限性；帧新鲜度使用帧进入本机队列的单调时间，避免把设备时钟误当作 PC 时钟。
- 对齐和跟随阶段每0.5～1秒打印 GP001 主臂、G1 从臂和逐关节差值，角度单位为度，顺序均为 J1～J7。
- 当前配置的 `mapping` 是 `absolute_identity_pending_calibration`。因此 `--execute` 会主动拒绝启动，必须在逐关节方向、零位和范围真机验收后，把配置状态改为 `validated`。

## 只读运行

```bash
cd "/home/lsy03/文档/ChatGPT/VLA G1 项目"
bash teleoperation/run_arm7_follow_collision.sh --seconds 30
```

只读运行仍会调用碰撞检查，但绝不调用 `publish_target()`。当前 G1 碰撞场景含 `ground`，此前探针对当前状态返回 `True`；在这个结果解释清楚前，执行模式会按安全策略拒绝运动。

## 执行前必须完成

1. 解释当前 `ground` 场景下的碰撞结果，核对碰撞模型、底盘位姿和工具配置；不能通过删除障碍物或忽略碰撞来绕过。
2. 逐个验证 GP001→G1 的方向、零位和比例，并把结果写入配置；完成七关节小幅只读映射后再标记 `mapping=validated`。
3. 用真实桌面/墙壁的坐标和尺寸添加独立障碍物 ID，设置 `safe_margin`，保留场景版本记录。
4. 先只读联合运行，确认日志中出现 `collision_allow` 且状态为 `collision=false`；任何 `collision_reject` 都不能执行。
5. 按单关节、双关节、七关节顺序进行现场验证，保持物理急停可触达。

执行命令（完成上述验收后）：

```bash
bash teleoperation/run_arm7_follow_collision.sh --execute --seconds 30
```

日志保存到 `lerobot_runs/arm7_follow_collision_*.jsonl`，其中每条允许发送的目标都绑定了全身反馈、候选目标、场景清单和碰撞查询耗时。