# R15 报告

日期：2026-11-06
本轮两件事：**修守卫 1**（先试最便宜的修法 A）、**给站点加"是否经人工核实"标记**。

> 范围界定（用户口径）：**主结果完好** —— `reps_r9_final` 的
> `default 0 / 1,102,847` vs `custom 617 / 640,359` 用的是 libredwg 那个经 R4/R5
> 两轮人工核实的真站点，而且 617 次命中**全部**是 `heap-use-after-free @ in_dxf.c:12267`。
> **受影响的只有 R13 那句**"`uaf-llm01` 在两个项目落地了"。

---

## 步骤 1 · 修守卫 1（修法 A：找不到源码就拒绝）

### 改了什么

`wrapper_frees_param()` 的三处回退从 `return True` 改成 `return False`，并加计数：

| 回退点 | 改前 | 改后 | 计数键 |
|---|---|---|---|
| `f = funcs_by_name.get(callee)` 为空 | `True` | **`False`** | `callee_not_in_worklist` |
| 有函数但 `src_cache` 里没源码 | `True` | **`False`** | `callee_source_unavailable` |
| 形参解析不出来 | `True` | **`False`** | `callee_param_unparsable` |

新增 `_WRAP_REJECT` 计数器——**"被拒了多少"是修法 A 的代价，必须能报出来**，不能静默。

### 验收 1：目标站点还在吗 —— **在** ✅

```
  found 1/5；权重 default 0.5 + 1×0.5 = 1.0
  站点数: 2
    dwg_read_dxf:12839→12842 (same_path)
    dxf_objects_read:12284→12267 (loop_back)      ← 目标，还在
  action.site: src/in_dxf.c 12284 → 12267  var=pair  branch=DXF
```

**修法 A 没有杀掉目标站点 → 不需要步骤 1b。** ✅

### 验收 2–4：三个项目的站点数变化

| 项目 | 修前站点数 | 修后站点数 | 被挡掉的是哪几条 | 与 R14 人工核实的对照 |
|---|---:|---:|---|---|
| **libredwg** | 4 | **2** | `encode_unknown_as_dummy:1271→1272`、`encode_unknown_as_dummy:1308→1313` | ✅ `1308` 是 R14 **确认的假阳性**（`dwg_free_object_private` 不释放 `obj`）；`1271` 是"可能真"（见下） |
| **leptonica** | 2 | **0** | `pixSetColormap:1665→1666`、`pixDisplayColorArray:2942→2953` | ✅ R14 核实**两条全假**（`pixFreeData` 只释放 `pix->data`；`if/else` 互斥） |
| **libxml2** | 1 | **0** | `list.c:307→308` | ✅ R14 核实**假**（`xmlListClear(l)` 清链表内容，不释放 `l`） |

**结论：修法 A 的挡掉结果与 R14 的人工核实完全一致**——该挡的全挡了，目标站点留住了。

**`leptonica` 和 `libxml2` 现在 `found 0/5`**（站点从 2/1 掉到 0）。
这是**修正后的正确结果**——它们之前的 `found 1/5` 依赖的是假阳性站点。

### 关于被挡掉的 `encode_unknown_as_dummy:1271→1272`

R14 标的是"◐ 可能真"（`dwg_free_object_private(obj)` 之后 `free(obj->unknown_bits)`）。
再看一眼 `src/free.c:884` 的 `dwg_free_object_private`：它按 `obj->type` 走 `switch`，
调 `dwg_free_<TYPE>_private(dat, dat, dat, obj)` —— **释放的是类型相关的私有数据**。
`unknown_bits` 是 `Dwg_Object` 的**公共字段**，不在这些 `_private` 函数的职责里。

**所以 `1271→1272` 也是假阳性**（`free(obj->unknown_bits)` 在 `dwg_free_object_private` 之后是正常的）。
→ **修法 A 挡掉它是对的。**

### 验收 5：修法 A 的代价（被拒计数）

| 项目 | `callee_not_in_worklist` | 其它 |
|---|---:|---:|
| libredwg | **8** | 0 |
| leptonica | **3** | 0 |
| libxml2 | **1** | 0 |

**共 12 次"因为被调函数不在 worklist 而拒绝"。** 这是修法 A 的代价：
这 12 个 free 调用所在的站点被整条丢掉了——其中**可能有真站点**，本轮无法区分。

**要不要做修法 B（把被 free 家族调用到的函数补进可查集合）？**
它们本来就在**项目源码**里，只是不在 worklist（worklist 只收调用图闭包内的函数）。
补进去的成本是"解析更多源码"，**不需要重跑 Joern**。**等确认。**

### ⚠️ 一个必须提的连带影响：libredwg 的 `plan` 现在会变

站点数 4 → 2 之后，如果重跑 `plan`，`by_site` 会得到 **2 个 mutation**（不是 1 个），
权重变成 `default 0.5 + 2 × 0.25 = 1.0`。

**本轮没有重跑 `plan` / `generate` / `verify`**（步骤 1 只要求报站点数，且铁律要求"不重跑 A/B"）。
所以现在 `projects/ARVO-42494732/v2/mutation_plan.json` 与 `feature_pipeline.json`
**是新旧不一致的**（plan 还是 1 site 那版）。

**这也是 `reps_r9_final` 能继续引用的原因**：A/B 用的是**旧算子**（1 site），
`mutator.c` sha1 仍是 `d7913b9e`。**一旦重跑 plan/generate，那个组合就不再成立。**

→ **要不要用它重跑 libredwg 的 plan/generate（从而得到 2 策略算子）？这是另一个决定，等确认。**

### ⏸ 停止点：等用户确认

| 你要的 | 结果 |
|---|---|
| 1. 目标站点 `12284 → 12267` 还在吗 | ✅ **在** |
| 2. libredwg 站点数 / 挡掉哪几条 | **4 → 2**；挡掉 `1271`、`1308`（`1308` 是 R14 确认假；`1271` 经复核也是假） |
| 3. leptonica 站点数 | **2 → 0** ✅（与 R14 核实一致） |
| 4. libxml2 站点数 | **1 → 0** ✅（与 R14 核实一致） |
| 5. 被拒计数 | `callee_not_in_worklist`：libredwg 8 / leptonica 3 / libxml2 1 |
| pytest | ✅ 26 passed |

**三个需要你定的**：
1. **要不要做修法 B**（把被 free 家族调用的函数补进可查源码集合，找回那 12 次拒绝里可能有的真站点）？
2. **要不要重跑 libredwg 的 plan/generate**（会变成 2 策略算子，但 `reps_r9_final` 的引用组合就失效了）？
3. 确认后进**步骤 2**（站点核实标记）。
