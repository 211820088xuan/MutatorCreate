"""R18：量 CPG 的 per-file 覆盖率。

对每个 CPG 的**每个源码文件**算：`CPG 里最后一行调用的行号 / 源码总行数`。
这是粗指标，但 `46%` 和 `99.97%` 的差距一眼能看出来。

**关键**：源码必须是 **pin**（限制 17）。这里直接用 `/tmp/opencode/cpg_cache/src/<repo>_<pin12>`
（`fetch` 用 `ensure_src` 按 commit 提取的那些）。

增量落盘：`docs/runs/r18/results.jsonl`（一行一个 CPG），可续跑。
每文件明细：`docs/runs/r18/coverage.tsv`。

用法（后台）：
    mkdir -p docs/runs/r18
    setsid nohup python3 tools/r18_cpg_coverage.py > docs/runs/r18/run.log 2>&1 < /dev/null &
    pgrep -f 'r18_cpg_coverag[e]' | head -1 > docs/runs/r18/run.pid
"""
import json
import os
import signal
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "runs", "r18")
RESULTS = os.path.join(OUT, "results.jsonl")
COV_TSV = os.path.join(OUT, "coverage.tsv")
CPGDIR = os.path.join(ROOT, "cpg_files")
SRCDIR = "/tmp/opencode/cpg_cache/src"
JL = "/usr/local/lib/python3.10/dist-packages/pyjoern/bin/joern-cli"
JOERN = os.path.join(JL, "joern")
PER_ITEM_TIMEOUT = 900
SRC_EXT = (".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp")

# R17 的 10 个 pin + libredwg 对照基准（同一个）
CPGS = [
    ("libredwg", "ff69eeda6658", "github.com_LibreDWG_libredwg"),
    ("libxml2", "d4d1f3f33d6d", "gitlab.gnome.org_GNOME_libxml2.git"),
    ("libxml2", "00ed736eecf9", "gitlab.gnome.org_GNOME_libxml2.git"),
    ("libxml2", "9de7b94d4ffb", "gitlab.gnome.org_GNOME_libxml2.git"),
    ("libxml2", "e45a4d711500", "gitlab.gnome.org_GNOME_libxml2.git"),
    ("libxml2", "f0fd1b67fc88", "gitlab.gnome.org_GNOME_libxml2.git"),
    ("igraph", "c83b6ecdc3fe", "github.com_igraph_igraph"),
    ("igraph", "883bd139af37", "github.com_igraph_igraph"),
    ("leptonica", "90ec70fd4322", "github.com_DanBloomberg_leptonica.git"),
    ("leptonica", "8d7717457caf", "github.com_DanBloomberg_leptonica.git"),
]

Q = r'''
importCpg("__CPG__")
val byM = cpg.method.l.groupBy(m => m.file.name.headOption.getOrElse("?"))
byM.foreach { case (f, ms) =>
  val real = ms.filter(_.name != "<global>")
  val maxEnd = real.flatMap(_.lineNumberEnd).maxOption.getOrElse(0)
  println(s"@@F\t$f\t${real.size}\t$maxEnd\t${ms.size - real.size}")
}
val byC = cpg.call.l.groupBy(c => c.file.name.headOption.getOrElse("?"))
byC.foreach { case (f, cs) =>
  println(s"@@C\t$f\t${cs.size}\t${cs.flatMap(_.lineNumber).maxOption.getOrElse(0)}")
}
'''


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run_joern(scala_src, tag):
    sc = os.path.join(OUT, f"_q_{tag}.scala")
    open(sc, "w", encoding="utf-8").write(scala_src)
    t0 = time.time()
    p = subprocess.Popen([JOERN, "--script", sc], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, errors="replace",
                         start_new_session=True, stdin=subprocess.DEVNULL)
    try:
        out, err = p.communicate(timeout=PER_ITEM_TIMEOUT)
        return p.returncode, out, err, time.time() - t0
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        except Exception:
            pass
        try:
            p.communicate(timeout=30)
        except Exception:
            pass
        return "timeout", "", "", time.time() - t0


def done():
    s = set()
    if os.path.isfile(RESULTS):
        for ln in open(RESULTS, encoding="utf-8"):
            ln = ln.strip()
            if not ln:
                continue
            try:
                s.add(json.loads(ln)["key"])
            except Exception:
                pass
    return s


def src_dir(prefix, pin):
    d = os.path.join(SRCDIR, f"{prefix}_{pin}")
    return d if os.path.isdir(d) else None


def count_lines(p):
    try:
        with open(p, "rb") as fh:
            return sum(1 for _ in fh)
    except Exception:
        return 0


def classify(ratio):
    if ratio is None:
        return "MISSING"
    if ratio >= 0.90:
        return "OK"
    if ratio >= 0.50:
        return "PARTIAL"
    return "BAD"


