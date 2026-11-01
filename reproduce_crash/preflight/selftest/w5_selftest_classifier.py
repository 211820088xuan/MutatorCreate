#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W5：② 失败分类器 + `_full_log` 的**固化自测**（此前只是内联 heredoc，§6 的「可复算」是空的）。

分类器的顺序即优先级，而顺序里藏着三个**用真实事故换来的**判定，任何一个被无意改动都会
让上游处置走错（重试 vs 跳过 vs 早停），所以必须有护栏：
  * **N16**：`network_fetch` 必须排在 `compile_error` 前 —— 网络失败的日志里也有 `error:`，
    W2 曾把它误判成编译错误（→ 该重试的没重试）。
  * **W2 修 G-2**：`toolchain_drift` 必须排在 `dead_external_url` 前 —— 裸 `404|Not Found`
    曾把「ninja: **not found**」判成死外链。
  * **W3 修**：分类要看**整份日志** —— harfbuzz 首试的 `unknown target` 在前、era-retry 的
    `-Werror` 在后，只读末 400KB 会把主因判成 toolchain_drift。
含**负对照**：把 `FAIL_PATTERNS` 倒序 → N16 那条必须被误判成 compile_error，证明测试有牙。

复算：python3 preflight/w5_selftest_classifier.py
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
import build_orchestrator as B
import run_repro as RR       # noqa: E402
import repro_common as rc    # noqa: E402   ← N54/N57 用例要桩掉 http_get

FAILS = []
N = [0]

# (名称, 合成日志, 期望类别)
CASES = [
    ("N16 网络失败（日志里有 error: 也不许判编译错误）",
     "+ git remote update\nerror: RPC failed; curl 56 GnuTLS recv error (-9)\n"
     "fatal: early EOF\nerror: Could not fetch origin\n", "network_fetch"),
    ("commit 不存在",
     "fatal: 'deadbeefdeadbeef' is not a commit and a branch 'x' cannot be created from it\n",
     "commit_not_found"),
    ("N19 形态① ninja 目标缺失（harfbuzz 6/6）",
     "ninja: error: unknown target 'test/fuzzing/hb-raster-fuzzer'\nninja: build stopped.\n",
     "buildscript_mismatch"),
    ("N23 形态② build.sh 执行的脚本不存在（pcapplusplus 3/3）",
     "projects/pcapplusplus/build.sh: line 22: Tests/Fuzzers/ossfuzz.sh: No such file or directory\n"
     "error: Tests/Fuzzers/ossfuzz.sh: No such file or directory\n", "buildscript_mismatch"),
    ("W2 修 G-2：ninja not found 不是死外链",
     "/usr/bin/sh: 1: ninja: not found\n", "toolchain_drift"),
    ("W3：era-retry 的 -Werror 归工具链漂移",
     "src/hb-ot-layout.cc:123:45: error: this statement may fall through "
     "[-Werror=maybe-uninitialized]\n", "toolchain_drift"),
    ("死外链（要求 HTTP 语境）",
     "ERROR: unable to download https://example.com/x.tar.gz: 404 Not Found\n",
     "dead_external_url"),
    ("Dockerfile 缺包", "E: Unable to locate package libfoo-dev\n", "dockerfile_drift"),
    ("超时", "# TIMEOUT after 3600s\n", "timeout"),
    ("真编译错误", "src/blosc2.c:120:5: error: 'ctx' undeclared\nninja: build stopped.\n",
     "compile_error"),
    ("era_retry 只是过程日志，优先级最低（W3 line 747 的过滤）",
     "INFO: Retrying on earlier OSS-Fuzz commit\nsrc/foo.c:1:1: error: x undeclared\n",
     "compile_error"),
    # [W5 openh264 实测] **首试**真因 = fuzzer 源码 include 了老 commit 里不存在的头文件
    # （N19 同族，但形态是 C++ `#include` → 预检的路径存在性检查看不到，是第三个盲点）；
    # 之后 era-retry 又因老 Dockerfile 要 `libstdc++-5-dev`（focal 已移除）而失败。
    # 原分类器报 `dockerfile_drift` —— **描述第二阶段、掩盖首试真因**（照它去查会完全跑偏）。
    ("W5 openh264：首试真因（头文件在该 commit 不存在）必须胜过 era-retry 的 Dockerfile 报错",
     "Step 2/9 : RUN apt-get install -y libstdc++-9-dev\n"
     "/src/decoder_fuzzer.cpp:28:10: fatal error: 'codec_def.h' file not found\n"
     "ERROR:helper:Building fuzzers failed.\n"
     "INFO:root:Build failed. Retrying on earlier OSS-Fuzz commit 456eded09c7f.\n"
     "Step 3/6 : RUN apt-get install -y libstdc++-5-dev nasm\n"
     "E: Package 'libstdc++-5-dev' has no installation candidate\n",
     "buildscript_mismatch"),
    ("首试段无错、只有 era 段有错 → 仍要能从 era 段分类（新逻辑不得把它变成 unclassified）",
     "INFO:root:Build failed. Retrying on earlier OSS-Fuzz commit abc123.\n"
     "E: Unable to locate package libfoo-dev\n",
     "dockerfile_drift"),
    ("空日志", "", "unknown_no_output"),
    ("无法归类", "something odd happened, no known marker\n", "unclassified"),
]
# openh264 那条在 CASES 里的下标（[A2] 节要用它验 detail）
# ⚠ [W5 修] 原来硬编码 13 → 实际指到「空日志」那条，于是 detail 恒为 None、
#    断言以**错误的理由**失败。改为按名字定位，避免下标漂移。
CASE_OH264 = next(i for i, (nm, _t, _w) in enumerate(CASES) if nm.startswith("W5 openh264"))


