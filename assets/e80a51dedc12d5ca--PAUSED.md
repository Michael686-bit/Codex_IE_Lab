# 跨组验证中断保存 — 2026-09-21

> 2026-09-22已完成A0 C补跑，并注明来源合并完整原版；原版与A4的28帧对照已完成。以下保留为历史中断快照，当前结果见FINAL_REPORT.md。

当前回合主动中断后，检测到原版容器仍运行，已停止本任务`codex-fdp-cross-original_all`；父SSH批次以143退出。任务容器为空，所有本次SSH命令已结束，未停止其他任务容器。

## 已完成

- 快速方案：全部28帧×5正式=140次完成，140/140小于1秒。
- 原版：84次正式已保存；D12帧×5=60、H3帧×5=15全部完成；C组L01完成5次，L02完成4次，其余C尚未运行。
- 完整可比的D12/12、H3/3均满足中心≤10mm、逐轴≤4°。D最大中心差约0.001mm，H约0.004mm，均远低于阈值。
- H三帧原版输出估计倾角约5.974/5.987/6.848°，不是独立实测真值。
- C目前只有1帧完成本轮全部原版重复，不能宣称本轮28帧全部验收完成；上一轮C13完整结果仍单独保留。
- 暂停后重新核验全部168输入文件哈希一致。

## 恢复入口

无需重跑已完成快速版或D/H原版。优先在原目录用新run_id补跑整个C组，使其具有完整独立预热与重复：

```bash
bash /home/galbot/Lsy03/fdp_cross_dataset_20260921/code/run_remote.sh original_C_resume1 --mode original --group C --repeats 5
```

完成后生成透明的组合原版结果：保留`original_all_partial.json`中的D/H全部行，使用新C组全部行替代旧C部分行，不能把旧C与新C叠加成更多重复。
核对两个源文件manifest SHA、共同输入哈希、原版配置一致；保留两份原始文件与来源/初始化时间记录。
组合结果应为28个唯一条件、140次formal、28次warmup，每帧index 0–4；其输入哈希与`upright_all.json`一致。
然后运行`compare.py`（不加--allow-partial）生成comparison.json/.csv，再运行render_report.py。
当前固定原版与快速版模式不要根据D/H结果调参；输入/容器隔离方式不变。

## 证据

本地：`upright_all.json`、`original_all_partial.json`、`progress_comparison.json/.csv`、`cases_manifest.json`、`PAUSE_STATE.json`。
远端：`/home/galbot/Lsy03/fdp_cross_dataset_20260921/`，代码、缓存、输入、输出均保留。
包`pause_evidence.tar.gz` SHA-256：`562b6154f2ac1fc22fcb253c7f751534e6c4a4918b31bcd8a67844fd46347d36`；本地哈希及包内两份原始结果逐字节核验通过。
证据包包含代码、日志、输出、清单与暂停状态，不含凭据、权重或编译缓存。