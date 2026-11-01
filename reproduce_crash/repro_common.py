#!/usr/bin/env python3
"""⓪ `repro_common.py` — crash 复现流水线的共享底座（无 CLI）。

对应设计文档 §5⓪（DELIVERY.md 第一部分）。职责：
  * 路径常量 + 4 个数据源加载（crash_dataset / crash_state_recovered / crash_testcase JSON /
    `_osv_cache`）；
  * 帧归一化 `normalize_frames()` —— **[实现 W1] 不重写**：用 `ast` 从
    `preflight/normalize_frames.py` **逐字提取**那份实现（含 `INTERNAL_PREFIXES` /
    `SUFFIX_RE` / `LAMBDA_RE` / `normalize_one_frame` / `normalize_frames`），保证「同一份代码」
    而非「同一份意图」；提取失败即 raise（不静默回退到另一份实现，防止两处悄悄分叉）。
    另提供 `verify_normalize_frames()`：复算 R2-extra 的逐帧计数并与报告里的数字对账。
  * 派生 helper：`osv_year`(M1)、`crash_type` 归一化、`language`(M3b/R5 exact-match)、
    `crash_cluster_id`(M7+R2)、`sanitizer`/`fuzz_target` 解析(R10/M9/R7)、
    testcase sha256 + `input_magic`(M8)；
  * OSV 解析：`osv_fixed_and_repo()`（R13a 选择规则，0 歧义）、`is_degenerate_range()`（**N6**）；
  * `fixed^` SHA 解析：`get_parent_local()`（§5⓪ 要求经 `repo_manager.get_parent`，用于
    ② 构建期、宿主已有 /src 副本时）；
  * **[实现 W1]** `resolve_repo_path()`（逐 crash 解析 `repo_path`，消费
    `artifacts/repo_path_map.json`）与 `static_check`（复合证据分定位真修复，见
    `preflight/2026-09-09-offbyone-sampling.md`）；
  * schema 定义（§6.3 的 ① 子集）。

约束：oss-fuzz 主树 `/root/gyx/oss-fuzz` **只读**；不 import driver_create；不跑 docker。
静态 check 需要网络（github/gitlab 的 `.patch` 端点，经宿主代理），**可关**（离线时全部记
`not_located`，绝不崩）。
"""
from __future__ import annotations

import ast
import hashlib
import json
import glob
import datetime
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict

# ============================================================ 路径常量
ROOT = "/root/gyx"
MC = os.path.join(ROOT, "mutator_create")
REPRO_DIR = os.path.join(MC, "reproduce_crash")
PREFLIGHT_DIR = os.path.join(REPRO_DIR, "preflight")
ARTIFACTS = os.path.join(REPRO_DIR, "artifacts")

DATA_DIR = os.path.join(MC, "data")
CRASH_DATASET = os.path.join(DATA_DIR, "crash_dataset.jsonl")          # 3,790 行
CRASH_STATE_RECOVERED = os.path.join(DATA_DIR, "crash_state_recovered.jsonl")
OSV_CACHE_DIR = os.path.join(DATA_DIR, "_osv_cache")                   # 3,790 个 json
CRASH_TESTCASE_DIR = os.path.join(MC, "crash_testcase")                # <crash_type>/<target>/<osv>.json
TESTCASE_MISSING_MANIFEST = os.path.join(CRASH_TESTCASE_DIR, "_MANIFEST_missing.txt")

# oss-fuzz：主树只读（project.yaml 口径与预飞测量一致，故 language/main_repo 读主树）；
# worktree 是构建用的官方树（REPRO_OSS_FUZZ_DIR，§7H）。
OSS_FUZZ_MAIN = os.environ.get("OSS_FUZZ_DIR", os.path.join(ROOT, "oss-fuzz"))
OSS_FUZZ_WORKTREE = os.environ.get("REPRO_OSS_FUZZ_DIR",
                                   os.path.join(ROOT, "oss-fuzz-repro"))
# 三补丁所在分支/commit（§7H#3 的 gate 条件①③；[实现 W1] 第二件固化）
REPRO_PATCH_BRANCH = "repro-patches"
REPRO_PATCH_COMMIT = "07522dc0e"

# **[W5 第十四轮 · N46] 资源上限诊断 ≠ 崩溃**（⑥ `classify` 与 ④ `verify_one` 共用，避免两处分叉）
# libFuzzer 打到时间/内存上限时会报 `ERROR: libFuzzer: timeout`（exit=70）或 `out-of-memory`，
# 并附一个 **DEDUP_TOKEN 全是引擎自身告警回调帧** 的 token：
#   `__sanitizer_print_stack_trace--fuzzer::PrintStackTrace()--fuzzer::Fuzzer::AlarmCallback()`
# 里面**没有任何目标代码帧**。✅ 实测抓到：`OSV-2023-1206`（libavc/address）期望
# `Heap-buffer-overflow WRITE {*}`，实测 `timeout`、`score_subseq=0.0`，却因 `engine_summary`+
# `dedup_token` 被 `classify` 判成 evidence → ④ 落到 else 分支给了 **loose**，白多算 1 条复现。
# ⚠ 只排除**纯资源上限**：若同时存在 sanitizer 报告（真崩溃），仍算崩溃。
# `deadly signal`（如裸 SEGV）**不排除**——那是真崩溃，只是没有 sanitizer 报告。
# ⚠ **不含空串**：空 `crash_type` 只说明解析器没认出来，不等于「没崩」；把空串列进来会误杀
#   `ERROR: libFuzzer: deadly signal` 这类无 sanitizer 报告的真崩溃。
# **[W7 修 N67] 加 `fuzz-target-exited`**：原先只有 timeout/OOM/no-crash，
# 漏了 `ERROR: libFuzzer: fuzz target exited`（exit=77）—— 它是**目标自行 exit()**，
# 报告里**没有任何 sanitizer 段**，DEDUP_TOKEN 形如
# `__sanitizer_print_stack_trace--fuzzer::PrintStackTrace()--fuzzer::Fuzzer::ExitCallback()`。
# ✅ 实测受害：espeak-ng 4 条被记成「复现 tier=loose」，真因是归档缺 `espeak-ng-data/`
#   → `Error processing file '/out/phontab': No such file or directory` → 初始化失败退出
#   （根因见 build_orchestrator.py 的 N66）。**这是环境缺文件，不是漏洞复现。**
NON_CRASH_DIAGNOSTICS = {"timeout", "out-of-memory", "oom", "no-crash",
                         "fuzz-target-exited", "fuzz target exited"}

REPO_PATH_MAP = os.path.join(ARTIFACTS, "repo_path_map.json")
STATIC_CHECK_CACHE = os.path.join(ARTIFACTS, "static_check_cache.jsonl")
MANIFEST_OUT = os.path.join(ARTIFACTS, "repro_manifest.jsonl")
BUILD_GROUPS_OUT = os.path.join(ARTIFACTS, "build_groups.json")
# [W5 整理] 原来写死 `preflight/normalize_frames.py`；preflight/ 已按「selftest / screen / history」分目录，该脚本移到了 `history/`。
# 与其再写死一层，不如**在 preflight/ 下递归找文件名** —— 以后再整理目录也不会断这条链。
# ⚠ 找到 0 个或 ≥2 个都必须报错：0 = 权威实现丢了；≥2 = 有两份实现，违反「不分叉」原则。
def _find_preflight(name):
    hits = sorted(glob.glob(os.path.join(PREFLIGHT_DIR, "**", name), recursive=True))
    if len(hits) != 1:
        raise RuntimeError(
            f"preflight/ 下 `{name}` 命中 {len(hits)} 个（必须恰好 1 个）: {hits}\n"
            "该文件是 normalize_frames 的**权威实现**，靠 AST 逐字复用；"
            "0 个=丢了，≥2 个=两份实现会分叉。")
    return hits[0]

PREFLIGHT_R2 = _find_preflight("normalize_frames.py")

PROXY = os.environ.get("REPRO_PROXY", "http://127.0.0.1:7890")   # ✅ P0 实测 clash 绑 loopback
SCHEMA_VERSION = "repro-manifest/1.0+[W1]"

# R10：`infra/constants.py:21 DEFAULT_SANITIZER='address'`
DEFAULT_SANITIZER = "address"
SANITIZER_ALIASES = {"address (ASAN)": "address", "memory (MSAN)": "memory",
                     "undefined (UBSAN)": "undefined", "ASAN": "address",
                     "MSAN": "memory", "UBSAN": "undefined"}
