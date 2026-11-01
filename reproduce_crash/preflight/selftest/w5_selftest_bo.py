#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W5：② `build_orchestrator` 的两项自测 —— **不碰 docker、不碰真实数据**。

T1 日志轮转（新发现 N25 的修法）
   `run_cmd` 用 `open(log_path,"w")` 无条件截断，而日志名只由 `project_san_commit` 决定
   → 重跑同一 commit 会**静默覆盖上一次的失败日志**。
   ✅ 实测事故：`c-blosc2_address_9ba29ef1584b.log` 现为 2026-09-10 18:00 那次**成功**构建，
   而 DELIVERY §4.5 引它作 N16（`GnuTLS recv error`）的证据 → 证据已被销毁。
   修法：写之前若目标已存在则**改名保留**（加 UTC 时间戳后缀），永不销毁。

T2 N16 重试接线（离线注入）
   重试块在 `build_pinned()` 内、docker 边界就是 `run_cmd` → 替掉 `run_cmd` 即可跑**真接线**。
   为什么要离线：该 commit 现在**能建成功**（build_records 同 key 两条：fail_pinned → ok），
   而网络失败是瞬态的 → 真实重跑几乎必然首试即过，销不掉这条账。
   含**负对照**证明测试有牙：把分类器改成恒返回 `compile_error`，重试必须不再触发。

