"""R17：测 Joern 的 CPG 能不能支撑两个探测器。

    A) 跨过程数据流（llm04 / llm03 依赖）：从释放点的实参 → 使用点，能不能连上
    B) 结构匹配（llm05 依赖）：循环体里 `p = p->next` 这种沿链遍历，CPG 能不能查出来

**只读**：不改 pipeline/，不改 projects/*/v2/ 下任何产物。
结果增量写 docs/runs/r17/results.jsonl（一行一条），可续跑。

用法（后台）：
    nohup python3 tools/r17_cpg_probe.py > docs/runs/r17/run.log 2>&1 &
    echo $! > docs/runs/r17/run.pid
"""
import json
import os
import signal
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "runs", "r17")
RESULTS = os.path.join(OUT, "results.jsonl")
JL = "/usr/local/lib/python3.10/dist-packages/pyjoern/bin/joern-cli"
JOERN = os.path.join(JL, "joern")
CPGDIR = os.path.join(ROOT, "cpg_files")
SRCDIR = "/tmp/opencode/cpg_cache/src"
PER_ITEM_TIMEOUT = 900          # 15 分钟

# ── 样本（见 docs/runs/R17_REPORT.md 步骤 1）─────────────────────────────
# 组 1：llm04 正例（测跨过程数据流）。R17 调整后 6 条（原第 6 条 leptonica 移到负例组）
G1 = [
    dict(osv="ARVO-42484562", free_fn="xmlTextReaderFreeProp", use_fn="__xmlRaiseError", proj="libxml2", pin="00ed736eecf9", file="xmlreader.c",
         free_line=311, free_var="cur->name", use_line=501, note="F1 字段"),
    dict(osv="ARVO-372547409", free_fn="xmlFreeAttribute", use_fn="xmlValidateOneElement", proj="libxml2", pin="d4d1f3f33d6d", file="valid.c",
         free_line=1625, free_var="attr", use_line=5992, note="F4 裸指针"),
    dict(osv="ARVO-42486565", free_fn="xmlFreeNode", use_fn="xmlXIncludeIncludeNode", proj="libxml2", pin="9de7b94d4ffb", file="tree.c",
         free_line=3819, free_var="cur", use_line=2216, note="F4 裸指针"),
    dict(osv="ARVO-42531532", free_fn="xmlFreeID", use_fn="xmlRemoveID", proj="libxml2", pin="e45a4d711500", file="valid.c",
         free_line=2503, free_var="id", use_line=2745, note="F4 裸指针"),
    dict(osv="ARVO-42494732", free_fn="dxf_free_pair", use_fn="dxf_objects_read", proj="libredwg", pin="ff69eeda6658", file="src/in_dxf.c",
         free_line=515, free_var="pair", use_line=12267, note="F4 裸指针（对照基准）"),
    dict(osv="ARVO-42491546", free_fn="igraph_gml_tree_destroy", use_fn="igraph_vector_ptr_size", proj="igraph", pin="883bd139af37", file="src/io/gml.c",
         free_line=189, free_var="t", use_line=264, note="F4 裸指针"),
]

# 组 2：llm05 正例（测结构匹配，与数据流无关）
G2 = [
    dict(osv="ARVO-42487785", proj="libxml2", pin="f0fd1b67fc88",
         file="xmlreader.c", func="xmlTextReaderFreeNodeList", note="沿 next 链释放"),
    dict(osv="ARVO-42486565", proj="libxml2", pin="9de7b94d4ffb",
         file="tree.c", func="xmlFreeNode", note="沿 children/next 递归释放"),
    dict(osv="ARVO-42491511", proj="igraph", pin="c83b6ecdc3fe",
         file="src/io/gml.c", func="igraph_i_gml_destroy_attrs", note="沿 finally_stack 遍历销毁"),
]

# 组 3：负例（R17 调整后 5 条）。**连不上是好结果**
G3 = [
    dict(osv="ARVO-42494732", proj="libredwg", pin="ff69eeda6658", file="src/encode.c",
         free_line=1308, free_var="obj", use_line=1313, note="不释放该对象（只释放类型私有数据）"),
    dict(osv="ARVO-42494732", proj="libredwg", pin="ff69eeda6658", file="src/in_dxf.c",
         free_line=12851, free_var="header_hdls", use_line=12847,
         note="顺序相反：resolve 在 12847，free 在 12851"),
    dict(osv="ARVO-42494732", proj="libredwg", pin="ff69eeda6658", file="src/in_dxf.c",
         free_line=12851, free_var="header_hdls", use_line=12848,
         note="顺序相反（同上，换 object_refs）"),
    dict(osv="ARVO-42488833", proj="leptonica", pin="8d7717457caf", file="src/pix1.c",
         free_line=653, free_var="pix", use_line=1313,
         note="顺序相反（R11 的 B 类：pixChangeRefcount 先于 LEPT_FREE）"),
    dict(osv="ARVO-42488049", proj="leptonica", pin="90ec70fd4322", file="src/pix1.c",
         free_line=653, free_var="pix", use_line=1313,
         note="顺序相反（同上，另一条 OSV）"),
]


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def done_keys():
    keys = set()
    if os.path.isfile(RESULTS):
        for ln in open(RESULTS, encoding="utf-8"):
            ln = ln.strip()
            if not ln:
                continue
            try:
                d = json.loads(ln)
                keys.add(d["key"])
            except Exception:
                pass
    return keys


