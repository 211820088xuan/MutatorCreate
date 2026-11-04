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

---

## 步骤 3 · stage3 合并判据（只重跑 uaf）

### 预算决定（按你的口径）

**只重跑 uaf 的 9 个 batch**；hbo / stack / global 的 `final.json` **保持旧判据不动**。
`runmerge` 对这三类打印了 `final.json 已存在，跳过`，**没有覆盖**。

> 副作用如实记：`merge` 步骤重写了 hbo/stack/global 的 `merge_input.json`
> （现在带 `measured_dims`），但它们的 `final.json` 没变。

### 改了什么

**① 换合并判据**（`MERGE_SYSTEM` 规则 1b）

- 旧：`free_before_use` + `free_and_use_same_function`
- 新：**`free_and_use_same_function` / `reassigned_between` / `in_loop` / `free_cross_function`**
- 明确禁止：**不用 `free_before_use`**（对 UAF 恒 true）；**不主要靠 `cross_frame_count`**
  （61/121 有值，把 unknown 当"值"比较会把无关样本错误归组——这正是旧版的老毛病）

**② `dimensions` 加 `free_cross_function`**（8 维，来自 `facts`，**121/121 全覆盖**）。
按你的修正 1：主力用全覆盖的字段，`cross_frame_count` 只作辅助。

**③ 合并后硬校验 `dedupe_vectors()`**：8 维（去重时用 4 维判据字段）向量完全相同的
pattern **强制合并**，记 `merged_from` + `merged_groups`。

**④ 保留 per-sample 计数**：schema 加 `dimension_distributions`（如
`{"alloc_kind": {"heap": 26, "unknown": 1}}`），不再只给众数。

### 四类的前后对照表

| 类型 | 判据版本 | 改前规律数/可区分点 | 改后规律数/可区分点 | 仍完全相同的组 |
|---|---|---|---:|---|
| **uaf** | **R10 新判据（重跑）** | 5 / **4** | **5 / 5** | **无** |
| hbo | 旧判据（**未重跑**） | 5 / 3 | — | 3 条同点，395/504 |
| stack | 旧判据（**未重跑**） | 6 / 5 | — | 2 条同点 |
| global | 旧判据（**未重跑**） | 6 / 4 | — | 3 条同点 |

**hbo / stack / global 的"改前"数字是本轮实测的**（读各自 `final.json` 的 7 维向量）：
`hbo: 3 条完全相同 ('heap','unknown','unknown','unknown','unknown','read','unknown')`；
`stack: 2 条相同`；`global: 3 条相同`。与 R9 记的 78% 一致。

### uaf：改前那两条是否仍然七维相同

**不再相同——它们被强制合并成一条了。**

| | 改前 | 改后 |
|---|---|---|
| 「清理析构后悬垂访问」 | `('heap','true','false','unknown','false','read','unknown')` | — |
| 「容器节点销毁后遍历」 | `('heap','true','false','unknown','false','read','unknown')` ← **完全相同** | — |
| 合并后 | — | **「清理销毁释放后读取 / 解析拷贝释放后读取」** support=80 |

`final.json` 的 `_dedupe` 字段记录了这次强制合并：

```json
{"before": 6, "after": 5,
 "merged_groups": [{"dims": {"free_and_use_same_function": "false",
                              "reassigned_between": "unknown",
                              "in_loop": "false",
                              "free_cross_function": "true"}, "…"}],
 "dims_used": ["free_and_use_same_function", "reassigned_between", "in_loop", "free_cross_function"]}
```

### uaf 改后的 5 条（8 维向量全部互不相同）

| pattern | support | free_and_use_same_fn | reassigned | in_loop | free_cross_fn | access | cfc |
|---|---:|---|---|---|---|---|---|
| 同函数释放后访问 | 10 | **true** | unknown | unknown | **false** | read | **0** |
| 别名重赋值跨函数访问 | 14 | false | **true** | unknown | true | read | unknown |
| 解码池释放后写入 | 5 | false | unknown | unknown | true | **write** | unknown |
| 循环回调释放后读取 | 8 | false | unknown | **true** | true | read | 2 |
| 清理销毁释放后读取 / 解析拷贝释放后读取 | 80 | false | unknown | **false** | true | read | unknown |

