#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W5：② `precheck_buildscript` / `path_exists_at` 的**误报**自测（两个真 bug）。

预检的契约写在自己 docstring 里：**「无法判定时一律放行」**（宁漏勿误）——
因为误报会**跳过本能成功的构建**，比漏报（白跑一次）代价大（N23 的教训）。
✅ W5 实测发现两条违反该契约的路径：

  **bug①：`sha=None` 被判成「确定缺失」。** `_raw_url` 直接插值 →
  `https://github.com/<o>/<r>/raw/None/<path>` → 必然 404 → `path_exists_at` 返回
  **False**（确定缺失）而不是 **None**（无法判定）→ 预检 `ok=False` + `missing=[…]`。
  实证：libredwg 在 `sha=None` 下报 `missing=['./autogen.sh','examples/llvmfuzz.c']`、
  而 `checked=0 undecidable=0` —— **一次都没真查就宣布缺失**。
  生产调用点（build_orchestrator.py:1432）传的是 walk-back 计划里的真 commit，
  故当前**潜伏**；但任何拿不到 sha 的调用方（如离线筛选）都会中招。

  **bug②：候选路径保留 `./` 前缀** → `raw/<sha>/./autogen.sh` 这种 URL 不该用来判存在性；
  候选归一化漏了 `./`（只 strip 了 `/`），属同一族「归一化不足 → 假 404 → 误报」。

含**负对照**证明测试有牙：把 `path_exists_at` 强制成 False（真 sha）→ 预检必须**照旧报缺失**
（即修复没有把预检阉割成恒放行）。

全部用例**零网络**：修复后 `sha=None` 必须在发 HTTP 之前就短路。
复算：python3 preflight/w5_selftest_precheck_sha.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
import build_orchestrator as B       # noqa: E402

FAILS = []
REPO = "https://github.com/LibreDWG/libredwg"
PROJ = "libredwg"
RPATH = "/src/libredwg"
SHA = "625da7ad8b7f0000000000000000000000000000"


def ck(cond, msg):
    print(("  ✅ " if cond else "  ❌ ") + msg)
    if not cond:
        FAILS.append(msg)


class HttpSpy:
    """替掉 `rc.http_get`：记录调用次数 → 证明「无法判定」时零网络开销。"""

    def __init__(self, ret=(None, "http404")):
        self.n = 0
        self.ret = ret

    def __call__(self, url, **kw):
        self.n += 1
        return self.ret


def patched(spy=None, exists=None):
    """替掉边界。⚠ `exists` 必须是**同签名的可调用**并直接装上——
    W5 踩过：原实现把它又包了一层 lambda 并 `return exists`（返回的是 lambda 对象本身、
    恒为真）→ 预检以为「路径都存在」，[B]/[C] 两节因此**空过**。测试自己也会骗自己。"""
    import repro_common as rc
    saved = (rc.http_get, B.path_exists_at)
    if spy is not None:
        rc.http_get = spy
    if exists is not None:
        assert callable(exists), "exists 必须是可调用（同 path_exists_at 签名）"
        B.path_exists_at = exists
    return saved


def restore(saved):
    import repro_common as rc
    rc.http_get, B.path_exists_at = saved


