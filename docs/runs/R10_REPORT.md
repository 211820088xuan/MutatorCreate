# R10 报告

日期：2026-11-04
本轮两件事：**把静默失败从地基上清掉**（步骤 1）、**修 stage3/stage4 的三层设计问题**（步骤 2–5）。

> 本文是本轮全部产出。每完成一步追加一节，不覆盖前面内容。

---

## 步骤 1 · 注入故障测试

### 做了什么

新建 **`tests/test_fault_injection.py`**（24 个测试，跟 `pytest tests -q` 一起跑，0.4 s）。
每个测试对应一个注入点：制造失败 → 跑流程 → 断言"故障被发现了"。

**关键设计**：测试通过 = **流程确实发现了故障**。为证明测试不是摆设，
对四处修复做了**变异检验**（把修复退回，确认测试变红）：

| 退回哪处修复 | 变红的测试 |
|---|---|
| `_as_bool` → `bool()` | 3 个（`test_string_false_means_false_not_true` / `test_string_reassigned_false` / `test_bool_and_string_agree`） |
| V4 缺 testcase → `pass` | 1 个（`test_v4_without_testcase_is_not_applicable`） |
| `emit_rules` 去掉 mtime 过滤 | 1 个（`test_emit_rules_skips_stale_file`） |
| Joern 失败去掉 `_failed` | 1 个（`test_guard_joern_failure_is_recorded`） |
| tool args 改回 `args = {}` | 1 个（`test_guard_bad_tool_args_not_executed`） |

### 注入点 × 实际反应 × 判定 × 处理

| # | 注入点 | 注入了什么 | 流程的实际反应 | 判定 | 处理 |
|---:|---|---|---|:---:|---|
| 1 | 类型/解析错 | 判据写字符串 `"false"` / `"true"` / `"any"` | `_match_conjunct` 走 `_as_bool`，语义与布尔一致（3 个测试 + `bool`/字符串等价断言） | ✅ 已发现 | R9 修过，本步**加了回归测试** |
| 2 | 参数被吞 | `worklist --depth 4` / `features --type hbo --feature X` | 直通把 `--depth 4`、`--type hbo`、`--feature X` 原样交给下游；`--osv` 只出现一次 | ✅ 已发现 | R7 修过，本步**加了 3 个回归测试**（抓 `_run` 收到的 argv，不是抓 `sys.argv`） |
| 3 | 产物残留 | 留一个 mtime 早于本次运行的 `feature_*.json` | `emit_rules` 跳过它并打印 `⚠️ 跳过 1 个上次运行残留的 feature_*.json: [...]` | ✅ 已发现 | R9 修过，本步**加了测试** |
| 4 | 产物残留（sidecar） | 同时留成功的 `feature_*.json` 和本次失败的 `*.no_rule.json` | 判据**不被采用**，进 `rule_missing` | ✅ 已发现 | R8 修过，本步**加了测试** |
| 5 | 产物过期 | `feature_pipeline.json` 的 mtime 改成比 `applicability_rules.json` 旧 | 判定为"过期"（逻辑测过） | ✅ 已发现 | R9 修过；本步把判定抽成通用 `warn_if_stale()` 并**加了 3 个测试** |
| 6 | **门禁假通过** | **去掉 `testcase_path`** | **R9 之前：`V4 = pass` + 一句 note，`overall = pass`** | ❌ **没发现** | **本步修**：改为 `not_applicable`，`overall` 变成 `pass_with_skipped` |
| 7 | 版本不符（pin 缺失） | 静态守卫：`s5_2_prepare.py` 必须有 `SystemExit(commit_not_found)` + `ALLOW_HEAD_FALLBACK` 逃生口 | 代码里有（R6 修） | ✅ 已发现 | **静态守卫测试**（见下"弱点"） |
| 8 | CPG 不覆盖 | 静态守卫：必须有 `cpg_missing_fault_fn` / `cpg_missing_fault_file` | 代码里有 | ✅ 已发现 | **静态守卫测试** |
| 9 | 外部工具失败（Joern） | 静态守卫：失败路径必须写 `"_failed": True` + 打 stderr | 代码里有（R9 修） | ✅ 已发现 | **静态守卫测试** |
| 10 | 工具参数坏 | 静态守卫：必须有 `bad_tool_args` 日志 + 回喂错误，且代码里不再有 `args = {}` | 代码里有（R9 修） | ✅ 已发现 | **静态守卫测试** |

**只有 1 个注入点"没发现"（#6 门禁假通过），已修。**

### ⚠️ 弱点必须说明

