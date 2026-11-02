# PHASE 4 · 交接文档修正补丁

日期：2026-11-02

> **前置说明（必读）**
> 计划中要更新的 `HANDOFF/00_INDEX.md` … `HANDOFF/05_BUGS_DECISIONS_OPEN.md` 与 `HANDOFF/PROMPT.md`
> 在 2026-11-02 15:20–15:53 之间**已不存在**（`HANDOFF/` 目录只剩新建的 `runs/`）。
> 已尝试恢复：全盘 `find / -name "01_GOAL_AND_DATA.md"` 无结果；无回收站；`/tmp/audit/backup/`
> 只备份了 4 个代码文件，没有文档备份。
> **因此本文件不是"已改好的文档"，而是"可直接套用的修正补丁"**：
> 每条给出「目标位置 / 修正前原文 / 修正后原文 / 证据」。
> 唯一幸存的总结文档 `HANDOFF.md` 已按同一批修正**重写**（见文末 §4）。

---

# 1 修正清单（8 条，按指令顺序）

## C1 · P0（去掉含 OBJECTS 的种子）**作废**，替换为路径 B

| 项 | 内容 |
|---|---|
| 目标 | `00_INDEX.md` §5「你现在应该做什么」；`05_BUGS_DECISIONS_OPEN.md` §3.1（P0）、§5.3（选项 1） |
| 修正前原文 | 「**推荐**：换一个 default 够不着的目标：去掉含 `OBJECTS` 段的种子……目标 UAF 需要 `0/SECTION` + `2/OBJECTS` + 段内 `code-0` 记录 三段结构同时成立，default 几乎不可能凭空构造出来」 |
| **修正后原文** | 「**P0 作废（2026-11-02 实测修正）**。剥掉 OBJECTS 段后，**目标对两臂都不可达**：<br>· 旧算子在剥段种子上 `CHANGED = 0/1000`（纯空转，`v2/mutator.c:129`、`:131` 直接 `return Size`）；<br>· default 在剥段种子上 60 s / 46,999 execs / **0 崩溃**；<br>· n=5 复跑（300 s × 5）default 只有 **3 次**命中 / 1,018,452 execs。<br>→ 「去掉 OBJECTS 种子」会把 custom 变成「50% default + 50% 空转」。**替换为路径 B：把算子从替换型扩成构造型**（见 `runs/PHASE3_REPORT.md`）。<br>路径 B 实测：剥段种子上 default 3 / 1,018,452 vs custom **675 / 609,670**，RR = 375.9，CI [120.9, 1168.3]。」 |
| 证据 | `runs/PHASE1_REPORT.md`（1A/1B 表）、`runs/PHASE3_REPORT.md`（表 2/表 3）、`v2/mutator.c:129,131` |

## C2 · `dimensions` 耦合：`02` §8 的这条是**假的**

| 项 | 内容 |
|---|---|
| 目标 | `02_STAGE1_TO_4_SCRIPTS.md` §8「阶段之间的耦合」表 |
| 修正前原文 | 「改 stage3 的 `dimensions` 键名 → 必须同时检查 `s5f_feature_pipeline.py` 的 `classify()`、`s5h_feature_audit.py`」 |
| **修正后原文** | 「~~改 stage3 的 `dimensions` 键名 → 必须同时检查 `s5f` / `s5h`~~ **（2026-11-02 实测修正：这条是错的）**。7 个维度名（`alloc_kind` / `free_before_use` / `free_and_use_same_function` / `reassigned_between` / `in_loop` / `access_kind` / `cross_frame_count`）在整个 **stage5 里没有任何真读取**：全部出现点都在生产端（`s2a` / `s2b` / `s2_lib_cpg`）或 prompt 字符串（`s3_extract_patterns.py:129-135,199-205`、`s4_abstract_features.py:146`）。<br>`s5f.classify()`（`s5f_feature_pipeline.py:253-283`）读的是 `site["function"]` / `site["use"]["kind"]` / `site["is_link_read"]` / `site["realloc_near"]` 和三个函数名正则。<br>改 dimensions 键名只会影响 **stage3 自身的合并轮**（提示词里的一致性判据，`s3_extract_patterns.py:172`）和 stage4 的 prompt。」 |
| 证据 | 上一轮 Q7（`docs/REPORT.md` §Q7）；`grep -n "alloc_kind\|..." pipeline/*.py` |

