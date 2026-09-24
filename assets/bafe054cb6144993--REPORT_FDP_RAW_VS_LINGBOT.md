# FDP raw 与其他算法 LingBot 的逐帧对比

每帧使用 5 次正式重复的中位数。FDP 取 raw 深度；V5-original、BCM、R1、RM、R1F 取 LingBot 深度。Δx/Δy/Δz 是算法位姿中心减去标定板参考中心，单位 mm，坐标为 base_link；yaw 是考虑箱体 180°对称后的差值。拒绝帧仍保留耗时，位姿差距记为 N/A。

## 汇总

|方法|深度|接受运行/尝试|有板可评分帧|Δx 中位数 mm|Δy 中位数 mm|Δz 中位数 mm|中心距离中位数 mm|yaw 中位数°|主耗时中位数 s|Docker Wall中位数 s|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|FDP|raw|65/65|11|3.415|0.145|-8.847|10.399|0.872|1.274|N/A|
|V5-original|lingbot|20/65|3|-5.512|-3.439|-2.044|7.346|0.414|21.406|22.225|
|BCM|lingbot|20/65|3|-5.512|-3.439|-2.044|7.346|0.414|21.193|22.229|
|R1|lingbot|15/65|3|-4.873|-1.321|-1.856|5.848|0.348|0.966|1.971|
|RM|lingbot|15/65|3|-5.512|-3.439|-2.044|7.346|0.348|5.293|6.332|
|R1F|lingbot|20/65|3|-4.873|-1.321|-1.856|5.848|0.348|22.186|23.226|

## 逐帧结果

