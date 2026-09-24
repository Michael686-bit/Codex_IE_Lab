# 13帧标定板基准 / FDP / V5系列位姿与耗时实验计划

日期：2026-09-17。状态：**执行中**。前端与FDP批次已完成，S1 Docker批次仍在运行；最终统计尚未生成。
执行者：后续由用户交给 Luna Max；本文件不代表已启动任务或新一轮远端授权。

## 1. 目标与必须回答的问题

在完整13帧标定板采集集上，以最新板安装关系推导的箱体位姿为统一参考，比较：

1. FDP；
2. 原入口 V5-2 + V5-3b（简称 V5-original）；
3. BCM 包装对照；
4. R1；
5. RM；
6. R1F（R1失败后BCM回退）。

保留此前用户指定的 **raw / LingBot 两种深度**。五个V5系列执行组必须在 **S1 同一个不可变 Docker 镜像、相同资源与线程设置**中执行。

报告回答：谁的正式输出相对板参考更近；是否以增加拒绝/误接受换取速度；R1F是否补回R1拒绝且回退后与BCM一致；raw与LingBot对位置/方向/状态/时间有何影响；初始化时间和拟合时间分别占多少；实际最慢回退需多久。

这批数据已被用于检测器和安装关系调试，不称为未见留出集。板参考仍有安装水平位置与模型适配不确定性，指标命名为“相对板参考偏差”，不称为绝对准确率或抓取精度。

## 2. 来源和本轮约定

已读取任务 **“9_16 制定V5-R与V5-3b实验计划”**，任务ID `01a0a8fb-d550-7961-9d1a-f39a2db16a5b`。
该任务先制定方案，随后已在D01–D12执行BCM/M/R1/R9/RM和R1F。那些D帧不是本轮13帧。

源码/证据入口：

- [前轮计划](s1_v5_r_roi_initialization_plan_20260916.md)
- [V5-R实现说明](../experiments/20260916_v5_r_roi_init/README.md)
- [包装入口](../experiments/20260916_v5_r_roi_init/entry_v5_r.py)
- [ROI转换](../experiments/20260916_v5_r_roi_init/roi_initializer.py)
- [旧远端runner](../experiments/20260916_v5_r_roi_init/run_remote.py)
- [前轮完整结果](../experiments/20260916_v5_r_roi_init/remote_full_20260916T071438Z/REPORT.md)
- [前轮fallback结果](../experiments/20260916_v5_r_roi_init/remote_fallback_20260916T072715Z/REPORT.md)
- [当前数据集定义](../experiments/20260915_charuco_comparison/DATASET_DEFINITION_20260917.md)

无须用户再选择软件细节，默认：两深度、每个有效输入/算法先1次预热再5次正式重复、串行运行、按轮次轮换算法顺序；保留原mesh与质量门禁。M、R9、RC4不在本轮必跑范围。

**BCM不是另一种全新后端。** 原V5-2+V5-3b已有B/C/M初值融合；BCM包装入口保留这些分支，只增加调用/耗时审计。仍按用户要求分别跑V5-original与BCM，先验证等价并量化包装开销；不要在“不同算法数”统计里把它们当两种独立思想。

## 3. 唯一的数据集清单

统一标识使用 `C01…C13`，仅为本轮索引，不借用旧D/H编号。必须始终保存完整capture ID。

|本轮ID|完整capture目录名|真实相机|现有V3板参考|
|---|---|---|---|
|C01|L01_wrist_charuco_20260915_093818_877801116|left|缺失，4角点|
|C02|L02_wrist_charuco_20260915_100236_358935353|left|47角点|
|C03|L03_00_wrist_charuco_20260915_104002_497962253|left|65角点|
|C04|L03_10_wrist_charuco_20260915_103928_398335507|left|55角点|
|C05|L04_00_wrist_charuco_20260915_104435_858773771|left|78角点|
|C06|L04_10_wrist_charuco_20260915_104717_786588568|left|77角点|
|C07|L04_wrist_charuco_20260915_104358_532673829|left|71角点|
|C08|R01_wrist_charuco_20260915_093900_967150252|left，目录误标|缺失，3角点|
|C09|R01_wrist_charuco_20260915_094033_680788016|right|9角点|
|C10|R02_wrist_charuco_20260915_100308_809523978|right|77角点|
|C11|R03_wrist_charuco_20260915_103743_184821162|right|100角点|
|C12|R04_00_wrist_charuco_20260915_104526_910331328|right|100角点|
|C13|R04_10_wrist_charuco_20260915_105839_488564574|right|100角点|

