#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s2a_build_facts.py —— 阶段2 入口①：生成 facts（含 5 个内部步骤）

  步骤1  解析 ASan 报告（66 字段）            → artifacts/_cache/crash_report_features.jsonl
  步骤2  CPG 数据流查询（reachability/guard） → artifacts/_cache/dataflow_features.jsonl
  步骤3  三源合成 facts                       → artifacts/facts/<OSV>/facts.json
  步骤4  CPG 深度查询（10 类代码结构字段）     → artifacts/_cache/deep_fields.jsonl
  步骤5  深度字段合并进 facts（只填空缺）      → 就地回写 artifacts/facts/<OSV>/facts.json

  * 中间产物都在 artifacts/_cache/；artifacts/ 根部只留 facts/ 与 interpretation/
  * 步骤2/4 要跑 Joern，产物已存在时自动跳过；--refresh 强制重跑
  * 步骤1/3/5 很便宜，每次都跑

用法：
  python3 s2a_build_facts.py [--refresh] [--steps 3,5] [--dry-run]
"""
from __future__ import annotations

import collections
import glob
import json
import os
import re
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from s2_lib_cpg import CPGDIR, JOERN, project_of, sh

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOP = os.path.dirname(ROOT)
A = os.path.join(ROOT, "artifacts")
CACHE = os.path.join(A, "_cache")
RC = os.path.join(ROOT, "reproduce_crash")

# ========================================================================
# 步骤 1
# ========================================================================

# ── 6 种「is located …」措辞（实测骨架，见模块 docstring）─────────────────────
RE_LOC_REGION = re.compile(
    r"is located (\d+) bytes? (after|before|inside of) (\d+)-byte region")
RE_LOC_GLOBAL = re.compile(
    r"is located (\d+) bytes? (before|after) global variable '([^']*)' "
    r"defined in '([^']*)' \(0x[0-9a-f]+\) of size (\d+)")
RE_LOC_STACK = re.compile(
    r"is located in stack of thread T\d+ at offset (-?\d+) in frame")

# ── 首条错误行 ────────────────────────────────────────────────────────────────
RE_SAN_ERROR = re.compile(
    r"^(?:==\d+==)?(ERROR|WARNING): (AddressSanitizer|MemorySanitizer|"
    r"UndefinedBehaviorSanitizer): ([\w-]+)")
RE_UBSAN = re.compile(
    r"^(/\S+?):(\d+):(\d+): runtime error: (.+)$")
RE_ACCESS = re.compile(r"(READ|WRITE) of size (\d+)")
RE_SEGV_ADDR = re.compile(r"SEGV on unknown address (0x[0-9a-f]+)?")
# ⚠ **[本轮补]** Shadow bytes 段原先**完全漏掉**：我写的正则是 `(?i)memory (?:around|state)`，
#   而 ASAN 的真实标题是 **`Shadow bytes around the buggy address:`** → 实测 0/162 命中，
#   但该段实际存在于 **107/162 = 66.0%** 的报告里。它给出故障地址周边的内存布局，
#   `=>` 行标出所在行、`[xx]` 标出**具体那个 shadow 字节**（如 `[f9]` = global redzone）。
RE_SHADOW_HDR = re.compile(r"Shadow bytes around the buggy address:")
RE_SHADOW_MARK = re.compile(r"=>(0x[0-9a-f]+):\s*(.+?)\[([0-9a-f]{2})\]")
RE_SHADOW_LEGEND = re.compile(r"^\s+(.+?):\s+((?:[0-9a-f]{2}\s*)+)\s*$", re.M)


def parse_shadow_legend(text: str) -> dict:
    """**从报告自身**解析 shadow legend，不硬编码。
    ⚠ 本轮实测：我硬编码的表有 2 处错 —— `fc` 官方是 **Container overflow**（我写成
      "heap right redzone"）、`fb` **根本不存在**（我编了个 "heap mid redzone"）。
      官方 legend 就在每份报告的 shadow 段之后（实测 107/107 都有），没有理由去猜。"""
    i = text.find("Shadow byte legend")
    if i < 0:
        return {}
    out = {}
    for ln in text[i:i + 900].split("\n")[1:16]:
        m = RE_SHADOW_LEGEND.match(ln.rstrip())
        if m:
            for b in m.group(2).split():
                out[b] = m.group(1).strip()
    return out
RE_NEG_SIZE = re.compile(r"negative-size-param: \(size=(-?\d+)\)")

RE_FRAME = re.compile(r"^\s*#(\d+)\s+(?:0x[0-9a-f]+|[0-9]+)\s+(.*)$")
HARNESS_FN = "LLVMFuzzerTestOneInput"


def _split_loc(loc: str):
    """/path[:line[:col]] → (file, line, col)。按 ':' 切而非用可选组正则（后者在
    「无行号」形态下会回溯出错，实测 `#2 … in tsm_vte_input /src/…/tsm-vte.c`）。"""
    if not loc.startswith("/"):
        return None, None, None
    parts = loc.split(":")
    f = parts[0]
    ln = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
    co = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
    return f, ln, co


def parse_frames(text: str):
    """解析 sanitizer 报告的栈帧。只取第一段连续 #N（崩溃栈），
    分配栈/释放栈由 parse_alloc_stack 单独处理。"""
    out = []
    for raw in text.split("\n"):
        m = RE_FRAME.match(raw)
        if not m:
            continue
        idx, rest = int(m.group(1)), m.group(2).strip()
        if rest.startswith("in "):
            rest = rest[3:]
            i = rest.rfind(" /")
            if i > 0:
                fn, loc = rest[:i].strip(), rest[i + 1:].strip()
            else:
                fn, loc = rest.strip(), ""
        else:
            # `#8 0x… (/lib/x86_64-linux-gnu/libc.so.6+0x29d8f) (BuildId: …)`
            mm = re.search(r"\((/\S+?)\+", raw)
            fn, loc = (mm.group(1) if mm else ""), ""
        f, ln, co = _split_loc(loc)
        out.append({"idx": idx, "fn": fn, "file": f, "line": ln, "col": co})
    return out


def _first_stack_after(text: str, marker: str, skip_interceptors: bool = True):
    """取 marker（如 `allocated by thread` / `freed by thread`）之后的第一段栈。

    ⚠ **[本轮修] 原先只解析 `allocated by thread`，完全没解析 `freed by thread`** ——
      而对 **UAF / double-free / invalid-free** 这三类，**释放栈才是关键证据**。
      实测 heap-double-free 的 3 条：ASAN 报告的故障帧 #0 是 `operator delete[](void*)`
      @ `asan_new_delete.cpp:179`（**ASAN runtime，不是项目代码**），真正的线索在第 2 段
      `freed by thread T0 here:` 里（`free_flag` @ hashmgr.cxx:108 ← `free_table()` :119
      ← `~HashMgr()` :128）。不抓这段 = 整个分析指向错误的代码。
      受影响面：13/166 条（UAF 9 + double-free 3 + invalid-free 1）。
    """
    i = text.find(marker)
    if i < 0:
        return None
    frames = []
    for raw in text[i:].split("\n")[1:]:
        m = RE_FRAME.match(raw)
        if m:
            rest = m.group(2).strip()
            if rest.startswith("in "):
                rest = rest[3:]
                j = rest.rfind(" /")
                fn, loc = (rest[:j].strip(), rest[j + 1:].strip()) if j > 0 else (rest.strip(), "")
                f, ln, co = _split_loc(loc)
                frames.append({"fn": fn, "file": f, "line": ln, "col": co})
            continue
        if frames:
            break                      # 栈已结束
    if not frames:
        return None
    if not skip_interceptors:
        return frames
    # 跳过分配器/释放器拦截帧，取**第一个项目帧**
    # ⚠ 必须用**前缀+边界**匹配，不能用子串：实测子串匹配下名单里的 `"free"` 会把项目函数
    #   `free_flag` / `free_table` 一并误剔（hunspell 的 double-free 正是这两个函数），
    #   导致所有帧被滤光、回退到 frames[0] = ASAN 的 `operator delete[]`。
    INTER_RE = re.compile(r"^(?:malloc|calloc|realloc|free|cfree|operator\s+new|operator\s+delete|"
                          r"__interceptor_\w+|_Zn?w?[maj]|_Zd[al][smnw]?|Allocator::\w+)"
                          r"(?:\(|\[|<|\s|$)")
    proj = next((f for f in frames
                 if f["fn"] and not INTER_RE.match(f["fn"])
                 and "compiler-rt" not in (f["file"] or "")), None)
    return {"frames": frames, "first_project_frame": proj or frames[0],
            "interceptor_skipped": proj is not None and proj is not frames[0]}


def parse_alloc_stack(text: str):
    """兼容旧调用：返回分配点的项目帧列表（保持原签名行为）。"""
    r = _first_stack_after(text, "allocated by thread")
    if not r:
        return None
    fp = r["first_project_frame"]
    return [fp] if fp else r["frames"][:1]


def parse_free_stack(text: str):
    """**新增**：解析 `freed by thread`（UAF / double-free / invalid-free 的关键证据）。"""
    return _first_stack_after(text, "freed by thread")


def extract(text: str, project: str | None = None) -> dict:
    """从一份 sanitizer 报告文本抽出全部 S1/D1 特征。"""
    out: dict = {
        "sanitizer_engine": None, "error_level": None, "fault_kind": None,
        "access_dir": None, "access_width": None,
        "loc_kind": None, "loc_dir": None, "loc_offset": None, "loc_size": None,
        "overshoot_ratio": None, "loc_global_var": None, "loc_global_file": None,
        "fault_fn": None, "fault_file": None, "fault_line": None, "fault_col": None,
        "fault_in_project": None, "fault_site_fn": None, "fault_site_file": None,
        "fault_site_line": None, "fault_site_col": None,
        "has_alloc_stack": False, "alloc_fn": None, "alloc_file": None,
        "alloc_line": None, "alloc_same_fn": None, "alloc_same_file": None,
        "alloc_interceptor_skipped": None,
        # **[本轮新增] 释放栈**（UAF / double-free / invalid-free 的关键证据）
        "has_free_stack": False, "free_fn": None, "free_file": None, "free_line": None,
        "free_n_frames": None, "free_interceptor_skipped": None,
        "free_vs_fault_same_fn": None, "free_vs_fault_same_file": None,
        "dedup_token": None, "scariness": None, "region_size": None,
        "n_frames": None, "harness_idx": None, "n_project_frames": None,
        "ubsan_file": None, "ubsan_line": None, "ubsan_col": None, "ubsan_msg": None,
        "neg_size_param": None,
        "has_shadow_bytes": False, "shadow_fault_addr": None, "shadow_byte": None,
        "shadow_byte_meaning": None, "shadow_line": None, "shadow_legend_size": 0,
    }

    # ① 首条错误行：sanitizer 引擎 / 级别 / 故障种类
    for raw in text.split("\n"):
        s = raw.strip()
        m = RE_UBSAN.match(s)
        if m:
            out.update(sanitizer_engine="UndefinedBehaviorSanitizer",
                       error_level="runtime error", fault_kind="ubsan-runtime-error",
                       ubsan_file=m.group(1), ubsan_line=int(m.group(2)),
                       ubsan_col=int(m.group(3)), ubsan_msg=m.group(4)[:200])
            break
        m = RE_SAN_ERROR.match(s)
        if m:
            fk = m.group(3)
            # ASan 有些信息是两段式："attempting double-free" / "attempting free on address ..."
            if fk == "attempting":
                if "double-free" in s:
                    fk = "double-free"
                elif "free on address" in s:
                    fk = "invalid-free"
                elif "realloc" in s:
                    fk = "invalid-realloc"
                else:
                    fk = "attempting-unknown"
            out.update(error_level=m.group(1), sanitizer_engine=m.group(2),
                       fault_kind=fk)
            break

    # ② 访问语义
    m = RE_ACCESS.search(text)
    if m:
        out["access_dir"], out["access_width"] = m.group(1), int(m.group(2))
    m = RE_NEG_SIZE.search(text)
    if m:
        out["neg_size_param"] = int(m.group(1))

    # ③ 越界几何（**核心特征**）
    m = RE_LOC_REGION.search(text)
    if m:
        d = m.group(2)
        out.update(loc_kind="region", loc_dir=d, loc_offset=int(m.group(1)),
                   loc_size=int(m.group(3)))
    else:
        m = RE_LOC_GLOBAL.search(text)
        if m:
            out.update(loc_kind="global", loc_dir=m.group(2),
                       loc_offset=int(m.group(1)), loc_global_var=m.group(3),
                       loc_global_file=m.group(4), loc_size=int(m.group(5)))
        else:
            m = RE_LOC_STACK.search(text)
            if m:
                out.update(loc_kind="stack_frame", loc_offset=int(m.group(1)))
    if out["loc_kind"] == "region" and out["loc_dir"] == "inside of":
        out["loc_dir"] = "inside"
    if out["loc_size"] not in (None, 0) and out["loc_offset"] is not None \
            and out["loc_dir"] in ("after", "before"):
        out["overshoot_ratio"] = round(out["loc_offset"] / out["loc_size"], 6)

    # ③b Shadow bytes（本轮补：原先整段漏掉）
    if RE_SHADOW_HDR.search(text):
        out["has_shadow_bytes"] = True
        m = RE_SHADOW_MARK.search(text)
        if m:
            out["shadow_fault_addr"] = m.group(1)
            out["shadow_byte"] = m.group(3)
            out["shadow_line"] = m.group(2).strip()[:120]
            leg = parse_shadow_legend(text)
            out["shadow_byte_meaning"] = leg.get(m.group(3)) or f"未编入 legend({m.group(3)})"
            out["shadow_legend_size"] = len(leg)

    # ④ 栈帧
    frames = parse_frames(text)
    if frames:
        out["n_frames"] = len(frames)
        f0 = frames[0]
        out.update(fault_fn=f0["fn"], fault_file=f0["file"],
                   fault_line=f0["line"], fault_col=f0["col"])
        pref = f"/src/{project}/" if project else None
        # ARVO 报告的路径形如 /work/build/../../src/<proj>/...，先 normpath 再前缀匹配
        def _normpath(p):
            return os.path.normpath(p) if p else p
        for f in frames:
            f["file_norm"] = _normpath(f["file"])
        proj = [f for f in frames
                if f["file"] and (f["file_norm"].startswith(pref) if pref
                                  else f["file_norm"].startswith("/src/"))]
        out["n_project_frames"] = len(proj)
        out["fault_in_project"] = bool(proj) and frames[0] is proj[0]
        # 项目级故障点 = 最靠近 #0 的项目帧（S2/S3 的定向入口）
        if proj:
            ps = proj[0]
            out.update(fault_site_fn=ps["fn"], fault_site_file=ps["file_norm"],
                       fault_site_line=ps["line"], fault_site_col=ps["col"])
        h = next((f["idx"] for f in frames if f["fn"] == HARNESS_FN), None)
        out["harness_idx"] = h

    # ④b DEDUP_TOKEN / SCARINESS / region 大小（double-free 报告独有）
    md = re.search(r"^DEDUP_TOKEN: (.+)$", text, re.M)
    if md:
        out["dedup_token"] = md.group(1).strip()[:160]
    ms = re.search(r"^SCARINESS: (\d+) \(([^)]+)\)", text, re.M)
    if ms:
        out["scariness"] = int(ms.group(1))
        out["scariness_kind"] = ms.group(2)
    mr = re.search(r"is located \d+ bytes? inside of (\d+)-byte region", text)
    if mr:
        out["region_size"] = int(mr.group(1))

    # ④c **释放栈**（本轮补：原先完全没解析）
    fr = parse_free_stack(text)
    if fr:
        out["has_free_stack"] = True
        fp = fr["first_project_frame"]
        out.update(free_fn=fp["fn"], free_file=fp["file"], free_line=fp["line"],
                   free_n_frames=len(fr["frames"]),
                   free_interceptor_skipped=fr["interceptor_skipped"])
        if out.get("fault_site_fn"):
            out["free_vs_fault_same_fn"] = (fp["fn"] == out["fault_site_fn"])
        if out.get("fault_site_file"):
            out["free_vs_fault_same_file"] = (fp["file"] == out["fault_site_file"])

    # ⑤ 分配栈
    al = parse_alloc_stack(text)
    if al:
        out["has_alloc_stack"] = True
        a0 = next((f for f in al if f["fn"] not in ("malloc", "calloc", "realloc",
                                                     "operator new", "new",
                                                     "__interceptor_malloc",
                                                     "Allocator::Allocate", "")), al[0])
        ar = _first_stack_after(text, "allocated by thread")
        out["alloc_interceptor_skipped"] = ar["interceptor_skipped"] if ar else None
        out.update(alloc_fn=a0["fn"], alloc_file=a0["file"], alloc_line=a0["line"])
        if out["fault_site_fn"] is not None:
            out["alloc_same_fn"] = (a0["fn"] == out["fault_site_fn"])
        if out["fault_site_file"] is not None:
            out["alloc_same_file"] = (a0["file"] == out["fault_site_file"])
    return out


def s1_load_ledger():
    """从 reproduced_crashes.jsonl 加载（字段名与旧日志兼容）。"""
    from s2_lib_cpg import load_reproduced
    return load_reproduced()


def run() -> list[dict]:
    lat = s1_load_ledger()
    VER = ("strict", "medium", "loose")
    v = {o: r for o, r in lat.items() if r.get("verification_tier") in VER}
    rows = []
    for p in sorted(glob.glob(os.path.join(
            RC, "artifacts/by_crash_type/*/*/*/*/*/INFO.txt"))):
        d = os.path.dirname(p)
        osv = os.path.basename(d)
        rep = os.path.join(d, "report.log")
        if not os.path.isfile(rep):
            continue
        text = open(rep, encoding="utf-8", errors="ignore").read()
        led = v.get(osv) or lat.get(osv) or {}
        f = extract(text, led.get("project"))
        f.update(osv_id=osv,
                 project=led.get("project"),
                 crash_type_norm=led.get("crash_type_norm"),
                 observed_crash_type=led.get("observed_crash_type"),
                 sanitizer=led.get("sanitizer"),
                 verification_tier=led.get("verification_tier"),
                 testcase_size=led.get("testcase_size"),
                 fuzz_target=led.get("fuzz_target"),
                 report_dir=os.path.relpath(d, RC))
        rows.append(f)
    return rows


# ── 已知答案自测 ──────────────────────────────────────────────────────────────
def selftest() -> int:
    """每条用例的期望值都取自本轮在 162 份真实报告里 dump 出的措辞骨架。"""
    bad = 0
    cases = [
        # (说明, 报告片段, {字段: 期望值})
        ("region after（74 份的主形态）",
         "==1==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x60200 at pc 0x1 bp 0x2 sp 0x3\n"
         "READ of size 1 at 0x60200 thread T0\n"
         "0x60200 is located 1 bytes after 16-byte region [0x60100,0x60110)\n",
         {"sanitizer_engine": "AddressSanitizer", "error_level": "ERROR",
          "fault_kind": "heap-buffer-overflow", "access_dir": "READ",
          "access_width": 1, "loc_kind": "region", "loc_dir": "after",
          "loc_offset": 1, "loc_size": 16, "overshoot_ratio": 0.0625}),
        ("region inside of → loc_dir 归一为 inside",
         "==1==ERROR: AddressSanitizer: heap-use-after-free on address 0x60 at pc 0x1 bp 0x2 sp 0x3\n"
         "READ of size 4 at 0x60 thread T0\n"
         "0x60 is located 0 bytes inside of 148-byte region [0x60,0xf4)\n",
         {"fault_kind": "heap-use-after-free", "loc_dir": "inside",
          "loc_offset": 0, "loc_size": 148, "overshoot_ratio": None}),
        ("global before（14 份）",
         "==1==ERROR: AddressSanitizer: global-buffer-overflow on address 0x5 in t\n"
         "0x5 is located 14 bytes before global variable 'g_tbl' defined in '/src/p/a.c' (0x9) of size 4\n",
         {"loc_kind": "global", "loc_dir": "before", "loc_offset": 14,
          "loc_size": 4, "loc_global_var": "g_tbl", "loc_global_file": "/src/p/a.c"}),
        ("stack frame（7 份）",
         "==1==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x7 in t\n"
         "Address 0x7 is located in stack of thread T0 at offset 32 in frame\n",
         {"loc_kind": "stack_frame", "loc_offset": 32, "loc_size": None}),
        ("⚠ MSAN 是 WARNING 不是 ERROR（14 份）",
         "==1==WARNING: MemorySanitizer: use-of-uninitialized-value\n"
         "    #0 0x5 in f /src/p/a.c:9:3\n",
         {"sanitizer_engine": "MemorySanitizer", "error_level": "WARNING",
          "fault_kind": "use-of-uninitialized-value", "access_dir": None,
          "loc_kind": None}),
        ("⚠ UBSan 完全不同构（1 份，本轮唯一的 undefined 正样本）",
         "/src/unicorn/qemu/target-arm/translate.c:514:8: runtime error: "
         "index 32 out of bounds for type 'TCGv_i32[8]'\n",
         {"sanitizer_engine": "UndefinedBehaviorSanitizer",
          "error_level": "runtime error", "fault_kind": "ubsan-runtime-error",
          "ubsan_file": "/src/unicorn/qemu/target-arm/translate.c",
          "ubsan_line": 514, "ubsan_col": 8}),
        ("negative-size-param 带 size=（2 份）",
         "==1==ERROR: AddressSanitizer: negative-size-param: (size=-1)\n",
         {"fault_kind": "negative-size-param", "neg_size_param": -1}),
        ("SEGV 无 address（4 份）不得崩",
         "==1==ERROR: AddressSanitizer: SEGV on unknown address (pc 0x1 bp 0x2 sp 0x3 T0)\n",
         {"fault_kind": "SEGV", "loc_kind": None}),
        ("帧无行号（实测 #2 tsm_vte_input）不得把路径吃掉",
         "==1==ERROR: AddressSanitizer: global-buffer-overflow on address 0x5 at pc 0x6\n"
         "    #0 0x1 in vte_write_debug /src/libtsm/src/tsm/tsm-vte.c:514:8\n"
         "    #1 0x2 in do_trans /src/libtsm/src/tsm/tsm-vte.c:1858:3\n"
         "    #2 0x3 in tsm_vte_input /src/libtsm/src/tsm/tsm-vte.c\n"
         "    #3 0x4 in LLVMFuzzerTestOneInput /src/libtsm_fuzzer.c:44:3\n"
         "    #4 0x5 in fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long) "
         "/src/llvm-project/compiler-rt/lib/fuzzer/FuzzerLoop.cpp:619:13\n",
         {"n_frames": 5, "fault_fn": "vte_write_debug",
          "fault_line": 514, "fault_col": 8, "harness_idx": 3,
          "fault_site_fn": "vte_write_debug", "fault_site_line": 514},
         "libtsm"),
        ("C++ 含空格的函数名不得被路径切分误伤",
         "    #0 0x1 in BEInt<unsigned short, 2>::operator unsigned short /src/hb/a.cc:7:1\n",
         {"fault_fn": "BEInt<unsigned short, 2>::operator unsigned short",
          "fault_file": "/src/hb/a.cc", "fault_line": 7}),
        ("Shadow bytes 段（**本轮补**：原先正则写错导致 0/162 漏掉，实际 107/162 有）",
         "==1==ERROR: AddressSanitizer: global-buffer-overflow on address 0x5 at pc 0x6\n"
         "Shadow bytes around the buggy address:\n"
         "  0x5601855bb800: f9 f9 f9 f9 00 02 f9 f9 00 00 02 f9 f9 f9 f9 f9\n"
         "=>0x5601855bb880: 00 03 f9 f9 00 00 00 02 f9 f9 f9 f9 00 00[f9]f9\n",
         {"has_shadow_bytes": True, "shadow_fault_addr": "0x5601855bb880",
          "shadow_byte": "f9", "fault_kind": "global-buffer-overflow"}),
        ("shadow legend **从报告解析**（不硬编码；实测我硬编码的 fc/fb 两处是错的）",
         "==1==ERROR: AddressSanitizer: heap-use-after-free on address 0x5 at pc 0x6\n"
         "Shadow bytes around the buggy address:\n"
         "=>0x0c0c: fa fa[fd]fd fa fa\n"
         "Shadow byte legend (one shadow byte represents 8 application bytes):\n"
         "  Addressable:           00\n"
         "  Partially addressable: 01 02 03 04 05 06 07\n"
         "  Heap left redzone:       fa\n"
         "  Freed heap region:       fd\n"
         "  Container overflow:      fc\n",
         {"has_shadow_bytes": True, "shadow_byte": "fd",
          "shadow_byte_meaning": "Freed heap region", "shadow_legend_size": 11}),  # 00 + 01..07(7个) + fa + fd + fc = 11
        ("**释放栈解析**（本轮补：double-free/UAF 的关键证据，原先完全没抓）",
         "==1==ERROR: AddressSanitizer: attempting double-free on 0x7b in thread T0:\n"
         "SCARINESS: 42 (double-free)\n"
         "    #0 0x1 in operator delete[](void*) /src/llvm-project/compiler-rt/lib/asan/asan_new_delete.cpp:179:46\n"
         "    #1 0x2 in HashMgr::~HashMgr() /src/hunspell/src/hunspell/hashmgr.cxx:131:5\n"
         "DEDUP_TOKEN: operator delete[](void*)--HashMgr::~HashMgr()--HunspellImpl::~HunspellImpl()\n"
         "0x7b is located 0 bytes inside of 2-byte region [0x7b,0x7d)\n"
         "freed by thread T0 here:\n"
         "    #0 0x1 in operator delete[](void*) /src/llvm-project/compiler-rt/lib/asan/asan_new_delete.cpp:179:46\n"
         "    #1 0x3 in free_flag /src/hunspell/src/hunspell/hashmgr.cxx:108:5\n"
         "    #2 0x4 in HashMgr::free_table() /src/hunspell/src/hunspell/hashmgr.cxx:119:7\n",
         {"has_free_stack": True, "free_fn": "free_flag", "free_line": 108,
          "free_n_frames": 3, "free_interceptor_skipped": True,
          "scariness": 42, "region_size": 2,
          "dedup_token": "operator delete[](void*)--HashMgr::~HashMgr()--HunspellImpl::~HunspellImpl()"}),
        ("分配栈：跳过 malloc 拦截帧取真实分配点",
         "==1==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x5 at pc 0x6\n"
         "READ of size 4 at 0x5 thread T0\n"
         "    #0 0x1 in use_it /src/p/a.c:20:5\n"
         "0x5 is located 4 bytes after 16-byte region [0x1,0x11)\n"
         "allocated by thread T0 here:\n"
         "    #0 0x9 in malloc /llvm/compiler-rt/lib/asan/asan_malloc_linux.cpp:1:1\n"
         "    #1 0xa in make_buf /src/p/a.c:10:9\n",
         {"has_alloc_stack": True, "alloc_fn": "make_buf", "alloc_line": 10,
          "alloc_same_file": True, "alloc_same_fn": False,
          "loc_offset": 4, "loc_size": 16, "overshoot_ratio": 0.25}),
    ]
    print("═══ S1 提取器已知答案自测 ═══")
    for case in cases:
        # 用例可选第 4 项 = project（帧路径形如 /src/<project>/… 时必须对上，
        # 否则「项目帧过滤」为空 —— 本轮实测撞到：libtsm 用例误传 project="p"）
        note, text, want = case[0], case[1], case[2]
        proj = case[3] if len(case) > 3 else "p"
        got = extract(text, proj)
        diffs = []
        for k, wv in want.items():
            gv = got.get(k)
            if isinstance(wv, float) and isinstance(gv, float):
                ok = abs(gv - wv) < 1e-6
            else:
                ok = (gv == wv)
            if not ok:
                diffs.append(f"{k}: got={gv!r} want={wv!r}")
        bad += 0 if not diffs else 1
        print(f"  {'✅' if not diffs else '❌'} {note}")
        for x in diffs:
            print(f"      {x}")
    print(f"  → {len(cases)-bad}/{len(cases)} 通过")

    print("\n═══ 全量实跑一致性（防「自测过但实跑解析不出」）═══")
    rows = run()
    n = len(rows)
    # ⚠ **不得硬编码条目数**：原写 `if n != 162` → 复现从 162 增到 166 后自测就假失败。
    #   改为独立数一遍盘上的交付目录，比「解析出的行数」与「实际条目数」是否一致。
    n_dir = len(glob.glob(os.path.join(
        RC, "artifacts/by_crash_type/*/*/*/*/*/INFO.txt")))
    cov = {k: sum(1 for r in rows if r.get(k) is not None) for k in
           ("fault_kind", "access_width", "loc_kind", "loc_size", "overshoot_ratio",
            "fault_site_file", "harness_idx", "testcase_size")}
    b2 = 0
    if n != n_dir:
        print(f"  ❌ 解析出 {n} 行 ≠ 盘上交付条目 {n_dir} 个"); b2 += 1
    else:
        print(f"  ✅ 解析到全部 {n} 个交付条目（与盘上目录数一致）")
    if n and cov["fault_kind"] < n * 0.95:
        print(f"  ❌ fault_kind 覆盖率仅 {cov['fault_kind']}/{n}"); b2 += 1
    else:
        print(f"  ✅ fault_kind 覆盖 {cov['fault_kind']}/{n} = {cov['fault_kind']/max(n,1):.1%}")
    print("  覆盖率:", json.dumps(cov, ensure_ascii=False))
    bad += b2
    print(f"\n{'✅ 全部通过' if bad==0 else f'❌ {bad} 项未通过'}")
    return 1 if bad else 0


def step1_main() -> int:
    out = os.path.join(CACHE, "crash_report_features.jsonl")
    rows = run()
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"写出 {len(rows)} 行 → {out}")
    return 0


# ========================================================================
# 步骤 2
# ========================================================================

sys.path.insert(0, HERE)
from s2_lib_cpg import CPGDIR, JOERN, sh, project_of

FEAT = os.path.join(A, "_cache", "crash_report_features.jsonl")
OUT_DF = os.path.join(CACHE, "dataflow_features.jsonl")

SCALA_QUERY = r'''
importCpg("__CPG__")
case class T(fn: String, line: Int, osv: String)
val targets = List(__TARGETS__)

def methodAt(fn: String, line: Int) = {
  val byName = cpg.method.nameExact(fn).l
  if (byName.nonEmpty) byName.head
  else {
    val byCall = cpg.call.lineNumber(line).method.l
    if (byCall.nonEmpty) byCall.head else null
  }
}
val CMP_RE = "<operator>.comparison|<operator>.lessThan|<operator>.greaterThan|<operator>.lessEqualsThan|<operator>.greaterEqualsThan|<operator>.notEquals|<operator>.equals"

for (t <- targets) {
  println(s"@@OSV ${t.osv}")
  val m = methodAt(t.fn, t.line)
  if (m == null) { println("@@METHOD_MISSING") }
  else {
    println(s"@@METHOD ${m.name}")
    println(s"@@NPARAMS ${m.parameter.l.size}")
    println(s"@@PARAMS ${m.parameter.name.l.mkString(",")}")
    println(s"@@CALLS_AT_LINE ${m.ast.isCall.lineNumber(t.line).l.size}")
    println(s"@@CALL_CODES ${m.ast.isCall.lineNumber(t.line).code.l.take(4).map(_.take(56)).mkString(" | ")}")
    println(s"@@LINE_NODES ${m.ast.isCall.lineNumber(t.line).l.size + m.ast.isIdentifier.lineNumber(t.line).l.size}")
    val lineIds = m.ast.isIdentifier.lineNumber(t.line).name.l.toSet
    println(s"@@LINE_IDS ${lineIds.mkString(",")}")
    def lineTrav = m.ast.isCall.lineNumber(t.line) ++ m.ast.isIdentifier.lineNumber(t.line)
    for (pn <- m.parameter.name.l) {
      def src = cpg.method.nameExact(m.name).parameter.nameExact(pn)
      val reached = lineTrav.reachableBy(src).l.size
      if (reached > 0) println(s"@@PARAM_REACHES ${pn} nodes=${reached} paths=0")
    }
    val cmps = m.ast.isCall.name(CMP_RE).l
    val cmpGuard = cmps.filter(c => c.argument.isIdentifier.name.l.exists(lineIds.contains))
    println(s"@@N_CMP_GUARD ${cmpGuard.size}")
    println(s"@@CMP_GUARD_CODES ${cmpGuard.map(_.code.take(70)).take(3).mkString(" | ")}")
    val inLoop = (m.ast.isCall.lineNumber(t.line).inAst.isControlStructure
                    .controlStructureType("DO|WHILE|FOR").l.nonEmpty)
    println(s"@@IN_LOOP $inLoop")
    val memops = m.ast.isCall.lineNumber(t.line).filter(_.name.matches("(memset|memcpy|memmove|strcpy|strncpy|__asan_memset|__asan_memcpy)"))
    if (memops.isEmpty) { println("@@NO_MEMOP") }
    else {
      for (mp <- memops) {
        println(s"@@MEMOP ${mp.name}||${mp.code.take(100)}")
        val args = mp.argument.l
        if (args.size >= 3) {
          val a = args(2)
          println(s"@@SIZE_ARG ${a.code.take(100)}")
          println(s"@@SIZE_IS_CONST ${a.isLiteral}")
          println(s"@@IS_MULT ${a.ast.isCall.name("<operator>.multiplication").l.nonEmpty}")
          println(s"@@IS_ADD ${a.ast.isCall.name("<operator>.addition").l.nonEmpty}")
          println(s"@@SIZE_IDS ${a.ast.isIdentifier.name.l.distinct.mkString(",")}")
        }
      }
    }
    println(s"@@CALLS " + m.ast.isCall.lineNumber(t.line).name.l.distinct.take(8).mkString(","))
    println(s"@@IDS " + m.ast.isIdentifier.lineNumber(t.line).name.l.distinct.take(10).mkString(","))
  }
}
'''


def cpg_build(cpg, targets):
    tl = ", ".join(f'T("{fn}", {ln}, "{osv}")' for fn, ln, osv in targets)
    return SCALA_QUERY.replace("__CPG__", cpg).replace("__TARGETS__", tl)


def cpg_parse(txt):
    out = {}
    cur = None
    for ln in txt.splitlines():
        s = ln.strip()
        if not s.startswith("@@"):
            continue
        k, _, v = s[2:].partition(" ")
        if k == "OSV":
            cur = v.strip(); out[cur] = {"osv_id": cur}; continue
        if cur is None:
            continue
        d = out[cur]
        if k == "PARAM_REACHES":
            d.setdefault("reachability", []).append(v.split()[0])
        elif k == "N_CMP_GUARD":
            d["guard"] = int(v) if v.isdigit() else None
        elif k in ("NPARAMS", "CALLS_AT_LINE", "LINE_NODES"):
            d[k.lower()] = int(v) if v.isdigit() else None
        elif k == "IN_LOOP":
            d["in_loop"] = (v == "true")
        elif k in ("METHOD", "PARAMS", "LINE_IDS", "CALL_CODES", "CMP_GUARD_CODES", "SIZE_ARG",
                   "SIZE_IS_CONST", "IS_MULT", "IS_ADD", "SIZE_IDS", "CALLS", "IDS"):
            d[k.lower()] = v
        elif k == "MEMOP":
            d.setdefault("memops", []).append(v)
        elif k in ("METHOD_MISSING", "NO_MEMOP"):
            d[k.lower()] = True
    return out


def step2_main():
    feat = {}
    for ln in open(FEAT, encoding="utf-8"):
        r = json.loads(ln)
        if r.get("fault_site_file") and r.get("fault_site_line"):
            feat[r["osv_id"]] = r
    led = {}
    for ln in open(LEDGER, encoding="utf-8"):
        r = json.loads(ln)
        if r.get("ok") and r.get("arvo_id"):
            led[r["osv_id"]] = r
        elif r.get("reproduced_any") and not r.get("arvo_id"):
            led[r["osv_id"]] = r
    print(f"有故障点 {len(feat)} | 复现记录表 {len(led)}")

    groups = collections.defaultdict(list)
    no_cpg = 0
    for osv, f in feat.items():
        l = led.get(osv)
        if not l:
            continue
        pin = l.get("pin_commit") or l.get("pinned_commit") or l.get("src_head")
        cpg = l.get("cpg")
        if not cpg and pin:
            cpg = os.path.join(CPGDIR, f"{project_of(l.get('repo_url'))}_{pin[:12]}.cpg")
        if not cpg or not os.path.isfile(cpg):
            no_cpg += 1
            continue
        groups[cpg].append((f.get("fault_site_fn") or "", int(f["fault_site_line"]), osv))
    print(f"分组 {len(groups)} 个 CPG | 无 CPG {no_cpg}")

    df, ast = {}, {}
    if os.path.isfile(OUT_DF):
        for ln in open(OUT_DF, encoding="utf-8"):
            try:
                x = json.loads(ln); df[x["osv_id"]] = x; ast[x["osv_id"]] = x
            except Exception:
                pass
    done = len(df)
    print(f"续跑：已完成 {done}")
    MAXG = int(os.environ.get("MAXG", "0"))
    for gi, (cpg, items) in enumerate(sorted(groups.items(), key=lambda kv: -len(kv[1])), 1):
        if MAXG and gi > MAXG:
            break
        items = [x for x in items if x[2] not in df]
        if not items:
            continue
        if os.path.getsize(cpg) > 40 * 1024 * 1024:
            _sz = round(os.path.getsize(cpg) / 1048576)
            for fn, line, osv in items:
                l = led.get(osv, {}); f = feat.get(osv, {})
                d = {"osv_id": osv, "error": "cpg_too_large_skipped", "cpg_size_mb": _sz}
                for k in ("project","crash_type_norm","sanitizer","method","fault_site_file","fault_site_line","fault_site_fn","src_head"):
                    d[k] = l.get(k) if l.get(k) is not None else f.get(k)
                df[osv] = d; ast[osv] = d
            print(f"  [跳过] {os.path.basename(cpg)} ({_sz}MB) {len(items)} 条", flush=True)
            continue
        sp = "/tmp/_an_cpg.scala"
        open(sp, "w", encoding="utf-8").write(cpg_build(cpg, items))
        try:
            r = sh([JOERN, "--script", sp], timeout=1800)
        except Exception as e:
            for fn, line, osv in items:
                l = led.get(osv, {}); f = feat.get(osv, {})
                d = {"osv_id": osv, "error": f"joern_timeout: {type(e).__name__}"}
                for k in ("project","crash_type_norm","sanitizer","method","fault_site_file","fault_site_line","fault_site_fn","src_head"):
                    d[k] = l.get(k) if l.get(k) is not None else f.get(k)
                df[osv] = d; ast[osv] = d
            print(f"  [超时] {os.path.basename(cpg)} {len(items)} 条", flush=True)
            continue
        parsed = cpg_parse((r.stdout or "") + "\n" + (r.stderr or ""))
        for fn, line, osv in items:
            d = parsed.get(osv, {"osv_id": osv})
            l = led.get(osv, {}); f = feat.get(osv, {})
            for k in ("project", "crash_type_norm", "sanitizer", "access_dir", "access_width",
                      "method", "vuln_commit", "commit_source", "fix_commit", "src_head"):
                if k not in d or d[k] is None:
                    d[k] = l.get(k) if l.get(k) is not None else f.get(k)
            d["fault_site_file"] = f.get("fault_site_file")
            d["fault_site_line"] = f.get("fault_site_line")
            d["fault_site_fn"] = f.get("fault_site_fn")
            df[osv] = d
            ast[osv] = d
        done += len(items)
        print(f"  [{gi}/{len(groups)}] {os.path.basename(cpg)[:38]:<40}{len(items)} 条  累计 {done}", flush=True)
        # 每完成一组就落盘，避免中途被杀丢进度
        with open(OUT_DF, "w", encoding="utf-8") as fh:
            for k in sorted(df): fh.write(json.dumps(df[k], ensure_ascii=False, sort_keys=True) + "\n")

    # 补上复现记录表/报告的元字段
    for osv, d in df.items():
        l = led.get(osv, {}); f = feat.get(osv, {})
        for k in ("project", "crash_type_norm", "sanitizer", "access_dir", "access_width",
                  "method", "vuln_commit", "commit_source", "fix_commit", "src_head"):
            if k not in d:
                d[k] = l.get(k) if l.get(k) is not None else f.get(k)
        d["fault_site_file"] = f.get("fault_site_file")
        d["fault_site_line"] = f.get("fault_site_line")
        d["fault_site_fn"] = f.get("fault_site_fn")
    for osv, d in ast.items():
        l = led.get(osv, {}); f = feat.get(osv, {})
        for k in ("project", "crash_type_norm", "fault_site_fn", "fault_site_line", "pin_commit", "src_head", "arvo_id"):
            if k not in d:
                d[k] = l.get(k) if l.get(k) is not None else f.get(k)

    with open(OUT_DF, "w", encoding="utf-8") as fh:
        for k in sorted(df): fh.write(json.dumps(df[k], ensure_ascii=False, sort_keys=True) + "\n")
    print(f"写出 {len(df)} 行 -> {OUT_DF}")


# ========================================================================
# 步骤 3
# ========================================================================

STORAGE = {
    "heap-buffer-overflow": "heap", "heap-use-after-free": "heap", "heap-double-free": "heap",
    "stack-buffer-overflow": "stack", "stack-buffer-underflow": "stack",
    "stack-use-after-return": "stack", "stack-use-after-scope": "stack",
    "global-buffer-overflow": "global", "global-use-after-free": "global",
}

ALLOC_APIS = ("malloc", "calloc", "realloc", "aligned_alloc", "memalign", "strdup", "strndup", "new")

# 报告 fault_kind 与记录表 crash_type_norm 的别名（语义同一）
TYPE_ALIAS = {
    "segv": "segv-on-unknown-address",
    "double-free": "heap-double-free",
    "bad-free": "invalid-free",
    "attempting-unknown": "invalid-free",
    "invalid-realloc": "invalid-free",
    "stack-use-after-scope": "stack-use-after-return",
}


def load_jsonl(path):
    if not os.path.isfile(path):
        return {}
    out = {}
    for ln in open(path, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        try:
            d = json.loads(ln)
        except Exception:
            continue
        if d.get("osv_id"):
            out[d["osv_id"]] = d
    return out


def s3_load_ledger():
    """从 reproduced_crashes.jsonl 加载（字段名与旧日志兼容）。"""
    from s2_lib_cpg import load_reproduced
    return load_reproduced()


def facts_build(osv, rep, df, led):
    """由三份数据构造 facts。只做事实归集，不做类型判断。"""
    # crash_type 以**报告的实测 fault_kind**为准（记录表可能是 ARVO 的预期类型）
    import re as _re
    def _norm(x):
        x = _re.split(r"\s+0x[0-9a-fA-F]+\b", str(x or ""))[0]
        x = _re.sub(r"\s+(READ|WRITE)\b.*$", "", x, flags=_re.I)
        x = _re.sub(r"[_\s]+", "-", x.lower())
        return _re.sub(r"[^a-z0-9\-]", "", x).strip("-")
    fk = (rep or {}).get("fault_kind")
    ctype = TYPE_ALIAS.get(_norm(fk), _norm(fk)) if fk else None
    if not ctype:
        ctype = (rep or {}).get("crash_type_norm") or (led or {}).get("crash_type_norm")
    ctype = TYPE_ALIAS.get(str(ctype), ctype)
    storage = STORAGE.get(str(ctype))

    # ── entity：崩溃行上的核心变量 ──
    ids = [x for x in str((df or {}).get("ids") or "").split(",") if x]
    # 优先选 free/memop 的实参；否则取第一个标识符
    entity_name = None
    calls = str((df or {}).get("calls") or "")
    if "free" in calls and ids:
        entity_name = ids[0]
    elif ids:
        entity_name = ids[0]

    # ── 分配事实：来自报告的 previously allocated 栈 ──
    alloc = None
    if (rep or {}).get("has_alloc_stack") and (rep or {}).get("alloc_fn"):
        alloc = {
            "api": next((a for a in ALLOC_APIS if a in str(rep.get("alloc_fn") or "").lower()), None)
                   or ("unknown:interceptor_skipped" if rep.get("alloc_interceptor_skipped") else None),
            "site": {"fn": rep.get("alloc_fn"), "file": rep.get("alloc_file"), "line": rep.get("alloc_line")},
            "size_expr": None,                      # 需要 CPG 查分配调用实参（P2）
            "size_bytes": rep.get("region_size"),
            "cross_function": (rep.get("alloc_fn") != (rep or {}).get("fault_site_fn")),
        }

    # ── 操作点：报告能给的（free 栈）+ 崩溃点 ──
    sites = []
    if (rep or {}).get("has_free_stack") and (rep or {}).get("free_fn"):
        sites.append({"kind": "free", "line": rep.get("free_line"), "fn": rep.get("free_fn"),
                      "code": None, "origin": "report:freed_by"})
    if (rep or {}).get("fault_site_line"):
        kind = "free" if "free" in calls else "unknown"
        sites.append({"kind": kind, "line": rep.get("fault_site_line"), "fn": rep.get("fault_site_fn"),
                      "code": (df or {}).get("call_codes"), "origin": "report:crash"})

    # ── 调用链：报告 recover 的帧（记录表 observed_frames）──
    # 注意：observed_frames 里可能拼接了"崩溃栈 + 释放栈/分配栈"，需去重
    INTERNAL = ("__interceptor_", "LLVMFuzzer", "ExecuteFilesOnyByOne", "main",
                "fuzzer::", "__libc_start_main", "_start", "__asan")
    chain, seen = [], set()
    stacks = [(led or {}).get("observed_frames") or []]
    for (stk, label) in [(stacks[0], "crash_stack")]:
        for f in stk:
            if not f or f in seen:
                continue
            seen.add(f)
            chain.append({"fn": f, "file": None, "line": None,
                          "is_project": not any(t in f for t in INTERNAL)})

    facts = {
        "osv_id": osv,
        "project": (rep or {}).get("project") or (led or {}).get("project"),
        "crash_type": ctype,
        "entity": {
            "name": entity_name,
            "kind": "pointer" if (storage == "heap" or "free" in calls) else None,
            "storage": storage,
            "decl": None,                            # 需要 CPG local 节点（P2）
        },
        "alloc": alloc,
        "sites": sites,
        "crash": {
            "site": {"fn": (rep or {}).get("fault_site_fn"), "file": (rep or {}).get("fault_site_file"),
                     "line": (rep or {}).get("fault_site_line")},
            "code": (df or {}).get("call_codes"),
            "access": {"dir": (rep or {}).get("access_dir"),
                       "width": (rep or {}).get("access_width"),
                       "region_bytes": (rep or {}).get("region_size")},
        },
        "context": {
            "fn": (df or {}).get("method") or (rep or {}).get("fault_site_fn"),
            "in_loop": bool((df or {}).get("in_loop")) if (df or {}).get("in_loop") is not None else None,
            "loop_type": None,
            "loop_range": None,
            "guards": (df or {}).get("cmp_guard_codes") or None,
            "guard_count": (df or {}).get("guard"),
        },
        "call_chain": chain,
        "types": {
            "entity_type": None,                     # 需要 CPG local 类型（P2）
            "cast_present": None,
            "is_signed": None,
        },
        "input_reachability": (df or {}).get("reachability") or [],
        "evidence": {
            "report": (led or {}).get("raw_log_path") or (rep or {}).get("report_dir"),
            "cpg": (led or {}).get("cpg"),
            "testcase_size": (led or {}).get("testcase_size"),
        },
        "type_reconciliation": {
            "report_fault_kind": (rep or {}).get("fault_kind"),
            "ledger_crash_type": (led or {}).get("crash_type_norm"),
            "used": ctype,
            "diverged": bool(fk) and str(TYPE_ALIAS.get(_norm(fk), _norm(fk))) != str((led or {}).get("crash_type_norm")),
        },
        "completeness": [],                          # 由 P2 补齐后填空
    }

    # ── 保留 deepen 已补的 CPG 字段（避免重建时清空）──
    old_p = os.path.join(A, "facts", osv, "facts.json")
    if os.path.isfile(old_p):
        try:
            od = json.load(open(old_p, encoding="utf-8"))
            if (od.get("entity") or {}).get("decl"):
                facts["entity"]["decl"] = od["entity"]["decl"]
                facts["entity"]["kind"] = od["entity"].get("kind") or facts["entity"].get("kind")
            if (od.get("types") or {}).get("entity_type"):
                facts["types"].update({k: v for k, v in od["types"].items() if v is not None})
            if od.get("free_related"):
                facts["free_related"] = od["free_related"]
            if (od.get("context") or {}).get("control_structures"):
                facts["context"]["control_structures"] = od["context"]["control_structures"]
            # 合并 cpg 来源的 sites（按 kind+line 去重）
            old_sites = {(s.get("kind"), s.get("line")) for s in facts.get("sites") or []}
            for s in od.get("sites") or []:
                if s.get("origin") == "cpg" and (s.get("kind"), s.get("line")) not in old_sites:
                    facts["sites"].append(s)
            facts["sites"] = sorted(facts.get("sites") or [], key=lambda x: (x.get("line") or 0))
        except Exception:
            pass

    # 标记缺失
    miss = []
    if not facts["entity"]["decl"]: miss.append("entity.decl")
    if facts["entity"]["storage"] is None: miss.append("entity.storage")
    if alloc and not alloc["size_expr"]: miss.append("alloc.size_expr")
    if not alloc and storage == "heap": miss.append("alloc")
    if not facts["types"]["entity_type"]: miss.append("types.entity_type")
    if facts["context"]["in_loop"] is None: miss.append("context.in_loop")
    if not chain: miss.append("call_chain")
    facts["completeness"] = miss
    return facts


def step3_main():
    rep = load_jsonl(os.path.join(CACHE, "crash_report_features.jsonl"))
    df = load_jsonl(os.path.join(CACHE, "dataflow_features.jsonl"))
    led = s3_load_ledger()
    print(f"报告 {len(rep)} | CPG {len(df)} | 记录表 {len(led)}")

    out_dir = os.path.join(A, "facts")
    os.makedirs(out_dir, exist_ok=True)
    n = 0
    import collections
    c = collections.Counter()
    # 以报告为准（995 条），CPG 有则补
    for osv in sorted(set(rep) | set(df)):
        r = rep.get(osv, {})
        d = df.get(osv, {})
        l = led.get(osv, {})
        if not r and not d:
            continue
        f = facts_build(osv, r, d, l)
        os.makedirs(os.path.join(out_dir, osv), exist_ok=True)
        with open(os.path.join(out_dir, osv, "facts.json"), "w", encoding="utf-8") as g:
            json.dump(f, g, ensure_ascii=False, indent=2, sort_keys=False)
            g.write("\n")
        c["有 alloc"] += bool(f.get("alloc"))
        c["有 in_loop"] += f.get("context", {}).get("in_loop") is not None
        c["有 reachability"] += bool(f.get("input_reachability"))
        c["有 call_chain"] += bool(f.get("call_chain"))
        n += 1
    print(f"写出 {n} 个 facts -> {out_dir}/<OSV>/facts.json")
    print("覆盖:", dict(c), "/", n)


# ========================================================================
# 步骤 4
# ========================================================================

sys.path.insert(0, HERE)
from s2_lib_cpg import CPGDIR, JOERN, sh, project_of

OUT = os.path.join(CACHE, "deep_fields.jsonl")
MAXW = int(os.environ.get("MAXW", "4"))
LOCK = threading.Lock()

SCALA_DEEP = r'''
importCpg("__CPG__")
case class T(fn: String, line: Int, osv: String, ent: String)
val targets = List(__TARGETS__)

def methodAt(fn: String, line: Int) = {
  val byName = cpg.method.nameExact(fn).l
  if (byName.nonEmpty) byName.head
  else {
    val byCall = cpg.call.lineNumber(line).method.l
    if (byCall.nonEmpty) byCall.head else null
  }
}
val CMP = "<operator>.lessThan|<operator>.lessThanEquals|<operator>.greaterThan|<operator>.greaterThanEquals|<operator>.equals|<operator>.notEquals"

for (t <- targets) {
  println(s"@@OSV ${t.osv}")
  val m = methodAt(t.fn, t.line)
  if (m == null) { println("@@MISSING") }
  else {
    // A. 故障行
    val calls = m.ast.isCall.lineNumber(t.line).l
    println(s"@@LINE_CALLS ${calls.size}")
    calls.foreach(c => println(s"@@LC|${c.name}|${c.code.take(200)}|${c.argument.l.size}"))
    val ids = m.ast.isIdentifier.lineNumber(t.line).l.map(_.name).distinct
    println(s"@@LINE_IDS|${ids.mkString(",")}")

    // B. 实体：声明 + 赋值
    val ent = if (t.ent.nonEmpty) t.ent else ids.headOption.getOrElse("")
    if (ent.nonEmpty) {
      println(s"@@ENT|$ent")
      val locs = m.local.nameExact(ent).l.map(x => (x.typeFullName, x.lineNumber.getOrElse(-1))) ++
                 m.parameter.nameExact(ent).l.map(x => (x.typeFullName, x.lineNumber.getOrElse(-1)))
      locs.take(1).foreach { case (tp, ln) => println(s"@@ENT_DECL|$tp|$ln") }
      m.ast.isCall.name("<operator>.assignment").l.foreach { a =>
        val aa = a.argument.l
        if (aa.size >= 2) {
          val lhs = aa(0).code.trim
          if (lhs == ent || lhs.startsWith(ent + " ") || lhs.startsWith(ent + "[") || lhs.startsWith(ent + ".") || lhs.startsWith(ent + "->")) {
            println(s"@@ENT_ASSIGN|${a.lineNumber.getOrElse(-1)}|${a.code.take(150)}")
          }
        }
      }
    }

    // C. 分配/释放调用（含包装函数）
    m.ast.isCall.l.filter { c =>
      c.name.matches("(?i).*(alloc|malloc|calloc|realloc|strdup|strndup|free).*")
    }.foreach { c =>
      val args = c.argument.code.l
      println(s"@@SITE|${c.name}|${c.lineNumber.getOrElse(-1)}|${c.code.take(150)}|${args.mkString(" ;; ").take(200)}")
    }

    // D. 比较（边界检查）
    m.ast.isCall.name(CMP).l.foreach { c =>
      println(s"@@GUARD|${c.lineNumber.getOrElse(-1)}|${c.code.take(150)}")
    }

    // E. 函数参数
    println(s"@@PARAMS|${m.parameter.name.l.mkString(",")}|${m.parameter.typeFullName.l.mkString(",")}")
    println(s"@@FUNC_LINES|${m.lineNumber.getOrElse(-1)}|${m.lineNumberEnd.getOrElse(-1)}")
  }
}
'''


def deep_build(cpg, targets):
    tl = ", ".join(f'T("{fn}", {ln}, "{osv}", "{ent}")' for fn, ln, osv, ent in targets)
    return SCALA_DEEP.replace("__CPG__", cpg).replace("__TARGETS__", tl)


def deep_parse(txt):
    out, cur = {}, None
    for ln in txt.splitlines():
        s = ln.strip()
        if not s.startswith("@@"):
            continue
        body = s[2:]
        k, _, v = body.partition("|") if "|" in body else body.partition(" ")
        if k == "OSV":
            cur = v.strip(); out[cur] = {"osv_id": cur, "line_calls": [], "line_ids": [],
                                         "entity_assignments": [], "sites": [], "guards": []}; continue
        if cur is None:
            continue
        d = out[cur]
        try:
            if k == "LC":
                p = v.split("|")
                d["line_calls"].append({"name": p[0], "code": p[1] if len(p) > 1 else None,
                                        "nargs": int(p[2]) if len(p) > 2 and p[2].isdigit() else None})
            elif k == "LINE_IDS":
                d["line_ids"] = [x for x in v.split(",") if x]
            elif k == "LINE_CALLS":
                d["line_call_count"] = int(v) if v.strip().isdigit() else 0
            elif k == "ENT":
                d["entity_name_cpg"] = v.strip()
            elif k == "ENT_DECL":
                p = v.split("|")
                d["entity_decl"] = {"type": p[0] if p else None,
                                    "line": int(p[1]) if len(p) > 1 and p[1].lstrip("-").isdigit() else None}
            elif k == "ENT_ASSIGN":
                p = v.split("|")
                d["entity_assignments"].append({"line": int(p[0]) if p[0].isdigit() else None,
                                                "code": p[1] if len(p) > 1 else None})
            elif k == "SITE":
                p = v.split("|")
                if len(p) >= 3:
                    d["sites"].append({"callee": p[0],
                                       "line": int(p[1]) if p[1].lstrip("-").isdigit() else None,
                                       "code": p[2] if len(p) > 2 else None,
                                       "args": p[3] if len(p) > 3 else None})
            elif k == "GUARD":
                p = v.split("|")
                d["guards"].append({"line": int(p[0]) if p[0].lstrip("-").isdigit() else None,
                                    "code": p[1] if len(p) > 1 else None})
            elif k == "PARAMS":
                p = v.split("|")
                d["func_params"] = {"names": [x for x in p[0].split(",") if x],
                                    "types": [x for x in (p[1] if len(p) > 1 else "").split(",") if x]}
            elif k == "FUNC_LINES":
                p = v.split("|")
                d["func_lines"] = [int(p[0]) if p[0].lstrip("-").isdigit() else None,
                                   int(p[1]) if len(p) > 1 and p[1].lstrip("-").isdigit() else None]
            elif k == "MISSING":
                d["method_missing"] = True
        except Exception:
            pass
    return out


def s4_load_ledger():
    """从 reproduced_crashes.jsonl 加载（字段名与旧日志兼容）。"""
    from s2_lib_cpg import load_reproduced
    return load_reproduced()


FOCUS = {"heap-buffer-overflow", "stack-buffer-overflow", "global-buffer-overflow",
         "heap-use-after-free", "heap-double-free"}


def step4_main():
    facts = {}
    for p in sorted(glob.glob(os.path.join(A, "facts", "*", "facts.json"))):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if d.get("crash_type") in FOCUS:
            facts[d["osv_id"]] = d
    led = s4_load_ledger()
    print(f"facts {len(facts)} | 记录表 {len(led)} | 并发 {MAXW}", flush=True)

    groups = collections.defaultdict(list)
    no_cpg = 0
    for osv, f in facts.items():
        l = led.get(osv) or {}
        cpg = l.get("cpg")
        if not cpg:
            pin = l.get("src_head") or l.get("pin_commit")
            if pin:
                cpg = os.path.join(CPGDIR, f"{project_of(l.get('repo_url'))}_{pin[:12]}.cpg")
        if not cpg or not os.path.isfile(cpg):
            no_cpg += 1
            continue
        if os.path.getsize(cpg) > 40 * 1024 * 1024:
            continue
        fn = f["crash"]["site"].get("fn"); line = f["crash"]["site"].get("line")
        ent = (f.get("entity") or {}).get("name") or ""
        if not fn:
            continue
        groups[cpg].append((fn, int(line) if line else 0, osv, ent))
    print(f"分组 {len(groups)} | 无 CPG {no_cpg}", flush=True)

    results = {}
    if os.path.isfile(OUT):
        for ln in open(OUT, encoding="utf-8"):
            try:
                x = json.loads(ln); results[x["osv_id"]] = x
            except Exception:
                pass
    print(f"续跑：已有 {len(results)}", flush=True)

    todo = []
    for cpg, items in groups.items():
        items = [x for x in items if x[2] not in results]
        if items:
            todo.append((cpg, items))
    MAXG = int(os.environ.get("MAXG", "0"))
    if MAXG:
        todo = todo[:MAXG]
    print(f"待跑 {len(todo)} 组 | 已有 {len(results)}", flush=True)

    def process(cpg, items):
        sp = f"/tmp/_deep_{threading.get_ident()}.scala"
        try:
            with open(sp, "w", encoding="utf-8") as fh:
                fh.write(deep_build(cpg, items))
            r = sh([JOERN, "--script", sp], timeout=1800)
            return deep_parse((r.stdout or "") + "\n" + (r.stderr or "")), items
        except Exception:
            return {}, items

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=MAXW) as ex:
        futs = {ex.submit(process, cpg, items): (cpg, items) for cpg, items in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            cpg, items = futs[fut]
            parsed, items = fut.result()
            with LOCK:
                for fn, line, osv, ent in items:
                    d = parsed.get(osv) or {"osv_id": osv}
                    d["osv_id"] = osv
                    results[osv] = d
                if i % 5 == 0 or i == len(todo):
                    with open(OUT, "w", encoding="utf-8") as fh:
                        for k in sorted(results):
                            fh.write(json.dumps(results[k], ensure_ascii=False, sort_keys=True) + "\n")
            print(f"  [{i}/{len(todo)}] {os.path.basename(cpg)[:34]:<36}{len(items)} 条 "
                  f"累计 {len(results)}  用时 {(time.time()-t0)/60:.0f}分", flush=True)

    print(f"完成 {len(results)} 条 -> {OUT}", flush=True)


# ========================================================================
# 步骤 5
# ========================================================================

FACTS_DIR = os.path.join(A, "facts")          # 唯一的 facts 存储：一崩溃一文件
DEEP = os.path.join(CACHE, "deep_fields.jsonl")
BACKUP = os.path.join(CACHE, "facts_before_deep.jsonl")   # 合并前快照

ALLOC_KEYS = ("alloc", "malloc", "calloc", "realloc", "new", "dup")


REPORT_KEYS = ("shadow_byte", "shadow_legend_size", "loc_size", "loc_global_var",
               "loc_offset", "loc_kind", "dedup_token", "overshoot_ratio", "region_size")


def load_report_extra():
    """从报告解析结果里提取 facts 没有但很有用的字段

    数据源：_cache/crash_report_features.jsonl（step1 的产物）。
    旧实现读的是 artifacts/crash_report/<OSV>/crash_report.json——那是同一份数据的
    拆分版（字段完全相同，各 63 个），由已归档的 split_artifacts 产出。
    改成读聚合 jsonl 后，artifacts/crash_report/ 与 artifacts/dataflow/ 都不再需要。
    """
    out = {}
    p = os.path.join(CACHE, "crash_report_features.jsonl")
    if not os.path.isfile(p):
        return out
    for ln in open(p, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        try:
            d = json.loads(ln)
        except Exception:
            continue
        osv = d.get("osv_id")
        if not osv:
            continue
        ex = {k: d.get(k) for k in REPORT_KEYS if d.get(k) is not None}
        if ex:
            out[osv] = ex
    return out


def load_deep():
    out = {}
    if not os.path.isfile(DEEP):
        return out
    for ln in open(DEEP, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        try:
            d = json.loads(ln)
        except Exception:
            continue
        out[d["osv_id"]] = d
    return out


def step5_main():
    deep = load_deep()
    rext = load_report_extra()
    print(f"deep_fields: {len(deep)} 条 | report_extra: {len(rext)} 条", flush=True)
    if not deep:
        print("没有 deep 数据，退出", flush=True)
        return 1

    facts = []
    for p in sorted(glob.glob(os.path.join(FACTS_DIR, "*", "facts.json"))):
        try:
            facts.append(json.load(open(p, encoding="utf-8")))
        except Exception:
            continue
    print(f"facts: {len(facts)} 条", flush=True)

    # 备份（合并前快照，写成 jsonl 便于对比）
    if not os.path.exists(BACKUP):
        with open(BACKUP, "w", encoding="utf-8") as fh:
            for f in facts:
                fh.write(json.dumps(f, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"已备份 -> {BACKUP}", flush=True)

    stat = {"merged": 0, "code": 0, "ent_name": 0, "ent_decl": 0,
            "site_args": 0, "alloc_args": 0, "report_extra": 0}

    for f in facts:
        osv = f.get("osv_id")
        # 先挂 crash_report 的额外字段（与 deep 无关，独立生效）
        ex = rext.get(osv)
        if ex:
            f["report_extra"] = ex
            stat["report_extra"] += 1

        d = deep.get(osv)
        if not d:
            continue
        stat["merged"] += 1
        f["deep"] = d

        # 1) crash.code：取该行最长的 call 代码（最外层语句）
        lc = d.get("line_calls") or []
        crash = f.get("crash") or {}
        f["crash"] = crash
        if not crash.get("code") and lc:
            best = max(lc, key=lambda x: len(x.get("code") or ""))
            if best.get("code"):
                crash["code"] = best["code"]
                stat["code"] += 1

        # 2) entity.name / decl
        ent = f.get("entity") or {}
        f["entity"] = ent
        if not ent.get("name") and d.get("entity_name_cpg"):
            ent["name"] = d["entity_name_cpg"]
            stat["ent_name"] += 1
        if not ent.get("decl") and d.get("entity_decl"):
            ed = d["entity_decl"]
            ent["decl"] = {"file": None, "line": ed.get("line"),
                           "type": ed.get("type"), "size": None}
            stat["ent_decl"] += 1

        # 3) 给 report 站点按行号补 args / code
        dsites = d.get("sites") or []
        by_line = {}
        for s in dsites:
            by_line.setdefault(s.get("line"), []).append(s)
        for s in (f.get("sites") or []):
            cands = by_line.get(s.get("line")) or []
            for c in cands:
                if c.get("args"):
                    if not s.get("args"):
                        s["args"] = c["args"]
                        stat["site_args"] += 1
                    if not s.get("code") and c.get("code"):
                        s["code"] = c["code"]
                    break

        # 4) alloc 的实参（标记来源为 CPG，可能对应错误的调用，供 interpret 判断）
        alloc = f.get("alloc") or {}
        f["alloc"] = alloc
        if not alloc.get("size_expr") and not alloc.get("size_expr_cpg"):
            al = [s for s in dsites
                  if any(k in (s.get("callee") or "").lower() for k in ALLOC_KEYS)]
            if al:
                alloc["size_expr_cpg"] = al[0].get("args")
                alloc["size_expr_cpg_callee"] = al[0].get("callee")
                stat["alloc_args"] += 1

    # 回写：逐条写回 facts/<OSV>/facts.json
    nw = 0
    for f in facts:
        osv = f.get("osv_id")
        if not osv:
            continue
        d = os.path.join(FACTS_DIR, osv)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "facts.json"), "w", encoding="utf-8") as fh:
            json.dump(f, fh, ensure_ascii=False, indent=2, sort_keys=False)
            fh.write("\n")
        nw += 1

    print(f"合并完成: {stat}", flush=True)
    print(f"facts 已更新 -> {FACTS_DIR}/<OSV>/facts.json（{nw} 个文件）", flush=True)
    return 0




# ============================================================================
# 编排
# ============================================================================

STEPS = [
    (1, "解析 ASan 报告",   "crash_report_features.jsonl", False, "step1_main"),
    (2, "CPG 数据流查询",   "dataflow_features.jsonl",     True,  "step2_main"),
    (3, "合成 facts",       None,                          False, "step3_main"),
    (4, "CPG 深度字段查询", "deep_fields.jsonl",           True,  "step4_main"),
    (5, "合并深度字段",     None,                          False, "step5_main"),
]


def main():
    import argparse
    ap = argparse.ArgumentParser(description="阶段2 入口①：生成 facts")
    ap.add_argument("--refresh", action="store_true", help="删除 _cache 中间产物后全部重跑")
    ap.add_argument("--steps", default="1,2,3,4,5", help="要跑的步骤，逗号分隔")
    ap.add_argument("--dry-run", action="store_true", help="只打印计划")
    a = ap.parse_args()
    want = {int(x) for x in a.steps.split(",") if x.strip().isdigit()}
    os.makedirs(CACHE, exist_ok=True)

    if a.refresh:
        for _, _, out, _, _ in STEPS:
            if out:
                p = os.path.join(CACHE, out)
                if os.path.exists(p):
                    if a.dry_run:
                        print(f"[dry-run] 会删除 {p}")
                    else:
                        os.remove(p); print(f"已删除 {p}")

    print(f"=== facts 生成：cache={CACHE}")
    print(f"=== 计划执行的步骤: {sorted(want)}\n")

    for n, desc, out, expensive, fn in STEPS:
        if n not in want:
            print(f"[{n}] {desc} —— 跳过（未在 --steps 中）"); continue
        if out:
            cached = os.path.join(CACHE, out)
            if os.path.exists(cached):
                print(f"[{n}] {desc} —— 复用缓存 {out} ({os.path.getsize(cached)/1048576:.1f} MB)")
                continue
            if expensive:
                print(f"[{n}] {desc} —— 需要跑 Joern，可能很慢…")
        else:
            print(f"[{n}] {desc} …")
        if a.dry_run:
            print(f"      [dry-run] 调用 {fn}()"); continue
        t0 = time.time()
        rc = globals()[fn]()
        if rc not in (0, None):
            print(f"      ❌ 失败 rc={rc}（{time.time()-t0:.1f}s）"); return 1
        print(f"      ✓ 完成（{time.time()-t0:.1f}s）")

    print("\n=== facts 已生成")
    print(f"    {os.path.join(A, 'facts')}/<OSV>/facts.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