def measure(proj, pin, prefix):
    key = f"{proj}_{pin}"
    cpg = os.path.join(CPGDIR, key + ".cpg")
    src = src_dir(prefix, pin)
    if not (os.path.isfile(cpg) and src):
        rec = dict(key=key, project=proj, pin=pin, error=f"cpg={os.path.isfile(cpg)} src={bool(src)}")
        json.dump(rec, open(RESULTS, "a", encoding="utf-8"), ensure_ascii=False)
        open(RESULTS, "a", encoding="utf-8").write("\n")
        log(f"{key} 跳过：{rec['error']}")
        return
    rc, out, err, sec = run_joern(Q.replace("__CPG__", cpg), key)
    if rc == "timeout":
        rec = dict(key=key, project=proj, pin=pin, error="timeout", elapsed_sec=round(sec, 1))
        open(RESULTS, "a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False) + "\n")
        log(f"{key} 超时 {sec:.0f}s")
        return
    mstats, cstats = {}, {}
    for ln in (out or "").split("\n"):
        t = ln.split("\t")
        if t[0] == "@@F" and len(t) >= 5:
            mstats[t[1]] = dict(methods=int(t[2]) if t[2].isdigit() else 0,
                                max_end=int(t[3]) if t[3].isdigit() else 0,
                                globals=int(t[4]) if t[4].isdigit() else 0)
        elif t[0] == "@@C" and len(t) >= 4:
            cstats[t[1]] = dict(calls=int(t[2]) if t[2].isdigit() else 0,
                                max_line=int(t[3]) if t[3].isdigit() else 0)
    # 遍历 pin 源码里的每个源文件
    files = []
    for dp, _, fns in os.walk(src):
        if "/.git" in dp:
            continue
        for fn in fns:
            if not fn.endswith(SRC_EXT):
                continue
            full = os.path.join(dp, fn)
            rel = os.path.relpath(full, src)
            n = count_lines(full)
            if n <= 0:
                continue
            # CPG 里的 filename 可能是绝对路径或相对路径。
            # **必须避免歧义**：`valid.c` 与 `fuzz/valid.c` 都以 `valid.c` 结尾，
            # 直接取第一个会把 `valid.c` 的数字换成 `fuzz/valid.c` 的。
            # 规则：① 精确相等优先；② 否则取 `/rel` 后缀里**最长公共尾部**最长的那个。
            def pick(stats, rel):
                if rel in stats:
                    return stats[rel]
                cands = [(k, v) for k, v in stats.items() if k.endswith("/" + rel)]
                if not cands:
                    return None
                cands.sort(key=lambda kv: len(kv[0]))
                return cands[0][1]
            mm = pick(mstats, rel)
            cc = pick(cstats, rel)
            # 覆盖指标 = max(最后一行调用, 最后一个真实方法的末行)
            # 只用 call 行号会把「无调用的文件」（尤其 .h）一律判成 0% —— 那是指标缺陷
            max_call = (cc or {}).get("max_line", 0)
            max_meth = (mm or {}).get("max_end", 0)
            max_line = max(max_call, max_meth)
            ratio = (max_line / n) if n else None
            files.append(dict(rel=rel, lines=n, max_line=max_line, max_call=max_call,
                              max_meth=max_meth, is_header=fn.endswith((".h", ".hh", ".hpp")),
                              calls=(cc or {}).get("calls", 0),
                              methods=(mm or {}).get("methods", 0),
                              globals=(mm or {}).get("globals", 0),
                              ratio=round(ratio, 4) if ratio is not None else None,
                              verdict=classify(ratio)))
    # 头文件不计入 OK/BAD 统计（它们本来就可能没有函数体）
    body = [f for f in files if not f["is_header"]]
    n_ok = sum(1 for f in body if f["verdict"] == "OK")
    n_part = sum(1 for f in body if f["verdict"] == "PARTIAL")
    n_bad = sum(1 for f in body if f["verdict"] == "BAD")
    n_miss = sum(1 for f in body if f["verdict"] == "MISSING")
    rec = dict(key=key, project=proj, pin=pin, src=src, elapsed_sec=round(sec, 1),
               files=len(files), body_files=len(body), headers=len(files) - len(body),
               ok=n_ok, partial=n_part, bad=n_bad, missing=n_miss,
               ok_pct=round(100.0 * n_ok / len(body), 1) if body else None,
               globals_total=sum(f["globals"] for f in files),
               calls_total=sum(f["calls"] for f in files),
               worst=[f["rel"] for f in body if f["verdict"] in ("BAD", "MISSING")][:20])
    open(RESULTS, "a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False) + "\n")
    with open(COV_TSV, "a", encoding="utf-8") as fh:
        for f in files:
            fh.write("\t".join([key, f["rel"], str(f["lines"]), str(f["max_line"]),
                                str(f["max_call"]), str(f["max_meth"]),
                                str(f["calls"]), str(f["methods"]), str(f["globals"]),
                                str(f["ratio"]), f["verdict"],
                                "header" if f["is_header"] else "body"]) + "\n")
    log(f"{key}: {len(files)} 文件  ✅{n_ok} ⚠️{n_part} ❌{n_bad} 缺失{n_miss}  ({sec:.0f}s)")


def main():
    os.makedirs(OUT, exist_ok=True)
    d = done()
    log(f"续跑：已完成 {len(d)} 个 CPG；待测 {len(CPGS)}")
    for proj, pin, prefix in CPGS:
        if f"{proj}_{pin}" in d:
            continue
        measure(proj, pin, prefix)
    log("全部完成")


if __name__ == "__main__":
    main()
