#!/usr/bin/env python3
"""Task: collect all 3,790 crash testcases, organized by crash_type then driver.

Layout:  crash_testcase/<crash_type_slug>/<driver>/
             OSV-<id>-testcase    (copied from /root/gyx/testcases/<proj>/... if on disk)
             <osv_id>.json         (copied from data/_osv_cache/)

- crash_type field: normalized (30 kinds); slug = replace(" ","_"), hyphens/case kept.
- driver = fuzz_target; empty -> "_unknown".
- copy (not symlink). osv_id all unique -> no name collisions.
- 35 missing testcase files on disk -> place OSV JSON only, log to _MANIFEST_missing.txt.
"""
import json, os, shutil
from collections import Counter, defaultdict

# [重构] 本脚本已移入 tools/，项目根在上一层
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DS = os.path.join(ROOT, "data", "crash_dataset.jsonl")
OSV_CACHE = os.path.join(ROOT, "data", "_osv_cache")
OUT = os.path.join(ROOT, "crash_testcase")
TC_ROOT = "/root/gyx/testcases"

def main():
    rows = [json.loads(l) for l in open(DS)]
    n = len(rows)
    missing = []
    ct_count = Counter()
    drv_per_ct = defaultdict(Counter)
    copied_tc = 0
    copied_osv = 0
    skipped_tc = 0

    for i, r in enumerate(rows):
        if i % 500 == 0:
            print(f"  {i}/{n}...", flush=True)
        crash_slug = r["crash_type"].replace(" ", "_")
        driver = r["fuzz_target"] or "_unknown"
        ct_count[crash_slug] += 1
        drv_per_ct[crash_slug][driver] += 1
        d = os.path.join(OUT, crash_slug, driver)
        os.makedirs(d, exist_ok=True)

        # testcase
        tc_src = r["testcase_path"]
        tc_dst = os.path.join(d, os.path.basename(tc_src))
        if os.path.exists(tc_src):
            shutil.copy2(tc_src, tc_dst)
            copied_tc += 1
        else:
            skipped_tc += 1
            missing.append((r["osv_id"], r["crash_type"], driver, tc_src))

        # OSV record
        osv_src = os.path.join(OSV_CACHE, r["osv_id"] + ".json")
        osv_dst = os.path.join(d, r["osv_id"] + ".json")
        if os.path.exists(osv_src):
            shutil.copy2(osv_src, osv_dst)
            copied_osv += 1

    # manifest of missing testcases
    man = os.path.join(OUT, "_MANIFEST_missing.txt")
    with open(man, "w") as f:
        f.write(f"# {len(missing)} testcases missing on disk (OSV JSON still placed)\n")
        f.write("osv_id\tcrash_type\tdriver\texpected_testcase_path\n")
        for oid, ct, drv, path in missing:
            f.write(f"{oid}\t{ct}\t{drv}\t{path}\n")

    # summary
    summ = os.path.join(OUT, "_SUMMARY.txt")
    with open(summ, "w") as f:
        f.write(f"# crash_testcase collection summary\n")
        f.write(f"total rows      : {n}\n")
        f.write(f"crash_type dirs : {len(ct_count)}\n")
        f.write(f"driver dirs     : {sum(len(v) for v in drv_per_ct.values())}\n")
        f.write(f"testcases copied: {copied_tc}\n")
        f.write(f"testcases missed: {skipped_tc} (see _MANIFEST_missing.txt)\n")
        f.write(f"OSV JSON copied: {copied_osv}\n\n")
        f.write("## per crash_type\n")
        for ct, c in ct_count.most_common():
            f.write(f"  {c:5d}  {ct}  ({len(drv_per_ct[ct])} drivers)\n")
    print(f"done: {copied_tc} tc + {copied_osv} osv copied, {skipped_tc} missing")
    print(f"  {len(ct_count)} crash_type dirs, {sum(len(v) for v in drv_per_ct.values())} driver dirs")

if __name__ == "__main__":
    main()
