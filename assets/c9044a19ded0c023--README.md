# 4317 箱口矩形重建与轻量位姿估计实验

最新进度（2026-09-09，V5-4 首轮）：已按顺序修正有限面高度统计、增加三面联合初值，
并实现表面朝向复核。11 帧中间几何通过从 v3 的 0 帧变为 2 帧，再变为 4 帧；
最终表面复核仍为 0 帧，不能当作可靠位姿。冻结 OBJ 中央截面证明箱身壁面
间距小于 400/300 mm 最大外形尺寸且随高度变化，下一步需内外壳体模型。
43 项测试通过，原参数未改。详见 [v4 评估结论](ROUND2_V4_REPORT_20260908.md)
和 [v4 机器摘要](ROUND2_V4_SUMMARY_20260908.json)。

V5-0/V5-1 已生成 mesh 壳体模型；V5-3 纯壳体拟合也已完成 11 帧实验：9 帧
通过拟合门限、D08 无初始化、D12 残差过高。V5-4 首轮 ICP A/B 已于 2026-09-09
执行，结果见 [V5-4 ICP 报告](V5_4_ICP_AB_REPORT_20260909.md) 和
[批次报告](outputs/v5_shell_fit_D02_D12_20260908_03/REPORT.md)
和 [V5 计划](../../docs/s1_v5_mesh_shell_plan_20260908.md)。
本机直连 FDP 后的逐帧对照见
[V5-3/FDP 批量报告](outputs/v5_shell_fit_fdp_compare_D02_D12_20260908_01/REPORT.md)。

V5-2/V5-3b 已补齐 B/C/mesh 初始化来源并加入投影、遮挡和触边处理：D08 获得
独立 mesh 初值，D12 明确拒绝，最终 9/11 通过实验门限。结果见
[V5-2/V5-3b 报告](V5_2_V5_3B_REPORT_20260908.md) 和
[逐帧输出](outputs/v5_2_visibility_D02_D12_20260908_03/REPORT.md)。

V5-4 首轮受约束 ICP 运行 11/11 无错误，但相对 shell-fit 的模型 p90 中位数
只变化 -0.02 mm（6/11 改善）；直接全 mesh ICP 中位数恶化 +65.38 mm。受约束分支 11/11
没有足够 z 法向支持，z 主要由初值/先验决定。该轮结果仍是拟合诊断，不代表
绝对精度或抓取可用。详细结果见 [V5-4 ICP 报告](V5_4_ICP_AB_REPORT_20260909.md)。

V5-0/V5-1 已完成 mesh 合同审计和随高度变化的壳体截面预计算；V5-3
纯壳体拟合、V5-2/V5-3b 可见性拟合和首轮 V5-4 ICP A/B 已执行。V5-0/V5-1
产物见 [阶段报告](V5_0_V5_1_REPORT_20260908.md) 和
[mesh 模型](outputs/v5_mesh_shell_model_20260908_01/mesh_shell_model.json)。

此前 v3 进度（2026-09-08）：D02–D12 默认 LingBot 目标经用户全部确认，已生成
11 个输入哈希绑定的独立案例；修正版 v3 完成固定参数批量评估。11 帧全部
正常运行、全部几何拒绝：3 帧当前搜索未找到三面候选，6 帧有竞争解释，
另 2 帧仅高度冲突（竞争解释帧中还有 5 帧同时高度冲突）。
38 项测试通过，参数未变。当前仍不能作为已验证 FDP 替代后端。
详见 [批量评估报告](ROUND2_BATCH_REPORT_20260908.md) 和
[机器摘要](ROUND2_BATCH_SUMMARY_20260908.json)。

批量入口 `run_multiplane_batch.py` 直接读取确认案例，**不要求 FDP 参照**；
旧 `run_offline.py` 继续用于已有 FDP 参照的单帧三分支对照。
本页以下的第一轮与 D01 数字是历史记录，最新批量结论以 v4 报告为准。
`--backend v3|finite_height|joint|surface` 选择评估分支；默认 `v3` 保持历史
复现。最新严格复核应显式使用 `--backend surface`，中间几何通过不能绕过它。

第一轮：2026-09-07，**单个冻结案例，纯本地离线**。

