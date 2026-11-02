# pipeline —— 生成 mutator 的完整流程

- **规格说明**：`../docs/GENERATION_PIPELINE.md`
- **实验规格**：`../docs/EXPERIMENT_PIPELINE.md`

路径基准（脚本内已定义，无需设环境变量）：

```
HERE = mutator_create/pipeline/
ROOT = mutator_create/     ← artifacts/ outputs/ projects/ cpg_files/ reproduce_crash/
```

## 文件（8 个 .py + 1 个 .sh）

| 阶段 | 文件 | 作用 |
|---|---|---|
| 1 | `s1_reproduce.sh` | 入口包装，转发到 `../reproduce_crash/arvo_repro.py` |
| 2 | `s2_lib_cpg.py` | Joern CPG 建图 / 查询 / 数据流辅助 |
| 2 | `s2a_build_facts.py` | 崩溃报告 + CPG + 深度字段 → `artifacts/facts/<OSV>/facts.json` |
| 2 | `s2b_build_interpretation.py` | facts → 确定性解释 |
| 3 | `s3_extract_patterns.py` | 解释 → 按崩溃类型归纳 pattern（LLM） |
| 4 | `s4_abstract_features.py` | pattern → 项目无关特征 → `outputs/stage4/<type>/features.json` |
| **5** | **`s5.py`** | **stage5 统一入口 + 确定性阶段**（5.0/5.1/5.3/5.4/5.5/5.6/5.7/5.8） |
| 5 | `s5_agent.py` | stage5 的 agent 阶段（5.2 审计 / 5.2b 机械规则 / 5.2c 跨函数 / 5.2d 特征审计） |
| 5 | `s5_lib.py` | 共享底座：行级 CFG（`flow`/`blocks`…）+ 自实现 agent 循环 |

stage5 原来有 12 个脚本 + 2 个库（共 14 个文件），2026-11-02 合并成 **3 个**。

## stage5 的 4 个阶段（`s5.py`）

```bash
python3 s5.py prepare --osv ARVO-42494732     # 5.0 抓源码 + 5.1 worklist
python3 s5.py audit   --osv ARVO-42494732 --all-chunks   # 5.2 agent 审计（LLM，需显式范围）
python3 s5.py analyze --osv ARVO-42494732    # 5.3 证据链 + 5.4 候选 + 5.5 每特征 6 阶段
python3 s5.py build   --osv ARVO-42494732    # 5.6 plan + 5.7 生成 C + 5.8 V1–V4 门禁
python3 s5.py all     --osv ARVO-42494732    # 四步（默认跳过 audit，加 --with-audit 才跑）
python3 s5.py list                            # 看阶段映射
```

`audit` 必须显式给范围，避免误跑 162 批：

| 参数 | 含义 |
|---|---|
| `--all-chunks` | 跑全部 162 批（LLM，很贵） |
| `--chunk N --chunk M` | 只跑指定批次 |
| `--merge` | 只把已有 `audit_chunks/` 合并成 `vuln_report.json`（**不调 LLM**） |

## 单阶段直通

想只跑某一步时，`s5.py` 也支持直接调（参数原样转发）：

```bash
python3 s5.py worklist --osv X --depth 3
python3 s5.py surface  --osv X --dry-run
python3 s5.py generate --plan <plan.json> --out <dir>     # 生成器单独跑
python3 s5.py verify   --osv X --binary <bin>
python3 s5.py mech     --osv X            # agent 阶段的机械规则
python3 s5.py feat-audit --osv X --feature uaf-llm02
```

## 产物链

```
target_surface.json → candidate_findings.json → feature_pipeline.json
→ mutation_plan.json → mutator.c + mutator.json → verification.json
```

都写在 `projects/<OSV>/v2/` 下。