def main():
    print("═" * 78)
    print("W5 ② 自测：预检不得误报（sha=None / `./` 前缀），且不得被修成恒放行")
    print("═" * 78)

    print("\n[A] bug①：sha=None → 必须「无法判定」而不是「确定缺失」")
    spy = HttpSpy()
    saved = patched(spy=spy)
    try:
        got = B.path_exists_at(REPO, None, "autogen.sh")
    finally:
        restore(saved)
    ck(got is None, f"path_exists_at(repo, sha=None, path) = {got!r}（期望 None=无法判定）")
    ck(spy.n == 0, f"且**零 HTTP**（实发 {spy.n} 次）→ 发请求前就短路，不浪费网络")

    spy = HttpSpy()
    saved = patched(spy=spy)
    try:
        got = B.path_exists_at(None, SHA, "autogen.sh")
    finally:
        restore(saved)
    ck(got is None, f"repo_url=None → {got!r}（同样无法判定，不发请求 {spy.n} 次）")

    spy = HttpSpy()
    saved = patched(spy=spy)
    try:
        res = B.precheck_buildscript(PROJ, REPO, None, verbose=False, repo_path=RPATH)
    finally:
        restore(saved)
    ck(res["ok"] is True, f"sha=None → 预检**放行**（ok={res['ok']}），契约「无法判定时一律放行」")
    ck(res["missing"] == [], f"missing 必须为空（实为 {res['missing']}）—— 没查过就不能说缺")
    ck(res["checked"] == 0 and res["undecidable"] == 0,
       f"checked={res['checked']} undecidable={res['undecidable']}（都没真查）")
    ck(res.get("reason") == "no_sha", f"reason 要能与「0 候选」区分：{res.get('reason')!r}")
    ck(spy.n == 0, f"零 HTTP（实发 {spy.n} 次）")

    print("\n[B] bug②：候选路径不得带 `./` 前缀（归一化不足 → 假 404）")
    asked = []

    def fake_ok(repo_url, sha, path, sleep=0.0):
        asked.append(path)
        return True
    saved = patched(exists=fake_ok)
    try:
        B.precheck_buildscript(PROJ, REPO, SHA, verbose=False, repo_path=RPATH)
    finally:
        restore(saved)
    ck(bool(asked), f"该项目确实产生了候选路径（实查 {len(asked)} 个）→ 本节不是空过")
    bad = [p for p in asked if p.startswith("./") or p.startswith("/")]
    ck(not bad, f"无 `./` 或 `/` 前缀的候选（违规：{bad}）")
    ck(all("/" in p for p in asked) or asked, f"候选形态：{sorted(set(asked))[:5]}")

    print("\n[D] bug③：解释器与脚本路径之间夹了 flag（`bash -x ./a/b.sh`）→ 形态②漏检")
    # ✅ W5 实证：ndpi/build.sh 第 24 行 `bash -x ./ndpi/tests/ossfuzz.sh`，而
    # `tests/ossfuzz.sh` 在抽样的 3 个 commit 上**全部缺失**（= pcapplusplus/libspng 同型灾难）。
    # 原 SCRIPT_RE 要求路径紧跟在 `bash ` 之后 → 被 `-x` 挡掉 → 预检报 `no_candidate_paths`
    # （「无证据」），离线筛选因此把 ndpi 排到**第 1 位**。
    asked2 = []

    def rec2(repo_url, sha, path, sleep=0.0):
        asked2.append(path)
        return True
    saved = patched(exists=rec2)
    try:
        B.precheck_buildscript("ndpi", "https://github.com/ntop/nDPI.git", SHA,
                               verbose=False, repo_path="/src/ndpi")
    finally:
        restore(saved)
    ck("tests/ossfuzz.sh" in asked2,
       f"`bash -x ./ndpi/tests/ossfuzz.sh` 必须被抽成候选 `tests/ossfuzz.sh`（实抽 {sorted(set(asked2))}）")
    ck(not [x for x in asked2 if x.startswith("./") or x.startswith("ndpi/")],
       f"且已归一化掉 `./` 与仓库名前缀（违规 {[x for x in asked2 if x.startswith(('./','ndpi/'))]}）")

    print("\n[E] bug④：整行就是一个裸脚本路径（libxml2 的 build.sh 全文只有一行）")
    # ✅ W5 实证：libxml2/build.sh 去掉注释后**只有一行** `fuzz/oss-fuzz-build.sh`
    # —— 没有解释器、没有 `$SRC/`、没有 `./` 前缀 → 原 SCRIPT_RE 的三个 alternative 全不匹配
    # → 预检报 `no_candidate_paths`（**无证据**），于是 52 条池只能被判「ⓘ 只能探针」。
    # 而它的 repo 在 **gitlab.gnome.org**，`path_exists_at` 是支持 gitlab 的 → 本来查得了。
    asked3 = []

    def rec3(repo_url, sha, path, sleep=0.0):
        asked3.append(path)
        return True
    saved = patched(exists=rec3)
    try:
        res3 = B.precheck_buildscript("libxml2", "https://gitlab.gnome.org/GNOME/libxml2.git",
                                      SHA, verbose=False, repo_path="/src/libxml2")
    finally:
        restore(saved)
    ck("fuzz/oss-fuzz-build.sh" in asked3,
       f"整行裸脚本路径必须被抽成候选（实抽 {sorted(set(asked3))}）")
    ck(res3.get("reason") != "no_candidate_paths",
       f"reason 不再是 no_candidate_paths（实为 {res3.get('reason')!r}）→ 该项目从「无证据」变「可判」")

    print("\n[F] 负对照：新 alternative 不得放宽成「任何行里出现的 .sh 路径」")
    # 若把 `^\s*` 单独当 alternative（不要求整行就是路径），`cp foo/bar.sh $OUT/` 这类
    # **非执行**语境也会被抽进来 → 假 404 → 误报（N23 的教训：误报比漏报更糟）。
    import tempfile as _tf
    td = _tf.mkdtemp()
    fake_proj = os.path.join(td, "projects", "fakeproj")
    os.makedirs(fake_proj, exist_ok=True)
    with open(os.path.join(fake_proj, "build.sh"), "w", encoding="utf-8") as f:
        f.write("#!/bin/bash -eu\ncp tools/helper.sh $OUT/\necho docs/guide.py\nmake -j8\n")
    asked4 = []

    def rec4(repo_url, sha, path, sleep=0.0):
        asked4.append(path)
        return True
    saved_wt = B.WT
    B.WT = td
    saved = patched(exists=rec4)
    try:
        B.precheck_buildscript("fakeproj", "https://github.com/x/y.git", SHA,
                               verbose=False, repo_path="/src/y")
    finally:
        restore(saved)
        B.WT = saved_wt
    ck(not any(p.endswith("helper.sh") or p.endswith("guide.py") for p in asked4),
       f"`cp`/`echo` 语境里的脚本路径**不得**被当成执行目标（实抽 {sorted(set(asked4))}）")

    print("\n[C] 负对照：修复不得把预检阉割成「恒放行」")
    saved = patched(exists=lambda repo_url, sha, path, sleep=0.0: False)
    try:
        res = B.precheck_buildscript(PROJ, REPO, SHA, verbose=False, repo_path=RPATH)
    finally:
        restore(saved)
    ck(res["ok"] is False and res["missing"],
       f"真 sha + 路径确实不存在 → 照旧报缺失（ok={res['ok']}, missing={res['missing'][:3]}）")
    saved = patched(exists=lambda repo_url, sha, path, sleep=0.0: True)
    try:
        res2 = B.precheck_buildscript(PROJ, REPO, SHA, verbose=False, repo_path=RPATH)
    finally:
        restore(saved)
    ck(res2["ok"] is True and res2["checked"] > 0 and not res2["missing"],
       f"真 sha + 路径都在 → 放行且 checked={res2['checked']}（计数仍准确）")

    print("\n" + (f"❌ {len(FAILS)} 项未通过：{FAILS}" if FAILS else "✅ 全部通过"))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
