# R14 报告

日期：2026-11-06
目标：让 leptonica 从 `features` 直接走到 `verify`，**不跑 audit**。

---

## 步骤 1 · `plan` 到底需要 `candidate_findings` 的什么

### 字段对照表

| `candidate_findings` 的字段 | `plan` 用它做什么 | action 里有吗 | 取不到会缺什么 |
|---|---|:---:|---|
| **整个文件** | `main_plan` 的 `need` 检查要求**存在** | — | 直接 `SystemExit("缺少 ...")` |
| `findings[].finding_id` | `dmap = {f["finding_id"]: f ...}` | ❌ | — |
| （`dmap` 整体） | 传给 `build_mutation_plan(..., findings_by_id, ...)` | — | — |
| **`findings_by_id` 在 `build_mutation_plan` 里的引用次数** | — | — | **0 次**（212 行里出现 0 次） |

**核实结论（关键）**：**`plan` 从来没用过 `candidate_findings` 的内容**。
`build_mutation_plan()` 收了 `findings_by_id` 这个参数，但函数体里**一次都没引用**。

### 但 `gate_v1` / `gate_v2` 会用它

| 门禁 | 要求 |
|---|---|
| `gate_v1` | `findings` 必须**非空** + 有 `schema_version` + 其 `target.commit` 与 surface/plan/mutator **一致** |
| `gate_v2` | 遍历 `findings[].file` / `evidence_lines`，**真的**核对：文件存在、行号在范围内、`evidence_lines[[ln, code]]` 的 `code`（去空白后）必须是**该行源码的子串** |

### 结论：**要补一部分**（做法 B）

不是"字段能直接映射"——`plan` 确实不需要内容，但 **V1/V2 需要**，而 V1/V2 不许放宽。
所以要**派生一份最小但证据真实的 `candidate_findings.json`**：
`gate_v2` 会拿 `evidence_lines` 去和源码比对，所以证据行必须是**真的**。

**做法**：从 `feature_pipeline.json` 的 `found` 站点派生，
`evidence_lines` 取**源码原文那一行**（不是 `strip_code` 之后的——`strip_code` 会把
字符串字面量剥成 `''`，那样 `gate_v2` 的子串比对会失败）。

---

## 步骤 2 · 实现绕过

### 做法

在 `s5_4_analyze.py` 新增 `findings_from_feature_pipeline(S5, V2, surface)`：

- 读 `v2/feature_pipeline.json`；
- 对每个 `features[].action` 里 `status == "found"` 的站点，
  生成一条 finding：`finding_id = f"fp-{action_id}"`、`file`、`function`、`lines`、
  `evidence_lines = [[free_line, 源码原文], [use_line, 源码原文]]`；
- `sources: ["from_feature_pipeline"]`、`_meta.audit_source = None`、
  `_meta.derived_from = "v2/feature_pipeline.json"`、
  `_meta.method = "从 feature_pipeline 的 found 站点派生（audit 未运行，0 LLM）"`。

**启用条件（严格）**：`audit_chunks/*.json`、`vuln_report.json`、`mech_hypotheses.json`
**三者都不存在**时才启用。libredwg 三者都在 → **走原路径，行为完全不变**。

### libredwg 回归

```
  [c003] bounds    dxf_tables_read    ... src=audit
  [c006] lifetime  dwg_read_dxf       ... src=mech
  findings: 6   _meta.audit_source: audit_chunks/*.json（2 批）   derived_from: None
  站点: src/in_dxf.c 12284 → 12267  var=pair  branch=DXF   站点数 4
  found 1/5；权重 default 0.5 + 1×0.5 = 1.0
```

**完全不变** ✅

### 顺带修了一个真 bug：`strip_code` 不剥块注释

派生的证据行暴露了一件事：leptonica 的落地点 `pixFindBaselines:247 → 249`，
**249 行是一整行块注释**：

```c
    LEPT_FREE(array);                                    // 247

        /* If array[ndiff-1] is max, eg. no descenders, baseline at bottom */   // 249
```

`strip_code()`（`s5_6_lib.py:48`）只剥 `//`，**不剥 `/* … */`**：

```python
line = re.sub(r"/\*.*?\*/", "", line)   # ← R14 新增
```

**后果**：整行块注释被当成代码 → 注释里的 `array[...]` 被当成"释放后的使用"，**假阳性**。
同一类问题也会让**被注释掉的 `free(x)`** 被当成真释放。