def ck(cond, msg):
    N[0] += 1
    print(("  ✅ " if cond else "  ❌ ") + msg)
    if not cond:
        FAILS.append(msg)


def main():
    print("═" * 72)
    print("W5 ② 自测：失败分类器（顺序即优先级）+ _full_log 不截断")
    print("═" * 72)
    print("\n[A] 13 个类别判定")
    for name, text, want in CASES:
        got, line = B.classify_build_failure(text)
        ck(got == want, f"{name} → {got}" + ("" if got == want else f"（期望 {want}）"))

    print("\n[A2] detail 也要指向**首试真因**（N28③：抓错行会把人引向完全错误的方向）")
    _c, detail = B.classify_build_failure(CASES[CASE_OH264][1])
    ck(detail is not None and "codec_def.h" in detail,
       f"detail 应含首试的头文件名，实为 {str(detail)[:72]!r}")
    ck(not (detail or "").startswith("E: Package"),
       f"detail 不应是 era 段的 apt 报错（实为 {str(detail)[:60]!r}）")

    print("\n[B] W3 修：整份日志都要看（主因在前、噪音在后）")
    with tempfile.TemporaryDirectory() as td:
        lp = os.path.join(td, "big.log")
        noise = "".join(f"[{i}] compiling object {i}.o\n" for i in range(30000))  # >400KB
        with open(lp, "w", encoding="utf-8") as f:
            f.write("ninja: error: unknown target 'test/fuzzing/hb-raster-fuzzer'\n"
                    + noise + "error: something [-Werror]\n")
        full = B._full_log(lp)
        ck(len(full) > 400_000, f"日志 {len(full):,} B（>400KB，W2 的旧 limit 会截掉开头）")
        ck("unknown target" in full, "**开头**的首试主因仍在读到的内容里")
        got, _ = B.classify_build_failure(full)
        ck(got == "buildscript_mismatch",
           f"大日志分类 = {got}（harfbuzz 实测形态：主因 buildscript_mismatch，不是 toolchain_drift）")

    print("\n[C] 负对照：把 FAIL_PATTERNS 倒序 → N16 那条必须被误判（证明测试有牙）")
    saved = B.FAIL_PATTERNS
    try:
        B.FAIL_PATTERNS = list(reversed(saved))
        got, _ = B.classify_build_failure(CASES[0][1])
        ck(got == "compile_error",
           f"倒序后网络失败被判成 {got} → 说明「顺序即优先级」这条真被本套自测守住")
    finally:
        B.FAIL_PATTERNS = saved
    got, _ = B.classify_build_failure(CASES[0][1])
    ck(got == "network_fetch", f"还原后仍是 {got}（monkeypatch 已复位，未污染真实模块）")

    
    # ══════════ [W5 N43] commit_not_found 的漏识别形态 + 它不该计入项目级早停 ══════════
    print("\n[N43] `does not exist in current branch` 必须归 commit_not_found，且**不计入早停**")
    _N43 = """+ git checkout abc
    Traceback (most recent call last):
      File "infra/build_specified_commit.py", line 100, in build_fuzzers
        raise ValueError('Commit %s does not exist in current branch' % commit)
    ValueError: Commit b7dc3513d68e23e88ab8bb347a17ec188137c96b does not exist in current branch"""
    _c = B.classify_build_failure(_N43)[0]
    ck(_c == "commit_not_found",
       f"✅ 实测 libavc 的形态 → `{_c}`（修之前落到 `compile_error`，触发早停**误伤 33 条**）")
    ck(_N43 and "commit_not_found" not in RR.DETERMINISTIC_FAIL,
       f"`commit_not_found` **不在** DETERMINISTIC_FAIL（它取决于「哪个 commit」，非项目级必然）→ {RR.DETERMINISTIC_FAIL}")
    # 负对照：真 compile_error 仍须计入早停（否则早停彻底失效）
    _ce = "src/x.c:12:5: error: use of undeclared identifier 'foo'\nninja: build stopped: subcommand failed."
    ck(B.classify_build_failure(_ce)[0] == "compile_error"
       and "compile_error" in RR.DETERMINISTIC_FAIL,
       "**负对照**：真 compile_error 仍归类正确且**仍计入**早停（早停没被这次修正搞失效）")
    # 负对照：buildscript_mismatch / dockerfile_drift 也仍在
    for _k in ("buildscript_mismatch", "dockerfile_drift", "toolchain_drift"):
        ck(_k in RR.DETERMINISTIC_FAIL, f"**负对照**：`{_k}` 仍在 DETERMINISTIC_FAIL")
    # 另一形态：ValueError: Commit <sha>（无 "does not exist" 那句时也要认）
    ck(B.classify_build_failure("ValueError: Commit 2351c638c0c3273a1b7fa8bf56761d6b8d66e769")[0]
       == "commit_not_found", "只有 `ValueError: Commit <sha>` 一行时也能认出")

    # ══════════ [W5 N54–N57] 解析器回显 bug 一族（一个 bug 造出两个假结论）══════════
    # ✅ 实测链：invent.kde.org（自建 GitLab）的 `.patch` 端点不认 `<sha>~d` →
    #   旧代码 `return {"sha": pc.get("sha") or sha}` **把输入原样回显**、`error=None` →
    #   ② 以为解析成功、把 `<sha>~3` 传给 infra → infra `checkout_commit` 的
    #   `get_current_commit() != commit`（完整 SHA vs 字面量）**必然**不等 → RuntimeError →
    #   分类器标 `compile_error` → N43 早停**封掉整个项目**（kimageformats 探针 0/3、2 条被跳过），
    #   同时离线预检拿假 SHA 报「14/14 放行」→ **假淘汰 + 假放行**。
    print("\n[N56] `Error checking out commit` 必须归 commit_not_found（不计入早停）")
    _N56 = """Traceback (most recent call last):
      File "infra/repo_manager.py", line 227, in checkout_commit
        raise RuntimeError('Error checking out commit %s' % commit)
    RuntimeError: Error checking out commit 780f3428253bff4b029736fa9f195ca5938203bc~3"""
    _c6 = B.classify_build_failure(_N56)[0]
    ck(_c6 == "commit_not_found",
       f"✅ 实测 kimageformats 的形态 → `{_c6}`（修之前落到 `compile_error` → 早停封项目）")
    ck(_c6 not in RR.DETERMINISTIC_FAIL,
       f"`{_c6}` **不在** DETERMINISTIC_FAIL → 不会因它封整个项目")

    print("\n[N54] 解析失败时**绝不得**把输入回显成 sha（静默失败的源头）")
    ck(bool(B.SHA_RE.match("780f3428253bff4b029736fa9f195ca5938203bc"))
       and not B.SHA_RE.match("780f3428253bff4b029736fa9f195ca5938203bc~3"),
       "SHA_RE 认纯 SHA、**不认**带 `~d` 的相对修订式")
    _orig = rc.http_get
    try:
        # 造一个「HTTP 200 但 patch 里没有 sha」的响应 → 旧代码会回显输入
        rc.http_get = lambda *a, **k: ("From nobody Mon Sep 16 00:00:00 2026\nSubject: x\n", 200)
        _r = B.resolve_commit_meta("https://github.com/foo/bar", "deadbeefdeadbeef~3")
        ck(not (_r or {}).get("sha"),
           f"解析不出 sha 时 `sha=None`（旧代码会返回 `'deadbeefdeadbeef~3'`）→ {_r}")
        ck(str((_r or {}).get("error") or "").startswith("unresolved_sha"),
           f"且 error 明确标 `unresolved_sha:…` → {(_r or {}).get('error')}")
    finally:
        rc.http_get = _orig

    print("\n[N55] 预检：输入非法 ≠ 无法判定（不得放行垃圾 sha）")
    _p1 = B.precheck_buildscript("kimageformats", "https://invent.kde.org/frameworks/kimageformats.git",
                                 "780f3428253bff4b029736fa9f195ca5938203bc~1", verbose=False)
    ck(_p1["ok"] is False and str(_p1.get("reason", "")).startswith("bad_rev"),
       f"非纯 SHA → ok=False, reason={_p1.get('reason')}（旧代码返回 ok=True → 假放行）")

    print("\n[N57] GitLab API 的 parent_ids 解析（离线：桩掉 http_get）")
    _gl = ('{"id":"297ed9a2fe339bfe36916b9fce628c3242e5be0f",'
           '"parent_ids":["55b4077f2c12a424aaaaaaaaaaaaaaaaaaaa"],'
           '"authored_date":"2021-04-30T00:07:21.000+02:00","title":"x"}')
    try:
        rc.http_get = lambda *a, **k: (_gl, 200)
        _g = B.gitlab_commit("invent.kde.org", "frameworks/kimageformats", "780f3428")
        ck(_g.get("sha") == "297ed9a2fe339bfe36916b9fce628c3242e5be0f"
           and _g.get("parents") == ["55b4077f2c12a424aaaaaaaaaaaaaaaaaaaa"]
           and not _g.get("error"),
           f"gitlab_commit 解析出 sha/parents/date → {str(_g)[:96]}")
        rc.http_get = lambda *a, **k: ('{"message":"404 Commit Not Found"}', 200)
        _g2 = B.gitlab_commit("invent.kde.org", "frameworks/kimageformats", "nope")
        ck(not _g2.get("sha") and _g2.get("error"),
           f"API 返回错误体时不得伪造 sha → {_g2.get('error')}")
    finally:
        rc.http_get = _orig

    # ══════════ [W5 N58] toolchain_drift 的正则过宽 → 命中**成功行/路径名/apt 行** ══════════
    # ✅ 实测三个假阳性来源（都取自真实构建日志）：
    #   ① autotools 的成功探针 `checking if the -Werror option is usable... yes`（几乎所有项目都打）
    #   ② Qt 的**路径名** `-- Installing: /usr/mkspecs/features/unsupported/testserver.prf`
    #   ③ **apt 安装行**里的包名 `ninja-build`（pcapplusplus 就是这么被误判成 toolchain_drift 的）
    # 而 kimageformats 的真正死因是 `No Qt6 qtpaths executable found`（镜像烘的是当前 ECM/Qt、
    # 要建的是 2021 年 commit；era-retry 救不了，因为 prepare_build.sh 来自 master 未被钉版），
    # 旧分类器却拿 Qt configure 的**非致命探针** `unknown argument: '-mavx512er'` 当证据 → 记错原因。
    print("\n[N58] toolchain_drift 不得被成功行/路径名/apt 行触发")
    for _benign, _why in (
        ("configure: checking if the -Werror option is usable... yes", "**成功探针行**（裸 -Werror）"),
        ("-- Installing: /usr/mkspecs/features/unsupported/testserver.prf", "**Qt 路径名**（裸 unsupported）"),
        ("+ apt-get install -y ninja-build cmake\nSuccessfully installed ninja-build",
         "**apt 安装行**（裸 ninja-build）"),
    ):
        _c8 = B.classify_build_failure(_benign + "\nninja: build stopped: subcommand failed.")[0]
        ck(_c8 != "toolchain_drift", f"{_why} → `{_c8}`（不得是 toolchain_drift）")
    # 真死因要有自己的一类，且计入早停（镜像固定 → 每个 commit 都同样失败）
    _kif = """-- Configuring incomplete, errors occurred!
CMake Error at /usr/local/share/ECM/modules/ECMQueryQt.cmake:84 (message):
  No Qt6 qtpaths executable found.  Can't check QT_INSTALL_PREFIX as required
ERROR:helper:Building fuzzers failed."""
    _c9 = B.classify_build_failure(_kif)[0]
    ck(_c9 == "era_dep_drift", f"✅ kimageformats 的真实死因 → `{_c9}`（旧代码给 `toolchain_drift`）")
    ck("era_dep_drift" in RR.DETERMINISTIC_FAIL,
       "`era_dep_drift` **在** DETERMINISTIC_FAIL（镜像固定 → 项目级确定性）")
    # 负对照①：`error: … -Werror` 同一行的形态仍须归 toolchain_drift（收紧不能把它弄丢）
    _osc = ("src/libopensc/card-openpgp.c:1234:5: error: variable 'octets_left' is uninitialized "
            "when used here [-Werror,-Wuninitialized]\nmake: *** [Makefile:17] Error 1")
    ck(B.classify_build_failure(_osc)[0] == "toolchain_drift",
       "**负对照①**：`error: … -Werror` 同行的真形态仍归 toolchain_drift")
    # 负对照②：**行为不变**才是重点。opensc 真实日志的**首试段**真因是缺依赖
    # （`configure: error: OpenPACE linkage required, but no OpenPACE was found`，`-Werror` 那行在
    # era 段里；分类器按 N28③ 优先用首试段）→ 收紧后标签由 toolchain_drift 变 compile_error，
    # 但**两者都在 DETERMINISTIC_FAIL 里，早停行为完全一致**。断言行为、不断言标签。
    _osc2 = "configure: error: OpenPACE linkage required, but no OpenPACE was found"
    _c10 = B.classify_build_failure(_osc2)[0]
    ck(_c10 in RR.DETERMINISTIC_FAIL,
       f"**负对照②**：opensc 首试段真因 → `{_c10}`，仍在 DETERMINISTIC_FAIL（**行为不变**）")

    print("\n" + (f"❌ {len(FAILS)} 项未通过：{FAILS}" if FAILS
                  else f"✅ 全部通过（{N[0]} 项）"))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