def record(d):
    with open(RESULTS, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(d, ensure_ascii=False) + "\n")


def find_cpg(proj, pin):
    p = os.path.join(CPGDIR, f"{proj}_{pin}.cpg")
    return p if os.path.isfile(p) else None


def ensure_src(proj, pin):
    """按 pin 提取源码（限制 17：源码必须是 pin，不是 HEAD）。返回目录或 None。"""
    cands = [d for d in os.listdir(SRCDIR) if d.endswith("_" + pin[:12])] if os.path.isdir(SRCDIR) else []
    if cands:
        return os.path.join(SRCDIR, cands[0])
    # 找克隆
    clones = [d for d in os.listdir("/tmp/opencode/src_local")] if os.path.isdir("/tmp/opencode/src_local") else []
    want = proj.lower()
    pick = next((c for c in clones if want in c.lower()), None)
    if not pick:
        return None
    repo = os.path.join("/tmp/opencode/src_local", pick)
    d = os.path.join(SRCDIR, f"{os.path.basename(repo)}_{pin[:12]}")
    os.makedirs(d, exist_ok=True)
    p1 = subprocess.Popen(["git", "-C", repo, "archive", pin], stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL)
    p2 = subprocess.run(["tar", "-x", "-C", d], stdin=p1.stdout, capture_output=True)
    p1.wait()
    return d if p1.returncode == 0 and p2.returncode == 0 else None


def run_joern(scala_src, tag):
    """跑 Joern，单条 15 分钟超时，超时 killpg 杀干净。返回 (rc, stdout, stderr, sec)。"""
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


# ── 能力 A：跨过程数据流 ────────────────────────────────────────────────
Q_FLOW = r'''
importCpg("__CPG__")
import io.joern.dataflowengineoss.language._
// R17 实测：**不施加 OSS dataflow overlay 时，reachableByFlows 只连同函数内的流**
// （6 条正例里只有 1 条同函数的连上；5 条跨函数的全 0）。施加后跨函数能连上（实测 804 条）。
// overlay 只作用在内存图上，不写回 cpg_files/。
import io.joern.dataflowengineoss.layers.dataflows.{OssDataFlow, OssDataFlowOptions}
import io.shiftleft.semanticcpg.layers.LayerCreatorContext
if (__OVERLAY__) {
  val _t0 = System.currentTimeMillis()
  new OssDataFlow(new OssDataFlowOptions()).run(new LayerCreatorContext(cpg))
  println(s"@@OVERLAY_SEC\t${(System.currentTimeMillis() - _t0) / 1000}")
}
val file = "__FILE__"
val freeLine = __FREE_LINE__
val useLine = __USE_LINE__
val varName = "__VAR__"

// 释放点的那个调用（同文件同行）
val freeCalls = cpg.call.filter(c => c.file.name.headOption.exists(_.endsWith(file)) &&
                                    c.lineNumber.contains(freeLine)).l
println(s"@@FREE_CALLS\t${freeCalls.size}")
freeCalls.foreach { c =>
  println(s"@@FREE_CALL\t${c.name}\tL${c.lineNumber.getOrElse(0)}\t${c.argument.code.l.mkString(" | ")}")
}

// 使用点的方法（同文件、行号落在方法内）
val useMeth = cpg.method.filter(m => m.file.name.headOption.exists(_.endsWith(file)) &&
                                     m.lineNumber.exists(a => a <= useLine) &&
                                     m.lineNumberEnd.exists(b => b >= useLine)).l
println(s"@@USE_METHODS\t${useMeth.size}")
useMeth.foreach(m => println(s"@@USE_METHOD\t${m.name}\tL${m.lineNumber.getOrElse(0)}-${m.lineNumberEnd.getOrElse(0)}"))

// 数据流：源 = 释放调用的实参；汇 = 使用点那一行的 call / identifier / literal
// （`ast.isCall` 在这个 Joern 版本返回 Expression，没有 reachableByFlows，必须用 cpg.call）
// 源有两个变体（这是本轮的一个重要区分）：
//  S1 = 释放语句所在的调用实参（对包装函数来说，这是**形参**）
//  S2 = **调用方**把变量传给释放包装的那个调用点的实参（真正悬空的是它）
// 跨函数形态里 S1 与 S2 是**不同函数的两个不同变量**，只测 S1 会系统性低估。
val wrapperCallers = cpg.call.filter(c => c.name == "__FREEFN__" &&
    c.method.name != "<global>").l
println(s"@@WRAPPER_CALLERS\t${wrapperCallers.size}")
wrapperCallers.take(8).foreach { c =>
  println(s"@@WCALL\t${c.method.name}\tL${c.lineNumber.getOrElse(0)}\t${c.argument.code.l.mkString(" | ")}")
}
val useFn = "__USEFN__"
// S2（主）：**use_fn 内部**把变量传给释放包装的那个调用点的实参
val srcs2 = cpg.call.filter(c => c.name == "__FREEFN__" && c.method.name == useFn)
                        .argument.l
// S1（备）：释放语句那行的调用实参
val srcs1 = freeCalls.flatMap(c => c.argument).l
println(s"@@SRC1\t${srcs1.size}\t@@SRC2\t${srcs2.size}")
val sinks = (cpg.call.filter(c => c.file.name.headOption.exists(_.endsWith(file)) && c.lineNumber.contains(useLine)) ++
             cpg.identifier.filter(c => c.file.name.headOption.exists(_.endsWith(file)) && c.lineNumber.contains(useLine)) ++
             cpg.literal.filter(c => c.file.name.headOption.exists(_.endsWith(file)) && c.lineNumber.contains(useLine))).l
println(s"@@SRC_NODES\t${srcs1.size + srcs2.size}\t@@SINK_NODES\t${sinks.size}")

val flows = (if (srcs2.nonEmpty) sinks.reachableByFlows(srcs2).l
             else sinks.reachableByFlows(srcs1).l)
println(s"@@FLOWS\t${flows.size}")
flows.take(5).foreach { f =>
  val hops = f.elements.l.map(e => s"${e.file.name.headOption.getOrElse("?")}:L${e.lineNumber.getOrElse(0)}:${e.code.take(60)}")
  println(s"@@FLOW\t${hops.mkString(" => ")}")
}
'''

