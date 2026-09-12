# 2026-09-07 S1 箱体位姿感知解耦：首个新帧 FDP 基线

## 目的与结论边界

在用户人工摆位并确认机器人静止后，独立完成右腕单帧采集、SAM3、
raw/LingBot ROI 对比、人工指定目标、一次 FDP 推理和语义坐标归一化。
本次跑通至 `T_base_link_from_4317_semantic`，保存了完整请求与响应。
它是新冻结输入的基线，不是历史 Mode 00 服务调用的逐字节复现。

没有执行定位、导航、双臂/腰部/夹爪动作，没有生成抓取目标。
当前仅验证输入输出合同与回放，未建立位姿真值、重复推理稳定性或抓取精度。

## 授权与执行位置

- 用户建立 SSH socket `/tmp/s1_fdp_mux_20260907`，明确确认已摆好并静止。
- S1 端采集只调用已核验的 SDK getter/lifecycle 白名单，持有共享
  `/home/galbot/ie_lab/control.lock`，采集结束销毁相机对象并释放锁。
  采集前没有运行中的 Docker 容器，未发现匹配的一键/采集脚本进程。
- 初次 SAM3/LingBot 命令被自动审批拦截，未执行。用户随后明确授权向
  `10.34.216.11:7861` 发送 RGB、向 `10.34.216.11:7865` 发送 RGB-D/K；
  配置字段核验一致后才执行，各调用一次。
- 用户看过原始方向的 ROI 叠加图后明确选择：“图中右侧绿色箱：编号 1”。
- 用户另行明确授权向 `http://10.34.216.13:7876/first_frame_track`
  发送本帧 RGB、LingBot 深度、最终 mask、K 和 mesh 路径，执行一次 FDP。
- 采集与 SAM3/LingBot/ROI 在 S1 `/home/galbot/Lsy03/fdp_baseline` 执行。
  完整产物复制至本仓库实验目录；人工确认案例、请求准备、FDP 客户端和
  归一化在本机执行。未修改生产代码或部署新增人工确认代码至 S1。

## 采集与感知结果

冻结采集 ID：`right_wrist_20260907_01`。RGB、深度均为 1280×720；
RGB/深度时间差、TF/深度时间差均为 0 ns。原始深度有效率 86.5964%。
外参与捕获 TF 差约 0.0198 mm、0.00250°；本地复制的五项文件哈希全部通过。
图像倒置，处理期间未旋转 RGB、深度或改变 K。

SAM3 返回 10 个 mask。以下 ROI center 是原算法的顶面中心，不能把其 Z
直接与 FDP 箱体中心 Z 比较。

| 指标 | raw | LingBot |
|---|---:|---:|
| H4 候选 SAM index | 1, 2 | 1, 2 |
| 默认选择 | 1 | 1 |
| ROI 顶面中心 base_link (m) | [1.260258, 0.210449, 0.607607] | [1.255430, 0.246426, 0.599353] |
| ROI yaw (deg) | 90.0 | 90.0 |
| 最终 mask 像素数 | 32,068 | 31,948 |
| 自动严格唯一性 | false | false |

两分支中心相差 37.2254 mm，yaw 对称差 0°，mask IoU 0.936768。
LingBot 报告全图 921,600 个有效点。两条纯文件 ROI 回放的选择相同、
中心/yaw 差均为 0、mask IoU 均为 1；没有再次调用服务或 SDK。

## 人工确认案例

原始 `right_wrist_20260907_01_raw` 和 `right_wrist_20260907_01_lingbot`
案例均保留 `ready_for_fdp=false`。

另建 `right_wrist_20260907_01_lingbot_operator1`，保留原始候选报告、父
manifest 和输入文件；记录用户原话、SAM index 1、RGB/mask 等输入哈希。
`strict_unique_4317_h4` 仍为 false；通过单独的
`operator_confirmed_frozen_target` 策略使本帧 `ready_for_fdp=true`。
此确认不传播到其他帧，不证明自动目标身份锁，也不授权运动。

新增 `confirm_frozen_target.py`，并在 `case.py` 中校验确认记录、父 manifest、
七项输入哈希和目标编号。15 项离线测试通过，包括更换深度后即便更新
manifest 哈希仍拒绝、确认编号与 materialized mask 不一致时拒绝、源案例不变。

## FDP 返回与离线核验

- HTTP 200；客户端请求耗时约 1.145 s，包含通信和服务处理，非纯模型计时。
- 输出标签：`new_result_from_frozen_exact_input`。
- mesh 服务路径：`/opt/s1-sjtu/assets/mesh/EU4322_midcut_target175mm.obj`。
  本地 mesh 副本哈希已锁定；本轮未独立核验服务端 mesh 文件哈希、模型权重或版本。
- 原始位姿是合法刚体变换，旋转行列式约 1.000000085。
- 语义高度轴与 base_link +Z 点积约 0.998095，满足现有 0.85 门限。
- 不需要 180° 翻转。最终语义中心为
  `[1.392452018, 0.255328013, 0.505903426] m`。
- 按 `R=Rz(yaw) Ry(pitch) Rx(roll)` 分解，roll/pitch/yaw 约
  `[3.279112, -1.327797, 91.288512] deg`。
- 发送的解压请求 JSON 与事先准备的请求相等；由保存的 raw response 和
  捕获 TF 重算的全部归一化矩阵与归档结果逐元素一致。
- 服务叠加框覆盖原图右侧所选箱体，目视没有明显选到左箱；这不是精度真值。

### 502 诊断与直连重试

