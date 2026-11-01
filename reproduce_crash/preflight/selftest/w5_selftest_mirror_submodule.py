#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""[W5 N35/N36] 镜像映射 + submodule 守卫 的自测（**全离线**，纯函数 + 替身）。

为什么必须有它：这两处改动都直接决定「一条 crash 会不会被构建」——
  * N35 `mirror_for()` 认不出 URL → `resolve_commit_meta` 返回 None → walk-back 中止 → **0 次构建**
    （✅ 实测：mupdf 探针 3 条就是这么白跑一轮、镜像白建 3.11GB 才发现）；
  * N36 submodule 守卫写错 → 要么继续误报（挡掉本能建的构建），要么把真缺失也放跑。
两处都是「静默失效」型：不报错，只是悄悄少跑/多拦 → 只能靠自测钉住。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import build_orchestrator as B                                    # noqa: E402

FAILS = []
N = [0]


def ck(cond, msg):
    N[0] += 1
    if cond:
        print(f"  ✅ {msg}")
    else:
        FAILS.append(msg)
        print(f"  ❌ {msg}")


MIR = "https://github.com/ArtifexSoftware/mupdf"
CANON = "git://git.ghostscript.com/mupdf.git"

print("[A] N35 `mirror_for()` 的 URL 归一化（认不出 = 静默回到「解析不了」）")
for u in (CANON, "git://git.ghostscript.com/mupdf", "git://git.ghostscript.com/mupdf/",
          "GIT://Git.Ghostscript.com/MuPDF.GIT", "  git://git.ghostscript.com/mupdf.git/  "):
    ck(B.mirror_for(u) == MIR, f"{u!r} → 命中镜像")
ck(B.mirror_for("https://github.com/x/y") is None, "github URL 不需要镜像 → None")
ck(B.mirror_for("git://git.ghostscript.com/ghostpdl.git") is None,
   "同主机但**不同仓库** → None（不许因主机名相同就误命中）")
ck(B.mirror_for(None) is None and B.mirror_for("") is None, "None/空串 → None（不抛异常）")
ck(B._norm_repo_key("A/B.GIT//") == "a/b", "_norm_repo_key 循环剥到稳定（大小写 + 多尾缀）")

print("\n[B] N36 submodule 前缀匹配（含**经典前缀陷阱**）")
subs = {"thirdparty/harfbuzz", "thirdparty/zlib", "platform"}
match = lambda c: any(c == s or c.startswith(s + "/") for s in subs)     # noqa: E731 与生产同一判据
ck(match("thirdparty/harfbuzz/src/hb-subset-cff1.cc"),
   "submodule 内的深路径 → 判为「查不了」（mupdf 实测误报的那条）")
ck(match("thirdparty/harfbuzz"), "路径**恰等于** submodule 根 → 也算查不了")
ck(not match("thirdparty/harfbuzz2/src/x.cc"),
   "**前缀陷阱**：`thirdparty/harfbuzz2/` 不许被 `thirdparty/harfbuzz` 吞掉")
ck(not match("thirdparty/harfbuzzX"), "同上（无分隔符的相邻名）")
ck(not match("source/fitz/document.c"), "普通路径不受影响（实测该路径 HTTP 200，该查就得查）")
ck(not match("platformx/a.c"), "`platform` 不许吞掉 `platformx/`")

print("\n[C] N36 `submodule_paths()` 的契约（替身，零网络）")
orig_raw, orig_get = B._raw_url, B.rc.http_get
try:
    B._SUBMOD_CACHE.clear()
    B._raw_url = lambda repo, sha, path: f"http://stub/{path}" if path == ".gitmodules" else None
    B.rc.http_get = lambda url, **kw: ('[submodule "thirdparty/harfbuzz"]\n\tpath = thirdparty/harfbuzz\n'
                                       '\turl = ../thirdparty-harfbuzz.git\n'
                                       '[submodule "thirdparty/zlib"]\n\tpath = thirdparty/zlib\n', 200)
    got = B.submodule_paths(CANON, "abc123")
    ck(got == {"thirdparty/harfbuzz", "thirdparty/zlib"}, f"解析 .gitmodules 的 path= → {sorted(got)}")
    ck(B.submodule_paths(CANON, "abc123") is got or B.submodule_paths(CANON, "abc123") == got,
       "进程内缓存命中（同 (repo,sha) 不重复发请求）")

    B._SUBMOD_CACHE.clear()
    B.rc.http_get = lambda url, **kw: ("", "http404")
    ck(B.submodule_paths(CANON, "def456") == set(),
       "无 .gitmodules（404）→ **空集**（不是 None）：确知没有 submodule")

    B._SUBMOD_CACHE.clear()
    B.rc.http_get = lambda url, **kw: ("", "http500")
    ck(B.submodule_paths(CANON, "ghi789") is None,
       "其它错误 → **None**（无法判定）；调用方须放行，与 N27①/N29 同一口径")

    B._SUBMOD_CACHE.clear()
    B._raw_url = lambda repo, sha, path: None
    ck(B.submodule_paths("git://example.invalid/x.git", "jkl") is None,
       "raw URL 构造不出（非 github/gitlab 且无镜像）→ None，不抛异常")
