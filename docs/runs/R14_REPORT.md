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
