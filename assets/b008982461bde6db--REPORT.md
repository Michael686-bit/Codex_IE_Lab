# V5-5 倾斜感知 6DoF 合成批量结果

输入为冻结 mesh 采样合成 RGB-D；truth_pose 仅用于评估，不进入估计器。

|场景|状态|总倾斜(°)|中心误差(mm)|高度轴误差(°)|设计门槛|可观测性|
|---|---|---:|---:|---:|---|---|
|H01L|tilt_fit_rejected|15.66|—|—|未通过|true|
|H02L|tilt_fit_rejected|22.10|—|—|未通过|true|
|H03L|tilt_fit_rejected|12.05|—|—|未通过|true|

设计门槛仅用于 B 合成验收；真实准确度、表面身份和抓取可用性仍未验证。

![真值/估计叠加图](contact_sheet.png)