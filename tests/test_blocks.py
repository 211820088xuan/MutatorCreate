"""R22 步骤 0：验证 `s5_6_lib.blocks()` 的修复。

## 为什么

R21 为了加 if/else 互斥守卫去用 `blocks()`，发现两个真 bug：

| # | bug | 影响 |
|---|---|---|
| 1 | **假设 Allman 风格**（`{` 独占一行），永远看**上一行**当头部 | K&R 的 `if (x) {` 整块被标成 `plain` → **所有 K&R 项目的 CFG 全错** |
| 2 | **`} else {` 判不出来**（`head` 是 `} else`，不匹配 `^else`） | else 块丢失 |

`blocks()` 是 `flow()` / `step()` / `loop_back` 的基础。**它错了二十轮没被发现，
因为 libredwg 恰好是 GNU 风格（`{` 独占一行）。**

**这一组测试就是那个 bug 的回归网。** 把修复退回，它们必须变红。
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "pipeline"))
from s5_6_lib import blocks  # noqa: E402


def mk(*rows):
    """把代码行拼成 lines 列表。"""
    return list(rows)


def kinds(blks):
    return sorted(b["kind"] for b in blks)


def by_kind(blks, kind):
    return [b for b in blks if b["kind"] == kind]


# ── 1. Allman `if` ────────────────────────────────────────────────────
def test_allman_if():
    L = mk("void f()", "{", "    if (x)", "    {", "        y();", "    }", "}")
    blks = blocks(L, 0, len(L) - 1)
    assert by_kind(blks, "if"), "Allman if 必须是 kind=if"
    b = by_kind(blks, "if")[0]
    assert b["open"] == 3 and b["close"] == 5
    assert b["header"] == 2          # 头部是 `if (x)` 那一行


# ── 2. K&R `if`（这是 bug 1 的核心）──────────────────────────────────
def test_kr_if():
    L = mk("void f() {", "    if (x) {", "        y();", "    }", "}")
    blks = blocks(L, 0, len(L) - 1)
    assert by_kind(blks, "if"), "K&R 的 `if (x) {` 必须被识别成 kind=if（原来标成 plain）"
    b = by_kind(blks, "if")[0]
    assert b["open"] == 1 and b["close"] == 3
    assert b["header"] == 1


# ── 3. `} else {`（这是 bug 2 的核心）────────────────────────────────
def test_brace_else():
    L = mk("void f() {", "    if (x) {", "        a();", "    } else {", "        b();", "    }", "}")
    blks = blocks(L, 0, len(L) - 1)
    assert by_kind(blks, "if"), "if 块必须在"
    assert by_kind(blks, "else"), "`} else {` 必须被识别成 kind=else（原来标成 plain）"
    ei = by_kind(blks, "if")[0]
    el = by_kind(blks, "else")[0]
    assert (ei["open"], ei["close"]) == (1, 3)
    assert (el["open"], el["close"]) == (3, 5)
    assert el["header"] == 3


# ── 4. Allman `else` ─────────────────────────────────────────────────
def test_allman_else():
    L = mk("void f()", "{", "    if (x)", "    {", "        a();", "    }", "    else", "    {",
           "        b();", "    }", "}")
    blks = blocks(L, 0, len(L) - 1)
    assert by_kind(blks, "if") and by_kind(blks, "else")
    el = by_kind(blks, "else")[0]
    assert el["header"] == 6         # `else` 那一行


# ── 5. K&R `for` / `while` ───────────────────────────────────────────
def test_kr_loops():
    L = mk("void f() {", "    for (i = 0; i < n; i++) {", "        a();", "    }",
           "    while (p) {", "        b();", "    }", "}")
    blks = blocks(L, 0, len(L) - 1)
    loops = by_kind(blks, "loop")
    assert len(loops) == 2, "K&R 的 for/while 都必须是 kind=loop"
    assert [b["header"] for b in loops] == [1, 4]


# ── 6. 嵌套：K&R 外层 + Allman 内层 ──────────────────────────────────
def test_nested_kr_outer_allman_inner():
    L = mk("void f() {", "    for (i = 0; i < n; i++) {", "        if (x)", "        {",
           "            a();", "        }", "    }", "}")
    blks = blocks(L, 0, len(L) - 1)
    outer = [b for b in by_kind(blks, "loop") if b["open"] == 1]
    inner = [b for b in by_kind(blks, "if") if b["open"] == 3]
    assert outer and inner, "外层 loop（K&R）+ 内层 if（Allman）都要识别"
    assert outer[0]["close"] == 6
    assert inner[0]["close"] == 5


# ── 7. `} else if (...) {` ───────────────────────────────────────────
def test_brace_else_if():
    """按**当前实现的语义**断言：`else if (...)` 归到 kind=if。

    注意：这是实现的既有语义（`hs.startswith("else") and "if" not in hs` 不成立
    → 落到 else 分支 `kind = "if"`）。这里**如实断言它**，不猜"应该是什么"。
    """
    L = mk("void f() {", "    if (a) {", "        x();", "    } else if (b) {", "        y();",
           "    }", "}")
    blks = blocks(L, 0, len(L) - 1)
    assert not by_kind(blks, "else"), "`else if` 不产生 kind=else（当前语义）"
    assert len(by_kind(blks, "if")) == 2, "两个都算 kind=if"
    assert [b["header"] for b in by_kind(blks, "if")] == [1, 3]


# ── 8. 单行块（无 `{`）→ 不产生块 ────────────────────────────────────
def test_single_line_if_has_no_block():
    """没有 `{` 就没有块 —— 当前实现只按花括号配对。

    这是**已知限制**（单行块不进 CFG），如实断言。
    """
    L = mk("void f() {", "    if (x) y();", "    z();", "}")
    blks = blocks(L, 0, len(L) - 1)
    assert not [b for b in blks if b["open"] == 1], "`if (x) y();` 不该产生块"


# ── 9. break 之前的守卫所依赖的那两个真实站点的形状 ──────────────────
def test_real_leptonica_shape():
    """leptonica `pix4.c` 的真实形状：`if (array) { … } else { … }`。"""
    L = mk(
        "void pixRankBinByStrip() {",
        "    if (mode == L_SCAN_HORIZONTAL) {",
        "        for (i = 0; i < n; i++) {",
        "            if (array) {",
        "                LEPT_FREE(array);",
        "            }",
        "        }",
        "    } else {  /* L_SCAN_VERTICAL */",
        "        for (i = 0; i < n; i++) {",
        "            if (array) {",
        "                array[j];",
        "            }",
        "            LEPT_FREE(array);",
        "        }",
        "    }",
        "}",
    )
    blks = blocks(L, 0, len(L) - 1)
    assert by_kind(blks, "else"), "`} else {  /* L_SCAN_VERTICAL */` 这一行必须识别成 else"
    el = by_kind(blks, "else")[0]
    assert el["open"] == 7 and el["close"] == 14
    assert el["header"] == 7
