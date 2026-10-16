# Galbot G1：LingBot-VLA 2.0 原始权重试验

## 当前推荐：分别启动常驻模型与机器人调用

2026-10-16 新增两个入口。模型服务只负责加载、预热和推理；机器人入口复用它，结束时仅清理本轮 SDK，模型继续占用显存。无需在每个新终端手动导出认证变量，默认读取 `~/.config/g1_policy_control/model.token`；首次启动仅在认证文件不存在时生成，既有文件不覆盖。

```bash
cd '/home/lsy03/文档/ChatGPT/VLA G1 项目'

# 第一步：启动并预热常驻原始模型；不连接机器人。
bash lingbot_pretrain_g1/model_service.sh start

# 第二步（只读）：使用已就绪的服务做5秒只读预览。
bash lingbot_pretrain_g1/run_robot.sh preview

# 第二步（现场操作人执行）：先只读预览，通过后自动进行5秒真实运动。
bash lingbot_pretrain_g1/run_robot.sh execute

# 查看状态与最近日志；均不创建控制会话。
bash lingbot_pretrain_g1/model_service.sh status
bash lingbot_pretrain_g1/model_service.sh logs

# 释放显存；测试占用服务期间会拒绝停止。
bash lingbot_pretrain_g1/model_service.sh stop
```

等待 `MODEL READY` 后再调用机器人。真实运动入口仍需现场交互终端、手臂附近净空、急停可用；左臂5秒控制窗口、每关节速度上限0.5rad/s、相对起点偏移不超过5°，夹爪保持；STOP回车或Ctrl+C停止。每个新预测仍只执行首个100ms动作段。该入口不保证整整5秒持续运动，也不把SDK位移判据当作肉眼可见或抓牛奶成功。

2026-10-16 按用户要求，将5秒实验的指令限速从0.05rad/s提高到0.5rad/s，使用独立的 `g1_policy_control/configs/pretrained_motion.json`。实测超速立即停止阈值随原有1.2倍规则变为0.6rad/s；指令加速度限制仍为0.3rad/s²。0.5是上限，实际指令还取决于模型目标、加速度限制和5°起点偏移预算；达到位移预算可能提前退出。历史0.05rad/s的通过记录不构成新速度验收。单命令入口 `run_step.sh` 继续使用 `validation.json` 的0.05rad/s配置。

模型输出通过本地映射还原成25×8动作数组：七个左臂绝对关节角（rad）和夹爪宽度（m）。当前 `PolicyClient.predict()` 只选择第0行，其余24行不进入执行队列。所选关节目标经过时效、范围、目标距离、速度、指令加速度和位移预算检查，由SDK执行进程再次读取反馈并限幅，构造 `t=0` 实测角度到 `t=0.1s` 受限目标的两点关节位置轨迹，使用 `TARGET_TYPE_OVERRIDE` 和 `TARGET_SAMPLING_LINEAR_INTERPOLATE` 交给 `left_arm_pvt_ctrl`。随后等待下一次新观测和推理，当前没有完整chunk轨迹跟踪器。100ms是本实验指定的段长，不能据此认定预训练chunk的25点对应2.5秒。

新版 `inference` 事件记录 `action_chunk`、`raw_action_chunk`、`selected_action_index=0`、`model_first_action` 和最终 `goal`，用于区分模型整块输出与实际执行目标。提高限速不会自动启用剩余24个动作。完整chunk执行还需要确认相邻动作的时间间隔、过期点处理、连续参考生成和新旧chunk衔接。

固定容器名为 `lingbot_vla_2_0-pretrain-service`，仅监听本机8092端口。重复 `start` 会校验完整模型profile及实例，已预热时直接复用；18000MiB空闲要求仅针对首次加载。`/health` 查询不重置会话，返回进程实例、加载/预热状态及计数。首次 `/warmup` 在同一持久推理线程完成，重复预热请求直接返回；每轮机器人调用通过 `/reset` 建立新的会话，不重新加载权重。

