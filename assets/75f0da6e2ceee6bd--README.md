# 牛奶数据：π0.5动作专家微调

入口：`pi05_deploy/scripts/train_milk_expert.sh`。使用已部署的独立镜像`lerobot-pi05:0.4.4-cu128`，原始数据、基础权重和tokenizer均只读，网络关闭。默认只打印配置；GPU检查和训练由用户显式执行。

## 当前数据准入

固定使用2026-09-30三批及2026-10-09 10:00、10:34两批牛奶数据，共59条、10,569帧。全部已有格式/Docker读取验证。

最新批次首组前52帧缺少SDK已接受的夹爪目标，导出裁去了5.2秒前缀。脚本默认将这条不完整任务示教排除出本轮实验，原件及LeRobot文件均不改；58条纳入实验。可用`--allow-trimmed`显式重新纳入，但实验划分会随之改变。

按原episode划分，并保留前三批旧实验的32/7划分。默认将最新批次其余9条作为独立采集批次的测试集，不用于归一化或模型选择：

| 划分 | 示教数 | 10步窗口数 |
|---|---:|---:|
| 训练 | 40 | 5,726 |
| 验证 | 9 | 1,255 |
| 测试 | 9 | 1,321 |
| 排除裁切示教 | 1 | 不用于本轮实验 |

只选择当前`quality.temporal_match_valid`与`action_valid`均为真的起点，要求未来H步动作完整有效且不跨原episode。完整时间线不删帧拼接，失败示教不引入训练。J2限位后的实际SDK接受目标保留，不用未裁剪的主臂请求或实测state代替action。

最新批次交付摘要的部分质量计数覆盖裁切前候选，不宜直接除以导出帧数。新数据模块按**实际导出范围**重算：1,664帧中时序有效1,481、时钟有效1,658、名义时钟标记6、动作有效1,664。所有数据仍保留物理同步未认证的状态，质量筛选仅支持离线实验准入。

## 损失与训练参数

使用与现有π0.5实现相同的conditional flow matching：对训练集分位数归一化后的动作a和高斯噪声ε构造`x_t=(1-t)a+tε`，监督速度场`u_t=ε-a`。时间采样沿用模型配置中的Beta分布。

损失只对实际8维计算：

`L = sum_{b,h} m[b,h] * (sum_{j=1..7}(v_j-u_j)^2 + λg*(v_grip-u_grip)^2) / ((7+λg)*sum(m))`

默认`λg=1`，等价于官方8维均方flow损失。`--gripper-weight 2`可作夹爪加权对照，此时夹爪占总标量权重2/9，不是夹爪组与七关节组各占一半。该权重是实验参数，不保证效果更好。

保留模型内部32维输入、官方噪声和采样路径，只把24个填充维度排除出损失。无效/padded动作步也不参加损失；正常入选窗口应完全无padding。夹爪目标是连续开度，不另加二分类头。第一轮不加入平滑或其他辅助损失，以保持可解释的基线。

默认H=10，在10Hz数据上覆盖约1秒；可用`--horizon 50`比较5秒目标。关节rad与夹爪m先分别用**训练组**的q01/q99归一化；视觉/语言骨干冻结，state按π0.5预处理离散成prompt中的状态token。

训练动作专家Transformer、AdaRMS和action/time投影；未使用的语言输出头冻结。不是LoRA，也不是整个VLM全参数微调。冻结骨干使用已验收的BF16配置，专家参数和Adam矩保持FP32，通过BF16 autocast计算，避免小学习率在BF16参数上被舍入掉。该混合精度训练路径需用下面的GPU检查实测，本次没有自动运行GPU训练。

默认batch=1、梯度累积4、AdamW lr=2.5e-5、betas=(0.9,0.95)、weight decay=0.01、100步warmup后余弦衰减、梯度裁剪1.0、2,000次优化器更新。启用gradient checkpointing，不启用torch.compile。

## 用户执行

