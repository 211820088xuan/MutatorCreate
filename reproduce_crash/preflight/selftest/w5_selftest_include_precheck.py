#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W5：**N34 盲点③**（C++ `#include` 的头文件在该 commit 不存在）的检测器自测。

✅ 已知答案（openh264，W5 实测 0/3 的真凶）：
  * Dockerfile 第 26 行 `COPY build.sh decoder_fuzzer.cpp $SRC/` → fuzzer 源码来自 **HEAD**
  * `decoder_fuzzer.cpp:28` `#include "codec_def.h"`
  * build.sh 的 `-I`：`./codec/api/wels`、`./codec/common/inc`、`./codec/console/common/inc`
  * 实测构建日志：`fatal error: 'codec_def.h' file not found` → 三个 -I 目录与仓库根**都没有**它

**为什么只做筛选维度、不接进 ② 的每次构建前预检**：6 个 include × (3 个 -I + 根) = **24 次 HTTP**，
约 10–25s/项目；作为**一次性筛选**划算（对比建镜像 2.3–2.9GB + 探针 10–30min），
但放进每次构建前就会逼近 N24 的教训（预检自身比它省下的构建更贵）。

分三层，前两层是**纯函数**（离线可测，直接读 worktree 里真实的 openh264 文件）：
  `parse_fuzzer_includes(project)` → 被 COPY 进 $SRC 的源码、其 quoted include、build.sh 的 -I 目录
  `include_candidates(inc, inc_dirs)` → 该 include 要依次试的仓库相对路径
  `precheck_includes(...)` → 走 `path_exists_at` 实查（本测试用替身，零网络）

复算：python3 preflight/w5_selftest_include_precheck.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
import build_orchestrator as B       # noqa: E402

FAILS = []
SHA = "9f8c8d19b5db0000000000000000000000000000"
REPO = "https://github.com/cisco/openh264.git"


def ck(cond, msg):
    print(("  ✅ " if cond else "  ❌ ") + msg)
    if not cond:
        FAILS.append(msg)