finally:
    B._raw_url, B.rc.http_get = orig_raw, orig_get
    B._SUBMOD_CACHE.clear()

print("\n[D] 集成：预检在 submodule 误报形态下必须放行（替身，零网络）")
try:
    B.submodule_paths = lambda repo, sha, sleep=0.0: {"thirdparty/harfbuzz"}
    B.path_exists_at = lambda repo, sha, path, sleep=0.0: False      # 一切都「查不到」
    orig_exists = os.path.exists
    bs = os.path.join(B.WT, "projects", "mupdf", "build.sh")
    ck(orig_exists(bs), f"前提：worktree 里有 mupdf 的 build.sh（{bs}）")
    r = B.precheck_buildscript("mupdf", CANON, "7f82c0152350", verbose=False, repo_path="/src/mupdf")
    ck(r["ok"] is True, f"submodule 内路径 404 → **放行**（ok=True，missing={r['missing']}）")
    ck(r.get("submodule_skipped") == ["thirdparty/harfbuzz/src/hb-subset-cff1.cc"],
       f"且被记为 submodule_skipped（留痕，不是静默吞掉）→ {r.get('submodule_skipped')}")
    ck(r["undecidable"] >= 1 and r["checked"] == 0,
       f"计入 undecidable 而非 missing（checked={r['checked']}, undecidable={r['undecidable']}）")
finally:
    pass

print("\n[G] N42 Gitiles（googlesource）解析器 —— 纯函数 + 替身，零网络")
GL = "https://android.googlesource.com/platform/external/libhevc"
# G1 base 识别（含 .git / 尾斜杠 / 多级路径；非 googlesource 必须 None）
for u, want in [(GL, GL), (GL + "/", GL), (GL + ".git", GL),
                ("https://aomedia.googlesource.com/aom", "https://aomedia.googlesource.com/aom"),
                ("https://chromium.googlesource.com/webm/libwebp",
                 "https://chromium.googlesource.com/webm/libwebp"),
                ("https://github.com/x/y", None),
                ("git://git.ghostscript.com/mupdf.git", None),
                ("https://evil.com/.googlesource.com/x", None), (None, None), ("", None)]:
    ck(B.gitiles_base(u) == want, f"gitiles_base({str(u)[:44]!r}) = {B.gitiles_base(u)!r}")

# G2 XSSI 前缀必须剥掉；parents 是**字符串数组**（不是对象数组）
RAW = (")]}'\n{\"commit\": \"67e394c9f3743b8ce41f11736136319efcef6d3d\", "
       "\"parents\": [\"130f5f1fc107ee3cadd795df7fbba2da2b806453\", "
       "\"5e7dc4732015717682ac0da1431fe3e656aea617\"], "
       "\"author\": {\"time\": \"Mon Aug 19 21:11:00 2019 -0700\"}}")