```bash
# 仅配置预览，不启动Docker
bash pi05_deploy/scripts/train_milk_expert.sh --dry-run

# CPU数据哈希、划分和训练集归一化
bash pi05_deploy/scripts/train_milk_expert.sh prepare

# 先执行：真实数据GPU前向/反向、专家梯度、保存重载及Adam矩内存检查
# 0次optimizer.step，不更新训练权重
bash pi05_deploy/scripts/train_milk_expert.sh check

# 检查通过后启动前台训练，显示loss、验证误差、梯度和学习率
bash pi05_deploy/scripts/train_milk_expert.sh train

# 自定义预算或夹爪加权对照；每次均创建新实验
bash pi05_deploy/scripts/train_milk_expert.sh train --steps 1000 --gripper-weight 2
```

每次输出新的绝对`RUN_DIR`，位于`pi05_deploy/runtime/outputs/milk_runs/`。`check`分配Adam一阶/二阶矩但执行0次优化器更新，以覆盖主要训练显存成本；正式训练峰值仍以训练日志为准。GPU反向/显存检查由用户运行，本次不宣称已在4090上完成专家训练验收。

## 验证与模型选择

每100步验证，当前默认每条验证示教取16个均匀固定起点，共144个；固定随机种子并保护训练RNG。记录flow loss、未经裁剪的首步/1秒平均关节角误差、夹爪毫米误差、保持当前实测状态基线、夹爪越界比例/幅度，并单列开闭转折窗口误差。

2026-10-09首轮实验使用旧默认3起点/示教，共27个。事后核查发现它们全部不包含开闭转折，导致夹爪指标偏乐观，因此已修正默认覆盖；历史权重、日志及源快照保留。新阶段必须在新验证口径下重新计算初始化基线，不把旧27点分数与新144点分数直接比较。

best按`1秒关节MAE(度)/2 + 1秒夹爪MAE(mm)/5`选择。这两个尺度是本项目的实验权重，不是行业安全标准；该分数不同于训练损失。连续10次验证未改进提前停止。若没有优于初始化模型，`best_step=0`且不伪造已训练best文件。

独立测试集不会在训练循环中读取。训练结束选择检查点后，再显式执行一次：

```bash
bash pi05_deploy/scripts/train_milk_expert.sh evaluate /完整RUN_DIR/checkpoints/step_001000
```

测试来自独立采集批次，但仍是相似桌面场景。离线误差不能作为真机任务成功率。

## 权重与恢复含义

首轮1900步检查点的新阶段续训入口是`pi05_deploy/scripts/continue_milk_expert.sh`，默认新增1000步、lr=5e-6、开闭转折采样权重2，并分别验证144个均匀窗口和全部192个转折窗口。默认仅预览，实际训练用`--execute`。详细设置与累计步数见本目录`CONTINUATION.md`。

检查点仅保存`action_expert.safetensors`、基础权重SHA-256、模型配置、数据划分、归一化与处理器，不重复保存冻结的视觉语言大模型。必须使用本目录`model.py:load_policy`加载，不能直接当作完整官方HF checkpoint。

输出包含`training_data.json`、`validation_anchors.json`、`trainable_parameters.json`、`run_config.json`、`metrics.jsonl`、`status.json`、代码快照、`best_checkpoint.json`/`latest_checkpoint.json`和专家检查点。

Ctrl+C停止前台训练，保留**已完成保存**的检查点；不把可能在optimizer.step中被中断的模型保存成新检查点。支持通过`--checkpoint /history/milk_runs/原RUN名/checkpoints/step_xxxxxx`在新实验中加载专家权重，但新建优化器/学习率计划/采样状态；不声称精确resume。`/history`对应宿主机`pi05_deploy/runtime/outputs/`。

## 已完成的脚本检查

- Python/shell语法及默认dry-run。
- CPU损失数学检查：8维等权基线、填充维度零梯度、无效动作mask、夹爪加权和空mask拒绝。
- 当前五批真实数据哈希、划分和训练集统计准备；40/9/9条，裁切示教排除1条。
- 真实10步窗口、三路RGB和划分隔离的CPU读取检查，结果见`pi05_deploy/reports/milk_expert_data_check.log`。

参考：[OpenPI](https://github.com/Physical-Intelligence/openpi)、[LeRobot π0.5](https://huggingface.co/docs/lerobot/pi05)、[π0.5论文](https://www.physicalintelligence.company/download/pi05.pdf)。