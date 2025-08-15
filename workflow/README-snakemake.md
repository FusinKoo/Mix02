# Snakemake Workflow

此目录包含使用 Snakemake 实现的编排示例。默认配置在 `config/config.yaml`，
本地 profile 位于 `profiles/local`。

快速测试：

```bash
cd workflow
snakemake --profile profiles/local --dry-run
```

运行上述命令将列出完整 DAG 与最终目标。

