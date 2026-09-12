# 原始 SAM index 1 与最终 ROI mask 单变量离线对照

日期：2026-09-07。实验全程只读取本机冻结文件，没有连接 S1、调用网络服务、
重新运行 SAM3/LingBot/FDP、生成抓取目标或发送运动命令。

## 结论

尖锐的三角形扩张不是原始 SAM3 index 1 的分割结果，而是 ROI 后处理产生的。
哈希锁定的原始 SAM mask 有 30,512 像素；最终 ROI mask 有 31,948 像素。
最终 ROI 完整保留原 SAM mask，并在其右上侧增加 1,436 像素，IoU 为
0.9550519594。

本地 `roi_estimator.py` 的 SHA-256 与冻结案例记录的生产源码哈希
`5343f49987c3eaa6d7b9c9ad90201e8ba5a2018f13fe1a68c9c6ab3f7a2a3014`
一致。该实现默认 `augment_mask=true`；`_augment_mask()` 把尺寸吸附后的
四个三维角点投影回图像，调用 `cv2.fillPoly()` 将整个投影矩形并入原 mask，
然后做 5×5 闭运算。投影矩形超出 SAM 轮廓的部分正是图中紫红色三角区。

因此，`sam_candidates_overlay.png` 还包含所有候选的轮廓、检测框和标签，
不适合据此判断单个 mask；实际原始 `sam_mask_01.png` 本身没有该新增区域。

## 严格控制变量

两次运行的下列内容经程序核对完全一致：

- RGB、LingBot float32 深度、K、拍摄时刻 `T_base_link_from_camera`；
- 人工确认的 SAM index 1、4317 尺寸；
- 算法源码快照和 `config/default.json`；
- 冻结案例、FDP 参照及所有输入文件 SHA-256。

唯一变量是传给相同估计器的分析 mask：

1. `sam_selected`：从案例中哈希锁定的 `sam3_response.json` 解码 index 1；
2. `final_roi`：人工确认案例的 `input/mask.png`。

机器可读对照见
`outputs/mask_ablation_01/comparison.json`，可视化见
`outputs/mask_ablation_01/mask_ablation_diagnostic.png`。

## 数值结果

### 箱沿矩形分支

| 指标 | 原始 SAM index 1 | 最终 ROI mask | 差异 |
|---|---:|---:|---:|
| 候选箱体中心 X/Y/Z (m) | 1.396619 / 0.255242 / 0.485506 | 1.396430 / 0.255018 / 0.486189 | 0.744 mm（3D） |
| 候选箱口中心差 | | | 0.826 mm（3D） |
| 候选 yaw | 93.548953° | 93.183008° | 0.365945°（180° 对称） |
| 矩形内点比例 | 85.45% | 84.56% | −0.89 个百分点 |
| 矩形内点 RMSE | 4.311 mm | 3.969 mm | −0.342 mm |
| 第四条边覆盖率 | 41.7% | 58.3% | +16.6 个百分点 |
| 正式结果 | 拒绝 | 拒绝 | 均存在平面歧义 |

最终 ROI 新增区域让第四条边从“不足支持”跨过当前 50% 门限，因而最终 ROI
少了 `insufficient_support_edge_3` 拒绝原因。但是，两种 mask 都仍有
`ambiguous_rim_planes`，候选中心和 yaw 只发生亚毫米到约 0.37° 的变化。

### 箱壁几何中心分支

| 指标 | 原始 SAM index 1 | 最终 ROI mask | 差异 |
|---|---:|---:|---:|
| 候选中心 X/Y/Z (m) | 1.389927 / 0.237556 / 0.504704 | 1.390316 / 0.238961 / 0.505199 | 1.540 mm（3D） |
| 候选 yaw | 91.779781° | 91.613534° | 0.166246°（180° 对称） |
| 选中竖直壁像素 | 10,982 | 11,024 | +42 |
| 正式结果 | 拒绝 | 拒绝 | 拒绝原因完全相同 |

两者都因一条短边支持不足、矩形总内点比例不足，以及壁面高度范围与直立
175 mm 模型不相容而拒绝。

## 工程判断

这次单变量实验不支持“当前几何失败主要由 SAM3 index 1 分割错误导致”。
它支持两个更具体的结论：

1. ROI 的模板投影扩张确实制造了肉眼可见的三角区域，并能改变边支持门禁；
2. 去掉这 1,436 个新增像素后，核心的多平面歧义和箱壁高度问题仍然存在。

两种结果都不是真值，不能用谁更接近 FDP 判断谁更准。对于后续轻量几何
后端，建议将原始 SAM mask 用作目标搜索范围，不把 `augment_mask` 新增区域
当作直接深度观测。若需要尺寸模板补全，应把它保留为显式先验，并增加深度
一致性检查，而不是直接把投影多边形并入观测 mask。

## 复现命令

从仓库根目录运行。输出目录必须不存在；几何被正常拒绝时单次运行退出码为 2。

```bash
cd /home/lsy03/文档/ChatGPT/S1

OPENBLAS_NUM_THREADS=1 python3 -B \
  experiments/20260907_bin_rim_pose/run_offline.py \
  --mask-source sam_selected \
  --output-dir experiments/20260907_bin_rim_pose/outputs/mask_ablation_sam01_replay

OPENBLAS_NUM_THREADS=1 python3 -B \
  experiments/20260907_bin_rim_pose/run_offline.py \
  --mask-source final_roi \
  --output-dir experiments/20260907_bin_rim_pose/outputs/mask_ablation_final_roi_replay

python3 -B experiments/20260907_bin_rim_pose/compare_mask_ablation.py \
  --sam-run experiments/20260907_bin_rim_pose/outputs/mask_ablation_sam01_replay \
  --final-run experiments/20260907_bin_rim_pose/outputs/mask_ablation_final_roi_replay \
  --output experiments/20260907_bin_rim_pose/outputs/mask_ablation_replay/comparison.json
```

当前保存的运行是 `mask_ablation_sam01_01`、`mask_ablation_final_roi_01`
和 `mask_ablation_01`。拒绝退出码属于算法门禁结果，不是程序运行失败。