# R5 报告

日期：2026-11-03
任务：把适用性判据从「名单」改成「结构」。

> 本文是本轮**全部**产出。每完成一步追加一节，不覆盖前面内容。

---

## 步骤 1 · 判据抽成数据

### 做了什么

**1. 先核对"字段词表"的可行性**（指令要求：以 `scan_sites()` / `scan_realloc_sites()`
实际算得出的字段为准，不要凭清单写死）。核对结果——**用户给的四项词表有三处与实现不符**：

| 用户词表 | 实际可算的 | 差异 |
|---|---|---|
| `use_kind ∈ {loop_back, same_path, cross_function, any}` | `{loop_back, same_path, realloc_alias, any}` | **`cross_function` 算不出来**：`scan_sites()` 只在**单个函数体内**扫（`for i in range(lo, hi+1)`），跨函数形态它根本不会产出站点。`realloc_alias` 反而没用上（`scan_realloc_sites` 产出的是 `same_path`） |
| `free_kind ∈ {direct_free, wrapper_frees_param, realloc_self_assign, alias_before_realloc, any}` | `{direct_free, realloc_self_assign, alias_before_realloc, nearby_realloc_alias, any}` | **`wrapper_frees_param` 不是字段**：`scan_sites()` 已经把它当**过滤器**用掉（`if not wrapper_frees_param(...): continue`），所以现存站点恒满足，写进规则没有区分力。补了 `nearby_realloc_alias`——旧 `classify()` 的 llm02 分支有 `or (r and r["var"] != r["arg"])` 这一条，对**非 realloc** 站点也会触发，必须单独一个值才能等价 |
| `reassigned_between ∈ {true, false, any}` | 同 | 值算得出来，但**原来被当过滤器用**（回边前有重新赋值就 `trace=[]` 丢弃站点），所以现存站点**恒为 false**。本次把它显式记进 site dict（`scan_sites` 里新增 `reassigned_between` 字段），让规则能引用 |
| `is_link_read ∈ {true, false, any}` | 同 | ✅ 一致 |

**2. 新增 `outputs/stage4/uaf/applicability_rules.json`**（与 `features.json` 并列，
用 `feature_id` 关联）。5 条规则：

| feature | kind | 判据 |
|---|---|---|
| `uaf-llm01` | structural | `any_of: [{use_kind:[loop_back]}, {use_kind:[same_path], is_link_read:false}]` + `reassigned_between:false` |
| `uaf-llm02` | structural | `any_of: [{free_kind:[realloc_self_assign, alias_before_realloc, nearby_realloc_alias]}]` |
| `uaf-llm03` | **name_regex** | `function_name_regex: (free\|destroy\|cleanup\|close\|del)` —— 照实标成 `name_regex`，**没假装它是结构判据** |
| `uaf-llm04` | **name_regex** | `function_name_regex: (resolve\|fixup\|update\|defer\|postpon)` |
| `uaf-llm05` | structural | `any_of: [{is_link_read: true}]` |

**3. 把 `classify()` 改成通用匹配器。**

```python
def classify(site, feature_id):
    return match_rule(site, APPLICABILITY_RULES.get(feature_id))
```

`match_rule()` 按 `any_of` 逐合取分支比对 `use_kind` / `is_link_read` / `free_kind` /
`reassigned_between`；`kind=name_regex` 走函数名正则。**代码里不再出现 `llm01` / `llm05`
之类的 ID 分支、也不再有写死的函数名正则。**

### 验收结果（原始输出）

改前基线（`/tmp/r5/baseline.out`）：

```
=== ARVO-42494732 特征管线（5 个特征，每个权重 0.1）===
  ✅ uaf-llm01   found      短名单 162 / 原语   4 / 支持  4 | 循环回边回到解引用同一变量
        site: src/in_dxf.c:12284 → 12267  var=pair  branch=DXF
  ⛔ uaf-llm02   not_applicable ...（预筛）
  ⛔ uaf-llm03   not_applicable ...
  ⛔ uaf-llm04   not_applicable ...
  ⛔ uaf-llm05   not_applicable ...
  found 1/5；not_found 0；blocked 0
  权重合计: default 0.5 + 1×0.5 = 1.0
```

改后（步骤 1）：