原始16组中排除 L02_10、R03_10lift、L03（103720）；不得重新纳入。
成员以 [exclusions.json](../experiments/20260915_charuco_comparison/exclusions.json) 与上表核对，不能用目录排序、前缀或同名R01作为唯一身份。

位置：

- 本机相机归档：`experiments/20260915_charuco_comparison/capture_archive/<capture>/`。
- S1原始目录：`/home/galbot/Lsy03/fdp_baseline/captures/<capture>/`。
- 本机归档主要有RGB、K、TF、meta/result；**不能假定已含所有raw深度**。执行前逐帧从S1只读取回 `depth_raw_m.npy`，按原 `capture_result.json.files_sha256` 校验完整冻结包。
- V3检测快照：[detector_v3/results.json](../experiments/20260915_charuco_comparison/detector_v3/results.json)。
- 现有同帧后端结果仅C11/R03 raw与LingBot；保留作历史复核，不代替此次S1统一计时。

完整13帧意味着：所有帧均进入输入核验、目标准备、算法尝试和状态/时间表。C01/C08可以测后端，板参考缺失时对板偏差为 `null/N/A`；**绝不从其他帧、FDP或V5补板真值**。采集失败/前端失败也占总表一行。

## 4. 冻结标定板参考

### 已确认参数及证据边界

- 9×14方格（几何排列等价于14×9方向），square=20 mm，marker=15 mm。
- 现有检测使用OpenCV4.5.4的14×9默认ID布局、DICT_5X5_1000作为字典超集；原始字典容量未唯一确定，不能假装已取得厂家生成配置。
- 板厚2 mm，红/蓝贴合边白边各10 mm，红长边贴箱前侧长边、蓝短边贴左侧短边，A角零间隙；板下表面接触内底面上表面。外形300×200 mm沿现有图示假设，未另外量取四边白边。
- 实物外高172 mm，内底面至最高点160 mm；最低点基准下内底面12、印刷面14、外包围盒中心86 mm；中心高于印刷面72 mm。
- 板参考用采集对应K/D、TF；当前meta中可读取D，不允许根据照片自行猜D=0。

采用现页面 [构建脚本](../experiments/20260915_charuco_comparison/measured_mount_20260916/build_mesh_comparison.py) 中的 `new` 安装矩阵，不取页面的显示坐标：

```text
T_board_from_box =
[[1, 0, 0, 0.1714464],
 [0, 1, 0, 0.059430301],
 [0, 0, 1, 0.072],
 [0, 0, 0, 1]]

T_camera_from_box = T_camera_from_board × T_board_from_box
T_base_from_box   = T_base_from_camera × T_camera_from_box
```

单位米。XY及轴方向仍是旧名义安装关系，**只Z有本轮实测支持**。
页面的 `X=boardX+10mm,Y=190mm-boardY,Z=boardZ+14mm` 是显示映射，含反射，不可作为机器人刚体位姿。

冻结 `board_reference.json`：13行，每行存板检测状态、角点、覆盖率、RMSE、K/D来源、TF、相机/基座两套箱体矩阵、安装版本、输入与检测器哈希。检查旋转det≈+1、正深度、单位、侧别、投影角点ID/边界与实际板吻合。
低RMSE不能替代布局/轴向/平面双解/覆盖率验证；C09仅9角点要标注低覆盖敏感性。全体参考冻结在看后端结果之前。

主表先用已保存V3结果；执行时若复现失败或发现参考几何矛盾则降级状态并说明。进一步恢复C01/C08只作为独立参考修订，记录前后版本并对全方法统一重算；不能因为某算法误差大就调整安装矩阵。

### 不改175 mm算法mesh

当前算法mesh SHA-256：
`adb0d1cf4ee3cc885641ce5e473efb31de4d80323e7665ec50fa5aaabbcc991b`。
其外高175 mm、内深约172.5 mm，与实物172/160 mm不同。本轮固定它以评估现有算法，不缩放、不换172 mm模型、不改变算法配置高度。
报告明确“算法模型中心估计 vs 172 mm实物参考中心”，它包含模型适配偏差；不能盲减1.5 mm或11 mm修饰输出。
除中心误差外增加独立箱口中心偏差：板参考沿箱体高度轴加86 mm；算法沿各自高度轴加其模型高度一半（87.5 mm）。这用于辨别中心定义/高度先验影响，不能替换主指标。