启动、预热、停止与机器人调用共用 `lerobot_runs/lingbot_pretrain_model.lock`。机器人入口从身份检查起持锁，覆盖只读预览、实际执行及SDK清理；模型实例发生变化则中止本轮，不能自动续跑旧动作。模型容器另有工作区归属标签，同名但不属于本项目的容器拒绝接管。停止模型前保存日志到 `service_runs/resident/<container_id>/`。电脑重启后需再次运行 `start`，未设置开机自启。

首次使用建议连续运行两轮 `run_robot.sh preview`，前后查看 `status`：容器ID、服务实例ID、模型进程保持一致，加载和预热计数各为1，会话ID应更新，两个只读报告均通过。当前实现已用本地HTTP模型替身验证复用和会话隔离，真实GPU常驻复用需现场运行这两轮确认。

下文的 `run_motion.sh`、`run_step.sh` 是历史一体化临时服务入口；常驻模式使用上面的两个新入口。

`models/lingbot-vla-v2-6b/` 是从“蚂蚁灵波具身大模型挑战赛”复制的官方通用预训练权重，revision `11c703bf6a5c1f45b3b69168482da11fdbba53d7`。六个 safetensors 分片逐个通过 SHA-256 校验；完整文件列表见 `source_manifest.json`。模型参数没有在本项目更新。

`checkpoints/global_step_0/hf_ckpt` 指向这份本地副本。`lingbotvla_cli.yaml` 是该权重的推理配置，G1 输入输出映射在 `configs/robot_configs/galbot_g1.yaml`，归一化统计来自项目内 32 个 G1 牛奶训练 episode，验证 episode 未参与统计。这是经过输入输出适配的零梯度更新试验，并非原始下载后直接运行。

## 离线评估

在项目根目录执行：

```bash
bash lingbot_pretrain_g1/run_offline.sh 70
```

脚本使用 GPU、牛奶数据和只读模型挂载，禁用网络，不连接机器人。报告写入新建的 `lingbot_pretrain_g1/evaluations/offline_*/report.json`。它比较预测与数据集中的 SDK 目标，也计算保持当前状态的基线。SDK 目标不是实测执行轨迹。

2026-10-13 已完成 70 个窗口的试验，覆盖 7 个验证 episode。报告见 `evaluations/offline_20261013_094421_1967078/report.json`。首步关节 MAE 为 0.368°，保持基线为 0.263°；70 段中有 62 段关节预测误差更大。首步夹爪 MAE 为 13.0 mm，保持基线为 35.2 mm；10 段的 25 步动作块出现小于 0 或大于 100 mm 的夹爪预测。预热后单次离线预测中位耗时约 384 ms。

## G1 实时只读预览

模型服务使用单独端口，不替换当前 `milk-v2-best` 服务：

```bash
export G1_POLICY_TOKEN_FILE=/tmp/g1_policy_control_20261009.token
G1_POLICY_DETACHED=1 G1_POLICY_CONTAINER=g1-policy-lingbot-pretrain-preview-20261013 \
  bash lingbot_pretrain_g1/serve_preview.sh
python3 -m lingbot_pretrain_g1.warm_service
bash g1_policy_control/run_pc.sh --mode preview --channels arm --seconds 10 \
  --server http://127.0.0.1:8092
bash g1_policy_control/run_pc.sh --mode preview --channels gripper --seconds 10 \
  --server http://127.0.0.1:8092
docker stop g1-policy-lingbot-pretrain-preview-20261013
```

新服务首次预测会编译 GPU 内核，耗时约 2 秒；`warm_service` 通过合成图像预热内核，不连接机器人。2026-10-13 完成预热后，手臂和夹爪预览各接受 26 次预测，均为零拒收、零运动接口调用；报告分别在 `lerobot_runs/model_20261013_094802_1968377/report.json` 和 `lerobot_runs/model_20261013_094825_1968592/report.json`。往返时延中位数分别为 378 ms 和 378 ms。

