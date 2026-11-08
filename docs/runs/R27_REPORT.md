# R27 报告

日期：2026-11-08
用户决定：选 C —— **让 agent 连使用行的原文一起给，程序逐字核对**。

---

## 步骤 1 · schema 扩成 `use_code` / `expr` / `access`

`use_lines` 每项从「行号」扩成：

```json
{"line": 12267, "code": "while (pair != NULL && pair->code == 0 && pair->value.s) {",
 "access": "deref", "expr": "pair->code"}
```

`access` 五选一：`deref` / `addr_of` / `assign_only` / `call_arg` / `other`。
prompt 明确：「**如果那一行里找不到这块内存被读到，就不要报这一行。**」
仍然只要事实（抄原文、指出表达式、分类性质），**不判断**。`use_lines` 仍 ≤3。

---

## 步骤 2 · 程序五道核对

| 核对 | 挡掉条数（libredwg） |
|---|---:|
| ① `code` 和 pin 源码逐字一致（去空白） | 0（`code_mismatch`） |
| ② `expr` 在 `code` 里出现 | **35**（`expr_not_in_code`） |
| ③ `expr` 里有 object（或宿主，全词） | **6**（`expr_no_object`） |
| ④ `access` 是 `deref` | **38** `assign_only` + **7** `other` + **1** `addr_of` |
| ⑤ `access` 是 `call_arg` → 保留但低置信 | — |
| 释放行没有触发调用 | 2（`no_trigger_call`） |

**213 条原始 → 124 条通过（挡掉 89 条）。**

**第 ① 道一条都没挡** —— 说明 agent **抄原文是准的**（这是好事，R23 也测过它报事实准确率 99.3%）。

---

## 🔴 步骤 3 · 两个坏消息

### 坏消息一：**标尺 `12284→12267` 丢了**

```
  r1 12284→12287 verified=True (call_arg_lowconf)
  r2 12284→12287 verified=True (call_arg_lowconf)
```

**两个实例都只报 `12284→12287`（另一处 free），没有报 `12267`。**
R26b 版本（`use_lines` 只有行号）两个实例都报了 12267 —— **加了 `code`/`expr` 之后它不报了**。

**按铁律「任何改动让它掉下 high 就是改错了，停下查」—— 停下。**

### 坏消息二：**配对后候选塌了**

| 项目 | R26b | **R27** |
|---|---:|---:|
| libredwg | 39 | **5** |
| leptonica | 41 | **5** |
| libxml2 | 44 | **4** |
| igraph | 13 | **6** |

**塌了 7–11 倍。** 因为新 schema 让它**只报"确凿的"**，`no_loop_back` 从 74 降到 17 ——
它现在**几乎不报回边**了（而标尺恰恰是回边）。

---

## 抽样核实（20 条全读，已核 8 条）

| # | 项目 | 站点 | pin 源码事实 | 判定 |
|---|---|---|---|---|
| 1 | libredwg | `free.c:1313→1316` | 1313 `FREE_IF(dwg->object_ref[i])`（循环里逐个释放元素）；1316 `FREE_IF(dwg->object_ref)`（释放**数组**）—— **正常的析构顺序** | ❌ 假 |
| 2 | libredwg | `free.c:1322→1324` | 1322 `FREE_IF(dwg->object)`；1324 `hash_free(dwg->object_map)` —— **不同字段** | ❌ 假 |
| 3 | libredwg | `in_dxf.c:12284→12287` | 12284 和 12287 是**同一处 `dxf_free_pair(pair)` 的两次调用** —— **double free**，**是真的缺陷** | ✅ **真**（但类型是 double free，不是 UAF） |
| 4 | leptonica | `recogident.c:926→925` | 926 `LEPT_FREE(text)`；925 `pixSetText(pix1, text)` —— 在**前一行**；且 `text` 每轮由 924 `rchExtract(..., &text, ...)` 重新取 | ❌ 假（out-param） |
| 5 | libxml2 | `valid.c:1270→1282` | 1270 `xmlFree(ret)` 在 `if (ret->name == NULL)` 分支里，紧接着 1272 `goto mem_error` —— **1271 就跳走了** | ❌ 假 |
| 6 | libxml2 | `valid.c:1270→1295` | 同上 | ❌ 假 |
| 7 | libxml2 | `valid.c:1282→1295` | 1282 `xmlFreeElement(ret)` 后 1283 `goto mem_error` | ❌ 假 |
| 8 | igraph | `gml-tree.c:168→172/176/180` | 168 在 `case TREE`，172/176/180 在 `case INTEGER/REAL/STRING` —— **switch 分支互斥** | ❌ 假 |

**→ 已核 8 条：1 真（double free）、7 假 = 精确度 12.5%。**

### 挡不住的两类（如你所料，占比很高）

| 类型 | 例子 | 本次占比 |
|---|---|---|
| **out-param 重新分配** | `recogident.c:926→925`（`&text` 每轮重取） | 2/8 |
| **正常析构顺序** | `free.c:1313→1316`、`free.c:1322→1324` | 2/8 |
| **switch 分支互斥** | `gml-tree.c:168→172`（**新发现**：`if_else_exclusive` 只管 if/else，不管 switch） | 3/8 |
| goto 提前跳走 | `valid.c:1270→1282` | 3/8 |

---

## 判定：落在 **<20%** 这一档 → **收口**

| 你的判据 | 结果 |
|---|---|
| ≥50% → 这条路成立 | ✗ |
| 20–50% → 有改善但信噪比仍低 | ✗ |
| **<20% → 收口** | ✅ **12.5%** |

**而且这次比 R26b 更差**：

| | R26b | **R27** |
|---|---:|---:|
| 标尺 | ✅ high | ❌ 丢 |
| 候选数 | 39/41/44/13 | **5/5/4/6** |
| 抽样精确度 | 0/10 = 0% | **1/8 = 12.5%** |
| 成本 | 502k / 2.6 min | 502k / 2.6 min |

**`use_code` 核对没有救回来** —— 它挡掉了 89 条噪音，但**也把标尺和 34 条候选一起挡掉了**，
而且剩下的仍然只有 1/8 是真的。

### 为什么（根因没变）

**agent 报的仍然是"释放点附近看着危险的行"**，只是现在要求它抄原文、说清 `expr`、分类 `access` 之后，
它**更保守了**（少报 7–11 倍），但**该报的回边还是不报**（标尺丢了），**不该报的还是报**（析构顺序、switch 分支）。

**程序核对只能验"这一行是不是真的写了这个 object，且是解引用"** ——
它验不出「这块内存是不是同一块」「这个解引用是不是发生在释放之后」（软性的语义）。

---

## 结论

**`use_code` 核对这条路也不成立。** 按你定的判据 <20% → **收口**。

**静态线回到 R22 的结论**：能落地的只有 libredwg 那一种形态；
agent 扫描在 UAF 上的信号比太低，**不值得投入变异预算**。

### 唯一站得住的增量

**`in_dxf.c:12284→12287` 是 double free，agent 报对了**（R26b 也报对了）。
**但 double free 和 UAF 是不同的崩溃类型**，拿它当 UAF 站点的标尺逻辑上不通（你在 R25 就指出过这一点）。
