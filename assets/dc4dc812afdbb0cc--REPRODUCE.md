# S1 箱体位姿感知解耦实验：运行与产物查询

本文保留已有基线的快捷复现命令。完整的“固定 RGB-D → SAM3 + LingBot →
ROI 选箱 → FDP”操作、批次目录及人工确认步骤，请优先使用
[FDP 剥离/解耦实验使用手册](FDP_DECOUPLING_USER_GUIDE.md)。

适用基线：2026-09-07，冻结帧 `right_wrist_20260907_01`，用户确认原图右侧
开口箱 SAM index 1，LingBot 深度分支。本指南中的本机是 Ubuntu 工作站
`lsy03`，S1 是 `galbot@10.34.216.17`；不要混用两台机器的目录。

| 方式 | 实际重做的部分 | 需要什么 |
|---|---|---|
| 离线回放 | 核验完整输入/请求/响应；由保存的 FDP 原始位姿重算最终坐标 | 本机文件，无 SSH、相机或推理服务 |
| 重跑 FDP | 固定本帧 RGB、LingBot 深度、mask、K，重新请求 FDP，再归一化 | 本机文件和 FDP 服务；不需要机器人摆位 |
| 重新采集 | 新帧 → SAM3/LingBot/ROI → 重新确认目标 → FDP | 静止且摆好位的 S1、SDK、三个服务 |

离线回放不会再次运行神经网络。重跑 FDP 尚不保证逐位一致；换新帧属于新
实验，不能沿用旧帧的编号 1 或旧 mask 确认。当前中心差异仍待分析，链路
复现不代表抓取精度合格。

## 1. 本机准备

在 Ubuntu 工作站终端执行。已核验 Python 3.10.12、NumPy 1.21.5、
OpenCV 4.5.4、Requests 2.25.1、PyYAML 5.4.1，本机目前不需要重新安装。

```bash
cd /home/lsy03/文档/ChatGPT/S1/experiments/20260903_fdp_baseline

FDP_CASE=cases/right_wrist_20260907_01_lingbot_operator1
FDP_REFERENCE=outputs/fdp_20260907_01_lingbot_operator1
FDP_TAG=$(date +%Y%m%d_%H%M%S_%N)

python3 scripts/verify_case.py --case-dir "$FDP_CASE"
sha256sum --quiet -c ASSET_MANIFEST_20260907.sha256
```

第一条校验应包含 `ok: true`、`hashes_verified: true`；第二条成功时不输出。
SHA 清单针对已归档的 9 月 7 日数据和当时列出的代码文件，不是服务端版本
或权重证明，也不是后续新增产物的清单。旧 `DEPLOYMENT_MANIFEST.sha256`
是早先 S1 部署清单，不用于判断本机新增人工确认代码是否正确。

所有输出目录拒绝覆盖；每次重新执行先生成新的 `FDP_TAG`。

## 2. 纯离线复现最终位姿（推荐先运行）

接着在同一终端执行：

```bash
FDP_OFFLINE_OUT="outputs/offline_fdp_${FDP_TAG}"

python3 scripts/replay_saved_fdp_result.py \
  --case-dir "$FDP_CASE" \
  --reference-run-dir "$FDP_REFERENCE" \
  --output-dir "$FDP_OFFLINE_OUT"

cat "$FDP_OFFLINE_OUT/replay_result.json"
```

预期：`ok: true`、`request_payload_matches: true`、
`all_matrices_exactly_equal: true`、三项 delta 为 0。
它会检查案例文件哈希、原始响应/请求/归一化结果哈希，以及从冻结输入重建的
请求是否匹配归档；不调用任何网络服务或机器人 SDK。
本机已实际验证通过，结果保存于 `outputs/offline_fdp_replay_guide_validation_20260907/`。

可另行复现 LingBot 分支的 ROI（使用已保存的 SAM3/LingBot 返回）：

```bash
python3 scripts/replay_roi_case.py \
  --case-dir cases/right_wrist_20260907_01_lingbot \
  --output-dir "outputs/offline_roi_lingbot_${FDP_TAG}" \
  --perception-root /home/lsy03/GalbotS1文件/260611_sjtu_workbin_movement/migrate_back/g1_workbin_perception/src
```