def main():
    print("═" * 84)
    print("W5 自测：N34 盲点③ —— fuzzer 源码的 #include 在该 commit 是否存在")
    print("═" * 84)

    print("\n[A] 解析层：从真实 openh264 文件里抽出源码 / include / -I 目录")
    info = B.parse_fuzzer_includes("openh264")
    ck("decoder_fuzzer.cpp" in info["sources"],
       f"Dockerfile 的 `COPY … $SRC/` 里认出 fuzzer 源码（实得 {info['sources']}）")
    ck("build.sh" not in info["sources"],
       f"build.sh 不算源码（实得 {info['sources']}）")
    ck("codec_def.h" in info["includes"],
       f"抽到 quoted include `codec_def.h`（实得 {info['includes'][:6]}）")
    ck(all(not i.startswith("<") for i in info["includes"]),
       "只取 `\"…\"` 形式（尖括号是系统头，查不了也不该查）")
    ck(set(info["inc_dirs"]) == {"codec/api/wels", "codec/common/inc", "codec/console/common/inc"},
       f"build.sh 的 -I 目录已归一化掉 `./`（实得 {info['inc_dirs']}）")

    print("\n[B] 候选路径生成（纯函数）")
    c = B.include_candidates("codec_def.h", ["codec/api/wels", "codec/common/inc"])
    ck(c == ["codec/api/wels/codec_def.h", "codec/common/inc/codec_def.h", "codec_def.h"],
       f"每个 -I 目录 + 仓库根，且**根放最后**（实得 {c}）")
    c2 = B.include_candidates("common/foo.h", ["inc"])
    ck(c2 == ["inc/common/foo.h", "common/foo.h"],
       f"include 自带子路径时也正确拼接（实得 {c2}）")
    ck(B.include_candidates("../evil.h", ["inc"]) == [],
       "`../` 逃逸 → 不生成候选（宁漏勿误，与既有预检同口径）")

    print("\n[C] 实查层（替身，零网络）：openh264 的已知答案")
    asked = []

    def absent(repo_url, sha, path, sleep=0.0):
        asked.append(path)
        return False                      # 该 commit 里这些头文件都不存在（= 实测失败形态）
    saved = B.path_exists_at
    B.path_exists_at = absent
    try:
        res = B.precheck_includes("openh264", REPO, SHA, verbose=False)
    finally:
        B.path_exists_at = saved
    ck(res["ok"] is False and "codec_def.h" in res["missing"],
       f"全不存在 → 报缺失且点名 `codec_def.h`（missing={res['missing'][:4]}）")
    ck(res["checked"] == 0 and res["n_checks"] <= res.get("max_checks", 24),
       f"计数自洽：checked={res['checked']}、实际查了 {res['n_checks']} 次（上限 {res.get('max_checks')}）")
    ck(any(p.startswith("codec/api/wels/") for p in asked),
       f"确实按 -I 目录去查了（样例 {asked[:2]}）")

    print("\n[D] 负对照：头文件在某个 -I 目录里找到 → 必须放行（不得误报）")
    def present_in_first_dir(repo_url, sha, path, sleep=0.0):
        return path.startswith("codec/api/wels/")
    B.path_exists_at = present_in_first_dir
    try:
        res2 = B.precheck_includes("openh264", REPO, SHA, verbose=False)
    finally:
        B.path_exists_at = saved
    ck(res2["ok"] is True and not res2["missing"],
       f"在 -I 目录里找到 → 放行（ok={res2['ok']}, missing={res2['missing']}）")
    ck(res2["checked"] > 0, f"且 checked={res2['checked']} 记的是**真查到的**次数")

    print("\n[E] 守卫：无法判定时一律放行（与 N27① 同一契约）")
    B.path_exists_at = lambda repo_url, sha, path, sleep=0.0: None
    try:
        res3 = B.precheck_includes("openh264", REPO, SHA, verbose=False)
        res4 = B.precheck_includes("openh264", REPO, None, verbose=False)
    finally:
        B.path_exists_at = saved
    ck(res3["ok"] is True and res3["undecidable"] > 0,
       f"全部无法判定 → 放行且计入 undecidable（{res3['undecidable']}）")
    ck(res4["ok"] is True and res4.get("reason") == "no_sha",
       f"sha=None → 放行、reason={res4.get('reason')!r}（不能重犯 N27① 的误报）")
    no_src = B.precheck_includes("__no_such_project__", REPO, SHA, verbose=False)
    # ⚠ [W5 修测试期望] 原来只允许 no_sources/no_build_sh/no_includes，漏了 `no_project_dir`
    # —— 项目根本不在 worktree 里时就是这个 reason，它同样是「查不了」的合法一类。
    ck(no_src["ok"] is True and no_src.get("reason") in
       ("no_sources", "no_build_sh", "no_includes", "no_project_dir"),
       f"没有可查的源码/include → 放行且 reason 与「查了没问题」区分（{no_src.get('reason')!r}）")

    print("\n[F] 适用范围（✅ W5 实测：该维度**只对把 fuzzer 源码 COPY 进 $SRC 的项目**有效）")
    # 8 个候选项目全部返回 no_sources/no_includes —— 它们直接编仓库里的 fuzzer，
    # 不像 openh264 那样 `COPY decoder_fuzzer.cpp $SRC/`。这不是缺陷，是**适用边界**，
    # 但筛选表必须显示成「不适用」而不是 `0/1`（后者会被读成"查了、干净" = N29 的陷阱）。
    for proj in ("libxml2", "radare2", "matio"):
        info = B.parse_fuzzer_includes(proj)
        r = B.precheck_includes(proj, REPO, SHA, verbose=False)
        ck(r["ok"] is True and r.get("reason") in ("no_sources", "no_includes", "no_project_dir"),
           f"{proj:<10}→ 不适用（reason={r.get('reason')!r}，sources={info['sources'][:2]}）且**放行**")

    print("\n" + (f"❌ {len(FAILS)} 项未通过：{FAILS}" if FAILS else "✅ 全部通过"))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
