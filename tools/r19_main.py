"""R19 主脚本：修掉 R17/R18 的全部已知测量缺陷。

## 修的四项

| # | 缺陷 | 修法 |
|---|---|---|
| 2.1 | `Q_FLOW` 只接受**一个** `file`，同时用于找释放点和找使用点 → 跨函数 UAF（释放与使用在不同文件）一律 `@@FREE_CALLS 0` | **`free_file` / `use_file` 分开传** |
| 2.2 | 取样时把 `facts.sites[kind=free].file` 和 `facts.crash.site.file` **混用** → 6 条正例里 2 条坐标错 | 分开取两个字段 |
| 2.3 | 单点判定没接进流程 | 每条样本**先**跑 `point(free)` / `point(use)`，两个都 `USABLE` 才进查询 |
| 2.4 | `results.jsonl` 的 `group` 被 `dict(s, overlay=True)` 搞丢 | **显式** `group` 字段 |

**回归要求**：`ARVO-42494732` 必须仍然连出流，且**第一条路径仍是**
`L12284:pair → L12267:pair → L12267:pair->code`。
"""
import json
import os
import signal
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "runs", "r19")
JL = "/usr/local/lib/python3.10/dist-packages/pyjoern/bin/joern-cli"
JOERN = os.path.join(JL, "joern")
CPGDIR = os.path.join(ROOT, "cpg_files")
RESULTS = os.path.join(OUT, "results.jsonl")
TMO = 900

# ── 修好的查询：free_file / use_file 分开 ─────────────────────────────
Q_FLOW2 = r'''
importCpg("__CPG__")
import io.joern.dataflowengineoss.language._
import io.joern.dataflowengineoss.layers.dataflows.{OssDataFlow, OssDataFlowOptions}
import io.shiftleft.semanticcpg.layers.LayerCreatorContext
new OssDataFlow(new OssDataFlowOptions()).run(new LayerCreatorContext(cpg))

val freeFile = "__FREEFILE__"
val useFile  = "__USEFILE__"
val freeLine = __FREELINE__
val useLine  = __USELINE__
val freeFn   = "__FREEFN__"
val useFn    = "__USEFN__"

// ① 释放语句那一行的调用（在 freeFile 里找）
val fc = cpg.call.filter(c => c.file.name.headOption.exists(_.endsWith(freeFile)) &&
                             c.lineNumber.contains(freeLine)).l
println(s"@@FREE_CALLS\t${fc.size}\t${fc.take(3).map(c => c.name).mkString(",")}")

// ② 源：S2 = use_fn 里对释放包装的调用的实参（R17 的关键发现：调用方实参，不是形参）
val s2 = cpg.call.filter(c => c.method.name == useFn && c.name == freeFn).argument.l
val s1 = fc.flatMap(_.argument).l
println(s"@@SRC\tS1=${s1.size}\tS2=${s2.size}")
val src = if (s2.nonEmpty) s2 else s1

// ③ 汇：useFile 里 useLine 那一行的 call / identifier
val sinks = (cpg.call.filter(c => c.file.name.headOption.exists(_.endsWith(useFile)) && c.lineNumber.contains(useLine)) ++
             cpg.identifier.filter(c => c.file.name.headOption.exists(_.endsWith(useFile)) && c.lineNumber.contains(useLine))).l
println(s"@@SINK\t${sinks.size}")
val flows = sinks.reachableByFlows(src).l
println(s"@@FLOWS\t${flows.size}")
flows.foreach { f =>
  println(s"@@FLOW\t${f.elements.l.map(e => s"L${e.lineNumber.getOrElse(0)}:${e.code.take(48)}").mkString(" => ")}")
}
'''

Q_POINT = r'''
importCpg("__CPG__")
val f = "__FILE__"
val ln = __LINE__
val calls = cpg.call.filter(c => c.file.name.headOption.exists(_.endsWith(f)) && c.lineNumber.contains(ln)).l
val ids   = cpg.identifier.filter(c => c.file.name.headOption.exists(_.endsWith(f)) && c.lineNumber.contains(ln)).l
val real  = cpg.method.filter(m => m.file.name.headOption.exists(_.endsWith(f)) &&
                    m.name != "<global>" && m.lineNumber.exists(_ <= ln) && m.lineNumberEnd.exists(_ >= ln)).l
println(s"@@CALLS\t${calls.size}")
println(s"@@IDS\t${ids.size}")
println(s"@@REAL\t${real.size}\t${real.take(3).map(_.name).mkString(",")}")
println(s"@@VERDICT\t${if (real.nonEmpty && (calls.nonEmpty || ids.nonEmpty)) "USABLE" else if (real.isEmpty) "NO_REAL_METHOD" else "NO_NODE"}")
'''


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def run(sc, tag, timeout=TMO):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, f"_q_{tag}.scala")
    open(p, "w", encoding="utf-8").write(sc)
    t0 = time.time()
    pr = subprocess.Popen([JOERN, "--script", p], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, errors="replace",
                          start_new_session=True, stdin=subprocess.DEVNULL)
    try:
        o, e = pr.communicate(timeout=timeout)
        return pr.returncode, o, e, time.time() - t0
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(pr.pid), signal.SIGKILL)
        except Exception:
            pass
        return "timeout", "", "", time.time() - t0