本机同系源码四项哈希与该帧记录一致；该分支已验证 index、中心、yaw、mask
完全一致。raw 分支在 S1 原环境中完全一致，但本机重算出现
`1.1920928955078125e-7 m` 中心差（约 0.000119 mm），选择/yaw/mask 一致。
当前回放脚本以 `1e-9 m` 为阈值，因此本机 raw 回放返回 `ok:false`、退出码 2。
该差异与 float32 舍入量级一致，具体数值来源尚未定位；未放宽阈值或改写结果。
保留诊断目录 `outputs/offline_roi_guide_validation_20260907_raw/`。

## 3. 用同一输入重新调用 FDP

这一步会把图像、LingBot 深度、最终 mask、K 和 mesh 路径发送到实验室
`http://10.34.216.13:7876/first_frame_track`。需要服务正常运行、服务端 mesh
路径可用；无需 SSH 到 S1，也无需移动机器人。下面命令带 `--call-service`，
执行它就会实际发起一次推理。新结果与历史结果的差异应查看，不能预先假定为零。

```bash
FDP_TAG=$(date +%Y%m%d_%H%M%S_%N)
FDP_NEW_OUT="outputs/fdp_repeat_${FDP_TAG}"

env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  NO_PROXY=10.34.216.0/24,localhost,127.0.0.1 \
  no_proxy=10.34.216.0/24,localhost,127.0.0.1 \
  python3 scripts/replay_fdp_case.py \
  --case-dir "$FDP_CASE" \
  --output-dir "$FDP_NEW_OUT" \
  --service-url http://10.34.216.13:7876 \
  --timeout-s 180 \
  --call-service
```

成功时 `run_result.json` 中为 `status: fdp_response_normalized`。随后比较：

```bash
python3 scripts/compare_results.py \
  "$FDP_REFERENCE/normalized_pose.json" \
  "$FDP_NEW_OUT/normalized_pose.json"

xdg-open "$FDP_NEW_OUT/foundationpose_vis.png"
cat "$FDP_NEW_OUT/run_result.json"
```

比较程序的 `ok:true` 只表示比较成功执行；它没有设定精度合格阈值，必须看
`delta.translation_l2_m`、`delta.rotation_geodesic_deg` 等实际数值。
去掉 `--call-service` 可以只准备请求，但仍须使用新的输出目录。
若 HTTP 超时/失败，保留失败目录，不覆盖它；这也不能算位姿推理成功。

## 4. 查询这一次已经生成的产物

所有下列相对路径均位于本机实验目录，图像保持原始倒置方向。

| 产物 | 路径 |
|---|---|
| 原始 RGB | `captures/right_wrist_20260907_01/rgb.png` |
| 原始深度（米，NumPy 数组） | `captures/right_wrist_20260907_01/depth_raw_m.npy` |
| 时间戳、状态、TF 检查 | `captures/right_wrist_20260907_01/capture_meta.json` |
| 全部 SAM 候选叠加图 | `outputs/live_perception_20260907_01/common/sam_candidates_overlay.png` |
| LingBot 补全深度（米） | `outputs/live_perception_20260907_01/common/depth_lingbot_m.npy` |
| 最终 ROI 叠加图 | `outputs/live_perception_20260907_01/lingbot/roi_mask_overlay.png` |
| ROI 坐标、候选与门禁 | `outputs/live_perception_20260907_01/lingbot/roi_result.json` |
| raw/LingBot 对比 | `outputs/live_perception_20260907_01/raw_vs_lingbot.json` |
| 人工确认及输入哈希 | `cases/right_wrist_20260907_01_lingbot_operator1/reference/operator_confirmation.json` |
| FDP 三维框叠加图 | `outputs/fdp_20260907_01_lingbot_operator1/foundationpose_vis.png` |
| 最终位姿与全部变换 | `outputs/fdp_20260907_01_lingbot_operator1/normalized_pose.json` |
| 调用是否成功、耗时 | `outputs/fdp_20260907_01_lingbot_operator1/run_result.json` |
| 完整发送请求 / 完整服务返回 | 同目录 `request_payload.json.gz` / `raw_response.json` |
| 离线复核及 ROI/FDP 差异 | 同目录 `offline_verification.json` |

常用查看命令：

