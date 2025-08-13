# Mix02 — 模块化音频管线（仓库脚手架｜可替换实现）

License: MIT

本仓库提供**分轨 → 主人声 → 去混响+降噪 → RVC → 每轨处理 → 总线 → 质检**的**独立 CLI 契约**与编排脚手架。默认实现仍为占位逻辑，但新增了**模型获取器**以自动拉取公共模型。
您可以在 `models/registry.json` 中查看注册表并通过 `python -m bin.model_fetcher` 将所需模型下载到本地。

## 快速使用
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
chmod +x scripts/run_pipeline.sh
./scripts/run_pipeline.sh MySong
# 或
python scripts/run_pipeline.py MySong
```

首次运行前可执行模型获取：
```bash
python -m bin.model_fetcher
```

## Dry Run

所有 CLI 支持 `--dry-run` 查看计划而不写文件，例如：
```bash
python -m bin.env_probe --dry-run
```

## 结构

* `bin/*`：每个 stage 的 CLI（占位实现）。
* `presets/*.yaml`：参数预设（best-quality / safe-vram / fast）。
* `schemas/*.json`：sidecar 与 error 的 JSON Schema。
* `scripts/run_pipeline.sh`：顺序编排执行。
* `scripts/run_pipeline.py`：跨平台编排器。
* `Makefile`：常用目标。
* `env/requirements-full.txt`：全量依赖列表。

## 契约

* 内部规格：48k/32f/立体声；
* 最终混音命名：`99_Final_<Song>_mix_24b48k.wav`；
* 质检报告：`QC.md`，运行留痕：`RUNLOG.json`；
* 退出码：0/1/12/22/32/42；
* sidecar 字段：见 `schemas/sidecar.schema.json`。

## 实现真实算法

在保持**文件契约与参数接口不变**的前提下，逐步将 `bin/*` 中的占位逻辑替换为真实 DSP/推理即可。