## 5. 算法组与fallback规则

|执行组|入口/初值|要求|
|---|---|---|
|Board-reference|同帧ChArUco + 上述安装矩阵|独立参考，禁止进入拟合初值|
|FDP|现有 `/first_frame_track` 服务|同RGB/depth/mask/K/mesh合同，随后归一化|
|V5-original|镜像原 `/opt/box-pose/app/compute_observation.py`|原 B+C+M，不装R包装|
|BCM|`entry_v5_r.py --group BCM`|原 B+C+M + 审计包装，等价控制|
|R1|`--group R1`|单一ROI初值 q0 + 原V5-3b|
|RM|`--group RM`|q0优先 + 原M粗初值，原去重/最多12候选|
|R1F|`--group R1F`|R1原生质量拒绝后再运行BCM，计入两段完整时间|

源码确认 R1F 在 `fast_result.ok` 为假时回退；目前并不捕获任意异常。保持这个定义：输入损坏、sidecar缺失、异常、OOM、超时是error/blocked，不伪装成正常回退。
R1F必须保留R1失败候选与拒绝原因、回退前后审计计数、最终来源；当前包装只保留部分fast结果，允许增加旁路日志但不改选择/质量门禁，开销单列。

R初值从同目标、同深度分支ROI生成：`q0=[ROI.x, ROI.y, ROI.z−h_model/2, radians(ROI.yaw_deg)]`；确认ROI.center_world是base_link箱口中心，h_model从镜像模型读（175 mm）。不要把板参考172 mm引入q0高度。
每个bundle对应独立sidecar，须在执行前验证其所有源/输入哈希；不能仅凭sidecar里面声明哈希就当验证通过。

## 6. 统一Docker环境与运行边界

历史确认镜像：`s1-box-pose-compute:v5_2_v5_3b_20260911_03`。
**不可变Image ID**：`sha256:651bcf7087b9ba1ee2702a4b58ef488936c45251e2a661db8b41d547042bae89`。
证据：[image.json](../experiments/20260916_v5_r_roi_init/remote_full_20260916T071438Z/image.json)、[前轮command.json](../experiments/20260916_v5_r_roi_init/remote_full_20260916T071438Z/00_D01_BCM/command.json)。执行前在S1重新核对，tag一致但ID不同也停止，不自动拉取替换镜像。

- 同一S1 Orin，arm64；`/usr/bin/python3`；同镜像内algorithm/model/config。
- CPU配额6、内存/内存加swap均8g、pids256、tmpfs `/tmp` 512m。
- OPENBLAS_NUM_THREADS、OMP_NUM_THREADS、MKL_NUM_THREADS、NUMEXPR_NUM_THREADS全部1。
- 非root（S1实际UID/GID）、readonly根、cap-drop ALL、no-new-privileges、network none。
- 输入、sidecar、独立实验包装只读挂载；输出写新目录；不挂Docker socket/SDK设备。
- 沿用前轮nvidia runtime及compute/utility设置，但算法仍为CPU路径，不能叫GPU加速。
- **增加 `--no-healthcheck`**：镜像继承了生产健康检查，计时实验不得让其后台调用；五组统一设置并记录与前轮差异。
- 每次用新Python进程/临时容器隔离进程内包装；串行运行。检查温度、CPU频率、loadavg、内存、throttling、OOM；不得为了跑分修改功耗/时钟或停止生产服务。
- 仅清理本轮确切命名的容器，禁止全局prune、重启Docker、切换current或修改third_party。

**现有runner不能直接用于本轮**：`run_remote.py`硬编码D01–D12、GROUPS及180s；`prepare_inputs.py`也绑定D案例。新建本轮包，改为读取13帧manifest和depth/repeat列，保留原文件。需支持V5-original与R1F、按组/轮次独立目录、sidecar对账、退出码0/3与异常区分。不得伪造D01等编号绕过校验。

若Board计时依赖的aruco在该镜像可用，则也在同镜像运行固定V3检测程序；若不兼容，保留本机板参考，在报告明确其主机/版本并不与S1后端计算时间直接排名，不能为板检测更换五组V5镜像。

FDP仍是4090外部服务，不伪称同S1 Docker计算。由S1宿主文件客户端调用已确认服务；客户端运行位置统一并记录。