复算：python3 preflight/w5_selftest_bo.py
"""
import argparse
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
import build_orchestrator as B       # noqa: E402

FAILS = []
NET_LOG = ("+ git remote update\nerror: RPC failed; curl 56 GnuTLS recv error (-9)\n"
           "fatal: early EOF\nerror: Could not fetch origin\n")
CC_LOG = ("src/blosc2.c:120:5: error: 'blosc2_ctx_s' was not declared in this scope\n"
          "ninja: build stopped: subcommand failed.\n")


def ck(cond, msg):
    print(("  ✅ " if cond else "  ❌ ") + msg)
    if not cond:
        FAILS.append(msg)


# ══════════════════════════ T1 日志轮转 ══════════════════════════
def t1_rotate():
    print("\n[T1] 日志轮转：重跑同 commit 不得销毁上一次的日志")
    with tempfile.TemporaryDirectory() as td:
        lp = os.path.join(td, "build", "proj_address_deadbeef0000.log")
        # (a) 目标不存在 → 不轮转、返回 None
        ck(B.rotate_existing_log(lp) is None, "目标日志不存在 → 返回 None（不产生空轮转文件）")
        # (b) 目标存在 → 原内容被改名保留，lp 让位给新一次
        os.makedirs(os.path.dirname(lp), exist_ok=True)
        with open(lp, "w", encoding="utf-8") as f:
            f.write("FIRST-FAILURE-EVIDENCE\n")
        rot = B.rotate_existing_log(lp)
        ck(bool(rot) and os.path.isfile(rot), f"已存在 → 返回轮转后路径 {rot and os.path.basename(rot)}")
        ck(rot != lp and os.path.exists(rot)
           and "FIRST-FAILURE-EVIDENCE" in open(rot, encoding="utf-8").read(),
           "轮转文件里仍是**上一次**的内容（证据未销毁）")
        ck(not os.path.exists(lp), "原路径已让位（新一次构建将重新创建它）")
        # (c) 同名同秒再轮转一次 → 不得互相覆盖
        with open(lp, "w", encoding="utf-8") as f:
            f.write("SECOND\n")
        rot2 = B.rotate_existing_log(lp)
        ck(rot2 != rot and os.path.isfile(rot) and os.path.isfile(rot2),
           "同一秒内第二次轮转不覆盖第一个（后缀去重）")

        # (d) 端到端：run_cmd 跑两次同一路径 → 第一次的内容仍可找到
        real_run = B.run_cmd
        B.LOGS = td
        rc1, _, _ = real_run([sys.executable, "-c", "print('RUN-ONE')"], td, lp)
        rc2, _, _ = real_run([sys.executable, "-c", "print('RUN-TWO')"], td, lp)
        ck(rc1 == 0 and rc2 == 0, "run_cmd 两次都 rc=0（轮转没有打断正常写入）")
        cur = open(lp, encoding="utf-8").read()
        rots = [os.path.join(td, "build", f) for f in os.listdir(os.path.join(td, "build"))
                if f.startswith("proj_address_deadbeef0000.log.")]
        kept = "".join(open(p, encoding="utf-8").read() for p in rots)
        ck("RUN-TWO" in cur, "当前日志 = 最新一次")
        ck("RUN-ONE" in kept, "**上一次**的日志被保留在轮转文件里（N25 修复生效）")


# ══════════════════ T1b N40：轮转推广到 reproduce 侧 ══════════════════
def t1b_rotate_reproduce():
    """N25 只修了 build 侧；③ 的 `run_once` 一直 `open(…,"w")` 无条件截断。

    ✅ 实证：113 条跑过多轮的 crash 里 **110 条盘上只剩 1 份** reproduce 日志
    （`logs/build/` 有 71 个轮转文件，`logs/reproduce/` 有 **0** 个）。
    """
    print("\n[T1b] N40：③ reproduce 日志也必须轮转（跨轮次不得覆盖上一次的崩溃报告）")
    import repro_common as RC
    import repro_runner as R

    ck(B.rotate_existing_log is RC.rotate_existing_log,
       "② 用的是 `repro_common` 里的**同一份**实现（别名，不是第二份拷贝 → 不会分叉）")
    ck(R.rc.rotate_existing_log is RC.rotate_existing_log, "③ 也指向同一份实现")

    with tempfile.TemporaryDirectory() as td:
        lp = os.path.join(td, "reproduce", "OSV-2099-1.log")

        class A:                                     # run_once 只读这几个字段
            timeout = 25
            rss_limit_mb = 2560
            run_timeout = 5

        class FakeP:
            def __init__(self, tag):
                self.returncode, self.stdout, self.stderr = 1, "", f"ASAN-{tag}"

        calls = {"n": 0}
        real_run = R.subprocess.run

        def fake_run(argv, **kw):
            calls["n"] += 1
            return FakeP("RUN-ONE" if calls["n"] == 1 else "RUN-TWO")

        R.subprocess.run = fake_run
        try:
            r1 = R.run_once(td, "fuzz", "/tc", "address", A(), lp)
            r2 = R.run_once(td, "fuzz", "/tc", "address", A(), lp)
        finally:
            R.subprocess.run = real_run

        ck(calls["n"] == 2, "run_once 跑了两次（替身生效，没碰 docker）")
        cur = open(lp, encoding="utf-8").read()
        rots = [os.path.join(td, "reproduce", f) for f in os.listdir(os.path.join(td, "reproduce"))
                if f.startswith("OSV-2099-1.log.")]
        kept = "".join(open(x, encoding="utf-8").read() for x in rots)
        ck("RUN-TWO" in cur, "当前日志 = 最新一次")
        ck(len(rots) == 1, f"产生了 **1 个**轮转文件（实得 {len(rots)}）")
        ck("RUN-ONE" in kept, "**上一次的崩溃报告被保留**（N40 修复生效；修之前它会被截断掉）")
        ck(r1["log_path"] == r2["log_path"] == lp,
           "两次返回的 log_path 都是原名 → 复现记录表 `raw_log_path` 的语义不变（旧行仍指原名）")


# ══════════════════════════ T2 N16 重试接线 ══════════════════════════
class FakeRun:
    """替掉 docker 边界：按脚本返回 (rc, secs, tail)，并把合成日志真写到 lp。"""

    def __init__(self, script):
        self.script = list(script)      # [(rc, log_text), ...]
        self.calls = []

    def __call__(self, cmd, cwd, log_path, env=None, timeout=3600, tee=False):
        i = min(len(self.calls), len(self.script) - 1)
        rc_, text = self.script[i]
        self.calls.append(log_path)
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("# cmd: fake\n\n" + text)
        return rc_, 1.0, text[-200:]


def _pinned(fake, retry_network=True, classify=None):
    """在临时目录里跑真的 `build_pinned()`，只替 docker/归档/状态三类边界。"""
    td = tempfile.mkdtemp()
    saved = (B.run_cmd, B.LOGS, B.restore_projects, B.archive_build, B._learn_era,
             B.classify_build_failure)
    B.run_cmd, B.LOGS = fake, td
    B.restore_projects = lambda p: True
    B.archive_build = lambda *a, **k: {"ok": True, "binary_dir": os.path.join(td, "bin"),
                                       "binary_sha256": "0" * 64, "bytes": 1,
                                       "symbolizer_sha256": "0" * 64, "targets_ok": ["f"]}
    B._learn_era = lambda *a, **k: None
    if classify:
        B.classify_build_failure = classify
    args = argparse.Namespace(retry_network=retry_network, dry_run=False, build_timeout=60)
    try:
        rec = B.build_pinned("c-blosc2", "address", "9ba29ef1584b7c29f5303dce", None,
                             "src/blosc2", ["f"], {}, args, depth=1)
    finally:
        (B.run_cmd, B.LOGS, B.restore_projects, B.archive_build, B._learn_era,
         B.classify_build_failure) = saved
    return rec, fake.calls


def t2_retry():
    print("\n[T2] N16 重试接线（离线注入，跑真的 build_pinned）")
    rec, calls = _pinned(FakeRun([(1, NET_LOG), (0, "INFO: build succeeded\n")]))
    ck(len(calls) == 2, f"network_fetch 失败 → **重试 1 次**（实调 {len(calls)} 次，期望 2）")
    ck(len(calls) == 2 and calls[1].endswith("_retry1.log"),
       f"重试日志另存 *_retry1.log（{len(calls) > 1 and os.path.basename(calls[1])}）")
    ck(rec["build_status"] == "ok", "重试成功 → 记录 build_status=ok（不被首试失败污染）")

    rec, calls = _pinned(FakeRun([(1, NET_LOG), (1, NET_LOG)]))
    ck(len(calls) == 2 and rec["build_status"] == "fail_pinned",
       "重试仍失败 → 只试 2 次（不无限重试）且记为 fail_pinned")

    rec, calls = _pinned(FakeRun([(1, CC_LOG)]))
    ck(len(calls) == 1, f"compile_error → **不重试**（实调 {len(calls)} 次，期望 1）")
    ck(rec["build_error_class"] == "compile_error",
       f"失败类正确 = {rec['build_error_class']}")

    rec, calls = _pinned(FakeRun([(1, NET_LOG)]), retry_network=False)
    ck(len(calls) == 1, "--no-retry-network → 即使是网络失败也不重试（开关有效）")

    # ── 负对照：证明上面的断言不是空过 ──
    print("  [负对照] 把分类器改成恒返回 compile_error → 重试必须**不再**触发")
    rec, calls = _pinned(FakeRun([(1, NET_LOG), (0, "ok\n")]),
                         classify=lambda text: ("compile_error", "forced"))
    ck(len(calls) == 1, f"分类器不认 network_fetch 时只调 1 次（实调 {len(calls)}）"
                        " → 说明「重试 2 次」确由分类结果驱动，测试有牙")


def main():
    print("═" * 72)
    print("W5 ② 自测：日志轮转（N25 / N40）+ N16 重试接线")
    print("═" * 72)
    t1_rotate()
    t1b_rotate_reproduce()
    t2_retry()
    print("\n" + ("❌ %d 项未通过：%s" % (len(FAILS), FAILS) if FAILS
                  else "✅ 全部通过"))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