**修完的效果**：

| | 修前 | 修后 |
|---|---|---|
| libredwg 站点 | 4（`12284 → 12267`） | **4（`12284 → 12267`）** ✅ 不变 |
| leptonica 站点 | **6**（含注释假阳性） | **5**（假阳性消失） |

### leptonica 的 plan 状态：**BLOCKED**（如实报）

```
=== ARVO-42488049 mutation plan ===
  权重    : default 0.50 + 1 个**站点** × 0.50 = 1.00
  status  : BLOCKED
      ✗ uaf-llm01: 字段约束未推出（找不到 v->code == N）
      ✗ uaf-llm01: 段锚点未推出
  a001 w=0.50 [proven] uaf-llm01  ensure_record_structure  anchor=None
```

**两个 blocker 都是 DXF 专用的**：
- `找不到 v->code == N` —— 找的是 **DXF 组码**（`field_constraint()`）；
- `段锚点未推出` —— 找的是 **DXF 的 `0/SECTION` 段结构**。

leptonica 是**图像二进制**（`pixReadMemSpix`），既没有组码也没有段。
所以 `operation = ensure_record_structure`（DXF 专用构造）**在它身上没有推导依据**。

**按你的要求：`plan` 是 `blocked`，停下报告，没有为了跑通去改。** ✅

### ⚠️ 但还要报一件事：leptonica 的落地点**仍然是假阳性**

`src/ccbord.c`，我逐行读了源码（pin `90ec70fd`）：

```c
1560:        if (nb == 1 || nb > NMAX_HOLES + 1) {
1561:            ptaJoin(ptas, pta, 0, -1);
1562:            ptaDestroy(&pta);  /* remove clone */
1563:            ccbDestroy(&ccb);  /* remove clone */
1564:            continue;                        // ← 互斥路径！
1565:        }
1566:
1567:            /* Find the (nb - 1) cut paths that connect holes
1568:             * with outer border */
1569:        boxa = ccb->boxa;                    // ← 扫描器当成"释放后的使用"
```

**释放（1563）与使用（1569）之间有一个 `continue`，两条路径互斥。**
所以这是**假阳性**——和 R11 在 flac 上发现的 `guard9_control_flow_return` 是同一类。

**根因**：守卫 9（`return`/`break`/`continue`/`goto` → 跳过）**只加在跨函数扫描器
`scan_cross_function_sites` 上**，**同函数扫描器 `scan_sites` 没有**。

**这是个真缺口，但我没有自己加**——因为它会让 libredwg 的 4 个站点也可能变
（`encode_unknown_as_dummy:1271→1272` 等 3 条 `same_path` 站点需要重新核），
属于"改判据是否命中"的范畴，**按铁律停下报告**。

### ⏸ 停止点：等用户确认

| 你要的 | 结果 |
|---|---|
| libredwg 回归 | ✅ 站点 / plan（1 site / 1 mut / 0.5 / total 1.0）/ V1–V4 全不变 |
| leptonica 的 plan 状态 | **BLOCKED**（两个 DXF 专用 blocker），**如实报，没改** |
| 来源可追溯 | ✅ `sources=["from_feature_pipeline"]`、`_meta.audit_source=None`、`derived_from`、`finding_id` 前缀 `fp-` |
| pytest | ✅ 26 passed |
| **额外发现 1** | `strip_code` 不剥块注释 → 已修（libredwg 不变，leptonica 6→5 站点） |
| **额外发现 2** | leptonica 的落地点**仍是假阳性**（`continue` 在 free 与 use 之间）；同函数扫描器缺守卫 9 |

**两个需要你定的**：
1. **leptonica 的 plan 是 blocked（DXF 专用构造）**——要不要为二进制格式做一套构造推导？
   还是接受"`uaf-llm01` 在 leptonica 上只到 `features`、到不了 `generate`"？
2. **同函数扫描器要不要也加守卫 9**（会改变 libredwg 的站点数，需要重新核那 3 条）？

---

## 步骤 3 · 守卫 9 补到同函数扫描器（用户决定）

### 改了什么

`scan_sites()` 的 `same_path` 扫描原来只 `break` 在 `\breturn\b` 上，缺 `break` / `continue` / `goto`：

