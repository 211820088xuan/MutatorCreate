#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W4 Phase 1a：两道数据完整性防御的**自测**（任务明确要求「构造一次降级写入、构造一次会删
verified 的裁剪，验证都被拦住」）。

两个测试都**不碰真实数据**：
  T1 把真 dataset 复制到 /tmp 后对副本做降级写入；
  T2 用 monkeypatch 把 ② 的 `BINARIES`/`STATE`/`PRUNE_AUDIT` 指到 /tmp 的假归档树，
     再喂一个「`binary_dir` 对不上但 `pinned_commit` 对得上」的合成 dataset —— 这正是
     W3 N20 事故的形态（保护集漏判 → 删掉 verified 归档）。

复算：python3 preflight/w4_phase1a_selftest.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
import repro_common as RC            # noqa: E402
import build_orchestrator as B       # noqa: E402

DATASET = os.path.join(ROOT, "repro_dataset.jsonl")
VERIFIED = ("strict", "medium", "loose")
FAILS = []


def ck(cond, msg):
    print(f"  {'✅' if cond else '❌'} {msg}")
    if not cond:
        FAILS.append(msg)


def pick_verified(path):
    """从真 dataset 里找一条 verified 记录（取最新行）。"""
    lat = {}
    for line in open(path, encoding="utf-8"):
        d = json.loads(line)
        lat[d["osv_id"]] = d
    for oid, d in lat.items():
        if d.get("verification_tier") in VERIFIED:
            return oid, d
    return None, None


def t1_monotonicity(tmp):
    print("\n" + "=" * 78)
    print("T1 ⑤ 单调性校验：把一条 verified 记录降级成 not_run/tier=null，应被**拒写**")
    print("=" * 78)
    oid, d = pick_verified(DATASET)
    if not oid:
        print("  ⓘ dataset 里没有 verified 记录 → 跳过")
        return
    print(f"  目标：{oid}（历史 tier={d['verification_tier']}, project={d['project']}）")
    ds_copy = os.path.join(tmp, "dataset_copy.jsonl")
    shutil.copy(DATASET, ds_copy)

    # 造一个只含该 osv_id 的 manifest + **空** observations/verifications
    # → --no-only-observed 时 ⑤ 会写一条 run_status=not_run / tier=null 的行
    man = os.path.join(tmp, "man.jsonl")
    with open(man, "w", encoding="utf-8") as f:
        f.write(json.dumps({k: d.get(k) for k in RC.MANIFEST_FIELDS}, ensure_ascii=False) + "\n")
    empty = os.path.join(tmp, "empty.jsonl")
    open(empty, "w").close()

    def run5(out, extra=()):
        cmd = [sys.executable, os.path.join(ROOT, "annotate_dataset.py"),
               "--manifest", man, "--observations", empty, "--verifications", empty,
               "--build-records", empty, "--out", out, "--run-id", "w4-selftest",
               "--no-only-observed", *extra]
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        return p.returncode, p.stderr

    before = sum(1 for _ in open(ds_copy, encoding="utf-8"))
    rc1, err1 = run5(ds_copy)
    after = sum(1 for _ in open(ds_copy, encoding="utf-8"))
    ck(after == before, f"默认（无 --force）：**拒写** → 行数 {before} → {after}（应不变）")
    ck("拒写" in err1, f"日志里有明确报错（含「拒写」）：{[l for l in err1.splitlines() if '拒写' in l][:1]}")
    lat = {}
    for line in open(ds_copy, encoding="utf-8"):
        r = json.loads(line)
        lat[r["osv_id"]] = r
    ck(lat[oid].get("verification_tier") == d["verification_tier"],
       f"该 osv_id 的当前状态仍是 {lat[oid].get('verification_tier')}（未被降级）")

    # --force 时应写入且打标
    rc2, err2 = run5(ds_copy, ("--force",))
    after2 = sum(1 for _ in open(ds_copy, encoding="utf-8"))
    lat2 = {}
    for line in open(ds_copy, encoding="utf-8"):
        r = json.loads(line)
        lat2[r["osv_id"]] = r
    ck(after2 == before + 1, f"--force：写入 1 行（{before} → {after2}）")
    ck(lat2[oid].get("tier_downgraded") is True,
       f"--force 的行带 tier_downgraded=true + 原因={str(lat2[oid].get('tier_downgrade_reason'))[:52]}…")
    g = os.path.join(RC.ARTIFACTS, "dataset_guard.jsonl")
    ck(os.path.exists(g) and sum(1 for _ in open(g, encoding="utf-8")) >= 2,
       f"两次都记进了 dataset_guard.jsonl（{sum(1 for _ in open(g, encoding='utf-8')) if os.path.exists(g) else 0} 条）")


