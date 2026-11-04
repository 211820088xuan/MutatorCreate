# INTERVENTIONS —— 人工介入台账

> 用途：证明"原封不动跑 stage5"这件事有没有被人为破坏。
> 每一次人工介入都要记：**时间 / 改了什么 / 为什么 / 属于哪一类**。
> 类别定义见本轮任务书 B0：
>
> | 类别 | 允许？ |
> |---|---|
> | **项目特有的环境工作**（建容器、拉源码、建 CPG、准备种子、写 build 脚本） | ✅ 允许，记录即可 |
> | **把写死的项目常量泛化成通用规则** | ⚠️ 有条件允许（必须从 harness 逻辑自动推导，且在 libredwg 上复现原结果） |
> | **改判据让特征落地**（改 shortlist 正则 / `classify()` / 预筛黑名单 / prompt） | ❌ 禁止 |
> | **手工指定站点或字段**（把 `free_line` / `use_line` / `section_anchor` 写进 plan） | ❌ 禁止 |

---

## R4（2026-11-03）—— 本轮

| 时间 | 改了什么 | 为什么 | 类别 |
|---|---|---|---|
| 12:1x | 重建 `llvmfuzz`（`docker exec … build.sh`） | `v2/mutator.c` 于 2026-11-02 19:12 被重新生成（440 行），旧二进制早于它;重跑 A/B 前必须让二进制与算子一致 | ✅ 环境工作 |
| 12:1x | `seeds/` 临时换成 4 个剥段 DXF（`mv` 到 `_pathB_removed/`），跑完移回 | Path B 的实验设计就是用"剥掉目标结构"的种子 | ✅ 环境工作 |
| 12:1x | `run_reps.sh 300 5`（`reps_pathB_r3`） | Phase A2 的重跑 | ✅ 环境工作 |
| 12:2x | 2 次 `raw.githubusercontent.com` fetch（curl / gpac 的源码） | 判"谓词方向"必须读源码（`sites[].code` 是析取，不可用） | ✅ 只读 |

**本轮没有任何"改判据"或"手工指定站点"的介入。** 没有改 `pipeline/` 下任何代码。

---

## 上一轮遗留（必须披露，因为它影响所有旧数据）

| 时间 | 改了什么 | 为什么 | 类别 |
|---|---|---|---|
| 2026-11-02 | `projects/ARVO-42494732/v2/experiment/run_reps.sh`：`-seed=1` → `-seed=$((SEED_BASE + r))` | 原来 10 个 run 全用同一个 `-seed=1`，5 个 rep 是**同一次确定性运行的重放**（`reps_pathB` 的 675 个崩溃文件只有 136 个唯一 sha1）。不改就没有独立的重复 | ⚠️ **方法学修正**（不是判据修正）——它只改"重复怎么采样"，不改任何"特征能不能落地"的判据 |

**影响面**：所有在此之前的 n=5 数据（`reps_n5_r1` / `reps_n5_r2` / `reps_n5_dxfonly` /
`reps_pathB` / `reps_after_pathB`）都有 22–80% 的跨 rep 崩溃输入重复，CI 偏窄。
**目前唯一独立的 n=5 数据是 `reps_pathB_r3`（731 个崩溃文件 / 731 个唯一 sha1 / 两两交集全 0）。**

---

## 待记录（B3 之后）

如果进入 B3，下列动作会逐条追加到上表：

- 为候选项目建容器 / 拉源码到 `pin_commit` / 建 CPG
- 准备种子（含 OSS-Fuzz `*_seed_corpus.zip` 的获取）
- 写该项目的 `build.sh`
- 任何 `pipeline/` 下的代码改动（若有，必须先归类；落到禁止类就停止）

---

## 当前状态

**B2 出表后已停止，未进入 B3。** 所以除上面的 4 条环境动作外，没有任何针对"第二个项目"的介入。

---

## R5（2026-11-03）—— 把适用性判据从「名单」改成「结构」

