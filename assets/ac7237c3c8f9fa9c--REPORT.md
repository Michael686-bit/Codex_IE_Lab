# 单帧离线运行结果

**状态：拒绝输出有效位姿；以下仅为诊断候选。**

- 拒绝原因：`['ambiguous_rim_planes']`
- 输入哈希全部核验，运行前后未变；保存 FDP 请求与冻结输入一致，归一化逐元素复现。
- ROI/FDP 是对照，不是真值；未调用服务、连接机器人或生成抓取目标。

## 几何候选

```json
{
  "top_center_base_m": [
    1.3972527801669088,
    0.2551825794051954,
    0.5736849891489644
  ],
  "box_center_base_m": [
    1.3964296671208971,
    0.2550179212400171,
    0.48618901568388356
  ],
  "corners_base_m": [
    [
      1.2363857675654972,
      0.4465473471762091,
      0.5748382075338593
    ],
    [
      1.258595903855626,
      0.04716480452903331,
      0.5753808627197162
    ],
    [
      1.5581197927683204,
      0.06381781163418172,
      0.5725317707640695
    ],
    [
      1.5359096564781916,
      0.4632003542813575,
      0.5719891155782125
    ]
  ],
  "axes_base": {
    "length": [
      -0.05552534072532224,
      0.9984563566179393,
      -0.0013566379646424071
    ],
    "width": [
      -0.9984129630423149,
      -0.05551002368382804,
      0.009496973185489426
    ],
    "height": [
      0.00940700624013436,
      0.0018818076020378704,
      0.9999539824580664
    ]
  },
  "short_edge_midpoints_base_m": [
    [
      1.3861477120218444,
      0.4548738507287833,
      0.5734136615560359
    ],
    [
      1.4083578483119732,
      0.055491308081607515,
      0.5739563167418928
    ]
  ],
  "dimensions_m": [
    0.4,
    0.3,
    0.175
  ],
  "canonicalized_by_180_deg": false,
  "T_base_link_from_4317_semantic": [
    [
      -0.05552534072532224,
      -0.9984129630423149,
      0.00940700624013436,
      1.3964296671208971
    ],
    [
      0.9984563566179393,
      -0.05551002368382804,
      0.0018818076020378704,
      0.2550179212400171
    ],
    [
      -0.0013566379646424071,
      0.009496973185489426,
      0.9999539824580664,
      0.48618901568388356
    ],
    [
      0.0,
      0.0,
      0.0,
      1.0
    ]
  ],
  "evidence": {
    "normal_and_edge_locations": "fitted from RGB edge pixels with frozen depth",
    "dimensions_and_top_to_center_offset": "4317 dimension prior",
    "corners": "intersections of fitted edges, not directly measured corner pixels",
    "outer_rim_identity": "hypothesis checked by edge support, not independently labelled",
    "edge_order": [
      "+length (short)",
      "+width (long)",
      "-length (short)",
      "-width (long)"
    ],
    "edge_order_frame": "pre-canonical rectangle; + and - exchange after a 180-degree flip"
  }
}
```

## 对照与坐标验证

```json
{
  "comparison": {
    "available": true,
    "references_are_ground_truth": false,
    "candidate_is_accepted": false,
    "B_yaw_deg": 93.18300761027903,
    "FDP_yaw_deg": 91.28851158941187,
    "ROI_yaw_deg": 90.0,
    "B_vs_FDP_box_pose": {
      "translation_l2_m": 0.020114070528980784,
      "rotation_geodesic_deg": 3.5958849788462426,
      "matrix_max_abs": 0.04829887243943303
    },
    "B_vs_FDP_yaw_180_deg": 1.894496020867166,
    "B_vs_ROI_yaw_180_deg": 3.1830076102790343,
    "B_minus_ROI_top_center_m": [
      0.1418232738650289,
      0.008757040150053186,
      -0.025667668645988018
    ],
    "B_vs_ROI_top_xy_m": 0.1420933733922333,
    "B_minus_FDP_top_center_m": [
      -0.0002485021207738747,
      0.0017657699187574316,
      -0.01955172623680934
    ],
    "B_vs_FDP_top_xy_m": 0.001783170409696656,
    "analysis_mask_source": "final_roi"
  },
  "coordinates": {
    "available": true,
    "rigid_transform": {
      "valid": true,
      "shape": [
        4,
        4
      ],
      "finite": true,
      "rotation_determinant": 0.9999999999999998,
      "rotation_orthogonality_error_fro": 1.5703251285422598e-16,
      "bottom_row_error_l2": 0.0
    },
    "edge_lengths_m": [
      0.4,
      0.2999999999999998,
      0.4,
      0.2999999999999998
    ],
    "dimensions_correct": true,
    "corner_plane_max_residual_m": 4.618701254788249e-17,
    "top_to_center_residual_m": 0.0,
    "projection_roundtrip_max_m": 3.3306690738754696e-16,
    "canonical_length_base_Y_nonnegative": true,
    "ok": true
  }
}
```

