# S1 Orin `box_pose_pipeline` 部署与离线回放

日期：2026-09-10。状态：本报告记录 V5-only 初始版本部署和同输入回放；未采集实时图像、未调用
SAM3/LingBot/FDP，未发送机器人运动命令。

## 部署对象

通过用户授权的 S1 SSH 连接检查并部署到 Jetson AGX Orin Developer Kit：

```text
host: galbot-echo
model: Jetson AGX Orin Developer Kit, 64 GB, p3701-0005
OS: Ubuntu 20.04.6 LTS
kernel: 5.10.216-tegra
JetPack/L4T: 5.1.4 / 35.6.0
architecture: aarch64
```

算法使用 `/home/galbot/ie_lab/bin/s1-python`，本次核对版本为 Python 3.8.20、
NumPy 1.24.4、SciPy 1.10.1、OpenCV 4.10.0、Requests 2.32.3。该环境没有
Matplotlib；CLI 在 aarch64 默认跳过绘图，`--render` 只在另行安装绘图库后使用。

系统 Python 3.8.10 也有 NumPy 1.17.4、SciPy 1.3.3 和 OpenCV 4.5.4，未用于
本次算法回放。目标盘约 1.4 TB 可用。

发布包本地 SHA-256 为：

```text
ab75ad84c86d31e73f6cc138a8feb5c2f43afaafd3db376692d69be188fbe8be
```

远端目录结构为：

```text
/home/galbot/Lsy03/box_pose_pipeline/
├── current -> releases/v5_2_v5_3b_20260910_01
├── releases/v5_2_v5_3b_20260910_01/
│   ├── app/                 # 统一接口、后端注册、回放 CLI、schema、配置
│   ├── versions/            # V5 源码、baseline loader、配置和 shell model
│   └── replay_cases/        # 一份人工确认的右腕冻结案例
└── runs/                    # Orin 回放结果
```

版本目录约 6.4 MB，包含 38 个文件；未覆盖旧目录
`/home/galbot/Lsy03/fdp_baseline`。部署前后该目录的
`DEPLOYMENT_MANIFEST.sha256` 均为
`c071b042906c5639796e47020634d95472422020a519423f3848784cf632ba58`。

## Orin 回放

使用随包案例和 `v5_2_v5_3b` 配置，在 Orin 上执行：

```bash
OPENBLAS_NUM_THREADS=1 /home/galbot/ie_lab/bin/s1-python \
  /home/galbot/Lsy03/box_pose_pipeline/current/app/scripts/replay_pose_backend.py \
  --pipeline-config /home/galbot/Lsy03/box_pose_pipeline/current/app/configs/v5_2_v5_3b.json \
  --case-dir /home/galbot/Lsy03/box_pose_pipeline/current/replay_cases/right_wrist_20260907_01_lingbot_operator1 \
  --output-dir /home/galbot/Lsy03/box_pose_pipeline/runs/replay_v5_2_v5_3b_20260910_01 \
  --no-render
```

结果为 `status=accepted`，中心：

```text
[1.3863633760476675, 0.2493339463832932, 0.4943560250186494] m
```

与本地同一案例回放比较：状态、后端、自由度和拒绝原因相同；中心欧氏差
`2.39e-12 m`，中心各轴最大绝对差 `2.26e-12 m`，4×4 矩阵最大元素差
`2.26e-12`。本地 x86 算法耗时约 `4.12 s`，Orin `s1-python` 算法耗时约
`16.91 s`；这只是一次冻结案例计时，不是性能承诺。

Orin 运行产物包括 `pose_result.json`、兼容的
`pose_backend_result.json`、`backend_native_result.json`、输入快照、运行清单
和 `timing.json`。运行清单确认：`motion_commands_sent=false`、
`network_services_called=false`、`robot_accessed=false`。结果的
`accuracy_validated=false` 和 `grasp_ready=false` 保持不变。

## 回退与当前边界

`current` 是版本指针；后续发布新版本时新增 `releases/<version>`，通过更新
指针切换，旧版本保留。此次没有执行切换或删除操作。

当前发布包完成的是离线回放闭环。它还没有在 Orin 上接入实时腕部采集、目标
候选人工确认界面或远端服务调用；这些属于下一阶段。默认配置中的 `camera_arm`
为 left，随包回放案例实际是 right，回放以案例中的 RGB/depth/K/TF 帧名为准。
V5 仍只估计 `x/y/z/yaw`，roll/pitch 使用直立先验，实际倾斜箱体需要独立后端。

## 证据范围

本次 SSH 操作包括只读环境检查、上传不含凭据的发布包、创建新版本目录、解包、
建立 `current` 指针和离线回放；未修改系统 Python、SDK、旧 baseline、控制锁、
服务进程或机器人状态。

2026-09-11 起 `current` 已切换到
`v5_2_v5_3b_live_20260910_01`，增加实时采集、SAM3/LingBot、ROI 候选和人工
确认入口；该后续版本及其验证边界见[实时感知实现记录](s1_orin_live_perception_implementation_20260911.md)。