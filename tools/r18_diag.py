"""R18：单点判定 + 数据流断点阶梯定位。

## 两件事

### ① 单点判定 `point(fp, line)`
给定 (文件, 行号)，回答 CPG 里**有没有节点**、**在不在真实方法里**。
每次数据流查询前先跑它 —— 比量整体覆盖率有用（libredwg 11.4% 覆盖却连出 67 条流，
tree.c 100% 却 0 条 —— 整体指标没有预测力）。

### ② 断点阶梯 `ladder(sample)`
对一条样本，逐级放大汇的范围，定位断在哪：
- **L0** 汇 = `use_fn` 里指定行的节点（**按函数名定位，不按文件+行** —— R18 发现
  `facts` 的 `use_line` 和 `free_file` 会被误配成同一文件，实测 `xmlXIncludeIncludeNode`
  在 `xinclude.c:2208` 而样本写的是 `tree.c`）
- **L1** 汇 = `use_fn` 里**任意**标识符/调用 → 能连就说明"跨函数这一跳通，只是行号定错了"
- **L2** 汇 = `free_fn` 里**任意**标识符 → 能连就说明"源本身没问题，断在跨函数那跳"
- **L3** 汇 = `free_fn` 里释放点**之后**的标识符 → 同函数内的最小验证

用法（单条）：
    python3 tools/r18_diag.py --osv ARVO-42494732
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "runs", "r18")
JL = "/usr/local/lib/python3.10/dist-packages/pyjoern/bin/joern-cli"
JOERN = os.path.join(JL, "joern")
CPGDIR = os.path.join(ROOT, "cpg_files")

Q_POINT = r'''
importCpg("__CPG__")
val f = "__FILE__"
val ln = __LINE__
val calls = cpg.call.filter(c => c.file.name.headOption.exists(_.endsWith(f)) && c.lineNumber.contains(ln)).l
val ids   = cpg.identifier.filter(c => c.file.name.headOption.exists(_.endsWith(f)) && c.lineNumber.contains(ln)).l
val ms    = cpg.method.filter(m => m.file.name.headOption.exists(_.endsWith(f)) &&
                                    m.lineNumber.exists(_ <= ln) && m.lineNumberEnd.exists(_ >= ln)).l
val real  = ms.filter(_.name != "<global>")
println(s"@@POINT\t$f\t$ln")
println(s"@@CALLS\t${calls.size}\t${calls.take(4).map(_.name).mkString(",")}")
println(s"@@IDS\t${ids.size}\t${ids.take(4).map(_.name).mkString(",")}")
println(s"@@METHODS\t${ms.size}\t${ms.take(4).map(_.name).mkString(",")}")
println(s"@@REAL_METHODS\t${real.size}\t${real.take(4).map(_.name).mkString(",")}")
println(s"@@VERDICT\t${if (real.nonEmpty && (calls.nonEmpty || ids.nonEmpty)) "USABLE" else if (real.isEmpty) "NO_REAL_METHOD" else "NO_NODE"}")
'''

Q_LADDER = r'''
importCpg("__CPG__")
import io.joern.dataflowengineoss.language._
import io.joern.dataflowengineoss.layers.dataflows.{OssDataFlow, OssDataFlowOptions}
import io.shiftleft.semanticcpg.layers.LayerCreatorContext
new OssDataFlow(new OssDataFlowOptions()).run(new LayerCreatorContext(cpg))
val freeFn = "__FREEFN__"
val useFn  = "__USEFN__"
val freeFile = "__FREEFILE__"
val freeLine = __FREELINE__
val useLine  = __USELINE__

// 释放语句那行的调用（用来拿"被调函数里的形参"作源）
val fc = cpg.call.filter(c => c.file.name.headOption.exists(_.endsWith(freeFile)) &&
                             c.lineNumber.contains(freeLine)).l
println(s"@@FREE_CALLS\t${fc.size}\t${fc.take(3).map(c => c.name + "(" + c.argument.code.l.mkString("|") + ")").mkString(";")}")

// 源：S2 = use_fn 里对释放包装的调用的实参（跨函数形态里真正悬空的）
val s2 = cpg.call.filter(c => c.name == freeFn && c.method.name == useFn).argument.l
val s1 = fc.flatMap(_.argument).l
println(s"@@SRC\tS1=${s1.size}\tS2=${s2.size}")
val src = if (s2.nonEmpty) s2 else s1
println(s"@@SRC_USED\t${if (s2.nonEmpty) "S2_callerside" else "S1_callee_param"}")

def atLine(fn: String, ln: Int) = {
  val tmp = cpg.call.filter(c => c.method.name == fn && c.lineNumber.contains(ln)).l ++
            cpg.identifier.filter(c => c.method.name == fn && c.lineNumber.contains(ln)).l
  tmp
}
def anyIn(fn: String) = cpg.identifier.filter(c => c.method.name == fn).l ++
                        cpg.call.filter(c => c.method.name == fn).l

val useMs = cpg.method.name(useFn).filter(_.name != "<global>").l
println(s"@@USE_METHODS\t${useMs.size}\t${useMs.take(3).map(m => m.file.name.headOption.getOrElse("?") + ":L" + m.lineNumber.getOrElse(0)).mkString(";")}")
val freeMs = cpg.method.name(freeFn).filter(_.name != "<global>").l
println(s"@@FREE_METHODS\t${freeMs.size}\t${freeMs.take(3).map(m => m.file.name.headOption.getOrElse("?") + ":L" + m.lineNumber.getOrElse(0)).mkString(";")}")

// ── 阶梯 ──
val l0 = atLine(useFn, useLine)
println(s"@@SINK_L0\t${l0.size}")
println(s"@@FLOWS_L0\t${l0.reachableByFlows(src).l.size}")
val l1 = anyIn(useFn)
println(s"@@SINK_L1\t${l1.size}")
println(s"@@FLOWS_L1\t${l1.reachableByFlows(src).l.size}")
// L2/L3 砍掉：`free_fn` 里的汇有几千个，在 40 万调用的图上跑 reachableByFlows 会超时。
// L0 vs L1 已经能区分"行号定错"和"跨函数这跳断"这两件事。
'''

# 三条要对比的样本（R17 的正例 + 两条"失败"）
SAMPLES = [
    dict(osv="ARVO-42494732", cpg="libredwg_ff69eeda6658",
         free_fn="dxf_free_pair", free_file="src/in_dxf.c", free_line=515,
         use_fn="dxf_objects_read", use_line=12267, tag="OK_连上了67条"),
    dict(osv="ARVO-42486565", cpg="libxml2_9de7b94d4ffb",
         free_fn="xmlFreeNode", free_file="tree.c", free_line=3819,
         use_fn="xmlXIncludeIncludeNode", use_line=2216, tag="FAIL_tree.c100%"),
    dict(osv="ARVO-42491546", cpg="igraph_883bd139af37",
         free_fn="igraph_gml_tree_destroy", free_file="src/io/gml.c", free_line=189,
         use_fn="igraph_vector_ptr_size", use_line=264, tag="FAIL_gml.c99.8%"),
]


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def run(sc, tag, timeout=900):
    p = os.path.join(OUT, f"_d_{tag}.scala")
    open(p, "w", encoding="utf-8").write(sc)
    t0 = time.time()
    pr = subprocess.Popen([JOERN, "--script", p], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, errors="replace",
                          start_new_session=True, stdin=subprocess.DEVNULL)
    try:
        out, err = pr.communicate(timeout=timeout)
        return out, err, time.time() - t0
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(pr.pid), signal.SIGKILL)
        except Exception:
            pass
        return "", "TIMEOUT", time.time() - t0


def parse(out, prefix):
    for ln in (out or "").split("\n"):
        if ln.startswith(prefix + "\t"):
            return ln.split("\t")[1:]
    return None


def point(cpg, f, ln):
    sc = (Q_POINT.replace("__CPG__", os.path.join(CPGDIR, cpg + ".cpg"))
          .replace("__FILE__", f).replace("__LINE__", str(ln)))
    out, err, sec = run(sc, f"point_{cpg}_{os.path.basename(f)}_{ln}", timeout=300)
    return dict(calls=parse(out, "@@CALLS"), ids=parse(out, "@@IDS"),
                methods=parse(out, "@@METHODS"), real=parse(out, "@@REAL_METHODS"),
                verdict=(parse(out, "@@VERDICT") or ["?"])[0], sec=round(sec, 1))


def ladder(s):
    sc = (Q_LADDER.replace("__CPG__", os.path.join(CPGDIR, s["cpg"] + ".cpg"))
          .replace("__FREE_FN__", "").replace("__FREEFN__", s["free_fn"])
          .replace("__USEFN__", s["use_fn"]).replace("__FREEFILE__", s["free_file"])
          .replace("__FREELINE__", str(s["free_line"]))
          .replace("__USELINE__", str(s["use_line"])))
    out, err, sec = run(sc, f"ladder_{s['osv']}")
    keys = ["@@FREE_CALLS", "@@SRC", "@@SRC_USED", "@@USE_METHODS", "@@FREE_METHODS",
            "@@SINK_L0", "@@FLOWS_L0", "@@SINK_L1", "@@FLOWS_L1"]
    d = {k.lstrip("@"): parse(out, k) for k in keys}
    d["osv"] = s["osv"]; d["tag"] = s["tag"]; d["elapsed_sec"] = round(sec, 1)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--osv", default=None)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    sel = [s for s in SAMPLES if not a.osv or s["osv"] == a.osv]
    res = []
    for s in sel:
        log(f"── {s['osv']} ({s['tag']})")
        # ① 单点判定：释放点 / 使用点
        p_free = point(s["cpg"], s["free_file"], s["free_line"])
        log(f"   point(释放) {s['free_file']}:{s['free_line']}  verdict={p_free['verdict']} "
            f"call={p_free['calls']} real_methods={p_free['real']}")
        p_use = point(s["cpg"], s["free_file"], s["use_line"])
        log(f"   point(使用-按样本文件) {s['free_file']}:{s['use_line']}  verdict={p_use['verdict']}")
        # ② 阶梯
        L = ladder(s)
        log(f"   ladder SRC={L.get('@@SRC')} used={L.get('@@SRC_USED')} "
            f"SINK_L0={L.get('@@SINK_L0')} FLOWS_L0={L.get('@@FLOWS_L0')} "
            f"SINK_L1={L.get('@@SINK_L1')} FLOWS_L1={L.get('@@FLOWS_L1')}  {L['elapsed_sec']}s")
        res.append(dict(sample=s, point_free=p_free, point_use_sample_file=p_use, ladder=L))
    dst = os.path.join(OUT, "diag.json")
    json.dump(res, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log(f"写出 {dst}")


if __name__ == "__main__":
    main()