## 7. 公平输入：raw / LingBot / mask / ROI

先补齐13组完整raw冻结数据。前端客户端只读文件，SAM3 `10.34.216.11:7861`、LingBot `10.34.216.11:7865`、FDP `10.34.216.13:7876`。凭据通过现有安全存储/受控配置读取，不输出或保存到实验包。不得打印含api_key的配置全文。

每帧SAM3一次，LingBot一次，保存响应和耗时；后端重复使用冻结结果，不重复生成mask/深度。首轮C11优先从已保存文件复核，避免重复服务；若旧响应不可验证则新建一次前端版本，记录原因。

目标始终为装板的那一个箱体。已知C11自动默认ROI0是旁边空箱，历史确认目标为ROI6；不能把ROI6跨帧套用。按图像逐帧绑定target identity，生成13帧mask接触表，保存审核证据；不明确的目标停该帧等待现场确认，其他明确帧继续。

**主对比固定mask**：每帧选定LingBot分支该物理目标的ROI mask，冻结为common mask；raw、LingBot下所有后端都用它，且输入哈希一致。若LingBot分支无法形成该目标mask，该帧标为前端阻塞，不能悄悄切成原SAM mask；若需要替代mask单列补充组。

两种深度各自用同一物理目标索引计算ROI q0，q0不得从板/FDP生成。保存ROI原mask与common mask的IoU，说明raw+固定LingBot mask属于控制深度的消融，而非原厂raw完整流水线。
板面保留在主mask中，与旧R03合同一致；不要让某一算法独自去掉板。是否扣除板面可另做显式辅助实验，但不纳入主矩阵或临时调门限。板姿态只供参考/显示，不给拟合后端。

FDP将深度量化为uint16毫米PNG。记录原深度哈希与请求编码哈希，明确与V5浮点米输入的量化区别；主试验沿用生产合同。若评估量化影响单列，不混进raw/LingBot主结果。

`/opt/s1-sjtu/assets/mesh/EU4322_midcut_target175mm.obj` 是FDP服务器内部请求路径，不是S1本机路径；执行前核实服务端模型身份/版本，不能仅核对S1模型就宣称服务端已匹配。身份未能确认可保存响应，但模型可比性标为未核验。

## 8. 参考对齐与偏差指标

主坐标为 `base_link` 下箱体几何中心，另存相机坐标矩阵用于消除对TF解释的混淆。FDP用现有语义转换函数，传入真实左右腕frame。V5-native的候选和正式输出分开。
先审计同一物理轴、长宽轴对应及右手性：shell-model原始轴重排可能含反射，不能直接把该重排矩阵当SE(3)。沿用已核验后端语义合同；发现不一致停坐标比较，不通过转轴“拟合最好误差”。

每帧每算法/深度/重复保存：

- 箱体中心XYZ（mm）、完整4×4矩阵；RPY仅展示，定义 `Rz(yaw)Ry(pitch)Rx(roll)`。
- ΔXYZ = algorithm − board、中心欧氏距离、Δ在板/箱体局部轴的分量。
- SO(3)完整旋转角，以及 `min(I,diag(-1,-1,1))` 两个矩形180°等价姿态的旋转角；不允许90°长短轴交换。
- yaw180对称差、两者高度轴夹角；原RPY因180°对称符号不同不能逐项直接减作唯一指标。
- 箱口中心、对称匹配后的两条短边中点差（使用各自声明的高度/长宽），注明模型尺寸不同。
- 与BCM、FDP的两两差异作为辅助，板参考仍是主列。
- accepted/rejected/error/timeout/oom/input_missing；rejection_reasons；参考valid/unavailable/provisional。

比较旋转前检查正交性，FDP浮点微误差可投影到最近SO(3)仅用于角差计算，保留原矩阵。
不能把V5的roll/pitch=0称为测得的倾角；四自由度直立先验会限制其相对板6DoF参考的完整旋转一致性。

## 9. 计时边界、重复次数和工作量

用monotonic/perf_counter，不用日志时间戳差充当算法计时。

