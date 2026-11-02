# pipeline —— 生成 mutator 的完整流程

- **规格说明**：`../docs/GENERATION_PIPELINE.md`
- **实验规格**：`../docs/EXPERIMENT_PIPELINE.md`

路径基准（脚本内已定义，无需设环境变量）：

```
HERE = mutator_create/pipeline/
ROOT = mutator_create/     ← artifacts/ outputs/ projects/ cpg_files/ reproduce_crash/
```

## 文件（11 个 .py + 1 个 .sh）

| 阶段 | 文件 | 行数 | 作用 |
|---|---|---:|---|
| 1 | `s1_reproduce.sh` | ~30 | 入口包装，转发到 `../reproduce_crash/arvo_repro.py` |
| 2 | `s2_1_lib_cpg.py` | 481 | Joern CPG 建图 / 查询 / 数据流辅助（共享库） |
| 2 | `s2_2_facts.py` | 1464 | 崩溃报告 + CPG + 深度字段 → `artifacts/facts/<OSV>/facts.json` |
| 2 | `s2_3_interpretation.py` | 369 | facts → 确定性解释 |
| 3 | `s3_extract_patterns.py` | 548 | 解释 → 按崩溃类型归纳 pattern（LLM） |
| 4 | `s4_abstract_features.py` | 282 | pattern → 项目无关特征 → `outputs/stage4/<type>/features.json` |
| **5** | **`s5_1_main.py`** | 176 | **stage5 入口 + CLI 调度**（不实现具体阶段） |
| 5 | `s5_2_prepare.py` | 675 | 5.0 fetch + 5.1 worklist |
| 5 | `s5_3_audit.py` | 1306 | 5.2 agent 审计 + 5.2b 机械规则 + 5.2c 跨函数 + 5.2d 特征审计 |
| 5 | `s5_4_analyze.py` | 1511 | 5.3 证据链 + 5.4 候选合并 + 5.5 每特征 6 阶段 |
| 5 | `s5_5_build.py` | 1202 | 5.6 plan + 5.7 生成 C + 5.8 V1–V4 门禁 |
| 5 | `s5_6_lib.py` | 547 | 共享底座：行级 CFG + 自实现 agent 循环 |

stage5 原来是 12 个脚本 + 2 个库（14 个文件），现在按 **4 个阶段拆成 6 个文件**：
入口、4 个阶段各一个、1 个共享底座。

## stage5 的 4 个阶段

```bash
python3 s5_1_main.py prepare --osv ARVO-42494732     # 5.0 抓源码 + 5.1 worklist
python3 s5_1_main.py audit   --osv ARVO-42494732 --all-chunks   # 5.2（需显式范围）
python3 s5_1_main.py analyze --osv ARVO-42494732     # 5.3 + 5.4 + 5.5
python3 s5_1_main.py build   --osv ARVO-42494732     # 5.6 + 5.7 + 5.8
python3 s5_1_main.py all     --osv ARVO-42494732     # 四步（默认跳过 audit）
python3 s5_1_main.py list                            # 看阶段映射
```

`audit` 必须显式给范围，避免误跑 162 批：

| 参数 | 含义 |
|---|---|
| `--all-chunks` | 跑全部 162 批（LLM，很贵） |
| `--chunk N --chunk M` | 只跑指定批次 |
| `--merge` | 只把已有 `audit_chunks/` 合并成 `vuln_report.json`（**不调 LLM**） |

## 单步直通

想只跑某一步时，`s5_1_main.py` 也支持直接调（参数原样转发）：

```bash
python3 s5_1_main.py fetch    ARVO-42494732
python3 s5_1_main.py worklist --osv X --depth 3
python3 s5_1_main.py surface  --osv X --dry-run
python3 s5_1_main.py features --osv X --feature uaf-llm01
python3 s5_1_main.py generate --plan <plan.json> --out <dir>
python3 s5_1_main.py verify   --osv X --binary <bin>
python3 s5_1_main.py mech     --osv X
```

## 产物链

```
target_surface.json → candidate_findings.json → feature_pipeline.json
→ mutation_plan.json → mutator.c + mutator.json → verification.json
```

都写在 `projects/<OSV>/v2/` 下。
