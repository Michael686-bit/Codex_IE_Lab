# 合成倾斜与退化验证（A 阶段）

使用已知倾角平面，加入轴向倾斜、XYZ 噪声、随机/连续缺失点，以及退化/竞争平面。

|场景|状态|真值倾角|估计倾角|法向误差|结果|
|---|---|---:|---:|---:|---|
|upright_noise|accepted|0.00°|0.01°|0.01°|通过|
|tilt_plus_x_5|accepted|5.00°|5.01°|0.01°|通过|
|tilt_minus_x_5|accepted|5.00°|4.98°|0.02°|通过|
|tilt_plus_y_8_missing|accepted|8.00°|8.05°|0.05°|通过|
|tilt_minus_y_8_noisy|accepted|8.00°|7.97°|0.04°|通过|
|tilt_combo_7|accepted|7.07°|7.07°|0.01°|通过|
|tilt_5_contiguous_occlusion|accepted|5.00°|5.00°|0.01°|通过|
|narrow_strip|rejected|—|—|—|通过|
|single_line|rejected|—|—|—|通过|
|two_competing_planes|ambiguous|—|—|—|通过|

红色为合成真值法向，绿色为估计法向。合成通过只说明数值估计和停止行为满足本测试条件，不说明实物箱口身份、FDP 或相机标定。

![合成真值/估计接触表](contact_sheet.png)