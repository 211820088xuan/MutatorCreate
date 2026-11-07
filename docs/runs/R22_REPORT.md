# R22 报告

日期：2026-11-07
唯一问题：**"没有第二个落地项目"是真的没有，还是因为工具当时是坏的？**

> 出发点（不重复论证）：R21 查出 `s5_6_lib.blocks()` 两个 bug（假设 Allman 风格、`} else {` 判不出来）。
> `blocks()` 是 `flow()` / `step()` / `loop_back` 的基础 → **所有 K&R 风格项目的控制流分析之前全是错的**。
> 证据：修好后 leptonica 的 `loop_back` 站点从 **0 变成 6**。

---

## 步骤 0 · 先确认 `blocks()` 真的修对了

### 9 个测试用例（`tests/test_blocks.py`）

| # | 用例 | 期望 | 结果 |
|---|---|---|---|
| 1 | Allman `if`（`{` 独占一行） | `kind=if`，`open/close/header` 正确 | ✅ |
| 2 | **K&R `if`**（`if (x) {`） | `kind=if`（**bug 1 的核心**） | ✅ |
| 3 | **`} else {`** | 两块，`kind=if` + `kind=else`，边界与 `header` 正确 | ✅ |
| 4 | Allman `else`（`else` 独占一行 + `{` 独占一行） | `kind=else`，`header` = `else` 那行 | ✅ |
| 5 | K&R `for` / `while` | 两个都 `kind=loop` | ✅ |
| 6 | 嵌套（K&R 外层 loop + Allman 内层 if） | 层级与边界都正确 | ✅ |
| 7 | `} else if (...) {` | **按当前实现的语义断言**：不产生 `kind=else`，两个都算 `kind=if` | ✅ |
| 8 | 单行 `if (x) foo();`（无 `{`） | **不产生块**（已知限制，如实断言） | ✅ |
| 9 | 真实 leptonica 形状（`if (array) { … } else { … }` 套循环） | `else` 块边界 = 7–14 | ✅ |

**第 7、8 条是"按实现的语义断言，不猜"** —— 它们的注释写明了这是既有语义/已知限制，
不是"应该怎样"。**如果将来改了语义，这两个测试会准确地提示需要更新。**

### 🔴 变异检验：退回修复 → **6 / 9 变红**

把 R21 的两处修复都退回（恢复"永远看上一行" + 去掉 `lstrip("}")`）：

```
  6 failed, 3 passed
  FAILED test_kr_if                      ← K&R
  FAILED test_brace_else                 ← `} else {`
  FAILED test_kr_loops                   ← K&R for/while
  FAILED test_nested_kr_outer_allman_inner
  FAILED test_brace_else_if
  FAILED test_real_leptonica_shape
```

**剩下 3 个通过的是 Allman 风格 + 单行块**（旧代码本来就能处理）—— 这正说明
**这 6 个测试打在 bug 上**，而另外 3 个是"对照组"。

恢复修复后 **9 / 9 绿**。

**变异体下的实际输出**（说明旧代码把 K&R 全标成 `plain`）：

```
  [{'open': 1, 'close': 7, 'kind': 'plain', 'header': 0},
   {'open': 7, 'close': 14, 'kind': 'plain', 'header': 6}, ...]
```

### libredwg 回归：✅ 全部不变

```
  uaf-llm01 found，原语 2
  站点: src/in_dxf.c 12284 → 12267  var=pair  kind=loop_back
  plan: ready 1 site 1 mut  total=1.0
  mutator.c sha1: d7913b9e
  verify: pass
  pytest: 35 passed（原有 26 + 新增 9）
```

### ⏸ 停止点：等确认

| 验收项 | 结果 |
|---|---|
| 新测试全绿 | ✅ 9 passed（总计 35 passed） |
| **变异检验能让它们变红** | ✅ **6 / 9 变红** |
| libredwg 回归（站点 / kind / plan / sha1 / verify） | ✅ 全部不变 |
| pytest | ✅ 35 passed |

**确认后进步骤 1**：判断哪些项目是 K&R（受 bug 影响）、哪些是 GNU（不受影响），然后重扫受影响的。

**⚠️ 一个要提前说的事**：R21 修好后 leptonica 的 `loop_back` 从 0 变 6，
但那 6 条里 5 条被"下一轮重赋值"检查挡掉、剩的 1 条（`pix4.c:3065→3064`）**仍是假阳性**（跨嵌套循环）。
所以**重扫后的新增站点，很可能仍然全是假阳性** —— 我会逐条读 pin 源码核，不预设结论。
