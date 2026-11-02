#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s5_1_main.py —— 阶段5（算子生成）的入口与 CLI 调度

实现按 4 个阶段分散在四个文件里，本文件只做调度：

    s5_2_prepare.py   5.0 fetch + 5.1 worklist
    s5_3_audit.py     5.2 agent 审计 + 5.2b 机械规则 + 5.2c 跨函数 + 5.2d 特征审计
    s5_4_analyze.py   5.3 证据链 + 5.4 候选合并 + 5.5 每特征 6 阶段
    s5_5_build.py     5.6 plan + 5.7 生成 C + 5.8 V1–V4 门禁
    s5_6_lib.py       共享底座（行级 CFG + agent 循环）

用法
    python3 s5_1_main.py prepare --osv ARVO-42494732
    python3 s5_1_main.py audit   --osv ARVO-42494732 --all-chunks
    python3 s5_1_main.py analyze --osv ARVO-42494732
    python3 s5_1_main.py build   --osv ARVO-42494732
    python3 s5_1_main.py all     --osv ARVO-42494732            # 默认跳过 audit
    python3 s5_1_main.py all     --osv ARVO-42494732 --with-audit
    python3 s5_1_main.py list

    # 单步直通（参数原样转发给该步自己的 argparse）
    python3 s5_1_main.py fetch   ARVO-42494732
    python3 s5_1_main.py worklist --osv X --depth 3
    python3 s5_1_main.py surface  --osv X --dry-run
    python3 s5_1_main.py generate --plan p.json --out dir
    python3 s5_1_main.py verify   --osv X --binary <bin>
    python3 s5_1_main.py mech     --osv X
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import s5_2_prepare as PR        # noqa: E402
import s5_3_audit as AU          # noqa: E402
import s5_4_analyze as AN        # noqa: E402
import s5_5_build as BU          # noqa: E402

STAGES = ("prepare", "audit", "analyze", "build")
PASSTHROUGH = ("fetch", "worklist", "surface", "findings", "features",
               "plan", "generate", "verify", "mech", "interproc", "feat-audit")

# 单步直通 → 具体的函数
STEP_FN = {
    "fetch":     PR.main_fetch,
    "worklist":  PR.main_worklist,
    "surface":   AN.main_surface,
    "findings":  AN.main_findings,
    "features":  AN.main_features,
    "plan":      BU.main_plan,
    "generate":  BU.main_generate,
    "verify":    BU.main_verify,
    "mech":      AU.main_mech,
    "interproc": AU.main_interproc,
    "feat-audit": AU.main_feat_audit,
}


def _run(fn, argv):
    """按 argv 调某个阶段函数，返回退出码（异常转成非零，不打 traceback）。"""
    old = sys.argv
    sys.argv = [getattr(fn, "__name__", "stage")] + list(argv)
    try:
        rc = fn()
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    except Exception as e:                                      # noqa: BLE001
        print(f"\n[stage5] {getattr(fn, '__name__', 'stage')} 抛出 "
              f"{type(e).__name__}: {e}", file=sys.stderr)
        rc = 1
    finally:
        sys.argv = old
    return rc or 0


def main():
    ap = argparse.ArgumentParser(
        description="阶段5 统一入口：prepare / audit / analyze / build / all / list",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=list(STAGES) + ["all", "list"] + list(PASSTHROUGH))
    ap.add_argument("--osv", default=None)
    ap.add_argument("--type", default="uaf")
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--default-weight", type=float, default=0.5)
    ap.add_argument("--feature", default=None)
    ap.add_argument("--with-audit", action="store_true")
    ap.add_argument("--all-chunks", action="store_true")
    ap.add_argument("--chunk", action="append", type=int)
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--model", default=None)
    ap.add_argument("--max-turns", type=int, default=None)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--binary", default=None)
    args, extras = ap.parse_known_args()
    osv = args.osv

    # ── 单步直通 ──
    if args.stage in PASSTHROUGH:
        fn = STEP_FN[args.stage]
        argv = list(extras)
        if args.stage == "fetch":
            argv = ([osv] if osv else []) + argv          # 位置参数
        elif osv and "--osv" not in argv:
            argv = ["--osv", osv] + argv                  # 入口吃掉了 --osv，补回
        return _run(fn, argv)

    if args.stage == "list":
        print("prepare: 5.0 fetch + 5.1 worklist                        (s5_2_prepare.py)")
        print("audit:   5.2 审计 + 5.2b 机械规则 + 5.2c 跨函数 + 5.2d 特征审计  (s5_3_audit.py)")
        print("analyze: 5.3 证据链 + 5.4 候选 + 5.5 每特征 6 阶段          (s5_4_analyze.py)")
        print("build:   5.6 plan + 5.7 生成 C + 5.8 V1-V4 门禁            (s5_5_build.py)")
        print("单步直通: " + " / ".join(PASSTHROUGH))
        return 0

    if not osv:
        ap.error("需要 --osv（例如 ARVO-42494732）")

    # ── 四个阶段 ──
    def run_prepare():
        return PR.main(["--osv", osv, "--depth", str(args.depth)])

    def run_audit():
        av = ["--osv", osv]
        if args.all_chunks:
            av.append("--all-chunks")
        av += sum((["--chunk", str(c)] for c in args.chunk or []), [])
        if args.merge:
            av.append("--merge")
        if args.model:
            av += ["--model", args.model]
        if args.max_turns:
            av += ["--max-turns", str(args.max_turns)]
        return AU.main(av)

    def run_analyze():
        av = ["--osv", osv, "--type", args.type,
              "--default-weight", str(args.default_weight)]
        if args.feature:
            av += ["--feature", args.feature]
        return AN.main(av)

    def run_build():
        av = ["--osv", osv, "--default-weight", str(args.default_weight),
              "--retries", str(args.retries)]
        if args.model:
            av += ["--model", args.model]
        if args.binary:
            av += ["--binary", args.binary]
        return BU.main(av)

    fns = {"prepare": run_prepare, "audit": run_audit,
           "analyze": run_analyze, "build": run_build}

    if args.stage == "all":
        for name in STAGES:
            if name == "audit" and not args.with_audit:
                print("\n（跳过 audit：需要时加 --with-audit）")
                continue
            print(f"\n{'='*70}\n== stage5 · {name}\n{'='*70}")
            rc = fns[name]()
            if rc:
                return rc
        print("\n[stage5] all 完成")
        return 0

    return fns[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
