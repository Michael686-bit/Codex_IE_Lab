# GP001 → G1 单臂映射（第一版）

左臂七关节碰撞拒绝跟随的新入口和验收边界见
[ARM7_FOLLOW_COLLISION.md](ARM7_FOLLOW_COLLISION.md)。该入口当前默认只读；碰撞检查失败或返回碰撞时拒绝运动。

## 当前进展（2026-09-10）

**当前选定映射已更新为直接角度映射**：`G1目标 = GP001驱动输出角度`，方向 +1、比例 1、
不减 GP 起点、不加 G1 起点或零偏。下面旧相对映射章节描述的是历史代码，不能用于本轮真机验证。
J7 真机准备记录见 [4J7 直接映射验证准备](J7_DIRECT_VALIDATION_20260910.md)。
只读对齐入口：`bash teleoperation/run_j7_direct_preview.sh`；没有运动选项。
新增小步跟随入口：`bash teleoperation/run_j7_follow.sh`（默认只读），
加 `--execute` 才运行真机。范围、速度和现场步骤见 [J7跟随使用说明](J7_FOLLOW_USAGE.md)。

有线与双端读取已恢复；GP001 中文引导控件辨识已完成首轮，61700 个有效帧、0 个应用
无效帧、52 个步骤标记。6 个连续轴通道及 12 个普通按钮已有观测对应关系。
正式成果、证据校验值、对应表和待验证项见 [GP001 第一轮辨识结论](GP001_IDENTIFICATION_20260910.md)。
G1 全臂映射、组合键/长按语义及真机跟随尚未验收。

历史状态（2026-09-08）：接收端独立限速和超时复核已同步 G1；两端 39 项遥操、2 项只读测试通过。401 条跨机合成目标全部接受，故意断流后 1 条迟到位置被拒绝，预览输出变化率不超过 0.03 rad/s。当时 GP001 USB 尚未被宿主识别，实时读取待恢复。证据与限制见 [合成验证记录](SYNTHETIC_VALIDATION_20260908.md)。

`mapping.py` 只实现映射计算；本目录另有 GP001 实时读取、G1 只读联合预览和网络 dry-run 工具。GP001 监视器不调用 G1 运动接口。

## 当前边界

- 默认只开放左臂第 7 关节（索引 6）。
- 使用相对映射：

  `q_g1_target = q_g1_start + direction × scale × (q_gp001 - q_gp001_start)`

- `q_g1_start` 必须来自同一次 G1 状态读取；不能用 `zero/home` 猜测。
- `q_gp001_start` 应在操作者保持中立时采集。
- GP001 采集文件的 `position_unit` 字段仍是 `unknown`；但 SynthNova 官方 G1 示例把 GP001 位置直接传给单位为弧度的仿真关节接口，因此当前 G1 路线将其按 `radian` 处理。配置仍需显式写出单位，代码拒绝 `unknown`。
- 方向、比例和限位均是配置项。第 7 关节的方向尚未通过 GP001→G1 真机映射验收，不能把默认 `+1` 当作实测结论。
- 每一帧目标依据实际时间间隔按 `max_speed_rad_s × elapsed` 限制，不能用固定“每帧角度”替代速度约束。
- 过期、时间逆序、序号回退、越过保守限位或首帧偏离过大的数据会拒绝。

## 离线验证

```bash
python3 -B -m unittest discover -s teleoperation/tests -v
```

本轮历史数据回放结果见 [OFFLINE_VALIDATION.md](OFFLINE_VALIDATION.md)。

## 消息协议与接收端门控

- `protocol.py` 定义带版本的 JSON/UDP 消息，只支持 `disable` 和 `position`。
- 新 `session_id` 必须先发送 `disable`；网络消息不能自行给接收端授权。
- 接收端需在本地显式授权后才接受位置预览。
- 第一阶段只允许 `left_arm_joint7`、相对起点 ±1°、预览输出变化率不超过 0.03 rad/s。当前 TTL 候选上限为 300 ms；昨日 200 ms 超时根因尚未定位，不能认定提高阈值已解决问题。真机前仍须验证 SDK 停止语义。
- 重复/回退序号、未开放关节、越限、超速和超时都拒绝；看门狗超时后必须先收到新的 `disable` 边界，再由本地重新授权。
- 发送端和接收端的 monotonic clock 不可直接相减；接收端用本地到达时间执行看门狗。
- 当前 UDP dry-run 没有身份认证或真机 SDK 适配，不能作为真机部署入口；真机版还需固定发送端来源并增加认证/部署边界。

## GP001 全控件监视与记录

推荐使用中文引导模式，第一帧有效数据到达后逐步提示动作。回车开始，自动倒计时并
记录步骤开始/结束；`s` 跳过，`r` 重做上一步，`q` 保存退出。每次自动生成新文件。
本轮包含静止基线、扳机、摇杆及普通按钮短按，组合键、长按及急停另轮辨识。

```bash
cd "/home/lsy03/文档/ChatGPT/VLA G1 项目"
set +x
set -a
source /home/lsy03/.config/synthnova/credentials.env
set +a
SYNTHNOVA_MODULE_ROOT="/home/lsy03/Lsy03_document/仿真软件/extracted/synthnova_delivery_20260801/delivery_dir/synthnova_delivery/module" \
  bash docker/run.sh python3 -B -m teleoperation.gp001_input_monitor --guided
```