| 时间 | 改了什么 | 为什么 | 类别 |
|---|---|---|---|
| 12:5x | 新增 `outputs/stage4/uaf/applicability_rules.json`（5 条规则） | 把 `classify()` 里按 `llm01`…`llm05` 硬编码的判据抽成数据 | ⚠️ **方法学修改**（本轮任务本身，不是 R4 B0 的禁止类） |
| 12:5x | `pipeline/s5_4_analyze.py`：`classify()` 改成通用匹配器 `match_rule()`；`scan_sites()` 新增记录 `reassigned_between` | 同上；让判据可被 stage4 产出、可被机器判定 | ⚠️ 方法学修改 |
| 13:0x | **删除** R4 Phase 2 的预筛（`applicability()` / `REACHABLE` / `PATTERN_BY_NAME` / `STDLIB_NAMES` 80 条黑名单） | 该预筛是"项目在不在训练集里"的成员测试（R4 已查明），不是适用性判定 | ⚠️ 方法学修改 |
| 13:0x | 状态机去掉 `not_applicable` | 它是成员测试的产物 | ⚠️ 方法学修改 |

**没有为了让某个特征落地而调任何判据值。** 步骤 1 的唯一一次"调"是把规则级 `why`
下移到 `any_of` 分支，目的是让**输出理由**与改前逐字一致，不改任何判定结果（diff 已验证无差异）。
| 13:2x | `pipeline/s4_abstract_features.py`：prompt 加 `applicability_rule` 词表 + `check_rule()` 校验 + `emit_rules()` | 让 stage4 自己产出判据（R5 步骤 3，研究主张本身） | ⚠️ 方法学修改 |
| 13:3x | `pipeline/s5_2_prepare.py::extract_function()`：兼容"返回类型与函数名同行"的签名，并排除声明/调用 | curl 的 `static int h2_session_send(...)` 匹配不到 → `function_not_found`。**这是通用解析缺陷，不是判据** | ⚠️ 有条件允许（已回归：libredwg 抽出的 938 字节逐字节相同） |
| 13:3x–13:5x | `git fetch` 补全 curl / gpac 的 pin commit（`5c55fe6df605` / `319d44795db1`） | 本地缓存缺 pin，`process()` 会**静默退回 HEAD** 用错源码 | ✅ 环境工作 |
| 13:4x | 新建 `projects/ARVO-42508326`、`projects/ARVO-42518828` 工作区（clone + CPG dump + worklist） | R5 步骤 5 的前置 | ✅ 环境工作 |

**本轮仍然没有为了让某个特征落地而调任何判据值。** 步骤 3 的 `expressible:false` 是模型的判断，
我**没有**去改 prompt 逼它产出一个规则；步骤 5 的两个项目都在 worklist 自检处停止，**没有绕过**。

---

## R6（2026-11-03）—— 让 gpac 跑通

| 时间 | 改了什么 | 为什么 | 类别 |
|---|---|---|---|
| 14:1x | `pipeline/s5_2_prepare.py::main_worklist()`：新增 `fault_anchor`（故障函数无条件入表）+ `fault_neighbor`（一层邻居，**仅在锚点补位时**） | 从 `LLVMFuzzerTestOneInput` 正向展开 depth≤2 够不到 gpac 的故障函数；锚点是局部补位，不是判据 | ⚠️ 方法学/工程修改（本轮任务本身） |
| 14:1x | `main_worklist()`：入表函数加 `source` 字段、打印来源分布、**显式告警**"故障函数靠锚点入表、不在闭包内" | 方法局限必须可见，不能藏 | ⚠️ 同上 |
| 14:2x | `process()`：`pin` 缺失 → 先 `git fetch --tags` 补全 → 仍缺则 **`SystemExit` 硬失败**；新增 `--allow-head-fallback`（默认关，启用时大字警告） | 原来静默退回 HEAD，会用错版本的源码（curl 退到 `f0da5390ad9d`、gpac 退到 `3f056542b377`） | ⚠️ 同上 |
| 14:2x | `main_worklist()`：CPG 校验加两道——`fault_file` 在不在图里、**故障函数本身**在不在图里 | `find_cpg()` 只按文件名匹配，选到的图可能解析不到故障函数 | ⚠️ 同上 |
| 14:3x | `pipeline/s5_1_main.py::_run()`：`SystemExit` 的字符串消息打印到 stderr | 原来只保留退出码，硬失败但**不说原因** | ✅ 缺陷修复 |