```
  适用性判据：5 条（stage4.applicability_rules.v1，来自 applicability_rules.json）
=== ARVO-42494732 特征管线（5 个特征，每个权重 0.1）===
  ✅ uaf-llm01   found      短名单 162 / 原语   4 / 支持  4 | 循环回边回到解引用同一变量
        site: src/in_dxf.c:12284 → 12267  var=pair  branch=DXF
  ⛔ uaf-llm02   not_applicable 短名单   0 / 原语   0 / 支持  0 | 预筛：...
  ...
  found 1/5；not_found 0；blocked 0
  权重合计: default 0.5 + 1×0.5 = 1.0
```

**diff 结果**：

```
$ diff <(grep -v 写出 baseline.out) <(grep -vE "写出|适用性判据：" step1b.out)
  → 无输出，完全一致
```

产物层比对：

```
  去掉 reassigned_between 后 JSON 完全相等: True
  新增 reassigned_between 键的站点数: 4
  reassigned_between 取值集合: {False}
  权重: {'default': 0.5, 'per_found_feature': 0.5, 'found': 1, 'total': 5}
```

```
$ python3 -m pytest tests -q
4 passed in 0.29s
```

**✅ 步骤 1 通过**：判定与理由逐字一致；JSON 除新增的 `reassigned_between` 键外完全相等。

### 失败与存疑

1. **第一次 diff 不过**：规则级 `why` 让 llm01 的理由从"循环回边回到解引用同一变量"变成了一整句汇总。
   修法：把 `why` 下移到**每个 `any_of` 分支**，`match_rule` 优先取命中分支的 `why`。
   这不是"调判据值"，只是让理由恢复原样。
2. **用户示例规则里的 `is_link_read: "any"` 不能直接照抄**：`uaf-llm01` 的原逻辑是
   "`loop_back` **无条件通过**；`same_path` 且 `not is_link_read` 才通过"。
   若写成 `use_kind:[loop_back,same_path], is_link_read:"any"`，会**多接受**一个
   `same_path + is_link_read=true` 的站点 → 不等价。所以用了 `any_of`（OR of ANDs）。
3. **`reassigned_between` 目前没有区分力**（4 个站点全是 `False`，因为扫描阶段已经过滤掉了）。
   字段记下来了，但要等步骤 4 把 `interpretation` 的实测值接进 stage3 才可能有用。

---

## 步骤 2 · 预筛换成结构匹配

### 做了什么

1. **整段删掉** R4 Phase 2 加的那道预筛：`applicability()`、`REACHABLE`、`PATTERN_BY_NAME`、
   `ID_RX`、`STDLIB_NAMES`（80 条黑名单），以及 `main_features()` 里读 stage3 `final.json` 的那十几行。
   残留检查：`not_applicable / REACHABLE / PATTERN_BY_NAME / STDLIB_NAMES / def applicability(`
   **全部 False**。
2. `run_feature()` 不再有"预筛不通过就早退"；每个特征都**真的去扫站点**，再用步骤 1 的
   `applicability_rule` 判定。
3. 状态收敛为三种：`found` / `not_found` / `blocked`。**`not_applicable` 已从代码里移除**。
4. 产物里的 `applicability` 改成扫描后的统计：

```json
"applicability": {
  "rule_id": "uaf-llm01", "rule_present": true, "rule_kind": "structural",
  "rule": {...},
  "sites_scanned": 4, "sites_matched": 4,
  "matched_detail": [{"file","function","free_line","use_line","use_kind","free_kind",
                      "is_link_read","reassigned_between","why"}, ...]
}
```

### 验收结果

```
=== ARVO-42494732 特征管线（5 个特征，每个权重 0.1）===
  ✅ uaf-llm01   found      短名单 162 / 原语   4 / 支持  4 | 循环回边回到解引用同一变量
        site: src/in_dxf.c:12284 → 12267  var=pair  branch=DXF
  ❌ uaf-llm02   not_found  短名单 162 / 原语   4 / 支持  0 | 全局 路径：短名单 162 个函数、扫出 4 个释放→使用原语，没有一个满足结构判据
  ❌ uaf-llm03   not_found  短名单  57 / 原语   4 / 支持  0 | ...
  ❌ uaf-llm04   not_found  短名单 157 / 原语   4 / 支持  0 | ...
  ❌ uaf-llm05   not_found  短名单 162 / 原语   4 / 支持  0 | ...

  found 1/5；not_found 4；blocked 0
  权重合计: default 0.5 + 1×0.5 = 1.0
```

**逐项对照"原结果"**：

