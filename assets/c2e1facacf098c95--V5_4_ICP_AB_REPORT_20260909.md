# V5-4 受约束 ICP A/B 实验结果

日期：2026-09-09。输出目录：
`outputs/v5_4_icp_ab_20260909_03/`。

前两次重跑因可见性实现不一致而被保留并标记为 superseded，详见
[重跑说明](V5_4_ICP_AB_REPLAY_NOTES_20260909.md)；本报告只引用 `_03`。

## 目的与范围

本阶段首次执行 V5-4，用来判断 ICP 是否能在现有 FDP 解耦链中改善位姿后端。
固定 D02–D12 的确认 LingBot 深度、最终 ROI mask、相机内参、捕获时刻 TF 和
冻结 mesh；没有重新运行 SAM3/LingBot，没有调用 FDP 服务，没有连接机器人。

比较三条后端：

1. `shell_fit`：现有 V5-2/V5-3b 最优纯壳体拟合结果；
2. `constrained_icp`：从同一 shell-fit 位姿开始，只配准可见的
   `rim_flange/outer_shell/inner_shell`，优化 x/y/z/yaw；
3. `direct_full_mesh_icp`：从 shell-fit 选择的同一粗初值开始，将全部 mesh
   角色作为可见模型点，作为负面对照。

ICP 实现使用 SciPy `least_squares`、`cKDTree`、多尺度体素、Cauchy 式对应权重、
最大对应距离和相对初值的 ±80 mm/±12° 边界；没有依赖 Open3D。ICP 残差和
FDP 差异都只是拟合诊断。

复现命令：

```bash
cd /home/lsy03/文档/ChatGPT/S1/experiments/20260907_bin_rim_pose
OPENBLAS_NUM_THREADS=1 python3 -B run_icp_ab_batch.py \
  --batch-index ../20260903_fdp_baseline/OPERATOR_CONFIRMED_D02_D12_20260908.json \
  --baseline-dir outputs/v5_2_visibility_D02_D12_20260908_03 \
  --model-dir outputs/v5_mesh_shell_model_20260908_01 \
  --config config/default.json \
  --output-dir outputs/v5_4_icp_ab_20260909_03
```

## 结果

11/11 帧完成，运行错误 0。受约束 ICP 和直接全 mesh ICP 均在 11/11 帧完成
数值优化，但“运行完成”不等于位姿接受或抓取可用。

| 帧 | shell p90 (mm) | 受约束 ICP p90 (mm) | 直接全 mesh p90 (mm) |
|---|---:|---:|---:|
| D02 | 17.79 | 17.93 | 36.40 |
| D03 | 17.60 | 18.18 | 34.42 |
| D04 | 15.40 | 15.20 | 87.61 |
| D05 | 13.76 | 13.74 | 97.86 |
| D06 | 15.88 | 15.75 | 117.89 |
| D07 | 15.94 | 16.01 | 81.31 |
| D08 | 27.04 | 27.25 | 38.07 |
| D09 | 25.32 | 26.84 | 36.24 |
| D10 | 15.35 | 15.29 | 124.39 |
| D11 | 17.32 | 16.75 | 126.64 |
| D12 | 58.27 | 58.12 | 70.75 |

相对 shell-fit 的模型到观测 p90：

- 受约束 ICP：6/11 帧下降，5/11 帧上升；变化中位数 **−0.02 mm**，均值
  **+0.13 mm**。中心位姿变化中位数约 **0.83 mm/0.009°**，p95 约
  **4.41 mm/0.21°**。
- 直接全 mesh ICP：0/11 帧下降，11/11 帧上升；变化中位数
  **+65.38 mm**，均值 **+55.63 mm**；偏航变化中位数约 **43.39°**。

当前数据支持的结论是：受约束 ICP 可以作为局部精修程序运行，但在现有观测
和模型上没有显示出有意义的整体收益；直接把完整 mesh 交给 ICP 不适合作为
主路径。

## 可观测性诊断

受约束分支的可见模型点几乎都是竖直壁面。11/11 帧的模型法向 z 轴支持都
低于当前诊断阈值，因此 z 方向没有被观测充分约束，主要继承 shell-fit 初值
和尺寸/直立先验。直接全 mesh 分支虽然有 z 法向点，但其表面角色混杂且残差
大，不能据此认为 z 已正确恢复。

合成回归也验证了这一点：只给四个竖直平面时，x/y/yaw 可恢复而 z 保留初值
误差；加入带 z 法向的水平面后，已知变换在 1 mm 噪声下可恢复到约 0.1 mm、
0.01° 量级。该结果是算法可观测性检查，不是实物精度承诺。

## 当前判断与下一步

本轮不把 ICP 接入抓取，也不把 9/11 或 ICP 残差称为准确率。下一步应优先
解决“观测点中是否包含可信的箱沿/水平面、匹配面属于内壁还是外壁”这两个
问题，再决定 ICP 是否值得继续调参：

1. 从同一确认 mask 中构造受控的箱沿/顶面点集或法向，增加 z 的真实观测，
   同时排除箱内货物和背景；
2. 对内壁、外壁、法兰分角色建立对应门禁，保留竞争解，不用更低 RMSE 强行
   选解；
3. 在模型和观测对应确认后，重新比较 shell-fit 与 shell-fit+ICP；
4. 只有独立测量参考可用且位姿/短边误差达标后，才评估抓取或 OrinX 性能。

## 证据与验证

- 机器结果：[批量 SUMMARY](outputs/v5_4_icp_ab_20260909_03/SUMMARY.json)
- 逐帧结果：各 `D02`～`D12` 目录下的 `icp_ab_result.json`
- 可视化：[接触表](outputs/v5_4_icp_ab_20260909_03/contact_sheet.png)
- 输入、模型和源码哈希：批次 `batch_input_manifest.json` 与 `ASSET_MANIFEST.json`
- 离线测试：`python3 -B -m unittest discover -s experiments/20260907_bin_rim_pose/tests -v`，
  **55 项通过**。

正式结果仍保持 `accuracy_validated=false`、`grasp_ready=false`、
`outer_surface_identity_verified=false`。全程 `network_services_called=false`、
`robot_accessed=false`、`motion_commands_sent=false`。