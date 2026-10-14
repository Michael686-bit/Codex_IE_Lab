# 用 Rerun 查看本地 LeRobot 数据

项目虚拟环境使用 LeRobot 0.4.4、Rerun SDK/Viewer 0.26.2。以下预览路径已实测读取本项目的 LeRobotDataset v3.0 单臂8维数据。

## 打开已经生成的示例

最近一批（15:44）的数据集 episode 0，对应原始 `episode_000003`，184帧、三路RGB，并叠加左腕六维力。原件和数据集保持不变。

```bash
cd '/home/lsy03/文档/ChatGPT/VLA G1 项目'
.venv-lerobot/bin/rerun --port 9890 reports/lerobot_rerun_20261008/milk_154454_ep0_six_axes.rrd
```

带原始六维力的版本在Rerun底部选 `g1_recorder_time` 时间线，按播放键或拖动游标；未带原始流的版本仍使用 `dataset_index`。上方是头左、左腕、右前环视；视频下方固定展示左腕Fx/Fy/Fz/Tx/Ty/Tz六条原始曲线；再下方可切换10Hz配对六维力和关节／夹爪state/action，另有 Quality flags、Metadata、Task and original episode 标签页。关节单位rad、夹爪单位m；state是反馈，action是被SDK接受的目标。多条episode之间的dataset_index只是行顺序，不能当作连续物理时间。

## 三批数据

| 会话 | 数据集目录 | episode编号（从0开始） |
|---|---|---|
| 14:21 | `/mnt/data/VLA_data/milk_left_20260930/lerobot/milk_left_v3` | 0～10 |
| 14:58 | `/mnt/data/VLA_data/milk_left_20260930_145800/lerobot/milk_left_v3` | 0～10 |
| 15:44 | `/mnt/data/VLA_data/milk_left_20260930_154454/lerobot/milk_left_v3` | 0～16 |

数据集episode编号经过筛选重新编号，不等于原始录制编号。先列出映射：

```bash
.venv-lerobot/bin/python -B -m acquisition.lerobot_capture.visualize_lerobot \
  /mnt/data/VLA_data/milk_left_20260930_154454/lerobot/milk_left_v3 --list
```

## 生成其他episode的预览

下面示例选择数据集episode 1和2。替换数据集路径及编号即可；输出必须使用尚不存在的新文件。省略 `--episodes` 会生成整批预览，耗时和文件体积都更大。

```bash
HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 \
HF_HOME=/tmp/g1-rerun-hf-home HF_DATASETS_CACHE=/tmp/g1-rerun-datasets \
XDG_CACHE_HOME=/tmp/g1-rerun-cache \
.venv-lerobot/bin/python -B -m acquisition.lerobot_capture.visualize_lerobot \
  /mnt/data/VLA_data/milk_left_20260930_154454/lerobot/milk_left_v3 \
  --episodes 1 2 --with-raw-wrench \
  --output reports/lerobot_rerun_20261008/milk_154454_ep1_2.rrd

.venv-lerobot/bin/rerun reports/lerobot_rerun_20261008/milk_154454_ep1_2.rrd
```

本机使用PyAV解码导出的MP4；RRD再用JPEG压缩显示图像。原始JPEG、深度和高频流在归档raw中。查看器自动显示source_rows中与每帧配对的左腕六维力；加 `--with-raw-wrench` 会再读取原件中的全部左腕六维力样本。质量字段按原值显示，查看器不会修复时序或自动筛掉坏点。

最新版Rerun官方文档还介绍了直接打开LeRobot v2.1/v3.0目录的能力：https://rerun.io/docs/howto/logging-and-ingestion/lerobot 。本机上述命令采用已验证的官方LeRobot Loader → RRD路径，不依赖当前Viewer是否带有最新目录加载器。

## 六维力的时间和单位

- 视频下方的 `LEFT WRIST Fx/Fy/Fz/Tx/Ty/Tz`：六条原始曲线Fx/Fy/Fz（N）及Tx/Ty/Tz（Nm）。保留SDK坐标轴和原始偏置，不自动去皮、重力补偿或变换坐标系。
- `Left wrist 6-axis | 10 Hz matched`：直接显示对齐来源清单中的六个原始数值；可在Quality flags中看 `sensor_valid_LEFT_WRIST_FORCE`。
- 原始曲线使用G1 recorder接收时刻，视频帧使用对齐计划映射到该recorder的时刻，主时间线为相对于首个选中视频帧的 `g1_recorder_time`。SDK源时间戳检查单调，并在报告中保存实际频率；没有把高频样本硬塞进整数视频帧号。
- 原始录制包含尾部缓冲，曲线可能比视频逻辑结束稍长。这种显示时间对应关系不代表曝光时间或力传感器物理同步已标定。
- 六维力用于此次Rerun显示；原LeRobot的8维state/action和数据集文件不变。

新版使用独立应用布局，六维力固定显示，纵轴覆盖选中原始数据的真实范围。打开命令指定 `--port 9890`，便于与旧窗口区分。实际渲染截图已核查六条曲线均可见。