已实现 RGB 边缘提取、RGB-D 箱沿候选平面、固定尺寸矩形重建、4317 语义位姿
构造及拒绝门禁。真实案例输出 **`ok=false / ambiguous_rim_planes`**：矩形
候选可重建，但多个高度/法向不同的平面仍支持四边拟合，尚不能确定真正箱沿。
这不是 FDP 替换成功或抓取精度验证。程序正常完成诊断，拒绝结果退出码为 2。

第一轮结论见 [ROUND1_REPORT.md](ROUND1_REPORT.md)。
完整数值和诊断图位于 [outputs/round1_03/REPORT.md](outputs/round1_03/REPORT.md)。
原始 SAM index 1 与最终 ROI mask 的严格单变量对照见
[MASK_ABLATION_REPORT.md](MASK_ABLATION_REPORT.md)。

第二轮已新增“多平面侧壁分解与几何中心估计”分支。它在 D01 的同一确认案例
中显式分解出 7 个竖直平面，并找到由三个面支持、包含一组相对面的固定尺寸
解释。候选中心为约 `[1.398724, 0.236702, 0.494088] m`，yaw 约
`89.359°`。三个匹配面的高度约束联合区间相差约 2.50 mm 而为空，因此正式
结果仍为 **`ok=false / multiplane_wall_heights_inconsistent_with_model`**。
这比第一轮明确缩小了问题：XY/yaw 已有无 FDP 的三面解释，剩余关键问题是
平面表面归属和 Z 一致性，而不是放宽门限。详见
[ROUND2_REPORT.md](ROUND2_REPORT.md) 与
[outputs/round2_02/REPORT.md](outputs/round2_02/REPORT.md)。

## 边界

- 算法运行仅访问本机文件；没有 SDK、ROS、外部推理服务或 ICP。D01～D12
  原始采集曾按用户明确授权通过只读 SSH 复制，复制过程未运行任何机器人程序。
- 不修改 FDP baseline、third_party 或生产抓取规则，不生成 TCP/轨迹。
- 历史单帧使用 `right_wrist_20260907_01_lingbot_operator1`，SAM index 1；
  9 月 8 日批次使用 D02–D12 各自的确认案例。人工确认和输入哈希由 baseline
  的 `load_case()` 验证，批入口额外绑定逻辑编号、capture 和确认索引。
- 输出目录必须为本实验 `outputs/` 下的新子目录；存在即拒绝覆盖。
- 运行前后核验输入与参照哈希，源代码和配置随每次输出保存副本。
- 入口安装禁止连接/DNS/发送数据的 Python audit guard；代码没有网络调用入口。

## 复现

已验证本机 Python 3.10.12、NumPy 1.21.5、OpenCV 4.5.4、SciPy 1.8.0，
诊断使用 Matplotlib。无需安装新依赖。不是 Orin 环境验证。

从仓库运行（`replay_01` 必须尚不存在）：

```bash
cd /home/lsy03/文档/ChatGPT/S1
OPENBLAS_NUM_THREADS=1 python3 -B \
  experiments/20260907_bin_rim_pose/run_offline.py \
  --case-dir experiments/20260903_fdp_baseline/cases/right_wrist_20260907_01_lingbot_operator1 \
  --fdp-result-dir experiments/20260903_fdp_baseline/outputs/fdp_20260907_01_lingbot_operator1 \
  --config experiments/20260907_bin_rim_pose/config/default.json \
  --output-dir experiments/20260907_bin_rim_pose/outputs/replay_01
```

退出码：0 = 至少一个分支的几何门禁通过，精度仍未验证；2 = 三分支均拒绝且诊断完成；
1 = 输入/运行错误。当前冻结案例预期退出码为 **2**，并输出
`completed=true, geometry_accepted=false, rejection_reasons=["ambiguous_rim_planes"]`。
重跑时更换输出目录名，不删除已有结果。

测试命令（50 项；冻结数据不存在时对应数据测试会跳过）：

```bash
cd /home/lsy03/文档/ChatGPT/S1
OPENBLAS_NUM_THREADS=1 python3 -B -m unittest discover \
  -s experiments/20260907_bin_rim_pose/tests -v
```