def t2_prune_guard(tmp):
    print("\n" + "=" * 78)
    print("T2 裁剪护栏：构造「保护集漏判」的 verified 归档，应被**拒绝删除**")
    print("=" * 78)
    # 假归档树：3 个目录，其中 v1 是「verified 用过、但 binary_dir 字段对不上」的（= N20 形态）
    fake = os.path.join(tmp, "binaries")
    for p, san, com in (("projA", "address", "aaa111"), ("projA", "address", "bbb222"),
                        ("projB", "address", "ccc333")):
        d = os.path.join(fake, p, san, com)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "fuzz"), "wb") as f:
            f.write(b"x" * 4096)
    sh = os.path.join(fake, "_shared")
    os.makedirs(sh, exist_ok=True)
    open(os.path.join(sh, "llvm-symbolizer-deadbeef"), "wb").write(b"y" * 2048)

    ds = os.path.join(tmp, "ds.jsonl")
    with open(ds, "w", encoding="utf-8") as f:
        # 一条 verified：binary_dir 指向**别处**（对不上），但 pinned_commit = aaa111（对得上）
        f.write(json.dumps(dict(osv_id="OSV-1", project="projA", sanitizer="address",
                                verification_tier="strict", pinned_commit="aaa111",
                                binary_dir="/nonexistent/projA/address/zzz999",
                                run_status="run")) + "\n")
        # 一条 none：应可删
        f.write(json.dumps(dict(osv_id="OSV-2", project="projA", sanitizer="address",
                                verification_tier="none", pinned_commit="bbb222",
                                binary_dir=os.path.join(fake, "projA/address/bbb222"),
                                run_status="run")) + "\n")
    st = os.path.join(tmp, "state.json")

    old_bin, old_audit = B.BINARIES, B.PRUNE_AUDIT
    B.BINARIES = fake
    B.PRUNE_AUDIT = os.path.join(tmp, "prune_audit.jsonl")
    try:
        r = B.prune_archive(ds, state_path=st, dry=False, verbose=True)
        ck(r.get("refused") is True, f"M={r.get('M')} > 0 → **拒绝执行**（未删任何目录）")
        ck(os.path.isdir(os.path.join(fake, "projA/address/aaa111")),
           "verified 用过的 aaa111 目录仍在")
        ck(os.path.isdir(os.path.join(fake, "projA/address/bbb222")),
           "连 none 的 bbb222 也没删（拒绝是整轮拒绝，不部分执行）")
        aud = [json.loads(l) for l in open(B.PRUNE_AUDIT, encoding="utf-8")]
        ck(aud and aud[-1]["action"] == "REFUSED", f"审计留痕 action=REFUSED（{len(aud)} 条）")

        # --prune-force 时应删，且审计留痕
        r2 = B.prune_archive(ds, state_path=st, dry=False, verbose=False, prune_force=True)
        ck(r2.get("n_pruned") == 3, f"--prune-force：照删 {r2.get('n_pruned')} 个（含被保护的，用户显式要求）")
        aud2 = [json.loads(l) for l in open(B.PRUNE_AUDIT, encoding="utf-8")]
        ck(aud2[-1]["action"] == "pruned" and aud2[-1]["M"] == 1,
           f"审计留痕 action=pruned, M={aud2[-1]['M']}")

        # 正常情形（binary_dir 对得上）：M=0 → 允许删非 verified 的
        ds3 = os.path.join(tmp, "ds3.json")
        fake2 = os.path.join(tmp, "binaries2")
        for p, san, com in (("projC", "address", "ddd444"), ("projC", "address", "eee555")):
            d = os.path.join(fake2, p, san, com)
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, "fuzz"), "wb").write(b"z" * 1024)
        with open(ds3, "w", encoding="utf-8") as f:
            f.write(json.dumps(dict(osv_id="OSV-3", project="projC", sanitizer="address",
                                    verification_tier="medium", pinned_commit="ddd444",
                                    binary_dir=os.path.join(fake2, "projC/address/ddd444"),
                                    run_status="run")) + "\n")
            f.write(json.dumps(dict(osv_id="OSV-4", project="projC", sanitizer="address",
                                    verification_tier="none", pinned_commit="eee555",
                                    binary_dir=os.path.join(fake2, "projC/address/eee555"),
                                    run_status="run")) + "\n")
        B.BINARIES = fake2
        r3 = B.prune_archive(ds3, state_path=os.path.join(tmp, "st3.json"), dry=False, verbose=False)
        ck(r3.get("M") == 0 and r3.get("n_pruned") == 1 and r3.get("n_kept") == 1,
           f"正常情形：M=0、保留 1（medium）、删 1（none）→ 实得 M={r3.get('M')} "
           f"kept={r3.get('n_kept')} pruned={r3.get('n_pruned')}")
        ck(os.path.isdir(os.path.join(fake2, "projC/address/ddd444"))
           and not os.path.isdir(os.path.join(fake2, "projC/address/eee555")),
           "目录级验证：verified 的在、none 的没了")
    finally:
        B.BINARIES, B.PRUNE_AUDIT = old_bin, old_audit


def main():
    tmp = tempfile.mkdtemp(prefix="w4_selftest_")
    print(f"临时目录 {tmp}（测试不碰真实数据）")
    t1_monotonicity(tmp)
    t2_prune_guard(tmp)
    shutil.rmtree(tmp, ignore_errors=True)
    print("\n" + "=" * 78)
    if FAILS:
        print(f"❌ {len(FAILS)} 项未通过：")
        for f in FAILS:
            print(f"   - {f}")
        return 1
    print("✅ 两道防御全部按预期拦住")
    return 0


if __name__ == "__main__":
    sys.exit(main())