```bash
xdg-open captures/right_wrist_20260907_01/rgb.png
xdg-open outputs/live_perception_20260907_01/common/sam_candidates_overlay.png
xdg-open outputs/live_perception_20260907_01/lingbot/roi_mask_overlay.png
xdg-open "$FDP_REFERENCE/foundationpose_vis.png"
cat "$FDP_REFERENCE/run_result.json"

python3 - <<'PY'
import json
from pathlib import Path
p = Path('outputs/fdp_20260907_01_lingbot_operator1/normalized_pose.json')
r = json.loads(p.read_text())
print('T_base_link_from_4317_semantic:')
for row in r['matrices']['T_base_link_from_4317_semantic']:
    print(' '.join(f'{x: .8f}' for x in row))
PY
```

`.npy` 用 `numpy.load()` 读取，不能按普通 PNG 打开。`raw_response.json`
含大段 base64 图像，日常先看 `run_result.json` 与 `normalized_pose.json`。
当前 137.3 mm ROI/FDP XY 中心差仍待验证，不要把 `ok:true` 当作抓取授权。

## 5. 重新拍一帧并运行 SAM3/LingBot

这是新数据实验，先在现场完成摆位并保持底盘、双臂、腰部和箱体静止。
本节脚本仅读取右腕图像、深度、标定和状态，不发送运动，不运行 Mode 00。
摆位若涉及底盘、手臂或腰部，须另行评估运动空间、碰撞、速度和急停条件，
不属于下面命令的操作范围。

如果当前 SSH 复用连接还在，本机打开 S1 shell：

```bash
ssh -S /tmp/s1_fdp_mux_20260907 -O check galbot@10.34.216.17
ssh -S /tmp/s1_fdp_mux_20260907 galbot@10.34.216.17
```

然后在 **S1 终端** 执行，确保 `control.lock` 未被其他任务占用：

```bash
cd /home/galbot/Lsy03/fdp_baseline
FDP_CAPTURE_ID="right_wrist_$(date +%Y%m%d_%H%M%S_%N)"

/home/galbot/ie_lab/bin/s1-python scripts/capture_right_wrist_rgbd_once.py \
  --output-dir "captures/$FDP_CAPTURE_ID" \
  --settle-s 3 --timeout-s 15 --acknowledge-readonly-live-s1
```

先检查采集命令成功及 `capture_result.json` 中 `ok:true`。下一条命令会向
Thor SAM3/LingBot 发送本次新数据，执行前确认这些地址仍是预期服务：

```bash
python3 scripts/build_fresh_fdp_case.py \
  --capture-dir "captures/$FDP_CAPTURE_ID" \
  --output-dir "outputs/perception_$FDP_CAPTURE_ID" \
  --case-root cases --depth-mode both \
  --site-config /home/galbot/ie_lab/projects/dual_arm_v5/workspace/s1_sjtu_0806/config/site.production.yaml \
  --perception-root /home/galbot/ie_lab/projects/dual_arm_v5/workspace/s1_sjtu_0806/vendor/g1_workbin_perception \
  --mesh /home/galbot/ie_lab/projects/dual_arm_v5/workspace/s1_sjtu_0806/assets/mesh/EU4322_midcut_target175mm.obj \
  --timeout-s 180

python3 scripts/render_live_diagnostics.py \
  --capture-dir "captures/$FDP_CAPTURE_ID" \
  --perception-dir "outputs/perception_$FDP_CAPTURE_ID"

cat "outputs/perception_$FDP_CAPTURE_ID/result.json"
```

这一步不会调用 FDP。若为多候选，`ready_for_fdp=false` 是正常阻止继续的
结果，不是把 mask 生成失败。应查看新图再确定新目标；禁止直接把旧帧
index 1 或确认文件复制过来。本轮新增的人工确认脚本仅在本机，尚未部署至
S1；若需要新一帧的人工确认流程，先把新案例与诊断图复制回本机再处理。

## 保存与搬移

`captures/`、`cases/`、`outputs/` 都是本地实验资产，已被 `.gitignore` 排除。
只复制 Git 仓库代码不会带走这些数据。要到另一台机器复现，至少携带完整的
`cases/right_wrist_20260907_01_lingbot_operator1/` 和
`outputs/fdp_20260907_01_lingbot_operator1/`，以及当前 `fdp_baseline/` 和
`scripts/`；要复现全部 ROI 则还需两条原始案例、对应 vendor 源码和依赖。
运行时重新 `verify_case.py`，不要更改输入文件或删掉父 manifest/确认记录。