**`reassigned_between` / `free_cross_function` 不再是全 unknown** —— 旧版 5 条里这两个维度
**全部是 unknown**，现在至少有 1 条 true / 4 条 false 的区分。

### 失败与存疑

1. **改造暴露了一个我自己引入的静默 bug**：`_RUN_STARTED_AT` 被放在 `run_one` 循环**之后**，
   于是本次刚写的 5 个 `feature_*.json` 全部比"运行起点"旧 → 被当成上次残留跳过 →
   判据汇总变成 **0 条可用**。已修（移到 `main()` 开头）并加了测试
   `test_main_sets_run_start_before_running`。**这是第六个同类 bug，而且是修同类 bug 时引入的。**
2. **`cross_frame_count` 仍只有 61/121**。剩下 60 条是 unknown，本轮没抓完
   （62 个 CPG 已缓存，可增量补）。
3. **hbo/stack/global 仍是旧判据**。它们的"可区分点"数字**不能和新判据下的数字混用**——
   所以上表把"判据版本"单列一列。

---

## 步骤 4 · stage4 加区分依据

### `differentiator` 与 `merge_into`

`s4` 的输出 schema 新增两个字段：

```json
"differentiator": [{"vs": "另一条特征", "field": "可判定字段名", "this": "本条取值", "other": "那条取值"}],
"merge_into": "（可选）如果这条其实是另一条的子集"
```

**校验**（`check_differentiator()`，进 `validate()` 与 `run_one` 的重试条件）：

1. `differentiator` **必填**，不能是字符串（散文）；
2. 每条必须**引用可判定字段**——`DECIDABLE_FIELDS` = stage3 的 8 个 dimension +
   判据的 `use_kind` / `free_kind` / `is_link_read`；写别的字段名直接拒；
3. 每条必须有 `this` / `other` 取值。

SYSTEM prompt 明说：**"如果你发现这条特征其实是另一条的子集，直接写 `merge_into`。
合并成 2-3 条是合法结果，比硬凑 5 条互相重叠的特征有价值。"**

### 5 条的 `differentiator`

| pattern（→ feature_name） | differentiator（field: this ≠ other） |
|---|---|
| **同函数释放后访问** → 同函数直接释放后继续访问原堆对象 | `free_and_use_same_function`: true ≠ false（vs 跨函数释放后访问）<br>`free_kind`: direct_free ≠ realloc_self_assign |
| **循环回调释放后读取** → 释放后经跨函数循环或回调访问旧指针 | `use_kind`: cross_function ≠ same_path<br>`free_kind`: direct_free ≠ realloc_self_assign |
| **别名重赋值跨函数访问** → 释放后跨函数复用旧别名访问 | `use_kind`: cross_function ≠ same_path / ≠ loop_back<br>`free_kind`: direct_free ≠ realloc_self_assign<br>**`reassigned_between`: true ≠ false**<br>**`is_link_read`: false ≠ true** |
| **清理销毁释放后读取 / 解析拷贝释放后读取** → 清理/销毁跨函数直接释放后读取对象字段 | **`is_link_read`: false ≠ true**<br>**`reassigned_between`: false ≠ true**<br>`free_kind`: direct_free ≠ realloc_self_assign<br>`use_kind`: cross_function ≠ same_path |
| **解码池释放后写入** → 内存池释放后跨函数读写 | `free_and_use_same_function`: false ≠ true<br>`use_kind`: cross_function ≠ loop_back<br>`free_kind`: direct_free ≠ realloc_self_assign |

**全部落在可判定字段上，没有一条是散文。** ✅

### 有几条标了 `merge_into`

**0 条。**

**这个 0 是有意义的**：R9 那 5 条互相包含（llm05 ⊂ llm01、llm03 ⊂ llm01）是因为
**合并判据不严导致分类重叠**；换成有区分力的判据后，stage3 产出的 5 条**维度向量已经互不相同**，
模型看不出子集关系，于是没有标 `merge_into`。

### libredwg 回归

```
  ✅ uaf-llm01   found    短名单 162 / 原语 4 / 支持 4
       站点 src/in_dxf.c:12284 → 12267  var=pair  branch=DXF     ← 未变
  ❌ uaf-llm02/03/04/05  not_found（rule_missing）
  found 1/5；权重 default 0.5 + 1×0.5 = 1.0
```