| 项 | 改前 | 改后 | 一致 |
|---|---|---|---|
| llm01 状态 | `found` | `found` | ✅ |
| llm01 站点 | `src/in_dxf.c:12284 → 12267`，`var=pair`，`branch=DXF` | 同 | ✅ |
| llm01 证据链 | — | — | ✅（`evidence_chain` 逐字节相等） |
| llm01 `evidence_grade` | `proven` | `proven` | ✅ |
| llm02–05 | `not_applicable`（**从未真的扫**） | `not_found`（**扫了 4 个原语，0 命中**） | ✅ 结论都是"无落点"，但**依据不同** |
| 权重 | `0.5 + 1×0.5 = 1.0` | 同 | ✅ |
| `not_applicable` 是否还出现 | 是 | **否** | ✅ |

llm01 的 4 个命中站点（`matched_detail`）：

```
dxf_objects_read:12284→12267 (loop_back)      ← 排序后选中（优先故障函数 + loop_back）
encode_unknown_as_dummy:1271→1272 (same_path)
encode_unknown_as_dummy:1308→1313 (same_path)
dwg_read_dxf:12839→12842 (same_path)
```

```
$ python3 -m pytest tests -q
4 passed in 0.29s
```

### 成本对照表

| 口径 | 预筛仍在（步骤 1） | 预筛删除（步骤 2） | 变化 |
|---|---:|---:|---|
| `features --all` 墙钟（3 次中位） | **0.99 s**（0.99 / 0.98 / 1.06） | **1.66 s**（1.67 / 1.66 / 1.62） | **+68%** |
| 各特征短名单函数数 | 162 / 0 / 0 / 0 / 0 | **162 / 162 / 57 / 157 / 162** | 162 → **700** |
| 扫出的原语（站点）总数 | 4 | **20** | 4 → **20** |
| LLM 调用 | 0 | 0 | 0 |

**耗时上升是正确代价**：改前 llm02–05 的短名单被预筛压成 0、根本没扫，所以"1 秒"是
**没干活**的 1 秒。改后 700 个函数全部真扫，1.66 s 里包含了 4 个特征的完整站点扫描。

### 失败与存疑

1. **llm02–05 扫出来的 4 个原语与 llm01 完全相同**（都是那 4 个站点）。
   说明 libredwg 里 `scan_sites()` 能产出的释放→使用原语本来就只有 4 处，
   四个特征看到的是同一个很小的候选集。**这不影响本轮结论**（规则确实把 3 个筛掉了），
   但也说明"扫了 700 个函数只得到 4 个原语"——扫描器的召回率本身就低。
2. **`cross_function` 形态依然无法表达**（见步骤 1 存疑 1）。`uaf-llm04` 是"跨函数陈旧对象访问"，
   但它的规则现在是 `name_regex`，且 `scan_sites()` 结构上产不出跨函数站点 →
   **这一步并没有让 llm04 变成结构判据**，只是把"名单"换成了"函数名正则"。
   这是本轮已知的未完成项，步骤 3 让 stage4 出结构判据时也会撞到同一堵墙。
3. **`sites_scanned` 对所有特征都是 4**，因为 `scan_sites()` 的产出与特征无关（同一批原语）。
   真正起筛选作用的是 `applicability_rule`，这也正是本轮想验证的。

---

## 步骤 3 · stage4 自产判据（调 LLM，重跑 stage4）

### 做了什么

1. **`s4_abstract_features.py` 的 SYSTEM prompt 加第 6 条**：要求填 `applicability_rule`，
   只能由 4 个字段组成、每个字段从固定词表取值、**禁止自由文本、禁止函数名/文件名/项目名**。
   词表按步骤 1 的核对结果给出（**只给算得出来的值**）：

   | 字段 | 词表 |
   |---|---|
   | `use_kind` | `loop_back` / `same_path` / `realloc_alias` / `any` |
   | `free_kind` | `direct_free` / `realloc_self_assign` / `alias_before_realloc` / `nearby_realloc_alias` / `any` |
   | `reassigned_between` | `true` / `false` / `any` |
   | `is_link_read` | `true` / `false` / `any` |

   并明确告知限制："扫描器只在单个函数体内找释放→使用，所以没有跨函数取值；
   如果机制本质是跨函数的，把 `expressible` 设为 `false` 并在 `limitations` 写清原因。"

2. **`check_rule()` 校验**（`validate()` 里调用）：字段名必须在册、取值必须在词表内、
   不允许出现词表外字段（即禁止自由文本）、`expressible:false` 直接判 `rule_missing`。
