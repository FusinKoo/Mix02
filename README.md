# Mix02
# Mix02 模块化音频管线（独立 CLI 版，最优解预设）

> 目标：以**最高稳定性与质量优先**为原则，把“分轨 → 主人声提取 → 去混响+降噪 → RVC 音色替换 → 每轨处理 → 总线混合 → 质检”的全过程拆成**完全独立**的 CLI 模块。模块之间仅以**文件为契约**衔接，可单步运行、断点续跑、随时替换任一环节。

---

## 设计原则

* **完全解耦**：每个 CLI 只做一件事；只读写磁盘，不共享内存状态。
* **幂等**：若目标产物 + sidecar 校验通过，默认跳过；`--force` 可重算。
* **稳定优先**：默认参数为“Best-Quality（2025-Q3）”预设，同时提供“Safe-VRAM / Fast”两档可选。
* **统一规格**：内部用 **48 kHz / 32-bit float / Stereo**；最终导出 **24-bit / 48 kHz WAV**。
* **严谨留痕**：每步产出 `*.json` sidecar（sha256/时长/峰值/TP/综合与短时 LUFS/均值 RMS），失败则输出 `*.error.json`。
* **文件契约**：上一步的**固定命名**输出，作为下一步的**唯一输入**；避免隐式依赖。

---

## 目录结构与命名规范

```
/workspace/Mix02/
  input/                         # 原始音频输入（一次处理一首）
  work/<SongName>/stage-XX/      # 各阶段中间产物（含 .json sidecar）
  output/<SongName>/             # 最终产物与报告
  models/
    uvr/                         # 分轨/去回声相关模型
    rvc/                         # RVC 模型与（可选）引导索引 *.index
    hubert/                      # hubert_base.pt（RVC 内容编码器）
    f0/                          # rmvpe.pt 等 F0 估计模型
    rnnoise/                     # rnnoise 模型（可选）
  logs/                          # 结构化日志（*.jsonl）
  bin/                           # 各 CLI 入口脚本/可执行
  presets/                       # 参数预设（*.yaml）
```

**关键文件命名**：

* 分轨输出：`Vocal.raw`、`Drums.raw`、`Bass.raw`、`Other.raw`（32f/48k/立体声）
* 主人声：`Lead.raw`
* 干声：`Lead_DRY.raw`
* RVC：`Lead_RVC.raw`（或 `.wav`）
* 轨道处理后：`01_Drums_stem.wav`、`02_Bass_stem.wav`、`03_Other_stem.wav`、`04_Lead_RVC_processed.wav`
* 总线：`99_Final_<SongName>_mix_24b48k.wav`
* 报告：`QC.md`，以及 `RUNLOG.json`

---

## 环境与依赖（三种安装方式）

* 操作系统：Linux 或 macOS（建议 GPU/CUDA 环境）
* 最小依赖：`ffmpeg (>=6.0)`、`sox`、`python (3.10+)`、`git`

### A) Docker（推荐，最稳）

1. `docker build -t mix02:latest -f docker/Dockerfile .`
2. `docker run --gpus all -v $PWD:/workspace -it mix02:latest bash`

### B) Conda

```
conda env create -f env/conda.yml
conda activate mix02
```

### C) Pip（干净虚拟环境）

```
python -m venv .venv && source .venv/bin/activate
pip install -r env/requirements.txt
```

> 我们同时提供三套 `presets/*.yaml`：`best-quality.yaml`、`safe-vram.yaml`、`fast.yaml`，可在任何 CLI 用 `--preset` 指定。

---

## 模型资产（必须放置到位，文件名固定）

> **不含下载链接**；只要把下列文件放到指定路径，所有 CLI 即可工作。

* **UVR 分轨/去回声**（任选性能优良的一组，文件名如下）：

  * `models/uvr/MDX23C-8KFFT-InstVoc_HQ.ckpt`
  * `models/uvr/UVR-MDXNET-KARAOKE-V2.onnx`（主人声提取）
  * （可选去回声模型）`models/uvr/DeReverb-Denoise.onnx`
* **RVC**：

  * 你的固定模型（示例名）：`models/rvc/G_8200.pth`
  * （可选）引导索引：`models/rvc/G_8200.index`
  * 内容编码器：`models/hubert/hubert_base.pt`
  * F0 模型：`models/f0/rmvpe.pt`
* **RNNoise**（可选）：`models/rnnoise/general.rnnn`

**manifest（可选但强烈建议）**：`models/manifest.json` 用于校验模型在位与完整性：

