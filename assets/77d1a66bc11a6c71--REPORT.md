# D01–D12 四组消融与 FDP 对比

## 范围与结论边界

12 个已确认右腕冻结 LingBot 输入 × 4 配置，每配置每帧一次，共 48 次。
运行设备：本机 x86_64；S1 SSH 超时/No route to host，Orin 批次未启动。本机时间不能当作 Orin 计时。
FDP 使用既有 D01 和 9/8 D02–D12 归档；逐帧请求 RGB/mask/K/mesh、毫米深度编码和坐标归一化已复核，不是本次新推理。
V5 使用 float32 米制深度，FDP 传输 uint16 毫米截断，最大差不足 1 mm。FDP 不是独立真值。

## 汇总

|配置|接受/12|算法中位数 s|中心差 FDP 均值 mm（全候选）|中心差 FDP 中位数 mm|yaw差 FDP 中位数 °|拒绝→接受|接受→拒绝|
|---|---:|---:|---:|---:|---:|---|---|
|BCM|10|4.726|10.768|10.100|1.189|无|无|
|CM|8|3.469|12.762|10.401|1.220|无|D02,D08|
|BM|9|3.503|10.774|10.100|1.135|无|D05|
|M|5|2.327|17.680|12.803|37.090|无|D01,D02,D05,D08,D09|

全候选统计保留拒绝诊断候选，避免只统计接受结果造成筛选偏差；仅接受子集另见 comparison.json，分母不同不直接排名。

## 逐帧中心差 FDP（mm）与接受状态

A=accepted，R=rejected（诊断候选，正式位姿不发布）。

|帧|BCM|CM|BM|M|
|---|---:|---:|---:|---:|
|D01|14.365 A|14.365 A|14.218 A|13.700 R|
|D02|12.349 A|11.985 R|12.349 A|22.175 R|
|D03|10.120 R|10.521 R|10.120 R|19.015 R|
|D04|11.237 A|11.237 A|11.905 A|11.905 A|
|D05|9.605 A|9.605 A|9.228 R|9.228 R|
|D06|10.282 A|10.282 A|10.282 A|10.282 A|
|D07|8.079 A|8.108 A|8.108 A|8.108 A|
|D08|8.647 A|32.515 R|8.647 A|32.515 R|
|D09|8.876 A|8.876 A|8.749 A|35.782 R|
|D10|7.651 A|7.651 A|7.651 A|7.651 A|
|D11|10.079 A|10.079 A|10.079 A|10.079 A|
|D12|17.925 R|17.925 R|17.947 R|31.725 R|

## yaw 对称差 FDP（度）

|帧|BCM|CM|BM|M|
|---|---:|---:|---:|---:|
|D01|1.175|1.175|1.318|75.312|
|D02|0.475|0.419|0.475|78.250|
|D03|0.314|0.095|0.314|75.363|
|D04|1.203|1.203|1.034|1.034|
|D05|1.372|1.372|1.393|1.393|
|D06|0.820|0.820|0.820|0.820|
|D07|1.567|1.526|1.526|1.526|
|D08|0.124|72.791|0.124|72.791|
|D09|0.848|0.848|0.911|74.204|
|D10|1.388|1.388|1.388|1.388|
|D11|1.236|1.236|1.236|1.236|
|D12|2.151|2.151|2.128|72.654|

## 箱口中心差 FDP（mm）

|帧|BCM|CM|BM|M|
|---|---:|---:|---:|---:|
|D01|16.439|16.439|16.296|16.566|
|D02|12.716|12.284|12.716|20.718|
|D03|10.334|10.686|10.334|20.808|
|D04|11.995|11.995|12.480|12.480|
|D05|9.843|9.843|9.435|9.435|
|D06|11.437|11.437|11.437|11.437|
|D07|9.054|9.040|9.040|9.040|
|D08|11.946|34.263|11.946|34.263|
|D09|11.248|11.248|11.124|37.796|
|D10|7.798|7.798|7.798|7.798|
|D11|10.374|10.374|10.374|10.374|
|D12|23.670|23.670|23.694|36.582|

## 数据名称与 FDP 历史计时

FDP 为历史客户端请求耗时，含网络/服务边界，与本机 V5 算法时间不构成同环境速度对照。

