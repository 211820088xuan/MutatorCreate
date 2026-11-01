#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W5：① `manifest_builder` 的**覆盖护栏**自测（新发现 N26）。

✅ W5 实测踩到两次「后一次运行静默销毁更强产物」：
  1. `python3 manifest_builder.py`（不带 `--static-check`）刷新全局 manifest →
     `fixed_real` 非空行从 167（W3 正典）变 **0**、`degenerate_resolved`  likewise；
     只因我顺手比了回归数字（25/0/4 → 20/0/9）才发现。
  2. 更险的 footgun：`--only-osv 3 条` 若用**默认 `--out`**，会把全局 manifest
     从 **3,790 行覆盖成 3 行**（main() 写的是过滤后的 records）。
这与 N25（构建日志被同名覆盖）、N20（归档被误删）同一根因：
**派生产物按固定路径写，后一次运行无条件覆盖前一次，而结论仍引用它。**

护栏判据（纯函数，可单测）：新产物若在**覆盖面**或**任一关键字段的强度**上严格更弱
→ 拒写并说明原因；`--force-overwrite` 才写（且留痕）。

复算：python3 preflight/w5_selftest_overwrite.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
import manifest_builder as M         # noqa: E402

FAILS = []


def ck(cond, msg):
    print(("  ✅ " if cond else "  ❌ ") + msg)
    if not cond:
        FAILS.append(msg)


def row(oid, **kw):
    r = {"osv_id": oid, "project": oid.split("-")[0], "repo_path": None,
         "repo_path_confidence": "none", "fixed_real": None,
         "static_check_verdict": "skipped", "degenerate_resolved": None}
    r.update(kw)
    return r


def guard(old, new):
    return M.overwrite_guard(old, new)


def main():
    print("═" * 72)
    print("W5 ① 自测：覆盖护栏（不得用更弱的产物静默覆盖更强的）")
    print("═" * 72)

    print("\n[A] 首次写盘 / 变强 → 必须放行")
    ok, why = guard(None, [row("OSV-1")])
    ck(ok and not why, f"目标文件不存在（首次写）→ 放行（{why}）")
    ok, why = guard([row("OSV-1")], [row("OSV-1", repo_path="/src/x",
                                         repo_path_confidence="high")])
    ck(ok, f"同一行变强（repo_path 由 None → /src/x）→ 放行（{why}）")
    ok, why = guard([row("OSV-1")], [row("OSV-1"), row("OSV-2")])
    ck(ok, f"覆盖面变大（1 → 2 行）→ 放行（{why}）")

    print("\n[B] 覆盖面缩水 → 必须拒写（`--only-osv` 打全局 manifest 的 footgun）")
    old = [row(f"OSV-{i}") for i in range(3790)]
    ok, why = guard(old, [row("OSV-1"), row("OSV-2"), row("OSV-3")])
    ck(not ok, "3790 行 → 3 行：拒写")
    ck(any("覆盖" in w or "coverage" in w for w in why), f"原因点明覆盖面：{why}")

    print("\n[C] 同一行字段变弱 → 必须拒写（我这次全量重跑的实际形态）")
    old = [row("OSV-1", repo_path="/src/pcre2", repo_path_confidence="high",
               fixed_real="d6836713", static_check_verdict="located",
               degenerate_resolved=True)]
    ok, why = guard(old, [row("OSV-1")])
    ck(not ok, "全部静态 check 字段丢失 → 拒写")
    for f in ("repo_path", "fixed_real", "static_check_verdict", "degenerate_resolved"):
        ck(any(f in w for w in why), f"原因点明具体字段 `{f}`：{[w for w in why if f in w]}")

    print("\n[D] 部分行变弱也要拦（不能被「其他行变强」抵消）")
    old = [row("OSV-1", fixed_real="aaa"), row("OSV-2")]
    new = [row("OSV-1"), row("OSV-2", fixed_real="bbb")]
    ok, why = guard(old, new)
    ck(not ok, f"OSV-1 丢 fixed_real（OSV-2 新增不算抵消）→ 拒写（{why}）")

    print("\n[E] 只在**交集**上比强度：新增行没值不算变弱")
    old = [row("OSV-1", fixed_real="aaa")]
    new = [row("OSV-1", fixed_real="aaa"), row("OSV-2")]
    ok, why = guard(old, new)
    ck(ok, f"老行原样保留 + 新增一行（新行字段为空是正常的）→ 放行（{why}）")

    print("\n[F] 负对照：证明上面不是空过")
    ok, why = guard([row("OSV-1", fixed_real="aaa")], [row("OSV-1", fixed_real="aaa")])
    ck(ok and not why, f"完全相同 → 放行且无原因（说明 [B][C][D] 的拒写不是恒拒）")

    print("\n" + (f"❌ {len(FAILS)} 项未通过：{FAILS}" if FAILS else "✅ 全部通过"))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
