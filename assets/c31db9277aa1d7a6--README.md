# LingBot-VLA G1 独立夹爪 head：500步小实验

从已验收第12步检查点加载，保持 rank=8、alpha=16 和冻结视觉语言主干；新增观察条件驱动的夹爪 head。此入口不连接机器人，也不上传数据。原模型、数据、旧检查点只读挂载，新结果写到新运行目录。

夹爪 head 读取当前图像和语言的冻结 VLM 上下文，以及当前归一化状态；不读取动作标签、未来图像、flow 噪声或去噪时间。输出 `0.1 × sigmoid(logits)` 米。目标保持 SDK 接受的绝对宽度，不能替换为抓持物体时传感器测出的宽度。

训练损失为 `joint_flow7 + 2×gripper_SmoothL1 + 0.2×extreme_BCE`。夹爪回归使用 `目标米数 / 0.1`，SmoothL1 beta=0.05；仅目标≤20mm或≥80mm参与边界 BCE，中间目标仍参与回归。三个损失项均对前3个动作时刻加倍权重。保持50步动作块和相同3581/713窗口划分。

关节 flow 只使用槽位0–6。夹爪和其他未使用动作槽位的 flow 输入噪声及积分更新均为0，夹爪由独立 head 输出。积分状态与时间网格使用FP32；基础VLM/动作专家BF16。此轮保留原生时间采样分布，不同时更改Beta实现，以便评估夹爪分离的效果。

加载第12步模型权重后创建新的 AdamW；不恢复旧目标函数下的优化器动量。默认关节LoRA/投影学习率2e-5，夹爪head学习率3e-4，前50次更新预热。默认500步，每100步保存/验证。四个预先固定种子为20261009、42、1729、9。验证覆盖7个episode的70个固定窗口，报告逐种子及平均/最差误差，并检查夹爪种子不变性；诊断loss同时检查t=0.1/0.5/0.9。全量713窗口评估可单独执行。

## 执行

在项目根目录执行。运行目录必须是新的；check目录与训练目录分开。

```bash
bash lingbot_finetune/gripper_v2.sh check lingbot_finetune/runs/gripper_v2_user_check
bash lingbot_finetune/gripper_v2.sh verify lingbot_finetune/runs/gripper_v2_user_check

# 启动500步后台训练，然后实时查看日志：
bash lingbot_finetune/gripper_v2.sh start lingbot_finetune/runs/gripper_v2_pilot_500 --steps 500 --eval-every 100
bash lingbot_finetune/gripper_v2.sh logs lingbot_finetune/runs/gripper_v2_pilot_500

# 完成后重新加载最佳模型并做全量评估：
bash lingbot_finetune/gripper_v2.sh verify lingbot_finetune/runs/gripper_v2_pilot_500 --best
bash lingbot_finetune/gripper_v2.sh evaluate lingbot_finetune/runs/gripper_v2_pilot_500 --best --full
```

全量评估也可使用 `evaluate-full RUN --best --full`：每25个窗口保存预测、分项loss和文件哈希；中断后重跑同一命令会复用已完成分段。最终生成同名的713窗口完整报告和预测文件。训练代码、检查点、四个固定种子及指标定义均保持一致；显存保护仍然生效。

`check` 做真实数据反向传播、梯度/边界/标签泄漏/噪声不变性检查，参数更新数为0；保存初始新结构检查点供 `verify` 新容器验证。`train` 是前台训练，`start` 是后台训练。关闭 `logs` 窗口不停止训练；后台独立GPU保护在整卡余量低于2GiB时只停止自己的容器。启动前至少需16500MiB空闲显存。

`status RUN` 查看进度。异常中断后用 `resume RUN` 从最近检查点恢复，继续到原定500步；恢复代码和数据哈希必须匹配。最多丢失不足100步。检查点包含基础模型增量、独立夹爪head、优化器、随机数、采样器与配置。旧 LingBot 推理服务不识别此新结构，须使用这里的加载和推理实现。

结果包括分项loss、逐种子关节/夹爪MAE、闭合被错误预测成张开的比例、最佳检查点、显存监测和加载验证。初始化新夹爪head的预测约为训练集平均宽度；只有实际训练后才能判断是否改善。最佳分数按四种子的平均动作误差选择，最差种子同时报告。此小实验不证明真机任务成功率。