## 动作定义与场景响应审计

`audit_20261013/report.json` 验证了本地转换：七关节使用相对当前观测的增量，夹爪使用绝对米制开度；有效统一槽位为 0–6 和 28。归一化再还原的最大误差为 0。公开权重及官方源码中未找到原始 Galbot 归一化统计，因此当前结论适用于“原始权重＋本地 G1 标定”。右前环视作为辅助视角，未当作右腕相机；只填充左臂和夹爪状态，没有复现预训练的全身配置。

`sensitivity_stable_20261013/report.json` 和同目录 `sensitivity.png` 保存了记录画面的配对比较。三组固定采样噪声下，相同输入重复预测的误差均为 0；遮挡头部画面中的牛奶瓶使首步关节平均变化约 0.002–0.006°，改变指令约 0.002–0.007°。全画面置灰明显改变夹爪预测。它证明视觉输入影响输出，但没有证明瓶子换位置后能朝正确方向靠近。

当前现场试验服务固定采样种子，使用官方快速 MoE 路径；它存在小幅浮点重复误差。离线场景比较使用稳定的 sorted grouped-GEMM 路径。稳定路径的真机预览在 `lerobot_runs/model_20261013_104015_1993755/report.json` 中有 11 次图像超时拒收，故没有用于运动；图像时效上限未放宽。配置、归一化及模型索引有哈希绑定，修改后须重新审计。之前 70 窗口和两轮实时预览保留为旧推理配置的结果。

最终快速路径配置的 10 秒只读预览见 `lerobot_runs/model_20261013_104328_1995509/report.json`：26 次接受、零拒收、零运动接口调用，往返中位时延 383 ms。控制回归测试 58 项和最终单步专项测试 11 项通过；该记录仅包含当时的只读预览，不构成运动验收。

真实位置响应采集需保持机器人姿态和蓝箱位置不变，由人将瓶子分别摆在左、中、右三个位置。先按上面的服务启动和预热命令启动模型，再逐次摆好瓶子、运行对应命令：

```bash
bash lingbot_pretrain_g1/capture_scene.sh left
bash lingbot_pretrain_g1/capture_scene.sh center
bash lingbot_pretrain_g1/capture_scene.sh right
```

这些命令只有只读预览，将完整观测写入 `lingbot_pretrain_g1/scenes/`，没有运动指令。记录采集时的真实瓶子位置；运行标签本身不证明摆放正确。完成后停止该预览服务，释放端口 8092，再使用下面的单步脚本。

## 用户执行一次受限真机动作

此处由现场操作人运行，会发送真实运动指令。先验证手臂；手臂动作和停止结果通过后再试夹爪。当前入口没有环境避障，执行前清空手臂附近的障碍和人员，保持现场急停可用。

```bash
# 仅显示脚本范围，不连接机器人、不启动模型：
bash lingbot_pretrain_g1/run_step.sh arm --dry-run

# 真正执行：一个手臂命令，保持夹爪不动：
bash lingbot_pretrain_g1/run_step.sh arm

# 手臂动作和停止验收通过后，真正执行一个夹爪命令：
bash lingbot_pretrain_g1/run_step.sh gripper
```

脚本自动启动自己的模型容器、等待就绪并预热，结束时停止该容器。需要本地交互终端；`--execute` 授权后，预检通过即执行，不另要求输入 ARM。终端打印测量姿态、原始预测和受限目标；输入 STOP 并回车或 Ctrl+C 可停止。

本机模型 HTTP 请求（127.0.0.1、localhost、::1）强制直连，不依赖终端的 HTTP_PROXY/NO_PROXY 设置。2026-10-14 已针对错误代理导致的 502 添加回归测试。模型容器日志在停止前保存到 `service_runs/<container-name>/model_service.log`，预热失败时可检查启动原因；该阶段尚未进入机器人运动入口。

