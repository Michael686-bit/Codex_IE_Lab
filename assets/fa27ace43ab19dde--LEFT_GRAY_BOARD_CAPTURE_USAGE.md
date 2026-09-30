# 仅左臂：白色方块放到灰色板子上

```bash
bash teleoperation/run_capture_left_gray_board.sh --execute
```

配置检查（不连接设备）：

```bash
bash teleoperation/run_capture_left_gray_board.sh --execute --dry-run
```

默认五组、1800秒，关节速度上限1.0rad/s、夹爪速度0.06m/s（60mm/s）。任务入口固定`--active-arm left`：右臂固定键不能开启跟随，右夹爪不接收开合命令；左右急停仍是全局停止。全身反馈读取及原有安全检查保留。数据仍保存在新的`lerobot_runs/dual_arm_capture_日期_时间_PID`会话，session.json标记active_arms=[left_arm]。

## 操作

启动自动预热完成后，对齐左侧主从臂，按左固定键开启跟随。按记录键开始，把方块抓起放到灰板上，松爪并退出后再次按记录键结束；失败按取消键。等待落盘完成，暂停左臂再人工复位；满五组提示后暂停左臂并Ctrl+C退出。右侧记录/取消按键仍可用于分段，右侧运动按键无效。

此入口仍是人工遥操采集，不自动规划抓取。截图中的左腕朝向地面，正式录制前需在接近、抓取、放置三种姿态确认方块和灰板可见；头左画面中桌面区域较小，先保留右前环视作为全桌视角。

## 已实施的七路记录

新入口固定`--sensor-profile left7`，实际保留：

| 通道 | 内容 |
|---|---|
| HEAD_LEFT_CAMERA | 头左RGB |
| LEFT_ARM_CAMERA | 左腕RGB |
| LEFT_ARM_DEPTH_CAMERA | 左腕uint16深度及depth_scale |
| RIGHT_FRONT_SURROUND_CAMERA | 右前环视RGB |
| JOINT_left_arm | 左臂7关节状态 |
| LEFT_GRIPPER | 左夹爪状态 |
| LEFT_WRIST_FORCE | 左腕六维力 |

记录器只订阅/调用所选四路图像的getter，只查询左腕力和左夹爪，并只落盘左臂关节组。全身关节读取仍用于SDK元信息核对及PC控制安全检查，不在G1原始数据中额外写成其余四组。右腕深度等十路不再写入该任务的原件。控制日志仍包含用于安全检查的全身反馈，不能将“七路原始传感器”理解为PC日志只能有左臂字段。

源头预热、数据新鲜度、落盘结束及校验都按七路检查；PC预热阶段确认远端七路身份一致后才开放遥操。旧任务继续使用原17路配置和旧G1部署目录，不改变已有数据。

## 文件究竟写在哪里

1. **G1先保存七路原件**：`/home/galbot/vla_capture/data/capture_sessions/<session_id>/episode_******/`，包含`.g1raw`分片、manifest、summary和分片校验信息。
2. **PC同时保存控制/动作日志与清单**：`lerobot_runs/dual_arm_capture_日期_时间_PID/`，包括`control.jsonl`、`control.samples.jsonl`、`session.json`和各组测时及manifest。
3. **结束后手动取回，PC才拥有传感器原件副本**：

```bash
python3 -B -m acquisition.lerobot_capture.fetch lerobot_runs/dual_arm_capture_实际目录
```

下载后位于该会话的`raw/episode_******/`，G1原件保留。采集脚本本身没有自动下载步骤；当前仍是原始格式，不是已经导出的LeRobot训练集。

## 部署与验收

G1独立版本：`/home/galbot/vla_capture/releases/capture-left7-20260929-v1`。部署工具：`python3 -B -m acquisition.raw_recorder.deploy_left7`；只安装文件和检查配置，不初始化SDK或运动。相同文件可重复核验，不覆盖不同内容的现有版本。

本地SDK getter模拟、七路写入/校验、缺流拒收、持久服务和旧17路回归已验证；远端安装及服务七路配置已检查。尚未进行真机动态试采，首次先短录一组，确认“各路条数”仅七个通道且均大于0。减少负载不等于已证明修复所有时钟/状态缺口或写盘积压。

新的捕获契约定义单臂state/action各8维（左臂7关节＋左夹爪）；它是后续导出约定，旧双臂16维导出器尚未改成自动导出此任务。不要为缺失右臂action补零。通用原始Rerun生成器已支持七路布局。

2026-09-30：按用户要求，灰板任务入口默认夹爪速度改为0.06m/s，用于中间速度对照；未自动启动真机。其他入口默认速度及120mm反馈保护保持原配置。