**没有为了让 gpac 命中而改任何判据值**（`applicability_rules.json`、`match_rule()`、`classify()`
本轮**零改动**）。锚点只是让**故障函数进入待扫描清单**，不做任何"它算不算 UAF"的判断。
| 14:2x | `pipeline/s5_4_analyze.py::shortlist()`：排序键 `depth` 改 None-safe | 步骤 1 给锚点填了 `depth=None`，`(None, int)` 比较报 TypeError（**这是步骤 1 引入的回归**） | ✅ 缺陷修复 |
| 14:3x | `pipeline/s5_4_analyze.py::wrapper_frees_param()`：free 检测正则加 `re.I` | gpac 的 `gf_free` 是 `{ FREE(ptr); }`，大写宏没被识别 → 被误判成"只释放成员的包装" → 真站点被丢弃 | ⚠️ **通用缺陷修复**（对照测量：gpac 站点 0→1，libredwg 4→4 不变；回滚：`cp /tmp/r6_s5_4_analyze.BEFORE pipeline/s5_4_analyze.py`） |

**判据层本轮零改动**（`applicability_rules.json` mtime 13:26、`s5_4_analyze.py` 的
`classify`/`match_rule` 未触碰，已用 mtime 与代码 diff 确认）。

---

## R7（2026-11-03）—— 自主发现 + 跨函数扫描

| 时间 | 改了什么 | 为什么 | 类别 |
|---|---|---|---|
| 15:1x | `pipeline/s5_1_main.py`：直通分支改为转发**原始 argv**（+`strip_osv`），不再只转发 `extras` | **bug**：`--depth` / `--type` / `--feature` / `--default-weight` 是 argparse 已知参数，被入口吃掉后没传给下游 → gpac 的 `--depth 3` 一直按 2 跑（R5/R6 两轮记录的疑点） | ✅ 缺陷修复 |
| 15:2x | `pipeline/s5_2_prepare.py`：`fault_anchor` / `fault_neighbor` 改为 `--fault-anchor` 显式开关，**默认关闭**；启用时打字警告 | R6 的锚点把答案喂给了流程，正式结果必须是流程自己走到的 | ⚠️ 方法学修改（本轮任务本身） |
| 15:2x | `s5_2_prepare.py`：自检"清单不覆盖已知崩溃行"从**只打印**改成**硬停**（不再写出不可信清单） | 覆盖不到崩溃行的清单没有使用价值，写出去会被下游当成有效输入 | ✅ 缺陷修复 |
| 15:2x | `s5_2_prepare.py`：`anchor_in_closure` 改为**永远计算**（原来在开关块内，默认关闭时为 None → 打印错误消息） | 修自身 bug | ✅ 缺陷修复 |
| 15:3x | `s5_4_analyze.py`：`target_surface.json` 的 `validation` 与 `feature_pipeline.json` 顶层继承 `fault_anchor_enabled` / `fault_fn_in_closure` | 让引用结果的人一眼看到"这份结果喂过答案没有" | ⚠️ 方法学修改（可观测性） |

