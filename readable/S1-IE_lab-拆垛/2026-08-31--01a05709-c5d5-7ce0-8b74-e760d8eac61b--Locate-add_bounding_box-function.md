# Locate add_bounding_box function

- 归档编号：`01a05709-c5d5-7ce0-8b74-e760d8eac61b`
- 项目：S1 IE_lab 拆垛
- 创建时间：2026-08-31T16:57:33.407000+08:00
- 更新时间：2026-08-31T17:02:11.143000+08:00
- 状态：活动
- 导出范围：用户可见消息与助手可见回复；不含隐藏推理和工具原始输出

## 1. 用户

我们明确一下 add_bounding_box()这个函数的功能流程，是否如何作用和去除点云的？告诉我在那个文件中能找到这个函数定义也行

## 2. 助手（进展）

我先按仓库要求读取基础文档，再定位 `add_bounding_box()` 的定义、调用链和点云过滤实现；这一步只做代码检查，不会改文件或操作机器人。

## 3. 助手（进展）

仓库里已经有一份今天形成的专项运行时分析，说明这个问题此前被追到融合服务内部了。我会把它与本地调用代码和 SDK 笔记交叉核对，区分“已经证实”和“仍属推断”的部分。

## 4. 助手

结论：`add_bounding_box()` 不是直接删除一份点云，也不会清除已经生成的地图。它的作用是注册一个随指定坐标系移动的三维过滤框，使框内的后续传感器点在进入 nvblox 融合前被过滤掉。

### 实际工作流程

```text
add_bounding_box(box_info)
    ↓
SDK 将 box_tag 转成 sdk_box_<tag>
    ↓
调用 fusion 服务 galbot_fusion_add_box
    ↓
galbot_fusion_main 保存过滤框
    ↓
根据 TF 将 box_pose 转换到融合坐标系
    ↓
过滤新进入的、位于箱体范围内的点
    ↓
剩余点才进入 TSDF / Occupancy / Color 融合
    ↓
由融合结果更新 ESDF
    ↓
PNS 和 Motion 使用更新后的 ESDF 做碰撞检测
```

`box_info` 的结构是：

```python
{
    "box_size": [length_x, length_y, length_z],
    "box_pose": [x, y, z, qx, qy, qz, qw],
    "box_tag": 4317,
    "parent_link_name": "base_link",
}
```

其中：

- `box_pose` 相对于 `parent_link_name`。
- 四元数决定过滤框方向，因此可理解为有方向的 OBB，而不只是 map 轴对齐框。
- 如果父坐标系是 `base_link`，过滤框会通过 TF 跟着底盘运动。
- 它是几何过滤：所有落进框内的点都会被过滤，并不识别“这是箱子还是墙”。因此过滤框不能随意扩大，否则也可能隐藏框内真实障碍物。

### “去除点云”具体是什么意思

它做的是：

- 过滤登记之后新进入 fusion 的点；
- 让这些点不参与 TSDF、Occupancy、Color 和后续 ESDF 更新；
- 原始 LiDAR 点云发布本身不会被修改；
- 不会追溯删除登记之前已经融合进去的 TSDF/ESDF 体素。

所以这两种理解是不正确的：

```text
add_bounding_box() ≠ 从原始 LiDAR 消息中永久删除点
add_bounding_box() ≠ 清除框内已有 TSDF/ESDF 地图
```

这也解释了当前 4317 箱体问题：箱体先被传感器观测并融合，随后才调用 `add_bounding_box()`，旧箱体体素可能仍留在 ESDF 中。函数只能阻止新的箱体点继续进入，不能保证旧体素立即消失。`remove_bounding_box()` 也只是撤销未来过滤规则，不是清图。

厂家程序里另有独立的 `galbot_fusion_clear_esdf` 清理服务，但其范围和恢复语义尚未核实，不能把它当作安全的“框内清除”接口直接调用。

### 和 `attach_box_to_link()` 的区别

两者用途完全不同，但携箱导航时通常互补：

| 函数 | 作用 |
|---|---|
| `add_bounding_box()` | 防止机器人携带的箱子点云被当成外部障碍 |
| `attach_box_to_link()` | 把箱子作为机器人携带的实体碰撞几何，让 PNS 考虑箱子会不会撞环境 |

也就是说，前者是“不要把箱子看成环境”，后者是“机器人现在确实变大了”。

### 函数在哪里

SDK 的 Python API 声明在：

[galbot_sdk/s1/\_\_init\_\_.pyi](/home/lsy03/Lsy03_document/galbot_s1_SDK_learning/third_party/GalbotSDK_official_full/galbot_sdk/linux-x86_64-gcc940/lib/python/galbot_sdk/s1/__init__.pyi:1221)

S1 包装类在：

[galbot_sdk/s1/\_\_init\_\_.py](/home/lsy03/Lsy03_document/galbot_s1_SDK_learning/third_party/GalbotSDK_official_full/galbot_sdk/linux-x86_64-gcc940/lib/python/galbot_sdk/s1/__init__.py:36)

这个 Python 包装类通过 `__getattr__()` 把调用转交给 SDK 的底层实现。真正的 SDK 函数体不在可读的 `.py` 文件中，而在编译好的：

```text
galbot_sdk.cpython-<Python版本>-<架构>-linux-gnu.so
```

融合服务的真正处理位于编译后的 `/data/galbot/bin/galbot_fusion_main`；现场没有部署对应的 C++ 源文件。

本项目调用它的位置是：

[s1_navigation_cli.py](/home/lsy03/文档/ChatGPT/S1/experiments/20260827_s1_navigation/s1_navigation_cli.py:507)

4317 过滤框参数在同一文件：

[s1_navigation_cli.py](/home/lsy03/文档/ChatGPT/S1/experiments/20260827_s1_navigation/s1_navigation_cli.py:58)

完整的二进制、日志和调用链分析记录在：

[s1_add_bounding_box_runtime_analysis_20260831.md](../../assets/7b81546798fced5b--s1_add_bounding_box_runtime_analysis_20260831.md:19)

另外，[test_s1_navigation_cli.py](/home/lsy03/文档/ChatGPT/S1/experiments/20260827_s1_navigation/test_s1_navigation_cli.py:117) 中也有一个同名 `def add_bounding_box()`，但那只是单元测试使用的伪 SDK，不能代表厂家真实实现。

[附件：7b81546798fced5b--s1_add_bounding_box_runtime_analysis_20260831.md](../../assets/7b81546798fced5b--s1_add_bounding_box_runtime_analysis_20260831.md)