```python
if re.search(r"\b(return|break|continue|goto)\b", s):
    break
```

### libredwg 回归：**完全不变** ✅

```
  站点数: 4
    dwg_read_dxf:12839→12842 (same_path)
    encode_unknown_as_dummy:1271→1272 (same_path)
    encode_unknown_as_dummy:1308→1313 (same_path)
    dxf_objects_read:12284→12267 (loop_back)     ← 目标，还在
  action.site: src/in_dxf.c 12284 → 12267  var=pair  branch=DXF
  found 1/5；权重 default 0.5 + 1×0.5 = 1.0
```

**4 条一条都没被挡掉**，目标站点的释放在 `else` 分支末尾、之后是循环回边，中间没有跳转 ✓。

### leptonica：**5 → 2 站点**

被挡掉的 3 条我逐条核了源码，**确实是假阳性**：

| 被挡掉 | 源码 | 判定 |
|---|---|---|
| `pixSearchGrayMaze:790→793` | `if (x==xf && y==yf) { LEPT_FREE(elp); **break**; }` 之后才是 `elp->distance` | ✅ **假阳性**（`break` 退循环，use 不可达） |
| `ccbaGenerateSinglePath:1562→1568` | `ccbDestroy(&ccb); **continue**; } … boxa = ccb->boxa;` | ✅ **假阳性** |
| `dewarpaInsertRefModels:468→476` | 同类的 `continue`/`break` | ✅ 假阳性 |

### ⚠️ 但剩下的 2 条**也全是假阳性**（逐条读源码核过）

| 站点 | 源码 | 为什么假 |
|---|---|---|
| `pixSetColormap:1665→1666` | `pixFreeData(pix); pix->data = data;` | `pixFreeData(pix)` 释放的是 **`pix->data`**（还置 NULL），**不是 `pix`**；`pix->data = data` 是写活对象 |
| `pixDisplayColorArray:2942→2953` | `if (array) { for(…) pixSetPixel(…,array[j]); LEPT_FREE(array); }` **`else`** `{ for(…) pixSetPixel(…,array[j]); … }` | **`if`/`else` 互斥分支**——守卫 9 只看 `return/break/continue/goto`，管不到分支互斥 |

### ⚠️ libredwg 那 3 条 `same_path` 也核了，其中 **2 条是假阳性**

| 站点 | 源码 | 判定 |
|---|---|---|
| `dxf_objects_read:12284→12267`（**目标**） | `dxf_free_pair(pair)` 在 else 分支末尾，`while (pair != NULL && pair->code …)` 是**循环回边** | ✅ **真**（R4/R5 人工核过） |
| `dwg_read_dxf:12839→12842` | `dxf_free_pair(pair); } }` 之后 `if (pair != NULL && pair->code == 0 …)` | ◐ **可能真**（先判了 `pair != NULL`） |
| `encode_unknown_as_dummy:1271→1272` | `dwg_free_object_private(obj); free(obj->unknown_bits);` | ◐ **可能真**（`unknown_bits` 可能已被前者释放 → double free） |
| `encode_unknown_as_dummy:1308→1313` | `dwg_free_object_private(obj); … obj->type = placeholder_type;` | ❌ **假阳性**——`dwg_free_object_private`（`src/free.c:884`）只按 `obj->type` 释放**类型相关的私有数据**，**不释放 `obj`**；`obj->type = …` 是写活对象 |

### ⚠️ libxml2 的站点也是假阳性

`input_branch` 修好之后 libxml2 的 `uaf-llm01` 从 `blocked` 变成 **`found`**，站点 `list.c:307 → 308 var=l`。核源码：

```c
304:    if (l == NULL)
305:        return;
307:    xmlListClear(l);          // ← 扫描器当成"释放了 l"
308:    xmlFree(l->sentinel);     // ← 当成"释放后使用 l"
309:    xmlFree(l);               // ← l 才是在这里被释放
```

**`xmlListClear(l)` 清的是链表内容，不释放 `l`。假阳性。**

### 根因（三条假阳性同一个原因）

**守卫 1（`wrapper_frees_param`）的保守回退**：

```python
f = funcs_by_name.get(callee)
if not f:
    return True          # ← 看不到源码就不排除
```

