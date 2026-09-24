# 当前状态

## 2026-09-20：独立 SAPIEN 可视化入门环境

- VERIFIED：新增 `robotwin-sim:20260920` 镜像和 `robotwin-learning` 容器，Python 3.10.18 / SAPIEN 3.0.0b1；入口 `http://127.0.0.1:8010`，与 LingBot 8006 服务同时运行。
- VERIFIED：官方 RoboTwin Aloha-AgileX 资产渲染成功，总览、顶部和双腕相机可见；关节滑块和浏览器预测按钮可用。当前仿真观测经 WebSocket 输入 LingBot，返回 `(25,14)` 有限动作，浏览器实测约 378 ms。
- 范围：简化场景中的关节姿态可视化及预测预览，未执行动态抓取闭环；完整 RoboTwin benchmark 依赖、任务成功率尚未验收。未连接 G1。
- 说明与证据：[入门环境](</home/lsy03/文档/ChatGPT/VLA G1 项目/robotwin_sim/README.md>)；`output/scene.png`、`output/policy-preview.json` 位于该目录。源码/资产版本见 `source-lock.json`。

## 2026-09-17：LingBot 本机 Docker 推理验收

- VERIFIED（下载）：基础镜像约 9.40 GB、模型约 25.52 GB 已下载并校验；`logs/image-complete.json`、`logs/model-complete.json` 均为 `verified: true`，模型 manifest 中 18 个文件大小全部匹配。
- VERIFIED（构建）：部署目录为 `/home/lsy03/Lsy03_document/VLA_G1/lingbot_deploy`；官方源码固定在 `4144e9c35c7ab490927cc3743e777f95433f953d`；镜像 `lingbot-vla-v2:4144e9c-infer` 已成功构建。构建阶段使用 Ubuntu/PyPI 镜像处理网络波动，并安装官方 FlashAttention 2.8.3 预编译 wheel。
- VERIFIED（GPU 与依赖）：`logs/check-env.log` 显示 Python 3.12.11、PyTorch 2.8.0+cu128、CUDA 12.8、FlashAttention 2.8.3、NVIDIA GeForce RTX 4090（24073.875 MiB）；BF16 矩阵运算和 policy 导入均通过。
- VERIFIED（离线推理）：`logs/smoke-infer.log` 的合成输入推理通过，动作输出形状为 `(25, 14)` 且无 NaN/Inf；不启用 compile 时预热后平均约 361.46 ms，峰值 allocated/reserved 显存约 12428/12468 MiB。
- VERIFIED（服务）：容器 `lingbot-vla-v2-local` 正在运行，`GET http://127.0.0.1:8006/healthz` 返回 `OK`。按协议先发送 `reset(robotwin)` 后，WebSocket 合成观测请求返回 `(25, 14)` 有限动作；连续服务端推理耗时约 353.3 ms、340.6 ms。
- 本轮没有连接 G1、挂载串口或发送机器人动作。RoboTwin 权重只用于验证本机运行链路，不能直接证明 G1 已适配。
- PLANNED（G1 接入）：准备 G1 LeRobot 数据、robot config、归一化统计和 G1 后训练 checkpoint；核对 G1 状态/动作 14 维映射，再做离线回放、限位和安全门控验证后，才考虑真机接入。操作入口：[部署说明](../lingbot_deploy/README.md)。

## 历史下载过程（已由上方验收状态取代）

