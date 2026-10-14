# 牛奶任务重训 v2：明确目标、独立夹爪、短期关节增量

这是新的离线重训实验，默认从缓存的SmolVLA基础权重开始。此前模型及三个原始LeRobot v3数据集保留为对照。深度仍为原始深度，腕力仍为原始SDK观测，没有加入LingBot-Depth，也没有证明腕力坐标、清零、重力补偿或物理曝光同步已完成标定。

## 目标及验证门槛

以下是本项目的探索性目标，不是行业安全标准，也不是效果承诺：

| 指标 | 旧模型全713窗口结果 | v2实验目标 |
|---|---:|---:|
| 首步关节MAE（七关节平均） | 3.59° | ≤2°（先看原始预测） |
| 首步夹爪MAE | 16.82mm | ≤5mm |
| 1秒动作范围关节MAE | 需用旧预测前10步同口径比较 | ≤3° |
| 1秒动作范围夹爪MAE | 需用旧预测前10步同口径比较 | ≤10mm |
| 夹爪输出范围 | 曾出现−32.59～146.77mm | sigmoid结构保证0～100mm |
| 关节输出范围 | 曾超出J2保守限位 | 输出加范围保护，同时单独统计限幅前越界 |
| 重复同一输入 | 有随机采样差异 | 默认固定采样种子可复现；不宣称已学会抗噪声 |
| 运动预测 | 某些组不优于保持目标 | 1秒范围误差应优于保持当前实测状态的基线 |

训练过程中使用7条验证示教上的56个固定起点选模型，最后必须对全部713个验证窗口评估。这个集合已经用于模型选择，不是独立测试集。正式实机成功率还需要新场景/新采集的闭环测试。

## 方案

1. **预测时间**：50步约5秒改成10步约1秒。保留同一缓存样本、同一32条训练/7条验证划分，仍使用3581个训练起点、713个验证起点。源标签不修改，只取原动作序列的前10步。
2. **关节目标**：保持原SDK绝对目标的物理含义，训练时转换为`未来目标角度−当前实测角度`。增量均值/标准差仅由训练起点拟合。首步目标仍是原SDK指令，不强行改为当前实测状态。
3. **关节loss**：只监督7个真实关节的flow-matching误差；其他25个内部槽位不参加该loss。训练和采样时填充槽位的噪声固定为0，采样时填充状态也保持0。它是对官方flow-matching构造的显式适配，不仅仅把旧loss乘4。
4. **夹爪**：新增观测条件注意力头，输出10个sigmoid开度，范围0～0.1m。用真实连续开度的SmoothL1监督，辅以接近全开/全闭目标的分类监督；中间开度标签保留。只读取当前RGB/语言/状态/深度/力，预测头不读取未来动作标签。
5. **近端权重**：前3个动作时刻权重为2，其余为1，按总权重归一化。
6. **采样**：训练中对1秒内夹爪变化≥20mm的训练起点提高到2倍采样权重，以增加抓放转折覆盖。验证分布不重采样。
7. **模型选择**：按物理误差综合分数，而不是旧32维loss选best：`首步原始关节MAE/2 + 首步夹爪MAE/5 + 1秒原始关节MAE/3 + 1秒夹爪MAE/10`。这些分母是人为指定的项目目标尺度。限幅前指标用于选模，避免靠裁剪隐藏坏预测。
8. **优化**：默认5000步、batch2、AdamW lr=1e-4、100步warmup。每100步验证，验证分数连续5次未有≥0.001改善则学习率减半；连续15次未达该改善则早停，给中间两次降学习率留时间。最低lr=1e-6。这里使用验证驱动调度，不再叠加余弦调度。

保留三路RGB、14维实测状态/原始腕力和深度+mask。冻结VLM；训练动作专家、状态/动作投影、深度编码器及新夹爪头。没有LoRA。

## 用户执行

缓存已由旧实验生成，不用重新prepare：

