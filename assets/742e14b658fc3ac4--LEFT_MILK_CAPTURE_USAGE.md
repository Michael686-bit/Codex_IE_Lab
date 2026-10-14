# 左臂牛奶入箱采集

沿用灰板入口的遥操、记录键分段和七路传感器配置，目标改为牛奶瓶放入蓝色料箱。

默认会话上限3600秒（1小时），目标40条：

```bash
bash teleoperation/run_capture_left_milk.sh --execute
```

计划采集50条、显式设置1小时：

```bash
bash teleoperation/run_capture_left_milk.sh --execute --seconds 3600 --target-episodes 50
```

采集30条时使用`--target-episodes 30`。不指定时长时默认3600秒，不指定组数时默认40条。允许1..3600秒，仍可传入`--seconds 600`缩短到10分钟。时限针对整个会话，不是每条长度，也不保证能录完40条；复位和等待落盘也占用会话时间。到时仍按现有停止/收尾逻辑处理，当前未完成条目不计入成功目标。重新启动创建新会话，计数从0开始，多次会话需合计有效条数。

采集启动器及底层采集模式的上限均已扩展到3600秒。通用入口仍默认1800秒，非采集遥操入口的600秒上限不变；远端原始记录服务已有3600秒支持。

只检查配置，不连接机器人或手柄：

```bash
bash teleoperation/run_capture_left_milk.sh --execute --dry-run
```

## 固定配置

- 仅左臂和左夹爪遥操，固定`--active-arm left`。
- 左夹爪SDK指令速度固定`0.06m/s = 60mm/s`，包括张开与闭合。该参数放在用户参数之后，即使额外传入`--gripper-speed-m-s`，最终仍使用0.06。它是SDK速度设置，不代表已经实测物理速度。
- 关节速度上限默认1.0rad/s，可通过`--speed-rad-s`降低，仍由原入口校验上限。
- 固定`left7`：头左RGB、左腕RGB、左腕深度、右前环视RGB、左臂关节、左夹爪、左腕力。
- 每条保存相同英文任务文本：`Pick up the milk bottle from the table and place it into the blue bin.`，用于后续SmolVLA训练/推理；终端显示中文操作说明。

本入口固定牛奶任务，不能用于采集插座或其他目标；否则会造成指令与示教不一致。

## 每条示教

1. 启动并等待自动预热，对齐左侧主从臂，按左固定键开启跟随。
2. 按记录键开始一条，抓起牛奶，放入蓝色料箱，松爪并撤手。
3. 再按记录键正常结束；抓错、掉落或未完成时按取消键。
4. 等待落盘完成，再用左固定键暂停左臂，然后人工复位。结束录制本身不会暂停左臂。
5. 改变牛奶的位置和朝向，也调整干扰物位置；初期避免严重遮挡，固定料箱位置。

记录键为左索引1或右索引10，取消键为左8或右17，与原入口一致。完成数只计入操作者正常结束且原始落盘完成的条目；取消条目保留文件但不计入目标。达到目标仅提示，遥操继续；完成采集后暂停左臂，再Ctrl+C退出。

## 保存位置

- PC控制日志与会话清单：`lerobot_runs/dual_arm_capture_日期_时间_PID/`，任务保存在会话/episode元数据中。
- 机器人传感器原件：`/home/galbot/vla_capture/data/capture_sessions/<session_id>/episode_******/`。
- 沿用已部署的left7记录器；新入口不要求修改远端记录器。结束后仍需按终端显示的PC会话目录取回原件：

```bash
python3 -B -m acquisition.lerobot_capture.fetch lerobot_runs/dual_arm_capture_实际目录
```

此步骤取回原始数据，不等于已经导出LeRobot训练集。任务文本需在后续导出时保留并映射到模型读取的字段。