# ── 能力 B：结构匹配（链式遍历循环）────────────────────────────────────
Q_LOOP = r'''
importCpg("__CPG__")
val file = "__FILE__"
val fn = "__FUNC__"

// 目标函数
val ms = cpg.method.name(fn).filter(m => m.file.name.headOption.exists(_.endsWith(file))).l
println(s"@@TARGET_METHODS\t${ms.size}")

// 该项目里所有"循环体内把链式字段赋回自身变量"的地方
// 形状： `x = x->next` / `x = x->prev` / `x = x->child` / `x = x->sibling`
val chainFields = List("next", "prev", "child", "sibling", "nxt", "succ", "link", "header")
// 去掉 ^ 锚定：`cs.code` 以 `while (...)` 开头，链式赋值在**体内**
val assignRx = """(\w+)\s*=\s*(\w+)\s*->\s*(\w+)""".r

val loops = cpg.method.l.flatMap { m =>
  m.ast.isControlStructure.controlStructureType("WHILE|FOR|DO").l.map(cs => (m, cs))
}

var total = 0
var chainLoops = 0
loops.foreach { case (m, cs) =>
  total += 1
  val code = cs.code
  val hit = assignRx.findAllMatchIn(code).exists { mm =>
    mm.group(1) == mm.group(2) && chainFields.contains(mm.group(3))
  }
  if (hit) {
    chainLoops += 1
    val inTarget = ms.exists(_.name == m.name) &&
                   ms.exists(_.lineNumber == m.lineNumber)
    if (inTarget) {
      println(s"@@TARGET_LOOP\t${m.name}\tL${cs.lineNumber.getOrElse(0)}\t${cs.code.take(80)}")
    }
  }
}
println(s"@@PROJECT_LOOPS\t${total}\t@@CHAIN_LOOPS\t${chainLoops}")
'''


