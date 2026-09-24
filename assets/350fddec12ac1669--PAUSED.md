# 暂停记录 — 2026-09-21

> 已于用户要求继续后恢复并完成最终重复验收，见 [FINAL_REPORT.md](FINAL_REPORT.md)。以下内容保留为历史暂停快照。

用户要求“我们先暂停，一会再继续”。已停止本任务 `codex-fdp21-final16` 容器。
最终验收批次SSH命令以143退出，`set -e`阻止后续final_exact启动；两次核验无
`codex-fdp21-*`活动容器。未停止其他业务容器。所有本次SSH均为非复用短时连接，已结束。

## 已完成

- exact分阶段计时：4条件，未插桩中位4.117秒；主要瓶颈为两轮refiner网络约2.057秒与scorer网络约0.939秒。
- LingBot全13帧单项消融、组合、缓存测试、布局单网络诊断、分阶段候选初筛。
- 当前最快通过配置：`microbatch64 + cuDNN benchmark（保持deterministic）+ 循环内第一轮252评分后保留16候选、第二轮16精修和联合评分`。
- 该配置初筛每帧1预热+1正式，13/13满足中心≤10mm、每轴RPY≤4°；中位2.693秒，最大中心差7.756mm，逐轴最大绝对差0.058/0.529/1.089°。
- 64候选初筛13/13与原始矩阵完全一致，中位2.966秒。32候选只有11/13通过，不能因为16通过而把32标成通过。
- 不筛候选的microbatch64+cuDNN组合13/13矩阵一致，中位3.094秒。
- raw仅本轮profile覆盖两个条件，未做完整优化初筛；用户只要求一个完整深度分支通过，当前选LingBot。

## 尚未完成

最终每条件1预热+5正式重复验收刚启动即被用户暂停：final16在初始化阶段停止，尚未生成结果JSON；final_exact未启动。
因此不能宣称65次正式验收通过，也不能宣称已经达到1秒、绝对真值精度或生产可用。

恢复时先核验固定镜像和输入、并行负载，再使用新的run_id，例如：

```bash
bash /home/galbot/Lsy03/fdp_accuracy_speed_20260921/code/run_remote.sh final16_resume1 --variant microbatch --tune-cudnn --candidate-k 16 --stage-mode inline --branch lingbot --repeats 5
bash /home/galbot/Lsy03/fdp_accuracy_speed_20260921/code/run_remote.sh final_exact_resume1 --variant exact --branch lingbot --repeats 5
```

仅在本任务已授权的冻结帧离线计算范围内恢复。保持原始生产环境不变，不调用SDK、相机或运动。
验收后核对每次中心和三个轴角度的最坏差异、重复矩阵一致性、P50/P95/最大时间，并与初筛输出比较。
原始Orin参考为`../20260920_fdp_13_validation/original_full.json`；本轮exact全13帧已复现它。

## 保存位置

- 远端：`/home/galbot/Lsy03/fdp_accuracy_speed_20260921/`，代码、各阶段代码快照、编译缓存、输出均保留。
- 本地：本目录全部结果、`all_runs_summary.json/.csv`、`pause_evidence/`及`pause_evidence.tar.gz`。
- 证据包SHA-256：`1217faf7fd3ae8874ed337866227e7b3275beb41985eeba7299eec0d3afda891`，本地核验一致。
- 证据包含完整运行日志和三次旧代码快照；不包含原始输入、权重、编译缓存或任何凭据。

下一步继续最终重复验收即可，不必重跑已完成初筛。