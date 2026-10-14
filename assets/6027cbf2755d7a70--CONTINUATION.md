# 牛奶π0.5专家：从1900步开始的新阶段

入口：`pi05_deploy/scripts/continue_milk_expert.sh`。默认仅预览，所有GPU检查和训练由用户手动执行。

```bash
# 预览参数，不启动Docker或训练
bash '/home/lsy03/文档/ChatGPT/VLA G1 项目/pi05_deploy/scripts/continue_milk_expert.sh' --dry-run

# 可选：重载1900步专家，按新验证口径评估初始化；0次优化器更新
bash '/home/lsy03/文档/ChatGPT/VLA G1 项目/pi05_deploy/scripts/continue_milk_expert.sh' --verify-init-only

# 前台低学习率续训，默认新增最多1000次优化器更新
bash '/home/lsy03/文档/ChatGPT/VLA G1 项目/pi05_deploy/scripts/continue_milk_expert.sh' --execute

# 改为新增最多2000步
bash '/home/lsy03/文档/ChatGPT/VLA G1 项目/pi05_deploy/scripts/continue_milk_expert.sh' --execute --steps 2000
```

默认源是`pi05-milk-train-20261009_114715-576014/checkpoints/step_001900`，不是最后2000步权重。加载前核对专家和基础模型SHA-256、数据配置；开始处理后重新核对当前数据集、原episode划分、窗口索引和训练集归一化，任一不符即停止。

## 本阶段默认参数

- 学习率5e-6，100步warmup后余弦衰减到5e-7。
- batch=1、梯度累积4、H=10、原8维flow-matching损失、夹爪损失权重仍为1。
- 训练开闭转折窗口（未来1秒目标开度跨度≥20mm）采样权重2，其余权重1。原850/5726（14.8%）转折窗口的预期抽样占比提高到约25.9%；不改目标值、不重新拟合归一化。可用`--transition-sample-weight 1`做原采样对照。
- 每100步验证，144个均匀窗口与全部192个转折窗口分开统计；不把两组混成一个无偏总体平均。相同窗口按batch/global index固定随机种子，复核时可重现。
- best/早停仍使用均匀验证集的物理综合分数：关节MAE°/2＋夹爪MAEmm/5。转折指标另行完整显示。连续5次均匀分数不改善就早停；转折指标持续不改善时也应审阅，不以总loss变低替代开闭时机改善。
- 每200步或验证改善时保存专家权重。每次创建新RUN_DIR，原实验、权重和数据不覆盖。

`step`是本阶段新增更新数；`cumulative_step`是该权重路径的累计更新数。默认从1900起步，新增1000步最多到累计2900。初始验证为本阶段step=0、累计1900；若没有超过初始化基线，best_step=0表示沿用源权重，`baseline_checkpoint.json`指向源检查点。

## 续训的含义

这是加载专家权重的新实验，使用新的AdamW、学习率计划和采样状态；旧优化器/RNG状态没有恢复，不是精确resume。新评估口径不能与旧27个无转折验证窗口的分数直接比较，应以本阶段重新计算的初始化基线为准。独立9条测试示教不参与训练或模型选择。

`--verify-init-only`进行模型重载和144＋192窗口推理，不执行optimizer.step；不进行GPU训练。`--prepare-only`只在CPU上核对数据/划分/统计。完整GPU初始化验证与续训由用户执行，助手只做语法、预览和CPU数据兼容性测试。

源模型下的144/192窗口预测应接近上一轮扩展复核的数值（均匀夹爪约6.17mm、转折夹爪约32.21mm），具体结果以新日志为准；这些不是任务成功率。

## 输出与停止

新RUN_DIR位于`pi05_deploy/runtime/outputs/milk_runs/`。包含初始化基线、`sampling_policy.json`、两套验证起点、metrics/status、专家检查点和源代码快照。事件日志用`metric_scope=validation_uniform`或`validation_all_transitions`标明统计范围。

```bash
bash '/home/lsy03/文档/ChatGPT/VLA G1 项目/pi05_deploy/scripts/continue_milk_expert.sh' --status /完整RUN_DIR
```

Ctrl+C停止前台训练，只保留已经完整保存的检查点，不将optimizer.step中断时可能部分更新的权重当成新检查点。后续可以用`--source-checkpoint /完整检查点目录`再开一阶段；仍是fresh optimizer。

范围：本机断网Docker、冻结视觉语言骨干、FP32专家参数/BF16计算。没有机器人控制、云端上传或自动部署。