```json
{
  "files": [
    {"path": "models/uvr/MDX23C-8KFFT-InstVoc_HQ.ckpt", "sha256": "<sha256>", "bytes": 123456789},
    {"path": "models/rvc/G_8200.pth", "sha256": "<sha256>", "bytes": 987654321}
  ]
}
```

---

## CLI 模块（彼此独立）

> 统一选项：`--in/--outdir/--tmpdir/--preset <name>/--force/--dry-run/--log-json <path>`；成功返回 `0` 并输出 sidecar；失败写 `*.error.json` 并返回非 0。

### 00. 环境探测 `env_probe`

* **作用**：检测 FFmpeg/Python/CUDA/Torch/ONNX、GPU 可用性、关键库版本、磁盘剩余、权限等。
* **输出**：`work/<Song>/stage-00/env.json`
* **示例**：`bin/env_probe --outdir work/<Song>/stage-00`

### 05. 预处理 `prep_audio`

* **作用**：重采样/对齐位深与声道；去非法峰值；基线指标。
* **输入**：`input/<Song>.wav`
* **输出**：`work/<Song>/stage-05/master_48k32f.wav`、`metrics.json`
* **核心参数（Best-Quality）**：`--peak-ceil -0.3 --channels 2 --samplerate 48000`

### 10. 分轨 `separate_stems`

* **作用**：4-stem（Vocal/Drums/Bass/Other）。
* **输入**：`master_48k32f.wav`
* **输出**：`Vocal.raw`、`Drums.raw`、`Bass.raw`、`Other.raw`
* **Best-Quality 预设**：`--model mdx23c --segment 10240 --overlap 0.25 --gpu on --tta on`
* **Safe-VRAM**：`--segment 6144 --overlap 0.15 --tta off`

### 21. 主人声提取 `extract_lead`

* **作用**：从 `Vocal.raw` 中提纯**主人声（Lead）**，抑制和声/伴唱。
* **输出**：`Lead.raw`
* **默认**：`--method karaoke2 --aggr 0.6 --hp 120Hz --lp 12kHz`

### 25. 去混响 + 降噪 `dereverb_denoise`

* **顺序**：**先去混响，再降噪**（保证 RVC 编码/F0 估计更稳定）。
* **输入/输出**：`Lead.raw` → `Lead_DRY.raw`
* **Best-Quality**：`--algo wpe+arnndn --wpe-taps 10 --wpe-delay 3 --wpe-iters 3 --arnndn-strength 0.20`
* **Safe-VRAM**：`--algo wpe+rnnoise --rnnoise-strength 0.50`
* **提示**：去混响太强会削弱气息与空间感，建议从默认值起步。

### 30. 生成/补全 RVC 引导索引 `build_rvc_index`

* **作用**：若无 `.index`，用你的**2 分钟参考人声 WAV**构建最小可用索引。
* **输入**：`assets/guide.wav`
* **输出**：`models/rvc/G_8200.index`
* **默认**：`--sr 48000 --frame 1024 --hop 320 --feature hubert --index-type faiss --clusters 200`

### 35. RVC 音色替换 `rvc_convert`

* **说明**：本模块即“rvc\_timbre”，底层为 RVC 推理。
* **输入/输出**：`Lead_DRY.raw` → `Lead_RVC.raw`
* **必需**：`--model models/rvc/G_8200.pth --hubert models/hubert/hubert_base.pt --f0 models/f0/rmvpe.pt`
* **可选**：`--index models/rvc/G_8200.index`
* **Best-Quality**：

  * `--f0-method rmvpe --f0-up-key 0`
  * `--index-rate 0.20 --filter-radius 3 --rms-mix-rate 0.25 --protect 0.33`
  * `--resample-sr 48000 --fade 8 --chunk 8.0 --crossfade 0.06`
* **Safe-VRAM**：`--chunk 4.0 --index-rate 0.10 --filter-radius 2`

### 40. 每轨处理链 `track_chain`

* **输入/输出**：

  * `Drums.raw` → `01_Drums_stem.wav`
  * `Bass.raw`  → `02_Bass_stem.wav`
  * `Other.raw` → `03_Other_stem.wav`
  * `Lead_RVC.raw` → `04_Lead_RVC_processed.wav`
* **处理建议（按顺序）**：

  1. 轻度降噪（必要时）
  2. 去谐振/整形 EQ（LSP 参量 EQ + Notch）
  3. 去齿音（Lead 专用）
  4. 压缩（双段：整形 → 黏合）
  5. 轻度色彩（饱和/ADT/微延时/板式混响）
  6. 峰值限制 + 响度双遍（`ffmpeg loudnorm`）