本轮执行记录：[tests/VALIDATION_20260907.txt](tests/VALIDATION_20260907.txt)。
最新批次验证：[tests/VALIDATION_BATCH_20260908.txt](tests/VALIDATION_BATCH_20260908.txt)。
v4 验证：[tests/VALIDATION_V4_20260908.txt](tests/VALIDATION_V4_20260908.txt)。
V5-3 验证：[tests/VALIDATION_V5_3_20260908.txt](tests/VALIDATION_V5_3_20260908.txt)。

## 实现与接口

- `bin_rim_pose/geometry.py`：投影/反投影、平面候选、矩形拟合和语义轴构造。
- `bin_rim_pose/box_center.py`：按用户追加要求，使用局部法向选择竖直箱壁，直接拟合几何中心；同样拒绝不足观测。
- `bin_rim_pose/multiplane_center.py`：第二轮显式分解竖直侧壁平面，以三面、
  相对面和有限面范围门禁联合估计已知尺寸箱体中心。
- `bin_rim_pose/diagnostics.py`：RGB 全图/局部图、点云全景/局部图和 PLY。
- `run_offline.py`：冻结输入加载、保存 FDP 请求核对、纯几何对照、报告与溯源。
- `run_multiplane_batch.py`：无 FDP 参照的本地确认案例批量估计、失败输出、
  逐帧诊断、参数/源码快照和哈希核验；批退出 0 表示运行完成，不等于几何通过。
- `compare_mask_ablation.py`：确认源码、配置及冻结哈希一致后比较两次 mask 运行。
- `render_mask_ablation.py`：显示原 SAM、ROI 新增像素与两次矩形候选。
- `config/default.json`：全部算法阈值。当前为探索参数，不是夹爪精度验收门限。
- `tests/`：合成几何、坐标合同、无效观测及当前帧集成测试。
- `scratch/`：初步检查与已废弃原型证据，不能作为最终入口。
- `bin_rim_pose/multiplane_refined.py`：有限面高度、联合初值和表面角色复核的
  v4 三阶段分支，保留原 v3 实现作为对照。
- `audit_wall_profile.py`：对冻结 OBJ 做中央射线截面审计。
- `compare_refinement_stages.py`：核验相同输入并生成四阶段对比和图表。

清晰复用 baseline 的纯文件接口 `fdp_baseline.case.load_case`、
`io_utils.sha256_file/write_json_new/load_json`、
`geometry.transform_quality/pose_delta/normalize_fdp_pose`。
不导入 baseline 的网络 client、SAM3/LingBot 调用器或实时采集模块。

估计器 `estimate(rgb, depth, mask, K, T, config)` 不接收 ROI/FDP 中心或姿态。
同一最终 mask 只作为空间选择范围，不把其几何生成边界作为观测边缘。
实际使用 RGB Canny 边缘与冻结深度；分割错误和 mask 截断仍会影响结果。

## 算法与拒绝门禁

1. 以原始倒置图像方向和原 K 反投影光学 Z 深度，并用捕获 TF 转到 base_link。
2. 在 mask 有效深度中取 Z 的 80%～99.7% 分位范围，提取 RGB 边缘点。
   这是近直立箱体的上部候选先验，不证明其中每一点都是箱沿。
3. 4 mm 体素降采样；固定种子 RANSAC 找到倾斜不超过 12° 的平面候选。
   非共线空间支持、最少点数及 TLS 残差用于排除退化平面。
4. 取候选平面 ±8 mm 内的 RGB 边缘，投影到平面坐标，用多初值、鲁棒损失
   拟合 0.40×0.30 m 的有限矩形边段。没有 ICP 或点云到 mesh 配准。
5. 四边分别统计 12 个区间的覆盖率；每边至少 10 点、至少 50% 覆盖，
   总内点比例至少 70%、内点 RMSE 不超过 8 mm。缺边保留先验候选，但拒绝。
6. 检查周界附近是否存在明显高于候选平面的观测、是否存在位置/yaw 不同的
   近评分矩形，以及其他具有足够支持且四边检查通过的不同平面。
   **平面点数/矩形评分更高本身不能消除真实箱沿身份歧义。**
7. 正常和拒绝路径都生成诊断；只有没有拒绝原因时才发布有效矩阵。

当前使用有限 RANSAC 与局部多初值搜索，不能保证发现全部歧义；仍需改进
箱沿顶缘、内外缘和筋条的语义区分，不能据门禁通过推断可抓取。

