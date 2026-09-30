# G1统一数据处理入口

入口：`acquisition/lerobot_capture/run_data_pipeline.sh`。仅支持当前已验证的`left7`：三RGB＋左腕深度＋左臂关节＋左夹爪＋左腕力。使用LeRobot软件0.4.4生成LeRobotDataset格式v3.0，默认10Hz、三路原尺寸H264、8维state/action。相同配置的其他物体任务也可使用，任务文本直接从会话清单读取。

## 1. 列出会话

在项目根目录运行：

```bash
bash acquisition/lerobot_capture/run_data_pipeline.sh list
```

列出本地会话路径、任务、状态、成功条数和原件是否已在本机。不会连接G1，也不会自动选取“最新会话”。只有明确指定且`closed`的会话会处理。

## 2. 先只取回原件

将命令中的实际会话目录替换为list输出路径：

```bash
bash acquisition/lerobot_capture/run_data_pipeline.sh run \
  --session '/home/lsy03/文档/ChatGPT/VLA G1 项目/lerobot_runs/实际会话目录' \
  --output-root /mnt/data/VLA_data \
  --until archive \
  --prepare-output-with-docker
```

默认子目录名就是原会话目录名，可用`--name milk_batch_02`指定新的目录名。指定目录已存在时拒绝覆盖，应使用`resume`。`--prepare-output-with-docker`只在父目录不可写时，利用现有本地镜像创建当前这一个子目录并归属当前用户；不更改父目录权限。

归档阶段复制PC日志，取回全部原始episode（包括失败/中断），核对文件SHA256、分片、数量、源序号和身份。日志分别显示传输字节百分比、文件校验百分比、记录校验episode百分比。**只有归档完整校验完成后，才提示可继续新会话采集。** G1原件保留。

远端默认`galbot@192.168.1.88`，凭据使用已有本地文件；可通过`--host`和`--password-file`显式更改。不读取或打印密码内容。`rsync`支持保留部分传输；恢复时重新核验。`--bandwidth-kib 10240`可限制传输速率。没有自动删除或清理G1数据的选项。

## 3. 本机离线续跑

```bash
bash acquisition/lerobot_capture/run_data_pipeline.sh resume \
  --bundle /mnt/data/VLA_data/实际归档子目录 \
  --offline
```

按顺序完成：

1. `archive`：原件＋控制日志归档与校验。
2. `audit`：状态/速度/间隔/命令统计、三视角关键帧、失败事件。
3. `align`：完整10Hz时间线，已接受目标action，时钟/采样质量标记。
4. `export`：官方LeRobot API写出并逐帧重载。
5. `validate`：现有训练Docker断网、CPU只读加载；视频与原图抽查。
6. `report`：版本、路径、数量、排除列表、质量标记、输出哈希和交付报告。

也可以首次`run`省略`--until archive`一次完成全部流程。`--until`可指定上述任一步。`--offline`禁止需要远端取回的操作，已有本机raw时仍可归档复制。

支持重复指定`--session`处理多个明确选择的会话，各自生成独立bundle；这不是将不同会话合并成一个训练集。批量模式不接受单个`--name`或`--repo-id`。

## 4. 进度与恢复

```bash
bash acquisition/lerobot_capture/run_data_pipeline.sh status \
  --bundle /mnt/data/VLA_data/实际归档子目录 --watch
```

- `pipeline_state.json`记录阶段、版本、来源指纹和完成输出哈希。
- `progress.json`记录当前阶段的实际已完成/总量/百分比，不给耗时不同的阶段拼造一个总进度。
- `logs/`保存各步骤完整输出。
- Ctrl+C保留文件；下一次使用`resume`。未完成的下载保存在`raw.incoming`；派生目录重试时保留为`.incomplete_时间_编号`，重新生成新结果。
- 已完成阶段会重新核对输出哈希，匹配时复用。源/完成输出被修改时停止，避免将旧验证用于新内容；请使用新的bundle或明确修复，不手改检查点。
- 同一bundle有排他锁。新的采集会话不会自动追加到已完成bundle。
- `run --dry-run`只检查参数和会话，不创建输出目录、不连接机器人。

## 5. 接管本次已有牛奶归档

```bash
bash acquisition/lerobot_capture/run_data_pipeline.sh adopt \
  --bundle /mnt/data/VLA_data/milk_left_20260930
```

仅适用于已有兼容交付清单、对齐计划和官方验证结果的bundle。重新检查原件和输出证据后创建统一流程检查点，不重新编码视频，不修改任务标签。接管完成后改用`status`或`resume`，不重复adopt。

## 目录布局

```text
bundle/
  source/会话名/          PC日志、episode清单、raw七路原件
  raw_inventory.json      原始文件清单与哈希
  audit/                  自动审计报告和关键帧
  alignment/source_nearest_v1/
  lerobot/dataset_v3/     官方v3.0数据集（已有归档可保留原名称）
  validation/            Docker与图像对照结果
  pipeline_report/       交付报告及数据集文件哈希
  pipeline_state.json
  progress.json
  logs/
```

## 数据语义与限制

- `observation.state`：真实左臂7关节rad＋夹爪开度m。
- `action`：当时已经被SDK接受的左臂绝对目标与夹爪目标；不使用实测state代替、不补造右臂维度。
- 默认只导出操作者标记成功的episode；失败/中断原件一直保留。裁切、重标注和多会话合并属于另外的明确数据版本变更，本入口不自动执行。
- 源时间最近邻对齐是离线候选。原ClockMap拒收区间保留名义映射和无效标记，`clock_uncertainty_ns=-1`表示缺少通过检查的不确定度界限，不能当作零误差。
- 保留完整时间线，不把删除坏帧后的时间压缩拼接，不默认平滑动作。
- `quality.*`不会被LeRobot默认训练器自动用来屏蔽样本。`training_ready=false`始终保持，格式通过与训练准入分别报告。
- G1 recorder的接收时间不是PC接收时间，源时间到接收时间的差值不是已标定曝光延迟。
- 自动统计和关键帧不等于完整视频语义审阅或末端抖动精度验收；skill应按异常选择人工可检查的图表/原始片段。

运行环境：系统Python用于流程编排，项目`.venv-lerobot/bin/python`用于离线数据模块（可用`--python`指定其他兼容0.4.4环境）；现有`lerobot-act-smolvla:0.4.4-cu128`镜像用于TorchCodec交叉验证。不自动安装依赖、不联网下载权重、不训练模型。