|帧|方法|状态|接受/尝试|板角点|Δx|Δy|Δz|中心距离|yaw|主耗时 s|Wall s|拒绝原因|
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
|L01_wrist_charuco_20260915_093818_877801116|FDP|accepted|5/5|4|N/A|N/A|N/A|N/A|N/A|1.267|N/A||
|L01_wrist_charuco_20260915_093818_877801116|V5-original|accepted|5/5|4|N/A|N/A|N/A|N/A|N/A|14.054|14.858||
|L01_wrist_charuco_20260915_093818_877801116|BCM|accepted|5/5|4|N/A|N/A|N/A|N/A|N/A|13.867|14.905||
|L01_wrist_charuco_20260915_093818_877801116|R1|rejected|0/5|4|N/A|N/A|N/A|N/A|N/A|0.795|1.821|ambiguous_inner_outer_surface_hypotheses|
|L01_wrist_charuco_20260915_093818_877801116|RM|rejected|0/5|4|N/A|N/A|N/A|N/A|N/A|4.092|5.081|ambiguous_inner_outer_surface_hypotheses|
|L01_wrist_charuco_20260915_093818_877801116|R1F|accepted|5/5|4|N/A|N/A|N/A|N/A|N/A|14.634|15.658||
|L02_wrist_charuco_20260915_100236_358935353|FDP|accepted|5/5|47|5.184|-3.979|-16.267|17.531|0.368|1.274|N/A||
|L02_wrist_charuco_20260915_100236_358935353|V5-original|rejected|0/5|47|N/A|N/A|N/A|N/A|N/A|19.683|20.472|ambiguous_inner_outer_surface_hypotheses|
|L02_wrist_charuco_20260915_100236_358935353|BCM|rejected|0/5|47|N/A|N/A|N/A|N/A|N/A|19.358|20.370|ambiguous_inner_outer_surface_hypotheses|
|L02_wrist_charuco_20260915_100236_358935353|R1|rejected|0/5|47|N/A|N/A|N/A|N/A|N/A|0.903|1.921|ambiguous_inner_outer_surface_hypotheses|
|L02_wrist_charuco_20260915_100236_358935353|RM|rejected|0/5|47|N/A|N/A|N/A|N/A|N/A|5.044|6.082|ambiguous_inner_outer_surface_hypotheses|
|L02_wrist_charuco_20260915_100236_358935353|R1F|rejected|0/5|47|N/A|N/A|N/A|N/A|N/A|20.307|21.323|ambiguous_inner_outer_surface_hypotheses|
|L03_00_wrist_charuco_20260915_104002_497962253|FDP|accepted|5/5|65|4.476|-5.014|-15.102|16.530|1.021|1.272|N/A||
|L03_00_wrist_charuco_20260915_104002_497962253|V5-original|rejected|0/5|65|N/A|N/A|N/A|N/A|N/A|23.096|23.879|ambiguous_inner_outer_surface_hypotheses;visible_shell_residual_or_coverage_too_low|
|L03_00_wrist_charuco_20260915_104002_497962253|BCM|rejected|0/5|65|N/A|N/A|N/A|N/A|N/A|22.867|23.879|ambiguous_inner_outer_surface_hypotheses;visible_shell_residual_or_coverage_too_low|
|L03_00_wrist_charuco_20260915_104002_497962253|R1|rejected|0/5|65|N/A|N/A|N/A|N/A|N/A|1.113|2.121|ambiguous_inner_outer_surface_hypotheses|
|L03_00_wrist_charuco_20260915_104002_497962253|RM|rejected|0/5|65|N/A|N/A|N/A|N/A|N/A|5.448|6.483|ambiguous_inner_outer_surface_hypotheses;visible_shell_residual_or_coverage_too_low|
|L03_00_wrist_charuco_20260915_104002_497962253|R1F|rejected|0/5|65|N/A|N/A|N/A|N/A|N/A|24.004|25.035|ambiguous_inner_outer_surface_hypotheses;visible_shell_residual_or_coverage_too_low|
|L03_10_wrist_charuco_20260915_103928_398335507|FDP|accepted|5/5|55|3.354|-6.793|-13.928|15.856|0.100|1.276|N/A||
|L03_10_wrist_charuco_20260915_103928_398335507|V5-original|rejected|0/5|55|N/A|N/A|N/A|N/A|N/A|24.158|24.984|ambiguous_inner_outer_surface_hypotheses;visible_shell_residual_or_coverage_too_low|
|L03_10_wrist_charuco_20260915_103928_398335507|BCM|rejected|0/5|55|N/A|N/A|N/A|N/A|N/A|23.969|25.030|ambiguous_inner_outer_surface_hypotheses;visible_shell_residual_or_coverage_too_low|
|L03_10_wrist_charuco_20260915_103928_398335507|R1|rejected|0/5|55|N/A|N/A|N/A|N/A|N/A|1.227|2.222|ambiguous_inner_outer_surface_hypotheses;visible_shell_residual_or_coverage_too_low|
|L03_10_wrist_charuco_20260915_103928_398335507|RM|rejected|0/5|55|N/A|N/A|N/A|N/A|N/A|6.211|7.235|ambiguous_inner_outer_surface_hypotheses;visible_shell_residual_or_coverage_too_low|
|L03_10_wrist_charuco_20260915_103928_398335507|R1F|rejected|0/5|55|N/A|N/A|N/A|N/A|N/A|25.225|26.240|ambiguous_inner_outer_surface_hypotheses;visible_shell_residual_or_coverage_too_low|
|L04_00_wrist_charuco_20260915_104435_858773771|FDP|accepted|5/5|78|1.002|1.439|-11.623|11.755|0.810|1.177|N/A||
|L04_00_wrist_charuco_20260915_104435_858773771|V5-original|rejected|0/5|78|N/A|N/A|N/A|N/A|N/A|21.064|21.873|ambiguous_inner_outer_surface_hypotheses|
|L04_00_wrist_charuco_20260915_104435_858773771|BCM|rejected|0/5|78|N/A|N/A|N/A|N/A|N/A|20.972|22.024|ambiguous_inner_outer_surface_hypotheses|
|L04_00_wrist_charuco_20260915_104435_858773771|R1|rejected|0/5|78|N/A|N/A|N/A|N/A|N/A|1.276|2.275|ambiguous_inner_outer_surface_hypotheses|
|L04_00_wrist_charuco_20260915_104435_858773771|RM|rejected|0/5|78|N/A|N/A|N/A|N/A|N/A|5.293|6.332|ambiguous_inner_outer_surface_hypotheses|
|L04_00_wrist_charuco_20260915_104435_858773771|R1F|rejected|0/5|78|N/A|N/A|N/A|N/A|N/A|22.186|23.226|ambiguous_inner_outer_surface_hypotheses|
|L04_10_wrist_charuco_20260915_104717_786588568|FDP|accepted|5/5|77|3.415|-4.653|-8.847|10.563|0.640|1.179|N/A||
|L04_10_wrist_charuco_20260915_104717_786588568|V5-original|accepted|5/5|77|4.400|-7.201|-9.766|12.907|0.414|21.406|22.225||
|L04_10_wrist_charuco_20260915_104717_786588568|BCM|accepted|5/5|77|4.400|-7.201|-9.766|12.907|0.414|21.193|22.229||
|L04_10_wrist_charuco_20260915_104717_786588568|R1|accepted|5/5|77|4.446|-5.490|-8.256|10.866|0.348|0.986|1.971||
|L04_10_wrist_charuco_20260915_104717_786588568|RM|accepted|5/5|77|4.446|-5.490|-8.256|10.866|0.348|8.359|9.391||
|L04_10_wrist_charuco_20260915_104717_786588568|R1F|accepted|5/5|77|4.446|-5.490|-8.256|10.866|0.348|0.985|2.021||
|L04_wrist_charuco_20260915_104358_532673829|FDP|accepted|5/5|71|1.694|-2.421|-9.970|10.399|0.314|1.196|N/A||
|L04_wrist_charuco_20260915_104358_532673829|V5-original|rejected|0/5|71|N/A|N/A|N/A|N/A|N/A|22.156|22.976|ambiguous_inner_outer_surface_hypotheses|
|L04_wrist_charuco_20260915_104358_532673829|BCM|rejected|0/5|71|N/A|N/A|N/A|N/A|N/A|22.243|23.277|ambiguous_inner_outer_surface_hypotheses|
|L04_wrist_charuco_20260915_104358_532673829|R1|rejected|0/5|71|N/A|N/A|N/A|N/A|N/A|0.888|1.921|ambiguous_inner_outer_surface_hypotheses|
|L04_wrist_charuco_20260915_104358_532673829|RM|rejected|0/5|71|N/A|N/A|N/A|N/A|N/A|5.422|6.434|ambiguous_inner_outer_surface_hypotheses|
|L04_wrist_charuco_20260915_104358_532673829|R1F|rejected|0/5|71|N/A|N/A|N/A|N/A|N/A|22.866|23.880|ambiguous_inner_outer_surface_hypotheses|
|R01_wrist_charuco_20260915_093900_967150252|FDP|accepted|5/5|3|N/A|N/A|N/A|N/A|N/A|1.265|N/A||
|R01_wrist_charuco_20260915_093900_967150252|V5-original|rejected|0/5|3|N/A|N/A|N/A|N/A|N/A|11.386|12.198|ambiguous_inner_outer_surface_hypotheses|
|R01_wrist_charuco_20260915_093900_967150252|BCM|rejected|0/5|3|N/A|N/A|N/A|N/A|N/A|11.214|12.249|ambiguous_inner_outer_surface_hypotheses|
|R01_wrist_charuco_20260915_093900_967150252|R1|rejected|0/5|3|N/A|N/A|N/A|N/A|N/A|0.966|1.971|ambiguous_inner_outer_surface_hypotheses|
|R01_wrist_charuco_20260915_093900_967150252|RM|rejected|0/5|3|N/A|N/A|N/A|N/A|N/A|3.647|4.678|ambiguous_inner_outer_surface_hypotheses|
|R01_wrist_charuco_20260915_093900_967150252|R1F|rejected|0/5|3|N/A|N/A|N/A|N/A|N/A|12.072|13.101|ambiguous_inner_outer_surface_hypotheses|
|R01_wrist_charuco_20260915_094033_680788016|FDP|accepted|5/5|9|2.314|5.333|2.860|6.479|1.501|1.373|N/A||
|R01_wrist_charuco_20260915_094033_680788016|V5-original|accepted|5/5|9|-6.447|-3.439|0.750|7.346|0.433|14.860|15.659||
|R01_wrist_charuco_20260915_094033_680788016|BCM|accepted|5/5|9|-6.447|-3.439|0.750|7.346|0.433|14.736|15.764||
|R01_wrist_charuco_20260915_094033_680788016|R1|accepted|5/5|9|-5.696|-1.321|0.058|5.848|0.596|0.847|1.871||
|R01_wrist_charuco_20260915_094033_680788016|RM|accepted|5/5|9|-6.447|-3.439|0.750|7.346|0.433|4.848|5.881||
|R01_wrist_charuco_20260915_094033_680788016|R1F|accepted|5/5|9|-5.696|-1.321|0.058|5.848|0.596|0.838|1.872||
|R02_wrist_charuco_20260915_100308_809523978|FDP|accepted|5/5|77|0.629|6.075|5.762|8.397|0.872|1.377|N/A||
|R02_wrist_charuco_20260915_100308_809523978|V5-original|accepted|5/5|77|-5.512|1.048|-2.044|5.972|0.044|19.025|19.868||
|R02_wrist_charuco_20260915_100308_809523978|BCM|accepted|5/5|77|-5.512|1.048|-2.044|5.972|0.044|18.852|19.868||
|R02_wrist_charuco_20260915_100308_809523978|R1|accepted|5/5|77|-4.873|2.333|-1.856|5.713|0.305|0.884|1.921||
|R02_wrist_charuco_20260915_100308_809523978|RM|accepted|5/5|77|-5.512|1.048|-2.044|5.972|0.044|5.572|6.587||
|R02_wrist_charuco_20260915_100308_809523978|R1F|accepted|5/5|77|-4.873|2.333|-1.856|5.713|0.305|0.894|1.923||
|R03_wrist_charuco_20260915_103743_184821162|FDP|accepted|5/5|100|5.409|4.084|3.102|7.454|1.322|1.371|N/A||
|R03_wrist_charuco_20260915_103743_184821162|V5-original|rejected|0/5|100|N/A|N/A|N/A|N/A|N/A|24.244|25.033|mask_touches_image_border;visible_shell_residual_or_coverage_too_low|
|R03_wrist_charuco_20260915_103743_184821162|BCM|rejected|0/5|100|N/A|N/A|N/A|N/A|N/A|24.369|25.381|mask_touches_image_border;visible_shell_residual_or_coverage_too_low|
|R03_wrist_charuco_20260915_103743_184821162|R1|rejected|0/5|100|N/A|N/A|N/A|N/A|N/A|1.105|2.123|ambiguous_inner_outer_surface_hypotheses;mask_touches_image_border|
|R03_wrist_charuco_20260915_103743_184821162|RM|rejected|0/5|100|N/A|N/A|N/A|N/A|N/A|8.075|9.092|mask_touches_image_border;visible_shell_residual_or_coverage_too_low|
|R03_wrist_charuco_20260915_103743_184821162|R1F|rejected|0/5|100|N/A|N/A|N/A|N/A|N/A|25.173|26.186|mask_touches_image_border;visible_shell_residual_or_coverage_too_low|
|R04_00_wrist_charuco_20260915_104526_910331328|FDP|accepted|5/5|100|4.798|6.785|0.681|8.337|1.342|1.367|N/A||
|R04_00_wrist_charuco_20260915_104526_910331328|V5-original|rejected|0/5|100|N/A|N/A|N/A|N/A|N/A|22.415|23.227|ambiguous_inner_outer_surface_hypotheses|
|R04_00_wrist_charuco_20260915_104526_910331328|BCM|rejected|0/5|100|N/A|N/A|N/A|N/A|N/A|21.925|22.976|ambiguous_inner_outer_surface_hypotheses|
|R04_00_wrist_charuco_20260915_104526_910331328|R1|rejected|0/5|100|N/A|N/A|N/A|N/A|N/A|0.794|1.871|ambiguous_inner_outer_surface_hypotheses|
|R04_00_wrist_charuco_20260915_104526_910331328|RM|rejected|0/5|100|N/A|N/A|N/A|N/A|N/A|4.725|5.781|ambiguous_inner_outer_surface_hypotheses|
|R04_00_wrist_charuco_20260915_104526_910331328|R1F|rejected|0/5|100|N/A|N/A|N/A|N/A|N/A|22.823|23.831|ambiguous_inner_outer_surface_hypotheses|
|R04_10_wrist_charuco_20260915_105839_488564574|FDP|accepted|5/5|100|6.246|0.145|5.395|8.254|1.360|1.380|N/A||
|R04_10_wrist_charuco_20260915_105839_488564574|V5-original|rejected|0/5|100|N/A|N/A|N/A|N/A|N/A|25.487|26.285|ambiguous_inner_outer_surface_hypotheses|
|R04_10_wrist_charuco_20260915_105839_488564574|BCM|rejected|0/5|100|N/A|N/A|N/A|N/A|N/A|25.309|26.335|ambiguous_inner_outer_surface_hypotheses|
|R04_10_wrist_charuco_20260915_105839_488564574|R1|rejected|0/5|100|N/A|N/A|N/A|N/A|N/A|1.326|2.372|ambiguous_inner_outer_surface_hypotheses|
|R04_10_wrist_charuco_20260915_105839_488564574|RM|rejected|0/5|100|N/A|N/A|N/A|N/A|N/A|4.802|5.832|ambiguous_inner_outer_surface_hypotheses|
|R04_10_wrist_charuco_20260915_105839_488564574|R1F|rejected|0/5|100|N/A|N/A|N/A|N/A|N/A|26.764|27.840|ambiguous_inner_outer_surface_hypotheses|

## 解释

FDP 的主耗时是 S1 宿主完整客户端时间，包含编码、请求和归一化；V5 主耗时是 S1 Docker 后端时间，Wall 列还包括容器启动和结果写入。两者运行平台不同，时间只作实测参考。C01/L01 与 C08/误标 R01 左腕没有可用板参考，所以它们的Δx/Δy/Δz/yaw为N/A。