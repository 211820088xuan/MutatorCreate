# archive/ — 历史底本归档（不再维护，以 `../DELIVERY.md` 为准）

`../DELIVERY.md` 是**唯一交付文档 + 唯一可编辑底本**。本目录冻结各轮的历史全文，仅作留存/对照与「看某轮完整推理过程」之用，**勿据此执行或引用其结论**（结论一律以 DELIVERY.md 为准，那里只保留当前有效版本）。

| 文件 | 行数 | 状态 | 内容 |
|---|---|---|---|
| `2026-09-07-crash-reproduction-pipeline-design.md` | 494 | **R17 历史快照** | 设计文档 R17 状态（DELIVERY 当时已含 R18，比此快照新一轮） |
| `2026-09-07-preflight-measurements.md` | 571 | **R17 历史快照** | 预飞报告 R17 状态（M1–M12 + 审计 A/B/C + R1–R15 + R16 + R17） |
| `2026-09-08-p0-environment-report.md` | 239 | **P0 底本** | P0 环境验证报告全文（worktree 建树 / 代理 path(i)vs(ii) / 4a–4e 五项实测 / 端到端+负对照 / N1·N2） |
| `2026-09-08-p0b-report.md` | 241 | **P0-B 底本** | P0-B 报告全文（§5④ off-by-one 规则 / 选样 5 类阻塞 / `fixed^` 主路径打通 / 首个 strict / N3·N4·N5） |
| `2026-09-09-p0c-report.md` | 160 | **P0-C 底本** | P0-C 报告全文（detect_repo 旁路评估 / 代理统一 / hunspell+c-blosc2 复验 / 三处文档修正 / worktree 改动清单） |
| `2026-09-09-w2-report.md` | 609 | **W2 底本**（md5 `ca67ed45…`，与并入前一致） | W2 报告原文（§1–§10：一句话结果 / Phase0 四项 / 五模块实现 + 13 个 bug / 逐条 crash 表 A·B·C / Phase5 五项分析 / 🅗→✅ / 仍🅗 / N7–N17 / 卡点 / 约束）。**内容已全量并入 `../DELIVERY.md` §4.5–§4.13**（§8「N7–N17」与 DELIVERY §3 重复，未重复并入） |
| `2026-09-09-DELIVERY-fulltext-snapshot.md` | 2,063 | **W1 精简前的 DELIVERY 全文快照**（md5 校验一致） | 精简重构前的完整状态：设计文档 **R18 全文** + 预飞报告 **R18 全文** + 三轮修正全文 + P0/P0-B/P0-C 逐字全文 + 当时的 §0–§4 总览（含 W1 之前的全部 `[修订 R#]`/`[实测 P0*]` 标记叙述） |

## 为什么有最后这份快照

W1 轮按用户要求把 DELIVERY.md 从 **2,063 行精简到 ~600 行**：删的是**历史叙述与逐字重复**（每轮「原表述→为何改→改成什么」的层层叠加，以及 P0/P0-B/P0-C 与上表三份底本逐字重复的部分），保留的是**全部当前有效规格、全部实测数字、全部结论及其证据出处**（精简后做过 112 个关键 token 的丢失核查，仅异名映射表一项被省、已补回）。

需要看某轮的**完整推理过程**（观测→假设→演绎→检验→评价）时：
- 设计/预飞的 R18 状态 → 本快照的第一/二部分；
- P0 / P0-B / P0-C 的实测过程 → 上表对应底本（或本快照第三部分，两者逐字相同）；
- **W1（off-by-one 抽样 / repo_path 审计 / ⓪① 两模块）没有独立底本**：其结论写在 DELIVERY §2.3/§2.4/§3/§4，**逐条原值数据**在 `../preflight/offbyone_sample_results.json`（48 条抽样 + 2 正对照的每个信号原值）与 `../artifacts/repo_path_map.json`（328 项目的 clone 清单），复算脚本 = `../preflight/w1_offbyone_sampling.py`、`../preflight/w1_repo_path_scan.py`。
- **W2（Phase0 四遗留 / ②③④⑤⑥ 五模块 / 首轮真跑）**：结论与逐条数据表都在 DELIVERY **§4.5–§4.13**（并入自本目录的 `2026-09-09-w2-report.md`）；**逐条原值数据**在 `../preflight/w2_phase0a_audit.json`（三种解析器复算）、`w2_phase0b_queue_order.json`（era 窗口 + 三代理秩相关 + 84 条真实 commit 日期）、`w2_phase0c_degenerate.json`（N6 53 条逐条证据）、`w2_phase5_analysis.json`、`w2_phase5d_negctl.json`、`w2_phase5e_build.json`，运行期数据在 `../repro_dataset.jsonl`（142 行/129 条/51 字段）+ `../artifacts/{state.json,build_records.jsonl,binaries/,logs/,runs/}`；复算脚本 = `../preflight/w2_phase*.py` 与五个模块本身。

> **今后约定**：每轮汇报内容**直接写进 DELIVERY.md 对应章节**（新实测→§2、新发现→§3、规格变更→§1、进度→§0.2、本轮明细→§4.x），**不再新建交付文档**；`preflight/` 只放脚本 + 逐条原值 JSON（可复算的数据，不是文档）。
> **W2 的做法（若某轮任务显式要求单独出报告）**：先按要求写报告文件 → **随后把全量内容并入 DELIVERY 对应章节** → 原文快照冻结进本目录 → 根目录只留 DELIVERY.md 一个交付文档。并入后**必须对着被并入的那份文件逐项做丢失核查**（W2 用 775 个 distinctive token：sha / osv_id / 带单位数字 / 反引号标识符 / N 编号 / 文件名，覆盖率 751/775，缺的 24 个逐个查过）。
> **这条核查是 W1 的教训**：W1 精简时只比了「旧 DELIVERY vs 新 DELIVERY」，而当时被删的报告**从未并进旧 DELIVERY**，那次对比在结构上就不可能发现报告正文丢失（结果丢了 6 项，含任务硬性要求的「48 条抽中清单」，是用户问了才查出来的）。**比较对象必须是「被删/被并的那份」，不能只是同一文件的前后两版。**
