# Orin FDP 接口以及调用方式

**版本：2026-09-30 · 面向调用方和算法开发同事**

本文对应独立Orin服务`fdp_unified_api_20260930`。它兼容当前一键拆垛项目使用的FDP首帧HTTP接口。A4与A4-64已通过冻结帧及原一键客户端测试；生产一键脚本仍使用4090，尚未切换到本服务。

服务只接收图像和参数并返回位姿，不采集相机、不调用机器人SDK、不控制运动。不要通过运行`dev-scenario`来测试接口，该命令会进入可运动的拆垛流程。

## 当前默认算法与选型说明

本文描述的是统一HTTP接口，不绑定单一算法。启动脚本默认加载 **A4（64→16→16）**，也是文中推荐命令`bash run_service.sh A4`所使用的后端；实际已加载算法可从`GET /health`的`backend`字段确认。默认配置不代表服务此刻正在运行。

A4和A4-64使用同一套FoundationPose Score/Refiner权重，不是重新训练的不同模型；区别主要在候选筛选与保留策略。均使用120×120、3轮精修、关闭matmul TF32，保留cuDNN TF32和AMP。A4保留64→16→16，A4-64保留64→64→64。

下面是已修正4帧mask并将D12切换为左侧ROI9后的28帧合并结果：

|后端|register中位耗时|相对4090中心差中位/最大|中心≤10mm且逐轴角度≤4°|
|---|---:|---:|---:|
|**A4（默认）**|**0.598秒**|0.229 / 5.144mm|28/28|
|A4-64|0.851秒|0.184 / 5.199mm|28/28|

按当前“尽量快，同时差距在10mm/4°以内”的要求，**A4是已测FDP方案中更合适的默认折中**。不能称它为所有场景绝对精度最优：A4-64中心差中位数更小，部分角度指标也更接近4090，但耗时更长，最大中心差并未更小。4090仅为对照，不是绝对真值。

上述为LingBot+PNG冻结数据、多批次合并的register统计，不等于HTTP端到端耗时，也不能直接外推到raw+JPEG实时数据。需要更多候选时，停止当前实例后执行`bash run_service.sh A4-64`，外部请求格式不变。

## 1. 地址与启动

| 项目 | 地址或路径 |
|---|---|
| Orin服务所在机器 | S1，`10.34.216.17` |
| S1上的独立服务目录 | `/home/galbot/Lsy03/fdp_unified_api_20260930` |
| Orin调用地址 | `http://127.0.0.1:17876`，默认仅S1本机可访问 |
| 当前4090生产接口 | `http://10.34.216.13:7876` |
| 健康检查 | `GET /health` |
| 首帧位姿估计 | `POST /first_frame_track` |

在S1终端启动：

```bash
cd /home/galbot/Lsy03/fdp_unified_api_20260930
bash run_service.sh A4
```

保持终端运行，等待日志输出`"ready": true`，再用另一个终端调用。模型首次初始化可能较慢，不要在服务尚未就绪时重复启动容器。

算法可选`A0 / A1 / A2 / A3 / A4 / A4-64`，默认A4。一个服务进程只加载一种算法，换算法需要停止原服务再启动；算法名称不放在HTTP请求里。

停止A4服务：

```bash
docker stop codex-fdp-api-A4
```

然后可运行`bash run_service.sh A4-64`。对应容器名为`codex-fdp-api-A4-64`。

**当前启动脚本是验证用途，有1800秒（30分钟）超时，不是开机自启或长期常驻服务。** 服务结束后容器自动删除，代码与输入文件保留。不要假定本说明交付时服务已经运行。

从另一台电脑访问时，使用已获授权的SSH账号建立转发：

```bash
ssh -N -L 17876:127.0.0.1:17876 galbot@10.34.216.17
```

保持转发终端运行，在调用方电脑使用`http://127.0.0.1:17876`。不要直接访问`http://10.34.216.17:17876`：默认服务没有监听S1的外部网卡。若本地17876被占用，可将命令第一个端口改为17877，并相应修改客户端URL。

## 2. 最快调用方式

同目录提供可直接运行的客户端：[examples/call_fdp.py](examples/call_fdp.py)。在有`numpy、opencv-python/cv2、requests`的Python环境中使用，不要求调用方安装CUDA或FoundationPose。

准备一个输入目录：

```text
input/
├── rgb.png                  # 与深度对齐的彩色图
├── depth_m.npy              # H×W，浮点数，单位米；0表示无效深度
├── mask.png                 # H×W，单通道，目标>0、背景0
├── intrinsics.npy           # 3×3，当前图像对应的K
└── base_from_camera.npy     # 4×4，采集时刻T_base_link_from_camera
```