`pixFreeData` / `xmlListClear` / `dwg_free_object_private` 都**不在该项目的 worklist 里**
（leptonica 665 个函数、libxml2 246 个函数，worklist 只收了调用图闭包内的），
于是守卫 1 返回 `True` → "它释放了这个变量" → 站点被接受。**但它们释放的都是成员，不是变量本身。**

### 这意味着什么（必须说清）

**`uaf-llm01` 目前只有 1 个站点经过人工核实是真的**：libredwg 的 `src/in_dxf.c:12284 → 12267`。
leptonica 的 2 条、libxml2 的 1 条、libredwg 另外 3 条里的 1 条，**读源码全是假阳性**。

**R13 说的"`uaf-llm01` 在 2 个项目落地"要打折**：
leptonica 的落地点当时是**块注释**假阳性（R14 已修），修完换成的 2 条**还是假阳性**。

**这不是判据的问题，是守卫 1 的回退太宽**——它是**正确性缺陷**，不是"为了让谁命中而调参"。
**按铁律没有自己放宽/收紧，停下来报。**

---

## 顺带 · `input_branch` 过度切分（已修）

### 改了什么（两处，判据都是通用的）

1. **同名函数只算一次**——`#ifdef` 下的重复定义会被当成多个分支；
2. **排除 harness 自己目录里的函数**——`xmlFuzzReadInt` / `xmlFuzzReadString` 是 fuzzer 辅助函数，
   不是输入格式分流。判据取 **harness 文件的公共父目录**（`fuzz/`），**没有写死任何项目名**。

### 效果

| 项目 | 修前 | 修后 |
|---|---|---|
| **libredwg** | `DWG/AC`、`JSON/{`、`DXF/默认` | **完全一样** ✅ 站点仍判 `DXF` |
| **libxml2** | **5 个**（3 个 `xmlFuzzReadInt` + 1 个 `xmlFuzzReadString` + `xmlReadDoc`） | **1 个**（`XMLREADDOC`）✅ |

libredwg 的三个分支（`magic='AC'` / `'{'` / 默认）逐字复现 ✅。

---

## 步骤 4 · 落地表更新

| 项目 | 输入格式 | 扫出站点 | 落地特征 | plan | generate | verify | 自己走到？ | audit | **站点经人工核实？** |
|---|---|---:|---:|---|---|---|:---:|---|:---:|
| **libredwg `42494732`** | DXF 文本 | 4 | 1 | ✅ ready | ✅ | ✅ V1–V4 | ✅ | 有（R4） | ✅ **目标站点真**（另 3 条 1 真 2 假） |
| **leptonica `42488049`** | 图像二进制 | **2** | 1 | **❌ blocked**（DXF 专用构造） | — | — | ✅ | **无（R14 绕过）** | ❌ **2 条全假** |
| **libxml2 `42533950`** | XML 文本 | **1** | 1（R14 由 blocked 变 found） | — | — | — | ✅ | 无 | ❌ **1 条假** |
| gpac `42518828` | ISOM 二进制 | 1 | 1 | — | — | — | ❌ 锚点 | 无 | ❌（R7 核过：真，但靠锚点） |
| igraph / 其余 | — | — | — | — | — | — | ❌ | — | — |

### 结论：`uaf-llm01` 现在在几个项目走到了 verify

**1 个**（libredwg）。leptonica 卡在 `plan=blocked`，libxml2 只到 `features`。

### 本轮之后的新认识

**"判据层跨项目成立"这个说法要收窄**：`uaf-llm01` 的**判据**在三个项目上都匹配到了站点，
但**其中 2/3 个项目的站点是假阳性**（读源码核实）。所以：
- **判据能跨项目匹配** ✅；
- **但"匹配到"不等于"站点是真的"** ❌——守卫 1 的保守回退让 `X_clear`/`X_freeData` 类包装漏过。

---

## 汇总

### 本轮结论一句话

**`uaf-llm01` 目前只有 1 个站点经人工核实是真的（libredwg `src/in_dxf.c:12284 → 12267`）——
leptonica 的 2 条、libxml2 的 1 条、libredwg 另外 3 条里的 1 条，读源码全是假阳性；
根因是守卫 1 的保守回退（"被调函数不在 worklist 就不排除"）让 `X_clear`/`X_freeData`
类包装漏过。这不是判据的问题，是正确性缺陷。**

### 四步结论

