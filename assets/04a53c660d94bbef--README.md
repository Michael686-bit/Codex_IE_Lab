# S1 主机及相机只读检查 — 2026-10-16

检查窗口：北京时间 10:12–10:17。用户明确授权连接机器人检查状态。

## 结论

SSH 可连接 `galbot@10.34.216.17`，主机为 `galbot-echo`，内核
`5.10.216-tegra`。**现有六路查看器当前未收到任何图像，不能沿用
2026-09-17 的成功记录宣称它在当前机器人系统上可用。**

本次复用了用户已启动的相机桥，仅新建本机 ROS 订阅检查节点，没有新建 SDK
reader、调用机器人状态/控制接口或发送运动命令。全部检查用短时独立 SSH，
不复用共享 ControlMaster；没有修改远端文件、配置、服务或进程。

## 已验证证据

- 本机已有 `ros2 launch s1_camera_viewer live_core_rgbd_viewer.launch.py
  rate_hz:=1.0 duration_s:=0.0 headless:=false`，bridge PID 为 `2474443`，
  对应 S1 reader PID `249616`。它们在本次检查前已存在，未停止。
- 本机 GUI PID `2474445` 的 launch 日志显示 10:11:50 正常退出；没有证据
  表明窗口崩溃。桥与 reader 仍在运行。
- 10:14:38 开始进行 15.065 秒订阅检查，六路远端状态均持续更新
  （时间线序号 133→146，最终状态 147），`transport_ok=true`、
  `init_ok=true`、`state=empty`，每路本地接收图像数和新源帧数均为 0。
  因而 SSH/本机 ROS 状态链路畅通，但没有来自 SDK getter 的图像。
- reader 使用的 runtime 源文件声明 `galbot_sdk.__version__ = "1.9.0"`，
  runtime 路径仍为 `/home/galbot/ie_lab/projects/chassis_env/build/sdk_runtime`。
  其 EmbOSA 日志为 **runtime/build V9.1.2**，启动时报
  `key 'peer_lists' not found`，多个相机、标定和深度订阅统计为 0；
  初始化期间另有 target/controller server 连接超时。
- 当前相机服务的 EmbOSA 日志为 **runtime/build V10.0.14**，使用新的
  discovery server 配置。HPU 版本文件为 `0118020020260918`，相机服务
  自报 0.8.3、GBS_1.18、构建日期 2026-09-18。
- 相机启动日志明确记录四路旧 RGB `image_raw` 的 JPEG writer disabled。
  当前 RGB 发布改为 H.264 视频：

  | 相机 | 当前视频话题 |
  | --- | --- |
  | 头部左 | `/cam_head_f/stereo_color_l/video` |
  | 头部右 | `/cam_head_f/stereo_color_r/video` |
  | 左腕 | `/cam_arm_l/color/video` |
  | 右腕 | `/cam_arm_r/color/video` |

- 10:17 的源端日志显示双腕约 14.99 FPS 采集、约 15 FPS 视频，原生深度
  持续发布；头部左右约 30 FPS，并有 `publish_ok=1`。这证明该窗口内
  采集/发布进程报告持续产出，**没有直接接收解码当前像素**，因此不把它
  等同于图像质量、标定、RGB-depth 配准或端到端同步验收。

## 主机附带观测

- 根盘占用 28%，可用约 1.3 TB；10:17 时内存可用 4377 MiB，swap 已用
  4936 MiB。资源快照不构成长期负载或内存泄漏诊断。
- 两个失败服务：`galbot-i2c-status.service` 和 `pps_ts2spe.service`。
  I2C 扫描日志为若干 link/video lock mismatch；其物理通道与实际安装
  相机的对应待验证，不能直接推断相机损坏。PPS 服务因 `/dev/pps0` 不存在
  在本次开机时失败，对当前同步链路的影响待验证。
- 查询时最近十分钟的 warning 及以上内核日志无记录；不代表整个启动周期
  或所有系统日志无异常。

## 复核方式与产物

- [远端证据摘要](remote_evidence.log)：独立 SSH 执行 `hostname`、`uptime`、
  `free -m`、`df -h /`、`systemctl --failed`，以及对相机和 EmbOSA 日志
  的 `head`/`tail` 查询。未执行 I2C 扫描器。
- [订阅检查脚本](check_local_streams.py)：只订阅已经存在的本机 ROS 话题，
  不含 SSH、SDK 或机器人命令。
- [完整订阅结果及时间线](results/report.json)：六路均无图像，本次检查
  **退出 1 为观测门槛未通过**，不是脚本异常。
- `results/grid_latest.png`：当前缺帧状态面板，不是真实相机画面。

在已有 bridge 正常运行的本机 ROS 环境复查：

```bash
cd '/home/lsy03/文档/ChatGPT/S1'
source /opt/ros/humble/setup.bash
source experiments/20260916_s1_camera_viewer/ros2_ws/install/setup.bash
export ROS_DOMAIN_ID=84
export ROS_LOCALHOST_ONLY=1
export ROS_LOG_DIR=/tmp/s1_camera_check_20261016_logs
/usr/bin/python3 experiments/20261016_s1_camera_check/check_local_streams.py \
  --output-dir /tmp/s1_camera_recheck --duration-s 15
```

## 下一步边界

查看器适配应先核对与当前 GBS_1.18/EmbOSA 10.0.14 匹配的 SDK/被动订阅
接口、发现配置和 H.264 消息/解码合同，再验证双腕原生深度及内参。
旧 SDK 解析失败与旧 RGB 话题停用均已证实，但深度订阅无匹配的全部根因
和新接口端到端可用性仍待验证。本次没有升级 SDK、修改生产相机配置，
也没有为排查重启服务或运行 Mode 00。