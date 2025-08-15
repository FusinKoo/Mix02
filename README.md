# Mix02 — 模块化音频管线（仓库脚手架｜可替换实现）

Mix02 是一个用于构建端到端音频处理流程的示例仓库。项目提供**分轨 → 主人声提取 → 去混响与降噪 → RVC 转换 → 每轨处理 → 总线混音 → 质检**的完整 CLI 契约。默认逻辑仍为占位实现，但接口与文件契约已经确定，可逐步替换为真实算法。

## 特性
- **模块化 stage**：通过 `python -m bin.<stage>` 调用，每一步都可单独运行或替换。
- **模型获取器**：使用 `bin.model_fetcher` 根据 `models/registry.json` 自动下载公共模型。
- **多预设**：`presets` 提供 `best-quality`、`safe-vram`、`fast` 三种参数组合。
- **dry-run 支持**：所有 CLI 支持 `--dry-run` 输出计划而不写文件。

## 快速开始
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
python -m bin.model_fetcher  # 可选，首次运行前拉取模型
chmod +x scripts/run_pipeline.sh
./scripts/run_pipeline.sh MySong
# 或
python scripts/run_pipeline.py MySong
```

### Snakemake 编排
项目同时提供 Snakemake 工作流，便于并行与复现：

```bash
cd workflow
snakemake --profile profiles/local --dry-run   # 预览 DAG
```
详见 `workflow/README-snakemake.md`。

## 项目结构
| 目录 | 说明 |
| --- | --- |
| `bin/` | 各 stage 的 CLI 占位实现 |
| `presets/` | 参数预设文件 |
| `schemas/` | JSON Schema 定义 |
| `scripts/` | 顺序或跨平台编排器 |
| `docs/` | 项目说明与契约文档 |
| `tests/` | 契约测试 |

更多信息请参阅 [docs/README.md](docs/README.md) 与 [docs/CONTRACTS.md](docs/CONTRACTS.md)。

## 契约摘要
- 内部规格：48kHz / 32-bit float / stereo
- 最终混音命名：`99_Final_<Song>_mix_24b48k.wav`
- 质检报告：`QC.md`；运行留痕：`RUNLOG.json`
- 退出码：0 / 1 / 12 / 22 / 32 / 42
- sidecar 字段详见 `schemas/sidecar.schema.json`

## 贡献与许可证
欢迎提交 Issue 或 PR 来完善脚手架。项目采用 [MIT License](LICENSE)。