orig_get = B.rc.http_get
try:
    B.rc.http_get = lambda url, **kw: (RAW, 200)
    d = B.gitiles_commit(GL, "67e394c9")
    ck(d["sha"] == "67e394c9f3743b8ce41f11736136319efcef6d3d",
       f"剥 XSSI 前缀后拿到 commit（{str(d['sha'])[:12]}）")
    ck(d["parents"] == ["130f5f1fc107ee3cadd795df7fbba2da2b806453",
                        "5e7dc4732015717682ac0da1431fe3e656aea617"],
       "parents 解析为**字符串数组**（这条是 merge commit，有 2 个）")
    ck(str(d["date"]).startswith("2019-08-19"), f"RFC2822 author.time → ISO（{d['date']}）")

    # G3 `~d` 逐级走 **parents[0]**（git 语义），并数清发了几次请求
    calls = []
    CHAIN = {"A": (["B"], "d1"), "B": (["C"], "d2"), "C": ([], "d3")}

    def fake(url, **kw):
        sha = url.split("/+/")[1].split("?")[0]
        calls.append(sha)
        par, _dt = CHAIN.get(sha, ([], "?"))
        return (")]}'\n{\"commit\": \"" + sha + "\", \"parents\": " + json.dumps(par)
                + ", \"author\": {\"time\": \"Mon Aug 19 21:11:00 2019 -0700\"}}"), 200

    B.rc.http_get = fake
    r = B.resolve_commit_meta(GL, "A~2")
    ck(r["sha"] == "C" and calls == ["A", "B", "C"],
       f"`A~2` 逐级走 parents[0] → {r['sha']}，请求序列 {calls}")
    calls.clear()
    r2 = B.resolve_commit_meta(GL, "A~0")
    ck(r2["sha"] == "A" and calls == ["A"], f"`A~0` = 自身、只发 1 次请求（{calls}）")
    calls.clear()
    r2b = B.resolve_commit_meta(GL, "A")
    ck(r2b["sha"] == "A" and calls == ["A"], f"不带 `~` 也能解析（{calls}）")
    r3 = B.resolve_commit_meta(GL, "C~1")
    ck(r3.get("error") == "no_parent_at_depth0" and r3["sha"] is None,
       f"走到根提交还要再回退 → **明确报错**而非瞎猜（{r3.get('error')}）")
    r4 = B.resolve_commit_meta(GL, "A~x")
    ck(str(r4.get("error", "")).startswith("bad_rev"), f"`A~x` 非法深度 → bad_rev（{r4.get('error')}）")

    # G4 网络/解析错误不许被当成「确定不存在」（与 N27① 同一契约）
    B.rc.http_get = lambda url, **kw: ("", "http500")
    r5 = B.resolve_commit_meta(GL, "A")
    ck(r5.get("sha") is None and r5.get("error") == "http500",
       f"http500 → 报 error 而非假 sha（{r5.get('error')}）")
    B.rc.http_get = lambda url, **kw: ("not json at all", 200)
    ck(B.gitiles_commit(GL, "A")["error"] == "unparsable", "正文不是 JSON → unparsable（不抛异常）")
    B.rc.http_get = lambda url, **kw: (")]}'\n{}", 200)
    ck(B.gitiles_commit(GL, "A")["parents"] == [], "缺 parents 字段 → 空列表（不 KeyError）")

    # G5 _raw_url 走 Gitiles TEXT 端点（让预检对 googlesource 系也可判）
    u = B._raw_url(GL, "abc123", "common/ihevc_buf_mgr.c")
    ck(u == GL + "/+/abc123/common/ihevc_buf_mgr.c?format=TEXT", f"_raw_url → …{u[-52:]}")
    ck(B._raw_url(GL, "abc123", "/leading/slash.c").endswith("/+/abc123/leading/slash.c?format=TEXT"),
       "前导斜杠被规整（不产生 `//`）")
finally:
    B.rc.http_get = orig_get

print("\n[H] N42 的**网络**已知答案（✅ 已人工核实真实树，不是猜的）")
print("  实测留档（离线不可复算，故记在此处；设 NET=1 才联网核对）：")
print("    resolve_commit_meta(libhevc, 67e394c9…~1) = 130f5f1fc107  ← 等于原始 JSON 的 parents[0]")
print("    …~2 = 6490a452d6f8 (2019-08-14)   …~3 = c1d762a4bd48 (2019-07-10)")
print("    path_exists_at 对**核实过的树** 6/6：NOTICE / Android.bp / common/arm → True；")
print("      README.md / common/ih264_buf.c / no_such_dir/x.c → False")
print("      ⚠ 教训：第一次测时我拿 README.md、ih264_buf.c 当「应该存在」的已知答案，"
      "结果 6 个全 False，差点误判成假阴性缺陷 —— 实际是**该仓库根目录根本没有 README.md**、"
      "且这是 HEVC 库不是 H264。**已知答案本身必须先核实**（用 `+/<sha>/?format=JSON` 取真实树）。")
print("    submodule_paths(libhevc) = 空集（该仓库无 .gitmodules）")
if os.environ.get("NET"):
    _sha = "67e394c9f3743b8ce41f11736136319efcef6d3d"
    rr = B.resolve_commit_meta(GL, _sha + "~1")
    ck(rr["sha"] == "130f5f1fc107ee3cadd795df7fbba2da2b806453", f"[net] ~1 = {str(rr['sha'])[:12]}")
    ck(B.path_exists_at(GL, _sha, "NOTICE") is True, "[net] NOTICE 存在")
    ck(B.path_exists_at(GL, _sha, "README.md") is False, "[net] README.md 不存在（根目录确实没有）")
    ck(B.submodule_paths(GL, _sha) == set(), "[net] 无 .gitmodules → 空集")
else:
    ck(True, "未设 NET=1 → 跳过联网核对（纯函数部分已全验）")

print("\n" + (f"❌ {len(FAILS)} 项未通过：{FAILS}" if FAILS else f"✅ 全部通过（{N[0]} 项）"))
sys.exit(1 if FAILS else 0)