首次从本机调用时，FDP 返回空 body 的 HTTP `502 Bad Gateway`。失败目录只
保存了 `request_payload.json.gz` 和 `request_summary.json`；案例校验已经
通过，未生成位姿结果。诊断发现本机环境存在 `HTTP_PROXY/HTTPS_PROXY`
指向 `192.168.42.129:7890`；默认 curl 路径得到同样 502，而
`curl --noproxy '*'` 访问同一主机的 `/health` 返回 HTTP 200，服务报告
`local_fdp_4090`、NVIDIA RTX 4090、`import_error=null`。因此 502 属于
代理路径故障，不是本帧输入门禁失败。

使用显式移除代理变量的同一案例重试后，FDP 返回 HTTP 200，耗时约 0.974 s。
与此前成功响应比较：`translation_l2_m=0`、`rotation_geodesic_deg=0`、
`matrix_max_abs=0`。重试产物位于
`outputs/fdp_diag_retry_full_20260907_110222_165338253_111518_743241865/`。
后续访问 `10.34.216.0/24` 内网服务应显式绕过代理。

### 未解决的几何差异

FDP 与 LingBot ROI 的 XY 中心相差 **137.311 mm**，与 raw ROI 相差
139.604 mm；yaw 差约 1.2885°。用 FDP 语义高度轴加半高 87.5 mm 后，
FDP 顶面中心 Z 比 LingBot ROI 顶面 Z 低约 6.116 mm。

XY 差异明显大于此前 8 个历史成功观测的 ROI/FDP 差异（最大约 26.5 mm）。
它可能涉及本次视角下 ROI 可见表面与完整箱体中心的差别、深度或 FDP 拟合，
原因均 **待验证**。ROI 与 FDP 都不是真值，不能把 137 mm 直接称为 FDP
误差，更不能据 HTTP 成功判定抓取精度通过。下一步应先核对两者中心定义、
可见几何、模型和深度一致性，再设计有参考测量的精度验证。

## 重现命令

以下是本次已执行记录，不构成后续自动采集或运动授权。S1 端工作目录为
`/home/galbot/Lsy03/fdp_baseline`：

```bash
/home/galbot/ie_lab/bin/s1-python scripts/capture_right_wrist_rgbd_once.py \
  --output-dir captures/right_wrist_20260907_01 --settle-s 3 --timeout-s 15 \
  --acknowledge-readonly-live-s1

python3 scripts/build_fresh_fdp_case.py \
  --capture-dir captures/right_wrist_20260907_01 \
  --output-dir outputs/live_perception_20260907_01 --case-root cases --depth-mode both \
  --site-config /home/galbot/ie_lab/projects/dual_arm_v5/workspace/s1_sjtu_0806/config/site.production.yaml \
  --perception-root /home/galbot/ie_lab/projects/dual_arm_v5/workspace/s1_sjtu_0806/vendor/g1_workbin_perception \
  --mesh /home/galbot/ie_lab/projects/dual_arm_v5/workspace/s1_sjtu_0806/assets/mesh/EU4322_midcut_target175mm.obj \
  --timeout-s 180
```

两个 mode 分别使用 `replay_roi_case.py --case-dir cases/right_wrist_20260907_01_<mode>`，
输出至 `outputs/offline_replay_20260907_01_<mode>`，perception-root 同上。

本机实验目录下：

```bash
python3 scripts/confirm_frozen_target.py \
  --source-case-dir cases/right_wrist_20260907_01_lingbot \
  --output-case-dir cases/right_wrist_20260907_01_lingbot_operator1 --sam-index 1 \
  --expected-rgb-sha256 eb045825a3ec3a497d0695a3f21722bfd67bdf07cf8f9d2dde0bb0b1f007d794 \
  --expected-mask-sha256 4f624276282eb32407018855c6fc1b2a8baf77abf23d81fb5b42d9fe238cdc07 \
  --operator-statement '用户在本任务中明确选择：图中右侧绿色箱：编号 1；仅用于本帧 FDP 感知基线。'

python3 scripts/replay_fdp_case.py \
  --case-dir cases/right_wrist_20260907_01_lingbot_operator1 \
  --output-dir outputs/prepare_20260907_01_lingbot_operator1

python3 scripts/replay_fdp_case.py \
  --case-dir cases/right_wrist_20260907_01_lingbot_operator1 \
  --output-dir outputs/fdp_20260907_01_lingbot_operator1 \
  --service-url http://10.34.216.13:7876 --timeout-s 180 --call-service

python3 -m unittest discover -s tests -v
```

## 保存位置与证据

本目录的 `captures/`、`cases/`、`outputs/` 保留全部数据但不纳入 Git；
相对路径和 SHA-256 清单见 `ASSET_MANIFEST_20260907.sha256`。
最终输出目录为 `outputs/fdp_20260907_01_lingbot_operator1/`，包含
`request_payload.json.gz`、`raw_response.json`、`foundationpose_vis.png`、
`normalized_pose.json`、`run_result.json` 和 `offline_verification.json`。

- 原始 RGB SHA-256：`eb045825a3ec3a497d0695a3f21722bfd67bdf07cf8f9d2dde0bb0b1f007d794`。
- LingBot 最终 mask SHA-256：`4f624276282eb32407018855c6fc1b2a8baf77abf23d81fb5b42d9fe238cdc07`。
- FDP raw response SHA-256：`1b205bcc9cde907c636e9713b49fabdccfbb6e3f4126914fa6d20cf83a1d958c`。
- 归一化输出 SHA-256：`556a6c138ed6dcc60b440a9da4c457f7a262744947c53e2e54de7d1ece7f7059`。