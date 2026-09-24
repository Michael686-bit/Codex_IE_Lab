# LingBot 新手上手教程

这份教程只练习本机推理，不连接 G1，也不会发送机器人动作。

## 先理解三件事

LingBot 不是聊天机器人。它接收三类信息：

1. 相机图像：顶部相机、左腕相机、右腕相机。
2. 机器人状态：当前测试是 14 个数值。
3. 任务文字：例如“把物体拿起来放到桌上”。

它输出一段动作。当前 RoboTwin 测试模型输出形状是 `(25, 14)`，表示 25 个动作时刻、每个时刻 14 个数值。这是 RoboTwin 配置的测试结果，不代表 G1 已经完成动作映射。官方模型还定义了更通用的 55 维统一动作空间，真实机器人需要自己的配置和后训练数据。

## 第一课：确认服务能用

打开终端执行：

```bash
cd /home/lsy03/Lsy03_document/VLA_G1/lingbot_deploy
scripts/lingbot.sh status
curl --noproxy '*' http://127.0.0.1:8006/healthz
```

看到 `OK` 就表示服务进程正在监听。再运行一次离线冒烟测试：

```bash
scripts/lingbot.sh smoke
```

这个测试使用随机图像和零状态，只验证“模型能否加载并输出合法动作”，不代表它完成了真实任务。

## 第二课：理解一次请求

WebSocket 客户端连接后，先发送 reset：

```json
{"reset": true, "robo_name": "robotwin"}
```

然后发送观测，字段如下：

```text
observation.state
observation.images.cam_high
observation.images.cam_left_wrist
observation.images.cam_right_wrist
task
```

服务返回 `action` 和 `server_timing`。官方客户端使用 MessagePack 传输 NumPy 数组，并提供 `reset(robo_name)` 方法；当前部署的请求协议与此一致。

## 第三课：学会看日志

```bash
scripts/lingbot.sh logs
```

重点看三类信息：

- `Model initialized`：模型完成加载。
- `sample_actions ... cost`：一次推理耗时。
- `connection handler failed`：请求格式或模型调用出错，需要查看 traceback。

## 第四课：理解目前距离 G1 还有什么

官方后训练流程要求准备 LeRobot 数据集、robot config 和 normalization statistics。G1 接入还要把 G1 的相机、状态、动作字段映射到模型配置，并先做离线回放和安全限位测试。当前 RoboTwin checkpoint 只用于学习和验证本机运行链路。

## 推荐学习顺序

1. 反复运行 `status`、`healthz`、`smoke`，熟悉容器、服务和日志。
2. 学会用 Python 字典表示一帧图像、状态和任务文字。
3. 修改任务文字，观察请求是否成功返回动作；不要把输出发送给 G1。
4. 学习 LeRobot 数据集的 episode、observation、action、task 概念。
5. 再研究 G1 的 robot config、归一化统计和动作映射。

服务停止或重启：

```bash
scripts/lingbot.sh stop
scripts/lingbot.sh start
```