第 **7–10** 个注入点用的是**静态守卫测试**（`assert "commit_not_found" in 源码`），
不是真实注入。原因是它们藏在 `s5_2_prepare.process()` 与 `s2_2_facts.main()` 的**闭包**里，
真实注入要造 git 仓库 + 跑 Joern，是分钟级。

**静态守卫的弱点：只证明"代码里有这个分支"，不证明"分支真的会走到"。**
变异检验能红，说明它能防"有人把硬失败改回静默回退"，但**不能**证明运行时行为。

要补上，需要把 `process()` 的 Joern 调用抽成可注入的依赖——**那是重构，不在本轮**。

### 剩余 JSON 读取的主链标注

R9 查出 45 处 `json.load(open(...))` 只有 2 处有时效检查。本步重新分类：

| 类别 | 处数 | 处理 |
|---|---:|---|
| **结论路径上**（读 `facts` / `source_context` / `audit_worklist` / `target_surface` / `vuln_report` / `feature_pipeline` / `mutation_plan` / `applicability_rules`） | **11** | 2 处已有（R9 的 `emit_rules` / `main_plan`），本步加 **1 处**（`s5_4_analyze.main_features` 的 `target_surface` 时效检查）；**剩 8 处** |
| 非结论路径（读缓存 / 批次 / 单项目工作区） | 34 | **不动**（列清单） |

**剩下 8 处（结论路径上但没加）**：

```
  pipeline/s2_2_facts.py:1308      读 per-OSV facts 汇总
  pipeline/s5_3_audit.py:943,1180  读 source_context.json
  pipeline/s5_3_audit.py:945,1182  读 audit_worklist.json
  pipeline/s5_4_analyze.py:841     读 source_context.json（拿 repo_local）
  pipeline/s5_4_analyze.py:849     读 vuln_report.json
  pipeline/s5_4_analyze.py:1772-73 读 audit_worklist.json / source_context.json
```

**没加的理由**：这些读的产物之间**没有明确的新旧依赖顺序**
（`source_context` 只在 `fetch` 时写一次；`vuln_report` 是 audit 的输出，
而 audit 的输入是 worklist，链条比 `target_surface ← worklist` 弱）。
**硬加一个"比谁新"会造出假告警**，反而降低告警的可信度。
→ 想让这 8 处也有保护，需要的是**产物清单 + 版本号**（比如每个产物记 `upstream: [...] + sha`），
那是新设计，不在本轮。

### libredwg 全流程回归

| 项 | 结果 |
|---|---|
| 站点 | **`src/in_dxf.c:12284 → 12267`，`var=pair`，`branch=DXF`，`status=found`** ✅ 未变 |
| `found` | 4/5 |
| plan | **1 site / 1 mutation / weight 0.5 / total 1.0** ✅ |
| V1–V4 | **全 PASS**，`overall = pass` |
| `pytest tests -q` | **24 passed**（原 4 + 新 20） |

### 顺带按用户口径改写「限制 9」

`HANDOFF.md` 的限制 9 从"算子不可重生成（缺陷）"改成
**"引用 A/B 结果必须连 `mutator.c` 的 sha1 一起记"（记录要求）**：

> 同一份 plan 每次 `generate` 产出不同的算子实现，**这是设计而不是缺陷**。
> 每次生成是一次独立的 LLM 调用，"能力等价 + 实现不同"完全可以接受。
>
> **记录要求**：引用任何 A/B 数字时必须同时记 `mutator.c` 的 sha1。
> 当前可引用的组合是：**`reps_r9_final` + `mutator.c` sha1 `d7913b9e` + 二进制 sha1 `a416b44d`**。

---

### ⏸ 停止点：等用户确认（步骤 1 出口）

| 验收项 | 结果 |
|---|---|
| 注入测试能跟 `pytest tests -q` 一起跑 | ✅ 24 passed / 0.4 s |
| 每个注入点报"注入什么 / 实际反应 / 判定 / 处理" | ✅ 10 个注入点，**1 个"没发现"已修** |
| 测试真的能抓回退（不是摆设） | ✅ 5 处变异检验全部变红 |
| 剩余 43 处 JSON 读取的主链标注 | ✅ 11 处在结论路径上，本步加 1 处；**剩 8 处未加，理由已写明** |
| libredwg 回归 | ✅ 站点 / 权重 / 门禁 / pytest 全不变 |

**请确认后进步骤 2（把 stage2 的 `reassigned_between` / `cross_frame_count` 接进 stage3）。**

---

## 步骤 2 · 接 `reassigned_between` / `cross_frame_count`（0 LLM）

### 做了什么

**① `reassigned_between` —— 直接用 stage2 已经算好的值**