这五项必须来自同一帧/同一目标合同。尤其不要把别的箱体mask、不同分辨率的内参或机械臂移动后的外参混入。

在**保存了本文及examples目录的调用方电脑**执行：

```bash
python3 examples/call_fdp.py \
  --url http://127.0.0.1:17876 \
  --input-dir /absolute/path/to/input \
  --roi-index 9 \
  --capture-id your-capture-id \
  --identity-key your-target-id \
  --encoding png \
  --vis \
  --output results/fdp_result.json
```

将路径、ROI序号及ID换成自己的数据。`--roi-index 9`只是示例，**不是所有帧都应选择ROI9**。

- 程序保存完整响应到`fdp_result.json`；如请求可视化，再保存同名`fdp_result.png`。
- `--encoding jpg`用于模拟一键客户端的JPEG输入；默认PNG便于保持原始像素。JPEG会改变图像像素，两者结果不能预设逐值相同。
- 去掉`--vis`可减少绘图/编码/传输开销。
- 客户端读取`AI_SERVICE_API_KEY`环境变量时会发送`x-api-key`头，不打印该值。
- 该脚本只调用健康检查和首帧推理，没有自动重试推理；超时后先检查服务日志，避免重复请求造成排队。

## 3. 健康检查

```http
GET /health
```

没有curl时可使用Python：

```python
import requests
with requests.Session() as session:
    session.trust_env = False
    response = session.get("http://127.0.0.1:17876/health", timeout=10)
    response.raise_for_status()
    print(response.json())
```

新Orin服务示例响应（部分字段）：

```json
{
  "ok": true,
  "service": "orin_fdp_compatible",
  "backend": "A4",
  "mesh_path": "EU4322_midcut_target175mm.obj",
  "pose_convention": "camera_from_fdp_oriented_box_center",
  "requires_base_link_from_camera": true,
  "endpoints": ["/health", "/first_frame_track"],
  "stateless_registration": true
}
```

健康检查说明模型已加载、服务可接收请求，不代表某个输入已通过精度验收。

## 4. 首帧估计请求

```http
POST /first_frame_track
Content-Type: application/json
x-api-key: <仅在配置了认证时需要>
```

当前`run_service.sh`未启用密钥校验，且只监听回环地址；服务程序支持`--api-key-env NAME`启用认证，但必须由部署方同时将该变量传入容器。仅在宿主设置环境变量不会自动启用当前启动脚本的认证。原一键客户端仍要求其自身环境中存在`AI_SERVICE_API_KEY`。

### 字段

| 字段 | 必需性 | 类型、单位和说明 |
|---|---|---|
| `rgb_png_base64`或`rgb_jpg_base64` | 二选一 | 编码后PNG/JPEG文件字节的base64字符串，不是数组字节；不要加`data:image/...`前缀 |
| `depth_png_base64` | 必须 | H×W单通道uint16 PNG，建议毫米值 |
| `mask_png_base64` | 必须 | H×W单通道PNG，>0为目标，推荐0/255 |
| `K` | 必须 | 有限数值3×3数组，fx、fy>0 |
| `depth_scale` | 建议明确填写 | 每米对应的整数单位；毫米深度填`1000.0`，默认1000 |
| `base_link_from_camera` | A4/A4-64必须 | 4×4刚体矩阵，平移单位米，方向为相机到base_link |
| `mesh_path` | 建议填写 | 当前固定为`EU4322_midcut_target175mm.obj`；不是让服务任意读取调用方路径 |
| `mesh_model` | 可选 | 当前只支持`"4317"` |
| `mesh_sha256` | 推荐 | 必须匹配部署模型，见下方常量 |
| `return_vis` | 可选 | 布尔值；默认true，推荐显式填写 |
| `capture_id` | 推荐 | 调用方管理的帧ID，响应原样返回 |
| `identity_key` | 推荐 | 调用方管理的目标身份，响应原样返回 |
| `source_roi_index` | 推荐 | 当前目标ROI整数序号，响应原样返回；服务不会据此另选mask |
| `transform_timestamp_ns` | 可选 | 原客户端发送的采集时刻TF时间戳；本服务不据此查询TF或检查时效 |
| `chosen_mask_sha256` | 推荐 | **实际发送的mask PNG字节**SHA256；有则校验 |
| `request_sha256` | 推荐 | 除自身字段外的规范JSON SHA256；有则校验 |
| `fdp_semantic_axes` | 可选 | 当前4317约定，见下方；有则校验 |

三个图像的H×W必须相同，mask非空。RGB应与深度对齐；服务不自动配准或根据ROI裁图。RGB别名字段同时存在时优先PNG，因此建议只传一个。兼容别名另有`rgb_base64`、`depth_base64`、`init_mask_png_base64`、`cam_K`/`intrinsics`，新调用推荐用表中主字段。

