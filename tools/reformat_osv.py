#!/usr/bin/env python3
"""Overwrite every crash_testcase/<slug>/<driver>/<osv_id>.json with the
human-readable flat OSS-Fuzz bug format sourced from /root/gyx/sh/vulns/.

The sh/vulns/<project>/<osv_id>.json files already have the desired schema:
  project, bug_id, fuzzing_engine, fuzz_target, job_type, platform,
  crash_type, crash_address, crash_state[], sanitizer, security_severity,
  introducing_commit, report_url, testcase_url.

We re-emit with indent=2 + ensure_ascii=False for consistent readability.
"""
import json, os

# [重构] 本脚本已移入 tools/，项目根在上一层
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DS = os.path.join(ROOT, "data", "crash_dataset.jsonl")
SH_VULNS = "/root/gyx/sh/vulns"
OUT = os.path.join(ROOT, "crash_testcase")

def build_index():
    idx = {}
    for proj in os.listdir(SH_VULNS):
        pd = os.path.join(SH_VULNS, proj)
        if not os.path.isdir(pd):
            continue
        for fn in os.listdir(pd):
            if fn.endswith(".json"):
                idx[fn[:-5]] = os.path.join(pd, fn)
    return idx

def main():
    idx = build_index()
    rows = [json.loads(l) for l in open(DS)]
    n = len(rows)
    rewritten = 0
    not_in_index = []
    for i, r in enumerate(rows):
        if i % 500 == 0:
            print(f"  {i}/{n}...", flush=True)
        osv_id = r["osv_id"]
        src = idx.get(osv_id)
        if not src:
            not_in_index.append(osv_id)
            continue
        crash_slug = r["crash_type"].replace(" ", "_")
        driver = r["fuzz_target"] or "_unknown"
        dst = os.path.join(OUT, crash_slug, driver, osv_id + ".json")
        obj = json.load(open(src))
        with open(dst, "w") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)
        rewritten += 1
    print(f"rewritten: {rewritten}/{n}, not in sh/vulns index: {len(not_in_index)}")
    if not_in_index:
        print("  missing:", not_in_index[:20])

if __name__ == "__main__":
    main()