def probe_flow(s):
    ov = s.get("overlay")
    key = f"{'A2' if ov else 'A'}|{s['osv']}|{s['file']}:{s['free_line']}->{s['use_line']}"
    if key in DONE:
        return
    cpg = find_cpg(s["proj"], s["pin"])
    src = ensure_src(s["proj"], s["pin"]) if cpg else None
    base = dict(key=key, capability=("A2_dataflow_overlay" if ov else "A_dataflow"),
                osv=s["osv"], project=s["proj"],
                pin=s["pin"], commit_used=s["pin"], file=s["file"],
                free_line=s["free_line"], use_line=s["use_line"],
                free_var=s.get("free_var"), note=s.get("note"),
                cpg=os.path.basename(cpg) if cpg else None,
                src_dir=src, group=("G3_negative" if s in G3 else "G1_positive"))
    if not cpg or not src:
        record(dict(base, connected="error", error="cpg/source 缺失", elapsed_sec=0))
        log(f"{s['osv']} 跳过：cpg={bool(cpg)} src={bool(src)}")
        return
    q = (Q_FLOW.replace("__CPG__", cpg).replace("__FILE__", s["file"])
         .replace("__FREE_LINE__", str(s["free_line"]))
         .replace("__USE_LINE__", str(s["use_line"]))
         .replace("__FREEFN__", s.get("free_fn") or "")
         .replace("__USEFN__", s.get("use_fn") or "")
         .replace("__OVERLAY__", "true" if s.get("overlay") else "false")
         .replace("__VAR__", s.get("free_var") or ""))
    rc, out, err, sec = run_joern(q, f"A_{s['osv']}_{s['free_line']}")
    if rc == "timeout":
        record(dict(base, connected="timeout", elapsed_sec=round(sec, 1), query=q))
        log(f"{s['osv']} A 超时 {sec:.0f}s")
        return
    lines = [l for l in (out or "").split("\n") if l.startswith("@@")]
    broken = (out or "").count("Could not create edge")
    n_flows = next((int(l.split("\t")[1]) for l in lines if l.startswith("@@FLOWS")), 0)
    paths = [l.split("\t", 1)[1] for l in lines if l.startswith("@@FLOW\t")]
    record(dict(base, connected=bool(n_flows), flows=n_flows, path=paths,
                path_len=(len(paths[0].split(" => ")) if paths else 0),
                broken_ref_edges=broken,
                elapsed_sec=round(sec, 1), query=q,
                raw_output_head=(out or "").split("\n")[:25],
                stderr_head=(err or "").split("\n")[:5]))
    log(f"{s['osv']} A: flows={n_flows} {sec:.0f}s")


def probe_loop(s):
    key = f"B|{s['osv']}|{s['func']}"
    if key in DONE:
        return
    cpg = find_cpg(s["proj"], s["pin"])
    src = ensure_src(s["proj"], s["pin"]) if cpg else None
    base = dict(key=key, capability="B_structure", osv=s["osv"], project=s["proj"],
                pin=s["pin"], commit_used=s["pin"], file=s["file"], func=s["func"],
                note=s.get("note"), cpg=os.path.basename(cpg) if cpg else None,
                src_dir=src, group="G2_positive")
    if not cpg or not src:
        record(dict(base, loop_found="error", error="cpg/source 缺失", elapsed_sec=0))
        log(f"{s['osv']} B 跳过")
        return
    q = (Q_LOOP.replace("__CPG__", cpg).replace("__FILE__", s["file"])
         .replace("__FUNC__", s["func"]))
    rc, out, err, sec = run_joern(q, f"B_{s['osv']}_{s['func'][:16]}")
    if rc == "timeout":
        record(dict(base, loop_found="timeout", elapsed_sec=round(sec, 1), query=q))
        log(f"{s['osv']} B 超时 {sec:.0f}s")
        return
    lines = [l for l in (out or "").split("\n") if l.startswith("@@")]
    tl = [l.split("\t")[1:] for l in lines if l.startswith("@@TARGET_LOOP")]
    proj = next((l.split("\t")[1:] for l in lines if l.startswith("@@PROJECT_LOOPS")), None)
    record(dict(base, loop_found=bool(tl), loop_detail=tl,
                project_total=(int(proj[1]) if proj and len(proj) > 1 and proj[1].isdigit() else None),
                project_chain_loops=(int(proj[3]) if proj and len(proj) > 3 and proj[3].isdigit() else None),
                elapsed_sec=round(sec, 1), query=q,
                raw_output_head=(out or "").split("\n")[:25],
                stderr_head=(err or "").split("\n")[:5]))
    log(f"{s['osv']} B: loops={bool(tl)} 项目内链式循环={proj} {sec:.0f}s")


def main():
    os.makedirs(OUT, exist_ok=True)
    global DONE
    DONE = done_keys()
    log(f"续跑：已完成 {len(DONE)} 条；待测 A={len(G1)+len(G3)} B={len(G2)}")
    # 第一遍：不施加 overlay（already measured）；第二遍：施加 overlay（A2）
    import sys as _sys
    if "--only-b" not in _sys.argv:
        for s in G1 + G3:
            probe_flow(dict(s, overlay=True))
    for s in G2:
        probe_loop(s)
    log(f"全部完成。结果 {RESULTS}")


if __name__ == "__main__":
    main()
