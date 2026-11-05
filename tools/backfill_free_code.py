"""补全 `facts.json` 里 free 站点的释放表达式（R12）。

## 为什么

`s2_2_facts.py:861` 里 free 站点是硬编码 `"code": None` 的：
它只从 ASan 报告的 "freed by" 栈拿到了**函数名 + 行号**，从来没读过那一行源码。
后果：116/125 个 free 站点不知道"释放的是 `obj->field` 还是 `free(ptr)`"，
于是"经结构体字段的跨函数 UAF"这类形态**无从判定**。

## 做法

1. 从 `report.log` 的 "freed by" 段重新解析出 `(fn, abs_path, line)`（`s2_2_facts` 拿过但没存）；
2. 按 `pin_commit` 用 raw HTTP 拉**那一个文件**（不克隆整仓）；
3. 读那一行，填进 `facts.sites[kind=free].code`（同时补 `file`）。

## 顺带修 `entity.name`

`freed_ptr` = `facts.entity.name`。有 4/110 是**全大写常量**或**类型名**
（`LOW_COMPLEXITY` / `HB_AAT_..._CASE` / `CURLOPT_FTP_SSL_CCC` / `uint32_t`），
不是指针。这些会让"110 条"这个分母掺假阳性。这里标 `entity_name_rejected` 并清空。

用法：
    python3 tools/backfill_free_code.py            # 干跑，只报
    python3 tools/backfill_free_code.py --write    # 真写
"""
import argparse
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRASH = os.path.join(ROOT, "reproduce_crash", "artifacts", "by_crash_type",
                     "heap-use-after-free")
FACTS = os.path.join(ROOT, "artifacts", "facts")

TYPEY = re.compile(r"^(u?int\d*_t|size_t|ssize_t|void|char|short|long|unsigned|signed|"
                   r"int|float|double|bool|_Bool|wchar_t)$")
ALLCAP = re.compile(r"^[A-Z][A-Z0-9_]{3,}$")

_CACHE = {}


def raw_url(repo_url, sha, path):
    """按 host 拼 raw 文件 URL。"""
    u = (repo_url or "").rstrip("/")
    if u.endswith(".git"):
        u = u[:-4]
    if "googlesource.com" in u:
        return f"{u}/+/{sha}/{path}?format=TEXT"
    if "gitlab" in u:
        return f"{u}/-/raw/{sha}/{path}"
        return f"{u}/-/raw/{sha}/{path}"
    m = re.search(r"github\.com[/:]([^/]+)/([^/]+)$", u)
    if m:
        return f"https://raw.githubusercontent.com/{m.group(1)}/{m.group(2)}/{sha}/{path}"
    return None


def fetch(repo_url, sha, path):
    key = (repo_url, sha, path)
    if key in _CACHE:
        return _CACHE[key]
    out = None
    url = raw_url(repo_url, sha, path)
    if url:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
            raw = urllib.request.urlopen(req, timeout=30).read()
            if url.endswith("?format=TEXT"):
                import base64
                raw = base64.b64decode(raw)
            out = raw.decode("utf-8", "replace")
        except Exception:
            out = None
    _CACHE[key] = out
    return out


def parse_freed_by(report_path):
    """从 report.log 的 "freed by" 段取 (fn, abs_path, line) 列表。"""
    if not os.path.isfile(report_path):
        return []
    frames, on = [], False
    for ln in open(report_path, encoding="utf-8", errors="replace"):
        if re.match(r"^\s*freed by thread", ln):
            on = True
            continue
        if on:
            if ln.strip() == "" or re.match(r"^\s*(previously allocated|Shadow bytes|"
                                            r"SUMMARY|==\d+==|#\d+\s+\S+\s+in\s+(?!))", ln):
                if frames:
                    break
                continue
            # 2026-11-05（R12）修：函数名里可能有**空格**（C++ 完整签名），
            # 原来用 `(\S+)` 会在第一个空格处失败、整帧被丢掉——
            # 于是 `#1 DecreasePicBuff(...) @234` 没了，只剩 `#2 WelsRequestMem @421`，
            # 把"包装内部释放"误判成"包装调用"。
            # 改成非贪婪匹配 + 路径必须是最后一个 `/...:行号`。
            m = re.search(r"in\s+(.+?)\s+(/[^\s:]+):(\d+)", ln)
            if m:
                frames.append((m.group(1), m.group(2), int(m.group(3))))
            elif frames and not re.match(r"^\s*#\d+", ln):
                break
    return frames