当前部署模型SHA256：

```text
adb0d1cf4ee3cc885641ce5e473efb31de4d80323e7665ec50fa5aaabbcc991b
```

输入大小限制：JSON请求体最多32MiB，深度图最多1600万像素；base64编码会增加体积。请求头需要Content-Length，推荐直接使用`requests.post(json=payload)`。

### 深度转换

```python
depth_u16_mm = (depth_m.astype(np.float32) * 1000).astype(np.uint16)
# 将depth_u16_mm编码为PNG，depth_scale=1000.0
# 服务端得到 depth_m = depth_u16_mm.astype(np.float32) / 1000.0
```

转换前检查有限值及范围，避免uint16溢出。示例脚本拒绝负值、NaN/Inf和超出65.535米的输入。已经是uint16毫米深度时不要再乘1000。当前该Orin接口不接受把float32数组字节直接放进`depth_png_base64`。

服务不负责生成LingBot深度。调用者可提供raw或LingBot生成的深度，但需要保持图像配准和单位；精度应针对实际深度来源验证。

### 哈希计算

```python
chosen_mask_sha256 = hashlib.sha256(mask_png_bytes).hexdigest()
# 先填好所有其他字段，最后计算request_sha256。
request_sha256 = hashlib.sha256(
    json.dumps(payload_without_request_sha256,
               ensure_ascii=False, sort_keys=True,
               separators=(",", ":"), allow_nan=False).encode("utf-8")
).hexdigest()
```

PNG文件压缩编码不同，即使mask像素相同，字节SHA256也可能不同。必须对本次真正发送的PNG字节计算，不能直接套用另一个文件的哈希。这些哈希用于一致性校验，不代替身份认证。

## 5. 响应格式

成功HTTP 200，响应示例**仅用于展示格式，数值不是测量结果**：

```json
{
  "ok": true,
  "mesh_path": "EU4322_midcut_target175mm.obj",
  "mesh_sha256": "adb0d1cf4ee3cc885641ce5e473efb31de4d80323e7665ec50fa5aaabbcc991b",
  "backend": "A4",
  "pose_convention": "camera_from_fdp_oriented_box_center",
  "pose": [[1,0,0,0.1],[0,1,0,0.2],[0,0,1,1.0],[0,0,0,1]],
  "register_s": 0.75,
  "elapsed_s": 0.81,
  "vis_png_base64": null,
  "capture_id": "example-frame",
  "identity_key": "example-target",
  "source_roi_index": 9
}
```

- `pose`：4×4、平移单位**米**。含义是`T_camera_from_fdp_box_center`，将FDP有向包围框坐标中的点变换到相机坐标。**不是原mesh原点位姿，不是base_link位姿，也不是已经转好语义轴的位姿。**
- `vis_png_base64`：可视化PNG；`return_vis=false`时为null。边框包括被遮挡的背面边，不代表分割轮廓。
- `register_s`：GPU同步后的算法register耗时，包含当前算法的候选选择。
- `elapsed_s`：本服务从请求解码开始，到推理和可选可视化完成的处理时间，包含等待算法锁；不包含全部HTTP收发/JSON序列化开销。
- HTTP总耗时需在客户端测量；不要把register_s当作完整业务时延。
- `chosen_mask_sha256`以及请求中存在的身份字段会返回；`diagnostics`含实际候选数等诊断，不建议业务流程依赖其内部结构。
- 当前4090响应可能没有`backend/register_s/pose_convention`等扩展字段，跨两端客户端应将这些字段视为可选。新Orin服务保持原客户端所需的主字段。

## 6. 坐标转换：只转换一次

当前4317语义轴：长度+X=FDP +Z，宽度+Y=FDP +Y，高度+Z=FDP −X。

```python
T_camera_from_fdp = np.asarray(result["pose"], dtype=float)
T_base_from_camera = np.asarray(payload["base_link_from_camera"], dtype=float)
T_fdp_from_semantic = np.array([
    [0, 0, -1, 0],
    [0, 1,  0, 0],
    [1, 0,  0, 0],
    [0, 0,  0, 1],
], dtype=float)
T_camera_from_semantic = T_camera_from_fdp @ T_fdp_from_semantic
T_base_from_semantic = T_base_from_camera @ T_camera_from_semantic
```

现有`FoundationPoseHttpClient`已做上述变换，接它返回的`semantic_object_in_base_link`时不要再转一次。不要把A4所需外参随意填成单位矩阵：它影响竖直先验和候选选择。

