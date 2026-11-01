#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重建被 `purge-on-verify` 回收的归档，并**逐字节校验**是否与复现记录表记录的 sha256 一致。

为什么需要它：`--purge-on-verify` 曾默认开（现已反转为默认关），把 106 条 verified 里
**72 条**的二进制删掉了（只留 sha256 + 配方）。而**重放必须有二进制** —— 「可重建」不等于「在场」。

做法（不重跑 ③④⑤，只补 ②）：
  1. 从复现记录表挑出 `verification_tier ∈ {strict,medium,loose}` 且 `binary_dir` 不在盘上的行；
  2. 按 `(project, sanitizer, pinned_commit, arch)` 去重 → **N 个归档**（一份归档可服务多条 crash）；
  3. 用 `--commit-override <osv>=<commit>:<depth>` **强制钉到复现记录表记录的那个 commit**
     （不能让 walk-back 自己找 —— 它可能在更浅的格就建成，那 restored 的就不是原来那份）；
  4. 重建后把每个 target 的 sha256 与复现记录表 `binary_sha256` 逐个比对 → **bit 级验证**。

✅ 已有先例证明这条路可行：W4 重建 4 个被误删归档 → **20/20 文件逐字节一致**；
   N30 恢复 2 条 strict 证据 → **5/5 sha256 一致**。

用法：
    python3 rebuild_archives.py --dry            # 只报要重建什么、预计多久
    python3 rebuild_archives.py                  # 真跑（默认 --min-free-gb 4）
    python3 rebuild_archives.py --project pcre2  # 只重建某项目
    python3 rebuild_archives.py --verify-only    # 不建，只校验盘上已有的与复现记录表是否一致
