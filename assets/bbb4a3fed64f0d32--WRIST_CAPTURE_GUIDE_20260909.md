# 左右腕 RGB-D 冻结采集与位姿说明（2026-09-09）

## 修改范围与验证状态

左右臂现在各有一个清晰的采集入口：

- `scripts/capture_left_wrist_rgbd_once.py`：固定左腕；
- `scripts/capture_right_wrist_rgbd_once.py`：缺省右腕，并保留旧的
  `--camera-arm left|right` 兼容参数。

两个入口共用 `capture_wrist_once()`；不复制底层采集逻辑。选择会同时切换
RGB、深度、K、外参查询及期望的 optical frame，元数据和结果保存相机侧别。
后续 `fresh_case.py` 支持左右腕，并检查相机侧别与 RGB/depth/TF 坐标系一致；
新案例来源描述使用实际侧别，旧数据不改写。

本次仅本机编辑，未连接机器人、未部署、未执行实时采集或服务推理。
本地官方 SDK 快照的 SensorType 定义与 example5 示例支持左腕枚举和
`left_arm_camera_color_optical_frame` 名称；实际左腕流、对齐与标定仍待验证。

## 更新后在 S1 使用

以下命令仅适用于将本次三个运行文件同步至 S1 的
`/home/galbot/Lsy03/fdp_baseline` 后：

- `scripts/capture_left_wrist_rgbd_once.py`
- `scripts/capture_right_wrist_rgbd_once.py`
- `fdp_baseline/live_capture.py`
- `fdp_baseline/fresh_case.py`

```bash
cd /home/galbot/Lsy03/fdp_baseline && \
FDP_CAPTURE_ID="left_wrist_H01_$(date +%Y%m%d_%H%M%S_%N)" && \
/home/galbot/ie_lab/bin/s1-python scripts/capture_left_wrist_rgbd_once.py \
  --output-dir "captures/$FDP_CAPTURE_ID" \
  --settle-s 3 \
  --timeout-s 15 \
  --acknowledge-readonly-live-s1 && \
python3 -m json.tool "captures/$FDP_CAPTURE_ID/capture_result.json"
```

右腕使用下面的独立入口：

```bash
FDP_CAPTURE_ID="right_wrist_H01_$(date +%Y%m%d_%H%M%S_%N)" && \
/home/galbot/ie_lab/bin/s1-python scripts/capture_right_wrist_rgbd_once.py \
  --output-dir "captures/$FDP_CAPTURE_ID" \
  --settle-s 3 \
  --timeout-s 15 \
  --acknowledge-readonly-live-s1
```

目录名只做标签；真正控制相机的是入口脚本（或旧右腕入口的
`--camera-arm` 参数）。H01 等留出集编号仅在
符合实验划分时使用。选择原装左/右相机无需重建采集算法；若把同一相机实际
拆装到另一只臂，必须重新确认设备映射和手眼外参，不能只改参数。

采集脚本不会移动左臂、右臂、夹爪、升降或底盘。现场摆位完成并静止后使用；
摆位的碰撞净空、速度和急停由现场操作员确认。采集本身不包含 FDP 物体位姿。

## 原脚本已保存的内容

| 文件/字段 | 内容及作用 |
|---|---|
| rgb.png | RGB 图像 |
| depth_raw_m.npy | 对齐深度，已换算为米 |
| intrinsics.npy | 本帧相机 3×3 K |
| base_from_camera.npy | 深度时间戳查询得到的 4×4 T_base_link_from_camera |
| capture_meta.json | 侧别、帧名、图像/TF 时间戳、TF 质量、全身状态、只读调用记录 |
| capture_result.json | 成功标记、文件 SHA-256、深度质量与调用记录 |

使用有效深度 z 和对应 K，将像素 (u,v) 反投影为相机坐标：
`p_camera = z * inverse(K) @ [u, v, 1]`。
再用该帧矩阵 `p_base = R @ p_camera + t` 转成 base_link 点云。
同一静止基座下的左右相机点云可按各自变换表达在同一 base_link；融合质量
仍受深度、标定误差和场景变化影响。基座跨帧移动后还需要同期可靠的
`T_map_from_base_link` 等公共坐标变换，现有采集不能据此保证地图级融合。

相机 TF 是按深度时间戳请求的，原门禁允许 RGB/depth 差不超过 50 ms、
返回 TF/depth 差不超过 100 ms；不是硬件严格同步保证。
`capture_time_joint_state` 保存 17 个 whole_body_joint 值和 SDK base_state
（允许为空），以及本机读取时间、与深度时间差。它在取得图像后读取，
不是按图像时间插值的状态；`whole_body_joint_rad` 是原代码字段名，不能仅凭
该名称推断所有关节的单位。base_state 的存在也不等于已验证的 map 变换。
原脚本没有图像最大年龄门禁，静止等待本身也不证明图像一定是最新帧。

## 本机验证

命令：`python3 -m unittest discover -s experiments/20260903_fdp_baseline/tests -v`

结果：19 项通过，包含左右传感器/K/TF 选择、保存与加载、旧入口兼容、错误
侧别/帧名拒绝、只读接口门禁。另对本机 D01～D12 历史采集执行加载兼容检查。
这些是离线验证，不是左腕真机验证或标定精度证明。