这段转换不额外做箱体180°对称归一化；如业务需要固定抓取朝向，应由调用方按现有语义规则处理，不要随意改变服务输出。

## 7. 与一键脚本接入

当前链路：

```text
run.sh dev-scenario mode00 RUN_ID
  → config/scenarios/mode00.yaml
  → config/services/lab.yaml
  → FoundationPoseHttpClient
  → POST /first_frame_track
```

已准备完整示例配置：[config/lab_orin.example.yaml](config/lab_orin.example.yaml)。主要修改如下：

```yaml
fdp:
  url: http://127.0.0.1:17876
  timeout_s: 180
  return_visualization: true
health:
  fdp: http://127.0.0.1:17876/health
```

这只是相关片段，**不要用它覆盖整个配置而丢失auth、workbin或其他health字段**。当前一键controller使用host网络，所以能访问S1回环端口；普通bridge网络容器的127.0.0.1不是S1宿主。

配置示例未应用到生产。一键脚本会冻结代码和配置，切换服务应建立新的配置快照/运行ID，不覆盖历史任务配置。现有目标身份、几何检查和运动门限不应因换服务而移除。

## 8. 算法可插拔接口

外部HTTP接口与算法实现分离，内部合同定义在`package/fdp_api/contracts.py`：

```python
class PoseBackend:
    name: str
    requires_base_transform: bool

    def estimate(self, observation) -> Estimate:
        ...
```

`Observation`字段：

| 字段 | 内部类型 |
|---|---|
| `rgb` | H×W×3 uint8，RGB通道顺序 |
| `depth_m` | H×W float32，米制光学Z深度 |
| `mask` | H×W bool |
| `K` | 3×3内参 |
| `base_from_camera` | 4×4外参或None；需要它的后端必须拒绝缺失值 |

`Estimate`包含`pose_camera_from_box`、`register_seconds`、对应坐标中的`bbox`（2×3）和`diagnostics`。新算法需转换成相同输出坐标后再接入。

已有算法通过启动参数选择；开发者可使用`--backend-factory your_module:create`注册自己的后端，工厂接收`MeshSpec`并返回后端实例。模块必须由部署方放入容器Python路径；不能在HTTP请求中指定代码。当前启动脚本仅暴露已实现的A系列选择，自定义工厂需另配启动命令。

每进程一个算法，重启切换。当前FDP优化hook有模块级状态，因此不支持同进程多算法热切换。服务串行执行推理；并发请求会排队，不承诺并发吞吐。

## 9. 常见错误与处理

| 现象/状态码 | 含义和处理 |
|---|---|
| 连接拒绝 | 确认服务ready、30分钟超时未到、URL/SSH转发正确 |
| HTTP 400 | 检查错误字符串；常见为图像尺寸、空mask、模型或哈希不匹配、缺少外参 |
| `depth must be uint16 PNG` | 深度编码或dtype错误，不要发送8位深度图 |
| `base_link_from_camera required...` | A4/A4-64缺少采集外参 |
| `request_sha256 mismatch` | 计算哈希后又改了字段，或JSON规范化方式不同 |
| HTTP 401 | 服务启用认证，需正确的`x-api-key`；不要把密钥写入脚本或文档 |
| HTTP 404 | GET路径不存在 |
| HTTP 501 | 当前只支持首帧POST；`/next_frame_track`、`/reset`、`/warmup`未实现 |
| HTTP 500 | 后端运行异常，检查本次服务终端日志；不要将错误响应视为有效位姿 |
| 客户端超时 | 服务初始化/推理/排队可能未结束，先检查状态再决定是否重新提交 |

## 10. 验证范围和性能口径

- 原一键客户端的JPEG请求、响应解析、可视化和坐标转换在独立Orin容器测试通过。
- A4/A4-64同一冻结D12左侧PNG输入，输出与各自归档位姿逐值一致。
- 单D12、各3次正式、PNG、不开可视化，本机HTTP中位/最大：A4 **0.816/0.837秒**，A4-64 **0.921/0.943秒**。这不是所有输入和负载下的保证。
- 当前一键流程发送采集raw深度；此前28帧加速基准和本次GPU接口测试使用LingBot冻结深度。**接口兼容不等于raw+JPEG的新场景精度已经验收。**
- A0/A1/A2/A3已提供适配，本轮未逐个做HTTP GPU复测。多模型、跟踪、长期运行、并发和完整机器人作业尚未验收。
- 4090是对照服务，不是独立物理真值。

进一步阅读：[实现说明](README.md)、[验证报告](REPORT.md)。本文件和`examples/call_fdp.py`可一起交给调用同事；本地示例默认不连接任何服务，只有显式执行客户端主程序时才发请求。