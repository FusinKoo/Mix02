# Mix02 — 模块化音频管线（仓库脚手架｜可替换实现）

本仓库提供**分轨 → 主人声 → 去混响+降噪 → RVC → 每轨处理 → 总线 → 质检**的**独立 CLI 契约**与编排脚手架。当前为**占位实现**：
- 不包含重型音频算法与外部模型；
- CLI 可运行、可解析参数、会输出 sidecar JSON 与占位产物；
- 目录/文件/字段/退出码等契约已固定，后续只需填充真实实现。

## 快速使用
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
chmod +x scripts/run_pipeline.sh
./scripts/run_pipeline.sh MySong
```

## 结构

* `bin/*`：每个 stage 的 CLI（占位实现）。
* `presets/*.yaml`：参数预设（best-quality / safe-vram / fast）。
* `schemas/*.json`：sidecar 与 error 的 JSON Schema。
* `scripts/run_pipeline.sh`：顺序编排执行。
* `Makefile`：常用目标。

## 契约

* 内部规格：48k/32f/立体声；
* 退出码：0/1/12/22/32/42；
* sidecar 字段：见 `schemas/sidecar.schema.json`。

## 实现真实算法

在保持**文件契约与参数接口不变**的前提下，逐步将 `bin/*` 中的占位逻辑替换为真实 DSP/推理即可。

```