**判据层零改动**：`applicability_rules.json`、`match_rule()`、`classify()` 本轮未触碰。
**没有为了让任何站点命中而调判据值。**
| 22:1x | 取 gpac 的 fuzz harness：`gpac/testsuite@master:oss-fuzzers/fuzz_parse.c` → `projects/ARVO-42518828/harness/` | harness 在 gpac 的 **submodule**（`gpac/testsuite`）里，`git grep` 不进入未初始化子模块；OSS-Fuzz 的 `projects/gpac/` 只有 Dockerfile/build.sh | ✅ **环境工作**（外部源码；来源：gpac/testsuite master，非 pin 提交） |
| 22:1x | `s5_2_prepare.py::fetch_harness`：预置 harness 优先；搜不到 → `SystemExit(harness_not_found)` + 读 `.gitmodules` 提示 | 原来静默留空目录 → `input_format` 悄悄退化为 `raw_bytes` | ✅ 缺陷修复 |
| 22:3x | `s5_4_analyze.py`：`input_branch()` 从写死的 libredwg 路径前缀表 → **从 harness 源码 + CPG 调用图推导**；新增 `_strip_if0` / `_func_body` / `derive_format_dispatch` / `_branch_name` | B0 的"⚠️ 有条件允许"类：把写死的项目常量泛化成通用规则，且**不含任何项目专属路径/函数名** | ⚠️ 有条件允许（已回归：libredwg 的 branch/magic/site/权重全项一致） |
| 22:4x | `s5_4_analyze.py`：新增 `scan_cross_function_sites()` + `dead_lines()` + `_params_of()`（跨函数站点，6 道守卫） | R7 步骤 4：让扫描看得见跨函数形态，才能检验另外 4 个特征 | ⚠️ 方法学修改（本轮任务本身） |
| 22:4x | `s4_abstract_features.py`：`RULE_VOCAB["use_kind"]` 加 `cross_function`；prompt 说明"只覆盖实参传递这一种跨函数形态" | 词表扩展（步骤 4 要求） | ⚠️ 方法学修改 |
| 22:5x | 重跑 stage4 → 新的 `applicability_rules.json`（5 条，0 条 rule_missing）；R5 版留档为 `applicability_rules.r5.json` | 步骤 4 第二层验收：看 4 个特征能否产出判据 | ⚠️ 方法学修改（**libredwg 结果因此改变**：found 1/5 → 4/5，权重 1×0.5 → 4×0.125） |

**没有为了让任何站点命中而手工改判据值。** 新判据全部是 stage4 自己产出的；
`llm02` 的恒真、`llm03/05` 的近恒真都**原样保留**并写进报告，没有修。

---

## R8（2026-11-04）—— 核实权重 / 收紧判据 / 定型

| 时间 | 改了什么 | 为什么 | 类别 |
|---|---|---|---|
| 00:1x | `s5_5_build.py`：合并动作的 `weight` 改为 `sum(rows[*].weight)`；`weighting.features` 与 `per_feature` 改按**站点数**算 | **潜伏 bug**：4 个特征指向同一站点时，站点合并成功但权重没合并 → `weight 0.125`、`total 0.625`（应为 0.5 / 1.0）。R7 之前只有 1 个 found，从未触发 | ✅ 缺陷修复 |
| 00:2x | `s4_abstract_features.py`：`check_rule()` 加**可证伪性校验**（每个合取分支至少一个字段是真子集）+ prompt 说明 | R7 放宽词表后模型给出 `any/any` 与"全列上"的恒真判据，等于没有判据 | ⚠️ 方法学修改（本轮任务本身） |
| 00:3x | `s4_abstract_features.py`：失败时写 `feature_<tag>.no_rule.json` sidecar；`emit_rules()` 先读 sidecar | **静默用旧值**：某特征本次失败时，`emit_rules` 会读上次残留的 `feature_*.json`，把旧判据当成新结果（实测 `uaf-llm04`"复活"过一次） | ✅ 缺陷修复 |
| 00:4x | 恢复 `source_context.json` 的 `testcase_path`（指向 ARC 复现的 testcase，256 字节） | 该键在 `source_context.json` 某次重新生成时丢了 → `s5_verify` 的 **V4 变成"跳过回放"** | ✅ 环境工作（R5 白名单项 1 的键） |
| 00:4x | 重建 `llvmfuzz`（`mutator.c` 已被 `generate` 重新生成为 294 行） | 让二进制与当前算子一致 | ✅ 环境工作 |

