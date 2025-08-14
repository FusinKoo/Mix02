# 项目说明

Mix02 是一个模块化音频处理管线的脚手架，旨在演示基于 CLI 契约的阶段化处理流程。仓库提供了一套可以自由替换的占位实现，便于根据需求逐步替换为真实算法。

## 核心特性
- 分层 CLI 契约：每一步都可以单独调用或替换。
- 自动模型获取器：根据 `models/registry.json` 下载公共模型。
- 多预设：`presets` 内提供 best-quality / safe-vram / fast 预设。

## 仓库结构
- `bin/`：各阶段 CLI 占位实现。
- `presets/*.yaml`：参数预设。
- `schemas/*.json`：sidecar 与错误 Schema。
- `scripts/`：跨平台编排器。
- `tests/`：契约测试。

更多契约细节见 [CONTRACTS.md](CONTRACTS.md)。