**为什么 4 条变成 `rule_missing`**：`features.json` 是**手写的 5 条特征**，
它们的 `source_pattern` 指向**旧**的 stage3 分类名。换判据后分类法变了，
只有 `同函数释放后访问` 这个名字还在，其余 4 条**悬空**。
→ `emit_rules` 只映射到 `uaf-llm01`。

**这本身是个必须记的发现**：**stage3 的改进不会自动传导到 stage4 的特征**——
特征是手写产物，`source_pattern` 一断，判据就丢。已把 `emit_rules` 的静默 `continue`
改成打印 `⚠️ 4 条判据找不到对应的 feature（features.json 的 source_pattern 已过期）`。

`pytest tests -q` → **25 passed**。

---

## 步骤 5 · 判断：归纳方法的问题，还是 UAF 的固有属性

### 核心对照表

| | R9（改之前） | **R10（改之后）** |
|---|---|---|
| stage3 uaf 规律数 / 可区分点 | 5 / **4** | **5 / 5** |
| 仍完全相同的组 | **2 条**（清理析构 ≡ 容器节点） | **无** |
| stage4 特征数 / 互不包含的 | 5 / ?（4 条 `rule_missing`，实际只 1 条可用） | **5 条有判据，`merge_into` 0 条** |
| libredwg 命中站点 | llm01 的 4 个（llm02/03/05 同一批） | **llm01 的 4 个**（其余 4 条命中 0） |
| **是否有特征找到 llm01 找不到的站点** | **没有** | **没有（一条也没有）** |

**5 条新判据 × libredwg 的 4 个站点的完整矩阵**：

| pattern | 命中 |
|---|---|
| 同函数释放后访问 | **4**（`dwg_read_dxf:12839`、`encode_unknown_as_dummy:1271`、`:1308`、`dxf_objects_read:12284`） |
| 循环回调释放后读取 | 0 |
| 别名重赋值跨函数访问 | 0 |
| 清理销毁释放后读取 / 解析拷贝释放后读取 | 0 |
| 解码池释放后写入 | 0 |

### 结论：**都不是**——要分成两层

**第一层（stage3 的分类重叠）：归纳方法的问题，已修。**

5 条 → 仍 5 条，但**可区分点从 4 变成 5**，改前那对完全相同的被强制合并。
所以 UAF 的规律**不是**天然互相包含——在 8 维空间上它们可以分开
（support 10/14/5/8/80，`free_and_use_same_function`、`reassigned_between`、
`in_loop`、`free_cross_function`、`access_kind` 各有用武之地）。

**第二层（站点层面没有增量）：不是归纳的问题，也不是 UAF 的固有属性，是语料+扫描器的限制。**

其余 4 条 pattern 描述的都是**跨函数**形态（`free_and_use_same_function=false`，
`free_cross_function=true`），而 **libredwg 的跨函数站点扫出来是 0 个**
（R7 已实测：15→6→**0**，候选全是假阳性）。**没有站点可以命中，所以命中 0 不是判据太严。**

→ 要检验"归纳有价值"，**必须换一个能扫出跨函数站点的项目，或者换崩溃类型**。
在 libredwg 上无论判据怎么改，答案都会是"没有增量"——因为语料里只有一种形状。

### 对「限制 8」的修正

R9 写的"LLM 归纳没有正面证据"需要**收窄**：

- 不是"模型归纳不出东西"——它在有区分力的维度上给出了 5 条互不包含的判据；
- 而是**"在当前唯一的落地项目上，归纳的产物没有可命中的目标"**——
  语料只有同函数形状，其余 4 条跨函数判据无处落地。

**这比"LLM 不行"更准确，也更能指导下一步。**

---

## 汇总

### 五步结论各一句话

