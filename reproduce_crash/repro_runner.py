#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""③ `repro_runner.py` — 复现执行（DELIVERY §1.3③）。

**一比一复刻 P0 已验证的形态**（✅ P0 §(d)：direct docker run 与官方 `helper.py reproduce`
给出**完全相同**的 DEDUP_TOKEN）：

```bash
docker run --rm -i -v <binary_dir>:/out -v <testcase>:/testcase \\
  -e FUZZING_ENGINE=libfuzzer -e SANITIZER=<san> -e RUN_FUZZER_MODE=interactive \\
  -e SKIP_SEED_CORPUS=1 -e TESTCASE=/testcase \\
  gcr.io/oss-fuzz-base/base-runner:ubuntu-24-04 \\
  bash -c '/out/<target> -- -rss_limit_mb=2560 -timeout=25 /testcase < /dev/null'
```

关键实现点（都有出处）
--------------------
* **二进制从归档位取**（`binary_dir` = `artifacts/binaries/<p>/<san>/<commit>/`），**不从临时
  `build/out`**——后者无 commit 分量、会被同项目下次构建 `rm -rf /out/*` 覆盖
  （✅ W2 实证：md4c 的 HEAD 二进制被随后的钉版构建覆盖，归档区两个 commit 并存）。
* **运行参数用 ✅ M11 实测的 base-runner 默认值**（`Dockerfile:77-80`）：`FUZZER_ARGS=
  -rss_limit_mb=2560 -timeout=25`；ASAN/MSAN/UBSAN_OPTIONS **不在命令行覆盖**，用镜像 ENV
  （含 `symbolize=1:dedup_token_length=3:strip_path_prefix=/workspace/`）。`malloc_limit_mb` 不设。
* **`.options`/`.dict` 按 `run_fuzzer:204-212` 的逻辑追加**（顺序：testcase → CUSTOM_LIBFUZZER_OPTIONS
  → `-dict=`），`.options` 由**容器内**的 `parse_options.py` 解析（不自己写 ini 解析器）；
  `SKIP_SEED_CORPUS=1` 故**不** append corpus 目录（`run_fuzzer:200-202`）。
  完整 CMD_LINE 回显进日志（`run_fuzzer:216 echo $CMD_LINE` 同法）→ 可审计。
* **UBSAN 不 abort**（✅ M11：`UBSAN_OPTIONS` 无 `halt_on_error`）→ exit 可能为 0，判定必须
  **解析 stderr** 的 `runtime error:` / `SUMMARY: UndefinedBehaviorSanitizer`，记
  `notes="ubsan_stderr_detected"`。ASAN/MSAN 仍可用 exit_code/signal
  （ASAN `handle_abort/handle_segv/handle_sigill=1`、MSAN `exit_code=86`）。
* **重试**（§1.7 D1 flaky，MSAN/uninit 875 条）：ASAN 1 次、MSAN/uninit ≤3 次；任一次崩即
  `reproduced_any=true`，记 `retry_count`。
* **完整 stderr 落盘**（Phase 5(c) 的原始依据）：`artifacts/logs/reproduce/<osv_id>[_rN].log`。

ⓘ 与设计的已知偏离（都在报告 §3 说明）
------------------------------------
* 不走 `run_fuzzer` 本体 → 少了它的 `sysctl -w vm.mmap_rnd_bits=28`（`run_fuzzer:22`，
  §1.7 D2）。P0 已实测：direct 形态与走 `run_fuzzer` 的 `helper.py reproduce` 给出**同一**
  DEDUP_TOKEN，故本轮沿用 direct（可用 `--engine-cmd run_fuzzer` 切回权威脚本做交叉校验）。
* UBSAN 的 `observed_crash_type` 无已验证样例（P0 只测过 ASAN）→ 同时存**逐字原文**
  `observed_crash_type_raw`，归一化比对用 ⓪ `normalize_crash_type()`；标 🅗。
