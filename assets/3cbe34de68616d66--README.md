# ACT / SmolVLA 独立 Docker 环境

本目录用于完成环境部署计划第 1—5 步：环境检查、镜像构建、ACT 验证、SmolVLA 验证、统一使用入口与记录。

ACT 与 SmolVLA 共用 `lerobot-act-smolvla:0.4.4-cu128` 镜像，每次命令启动一个临时容器。数据、缓存、权重和日志保存在宿主机，退出容器不会丢失。现有 LingBot 与 RoboTwin 环境独立保留。

## 版本与目录

- Ubuntu 22.04 / Python 3.11.13。
- PyTorch 2.8.0+cu128 / torchvision 0.23.0+cu128 / TorchCodec 0.6.0。
- LeRobot 0.4.4，源码提交和归档 SHA-256 见 `manifests/source-lock.json`。
- Transformers 4.57.1；完整解析版本见 `constraints.txt`。
- 官方 SmolVLA 基础权重与 VLM 配置/分词器固定到提交，见 `manifests/assets-lock.json`。
- 基础镜像使用 digest 锁定；源码在 Docker 构建时验证摘要；模型下载验证上游文件摘要。
- 系统 apt 包来自 Ubuntu 镜像源，未使用历史快照，因此不保证未来重建镜像逐字节相同；本次镜像 ID 另行记录。

```text
configs/                 ACT、SmolVLA 的最小验证配置
scripts/                 统一入口与验证程序
manifests/               版本、源码、权重和镜像记录
reports/                 GPU 检查、训练日志、推理与验收 JSON
runtime/datasets/        数据集
runtime/cache/           模型、分词器与 Torch 缓存
runtime/outputs/          训练结果、checkpoint、优化器状态
runtime/checkpoints/     可用于归档后续正式训练权重
```

`runtime/` 和 `vendor/` 不纳入 Git。默认数据目录在本目录下，可在首次使用前设置绝对路径 `LEROBOT_DATA_DIR`；全部容器内统一挂载成 `/data`。已有数据迁移时，应完整复制对应目录。

## 使用入口

在宿主机终端运行，需要当前用户具有 Docker 使用权限：

```bash
cd '/home/lsy03/文档/ChatGPT/VLA G1 项目/lerobot_deploy'
bash scripts/lerobot.sh help
bash scripts/lerobot.sh status
bash scripts/lerobot.sh check
```

从头构建与准备：

```bash
bash scripts/lerobot.sh build
bash scripts/lerobot.sh download
bash scripts/lerobot.sh prepare
```

`build` 自动下载并校验源码。`download` 下载并校验官方 SmolVLA、分词器及 ACT 的 ResNet18 权重，支持 SmolVLA 大文件断点续传；重复执行复用已验证文件。下载阶段需要网络，其余运行命令默认在无网络容器内执行，不上传数据或模型。

`prepare` 生成 2 个 episode、共 128 帧的合成视频样例，并创建引用本地 VLM 配置和分词器的 SmolVLA 配置副本。官方原始配置保留。SmolVLA checkpoint 已包含骨干权重，所以本地副本设置 `load_vlm_weights=false`，避免先额外下载骨干权重再被完整 checkpoint 覆盖；完整权重加载另有严格验证。

## 验证 ACT 和 SmolVLA

按顺序运行，避免同时训练争抢显存：

```bash
bash scripts/lerobot.sh smoke act
bash scripts/lerobot.sh smoke smolvla
bash scripts/lerobot.sh report
```

每条 `smoke` 命令：

1. 使用官方 `lerobot.scripts.lerobot_train.main` 训练 5 步。
2. 保存模型、处理器、归一化统计和优化器状态。
3. 退出训练容器，在全新容器中严格加载 checkpoint。
4. 执行完整动作块推理，检查形状和 NaN/Inf，测量预热后的 10 次延迟。
5. 检查训练 loss / 梯度、权重数值和保存状态，生成 `*.acceptance.json`。

