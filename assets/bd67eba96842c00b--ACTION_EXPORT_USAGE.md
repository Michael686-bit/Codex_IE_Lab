# 带实际动作目标的LeRobot候选数据导出

仅操作已关闭会话和离线原件，不连接机器人，不上传数据。

```bash
python3 -B -m acquisition.lerobot_capture.action_alignment \
  reports/dynamic_capture_20260923_145410/alignment \
  --output reports/dynamic_capture_20260923_145410/action_alignment_新的目录

HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 \
  HF_HOME=/tmp/g1-lerobot-export-cache \
  HF_DATASETS_CACHE=/tmp/g1-lerobot-export-cache/datasets \
  .venv-lerobot/bin/python -B -m acquisition.lerobot_capture.export_actions \
  reports/dynamic_capture_20260923_145410/action_alignment_新的目录 \
  --output lerobot_runs/lerobot_towel_candidate_新的目录 --candidate
```

所有输出目录必须尚不存在。动作方案复用已校验的观测网格、原件哈希及缺口检查，不修改观测质量阈值。

## 字段与语义

- `observation.state`：14个实测关节角＋双夹爪实测开度，16维float32，rad/m。
- `action`：同样顺序的14个实际接受的轨迹端点目标＋双夹爪目标开度，16维float32。
- 三路原尺寸RGB：`observation.images.head_left_camera`、`left_arm_camera`、`right_arm_camera`。
- `task`及LeRobot标准episode/frame/timestamp字段。
- action取目标网格时刻之前最近一次SDK接受的目标，按publish_end确认可用；机械臂目标最多保持300ms；夹爪目标按命令保持至下一条。不是实测状态或原始GP目标，不插值猜测驱动内部执行轨迹。
- episode起点之前只使用episode_start显式保存的accepted_action_context，并逐字段核对原始命令日志。
- 每行另要求两侧最近控制样本处于FOLLOWING。缺目标、过期、命令身份不符不伪造动作。

这些是“当时已下发的目标”标签，不是“给定图像后下一次决策”的因果标签。当前图像按源时间做离线最近邻，可能晚于网格时间；上线策略需要另行确定观测延迟和预测动作的时间约定。

## 原始17流与溯源

模型输入表使用三路RGB＋16维state/action；其余RGB、深度、力和全身关节仍保存在完整17流原件中，未删除。`capture_provenance.json`指向原始会话；`source_rows.jsonl`保存每行对应的源时间、原始文件位置/哈希、命令ID与下发时间。不能将三路训练视图说成17路都已编码到LeRobot表里。

缺口处切分为独立派生episode，排除孤立单帧；不删除坏行后压缩原时间。派生episode不是独立成功演示，划分训练/验证集必须按原始session/episode，避免同一次任务泄漏到两边。

## 验证与限制

导出后逐行重载，核对state/action数值、三路图像维度和有限值，并读取DataLoader批次；已校验原始媒体负载哈希。观测物理同步、相机曝光时间含义以及最终策略效果未经认证，`training_ready=false`保留。