* **目标门限**：

  * Lead：`I -17.0 LUFS / TP ≤ -2.0 dBTP`
  * Drums/Bass/Other：`I -19.0 ±1 LUFS / TP ≤ -2.5 dBTP`

### 60. 总线混合 `mix_bus`

* **输入**：四个 stem + 处理后 Lead
* **输出**：`99_Final_<SongName>_mix_24b48k.wav`
* **处理建议**：FIR 高通 → 总线 EQ → 多段压缩（温和）→ 胶合压缩（慢攻快释）→ 微饱和 → 立体声宽度/舞台 → `loudnorm` 双遍 → True Peak 限制 → SoX 抖动导出
* **目标门限**：`I -16.0 LUFS（±0.5） / TP ≤ -3.0 dBTP`

### 80. 质检 `qc_report`

* **汇总**：各轨与总线的 LUFS/TP/峰值/时长/动态范围；判定 PASS/FAIL 与修正建议；生成 `QC.md`

### 90. 留痕与打包 `finalize_run`

* **产出**：`RUNLOG.json`（组件版本、sha256、参数快照、阶段结果、失败点）

---

## 参数预设（节选）

> 任何 CLI 可通过 `--preset <name>` 选用下列预设；`--override key=value` 可覆写单一参数。

### `presets/best-quality.yaml`

```yaml
separate_stems:
  model: mdx23c
  segment: 10240
  overlap: 0.25
  tta: true
  gpu: true
extract_lead:
  method: karaoke2
  aggr: 0.6
  hp: 120
  lp: 12000
dereverb_denoise:
  algo: wpe+arnndn
  wpe_taps: 10
  wpe_delay: 3
  wpe_iters: 3
  arnndn_strength: 0.20
rvc_convert:
  f0_method: rmvpe
  f0_up_key: 0
  index_rate: 0.20
  filter_radius: 3
  rms_mix_rate: 0.25
  protect: 0.33
  resample_sr: 48000
  chunk: 8.0
  crossfade: 0.06
track_chain:
  lead_target_lufs: -17.0
  other_target_lufs: -19.0
  tp_ceil: -2.0
mix_bus:
  target_lufs: -16.0
  tp_ceil: -3.0
```

### `presets/safe-vram.yaml`

```yaml
separate_stems: {segment: 6144, overlap: 0.15, tta: false, gpu: true}
dereverb_denoise: {algo: wpe+rnnoise, rnnoise_strength: 0.50}
rvc_convert: {chunk: 4.0, index_rate: 0.10, filter_radius: 2}
```

### `presets/fast.yaml`

```yaml
separate_stems: {segment: 4096, overlap: 0.12, tta: false}
rvc_convert: {chunk: 3.0, crossfade: 0.04}
```

---

## 快速开始（逐步示例）

以歌曲名 `MySong` 为例：

```bash
# 0) 目录就绪
mkdir -p input work/MySong output/MySong models/{uvr,rvc,hubert,f0,rnnoise} logs bin presets

# 1) 环境探测
bin/env_probe --outdir work/MySong/stage-00

# 2) 预处理
bin/prep_audio \
  --in input/MySong.wav \
  --outdir work/MySong/stage-05 \
  --samplerate 48000 --peak-ceil -0.3

# 3) 分轨
bin/separate_stems \
  --in work/MySong/stage-05/master_48k32f.wav \
  --outdir work/MySong/stage-10 \
  --preset best-quality

# 4) 主人声提取
bin/extract_lead \
  --in work/MySong/stage-10/Vocal.raw \
  --outdir work/MySong/stage-21 \
  --preset best-quality

# 5) 去混响 + 降噪（先去混响）
bin/dereverb_denoise \
  --in work/MySong/stage-21/Lead.raw \
  --outdir work/MySong/stage-25 \
  --preset best-quality

# 6) 若无 RVC 引导索引则构建
bin/build_rvc_index \
  --in assets/guide.wav \
  --out models/rvc/G_8200.index \
  --sr 48000 --feature hubert --index-type faiss --clusters 200

# 7) RVC 音色替换（使用你的固定模型）
bin/rvc_convert \
  --in work/MySong/stage-25/Lead_DRY.raw \
  --outdir work/MySong/stage-35 \
  --preset best-quality \
  --model models/rvc/G_8200.pth \
  --hubert models/hubert/hubert_base.pt \
  --f0 models/f0/rmvpe.pt \
  --index models/rvc/G_8200.index

# 8) 每轨处理（可选）
bin/track_chain --in work/MySong/stage-10/Drums.raw --outdir work/MySong/stage-40 --target-lufs -19 --tp -2.5
bin/track_chain --in work/MySong/stage-10/Bass.raw  --outdir work/MySong/stage-41 --target-lufs -19 --tp -2.5
bin/track_chain --in work/MySong/stage-10/Other.raw --outdir work/MySong/stage-42 --target-lufs -19 --tp -2.5
bin/track_chain --in work/MySong/stage-35/Lead_RVC.raw --outdir work/MySong/stage-43 --target-lufs -17 --tp -2

# 9) 总线混合（可选）
bin/mix_bus \
  --lead work/MySong/stage-43/04_Lead_RVC_processed.wav \
  --drums work/MySong/stage-40/01_Drums_stem.wav \
  --bass  work/MySong/stage-41/02_Bass_stem.wav \
  --other work/MySong/stage-42/03_Other_stem.wav \
  --outdir output/MySong --target-lufs -16 --tp -3

# 10) 质检与留痕
bin/qc_report    --in output/MySong --outdir output/MySong
bin/finalize_run --song MySong --outdir output/MySong --log-json logs/MySong.jsonl
```