## C3 · V4 已闭环

| 项 | 内容 |
|---|---|
| 目标 | `03_STAGE5_V2.md` §12.7；`05_BUGS_DECISIONS_OPEN.md` §3.6（P5） |
| 修正前原文 | 「V4 behavior：`not_applicable`（缺 `testcase_path`）」；「P5 · V4 行为门禁未闭环」 |
| **修正后原文** | 「**（2026-11-02 实测修正）V4 已闭环**。给 `source_context.json` 加了 `testcase_path`（指向 `reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libredwg/address/ff69eeda…/ARVO-42494732/testcase`，256 字节）。<br>`s5_verify_mutator_v2.py --binary <llvmfuzz>` 输出：`V4_behavior PASS · 已知 crash 回放: heap-use-after-free /src/libredwg/src/in_dxf.c:12267`；`overall = **pass**`（不再是 `pass_with_skipped`）。<br>注意：实验二进制可在**主机**直接运行，不需要进容器跑验证脚本。」 |
| 证据 | 上一轮白名单项 1 的原始输出；`v2/verification.json` |

## C4 · 三配置横向对比**待复核**

| 项 | 内容 |
|---|---|
| 目标 | `04_CASE_AND_EXPERIMENTS.md` §8.4「三配置横向对比」 |
| 修正前原文 | 「**结论**：只保留"找到落点的特征"明显优于"5 个都塞进去"」（配 0.60× / 1.33× 的表） |
| **修正后原文** | 「**（2026-11-02 实测修正）本表待复核，不能作为结论**。<br>· 配置 A（100% a001）与 B（50%+5×10%）的原始 `run.log` **已被 `run_matrix.sh` 的 `rm -rf default custom` 删除**，只有 `README.md` 的记录，无法复算；<br>· 配置 C 的日志在（`default/run.log` 11-01 23:22，`exec/s 82`；`custom/run.log` 11-01 23:26，`exec/s 45`），但其 default 密度 137.94/100k 与 n=5 各 rep 的 63.71–359.45 同量级波动；<br>· 同一 default 配置在 n=5 里的密度范围是 **63.71–359.45（5.6 倍）**，0.60× 与 1.33× 都落在波动内。<br>→ 「只保留 found 特征更优」这个结论**不成立**。路径 B 的效果（RR 375.9）是靠**换场景**（剥段种子）取得的，不是靠权重调优。」 |
| 证据 | `docs/REPORT.md` §Q9；`runs/PHASE1_REPORT.md` 表 1A |

## C5 · rep05 日志已被覆盖；补 1A 复跑

| 项 | 内容 |
|---|---|
| 目标 | `04_CASE_AND_EXPERIMENTS.md` §8.5「n=5 配对重复」 |
| 修正前原文 | rep05/default = 1,391 execs、密度 359.45；pooled `RR = 0.954，95% CI = [0.61, 1.48]` |
| **修正后原文** | 「**（2026-11-02 实测修正）rep05 的原始 `run.log` 已被残留进程覆盖**：`reps_n5_r1/summary.json` 记 1,391 execs，而现存 `reps/rep05/default/run.log` 是 12,178 execs（`rep05/custom/run.log` 无进度行）。**`summary.json` 是旧 rep05 数值的唯一来源。**<br><br>**1A 复跑（`reps_n5_r2`，2026-11-02，150 s × 5，现种子）**：<br>| rep | default 命中/execs | custom 命中/execs | 比值 |<br>|---|---|---|---|<br>| rep01 | 10/7,048 | 7/7,796 | 0.63× |<br>| rep02 | 4/9,211 | 7/7,552 | 2.13× |<br>| rep03 | 2/9,120 | 11/5,520 | 9.09× |<br>| rep04 | 7/6,911 | 5/5,741 | 0.86× |<br>| rep05 | 18/10,622 | 5/5,770 | 0.51× |<br><br>pooled：default 41/42,912 = 95.54/100k；custom 35/32,379 = 108.09/100k；**RR = 1.131，95% CI = [0.72, 1.78]**。配对胜出 2/5，覆盖率比中位 0.967。<br>**与旧的 0.954 符号相反**——两次 CI 都含 1，但点估计方向相反，说明该配置下效应量在噪声以下。」 |
| 证据 | `runs/PHASE1_REPORT.md`；`reps_n5_r1/summary.json` vs `reps_n5_r2/summary.json` |

