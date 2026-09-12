# S1 Orin 可插拔箱体位姿流程

这是统一数据接口、本地回放和实时一次检测入口的实现。它把已有的
`v5_2_v5_3b` 估计器放在一个后端适配器后面；采集、远端 SAM3/LingBot
和未来的其他位姿算法不与该估计器互相导入。

本机开发目录仍未连接机器人或调用网络服务；实时入口只在部署到 S1 后使用。
它已安装为
`/home/galbot/Lsy03/box_pose_pipeline`，而原有
`/home/galbot/Lsy03/fdp_baseline` 作为数据和前处理基线目录。

## 接口

`pose_pipeline.contracts.Observation` 是后端输入。它包含 RGB、米制光学 Z
深度、确认 mask、K、`T_base_link_from_camera`、相机侧别/帧名、来源及哈希；
数组在构造后设为只读。`Observation.manifest()` 是不含图像数组的 JSON 清单。

`pose_pipeline.contracts.BackendResult` 是统一输出。正式接受时中心和矩阵
同时存在，且矩阵平移列与中心相同；拒绝或异常时正式中心/矩阵为空，候选和
原因仍保留在诊断字段。输出还保留已有的
`s1.pose_backend_result.v1` 兼容文件。

`ObservationSource.read_once()` 是采集/回放的边界；当前提供的
`CaseObservationSource` 只读加载冻结案例，未来实时腕部采集实现同一方法。
`ResultSink.save()` 是输出边界，算法不负责文件写入。这样替换实时来源、
远端前处理适配器或位姿后端时，其他层的输入输出不变。

机器可读的采集、感知候选、确认和结果约束分别在
`schemas/capture_frame.schema.json`、`schemas/perception_bundle.schema.json`、
`schemas/target_confirmation.schema.json` 和 `schemas/pose_result.schema.json`；
字段允许增加诊断信息，但核心坐标和状态语义保持稳定。

后端由名称注册：

```python
from pose_pipeline import Observation, create_backend

backend = create_backend(
    "v5_2_v5_3b",
    algorithm_root="/path/to/20260907_bin_rim_pose",
    model_dir="/path/to/mesh_shell_model",
)
result = backend.estimate(observation, model_dir, v5_config)
```

增加算法时实现相同的 `estimate(observation, model, config)`，再注册一个新
名称。命令行可以用 `--backend-module your_package.your_backend` 先导入注册
模块；后端不得访问 SDK、相机、远端服务或控制接口。

## 本地回放

在仓库根目录运行：

```bash
python3 experiments/20260910_orin_pose_pipeline/scripts/replay_pose_backend.py \
  --case-dir experiments/20260903_fdp_baseline/cases/right_wrist_20260907_01_lingbot_operator1 \
  --output-dir experiments/20260910_orin_pose_pipeline/runs/replay_right_01
```

默认要求案例已经有人工确认的目标；仅做诊断时可增加
`--allow-unconfirmed-case`。输出目录必须不存在，包含 observation 清单、
运行/源码/模型/配置哈希、统一结果、兼容结果、原生 V5 结果、耗时和诊断图。
本机 x86 默认生成绘图；Orin 上因 SDK 环境没有 Matplotlib 默认跳过绘图，
需要时可显式加 `--render`。

配置示例见 `configs/v5_2_v5_3b.json`。其中路径是本地开发树的相对示例；
部署到 Orin 时改为部署目录内的版本固定路径，并把 V5 的完整 JSON 参数作为
`backend_config` 指向；`baseline_root` 指向随发布包携带的只读案例加载器。
`camera_arm` 是流程配置项，真实采集时必须与对应
RGB/depth/K/TF 一起切换，不能只替换图像。

也可以直接使用选择器配置运行：

```bash
python3 experiments/20260910_orin_pose_pipeline/scripts/replay_pose_backend.py \
  --pipeline-config experiments/20260910_orin_pose_pipeline/configs/v5_2_v5_3b.json \
  --case-dir experiments/20260903_fdp_baseline/cases/right_wrist_20260907_01_lingbot_operator1 \
  --output-dir /tmp/s1_pose_replay_once
```

## 实时一次检测

`run_pose_once.py` 将实时 getter-only 腕部采集、SAM3、LingBot、ROI 候选和
人工确认串成一次流程，确认后才调用本地后端：

```bash
python3 experiments/20260910_orin_pose_pipeline/scripts/run_pose_once.py \
  --pipeline-config experiments/20260910_orin_pose_pipeline/configs/live_v5_2_v5_3b.json \
  --run-dir /tmp/s1_pose_live_once \
  --acknowledge-readonly-live-s1
```

程序会先打印所有 ROI 候选，必须输入一个 `4317/H4` 的 `roi_index` 和人工
说明；没有自动选择或复用上一次目标。也可以用 `--selected-index` 和
`--operator-statement` 预先提供这两项。API key 只从配置指定的环境变量读取，
结果只记录是否使用，不保存 key。

实时流程需要 Orin 可访问 S1 相机和 `10.34.216.11:7861/7865` 服务；本地
开发机只用 mock/冻结数据测试，未执行实时调用。采集阶段只调用已有
`fdp_baseline.live_capture.capture_wrist_once()` 的 getter/lifecycle 白名单，
并在 `/home/galbot/ie_lab/control.lock` 上使用非阻塞锁；前处理和目标确认
完成后才创建 backend 输入。单独的
`confirm_live_target.py` 可从已经保存的 `perception_manifest.json` 生成带
哈希绑定的确认文件。

## 当前 V5 语义边界

V5-2＋V5-3b 接收的是确认后的 LingBot/ROI 输入，估计 `x/y/z/yaw`，
roll/pitch 采用直立先验。其“通过”表示当前几何门限通过，不表示箱体外壁
身份、绝对精度或抓取可用性已经验证。实际倾斜箱体应另接支持完整旋转的
后端，并在相同 Observation 上进行对照。