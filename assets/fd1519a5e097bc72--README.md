# SmolVLA：三路RGB + 左腕原始六维力 + 原始深度

这是现有牛奶任务的离线多模态对照代码。不会自动启动机器人，不上传数据。现有三个LeRobot v3数据集保持只读，增加派生深度缓存；目前使用原始深度，尚未进行LingBot-Depth补全。

## 用户执行

项目根目录下：

```bash
# 查看配置，不启动Docker/训练
bash lerobot_deploy/scripts/train_milk_depth_force.sh --dry-run

# 1. 准备缓存：CPU提取、逐个深度负载哈希验证、保留帧来源
bash lerobot_deploy/scripts/train_milk_depth_force.sh prepare

# 2. 检查：真实数据GPU前向、反向及保存/加载，不更新权重
bash lerobot_deploy/scripts/train_milk_depth_force.sh check

# 3. 后台启动初步训练，默认2000步，打印RUN_DIR
bash lerobot_deploy/scripts/train_milk_depth_force.sh train

# 按同一数据划分做消融对照，分别执行；不要无意同时启动多轮
bash lerobot_deploy/scripts/train_milk_depth_force.sh start --mode rgb
bash lerobot_deploy/scripts/train_milk_depth_force.sh start --mode force
bash lerobot_deploy/scripts/train_milk_depth_force.sh start --mode depth

# 查看状态和日志
bash lerobot_deploy/scripts/train_milk_depth_force.sh status RUN_DIR
bash lerobot_deploy/scripts/train_milk_depth_force.sh logs RUN_DIR
```

默认batch=1、lr=1e-4、100步warmup、每100步验证、每500步及验证改进时保存；连续15次验证没有改善提前停止。需要20k预算时使用 `start --steps 20000 --warmup-steps 1000 --eval-every 500 --save-every 1000`。先看小规模结果再决定预算。

## 模型与输入

- 三路RGB：头左、左腕、右前环视，沿用SmolVLA视觉通路。
- 14维数值观测：[J1…J7, gripper_width, Fx,Fy,Fz,Tx,Ty,Tz]，前7维rad、夹爪m、力N、力矩N·m。
- 腕部深度原件：1280×720、小端uint16，米=raw/10000；缓存以最近邻降至128×224，保留0/65535编码。读取后使用 `depth_near <= depth <= depth_far`、有限值及原始无效掩码，默认0.07～1.0m。这个范围是实验输入筛选，不是精度合格声明。
- 深度经过固定对数尺度映射，与像素有效mask组成2通道，送入轻量CNN，产生18维深度特征。原8维状态+6维力+18维深度特征占用SmolVLA内部32个状态槽位，经原state_proj融合。
- 深度编码器末层零初始化，使新分支初始输出为零；最后一层先获得梯度，随训练建立深度影响。模型并非一开始就已学会深度。
- 输出依然为50×8的关节/夹爪绝对位置目标，10Hz动作时间线。没有力目标或力控指令。
- 冻结VLM，训练动作专家、相关状态/动作投影和新增深度编码器。无LoRA，rank不适用。

这是自定义多模态扩展，不能把保存结果直接当作未修改的官方SmolVLA checkpoint。低分辨率CNN压缩是初步方案，尚未验证其细粒度几何收益。

## 数据、质量与公平对照

沿用39条候选的32条训练/7条验证划分。仅保留当前RGB/深度/腕力时序检查通过、腕RGB与深度原始时间戳一致、后续50步动作完整不跨组的起点。预计3581个训练起点、713个验证起点；实际以prepare输出为准。四种mode共用同一子集，基线比较请使用新脚本的 `--mode rgb`，避免和旧实验因样本/归一化不同混比。

状态14维统计仅由最终训练起点计算；动作统计沿用原训练集接受目标。验证数据不参与统计。默认每条验证示教选择8个固定起点，共56个，噪声seed9042。固定验证损失是模型选择指标，不能视为实机成功率。

六维力采用SDK原始传感器观测：坐标系标定、tare和重力补偿状态未知，不减去首帧或擅自构造纯接触力。静态重力/安装偏置可能影响泛化。当前时序源时钟和在线观测因果性仍未物理验收。

## 缓存与输出