MAINLINE_LANGUAGES = ("c", "c++")     # R5 exact-match：主线 3,502
# ❌ 不内置任何项目名映射：R5 的教训是 substr 回落把 unrar26 误映 junrar、污染 language 口径。
# M2 name-miss 的项目一律标 `unmapped_project`，等人批准后再填这里（§5⓪「M2 仅 ≤6 项」）。
PROJECT_NAME_MAP: dict[str, str] = {}


# ============================================================ 数据加载
def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def load_crash_dataset():
    """3,790 条 crash（`osv_id`/`project`/`crash_type`/`sanitizer`/`fuzz_target`/`frames`/
    `testcase_path`/…）。"""
    return list(load_jsonl(CRASH_DATASET))


def load_crash_testcase_meta():
    """`crash_testcase/**/<osv_id>.json` → dict（权威 fuzz_target/sanitizer/engine/job_type/
    introducing_commit/report_url/testcase_url）。与预飞脚本同口径（meta 优先于 crash_dataset）。"""
    import glob
    meta = {}
    for f in glob.glob(os.path.join(CRASH_TESTCASE_DIR, "**", "*.json"), recursive=True):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if d.get("bug_id"):
            meta[d["bug_id"]] = d
    return meta


def rotate_existing_log(log_path):
    """[W5 N25 → **N40 推广到 reproduce 侧**] 写日志前，若同名文件已存在 → **改名保留**。

    权威实现放这里（不放 `build_orchestrator`）是因为**两侧都要用**：
      * ② `logs/build/<project>_<san>_<commit>.log` —— N25 原本只修了这一侧；
      * ③ `logs/reproduce/<osv_id>[_rN].log` —— **N40：一直用 `open(…,"w")` 无条件截断**。
    ✅ N40 实证：复现记录表里跑过多轮的 crash **113 条**（最多 6 行），盘上只剩 1 份日志的 **110 条**
      → 早先各轮的 reproduce 日志**已被静默覆盖**；对照 `logs/build/` 有 **71** 个轮转文件、
      `logs/reproduce/` 有 **0** 个。文件名里的 `_r{i}` 只管**同一轮内的重试**（N16），跨轮次不管。
    返回轮转后的路径；目标不存在则返回 None（不产生空文件）。
    """
    if not os.path.isfile(log_path):
        return None
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S")
    rot = f"{log_path}.{stamp}"
    k = 1
    while os.path.exists(rot):                 # 同一秒内多次 → 加序号，不互相覆盖
        rot = f"{log_path}.{stamp}.{k}"
        k += 1
    os.replace(log_path, rot)
    return rot


def load_recovered():
    """`crash_state_recovered.jsonl` → {osv_id: {frames, is_file_frame, …}}（ground-truth 栈帧）。"""
    return {d["osv_id"]: d for d in load_jsonl(CRASH_STATE_RECOVERED)}