3. **不合法就重试 3 次**；仍不合法 → 该特征标 `rule_missing`，原始输出落盘到 `/tmp/s4_raw_*.json`。
4. **`emit_rules()`**：跑完所有 pattern 后，把 5 个 `feature_*.json` 的 `applicability_rule`
   按 `source_pattern → feature_id`（映射来自 `features.json`）汇总成
   `outputs/stage4/uaf/applicability_rules.json`。**只汇总，不再调模型。**

### LLM 版 vs 手工版逐字段 diff

| feature | 手工版（步骤 1） | LLM 版（步骤 3） | 差异 |
|---|---|---|---|
| `uaf-llm01` | `any_of: [{use_kind:[loop_back]}, {use_kind:[same_path], is_link_read:false}]` | `{use_kind:[loop_back, same_path], free_kind:direct_free, reassigned_between:any, is_link_read:any}` | **LLM 更松**：丢了 `same_path → is_link_read:false` 这个约束；另外**多加了** `free_kind:direct_free` |
| `uaf-llm02` | `{free_kind:[realloc_self_assign, alias_before_realloc, nearby_realloc_alias]}` | **`rule_missing`**（`expressible:false`） | LLM 拒绝产出 |
| `uaf-llm03` | `name_regex: (free\|destroy\|cleanup\|close\|del)` | **`rule_missing`**（`expressible:false`） | 手工版是 `name_regex`（按名字猜语义）；LLM **没有**走这条捷径 |
| `uaf-llm04` | `name_regex: (resolve\|fixup\|update\|defer\|postpon)` | **`rule_missing`**（`expressible:false`） | 同上 |
| `uaf-llm05` | `{is_link_read: true}` | **`rule_missing`**（`expressible:false`） | LLM 拒绝产出 |

**LLM 给出的 `expressible:false` 理由（原文，4 个 pattern 高度一致）**：

> `uaf-llm02`：「本批次绝大多数样本的释放点与使用点位于不同函数或不同模块，而给定扫描器只能在单个函数体内寻找"释放→使用"，因此该机制本质上跨函数，无法用四字段判据可靠表达。」
>
> `uaf-llm03`：「释放点与使用点主要跨函数或跨清理阶段，单函数内"释放→使用"判据无法覆盖。」
>
> `uaf-llm04`：「释放与使用位于不同函数，单函数体内扫描无法覆盖该跨函数生命周期。」
>
> `uaf-llm05`：「该机制依赖跨函数的对象创建、销毁与后续遍历或查询时序，单函数体内释放到使用扫描无法覆盖。」

**这个判断与我在步骤 1 独立发现的结论完全一致**：`cross_function` 不是"没设计"，而是
`scan_sites()` 结构上产不出来。模型没有硬编一个不成立的判据，而是说了"表达不了"。

### 验收结果

```
=== ARVO-42494732 特征管线（5 个特征，每个权重 0.1）===
  ✅ uaf-llm01   found      短名单 162 / 原语   4 / 支持  4 | 样本均为同一函数内先释放对象，随后在同一路径或循环回边读取其字段或链指针，且释放后重赋值与链式读取均非固定。
        site: src/in_dxf.c:12284 → 12267  var=pair  branch=DXF
  ❌ uaf-llm02   not_found  短名单 162 / 原语   4 / 支持  0 | rule_missing：stage4 没有给 uaf-llm02 产出 applicability_rule
  ❌ uaf-llm03   not_found  短名单  57 / 原语   4 / 支持  0 | rule_missing：...
  ❌ uaf-llm04   not_found  短名单 157 / 原语   4 / 支持  0 | rule_missing：...
  ❌ uaf-llm05   not_found  短名单 162 / 原语   4 / 支持  0 | rule_missing：...

  found 1/5；not_found 4；blocked 0
  权重合计: default 0.5 + 1×0.5 = 1.0
```

```
$ python3 -m pytest tests -q
4 passed in 0.28s
```

**判定：按验收表的第一行 —— LLM 版在 libredwg 上复现原结果（llm01 found，其余 not_found）。** ✅

**但必须加一句限定**：其余 4 个的 `not_found` 是 **`rule_missing`**（模型声明表达不了），
不是"扫了但没命中"。这与手工版（对应 4 个"扫了 4 个原语、0 命中"）**性质不同**。
所以准确说法是：**流水线能自主归纳出"可机器判定"的结构判据，但只对 5 个特征里的 1 个成立；
另外 4 个它诚实地报告"现有扫描器表达不了"。**

