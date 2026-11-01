#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W5：交付面审计的**牙齿测试** —— 往复现记录表**副本**里注入违规，审计必须抓出来。

为什么需要它：`w5_audit_delivery.py` 对真复现记录表报「✅ 0 条红线违反」。但一个**恒真**的审计
也会报绿 —— 不注入违规就永远不知道它有没有牙。这是本项目反复用的手法（分类器倒序负对照、
N16 的分类器负对照、覆盖护栏的"完全相同→放行"负对照）。

✅ 本测试**已经抓到过一个真缺陷**：审计原来把 medium/loose 的判据写成
`… and nrec`（`n_recovered_frames`），而复现记录表里该字段**常为 None**（⑤ 未透传 ④ 的这个字段）
→ 条件恒假 → **R 为空的那批行完全不检查**。注入 `medium + crash_type_match=False` 后审计不报，
才发现这条漏检。修法：重读 ④ 的分支，确认 `medium ⇒ crash_type_match`、`loose ⇒ ¬crash_type_match`
在 **R 为空与 R 非空两种情况下都成立** → 去掉多余的 `nrec` 前置条件。

**绝不碰真复现记录表**：所有变异都写在临时副本上，用 `--dataset` 指过去。
复算：python3 preflight/w5_selftest_audit_teeth.py
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATASET = os.path.join(ROOT, "repro_dataset.jsonl")
AUDIT = os.path.join(HERE, "w5_audit_delivery.py")
VERIFIED = ("strict", "medium", "loose")


def build_mutated(dest):
    """按 tier 各挑一条 verified 行，注入三类**确实违规**的变异。

    ⚠ 选样要点（本测试自己踩过的坑）：不能随便取前几条 verified 行。
    例如给一条 `loose` 行设 `crash_type_match=False` —— 那**本来就是自洽的**
    （④：loose ⇔ crash_type 不一致），审计不报是**对的**，于是测试会误判成"审计无牙"。
    必须按 tier 选「注入后确实违反不变量」的行。
    """
    rows = [json.loads(l) for l in open(DATASET, encoding="utf-8")]
    lat = {}
    for i, r in enumerate(rows):
        lat[r["osv_id"]] = i
    by_tier = {}
    for o, i in lat.items():
        by_tier.setdefault(rows[i].get("verification_tier"), []).append(o)
    for t in ("strict", "medium", "loose"):
        if not by_tier.get(t):
            raise SystemExit(f"复现记录表里没有 tier={t} 的行 → 无法构造该变异（不是审计的问题）")

    inj = []
    a = by_tier["strict"][0]
    rows[lat[a]]["crash_type_match"] = False          # strict 却 crash_type 不一致
    inj.append(("strict∧¬crash_type_match", a))
    b = by_tier["medium"][0]
    rows[lat[b]]["binary_sha256"] = None              # verified 却丢了指纹
    inj.append(("verified 缺 binary_sha256", b))
    c = by_tier["loose"][0]
    rows[lat[c]]["binary_dir"] = "/definitely/gone/xyz"
    rows[lat[c]]["binary_pruned"] = None              # verified 悬空且未标记
    inj.append(("verified 悬空未标记", c))
    # 第四类：把一条 none 行说成复现了（tier 与 reproduced_any 矛盾）
    nones = [o for o, i in lat.items() if rows[i].get("verification_tier") == "none"]
    if nones:
        d = nones[0]
        rows[lat[d]]["reproduced_any"] = True
        inj.append(("none 却 reproduced_any=True", d))
    with open(dest, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return inj


def main():
    print("═" * 84)
    print("W5 交付面审计 · 牙齿测试（注入违规 → 审计必须变红）")
    print("═" * 84)
    td = tempfile.mkdtemp()
    mutated = os.path.join(td, "mutated.jsonl")
    inj = build_mutated(mutated)
    print("\n注入的违规：")
    for why, oid in inj:
        print(f"  • {oid:<16}{why}")

    out = subprocess.run([sys.executable, AUDIT, "--dataset", mutated],
                         capture_output=True, text=True)
    print(f"\n审计退出码 {out.returncode}（期望 **非 0**）")
    caught = [l.strip()[:118] for l in out.stdout.splitlines() if "❌ [硬]" in l]
    for l in caught:
        print("  " + l)

    need = ["crash_type_match", "binary_sha256", "悬空", "reproduced_any"]
    hit = [k for k in need if any(k in l for l in caught)]
    fails = []
    if out.returncode == 0:
        fails.append("审计对注入违规仍返回 0（= 恒真，无牙）")
    if len(hit) != len(need):
        fails.append(f"只抓到 {len(hit)}/{len(need)} 类违规：缺 {set(need) - set(hit)}")
    if len(caught) < len(inj):
        fails.append(f"报出 {len(caught)} 条红线 < 注入 {len(inj)} 类")

    # 对照：真复现记录表必须仍然通过（证明审计不是"恒红"）
    real = subprocess.run([sys.executable, AUDIT], capture_output=True, text=True)
    print(f"\n对照：真复现记录表审计退出码 {real.returncode}（期望 **0**）")
    if real.returncode != 0:
        fails.append("真复现记录表被判红 → 审计过严或复现记录表真有红线问题")

    print("\n" + ("❌ 牙齿测试未通过：\n   - " + "\n   - ".join(fails) if fails
                  else f"✅ 审计有牙：{len(inj)} 类注入违规全部被抓、退出非 0；"
                       f"且真复现记录表仍判绿（不是恒红）"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
