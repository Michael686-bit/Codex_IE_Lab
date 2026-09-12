# Orin Docker GPU 接入验证

2026-09-11，用户授权检查和接通 GPU Docker。状态：实机通过。

## 环境与执行

- 主机 galbot-echo / aarch64，L4T R35.6.0。
- Docker 26.1.3，NVIDIA runtime 3.9.0-1、toolkit 1.11.0~rc.1-1 已安装。
- `/etc/docker/daemon.json` 已注册 nvidia；默认 runtime 为 runc，未修改。
- 包 `nvidia-container` 报 5.1.5-b11；不要仅凭历史 JetPack 标签推断整套组件
  版本一致。GPU driver API 返回 11040（CUDA 11.4 API），不是 nvcc/toolkit 实测。
- 复用本机已有 `s1-sjtu-0806-slim:latest` 对应固定 image ID：
  `sha256:6359272ddc5c520c60dd61a2293672d826e5312046c3986170bbdd0849c71697`。
  此镜像仅用作 GPU 驱动测试载体；不是已完成的算法开发镜像。

先覆盖原 ROS entrypoint，在断网只读临时容器中检查 Python 和库；其系统
Python 无 pip，本次未安装任何包。然后用 NVIDIA runtime 验证 libcuda 和设备
映射，最后以宿主机用户 UID/GID 加 video 组运行 ctypes CUDA Driver API 测试。
PTX 核函数用一个 GPU 线程写入 42，同步后复制回 CPU 断言结果。

```json
{"status":"passed","device":"Orin","device_count":1,"cuda_driver_api_version":11040,"kernel_output":42,"expected":42,"robot_sdk_called":false}
```

## 在 Orin 上复验

```bash
bash /home/galbot/Lsy03/box_pose_pipeline_docker/gpu_check_20260911/run_gpu_smoke.sh
```

脚本与 gpu_smoke.py 已上传到该目录，本地远端 SHA-256 一致：

```text
3daa1acb643c8ade480ad0600de15481c66789162a22cc8dfd06960169e9f166  gpu_smoke.py
80f958a2e2f00b0eda491406fc9d00082d0b9b33b0e93463af4792eca2e08cc3  run_gpu_smoke.sh
```

启动采用 `--runtime nvidia`、`NVIDIA_VISIBLE_DEVICES=all` 和
`NVIDIA_DRIVER_CAPABILITIES=compute,utility`；非 root、无 privileged、断网、
只读根文件系统、cap-drop ALL、no-new-privileges；2 CPU / 2 GiB 内存、128
PIDs、128 MiB 临时目录。输入脚本只读挂载，退出自动删除容器。
CPU/内存限制不等于 GPU 算力或显存配额，本次只执行极小任务，未做压力测试。

## 变更与边界

仅创建独立远端目录并上传两个文件，执行临时容器。没有安装/升级宿主机包、
重启 Docker、修改默认 runtime、启动原镜像入口或调用机器人 SDK。未采集、
未运动；测试结束 docker ps 为空，单次 SSH 已退出。
旧流水线 current 仍为 `releases/v5_2_v5_3b_live_20260910_01`。

后续算法镜像仍需锁定 ARM64 CUDA/PyTorch/CuPy 等实际依赖并逐项测试。
现有 NumPy/SciPy V5 不会因 runtime 接入而自动使用 GPU。GPU 接入完成不代表
流水线 Docker 迁移、算法加速或性能验证完成。

参考：[NVIDIA JetPack 5.1.4 容器支持](https://docs.nvidia.com/jetson/jetpack/5.1.4/introduction/index.html)、
[NVIDIA L4T JetPack 容器运行参数](https://catalog.ngc.nvidia.com/orgs/nvidia/-/containers/l4t-jetpack/-)。