成功后打印 `PASS`。训练目录带时间戳，不覆盖旧结果。最近一次成功权重的容器路径写入 `reports/act-latest-checkpoint.txt` 或 `reports/smolvla-latest-checkpoint.txt`。

该样例是**合成测试数据**：单路 224×224 RGB、6 维状态/动作、10Hz、50 步动作块、batch size 1。6 维只是测试维度，与 G1 关节定义无关。ACT 使用完整默认网络和预训练 ResNet18；SmolVLA 从官方基础权重微调，保留其骨干冻结/动作专家训练设置，模型内部图像处理尺寸另在报告中记录。

验收结果只说明软件链路工作正常，不说明已经学会操作，也不能用于比较真机成功率。SmolVLA 的训练前基础权重测试可保留原有三相机配置，缺失视角按模型实现填充；正式微调样例配置依据数据集使用单相机。

## 重载已有 checkpoint

```bash
bash scripts/lerobot.sh infer "$(cat reports/act-latest-checkpoint.txt)"
bash scripts/lerobot.sh infer "$(cat reports/smolvla-latest-checkpoint.txt)"
```

默认在合成样例上做离线推理。对其他数据集需同时传入 `--dataset-root=/data/datasets/实际目录 --dataset-id=组织/数据集`，并确保输入字段与 checkpoint 匹配。

记录包含首次加载、首次推理、预热、完整动作块延迟、进程 PyTorch 显存峰值、输入配置及输出形状。延迟包含预处理和后处理，不含磁盘视频解码；GPU 上若还有其他进程，这些结果不能视为独占显卡基准。PyTorch 分配显存不包含全部 CUDA 上下文开销。

## 后续正式训练入口

下面是命令模板，数据集 ID 和目录必须替换成实际数据；当前没有开展 G1 正式训练。

```bash
bash scripts/lerobot.sh train act \
  --dataset.repo_id=local/your_dataset \
  --dataset.root=/data/datasets/your_dataset \
  --dataset.video_backend=torchcodec \
  --output_dir=/data/outputs/act_first_run \
  --policy.device=cuda --batch_size=1 --num_workers=0 --steps=10000

bash scripts/lerobot.sh train smolvla \
  --dataset.repo_id=local/your_dataset \
  --dataset.root=/data/datasets/your_dataset \
  --dataset.video_backend=torchcodec \
  --output_dir=/data/outputs/smolvla_first_run \
  --policy.device=cuda --batch_size=1 --num_workers=0 --steps=10000
```

这里的训练步数和 batch size 是起始模板，不是针对 G1 优化后的参数。训练前需确定相机键、关节顺序、动作语义、单位、时间对齐和按 episode 划分的数据集。不同相机键可通过官方 `--rename_map` 参数适配。

## 常见问题

- **显存不足**：用 `status` 检查占用，先降低 batch size。若要释放现有服务占用，先确认该服务当前用途，再手动安排停启；脚本不会自动停止 LingBot 或 RoboTwin。
- **离线加载缺文件**：运行 `download`，随后 `prepare`。不要只复制 `model.safetensors`，处理器和分词器同样需要。
- **Docker 权限错误**：需要有权访问宿主机 Docker daemon；这与模型代码无关。
- **视频后端失败**：本环境已配对 Torch 2.8 / TorchCodec 0.6，并安装 FFmpeg；不要单独升级其中一项。
- **数据生成中断**：保留故障目录用于检查，移走不完整的 `runtime/datasets/synthetic_smoke` 后再执行 `prepare`。

Compose 配置作为可选入口；统一脚本使用 Docker CLI，不要求安装 Compose 插件。整个环境不映射机器人设备、不开放控制端口、不发送机器人动作。

## 官方来源

- https://github.com/huggingface/lerobot/tree/v0.4.4
- https://huggingface.co/lerobot/smolvla_base
- https://huggingface.co/HuggingFaceTB/SmolVLM2-500M-Video-Instruct
- https://huggingface.co/docs/lerobot/act
- https://huggingface.co/docs/lerobot/smolvla