def load_osv(osv_id):
    fp = os.path.join(OSV_CACHE_DIR, f"{osv_id}.json")
    if not os.path.exists(fp):
        return None
    try:
        return json.load(open(fp, encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def load_all_osv():
    import glob
    out = {}
    for f in glob.glob(os.path.join(OSV_CACHE_DIR, "*.json")):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if d.get("id"):
            out[d["id"]] = d
    return out


def ossfuzz_project_dirs(root=None):
    root = root or OSS_FUZZ_MAIN
    p = os.path.join(root, "projects")
    return set(os.listdir(p)) if os.path.isdir(p) else set()


# ============================================================ 帧归一化（逐字复用 preflight）
def _extract_normalize_impl():
    """用 ast 从 `preflight/normalize_frames.py` 逐字提取 normalize 实现。

    为什么不用 import：该脚本是**一次性测量脚本**，模块级代码会立即跑完整套 R2/R5/R6/R7
    测量并打印；import 它有副作用。为什么不用复制：复制会出现两份实现、迟早分叉
    （任务明确要求「别重写」）。故按 AST 节点提取源码并 exec 到独立命名空间——
    提取不到就 raise，绝不静默用另一份实现。
    """
    if not os.path.exists(PREFLIGHT_R2):
        raise RuntimeError(
            f"normalize_frames 的权威实现不存在: {PREFLIGHT_R2}\n"
            "本模块按「不重写、逐字复用」原则从该脚本 AST 提取；文件缺失即失败，"
            "不做静默回退（防两份实现分叉）。")
    src = open(PREFLIGHT_R2, encoding="utf-8").read()
    tree = ast.parse(src)
    want_fn = {"normalize_one_frame", "normalize_frames"}
    want_var = {"INTERNAL_PREFIXES", "SUFFIX_RE", "LAMBDA_RE"}
    ns = {"re": re}
    for node in tree.body:
        keep = False
        if isinstance(node, ast.FunctionDef) and node.name in want_fn:
            keep = True
        elif isinstance(node, ast.Assign):
            keep = any(isinstance(t, ast.Name) and t.id in want_var for t in node.targets)
        if keep:
            mod = ast.Module(body=[node], type_ignores=[])
            exec(compile(mod, PREFLIGHT_R2, "exec"), ns)   # noqa: S102 受控输入（本仓库脚本）
    # normalize_frames 依赖模块级全局 `rec`（原脚本在 import 时从 crash_state_recovered.jsonl 加载）；
    # AST 提取只带函数定义、不带数据 → 这里按同一份数据文件补上，避免运行期 NameError。
    rec = {}
    if os.path.isfile(CRASH_STATE_RECOVERED):
        with open(CRASH_STATE_RECOVERED, encoding="utf-8") as fh:
            for line in fh:
                d = json.loads(line)
                rec[d["osv_id"]] = d
    ns["rec"] = rec
    missing = (want_fn | want_var) - set(ns)
    if missing:
        raise RuntimeError(f"从 {PREFLIGHT_R2} 提取 normalize 实现失败，缺 {sorted(missing)}")
    return ns


_NORM = _extract_normalize_impl()
INTERNAL_PREFIXES = _NORM["INTERNAL_PREFIXES"]
SUFFIX_RE = _NORM["SUFFIX_RE"]
LAMBDA_RE = _NORM["LAMBDA_RE"]


def install_recovered(rec):
    """把 recovered 帧表装进提取来的命名空间——`normalize_frames(osv)` 在 preflight 里
    就是闭包引用模块级 `rec`（`{osv_id: {frames, is_file_frame}}`），故必须同样注入。"""
    _NORM["rec"] = rec
    return rec


def normalize_one_frame(fr, is_file):
    """= preflight 的 `normalize_one_frame`（同一份代码对象）。"""
    return _NORM["normalize_one_frame"](fr, is_file)


def normalize_frames(osv_id, topk=3):
    """= preflight 的 `normalize_frames`（recovered top-3，归一化后）。"""
    return _NORM["normalize_frames"](osv_id)[:topk]


# observed 侧**附加**过滤（设计 §1.3④ 步骤 3 明确列了 `main`/libc）：
# recovered 侧的 `INTERNAL_PREFIXES` 不含 `main`，因为 ClusterFuzz 的 ground-truth 栈
# （DEDUP_TOKEN）里本来就没有它；而 observed 侧的完整栈**有**（✅ P0 实测 md4c：`main` 在 #15、
# libc 在 #16-18、`LLVMFuzzerTestOneInput` #11、`fuzzer::*` #12-15）。
# [实现 W2] 这不是重写归一化——逐帧仍走 AST 提取来的同一份 `normalize_one_frame`，
# 只在其后追加「模块帧/`main`」两类 observed 独有的非项目帧过滤。
OBSERVED_EXTRA_DROP = ("main",)
# **[N39]** 剥完参数签名后，`A::operator()` 会剩下空括号 → 与 `normalize_one_frame` 里
# `re.sub(r"::operator\(\)$","::operator",f)` 的尾处理保持一致（同一目标形态，不新造规则）。
OPER_PAREN_RE = re.compile(r"::operator\(\)$")


def strip_cpp_signature(f):
    """**[N39]** 剥掉 C++ **参数签名**：`A::b(std::__1::basic_string<char,…> const&) const` → `A::b`。

    为什么需要：observed 侧的栈来自 ASan/MSan 的**符号化输出**，带完整参数类型；
    而 recovered 侧（R，ground truth）来自 ClusterFuzz 的 `DEDUP_TOKEN`/crash state，
    **只有函数名**。两者逐字比对必然不等 → ✅ 实测 17 条 hunspell 明明
    `crash_type` 一致、函数名也一致，却因签名差异拿到 `score_subseq=0.0`，只能判 **medium**。

    ⚠ **只用在 observed 侧**（`normalize_observed`）。绝不能塞进 `normalize_one_frame`：
    那是从 `preflight/history/normalize_frames.py` **AST 逐字提取**的权威实现，
    R/O 两侧共用；改它等于同时改 ground truth，并与历史结果分叉（N4 同族事故）。

    ⚠ 不引入新的假 strict：R 侧本来就没有签名粒度，把 O 降到同一粒度是**对齐**而非放宽；
    重载折叠（`f(int)`/`f(double)` 同为 `f`）是 R 侧 ground truth 固有的，不是本函数带来的。
    """
    if not f:
        return f
    s = str(f)
    i = s.find("(")
    while i > 0 and s[:i].rstrip().endswith("operator"):   # `operator()` 的括号是**函数名本身**
        j = s.find("(", i + 1)
        if j < 0:
            break
        i = j
    if i > 0:
        s = s[:i]
    s = OPER_PAREN_RE.sub("::operator", s.strip())          # 与 normalize_one_frame 的尾处理一致
    return s.strip()


def normalize_observed(frames):
    """observed 完整栈归一化：**不截断**（§1.3④ 步骤 1），逐帧走同一份 `normalize_one_frame`，
    再剔 `main` 与「只有模块路径没有函数名」的帧（形如 `/lib/x86_64-linux-gnu/libc.so.6`）。

    **[N39]** 末尾追加 `strip_cpp_signature`：observed 是符号化输出（带参数类型），
    recovered 是 DEDUP_TOKEN（只有函数名）→ 不剥签名则逐字比对必然失败。
    """
    out = []
    for f in frames or []:
        if not f:
            continue
        s = str(f).strip()
        if s in OBSERVED_EXTRA_DROP:
            continue
        # 模块帧（无符号）：以 / 开头或 .so 结尾、且不含空格 → 非项目函数帧
        if (s.startswith("/") or s.endswith(".so") or ".so." in s) and " " not in s:
            continue
        nf = normalize_one_frame(s, False)
        if nf:
            nf = strip_cpp_signature(nf)
            if nf and nf not in OBSERVED_EXTRA_DROP:
                out.append(nf)
    return out


# R2-extra（✅ 实测值，`python3 preflight/normalize_frames.py` 的 R2-extra 段）：
# 用于验证提取来的实现确实是那一份（逐项对账，任一不符即 ❌）
R2_EXTRA_EXPECTED = {"n_with_frames": 3770, "n_key_changed": 502, "n_removal_only": 498,
                     "n_text_norm": 4, "fire_file": 635, "fire_internal": 22,
                     "fire_suffix": 0, "fire_auto": 4, "fire_lambda": 0, "fire_oper": 0}


def verify_normalize_frames(rows=None, rec=None, verbose=False):
    """复算 R2-extra 的全部逐帧计数并与实测值对账（= 证明「用的是同一份实现」）。

    计数逻辑逐行对齐 `preflight/normalize_frames.py:93-125`（含 text_fired /
    removal_fired 的判定顺序），只把 `normalize_frames` 换成本模块提取来的同一个对象。
    """
    rows = rows if rows is not None else load_crash_dataset()
    rec = rec if rec is not None else load_recovered()
    install_recovered(rec)
    c = Counter()
    for r in rows:
        d = rec.get(r["osv_id"], {})
        raw = d.get("frames") or []
        if not raw:
            continue
        iff = d.get("is_file_frame") or [False] * len(raw)
        c["n_with_frames"] += 1
        if normalize_frames(r["osv_id"]) != tuple(raw[:3]):
            c["n_key_changed"] += 1
        text_fired = removal_fired = False
        for i, f in enumerate(raw):
            fs = str(f).strip() if f else ""
            if not fs:
                continue
            if iff[i] if i < len(iff) else False:
                c["fire_file"] += 1
                removal_fired = True
                continue
            if any(fs.startswith(p) or p in fs for p in INTERNAL_PREFIXES):
                c["fire_internal"] += 1
                removal_fired = True
                continue
            s2 = SUFFIX_RE.sub("", fs)
            if s2 != fs:
                c["fire_suffix"] += 1
                text_fired = True
            s3 = re.sub(r"^auto\s+", "", s2)
            if s3 != s2:
                c["fire_auto"] += 1
                text_fired = True
            s4 = LAMBDA_RE.sub("", s3)
            if s4 != s3:
                c["fire_lambda"] += 1
                text_fired = True
            s5 = re.sub(r"::operator\(\)$", "::operator", s4).strip()
            if s5 != s4:
                c["fire_oper"] += 1
                text_fired = True
        if text_fired:
            c["n_text_norm"] += 1
        if removal_fired and not text_fired:
            c["n_removal_only"] += 1
    got = {k: c[k] for k in R2_EXTRA_EXPECTED}
    ok = got == R2_EXTRA_EXPECTED
    if verbose or not ok:
        print(f"[verify_normalize_frames] ok={ok}\n  got     ={got}\n  expected={R2_EXTRA_EXPECTED}")
    return ok, got


# ============================================================ 派生 helper
def osv_year(osv_id):
    """M1：从 `OSV-YYYY-NNN` 抽年份（背景/分层用，非分流键——R1 已撤回年份硬分流）。"""
    m = re.match(r"OSV-(\d{4})-", osv_id or "")
    return int(m.group(1)) if m else None


def read_project_yaml_key(project, key, root=None):
    """与 `preflight/r1_r13_r14_routing_scale.py:22-28` 同口径（crude 行匹配，不引入 yaml 依赖）。"""
    yp = os.path.join(root or OSS_FUZZ_MAIN, "projects", project, "project.yaml")
    if not os.path.exists(yp):
        return None
    try:
        for line in open(yp, encoding="utf-8", errors="replace"):
            m = re.match(rf"\s*{re.escape(key)}\s*:\s*([^\s]+)", line)
            if m:
                return m.group(1).strip('"\'')
    except OSError:
        return None
    return None


def language_of(project, of_dirs=None, _cache={}):
    """R5 exact-match：project 不在 oss-fuzz/projects/ → `unknown(name-miss)`（**不做 substr
    回落**，原 M3b 因回落把 unrar26 误映 junrar 致 jvm 虚高）。"""
    key = (project, tuple(sorted(of_dirs)) if of_dirs is not None else None)
    if key in _cache:
        return _cache[key]
    if of_dirs is not None and project not in of_dirs:
        lg = "unknown(name-miss)"
    else:
        lg = read_project_yaml_key(project, "language") or "(yaml无language)"
    _cache[key] = lg
    return lg


_CT_SUFFIX_RE = re.compile(
    r"\s+(READ|WRITE|of size \d+|\{\*\}|UNKNOWN)?\s*\d*\s*$", re.I)


def normalize_crash_type(ct):
    """crash_type 归一化（④ medium 档比对用；🅗 observed 侧形态仅 P0 测过 md4c 一例）。

    `Heap-buffer-overflow READ 1` / `heap-buffer-overflow ... READ of size 1` → `heap-buffer-overflow`。
    保留原值于 `crash_type_expected`，归一值另存，比对时可复核。
    """
    if not ct:
        return ""
    s = str(ct).strip()
    s = re.split(r"[\r\n]", s)[0]                     # 取首行
    # **[N59①] 十六进制地址不属于 crash 类型。** ✅ 实测 `OSV-2020-1373`（unicorn/memory）：
    #   observed = `SEGV on unknown address 0x7fb916c00470 (pc 0x…)` → 归一成
    #   `segv-on-unknown-address-0x7fb916c00470`，而 expected 是 `segv-on-unknown-address`
    #   → `crash_type_match=False` → 被压在 loose。
    #   ASan 那条路是**硬编码** `"Segv on unknown address"`（不含地址）所以没这问题；
    #   MSan 的 `MSAN_ERR_RE` 捕获到 `(` 之前，把地址一起带进来了。
    #   放在**共享**归一化里（两侧对称）：地址是运行时值，不是类型的一部分。
    s = re.split(r"\s+0x[0-9a-fA-F]+\b", s)[0].strip()
    s = _CT_SUFFIX_RE.sub("", s).strip()
    s = re.sub(r"\s+\{\*\}\s*$", "", s).strip()
    s = re.sub(r"\s+(READ|WRITE)\b.*$", "", s, flags=re.I).strip()
    s = re.sub(r"[_\s]+", "-", s.lower())
    s = re.sub(r"[^a-z0-9\-]", "", s)
    return s.strip("-")


def sanitizer_of(row, meta):
    """→ (sanitizer, sanitizer_inferred)。口径同预飞：meta 优先、其次 crash_dataset。
    空 sanitizer（C/C++ 25 条）→ 默认 `address`(R10 `constants.py:21`) + `sanitizer_inferred=True`(R16/§7B2)。"""
    m = meta or {}
    raw = m.get("sanitizer") or row.get("sanitizer") or ""
    san = SANITIZER_ALIASES.get(raw, raw).strip().lower()
    if san in ("", "none"):
        return DEFAULT_SANITIZER, True
    return san, False


def job_arch(job_type):
    """从 `job_type` 解析**架构**（[实现 W2] 新发现 **N8**）。

    ✅ W2 实测：`job_type` 形如 `libfuzzer_asan_i386_hunspell` → **i386**；无架构标记
    （`libfuzzer_asan_ghostscript`）= OSS-Fuzz 默认 **x86_64**。
    全量分布：i386 **164**（4.3%；可执行 3,136 中 **163**）、无标记 3,606、空 20。
    ⚠ ②/③ 本轮全部按 x86_64 构建（`build_specified_commit --architecture` 默认 x86_64），
    故 **i386 专属崩溃在 x86_64 上结构性不可复现**（✅ 实证：hunspell OSV-2022-886 在
    HEAD + 三格钉版共 4 个版本上全 none，而其 `job_type=libfuzzer_asan_i386_hunspell`）。
    **不据此 skip**（很多内存错与架构无关），只作分层先验，交实测判定。
    """
    jt = (job_type or "").lower()
    if not jt:
        return None
    if "_i386" in jt or jt.endswith("i386"):
        return "i386"
    if "aarch64" in jt or "arm64" in jt:
        return "aarch64"
    return "x86_64"


def fuzz_target_of(row, meta):
    m = meta or {}
    return (m.get("fuzz_target") or row.get("fuzz_target") or "").strip()


def crash_cluster_id(project, crash_type, norm_frames):
    """M7+R2：`(project, crash_type, 归一化 recovered top-3)` 的哈希（**基于归一化帧**，R2）。"""
    key = json.dumps([project, crash_type or "", list(norm_frames or [])],
                     ensure_ascii=False, sort_keys=True)
    return "cl_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def testcase_facts(path):
    """M8：testcase sha256 + size + `input_magic`（前 16 字节可打印表示）。缺文件 → None 三件。"""
    if not path or not os.path.exists(path):
        return None, None, None, False
    try:
        with open(path, "rb") as f:
            head = f.read(16)
            f.seek(0)
            h = hashlib.sha256()
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        size = os.path.getsize(path)
    except OSError:
        return None, None, None, False
    magic = "".join(chr(b) if 32 <= b < 127 else f"\\x{b:02x}" for b in head)
    return h.hexdigest(), size, magic, True


# ============================================================ OSV 解析（R13a / N6）
def osv_fixed_and_repo(osv_rec, introducing_commit=None):
    """R13a 选择规则（✅ 实测 3,301 条 0 歧义）+ repo 与 fixed **同 range 配对**。

    规则：①`introducing_commit` 匹配某 `introduced` → 取配对 `fixed`；②无匹配 → 取最后一个
    `fixed`；③多匹配 → 取最后并标 `intro_match_multi`（notes）。
    → (fixed, repo, rule, n_pairs, introduced)

    [实现 W2 Phase0a] `"0"`/`""` 是 OSV 的**哨兵**（`introduced:"0"` = 从最初即有漏洞，
    不是 commit sha），故**永不参与规则① 匹配**——此处设防而非依赖调用方归一：
    ✅ 实测全量 9 条 crash 的 `introducing_commit` 是 `"0"` 且其 OSV 内也含 `introduced:"0"`
    事件，传原始值必然假匹配（R1 预飞脚本就是这么错的：报「15 条走取最后 fixed」，真值 **24**；
    ① 因 `manifest_builder.py:145` 已归一而未受影响，W1 抽样脚本 `:563-564` 亦然）。
    """
    if not osv_rec:
        return None, None, "no_osv", 0, None
    pairs = []
    any_repo = None          # [实现 W1] 修：repo 不得只在「有 fixed 的 range」里找
    any_introduced = None    #   （原实现致 repo_url 只有 3,550 条，而 R13b 实测 3,776 条
    for a in (osv_rec.get("affected") or []):   #   = 99.6%；no_fixed 的 240 条也有 repo）
        for rng in (a.get("ranges") or []):
            repo = rng.get("repo")
            if repo and not any_repo:
                any_repo = repo
            cur = None
            for e in (rng.get("events") or []):
                if "introduced" in e:
                    cur = e["introduced"]
                    if cur and cur != "0" and not any_introduced:
                        any_introduced = cur
                elif "fixed" in e:
                    pairs.append((cur, e["fixed"], repo))
                    cur = None
    fixeds = [(i, f, r) for (i, f, r) in pairs if f]
    if not fixeds:
        return None, any_repo, "no_fixed", len(pairs), any_introduced
    if introducing_commit in ("", "0"):
        introducing_commit = None          # [实现 W2 Phase0a] 哨兵不参与匹配
    matched = [(i, f, r) for (i, f, r) in fixeds
               if i and i not in ("", "0") and introducing_commit
               and i == introducing_commit]
    if matched:
        i, f, r = matched[-1]
        return f, (r or any_repo), ("intro_match" if len(matched) == 1
                                    else "intro_match_multi"), len(pairs), (i or any_introduced)
    i, f, r = fixeds[-1]
    return f, (r or any_repo), "last_fixed", len(pairs), (i or any_introduced)


def is_degenerate_range(osv_rec):
    """**N6**（[实现 W1] 新发现）：OSV 某 range 的 `introduced == fixed` → vulnerable 窗口为空，
    `fixed^` 早于 bug 引入 → 钉版必然假 none。✅ 全量实测 60 对 / 53 条记录 / 53 crash(1.4%)。
    返回命中的 sha 列表（空 = 非退化）。"""
    if not osv_rec:
        return []
    hits = []
    for a in (osv_rec.get("affected") or []):
        for rng in (a.get("ranges") or []):
            cur = None
            for e in (rng.get("events") or []):
                if "introduced" in e:
                    cur = e["introduced"]
                elif "fixed" in e:
                    if cur and cur == e["fixed"]:
                        hits.append(cur)
                    cur = None
    return hits


def osv_repos(osv_rec):
    if not osv_rec:
        return []
    out = []
    for a in (osv_rec.get("affected") or []):
        for rng in (a.get("ranges") or []):
            if rng.get("repo") and rng["repo"] not in out:
                out.append(rng["repo"])
    return out


ISSUE_RE = re.compile(r"[?&]id=(\d+)")


def issue_id_of(report_url):
    """OSS-Fuzz Monorail issue id（`report_url` 的 `?id=<n>`）。✅ 全量 **3,790/3,790** 可解析。

    [实现 W2 Phase0b] 这个号**按报告时间单调递增**，而修复通常紧随报告（天–周级）→ 它是
    pin commit 日期的**离线最优代理**（实测：对真实 commit author date 的 Spearman
    **同年组内 +0.733**，优于 `osv_id` 字典序 +0.478 与 OSV `published` +0.456；
    era 邻接命中 65.9% vs 52.4%，达真实日期上界 69.5% 的 95%。
    见 `preflight/w2_phase0b_queue_order.py`）。
    两处用途：① 静态 check 打分器的 `issue_id_in_msg` 信号（+3）；② `pinned_queue` 的
    项目内排序键（让同 era 的钉版构建相邻 → N4 era 缓存才命中）。
    """
    if not report_url:
        return None
    m = ISSUE_RE.search(report_url)
    return int(m.group(1)) if m else None


# ============================================================ fixed^ 解析（§5⓪：经 repo_manager）
def get_parent_local(repo_dir, commit, count=1):
    """§5⓪「`fixed^` SHA 解析（经 `repo_manager.get_parent`）」——用于 ② 构建期
    （宿主已有 /src 副本、宿主有代理，`fetch_unshallow` 可跑）。

    manifest 阶段**不用**它（那时没有本地 clone）；① 走 `static_check` 的 patch 链解析
    （0 clone、0 API）。两条路径都给出同一个量：`get_parent(commit, count)` = `commit~count`。
    """
    infra = os.path.join(OSS_FUZZ_WORKTREE, "infra")
    if infra not in sys.path:
        sys.path.insert(0, infra)
    import repo_manager                                   # noqa: PLC0415 worktree 官方版
    return repo_manager.RepoManager(repo_dir).get_parent(commit, count)


# ============================================================ repo_path 解析（[实现 W1]）
def norm_repo_url(u):
    """URL 归一化以便跨协议/镜像比较（与 `w1_repo_path_scan.py` 同规则）。"""
    if not u:
        return ""
    u = u.strip().strip('"\'').lower()
    u = re.sub(r"^[a-z+]+://", "", u)
    u = re.sub(r"^[^/@]+@", "", u)
    u = re.sub(r"^www\.", "", u)
    u = re.sub(r"\.git$", "", u)
    return u.rstrip("/")


_REPO_MAP_CACHE: dict = {}


def load_repo_path_map(path=None, quiet=False):
    """`artifacts/repo_path_map.json`（由 `preflight/w1_repo_path_scan.py` 生成）。

    ⚠ **[W5 修正 docstring]** 原文写「缺失时返回空表 → `resolve_repo_path` 回退
    `/src/<project>` 并标 `medium`」——**与代码实际行为相反**：`resolve_repo_path`
    在查不到项目条目时返回 `(None, "none", [])`（见其内注释「宁缺勿错」），
    因为给一个看似可用的 `/src/<project>` 会让 ② 误用（实测反例 xpdf→/src/freetype）。
    缺失时**不崩**、但 `repo_path` 全为 None → ② 回退 `detect_main_repo`。
    ✅ W5 实测踩到：`--repo-map` 指向不存在的路径 → 3 条已知答案的 `repo_path` 全 None、
    回归从 25/0/4 变成 22/**3 不符**/4（正是这条 docstring 把我引向「以为是 static-check 的锅」）。
    """
    path = path or REPO_PATH_MAP
    if path in _REPO_MAP_CACHE:
        return _REPO_MAP_CACHE[path]
    data = {"projects": {}, "meta": {}}
    if os.path.exists(path):
        try:
            data = json.load(open(path, encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            if not quiet:
                print(f"[repro_common] ⚠ repo_path_map 读取失败({e})，回退 /src/<project>",
                      file=sys.stderr)
    elif not quiet:
        print(f"[repro_common] ⚠ 缺 {path}（先跑 preflight/w1_repo_path_scan.py）；"
              f"repo_path 一律回退 /src/<project>", file=sys.stderr)
    _REPO_MAP_CACHE[path] = data
    return data


def resolve_repo_path(project, osv_repo_urls, map_path=None):
    """逐 crash 解析 `repo_path`（**不能按项目猜**，实测反例见 §7.3/7.4 of the W1 report）。

    → (repo_path|None, confidence, candidates)
      high       OSV repo 归一化后精确匹配唯一 clone dest（实测 C/C++ 91.1%）
      medium     无 URL 匹配，但 `/src/<project>` 确在该项目 dest 集内（6.5%）
      candidates 同一 repo 被 clone 到多个目录（openssl/capstone/open62541，1.4%）→
                 运行期在宿主 /src 副本上 `git cat-file -e <commit>` 逐个试
      none       无匹配 / dest 非 /src 直接子目录（qt，basename 拼接会指错）→ 回退 detect_main_repo
    ❌ 不做「仅一个 clone 就用它」的回退：实测会选到**依赖仓库**（xpdf→/src/freetype、
       mosquitto→/src/libprotobuf-mutator）。宁可 none，不给错值。
    """
    pm = load_repo_path_map(map_path)
    projects = pm.get("projects") or {}
    pi = projects.get(project)
    default = f"/src/{project}"
    if not pi:
        # 无映射表条目（项目不在 worktree，如 unrar 的 M2 name-miss；或映射表未生成）：
        # **返回 None 而不是默认值**——conf=none 时 ② 会回退 detect_main_repo，但若同时给出
        # 一个看似可用的 repo_path，就有被误用的风险（宁缺勿错，与「不做单-clone 回退」同理）。
        return None, "none", []
    clones = pi.get("clones") or []
    if not clones:
        return None, "none", []
    want = {norm_repo_url(u) for u in (osv_repo_urls or []) if u}
    hit = [c for c in clones if c.get("url_norm") in want]
    if len(hit) == 1 and not hit[0].get("dynamic"):
        return _depth_check(hit[0]["dest"], "high")
    if len(hit) > 1:
        ds = sorted({c["dest"] for c in hit if c.get("dest") and not c.get("dynamic")})
        if len(ds) == 1:
            return _depth_check(ds[0], "high")
        return None, "candidates", ds
    dests = sorted({c["dest"] for c in clones if c.get("dest") and not c.get("dynamic")})
    if default in dests:
        return _depth_check(default, "medium")
    return None, "none", []


def _depth_check(dest, conf):
    """假设 (B)：dest 必须是 /src 的直接子目录，否则 `build_specified_commit.py:425` 的
    `os.path.basename` 拼接会指错目录（✅ 实测反例 qt → `/src/qt/qt5`）。"""
    if (dest and dest.startswith("/src/") and "$" not in dest
            and len([x for x in dest.split("/") if x]) == 2):
        return dest, conf, []
    return None, "none", [dest] if dest else []


# ============================================================ 静态 check（[实现 W1]，需网络、可关）
DOC_CI_RE = re.compile(
    r"(^|/)(\.github|\.gitlab|\.circleci|\.ci|ci|doc|docs|documentation|www|website|"
    r"packaging|dist|debian|snap|\.devcontainer|\.azure)(/|$)"
    r"|\.(md|rst|txt|yml|yaml|toml|ini|cfg|spec|cmake|ps1|bat|svg|png|gif|ico|pdf|po)$"
    r"|(^|/)(UPGRADING|CHANGELOG|CHANGES|NEWS|README|LICEN[CS]E|AUTHORS|CONTRIBUTING|"
    r"CODE_OF_CONDUCT|TODO|CREDITS|MAINTAINERS|\.gitignore|\.mailmap)", re.I)
TEST_RE = re.compile(
    r"(^|/)(tests?|testdata|testing|testcases?|fuzz|fuzzers|fuzzing|regressions?|"
    r"corpus|seeds?)(/|$)|_test\.(c|cc|cpp)$|(^|/)test_[^/]*\.(c|cc|cpp)$", re.I)
OFZ_REF_RE = re.compile(r"ofz\s*#?\d+|oss-fuzz|ossfuzz|clusterfuzz|bugs\.chromium\.org", re.I)
FIX_INTENT_RE = re.compile(
    r"\bfix(es|ed|ing)?\b|\bcrash(es|ed|ing)?\b|overflow|underflow|sanitiz|"
    r"\bCVE-|use-after-free|\buaf\b|null[- ]?deref|\boob\b|\bheap\b|\bsegv\b|"
    r"\basan\b|\bmsan\b|\bubsan\b|\btsan\b|out[- ]of[- ]bound|\bbound(s)?\b|"
    r"\bleak\b|uninitiali[sz]ed|\bassert\b|\bdouble[- ]free\b|\bundefined\b", re.I)
# [实现 W2 Phase0c] **N7**：「加/改 fuzzing harness」类 commit **不可能是库漏洞的修复**，
# 但它天然满足打分器的两个强信号（消息提 OSS-Fuzz → `ofz_ref` +2；diff 动被测函数 →
# `frames_in_diff` +2）→ 在 N6 退化 range 上造成 **6/8 = 75% 假阳性**。
# 实测（preflight/w2_phase0c_degenerate.py，40 条取到 patch）：命中 7 条 = 全部 6 个假阳性
# + 1 条 S=0 的同族 commit；**不**命中两个必须放行的（file「Use signed offsets to reduce
# false positives」、h3「Add error return codes to gridDisk functions」）→ 精确率 7/7、无误杀。
# ⚠ 只作**取消资格**信号、且**只用于 N6 退化复核**（`resolve_degenerate`）：
#   不改 `score_commit` 的任何权重 → W1 已标定的 off-by-one 14.3% 不受影响（S 值逐条不变）。
HARNESS_RE = re.compile(
    r"(?:\b(?:add|added|adds|adding|include|includes|introduce|introducing|new|create|created)\b"
    r"[^.]{0,40}?\b(?:fuzz(?:er|ers|ing)?(?:\s+(?:target|harness|corp(?:us|ora)))?"
    r"|oss-?fuzz(?:\s+target)?|clusterfuzz|corp(?:us|ora)|sanitiz\w+)\b)"
    r"|(?:\bmake\b[^.]{0,50}\bpublic\b[^.]{0,30}\bfuzzer\b)"
    r"|(?:\bfuzz(?:er|ing)?\s+(?:target|harness|corp(?:us|ora))\b)", re.I)
OFZ_NUM_RE = re.compile(r"ofz\s*#?\s*(\d{3,7})", re.I)
GITHUB_RE = re.compile(r"^(?:https?|git)://(?:www\.)?github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", re.I)
GITLAB_HOSTS = ("gitlab.com", "gitlab.gnome.org", "gitlab.freedesktop.org", "invent.kde.org")
GITLAB_RE = re.compile(r"^(?:https?|git)://(" + "|".join(map(re.escape, GITLAB_HOSTS)) +
                       r")/(.+?)(?:\.git)?/?$", re.I)
PATCH_CACHE_DIR = "/tmp/opencode/ofz_patch_cache"


def classify_repo(repo):
    if not repo:
        return ("other", "no-repo", None)
    m = GITHUB_RE.match(repo)
    if m:
        return ("github", m.group(1), m.group(2))
    m = GITLAB_RE.match(repo)
    if m:
        return ("gitlab", m.group(1), m.group(2))
    return ("other", re.sub(r"^[a-z+]+://", "", repo).split("/")[0] or "malformed", None)


def http_get(url, tries=3, timeout=40, cache=True):
    """经宿主代理 GET（✅ P0 实测 clash 仅绑 loopback、宿主可用）。缓存于 /tmp（非交付物）。"""
    if cache:
        os.makedirs(PATCH_CACHE_DIR, exist_ok=True)
        fp = os.path.join(PATCH_CACHE_DIR,
                          hashlib.sha256(url.encode()).hexdigest()[:24] + ".blob")
        if os.path.exists(fp):
            return open(fp, encoding="utf-8", errors="replace").read(), "cache"
    else:
        fp = None
    op = urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    op.addheaders = [("User-Agent", "repro-manifest-builder/1.0 (research)")]
    last = None
    for i in range(tries):
        try:
            with op.open(url, timeout=timeout) as r:
                txt = r.read().decode("utf-8", "replace")
                if fp:
                    try:
                        open(fp, "w", encoding="utf-8").write(txt)
                    except OSError:
                        pass
                return txt, r.status
        except urllib.error.HTTPError as e:
            return None, f"http{e.code}"
        except Exception as e:                                   # noqa: BLE001 网络异常一律重试
            last = f"{type(e).__name__}"
            time.sleep(1.0 * (i + 1))
    return None, last or "err"


def parse_patch(txt):
    """解析 mbox 式 patch（`.patch` 端点）→ sha/date_raw/message/files/body。"""
    if not txt:
        return None
    m = re.match(r"^From ([0-9a-f]{7,40}) ", txt)
    sha = m.group(1) if m else None
    dm = re.search(r"^Date: (.+)$", txt, re.M)
    date_raw = dm.group(1).strip() if dm else None
    msg_lines, in_msg = [], False
    for line in txt.splitlines():
        if line.startswith("Subject:"):
            in_msg = True
            msg_lines.append(re.sub(r"^Subject:\s*(\[PATCH[^\]]*\]\s*)?", "", line))
            continue
        if in_msg:
            if line.startswith("---"):
                break
            if line.startswith(("From:", "Date:", "To:", "Cc:", "In-Reply-To:",
                                "References:", "Message-Id:", "Message-ID:")):
                continue
            msg_lines.append(line.strip())
    message = " ".join(x for x in msg_lines if x).strip()
    idx = txt.find("\ndiff --git ")
    body = txt[idx + 1:] if idx >= 0 else ""
    files = [fm.group(2) for fm in re.finditer(r"^diff --git a/(.+?) b/(.+?)$", txt, re.M)]
    return {"sha": sha, "date_raw": date_raw, "message": message, "files": files,
            "body": body, "has_diff": bool(body.strip())}


def classify_files(files):
    """→ (no_source, test_only)。`no_source`（全 docs/CI/打包/构建配置）= **硬否定**：
    不可能修掉内存安全 crash（✅ 实测 8.3% 的 OSV `fixed` 属此类）。`test_only` = 中性
    （可能就是 harness 修复，此时 `fixed^` 是旧 harness、crash 仍复现）。"""
    if not files:
        return False, False
    no_src = all(DOC_CI_RE.search(f) for f in files)
    return no_src, (not no_src) and all(TEST_RE.search(f) for f in files)


def frame_tokens(fr):
    """帧名 → whole-word 匹配变体（len≥4）。`Class::method` 不单独匹配 method（add/get 太通用）。"""
    variants, cls = [], None
    if "::" in fr:
        cls = fr.split("::")[0].strip()
        meth = fr.split("::")[-1].strip()
        variants.append(fr)
        if len(meth) >= 6:
            variants.append(meth)
    else:
        variants.append(fr)
        base = re.sub(r"^_+", "", fr)
        if base != fr:
            variants.append(base)
        nowidth = re.sub(r"_\d+$", "", base)
        if nowidth != base and len(nowidth) >= 4:
            variants.append(nowidth)
    out, seen = [], set()
    for v in variants:
        v = re.sub(r"<[^>]*>", "", v).strip()
        if len(v) >= 4 and v not in seen:
            seen.add(v)
            out.append(v)
    return out, cls


def score_commit(pc, frames, issue_id):
    """复合证据分 S（权重见 W1 报告 §4）。返回 (score, evidence)。"""
    ev = {"issue_id_in_msg": 0, "frames_in_diff": [], "ofz_ref": 0, "fix_intent": 0,
          "class_or_filestem": [], "frame_path_tokens": [], "harness_like": 0,
          "ofz_other_id": None}
    if not pc:
        return 0, ev
    msg, body, files = pc["message"], pc["body"], pc["files"]
    # [实现 W2 Phase0c] **只记证据、不改分**（N7 的取消资格信号，供 resolve_degenerate 用）
    ev["harness_like"] = 1 if HARNESS_RE.search(msg or "") else 0
    score = 0
    if issue_id and re.search(rf"\b{re.escape(issue_id)}\b", msg):
        ev["issue_id_in_msg"] = 1
        score += 3
    for fr in frames:
        variants, cls = frame_tokens(fr)
        if any(re.search(rf"(?<![A-Za-z0-9_]){re.escape(v)}(?![A-Za-z0-9_])", body)
               for v in variants):
            ev["frames_in_diff"].append(fr)
        elif cls and re.search(rf"(?<![A-Za-z0-9_]){re.escape(cls)}(?![A-Za-z0-9_])", body):
            ev["class_or_filestem"].append(f"{fr}(class {cls})")
    if ev["frames_in_diff"]:
        score += 2
    if OFZ_REF_RE.search(msg):
        ev["ofz_ref"] = 1
        score += 2
        # [实现 W2] **N9**：`ofz_ref` 不校验**是哪个** issue 号 → 修别家 bug 的 commit 也拿 +2。
        # ✅ 实证：hunspell OSV-2022-886（本 id=51242）被归因到 d6836713「ofz#**51277** fix
        # negative condition length」——修的是另一个 issue。W1 48 条链上该形态 0/25（都是泛提
        # oss-fuzz 无号），故**不改权重**（改则 W1 的 off-by-one 14.3% 失效），只把「别家号」
        # 记成证据，交上层标注 `fixed_real_disputed`。
        m_other = OFZ_NUM_RE.search(msg or "")
        if m_other and issue_id and m_other.group(1) != str(issue_id):
            ev["ofz_other_id"] = m_other.group(1)
    if FIX_INTENT_RE.search(msg):
        ev["fix_intent"] = 1
        score += 1
    stems = set()
    for f in files:
        b = re.sub(r"\.(c|cc|cpp|cxx|h|hh|hpp|hxx|C|py|rs|java|go|m|mm)$", "",
                   os.path.basename(f))
        b = re.sub(r"[^a-z0-9]", "", b.lower())
        if len(b) >= 5:
            stems.add(b)
    if stems and not ev["class_or_filestem"]:
        for fr in frames:
            core = re.sub(r"[^a-z0-9]", "", re.sub(r"^_+|_\d+$", "",
                                                   fr.split("::")[-1].lower()))
            if len(core) >= 5 and any(s in core or core in s for s in stems):
                ev["class_or_filestem"].append(f"{fr}~file")
                break
    if ev["class_or_filestem"]:
        score += 1
    if stems and not ev["frame_path_tokens"]:
        for fr in frames:
            toks = set()
            for part in re.split(r"::|<|>|\s", fr):
                toks.update(t.lower() for t in
                            re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z]+|[a-z]+|\d+", part)
                            if len(t) >= 4)
            if len(toks) < 2:
                continue
            for f in files:
                ptoks = {t for t in re.split(r"[^a-z0-9]+", f.lower()) if len(t) >= 4}
                if len(toks & ptoks) >= 2:
                    ev["frame_path_tokens"].append(f"{fr}@{f}")
                    break
            if ev["frame_path_tokens"]:
                break
    if ev["frame_path_tokens"]:
        score += 1
    return score, ev


def _gitlab_parent(host, path, sha):
    url = (f"https://{host}/api/v4/projects/{urllib.parse.quote(path, safe='')}"
           f"/repository/commits/{sha}")
    txt, code = http_get(url)
    if not txt:
        return None, code
    try:
        pids = json.loads(txt).get("parent_ids") or []
        return (pids[0] if pids else None), code
    except json.JSONDecodeError:
        return None, "parse_err"


def locate_fixed_real(fixed_commit, repo_url, frames, issue_id, introduced=None,
                      max_depth=3, sleep=0.0):
    """**[实现 W1] 静态 check 主函数**：深度游走定位真修复。

    C0 = OSV `fixed`，Cd = C0~d。`d_fix` = 最小 d 使 `S(Cd)≥2 且 非 no_source 且 d<intro_depth`
    （末条由 harfbuzz OSV-2018-126 反例确立：**引入 bug 的 commit 必然含帧函数**，会被
    `frames_in_diff` 误命中）。→ `fixed_real=C_{d_fix}`、`pin_commit=C_{d_fix+1}`、
    `walkback_depth=d_fix+1`。

    **不 clone、不用 GitHub API**：github 用 `<sha>~N.patch`（✅ 实测 N=1,2,3 均 200），
    gitlab 用 `/-/commit/<sha>.patch` + `/api/v4` 取 parent_ids。

    → dict(verdict=located/not_located/undecidable, d_fix, walkback_depth, fixed_real,
           pin_commit, chain=[…], why)
    """
    kind, a, b = classify_repo(repo_url)
    if kind == "other":
        return {"verdict": "undecidable", "d_fix": None, "walkback_depth": None,
                "fixed_real": None, "pin_commit": None, "chain": [],
                "why": f"non-github/gitlab host ({a})", "host": a}
    if not frames and not issue_id:
        return {"verdict": "undecidable", "d_fix": None, "walkback_depth": None,
                "fixed_real": None, "pin_commit": None, "chain": [],
                "why": "no usable frames and no OF issue id"}
    base = (f"https://github.com/{a}/{b}/commit" if kind == "github"
            else f"https://{a}/{b}/-/commit")
    chain, cur = [], fixed_commit
    for d in range(max_depth + 1):
        if not cur:
            break
        txt, code = http_get(f"{base}/{cur}.patch")
        if not txt:
            chain.append({"depth": d, "sha": cur, "http": code, "error": True})
            break
        pc = parse_patch(txt)
        if not pc or not pc["has_diff"]:
            chain.append({"depth": d, "sha": (pc or {}).get("sha") or cur, "http": code,
                          "error": True, "why": "no diff body"})
            break
        s, ev = score_commit(pc, frames, issue_id)
        no_src, test_only = classify_files(pc["files"])
        chain.append({"depth": d, "sha": pc["sha"], "msg": pc["message"][:160],
                      "date": pc["date_raw"], "files": pc["files"], "n_files": len(pc["files"]),
                      "S": s, "ev": ev, "no_source": no_src, "test_only": test_only})
        if d + 1 > max_depth:
            cur = None
        elif kind == "github":
            cur = f"{fixed_commit}~{d+1}"
        else:
            cur, _c = _gitlab_parent(a, b, pc["sha"] or cur)
        if sleep:
            time.sleep(sleep)
    ok = [c for c in chain if not c.get("error")]
    if not ok:
        return {"verdict": "undecidable", "d_fix": None, "walkback_depth": None,
                "fixed_real": None, "pin_commit": None,
                "chain": chain, "why": f"no patch retrievable ({chain[0].get('http') if chain else 'n/a'})"}
    intro_depth = None
    if introduced and introduced != "0":
        intro_depth = next((c["depth"] for c in ok if c.get("sha") and
                            (c["sha"].startswith(introduced) or introduced.startswith(c["sha"]))),
                           None)
    d_fix = next((c["depth"] for c in ok
                  if c["S"] >= 2 and not c["no_source"]
                  and (intro_depth is None or c["depth"] < intro_depth)), None)
    res = {"chain": chain, "intro_depth": intro_depth,
           "S_by_depth": {c["depth"]: c["S"] for c in ok},
           "no_source_depths": [c["depth"] for c in ok if c["no_source"]],
           "test_only_depths": [c["depth"] for c in ok if c["test_only"]],
           "depths_fetched": len(ok)}
    if d_fix is None:
        res.update(verdict="not_located", d_fix=None, walkback_depth=None,
                   fixed_real=None, pin_commit=None,
                   why=f"0..{len(ok)-1} 深度内无 (S≥2 且非 no_source 且 d<intro_depth)")
        return res
    pin = ok[d_fix + 1]["sha"] if d_fix + 1 < len(ok) else None
    if pin is None:
        # 需要 pin 的深度超出已抓取范围 → 再抓一格（GitHub 直接 ~N；GitLab 走 API）
        nd = d_fix + 1
        if kind == "github":
            txt, code = http_get(f"{base}/{fixed_commit}~{nd}.patch")
        else:
            psha, _c = _gitlab_parent(a, b, ok[-1]["sha"])
            txt, code = http_get(f"{base}/{psha}.patch") if psha else (None, "no_parent")
        pc = parse_patch(txt) if txt else None
        pin = pc["sha"] if pc else None
        res["pin_fetch_http"] = code
    depth = d_fix + 1
    if intro_depth is not None and depth > intro_depth:
        # clamp：不得钉到 bug 引入之前（会假 none）
        res.update(verdict="located", d_fix=d_fix, walkback_depth=intro_depth,
                   fixed_real=ok[d_fix]["sha"], pin_commit=None,
                   why=f"clamp: d_fix+1={depth} > intro_depth={intro_depth} → 钉版不可用")
        res["clamped"] = True
        return res
    res.update(verdict="located", d_fix=d_fix, walkback_depth=depth,
               fixed_real=ok[d_fix]["sha"], pin_commit=pin,
               why=f"fixed_real=fixed~{d_fix} (S={ok[d_fix]['S']}) → pin=fixed~{depth}")
    return res


# ============================================================ schema（§6.3 的 ① 子集）
# 顺序即 manifest 输出顺序；来源标注见 §6.3 表。
MANIFEST_FIELDS = [
    "osv_id", "project", "project_ossfuzz_dir", "language", "osv_year",
    "fuzz_target", "target_inferred", "sanitizer", "sanitizer_inferred",
    "fuzzing_engine", "job_type", "job_arch", "crash_type_expected", "crash_type_full_expected",
    "crash_type_norm", "crash_cluster_id",
    "introducing_commit", "fixed_commit", "fixed_parent", "fixed_real", "pin_commit",
    "walkback_depth", "fixed_misattributed", "static_check_verdict", "static_check_why",
    "expected_repro_version",
    "osv_degenerate_range", "degenerate_resolved", "commit_source", "fixed_rule", "n_osv_pairs",
    "repo_url", "repo_path", "repo_path_confidence", "repo_path_candidates",
    "testcase_path", "testcase_sha256", "testcase_size", "input_magic",
    "testcase_is_minimized", "recovered_frames", "recovered_is_file_frame",
    "issue_id", "report_url", "testcase_url", "skip_reason", "notes",
]


# ---- ②③④⑤ 追加到 repro_dataset.jsonl 的字段（§1.5）----
# [实现 W2 Phase0d] 在此**先定义好**，⑤ `annotate_dataset` 直接按此顺序落盘，不自行发明。
# 关键区分（任务 Phase 0(d)）：
#   `walkback_depth`       = ① 静态预测 / ② 计划要钉的格数（1=fixed^）
#   `walkback_depth_actual`= **实际**在第几格复现（0=HEAD 即复现；未复现=最后试到的格数，
#                            须与 `reproduced_any` 合读）。分开存的理由：Phase 5(a) 要用真实
#                            depth 分布检验 W1 策略 B vs C 之争（那个争的全部不确定性都在
#                            「未定位者三格全败」这个**仪器假设**上，只有实跑能证伪）。
RUNTIME_FIELDS = [
    # ⑤ 轮次标识（append-only，跨轮同 osv_id 按 run_ts 取最新）
    "run_id", "run_ts",
    # ② 构建
    "repro_version", "commit_source", "oss_fuzz_commit", "pinned_commit", "base_builder_digest",
    "build_status", "build_stage", "build_error_class", "build_seconds", "binary_dir",
    "binary_sha256", "era_commit", "era_cache_hit",
    "walkback_depth_actual", "walkback_exhausted",
    # [实现 W3] N12/N17 的产物：逐格走完后**最佳 tier 那一格**的深度与 tier、试过几格、
    # 几格构建失败（Phase 5(a) 与 B/C 重算的原始依据）；`commit_source_prior` = ① 的先验
    # （W2 的 ⑤ 会用 ② 的实际值**覆盖** `commit_source`，导致先验丢失、跨轮分析必须回 join
    #  manifest —— ✅ W3 实测 109/129 条被覆盖，故两个都存）。
    "walkback_best_depth", "walkback_best_tier", "walkback_depths_tried",
    "walkback_n_build_fail", "commit_source_prior",
    # ③ 复现
    "observed_crash_type", "observed_frames", "exit_code", "signal", "reproduced_any",
    "retry_count", "runtime_limits", "raw_log_path",
    # ④ 分级
    "verification_tier", "frame_match_score", "crash_type_match",
    "score_pos", "score_subseq", "score_set",
    # [实现 W2] 两个新增量：`score_set_top3` = 对 observed top-3 的集合分（= ✅ P0 报告 :194
    # 记的「集合 2/3」口径，也是 §1.3④ 标定点 md4c「set 0.67」唯一能复现的口径）；
    # `score_subseq_frac` = LCS(R,O)/|R|，**分数化**的子序列匹配 —— 因为 `score_subseq`
    # 是二值的，T_strict∈(0,1] 结构上不可能有区分力（见 W2 报告 Phase 5(b)）。
    "score_set_top3", "score_subseq_frac", "run_status",
]
SKIP_REASONS = ("unreproducible_no_target", "missing_testcase", "non_cpp_language",
                "unmapped_project")
# §6.3：repro_version 由 ②③ 填；① 只给 `commit_source` 先验（head/introducing/fixed_parent）
COMMIT_SOURCES = ("head", "fixed_parent", "introducing")


def resolve_degenerate(sha, repo_url, frames, issue_id, sleep=0.0):
    """[实现 W2 Phase0c] **N6 退化 range 的个案复核**——不再一刀切禁钉版。

    N6 原处置的前提是「退化 sha 真的是 introducing commit」→ `sha^` 早于 bug 引入 → 钉版假 none。
    但 `introduced == fixed` 同样可能是 **OSV 定不出区间的数据缺陷**，那个 sha 也可能就是**修复**
    （若是，`sha^` 恰恰是最后一个漏洞版本）。用 W1 现成的复合证据打分器判，**零额外成本**。

    **故意传 `introduced=None`**：若传退化 sha 自身，`intro_depth=0` 会让 `d_fix` 的判据
    （`d < intro_depth`）永假 → 必然 not_located，等于把待检验的前提当输入（循环论证）。

    放行需**同时**满足（逐条实测依据见 `preflight/w2_phase0c_degenerate.py`）：
      ① `S(C0) ≥ 2`（W1 原阈值，不改）；② `¬no_source`（W1 原判据）；
      ③ `¬test_only`（只改测试/语料脚本的 commit 不可能是库漏洞的修复；本样本非绑定）；
      ④ `¬harness_like`（**N7**，本样本的**实际决定性**条件，挡掉 6 个假阳性）；
      ⑤ `frames_in_diff ≠ ∅`（推翻一条「禁钉版」规则要有结构性证据；本样本非绑定）；
      ⑥ `pin_commit` 可解析。
    → dict(resolved, pin_commit, fixed_real, walkback_depth, S_C0, reject, verdict, why)
    """
    res = locate_fixed_real(sha, repo_url, frames, issue_id,
                            introduced=None, max_depth=1, sleep=sleep)
    ch = res.get("chain") or []
    c0 = ch[0] if ch else {}
    out = dict(resolved=False, pin_commit=None, fixed_real=None, walkback_depth=None,
               S_C0=c0.get("S"), verdict=res.get("verdict"), why=res.get("why"),
               reject=None, harness_like=bool((c0.get("ev") or {}).get("harness_like")))
    if not c0 or c0.get("error"):
        out["reject"] = f"patch_unavailable({(c0 or {}).get('http', 'n/a')})"
        return out
    if (c0.get("S") or 0) < 2:
        out["reject"] = f"S(C0)={c0.get('S')}<2"
        return out
    if c0.get("no_source"):
        out["reject"] = "no_source"
        return out
    if c0.get("test_only"):
        out["reject"] = "test_only"
        return out
    if out["harness_like"]:
        out["reject"] = "harness_like_commit(N7)"
        return out
    if not (c0.get("ev") or {}).get("frames_in_diff"):
        out["reject"] = "no_frames_in_diff"
        return out
    if not res.get("pin_commit"):
        out["reject"] = "pin_unresolvable"
        return out
    out.update(resolved=True, pin_commit=res["pin_commit"], fixed_real=c0.get("sha"),
               walkback_depth=res.get("walkback_depth") or 1, reject=None)
    return out


def empty_manifest_record(osv_id):
    return {k: None for k in MANIFEST_FIELDS} | {"osv_id": osv_id, "notes": []}


if __name__ == "__main__":
    # 自检：路径常量 + normalize_frames 逐字复用对账（R2-extra 数字）
    print("=" * 70)
    print("repro_common 自检")
    print("=" * 70)
    for name, p in [("crash_dataset", CRASH_DATASET), ("crash_state_recovered", CRASH_STATE_RECOVERED),
                    ("crash_testcase/", CRASH_TESTCASE_DIR), ("_osv_cache/", OSV_CACHE_DIR),
                    ("oss-fuzz 主树", OSS_FUZZ_MAIN), ("worktree", OSS_FUZZ_WORKTREE),
                    ("repo_path_map", REPO_PATH_MAP)]:
        print(f"  {name:<22} {'OK ' if os.path.exists(p) else 'MISS'} {p}")
    rows = load_crash_dataset()
    rec = load_recovered()
    meta = load_crash_testcase_meta()
    print(f"  加载：crash_dataset={len(rows)} recovered={len(rec)} crash_testcase_meta={len(meta)}")
    print(f"  worktree projects/={len(ossfuzz_project_dirs(OSS_FUZZ_WORKTREE))} "
          f"主树 projects/={len(ossfuzz_project_dirs(OSS_FUZZ_MAIN))}")
    ok, got = verify_normalize_frames(rows, rec, verbose=True)
    print(f"  normalize_frames 逐字复用对账: {'✅ 一致' if ok else '❌ 不一致'}")
    print(f"  crash_cluster_id 例: {crash_cluster_id('md4c', 'Heap-buffer-overflow', normalize_frames('OSV-2022-126'))}")
    print(f"  normalize_crash_type('Heap-buffer-overflow READ 1') = "
          f"{normalize_crash_type('Heap-buffer-overflow READ 1')!r}")
    print(f"  N6 degenerate(OSV-2016-6) = {is_degenerate_range(load_osv('OSV-2016-6'))}")
    print(f"  resolve_repo_path(php, [osv repo]) = "
          f"{resolve_repo_path('php', osv_repos(load_osv('OSV-2024-88')))}")
    sys.exit(0 if ok else 1)