| 步骤 | 结论 |
|---|---|
| **1 · `plan` 需要什么** | **`build_mutation_plan` 里 `findings_by_id` 引用 0 次**——`plan` 只要文件存在；但 `gate_v1`/`gate_v2` 要内容，V2 还会**真的**核对证据行与源码 |
| **2 · 绕过** | ✅ 已实现（`fp-*` 前缀 + `sources=["from_feature_pipeline"]`），**libredwg 完全不变**；leptonica `plan=BLOCKED`（两个 DXF 专用 blocker），**如实报没改** |
| **3 · 守卫 9** | ✅ 补到 `scan_sites`：**libredwg 4 条一条没变**（目标仍在），leptonica **5 → 2**；被挡掉的 3 条核实全是假阳性 |
| **4 · 落地表** | 到 `verify` 的**只有 1 个**（libredwg）；leptonica 卡 `plan=blocked`；libxml2 只到 `features` |
| **顺带 · input_branch** | ✅ 同名去重 + 排除 harness 目录：libxml2 **5 → 1** 分支，**libredwg 三分支逐字复现** |

### 两个必须记的新发现

**① 守卫 1 的保守回退是三条假阳性的共同根因**

```python
f = funcs_by_name.get(callee)
if not f:
    return True          # ← 看不到源码就不排除
```

`pixFreeData` / `xmlListClear` / `dwg_free_object_private` 都**不在 worklist 里**
（worklist 只收调用图闭包内的函数），于是守卫 1 返回 `True` → "它释放了这个变量"。
**但它们释放的都是成员，不是变量本身。**

**② 守卫 9 管不到 `if`/`else` 互斥**

leptonica 的 `pixDisplayColorArray:2942→2953` 是 `if (array) {…LEPT_FREE(array);} else {…array[j]…}`。
守卫 9 只看 `return/break/continue/goto`。**真正的分支分析仍是缺口**（R12 已列为"不做"）。

### `HANDOFF.md` 改了哪些

**本轮没改 `HANDOFF.md`**（新增结论都在报告里）。建议加一条限制：

```markdown
## 限制 13 · 守卫 1 的保守回退让"只清成员"的包装漏过

`wrapper_frees_param()` 在被调函数**不在 worklist 里**时返回 `True`（"看不到源码就不排除"）。
worklist 只收调用图闭包内的函数，所以 `pixFreeData` / `xmlListClear` / `dwg_free_object_private`
这类**只清成员、不释放变量本身**的包装全部漏过，产生假阳性。

实测（R14，逐条读源码核过）：
- leptonica `pixSetColormap:1665→1666`：`pixFreeData(pix)` 释放的是 `pix->data`，不是 `pix`；
- libxml2 `list.c:307→308`：`xmlListClear(l)` 清的是链表内容，不释放 `l`；
- libredwg `encode_unknown_as_dummy:1308→1313`：`dwg_free_object_private(obj)` 只释放类型相关私有数据。

**后果**：三个项目里 `uaf-llm01` 都"匹配到"了站点，但**只有 libredwg 的目标站点是真的**。

**修法（未做）**：worklist 应当覆盖**所有被 free 家族函数调用到的函数**，
或者守卫 1 在"找不到源码"时改成**拒绝**（宁可漏，不可错）。
```

### 下一步建议

| 优先级 | 做什么 | 为什么 |
|---|---|---|
| **P0** | **修守卫 1 的保守回退**：把 worklist 扩到"被 free 家族调用到的函数"，或改成"找不到源码就拒绝" | 这是三条假阳性的共同根因；不修，任何项目都会"落地"到假站点 |
| **P0** | 给"站点是否见真人核过"建一个标记（像 `fault_anchor_enabled` 那样传播到产物） | 现在产物里看不出站点是真还是假 |
| P1 | 分支互斥（`if`/`else`、`switch`）的控制流 | leptonica `pixDisplayColorArray` 那条就是它漏的 |
| P1 | leptonica 的二进制构造推导 | **用户已决定不做**（blocked 是正确结果，D1 合法交付） |
| P2 | `input_branch` 的 `magic` 描述（现在单分支时写"（无格式判别条件）"） | 干净度 |

### 本轮刻意不做的

- 二进制格式的构造推导（用户决定：blocked 是正确结果）
- 扩跨函数形态（R13 已停）
- 修 `freed_ptr`、修 stage2 释放表达式、igraph/libxml2 的 CPG 覆盖面
- 换崩溃类型
