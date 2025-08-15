     1	# Mix02 — 模块化音频管线（仓库脚手架｜可替换实现）
     2	
     3	Mix02 是一个用于构建端到端音频处理流程的示例仓库。项目提供**分轨 → 主人声提取 → 去混响与降噪 → RVC 转换 → 每轨处理 → 总线混音 → 质检**的完整 CLI 契约。默认逻辑仍为占位实现，但接口与文件契约已经确定，可逐步替换为真实算法。
     4	
     5	## 特性
     6	- **模块化 stage**：通过 `python -m bin.<stage>` 调用，每一步都可单独运行或替换。
     7	- **模型获取器**：使用 `bin.model_fetcher` 根据 `models/registry.json` 自动下载公共模型。
     8	- **多预设**：`presets` 提供 `best-quality`、`safe-vram`、`fast` 三种参数组合。
     9	- **dry-run 支持**：所有 CLI 支持 `--dry-run` 输出计划而不写文件。
    10	
    11	## 快速开始
    12	```bash
    13	python -m venv .venv && source .venv/bin/activate
    14	pip install -e .[dev]
    15	python -m bin.model_fetcher  # 可选，首次运行前拉取模型
    16	chmod +x scripts/run_pipeline.sh
    17	./scripts/run_pipeline.sh MySong
    18	# 或
    19	python scripts/run_pipeline.py MySong
    20	```
    21	
    22	## 项目结构
    23	| 目录 | 说明 |
    24	| --- | --- |
    25	| `bin/` | 各 stage 的 CLI 占位实现 |
    26	| `presets/` | 参数预设文件 |
    27	| `schemas/` | JSON Schema 定义 |
    28	| `scripts/` | 顺序或跨平台编排器 |
    29	| `docs/` | 项目说明与契约文档 |
    30	| `tests/` | 契约测试 |
    31	
    32	更多信息请参阅 [docs/README.md](docs/README.md) 与 [docs/CONTRACTS.md](docs/CONTRACTS.md)。
    33	
    34	## 契约摘要
    35	- 内部规格：48kHz / 32-bit float / stereo
    36	- 最终混音命名：`99_Final_<Song>_mix_24b48k.wav`
    37	- 质检报告：`QC.md`；运行留痕：`RUNLOG.json`
    38	- 退出码：0 / 1 / 12 / 22 / 32 / 42
    39	- sidecar 字段详见 `schemas/sidecar.schema.json`
    40	
    41	## 贡献与许可证
    42	欢迎提交 Issue 或 PR 来完善脚手架。项目采用 [MIT License](LICENSE)。