|帧|冻结 case 名称|SAM index|历史 FDP s|
|---|---|---:|---:|
|D01|right_wrist_20260907_01_lingbot_operator1|1|1.145|
|D02|right_wrist_D02_20260907_165547_084851541_lingbot_operator_confirmed|3|1.440|
|D03|right_wrist_D03_20260907_170359_732494930_lingbot_operator_confirmed|6|1.359|
|D04|right_wrist_D04_20260907_182659_071599799_lingbot_operator_confirmed|0|1.263|
|D05|right_wrist_D05_20260907_183211_489378596_lingbot_operator_confirmed|1|1.226|
|D06|right_wrist_D06_20260907_183534_988072685_lingbot_operator_confirmed|10|1.236|
|D07|right_wrist_D07_20260907_183622_577749279_lingbot_operator_confirmed|5|1.231|
|D08|right_wrist_D08_20260907_190617_386973688_lingbot_operator_confirmed|1|1.189|
|D09|right_wrist_D09_20260907_190653_193583878_lingbot_operator_confirmed|0|1.123|
|D10|right_wrist_D10_20260907_190736_821693545_lingbot_operator_confirmed|0|1.173|
|D11|right_wrist_D11_20260907_190826_818308342_lingbot_operator_confirmed|6|1.189|
|D12|right_wrist_D12_20260907_190946_145566561_lingbot_operator_confirmed|3|1.200|

## 消融相对完整基线的变化

|帧/配置|中心差 mm|yaw差 °|箱口差 mm|短边最大差 mm|状态变化|最佳来源|
|---|---:|---:|---:|---:|---|---|
|D01/BM|0.1511|0.1432|0.1511|0.6020|不变|B_rim|
|D01/M|13.8967|76.4868|13.8967|254.8193|A→R|mesh_coarse_projection|
|D02/CM|0.6047|0.0564|0.6047|0.6755|A→R|C_multiplane_rival|
|D02/M|12.4610|78.7254|12.4610|265.5899|A→R|mesh_coarse_projection|
|D03/CM|0.4739|0.2188|0.4739|1.0575|不变|C_multiplane_joint|
|D03/M|16.4884|75.0485|16.4884|257.1598|不变|mesh_coarse_projection|
|D04/BM|0.8694|0.1689|0.8694|1.1602|不变|mesh_coarse_projection|
|D04/M|0.8694|0.1689|0.8694|1.1602|不变|mesh_coarse_projection|
|D05/BM|1.3000|0.0208|1.3000|1.3031|A→R|mesh_coarse_projection|
|D05/M|1.3000|0.0208|1.3000|1.3031|A→R|mesh_coarse_projection|
|D07/CM|0.1564|0.0405|0.1564|0.2655|不变|mesh_coarse_projection|
|D07/BM|0.1564|0.0405|0.1564|0.2655|不变|mesh_coarse_projection|
|D07/M|0.1564|0.0405|0.1564|0.2655|不变|mesh_coarse_projection|
|D08/CM|26.3592|72.9155|26.3592|256.7593|A→R|mesh_coarse_projection|
|D08/M|26.3592|72.9155|26.3592|256.7593|A→R|mesh_coarse_projection|
|D09/BM|0.1590|0.0637|0.1590|0.3160|不变|B_rim|
|D09/M|27.8743|75.0518|27.8743|268.5063|A→R|mesh_coarse_projection|
|D12/BM|0.1042|0.0229|0.1042|0.1394|不变|B_rim|
|D12/M|17.5140|70.5028|17.5140|246.3690|不变|mesh_coarse_projection|

## 全部逐帧时间（秒）

|帧|BCM|CM|BM|M|
|---|---:|---:|---:|---:|
|D01|4.169|2.377|3.470|1.985|
|D02|4.432|2.296|3.536|1.619|
|D03|4.772|2.791|3.851|2.325|
|D04|4.459|3.982|3.119|2.737|
|D05|4.980|3.301|3.260|1.724|
|D06|4.580|4.142|2.856|2.476|
|D07|4.639|3.483|2.965|1.732|
|D08|4.680|3.455|3.376|2.125|
|D09|5.450|3.885|4.226|2.700|
|D10|5.905|4.160|4.760|2.869|
|D11|5.638|3.946|3.966|2.385|
|D12|5.433|3.428|4.514|2.330|

## 拒绝与竞争诊断