|时间字段|边界|
|---|---|
|t_backend|Observation已加载后，进入backend.estimate直到accepted/rejected结果返回，含所有初值、拟合和原检查|
|t_seed_B/C/M/R、t_fit、t_quality|阶段诊断，注明嵌套，不相加重复计数；计时补丁必须所有组一致或单列开销|
|t_roi|固定RGB/depth/SAM目标生成ROI粗几何；raw/LingBot各一次，单独记录，不靠载入sidecar假装ROI零成本|
|t_container_wall|宿主启动docker至其退出，含启动、import、加载、写结果，不含先验准备和人工等待|
|t_fdp_client|编码/请求HTTP/解码分别计，主值为完整客户端调用；若服务返回内部耗时再另列|
|t_board_detect|RGB已加载至本帧参考位姿，包含V3全部尺度/CLAHE尝试和选择，不只计PnP|
|t_frontend|SAM3、LingBot、ROI、bundle建立分别计；人工选箱等待另列|

R1F总时间必须实际执行一次完整快路径+必要回退，不能取独立R1与BCM表中较优值拼接，也不能只报快路径。记录fast、fallback、total、是否回退、最终来源。共享输入I/O或导入的开销按实际测量，避免重复加。

每个frame×depth×五个V5执行组：1次预热（独立保留）+5次正式重复。共26输入条件×5组×5正式=**650次正式计算**，外加130预热；等价smoke额外运行单列。
FDP对每个可用输入1次预热+5次新请求，最多26×6=156次请求；固定输入，记录服务版本、客户端位置和负载。既有R03两次旧调用不是本轮计时样本。
Board每帧1+5次，只按RGB计，不因raw/LingBot重复乘2；若以保存参考为主，计时复跑输出应核对，不自动替换冻结参考。

前端/模型/服务问题使某单元缺失时登记原因，不能填0或静默减少总数。质量拒绝属于完成一次算法；不自动“重试到接受”。超时按右删失记录，不用成功子集代替总延迟；后端单次容器限180s、FDP单次180s，超时停止该实例后保留证据。
正式顺序采用固定seed的平衡轮换：按frame/depth/repeat轮换组首位，不能先跑完全部BCM再跑R1。每帧每组五次先取中位数，再做跨帧中位数/均值/范围；报告P90和最大值、样本数，13帧不作可靠P99结论。

输出两种速度口径：纯后端差异（突出ROI提前可得的条件）和冻结RGB-D到结果的分阶段成本（计入ROI等所需前端，避免漏算/重复算）。FDP服务GPU时间与Orin CPU时间按平台分栏，不宣称相同硬件公平排名。

## 10. 执行阶段与检查点

### A. 只读预检与输入准备

读取本计划、项目README/知识库/OpenCode历史、S1 SSH skill。确认用户已将此执行计划交给Luna执行后再访问S1。
记录精确13帧清单、depth存在性、数据哈希、SDK坐标/时间信息；冻结本地计划目录到独立S1包，不覆盖历史runs。
核对镜像ID、model/config/算法hash、S1负载及磁盘空间、服务可达性/模型合同。

### B. 冻结板参考与生成前端

冻结13行板参考、安装矩阵与11/2现状。先C11/C13验证左右显示、目标语义、单位。
完成13帧前端raw/LingBot双分支和逐帧目标审核，生成26个独立Observation bundle与26个ROI sidecar（无法生成者有blocked记录）。
核验两深度common mask一致、同深度所有后端输入一致；推理包不挂载板参考/FDP结果。

### C. 必须先跑的等价smoke

选 C11/R03 + C05/L04_00，覆盖左右相机，两深度。
V5-original与BCM在同镜像相同输入下比对accepted、原因集合、候选、seed/fit数量。
中心最大分量差≤1e-8 m、旋转对称角≤1e-5°作为数值等价检查（时间、绝对路径、实验标签忽略）。不通过先查包装/输入合同，禁止直接发全批次。
R1确认不调用B/C/M初值；RM只调用R/M；BCM调用B/C/M；R1F快路径无B/C/M，回退才调用BCM。内外表面两次复核继续保留。
对照原配置中“竞争残差≤best×0.95”的已知疑点，保留原native门禁并单列审计；不要在这一试验改门禁获得接受率。

### D. 批次执行

按预先生成的schedule逐个容器执行650次正式组，记录拒绝和故障；FDP独立顺序请求并保存请求/响应。中途按完成单元落盘checkpoint；恢复时校验哈希后跳过已完整单元，不把半写入当完成。
若发生环境异常/OOM/结构性错误，停止受影响阶段，保存证据；可以继续整理已有离线结果，不擅自换依赖/镜像或删除失败记录。