"""
from __future__ import annotations

import argparse
import collections
import json
import glob
import os
import re
import shlex
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import repro_common as rc  # noqa: E402

OBSERVATIONS = os.path.join(rc.ARTIFACTS, "observations.jsonl")
REPRO_LOGS = os.path.join(rc.ARTIFACTS, "logs", "reproduce")
RUNNER_IMAGE = "gcr.io/oss-fuzz-base/base-runner:ubuntu-24-04"     # ✅ P0 用的就是这个 tag

# ---- sanitizer 报告解析 ----
ASAN_ERR_RE = re.compile(r"ERROR:\s*AddressSanitizer:\s*([^\s]+)\s+on address\s+(0x[0-9a-f]+)"
                         r"(?:\s+at pc\s+\S+\s+bp\s+\S+\s+sp\s+\S+\s+T\d+)?", re.I)
ASAN_ACCESS_RE = re.compile(r"\b(READ|WRITE) of size (\d+) at", re.I)
MSAN_ERR_RE = re.compile(r"ERROR:\s*MemorySanitizer:\s*([^\n(]+)", re.I)
UBSAN_RT_RE = re.compile(r"runtime error:\s*(.+)")
UBSAN_SUM_RE = re.compile(r"SUMMARY:\s*UndefinedBehaviorSanitizer:\s*([^\n]+)")
# **[N59②] UBSan `runtime error:` 的消息文本 → ClusterFuzz 的具体检查名。**
# expected 侧（ClusterFuzz 的 `crash_type`）给的是具体名，observed 侧原先一律压成泛化的
# `Undefined-behavior` → `crash_type_match` 永远 False → UBSAN 条目**结构性地**拿不到 medium+。
# ⚠ **只收已实测对上的形态**（键 = 匹配 `runtime error:` 之后文本的正则）；未命中仍退回泛化值。
#   宁可不升档，不可靠猜升档 —— 每加一条都要有「expected 与 observed 真的对上了」的实测样本。
UBSAN_CHECK_MAP = {
    r"index \d+ out of bounds for type": "Index-out-of-bounds",   # ✅ OSV-2020-1123（unicorn）
}
SEGV_RE = re.compile(r"ERROR:\s*AddressSanitizer:\s*(SEGV|segmentation fault)", re.I)
# `    #0 0x55f1a2 in md_resolve_links /src/md4c/src/md4c.c:3481:26`
FRAME_IN_RE = re.compile(r"^\s*#(\d+)\s+(?:0x[0-9a-f]+|\(.*?\))\s+in\s+(.+?)\s+(\S+:\d+(?::\d+)?)\s*$")
# `    #1 0x7f3b2c (/lib/x86_64-linux-gnu/libc.so.6+0x28189)`（无符号 → 只有模块）
FRAME_MOD_RE = re.compile(r"^\s*#(\d+)\s+(?:0x[0-9a-f]+)?\s*\((\S+?)\+(0x[0-9a-f]+)\)\s*$")
DEDUP_RE = re.compile(r"DEDUP_TOKEN:\s*(\S+)")
# libFuzzer 自身的终止原因（无 sanitizer 报告时也可能崩：deadly signal / timeout / OOM）
LIBFUZZER_FATAL_RE = re.compile(r"ERROR:\s*libFuzzer:\s*(deadly signal|timeout|"
                                r"out-of-memory|fuzz target exited|\S+)", re.I)
LIBFUZZER_SUM2_RE = re.compile(r"==\d+==\s*(?:ERROR|WARNING):\s*libFuzzer:\s*(.+)")
# **[实现 W2 bug 修 C] 输入是否真被执行过**：libFuzzer 跑单文件时会打
# `Running: /testcase` + `Executed /testcase in 10 ms`。若崩在 `LLVMFuzzerInitialize`
# （= target 启动阶段，还没碰输入），那是**环境/数据文件缺失**，不是复现。
# ✅ W2 首轮实测抓到：flatbuffers `monster_fuzzer` 因归档缺 `monster_test.bfbs` →
# `LoadBinarySchema` 的测试断言 helper 故意 trap（SIGILL）→ 10 条被误记成 loose 复现。
EXECUTED_RE = re.compile(r"Executed \S+ in \d+ ms")
# ⚠ **`Executed … in N ms` 不是有效判据**：libFuzzer 只在输入**跑完没崩**时才打它；
# 真崩溃时只有 `Running: /testcase`（后面直接接 sanitizer 报告）。
# ✅ W2 实测三例：libtsm 真崩溃 = Running 1 / Executed 0；hunspell 真无崩溃 = Running 1 / Executed 1；
# flatbuffers init trap = Running **0** / Executed 0（崩在 Initialize，压根没开始跑输入）。
RUNNING_RE = re.compile(r"^Running: ", re.M)
INIT_FRAME_RE = re.compile(r"\bLLVMFuzzerInitialize\b")
# **[实现 W2 bug 修] docker/shell 自身的退出码 ≠ 崩溃**：
# 125=docker daemon 报错（如挂载路径非法）、126=不可执行、127=命令未找到、
# -99=我方 run_timeout、-98=docker 不存在。把这些当「复现」会**虚高产出率**——
# ✅ W2 已知答案回归当场抓到：相对路径挂载 → exit=125 → 被误判 crashed（md4c HEAD 本该 none）。
RUNNER_ERROR_CODES = {125, 126, 127, -99, -98}
# 各 sanitizer 崩溃时的**预期**退出码（✅ M11：ASAN handle_abort/segv/sigill=1、MSAN exit_code=86）
SAN_CRASH_CODES = {"address": {1}, "memory": {86}, "undefined": {1}, "thread": {1}}
SCARINESS_RE = re.compile(r"SCARINESS:\s*(\d+)\s*\(([^)]*)\)")
LIBFUZZER_SUMMARY_RE = re.compile(r"SUMMARY:\s*\S*Sanitizer:\s*(\S+)")
# **[N46] 是否存在**真 sanitizer 报告**——用来把「libFuzzer 打到 timeout/OOM 上限」与
# 「真崩溃」分开。timeout 的 SUMMARY 是 `SUMMARY: libFuzzer: timeout`，**不含** `*Sanitizer`，
# 所以这条正则对它不命中 → 配合 `rc.NON_CRASH_DIAGNOSTICS` 判为「不是崩溃」。
SAN_ERROR_RE = re.compile(r"ERROR:\s*(?:Address|Memory|Thread|Leak)Sanitizer"
                          r"|SUMMARY:\s*(?:Address|Memory|Thread|Leak)Sanitizer"
                          r"|runtime error:", re.I)


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def parse_sanitizer_report(stderr, stdout=""):
    """从 stderr 解析 crash 类型 / 帧栈 / DEDUP_TOKEN。

    → dict(crash_type, crash_type_raw, crash_type_norm, frames, frames_full, dedup_token,
           scariness, ubsan_detected, signal_hint)
    `frames` = **函数名序列（不截断）**；`frames_full` = `func @ file:line`（Phase 5(c) 用）。
    """
    out = dict(crash_type=None, crash_type_raw=None, crash_type_norm="", frames=[],
               frames_full=[], dedup_token=None, scariness=None, scariness_label=None,
               ubsan_detected=False, signal_hint=None, engine_summary=None,
               libfuzzer_fatal=None, input_executed=False, started_running=False,
               init_crash=False)
    txt = stderr or ""
    if not txt:
        return out

    out["input_executed"] = bool(EXECUTED_RE.search(txt))     # 只作记录，**不作判据**
    out["started_running"] = bool(RUNNING_RE.search(txt))
    out["init_crash"] = bool(INIT_FRAME_RE.search(txt))
    frames, full = [], []
    for line in txt.splitlines():
        m = FRAME_IN_RE.match(line)
        if m:
            frames.append(m.group(2).strip())
            full.append(f"{m.group(2).strip()} @ {m.group(3)}")
            continue
        m = FRAME_MOD_RE.match(line)
        if m:
            mod = m.group(2)
            frames.append(mod)                       # 无符号帧：保留模块名（归一化阶段会剔内部帧）
            full.append(f"{mod}+{m.group(3)}")
    out["frames"], out["frames_full"] = frames, full

    m = DEDUP_RE.search(txt)
    if m:
        out["dedup_token"] = m.group(1)
    m = SCARINESS_RE.search(txt)
    if m:
        out["scariness"], out["scariness_label"] = int(m.group(1)), m.group(2)
    m = LIBFUZZER_SUMMARY_RE.search(txt)
    if m:
        out["engine_summary"] = m.group(1)
    m2 = LIBFUZZER_FATAL_RE.search(txt)
    if m2 and not out["engine_summary"]:
        out["engine_summary"] = m2.group(1).strip()
        out["libfuzzer_fatal"] = m2.group(0).strip()[:120]

    # ---- ASAN ----
    m = ASAN_ERR_RE.search(txt)
    if m:
        kind = m.group(1).strip()
        acc = ASAN_ACCESS_RE.search(txt)
        raw = m.group(0).strip()
        out["crash_type_raw"] = raw
        ct = kind[0].upper() + kind[1:]
        # ClusterFuzz 形态：`Heap-buffer-overflow READ 1`（数据集里就是这个格式）
        if acc:
            ct = f"{ct} {acc.group(1).upper()} {acc.group(2)}"
        out["crash_type"] = ct
        out["crash_type_norm"] = rc.normalize_crash_type(ct)
        return out
    if SEGV_RE.search(txt):
        out["crash_type"] = "Segv on unknown address"
        out["crash_type_raw"] = SEGV_RE.search(txt).group(0)
        out["crash_type_norm"] = rc.normalize_crash_type(out["crash_type"])
        out["signal_hint"] = "SIGSEGV"
        return out

    # ---- MSAN ----
    m = MSAN_ERR_RE.search(txt)
    if m:
        kind = m.group(1).strip().rstrip(".")
        out["crash_type_raw"] = m.group(0).strip()
        ct = kind[0].upper() + kind[1:] if kind else kind
        out["crash_type"] = ct
        out["crash_type_norm"] = rc.normalize_crash_type(ct)
        return out

    # ---- UBSAN（不 abort：exit 可能为 0，必须靠 stderr）----
    rt = UBSAN_RT_RE.search(txt)
    su = UBSAN_SUM_RE.search(txt)
    if rt or su:
        out["ubsan_detected"] = True
        out["crash_type_raw"] = (rt or su).group(0).strip()
        # **[N59②] 不要一律压成泛化的 `Undefined-behavior`。**
        # expected 侧来自 ClusterFuzz 的 `crash_type`，它给的是**具体检查名**
        # （✅ 实测 `OSV-2020-1123`：expected=`Index-out-of-bounds`），
        # 而报告原文里具体信息是有的：
        #   `…/translate.c:157:30: runtime error: index 16 out of bounds for type 'TCGv_i32[16]'`
        # 一律压成 `undefined-behavior` → `crash_type_match` 永远 False → UBSAN 条目**结构性地**
        # 拿不到 medium/strict（这是 UBSAN 覆盖长期为 0 时没人注意到的一个原因）。
        # ⚠ 只收**已实测对上**的形态，其余仍退回泛化值（宁可不升档，不可靠猜升档）。
        msg = (rt.group(1) if rt else "") or ""
        ct = UBSAN_CHECK_MAP.get(next((k for k in UBSAN_CHECK_MAP
                                       if re.search(k, msg, re.I)), None), "Undefined-behavior") \
            if msg else "Undefined-behavior"
        out["crash_type"] = ct
        out["crash_type_norm"] = rc.normalize_crash_type(ct)
        return out

    # ---- 其它崩溃（abort/timeout/OOM 由 libFuzzer 报）----
    if out["engine_summary"]:
        out["crash_type"] = out["engine_summary"]
        out["crash_type_norm"] = rc.normalize_crash_type(out["engine_summary"])
    return out


def build_cmd(binary_dir, target, testcase, san, timeout, rss_mb, engine_cmd="direct"):
    """拼 docker 命令。返回 (argv, human_readable_cmd_line)。

    **[实现 W2 bug 修]** 挂载路径一律 `abspath`：docker 对相对路径报
    `includes invalid characters for a local volume name` → exit **125**（不启动容器）。
    """
    binary_dir = os.path.abspath(binary_dir)
    testcase = os.path.abspath(testcase)
    mounts = ["-v", f"{binary_dir}:/out", "-v", f"{testcase}:/testcase"]
    env = ["-e", "FUZZING_ENGINE=libfuzzer", "-e", f"SANITIZER={san}",
           "-e", "RUN_FUZZER_MODE=interactive", "-e", "SKIP_SEED_CORPUS=1",
           "-e", "TESTCASE=/testcase"]
    if engine_cmd == "run_fuzzer":
        # 权威脚本本体（含 sysctl vm.mmap_rnd_bits=28 + .options/.dict 追加）；交叉校验用
        inner = f"run_fuzzer {shlex.quote(target)} /testcase"
    else:
        # ✅ P0 验证过的 direct 形态 + run_fuzzer:204-212 的 .options/.dict 追加逻辑
        inner = (
            f"cd /out; "
            f"FUZZER_ARGS='-rss_limit_mb={rss_mb} -timeout={timeout}'; "
            f"CMD=\"$OUT/{target} -- $FUZZER_ARGS /testcase\"; "
            f"if [ -f '{target}.options' ]; then "
            f"CMD=\"$CMD $(parse_options.py '{target}.options' libfuzzer 2>/dev/null)\"; fi; "
            f"if [[ ! \"$CMD\" =~ \"-dict=\" ]] && [ -f '{target}.dict' ]; then "
            f"CMD=\"$CMD -dict={target}.dict\"; fi; "
            f"echo \"CMD_LINE: $CMD\"; "
            f"unset OUT; bash -c \"$CMD < /dev/null\""
        )
    argv = ["docker", "run", "--rm", "-i", *mounts, *env, RUNNER_IMAGE, "bash", "-c", inner]
    return argv, inner


def run_once(binary_dir, target, testcase, san, args, log_path, engine_cmd="direct"):
    """跑一次。→ dict(exit_code, seconds, stderr, stdout, cmd_line, log_path, docker_error)"""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    # [W5 **N40**] 写之前先轮转：本函数原先 `open(log_path,"w")` 无条件截断，
    # 而日志名只由 `<osv_id>[_rN]` 决定 → **同一条 crash 跨轮次重跑会静默覆盖上一次的报告**。
    # ✅ 实证：113 条跑过多轮的 crash 里 110 条盘上只剩 1 份日志（N25 当时只修了 build 侧）。
    rot = rc.rotate_existing_log(log_path)
    if rot:
        log(f"    [N40 轮转] 上一次的同名报告已保留 → {os.path.basename(rot)}")
    argv, inner = build_cmd(binary_dir, target, testcase, san, args.timeout,
                            args.rss_limit_mb, engine_cmd)
    t0 = time.time()
    try:
        p = subprocess.run(argv, capture_output=True, text=True,
                           timeout=args.run_timeout, stdin=subprocess.DEVNULL)
        ex, so, se = p.returncode, p.stdout, p.stderr
        derr = None
    except subprocess.TimeoutExpired as e:
        ex, so, se = -99, e.stdout or "", (e.stderr or "") + f"\n# TIMEOUT {args.run_timeout}s"
        derr = "docker_timeout"
    except FileNotFoundError as e:
        ex, so, se, derr = -98, "", str(e), "docker_not_found"
    secs = time.time() - t0
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"# cmd: {' '.join(argv[:9])} … bash -c <inner>\n")
        f.write(f"# inner: {inner}\n")
        f.write(f"# binary_dir: {binary_dir}\n# target: {target}\n# testcase: {testcase}\n")
        f.write(f"# sanitizer: {san}\n# exit: {ex}\n# seconds: {secs:.2f}\n")
        f.write(f"# ts: {time.strftime('%Y-%m-%dT%H:%M:%S')}\n\n===== stdout =====\n{so}\n"
                f"\n===== stderr =====\n{se}\n")
    return dict(exit_code=ex, seconds=round(secs, 2), stdout=so, stderr=se,
                cmd_line=inner, log_path=log_path, docker_error=derr)


def classify(rep, exit_code, san, stderr=""):
    """**崩溃判定的单一真源**（run 循环与 `--selftest` 共用，避免两处逻辑分叉）。

    → dict(crashed, evidence, fallback, init_fail, runner_error)
    * `runner_error`：docker/shell 自身失败（125/126/127/-99/-98）→ **绝不是**复现
      （✅ W2 抓到：相对路径挂载 → exit=125 → 曾被误判 crashed）。
    * `evidence`：有 sanitizer 报告 / UBSAN stderr / libFuzzer 致命信号 / DEDUP_TOKEN。
    * `fallback`：无上述证据但退出码属该 sanitizer 的预期崩溃码且 stderr 非空
      （防解析器漏掉未知形态 → 假阴性）。
    * `init_fail`：**崩在 `LLVMFuzzerInitialize`，或 libFuzzer 还没开始跑输入**
      （无 `Running:` 行）→ target 启动阶段失败（缺运行期数据文件等），**不计复现**
      （✅ W2 抓到：flatbuffers 归档缺 `monster_test.bfbs` → 10 条被误记成 loose 复现）。
    """
    runner_error = exit_code in RUNNER_ERROR_CODES
    evidence = bool(rep.get("crash_type") or rep.get("ubsan_detected")
                    or rep.get("engine_summary") or rep.get("dedup_token"))
    fallback = (not runner_error and exit_code in SAN_CRASH_CODES.get(san, {1})
                and bool((stderr or "").strip()) and not evidence)
    init_fail = bool(evidence or fallback) and (rep.get("init_crash")
                                                or not rep.get("started_running"))
    # **[N46] 资源上限诊断（timeout / out-of-memory）不是崩溃**：libFuzzer 打到 `-timeout=25`
    # 或 `-rss_limit_mb` 上限时会报 `ERROR: libFuzzer: timeout` 并给出一个**全是引擎告警回调帧**
    # 的 DEDUP_TOKEN → 旧逻辑因 `engine_summary`/`dedup_token` 命中 evidence 而判 crashed。
    # ✅ 实测受害者：OSV-2023-1206（期望 Heap-buffer-overflow WRITE，实测 timeout，
    # score_subseq=0.0）被记成 loose 复现。
    # ⚠ 只在**没有任何 sanitizer 报告**时排除；真崩溃 + 顺带超时仍算崩溃。
    _ct = str(rep.get("crash_type") or "").strip().lower()
    _ctn = str(rep.get("crash_type_norm") or "").strip().lower()
    has_san = bool(rep.get("ubsan_detected")) or bool(SAN_ERROR_RE.search(stderr or ""))
    non_crash = (not has_san) and (_ct in rc.NON_CRASH_DIAGNOSTICS
                                   or _ctn in rc.NON_CRASH_DIAGNOSTICS)
    crashed = (evidence or fallback) and not init_fail and not runner_error and not non_crash
    return dict(crashed=crashed, evidence=evidence, fallback=fallback,
                init_fail=init_fail, runner_error=runner_error,
                non_crash_diagnostic=bool(non_crash and (evidence or fallback)),
                has_sanitizer_report=has_san)


def retries_for(san, crash_type_expected):
    """§1.7 D1：ASAN 1 次；MSAN / uninit ≤3 次（flaky）。"""
    if san == "memory":
        return 3
    if "uninitial" in (crash_type_expected or "").lower():
        return 3
    return 1


def pick_binary(rec, build_records, state, prefer="head"):
    """给一条 crash 找 `binary_dir`（**归档位**）。

    **[实现 W2 bug 修]** 原版无条件优先「该 osv_id 的钉版记录」，而 `build_records.jsonl` 是
    **跨轮全局追加**的 → HEAD 轮会捡到上一轮/验证轮留下的钉版二进制，把「HEAD 不复现」
    误判成「HEAD 复现」（✅ W2 端到端首跑当场抓到：md4c/pcre2 在 HEAD 轮报 crash=Y，
    而同一二进制单独跑是 exit=0）。故必须**显式指定要哪个版本**：

    `prefer="head"`   → 只要 HEAD 构建：① state.head_sha_cache[(p,san)] → state.builds[key]
                        （正规缓存，跨轮可复用）；② 本轮 build_records 里 path=head 的最新记录
    `prefer="pinned"` → 只要该 osv_id 的钉版记录（path=pinned）
    `prefer="any"`    → 先 pinned 后 head（调试用）
    → (build_record|None, how)
    """
    p, san, oid = rec["project"], rec["sanitizer"], rec["osv_id"]
    builds = state.get("builds") or {}
    hsc = state.get("head_sha_cache") or {}

    def _dir_ok(b):
        return bool(b) and b.get("build_status") == "ok" and os.path.isdir(b.get("binary_dir") or "")

    if prefer in ("head", "any"):
        prev = hsc.get(f"{p}|{san}")
        if prev:
            b = builds.get(f"{p}|{san}|{prev['sha']}")
            if _dir_ok(b):
                return b, "head_state_cache"
        cand = [b for b in build_records if b.get("path") == "head" and b.get("project") == p
                and b.get("sanitizer") == san and _dir_ok(b)]
        if cand:
            return cand[-1], "head_build_record"
    if prefer in ("pinned", "any"):
        cand = [b for b in build_records if b.get("osv_id") == oid and b.get("path") == "pinned"
                and _dir_ok(b)]
        if cand:
            return cand[-1], "pinned_this_osv"
        # 该 crash 的 pin_commit（① 静态 check 给）→ 直接查正规缓存键
        pc = rec.get("pin_commit")
        if pc:
            b = builds.get(f"{p}|{san}|{pc}")
            if _dir_ok(b):
                return b, "pinned_state_cache"
    if prefer == "head":
        # HEAD 拿不到时**不得**退回钉版二进制（那会把 Stage1 的结论污染成 Stage2 的）
        return None, "no_head_binary"
    cand = [b for b in build_records if b.get("project") == p and b.get("sanitizer") == san
            and _dir_ok(b)]
    if cand:
        return cand[-1], "same_project_sanitizer_other_commit"
    return None, "no_binary"


# ============================================================ 解析器自测（永久回归护栏）
# [实现 W2] 起因：本轮**两次**被崩溃判据咬到——① docker exit=125 被当成复现；
# ② 我为修 ① 而加的 `Executed … in N ms` 判据把**所有真崩溃**误杀（libtsm 的
# global-buffer-overflow 被记成 no_crash，直到我去翻日志才发现）。
# 故把 4 段**真实 stderr** 存成 fixture，每次跑 ③ 前先自测解析器；任一不符即退出 3。
# [W5 整理] preflight/ 已分 selftest / screen / history 三个子目录；fixtures 是**活的自测输入**
# （被本文件的 --selftest 用），故留在 preflight/ 顶层。查找加一层递归兜底：
# 万一以后再挪，也能找到，而不是报「fixture 缺失」这种指向错误方向的错。
def _find_fixtures():
    top = os.path.join(rc.PREFLIGHT_DIR, "fixtures")
    if os.path.isdir(top):
        return top
    hits = sorted(glob.glob(os.path.join(rc.PREFLIGHT_DIR, "**", "fixtures"), recursive=True))
    if len(hits) != 1:
        raise RuntimeError(f"preflight/ 下 fixtures/ 命中 {len(hits)} 个（须恰好 1）: {hits}")
    return hits[0]


FIXTURES = _find_fixtures()
SELFTEST = [
    # (文件, exit_code, sanitizer, 期望 crashed, 期望 init_fail, 期望 crash_type_norm, 说明)
    ("crash_real_libtsm.log", 1, "address", True, False, "global-buffer-overflow",
     "真崩溃：有 Running、无 Initialize 帧、ASAN global-buffer-overflow READ 1"),
    ("no_crash_hunspell.log", 0, "address", False, False, None,
     "真无崩溃：exit=0、有 Executed、无 sanitizer 报告"),
    ("init_trap_flatbuffers.stderr", 1, "address", False, True, "ill",
     "init trap：崩在 LLVMFuzzerInitialize（归档缺 .bfbs）→ **不算复现**"),
    ("ubsan_exit0.stderr", 0, "undefined", True, False, "undefined-behavior",
     "UBSAN 不 abort（M11）：exit=0 但 stderr 有 runtime error → **算崩**"),
    # **[N46]** 真实受害者 OSV-2023-1206（libavc/address）：期望 Heap-buffer-overflow WRITE，
    # 实测 libFuzzer 打到 `-timeout=25` 上限。DEDUP_TOKEN 全是引擎告警回调帧
    # （`__sanitizer_print_stack_trace--fuzzer::PrintStackTrace()--fuzzer::Fuzzer::AlarmCallback()`），
    # **没有任何目标代码帧** → 旧逻辑因 engine_summary+dedup_token 命中 evidence 而误判 crashed，
    # ④ 再给 loose，白多算 1 条复现。
    ("timeout_libavc.log", 70, "address", False, False, "timeout",
     "**[N46] libFuzzer 超时**：只有 `ERROR: libFuzzer: timeout`、无 sanitizer 报告 → **不算复现**"),
]


def _fixture_stderr(name):
    txt = open(os.path.join(FIXTURES, name), encoding="utf-8", errors="replace").read()
    m = "===== stderr ====="
    return txt.split(m, 1)[1] if m in txt else txt


def selftest(verbose=True):
    nfail = 0
    if verbose:
        print("=" * 78)
        print("③ 解析器自测（5 段真实 stderr fixture + 1 段合成反向对照；任一不符 → 退出 3）")
        print("=" * 78)
    for name, ex, san, want_crash, want_init, want_ct, note in SELFTEST:
        path = os.path.join(FIXTURES, name)
        if not os.path.exists(path):
            print(f"  ❌ fixture 缺失: {name}")
            nfail += 1
            continue
        se = _fixture_stderr(name)
        rep = parse_sanitizer_report(se)
        cl = classify(rep, ex, san, se)
        okc = cl["crashed"] == want_crash
        oki = cl["init_fail"] == want_init
        okt = (rep["crash_type_norm"] or None) == want_ct
        good = okc and oki and okt
        nfail += 0 if good else 1
        if verbose:
            print(f"  {'✅' if good else '❌'} {name}")
            print(f"      {note}")
            print(f"      crashed={cl['crashed']}（期望 {want_crash}）  "
                  f"init_fail={cl['init_fail']}（期望 {want_init}）  "
                  f"crash_type_norm={rep['crash_type_norm']!r}（期望 {want_ct!r}）")
            if not good:
                print(f"      证据: crash_type={rep['crash_type']!r} ubsan={rep['ubsan_detected']} "
                      f"engine_summary={rep['engine_summary']!r} started_running="
                      f"{rep['started_running']} init_crash={rep['init_crash']} "
                      f"dedup={str(rep['dedup_token'])[:40]!r}")
            if name == "crash_real_libtsm.log" and good:
                print(f"      frames(前3)={rep['frames'][:3]}")

    # **[N46 反向对照 · 合成]** 排除逻辑**不能过度触发**：真崩溃 + 顺带打到超时上限，仍须算崩。
    # （没有现成的真实日志同时含两者 → 明确标注为合成用例，用真 ASan 报告的 stderr 拼接。）
    _asan = _fixture_stderr("crash_real_libtsm.log")
    _to = _fixture_stderr("timeout_libavc.log")
    _rep2 = parse_sanitizer_report(_asan + "\n" + _to)
    _cl2 = classify(_rep2, 70, "address", _asan + "\n" + _to)
    _ok2 = _cl2["crashed"] is True and _cl2["non_crash_diagnostic"] is False
    nfail += 0 if _ok2 else 1
    if verbose:
        print(f"  {'✅' if _ok2 else '❌'} [合成] 真 ASan 报告 + 超时诊断并存")
        print(f"      期望 crashed=True、non_crash_diagnostic=False（有 sanitizer 报告就不排除）")
        print(f"      实际 crashed={_cl2['crashed']} non_crash={_cl2['non_crash_diagnostic']} "
              f"has_san={_cl2['has_sanitizer_report']} crash_type_norm={_rep2['crash_type_norm']!r}")
    if verbose:
        print(f"  → {len(SELFTEST)+1-nfail}/{len(SELFTEST)+1} 通过")
    return nfail == 0


def main():
    ap = argparse.ArgumentParser(description="③ 复现执行（DELIVERY §1.3③）")
    ap.add_argument("--selftest", action="store_true", help="只跑解析器自测（4 fixture）后退出")
    ap.add_argument("--manifest", default=rc.MANIFEST_OUT)
    ap.add_argument("--build-records", default=os.path.join(rc.ARTIFACTS, "build_records.jsonl"))
    ap.add_argument("--state", default=os.path.join(rc.ARTIFACTS, "state.json"))
    ap.add_argument("--out", default=OBSERVATIONS)
    ap.add_argument("--only-osv", default=None)
    ap.add_argument("--projects", default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--timeout", type=int, default=25, help="libFuzzer -timeout（M11 默认 25）")
    ap.add_argument("--rss-limit-mb", type=int, default=2560, help="M11 默认 2560")
    ap.add_argument("--run-timeout", type=int, default=300, help="docker 整体超时（秒）")
    ap.add_argument("--engine-cmd", choices=["direct", "run_fuzzer"], default="direct")
    ap.add_argument("--prefer", choices=["head", "pinned", "any"], default="head",
                    help="**必须显式**：本轮用哪个版本的二进制（HEAD 轮=head、钉版轮=pinned）。"
                         "默认 head；混用会污染 tier 归因（见 pick_binary 的 bug 记录）")
    ap.add_argument("--binary-override", default=None,
                    help="`osv_id=<binary_dir>[,…]`：强制用指定归档位（已知答案回归用）")
    ap.add_argument("--max-runs", type=int, default=0)
    a = ap.parse_args()

    if not selftest(verbose=True):
        log("❌ 解析器自测未过 → 拒绝执行（判定逻辑不可信时跑出来的 yield 无意义）")
        return 3
    if a.selftest:
        return 0

    mf = [json.loads(l) for l in open(a.manifest, encoding="utf-8")]          # noqa: E741
    if a.only_osv:
        want = set(x.strip() for x in a.only_osv.split(",") if x.strip())
        mf = [r for r in mf if r["osv_id"] in want]
    if a.projects:
        ps = set(x.strip() for x in a.projects.split(","))
        mf = [r for r in mf if r["project"] in ps]
    mf = [r for r in mf if not r["skip_reason"]]
    if a.limit:
        mf = mf[:a.limit]

    br = []
    if os.path.exists(a.build_records):
        br = [json.loads(l) for l in open(a.build_records, encoding="utf-8")]  # noqa: E741
    by_dir = {}
    for b in br:
        if b.get("binary_dir"):
            by_dir[b["binary_dir"]] = b          # 后者覆盖前者 = 最新
    state = {}
    if os.path.exists(a.state):
        state = json.load(open(a.state, encoding="utf-8"))
    overrides = {}
    if a.binary_override:
        for kv in a.binary_override.split(","):
            if "=" in kv:
                k, v = kv.split("=", 1)
                overrides[k.strip()] = v.strip()

    log(f"[③ 范围] {len(mf)} 条 crash；build_records {len(br)} 条；engine={a.engine_cmd}")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    n_run = n_repro = n_nobin = 0
    tiers = collections.Counter()
    for rec in mf:
        if a.max_runs and n_run >= a.max_runs:
            log(f"  ⛔ --max-runs {a.max_runs} 用尽")
            break
        oid = rec["osv_id"]
        san = rec["sanitizer"]
        target = rec.get("fuzz_target")
        tc = rec.get("testcase_path")
        obs = {"osv_id": oid, "project": rec["project"], "sanitizer": san, "fuzz_target": target,
               "crash_type_expected": rec.get("crash_type_expected"),
               "crash_type_norm_expected": rec.get("crash_type_norm"),
               "commit_source": rec.get("commit_source"),
               "static_check_verdict": rec.get("static_check_verdict"),
               "ts": int(time.time())}
        if not target:
            obs.update(reproduced_any=False, skip_reason="no_fuzz_target", retry_count=0)
            _emit(a.out, obs); tiers["no_target"] += 1; continue
        if not tc or not os.path.exists(tc):
            obs.update(reproduced_any=False, skip_reason="missing_testcase", retry_count=0)
            _emit(a.out, obs); tiers["missing_testcase"] += 1; continue

        if oid in overrides:
            bdir, how = overrides[oid], "override"
            # [实现 W2] 即便强制指定归档位，也要按 binary_dir 反查那次构建的记录，
            # 好把 pinned_commit / walkback_depth_actual / era_cache_hit 等**如实**带进 observation
            brec = by_dir.get(bdir) or {"binary_dir": bdir, "pinned_commit": None,
                                        "build_seconds": None}
        else:
            brec, how = pick_binary(rec, br, state, prefer=a.prefer)
            bdir = (brec or {}).get("binary_dir")
        obs["binary_source"] = how
        obs["prefer"] = a.prefer
        if not bdir or not os.path.isdir(bdir):
            obs.update(reproduced_any=False, skip_reason=f"no_binary({how})", retry_count=0)
            _emit(a.out, obs); n_nobin += 1; tiers["no_binary"] += 1
            log(f"  {oid}: 无可用归档二进制（{how}）")
            continue
        bin_path = os.path.join(bdir, target)
        if not (os.path.isfile(bin_path) and os.access(bin_path, os.X_OK)):
            obs.update(reproduced_any=False, skip_reason="target_not_in_archive",
                       binary_dir=bdir, retry_count=0)
            _emit(a.out, obs); n_nobin += 1; tiers["target_not_in_archive"] += 1
            log(f"  {oid}: 归档位无 {target}（{bdir}）")
            continue

        obs.update(binary_dir=bdir, pinned_commit=brec.get("pinned_commit"),
                   build_seconds=brec.get("build_seconds"),
                   oss_fuzz_commit=brec.get("oss_fuzz_commit"),
                   walkback_depth_actual=brec.get("walkback_depth_actual"),
                   era_cache_hit=brec.get("era_cache_hit"))
        obs["runtime_limits"] = (f"timeout={a.timeout}:rss_limit_mb={a.rss_limit_mb}:"
                                 f"symbolize=1:dedup_token_length=3:"
                                 f"strip_path_prefix=/workspace/")
        n_try = retries_for(san, rec.get("crash_type_expected"))
        attempts = []
        reproduced = False
        n_run += 1
        for i in range(n_try):
            lp = os.path.join(REPRO_LOGS, f"{oid}" + (f"_r{i}" if i else "") + ".log")
            r = run_once(bdir, target, tc, san, a, lp, a.engine_cmd)
            rep = parse_sanitizer_report(r["stderr"], r["stdout"])
            ex = r["exit_code"]
            cl = classify(rep, ex, san, r["stderr"])
            crashed, evidence, fallback = cl["crashed"], cl["evidence"], cl["fallback"]
            init_fail, runner_err = cl["init_fail"], cl["runner_error"]
            attempts.append({"try": i, "exit_code": ex, "seconds": r["seconds"],
                             "crash_type": rep["crash_type"], "crashed": crashed,
                             "evidence": evidence, "fallback_exit_code": fallback,
                             "runner_error": runner_err, "init_fail": init_fail,
                             "input_executed": rep["input_executed"],
                             "init_crash": rep["init_crash"],
                             "log_path": lp, "docker_error": r["docker_error"]})
            if init_fail:
                obs["skip_reason"] = "target_init_failed"
                obs["init_crash"] = rep["init_crash"]
                obs["input_executed"] = rep["input_executed"]
                obs["observed_crash_type"] = rep["crash_type"]
                obs["observed_frames"] = rep["frames"]
                obs["raw_log_path"] = lp
                log(f"    ⚠ 崩在 LLVMFuzzerInitialize/输入未执行（exit={ex}, "
                    f"type={rep['crash_type']}）→ **不计为复现**：target 缺运行期数据文件"
                    f"或环境不满足（W2 bug 修 C）")
                break
            if runner_err:
                obs["runner_error"] = (r["docker_error"] or f"docker_exit_{ex}")
                obs["runner_error_detail"] = (r["stderr"] or "")[-300:]
                log(f"    ⚠ runner 错误（exit={ex}，**不计为复现**）: "
                    f"{(r['stderr'] or '').strip().splitlines()[-1][:150] if r['stderr'] else ''}")
                break
            log(f"  {oid:<18}{rec['project']:<12}{san:<10}try{i} exit={r['exit_code']} "
                f"{r['seconds']:>5.1f}s crash={'Y' if crashed else 'n'} "
                f"type={rep['crash_type'] or '-'}")
            if crashed:
                reproduced = True
                obs.update(exit_code=r["exit_code"], signal=rep.get("signal_hint"),
                           observed_crash_type=rep["crash_type"],
                           observed_crash_type_raw=rep["crash_type_raw"],
                           observed_crash_type_norm=rep["crash_type_norm"],
                           observed_frames=rep["frames"], observed_frames_full=rep["frames_full"],
                           dedup_token=rep["dedup_token"], scariness=rep["scariness"],
                           scariness_label=rep["scariness_label"],
                           ubsan_stderr_detected=rep["ubsan_detected"],
                           raw_log_path=lp, cmd_line=r["cmd_line"],
                           run_seconds=r["seconds"], docker_error=r["docker_error"])
                break
            obs.update(exit_code=r["exit_code"], raw_log_path=lp, cmd_line=r["cmd_line"],
                       run_seconds=r["seconds"], observed_frames=rep["frames"],
                       observed_frames_full=rep["frames_full"],
                       observed_crash_type=rep["crash_type"],
                       observed_crash_type_norm=rep["crash_type_norm"],
                       dedup_token=rep["dedup_token"],
                       ubsan_stderr_detected=rep["ubsan_detected"],
                       docker_error=r["docker_error"])
        obs["reproduced_any"] = reproduced
        obs["retry_count"] = len(attempts) - 1
        obs["attempts"] = attempts
        if reproduced:
            n_repro += 1
            tiers["crashed"] += 1
        else:
            tiers["no_crash"] += 1
        if reproduced and rec.get("crash_type_norm") and obs.get("observed_crash_type_norm"):
            obs["crash_type_match"] = (obs["observed_crash_type_norm"]
                                       == rec["crash_type_norm"])
        _emit(a.out, obs)

    log(f"\n[③ 汇总] 实跑 {n_run} 条；复现 {n_repro}；无二进制 {n_nobin}；分布 {dict(tiers)}")
    log(f"  → {a.out}")
    return 0


def _emit(path, obs):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obs, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    sys.exit(main())
