# P0 环境与数据格式验收

状态：**离线环境及真机 17 流可用性已验证；P0 源字段语义与时钟映射仍待闭环，正式数采未就绪。** 没有发送机器人运动命令、改变校时配置或修改现有控制入口。

## 16:32 后连接恢复补验

- PC eno1=192.168.1.99 与 G1 eth1=192.168.1.88 恢复千兆有线，SSH 身份验证正常。
- G1 Python 3.8.10 / aarch64，SDK 1.9.0，固件 GBS_1.17.0.0.rc7。活动与标定 URDF 哈希均与本地一致，25 个身体关节顺序一致。
- 刚启动后的首轮短检暂缺头部双目；稍后第二轮已读取 8 路图像及全部低维流的不同时间戳，17 个必采流可用。以后预检必须等待必采流准备完成，不能只检查进程存在。
- 最新数据：robot_environment_recheck.json；首轮数据：robot_environment.json。生成器已经使用新证据更新环境清单和通道验证状态。
- G1 的 NTP 上游仍为 PC。服务当时报告 offset +0.169～0.720 ms，但启动历史 jitter 约 2.037 s，尚不能将这个瞬时数值当作稳定校时验收。
- G1 上 venv、NumPy、OpenCV 模块存在。本次未创建虚拟环境或安装包；部署隔离建议见 G1环境隔离方案.md。

下文连接失败记录是本次补验前的历史过程，已经解除该连接阻挡；字段语义、源时钟与动作入口的限制仍然有效。

## 实际完成

后续已完成 60 秒、301 次主机/源时钟补验，并交叉核对机器人 C++ SDK 头文件。最新发现与具体未确认项见 [P0补充结论.md](P0补充结论.md)。raw_recording_policy 已允许在明确保留未知语义的前提下开发原始记录器，但未把 P0 标为全部通过或开放正式训练导出。

| 检查 | 实际结果 |
|---|---|
| PC 基线镜像 | `vla-g1-teleop:lerobot-0.4.4`，amd64，固定镜像 ID，见 environment_manifest.json |
| Python / LeRobot | 镜像内 Python 3.11.15、LeRobot 0.4.4 |
| PyTorch / PC SDK | PyTorch 2.7.0+cu128；挂载 SDK 1.9.1 导入成功，没有初始化机器人 |
| 数据库/图像依赖 | NumPy、PyArrow、OpenCV、PyAV 和 LeRobotDataset 导入通过，包版本列表已保存 |
| LeRobot 镜像内读取 | 9 月 18 日诊断数据 20 帧×3 路 RGB 全部可解码，14 维状态、12 维腕力形状符合预期；无动作、无深度，不是训练数据 |
| H.264 实际编解码 | 4 帧合成图像编码并解码通过 |
| 深度存储能力 | uint16 PNG 边界值无损往返；FFV1/gray16le 4 帧逐像素一致。只是编码能力验证，完整 LeRobot 深度适配留待 P2 |
| 无硬件离线入口 | 新增 `docker/run_data.sh`，不要求 GP001、不挂设备、不提供网络，不读取认证凭据 |
| 数据格式草案 | 17 个必采流：6 RGB、2 深度、2 腕力、5 关节组、2 夹爪；包含原始时间戳、时钟域、有效性、动作语义 |
| 可追溯清单 | 镜像 ID、PC 包版本、关键源码、SDK 文件与 URDF 哈希已记录 |

镜像只以临时离线容器运行，结束后删除容器；镜像本身、现有遥操启动脚本、机器人配置与现有推理容器均未修改。

## 已发现的问题及处置