引导模式不刷长行，避免打断输入提示；自由监视模式仍按指定间隔显示状态。
2026-09-10 修复了状态刷新中秒/纳秒混用导致不显示的问题，以及 age 计算单位错误。

`gp001_input_monitor.py` 复用 SynthNova 的 `remote_control_lite.GalbotDriver`
只读取 GP001，不导入 G1 SDK，也不发送机器人命令。它将解码后的完整公开帧保存
为 JSONL，并额外记录按钮按下/释放和轴变化事件；`--marker-stdin` 可从终端写入
人工辨识标签。

## 通过 LeRobot 标准入口进行 GP001 标定

项目已注册 `gp001` teleoperator。`lerobot-calibrate` 会调用适配器的
`connect(calibrate=False)` 和 `calibrate()`；`live_driver` 模式直接从 GP001 串口
读取数据，整个流程不会连接 G1 或发送运动命令。默认会引导静止基线、左右臂 14
个关节的正向/负向动作和回中，并检查最小变化、联动、回中误差以及 GP 索引是否一一
对应。

在项目根目录执行（容器内的 `/workspace` 对应项目根目录）：

```bash
set -a
source /home/lsy03/.config/synthnova/credentials.env
set +a

SYNTHNOVA_MODULE_ROOT="/home/lsy03/Lsy03_document/仿真软件/extracted/synthnova_delivery_20260801/delivery_dir/synthnova_delivery/module" \
  bash docker/run.sh lerobot-calibrate \
  --teleop.type=gp001 \
  --teleop.id=gp001-main \
  --teleop.source_mode=live_driver \
  --teleop.port=/dev/ttyACM0 \
  --teleop.calibration_dir=/workspace/.docker-cache/huggingface/lerobot/calibration/teleoperators/gp001 \
  --teleop.position_unit=unknown
```

提示出现后按回车开始每个时间窗；`s` 跳过当前步骤，`q` 保存失败记录并退出。
实时源首帧默认最多等待 5 秒；如果 GP001 上电较慢，可以增加
`--teleop.startup_timeout_s=10`。
成功时按 LeRobot 的 ID 约定写入 `gp001-main.json`，同时生成带时间戳的 `_raw.jsonl`
和 `_report.md`。失败或中断只生成原始记录和报告，不会覆盖已有通过配置。

`position_unit=unknown` 表示单位仍未由现场已知角度核验；它可以完成输入标定，但
后续 GP001→G1 映射启动前仍必须显式确认单位并设置 `radian` 或 `degree`。如果暂时
只想用已有 JSONL 做离线演练，把 `source_mode` 改为 `replay` 并提供
`--teleop.capture_path=/workspace/lerobot_runs/<capture>.jsonl`，再把
`--teleop.calibration_interactive=false` 用于自动化测试。

GP001 的按钮和轴变化本身会自动写入每帧的 `sample` 与 `control_events`；marker
只是操作者输入的文字标签，不输入标签时 `markers` 为 0 仍是正常结果。

```bash
set -a; source /home/lsy03/.config/synthnova/credentials.env; set +a
SYNTHNOVA_MODULE_ROOT=/home/lsy03/Lsy03_document/仿真软件/extracted/synthnova_delivery_20260801/delivery_dir/synthnova_delivery/module \
  bash docker/run.sh python3 -B -m teleoperation.gp001_input_monitor \
  --duration-s 30 --output lerobot_runs/gp001_controls_20260910.jsonl
```

记录中的 `sample` 保留 `joint_states`、`action_list.axes`、`action_list.buttons`
及驱动返回的其他公开字段；`position_unit` 在完成现场辨识前保持 `unknown`。

## G1 SDK 只读状态接入

`robot_g1/read_only_state.py` 只读取 G1 左臂状态、活动控制器和部署 URDF，不暴露运动方法。它要求状态新鲜且静止，并对活动 URDF 与标定 URDF 的限位取保守交集。

`teleoperation/g1_sdk_policy_preview.py` 使用真实 `left_arm_joint7` 起点和限位构造接收策略，只打印 JSON 策略预览；该程序没有调用运动接口。首次在 G1 上运行前仍需把 `robot_g1/`、`teleoperation/` 和既有 `g1_arm_smoke_test/` 放在同一 Python 工作目录。

本机 dry-run 接收器不导入 Galbot SDK：

```bash
python3 -B -m teleoperation.g1_receiver_dry_run \
  --robot-start-j7-rad 0 \
  --joint7-lower-rad -1.538202778 \
  --joint7-upper-rad 1.538202778
```

默认只建立会话并保持未授权；`--allow-position-preview` 也只允许终端预览，不会发送机器人命令。

历史采集离线预览示例（使用的是 SynthNova G1 模型第 7 关节限位和人为指定的合成起点，不是真机状态）：

```bash
python3 -B -m teleoperation.preview_capture \
  /path/to/gp001_capture.jsonl \
  --synthetic-robot-start-j7-rad 0 \
  --joint7-lower-rad -1.538202778 \
  --joint7-upper-rad 1.538202778
```

下一步现场流程：先重新读取 G1 左臂状态和当前限位，再让 GP001 保持中立采一小段帧，确认单位/方向后只对左臂第 7 关节做受限映射测试。该步骤仍需现场人员看护、物理急停可触达，并由现场人员执行运动命令。