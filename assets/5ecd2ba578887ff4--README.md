# LingBot-VLA 本机 Docker 部署

此目录只负责 LingBot-VLA 的本机推理容器。当前阶段不连接 Galbot G1，不发送任何机器人动作。

## 当前部署方式（2026-09-17）

基础镜像和模型已经完成下载及校验。基础镜像约 9.40 GB，模型约 25.52 GB；`logs/image-complete.json`、`logs/model-complete.json` 均记录 `verified: true`，模型 manifest 中的 18 个文件大小全部匹配。

本机推理镜像 `lingbot-vla-v2:4144e9c-infer` 已构建完成。构建使用 Ubuntu 清华镜像和 PyPI 清华镜像处理网络波动，FlashAttention 使用官方 v2.8.3 预编译 wheel（CUDA 12、PyTorch 2.8、Python 3.12、cxx11 ABI），没有改动模型或官方源码版本。

已完成实际验收：RTX 4090、CUDA 12.8、PyTorch 2.8.0、FlashAttention 2.8.3 和 policy 导入通过；合成输入离线推理输出 `(25, 14)` 动作块，预热后平均约 361 ms，峰值显存约 12.4 GiB；WebSocket 服务监听 `127.0.0.1:8006`，健康检查和真实推理请求均通过。

镜像 API 和模型下载脚本仍保留在目录中，便于以后重新校验或断点续传；不要删除 `models/model-manifest.json`。

现使用 `scripts/resumable_download.py`：每次请求 4 MiB，验证 Content-Range 后才追加，完成文件后校验官方 SHA256；小型 Git 文件校验 Git blob SHA1。保留并复用之前下载的部分文件。

三个用户级服务分别负责镜像下载、模型下载和后续构建验收，独立于对话运行：

```bash
systemctl --user status lingbot-image-download lingbot-model-download lingbot-install
tail -n 20 logs/image-download.log
tail -n 20 logs/model-download.log
tail -n 30 logs/pipeline.log
```

`lingbot-install` 按顺序执行：镜像校验完成 → 导入镜像 → 构建 → GPU 运算检查 → 权重校验完成 → 离线推理 → 启动 localhost 服务。任一步失败即停止后续步骤；日志中出现 `PASS: localhost health endpoint ready` 才表示本轮部署流程完成。

基础镜像约 9.40 GB，模型约 25.52 GB。临时镜像 tar 还会额外占用约 9.40 GB；下载速度取决于当前代理。下载辅助进程在宿主机运行，模型推理环境始终位于 Docker 容器。

## 目录

- `lingbot-vla-v2/`：固定 commit 的官方源码
- `models/`：Qwen3-VL 处理器文件和 LingBot 后训练权重
- `Dockerfile`：Python 3.12、PyTorch 2.8.0 推理镜像
- `scripts/lingbot.sh`：构建、检查、离线冒烟和启动命令
- `logs/`：构建和验收日志

## 使用

以下为手动操作参考。先确认宿主机 `nvidia-smi` 正常；已有完整镜像和模型时不要重复下载：

```bash
docker load --input cache/base-image/image.tar
```

然后在本目录执行：

```bash
scripts/lingbot.sh build
scripts/lingbot.sh check
scripts/lingbot.sh smoke
scripts/lingbot.sh start
```

`check` 验证 CUDA、PyTorch、FlashAttention 和模型模块导入；`smoke` 使用随机图像、零状态和合成任务做离线推理，验证动作张量形状、有限值、耗时和峰值显存。它不代表 G1 动作已经适配，也不代表任务成功。

默认服务器监听 `127.0.0.1:8006`。后续 G1 控制容器只通过 WebSocket 接入；G1 串口和 SDK 不挂载到 LingBot 容器。

WebSocket 客户端首次连接后要先发送 `{"reset": true, "robo_name": "robotwin"}`，再发送包含 `observation.state`、三个 `observation.images.*` 图像和 `task` 字段的观测。服务返回的动作块在本机验收中为 `(25, 14)`；该协议验证不代表 G1 的状态或动作映射已经完成。

## 模型文件

当前离线验收使用 `robbyant/lingbot-vla-v2-6b-robotwin` 的固定 revision。它用于验证模型运行链路，不能直接控制 G1。G1 真正部署前必须准备 G1 的 LeRobot 数据、robot config、归一化统计和后训练 checkpoint。