1. **TorchCodec 0.10.0 无法导入。** 错误包含 FFmpeg 共享库缺失及已找到版本的符号不匹配。当前已验证路径明确使用 `video_backend="pyav"`，不依赖 TorchCodec；H.264 编码使用 PyAV 的 h264/libx264。不能宣称该镜像所有视频后端可用，也不能宣称训练的默认后端已经通过。
2. **`pip check` 不通过。** 基础环境的 isaacsim-core 要求 packaging==23.0；numba 0.59.1 要求 NumPy<1.27；isaacsim-kernel 要求 NumPy==1.26.0，而 LeRobot 虚拟环境实际为 packaging 25.0 / NumPy 2.4.6。本次未导入 Isaac Sim/Numba，选定的离线数据路径通过。保留当前镜像作为有条件基线，数采转换不调用这些组件；需要同进程仿真时必须另行隔离或构建镜像并回归，不能直接覆盖安装包。
3. **G1 当前无法连接。** 192.168.1.88:22 超时，10.34.216.136:22 返回 No route to host。没有关闭主机密钥检查，没有修改网络，没有反复重试。对应日志保存为 robot_check.log / robot_wifi_check.log。本次 check_robot.py 未在 G1 执行成功，因此不把历史配置当作本次实时验证。
4. **字段单位有明确未知项。** 现有 URDF 中头、腿、双臂共 21 个反馈关节为 revolute，可据此暂定位置 rad、速度 rad/s；chassis_joint1–4 不在 URDF，SDK 文档仅说明是被动底盘状态分组，未能核实单位，必须原样保存且禁止自动归一化。关节 effort/current 和夹爪 effort 的实际标定含义未确认，六维腕力坐标系与归零/重力补偿状态也未确认。
5. **控制入口与 action 范围。** `teleoperation.arm7_record` 调用 `direct_main(recording=True)`，没有启用 gripper，因此现有记录入口 action 为左臂 7 关节的限速后轨迹终点，单位 rad；必须同时记录起点、周期、速度限制和 command_id。`arm7_direct_gripper` 是另一个左臂＋左夹爪入口，不代表长录制入口已经支持夹爪。双臂双夹爪 16 维 action 暂不能启用。
6. **时钟尚未闭环。** 当前现有控制入口仍使用历史 104 ms 常数；本次只定位问题，未改变控制逻辑。数据格式已要求分时钟域、分段映射和残差记录，未知映射禁止直接导出训练样本。真实源时钟与机器人在线重验证仍待完成。

`container_environment.json` 中 `passed=true` 只表示选定的 PyAV 离线数据路径通过；`passed_scope` 明确限定范围，`environment_dependency_check_passed=false` 明确指出整个已安装依赖集合不干净。

## 已固定的数据格式决策

- 不减少用户指定模态，所有 17 个流标为 required；左右后环视不在范围内。
- 保存原始频率，导出层默认 10 Hz；uint16 深度与 scale 完整保留，不能转换成 8 位深度预览替代原始数据。
- `source_timestamp_ns`、接收 wall/monotonic、时钟域和映射段、序号、有效性、文件索引及哈希都必须保存。
- 关节按名称建立确定顺序，不隐式依赖 SDK vector 顺序；真实 joint manifest 在连接恢复后重新读取。
- `action` 保存实际限位/限速后下发的目标，SDK 发布成功与真实硬件执行分开；无法观察的机器人接收/执行时刻用 null，不伪造。
- 默认候选 action profile 为当前左臂 7 维；左臂＋夹爪 8 维、双臂双夹爪 16 维独立标记为未集成/未验证，不能混合 schema。
- 格式文件为**设计契约草案**，不是完整的 JSON Schema 校验器，也不是已实现的 recorder。待真机和字段语义补齐后冻结为正式版本。

## 文件

- `capture_contract.v1.json`：17 流数据格式和单位/时钟/动作契约草案。
- `environment_manifest.json`：镜像、关键代码、SDK/URDF 哈希及历史证据来源。
- `container_environment.json`：镜像内依赖清单、可用路径与失败项。
- `check_container.py`：可重复的离线容器检查。
- `check_robot.py`：连接恢复后使用的只读真机通道/标定检查程序。
- `build_contract.py`：基于明确标记的历史样本和当前源码生成本次格式草案，内置通道数量/唯一性断言。

离线复核入口（在项目根目录执行）：

```bash
bash docker/run_data.sh bash -c 'source /opt/galbot/galbot_sdk/linux-x86_64-gcc940/setup.sh; python -B acquisition/p0_20260920/check_container.py'
```

此入口没有网络/串口，不能用于遥操。实际控制继续使用原控制入口；本次不改变任何运动入口。

## P0 结束条件与剩余工作

已完成所有当前可离线验证的环境、格式和源码审查工作。仍需：

1. G1 恢复连接后运行只读检查，核对实际 SDK、固件、URDF/标定、全部 17 流与关节顺序；不同 PC/G1 SDK 版本的当前兼容性也需重验证。
2. 核实底盘 4 个字段的含义/单位、腕力坐标系，以及各源时钟语义；允许原始层 unknown 保存，但在宣称训练 schema 完全冻结前应解决或明确限制使用。
3. 在线验收时钟映射，设计替换历史固定补偿并保留控制安全检查的独立改动和验证。

因此当前可供下一步参考的离线成果已经交付，但不将 P0 标为全部完成，不启动正式数据录制。