def pick_frame(frames, fn):
    """从 freed-by 帧里挑出"真正做释放的那一帧"。

    - 跳过落到 `compiler-rt` / `llvm-project` 的**拦截器**帧；
    - 先按函数名匹配（报告里是短名，`facts.free_fn` 可能是完整签名 → 取 `::`/`(` 前那段比）；
    - 匹配不上就回退到第一个非拦截器帧（很多项目的释放包装是 inline 的，
      `facts.free_fn` 记的是包装名，而栈上只有它被内联后的调用者）。
    """
    real = [f for f in frames
            if "compiler-rt" not in f[1] and "llvm-project" not in f[1]
            and "/lib/asan/" not in f[1]]
    if not real:
        return None
    short = (fn or "").split("(")[0].split("::")[-1].strip()
    for f in real:
        if f[0] == fn or (short and (f[0] == short or f[0].endswith(short))):
            return f
    return real[0]


def repo_rel(abs_path):
    """把报告里的绝对路径归一化成仓库相对路径。

    实际见过的形态：
      `/src/libxml2/valid.c`                        → `valid.c`
      `/work/build/../../src/perfetto/src/x.cc`     → `src/x.cc`（要真的解 `..`）
    """
    p = (abs_path or "").lstrip("/")
    # 先用 posixpath 解 `..`（`work/build/../../src/x` → `src/x`）
    import posixpath
    p = posixpath.normpath(p)
    m = re.match(r"^src/[^/]+/(.+)$", p)
    if m:
        return m.group(1)
    m = re.match(r"^src/(.+)$", p)
    return m.group(1) if m else p


def find_report(osv):
    for dp, _, fns in os.walk(CRASH):
        if "report.log" in fns and os.path.basename(dp) == osv:
            return os.path.join(dp, "report.log")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="已有 code 也重新推导（解析器改过之后要用这个覆盖旧值）")
    a = ap.parse_args()

    rec = {}
    for ln in open(os.path.join(ROOT, "artifacts", "reproduced_crashes.jsonl"),
                   encoding="utf-8"):
        ln = ln.strip()
        if ln:
            d = json.loads(ln)
            rec[d.get("osv_id")] = d

    stats = {"total": 0, "filled": 0, "no_report": 0, "no_frame": 0,
             "no_fetch": 0, "name_rejected": 0}
    for fn in sorted(os.listdir(FACTS)):
        fp = os.path.join(FACTS, fn, "facts.json")
        if not os.path.isfile(fp):
            continue
        d = json.load(open(fp, encoding="utf-8"))
        if d.get("crash_type") != "heap-use-after-free":
            continue
        stats["total"] += 1
        changed = False

        # ── ① entity.name 像常量/类型名 → 不是指针 ──
        ent = d.get("entity") or {}
        nm = ent.get("name") or ""
        if nm and (TYPEY.match(nm) or ALLCAP.match(nm)):
            ent["_rejected_name"] = nm
            ent["name"] = None
            d["entity"] = ent
            stats["name_rejected"] += 1
            changed = True

        # ── ② 补 free 站点的 code ──
        frees = [s for s in (d.get("sites") or []) if s.get("kind") == "free"]
        for s in frees:
            if s.get("code") and not a.force:
                continue
            rp = find_report(d["osv_id"])
            if not rp:
                stats["no_report"] += 1
                break
            frames = parse_freed_by(rp)
            hit = pick_frame(frames, s.get("fn"))
            if not hit:
                stats["no_frame"] += 1
                break
            _f, absp, line = hit
            rel = repo_rel(absp)
            r = rec.get(d["osv_id"]) or {}
            txt = fetch(r.get("repo_url"), r.get("pin_commit"), rel)
            if txt is None:
                stats["no_fetch"] += 1
                break
            lines = txt.split("\n")
            if not (1 <= line <= len(lines)):
                stats["no_fetch"] += 1
                break
            s["code"] = lines[line - 1].strip()
            s["file"] = rel
            s["_line_in_repo"] = line
            stats["filled"] += 1
            changed = True
            break

        if changed and a.write:
            json.dump(d, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"  UAF facts: {stats['total']}")
    print(f"  ✅ 补上释放表达式: {stats['filled']}")
    print(f"  ✅ entity.name 判为常量/类型名（已清空）: {stats['name_rejected']}")
    print(f"  ⚠️ 找不到 report.log: {stats['no_report']}")
    print(f"  ⚠️ freed-by 段里没有对应帧: {stats['no_frame']}")
    print(f"  ⚠️ 拉不到源码: {stats['no_fetch']}")
    print(f"  {'已写回' if a.write else '（干跑，加 --write 才写）'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