`pipeline/s2_3_interpretation.py::_reassign_between()` 的结果在
`artifacts/interpretation/<OSV>/interpretation.json` 的 `findings.reassigned_between`。
`measure_dims()` 直接读它，**没有重写逻辑**。

**② `cross_frame_count` —— 用 CPG 调用图算**

新增 `_call_graphs()`（读 `artifacts/call_edges/<project>_<pin>.tsv` 与
`projects/*/cpg_dump.tsv`）+ `_hops()`（无向 BFS + 邻接索引）。

**调用边是怎么来的**：`cpg_files/*.cpg` 是 Joern 图，**不能直接读边**，
所以写了一个 Scala 脚本 `cpg.call.map(c => (c.method.name, c.methodFullName))` 抓边，
每个图约 22 s，结果缓存成 TSV（`artifacts/call_edges/`，**已加进 `.gitignore`**，
116 M，可由 `cpg_files/*.cpg` 重建）。

**③ 接进 stage3**：`prepare()` 给每个样本加 `measured_dims` 字段，
prompt 里明说"这是 **stage2 实测**的，不是让你猜的；`cross_frame_exact=false` 时
`cross_frame_count` 写 unknown"。

### 分布数据

**`reassigned_between`（121 条 UAF，来源 `interpretation.findings`）**

```
  None  80
  True  25
  False 16
```

✅ **与用户给的数字完全一致（None 80 / True 25 / False 16）。**

> 途中发现：还有一个 `free_related.reassign_between` 回退源，挂上会把一条 `None` 变成 `False`
> （变成 79/25/17）。为了与 stage2 的正式产物一致、可复现用户的数字，**只用 `findings` 一个来源**。

**`cross_frame_count`（无向调用图距离，可算出 61/121）**

```
  0 跳      11
  1 跳      15
  2 跳      30
  3 跳       3
  4 跳       2
  None      60   （项目没有 CPG，或该 pin 的图不在 cpg_files 里）
```

**`free_cross_function`（`facts` 里已有，121/121 全覆盖）**

```
  True  110
  False  11
```

### 两个必须说明的方法学问题

**① 有向距离错，必须用无向**

第一版用**有向** BFS（free_fn → use_fn），**121 条里只有 16 条能算出**。
原因：UAF 的"释放"与"使用"通常在**兄弟函数**里（都由更上层调用），
从 free_fn 出发**根本到不了** use_fn。
改成**无向**距离后能算出 61/121。
`_hops()` 的 docstring 里写清了这个理由。

**② 覆盖不到全部 121 条**

- 121 条 UAF 跨 35 个项目，需要 **95 个不同的 CPG**（`<project>_<pin>.cpg`）；
- `cpg_files/` 里有 **81 个**，缺 14 个；
- 本轮按 **UAF 样本数降序**抓了 **62 个**（116 M），覆盖 **61 条**；
- **剩下的没抓完**（每个图 ~22 s，全抓 ~35 min）。缓存是**增量**的，
  `measure_dims()` 会自动捡到新抓的图，**补跑不需要改代码**。

**所以 `cross_frame_count` 现在 61/121 有精确值，60 条是 unknown。**
步骤 3 的合并判据不应该只用它——**`free_cross_function`（121/121 全覆盖）更可靠**。

### 验证传到了、传得对

重跑 `python3 pipeline/s3_extract_patterns.py prepare`（**0 LLM**），检查 batch 输入：

```
  batch 文件: 9（uaf）
  全部 batch 汇总: {'rb=已知': 41, 'cfc=已知': 61, 'rb=None': 80, 'cfc=None': 60}
```

✅ **`rb=已知 41` 与用户给的"121 条里 41 条有确定值"完全一致。**
✅ 61 条带精确跳数。
✅ 样例：
```json
{"reassigned_between": true, "cross_frame_count": null, "cross_frame_exact": false,
 "free_cross_function": true, "free_fn": "xmlFreeAttribute", "use_fn": "xmlValidateOneElement"}
```

**这一步没有重跑 stage3**（只跑了 `prepare`，它不调 LLM）。

### 失败与存疑

1. **14 个 pin 的 CPG 不在 `cpg_files/` 里**，那 14 条 UAF 永远算不出跳数。
   要补需要重新建图（Joern 解析源码，分钟级/项目）。
2. **`cross_frame_count` 的语义是"两个函数在调用图上的无向距离"**，
   不是"释放与使用相隔的栈帧数"。后者在"释放已经返回"的场景下没有定义。
   引用时必须写明是前者。
3. **`prepare()` 重写了全部 stage3 的 batch 输入与 prompt**（uaf/hbo/stack/global 共 62 个 batch），
   所以 `git status` 里有大量 `M outputs/stage3/*/input|prompt/*`。这是预期的。
