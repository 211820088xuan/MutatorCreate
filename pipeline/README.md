# pipeline —— 生成 mutator 的完整流程

- **规格说明**：`../docs/GENERATION_PIPELINE.md`
- **实验规格**：`../docs/EXPERIMENT_PIPELINE.md`

路径基准（脚本内已定义，无需设环境变量）：

```
HERE = mutator_create/pipeline/
ROOT = mutator_create/     ← artifacts/ outputs/ projects/ cpg_files/ reproduce_crash/
```

## 文件索引

| 阶段 | 脚本 | 作用 |
|---|---|---|
| 1 | `s1_reproduce.sh` | 用 ARVO 镜像复现崩溃（实现主体在 `../reproduce_crash/`） |
| 2 | `s2_lib_cpg.py` | Joern CPG 建图/查询与数据流辅助 |
| 2 | `s2a_build_facts.py` | 报告 + CPG + 深度字段 → `artifacts/facts/<OSV>/facts.json` |
| 2 | `s2b_build_interpretation.py` | facts → 确定性解释 |
| 3 | `s3_extract_patterns.py` | 解释 → 按崩溃类型归纳 pattern（LLM） |
| 4 | `s4_abstract_features.py` | pattern → 项目无关特征 → `outputs/stage4/<type>/features.json` |
| 5.0 | `s5_fetch_source.py` | 固定版本源码 + harness + 种子 |
| 5.1 | `s5a_scan_target.py` | 调用图 depth≤2 生成 worklist（0 LLM） |
| 5.2 | `s5b_audit_agent.py` | agent 审计风险函数（带 `flow` 控制流工具） |
| 5.3 | `s5_target_surface.py` | 输入攻击面 + 六步证据链（0 LLM） |
| 5.4 | `s5_candidate_findings.py` | 多路候选合并、证据核验、去重（0 LLM） |
| 5.5 | `s5f_feature_pipeline.py` | **每个特征走同一套 6 阶段流程**（0 LLM） |
| 5.6 | `s5_mutation_plan.py` | 声明式 mutation plan（权重在这里定） |
| 5.7 | `s5_generate_mutator_v2.py` | 从 ready plan 生成 C（含行为门禁） |
| 5.8 | `s5_verify_mutator_v2.py` | V1 schema / V2 evidence / V3 code / V4 behavior |
| 辅助 | `s5c_mech_hypotheses.py` | 机械规则找"释放→使用"形态（可选离线自检） |
| 辅助 | `s5g_interproc.py`, `s5h_feature_audit.py` | 跨函数视野（补 llm04/llm05） |
| 库 | `agent_runtime.py`, `cfg_lib.py` | 自实现 agent 循环；行级 CFG |

## 产物链

```
target_surface.json → candidate_findings.json → feature_pipeline.json
→ mutation_plan.json → mutator.c + mutator.json → verification.json
```

都写在 `projects/<OSV>/v2/` 下。
