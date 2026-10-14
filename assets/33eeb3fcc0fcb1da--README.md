# G1 牛奶 ACT 离线训练

入口 `lerobot_deploy/scripts/train_milk_act.sh` 使用已验收的 LeRobot 0.4.4 Docker 镜像。
从 ImageNet ResNet18 开始，ACT Transformer/动作头新初始化；训练完整 ACT（含视觉骨干），不用 LoRA。
官方 ACT VAE 目标为归一化动作 L1＋10×KL。自定义训练循环显式应用质量筛选、五批采样与验证；不是未经修改的官方 CLI。

## 执行

在项目根目录运行：

```bash
bash lerobot_deploy/scripts/train_milk_act.sh --dry-run
bash lerobot_deploy/scripts/train_milk_act.sh prepare
bash lerobot_deploy/scripts/train_milk_act.sh check
# 正式训练：默认最多10000次更新，batch4
bash lerobot_deploy/scripts/train_milk_act.sh train
# 如需先做2000步试验，用下行替代上行，不要同时启动
bash lerobot_deploy/scripts/train_milk_act.sh train --steps 2000
```

无参数时只预览。`prepare` 核对数据文件/对齐计划/逐帧源记录哈希、全量Parquet标签及质量标记一致性、有限值、关节顺序、夹爪单位/范围和episode隔离；不启动模型。
`check` 用训练和验证组当前观测做GPU前后向、有限梯度、动作输出、未来标签泄漏和精确权重重载检查，执行0次优化器更新；不读测试组图像。
检查中的Adam显存为估计值，正式训练以实际峰值为准。

每次创建独立目录，启动时显示绝对 `RUN_DIR`，默认位于 `lerobot_deploy/runtime/outputs/milk_act_runs/`。
输入原数据和缓存权重只读，运行断网。训练是前台执行，Ctrl+C停止容器并保留已经写完的检查点；没有后台日志退出即继续的模式，也没有精确resume接口。

## 数据准入及固定划分

固定使用9月30日三批及10月9日10:00、10:34两批，共59条、10569帧。
最新批次episode_000001裁去了缺少已接受夹爪目标的52帧前缀，默认整条排除，原件与导出文件保留。
其余58条采用与当前π0.5实验相同的 **40训练／9验证／9独立测试**，前三批保留原32/7划分。
默认10步窗口：训练5726、验证1255、测试1321。改变horizon会重算窗口，episode划分保持。

只采样当前时序有效且当前动作有效、未来H步动作有效且完整、无跨episode padding的起点；不删帧后拼接时间轴。
state为实测左臂七关节rad＋夹爪m，action为SDK已接受绝对目标，J2已裁剪的实际标签保留。
默认H=10（约1秒），可用`--horizon 50`做5秒动作块对照；这不表示实机应该开环执行整个动作块。

原始三路相机分辨率不同。输入等比例缩放后居中黑色补边到224×224，三视角保留；按固定ImageNet均值/方差处理RGB。
state/action使用仅训练episodes拟合的mean/std归一化，验证/测试不参与统计。
原始深度和腕力保留，此ACT基线只用RGB和8维state。

## 默认参数和模型选择

- 10000步、batch4、FP32，官方ACT网络、ResNet18骨干、VAE latent32、KL权重10。
- AdamW主网络/视觉骨干学习率均1e-5，weight decay1e-4，梯度裁剪1；固定学习率，无额外调度器。
- 每10步打印总loss、L1、KL、梯度、学习率、耗时与ETA。
- 每500步验证，每1000步保存；验证改进立即保存best。
- 每条验证示教16个均匀起点（144窗口），另行评估全部夹爪开闭转折窗口（目标变化≥20mm）。
- 按均匀验证集`关节MAE(度)/2＋夹爪MAE(mm)/5`选择最佳已训练模型；分母是项目比较尺度。连续10次验证未改善≥0.001提前停止，`--early-stop-patience 0`关闭。

验证走真正推理路径（eval、零latent），仅传入当前观测，不提供未来标签。验证的`val_l1_normalized`是推理L1，不是含KL的训练总loss；二者不直接等同比较。
保存训练前随机模型的baseline指标，并记录已训练best是否优于baseline。物理误差为未经限幅输出，报告保持当前实测状态基线和夹爪越界。

## 检查点、评估及状态

```bash
bash lerobot_deploy/scripts/train_milk_act.sh status /完整RUN_DIR
bash lerobot_deploy/scripts/train_milk_act.sh logs /完整RUN_DIR
# 训练后先对选出的best做全部验证窗口评估
bash lerobot_deploy/scripts/train_milk_act.sh evaluate /完整RUN_DIR/checkpoints/step_001000/pretrained_model
# 方案和模型选定后，再评估保留的独立测试集；不要用于反复调参
bash lerobot_deploy/scripts/train_milk_act.sh evaluate /完整RUN_DIR/checkpoints/step_001000/pretrained_model --split test
```

将示例step_001000替换为`best_checkpoint.json`中实际路径。指针里的`/output/`对应该宿主机RUN_DIR；不能当作宿主机路径直接执行。
改变horizon的实验评估需传相同`--horizon`；图像尺寸从检查点的输入契约读取。
评估只执行推理，验证数据/划分/归一化与检查点哈希一致性，不更新优化器。

输出含`training_data.json`、`data_audit.json`、`run_config.json`、`validation_anchors.json`、`metrics.jsonl`、`status.json`及best/latest指针。
检查点含官方格式`pretrained_model/`（配置、safetensors、预处理/后处理、统计量、`inference_io.json`）、数据清单/文件摘要及训练模式下的优化器状态。
优化器状态用于审计，未提供采样器游标/进程的精确恢复。每次train都是新实验。

外部推理必须复现resize/padding，再应用保存的官方处理器。可使用本次RUN_DIR的src/runtime.py：

```python
from runtime import load_model, predict
policy, pre, post = load_model('/完整检查点/pretrained_model')
# raw: 已batch化的当前三RGB（CHW float[0,1]）和8维实测state，rad/m。
action = predict(policy, pre, post, raw)  # [B,H,8]，rad/m；无未来标签输入
```

## 结果范围

2026-10-09已完成本入口数据准备和GPU零更新检查：五批10569帧数值标签/质量标记与源记录一致，40/9/9划分及训练统计与π0.5实验一致；49条训练/验证示教抽样读取、真实batch4前后向、未来标签泄漏、精确权重重载、144个均匀验证窗口及192个转折窗口检查通过。在新容器中重载零更新权重的全部1255个验证窗口评估也通过。**没有启动正式训练，没有读取独立测试集图像。** 证据索引见`lerobot_deploy/reports/milk_act_preflight_20261009.json`。

数据哈希和格式验证通过、质量筛选支持离线实验；物理曝光同步、环视时间差与在线因果对应仍未认证。
所有权重标记`real_robot_ready=false`；离线误差不等于抓取成功率，脚本不发送机器人指令。