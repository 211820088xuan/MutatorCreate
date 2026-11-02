#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s5.py —— 阶段5（算子生成）的统一入口

原来 stage5 有 9 个子步、9 个脚本，命令行要敲 9 次。现在收成 **4 个阶段**：

    prepare   5.0 抓源码/harness/种子   + 5.1 生成 worklist
    audit     5.2 agent 静态审计（LLM，可选且较贵）
    analyze   5.3 输入攻击面/证据链     + 5.4 候选合并     + 5.5 每个特征过 6 阶段
    build     5.6 声明式 plan           + 5.7 生成 C       + 5.8 V1–V4 门禁

底层脚本**没有合并**，仍然各管一件事、可单独调用；本文件只负责按顺序驱动它们，
并在某一步失败时立刻停下。这样"想跑全流程"只需要一条命令，"想调某一步"仍然可以单独跑。

用法
    python3 s5.py prepare --osv ARVO-42494732
    python3 s5.py audit   --osv ARVO-42494732 --all-chunks
    python3 s5.py analyze --osv ARVO-42494732
    python3 s5.py build   --osv ARVO-42494732
    python3 s5.py all     --osv ARVO-42494732            # prepare → analyze → build
    python3 s5.py all     --osv ARVO-42494732 --with-audit
    python3 s5.py list                                    # 看阶段与底层脚本的对应

设计约定
    · 每个阶段内部按顺序执行，任一步非零退出 → 整个阶段中止（不吞错）。
    · `all` 默认**不跑 audit**：审计是 LLM 调用、比较贵，而且可以离线补齐；
      要跑就显式加 `--with-audit`。
    · 底层脚本的产物路径不变（都在 projects/<OSV>/v2/），所以单独跑与用本入口跑结果一致。