|帧/组|拒绝原因|最佳来源|初值数/拟合数|合格竞争解数|
|---|---|---|---:|---:|
|D01/M|visible_shell_residual_or_coverage_too_low,ambiguous_inner_outer_surface_hypotheses|mesh_coarse_projection|12/14|0|
|D02/CM|ambiguous_inner_outer_surface_hypotheses|C_multiplane_rival|12/14|0|
|D02/M|visible_shell_residual_or_coverage_too_low,ambiguous_inner_outer_surface_hypotheses|mesh_coarse_projection|12/14|0|
|D03/BCM|ambiguous_inner_outer_surface_hypotheses|B_rim|12/14|0|
|D03/CM|ambiguous_inner_outer_surface_hypotheses|C_multiplane_joint|12/14|0|
|D03/BM|ambiguous_inner_outer_surface_hypotheses|B_rim|12/14|0|
|D03/M|visible_shell_residual_or_coverage_too_low,ambiguous_inner_outer_surface_hypotheses|mesh_coarse_projection|12/14|0|
|D05/BM|ambiguous_inner_outer_surface_hypotheses|mesh_coarse_projection|12/14|0|
|D05/M|ambiguous_inner_outer_surface_hypotheses|mesh_coarse_projection|12/14|0|
|D08/CM|visible_shell_residual_or_coverage_too_low|mesh_coarse_projection|12/14|0|
|D08/M|visible_shell_residual_or_coverage_too_low|mesh_coarse_projection|12/14|0|
|D09/M|visible_shell_residual_or_coverage_too_low|mesh_coarse_projection|12/14|0|
|D12/BCM|visible_shell_residual_or_coverage_too_low,mask_touches_image_border|C_multiplane_joint|12/14|0|
|D12/CM|visible_shell_residual_or_coverage_too_low,mask_touches_image_border|C_multiplane_joint|12/14|0|
|D12/BM|visible_shell_residual_or_coverage_too_low,mask_touches_image_border|B_rim|12/14|0|
|D12/M|visible_shell_residual_or_coverage_too_low,mask_touches_image_border,ambiguous_inner_outer_surface_hypotheses|mesh_coarse_projection|12/14|0|

## 复核与文件

48 次输入 SHA、源码/配置/模型一致性及 B/C 实际调用次数断言通过；FDP 归档哈希未改变。
输入名称、ROI 索引、FDP 请求校验见 ../d01_d12_reference_index.json；完整 48 行见 results.csv 和 comparison.json。
短边同时保存固定标签差和允许两端交换的最小总距离配对差。V5 长度 402.1185 mm，历史 FDP 参考点长度 400 mm；机器结果另附统一尺寸的参考点差，中心/yaw 不受此约定影响。
箱口和短边点均由模型推导，不能作为已验证抓取 TCP。
组顺序按帧轮换，各帧配置共享全部参数；一次运行不支持稳定 P95 或跨设备加速比。
原代码中 evidence 字段仍为通用 B/C/mesh 文案，实际来源以 sidecar group、调用数和 fit.sources 为准。

![对比图](comparison.png)

## 实验结论

- B 不能直接视为冗余：去掉 B 后 D08 yaw 相对完整基线变化 72.92°，中心变化
  26.36 mm；D02 虽中心仅变化 0.60 mm，也触发内外表面歧义拒绝。
- C 的位姿回归变化较小（12 帧中心最大 1.30 mm），但 D05 会由接受转拒绝。
  D05 外/内表面 p90 比由约 1.135 变为约 1.086，跨过固定歧义比例 1.10；
  这是竞争解释判定变化，不能仅因 FDP 中心差相近就认为功能一致。
- 仅 M 的 D01/D02/D03/D08/D09/D12 yaw 与 FDP 相差约 72.65°–78.25°，
  相对完整基线的短边参考点变化最高约 268.51 mm。这些大方向差候选均被拒绝，
  单看中心差会掩盖方向及抓取参考点风险。
- 没有原拒绝转接受（本批原拒绝仅 D03、D12），不构成已排除错误接受的证明。
- 先保留 B/C 正式流程。C 可作为后续有条件跳过研究对象，但须复核 D05 的
  表面竞争和触发策略，不直接调整拒绝阈值；不能据此称精度已验证。
- D02–D12 本轮 BCM 的 candidate、fit、初始化、表面解释、拒绝原因均与历史
  同机 V5-2+V5-3b 逐字段一致。D01 本轮新跑该完整基线，未冒称已有同版回归。

本批 S1 输入上传连接超时、执行连接返回 No route to host，无远端实验成功启动。
Orin 48 次性能复核待连通后补齐；本机计算和历史 FDP 对比已完成。