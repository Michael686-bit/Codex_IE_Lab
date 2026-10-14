# LingBot 全图输出版本

按用户选择，所有有效B深度值均来自LingBot-Depth v0.5整张预测，包括原来已有深度的像素。保留原始A，不做只填空洞、不做邻域筛选、不混合原始有效值；模型输出mask为假、非有限或非正值的位置保持无效。

## 执行

```bash
cd '/home/lsy03/文档/ChatGPT/VLA G1 项目'

# 可选CPU检查，不运行推理
bash lingbot_depth/full_output.sh inspect

# GPU生成完整独立B缓存，包含训练和验证的同一批输入窗口
bash lingbot_depth/full_output.sh build

# 仅在上一步中断后执行；不覆盖不同实验
bash lingbot_depth/full_output.sh build --resume

# 生成结束后也可独立复核；build最后已自动执行一次
bash lingbot_depth/full_output.sh verify \
  /mnt/data/VLA_data/smolvla_runs/multimodal_data/lingbot_full_depth_force_v1
```

`build`与`build --resume`二选一。已有完成缓存禁止重复覆盖，`--resume`会验证并返回。终端每25帧打印进度，失败保留已完成帧的哈希和来源，可继续；不自动启动训练。

默认输入A：`/mnt/data/VLA_data/smolvla_runs/multimodal_data/raw_depth_force_v1`。

默认输出B：`/mnt/data/VLA_data/smolvla_runs/multimodal_data/lingbot_full_depth_force_v1`。

可用`--output /另一个独立目录`指定B位置，恢复时必须传同一目录。不得将输出写进原始会话、LeRobot数据集或A目录。磁盘至少预留6GiB，GPU至少5GiB空闲；不足时停止，不删除文件。

## 数据范围与公平对照

只处理现有A缓存需要的4294个观察窗口（3581训练、713验证），不额外改变RGB、六维力、动作、任务、32/7示教划分或归一化统计。不是将所有12108个原始深度帧重新导出为LeRobot。

原始RGB与深度按照A中的来源精确时间戳取回，核对负载SHA256、原始尺度/尺寸、manifest身份、内参与A缓存重现。每个原始输入只运行一次模型，重复输入可对应多个窗口。脚本从真实清单打印唯一推理帧数。

对验证集使用已经固定的同一模型、推理参数和处理规则；不会根据验证数据调整阈值或拟合模型。LingBot推理期间不更新任何权重。

## 深度语义

- 输入原始1280×720深度：uint16/10000转米，0、65535清零；RGB为同帧彩色原件；K按原始宽高归一化。
- 全分辨率LingBot推理，`apply_mask=True,resolution_level=9,use_fp16=True`，与之前图集的“LingBot全图输出”一致。
- `fullres/*.npz`保存完整1280×720模型深度（float32米，可能含模型mask产生的inf）和模型mask。没有截断到0.07～1.0m，也没有截断到uint16最大距离。
- `depth_m.npy`保存最近邻缩放到128×224的float32米制预测，无效位置清零；`depth_valid.npy`为模型mask且有限正值；`depth_source_mask.npy`为0无效、2模型预测，不存在1原始测量。
- 来源mask仅标注来源，不是置信度，不直接输入当前模型。原始测量及原始有效mask仍可从A追溯。
- 训练时原深度分支仍应用0.07～1.0m范围，保证首轮只改变深度处理方式。范围外输出保存在B，范围筛选发生在模型输入端。

全图输出会改变原本有效的瓶身距离；完整性验证不能证明距离更准确或抓取收益。此选择按独立实验版本记录，不覆写已训练模型。

## 输出

- `manifest.json`：完整处理成功后才生成；格式`g1_rgb_depth_force_cache/2`。
- `processing_plan.json/.sha256`、`A_manifest_snapshot.json`、`runtime.json`、`code_snapshot/`：固定A、模型、源码与运行环境。
- `fullres/*.npz/.json`：全分辨率输出、原始输入位置与负载哈希、输出哈希及改变量统计。
- `depth_m.npy`、`depth_valid.npy`、`depth_source_mask.npy`、`state14.npy`：训练缓存。state14与A逐文件相同。
- `fullres_provenance.json`：全分辨率结果与4294个窗口的映射。
- `verification.json`、`status.json`、`report.html`：完整性/格式验证结果与报告。

状态`cache_verified`表示：窗口/划分/统计不变、缓存可从全分辨率输出重现、米制数值/掩码语义正确、哈希一致；`metric_accuracy_verified`仍为false，`training_started`为false。

## 后续训练入口（本次不会自动运行）

训练读取器已兼容新的米制浮点缓存，也保留原uint16 A读取方式。新模型bundle会记录`depth_processing=lingbot_full_frame`和权重SHA，避免部署时误用原始深度。

```bash
# 只显示选择的缓存，不运行训练
bash lerobot_deploy/scripts/train_milk_lingbot_full.sh --dry-run

# 如果后续决定训练，再执行这两步；它们不属于数据处理命令
bash lerobot_deploy/scripts/train_milk_lingbot_full.sh check
bash lerobot_deploy/scripts/train_milk_lingbot_full.sh train
```

训练默认从SmolVLA基础权重开始；旧raw缓存模型不能通过原`continue`脚本无缝续训到新B（原脚本会校验缓存不一致并拒绝）。公平A/B应从相同初始化、相同预算开始。部署B模型时须在每个在线输入上复现相同LingBot处理和mask、缩放，不能直接换回原始深度。

`bash lingbot_depth/full_output.sh self-test`只进行CPU测试与读取已保存预测，不重新运行GPU或创建全量B。

## B 第5000步后的续训

默认从`smolvla-multimodal-train-20261008_183825-176799`的最佳B模型（第5000步）开始，绑定同一补全缓存。新增最多3000步、LR=5e-6、warmup=100、每100步验证、每500步保存、patience=15；累计最多8000步。使用fresh AdamW/scheduler，重新开始采样，不是精确恢复旧优化器/游标。

```bash
# 仅复核初始固定56窗口loss，预期约0.068760，不更新权重
bash lerobot_deploy/scripts/continue_milk_lingbot_full.sh verify

# 确认verify通过后，开启独立小学习率续训阶段
bash lerobot_deploy/scripts/continue_milk_lingbot_full.sh
```

保存已有B第5000步模型，新阶段结果写独立目录。后续若再续训，可用`--source-run /新阶段RUN_DIR`明确指定该阶段的最佳模型。只看56窗口loss不足以证明动作改善，仍需对全部713验证窗口检查预测误差与稳定性。