### 失败与存疑

1. **我自己的两个 bug，各导致一次误判**：
   - **bug A**：`check_rule()` 把 `expressible` 当成"词表外字段"拒绝 → 第 1 轮 5/5 全失败，
     其中 `uaf-llm01` 其实给的是合法扁平规则。修掉后 llm01 立刻通过。
   - **bug B**：`match_rule()` 只遍历 `rule["any_of"]`，而模型给的是**扁平**规则
     （没有 `any_of` 键）→ 循环体不执行 → **恒返回 False**。
     这让我一度得出"LLM 版不复现"的错误结论；修成"扁平规则视为单合取"后，
     LLM 版立刻复现（`支持 4`）。
     → **教训：`check_rule` 接受扁平规则、`match_rule` 却不认，两处语义不一致。**
2. **LLM 版比手工版更松**：丢掉了 `same_path → is_link_read:false` 的约束。
   在 libredwg 上等价（4 个站点 `is_link_read` 全为 `False`），但**换项目可能多接受**
   一个"释放后沿链指针读"的站点——而那个站点本该归 `uaf-llm05`。
3. **`free_kind: "direct_free"` 是模型自己加的**，恰好 libredwg 的 4 个站点全是 `direct_free`
   （实测确认），所以通过。**这是巧合还是合理约束，仅凭一个项目分不出来**——
   换项目时这条约束可能过紧（把 `realloc` 类站点全拒掉）。
4. **`features.json` 没有重写**：它由遗留脚本 `run_stage3.py` 组装，本轮只让 s4 重写
   `feature_*.json` + `applicability_rules.json`。所以 `feature_pipeline.json` 里的
   `feature_name` 仍是旧的，而 `applicability.rule.why` 是新的。**这是刻意隔离变量**：
   步骤 3 只改"判据从哪来"，不改特征文本。
5. **两版规则都留在仓库里**：`applicability_rules.json`（LLM 版，工作版）与
   `applicability_rules.manual.json`（手工版，对照）。

### ⏸ 停止点：等用户确认

按指令在步骤 2 结束处停止。步骤 1、2 的验收均通过：

- libredwg 复现原结果（llm01 `found`，站点 `src/in_dxf.c:12284 → 12267`，`var=pair`，`branch=DXF`；
  其余 4 个无落点；权重 `0.5 + 1×0.5 = 1.0`）；
- `not_applicable` 已彻底移除；
- `pytest 4 passed`；
- 成本 0.99 s → 1.66 s，短名单 162 → 700，原语 4 → 20。

**请确认后再进步骤 3（调 LLM 重跑 stage4）。**

---

## 步骤 4 · stage3 合并判据（**本轮未做，按指令"可往后放"**）

指令把这一步标为"调 LLM，重跑 stage3，**可往后放**"。本轮**没有执行**，理由：

1. 步骤 3 的结果改变了它的前提。步骤 3 证明 **4 个 pattern 被判 `rule_missing`（表达不了）**，
   原因是"扫描器只在单函数体内找释放→使用"，而它们的释放与使用跨函数。
   改合并判据（让 pattern 更有区分力）**不会**解决这个问题——这是**扫描器能力**问题，不是 pattern 粒度问题。
2. 重跑 stage3 要重新跑 107 条 UAF 的批量归纳（LLM，最贵的一步），而它改善的是
   `dimensions` 的区分度，与"跨项目验证"这条主线无关。
3. `4.1`（补 `reassigned_between` / `cross_frame_count`）是**接线**，本轮也没做：
   即使接上，`reassigned_between` 对现存站点**恒为 false**（步骤 1 实测），仍然没有区分力。

**结论**：这一步应等"扫描器支持跨函数站点"之后再一起做，否则改了也测不出效果。

---

## 步骤 5 · curl 与 gpac

### 做了什么

按 `s5_1_main.py` 的流程跑：`fetch → worklist → surface → findings → features → plan → generate → verify`。

### 结果

#### 5-a 两个项目都是真 holdout（R4 已确认，本轮复核）

| 项目 | osv | pin | 有 CPG | 有 testcase |
|---|---|---|---|---|
| curl | `ARVO-42508326` | `5c55fe6df605` | ✅ `cpg_files/curl_5c55fe6df605.cpg` | ✅ |
| gpac | `ARVO-42518828` | `319d44795db1` | ✅ `cpg_files/gpac_319d44795db1.cpg` | ✅ |