## 限制

平面与矩形来源于同一冻结深度中的 RGB 边缘。高分位高度和近竖直是先验；
箱沿外缘/内缘与筋条身份未经独立标注。多个可行平面时不能用点数最多替代箱口身份判断。
尺寸与半高偏移来自 4317 合同；四角是拟合交点，不是逐角直接深度测量。
默认使用原 float32 深度，FDP 传输使用 uint16 毫米截断；具体差值见 input_manifest。
本轮只有一帧与一次本机计时，不能作为毫米精度、成功率、p95 或 Orin 性能证据。

## 箱壁几何中心分支（用户补充允许的同帧对照）

以下顶面和四角是由中心及尺寸推断，不能解读为直接恢复的箱沿。

```json
{
  "ok": false,
  "rejection_reasons": [
    "insufficient_support_edge_2",
    "rectangle_inlier_fraction_too_low",
    "wall_height_extent_incompatible_with_upright_model"
  ],
  "candidate": {
    "top_center_base_m": [
      1.3903156373961583,
      0.23896142749422308,
      0.5926991637825315
    ],
    "box_center_base_m": [
      1.3903156373961583,
      0.23896142749422308,
      0.5051991637825315
    ],
    "corners_base_m": [
      [
        1.234743561323904,
        0.43465846157131066,
        0.5926991637825315
      ],
      [
        1.2460066659823854,
        0.034817064923274556,
        0.5926991637825315
      ],
      [
        1.5458877134684126,
        0.043264393417135526,
        0.5926991637825315
      ],
      [
        1.5346246088099311,
        0.44310579006517165,
        0.5926991637825315
      ]
    ],
    "axes_base": {
      "length": [
        -0.02815776164620325,
        0.9996034916200901,
        0.0
      ],
      "width": [
        -0.9996034916200901,
        -0.02815776164620325,
        0.0
      ],
      "height": [
        0.0,
        0.0,
        1.0
      ]
    },
    "short_edge_midpoints_base_m": [
      [
        1.3846840850669175,
        0.43888212581824115,
        0.5926991637825315
      ],
      [
        1.395947189725399,
        0.03904072917020504,
        0.5926991637825315
      ]
    ],
    "dimensions_m": [
      0.4,
      0.3,
      0.175
    ],
    "canonicalized_by_180_deg": false,
    "T_base_link_from_4317_semantic": [
      [
        -0.02815776164620325,
        -0.9996034916200901,
        0.0,
        1.3903156373961583
      ],
      [
        0.9996034916200901,
        -0.02815776164620325,
        0.0,
        0.23896142749422308
      ],
      [
        0.0,
        0.0,
        1.0,
        0.5051991637825315
      ],
      [
        0.0,
        0.0,
        0.0,
        1.0
      ]
    ],
    "evidence": {
      "center_xy_and_yaw": "fixed-size fit to projected vertical-wall samples",
      "center_z": "midpoint of robust wall-height range; missing/occluded surfaces can bias this",
      "top_center_and_corners": "model-inferred from center + half height, not observed rim",
      "roll_pitch": "upright prior",
      "dimensions": "4317 fixed prior"
    }
  },
  "comparison": {
    "available": true,
    "references_are_ground_truth": false,
    "candidate_is_accepted": false,
    "wall_yaw_deg": 91.6135341684403,
    "FDP_yaw_deg": 91.28851158941187,
    "ROI_yaw_deg": 90.0,
    "wall_vs_FDP_box_pose": {
      "translation_l2_m": 0.016520448522901663,
      "rotation_geodesic_deg": 3.5490924546455545,
      "matrix_max_abs": 0.05770587867956739
    },
    "wall_vs_FDP_yaw_180_deg": 0.32502257902842757,
    "wall_vs_ROI_yaw_180_deg": 1.613534168440296,
    "wall_minus_ROI_top_center_m": [
      0.13488613109427838,
      -0.007464111760919129,
      -0.00665349401242088
    ],
    "wall_vs_ROI_top_xy_m": 0.13509249174533108,
    "wall_minus_FDP_top_center_m": [
      -0.007185644891524401,
      -0.014455381992214883,
      -0.0005375516032422034
    ],
    "wall_vs_FDP_top_xy_m": 0.016142848603884662
  }
}
```

## 第二轮：多平面侧壁分解与几何中心

至少需要三个已分解侧壁面，且其中一组必须观测到相对两面；高度由各面与已知箱高的联合区间约束。

