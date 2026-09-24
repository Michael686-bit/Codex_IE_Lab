# FDP raw 与其他算法 LingBot（含拒绝运行候选）的对比

每帧使用 5 次正式重复的中位数，再跨帧统计最小值 / 中位数 / 最大值。FDP 取 raw 深度；V5-original、BCM、R1、RM、R1F 取 LingBot 深度。正式接受行的 Δx/Δy/Δz/yaw 来自正式位姿；拒绝行没有正式位姿，表中改列出保存的诊断候选相对标定板的差距，并明确标记为 `rejected_candidate_diagnostic`。

## 汇总

单元格格式：最小值 / 中位数 / 最大值。

|方法|深度|结果来源|运行数|可评分帧|Δx mm|Δy mm|Δz mm|中心距离 mm|yaw °|主耗时 s|
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|FDP|raw|accepted formal|65|11|0.629 / 3.415 / 6.246|-6.793 / 0.145 / 6.785|-16.267 / -8.847 / 5.762|6.479 / 10.399 / 17.531|0.100 / 0.872 / 1.501|1.177 / 1.274 / 1.380|
|FDP|raw|rejected candidate diagnostic|0|0|N/A / N/A / N/A|N/A / N/A / N/A|N/A / N/A / N/A|N/A / N/A / N/A|N/A / N/A / N/A|N/A / N/A / N/A|
|V5-original|lingbot|accepted formal|20|3|-6.447 / -5.512 / 4.400|-7.201 / -3.439 / 1.048|-9.766 / -2.044 / 0.750|5.972 / 7.346 / 12.907|0.044 / 0.414 / 0.433|14.054 / 16.943 / 21.406|
|V5-original|lingbot|rejected candidate diagnostic|45|8|-3.567 / 3.815 / 7.084|-10.599 / -4.023 / 7.049|-22.679 / -14.363 / -5.352|8.587 / 15.677 / 24.906|0.080 / 0.712 / 1.105|11.386 / 22.415 / 25.487|
|BCM|lingbot|accepted formal|20|3|-6.447 / -5.512 / 4.400|-7.201 / -3.439 / 1.048|-9.766 / -2.044 / 0.750|5.972 / 7.346 / 12.907|0.044 / 0.414 / 0.433|13.867 / 16.794 / 21.193|
|BCM|lingbot|rejected candidate diagnostic|45|8|-3.567 / 3.815 / 7.084|-10.599 / -4.023 / 7.049|-22.679 / -14.363 / -5.352|8.587 / 15.677 / 24.906|0.080 / 0.712 / 1.105|11.214 / 22.243 / 25.309|
|R1|lingbot|accepted formal|15|3|-5.696 / -4.873 / 4.446|-5.490 / -1.321 / 2.333|-8.256 / -1.856 / 0.058|5.713 / 5.848 / 10.866|0.305 / 0.348 / 0.596|0.847 / 0.884 / 0.986|
|R1|lingbot|rejected candidate diagnostic|50|8|-1.945 / 4.624 / 6.640|-8.566 / -3.462 / 7.397|-21.044 / -14.507 / -1.919|6.024 / 16.120 / 23.466|0.166 / 0.515 / 0.726|0.794 / 1.035 / 1.326|
|RM|lingbot|accepted formal|15|3|-6.447 / -5.512 / 4.446|-5.490 / -3.439 / 1.048|-8.256 / -2.044 / 0.750|5.972 / 7.346 / 10.866|0.044 / 0.348 / 0.433|4.848 / 5.572 / 8.359|
|RM|lingbot|rejected candidate diagnostic|50|8|-2.955 / 3.815 / 7.082|-10.429 / -4.023 / 6.429|-22.679 / -14.363 / -5.506|8.587 / 15.677 / 25.414|0.080 / 0.649 / 1.105|3.647 / 5.169 / 8.075|
|R1F|lingbot|accepted formal|20|3|-5.696 / -4.873 / 4.446|-5.490 / -1.321 / 2.333|-8.256 / -1.856 / 0.058|5.713 / 5.848 / 10.866|0.305 / 0.348 / 0.596|0.838 / 0.939 / 14.634|
|R1F|lingbot|rejected candidate diagnostic|45|8|-3.567 / 3.815 / 7.084|-10.599 / -4.023 / 7.049|-22.679 / -14.363 / -5.352|8.587 / 15.677 / 24.906|0.080 / 0.712 / 1.105|12.072 / 22.866 / 26.764|