"""
from __future__ import annotations

import argparse
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# 阶段 → [(底层脚本, 说明)]
STAGES = {
    "prepare": [
        ("s5_fetch_source", "5.0 抓固定版本源码 + harness + 种子"),
        ("s5a_scan_target", "5.1 调用图 depth≤2 → audit_worklist.json"),
    ],
    "audit": [
        ("s5b_audit_agent", "5.2 agent 静态审计（每批一个 agent）"),
    ],
    "analyze": [
        ("s5_target_surface", "5.3 输入攻击面 + 六步证据链"),
        ("s5_candidate_findings", "5.4 多路候选合并 / 证据核验 / 去重"),
        ("s5f_feature_pipeline", "5.5 每个特征走同一套 6 阶段"),
    ],
    "build": [
        ("s5_mutation_plan", "5.6 声明式 mutation plan（权重在这里定）"),
        ("s5_generate_mutator_v2", "5.7 从 ready plan 生成 C（含行为门禁）"),
        ("s5_verify_mutator_v2", "5.8 V1 schema / V2 evidence / V3 code / V4 behavior"),
    ],
}
ORDER = ["prepare", "audit", "analyze", "build"]


def run(mod_name: str, argv: list[str]) -> int:
    """按给定 argv 调用底层脚本的 main()，返回退出码。"""
    mod = importlib.import_module(mod_name)
    old = sys.argv
    sys.argv = [f"{mod_name}.py"] + argv
    try:
        rc = mod.main()
    except SystemExit as e:
        code = e.code
        rc = code if isinstance(code, int) else (0 if code is None else 1)
    except Exception as e:                                  # noqa: BLE001
        # 底层脚本抛异常（例如 LLM finish_reason=length）时，不要把 traceback
        # 甩给用户；打一条清楚的说明并按失败处理，让阶段立刻停下。
        print(f"\n[stage5] {mod_name}.py 抛出 {type(e).__name__}: {e}", file=sys.stderr)
        rc = 1
    finally:
        sys.argv = old
    return rc or 0


def argv_for(mod_name: str, osv: str, args) -> list[str]:
    """给每个底层脚本拼它自己的参数（各脚本接受的选项不同）。"""
    if mod_name == "s5_fetch_source":
        return [osv]                                   # 位置参数
    if mod_name == "s5a_scan_target":
        return ["--osv", osv, "--depth", str(args.depth)]
    if mod_name == "s5b_audit_agent":
        a = ["--osv", osv]
        if args.all_chunks:
            a.append("--all-chunks")
        if args.model:
            a += ["--model", args.model]
        if args.max_turns:
            a += ["--max-turns", str(args.max_turns)]
        return a
    if mod_name in ("s5_target_surface", "s5_candidate_findings"):
        return ["--osv", osv]
    if mod_name == "s5f_feature_pipeline":
        a = ["--osv", osv, "--type", args.type, "--default-weight",
             str(args.default_weight)]
        a += ["--feature", args.feature] if args.feature else ["--all"]
        return a
    if mod_name == "s5_mutation_plan":
        return ["--osv", osv, "--default-weight", str(args.default_weight)]
    if mod_name == "s5_generate_mutator_v2":
        a = ["--osv", osv, "--retries", str(args.retries)]
        if args.model:
            a += ["--model", args.model]
        return a
    if mod_name == "s5_verify_mutator_v2":
        return ["--osv", osv] + (["--binary", args.binary] if args.binary else [])
    raise SystemExit(f"未知脚本 {mod_name}")


def run_stage(stage: str, osv: str, args) -> int:
    steps = STAGES[stage]
    print(f"\n{'='*72}\n== stage5 · {stage}（{len(steps)} 步）\n{'='*72}")
    for i, (mod, desc) in enumerate(steps, 1):
        print(f"\n--- [{i}/{len(steps)}] {desc}  ({mod}.py)")
        rc = run(mod, argv_for(mod, osv, args))
        if rc != 0:
            print(f"\n[stage5] {stage} 在 {mod}.py 中止（退出码 {rc}）", file=sys.stderr)
            return rc
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="阶段5 统一入口：prepare / audit / analyze / build / all / list",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join(f"  {s:<9} " + " → ".join(m for m, _ in STAGES[s])
                         for s in ORDER))
    ap.add_argument("stage", choices=ORDER + ["all", "list"])
    ap.add_argument("--osv", default=None, help="崩溃 id，如 ARVO-42494732")
    ap.add_argument("--type", default="uaf", help="崩溃类型目录名（默认 uaf）")
    ap.add_argument("--depth", type=int, default=2, help="worklist 的调用图深度")
    ap.add_argument("--default-weight", type=float, default=0.5,
                    help="default 变异占比（默认 0.5）")
    ap.add_argument("--feature", default=None, help="feature_pipeline 只跑这一个特征")
    ap.add_argument("--with-audit", action="store_true",
                    help="all 时也跑 audit（LLM，较贵）")
    ap.add_argument("--all-chunks", action="store_true", help="audit 跑全部批次")
    ap.add_argument("--model", default=None)
    ap.add_argument("--max-turns", type=int, default=None)
    ap.add_argument("--binary", default=None, help="verify 的 V4 行为门禁用")
    ap.add_argument("--retries", type=int, default=3,
                    help="build 里 LLM 生成的重试次数（默认 3）")
    args = ap.parse_args()

    if args.stage == "list":
        for s in ORDER:
            print(f"{s}:")
            for m, d in STAGES[s]:
                print(f"    {m:<26} {d}")
        return 0

    if not args.osv:
        ap.error("需要 --osv（例如 ARVO-42494732）")

    if args.stage == "all":
        for s in ORDER:
            if s == "audit" and not args.with_audit:
                print("\n（跳过 audit：需要时加 --with-audit）")
                continue
            rc = run_stage(s, args.osv, args)
            if rc != 0:
                return rc
        print("\n[stage5] all 完成")
        return 0

    return run_stage(args.stage, args.osv, args)


if __name__ == "__main__":
    sys.exit(main())