首次模型启动通常需要几十秒。等待期间会定期打印进度，连接重置会自动重试，最长等候 90 秒；看到“模型服务已就绪”后才开始 GPU 预热。Ctrl+C 会显示取消提示并清理本轮模型容器。模型预热完成不等于单步运动验证完成，仍须之后的 SDK 动作、停止及反馈日志通过验收。

单步入口用 `[1/4]`–`[4/4]` 标示容器启动、模型预热、机器人预检与控制、流程结束。GPU 预热、SSH 检查、SDK 初始化与清理等较长等待约每 5 秒打印已等待时间；SDK 等待还显示当前阶段。停稳确认会显示等待、通过或未确认的结果。等待提示仅打印状态，实际操作仍在原线程执行，既有运动预算、超时和取消规则保持有效。

每次只发送一个正常模型命令，目标预算每关节不超过 0.5°、夹爪不超过 2 mm，关节速度上限 0.05 rad/s、夹爪上限 0.02 m/s；实际位移须用反馈验收。动作段为 100 ms，结束后检查停止和停稳。预检展示的预测就是本次拟执行预测，发送前再次检查时效。未来动作块不执行；原始越界预测仍直接拒收。日志写入 `lerobot_runs/model_*/`，`single_step_validation_passed` 要求一个 SDK 确认动作、停止及停稳确认、无拒收/异常并完成 SDK 清理。

2026-10-14 用户执行的手臂单步记录为 `lerobot_runs/model_20261014_155957_2142675/report.json`：一个正常手臂目标获 SDK 确认，最大目标变化 0.172°，夹爪目标保持 50 mm；停止请求获确认，但停稳反馈过期约 849 ms，故 `single_step_validation_passed=false`。没有足够的动作后反馈确认实际位移和停稳，不能把这一轮记为成功。

该轮暴露了停稳确认遇到第一条过期反馈就提前退出的问题。现在仅针对 `FeedbackUnavailable` 在原有 2 秒确认窗口内等待新鲜反馈，过期样本不计入停稳、连续有效样本仍需三次；持续缺失和其他安全错误继续失败。61 项相关回归测试通过。修复后的真实动作尚待用户重测。当前三客户端只读反馈复查见 `lerobot_runs/model_20261014_160650_2144426/sdk_clients.json`，各 25 个反馈持续更新，零运动指令；该复查不替代停止阶段运动验收。

`g1_task_weights` 保持 `false`。普通 `--execute` 继续拒绝原始权重；单步脚本使用独立的 `--pretrained-step-experiment` 授权，只允许该固定模型和单一通道的一次动作，拒绝闭环、both 通道、扩大的预算或超时参数。单步通过也不构成抓牛奶任务成功验收。

## 2026-10-15 只读排查结论

汇总见 `diagnostics_20261015/summary.json`。本轮零运动指令，未调用机器人停止接口；临时模型服务已清理。

图像超时原因：此前右前相机取样已旧约 180 ms，再加约 421 ms 推理/处理，超过 600 ms。现在单步预检等待所有图像年龄不超过 150 ms，为推理留出 450 ms，并在解锁前有限重试过期预测。修复 IPC 错误前缀识别和观察/推理返回后的截止时间检查。原有 600 ms 图像上限、300 ms 反馈上限不变。

三客户端真实图像和 GPU 推理的只读预检 8/8 通过，7 次等待新鲜帧、0 次过期预测；预测并读取反馈后的最大图像年龄约 546 ms。报告：`lerobot_runs/model_20261015_143319_2312057/sdk_preflight.json`。该结果仅证明本次有限检查通过。