## C6 · `reassigned_between` 不是「batch 层就没有」

| 项 | 内容 |
|---|---|
| 目标 | `01_GOAL_AND_DATA.md` §3.7.1「两个 unknown」段 |
| 修正前原文 | 「`reassigned_between` 在 **batch 层就是 unknown**（batch_001/002/009 都是），LLM 从未算过它」 |
| **修正后原文** | 「**（2026-11-02 实测修正）这个说法不准确。** `s2b_build_interpretation.py` 里 `_reassign_between()` 已经算了并写进 `interpretation.findings.reassigned_between`：121 条 UAF 里 **`None` 80 / `True` 25 / `False` 16**（即 **41 条有确定值**）。<br>stage3 的 5 个 pattern 全写 `unknown`，是 LLM 自己的选择，不是数据没有。<br>按 pattern 的 per-sample 分布：<br>· 缓冲释放后旧指针：`None`21 / `False`6 / `True`7 → 多数 `None`<br>· 清理析构后悬垂访问：`None`25 / `False`3 / `True`3 → 多数 `None`<br>· 容器节点销毁后遍历：`None`17 / `True`5 / `False`4 → 多数 `None`<br>· 同函数释放后访问：`True`2 / `None`3 → 多数 `None`<br>· **跨函数陈旧对象访问：`True`6 / `None`5 → 多数 `True`**，但 stage3 写成 `unknown`——**与 stage3 自己定的"dimensions 取多数值"规则（`s3_extract_patterns.py:175`）矛盾**。」 |
| 证据 | `docs/REPORT.md` §Q7；`artifacts/interpretation/*/interpretation.json` 的 `findings.reassigned_between` |

## C7 · 新增 bug：`run_reps.sh` 的残留进程会覆盖 `reps/`

| 项 | 内容 |
|---|---|
| 目标 | `05_BUGS_DECISIONS_OPEN.md` §1（已修 bug 清单，新增一条） |
| **新增原文** | 「### B22 · `run_reps.sh` 的残留进程覆盖 `reps/`<br>**现象**：n=5 跑完后 `reps/rep05/default/run.log` 记录 1,391 execs，但 `summary.json` 与 `REPS.md` 写的是 1,391；隔一段时间再看同一文件变成 12,178 execs；`rep05/custom/run.log` 干脆没有进度行。<br>**根因**：`run_reps.sh` 第一步就 `rm -rf "$ROOT"`（`ROOT=/exp/v2/experiment/reps`），然后启动 10 个后台 run 并 `wait`。如果上一次的 `run_reps.sh` 没被彻底杀掉（`job_kill` 只杀了外层 `docker exec`，容器内的 `sh -c` 和 `llvmfuzz` 仍在跑），它会在新的 `rm -rf` **之后**继续往同一个 `reps/` 目录写，覆盖新结果。<br>**修法（运维层面，未改脚本）**：<br>1. 跑前 `docker exec libredwg-exp ps aux | grep [l]lvmfuzz` 确认无运行中进程（`Z`/defunct 无害）；<br>2. 每次跑完**立刻** `cp -a reps reps_<tag>`，不要留在原地；<br>3. 分析一律针对快照，不针对 `reps/`。<br>**教训**：`rm -rf` + 后台进程 + `wait` 的组合在"上次没杀干净"时不安全；产物必须落地到不可变的快照。」 |
| 证据 | `docs/REPORT.md` §Q9；本轮 Phase 0/1A 的操作记录（`reps_n5_r1` / `reps_n5_r2` 两份快照） |

