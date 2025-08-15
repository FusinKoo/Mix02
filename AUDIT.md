# Mix02 仓库健康审计（Snakemake 版）

**结论**：Blocked  
**提交范围**：main@cde0fdc（比较基线：交接清单）  
**时间**：2025-08-15 19:40 UTC

## 1. 总览评分
- 结构契约：不通过（缺少 `workflow/` 目录及 Snakefile）
- Snakemake 编排：不通过（无任何规则与配置文件）
- CLI 真实推理落地度：不通过（除模型获取器外均为占位实现）
- 命名/门限对齐：不通过（轨道响度门限未按规格区分；QC/RUNLOG 字段缺失）
- 模型注册/拉取：通过（`models/registry.json` 覆盖 Hubert/RMVPE/FCPE/DFN）
- 文档与依赖：不通过（缺 Snakemake 运行示例与依赖）

## 2. 差距矩阵（应有项 vs 现状）
| 类别 | 应有项 | 现状 | 结论 | 证据 |
|---|---|---|---|---|
| 目录/文件 | workflow/ | 缺失 | 不通过 | `ls workflow` 报错【714c14†L1-L3】 |
| 目录/文件 | workflow/Snakefile | 缺失 | 不通过 | 同上 |
| 目录/文件 | workflow/config/config.yaml | 缺失 | 不通过 | 同上 |
| 目录/文件 | workflow/profiles/local/config.yaml | 缺失 | 不通过 | 同上 |
| 目录/文件 | scripts/run_pipeline.py | 存在 | 通过 | 【F:scripts/run_pipeline.py†L1-L40】 |
| 目录/文件 | env/requirements-full.txt | 存在但缺 snakemake | 不通过 | `rg snakemake` 无结果【2755c1†L1-L2】 |
| 目录/文件 | models/registry.json | 存在 | 通过 | 【F:models/registry.json†L1-L21】 |
| CLI | env_probe 等 stage CLI | 仅写入占位文本 | 不通过 | 如 `bin/prep_audio.py`【F:bin/prep_audio.py†L18-L22】 |
| 命名 | 99_Final_<Song>_mix_24b48k.wav | mix_bus 中硬编码 | 通过 | 【F:bin/mix_bus.py†L19-L20】 |
| 命名 | 四轨 stem 文件名 | track_chain NAME_MAP | 通过 | 【F:bin/track_chain.py†L5-L10】 |
| 命名 | QC.md 与 RUNLOG.json 字段 | 无 `components.sha256` 等 | 不通过 | `qc_report`、`finalize_run` 仅写占位【F:bin/qc_report.py†L19-L21】【F:bin/finalize_run.py†L26-L28】 |
| 依赖 | Snakemake | requirements 未列 | 不通过 | 【2755c1†L1-L2】 |
| 文档 | Snakemake 使用示例 | README 未提及 | 不通过 | 【F:README.md†L13-L24】 |
| 文档 | 归档参数 (pipeline_params_fixed.md) | 缺失 | 不通过 | 目录无该文件【25b2d2†L1-L40】 |

## 3. 最高优先级修复清单
- **P0（阻塞跑链）**  
  1) 缺 `workflow/` 及 Snakefile — 建议提交信息：`feat(workflow): add Snakemake DAG and configs`  
  2) 未纳入归档参数文档 — 建议提交信息：`docs: add pipeline_params_fixed.md for audit`  
- **P1（强建议立即补齐）**  
  - 各 stage CLI 为占位实现，需接入真实算法；提交信息如 `feat(cli): implement real separation with demucs`  
  - `env/requirements-full.txt` 补充 `snakemake` 等缺失依赖  
  - `README` 提供 Snakemake `--profile` 运行示例  
  - `QC.md`/`RUNLOG.json` 补充 `metrics.per_track.*`、`components.sha256` 等字段  
  - 轨道响度门限按 Drums/Bass/Other/Lead 细分并默认值对齐归档  
- **P2（优化/文档）**  
  - 补充环境锁定文档（如 `docs/envlock.md`）  
  - 升级 placeholder 脚手架测试覆盖度

## 4. 关键证据
- 目录树：见 `EVIDENCE/repo_tree.txt`
- Snakefile 规则摘要：见 `EVIDENCE/snakemake_probe.txt`
- 占位痕迹：见 `EVIDENCE/grep_placeholders.txt`
- 文件摘录：`EVIDENCE/<path>.excerpt.txt`

## 5. 备注
- 由于缺少 Snakemake 编排，本仓库当前无法按目标 DAG 运行。
