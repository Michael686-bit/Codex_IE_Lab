# VLA G1 PC 端容器

该容器用于 PC 端 LeRobot、GP001 和 G1 有线通信开发。它不包含闭源 Galbot SDK，也不提供真机运动入口。

## 固定环境

- 基础镜像：本地已校验的 `synthnova-runtime:20260801`
- Ubuntu 22.04
- Python 3.11
- LeRobot 0.4.4（独立 `/opt/vla-venv`）
- 复用基础镜像中的 CUDA PyTorch 2.7.0，不重复下载 PyTorch
- 宿主网络，直接使用 `eno1 -> 192.168.1.0/24`
- 只映射 GP001 串口 `/dev/ttyACM0`

## 构建和验证

从项目根目录执行：

```bash
bash docker/check_host.sh
bash docker/build.sh
bash docker/verify.sh
```

进入交互容器：

```bash
bash docker/run.sh
```

如果 GP001 设备名变化：

```bash
GP001_DEVICE=/dev/ttyACM1 bash docker/run.sh
```

`docker/run.sh` 使用 host 网络，并且只映射指定串口，没有使用 `privileged` 模式。仓库同时保留 `compose.yaml`；当主机安装 Compose 插件后可作为可选入口，当前不依赖它。

## 可选 Galbot PC SDK

PC 端容器只能使用 `linux-x86_64-gcc940` SDK，不能使用 G1 上的 `linux-aarch64-gcc940` SDK。当官方 x86_64 SDK 安装包就绪后，先核对它的版本和安装脚本，再增加单独的 SDK 镜像层。当前项目记录的 G1 机器人端 SDK 是 1.9.0，不应在未验证兼容性时混装 1.9.1。

如果已将 PC SDK 安装到项目的 `.vendor/galbot-pc-sdk`，`docker/run.sh` 会将它以只读方式挂载到容器的 `/opt/galbot`。也可以显式指定目录：

```bash
GALBOT_SDK_HOST_DIR=/path/to/galbot-pc-sdk bash docker/run.sh
```

`docker/verify_container.sh` 如果发现可读的 `/opt/galbot/galbot_sdk/linux-x86_64-gcc940/setup.sh`，只会执行 SDK 导入和版本检查，不会初始化机器人或发送运动命令。

GP001 的 Remote Control Lite 是单独的厂商受保护组件，不放进本项目镜像。若当前终端已经由厂商环境完成授权，可在启动时挂载其模块目录；脚本只透传当前 shell 中已存在的 `ENCMGR_APP_ID` 和 `ENCMGR_APP_SECRET`，不会把值写入文件：

```bash
SYNTHNOVA_MODULE_ROOT=/path/to/synthnova_delivery/module \
  bash docker/run.sh python3 /path/to/gp001_capture.py --check-only --port /dev/ttyACM0
```