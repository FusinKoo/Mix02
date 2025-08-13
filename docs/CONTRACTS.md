# Mix02 契约说明

| Stage | CLI | Input | Output | Spec | Notes |
| ----- | --- | ----- | ------ | ---- | ----- |
| 00 | env_probe | N/A | env.txt | - | 确认运行环境 |
| 05 | prep_audio | `input/<song>.wav` | `work/<song>/stage-05/master_48k32f.wav` | 48k/32f/stereo | 校验输入存在 |
| 10 | separate_stems | `stage-05/master_48k32f.wav` | `stage-10/{Vocal,Drums,Bass,Other}.raw` | 48k/32f/stereo | 分轨占位 |
| 21 | extract_lead | `stage-10/Vocal.raw` | `stage-21/Lead.raw` | 48k/32f/stereo | 提取主人声 |
| 25 | dereverb_denoise | `stage-21/Lead.raw` | `stage-25/Lead_DRY.raw` | 48k/32f/stereo | 去混响+降噪 |
| 30 | build_rvc_index | `assets/guide.wav` | `models/rvc/G_8200.index` | 48k/32f/stereo | 可重复运行 |
| 35 | rvc_convert | `stage-25/Lead_DRY.raw` | `stage-35/Lead_RVC.raw` | 48k/32f/stereo | RVC 转换 |
| 40-43 | track_chain | `<stem>.raw` | `<stage>/0x_<Name>_stem.wav` | 48k/32f/stereo | 各轨处理 |
| 50 | mix_bus | 各轨 stem | `output/<song>/final_mix.wav` | 48k/32f/stereo | 总线混音 |
| 60 | qc_report | 输出目录 | `qc.json` | - | 生成质检报告 |
| 99 | finalize_run | 输出目录 | 标记完成 | - | 归档运行 |

## 退出码

- `0` 成功
- `1` 未知异常
- `12` 输入不合规
- `22` 模型缺失
- `32` 资源不足
- `42` 响度不达标（占位实现永不触发）

内部音频统一规格：**48 kHz / 32-bit float / Stereo**。