---

## Makefile 与编排（可选，不与模块耦合）

```
# 示例：按 stage 逐步执行，可 --resume 跳过已完成
make song=MySong prep|stems|lead|dry|index|rvc|tracks|bus|qc|all
```

* `run_pipeline.sh`：仅做顺序与断点续跑（检查目标文件与 sidecar 是否存在且校验通过）。

---

## 错误码与自愈建议

* `12` 输入不合规（采样率/通道/损坏）→ 建议重新导出或跑 `prep_audio --force`
* `22` 模型缺失或校验失败 → 补齐 `models/*` 并检查 `manifest.json`
* `32` GPU/显存不足 → 切换 `safe-vram.yaml` 或降低 `segment/chunk`
* `42` 响度不达标 → 允许继续，`QC.md` 标红并给出校正建议
* `1`  未知异常 → 查看对应阶段的 `*.error.json` 和 `logs/*.jsonl`

---

## 质量与稳定性建议

1. **先去混响再做 RVC**：混响会干扰内容编码与 F0，先做 WPE/ARNNDN（或 RNNoise）能显著稳定音色替换。
2. **提供/生成引导索引**：使用 2 分钟干声生成 `.index`，对拟真度与稳定性帮助显著。
3. **轻量而克制的动态处理**：每轨与总线尽量温和；把主体音色与平衡交给分轨与 RVC，避免过压缩导致“AI 味”。
4. **响度双遍**：`loudnorm` 双遍（测量→应用）更稳，TP 控制请在最后使用 True Peak 限制。
5. **可重复性**：在 `RUNLOG.json` 固定记录模型 sha256、预设、随机种子、软件版本，保证复现。

---

## 常见问答（FAQ）

* **Q：`rvc_timbre` 和 RVC 是一回事吗？** A：是的；`rvc_convert` 就是把 RVC 推理封装为独立 CLI 的实现名。
* **Q：没有 `.index` 能直接跑吗？** A：可以，但建议先用 `build_rvc_index` 从你的 2 分钟参考人声生成索引以提升稳定性。
* **Q：只想做人声链可以吗？** A：可以。执行 `extract_lead → dereverb_denoise → rvc_convert → track_chain(Lead)` 即可。
* **Q：CPU 可以跑吗？** A：可以但很慢；优先使用 GPU，并用 `safe-vram` 预设降低峰值显存需求。

---

## 仓库结构建议（落地时）

```
Mix02/
  bin/
    env_probe            # python/cli
    prep_audio
    separate_stems
    extract_lead
    dereverb_denoise
    build_rvc_index
    rvc_convert
    track_chain
    mix_bus
    qc_report
    finalize_run
  presets/
    best-quality.yaml
    safe-vram.yaml
    fast.yaml
  env/
    requirements.txt
    conda.yml
  docker/
    Dockerfile
  .gitignore
  README.md
```

---

## 下一步

* 若你同意本 README 的接口与契约，我可以：

  1. **在仓库中生成上述目录与 CLI 骨架**（参数解析 + 占位实现 + 校验 + sidecar 写出）；
  2. 附带 `presets/*.yaml`、`Makefile` 与 `run_pipeline.sh`；
  3. 提供 `models/manifest.json` 样板与校验脚本，确保“缺模型就失败在第 0 步”，实现稳定与可预期的错误处理。
