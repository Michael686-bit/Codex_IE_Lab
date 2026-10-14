# G1 LingBot-VLA 2.0 LoRA 微调

此入口使用真实 G1 牛奶数据验收单张 RTX 4090 的微调能力。它不提供机器人控制接口。

## 模型与数据

- 固定官方源码 `4144e9c35c7ab490927cc3743e777f95433f953d`。
- 基础权重为 `robbyant/lingbot-vla-v2-6b-robotwin`，revision `0451855729ec904f970600e0aec8b84661423afe`。这是 RoboTwin 后训练权重；正式任务训练前应评估通用预训练初始化。
- 基础镜像 `lingbot-vla-v2:4144e9c-infer`，独立派生镜像 `lingbot-vla-v2:4144e9c-g1-lora-v1`。
- 沿用已有数据的 32 个训练 episode、7 个验证 episode，3581/713 个有效的 50 步窗口，10 Hz。
- 仅当前三路 RGB、当前 8 维状态和任务文字作为输入。三路视角是头左、左腕、右前环视；第三路命名为辅助视角。
- 关节动作是 SDK 接受的绝对目标，训练前减去当前观测关节；夹爪动作保持绝对宽度。SDK 接受目标不等同于实际执行轨迹。单位分别为弧度、米。
- 官方统一空间维度为 55；G1 左臂有效槽位为 0–6，左夹爪为 28。其他槽位不参与动作损失。
- 按训练窗口统计 mean/std，验证 episode 不参与归一化。

## 训练方式

动作专家的 36 层 q/k/v/o 共 144 个投影模块加入 rank=8、alpha=16 的 LoRA；另外训练状态输入、动作输入和动作输出投影。原模型参数、MoE 参数和教师查询模块冻结。基础权重为 BF16，可训练权重和 AdamW 状态为 FP32；batch=1，学习率 1e-4，梯度检查点开启，torch.compile 关闭。

只计算有效动作维度的 MSE flow matching 损失。`patch_model.py` 仅为辅助损失增加开关；深度、未来视频模块及原有查询 token 均保留。没有加载教师模型，也没有把未来图像或动作标签用于推理。

验收使用官方的排序 grouped-GEMM MoE 路径，并固定 FP32 矩阵乘法精度为 `highest`。官方快速推理 MoE 路径含浮点并行累加，在本次严格重新加载检查中出现预测漂移，因此本入口关闭该快速路径。推理延迟应按本配置重新实测。

检查点保存增量权重、完整优化器状态、步数、随机数和采样器状态，并带有数据、配置、代码哈希。恢复时拒绝配置不一致。基础模型需保留在原本的只读模型目录。

## 命令

在本目录执行，显式指定独立运行目录：

```bash
bash run.sh build
bash run.sh prepare runs/my_run
bash run.sh check runs/my_run
bash run.sh train runs/my_run --steps 10
bash run.sh verify runs/my_run
bash run.sh resume runs/my_run --steps 2
bash run.sh verify runs/my_run
```

`check` 执行一次真实数据反向传播但不更新优化器。`train --steps N` 从基础权重开始，已有检查点时拒绝覆盖。`resume --steps N` 在已有检查点基础上再更新 N 步。`verify` 在新容器内加载检查点并比较固定噪声下的预测。这些命令用于能力验收；正式续训使用下面的平台期训练入口。

## 平台期续训

`acceptance_core.py` 保留验收版本的模型和数据适配。`plateau_train.py` 从第 12 步恢复模型、AdamW 和随机采样状态，在新目录继续训练，rank=8、alpha=16 不变。

```bash
bash start_plateau.sh runs/plateau_rank8_20261009
# 前台启动或从已保存的平台期检查点恢复：
bash run.sh plateau runs/another_new_run
bash run.sh plateau runs/existing_plateau_run --resume
# 新容器重载检查：
bash run.sh plateau runs/existing_plateau_run --verify-only
```

默认规则：前 100 次新增更新将学习率从 1e-6 预热至 1e-4；每新增 500 步评估完整 713 个验证窗口的固定噪声 flow-matching loss，并在覆盖全部 7 个验证 episode 的固定 70 个窗口上生成真实动作预测。选择分数为 `首步关节MAE_deg/2 + 首步夹爪MAE_mm/5 + 前10步关节MAE_deg/3 + 前10步夹爪MAE_mm/10`，采用原始输出，不使用动作裁剪掩盖误差。实际改善应超过相对 0.5%；连续 3 次无明显改善将学习率减半，连续 10 次无明显改善且至少完成 1500 次新增更新时停止。最低学习率 1e-6，新增更新上限 20000。达到步数上限会明确标记为上限停止，不能当作平台期。

每次验证保存检查点、优化器、随机数和控制器状态。任何更低分数都会更新最佳检查点；显著改善阈值只控制 patience。停止后加载最佳模型，在所有 713 个验证窗口上生成动作预测与分 episode 指标。验证集用于选择模型，并非独立测试集；离线动作误差不是抓取成功率。

后台容器独立于聊天运行。每次启动保存不可变代码快照、镜像 ID 和 GPU 监测日志，整卡余量低于 2 GiB 时只停止自己的训练容器。运行目录中的 `container_name.txt`、`status.json`、`metrics.jsonl`、`validation_metrics.jsonl`、`best_checkpoint.json` 和 `completion.json` 记录进度与结果。若意外退出，从最近一次验证保存的检查点恢复，最多丢失不足 500 步更新。

数据与基础模型只读挂载；根文件系统只读，临时目录允许执行 Triton 本地编译模块，容器无网络。每次调用在 `invocations/` 保存代码快照和镜像 ID。GPU 与其他程序共享，运行时应保留整卡至少 2 GiB 余量。

## 验收证据

运行目录保存数据 manifest、G1 配置、训练统计、可训练参数清单、指标日志、冻结参数校验、检查点、离线预测及重新加载结果。一次十步训练只验证微调链路，不代表抓取成功率或可直接控制 G1。

2026-10-09 第一阶段验收通过，最终运行目录为 `runs/acceptance_20261009_v3/`：

- 真实数据完成 10 步更新；恢复后再更新 2 步，最终检查点 `checkpoints/step_000012/`。
- 第 10、12 步均在新容器重新加载，固定观测和噪声下预测最大误差为 0。
- 3962167 个可训练参数；冻结参数和持久化路由偏置校验一致；优化器计数与采样器续接均经独立检查。
- 峰值 PyTorch 分配 14553 MiB、保留 14700 MiB；整卡监测最小空闲 5661 MiB，原有真机验证服务未重启。
- G1 输出 `[1, 50, 8]`，数值有限。未评估完整验证集误差、抓取成功率或完整教师训练。
- 汇总证据见 `runs/acceptance_20261009_v3/acceptance_summary.json`。前两版运行保留作兼容性调试记录，以 v3 作为验收结果。