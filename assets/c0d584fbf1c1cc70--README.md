# 一键拆垛FDP接口与Orin统一适配 — 2026-09-30

本目录是独立适配实现，不修改 `/home/galbot/ie_lab/projects/s1_continuous_destack`、4090生产源码或固定Orin镜像。未执行dev-scenario、未调用SDK/相机/运动。新HTTP服务验证后退出，不是已经切换生产后端。

## 查明的实际调用链

`deploy/run.sh dev-scenario mode00 lsycheck_h4_20260915_note01`：最后一个参数是RUN_ID，不是FDP配置名。当前源码冻结后执行mode00场景，属于可运动入口。本次只读检查，没有运行该命令。

当前mode00.yaml引用`config/services/lab.yaml`，`fdp.url=http://10.34.216.13:7876`，超时180秒，可视化开启。客户端为`FoundationPoseHttpClient.estimate_first_frame`，HTTP POST `/first_frame_track`。controller采用host网络。检查到项目HEAD为0904406d0a8b35cbee2a63d7d47ed1de34acbc85；历史特定RUN_ID的配置快照未回放，本报告描述当前调用链。

请求字段：

```json
{
  "mesh_path": "EU4322_midcut_target175mm.obj",
  "mesh_model": "4317",
  "mesh_sha256": "模型文件SHA256",
  "capture_id": "当前帧ID",
  "identity_key": "目标身份",
  "source_roi_index": 9,
  "rgb_jpg_base64": "JPEG字节的base64",
  "depth_png_base64": "uint16毫米深度PNG的base64",
  "mask_png_base64": "二值mask PNG的base64",
  "K": [[911.9,0,648.1],[0,911.7,360.4],[0,0,1]],
  "depth_scale": 1000.0,
  "base_link_from_camera": "4×4采集时刻外参矩阵",
  "transform_timestamp_ns": 1,
  "return_vis": true,
  "fdp_semantic_axes": {"length":"+raw_axis_2","width":"+raw_axis_1","height":"-raw_axis_0"},
  "chosen_mask_sha256": "mask PNG字节SHA256",
  "request_sha256": "除本字段外规范化JSON的SHA256"
}
```

上例是字段说明，base_link_from_camera必须传实际4×4数值数组。客户端头部发送`x-api-key`；当前4090 wrapper路由未校验该头。本适配支持可选环境变量密钥校验，不打印密钥。

4090响应主字段为`ok / mesh_path / elapsed_s / pose / vis_png_base64`。**pose是相机坐标下FDP有向包围框中心位姿，不是base_link或箱体语义轴位姿。** 客户端自行做semantic轴变换和采集时刻TF转换。新服务保持这个含义；新增算法名、register_s和诊断信息，不重复转换语义轴。

## 与原Orin实验的区别

|项目|一键脚本当前4090调用|此前Orin实验runner|新Orin适配|
|---|---|---|---|
|入口|HTTP JSON|固定目录文件+Python脚本|相同HTTP JSON|
|RGB|JPEG|PNG无损|JPEG/PNG均支持，统一解码RGB|
|深度|当前采集原始深度转毫米PNG|预先生成的LingBot深度，毫米量化|调用者提供uint16深度，内部统一米制float32|
|模型路径|客户端传basename，服务器解析|/data固定模型路径|部署时固定模型及SHA，basename映射；错误模型拒绝|
|外参|随请求发送，客户端用于结果转换|从base_from_camera.npy读|随请求解码；A4/A4-64先验必须有|
|返回|中心pose in camera|原mesh pose和base语义pose|中心pose in camera，保持客户端约定|
|候选算法|生产默认252候选|由实验脚本mode控制|启动参数选择A0/A1/A2/A3/A4/A4-64|
|前端/数据集路径|调用方管理|runner含帧清单和路径|不进入算法后端|

当前一键路径是`latest_frame → identity-selected mask → estimate_first_frame(frame, mask)`。frame.depth来自采集原始深度，没有在这段FDP调用链中替换成LingBot结果；8040可参与候选/目标处理，不能据此认定FDP收到的是LingBot深度。28帧离线精度数字基于LingBot+PNG，不能直接外推到raw+JPEG在线流程。