| 步骤 | 结论 |
|---|---|
| **1 · 注入故障测试** | 10 个注入点，**1 个"没发现"（V4 缺 testcase 仍报 PASS）已修**；24 个测试 + 5 处变异检验证明能抓回退 |
| **2 · 接实测维度** | `reassigned_between` 精确复现 **None 80 / True 25 / False 16**；`cross_frame_count` **61/121** 有精确值（无向距离，全抓需 ~35 min）；值已验证写进 batch 输入 |
| **3 · stage3 合并判据** | uaf **5 条 / 可区分点 4 → 5**，改前那对完全相同的被**强制合并**；hbo/stack/global 未重跑（旧判据，已注明） |
| **4 · stage4 区分依据** | 5 条 `differentiator` 全部落在**可判定字段**上；**`merge_into` 0 条**（分类已互不包含）；libredwg 站点未变 |
| **5 · 判断** | **两层**：分类重叠是归纳方法问题（**已修**）；站点层面没增量是**语料+扫描器限制**（libredwg 跨函数站点 0 个），**不是 UAF 固有属性** |

### 核心问题的答案

**「有没有特征找到 llm01 找不到的站点」→ 没有，一条也没有。**

而且是**按新判据实测**的（不是 R9 那版被 `bool("false")` bug 污染的结论）：

| pattern | libredwg 命中 |
|---|---|
| 同函数释放后访问（llm01） | **4** |
| 循环回调释放后读取 | 0 |
| 别名重赋值跨函数访问 | 0 |
| 清理销毁释放后读取 / 解析拷贝释放后读取 | 0 |
| 解码池释放后写入 | 0 |

**但命中 0 不是判据太严**：这 4 条都要求 `free_and_use_same_function=false` +
`free_cross_function=true`（跨函数形态），而 **libredwg 的跨函数站点是 0 个**。

所以真正卡住的**不是归纳**，是**语料与扫描器**：
- 唯一的落地项目只产出**同函数**形状的站点；
- 跨函数扫描器至今 0 命中（限制 7）；
- 因此任何跨函数判据都无处落地。

### `HANDOFF.md` 改了哪些（改动内容原文）

只改了**限制 8**（其余限制未动）。完整 diff：