def g(out, k):
    for ln in (out or "").split("\n"):
        if ln.startswith(k + "\t"):
            return ln.split("\t")[1:]
    return None


def point(cpg, f, ln):
    """单点判定（缺陷 2.3）。"""
    sc = (Q_POINT.replace("__CPG__", cpg).replace("__FILE__", f).replace("__LINE__", str(ln)))
    rc, o, e, sec = run(sc, f"pt_{os.path.basename(cpg)[:-4]}_{os.path.basename(f)}_{ln}", timeout=300)
    return dict(verdict=(g(o, "@@VERDICT") or ["?"])[0],
                calls=g(o, "@@CALLS"), ids=g(o, "@@IDS"),
                real=g(o, "@@REAL"), sec=round(sec, 1))


def flow(s):
    """缺陷 2.1：free_file / use_file 分开。"""
    cpg = os.path.join(CPGDIR, s["cpg"] + ".cpg")
    sc = (Q_FLOW2.replace("__CPG__", cpg)
          .replace("__FREEFILE__", s["free_file"]).replace("__USEFILE__", s["use_file"])
          .replace("__FREELINE__", str(s["free_line"])).replace("__USELINE__", str(s["use_line"]))
          .replace("__FREEFN__", s.get("free_fn") or "").replace("__USEFN__", s.get("use_fn") or ""))
    rc, o, e, sec = run(sc, f"fl_{s['osv']}")
    return dict(rc=rc, free_calls=g(o, "@@FREE_CALLS"), src=g(o, "@@SRC"),
                sink=g(o, "@@SINK"), flows=(g(o, "@@FLOWS") or ["0"])[0],
                paths=[x for x in (o or "").split("\n") if x.startswith("@@FLOW\t")],
                elapsed_sec=round(sec, 1))


# 回归样本（必须复现 R17 的第一条路径）
REGRESSION = dict(osv="ARVO-42494732", project="libredwg", group="regression",
                  cpg="libredwg_ff69eeda6658",
                  free_file="src/in_dxf.c", free_line=515,
                  use_file="src/in_dxf.c", use_line=12267,
                  free_fn="dxf_free_pair", use_fn="dxf_objects_read")


def main():
    os.makedirs(OUT, exist_ok=True)
    s = REGRESSION
    log(f"── 回归 {s['osv']}")
    pf = point(os.path.join(CPGDIR, s["cpg"] + ".cpg"), s["free_file"], s["free_line"])
    pu = point(os.path.join(CPGDIR, s["cpg"] + ".cpg"), s["use_file"], s["use_line"])
    log(f"   point(free)={pf['verdict']}  point(use)={pu['verdict']}")
    rec = dict(**s, key=f"{s['group']}|{s['osv']}", point_free=pf, point_use=pu)
    rec["group"] = s["group"]          # 缺陷 2.4：显式带 group，不靠 dict 合并
    if pf["verdict"] != "USABLE" or pu["verdict"] != "USABLE":
        rec["skipped"] = "单点判定不合格"
    else:
        rec.update(flow(s))
    # 回归判据：流的**顺序不稳定**（实测两次都是 67 条但首条不同），
    # 所以要判"**是否存在** 源 L12284 → 汇 L12267:pair->code 的那一条"，不是判第一条
    rec["has_expected_path"] = any(("L12284" in x and "L12267" in x and "pair->code" in x)
                                   for x in (rec.get("paths") or []))
    rec["n_paths"] = len(rec.get("paths") or [])
    open(RESULTS, "a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False) + "\n")
    log(f"   flows={rec.get('flows')}  {rec.get('elapsed_sec')}s")
    log(f"   paths={rec.get('n_paths')}  含期望路径={rec.get('has_expected_path')}")
    for p in (rec.get("paths") or [])[:3]:
        log(f"   {p[:130]}")
    log("完成")


if __name__ == "__main__":
    main()
