"""R25 步骤 2–3：核对结果聚合 + 两个实例的重合度 + 和工具扫描的对照。

用法：
    python3 tools/r25_merge.py --osv ARVO-42494732
产出：
    docs/runs/r25/merged_<osv>.json
"""
import argparse
import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
OUT = os.path.join(ROOT, "docs", "runs", "r25")
from r25_agent_scan import verify as _verify  # noqa: E402  用**同一套**核对规则


def _ROOT_OF(osv):
    import json as _j
    P = os.path.join(ROOT, "projects", osv, "source_context.json")
    return _j.load(open(P, encoding="utf-8"))["repo_local"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--osv", default="ARVO-42494732")
    a = ap.parse_args()

    rows = []
    for fn in sorted(os.listdir(OUT)):
        if not (fn.startswith(f"batch_{a.osv}_") and fn.endswith(".json")):
            continue
        d = json.load(open(os.path.join(OUT, fn), encoding="utf-8"))
        for c in d.get("candidates") or []:
            ok, why = _verify(_ROOT_OF(a.osv), c)          # ← 用当前规则**重新核对**
            c = dict(c, verified=ok, verify_reason=why)
            rows.append(dict(c, run=d["run"], batch=d["batch"]))

    # ── 步骤 2 的统计：核对通过率 ──
    reasons = collections.Counter(r.get("verify_reason") for r in rows)
    n = len(rows)
    n_ok = sum(1 for r in rows if r.get("verified"))
    print(f"  原始候选 {n} 处；核对通过 {n_ok}（{100.0 * n_ok / n:.1f}%）" if n else "  无候选")
    for k, v in reasons.most_common():
        print(f"    {k:<22} {v}")

    # ── 步骤 3：按 (file, free_line, use_line) 合并，算重合度 ──
    ok = [r for r in rows if r.get("verified")]
    key = lambda r: (r["file"].lstrip("./"), r["free_line"], r["use_line"])
    groups = collections.defaultdict(list)
    for r in ok:
        groups[key(r)].append(r)

    merged = []
    for k, rs in groups.items():
        runs = sorted({r["run"] for r in rs})
        # 用 where 更好的 why / 更高的自报 confidence
        best = max(rs, key=lambda r: ({"high": 2, "medium": 1, "low": 0}.get(r.get("confidence"), -1),
                                      len(r.get("why") or "")))
        merged.append(dict(
            file=k[0], free_line=k[1], use_line=k[2], object=best.get("object"),
            why=best.get("why"), self_confidence=best.get("confidence"),
            runs=runs, n_runs=len(runs),
            confidence=("high" if len(runs) >= 2 else "medium"),
            batch=best.get("batch"), source="agent",
        ))
    merged.sort(key=lambda m: (m["confidence"] != "high", m["file"], m["free_line"]))

    hi = sum(1 for m in merged if m["confidence"] == "high")
    print(f"\n  合并后 {len(merged)} 处：high（两实例都圈到）{hi} / medium（只一个）{len(merged) - hi}")

    # ── 和工具扫描对照 ──
    tool = []
    fp = os.path.join(ROOT, "json", "projects", a.osv, "feature_pipeline.json")
    if os.path.isfile(fp):
        d = json.load(open(fp, encoding="utf-8"))
        for f in d.get("features") or []:
            for s in f.get("sites") or []:
                tool.append((s["file"].lstrip("./"), s["free_line"], s["use"]["line"]))
    tool = sorted(set(tool))
    ag = {(m["file"], m["free_line"], m["use_line"]) for m in merged}
    both = sorted(ag & set(tool))
    print(f"\n  工具扫到 {len(tool)} 处：{tool}")
    print(f"  三方重合（工具 + 至少一个实例）: {len(both)} 处 {both}")
    print(f"  agent 有、工具没有（**增量**）: {len(ag - set(tool))} 处")
    print(f"  工具有、agent 没圈到（**漏检**）: {len(set(tool) - ag)} 处 {sorted(set(tool) - ag)}")

    # ── 命中验收标尺 ──
    TARGET = ("src/in_dxf.c", 12284, 12267)
    hit = [m for m in merged if (m["file"], m["free_line"], m["use_line"]) == TARGET]
    print(f"\n  ⭐ 标尺 {TARGET[0]}:{TARGET[1]}→{TARGET[2]}: "
          f"{'✅ 圈到了（置信度 ' + hit[0]['confidence'] + '）' if hit else '❌ 没圈到'}")

    json.dump(dict(osv=a.osv, n_raw=n, n_ok=n_ok, reasons=dict(reasons),
                   merged=merged, tool=tool, both=both,
                   incremental=sorted(ag - set(tool)),
                   missed=sorted(set(tool) - ag),
                   target_hit=bool(hit)),
              open(os.path.join(OUT, f"merged_{a.osv}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n  写出 {os.path.join(OUT, f'merged_{a.osv}.json')}")


if __name__ == "__main__":
    main()