```bash
# 查看配置，无训练操作
bash lerobot_deploy/scripts/train_milk_retrain_v2.sh --dry-run

# GPU数据/前后向/目标泄漏/确定性/模型保存加载检查；0次优化器更新
bash lerobot_deploy/scripts/train_milk_retrain_v2.sh check

# 新的一轮重训，直接显示训练与验证指标
bash lerobot_deploy/scripts/train_milk_retrain_v2.sh train

# 也可以先做2000步试验
bash lerobot_deploy/scripts/train_milk_retrain_v2.sh train --steps 2000

# 默认启动5000步；注意不要把两条train命令同时执行
# 进度/日志：用启动时打印的RUN_DIR替换
bash lerobot_deploy/scripts/train_milk_retrain_v2.sh status RUN_DIR
bash lerobot_deploy/scripts/train_milk_retrain_v2.sh logs RUN_DIR

# 结束后对该RUN_DIR的best模型评估全部713个验证窗口
bash lerobot_deploy/scripts/train_milk_retrain_v2.sh eval RUN_DIR

# 从这一轮的best完整v2权重开始新的低学习率阶段
# 先复核载入模型是否复现同一56窗口分数；0次优化器更新
bash lerobot_deploy/scripts/train_milk_retrain_v2.sh verify-continue RUN_DIR
# 再追加最多3000步，默认LR2e-5，仍显示训练loss/验证loss/物理误差
bash lerobot_deploy/scripts/train_milk_retrain_v2.sh continue RUN_DIR
```

`continue`会保留完整v2模型，包括动作专家、深度编码器、夹爪头、输入归一化、训练集增量统计、关节限位和训练/验证划分。它创建新的输出目录，重新初始化AdamW与平台调度器，warmup100步，再以2e-5继续学习；每100步验证、连续5次无显著改善降LR、15次早停。它不是恢复旧优化器/采样器游标的精确resume。会先检查缓存哈希、验证起点及原best分数复现，失败即停止。`step`表示新阶段步数，`cumulative_step`表示该权重路径累计步数，例如从1800步best继续3000步，累计4800步；原来2000步末尾被放弃的200步不计入这条路径。

`train`和`check`显示控制台日志；Ctrl+C只退出日志查看，后台容器会继续。`start`可仅启动后台训练。关机前要另行安排保存点和停止，不要把退出日志当作停止训练。

控制台显示`train_loss`、`joint7_loss`、`grip_loss`、`val_loss`及首步角度/毫米误差、best_score和学习率。新loss定义不同，不与旧0.076做绝对数值比较。

## 代码与输出

- `data.py`：复用v1缓存/原数据，训练集增量统计与转折采样权重。
- `model.py`：7维关节增量flow、专门夹爪头、原始预测/限幅结果、专用加载器。
- `runtime.py`：共同数据处理、固定验证样本、物理误差和保持当前实测状态基线。
- `controller.py`：warmup、平台降lr、早停。
- `train.py`：训练、GPU零更新检查、检查点。
- `evaluate.py`：全713窗口推理评估，保存预测数组。

每轮输出独立目录到`/mnt/data/VLA_data/smolvla_runs/`；包含源代码快照、数据/目标变换配置、metrics.jsonl、status.json、baseline.json、validation_anchors.json、best_checkpoint.json、模型和优化器状态。没有精确DataLoader游标续训接口，不声称可以无缝resume。

## 推理接口

这套权重必须用v2专用加载器，不能用原始SmolVLA或v1 DepthForcePolicy加载：

```python
from model import RetrainPolicy, preprocess
model, pre = RetrainPolicy.load_bundle('/output/checkpoints/step_001000/model_bundle', 'cuda')
model.eval()
# raw是已batch化的当前RGB/14维实测状态和腕力/米制深度+mask/task。
# 不要求未来action标签。pre会应用检查点中的输入归一化。
result = model.predict(preprocess(raw, pre, 'cuda'))
# result['raw_action']: [B,10,8]，关节未经限幅，夹爪有界
# result['action']: [B,10,8]，关节范围保护后的绝对角度rad/夹爪m
# result['joint_clamped']: [B,10,7]，范围保护触发位置
```

仅输出范围保证不能替代碰撞、速度/加速度、接触安全与物理时序验收。该脚本只做离线训练/推理，不发送机器人指令。