停机后 849 ms 过期反馈尚未复现：保持客户端、强制退出客户端、正常关闭客户端、推理加退出、推理加退出并暂停父进程读取约 1.4 秒，五组只读检查均通过。最后一组恢复后反馈源年龄最大约 27 ms。检查只用观察/反馈角色，未复现真实执行器发布和停止 RPC，因此尚不能确定根因或认定真实停机问题已解决。

保留原有停止顺序，新增执行器退出耗时、停止 RPC 耗时和停稳逐样本诊断。停稳仍在原有 2 秒窗口内要求三个连续新鲜、时间戳推进且低速度/低漂移的样本；过期反馈不计入通过。相关 92 项回归测试通过。修复后的真实动作、停止与停稳验收仍待现场操作人执行；抓牛奶任务尚未验证成功。

## 原始权重的 5 秒运动验证

2026-10-15 用户执行的 `lerobot_runs/model_20261015_172543_2412777/report.json` 已通过单步验收：一次手臂命令、停止确认、连续新鲜停稳反馈及 SDK 清理均通过；最大最终关节位移约 0.158°，夹爪变化 0mm。这是一轮成功记录，未确定历史偶发反馈过期的根因，也未验证抓牛奶成功。

新增独立入口 `run_motion.sh`，沿用本地原始权重与标定、固定模型身份和原有 600ms 图像/300ms 反馈时效限制。仅左臂；固定 5 秒控制窗口、0.05rad/s 速度上限、0.3rad/s² 指令加速度限制、各关节相对起点最多偏移 5°。夹爪不发送指令，实测开度偏移超过 2mm 则停止。保留 URDF 交集内缩 3°、J7 的 ±45°限制及原始越界预测拒收；不具备环境避障。

```bash
# 只显示范围；不启动容器或连接机器人：
bash lingbot_pretrain_g1/run_motion.sh execute --dry-run

# 只读：本机推理、三个只读 SDK 客户端、5秒候选动作与反馈检查：
bash lingbot_pretrain_g1/run_motion.sh preview

# 由现场操作人运行：先只读预览，通过后重新预检并自动开始真实运动：
bash lingbot_pretrain_g1/run_motion.sh execute
```

执行前保持手臂附近净空、现场急停可用；输入 STOP 并回车或 Ctrl+C 停止。脚本自动启动端口 8092 的原始 LingBot 服务并预热，结束保存日志、清理自己的容器。容器名含 `lingbot_vla_2_0-motion-5s`。启动预检要求 GPU 0 至少空闲 18000MiB，为模型加载和首次预热保留余量；这是保守的启动要求，不是测得的模型最低显存。显存不足时在启动模型和机器人之前退出。

反馈线程独立于模型 HTTP 推理运行，按源时间戳监督更新；5秒绝对截止时间和600ms新指令看门狗独立触发停止。每次新预测只执行首个100ms动作段，两次预测之间保持，不重复旧预测，也不放大预测或假设25步输出的时间间隔。因此5秒指控制窗口，不保证机械臂全程持续运动，也不保证肉眼可见幅度。旧单步脚本的运动范围及普通执行对原始权重的拒绝继续保留；新模块仅开放上述固定预算。

首次只读联调在 `lerobot_runs/model_20261015_174557_2421519/pretrained_motion_report.json` 因取帧等待触发指令看门狗提前退出。连续入口改用10ms取帧等待，避免50ms轮询反复错过相机的短暂可用窗口，时效上限不变。最终只读联调在 `lerobot_runs/model_20261015_174925_2427978/pretrained_motion_report.json` 跑满约5.005秒、接受13次新预测，零运动和夹爪命令、三客户端清理确认。真实5秒运动尚待现场执行。

报告为每次运行目录内的 `pretrained_motion_report.json`。真实运动通过要求跑满5秒、至少两次SDK确认指令、有采样位移、停止和连续停稳确认、反馈与清理无异常。`motion_observed` 的小幅采样位移判据不等于人工确认肉眼可见或平顺，报告不认证抓牛奶任务成功。