# 2026-09-23 两次15秒传感器录制对比

两次均正常结束，原始分片完整性及身份校验通过，17路齐全。全量RGB和深度解码通过。未发送运动命令，未修改相机设置。补光前后标签仅按操作顺序推定，尚未由操作者确认。

| 指标 | 08:58:01 | 09:00:57 |
|---|---:|---:|
| HEAD_LEFT_CAMERA Hz | 15.02 | 15.03 |
| HEAD_LEFT_CAMERA 年龄P95 ms | 70.19 | 71.48 |
| HEAD_LEFT_CAMERA 最大源帧间隔 ms | 68.12 | 68.32 |
| HEAD_RIGHT_CAMERA Hz | 15.02 | 15.03 |
| HEAD_RIGHT_CAMERA 年龄P95 ms | 71.33 | 73.39 |
| HEAD_RIGHT_CAMERA 最大源帧间隔 ms | 68.12 | 68.32 |
| LEFT_ARM_CAMERA Hz | 14.99 | 15.00 |
| LEFT_ARM_CAMERA 年龄P95 ms | 31.20 | 34.55 |
| LEFT_ARM_CAMERA 最大源帧间隔 ms | 66.69 | 66.73 |
| RIGHT_ARM_CAMERA Hz | 14.99 | 15.00 |
| RIGHT_ARM_CAMERA 年龄P95 ms | 34.28 | 35.36 |
| RIGHT_ARM_CAMERA 最大源帧间隔 ms | 66.70 | 66.73 |
| LEFT_FRONT_SURROUND_CAMERA Hz | 10.02 | 10.04 |
| LEFT_FRONT_SURROUND_CAMERA 年龄P95 ms | 265.56 | 269.05 |
| LEFT_FRONT_SURROUND_CAMERA 最大源帧间隔 ms | 100.09 | 166.66 |
| RIGHT_FRONT_SURROUND_CAMERA Hz | 10.02 | 10.11 |
| RIGHT_FRONT_SURROUND_CAMERA 年龄P95 ms | 265.92 | 268.42 |
| RIGHT_FRONT_SURROUND_CAMERA 最大源帧间隔 ms | 100.09 | 166.66 |
| JOINT_left_arm Hz | 58.93 | 59.75 |
| JOINT_left_arm 年龄P95 ms | 18.05 | 19.62 |
| JOINT_left_arm 最大源帧间隔 ms | 96.82 | 119.88 |

## 10 Hz三视角加状态组帧（现有规则）

- 08:58:01：140/151候选行通过（92.7%）；最长连续区间30行。
  拒收原因计数（同一行可有多个原因）：{"JOINT_left_arm:alignment_tolerance": 3, "JOINT_right_arm:alignment_tolerance": 3, "JOINT_left_arm:stream_gap": 7, "JOINT_right_arm:stream_gap": 7, "LEFT_GRIPPER:stream_gap": 4, "RIGHT_GRIPPER:stream_gap": 4, "LEFT_GRIPPER:alignment_tolerance": 2, "RIGHT_GRIPPER:alignment_tolerance": 2, "LEFT_ARM_CAMERA:outside_stream_coverage": 1, "RIGHT_ARM_CAMERA:outside_stream_coverage": 1}
- 09:00:57：126/151候选行通过（83.4%）；最长连续区间29行。
  拒收原因计数（同一行可有多个原因）：{"HEAD_LEFT_CAMERA:alignment_tolerance": 6, "JOINT_left_arm:stream_gap": 6, "JOINT_right_arm:stream_gap": 6, "LEFT_GRIPPER:stream_gap": 5, "RIGHT_GRIPPER:stream_gap": 5, "JOINT_left_arm:alignment_tolerance": 5, "JOINT_right_arm:alignment_tolerance": 5, "LEFT_GRIPPER:alignment_tolerance": 2, "RIGHT_GRIPPER:alignment_tolerance": 2, "clock_rate_or_offset_change": 10}

## 解释与下一步

- 今日两段头部均恢复约15Hz，最大头部源帧间隔约68ms，未重现昨晚2.51Hz。第一段已恢复，不能把恢复归因于第二段补光，也不能证明自动曝光根因或长期修复。
- 数据年龄为G1读取wall时间减源时间，包含缓存与时钟误差，不是校准的纯物理延迟。前环视仍约266–269ms。
- 关节/夹爪等保存的源时间序列仍有约90–121ms缺口；这不能单凭离线日志定位到硬件丢帧。
- 第二段有一个约1秒的跨机时钟映射区间被clock_rate_or_offset_change拒收，影响10行；这并不直接证明系统时钟跳变，需复核原始测时样本和采样抖动。
- 当前规则为图像34ms、状态10ms、时钟不确定度2ms、状态最大间隔40ms；只是项目诊断规则，不是通用VLA验收标准。
- 尚未分析共同可见事件的物理时序；无action，不可作为正式训练演示。
- 下一步优先复核状态缺口及测时异常，并在稳定照明下完成共同可见标记的30秒时序检查；随后验证更长时间连续性。

## 复现

每段使用 reports/capture_data_audit_20260922/audit.py 全量审计；使用 python3 -B -m acquisition.lerobot_capture.alignment SESSION --output NEW_OUTPUT --fps 10 组帧。审计结果在本目录各时间子目录，逐行通过/拒收结果在 alignment_* 子目录。