- 最新停点：用户修正镜像与代理变量后继续运行模型命令。模型进程仍在前台运行，分片缓存持续保留；当前小段时间可能等待网络响应。
- 用户明确选择独立 Docker 镜像与容器部署 LingBot，并在确认方案后授权继续执行。部署目录：`/home/lsy03/Lsy03_document/VLA_G1/lingbot_deploy`。
- VERIFIED（本次 Docker 实测）：现有镜像启动的临时容器能识别 RTX 4090、24564 MiB 显存、驱动 595.84；现有 CUDA PyTorch 可访问 GPU。此结论不代表 LingBot 新镜像已安装成功。
- VERIFIED（本次源代码检查）：官方仓库已固定到 `4144e9c35c7ab490927cc3743e777f95433f953d`，独立 Dockerfile 与离线验收脚本已写入并通过 Python/Shell 语法检查，构建和推理尚未验收。
- UNRESOLVED（网络）：Docker 直连超时，普通 HF 下载及 hf_transfer 曾遇到断流；镜像 API 的 308 已处理，当前仍可能因代理 TLS 断连重试。
- VERIFIED（2026-09-17 09:22 进度检查）：基础镜像 9.398/9.398 GB 已通过官方层哈希，`cache/base-image/image.tar` 和 `logs/image-complete.json` 已生成。模型按 manifest 为约 18.223/25.518 GB（71.41%，剩 7.296 GB）；第 1–3 个分片完整，第 4 个分片约完成 67.5%，第 5–6 个分片尚未开始。正确镜像 URL 对范围请求可返回 HTTP 206。
- VERIFIED（2026-09-17 短时测速）：模型进程仍存活；最近 45 秒新增 25,165,824 字节，约 0.533 MiB/s（0.559 MB/s）。按最新统计剩余约 7.113 GB，理论约 3.5 小时，按代理重试和波动预留 4–6 小时。
- VERIFIED（2026-09-16 短时测速）：模型当前分片增长约 0.27 MiB/s；按此瞬时速度，剩余部分约需 11 小时，实际时间会受代理重试和带宽波动影响，按 10–15 小时预留。
- PLANNED（后台部署顺序）：导入镜像 → 构建独立推理镜像 → GPU 运算/导入检查 → 权重校验 → 合成输入离线推理 → localhost 8006 服务。任一步失败即停止后续步骤；不能把服务启动/下载中表述成推理成功。
- 本次未连接机器人。RoboTwin 权重仅用于本机运行链路验证；G1 数据映射、微调与真机执行另行开展。
- 下一次接续先查下载服务及 `lingbot_deploy/logs/`，不要重复下载；恢复前应确认代理能稳定访问大文件。操作入口：[部署说明](../lingbot_deploy/README.md)。

以下为保留的历史 G1 进度；不代表本次重新验证。

更新日期：2026-09-08。下述真机结论来自历史特定测试，不能代替下一次现场状态检查。

## 9 月 8 日接续停点

- VERIFIED（开发工作区本地测试）：遥操映射、JSON 协议、接收门控共 39 项通过，只读状态适配 2 项通过；401 帧虚拟时间合成目标完成 0 → +1° → 0 → -1° → 0，预览输出变化率不超过 0.03 rad/s。接收端新增首帧起点检查、独立限速、收包时超时复核及旧会话拒绝。无运动执行。
- VERIFIED（9 月 7 日历史远端测试）：G1 左臂只读 SDK 采样通过，第 7 关节约 0.717 rad；当时 joint1、joint5、joint6 位于硬限位。已有历史 JSONL 跨机预览一次 50/50 通过；200 ms 超时根因仍未定位，300 ms 仅为预览候选，不能据此报告停止距离或稳定性已验收。
- VERIFIED（9 月 8 日后续复测）：用户重建 SSH 后连接恢复，今日修改已同步到 G1 独立目录，两端 24 个代码文件 SHA256 一致。G1 上 39+2 项测试通过；跨机合成预览接受 401/401 条目标，故意断流后拒绝 1 条迟到位置，输出变化率不超过 0.03 rad/s，最终回到合成起点 0.4 rad。最大接收间隔 209.689 ms；这次短测仍不代表长期网络稳定性。
- 用户选择跳过厂商授权及新 GP001 采集；目前没有主动方向实测。协议源数据年龄、积压处理、认证、连续使能、反馈闭环及真实 SDK 停止仍未验收，P0 未完成。
- 当前阻碍：宿主未识别到 GP001 USB，无 /dev/ttyACM0；宿主直读依赖齐全，助手进程未设置授权变量。现有 SynthNova 容器有授权变量与旧串口节点，但未验证授权有效性或设备在线。用户确认走宿主直读、跳过容器；下一步恢复 GP001 USB 识别并核查宿主正常授权环境，再做实时无运动预览。本轮没有打开 GP001 串口或运行运动接口。