## 坐标与观测边界

语义 +X/+Y/+Z = 长/宽/高，米制，右手系，原点为箱体几何中心。
由上沿中心和法向计算 `c_box = c_top - 0.175/2 * normal`。
法向朝 base +Z；长轴水平投影的 base Y 非负，否则绕语义 Z 翻转 180°。
B 已直接生成语义轴，不再次套用 FDP mesh 轴转换。

- 深度与 RGB 边缘：冻结的观测数据；本轮深度已经由 LingBot 补全，并非全部原始传感器测量。
- 平面和边位置：观测拟合量；仍是假设属于真正外沿的边缘。
- 长宽高与半高偏移：4317 尺寸先验。
- 四角：拟合直线的交点，不是四个独立直接测得的角点。
- 正反方向：已有 180° 约定，不表示真实正反面已识别。

正式 `pose_backend_result.json` 在拒绝时保留 `ok=false`，
`matrices.T_base_link_from_4317_semantic=null`，避免被当作可用结果。
完整候选矩阵只保存在 `geometry_result.json` 的 `candidate` 中。
这明确扩充了 baseline 的失败表达；有效路径使用同一个 4×4 位姿字段。
不伪装成生产链要求的 `source=fdp/foundationpose_real=true`。

## 产物与数据管理

每次输出包含 `geometry_result.json`、`pose_backend_result.json`、
`coordinate_checks.json`、`comparison.json`、`input_manifest.json`、
`run_manifest.json`、`source_snapshot/`、`REPORT.md`、RGB/点云 PNG、
`target_cloud.ply`、`diagnostic_points.npz` 和 `ASSET_MANIFEST.json`。

`pointcloud_overview.png` 保留背景离群点；`pointcloud_diagnostic.png` 放大箱体
附近并明确注明裁剪。PLY 保存有效 mask 点云的确定性抽样，完整数据仍在原案例。

原始冻结数据与大体积输出不随 Git 提交。索引和哈希保存在
[ROUND1_ASSET_INDEX.json](ROUND1_ASSET_INDEX.json)，机器可读摘要为
[ROUND1_SUMMARY.json](ROUND1_SUMMARY.json)。原案例缺失或哈希不匹配时不能复现。

## 同帧箱体几何中心分支

用户允许不限定箱口方法后，增加 `box_center.py`，始终使用同一冻结深度和
mask。以 5×5 邻域跨度计算法向，选择近竖直且邻域连续的壁面点，再拟合
已知长宽矩形；Z 中心由壁面高度范围与 175 mm 高度先验约束。

此分支不使用箱沿平面；roll/pitch 固定直立，是先验。其推算顶面/四角不是
直接观测箱口。观测高度范围过短时中心 Z 欠约束，过长时与直立箱体模型冲突；
给出的中心可行区间是先验约束区间，不是统计置信区间。

当前分支同样拒绝：一条短边缺乏支持、整体矩形内点比例不足、壁面高度范围
与直立模型不一致。原 B 与箱壁分支的结果独立保存；不会把 B 的 XY 与另一
分支的 Z 任意拼接成所谓更高精度结果。

额外输出：`box_center_result.json`、`box_center_pose_backend_result.json`、
`box_center_comparison.json`、`box_center_coordinate_checks.json` 和
`box_center_diagnostic.png`。当前 `run_offline.py` 一次运行箱沿、整体箱壁、
多平面三分支，均无服务调用；批量入口单独评估多平面分支。

## 原始 SAM 与最终 ROI mask 对照

`run_offline.py --mask-source sam_selected|final_roi` 允许只改变分析 mask。
2026-09-07 同帧对照确认：最终 ROI 在原 SAM index 1 外增加了 1,436 像素，
没有删除像素；新增区来自生产哈希一致的 ROI `_augment_mask()` 将尺寸模板
四角投影后填充。它使箱沿第四条边覆盖率从 41.7% 增到 58.3%，但两个输入
仍都因 `ambiguous_rim_planes` 拒绝。箱沿候选中心相差 0.744 mm、yaw 相差
0.366°；箱壁候选中心相差 1.540 mm、yaw 相差 0.166°。这表明扩张会改变
门禁，但不是当前核心歧义的主要来源。完整证据见 mask 消融报告。