```json
{
  "ok": false,
  "rejection_reasons": [
    "multiplane_wall_heights_inconsistent_with_model"
  ],
  "candidate": {
    "top_center_base_m": [
      1.3987238492945724,
      0.23670176206444543,
      0.5815878974014812
    ],
    "box_center_base_m": [
      1.3987238492945724,
      0.23670176206444543,
      0.4940878974014812
    ],
    "corners_base_m": [
      [
        1.2509713019253514,
        0.43836778484941064,
        0.5815878974014812
      ],
      [
        1.2464951806843876,
        0.038392830210203024,
        0.5815878974014812
      ],
      [
        1.5464763966637933,
        0.03503573927948021,
        0.5815878974014812
      ],
      [
        1.5509525179047572,
        0.43501069391868785,
        0.5815878974014812
      ]
    ],
    "axes_base": {
      "length": [
        0.011190303102409385,
        0.999937386598019,
        0.0
      ],
      "width": [
        -0.999937386598019,
        0.011190303102409385,
        0.0
      ],
      "height": [
        0.0,
        0.0,
        1.0
      ]
    },
    "short_edge_midpoints_base_m": [
      [
        1.4009619099150543,
        0.43668923938404924,
        0.5815878974014812
      ],
      [
        1.3964857886740905,
        0.03671428474484162,
        0.5815878974014812
      ]
    ],
    "dimensions_m": [
      0.4,
      0.3,
      0.175
    ],
    "canonicalized_by_180_deg": false,
    "T_base_link_from_4317_semantic": [
      [
        0.011190303102409385,
        -0.999937386598019,
        0.0,
        1.3987238492945724
      ],
      [
        0.999937386598019,
        0.011190303102409385,
        0.0,
        0.23670176206444543
      ],
      [
        0.0,
        0.0,
        1.0,
        0.4940878974014812
      ],
      [
        0.0,
        0.0,
        0.0,
        1.0
      ]
    ],
    "evidence": {
      "center_xy_and_yaw": "joint known-size fit to explicitly decomposed vertical wall planes",
      "center_z": "intersection of per-face containment intervals under known-height upright prior",
      "dimensions": "4317 fixed prior",
      "roll_pitch": "upright prior",
      "top_center_and_corners": "model-inferred; not direct rim observations"
    }
  },
  "fit": {
    "score": 943.7609731397342,
    "observed_faces": [
      "length:+1",
      "width:+1",
      "width:-1"
    ],
    "opposite_pair_observed": true,
    "rival_count": 0,
    "matches": [
      {
        "family": "width",
        "sign": -1,
        "plane_index": 0,
        "offset_residual_m": 0.013607220894304772,
        "angle_residual_deg": 3.23316577816166,
        "finite_face_containment": 1.0,
        "point_count": 1810
      },
      {
        "family": "length",
        "sign": 1,
        "plane_index": 3,
        "offset_residual_m": 0.00012442784041472033,
        "angle_residual_deg": 0.0,
        "finite_face_containment": 1.0,
        "point_count": 413
      },
      {
        "family": "width",
        "sign": 1,
        "plane_index": 5,
        "offset_residual_m": 0.0030799722187193623,
        "angle_residual_deg": 2.2155541421984157,
        "finite_face_containment": 1.0,
        "point_count": 245
      }
    ]
  },
  "comparison": {
    "available": true,
    "references_are_ground_truth": false,
    "candidate_is_accepted": false,
    "multiplane_yaw_deg": 89.35882947874808,
    "FDP_yaw_deg": 91.28851158941187,
    "ROI_yaw_deg": 90.0,
    "multiplane_vs_FDP_box_pose": {
      "translation_l2_m": 0.022932069339829657,
      "rotation_geodesic_deg": 4.047750143684691,
      "matrix_max_abs": 0.05770587867956739
    },
    "multiplane_vs_FDP_yaw_180_deg": 1.9296821106637907,
    "multiplane_vs_ROI_yaw_180_deg": 0.6411705212519223,
    "multiplane_minus_ROI_top_center_m": [
      0.1432943429926925,
      -0.00972377719069678,
      -0.01776476039347119
    ],
    "multiplane_vs_ROI_top_xy_m": 0.14362388581486618,
    "multiplane_minus_FDP_top_center_m": [
      0.0012225670068897188,
      -0.016715047421992535,
      -0.011648817984292514
    ],
    "multiplane_vs_FDP_top_xy_m": 0.016759698100079087
  }
}
```

## 诊断图

![RGB crop](rgb_crop.png)

![Cloud](pointcloud_diagnostic.png)

![Wall center](box_center_diagnostic.png)

![Multiplane center](multiplane_center_diagnostic.png)