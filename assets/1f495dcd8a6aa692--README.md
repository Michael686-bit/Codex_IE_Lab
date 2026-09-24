# 17路完整时间轴 LeRobot 候选数据集

本目录从一条叠毛巾演示导出：LeRobot v3.0，10Hz，1个原始episode，868行（无质量筛选删行）。这是17路在统一网格上的近邻重采样，不是把每个高频原始样本都变成一行；完整高频原件仍独立保留。

## 17路字段

| 原始流 | LeRobot字段 |
|---|---|
| HEAD_LEFT_CAMERA | `observation.images.head_left_camera` |
| HEAD_RIGHT_CAMERA | `observation.images.head_right_camera` |
| LEFT_ARM_CAMERA | `observation.images.left_arm_camera` |
| RIGHT_ARM_CAMERA | `observation.images.right_arm_camera` |
| LEFT_ARM_DEPTH_CAMERA | `observation.depth.left_arm_depth_camera`, `observation.depth_scale.left_arm_depth_camera` |
| RIGHT_ARM_DEPTH_CAMERA | `observation.depth.right_arm_depth_camera`, `observation.depth_scale.right_arm_depth_camera` |
| LEFT_FRONT_SURROUND_CAMERA | `observation.images.left_front_surround_camera` |
| RIGHT_FRONT_SURROUND_CAMERA | `observation.images.right_front_surround_camera` |
| LEFT_WRIST_FORCE | `observation.wrench.left_wrist_force` |
| RIGHT_WRIST_FORCE | `observation.wrench.right_wrist_force` |
| JOINT_chassis | `observation.joints.joint_chassis`, `observation.joint_timestamp_ns.joint_chassis` |
| JOINT_head | `observation.joints.joint_head`, `observation.joint_timestamp_ns.joint_head` |
| JOINT_left_arm | `observation.joints.joint_left_arm`, `observation.joint_timestamp_ns.joint_left_arm` |
| JOINT_right_arm | `observation.joints.joint_right_arm`, `observation.joint_timestamp_ns.joint_right_arm` |
| JOINT_leg | `observation.joints.joint_leg`, `observation.joint_timestamp_ns.joint_leg` |
| LEFT_GRIPPER | `observation.gripper.left_gripper`, `observation.gripper_moving.left_gripper` |
| RIGHT_GRIPPER | `observation.gripper.right_gripper`, `observation.gripper_moving.right_gripper` |

6路RGB保存原始JPEG字节、原始分辨率；深度直接保存在Parquet中，为uint16[720,1280]，单位换算depth_m = raw / depth_scale。没有彩色化、压缩成视频或缩小。当前LeRobot读取深度时提升为torch.int64，值不变。

五组关节各自保存position、velocity、acceleration、effort、current（按关节名称排序），另存每个关节timestamp_ns。腕力为Fx/Fy/Fz/Tx/Ty/Tz；夹爪有width、velocity、effort及is_moving。SDK其它原始结构（包括joint_positions）精确保留在source_rows.jsonl的data内。

observation.state为常用16维实测状态，action为相同顺序的已接受目标。action仍是该网格时刻之前最近已下发的目标，不是测量出的执行时刻。

## 必须同时查看有效性

- observation.stream_valid：[17]，顺序见capture_provenance.json的stream_order。
- observation.stream_flags：[17]位标记：1超出覆盖、2源时间缺口、4配对误差过大、8时钟映射不确定度超限。
- observation.stream_source_timestamp_ns / receive_wall_ns / receive_monotonic_ns / sequence / delta_ns / gap_ns保留每一路的溯源时间与配对信息，均为整数。
- quality.action_valid / state_valid / all_17_valid / training_row_valid：对应字段的行有效性。
- 无有效action的行用NaN占位，action_valid=false，不能直接送入训练损失。

某行匹配超阈值时保留真实最近样本并标false，不代表凭空补齐。depth中的0/65535仍为原始像素，stream_valid是时间有效性，不是每个深度像素有效性。图像近邻也可能来自目标时刻之后；物理曝光同步和在线因果可用性仍未认证。

本目录training_ready=false；不要忽略mask直接训练。meta/stats.json只计算非图像数值字段，action排除NaN行；未提供RGB和深度的归一化统计，训练前需按选定通道/有效行单独计算。

## 文件与查看

- meta/info.json：完整feature字典、17路原生分辨率、总帧数。
- data/chunk-000/file-000.parquet：整条episode，分row group流式写入，未分割任务。
- meta/episodes/chunk-000/file-000.parquet：原始episode元信息。
- meta/tasks.parquet：叠毛巾任务文本。
- source_rows.jsonl：逐行原件位置/哈希、原始结构和接受的动作来源。
- capture_provenance.json：转换规则、各路无效行数量和最终验证状态。只有status=verified表示本次导出验证完成。

旧的9093查看器仍是三视角638帧版本，不会自动切换到本目录。

## Python读取

```python
from lerobot.datasets.lerobot_dataset import LeRobotDataset

ds = LeRobotDataset('local/g1_towel_all17',
    root='lerobot_runs/lerobot_towel_all17_20260923_145410',
    download_videos=False)
sample = ds[100]
print(sample['observation.stream_valid'])
print(sample['observation.depth.left_arm_depth_camera'].shape)
print(sample['quality.action_valid'])
```

本次转换只读原始文件，不运行机器人SDK、不上传数据。之前的638帧三视角候选集未覆盖。

## 本次完成结果

status=verified，868行、1个episode，17路齐全。868行的Parquet数值、RGB负载和uint16深度逐行核验通过；LeRobot全量索引、指定episode加载、首/中/末行及DataLoader批次验证通过。全部17路同时通过时间规则的行数为703，有效action行数为867。数据目录大小约1.82GiB。