缓存：`/mnt/data/VLA_data/smolvla_runs/multimodal_data/raw_depth_force_v1/`。
包含 `depth_uint16.npy`、`state14.npy`、`manifest.json`，记录逐样本原始会话、episode、索引、深度和腕力来源、质量筛选及哈希。完成manifest之前的目录视为未完成；脚本拒绝覆盖已有缓存，失败后先检查原因，不删除原件。

每次训练创建独立RUN_DIR，含状态、metrics.jsonl、配置、代码快照和检查点。`checkpoints/step_xxxxxx/model_bundle/` 包含：

- `policy/`：官方SmolVLA权重/14维配置/归一化与预后处理。
- `depth_encoder.safetensors`：深度编码器参数（启用深度时）。
- `multimodal_config.json`：输入语义、模式、深度尺度和范围、专用加载器要求。

所有保存模型均标记为尚未验收实机部署。优化器状态保存用于追溯，但本版没有精确DataLoader游标恢复功能，不提供无缝resume命令。

## 加载与推理

在对应容器环境内，把本次RUN_DIR的src目录加入Python路径：

```python
from model import DepthForcePolicy, preprocess
model, pre, post = DepthForcePolicy.load_bundle('/output/checkpoints/step_002000/model_bundle', 'cuda')
model.eval()
# raw必须是已经batch化的字典：三路RGB[1,3,H,W]、原始state[1,14]、task列表、
# observation.depth.left_wrist_m [1,128,224]（米）、
# observation.depth.left_wrist_valid [1,128,224]（bool）。
# pre会应用检查点保存的训练集归一化。不要提前重复归一化。
import torch
with torch.inference_mode():
    actions = post(model.predict_action_chunk(preprocess(raw, pre, 'cuda')))
# actions: [1,50,8]，仅用于离线检查。
```

## 控制台loss显示

使用 `train` 会启动后台容器并立即跟随日志。控制台每10步显示当前小段训练loss平均值、最近一次固定验证loss及其计算步数、最佳验证loss、梯度、学习率和进度。每100步重新计算验证loss，因此两次验证之间显示的val_loss相同是正常的。日志同时写入RUN_DIR/metrics.jsonl；实时状态写入status.json。

查看日志时按Ctrl+C只退出日志界面，容器训练仍继续。不要再次运行train来查看同一轮训练，请用logs RUN_DIR。若要停止训练，需要单独安排检查点保存和容器停止。

## 从本轮最佳权重继续

```bash
# 先核对初始验证loss，预期约0.08353058；此命令不更新权重
bash lerobot_deploy/scripts/continue_milk_depth_force.sh verify

# 从原实验best_checkpoint.json加载，低学习率继续最多5000步
bash lerobot_deploy/scripts/continue_milk_depth_force.sh
```

默认加载`smolvla-multimodal-train-20261008_132914-76903`的最佳多模态权重（第1900步），完整恢复SmolVLA、深度编码器、预处理和归一化。启动前严格检查缓存哈希、模式、种子、深度范围及固定验证样本与原实验一致。新阶段使用fresh AdamW和学习率调度，采样重新开始；这不是精确恢复旧优化器/数据游标。默认新增最多5000步，累计上限为1900+5000=6900步，而不是重新训练基础模型。

新阶段每100步验证；连续15次不优于该阶段最佳值即停止。每500步及验证改进时保存。若没有优于起始权重，源模型仍是最佳选择。可以加`--steps 3000`改变本阶段预算。终端显示本阶段步数及累计步数；旧实验目录不覆盖。

## 放宽早停（2026-10-08）

续训默认源更新为第二轮`smolvla-multimodal-train-20261008_134056-77817`的最佳模型（本阶段1300步、累计3200步）。默认patience=15，每100步验证，相当于连续1500个新增更新没有刷新最佳值才停止；总预算仍最多新增5000步。保留最佳检查点规则。

```bash
bash lerobot_deploy/scripts/continue_milk_depth_force.sh --early-stop-patience 15
# 指定其他实验的best_checkpoint作为来源：
bash lerobot_deploy/scripts/continue_milk_depth_force.sh --source-run /实际RUN_DIR --early-stop-patience 15
```

新阶段使用较小学习率和fresh AdamW/scheduler。若确需关闭早停，可传0；初步实验建议保留早停。提高patience不会保证更好的验证结果。