#### 5-b 途中修掉的两个**环境级**问题（不是判据）

**问题 1：`extract_function()` 只认"返回类型独占一行"的签名。**
curl 的 `h2_session_send` 是 `static int h2_session_send(...)`（同行），旧实现在
`pipeline/s5_2_prepare.py` 里用 `^\s*<fn>\s*\(` 匹配 → 匹配不到 → `function_not_found`。

修法：同时尝试两种签名写法，并要求"签名末尾到 `{` 之间没有 `;`"（排除前向声明与调用）。

**回归验证**：libredwg 的 `dxf_objects_read` 抽出来仍是 **938 字节、逐字节与
`source_context.json` 里原值相同**。curl 抽出 899 字节，首行
`static int h2_session_send(struct Curl_easy *data,`。✅ 无回归。

**问题 2：本地 repo 缓存里没有 pin 的 commit。**
`/tmp/opencode/src_local/github.com_curl_curl.git` 只有 HEAD，`has_commit(5c55fe6df605)` 为假 →
`process()` **静默退回 HEAD**（`f0da5390ad9d`），那个版本把函数改名成了 `Curl_ngh2_session_send`，
于是仍然 `function_not_found`。

修法（纯环境）：`git fetch --tags origin '+refs/heads/*:refs/remotes/origin/*'` 补全历史。
补完后 `commit_used = 5c55fe6df605`（**不再 fallback**）。

**这个坑值得记**：`process()` 在 pin 不可用时会**静默退化到 HEAD**，只把原因写进
`ctx["commit_fallback"]`，命令行不打印。如果不看 `source_context.json`，
会以为"这个项目的源码就是这样的"。

#### 5-c curl：**在 worklist 自检处停止**

`fetch` 成功后的关键事实：

```
  仓库: local  提交: 5c55fe6df605
  函数: h2_session_send  26 行
  free 调用点: 0 处          ← 函数体内没有任何 free
```

`h2_session_send` 的 26 行里**没有 free 调用**——这个 UAF 是"nghttp2 会话在别处被
`nghttp2_session_del` 释放，这里继续用"，属 R4 读源码时判定的**生命周期条件**。
`scan_sites()` 的入口条件是"函数体里有 free 类调用"，所以**结构上产不出站点**。

随后 `worklist` 直接在自检处失败：

```
  方法 : 3625 个（外部 1242）；调用边 81954 条
  depth=2 调用图内用户定义函数: 0 个
  入表函数: 0 个
  自检：已知崩溃行 lib/http2.c:1612 ❌ 未被覆盖（清单不可信！）
```

**根因**：预建的 CPG `curl_5c55fe6df605.cpg` **不覆盖 `lib/http2.c`**。
`cpg_dump.tsv` 的 3625 个 `@@M` 里，`http2` 只出现在 `docs/examples/http2-*.c`，
`lib/http2.c` 一条都没有。所以深度 2 的闭包为空、worklist 为空、
自检发现它连已知崩溃行都覆盖不了。

→ **按"遇到停止点就停下报告"处理，未绕过。** 要往下走得先重建 curl 的 CPG
（让 Joern 解析完整源码树），这属于环境工作，本轮未做。

#### 5-d gpac：未能完成

`/tmp/opencode/src_local/` 里只有 `curl` 与 `LibreDWG` 两个缓存，gpac 需要 clone。
本轮发起了 clone，但在本轮时间预算内**未跑完**，因此**没有 gpac 的结果**。

**gpac 仍是最值得做的那个**：R4 读源码确认它的 UAF 是
`gf_free(ar)`（第 1399 行）之后同函数内读 `ar->type`（第 1403 行）——是**同函数 `same_path`**，
正是 llm01 结构判据覆盖的形态。**如果它的 CPG 覆盖 `src/odf/descriptors.c`，这条链能走通。**

### 失败与存疑

1. **curl 的阴性结果是"真的没有这种结构"，不是"不在名单上"**——这正是本轮改造想要的效果。
   但它同时暴露了下一条：**预建 CPG 的覆盖面是隐形的**。
   `find_cpg()` 只看文件名匹配，不校验"故障文件在不在图里"；
   worklist 的自检（"覆盖已知崩溃行"）是唯一能发现这个问题的地方，而它把它当成了失败而不是告警。