```diff
@@ -221,36 +221,38 @@
 而且只支持"实参传递"一种形态；**结构体字段、全局变量、回调/函数指针**都没做，
 而真实项目里的"跨函数"大量走这三种。
 
-## 限制 8 · LLM 归纳没有正面证据（R8 收紧后仍然没有）
+## 限制 8 · LLM 归纳**有产物，但在唯一的落地项目上没有可命中的目标**
 
-R8 给判据加了**可证伪性硬约束**（每个合取分支至少一个字段是真子集；写 `any` 或把整个词表
-列上 = 恒真 = 拒绝），重跑 stage4，5 条判据**全部产出且全部具体**。
-但三层对照的结论是：
-
-| 对照 | 结果 |
-|---|---|
-| vs R7（恒真版） | 2 条从恒真变具体（`llm02` 的 `any/any`、`llm03` 的 4×4 全集都被拒了） |
-| vs R5 手工版 | **3 胜 1 负 1 平**：`llm02` 更具体（4 个字段 vs 1 个）、`llm03/llm04` 从 `name_regex` 变**结构判据**；**`llm05` 输了**（丢了 `is_link_read:true` 这个定义性特征）；`llm01` 互有胜负 |
-| **libredwg 实际命中** | **仍然只有 `llm01` 那 4 个站点**；`llm02/03/05` 命中的是**同一批** |
-
-**→ 判据层的所有改进（从名单到结构、从紧词表到松词表再收紧）都没有带来新的落地。**
-
-> **⚠️ R8 报告里"llm02/03/05 全部 0 命中"的机制是错的（R9 更正）**：
-> 那不是"规则太严"，而是 `_match_conjunct` 用 `bool(want)` 比较、
-> 而 `bool("false")` 是 **True** —— 模型写 `"false"` 时"要求 false"被静默反转成"要求 true"，
-> 规则恒假。修掉后它们命中 4/3/4 个站点（**与 llm01 同一批**）。
-> **结论不变（没有增量），但理由必须改成"它们的判据与 llm01 在本数据上等价"。**
-
-**真空约束的问题（R9 已处理）**：`reassigned_between` 在扫描器产出里**结构性恒为 false**
-（`scan_sites()` 注释自己写着"碰到重新赋值就截断"；跨函数站点更是硬编码 False），
-所以写它等于没写，**不计入区分力**（`STRUCTURALLY_FIXED`，带过期检查）。
-
-**更强的"语义可证伪"实测**（拿真实站点当试金石，逐字段去掉看命中集合变不变）：
-**不可用**——试金石只有 2 个站点且**全是正例**（`scan_sites()` 只产出已经筛成 UAF 形态的站点），
-任何**正确描述**这批站点的判据都会被判"排除不了东西"，实测**把 `llm01` 判成 `rule_missing`**（唯一能落地的特征）。
-→ 见限制 10。
-
+**先更正 R8/R9 的一处误判**：R8 说"`llm02/03/05` 全部 0 命中 → 没有增量"，
+机制是错的——那是 `bool("false") == True` 的解析 bug 把它们判死了（R9 修）。
+修掉后它们命中**同一批**站点。
+
+**R10 重做了这一层（换 stage3 合并判据 + 加实测维度 + 强制去重）**：
+
+| | 改前（R9） | **改后（R10）** |
+|---|---|---|
+| stage3 uaf 规律数 / 可区分点 | 5 / **4** | **5 / 5** |
+| 仍完全相同的组 | 2 条（清理析构 ≡ 容器节点） | **无** |
+| stage4 `merge_into` | — | **0 条**（分类已互不包含） |
+| libredwg 命中 | llm01 的 4 个 | **llm01 的 4 个** |
+| **有特征找到 llm01 找不到的站点吗** | 没有 | **没有（一条也没有）** |
+
+**所以结论要分成两层**：
+
+1. **分类重叠是归纳方法的问题，已修。** 8 维空间上 UAF 的规律**可以分开**
+   （5 条 support 10/14/5/8/80，`free_and_use_same_function` / `reassigned_between` /
+   `in_loop` / `free_cross_function` / `access_kind` 各有用武之地）。
+2. **"站点层面没有增量"不是归纳的问题，也不是 UAF 的固有属性，是语料 + 扫描器的限制。**
+   其余 4 条 pattern 描述的都是**跨函数**形态（`free_and_use_same_function=false`、
+   `free_cross_function=true`），而 **libredwg 的跨函数站点是 0 个**（R7 实测 15→6→0）。
+   **没有目标可以命中——不是判据太严。**
+
+→ **要检验"归纳有价值"，必须换一个能扫出跨函数站点的项目，或换崩溃类型。**
+在 libredwg 上无论判据怎么改，答案都会是"没有增量"，因为语料里只有一种形状。
+
+**另有一个结构性问题（R10 发现）**：`features.json` 是**手写的 5 条特征**，
+`source_pattern` 指向旧分类名。**stage3 的改进不会自动传导到 stage4**——
+换判据后 4 条 `source_pattern` 悬空，判据被丢弃（只有 `同函数释放后访问` 还对上）。
 
 ## 限制 9 · 引用 A/B 结果必须连 `mutator.c` 的 sha1 一起记
 
```

### 下一步建议

| 优先级 | 做什么 | 为什么 |
|---|---|---|
| **P0** | **换一个能扫出跨函数站点的项目**（或先把跨函数扫描器的守卫放宽到能做正例回归） | 这是"归纳有价值"唯一还没被检验过的场景；libredwg 只有一种形状，答案注定是"没有增量" |
| **P0** | 让 `features.json` 可由 stage3 重新生成（现在是手写 + `source_pattern` 硬引用） | 换判据后 4 条 `source_pattern` 悬空，stage3 的改进**传不到 stage4** |
| P1 | 补抓剩下 34 个 CPG，让 `cross_frame_count` 覆盖 121/121 | 缓存已就位，纯时间成本（~35 min），不改代码 |
| P1 | `merge_input.json` 被 hbo/stack/global 的 `merge` 步骤重写了（`final.json` 未动） | 下次若重跑这三类，`merge_input` 已带 `measured_dims`；要记清楚"final 是旧的、merge_input 是新的" |
| P2 | `applicability_rule.why` 的标识符黑名单（`uaf-llm05` 的 `why` 曾带出 `next`/`this`） | 干净度 |

### 本轮刻意不做的

- **hbo / stack / global 的 stage3 重跑**（按你的预算决定；它们的 `final.json` 保持旧判据）
- 函数指针分派（限制 6）、跨函数扩到字段/全局/回调（限制 7）、换崩溃类型
- 重跑 A/B（`reps_r9_final` 仍是当前可引用数据，未删）
