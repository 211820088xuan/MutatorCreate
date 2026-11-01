#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""② `build_orchestrator.py` — 构建编排（DELIVERY §1.3②）。

职责（**只做构建与归档**，不复现、不分级、不写数据集）
----------------------------------------------------
1. **前置 §1.7 H gate**（四条件 + [实现 W2] 第五条镜像污染检查）→ 不过则 ABORT + 写 `BLOCKED.md`。
2. **缓存键 `(project, sanitizer, commit)`**（R16/R17/R18 三层修正的落点）：
   * HEAD 路径的 commit 分量 = **构建时在 builder 镜像内 `git rev-parse HEAD` 解析出的上游 SHA**，
     **绝不用字面 `"HEAD"`**（✅ P0：md4c=`61f5ce76…`、✅ P0-B：pcre2=`aac57f97…`）。
     解析不到（tarball 项目无 `.git`）→ `pinned_commit="UNKNOWN"` + **不跨轮复用**（每轮重建）。
   * 钉版路径的 commit 分量 = `pin_commit`（① 给）或 walk-back 解析出的 `fixed~d` 真实 SHA。
     **严禁**用旧 `(project,sanitizer)` 键复用（同项目两条 crash 的 `fixed^` 通常不同 →
     第二条复用第一条二进制 = **假复现**）。
3. **构建成功即归档**（② 的专属职责）：`build/out/<p>/` → `artifacts/binaries/<p>/<san>/<commit>/`，
   `binary_dir` 指归档位、记 `binary_sha256`；`llvm-symbolizer` 按 sha256 **内容寻址去重 + 硬链接**
   （✅ P0-B：4 个新构建的 symbolizer sha256 完全相同、仅 2 个内容变体）。归档失败 → `archive_failed`
   且**不计入缓存**。
4. **假成功防护**：校验目标二进制**实际存在且可执行且非空**，不轻信退出码
   （✅ 审计B：主树 `ndpi/build.sh:3 set +e` + `:87 exit 0` → 构建恒假成功）。
5. **N4 era 缓存 + worktree 还原**：era commit 由目标 commit 日期**确定性**决定
   （`build_specified_commit.py:243-248`）→ 按 `(project, era_commit)` 缓存学习结果；
   已知「HEAD 配置失败 + era 配置成功」时**预 checkout era、跳过注定失败的首试**
   （✅ P0-B：pcre2 `fixed^` 含 era-retry 9m44s vs 复用 era 残留 4m52s → 省约一半）。
   每次钉版后 `git checkout HEAD -- projects/<p>` 还原（✅ W1：该命令受 pathspec 限制只动
   `projects/`，`infra/` 三补丁 md5 逐一不变）。
6. **walk-back（N3）**：① 判 `located` → 直接钉 `pin_commit`（1 次构建）；`not_located`/
   `undecidable` → depth 1→2→3 逐格，**按 `intro_depth` clamp**（钉到 bug 引入之前 = 假 none），
   首个复现即停（由 ⑥ 结合 ③ 的结果驱动，本模块只负责按计划构建 + 记 `walkback_depth_actual`）。

[实现 W2] 与设计的偏离（都在 §3 报告里说明）
------------------------------------------
* `--stage auto` 需要 ③ 的 observations 才能知道谁没复现 → 本模块的 `auto` 要求 `--observations`；
  没给则退化为 stage1 并告警（不擅自把「全部 crash」都钉一遍，那是 8× 成本）。
* era 日期用 `.patch` 的 **author date**（零 clone），而 `build_specified_commit.py:239` 用
  `git show --format=%ct` = **committer date** → 两者可能跨 `projects/<p>` 变更边界而不一致。
  故 era 预 checkout 是**优化而非前提**：预测错了，官方 era-retry 仍会兜底。实测差异见 W2 报告。