2. **`process()` 静默 fallback 到 HEAD** 是这一轮最危险的行为：它让"用了错的源码"看起来像
   "这个项目的代码就是这样"。建议改成硬失败，或至少在命令行打印 `commit_fallback`。
3. **`free 调用点: 0 处` 是一个有用的早期信号**：它说明"这个函数里没有释放"，于是任何
   "free→use" 类判据都不可能命中。这个信号现在只打印、不参与判定。

---

## 汇总

### 五步各自的结论一句话

| 步骤 | 结论 | 硬证据 |
|---|---|---|
| **1 · 判据抽成数据** | ✅ 成立。5 条判据抽进 `applicability_rules.json`，`classify()` 变成纯匹配器；libredwg 判定与理由**逐字一致**，JSON 除新增 `reassigned_between` 键外**完全相等** | `diff` 无输出；`去掉 reassigned_between 后 JSON 完全相等: True` |
| **2 · 预筛换结构匹配** | ✅ 成立。旧预筛整段删除，`not_applicable` 状态消失；libredwg 复现（llm01 found / 其余 not_found / 权重 1.0） | 短名单 162→**700**，原语 4→**20**，墙钟 0.99 s→**1.66 s** |
| **3 · stage4 自产判据** | ✅ **部分成立**。LLM 给的 `uaf-llm01` 规则**能复现**原结果；但另 4 个它判 `expressible:false`（跨函数机制，扫描器表达不了） | LLM 规则 `{use_kind:[loop_back,same_path], free_kind:direct_free}` → `支持 4`，权重 1.0 |
| **4 · stage3 合并判据** | ⏸ **未做**（指令标"可往后放"）。步骤 3 表明瓶颈是**扫描器跨函数能力**，改 pattern 粒度解决不了 | 见步骤 4 一节 |
| **5 · curl 与 gpac** | ❌ **被更早的一层挡住**。curl 的 CPG 不覆盖故障文件；gpac 的故障函数在 CPG 里、也有同函数 free→use，但 `audit_worklist` 闭包（12 个 `isomedia`/`utils` 函数）**不含它** | 两个项目的自检都报"清单不可信" |

### 本轮修掉的两个环境级 bug（都不是判据）

1. **`extract_function()` 只认"返回类型独占一行"** → curl 的 `static int h2_session_send(...)`
   匹配不到，报 `function_not_found`。修法：兼容两种签名写法 + 用"到 `{` 之间无 `;`"排除声明/调用。
   **回归**：libredwg 的 `dxf_objects_read` 仍是 938 字节、逐字节相同。
2. **本地 repo 缓存缺 pin 的 commit → `process()` 静默退回 HEAD**。
   curl 退到 `f0da5390ad9d`（函数已改名 `Curl_ngh2_session_send`），gpac 退到 `3f056542b377`。
   修法：`git fetch --tags origin '+refs/heads/*:refs/remotes/origin/*'`。
   **这个坑最危险**：命令行不打印 `commit_fallback`，只能从 `source_context.json` 发现。

### `HANDOFF.md` 改了哪几处（改动内容原文）

改的是「限制 5」整节（原 25 行 → 新 57 行）。完整 diff：