## C8 · 新增条目：a001 是 default 的**真子集**

| 项 | 内容 |
|---|---|
| 目标 | `05_BUGS_DECISIONS_OPEN.md` §1（或 `05` §2.2「被否决的方案」） |
| **新增原文** | 「### 关于 a001 的能力边界（2026-11-02 实测）<br>改造前（替换型）的 `pm003_mutate_a001` **能力是 libFuzzer default 的真子集**：<br>1. **只在段存在时起作用**：找不到 `OBJECTS` 就 `return Size`（`v2/mutator.c:129`）；段内无 code-0 记录也 `return Size`（`:131`）。<br>2. **最多增长 63 字节**：`new_len = 1 + (r % 64)`（`:150`），且只替换一条值行。<br>3. 而 default 的崩溃输入**有插入**：最大 164,002 字节 > 最大种子 127,870（`reps/rep01/default/crash/`，10 个文件里 8 个与种子不同长）；**有拼接**：`POLYLINXRECORD`（= `POLYLINE` + `XRECORD` 的混合）。<br>→ 所以在"结构已存在"的场景里 a001 赢不了（default 改一个字节就命中，96/100k）；在"结构不存在"的场景里 a001 空转（`CHANGED = 0/1000`）。**两格都赢不了**——这是必须把它改成构造型的直接理由。<br>**改造后（`ensure_record_structure`）**：剥段种子上 `CHANGED` 从 0 变 500，A/B 里 default 3 vs custom 675。」 |
| 证据 | `docs/REPORT.md` §Q1、§Q2；`runs/PHASE3_REPORT.md` 表 2 |

---

# 2 本轮新增的两条限制（也应进文档）

## C9 · 构造路径在 DWG 上无效（设计限制）

`is_dxf_format()` 把 DWG / JSON 全部路由到 `LLVMFuzzerMutate`（`v2/mutator.c` 分发器），
所以 `construct` 只在 `format_scope = ["DXF"]` 内生效。实测 `Arc.dwg` 上 `CHANGED = 0/1000`。
→ 那张 375× 的效应**只在 DXF 上成立**。DWG 上的 49% 语料仍然只有 default。

## C10 · 构造型的代价：覆盖率降 18%

剥段种子上 `custom/default` 的覆盖率比只有 **0.820**（范围 0.795–0.841）。
构造路径每 2 次迭代就塞一个 `OBJECTS` 段，语料被这类结构主导。
回归（现种子）里覆盖率比是 1.023，但 custom 的 execs 只有 default 的 74%，两者不可直接比。

---

# 3 修正后的「下一步」优先级

| 新优先级 | 内容 | 依据 |
|---|---|---|
| **P0（已完成）** | 路径 B：算子从替换型扩成构造型 | `runs/PHASE3_REPORT.md`：RR = 375.9 |
| **P1** | 降构造频率（例如段不存在时只以 1/4 概率构造），把覆盖率比从 0.820 拉回 ≥0.95，且不损失命中率 | C10 |
| P2 | 权重按输入格式分配（DWG 仍无策略） | C9 |
| P3 | 补算 `cross_frame_count`；把 `reassigned_between` 从 interpretation 传进 stage3 | C6 |
| P4 | stage4 加 `differentiator` + "维度向量相同就合并" | 上一轮 Q10 |

---

# 4 `HANDOFF.md` 已重写

`HANDOFF/00-05 + PROMPT.md` 丢失后，唯一幸存的总结文档是 `HANDOFF.md`。
它已按本文件的 C1–C10 重写：去掉指向已删文件的链接，把 10 条修正内联，并指向
`docs/REPORT.md`（上一轮 Q1–Q12 完整调查）与 `HANDOFF/runs/`（本轮四份阶段报告）。
