# Orin 冻结右腕四组消融结果

所有位姿差为相对本轮 BCM 的回归差异，不是绝对误差。每组一次筛查，不是重复性能统计。

|组|算法 s|容器墙钟 s|状态|中心差 mm|yaw差 °|箱口差 mm|短边最大差 mm|最佳来源|seed/fit|
|---|---:|---:|---|---:|---:|---:|---:|---|---|
|BCM|15.4767|17.0108|accepted|0.0000|0.0000|0.0000|0.0000|mesh_coarse_projection|12/14|
|CM|10.4979|11.4978|accepted|0.0000|0.0000|0.0000|0.0000|mesh_coarse_projection|12/14|
|BM|8.9887|10.0420|accepted|0.0000|0.0000|0.0000|0.0000|mesh_coarse_projection|12/14|
|M|4.0884|5.1288|accepted|0.0000|0.0000|0.0000|0.0000|mesh_coarse_projection|12/14|

## 验证

- 本轮 BCM native 与旧容器基线完全一致：True
- 输入/镜像核验：{"input_unchanged": true, "image_unchanged": true}
- 分支调用次数已断言验证；B/C 跳过确实未执行相应分支。

## 竞争与拒绝

- BCM: rivals=0; reasons=[]
  surface p90 mm: {'outer_plus_rim': 18.990962799174262, 'inner_plus_rim': 15.98418234628422}

- CM: rivals=0; reasons=[]
  surface p90 mm: {'outer_plus_rim': 18.990962799174262, 'inner_plus_rim': 15.98418234628422}

- BM: rivals=0; reasons=[]
  surface p90 mm: {'outer_plus_rim': 18.990962799174262, 'inner_plus_rim': 15.98418234628422}

- M: rivals=0; reasons=[]
  surface p90 mm: {'outer_plus_rim': 18.990962799174262, 'inner_plus_rim': 15.98418234628422}

完整初值、竞争位姿、残差、迭代信息见各轮 result 与 ablation_audit.json。短边最大差采用两端最小总距离配对；机器摘要同时保留原标签逐点差。
候选箱口/短边由模型推导，不是直接测量或机器人 TCP。
本轮不支持正式删除分支；多视角/遮挡/拒绝帧和独立参考仍需验证。