## 解耦边界与可插拔

```text
调用方（当前一键客户端 / 离线测试 / 其他应用）
        ↓ 相同 POST /first_frame_track
server.py：HTTP、可选认证、状态码
        ↓
codec.py：图像解码、单位、维度、模型/请求/mask哈希、TF校验
        ↓ Observation（RGB、depth_m、mask、K、base_from_camera）
service.py：串行调用、统一响应、可视化
        ↓ PoseBackend.estimate(observation) → Estimate
registry.py → A0 / A1 / A2 / A3 / A4 / A4-64 / 部署指定factory
```

- 算法层不认识HTTP、base64、case目录、D12或ROI序号；模型与算法配置在启动时注入。
- 外部层不依赖252或64个候选的细节。新算法实现`PoseBackend`契约，可用`--backend-factory package.module:create`挂接；factory仅可信启动配置可设，请求不能指定Python代码。
- 插件输出必须统一为**camera_from_fdp_oriented_box_center**、米制4×4刚体矩阵；语义轴不同的算法需在自己的适配器里转换。不是给任意算法改个名字就兼容；当前未实现/验证ICP插件。
- **每进程一个算法实例，重启切换**。原优化代码会修改上游模块级hook，因此不支持同进程多算法热切换。单实例加锁串行，不宣称并发吞吐能力。
- 当前首帧估计无跨帧身份跟踪状态；`/next_frame_track`、`/reset`、`/warmup`未实现，明确返回501，不冒充4090完整API。mode00原客户端实际只用首帧接口与健康检查。
- 仍限定已审核4317模型及坐标合同；数据解耦不等于模型、相机、TF等物理依赖可以省略。A4软竖直先验要求base Z/箱体姿态满足已测使用条件。

## 部署与切换方式（未修改生产）

S1独立验证目录：`/home/galbot/Lsy03/fdp_unified_api_20260930`。

```bash
cd /home/galbot/Lsy03/fdp_unified_api_20260930
bash run_service.sh A4
# 或停止当前服务后选择 A4-64 / A0 / A1 / A2 / A3
```

脚本使用固定原镜像sha256:55ddb6d387b52fc8d4e6c50461faa6976598310d59935b6f247f43c43a7e0a98，将独立代码和模型只读挂载，6CPU/8GiB，监听127.0.0.1:17876。验证脚本有30分钟超时，不是常驻生产部署。模型启动一次，后续请求复用权重。

已准备`config/lab_orin.example.yaml`：保留其他服务，只把`fdp.url`与`health.fdp`改成127.0.0.1:17876。当前一键controller为host网络，因此此地址可达；如果以后采用bridge网络则需调整网络寻址。

该示例**尚未替换生产lab.yaml**。未来切换需使用新的配置快照/RUN_ID，不能修改已有任务的冻结配置冒充原任务；既有目标身份、几何和运动机器门保持原逻辑。仅HTTP请求/响应兼容不等于完整机器人作业验收。

## 复现验证

本地：`python3 tests/test_contract.py`，使用原一键客户端源码快照通过真实本机HTTP测试。包括RGB通道、深度单位、相机pose不重复转换、外参/模型/哈希错误拒绝、认证、可视化与不支持的跟踪拒绝。

S1：`smoke_on_s1.py`只读冻结D12左侧数据，先以无损PNG比较归档A4/A4-64 pose，再用项目原FoundationPoseHttpClient发送JPEG请求。测试启动独立容器，结束停止本任务容器，不执行场景、SDK或相机。验证结果见`received/output/results.json`及REPORT.md。

计时分开报告register_s、服务处理elapsed_s和客户端HTTP墙钟；不能用0.598秒历史register时间代替HTTP端到端耗时。

同事调用手册：[Orin FDP 接口以及调用方式.md](<Orin FDP 接口以及调用方式.md>)，附[Python调用示例](examples/call_fdp.py)。