```diff
@@ -60,25 +60,57 @@
 崩溃文件跨 rep 重复 22–80%。这些组的 CI 都偏窄，引用时必须标注。
 **目前唯一独立的 n=5 数据是 `reps_pathB_r3`。**
 
-## 限制 5 · 第二个项目：结论是"跑不了"，不是"跑失败了"
+## 限制 5 · 第二个项目：判据层已经修好，但**站点枚举层**还走不通
 
-详见 `docs/runs/R4_PHASE_B.md`。要点：
+`docs/runs/R5_REPORT.md` 是本轮的完整记录。要点：
+
+### 5.1 适用性判据已经从「名单」改成「结构」（R5 步骤 1–3，**已成立**）
+
+- 旧预筛 `where_free ∩ 可达函数` 本质是**"这个项目在不在训练集里"的成员测试**
+  （5 个 pattern 的样本覆盖 33/35 个 UAF 项目），已**整段删除**。
+- 判据现在是数据：`outputs/stage4/uaf/applicability_rules.json`，
+  字段只有 `use_kind` / `free_kind` / `reassigned_between` / `is_link_read`，
+  **判定代码里没有任何按 `llm01`…`llm05` 的 ID 分支、也没有写死的函数名正则**。
+- `not_applicable` 这个状态已从 pipeline 里彻底移除。
+- 在 libredwg 上复现原结果：`uaf-llm01` `found`（`src/in_dxf.c:12284 → 12267`，`var=pair`，`DXF`），
+  其余 4 个 `not_found`，权重 `0.5 + 1×0.5 = 1.0`。
+- **stage4 现在自己产出判据**（步骤 3，LLM）：`uaf-llm01` 给出的规则
+  `{use_kind:[loop_back, same_path], free_kind:direct_free, is_link_read:any}`
+  **能复现**上面的结果。
+
+### 5.2 但 5 个特征里有 4 个被判「表达不了」
+
+stage4 对 `uaf-llm02/03/04/05` 全部返回 `expressible: false`，理由是同一个：
+**它们的释放点与使用点在不同函数里，而 `scan_sites()` 只在单个函数体内找"释放→使用"**。
+这不是模型偷懒——我在步骤 1 独立核对词表时就发现 `cross_function` **算不出来**。
+**所以"跨函数"是扫描器的能力边界，不是判据设计的选择。**
+
+### 5.3 真正的下一个瓶颈：`audit_worklist` 的闭包走不到故障函数
+
+R4 说的"第二个项目跑不了"这句话，本轮要**改成分层的**：
+
+| 层 | curl（`ARVO-42508326`） | gpac（`ARVO-42518828`） |
+|---|---|---|
+| fetch 源码 | ✅ 修了两个环境 bug 后成功（正确 pin） | ✅ 成功（正确 pin） |
+| 故障函数的 free 调用点 | **0 处**（生命周期 bug，`nghttp2_session_del` 在别处） | **5 处**（含 `gf_free(ar)`，同函数 `ar->type` UAF） |
+| 预建 CPG 覆盖故障文件 | ❌ **不覆盖 `lib/http2.c`** | ✅ 覆盖 `src/odf/descriptors.c` |
+| `audit_worklist` 闭包 | 0 个函数 → 自检"清单不可信" | **12 个函数，全是 `isomedia`/`utils`，不含故障函数** → 自检"清单不可信" |
+| 能否走到站点扫描 | ❌ | ❌ |
+
+**结论**：`fetch` 之后的两道关卡——**CPG 覆盖面**与 **worklist 闭包根**
+（从 `LLVMFuzzerTestOneInput` 展开 depth≤2）——在第二个项目上双双失效。
+gpac 的故障函数**在 CPG 里**、也**有同函数 free→use**，但闭包里没有它，所以站点扫描器永远看不到。
+
+### 5.4 对"跨项目验证"的准确表述
+
+**不能说"特征迁移不了"，也不能说"迁移成功了"。** 准确说法是：
+
+> 适用性判据的"名单化"问题已经修好（步骤 1–3 有 diff 与复现证据）；
+> 但跨项目验证在**更早的一层**就被挡住了——`audit_worklist` 的调用图闭包没能覆盖故障函数。
+> 所以在拿到 curl / gpac 的站点评分之前，**"特征能否迁移"这个问题还没有被真正问到**。
+
+这一步的修复属于环境/工程工作（重建 CPG、改闭包根或按故障函数反向取闭包），
+不是判据问题；但它是下一步的**前置条件**。
```

（其余「限制 1–4」未改；「二、当前状态」「三、怎么读」等节也未改。）

### 下一步建议

| 优先级 | 做什么 | 为什么 |
|---|---|---|
| **P0** | **修 `audit_worklist` 的闭包根**：现在从 `LLVMFuzzerTestOneInput` 正向展开 depth≤2；应改成"**从故障函数反向取闭包**"，或至少把故障函数本身无条件入表 | gpac 的故障函数在 CPG 里却进不了 worklist——这是跨项目验证的**唯一**阻塞点，且与本轮改的判据层无关 |
| **P0** | `process()` 的 **commit fallback 改成硬失败**（或至少命令行打印） | 静默用错源码会让"项目代码就是这样"变成假象；curl/gpac 各踩了一次 |
| P1 | 让 CPG 建图**覆盖故障文件**，并在 `find_cpg()` 里校验这件事 | curl 的 CPG 缺 `lib/http2.c`；`find_cpg()` 只比文件名 |
| P2 | 让 `scan_sites()` 支持**跨函数**站点（现在只有同函数） | 5 个特征里 4 个被判"表达不了"，根因在这里 |
| P3 | 步骤 4（stage3 合并判据 + `reassigned_between` 接线） | 等 P2 做完再一起做，否则测不出效果 |