约束：主树 `/root/gyx/oss-fuzz` 只读；只在 worktree 内构建；不改 Dockerfile/build.sh；
不动 driver_create；`infra/` 三补丁不得改动（gate 条件③④ 正向校验）。
"""
from __future__ import annotations

import argparse
import collections
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import repro_common as rc  # noqa: E402

WT = rc.OSS_FUZZ_WORKTREE
BUILD_RECORDS = os.path.join(rc.ARTIFACTS, "build_records.jsonl")
STATE_PATH = os.path.join(rc.ARTIFACTS, "state.json")
BINARIES = os.path.join(rc.ARTIFACTS, "binaries")
SHARED = os.path.join(BINARIES, "_shared")
LOGS = os.path.join(rc.ARTIFACTS, "logs")
BLOCKED = os.path.join(HERE, "BLOCKED.md")
BUILD_OUT = os.path.join(WT, "build", "out")

PROXY_ENV = {"http_proxy": rc.PROXY, "https_proxy": rc.PROXY,
             "HTTP_PROXY": rc.PROXY, "HTTPS_PROXY": rc.PROXY}
ERA_LOG_RE = re.compile(r"Retrying on earlier OSS-Fuzz commit ([0-9a-f]{7,40})")
ARCHIVE_DATA_MAX_BYTES = 32 << 20        # 单个数据文件上限 32MB（.bfbs/.dict 都是 KB 级）
ARCHIVE_DIR_MAX_BYTES = 64 << 20         # **[N66] 单个子目录树总量上限 64MB**
                                         # （espeak-ng-data 实测仅 1.4MB/351 文件；设上限防归档膨胀）
DC_PATTERNS = ("*crfuzzer*",)


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def free_gb(path="/"):
    """[W3 Phase2] 磁盘余量（GB）。"""
    st = os.statvfs(path)
    return st.f_bavail * st.f_frsize / (1 << 30)


def disk_guard(min_free_gb, what):
    """低于阈值 → True（调用方应停止）。**不把盘写满**：单次钉版构建的 build/out + 归档
    实测 ~46MB，但 docker 镜像/中间层可达 GB 级（✅ W2：每个新项目镜像 ~2.2GB）。"""
    if not min_free_gb:
        return False
    f = free_gb()
    if f < min_free_gb:
        log(f"  ⛔ 磁盘余量 {f:.1f}G < --min-free-gb {min_free_gb}（{what}）→ 停止")
        return True
    return False


# ============================================================ §1.7 H gate
def rebuild_project_image(project, timeout=2400):
    """从 **worktree** 强制重建项目镜像（N10 自愈）。`--no-pull` 避开 helper.py 的交互式
    `raw_input('Pull latest base images?')`（✅ W3 实测：不给该参数会 EOFError 退出 1）。"""
    lp = os.path.join(LOGS, "build", f"_image_rebuild_{project}.log")
    rc_, _secs, _tail = run_cmd([sys.executable, "infra/helper.py", "build_image", "--no-pull",
                                 project], WT, lp, timeout=timeout)
    return rc_ == 0


def worktree_gate(check_image=None, verbose=True, auto_rebuild_image=True):
    """四条件 gate（DELIVERY §1.7 H）+ [实现 W2] 第五条：镜像污染检查。

    → (ok, [(name, ok, detail)])。任一不过 → 调用方 ABORT + 写 BLOCKED.md。
    """
    checks = []

    def git(*a):
        return subprocess.run(["git", "-C", WT, *a], capture_output=True, text=True)

    # ① 在 repro-patches 分支（不是 detached HEAD、不是 master）
    br = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    checks.append(("①分支=repro-patches", br == rc.REPRO_PATCH_BRANCH, br or "(空)"))

    # ② 无未提交改动（N4 era-retry 的 projects/ 脏项已还原）
    st = git("status", "--porcelain").stdout.strip()
    checks.append(("②无未提交改动", st == "", (st.splitlines()[:3] or ["(干净)"])[0] if st else "干净"))

    # ③ 三补丁的 commit 在 HEAD 历史里（**正向校验**：干净却在官方 HEAD 的树会静默缺补丁）
    anc = git("merge-base", "--is-ancestor", rc.REPRO_PATCH_COMMIT, "HEAD")
    checks.append((f"③{rc.REPRO_PATCH_COMMIT} 在 HEAD 历史", anc.returncode == 0,
                   "是" if anc.returncode == 0 else f"否 rc={anc.returncode}"))

    # ④ 无 dc-injected 残留
    dc = subprocess.run(["grep", "-rl", "dc-injected", os.path.join(WT, "projects")],
                        capture_output=True, text=True)
    dcl = [x for x in dc.stdout.splitlines() if x.strip()]
    checks.append(("④无 dc-injected 残留", not dcl, f"{len(dcl)} 个文件" if dcl else "0"))

    # ⑤ [实现 W2] **镜像污染检查**：worktree 隔离**不覆盖 docker 镜像**。
    #   ✅ W2 实测：`gcr.io/oss-fuzz/harfbuzz` 等 3 个镜像是 8 天前从**污染主树**建的，
    #   `/src` 里躺着 74/55/60 个 driver_create 注入的 `*crfuzzer*` 源文件；gate ①–④ 全过
    #   也看不出来。若项目 build.sh 广谱 glob 源文件，会编进不属于本研究的 target。
    if check_image:
        for p in (check_image if isinstance(check_image, (list, tuple)) else [check_image]):
            n = image_dc_files(p)
            if n > 0 and auto_rebuild_image:
                # [实现 W3 Phase4(b)] **N10 的处置从「ABORT 排除」改为「重建后复检」**。
                # ✅ W3 实测：`docker rmi gcr.io/oss-fuzz/harfbuzz` + 从 worktree
                # `helper.py build_image --no-pull harfbuzz`（2m17s）→ `/src` 里 dc 注入源
                # **74 → 0**（worktree 的 Dockerfile 只有 5 步、无 `COPY *_cross_crfuzzer.cpp $SRC/`）。
                # 即镜像污染**可自愈**，不必因此排除整个项目（harfbuzz = 68 条可执行 crash）。
                log(f"  ⚠ 镜像 {p} 含 {n} 个 dc 注入源 → 从 worktree 强制重建（N10 自愈）")
                ok_rb = rebuild_project_image(p)
                n2 = image_dc_files(p) if ok_rb else n
                checks.append((f"⑤镜像 {p} 无 dc 注入源（重建后复检）", n2 == 0,
                               f"重建{'成功' if ok_rb else '失败'}；/src 注入源 {n} → {n2}"))
            else:
                checks.append((f"⑤镜像 {p} 无 dc 注入源", n == 0,
                               f"/src 里 {n} 个 *crfuzzer*" if n else "0（或镜像不存在）"))

    ok = all(c[1] for c in checks)
    if verbose:
        for name, good, detail in checks:
            log(f"  [{'✅' if good else '❌'}] {name}: {detail}")
    return ok, checks


def image_dc_files(project):
    """镜像 `/src` 里 driver_create 注入源文件的个数（镜像不存在 → 0，交由构建期重建）。"""
    img = f"gcr.io/oss-fuzz/{project}"
    if subprocess.run(["docker", "image", "inspect", img], capture_output=True).returncode != 0:
        return 0
    script = "ls /src/" + " /src/".join(DC_PATTERNS) + " 2>/dev/null | wc -l"
    r = subprocess.run(["docker", "run", "--rm", "--entrypoint", "bash", img, "-c", script],
                       capture_output=True, text=True, timeout=300)
    try:
        return int(r.stdout.strip().splitlines()[-1])
    except Exception:                                             # noqa: BLE001 输出异常按未知处理
        return -1


def write_blocked(checks, extra=""):
    os.makedirs(HERE, exist_ok=True)
    with open(BLOCKED, "w", encoding="utf-8") as f:
        f.write("# BLOCKED —— worktree gate 未通过，② 拒绝构建\n\n")
        f.write(f"时间：{datetime.datetime.now().isoformat(timespec='seconds')}\n\n")
        f.write("| 条件 | 结果 | 实测 |\n|---|---|---|\n")
        for name, good, detail in checks:
            f.write(f"| {name} | {'✅' if good else '❌'} | {detail} |\n")
        if extra:
            f.write(f"\n{extra}\n")
        f.write("\n**处置**：不带污染构建。修好 gate 条件后重跑（DELIVERY §1.7 H）。\n")
    log(f"  → 已写 {BLOCKED}")


# ============================================================ state（续跑/缓存）
def load_state(path=STATE_PATH):
    if os.path.exists(path):
        try:
            return json.load(open(path, encoding="utf-8"))
        except Exception as e:                                    # noqa: BLE001 损坏则重建（不静默复用）
            log(f"  ⚠ state.json 损坏（{e}）→ 备份后重建")
            shutil.copy(path, path + f".corrupt.{int(time.time())}")
    return {"schema": "repro-state/1.0", "builds": {}, "era_cache": {},
            "head_sha_cache": {}, "done": {}, "runs": []}


def save_state(st, path=STATE_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    json.dump(st, open(tmp, "w"), ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def bkey(project, san, commit, arch="x86_64"):
    """缓存键 = `(project, sanitizer, commit[, architecture])`（R16；[W3] 加架构分量）。

    **钉版严禁退化成 (project,sanitizer)**（同项目两条 crash 的 `fixed^` 通常不同 → 第二条
    复用第一条二进制 = 假复现）。[W3 Phase4(a)] 架构分量同理：x86_64 与 i386 产物若共用一个键，
    会互相覆盖并给出**假复现/假 none**。x86_64 时省略该分量 → 与 W2 的既有键**完全兼容**
    （state.json 不用迁移）。
    """
    return f"{project}|{san}|{commit}" if arch == "x86_64" else f"{project}|{san}|{commit}|{arch}"


# ============================================================ 子进程
# [W5 N40] 权威实现已移进 `repro_common.rotate_existing_log`（③ reproduce 侧也要用）。
# 这里保留同名别名 → 既有调用点与 `w5_selftest_bo.py` 的断言都不用改。
rotate_existing_log = rc.rotate_existing_log

def run_cmd(cmd, cwd, log_path, env=None, timeout=3600, tee=False):
    """跑命令，stdout+stderr 落日志文件。→ (rc, seconds, tail)。"""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    rotate_existing_log(log_path)              # [W5 N25] 永不覆盖上一次的证据
    e = dict(os.environ)
    e.update(PROXY_ENV)
    e["OSS_FUZZ_DIR"] = WT                     # 显式钉死，绝不用主树
    if env:
        e.update(env)
    t0 = time.time()
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"# cmd: {' '.join(cmd)}\n# cwd: {cwd}\n# ts: {datetime.datetime.now().isoformat()}\n\n")
        f.flush()
        p = subprocess.Popen(cmd, cwd=cwd, env=e, stdout=f, stderr=subprocess.STDOUT,
                             stdin=subprocess.DEVNULL)
        try:
            rc_ = p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
            f.write(f"\n# TIMEOUT after {timeout}s\n")
            rc_ = -99
    secs = time.time() - t0
    tail = ""
    try:
        lines = open(log_path, encoding="utf-8", errors="replace").read().splitlines()
        tail = "\n".join(lines[-25:])
    except Exception:                                             # noqa: BLE001
        pass
    return rc_, secs, tail


def docker_capture(image, args, timeout=300):
    """`docker run --rm <image> <args>` 取 stdout（失败 → None）。"""
    try:
        r = subprocess.run(["docker", "run", "--rm", image, *args], capture_output=True,
                           text=True, timeout=timeout)
    except Exception:                                             # noqa: BLE001
        return None
    return r.stdout.strip() if r.returncode == 0 else None


# ============================================================ commit / era 解析
def resolve_head_sha(project, repo_path=None, tries=3):
    """HEAD 路径的 commit 分量 = **镜像内解析出的上游 SHA**（R18，绝不用字面 "HEAD"）。

    ✅ P0-B 形态：`docker run --rm gcr.io/oss-fuzz/pcre2 git -C /src/pcre2 rev-parse HEAD`
    → `aac57f97…`。`repo_path` 有则优先（① 的逐 crash 解析），否则依次试 `/src/<project>`
    与「/src 下唯一的 git 仓库」。
    """
    img = f"gcr.io/oss-fuzz/{project}"
    cands = []
    if repo_path:
        cands.append(repo_path)
    cands.append(f"/src/{project}")
    for c in cands:
        out = docker_capture(img, ["git", "-C", c, "rev-parse", "HEAD"])
        if out and re.fullmatch(r"[0-9a-f]{7,40}", out.splitlines()[-1].strip()):
            return out.splitlines()[-1].strip(), c, None
    # 兜底：找 /src 下所有 git 仓库
    out = docker_capture(img, ["bash", "-c",
                              "for d in /src/*/; do [ -e \"$d/.git\" ] && echo \"$d\"; done"])
    repos = [x.strip().rstrip("/") for x in (out or "").splitlines() if x.strip()]
    if len(repos) == 1:
        sha = docker_capture(img, ["git", "-C", repos[0], "rev-parse", "HEAD"])
        if sha:
            return sha.strip(), repos[0], None
    return None, None, (f"no_git_in_image({len(repos)} repos: {repos[:3]})" if out is not None
                        else "docker_run_failed")


# ============================================================ 非 github/gitlab 仓库的镜像映射
# [W5 N35] `resolve_commit_meta()` 只认 github/gitlab（走 `.patch` 端点），其余一律 `return None`
#   → `plan_pinned()` 拿到 `(d, None, "fixed~d 解析失败")` → **walk-back 在建之前就中止**。
#   ✅ 实测爆炸半径：可执行池 3,136 条里 **542 条（17.3%）/ 32 个项目**被这一条挡死，
#   含池最大的 ghostscript 197、matio 46、kimageformats 39、mupdf 37、libhevc 24…
#   而 mupdf 探针 3 条**一次构建都没发生**（镜像白建 3.11GB）才暴露它。
#
# 为什么用镜像是安全的（两条独立理由）：
#   ① **git SHA 是内容寻址的** —— 镜像无法伪造 SHA。实测 `71ceebcf56e6` 在
#      `ArtifexSoftware/mupdf` 上解析回它自己（date 2018-01-23），即同一对象、同一祖先链。
#   ② **构建仍从原始 `repo_url` 拉取** —— 若镜像给出错误 SHA，`build_specified_commit.py`
#      会在 fetch 时**当场失败**，不会静默产出错结果。故镜像只影响「选哪一格」，不影响「用什么源构建」。
# ⚠ 宿主直连原始 repo 不可行（已实测）：mupdf 的 `git://` 服务器**不支持 partial clone**
#   （`warning: filtering not recognized by server`）→ 退化成全量克隆 → **15min 超时失败**；
#   镜像内的克隆又是 **shallow depth=1**（`rev-list --count HEAD`=1）→ `fixed~1` 解析不了。
REPO_MIRRORS = {
    # 规范 repo_url → 可解析 `~d` / raw 路径的 github 镜像（ArtifexSoftware = mupdf/ghostscript 上游厂商）
    "git://git.ghostscript.com/mupdf.git": "https://github.com/ArtifexSoftware/mupdf",
}


def _norm_repo_key(u):
    """归一：strip + 小写 + 去尾 `.git` / `/`。"""
    if not u:
        return ""
    k = u.strip().lower()
    # ⚠ 循环剥到稳定：`…mupdf.git/` 这种尾斜杠 + `.git` 同时存在时，单轮 for 只剥掉一个
    #   → 键不匹配 → **镜像静默失效**（表现为「又回到解析不了」，很难查）。
    while True:
        k2 = k
        for suf in (".git", "/"):
            if k2.endswith(suf):
                k2 = k2[: -len(suf)]
        if k2 == k:
            return k
        k = k2


def mirror_for(repo_url):
    """返回该 repo 的**可解析镜像**（无则 None）。"""
    k = _norm_repo_key(repo_url)
    if not k:
        return None
    for pat, mir in REPO_MIRRORS.items():
        if k == _norm_repo_key(pat):
            return mir
    return None


# ============================================================ [W5 N42] Gitiles（googlesource）支持
# N35 只用「镜像映射」救了 mupdf 一个项目；但可执行池里 **112 条**属于 googlesource 系
# （android 58 / skia 18 / chromium 17 / aomedia 14 / boringssl 4 / code 1），它们**不需要镜像**——
# Gitiles 自带 JSON 端点，且能直接拿 `parents`，比 GitHub 的 `.patch` 信息还全。
# ✅ 实测 `android.googlesource.com/platform/external/libhevc`：
#    `+/<sha>?format=JSON` → `parents=['130f5f1f…','5e7dc473…']`（**字符串数组**，非对象数组）、
#    `author.time='Mon Aug 19 21:11:00 2019 -0700'`（RFC2822）；响应带 **XSSI 前缀 `)]}'`** 须剥掉。
#    该样例还是 **merge commit（2 个 parent）** → git 的 `~1` 语义就是**第一个 parent**，取 parents[0] 正确。
GOOGLESOURCE_RE = re.compile(r"^https?://([^/]*\.googlesource\.com)/(.+?)(?:\.git)?/?$")


def _http_err(code):
    """把 `rc.http_get` 的 code 变成错误串。

    **[W5 N42 顺带修]** 原来三处都写 `_http_err(code)`，而 `http_get` 返回的 code **本身已带
    `http` 前缀**（如 `"http404"`）→ 实际产出 **`httphttp403`** 这种双重前缀。
    ✅ 这不是假想：mupdf 探针时 GitHub 那条路就印过 `err=httphttp403`。
    危害是**诊断字符串误导**（且任何按 `http403` 匹配的下游都会失配），故统一在此归一。
    """
    c = str(code)
    return c if c.startswith("http") else f"http{c}"


def gitiles_base(repo_url):
    """是 googlesource 仓库 → 返回 `https://<host>/<path>`（去尾 `.git`/`/`）；否则 None。"""
    m = GOOGLESOURCE_RE.match((repo_url or "").strip())
    if not m:
        return None
    path = m.group(2).strip("/")
    return f"https://{m.group(1)}/{path}" if path else None


def gitiles_commit(base, sha, sleep=0.0):
    """`GET <base>/+/<sha>?format=JSON` → dict(sha, date, parents[list[str]], error)。

    ⚠ 与 GitHub 的 `.patch` 不同：Gitiles **没有 rev 语法**（`<sha>~1` 不认）→ 由调用方逐级走 parents[0]。
    """
    url = f"{base}/+/{sha}?format=JSON"
    txt, code = rc.http_get(url, tries=2, timeout=40)
    if sleep:
        time.sleep(sleep)
    if not txt:
        return {"error": _http_err(code), "sha": None, "date": None, "parents": []}
    i = txt.find("{")                                   # 剥 XSSI 前缀 )]}'
    if i < 0:
        return {"error": "unparsable", "sha": None, "date": None, "parents": []}
    try:
        d = json.loads(txt[i:])
    except Exception:                                                  # noqa: BLE001
        return {"error": "unparsable", "sha": None, "date": None, "parents": []}
    date = None
    t = (d.get("author") or {}).get("time")
    if t:
        try:
            import email.utils                                         # noqa: PLC0415
            dt = email.utils.parsedate_to_datetime(t)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            date = dt.isoformat()
        except Exception:                                              # noqa: BLE001
            date = None
    par = [x for x in (d.get("parents") or []) if isinstance(x, str)]
    return {"sha": d.get("commit") or sha, "date": date, "error": None, "parents": par}


SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


def gitlab_commit(host, path, sha, sleep=0.0):
    """**[N57]** `GET https://<host>/api/v4/projects/<path>/repository/commits/<sha>`
    → dict(sha, date, parents[list[str]], error)。

    为什么要单独做（而不是复用 `.patch` 端点）：**GitLab 的 `/-/commit/<rev>.patch` 不接受
    `<sha>~d` 相对修订式**，而自建实例（`invent.kde.org`）也没有 Gitiles 那套 JSON 端点。
    GitLab API v4 的 `parent_ids` 正好等价于 git 的 parent 列表 → 由调用方逐级走 `parents[0]`
    （与 N42 的 Gitiles 走法完全一致：`~1` = **第一个** parent，merge commit 亦正确）。
    ✅ 实测 `invent.kde.org/frameworks/kimageformats`：
       `780f3428…` → parent `297ed9a2…` → `55b4077f…`（标题正是 `xcf: Fix Stack-buffer-overflow WRITE`）。
    """
    enc = str(path).replace("/", "%2F")
    url = f"https://{host}/api/v4/projects/{enc}/repository/commits/{sha}"
    txt, code = rc.http_get(url, tries=2, timeout=40)
    if sleep:
        time.sleep(sleep)
    if not txt:
        return {"error": _http_err(code), "sha": None, "date": None, "parents": []}
    try:
        d = json.loads(txt)
    except Exception:                                                  # noqa: BLE001
        return {"error": "unparsable", "sha": None, "date": None, "parents": []}
    if not isinstance(d, dict) or not d.get("id"):
        return {"error": f"api_shape:{str(d)[:40]}", "sha": None, "date": None, "parents": []}
    return {"sha": d["id"], "date": d.get("authored_date"),
            "parents": list(d.get("parent_ids") or []), "error": None}


def resolve_commit_meta(repo_url, sha, sleep=0.0, via_mirror=None):
    """取 commit 的**真实 SHA + author date**（零 clone、零 API：`.patch` 端点，⓪ 带磁盘缓存）。

    ⓘ 与 `build_specified_commit.py:239 repo_manager.commit_date()` 的 **committer date**
    （`git show -s --format=%ct`）可能不同 → era 预测可能偏；官方 era-retry 兜底。
    用途：① walk-back 的 `fixed~d` → 真实 SHA（缓存键与归档目录必须用真实 SHA）；
         ② era 缓存的日期分量。
    """
    # [W5 N35] 非 github/gitlab → 先换成可解析镜像（只影响「选哪一格」，不影响构建源）
    mir = via_mirror or mirror_for(repo_url)
    if mir:
        repo_url = mir
    # [W5 **N42**] Gitiles：不需要镜像，直接用规范 URL 解析（含 `<sha>~d`）
    gb = gitiles_base(repo_url)
    if gb:
        base_sha, sep, ds = str(sha).partition("~")
        try:
            depth = int(ds) if sep else 0
        except ValueError:
            return {"error": f"bad_rev:{sha}", "sha": None, "date": None}
        cur, last = base_sha, None
        for step in range(depth + 1):
            last = gitiles_commit(gb, cur, sleep=sleep)
            if not last or last.get("error") or not last.get("sha"):
                return last or {"error": "no_response", "sha": None, "date": None}
            if step < depth:
                ps = last.get("parents") or []
                if not ps:                            # 走到根提交还要再往回 → 无法解析
                    return {"error": f"no_parent_at_depth{step}", "sha": None, "date": None}
                cur = ps[0]                           # git 的 `~1` = **第一个** parent
        return {"sha": last["sha"], "date": last["date"], "error": None}
    kind, a, b = rc.classify_repo(repo_url)
    # **[N57]** GitLab + 相对修订式 → 走 API 的 `parent_ids` 逐级回退（`.patch` 端点不认 `~d`）
    if kind == "gitlab" and "~" in str(sha):
        base_sha, sep, ds = str(sha).partition("~")
        try:
            depth = int(ds) if sep else 0
        except ValueError:
            return {"error": f"bad_rev:{sha}", "sha": None, "date": None}
        cur, last = base_sha, None
        for step in range(depth + 1):
            last = gitlab_commit(a, b, cur, sleep=sleep)
            if not last or last.get("error") or not last.get("sha"):
                return last or {"error": "no_response", "sha": None, "date": None}
            if step < depth:
                ps = last.get("parents") or []
                if not ps:
                    return {"error": f"no_parent_at_depth{step}", "sha": None, "date": None}
                cur = ps[0]                           # git 的 `~1` = **第一个** parent
        return {"sha": last["sha"], "date": last["date"], "error": None}
    if kind == "github":
        url = f"https://github.com/{a}/{b}/commit/{sha}.patch"
    elif kind == "gitlab":
        url = f"https://{a}/{b}/-/commit/{sha}.patch"
    else:
        return None
    txt, code = rc.http_get(url)
    if sleep:
        time.sleep(sleep)
    if not txt:
        return {"error": _http_err(code), "sha": None, "date": None}
    pc = rc.parse_patch(txt)
    if not pc:
        return {"error": "unparsable", "sha": None, "date": None}
    d = None
    if pc.get("date_raw"):
        try:
            import email.utils                                    # noqa: PLC0415 仅此处用
            dt = email.utils.parsedate_to_datetime(pc["date_raw"])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            d = dt.isoformat()
        except Exception:                                         # noqa: BLE001 日期不可解析 → None
            d = None
    # **[N54] 绝不把输入原样回显成 `sha`。** 旧代码是 `pc.get("sha") or sha` → 解析失败时
    # 返回 `{"sha": "<输入>", "error": None}`，把**没解析**伪装成**解析成功**。
    # ✅ 实测后果链：invent.kde.org 的 `<sha>~3` 被原样回显 → ② 以为拿到了真 SHA、传给 infra →
    #   infra `checkout_commit` 里 `get_current_commit() != commit`（完整 SHA vs 字面量 `…~3`）
    #   **必然**不等 → `RuntimeError: Error checking out commit …~3` → 分类器标成 `compile_error`
    #   → N43 早停**封掉整个项目**（kimageformats 探针 0/3、2 条被跳过），
    #   且离线预检也拿假 SHA 报「14/14 放行」→ **一个 bug 造出两个假结论**。
    got = pc.get("sha")
    if not got or not SHA_RE.match(str(got)):
        return {"error": f"unresolved_sha:{sha}", "sha": None, "date": None}
    return {"sha": str(got), "date": d, "error": None}


def era_commit_for(project, iso_date):
    """`git log --before=<date> -n1 --format=%H projects/<p>`（= 官方 `:243-248` 的同一算法，
    在**宿主 worktree** 上算，零容器成本）。取不到 → 回退最老 commit（官方 `:255-258` 同法）。"""
    if not iso_date:
        return None
    pd = os.path.join(WT, "projects", project)
    r = subprocess.run(["git", "-C", WT, "log", f"--before={iso_date}", "-n1", "--format=%H",
                        f"projects/{project}"], capture_output=True, text=True)
    out = r.stdout.strip()
    if out:
        return out.splitlines()[0].strip()
    r = subprocess.run(["git", "-C", WT, "log", "--reverse", "--format=%H", f"projects/{project}"],
                       capture_output=True, text=True)
    lines = [x for x in r.stdout.splitlines() if x.strip()]
    return lines[0].strip() if lines else None


# ============================================================ 归档
def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(chunk), b""):
            h.update(blk)
    return h.hexdigest()


def dedup_symbolizer(src, dst_dir):
    """`llvm-symbolizer` 内容寻址去重（✅ P0-B：4 个新构建 sha256 完全相同、仅 2 个内容变体）
    → `binaries/_shared/llvm-symbolizer-<sha8>` + 各 commit 目录**硬链接**（0 边际增量）。"""
    if not os.path.exists(src):
        return None, None
    digest = sha256_file(src)
    os.makedirs(SHARED, exist_ok=True)
    shared = os.path.join(SHARED, f"llvm-symbolizer-{digest[:8]}")
    if not os.path.exists(shared):
        shutil.copy2(src, shared)
    dst = os.path.join(dst_dir, "llvm-symbolizer")
    if os.path.exists(dst):
        os.remove(dst)
    try:
        os.link(shared, dst)                       # 硬链接：0 额外磁盘
    except OSError:
        shutil.copy2(shared, dst)                  # 跨设备则退回拷贝
    return digest, shared


def archive_build(project, san, commit, targets, log_path=None, arch="x86_64"):
    """构建成功**立即**归档：`build/out/<p>/` → `artifacts/binaries/<p>/<san>/<commit>/`。

    只拷 fuzz_target 二进制 + 同名 `.options`/`.dict`（**不含 seed_corpus.zip**，设计 §1.3②）。
    → dict(binary_dir, targets_ok, targets_missing, binary_sha256, bytes, symbolizer_sha256)
    """
    src_dir = os.path.join(BUILD_OUT, project)
    if not os.path.isdir(src_dir):
        return {"ok": False, "why": f"no_build_out({src_dir})"}
    # [W3] 非 x86_64 时归档路径加架构分量（防两种架构的产物混在同一目录）
    dst_dir = os.path.join(BINARIES, project, san, commit if arch == "x86_64"
                           else f"{commit}__{arch}")
    os.makedirs(dst_dir, exist_ok=True)
    ok, missing, nbytes, digests = [], [], 0, {}
    # [实现 W2 bug 修 A] **归档全部 target + 全部非可执行数据文件**（只排除 seed_corpus.zip）。
    # 原实现只拷「本次请求的 target + 同名 .options/.dict」，两个后果都被 W2 首轮实测抓到：
    #  ① **缺数据文件** → flatbuffers `monster_fuzzer` 在 `LLVMFuzzerInitialize →
    #     LoadBinarySchema` 里找不到 `monster_test.bfbs`（14,520 B，就在 build/out 里）
    #     → 测试断言 helper 故意 trap（SIGILL）→ 被误记成「复现 10 条 loose」；
    #  ② **缺 target** → pcre2 的归档只有 `pcre2_fuzzer_16`（P1 验证时只请求了它），
    #     下一轮同 (project,san,commit) 缓存命中却找不到另外 5 个变体 → 8 条
    #     `target_not_in_archive`。缓存键承诺的是「该 commit 的构建产物」，就该自洽完整。
    wanted = set(targets or [])
    execs, datas = [], []
    for name in sorted(os.listdir(src_dir)):
        fp = os.path.join(src_dir, name)
        if not os.path.isfile(fp):
            continue
        if name.endswith("_seed_corpus.zip"):        # 设计明确不归档 seed corpus
            continue
        if os.access(fp, os.X_OK):
            execs.append(name)
        elif os.path.getsize(fp) <= ARCHIVE_DATA_MAX_BYTES:
            datas.append(name)
    for t in sorted(wanted | set(execs)):
        src = os.path.join(src_dir, t)
        # **假成功防护**：必须存在、是文件、可执行、非空（✅ 审计B：build.sh `set +e`+`exit 0`）
        if not (os.path.isfile(src) and os.access(src, os.X_OK) and os.path.getsize(src) > 0):
            if t in wanted:
                missing.append(t)
            continue
        dst = os.path.join(dst_dir, t)
        shutil.copy2(src, dst)
        os.chmod(dst, 0o755)
        d = sha256_file(dst)
        digests[t] = d
        nbytes += os.path.getsize(dst)
        ok.append(t)
    for name in datas:                              # .bfbs/.dict/.options/.json 等运行期数据
        src = os.path.join(src_dir, name)
        dst = os.path.join(dst_dir, name)
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
            nbytes += os.path.getsize(dst)
    # **[W7 修 N66] 递归归档子目录**。原先上面 `if not os.path.isfile(fp): continue`
    # **跳过所有目录** → espeak-ng 的 `espeak-ng-data/`（1.4MB / 351 文件，由
    # `projects/espeak-ng/build.sh:25` 的 `cp -r espeak-ng-data/ $OUT/` 产出）**从未被归档**
    # → 重放时 `Error processing file '/out/phontab': No such file or directory`
    # → 目标初始化失败退出（exit=77、`ERROR: libFuzzer: fuzz target exited`），
    #   却被记成「复现成功 tier=loose」。✅ 实测受害：espeak-ng 已落账 **4 条**全是这种假复现
    #   （报告里**没有任何 sanitizer 段**，DEDUP_TOKEN 是 `…--fuzzer::Fuzzer::ExitCallback()`）。
    # 与 W2 修过的 flatbuffers `.bfbs` 缺失同族，但那次缺的是**顶层文件**、这次是**顶层目录**。
    # 预算：单文件沿用 ARCHIVE_DATA_MAX_BYTES，另加**每目录树总量**上限，防归档膨胀。
    dir_files = []
    for dname in sorted(os.listdir(src_dir)):
        droot = os.path.join(src_dir, dname)
        if not os.path.isdir(droot):
            continue
        used = 0
        for root, _ds, files in os.walk(droot):
            for fn in sorted(files):
                if fn.endswith("_seed_corpus.zip"):
                    continue
                src = os.path.join(root, fn)
                try:
                    sz = os.path.getsize(src)
                except OSError:
                    continue
                if sz > ARCHIVE_DATA_MAX_BYTES or used + sz > ARCHIVE_DIR_MAX_BYTES:
                    continue
                rel = os.path.relpath(src, src_dir)
                dst = os.path.join(dst_dir, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
                    used += sz
                    nbytes += sz
                    dir_files.append(rel)
    sym_digest, _shared = dedup_symbolizer(os.path.join(src_dir, "llvm-symbolizer"), dst_dir)
    return {"ok": bool(ok), "binary_dir": dst_dir if ok else None, "targets_ok": ok,
            "targets_missing": missing, "binary_sha256": digests, "bytes": nbytes,
            "data_files": datas, "dir_files": dir_files,
            "targets_requested_missing": [t for t in (targets or [])
                                                               if t not in digests],
            "symbolizer_sha256": sym_digest,
            "why": None if ok else f"no_executable_target({','.join(missing) or 'none requested'})"}


def restore_projects(project, verbose=True):
    """**N4 还原**。返回还原后 `git status --porcelain` 是否干净。

    [实现 W3 修 / **N18**] W1 记的 `git checkout HEAD -- projects/<p>` **不够**：
    era-retry 的 `git checkout <era> projects/<p>`（`build_specified_commit.py:268`）会把
    **era commit 里有、HEAD 里没有**的文件**加进 index**（状态 `A`），而 `checkout HEAD -- <path>`
    对「HEAD 中不存在的路径」无从恢复 → 文件留在 index 里。
    ✅ W3 实测抓到：harfbuzz 的 era `e32b716754` 含 `hb-draw-fuzzer.options`/`hb-set-fuzzer.options`，
    HEAD 无 → 两个文件以 `A` 状态残留，**gate 条件② 判脏 → ② ABORT**，而 ⑥ 把 ABORT 当成
    「无钉版计划」继续跑（第二个 bug，见 ⑥）。W1 当时只验了「不动 `infra/`」，没验
    「era 新增文件能否被还原」——**验证覆盖不全的典型**。
    正确做法：`git restore --source=HEAD --staged --worktree`（同时清 index 与工作区）
    + `git clean -fdq`（清未跟踪）。✅ W3 实测两条命令后 `git status --porcelain` = 空。
    """
    subprocess.run(["git", "-C", WT, "restore", "--source=HEAD", "--staged", "--worktree",
                    "--", f"projects/{project}"], capture_output=True, text=True)
    subprocess.run(["git", "-C", WT, "clean", "-fdq", "--", f"projects/{project}"],
                   capture_output=True, text=True)
    # 兜底：projects/ 全域再扫一遍（era checkout 理论上只动该项目，但便宜）
    st = subprocess.run(["git", "-C", WT, "status", "--porcelain", "--", "projects"],
                        capture_output=True, text=True).stdout
    if st.strip():
        subprocess.run(["git", "-C", WT, "restore", "--source=HEAD", "--staged", "--worktree",
                        "--", "projects"], capture_output=True, text=True)
        subprocess.run(["git", "-C", WT, "clean", "-fdq", "--", "projects"],
                       capture_output=True, text=True)
    clean = subprocess.run(["git", "-C", WT, "status", "--porcelain"],
                           capture_output=True, text=True).stdout.strip()
    if verbose and clean:
        log(f"    ⚠ 还原后 worktree 仍脏: {clean.splitlines()[:3]}")
    return not clean


# ============================================================ 构建
def build_head(project, san, targets, st, args, repo_path=None, architecture="x86_64"):
    """Stage1：`helper.py build_fuzzers --sanitizer <san> <project>`（✅ P0/P0-B 形态）。"""
    key0 = bkey(project, san, "HEAD")            # 仅用于查「本轮/上轮解析出的 SHA」
    log(f"  [HEAD] {project}/{san} targets={targets}")
    lp = os.path.join(LOGS, "build", f"{project}_{san}_HEAD.log")
    rc_, secs, tail = run_cmd(
        [sys.executable, "infra/helper.py", "build_fuzzers", "--sanitizer", san,
         "--architecture", architecture, project],
        WT, lp, timeout=args.build_timeout)
    if rc_ != 0:
        cls, detail = classify_build_failure(_full_log(lp) or tail)
        return _fail("head", project, san, None, rc_, secs, lp, tail, cls, stage=1,
                     extra={"build_error_detail": detail})

    # commit 分量 = **解析出的上游 SHA**（R18）
    sha, src_dir, why = resolve_head_sha(project, repo_path)
    if not sha:
        # 🅗 拿不到 SHA（tarball 无 .git）→ **不跨轮缓存**、pinned_commit="UNKNOWN"
        log(f"    ⚠ HEAD SHA 解析失败（{why}）→ pinned_commit=UNKNOWN、不缓存")
        sha_key = "UNKNOWN"
    else:
        sha_key = sha
        log(f"    HEAD SHA = {sha[:12]}（解析自 {src_dir}）")
    cache_key = bkey(project, san, sha_key)
    arch = archive_build(project, san, sha_key, targets, arch=architecture)
    if not arch.get("ok"):
        return _fail("head", project, san, sha_key, rc_, secs, lp, tail,
                     "archive_failed", stage=1, extra={"archive_why": arch.get("why")},
                     architecture=architecture)
    rec = _ok("head", project, san, sha_key, secs, lp, arch, stage=1, architecture=architecture,
              head_sha_resolved=bool(sha), head_sha_why=why)
    if sha_key == "UNKNOWN":
        rec["notes"] = "head_commit_unresolved（不跨轮缓存，R18）"
    else:
        st["head_sha_cache"][f"{project}|{san}"] = {"sha": sha, "ts": int(time.time()),
                                                    "oss_fuzz_commit": rec["oss_fuzz_commit"]}
    return rec


def build_pinned(project, san, commit, repo_url, repo_path, targets, st, args,
                 era_pre=None, depth=None, architecture="x86_64"):
    """Stage2：`build_specified_commit.py --project_name … --commit … --sanitizer …
    [--repo_url … --repo_path …]`（P0-C 的旁路参数 → 跳过 `detect_main_repo` 的 bespoke
    `docker run`，避开 **N5** 浅克隆阻塞）。"""
    cache_key = bkey(project, san, commit)
    log(f"  [PIN d={depth}] {project}/{san} commit={commit[:12]} targets={targets}"
        + (f" era_pre={era_pre[:10]}" if era_pre else ""))
    lp = os.path.join(LOGS, "build", f"{project}_{san}_{commit[:12]}.log")

    # era 预 checkout（**优化**：已知 HEAD 配置失败 + era 配置成功时才做；错了有官方兜底）
    pre = None
    if era_pre:
        subprocess.run(["git", "-C", WT, "checkout", era_pre, "--", f"projects/{project}"],
                       capture_output=True, text=True)
        pre = era_pre

    cmd = [sys.executable, "infra/build_specified_commit.py",
           "--project_name", project, "--commit", commit, "--sanitizer", san,
           "--architecture", architecture]
    # [W5 N37] **构建源也走镜像**：`resolve_commit_meta` 用镜像只是「能排格子」，但
    #   `build_specified_commit.py` 的 RepoManager 还要在**宿主机全量克隆** `--repo_url`。
    #   ✅ 实测 mupdf：`git://git.ghostscript.com/mupdf.git` 全量克隆 **>15min 未完**
    #   → 单格 **`# TIMEOUT after 3600s`**、3 格共 **240.2min / 0 复现**；
    #   而 `https://github.com/ArtifexSoftware/mupdf` 全量克隆 **51s（211MB）**，
    #   且本地克隆解析出的 `7f82c015…~1 = 813144d395bb` 与 GitHub API 结果**逐字一致**
    #   → 两种独立方法互证镜像历史相同。**git SHA 内容寻址 → 同一 SHA 检出的树逐字节相同**，
    #   故换源不改变被复现的对象；实际用的源记进 `repo_url_build` 以留痕。
    repo_url_build = mirror_for(repo_url) or repo_url
    if repo_url_build != repo_url:
        log(f"    [N37 镜像源] {repo_url} -> {repo_url_build}（仅换拉取源，SHA 不变）")
    if repo_url_build:
        cmd += ["--repo_url", repo_url_build]
    if repo_path:
        cmd += ["--repo_path", repo_path]
    try:
        rc_, secs, tail = run_cmd(cmd, WT, lp, timeout=args.build_timeout)
        # [实现 W3 N16] `network_fetch` 类失败**自动重试 1 次**：W2 实测 c-blosc2@9ba29ef1 的失败是
        # `repo_manager.git(['remote','update'])` → `RPC failed; curl 56 GnuTLS recv error (-9)`
        # → `Could not fetch origin`，属**瞬态**；而 compile_error 重试无用。分类器已能分开两者
        # （`network_fetch` 置最高优先级，自测 8/8），故只对这一类重试。
        if rc_ != 0 and args.retry_network and not args.dry_run:
            full = _full_log(lp) or tail
            if classify_build_failure(full)[0] == "network_fetch":
                log(f"    ↻ network_fetch 类失败 → 重试 1 次（N16；瞬态网络，非项目问题）")
                lp2 = lp.replace(".log", "_retry1.log")
                rc2, secs2, tail2 = run_cmd(cmd, WT, lp2, timeout=args.build_timeout)
                secs += secs2
                if rc2 == 0:
                    rc_, tail = rc2, tail2
                    log(f"    ✅ 重试成功（+{secs2:.0f}s）")
                else:
                    tail = tail2 + "\n# retry1 also failed"
    finally:
        restored = restore_projects(project)          # **N4 还原**（无论成败）

    era_logged = None
    try:
        m = ERA_LOG_RE.search(open(lp, encoding="utf-8", errors="replace").read())
        era_logged = m.group(1) if m else None
    except Exception:                                                 # noqa: BLE001
        pass

    if rc_ != 0:
        cls, detail = classify_build_failure(_full_log(lp) or tail)
        rec = _fail("pinned", project, san, commit, rc_, secs, lp, tail, cls, stage=2,
                    architecture=architecture,
                    extra={"era_commit": era_logged, "era_prechecked_out": pre,
                           "build_error_detail": detail,
                           "walkback_depth_actual": depth, "worktree_restored": restored, "repo_url_build": repo_url_build})
        _learn_era(st, project, era_logged or pre, head_ok=False, era_ok=False)
        return rec

    arch = archive_build(project, san, commit, targets, arch=architecture)
    if not arch.get("ok"):
        rec = _fail("pinned", project, san, commit, rc_, secs, lp, tail, "archive_failed",
                    stage=2, architecture=architecture,
                    extra={"archive_why": arch.get("why"), "era_commit": era_logged,
                                    "walkback_depth_actual": depth,
                                    "worktree_restored": restored, "repo_url_build": repo_url_build})
        return rec
    rec = _ok("pinned", project, san, commit, secs, lp, arch, stage=2, architecture=architecture,
              era_commit=era_logged, era_prechecked_out=pre,
              walkback_depth_actual=depth, worktree_restored=restored,
              repo_url_build=repo_url_build)
    # era 学习：这次成功用的是哪种配置
    if pre and era_logged is None:
        _learn_era(st, project, pre, head_ok=False, era_ok=True)     # 预 checkout era 后首试即成
    elif era_logged:
        _learn_era(st, project, era_logged, head_ok=False, era_ok=True)  # 官方 era-retry 救回
    else:
        _learn_era(st, project, None, head_ok=True, era_ok=None)     # HEAD 配置首试即成
    return rec


def _learn_era(st, project, era, head_ok, era_ok):
    if not era:
        return
    k = f"{project}|{era}"
    e = st["era_cache"].setdefault(k, {"project": project, "era_commit": era,
                                       "head_ok": 0, "head_fail": 0, "era_ok": 0, "era_fail": 0})
    if head_ok:
        e["head_ok"] += 1
    elif era_ok is True:
        e["era_ok"] += 1
    elif era_ok is False:
        e["era_fail"] += 1
    else:
        e["head_fail"] += 1


def era_suggestion(st, project, iso_date):
    """该 (project, date) 是否值得**预 checkout era**（跳过注定失败的首试）。
    只在「已观测到 HEAD 配置失败 ≥1 次 且 era 配置成功 ≥1 次」时才建议——**学习式**，
    不预设「老 commit 一定要 era」（那会把本可首试成功的构建也拖慢）。"""
    if not iso_date:
        return None, None
    era = era_commit_for(project, iso_date)
    if not era:
        return None, None
    e = st["era_cache"].get(f"{project}|{era}")
    if e and e["head_fail"] + e["era_ok"] > 0 and e["era_ok"] > 0 and e["head_ok"] == 0:
        return era, e
    return None, e


def _base(path_kind, project, san, commit, stage, arch="x86_64"):
    ofz = subprocess.run(["git", "-C", WT, "rev-parse", "HEAD"], capture_output=True,
                         text=True).stdout.strip()
    return {"key": bkey(project, san, commit or "?", arch), "path": path_kind, "project": project,
            "sanitizer": san, "pinned_commit": commit, "stage": stage, "architecture": arch,
            "oss_fuzz_commit": ofz, "base_builder_digest": None,   # ⓘ gcloud 不可用（P0-B）
            "ts": int(time.time())}


def _ok(path_kind, project, san, commit, secs, lp, arch, stage, architecture="x86_64", **kw):
    r = _base(path_kind, project, san, commit, stage, architecture)
    r.update(build_status="ok", build_stage=stage, build_seconds=round(secs, 1),
             build_log=lp, binary_dir=arch["binary_dir"], binary_sha256=arch["binary_sha256"],
             archived_bytes=arch["bytes"], symbolizer_sha256=arch["symbolizer_sha256"],
             targets_ok=arch["targets_ok"], data_files=arch.get("data_files"),
             targets_absent_at_commit=arch.get("targets_requested_missing"),
             build_error_class=None, notes=None)
    r.update(kw)
    return r


def _fail(path_kind, project, san, commit, rc_, secs, lp, tail, cls, stage, extra=None,
          architecture="x86_64"):
    r = _base(path_kind, project, san, commit, stage, architecture)
    r.update(build_status=("fail_head" if stage == 1 else "fail_pinned"), build_stage=stage,
             build_seconds=round(secs, 1), build_log=lp, binary_dir=None, binary_sha256=None,
             exit_code=rc_, build_error_class=cls, notes=(tail or "")[-400:])
    if extra:
        r.update(extra)
    return r


# [实现 W2 修 G] **顺序即优先级**，且新增 `network_fetch` 置于最前。
# ✅ W2 实测抓到误分类：c-blosc2@9ba29ef1 的失败其实是
#   `repo_manager.git(['remote','update'])` → `RPC failed; curl 56 GnuTLS recv error (-9)`
#   → `Could not fetch origin`，却因日志尾部含 `error:` 被判成 `compile_error`。
# 两者处置完全不同（网络失败**该重试**；编译失败是 A2 工具链漂移、重试无用），故必须先判网络。
FAIL_PATTERNS = [
    ("network_fetch", re.compile(r"RPC failed|Could not fetch origin|GnuTLS recv error|"
                                 r"early EOF|fetch-pack|Could not read from remote|"
                                 r"Could not resolve host|Connection reset|Failed to connect|"
                                 r"Temporary failure in name|unexpected disconnect", re.I)),
    # [W5 **N43**] 补一个实测漏掉的形态：`build_specified_commit.py` 的 RepoManager 抛
    #   `ValueError: Commit <sha> does not exist in current branch`。
    # ✅ 实测 libavc：3 次构建都栽在这句上，却因不匹配任何 pattern 而落到 `compile_error`
    #   → 触发「连续 2 次同类确定性失败」早停 → **封掉整个项目、33 条被跳过**，
    #   而同轮已试的 10 条里 **7 条复现成功**（github 与 googlesource 两种源都出过）。
    ("commit_not_found", re.compile(r"fatal: .*not a commit|invalid reference|"
                                    r"Could not find commit|pathspec .* did not match|"
                                    r"does not exist in current branch|"
                                    r"ValueError: Commit [0-9a-f]{7,40}|"
                                    # [W5 **N56**] 实测漏掉的第二个形态：`repo_manager.checkout_commit`
                                    # 末尾的 `if self.get_current_commit() != commit: raise RuntimeError(
                                    # 'Error checking out commit %s')`。当传进去的是**相对修订式**
                                    # （`<sha>~3`，N54 的回显 bug 造成）时，`git checkout -f` 成功、
                                    # 但完整 SHA 与字面量 `…~3` **必然**不等 → 每次必抛。
                                    # 与 `does not exist in current branch` 同族（**逐 commit 成立、
                                    # 不是项目级必然**）→ 归入本类，自动排除在 DETERMINISTIC_FAIL 外，
                                    # 否则连续 2 次就封整个项目（✅ 实测误伤 kimageformats 2 条探针）。
                                    r"Error checking out commit", re.I)),
    # [实现 W2 修 G-2] 原 `dead_external_url` 含裸 `404|Not Found` + re.I → 会把
    # 「ninja: **not found**」误判成死外链（✅ 自测抓到）。改为要求 HTTP 语境，
    # 并把 `toolchain_drift` 提到它前面。
    # [实现 W3 N19] `ninja: error: unknown target '<path>'` = **build.sh 与上游 commit 版本错配**
    # （当前 `projects/<p>/build.sh` 要求一个该老 commit 里不存在的 target）。✅ W3 实测：harfbuzz
    # 6 次钉版**全部**栽在 `unknown target 'test/fuzzing/hb-raster-fuzzer'`，且 era 自愈**已触发**
    # （era `242b6ae6`）仍失败 → era 侧的 build.sh 也要这个 target。与 compile_error 处置不同，
    # 故单列一类并排在它前面。
    ("buildscript_mismatch", re.compile(r"ninja: error: unknown target|"
                                        r"no rule to make target|"
                                        # [W4] N19 形态②：build.sh 引用的脚本/文件在该 commit 不存在
                                        r"error: \S+: No such file or directory|"
                                        r"cannot stat .*No such file|"
                                        r"can't open file|"
                                        # [W5 openh264 实测] **形态③**：C++ `#include` 的头文件在该
                                        # commit 不存在（clang: `fatal error: 'X' file not found`；
                                        # GCC 的 `fatal error: X: No such file or directory` 已被上面覆盖）。
                                        # 仍是「构建脚本/fuzzer 源码 与 上游 commit 版本错配」，但
                                        # **预检的路径存在性检查看不到它**（不是 shell 路径）→ 第三个盲点。
                                        r"fatal error: '[^']+' file not found", re.I)),
    # **[N58] 镜像里烘死的依赖与「要建的那个 era」不匹配** —— 与 `dockerfile_drift`（apt 包装不上）
    # 不同：包**装上了**，但版本/形态不对，导致 CMake/configure 阶段找不到期望的东西。
    # ✅ 实测 kimageformats：Dockerfile 是 `git clone --depth 1 -b **master**` 后跑上游
    #   `prepare_build.sh` → 镜像里烘的是**当前（2026）的 ECM/Qt**，而我们要建 2021 年的 commit：
    #   `CMake Error at /usr/local/share/ECM/modules/ECMQueryQt.cmake:84: No Qt6 qtpaths
    #    executable found`。**era-retry 救不了**——那个 prepare 脚本来自 master、根本没被钉版。
    #   旧分类器把它标成 `toolchain_drift`，证据行是 Qt configure 的**非致命探针**
    #   `clang++: error: unknown argument: '-mavx512er'`（`test config.qtbase.tests.avx512er FAILED`
    #   属正常探测失败）→ **记错原因**会让后来人去换工具链，而真正该做的是钉 ECM/Qt 版本。
    ("era_dep_drift", re.compile(r"No Qt\d+ \S* ?executable found|"
                                 r"Could NOT find [A-Z]\w+|"
                                 r"CMake Error at \S*(ECM|Find\w+|KDE\w+)\.cmake|"
                                 r"Configuring incomplete, errors occurred", re.I)),
    ("toolchain_drift", re.compile(r"ninja: not found|command not found|"
                                   r"No such file or directory.*\.cmake|unknown argument|"
                                   r"unsupported option|"
                                   # [W5 **N58** 收紧] 原来是裸 `-Werror` → ✅ 实测会命中 autotools 的
                                   # **成功探针行** `checking if the -Werror option is usable... yes`
                                   # （几乎所有 autotools 项目都打这行）；裸 `unsupported` 会命中
                                   # Qt 的**路径名** `/usr/mkspecs/features/unsupported`；
                                   # 裸 `ninja-build` 会命中 **apt 安装行**（✅ pcapplusplus 就是这么被误判的）。
                                   # 改为要求 `-Werror` 出现在**真错误行**里（opensc 的形态：
                                   # `error: variable 'octets_left' is uninitialized … -Werror`）。
                                   r"error:.*-Werror", re.I)),
    ("dead_external_url", re.compile(r"404 Not Found|(?:HTTP|status|code)\D{0,6}4\d\d|"
                                     r"dead link|Could not download|curl: \(22\)|"
                                     r"wget: unable to resolve|ERROR: .*download", re.I)),
    ("dockerfile_drift", re.compile(r"E: Unable to locate package|Package .* has no installation|"
                                    r"dpkg.*error", re.I)),
    ("timeout", re.compile(r"# TIMEOUT after", re.I)),
    ("compile_error", re.compile(r"error:|fatal error:|undefined reference|"
                                 r"Error \d+", re.I)),
    ("era_retry_exhausted", re.compile(r"Retrying on earlier OSS-Fuzz commit", re.I)),
]
def _norm_cand(t):
    """[W5 修 **bug②**] 归一化预检候选路径：去掉 `./` 前缀。

    `raw/<sha>/./autogen.sh` 这种 URL 不该用来判存在性 → 必然 404 → **误报**
    （与 bug① 同族：归一化/前置条件不足 → 假 404 → 跳过本能成功的构建）。
    归一化后若变成单段名（如 `autogen.sh`），会被既有的「`/` not in t → 不查」规则挡掉
    → 结果是**少查一个**（漏报），符合「宁漏勿误」。
    """
    t = (t or "").strip().strip("/")
    while t.startswith("./"):
        t = t[2:].strip("/")
    return t


# 失败详情：抓第一条真正的错误行，供报告按**根因**分组（classifier 只给粗类）
ERROR_LINE_RE = re.compile(r"^.*?(?:error:|fatal:|ERROR:|RuntimeError|E: ).*$", re.M)
# [W5 修 N28③] era-retry 的分界：该标记之后是**第二次尝试**的日志，其报错常掩盖首试真因
ERA_SPLIT_RE = re.compile(r"Retrying on earlier OSS-Fuzz commit", re.I)


def _full_log(path, limit=8 << 20):
    # [实现 W3 修] 原 limit=400000 会**截掉日志开头**：✅ W3 实测 harfbuzz 的日志 478,431 B，
    # 首试失败原因 `ninja: error: unknown target …`（buildscript_mismatch）在前、era-retry 的
    # `-Werror` 报错在后 → 只读末 400KB 会把主因误判成 toolchain_drift。分类要看**整份**。
    try:
        return open(path, encoding="utf-8", errors="replace").read()[-limit:]
    except OSError:
        return None


def classify_build_failure(tail):
    """失败原因分类（**记录后继续走**，任务约束：单个项目排查 >30min 就跳过）。

    分类基于**整份日志**而非尾部片段（网络失败的证据常在中间）；`era_retry_exhausted`
    只是过程日志、优先级最低。返回 (类别, 首条错误行)。
    """
    if not tail:
        return "unknown_no_output", None

    def _pick(scope):
        h = [name for name, pat in FAIL_PATTERNS if pat.search(scope)]
        h = [x for x in h if x != "era_retry_exhausted"] or h
        return h[0] if h else None

    # [W5 修 **N28③**] **首试段优先**：`Retrying on earlier OSS-Fuzz commit` 之后是第二次尝试的
    # 日志，它的报错（常是老 Dockerfile 的 apt 失败）会**掩盖首试真因**。
    # ✅ 两次实测被它误导：
    #   * opensc：detail 报 `OpenPACE linkage required`，真凶是 `-Werror,-Wuninitialized`；
    #   * openh264：class 报 `dockerfile_drift`（era 段 `libstdc++-5-dev` 在 focal 已下架），
    #     真凶是首试的 `fatal error: 'codec_def.h' file not found`（头文件在该 commit 不存在）。
    # 故先用 era 标记**之前**的段落分类；该段无命中时才退回整份日志（保留原行为，见自测「首试段无错」用例）。
    first_seg = ERA_SPLIT_RE.split(tail, 1)[0]
    for scope in ((first_seg, tail) if first_seg.strip() else (tail,)):
        cls = _pick(scope)
        if cls:
            m = ERROR_LINE_RE.search(scope)
            return cls, (m.group(0).strip()[:200] if m else None)
    m = ERROR_LINE_RE.search(tail)
    return "unclassified", (m.group(0).strip()[:200] if m else None)


# ============================================================ walk-back 计划
def plan_pinned(rec, args):
    """给一条 crash 排出钉版计划 → [(depth, commit, note)]。

    **[实现 W4 Phase2] 一律走策略 A：从 `fixed~1` 起逐格 walk-back。**
    静态 check 的 `pin_commit`/`walkback_depth`/`fixed_real`/`fixed_misattributed` **照常算、
    照常记进 manifest**（对下游理解 crash 有价值），但**不再用于选格**——降为 advisory。

    为什么（✅ W3 实测，n=13 条走完 tier 感知 walk-back）：
      * 构建次数 **A≈21 < C=23 < W3 当时实现 28 < B=33**：W1 说「B 比 A 省 12.3%」，实测**方向相反**；
      * 主因是 `not_located` 桶 **8/8 全落在 depth1**（W4 前累积 9/9）→ 静态 check 想省的
        「off-by-one 白构建」本来就不多，而它**指错格**的代价是实打实的；
      * 加上 N17 的构建失败回退（钉版失败率 25.5%），`located` 分支的净成本为正。
    ⚠ **前提标注**：n 小（`not_located` 10 条），且 located 率**跨项目不稳**（W3 的 3 项目
      87.3% vs W1 的 41 项目分层抽样 64.6%）→ 本改动是「**按现有证据的默认选择**」，
      不是终局结论；`not_located` 补到 ≥30 条后复核（§5 待办）。

    不受影响的排除档：**N6** `degenerate` 未复核通过 → 不钉；无 `fixed` 且无 `introducing_commit`
    → 无可钉 commit；无 `repo_url` → 无法解析 `fixed~d`。
    """
    if rec.get("osv_degenerate_range") and not rec.get("degenerate_resolved"):
        return [], "N6 退化 range 未复核通过 → 禁钉版（只跑 HEAD）"
    fixed = rec.get("fixed_commit")
    if not fixed:
        if rec.get("introducing_commit"):
            # depth=None：这不是 walk-back 的某一格（`walkback_depth_actual` 只在 1..3 有意义）
            return [(None, rec["introducing_commit"],
                     "无 fixed → 回退链第 2 档 introducing_commit（非 walk-back 格）")], None
        return [], "无 fixed 且无 introducing_commit → 无可钉 commit（no_commit_to_pin）"
    if not rec.get("repo_url"):
        return [], "无 repo_url → 无法解析 fixed~d（undecidable）"
    out = []
    for d in range(1, args.max_depth + 1):
        m = resolve_commit_meta(rec["repo_url"], f"{fixed}~{d}", sleep=args.sleep)
        if not m or m.get("error") or not m.get("sha"):
            out.append((d, None, f"fixed~{d} 解析失败（{(m or {}).get('error')}）"))
            break
        adv = ""
        if d == 1 and rec.get("pin_commit") and rec["pin_commit"] != m["sha"]:
            adv = f"（advisory：① 静态 check 会钉 {str(rec['pin_commit'])[:12]}=depth" \
                  f"{rec.get('walkback_depth')}，本轮不采用）"
        out.append((d, m["sha"], f"fixed~{d}{adv}"))
    if not out:
        return [], "fixed~1 解析失败"
    return out, None


# ============================================================ 构建前静态预检（W4 Phase3a）
BRACE_RE = re.compile(r"\{([^{}]+)\}")
# 只挑「像构建目标/源文件」的 token：`*-fuzzer` / `*_fuzzer` / 带源码扩展名的相对路径。
# **故意窄**：build.sh 里还有字体目录、`$OUT`、`cp $d/*` 之类，缺了未必致命，误报会白跳过
# 本可成功的构建（比 N19 的浪费更糟）。
# [实现 W4 Phase3a 扩展] N19 有**两种**形态，只查 fuzzer target 会漏掉第二种：
#   形态①（harfbuzz）：`ninja … test/fuzzing/hb-raster-fuzzer` → `ninja: error: unknown target`
#   形态②（pcapplusplus）：build.sh 第 22 行**直接执行** `$SRC/PcapPlusPlus/Tests/Fuzzers/ossfuzz.sh`
#     → `error: Tests/Fuzzers/ossfuzz.sh: No such file or directory`（✅ W4 实测 3/3 次同错，
#       而旧版预检**漏掉了它**：`.sh` 不在扩展名表里、且该行不含构建命令）
# 故候选路径扩到「任何 ≥2 段的变量无关相对路径」，剥掉 `$SRC/[<repo basename>/]` 前缀；
# 只看**消费文件**的行（构建命令 + cp/mv/cat/bash/sh/source/cd/zip + 以路径开头的行）。
# 窄口径（形态①）：ninja/meson 的 fuzzer target（无扩展名）或带源码扩展名的路径
CAND_RE = re.compile(r"(?<![\w$~])((?:[\w.+~-]+/)+[\w.+~-]*(?:-|_)fuzzer(?:\.\w+)?"
                     r"|(?:[\w.+~-]+/)+[\w.+~-]+\.(?:c|cc|cpp|cxx|h|hh|hpp|hxx))\b")
# [实现 W4] 形态②的**精确**补丁：只认「被当作脚本调用/执行」的 `.sh/.py/.pl` 路径。
# ✅ W4 实测 pcapplusplus 的 build.sh 第 22 行就是一行 `$SRC/PcapPlusPlus/Tests/Fuzzers/ossfuzz.sh`。
# ⚠ **故意不放宽成「任何路径」**：试过宽口径，会把 `www.apache.org/licenses/LICENSE-2.0`、
# `$OUT/*.zip`、`.libs/libpcre2-8.a`、`bin/bash` 全抓进来 → 这些必然 404 → **误报会跳过本能
# 成功的构建**，比漏报代价大得多。窄口径 + 精确脚本模式 = harfbuzz 6/6、pcapplusplus 3/3 命中，
# 已知能建的 6 个项目 0 误报。
# [W5 修 **bug③**] 允许解释器与脚本路径之间夹 `-flag`：`bash -x ./ndpi/tests/ossfuzz.sh`。
# ✅ W5 实证漏检的后果：ndpi 的 `tests/ossfuzz.sh` 在抽样 3 个 commit 上**全部缺失**
# （= pcapplusplus/libspng 同型的 0/N 灾难），而预检报 `no_candidate_paths`（「无证据」）
# → 离线筛选把 ndpi 排到**第 1 位**推荐去建镜像。
# ⚠ 只放宽「破折号开头的 flag」这一种形态，**不**放宽成任意 token（W4 的教训：宽口径会把
# LICENSE URL / `$OUT/*.zip` / `.libs/*.a` 抓进来 → 必然 404 → 误报比漏报更糟）。
# [W5 修 **bug④**] 加 `^\s*` 这个 alternative：**整行就是一个裸脚本路径**的形态。
# ✅ W5 实证：libxml2/build.sh 去掉注释后**只有一行** `fuzz/oss-fuzz-build.sh`
# （无解释器、无 `$SRC/`、无 `./`）→ 原三个 alternative 全不匹配 → 预检报 `no_candidate_paths`
# = **无证据**，于是 52 条池只能被判「ⓘ 只能探针」。而它在 **gitlab.gnome.org** 上，
# `path_exists_at` 本来就支持 gitlab → 属于「查得了却没去查」。
# ⚠ 为什么加 `^\s*` 不会放宽成误报：capture 要求 `[\w.+~-]+(?:/[\w.+~-]+)+\.(sh|py|pl)`，
#   而 `cp tools/helper.sh $OUT/` 这类行**行首是 `cp`**，其后是空格 → 既不能进字符类也接不上 `/`
#   → 回溯也匹配不成（自测 [F] 就是这条负对照）。shell 里「整行以路径开头」本身就等于执行它。
SCRIPT_RE = re.compile(r"(?:\$SRC/|\b(?:bash|sh|source)\s+(?:-\S+\s+)*|^\s*\.?/|^\s*)"
                       r"([\w.+~-]+(?:/[\w.+~-]+)+\.(?:sh|py|pl))\b", re.M)
SRC_EXTS = ("", ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx",
            ".sh", ".py", ".pl", ".dict", ".options", ".txt", ".cmake")
MAX_PRECHECK_PATHS = 40        # 单次预检最多查多少个路径（成本护栏）
BUILD_CMD_RE = re.compile(r"\b(?:ninja|make|meson|cmake)\b|\$CXX|\$CC\b|\bcd\s|"
                          r"\b(?:cp|mv|cat|bash|sh|source|zip|unzip|tar|install)\b|"
                          r"^\s*\$SRC/|^\s*\./", re.I)


def expand_braces(txt):
    """展开 shell 花括号 `a-{x,y}-b` → `a-x-b a-y-b`（harfbuzz 的 build.sh 正用此写法）。"""
    out = [txt]
    for _ in range(4):                                  # 最多嵌套 4 层，够覆盖实测形态
        nxt = []
        changed = False
        for line in out:
            m = BRACE_RE.search(line)
            if not m:
                nxt.append(line)
                continue
            changed = True
            for alt in m.group(1).split(","):
                nxt.append(line[:m.start()] + alt.strip() + line[m.end():])
        out = nxt
        if not changed:
            break
    return out


def _raw_url(repo_url, sha, path):
    # [W5 N35] 同 resolve_commit_meta：镜像让 `path_exists_at` 对非 github 仓库也可判
    #   （mupdf 此前在筛选里被标 ⓘ「判不了」正因这里返回 None）
    repo_url = mirror_for(repo_url) or repo_url
    # [W5 **N42**] Gitiles 的 raw 端点：`+/<sha>/<path>?format=TEXT`（base64 正文；
    #   我们只看状态码，故 `path_exists_at` / `submodule_paths` 都能直接复用）
    #   → 这让 googlesource 系项目从筛选里的 ⓘ「判不了」升为**可预检**。
    gb = gitiles_base(repo_url)
    if gb:
        return f"{gb}/+/{sha}/{path.lstrip('/')}?format=TEXT"
    kind, a, b = rc.classify_repo(repo_url)
    if kind == "github":
        return f"https://github.com/{a}/{b}/raw/{sha}/{path}"
    if kind == "gitlab":
        return f"https://{a}/{b}/-/raw/{sha}/{path}"
    return None


def path_exists_at(repo_url, sha, path, sleep=0.0):
    """该 path（或其某个源码扩展名变体）在 commit `sha` 的树里是否存在。
    用 `raw` 端点（**0 次 API、0 次 clone**，与 ⓪ 的 `.patch` 同口径，走宿主代理 + /tmp 缓存）。
    → True / False / None（无法判定：非 github/gitlab、或网络错）

    [实现 W4 修] **已有扩展名的路径只查一次**：原实现对每个候选都把 SRC_EXTS 全试一遍
    （15 次 HTTP），扩展候选集后直接卡死（✅ W4 实测：验证脚本 >15min 未返回）。
    只有**无扩展名**的候选（ninja/meson target，如 `test/fuzzing/hb-raster-fuzzer`）
    才需要试源码扩展名。另把 tries 降到 1、超时降到 15s（404 是确定性答案，不需重试）。
    """
    # [W5 修 **bug①**] 缺 sha / repo_url → **无法判定**（None），不是「确定缺失」（False）。
    # 原实现直接插值出 `raw/None/<path>` → 必然 404 → 被当成确定缺失 → 预检**误报**、
    # 违反本节契约「无法判定时一律放行」。✅ W5 实证：libredwg 在 sha=None 下报
    # `missing=['./autogen.sh','examples/llvmfuzz.c']` 而 `checked=0`（一次都没真查）。
    # 顺带省掉这次注定无意义的 HTTP。
    if not repo_url or not sha:
        return None
    has_ext = bool(re.search(r"\.\w{1,6}$", path))
    # 无扩展名的候选（ninja/meson target）只试**最可能的 4 个**源码扩展名：
    # ✅ W4 实测 harfbuzz 6 个候选 × 15 个扩展名 = 64.2s/条预检；收窄后应 ≈1/3。
    exts = ("",) if has_ext else ("", ".cc", ".cpp", ".c")
    for ext in exts:
        url = _raw_url(repo_url, sha, path + ext)
        if not url:
            return None
        _txt, code = rc.http_get(url, tries=1, timeout=15)
        if sleep:
            time.sleep(sleep)
        if code == 200 or code == "cache":
            return True
        if code in ("http404", 404):
            continue                      # 无扩展名时才继续试下一个
        return None                       # 其它错误 → 无法判定，不拦
    return False


GITMODULES_PATH_RE = re.compile(r"^\s*path\s*=\s*(.+?)\s*$", re.M)
_SUBMOD_CACHE = {}


def submodule_paths(repo_url, sha, sleep=0.0):
    """该 commit 的 `.gitmodules` 里声明的 submodule 路径集合（带进程内缓存）。

    **[W5 N36] 为什么必须有它**：GitHub/GitLab 的 raw 端点**看不见 submodule 内部**
    （内容在另一个仓库里）→ 对 `thirdparty/harfbuzz/src/x.cc` 这类路径**必然 404**。
    ✅ 实测 mupdf@`7f82c015`：同一 commit 下 `source/fitz/document.c`、`include/mupdf/fitz.h`
    都 **HTTP 200**，唯独 submodule 内的 `thirdparty/harfbuzz/src/hb-subset-cff1.cc` **404**，
    而 `build.sh:19` 正是 `sed -i … ./thirdparty/harfbuzz/src/hb-subset-cff1.cc`
    → 预检误判 `buildscript_mismatch`，**一次挡死 mupdf 全部 37 条**
    （构建时容器会带 submodule 克隆，该文件必然存在 → 纯误报）。
    与 N27①/N29 同一口径：**查不了 ≠ 查过没有** → 记 `undecidable` 并放行。

    → `set()`：无 `.gitmodules` 或其中无 submodule；`None`：无法判定（调用方须放行）。
    """
    key = (repo_url, sha)
    if key in _SUBMOD_CACHE:
        return _SUBMOD_CACHE[key]
    url = _raw_url(repo_url, sha, ".gitmodules")
    if not url:
        return None
    txt, code = rc.http_get(url, tries=1, timeout=15)
    if sleep:
        time.sleep(sleep)
    if code in ("http404", 404):
        _SUBMOD_CACHE[key] = set()
        return set()
    if not txt:
        return None                      # 其它错误 → 无法判定
    out = {m.group(1).strip().strip("/") for m in GITMODULES_PATH_RE.finditer(txt)}
    _SUBMOD_CACHE[key] = out
    return out


def precheck_buildscript(project, repo_url, sha, sleep=0.0, verbose=True, repo_path=None):
    """**构建前**静态预检（W4 Phase3a）：`projects/<p>/build.sh` 引用的构建目标，在该上游
    commit 的树里是否都存在。

    动机（**N19**）：harfbuzz 6 次钉版**全部**栽在 `ninja: error: unknown target
    'test/fuzzing/hb-raster-fuzzer'`——当前 build.sh 要一个老 commit 里不存在的 target，
    era 自愈**救不了**（era 侧的 build.sh 也要它）。这类失败**构建前就能判定**：
    早停要先白跑一两次才触发，预检**一次都不用跑**（每次省 ~90–320s）。

    → dict(ok, missing, checked, undecidable, build_sh) ；`ok=False` → 跳过并标
      `build_error_class=buildscript_mismatch`。**无法判定时一律放行**（宁可白跑一次构建，
      不可因预检误报而跳过本可成功的构建）。
    """
    bs = os.path.join(WT, "projects", project, "build.sh")
    res = dict(ok=True, missing=[], checked=0, undecidable=0, build_sh=bs, reason=None)
    # **[N55] 输入非法 ≠ 无法判定。** 上面那句「无法判定时一律放行」针对的是**查不到**，
    # 不是**给了垃圾**。✅ 实测：`sha` 传成 `<sha>~1`（N54 回显 bug 的产物）时，
    # 本函数照样返回 `ok=True, reason='no_build_sh'` → 离线筛选据此报「kimageformats 14/14 放行」，
    # 是个**假结论**（那条路后面根本构建不了）。故非空但非纯 SHA → 直接判失败。
    if sha and not SHA_RE.match(str(sha)):
        res.update(ok=False, build_sh=bs, reason=f"bad_rev:{sha}")
        if verbose:
            print(f"    [预检] {project}@{str(sha)[:24]}：⛔ **sha 不是纯 SHA**（含相对修订式？）→ 判失败")
        return res
    # [W5 修 **bug①**] 没有 sha 就无从查起 → **放行**，且 reason 用独立的 `no_sha`
    # （W4 的教训：「跳过」的原因必须能与「0 候选」区分，否则变量遮蔽会静默吃掉整段验证）。
    # 生产调用点（本文件 walk-back 处）传的总是计划里的真 commit → 该分支只在离线调用
    # （如 preflight/w5_screen_next_projects.py 拿不到 fixed_parent 时）才会走到。
    if not sha:
        res["reason"] = "no_sha"
        return res
    if not os.path.exists(bs):
        res["reason"] = "no_build_sh"
        return res
    txt = open(bs, encoding="utf-8", errors="replace").read()
    # `$SRC/<repo basename>/…` → 仓库相对路径（basename 取自 ① 逐 crash 解析的 repo_path）
    prefix = os.path.basename(repo_path.rstrip("/")) if repo_path else None
    cands = set()
    foreign = set()          # **[N68] 出现在 `cd $SRC/<其它仓库>` 之后的路径 → 无法判定**
    cur_repo = None
    for line in expand_braces(txt):
        # **[W7 修 N68] 追踪 `cd $SRC/<dir>` 上下文。**
        # ✅ 实测 wolfssl：build.sh 第 42 行 `cd $SRC/cryptofuzz`，第 53 行的
        #   `sed -i … modules/wolfcrypt/module.cpp` 是**相对 cryptofuzz** 的路径，
        #   拿 wolfssl 仓库去查必然 404 → 误报 `buildscript_mismatch` → **整个 wolfssl
        #   23 条池被跳过**。与 N36（submodule 看不见）、N65（构建产物）同族：
        #   都是「查不到 ≠ 查过没有」→ 应记 undecidable 并放行。
        mcd = re.search(r"\bcd\s+(?:\$SRC/|/src/)([\w.+~-]+)", line)
        if mcd:
            cur_repo = mcd.group(1)
        if cur_repo and prefix and cur_repo != prefix and cur_repo != project:
            for m in list(CAND_RE.finditer(line)) + list(SCRIPT_RE.finditer(line)):
                t = _norm_cand(m.group(1))
                if t and "/" in t and "$" not in t:
                    foreign.add(t)
        # [实现 W4 Phase3a 修] **只看构建命令行**（ninja/make/meson/cmake/$CXX/$CC/cd）：
        # N19 的形态就是「构建命令要一个不存在的 target」。别的行（cp/zip/mkdir）里出现的
        # 路径缺了未必致命，纳进来只会增加误报。
        if not BUILD_CMD_RE.search(line):
            continue
        for m in CAND_RE.finditer(line):
            t = _norm_cand(m.group(1))
            # **[W8 修 N71] 形态① 也要剥 `$SRC/<repo>/` 前缀 —— 原来只有形态②(`SCRIPT_RE`)剥了。**
            # `CAND_RE` 的负向断言 `(?<![\w$~])` 让匹配**从 `$SRC/` 之后的第一段开始**，于是把
            # 仓库目录名也算进了路径；而 git 树里没有这一层 → 必然 404 → **假阴性**。
            # ✅ 实证 icu：`build.sh:40` 是
            #   `$CXX $CXXFLAGS -c $SRC/icu/icu4c/source/test/fuzzer/locale_util.cpp \`
            #   候选被抓成 `icu/icu4c/source/test/fuzzer/locale_util.cpp`（带 `icu/`），
            #   GitHub contents API 查 `906093f31b44` 与 `7cec4a9308b0` 两棵树都**确实有**
            #   `icu4c/source/test/fuzzer/locale_util.cpp` → 预检误判 `buildscript_mismatch`，
            #   **一次挡死 icu 全部钉版池**（Stage1/HEAD 那条不做预检，所以探测批看着"能建"，
            #   掩盖了这个 bug）。与 N36(submodule)、N65(构建产物)、N68(跨仓库 cd) 同族。
            if prefix and t.startswith(prefix + "/"):
                t = t[len(prefix) + 1:]
            # **紧邻 shell 变量的匹配一律丢弃**：✅ W4 实测 pcre2 的
            # `cp "testdata/fuzzing/pcre2_fuzzer${bits}.dict"` 被截成
            # `testdata/fuzzing/pcre2_fuzzer` → 404 → **误报**（而 pcre2 实测 10/10 能建）。
            # 变量未展开的路径无法判定存在性 → 宁可不查（误报比漏报代价大：会跳过本能成功的构建）。
            nxt = line[m.end():m.end() + 1]
            if nxt in ("$", "{"):
                continue
            if "$" in t or not t or t.startswith(("/", "..")) or "/" not in t:
                continue                           # 含变量 / 单段名（可能是生成物或命令）→ 不查
            # **[W6 修 N65] 非源码扩展名 = 构建产物 → 不查。**
            # `CAND_RE` 的第一个 alternative 是 `…(?:-|_)fuzzer(?:\.\w+)?`，`\.\w+` 允许**任意**
            # 扩展名，于是把 make 的产物也抓了进来。
            # ✅ 实测 htslib@`92ea05adb2`：`build.sh:23` 是
            #   `make -j$(nproc) libhts.a bgzip htsfile tabix annot-tsv test/fuzz/hts_open_fuzzer.o`
            #   —— `.o` 是 make **目标**（第 35 行才拿它去链接），同 commit 树里只有
            #   `test/fuzz/hts_open_fuzzer.c`（✅ `git ls-tree` 实测：`.o` 0 个、`.c` 1 个）。
            #   raw 端点对 `.o` 必然 404 → 判 `buildscript_mismatch` → **一次挡死 htslib 全部 25 条池**
            #   （19 条 heap-buffer-overflow，是当轮分析价值最高的候选项目）。
            # 与 N36（mupdf 的 submodule 误报）同族：**该文件构建时必然存在，只是不在 git 树里**。
            # 用**已有的 SRC_EXTS 白名单**判，不另造黑名单（`.dict`/`.options` 是签入的，仍在白名单内）。
            _ext = os.path.splitext(t)[1].lower()
            if _ext and _ext not in SRC_EXTS:
                res["artifact_skipped"] = res.get("artifact_skipped", 0) + 1
                res.setdefault("artifact_paths", []).append(t)
                continue
            cands.add(t)
        # 形态②：被调用的脚本路径（`$SRC/<repo>/a/b.sh` → 仓库相对 `a/b.sh`）
        for m in SCRIPT_RE.finditer(line):
            t = _norm_cand(m.group(1))
            if prefix and t.startswith(prefix + "/"):
                t = t[len(prefix) + 1:]
            if t and "/" in t and "$" not in t:
                cands.add(t)
    if not cands:
        res["reason"] = "no_candidate_paths"
        return res
    if len(cands) > MAX_PRECHECK_PATHS:
        # 成本护栏：候选过多说明该 build.sh 大量引用路径，逐个查会拖慢每次构建前的预检
        res["reason"] = f"too_many_candidates({len(cands)})"
        res["n_candidates"] = len(cands)
        if verbose:
            log(f"    [预检] 候选 {len(cands)} 个 > {MAX_PRECHECK_PATHS} → 只查前 "
                f"{MAX_PRECHECK_PATHS} 个（按字典序，成本护栏）")
        cands = set(sorted(cands)[:MAX_PRECHECK_PATHS])
    res["n_candidates"] = len(cands)
    subs = submodule_paths(repo_url, sha, sleep=sleep)
    res["submodules"] = sorted(subs) if subs else []
    res["foreign_repo_paths"] = sorted(foreign & cands)
    for c in sorted(cands):
        # **[N68] 属于其它仓库的路径**（出现在 `cd $SRC/<其它>` 之后）→ 无法判定，不拦
        if c in foreign:
            res["undecidable"] += 1
            continue
        # [W5 N36] submodule 内的路径 raw 端点看不见 → **无法判定，不拦**
        if subs and any(c == sm or c.startswith(sm + "/") for sm in subs):
            res["undecidable"] += 1
            res.setdefault("submodule_skipped", []).append(c)
            continue
        e = path_exists_at(repo_url, sha, c, sleep=sleep)
        if e is None:
            res["undecidable"] += 1
        elif e:
            res["checked"] += 1
        else:
            res["missing"].append(c)
    if res["missing"]:
        res["ok"] = False
        res["reason"] = f"build.sh 引用但 commit {str(sha)[:12]} 树里没有: {res['missing']}"
    if verbose:
        log(f"    [预检] {project}@{str(sha)[:12]}：候选 {len(cands)} 个路径，存在 {res['checked']}、"
            f"**缺失 {len(res['missing'])}**、无法判定 {res['undecidable']}"
            + (f"；submodule 内跳过 {len(res['submodule_skipped'])} 个（N36）"
               if res.get("submodule_skipped") else "")
            + (f" → {res['missing'][:4]}" if res["missing"] else " → 放行"))
    return res


# ============================================ [W5 N34③] fuzzer 源码的 #include 预检
INCLUDE_RE = re.compile(r'^\s*#\s*include\s*"([^"]+)"', re.M)
INC_DIR_RE = re.compile(r"-I\s*(\S+)")
SRC_FILE_RE = re.compile(r"\.(?:c|cc|cpp|cxx|C)$")
COPY_LINE_RE = re.compile(r"^\s*COPY\s+(.+)$", re.M)


def parse_fuzzer_includes(project):
    """从 `projects/<p>/` 的 Dockerfile + fuzzer 源码 + build.sh 里抽出三样东西：
    **被 COPY 进 `$SRC` 的源码** / 它们的 **quoted `#include`** / build.sh 的 **`-I` 目录**。

    纯文件解析、**零网络** → 可离线单测（自测直接读 worktree 里真实的 openh264 文件）。
    动机（**N34③**）：fuzzer 源码由 Dockerfile 从 **HEAD** 拷进容器，却要编译**老 commit** 的树
    → include 的头文件可能在那个 commit 里还不存在/已改名。✅ W5 实测：openh264 的
    `decoder_fuzzer.cpp:28 #include "codec_def.h"` 在钉版 commit 的三个 `-I` 目录与仓库根**都没有**
    → `fatal error: 'codec_def.h' file not found` → 0/3 构建失败，而**路径存在性预检看不到它**
    （它不是 shell 路径）。只取 `"…"` 形式：`<…>` 是系统头，既查不了也不该查。
    """
    pdir = os.path.join(WT, "projects", project)
    out = {"sources": [], "includes": [], "inc_dirs": [], "reason": None}
    if not os.path.isdir(pdir):
        out["reason"] = "no_project_dir"
        return out
    # ① Dockerfile 的 `COPY … $SRC/` → 哪些**源码**被带进容器（build.sh/Dockerfile 自身不算）
    dfp = os.path.join(pdir, "Dockerfile")
    srcs = []
    if os.path.exists(dfp):
        for line in open(dfp, encoding="utf-8", errors="replace"):
            m = COPY_LINE_RE.match(line)
            if not m or "$SRC" not in line:
                continue
            for tok in m.group(1).split():
                if tok.startswith("$") or tok.endswith("/") or not SRC_FILE_RE.search(tok):
                    continue
                b = os.path.basename(tok)
                if b not in srcs:
                    srcs.append(b)
    out["sources"] = srcs
    # ② 这些源码里的 quoted include（去重保序）
    incs, seen = [], set()
    for s in srcs:
        fp = os.path.join(pdir, s)
        if not os.path.exists(fp):
            continue
        for m in INCLUDE_RE.finditer(open(fp, encoding="utf-8", errors="replace").read()):
            h = m.group(1).strip()
            if h and h not in seen:
                seen.add(h)
                incs.append(h)
    out["includes"] = incs
    # ③ build.sh 的 -I 目录（归一化掉 `./`；含 `$` 的查不了 → 跳过）
    bsp = os.path.join(pdir, "build.sh")
    dirs, dseen = [], set()
    if os.path.exists(bsp):
        btxt = open(bsp, encoding="utf-8", errors="replace").read()
        for m in INC_DIR_RE.finditer(btxt):
            raw = m.group(1)
            if "$" in raw:
                continue
            d = _norm_cand(raw)
            if not d or d.startswith("..") or d in dseen:
                continue
            dseen.add(d)
            dirs.append(d)
    out["inc_dirs"] = dirs
    return out


def include_candidates(inc, inc_dirs):
    """一个 quoted include 要**依次**试的仓库相对路径：每个 `-I` 目录，**最后**仓库根。

    `../` 逃逸 / 绝对路径 → 返回空（宁漏勿误，与既有预检同口径）。
    """
    inc = (inc or "").strip().strip("/")
    if not inc or inc.startswith("..") or "/../" in inc or inc.startswith("/"):
        return []
    out = []
    for d in (inc_dirs or ()):
        d = (d or "").strip().strip("/")
        if not d or d.startswith(".."):
            continue
        out.append(f"{d}/{inc}")
    out.append(inc)
    return out


def precheck_includes(project, repo_url, sha, repo_path=None, sleep=0.0, verbose=True,
                      max_checks=24):
    """[W5 **N34③**] 查 fuzzer 源码的 quoted `#include` 在该 commit 的 `-I` 目录/仓库根下是否存在。

    → dict(ok, missing, checked, undecidable, n_checks, max_checks, reason)
    **无法判定时一律放行**（与 `precheck_buildscript` 同一契约，见 N27①：误报会跳过本能成功的构建）。

    ⚠ **只做筛选维度、不接进 ② 的每次构建前预检**：6 个 include ×（3 个 `-I` + 根）= **24 次 HTTP**
    ≈ 10–25s/项目。作一次性筛选划算（对比建镜像 2.3–2.9GB + 探针 10–30min），
    但放进每次构建前就逼近 **N24** 的教训（预检自身比它省下的构建更贵）。
    """
    res = dict(ok=True, missing=[], checked=0, undecidable=0, n_checks=0,
               max_checks=max_checks, reason=None)
    if not sha:
        res["reason"] = "no_sha"
        return res
    if not repo_url:
        res["reason"] = "no_repo_url"
        return res
    info = parse_fuzzer_includes(project)
    if info.get("reason"):
        res["reason"] = info["reason"]
        return res
    if not info["sources"]:
        res["reason"] = "no_sources"
        return res
    if not info["includes"]:
        res["reason"] = "no_includes"
        return res
    res["n_includes"] = len(info["includes"])
    res["inc_dirs"] = info["inc_dirs"]
    capped = False
    for inc in info["includes"]:
        cands = include_candidates(inc, info["inc_dirs"])
        if not cands:
            continue
        hit, und, tried = False, 0, 0
        for c in cands:
            if res["n_checks"] >= max_checks:
                capped = True
                break
            res["n_checks"] += 1
            tried += 1
            e = path_exists_at(repo_url, sha, c, sleep=sleep)
            if e is True:
                hit = True
                break
            if e is None:
                und += 1
        if hit:
            res["checked"] += 1
        elif tried and und == tried:
            res["undecidable"] += 1          # 全查不了 → 不算缺失（契约：宁漏勿误）
        elif tried:
            res["missing"].append(inc)
    if capped:
        res["reason"] = f"capped({max_checks})"
    if res["missing"]:
        res["ok"] = False
        res["reason"] = (f"{len(res['missing'])} 个 #include 在该 commit 的 -I 目录与仓库根都找不到: "
                         f"{res['missing'][:4]}")
    if verbose:
        log(f"    [include 预检] {project}@{str(sha)[:12]}：{res.get('n_includes', 0)} 个 include、"
            f"{len(info['inc_dirs'])} 个 -I 目录 → 查 {res['n_checks']} 次、找到 {res['checked']}、"
            f"**缺 {len(res['missing'])}**、无法判定 {res['undecidable']}"
            + (f" → {res['missing'][:4]}" if res["missing"] else " → 放行"))
    return res


# ============================================================ 归档裁剪（W3 Phase2）
VERIFIED_TIERS = ("strict", "medium", "loose")
PRUNE_AUDIT = os.path.join(rc.ARTIFACTS, "prune_audit.jsonl")


def prune_archive(dataset_path, state_path=STATE_PATH, dry=False, verbose=True,
                  prune_force=False):
    """**默认执行**的归档裁剪（§1.6 Hybrid：只交付 verified 子集，`none` 的二进制对下游无价值）。

    规则：
      * **保留** = 任何 `verification_tier ∈ {strict, medium, loose}` 的记录所引用的 `binary_dir`
        （含其同 `(project,san,commit)` 归档目录整体——一个目录可能服务多条 crash）；
      * **裁掉** = 其余归档目录（走完 walk-back 仍 `none`、或从未被任何 verified 记录用到）；
      * `state.json` 对应缓存键**一并删除** → 重跑时会重建（不是静默指向已删目录）；
      * `_shared/` 的 symbolizer **不动**（内容寻址 + 硬链接，删归档只是少一个链接；
        两个变体合计 ~14MB，且后续构建还要用）。

    依据（✅ W2 实测）：782MB / 17 个 commit 目录 ≈ **46MB/次构建**，而 129 条里 **113 条是 `none`**；
    按队列外推 3,093 条钉版 × 46MB ≈ **142GB** ≫ 磁盘余量（W2 结束时 13G）。
    → dict(kept_dirs, pruned_dirs, freed_bytes, kept_bytes, protected_by_tier)
    """
    st = load_state(state_path)
    tiers = {}
    if os.path.exists(dataset_path):
        for line in open(dataset_path, encoding="utf-8"):
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("osv_id"):
                tiers[d["osv_id"]] = d           # 后者覆盖 = 最新
    protected, prot_by = set(), collections.Counter()
    # [实现 W3 修 / **N20**] 保护集必须扫**全部行**，不能只看「同 osv_id 的最新一行」。
    # ✅ W3 实测事故：⑤ 的 scope bug 曾把 W2 的 OSV-2020-2183/-2184/-2251/-1663（2 strict + 2 loose）
    # 覆盖成 `not_run`/tier=null → 那一轮的裁剪据此判定「无人引用」→ **把 4 个 verified 归档目录删了**
    # （不可逆；记录本身仍有效，但二进制要重建）。dataset 是 append-only 的历史复现记录表，
    # 任何一行标了 verified 就说明该二进制曾产出过被交付的结论 → 一律保护。
    if os.path.exists(dataset_path):
        for line in open(dataset_path, encoding="utf-8"):
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("verification_tier") in VERIFIED_TIERS and d.get("binary_dir"):
                # [W5 **N41**] 用 `realpath` 而不是 `normpath`：复现记录表是 **append-only**，
                # 里面的 `binary_dir` 是**写下当时的绝对路径**，永远不能改。一旦归档区被改名或
                # 经符号链接访问（例如加一层「按 crash 类型浏览」的视图），`normpath` 的**字符串**
                # 比对就会两边对不上 → 保护集为空 → **所有 verified 归档都被判「无人引用」而删掉**。
                # 这正是 N30/N20 的形态，只是触发方式从「绕过保护集」变成「保护集静默失配」。
                protected.add(os.path.realpath(d["binary_dir"]))
                prot_by[d["verification_tier"]] += 1
    for d in tiers.values():                     # 最新行也纳入（含尚未落 dataset 的本轮结果）
        if d.get("verification_tier") in VERIFIED_TIERS and d.get("binary_dir"):
            protected.add(os.path.realpath(d["binary_dir"]))
    # 现有归档目录（跳过 _shared）
    existing = []
    if os.path.isdir(BINARIES):
        for proj in sorted(os.listdir(BINARIES)):
            pd = os.path.join(BINARIES, proj)
            if proj == "_shared" or not os.path.isdir(pd):
                continue
            for san in sorted(os.listdir(pd)):
                sd = os.path.join(pd, san)
                if not os.path.isdir(sd):
                    continue
                for com in sorted(os.listdir(sd)):
                    existing.append(os.path.join(sd, com))

    dsize = _dsize          # [W5] 与 purge_archives 共用同一口径（硬链接不计入回收量）

    # [实现 W4 Phase1a(ii)] **独立**交叉校验：保护集是按 verified 行的 `binary_dir` 算的；
    # 这里改用**另一个字段** `pinned_commit`（+ project/sanitizer）重算一遍「哪些 commit 曾被
    # verified 记录用过」。两条路径若不一致 → 说明保护逻辑有 bug（正是 W3 N20 那种），
    # **拒绝执行**而不是删了再说。用同一字段自查等于没查，故必须换字段。
    used_commit = set()
    for d in tiers.values():
        if d.get("verification_tier") in VERIFIED_TIERS and d.get("pinned_commit"):
            used_commit.add((d.get("project"), d.get("sanitizer"), d["pinned_commit"]))
    if os.path.exists(dataset_path):
        for line in open(dataset_path, encoding="utf-8"):
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("verification_tier") in VERIFIED_TIERS and d.get("pinned_commit"):
                used_commit.add((d.get("project"), d.get("sanitizer"), d["pinned_commit"]))

    # [W5 N41] 比对两侧都取 realpath（盘上路径也可能是符号链接进来的）
    kept = [p for p in existing if os.path.realpath(p) in protected]
    gone = [p for p in existing if os.path.realpath(p) not in protected]
    # 待删目录里，有多少其实被 verified 记录用过（按 commit 口径 / 按 binary_dir 口径）
    def _parts(path):
        rel = os.path.relpath(path, BINARIES).split(os.sep)
        return tuple(rel) if len(rel) == 3 else (None, None, None)
    conflict_commit = [p for p in gone if _parts(p) in used_commit]
    conflict_dir = [p for p in gone if os.path.realpath(p) in protected]     # 恒为空（自查）
    M = len(set(conflict_commit) | set(conflict_dir))
    freed = sum(dsize(p) for p in gone)
    keptb = sum(dsize(p) for p in kept)
    if verbose:
        log(f"[裁剪] 归档目录 {len(existing)} 个：保留 {len(kept)}（被 verified 记录引用："
            f"{dict(prot_by)}）、**将删 {len(gone)} 个，其中 {M} 个在历史行里标过 verified**")
        log(f"[裁剪] 预计回收 **{freed/1e6:.0f} MB**，保留 {keptb/1e6:.0f} MB"
            f"（硬链接的 symbolizer 不计入回收量）")
    # ---- W4：M>0 即拒绝（除非 --prune-force）----
    if M and not prune_force:
        log(f"  ❌ 拒绝裁剪：{M} 个待删目录曾被 verified 记录引用 → 保护逻辑有 bug（W3 N20 同型）")
        for c in sorted(set(conflict_commit) | set(conflict_dir))[:8]:
            log(f"     {c}")
        log(f"     确需删除请加 --prune-force（会记进 prune_audit.jsonl）")
        _audit(dict(action="REFUSED", n_existing=len(existing), n_pruned=0, M=M,
                    conflicts=sorted(set(conflict_commit) | set(conflict_dir)),
                    dataset=dataset_path))
        return dict(n_existing=len(existing), n_kept=len(kept), n_pruned=0, freed_bytes=0,
                    kept_bytes=keptb, protected_by_tier=dict(prot_by), refused=True, M=M,
                    pruned_dirs=[], kept_dirs=kept)
    if dry:
        log("[裁剪] dry-run：只报告、不删")
        _audit(dict(action="dry-run", n_existing=len(existing), n_pruned=len(gone), M=M,
                    freed_bytes=freed, pruned_dirs=gone, dataset=dataset_path))
        return dict(n_existing=len(existing), n_kept=len(kept), n_pruned=len(gone),
                    freed_bytes=freed, kept_bytes=keptb, protected_by_tier=dict(prot_by),
                    dry=True, M=M, pruned_dirs=gone, kept_dirs=kept)
    if True:
        for p in gone:
            shutil.rmtree(p, ignore_errors=True)
        # state.builds 里指向已删目录的键一并删除
        nk = 0
        for k, b in list((st.get("builds") or {}).items()):
            bd = b.get("binary_dir")
            if bd and not os.path.isdir(bd):
                del st["builds"][k]
                nk += 1
        st.setdefault("prune_history", []).append(
            {"ts": int(time.time()), "pruned": len(gone), "kept": len(kept),
             "freed_bytes": freed, "protected_by_tier": dict(prot_by), "M_conflicts": M})
        _audit(dict(action="pruned", n_existing=len(existing), n_kept=len(kept),
                    n_pruned=len(gone), M=M, freed_bytes=freed, kept_bytes=keptb,
                    protected_by_tier=dict(prot_by), pruned_dirs=gone, kept_dirs=kept,
                    dataset=dataset_path))
        save_state(st, state_path)
        if verbose:
            log(f"[裁剪] state.json 删除 {nk} 个失效缓存键；剩余 {len(st.get('builds') or {})} 个")
            # 清掉空的项目/sanitizer 目录
            for proj in list(os.listdir(BINARIES)) if os.path.isdir(BINARIES) else []:
                pd = os.path.join(BINARIES, proj)
                if proj == "_shared" or not os.path.isdir(pd):
                    continue
                for san in list(os.listdir(pd)):
                    sd = os.path.join(pd, san)
                    if os.path.isdir(sd) and not os.listdir(sd):
                        os.rmdir(sd)
                if not os.listdir(pd):
                    os.rmdir(pd)
    return dict(n_existing=len(existing), n_kept=len(kept), n_pruned=len(gone),
                freed_bytes=freed, kept_bytes=keptb, protected_by_tier=dict(prot_by),
                M=M, pruned_dirs=gone, kept_dirs=kept)


# ==================================================== 逐条回收（W5：复现完立即删）
def _dsize(p):
    """目录实际占用；**硬链接**（symbolizer）不计入回收量（与 `prune_archive` 同口径）。"""
    t = 0
    for r, _d, fs in os.walk(p):
        for f in fs:
            fp = os.path.join(r, f)
            try:
                st_ = os.lstat(fp)
                if st_.st_nlink <= 1:
                    t += st_.st_size
            except OSError:
                pass
    return t


def select_purge_dirs(brecs, keep_head=True):
    """从构建记录里挑出**可以立即删**的归档目录（去重、normpath、跳过空值）。

    `keep_head=True`（默认）→ **HEAD 归档永不删**：它按 `(project, sanitizer)` 被同组
    全部 crash 共享，且负对照（§1.7 I）要用；删了会让下一条 crash 白白重建。
    钉版归档是 **per-commit 独占**（R16），一条 crash 用完即无共享价值 → 可删。
    """
    # [W5 修] 用**白名单**而不是「非 head 即删」：`path` 缺失/未知 → **不删**。
    # 删错是不可逆的（留错只是多占磁盘），故 fail-safe 必须偏向保留 —— 与预检的
    # 「无法判定时一律放行」同一条原则。✅ 自测 [A] 抓到：原实现把无 `path` 的记录也当成可删。
    allowed = ("pinned",) if keep_head else ("pinned", "head")
    out, seen = [], set()
    for r in (brecs or ()):
        d = (r or {}).get("binary_dir")
        if not d:
            continue
        if (r or {}).get("path") not in allowed:
            continue
        nd = os.path.normpath(d)
        if nd in seen:
            continue
        seen.add(nd)
        out.append(nd)
    return out


def purge_archives(dirs, state_path=STATE_PATH, why=None, dry=False, verbose=True,
                   dataset_path=None):
    """**逐条**回收归档：删目录 + 失效 state 缓存键 + 写审计。→ dict(n_deleted, freed_bytes, …)

    与 `prune_archive` 的分工：prune 是**轮末**按 dataset 保护集裁剪（只删未被 verified 引用的）；
    purge 是**每条 crash 证据落盘后立刻**回收，且**连 verified 的也删**。
    ✅ 为什么删 verified 也安全：W4 实测归档重建**逐字节一致 20/20**（4 commit × 5 文件）
    → 删除是**可恢复**的，损失只是重建时间、不是信息。前提是 dataset 行留住
    `binary_sha256`（来自 build_records，删目录不影响）+ 重建配方（`pinned_commit`/sanitizer/
    arch/era）并标 **`binary_pruned=true`** —— 否则 `binary_dir` 就成了**无声的悬空指针**
    （N25/N26 同族：产物没了而记录还指着它）。
    ✅ 为什么必须逐条：92 条积压一轮的归档峰值 ≈ 92×50MB ≈ **4.6GB**，磁盘仅 7.7G
    → 轮末才裁会中途撞 `--min-free-gb` 护栏而**中止整轮**。
    `_shared` 与 HEAD 目录**拒绝删除**（前者是共享工具、后者见 `select_purge_dirs`）。

    ⚠ **[W5 修事故] `dataset_path` 必须传**：**钉到同一 commit 的 crash 共享归档目录**，
    所以「本条用完即删」会连带删掉**别条**（可能是早几轮已交付的）verified 行的证据。
    ✅ 实测事故：`purge_on_verify:OSV-2021-1676` 删掉了 **OSV-2021-1663 / OSV-2021-1712**
    （都是 w4-stratA 的 **strict** 行）的归档，而那两行**没有任何标记** → 无声悬空指针。
    给了 `dataset_path` 就按 `prune_archive` 同一套保护集（verified 行引用的 `binary_dir`）
    跳过；不传 = 无保护（仅供自测对照），⑥ 里必须传。
    """
    # [W5 修事故] 保护集：dataset 里**已落盘**的 verified 行所引用的归档（本轮的行还没写，
    # 所以本条自己的目录不在保护集内 → 照删，符合「复现完立即删」的策略）。
    protected = set()
    if dataset_path and os.path.exists(dataset_path):
        try:
            for line in open(dataset_path, encoding="utf-8"):
                d = json.loads(line)
                if d.get("verification_tier") in VERIFIED_TIERS and d.get("binary_dir"):
                    # [W5 **N41**] realpath 而非 normpath：理由同 `prune_archive`。
                    # 这一处更要命 —— `purge_archives` 是 **N30 事故**（删掉 W4 已交付的 strict 证据）
                    # 的当事人，保护集一旦因路径别名静默失配，就会重演同一次删除。
                    protected.add(os.path.realpath(d["binary_dir"]))
        except (OSError, json.JSONDecodeError) as e:
            if verbose:
                log(f"    [回收] ⚠ 保护集读取失败（{e}）→ **本轮不删任何东西**（宁留勿误删）")
            return dict(n_deleted=0, freed_bytes=0, dirs=[], protected=[], refused=True)
    want, skipped = [], []
    for d in (dirs or ()):
        if not d:
            continue
        nd = os.path.normpath(d)
        if os.sep + "_shared" + os.sep in nd + os.sep or nd.endswith(os.sep + "_shared"):
            if verbose:
                log(f"    [回收] 拒绝删除 `_shared`：{nd}")
            skipped.append(nd)
            continue
        if os.path.realpath(nd) in protected:
            if verbose:
                log(f"    [回收] 保住（被历史 verified 行引用，共享归档）：{nd[-52:]}")
            skipped.append(nd)
            continue
        want.append(nd)
    freed = sum(_dsize(d) for d in want if os.path.isdir(d))
    if dry:
        _audit(dict(action="purge-dry-run", n_pruned=len(want), freed_bytes=freed,
                    pruned_dirs=want, protected=skipped, why=why))
        return dict(n_deleted=0, freed_bytes=freed, dirs=want, protected=skipped, dry=True)
    nd_ = 0
    for d in want:
        if os.path.isdir(d):
            shutil.rmtree(d, ignore_errors=True)
            nd_ += 1
    st = load_state(state_path)
    nk = 0
    for k, b in list((st.get("builds") or {}).items()):
        bd = b.get("binary_dir")
        if bd and not os.path.isdir(bd):
            del st["builds"][k]
            nk += 1
    st.setdefault("prune_history", []).append(
        {"ts": int(time.time()), "action": "purge_on_verify", "pruned": nd_,
         "freed_bytes": freed, "why": why})
    save_state(st, state_path)
    _audit(dict(action="purge_on_verify", n_pruned=nd_, freed_bytes=freed,
                pruned_dirs=want, protected=skipped, why=why, state_keys_dropped=nk))
    if verbose and nd_:
        log(f"    [回收] 删除 {nd_} 个钉版归档、释放 {freed/1e6:.0f} MB、"
            f"state 失效 {nk} 个缓存键（sha256+配方已留档 → 可 bit 级重建）")
    return dict(n_deleted=nd_, freed_bytes=freed, dirs=want, protected=skipped,
                state_keys_dropped=nk)


def _audit(rec):
    """[W4 Phase1a(ii)] 每次裁剪（含 dry-run 与拒绝）都留一条审计。"""
    rec["ts"] = int(time.time())
    os.makedirs(os.path.dirname(PRUNE_AUDIT), exist_ok=True)
    with open(PRUNE_AUDIT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ============================================================ 主流程
def load_scope(args):
    mf = [json.loads(l) for l in open(args.manifest, encoding="utf-8")]      # noqa: E741
    if args.only_osv:
        want = set(x.strip() for x in args.only_osv.split(",") if x.strip())
        mf = [r for r in mf if r["osv_id"] in want]
    if args.projects:
        ps = set(x.strip() for x in args.projects.split(",") if x.strip())
        mf = [r for r in mf if r["project"] in ps]
    if args.sanitizers:
        ss = set(x.strip() for x in args.sanitizers.split(",") if x.strip())
        mf = [r for r in mf if r["sanitizer"] in ss]
    if args.crash_types:
        cs = set(x.strip() for x in args.crash_types.split(",") if x.strip())
        mf = [r for r in mf if r["crash_type_norm"] in cs]
    mf = [r for r in mf if not r["skip_reason"]]
    if args.limit:
        mf = mf[:args.limit]
    return mf


def main():
    ap = argparse.ArgumentParser(description="② 构建编排（DELIVERY §1.3②）")
    ap.add_argument("--manifest", default=rc.MANIFEST_OUT)
    ap.add_argument("--out", default=BUILD_RECORDS)
    ap.add_argument("--state", default=STATE_PATH)
    ap.add_argument("--stage", choices=["1", "2", "auto"], default="1")
    ap.add_argument("--observations", default=None,
                    help="③ 的 observations.jsonl；--stage auto 用它决定谁需要 Stage2")
    ap.add_argument("--projects", default=None)
    ap.add_argument("--only-osv", default=None)
    ap.add_argument("--sanitizers", default=None)
    ap.add_argument("--crash-types", default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--max-builds", type=int, default=0, help="本轮构建上限（HEAD+钉版合计）")
    ap.add_argument("--max-depth", type=int, default=3, help="walk-back 上限（§1.3② ≤3）")
    ap.add_argument("--stop-after-failures", type=int, default=5,
                    help="连续失败 N 次即急停（0=不停）")
    ap.add_argument("--build-timeout", type=int, default=3600)
    ap.add_argument("--sleep", type=float, default=0.2)
    ap.add_argument("--force", action="store_true", help="忽略 state 缓存，重建")
    ap.add_argument("--dry-run", action="store_true", help="只打印计划，不跑 docker")
    ap.add_argument("--no-gate", action="store_true", help="跳过 gate（仅调试；会记 notes）")
    ap.add_argument("--gate-image", action="store_true", default=True,
                    help="gate 第⑤条：检查项目镜像是否含 dc 注入源（默认开）")
    ap.add_argument("--no-image-selfheal", action="store_true",
                    help="[W3 Phase4(b)] 关闭 gate 第⑤条的**自动重建自愈**（则污染即 ABORT，W2 旧行为）")
    ap.add_argument("--architecture", default="x86_64", choices=["x86_64", "i386", "aarch64"],
                    help="[W3 Phase4(a)] 构建架构。**进缓存键与归档路径**，否则 x86_64/i386 产物"
                         "会互相覆盖（同 R16/R17 那类）。默认 x86_64；✅ W3 配对实验证明 i386 上报的"
                         "crash 在 x86_64 下同样复现，故常规路由不需要 i386")
    ap.add_argument("--commit-override", default=None,
                    help="`osv_id=sha[:depth][,…]`：Stage2 **强制**钉指定 commit（跳过 walk-back 计划）。"
                         "两个用途：①已知答案回归（P0-B/P0-C 手工跑过的 commit 有留存二进制 sha256，"
                         "可比对 ② 是否走对路径、构建是否 bit 可复现）；②[实现 W2] ⑥ 的 walk-back 循环"
                         "逐格调用本模块，用 `:depth` 把**实际格数**带进 build record → ③ 抄进 "
                         "observation → ⑤ 落 `walkback_depth_actual`（Phase 0(d) 要的字段）。")
    ap.add_argument("--min-free-gb", type=float, default=0.0,
                    help="[W3 Phase2] 磁盘余量护栏：低于此值即停止本轮（0=不检查）")
    ap.add_argument("--print-plan", action="store_true",
                    help="只打印每条 crash 的钉版计划（JSON 到 stdout），不跑 docker。⑥ 的 walk-back 用它。")
    ap.add_argument("--no-retry-network", dest="retry_network", action="store_false",
                    help="[W3 N16] 关闭 network_fetch 类失败的自动重试 1 次（默认开）")
    ap.add_argument("--no-precheck", action="store_true",
                    help="[W4 Phase3a] 关闭构建前 build.sh↔commit 静态预检（默认开）")
    ap.add_argument("--quiet-precheck", action="store_true", help="预检不打印明细")
    ap.add_argument("--no-era-precheckout", action="store_true",
                    help="关闭 era 预 checkout（对照组，用于 Phase 4 测「省一半」是否成立）")
    ap.add_argument("--prune-archive", action="store_true",
                    help="[W3 Phase2] 只做归档裁剪后退出（读 repro_dataset.jsonl 的 tier）")
    ap.add_argument("--dataset", default=os.path.join(rc.REPRO_DIR, "repro_dataset.jsonl"))
    ap.add_argument("--prune-dry", action="store_true",
                    help="只报告不删（与 --prune-apply 互斥；两者都不给时**默认 dry**，"
                         "[W4] 删除是不可逆操作，必须显式要求）")
    ap.add_argument("--prune-apply", action="store_true", help="[W4] 真删（显式）")
    ap.add_argument("--prune-force", action="store_true",
                    help="[W4] 即使有 M>0 个待删目录曾被 verified 引用也照删（会记审计）")
    a = ap.parse_args()

    if a.prune_archive:
        dry = not a.prune_apply            # [W4] 默认 dry-run
        r = prune_archive(a.dataset, a.state, dry=dry, prune_force=a.prune_force)
        log(f"[裁剪] {'（dry-run，未删）' if a.prune_dry else ''} → {json.dumps({k: v for k, v in r.items() if k not in ('pruned_dirs','kept_dirs')}, ensure_ascii=False)}")
        return 0

    scope = load_scope(a)
    log(f"[② 范围] {len(scope)} 条 crash，{len(set(r['project'] for r in scope))} 个项目，"
        f"stage={a.stage}")
    if not scope:
        log("  （空范围，退出）")
        return 0

    # ---------- gate ----------
    if a.print_plan:
        # [实现 W3] `--print-plan` **不跑 gate**：它只解析补丁链、不碰 docker/不构建，
        # 而 gate 的第⑤条要对每个项目 `docker run` 一次（~2-5s）→ ⑥ 逐条 crash 调它时
        # 会把「出计划」变成分钟级操作（✅ W3 实测：14 条 not_located 的 dry-run 卡住 >15min）。
        log("[gate] --print-plan：跳过（不碰 docker、不构建）")
    elif a.dry_run:
        log("[gate] --dry-run：跳过")
    elif a.no_gate:
        log("[gate] ⚠ --no-gate：跳过（会记进 notes）")
    else:
        projs = sorted(set(r["project"] for r in scope))
        log("[gate] §1.7 H 四条件 + 镜像污染检查：")
        ok, checks = worktree_gate(check_image=projs if a.gate_image else None,
                                   auto_rebuild_image=not a.no_image_selfheal)
        if not ok:
            write_blocked(checks, f"范围：{len(scope)} 条 crash / {len(projs)} 个项目")
            log("❌ gate 未通过 → ABORT（不带污染构建）")
            return 2
        log("  ✅ gate 全过")

    overrides, odepth = {}, {}
    if a.commit_override:
        for kv in a.commit_override.split(","):
            if "=" not in kv:
                continue
            k, v = kv.split("=", 1)
            k, v = k.strip(), v.strip()
            if ":" in v:                        # osv_id=sha:depth
                v, d = v.rsplit(":", 1)
                try:
                    odepth[k] = int(d)
                except ValueError:
                    pass
            overrides[k] = v
        log(f"[override] {len(overrides)} 条强制 commit: {overrides}"
            + (f"（depth={odepth}）" if odepth else ""))

    # --print-plan：只出计划（⑥ 的 walk-back 循环消费），不碰 docker
    if a.print_plan:
        plans = {}
        for r in scope:
            if overrides.get(r["osv_id"]):
                pl = [(odepth.get(r["osv_id"]), overrides[r["osv_id"]], "--commit-override")]
                why = None
            else:
                pl, why = plan_pinned(r, a)
            plans[r["osv_id"]] = {"project": r["project"], "sanitizer": r["sanitizer"],
                                  "plan": [[d, c, n] for d, c, n in pl], "no_plan_why": why,
                                  "static_check_verdict": r.get("static_check_verdict"),
                                  "commit_source": r.get("commit_source"),
                                  "pin_commit": r.get("pin_commit"),
                                  "repo_url": r.get("repo_url"), "repo_path": r.get("repo_path")}
        print(json.dumps(plans, ensure_ascii=False))
        return 0

    st = load_state(a.state)
    run_id = f"w2-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    st["runs"].append({"run_id": run_id, "stage": a.stage, "n_scope": len(scope),
                       "ts": int(time.time())})

    records = []
    n_builds = 0
    n_precheck_skip = 0
    precheck_blocked = False
    consec_fail = 0
    aborted = None

    def cache_get(key, need_targets=()):
        """查构建缓存。**[实现 W2 bug 修 B]** 命中还要求归档里**含本次需要的全部 target**，
        否则视为未命中重建（旧归档可能只存了当时请求的那一个 target）。"""
        if a.force:
            return None
        b = st["builds"].get(key)
        if not (b and b.get("build_status") == "ok" and b.get("binary_dir")
                and os.path.isdir(b["binary_dir"])):
            return None
        lack = [t for t in need_targets
                if not os.access(os.path.join(b["binary_dir"], t), os.X_OK)]
        if lack:
            # [实现 W2 bug 修 B-2] 缺件分两种：
            #  ① 该 commit **根本不产出**这个 target（✅ 实测 c-blosc2 HEAD 无 `compress_fuzzer`，
            #     build/out 里就只有 4 个 target）→ 重建也拿不到，**仍算命中**，否则每轮无限重建；
            #  ② 旧归档只存了当时请求的那一个 target（✅ 实测 pcre2 归档只有 `pcre2_fuzzer_16`）
            #     → 真缺件，必须重建。
            # 区分依据 = 那次构建自己记下的 `targets_absent_at_commit`。
            absent = set(b.get("targets_absent_at_commit") or [])
            real_lack = [t for t in lack if t not in absent]
            if real_lack:
                log(f"    ⚠ 缓存归档缺 target {real_lack} → 视为未命中、重建（W2 bug 修 B）")
                return None
            log(f"    ⓘ 缓存归档缺 {lack}，但该 commit 本就不产出（上次构建已记）→ 仍复用")
        return b

    def emit(rec):
        records.append(rec)
        with open(a.out, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if rec.get("build_status") == "ok":
            st["builds"][rec["key"]] = rec        # **归档成功才计入缓存**
        save_state(st, a.state)

    # ---------- Stage 1：HEAD ----------
    if a.stage in ("1", "auto"):
        byps = collections.defaultdict(list)
        for r in scope:
            byps[(r["project"], r["sanitizer"])].append(r)
        log(f"\n=== Stage1 HEAD：{len(byps)} 个 (project,sanitizer) 构建单元"
            f"（HEAD 构建**共享**：一次服务同组全部 crash）===")
        for (p, san), rs in sorted(byps.items()):
            targets = sorted(set(r["fuzz_target"] for r in rs if r.get("fuzz_target")))
            if not targets:
                for r in rs:
                    emit(_fail("head", p, san, None, 0, None, "", "no_target", 1,
                               extra={"osv_ids": [x["osv_id"] for x in rs]}))
                continue
            repo_path = next((r.get("repo_path") for r in rs if r.get("repo_path")), None)
            # HEAD 的缓存键要等 SHA 解析后才知道 → 先查上轮解析结果
            prev = st["head_sha_cache"].get(f"{p}|{san}")
            if prev and not a.force:
                hit = cache_get(bkey(p, san, prev["sha"], a.architecture), targets)
                if hit:
                    log(f"  [HEAD] {p}/{san} 命中缓存 {prev['sha'][:12]} → 复用 {hit['binary_dir']}")
                    h = dict(hit); h["cache_hit"] = True; h["run_id"] = run_id
                    h["osv_ids"] = [x["osv_id"] for x in rs]
                    emit(h); continue
            if disk_guard(a.min_free_gb, "Stage1"):
                aborted = f"磁盘余量 < {a.min_free_gb}G（Stage1）"; break
            if a.max_builds and n_builds >= a.max_builds:
                aborted = f"--max-builds {a.max_builds} 用尽（Stage1）"; break
            if a.dry_run:
                log(f"  [dry-run] HEAD {p}/{san} targets={targets} repo_path={repo_path}")
                n_builds += 1; continue
            rec = build_head(p, san, targets, st, a, repo_path=repo_path,
                             architecture=a.architecture)
            rec["run_id"] = run_id
            rec["osv_ids"] = [x["osv_id"] for x in rs]
            rec["n_crash_served"] = len(rs)
            emit(rec); n_builds += 1
            consec_fail = 0 if rec["build_status"] == "ok" else consec_fail + 1
            if a.stop_after_failures and consec_fail >= a.stop_after_failures:
                aborted = f"连续 {consec_fail} 次构建失败 → 急停"; break
        if aborted:
            log(f"\n⛔ {aborted}")

    # ---------- Stage 2：钉版 ----------
    if a.stage in ("2", "auto") and not aborted:
        todo = scope
        if a.stage == "auto":
            if a.observations and os.path.exists(a.observations):
                obs = {}
                for line in open(a.observations, encoding="utf-8"):
                    d = json.loads(line)
                    obs[d["osv_id"]] = d            # 同 osv_id 取最后一条
                todo = [r for r in scope if not (obs.get(r["osv_id"]) or {}).get("reproduced_any")]
                log(f"\n=== Stage2 钉版：auto 用 observations 筛出 {len(todo)}/{len(scope)} 条未复现 ===")
            else:
                log("\n⚠ --stage auto 但没给 --observations（或文件不存在）→ **只做 Stage1**"
                    "（不擅自把全部 crash 钉一遍：钉版 per-commit 独占，成本约 8×）")
                todo = []
        else:
            log(f"\n=== Stage2 钉版：{len(todo)} 条（per-commit 独占）===")
        # **尊重 ① 的 pinned_queue 顺序**（Phase 0(b)：同项目相邻 + issue_id 日期代理聚拢）
        order = {}
        try:
            bg = json.load(open(rc.BUILD_GROUPS_OUT, encoding="utf-8"))
            order = {x["osv_id"]: i for i, x in enumerate(bg.get("pinned_queue") or [])}
        except Exception:                                                 # noqa: BLE001
            pass
        todo = sorted(todo, key=lambda r: order.get(r["osv_id"], 10 ** 9))

        for r in todo:
            if a.max_builds and n_builds >= a.max_builds:
                aborted = f"--max-builds {a.max_builds} 用尽（Stage2）"; break
            if overrides.get(r["osv_id"]):
                plan, why = [(odepth.get(r["osv_id"]), overrides[r["osv_id"]],
                              "--commit-override（⑥ walk-back 逐格 / 已知答案回归）")], None
            else:
                plan, why = plan_pinned(r, a)
            if not plan:
                emit({**_base("pinned", r["project"], r["sanitizer"], None, 2),
                      "build_status": "skipped", "build_error_class": "no_pin_plan",
                      "notes": why, "osv_id": r["osv_id"], "run_id": run_id})
                continue
            built_ok = False
            for depth, commit, note in plan:
                if not commit:
                    log(f"    {r['osv_id']}: depth {depth} 无法解析（{note}）→ walk-back 中止")
                    break
                key = bkey(r["project"], r["sanitizer"], commit, a.architecture)
                hit = cache_get(key, [r["fuzz_target"]] if r.get("fuzz_target") else [])
                if hit:
                    log(f"    {r['osv_id']} depth={depth} 命中缓存 {commit[:12]} → 复用")
                    h = dict(hit); h["cache_hit"] = True; h["run_id"] = run_id
                    h["osv_id"] = r["osv_id"]; h["walkback_depth_actual"] = depth
                    emit(h); built_ok = True
                    break
                if disk_guard(a.min_free_gb, "Stage2"):
                    aborted = f"磁盘余量 < {a.min_free_gb}G（Stage2）"; break
                if a.max_builds and n_builds >= a.max_builds:
                    aborted = f"--max-builds {a.max_builds} 用尽（walk-back 中）"; break
                # [实现 W4 Phase3a] **构建前静态预检**（N19）：比早停更省——一次构建都不用跑
                if not a.no_precheck:
                    pc = precheck_buildscript(r["project"], r.get("repo_url"), commit,
                                              sleep=a.sleep, verbose=not a.quiet_precheck,
                                              repo_path=r.get("repo_path"))
                    if not pc["ok"]:
                        log(f"    ⛔ 预检判定 buildscript_mismatch：{pc['reason']}")
                        emit({**_base("pinned", r["project"], r["sanitizer"], commit, 2,
                                      a.architecture),
                              "build_status": "skipped", "build_error_class": "buildscript_mismatch",
                              "build_error_detail": pc["reason"], "build_seconds": 0,
                              "osv_id": r["osv_id"], "walkback_depth_actual": depth,
                              "notes": "W4 Phase3a 构建前预检拦截（未跑构建）"})
                        n_precheck_skip += 1
                        precheck_blocked = True
                        break
                # era 预 checkout（学习式）
                era, era_info = (None, None)
                if not a.no_era_precheckout:
                    m = resolve_commit_meta(r.get("repo_url"), commit, sleep=a.sleep)
                    era, era_info = era_suggestion(st, r["project"], (m or {}).get("date"))
                    if era:
                        log(f"    era 缓存命中：{era[:10]}（{(era_info or {}).get('era_ok')} 次成功）"
                            f"→ 预 checkout、跳过注定失败的首试")
                if a.dry_run:
                    log(f"    [dry-run] PIN {r['osv_id']} d={depth} {commit[:12]} era={era and era[:10]}")
                    n_builds += 1; continue
                rec = build_pinned(r["project"], r["sanitizer"], commit, r.get("repo_url"),
                                   r.get("repo_path"), [r["fuzz_target"]] if r.get("fuzz_target")
                                   else [], st, a, era_pre=era, depth=depth,
                                   architecture=a.architecture)
                rec["run_id"] = run_id
                rec["osv_id"] = r["osv_id"]
                rec["walkback_depth_planned"] = depth
                rec["walkback_note"] = note
                rec["era_cache_hit"] = bool(era)
                emit(rec); n_builds += 1
                consec_fail = 0 if rec["build_status"] == "ok" else consec_fail + 1
                if rec["build_status"] == "ok":
                    built_ok = True
                    break                      # 首个成功构建即停（复现判定交 ③/⑥）
                if a.stop_after_failures and consec_fail >= a.stop_after_failures:
                    aborted = f"连续 {consec_fail} 次构建失败 → 急停"; break
            if aborted:
                break
            # [实现 W2 修 E] ⑥ 的 walk-back 是**逐格**调本模块（--commit-override 单格），
            # 「三格全试完仍没复现」只有 ⑥ 知道 → 那种情况下不发 fail_both/walkback_exhausted，
            # 否则每格失败都会在 build_records 里留一条 premature 的 exhausted 记录。
            if precheck_blocked:
                precheck_blocked = False        # 每条 crash 独立；⑥ 据 class 决定是否放弃整条
            if not built_ok and plan and not overrides.get(r["osv_id"]):
                emit({**_base("pinned", r["project"], r["sanitizer"], None, 2),
                      "build_status": "fail_both", "build_error_class": "walkback_exhausted",
                      "notes": f"{len(plan)} 格全部**构建失败**（非「构建成功但未复现」）",
                      "osv_id": r["osv_id"],
                      "walkback_exhausted": True, "run_id": run_id})
        if aborted:
            log(f"\n⛔ {aborted}")

    save_state(st, a.state)
    # ---------- 汇总 ----------
    ct = collections.Counter(r.get("build_status") for r in records)
    cls = collections.Counter(r.get("build_error_class") for r in records if r.get("build_status") != "ok")
    secs = [r.get("build_seconds") or 0 for r in records if r.get("build_status") == "ok"]
    log(f"\n[② 汇总] 本轮记录 {len(records)} 条；实际构建 {n_builds} 次；状态 {dict(ct)}")
    if cls:
        log(f"  失败分类: {dict(cls.most_common())}")
    if secs:
        log(f"  成功构建时长: n={len(secs)} 中位 {sorted(secs)[len(secs)//2]:.0f}s "
            f"min {min(secs):.0f}s max {max(secs):.0f}s 合计 {sum(secs)/60:.1f}min")
    if aborted:
        log(f"  ⛔ 中止原因: {aborted}")
    log(f"  → {a.out}（append）；state = {a.state}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