### E. 统计、可视化、交付

逐帧显示：原RGB + 板参考框 + FDP + 各V5组框（可开关），将诊断候选与正式输出视觉区分。选择单一重复编号展示，不挑最贴合的一次；默认第1次正式输出，其余可切换。
主表全部13行；板失效两帧对板列N/A，后端时间/状态照常列。偏差汇总至少给每方法自身accepted子集、两方法共同accepted子集及分左右腕/深度结果，显式列分母。所有拒绝候选另表，不混进正式精度均值。
先对每帧5次取中位数再跨帧聚合；冻结重复仅是计算/服务重复性，不称为物理采集重复性。

## 11. 验收与交付物

必须完成：

1. 13帧全部可追溯，每frame/depth/group有结果或明确缺失状态；排除名单不变。
2. 五个V5执行组使用相同镜像ID、资源、参数、模型；原入口/BCM等价检查通过。
3. 参考未泄漏到拟合/初值；R组sidecar对应同帧同目标同深度。
4. 各组正式/候选分离，C01/C08无参考时不生成虚假偏差。
5. R1F记录真实失败与回退耗时；回退最终数值/状态应与同输入BCM相符，不符必须解释。
6. 含完整流程时间分解和环境证据，FDP/Board与S1后端时钟口径不混淆。
7. 所有输入/模型前后hash不变，本轮容器清理；原current、服务、机器人状态不改。

性能评价先报告事实，不设未经用户定义的“绝对精度达标”阈值。可保留研究目标“中位数接近1s、相对BCM明显加速”，但一旦有新增拒绝/不确定参考/长尾，须共同报告，不据中位数独自推荐抓取上线。

建议新目录：本机 `experiments/20260917_charuco_13_benchmark/`；S1 `/home/galbot/Lsy03/box_pose_pipeline/runs/charuco13_benchmark_<UTC时间>/`。
要交付：

```text
README.md / REPORT.md / EXECUTION_LOG.md
dataset_manifest.json             # 全13帧完整ID、真实侧别、全部源哈希
experiment_config.json           # 镜像、版本、参数、安装、深度/重复/计时定义
board_reference.json             # 13行状态，11个现有参考
target_review/                   # RGB+mask接触表与逐帧确认来源
bundles/<Cxx>/<raw|lingbot>/      # 冻结Observation，不含板参考/FDP结果
roi_sidecars/<Cxx>/<depth>.json
schedule.json / checkpoint.json
runs/<Cxx>/<depth>/<group>/<warmup|rep01..05>/
fdp/<Cxx>/<depth>/<warmup|rep01..05>/
results_long.json / results_long.csv
paired_deltas.json / timing_summary.json / fallback_audit.json
environment/                     # image inspect、库版本、负载、频率、内存、完整性
visualizations/index.html        # 本机浏览，禁止Sites发布
```

长表字段至少含capture/侧别/目标/深度/组/重复号/参考版本/全部hash、状态、正式矩阵、候选矩阵、中心/方向偏差、时间口径、回退计数、OOM/timeout与原因。报告顶部说明实际执行数量及缺失数量。

## 12. 给 Luna Max 的执行交接

将以下内容作为后续执行请求（本轮尚未执行）：

> 按 docs/s1_charuco_13_algorithms_plan_20260917.md 执行。范围为本轮13帧完整数据集，raw与LingBot双分支，标定板为统一参考；比较FDP、V5-original、BCM、R1、RM、R1F及运行时间。授权读取S1冻结文件、在S1指定不可变Docker中新增独立离线计算容器，以及向已列SAM3/LingBot/FDP服务发送这些冻结输入。先冻结输入/参考和目标，再通过原入口-BCM等价smoke，最后执行5次正式重复。保留两帧无板参考状态、所有拒绝及回退长尾；任何算法不得读取板/FDP作初值。使用skill安全读取凭据，不打印配置秘密。只生成本地和独立远端实验产物，不调用SDK/相机/运动，不改生产服务/current、原mesh/third_party，不发布站点。完成后给出逐帧偏差/时间、共同accepted比较、R1F回退证据和可查看图集。遇到输入损坏、模型合同或镜像不匹配暂停相关阶段，报告确切阻塞。

需要现场人员回答的仅是执行中出现的真实歧义：目标箱不明确、板是否换位/垫高、服务或模型身份无法核验。无需为了现有已明确参数再次索问用户。