当前实现仍维护于 `/home/lsy03/文档/ChatGPT/VLA G1 项目` 的 `teleoperation/` 和 `robot_g1/`，尚未迁入正式仓库。详细证据：[9 月 8 日合成验证](</home/lsy03/文档/ChatGPT/VLA G1 项目/teleoperation/SYNTHETIC_VALIDATION_20260908.md>)、[9 月 7 日只读实测](</home/lsy03/文档/ChatGPT/VLA G1 项目/robot_g1/READ_ONLY_VALIDATION.md>)。下方初始化记录与上述停点冲突时，以本节为准。

## 当前主线

初始化项目协作文档，随后实现 **GP001 → G1 左臂** 遥操作。首次实机映射仅开放左臂第 7 关节；先做无运动映射检查和接收端故障测试，再开展用户现场操作。

## 已有证据

| 模块 | 状态与范围 |
|---|---|
| GP001 宿主机读取 | VERIFIED，9 月 4 日历史测试：100/100 帧有效、左右各 7 维、时间戳递增。约 95 Hz 为短测估计；未完成长期稳定性与跨设备同步验收 |
| SynthNova | VERIFIED，历史记录：虚拟双臂 5 秒消费 494 帧；不代表真机遥操已完成 |
| G1 状态 / SDK | VERIFIED，9 月 7 日 dry-run：SDK 1.9.0、Python 3.8.10、状态时间戳更新 |
| 左臂第 7 关节 | VERIFIED，用户提供日志：+1° 目标、反馈与回程通过 |
| 右臂第 7 关节 | VERIFIED，用户提供日志：+1° 目标、反馈与回程通过 |
| 右夹爪 | VERIFIED，用户提供日志：20 mm、100 mm 两次命令成功；最终回读 100 mm、静止 |
| 左夹爪 | VERIFIED 状态读取为 50 mm、静止；USER_REPORTED“左夹爪可以了”，未提供动作命令与到位日志，动作验收待补 |

具体数值、来源和限制见 [实测记录](../experiments/20260907_g1_control_smoke/README.md)。上述证据仅支持基础控制子项通过，**P0 尚未整体验收**。

## 待解决

- GP001 历史回放映射与网络预览已实现；实时 GP001 到真机执行尚未打通。
- 左右臂第 5/6 关节在当时姿态接近或处于限位；新姿态必须重新测量。安全中立姿态尚未核验。
- 持续使能、接收端超时停止、进程退出/断网、过期目标拒绝和重连防跳变尚未实测。
- 夹爪 `effort=100.0` 的实际反馈含义未核验，不能当成已标定夹持力。
- GP001 夹爪字段、单位、关节方向及设备时钟语义仍需核验。
- 相机/状态/动作联合 episode、数据转换、模型训练与策略部署尚未闭环。

## 下一步

1. 盘点并迁入自有 GP001 读取与 G1 冒烟测试代码，保留来源及测试；官方依赖继续引用既有安装。
2. 定义单臂消息与映射：关节名/顺序、单位、序号、有效时限、使能状态、零位和目标边界。
3. 实现默认无运动的映射预览和 G1 接收端；通过离线与故障注入测试。
4. 由用户在现场执行受限的左臂第 7 关节映射测试；完成前不扩展七轴。

## 环境与部署

正式根目录 `/home/lsy03/Lsy03_document/VLA_G1` 已建立文档入口。预览代码已部署到 G1 `/home/galbot/vla_g1_readonly_20260907`，9 月 8 日修改已同步且核验代码哈希。开发源代码仍在原工作区，未迁入正式仓库。

历史 G1 地址为 `galbot@10.34.216.136`，SDK 模块 `/data/galbot/lib/galbot_sdk`。SSH 复用连接是临时会话，不能默认仍有效；本次初始化未重新连接机器人。

仓库版本状态以 `git status` 和 `git log` 为准，不在本文件手写固定“干净”或提交号。