"""
import argparse
import collections
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.path.join(HERE, "repro_dataset.jsonl")
MANIFEST = os.path.join(HERE, "artifacts", "repro_manifest.jsonl")
BREC = os.path.join(HERE, "artifacts", "build_records.jsonl")
STATE = os.path.join(HERE, "artifacts", "state.json")
BO = os.path.join(HERE, "build_orchestrator.py")
VERIFIED = ("strict", "medium", "loose")


def log(*a):
    print(*a, flush=True)


def load_latest():
    lat = {}
    with open(DATASET, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                r = json.loads(line)
                lat[r["osv_id"]] = r          # 后者覆盖 = 最新
    return lat


def sha256_file(path, chunk=1 << 20):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def arch_of(binary_dir):
    """归档目录名 `<commit>` = x86_64；`<commit>__i386` = i386（与 ② 的 `_base()` 同口径）。"""
    base = os.path.basename((binary_dir or "").rstrip("/"))
    return base.split("__", 1)[1] if "__" in base else "x86_64"


def need_rebuild(lat, project=None):
    """→ {(project, san, commit, arch): [rows]}，只含 verified 且归档不在盘上的。"""
    out = collections.defaultdict(list)
    for r in lat.values():
        if r.get("verification_tier") not in VERIFIED:
            continue
        if project and r.get("project") != project:
            continue
        bd = r.get("binary_dir")
        if not bd or os.path.isdir(bd):
            continue                                    # 没有路径 / 已在盘 → 不用建
        key = (r.get("project"), r.get("sanitizer"), r.get("pinned_commit"), arch_of(bd))
        if not all(key[:3]):
            log(f"  ⚠ {r['osv_id']} 缺 project/sanitizer/pinned_commit → 无法重建，跳过")
            continue
        out[key].append(r)
    return out


def median_build_seconds(project):
    """该项目历史成功构建的耗时中位数（只用于估算，不参与决策）。"""
    xs = []
    if os.path.exists(BREC):
        for line in open(BREC, encoding="utf-8"):
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            k = (r.get("key") or "").split("|")
            if k and k[0] == project and r.get("build_status") == "ok" and r.get("build_seconds"):
                xs.append(r["build_seconds"])
    return sorted(xs)[len(xs) // 2] if xs else None


def verify(lat, project=None, verbose=True):
    """逐字节校验：盘上归档里每个 target 的 sha256 是否等于复现记录表记录值。"""
    ok = bad = miss = 0
    bad_list = []
    for r in lat.values():
        if r.get("verification_tier") not in VERIFIED:
            continue
        if project and r.get("project") != project:
            continue
        bd, rec = r.get("binary_dir"), r.get("binary_sha256") or {}
        if not bd or not rec:
            continue
        if not os.path.isdir(bd):
            miss += 1
            continue
        for name, want in rec.items():
            p = os.path.join(bd, name)
            if not os.path.exists(p):
                bad += 1
                bad_list.append((r["osv_id"], name, "文件不在"))
                continue
            got = sha256_file(p)
            if got == want:
                ok += 1
            else:
                bad += 1
                bad_list.append((r["osv_id"], name, f"sha256 不符 期望{want[:12]}… 实得{got[:12]}…"))
    if verbose:
        log(f"  逐字节校验：✅ 一致 {ok} 个文件 · ❌ 不符 {bad} · 归档仍缺 {miss} 条")
        for x in bad_list[:8]:
            log(f"     ❌ {x[0]} {x[1]}: {x[2]}")
    return ok, bad, miss


def build(keys, min_free_gb, build_timeout, dry=False):
    """按 arch 分组调用 ②，用 --commit-override 强制钉到复现记录表记录的 commit。"""
    by_arch = collections.defaultdict(list)
    for k, rows in keys.items():
        by_arch[k[3]].append((k, rows))
    total = 0
    for arch, items in sorted(by_arch.items()):
        ov, osvs = [], []
        for (proj, san, commit, _a), rows in items:
            rep = rows[0]                                # 同一归档任取一条作构建入口
            depth = rep.get("walkback_depth_actual") or 1
            ov.append(f"{rep['osv_id']}={commit}:{depth}")
            osvs.append(rep["osv_id"])
        cmd = [sys.executable, BO, "--manifest", MANIFEST, "--out", BREC, "--state", STATE,
               "--stage", "2", "--build-timeout", str(build_timeout),
               "--stop-after-failures", "0",            # 一条失败不要连坐整批
               "--min-free-gb", str(min_free_gb),
               "--architecture", arch,
               "--only-osv", ",".join(osvs),
               "--commit-override", ",".join(ov)]
        log(f"\n▶ arch={arch}：{len(items)} 个归档 / {len(osvs)} 条 crash")
        if dry:
            log("  [dry] " + " ".join(cmd[:6]) + f" … --only-osv {len(osvs)} 条")
            for i, o in enumerate(osvs):
                log(f"        {o} → {ov[i]}")
            total += len(items)
            continue
        rc = subprocess.run(cmd, cwd=HERE).returncode
        log(f"  ② 退出码 {rc}")
        total += len(items)
    return total


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry", action="store_true", help="只报计划，不构建")
    ap.add_argument("--project", help="只处理某项目")
    ap.add_argument("--verify-only", action="store_true", help="不构建，只逐字节校验盘上已有的")
    ap.add_argument("--min-free-gb", type=float, default=4.0,
                    help="磁盘余量护栏（默认 4G；② 的默认是 0=不检查，这里显式给一个）")
    ap.add_argument("--build-timeout", type=int, default=1800)
    a = ap.parse_args()

    lat = load_latest()
    if a.verify_only:
        log("═══ 只校验，不构建 ═══")
        ok, bad, miss = verify(lat, a.project)
        return 1 if bad else 0

    keys = need_rebuild(lat, a.project)
    n_crash = sum(len(v) for v in keys.values())
    log("═" * 78)
    log(f"需重建 **{len(keys)} 个归档**（服务 {n_crash} 条 verified crash）")
    log("═" * 78)
    est = 0.0
    byp = collections.Counter(k[0] for k in keys)
    for p, c in byp.most_common():
        med = median_build_seconds(p)
        e = c * (med or 120)
        est += e
        log(f"  {p:<12}{c:>3} 个归档   单次构建中位 {med and round(med) or '?'}s   预计 {e/60:.0f}min")
    log(f"  → 合计预计 **{est/3600:.1f} 小时**")
    log(f"  按 arch: {dict(collections.Counter(k[3] for k in keys))}")
    if not keys:
        log("\n没有需要重建的归档。")
        verify(lat, a.project)
        return 0
    if a.dry:
        log("\n[dry-run] 计划如下：")
    build(keys, a.min_free_gb, a.build_timeout, dry=a.dry)
    if a.dry:
        return 0
    log("\n═══ 重建后逐字节校验 ═══")
    ok, bad, miss = verify(lat, a.project)
    log(f"\n结果：✅ {ok} 个文件 sha256 一致 · ❌ {bad} 不符 · 仍缺 {miss} 条")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