**判据层的判定函数本轮零改动**（`match_rule` / `classify` / `_site_free_kind` / `_match_conjunct`）。
**没有为了让任何站点命中或不命中而手工改判据值**：`llm02` 的恒真、`llm05` 丢掉
`is_link_read` 都**原样保留**并写进报告。
| 00:5x | 新建 `docs/ARCHITECTURE.md`（241 行 / 12 节，只写当前状态） | R8 步骤 4：这份文档在 2026-11-02 重构里被删，之后没有任何文档讲清布局/五阶段/产物层次/门禁/实验设施 | ✅ 文档 |
| 00:5x | `HANDOFF.md`：开头加「证明了什么 / 没证明什么」；限制 5→8 条；更新限制 2；补六层产物实测数字 | R8 步骤 5/6：把限制写全、结论定稿 | ✅ 文档 |
| 00:6x | 提交 `0df91f35`（77 文件 / 1.14 MB） | R8 步骤 7：代码 + 文档 + JSON 产物提交一次。**刻意未提交 `docs/` 下 7 份被删文档的删除**，那需要你决定 | ✅ 版本控制 |
| 01:0x | 删除 5 组非独立的 `reps_*` 快照（`reps_n5_r1`/`reps_n5_r2`/`reps_n5_dxfonly`/`reps_pathB`/`reps_pathB_r2`，回收 40.2 M）；删前把 4 组的 `summary.json` **移**到 `docs/runs/reps_summaries/` | 用户确认按推荐清理。保留 `reps_pathB_r3`（128 M，唯一独立的 n=5，731 个 `crash/` 是证据）与 `reps_after_pathB`（回归证据） | ✅ 用户批准的清理 |
| 01:0x | 提交 `docs/` 下 7 份被删文档的删除 | **用户确认那 7 份是用户自己删的**（R5 时就说过"不要恢复"） | ✅ 用户批准的删除 |

---

## R9（2026-11-04）—— 加固已有结果

| 时间 | 改了什么 | 为什么 | 类别 |
|---|---|---|---|
| 00:29 | 用当前二进制（`a416b44d`，算子 294 行 sha1 `d7913b9e`）重跑 A/B：`default 0 / 1,102,847` vs `custom 617 / 640,359`，产物 `reps_r9_final`（128 M） | R6 的 `reps_pathB_r3` 测的是 440 行那版算子，不是同一个可执行文件 | ✅ 实验（重跑） |
| 12:3x | **`s5_4_analyze.py::_match_conjunct`：`bool(want)` → `_as_bool(want)`** | **bug**：`bool("false")` 是 True，判据里"要求 false"被静默反转成"要求 true"→ 规则恒假、0 命中。R8 的"llm02/03/05 0 命中"就是这个 bug | ✅ 缺陷修复 |
| 12:3x | `s4_abstract_features.py`：加 `load_touchstone()` / `_conjunct_real_fields()`（语义诊断）+ `STRUCTURALLY_FIXED`（`reassigned_between` 不计入区分力）+ `falsifiability_check` 写进产物 | R8 的语法校验放过了真空约束 | ⚠️ 方法学修改（本轮任务本身） |
| 12:3x | 门禁默认 `structural`（不是 `semantic`）：实测 `semantic` 会把 `llm01` 判成 `rule_missing`（试金石只有 2 个正例） | 语义模式在这套数据上不可用；保留 `--falsifiability semantic` 可复现 | ⚠️ 方法学修改 |
| 12:4x | `s2_2_facts.py`：Joern deep 失败从 `return {}, items` 改成写 stderr + `{"_failed": True}` | **静默失败**：下游看到"字段缺失"而不是"分析失败" | ✅ 缺陷修复 |
| 12:4x | `s5_6_lib.py`：tool `arguments` 不是合法 JSON 时不再 `args={}` 执行，改成跳过 + 回喂错误 | **静默失败**：空参数跑工具会产出"看起来正常但没查对"的结果 | ✅ 缺陷修复 |
| 12:4x | `s4_abstract_features.py::emit_rules`：按 `_RUN_STARTED_AT` 过滤 mtime，跳过上次残留的 `feature_*.json` | **静默用旧值**（R8 的 sidecar 只挡了一半） | ✅ 缺陷修复 |
| 12:4x | `s5_5_build.py::main_plan`：判据比 `feature_pipeline.json` 新时打 stderr 警告 | **读文件不校验时效**（R7/R8 出现过 plan 停在 11-02） | ✅ 缺陷修复 |
| 12:4x | `git checkout -- v2/mutator.c v2/mutator.json`（恢复 294 行那版），重建二进制 | `generate` 不可复现（440/294/243 三版）；恢复后二进制 sha1 与 `reps_r9_final` 逐字节相同 | ✅ 环境工作 |

**判据值一个都没有手工改。** `llm05` 丢掉 `is_link_read`、`reassigned_between` 恒为 false 都原样保留并写进报告。