## 逐帧结果

|完整帧 ID|方法|状态|诊断来源|接受/尝试|板角点|Δx|Δy|Δz|中心距离|yaw|主耗时 s|Wall s|拒绝原因|
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
|L01_wrist_charuco_20260915_093818_877801116|FDP|accepted|formal_accepted|5/5|4|N/A|N/A|N/A|N/A|N/A|1.267|N/A||
|L01_wrist_charuco_20260915_093818_877801116|V5-original|accepted|formal_accepted|5/5|4|N/A|N/A|N/A|N/A|N/A|14.054|14.858||
|L01_wrist_charuco_20260915_093818_877801116|BCM|accepted|formal_accepted|5/5|4|N/A|N/A|N/A|N/A|N/A|13.867|14.905||
|L01_wrist_charuco_20260915_093818_877801116|R1|rejected|unavailable|0/5|4|N/A|N/A|N/A|N/A|N/A|0.795|1.821|ambiguous_inner_outer_surface_hypotheses|
|L01_wrist_charuco_20260915_093818_877801116|RM|rejected|unavailable|0/5|4|N/A|N/A|N/A|N/A|N/A|4.092|5.081|ambiguous_inner_outer_surface_hypotheses|
|L01_wrist_charuco_20260915_093818_877801116|R1F|accepted|formal_accepted|5/5|4|N/A|N/A|N/A|N/A|N/A|14.634|15.658||
|L02_wrist_charuco_20260915_100236_358935353|FDP|accepted|formal_accepted|5/5|47|5.184|-3.979|-16.267|17.531|0.368|1.274|N/A||
|L02_wrist_charuco_20260915_100236_358935353|V5-original|rejected|rejected_candidate_diagnostic|0/5|47|5.388|-5.453|-19.028|20.514|0.641|19.683|20.472|ambiguous_inner_outer_surface_hypotheses|
|L02_wrist_charuco_20260915_100236_358935353|BCM|rejected|rejected_candidate_diagnostic|0/5|47|5.388|-5.453|-19.028|20.514|0.641|19.358|20.370|ambiguous_inner_outer_surface_hypotheses|
|L02_wrist_charuco_20260915_100236_358935353|R1|rejected|rejected_candidate_diagnostic|0/5|47|6.078|-4.075|-19.706|21.020|0.407|0.903|1.921|ambiguous_inner_outer_surface_hypotheses|
|L02_wrist_charuco_20260915_100236_358935353|RM|rejected|rejected_candidate_diagnostic|0/5|47|5.388|-5.453|-19.028|20.514|0.641|5.044|6.082|ambiguous_inner_outer_surface_hypotheses|
|L02_wrist_charuco_20260915_100236_358935353|R1F|rejected|rejected_candidate_diagnostic|0/5|47|5.388|-5.453|-19.028|20.514|0.641|20.307|21.323|ambiguous_inner_outer_surface_hypotheses|
|L03_00_wrist_charuco_20260915_104002_497962253|FDP|accepted|formal_accepted|5/5|65|4.476|-5.014|-15.102|16.530|1.021|1.272|N/A||
|L03_00_wrist_charuco_20260915_104002_497962253|V5-original|rejected|rejected_candidate_diagnostic|0/5|65|5.851|-3.229|-22.679|23.643|0.423|23.096|23.879|ambiguous_inner_outer_surface_hypotheses;visible_shell_residual_or_coverage_too_low|
|L03_00_wrist_charuco_20260915_104002_497962253|BCM|rejected|rejected_candidate_diagnostic|0/5|65|5.851|-3.229|-22.679|23.643|0.423|22.867|23.879|ambiguous_inner_outer_surface_hypotheses;visible_shell_residual_or_coverage_too_low|
|L03_00_wrist_charuco_20260915_104002_497962253|R1|rejected|rejected_candidate_diagnostic|0/5|65|5.356|-2.849|-21.044|21.901|0.436|1.113|2.121|ambiguous_inner_outer_surface_hypotheses|
|L03_00_wrist_charuco_20260915_104002_497962253|RM|rejected|rejected_candidate_diagnostic|0/5|65|5.851|-3.229|-22.679|23.643|0.423|5.448|6.483|ambiguous_inner_outer_surface_hypotheses;visible_shell_residual_or_coverage_too_low|
|L03_00_wrist_charuco_20260915_104002_497962253|R1F|rejected|rejected_candidate_diagnostic|0/5|65|5.851|-3.229|-22.679|23.643|0.423|24.004|25.035|ambiguous_inner_outer_surface_hypotheses;visible_shell_residual_or_coverage_too_low|
|L03_10_wrist_charuco_20260915_103928_398335507|FDP|accepted|formal_accepted|5/5|55|3.354|-6.793|-13.928|15.856|0.100|1.276|N/A||
|L03_10_wrist_charuco_20260915_103928_398335507|V5-original|rejected|rejected_candidate_diagnostic|0/5|55|7.084|-10.599|-21.395|24.906|0.865|24.158|24.984|ambiguous_inner_outer_surface_hypotheses;visible_shell_residual_or_coverage_too_low|
|L03_10_wrist_charuco_20260915_103928_398335507|BCM|rejected|rejected_candidate_diagnostic|0/5|55|7.084|-10.599|-21.395|24.906|0.865|23.969|25.030|ambiguous_inner_outer_surface_hypotheses;visible_shell_residual_or_coverage_too_low|
|L03_10_wrist_charuco_20260915_103928_398335507|R1|rejected|rejected_candidate_diagnostic|0/5|55|6.640|-8.566|-20.813|23.466|0.726|1.227|2.222|ambiguous_inner_outer_surface_hypotheses;visible_shell_residual_or_coverage_too_low|
|L03_10_wrist_charuco_20260915_103928_398335507|RM|rejected|rejected_candidate_diagnostic|0/5|55|7.082|-10.429|-22.067|25.414|0.986|6.211|7.235|ambiguous_inner_outer_surface_hypotheses;visible_shell_residual_or_coverage_too_low|
|L03_10_wrist_charuco_20260915_103928_398335507|R1F|rejected|rejected_candidate_diagnostic|0/5|55|7.084|-10.599|-21.395|24.906|0.865|25.225|26.240|ambiguous_inner_outer_surface_hypotheses;visible_shell_residual_or_coverage_too_low|
|L04_00_wrist_charuco_20260915_104435_858773771|FDP|accepted|formal_accepted|5/5|78|1.002|1.439|-11.623|11.755|0.810|1.177|N/A||
|L04_00_wrist_charuco_20260915_104435_858773771|V5-original|rejected|rejected_candidate_diagnostic|0/5|78|4.062|-5.129|-13.853|15.321|0.080|21.064|21.873|ambiguous_inner_outer_surface_hypotheses|
|L04_00_wrist_charuco_20260915_104435_858773771|BCM|rejected|rejected_candidate_diagnostic|0/5|78|4.062|-5.129|-13.853|15.321|0.080|20.972|22.024|ambiguous_inner_outer_surface_hypotheses|
|L04_00_wrist_charuco_20260915_104435_858773771|R1|rejected|rejected_candidate_diagnostic|0/5|78|4.894|-5.357|-13.937|15.713|0.675|1.276|2.275|ambiguous_inner_outer_surface_hypotheses|
|L04_00_wrist_charuco_20260915_104435_858773771|RM|rejected|rejected_candidate_diagnostic|0/5|78|4.062|-5.129|-13.853|15.321|0.080|5.293|6.332|ambiguous_inner_outer_surface_hypotheses|
|L04_00_wrist_charuco_20260915_104435_858773771|R1F|rejected|rejected_candidate_diagnostic|0/5|78|4.062|-5.129|-13.853|15.321|0.080|22.186|23.226|ambiguous_inner_outer_surface_hypotheses|
|L04_10_wrist_charuco_20260915_104717_786588568|FDP|accepted|formal_accepted|5/5|77|3.415|-4.653|-8.847|10.563|0.640|1.179|N/A||
|L04_10_wrist_charuco_20260915_104717_786588568|V5-original|accepted|formal_accepted|5/5|77|4.400|-7.201|-9.766|12.907|0.414|21.406|22.225||
|L04_10_wrist_charuco_20260915_104717_786588568|BCM|accepted|formal_accepted|5/5|77|4.400|-7.201|-9.766|12.907|0.414|21.193|22.229||
|L04_10_wrist_charuco_20260915_104717_786588568|R1|accepted|formal_accepted|5/5|77|4.446|-5.490|-8.256|10.866|0.348|0.986|1.971||
|L04_10_wrist_charuco_20260915_104717_786588568|RM|accepted|formal_accepted|5/5|77|4.446|-5.490|-8.256|10.866|0.348|8.359|9.391||
|L04_10_wrist_charuco_20260915_104717_786588568|R1F|accepted|formal_accepted|5/5|77|4.446|-5.490|-8.256|10.866|0.348|0.985|2.021||
|L04_wrist_charuco_20260915_104358_532673829|FDP|accepted|formal_accepted|5/5|71|1.694|-2.421|-9.970|10.399|0.314|1.196|N/A||
|L04_wrist_charuco_20260915_104358_532673829|V5-original|rejected|rejected_candidate_diagnostic|0/5|71|3.567|-4.816|-14.872|16.034|0.203|22.156|22.976|ambiguous_inner_outer_surface_hypotheses|
|L04_wrist_charuco_20260915_104358_532673829|BCM|rejected|rejected_candidate_diagnostic|0/5|71|3.567|-4.816|-14.872|16.034|0.203|22.243|23.277|ambiguous_inner_outer_surface_hypotheses|
|L04_wrist_charuco_20260915_104358_532673829|R1|rejected|rejected_candidate_diagnostic|0/5|71|4.355|-5.186|-15.076|16.527|0.166|0.888|1.921|ambiguous_inner_outer_surface_hypotheses|
|L04_wrist_charuco_20260915_104358_532673829|RM|rejected|rejected_candidate_diagnostic|0/5|71|3.567|-4.816|-14.872|16.034|0.203|5.422|6.434|ambiguous_inner_outer_surface_hypotheses|
|L04_wrist_charuco_20260915_104358_532673829|R1F|rejected|rejected_candidate_diagnostic|0/5|71|3.567|-4.816|-14.872|16.034|0.203|22.866|23.880|ambiguous_inner_outer_surface_hypotheses|
|R01_wrist_charuco_20260915_093900_967150252|FDP|accepted|formal_accepted|5/5|3|N/A|N/A|N/A|N/A|N/A|1.265|N/A||
|R01_wrist_charuco_20260915_093900_967150252|V5-original|rejected|unavailable|0/5|3|N/A|N/A|N/A|N/A|N/A|11.386|12.198|ambiguous_inner_outer_surface_hypotheses|
|R01_wrist_charuco_20260915_093900_967150252|BCM|rejected|unavailable|0/5|3|N/A|N/A|N/A|N/A|N/A|11.214|12.249|ambiguous_inner_outer_surface_hypotheses|
|R01_wrist_charuco_20260915_093900_967150252|R1|rejected|unavailable|0/5|3|N/A|N/A|N/A|N/A|N/A|0.966|1.971|ambiguous_inner_outer_surface_hypotheses|
|R01_wrist_charuco_20260915_093900_967150252|RM|rejected|unavailable|0/5|3|N/A|N/A|N/A|N/A|N/A|3.647|4.678|ambiguous_inner_outer_surface_hypotheses|
|R01_wrist_charuco_20260915_093900_967150252|R1F|rejected|unavailable|0/5|3|N/A|N/A|N/A|N/A|N/A|12.072|13.101|ambiguous_inner_outer_surface_hypotheses|
|R01_wrist_charuco_20260915_094033_680788016|FDP|accepted|formal_accepted|5/5|9|2.314|5.333|2.860|6.479|1.501|1.373|N/A||
|R01_wrist_charuco_20260915_094033_680788016|V5-original|accepted|formal_accepted|5/5|9|-6.447|-3.439|0.750|7.346|0.433|14.860|15.659||
|R01_wrist_charuco_20260915_094033_680788016|BCM|accepted|formal_accepted|5/5|9|-6.447|-3.439|0.750|7.346|0.433|14.736|15.764||
|R01_wrist_charuco_20260915_094033_680788016|R1|accepted|formal_accepted|5/5|9|-5.696|-1.321|0.058|5.848|0.596|0.847|1.871||
|R01_wrist_charuco_20260915_094033_680788016|RM|accepted|formal_accepted|5/5|9|-6.447|-3.439|0.750|7.346|0.433|4.848|5.881||
|R01_wrist_charuco_20260915_094033_680788016|R1F|accepted|formal_accepted|5/5|9|-5.696|-1.321|0.058|5.848|0.596|0.838|1.872||
|R02_wrist_charuco_20260915_100308_809523978|FDP|accepted|formal_accepted|5/5|77|0.629|6.075|5.762|8.397|0.872|1.377|N/A||
|R02_wrist_charuco_20260915_100308_809523978|V5-original|accepted|formal_accepted|5/5|77|-5.512|1.048|-2.044|5.972|0.044|19.025|19.868||
|R02_wrist_charuco_20260915_100308_809523978|BCM|accepted|formal_accepted|5/5|77|-5.512|1.048|-2.044|5.972|0.044|18.852|19.868||
|R02_wrist_charuco_20260915_100308_809523978|R1|accepted|formal_accepted|5/5|77|-4.873|2.333|-1.856|5.713|0.305|0.884|1.921||
|R02_wrist_charuco_20260915_100308_809523978|RM|accepted|formal_accepted|5/5|77|-5.512|1.048|-2.044|5.972|0.044|5.572|6.587||
|R02_wrist_charuco_20260915_100308_809523978|R1F|accepted|formal_accepted|5/5|77|-4.873|2.333|-1.856|5.713|0.305|0.894|1.923||
|R03_wrist_charuco_20260915_103743_184821162|FDP|accepted|formal_accepted|5/5|100|5.409|4.084|3.102|7.454|1.322|1.371|N/A||
|R03_wrist_charuco_20260915_103743_184821162|V5-original|rejected|rejected_candidate_diagnostic|0/5|100|-3.567|7.049|-5.352|9.542|0.800|24.244|25.033|mask_touches_image_border;visible_shell_residual_or_coverage_too_low|
|R03_wrist_charuco_20260915_103743_184821162|BCM|rejected|rejected_candidate_diagnostic|0/5|100|-3.567|7.049|-5.352|9.542|0.800|24.369|25.381|mask_touches_image_border;visible_shell_residual_or_coverage_too_low|
|R03_wrist_charuco_20260915_103743_184821162|R1|rejected|rejected_candidate_diagnostic|0/5|100|-1.945|5.369|-1.919|6.024|0.470|1.105|2.123|ambiguous_inner_outer_surface_hypotheses;mask_touches_image_border|
|R03_wrist_charuco_20260915_103743_184821162|RM|rejected|rejected_candidate_diagnostic|0/5|100|-2.955|6.429|-5.506|8.966|0.656|8.075|9.092|mask_touches_image_border;visible_shell_residual_or_coverage_too_low|
|R03_wrist_charuco_20260915_103743_184821162|R1F|rejected|rejected_candidate_diagnostic|0/5|100|-3.567|7.049|-5.352|9.542|0.800|25.173|26.186|mask_touches_image_border;visible_shell_residual_or_coverage_too_low|
|R04_00_wrist_charuco_20260915_104526_910331328|FDP|accepted|formal_accepted|5/5|100|4.798|6.785|0.681|8.337|1.342|1.367|N/A||
|R04_00_wrist_charuco_20260915_104526_910331328|V5-original|rejected|rejected_candidate_diagnostic|0/5|100|-1.789|6.266|-5.592|8.587|1.105|22.415|23.227|ambiguous_inner_outer_surface_hypotheses|
|R04_00_wrist_charuco_20260915_104526_910331328|BCM|rejected|rejected_candidate_diagnostic|0/5|100|-1.789|6.266|-5.592|8.587|1.105|21.925|22.976|ambiguous_inner_outer_surface_hypotheses|
|R04_00_wrist_charuco_20260915_104526_910331328|R1|rejected|rejected_candidate_diagnostic|0/5|100|-1.451|7.397|-11.373|13.644|0.560|0.794|1.871|ambiguous_inner_outer_surface_hypotheses|
|R04_00_wrist_charuco_20260915_104526_910331328|RM|rejected|rejected_candidate_diagnostic|0/5|100|-1.789|6.266|-5.592|8.587|1.105|4.725|5.781|ambiguous_inner_outer_surface_hypotheses|
|R04_00_wrist_charuco_20260915_104526_910331328|R1F|rejected|rejected_candidate_diagnostic|0/5|100|-1.789|6.266|-5.592|8.587|1.105|22.823|23.831|ambiguous_inner_outer_surface_hypotheses|
|R04_10_wrist_charuco_20260915_105839_488564574|FDP|accepted|formal_accepted|5/5|100|6.246|0.145|5.395|8.254|1.360|1.380|N/A||
|R04_10_wrist_charuco_20260915_105839_488564574|V5-original|rejected|rejected_candidate_diagnostic|0/5|100|-2.687|4.882|-8.569|10.222|0.784|25.487|26.285|ambiguous_inner_outer_surface_hypotheses|
|R04_10_wrist_charuco_20260915_105839_488564574|BCM|rejected|rejected_candidate_diagnostic|0/5|100|-2.687|4.882|-8.569|10.222|0.784|25.309|26.335|ambiguous_inner_outer_surface_hypotheses|
|R04_10_wrist_charuco_20260915_105839_488564574|R1|rejected|rejected_candidate_diagnostic|0/5|100|-1.472|6.692|-10.278|12.352|0.601|1.326|2.372|ambiguous_inner_outer_surface_hypotheses|
|R04_10_wrist_charuco_20260915_105839_488564574|RM|rejected|rejected_candidate_diagnostic|0/5|100|-2.687|4.882|-8.569|10.222|0.784|4.802|5.832|ambiguous_inner_outer_surface_hypotheses|
|R04_10_wrist_charuco_20260915_105839_488564574|R1F|rejected|rejected_candidate_diagnostic|0/5|100|-2.687|4.882|-8.569|10.222|0.784|26.764|27.840|ambiguous_inner_outer_surface_hypotheses|

## 如何阅读拒绝候选

拒绝候选的 Δx/Δy/Δz/yaw 只说明算法在门禁之前形成了什么候选；它不代表算法向上层正式输出了这个位姿，也不应和 accepted 正式位姿混合计算精度均值。C01/L01 和 C08/误标 R01 左腕没有有效板参考，因此无论接受还是拒绝，相关差距均为 N/A。FDP raw 本批没有拒绝运行。