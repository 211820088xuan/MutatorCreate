"""R20 步骤 1：量清 CPG 的 REF 边断裂规模。

## 为什么

R17 加载 `libxml2_d4d1f3f33d6d.cpg` 时 Joern 打出：

    [INFO] Could not create edge. Destination lookup failed.
           edgeType=REF, srcNodeType=CALL, dstNodeType=MEMBER, dstFullName=xmlSAXHandler*.serror

**10,180 条**。R18/R19 把它写成了"字段级数据流做不了"的原因，但**没量过分母**。

## 要量的

| 指标 | 怎么量 |
|---|---|
| MEMBER 节点数 | 图里有多少结构体成员节点 |
| CALL→MEMBER 的 REF 边（**成功建立**） | `cpg.call.out("REF")` 里目标是 MEMBER 的 |
| 断掉的条数 | Joern **加载时**打印的 `Could not create edge ... dstNodeType=MEMBER` 行数 |
| 断边占"所有 CALL→MEMBER 引用"的比例 | 断 /（断 + 成功） |

**关键**：断边**不在图里**（创建失败），所以只能从**加载日志**数。
为了让它每次都真的重新加载，先删 `workspace/<cpg>/` 这个工作副本。

用法：
    mkdir -p docs/runs/r20
    setsid nohup python3 tools/r20_refedge.py > docs/runs/r20/run.log 2>&1 < /dev/null &
"""
import json
import os
import shutil
import signal
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "runs", "r20")
RESULTS = os.path.join(OUT, "results.jsonl")
CPGDIR = os.path.join(ROOT, "cpg_files")
WS = os.path.join(ROOT, "workspace")
JL = "/usr/local/lib/python3.10/dist-packages/pyjoern/bin/joern-cli"
JOERN = os.path.join(JL, "joern")
TMO = 900

CPGS = [
    ("libxml2", "d4d1f3f33d6d"),
    ("libredwg", "ff69eeda6658"),
    ("leptonica", "90ec70fd4322"),
    ("igraph", "c83b6ecdc3fe"),
]

# flatgraph 没有 graph.edges（R17 踩过）→ 逐个节点用 out("REF") 数
Q = r'''
importCpg("__CPG__")
val memberNodes = cpg.graph.nodes("MEMBER").size
println(s"@@MEMBER_NODES\t$memberNodes")
val methodNodes = cpg.graph.nodes("METHOD").size
val typeDecl = cpg.graph.nodes("TYPE_DECL").size
println(s"@@METHOD_NODES\t$methodNodes\t@@TYPE_DECL\t$typeDecl")
// 成功的 CALL -> REF 边（traversal 形式，R17 踩过 flatMap(_.out(...)) 那种写法）
val callOut = cpg.call.out("REF").l
val callOutMember = callOut.filter(_.label == "MEMBER")
println(s"@@CALL_REF_TOTAL\t${callOut.size}\t@@CALL_REF_MEMBER\t${callOutMember.size}")
// 另外数一下 MEMBER 被引用的入边（参考）
val memberIn = cpg.graph.nodes("MEMBER").in("REF").l
println(s"@@MEMBER_IN_REF\t${memberIn.size}")
// 全部 CALL 数（分母参考）
println(s"@@CALLS\t${cpg.call.l.size}")
'''


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def run(sc, tag, timeout=TMO):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, f"_q_{tag}.scala")
    open(p, "w", encoding="utf-8").write(sc)
    t0 = time.time()
    pr = subprocess.Popen([JOERN, "--script", p], stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True, errors="replace",
                          start_new_session=True, stdin=subprocess.DEVNULL)
    try:
        o, _ = pr.communicate(timeout=timeout)
        return pr.returncode, o, time.time() - t0
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(pr.pid), signal.SIGKILL)
        except Exception:
            pass
        return "timeout", "", time.time() - t0


def g(out, k):
    """宽松匹配：stderr 合并会让行首带前缀，用 `in` 而不是 startswith。"""
    for ln in (out or "").split("\n"):
        i = ln.find(k + "\t")
        if i >= 0:
            return ln[i:].split("\t")[1:]
    return None


def done():
    s = set()
    if os.path.isfile(RESULTS):
        for ln in open(RESULTS, encoding="utf-8"):
            ln = ln.strip()
            if ln:
                try:
                    s.add(json.loads(ln)["key"])
                except Exception:
                    pass
    return s


def measure(proj, pin):
    key = f"{proj}_{pin}"
    cpg = os.path.join(CPGDIR, key + ".cpg")
    if not os.path.isfile(cpg):
        open(RESULTS, "a", encoding="utf-8").write(
            json.dumps(dict(key=key, error="cpg 缺失"), ensure_ascii=False) + "\n")
        return
    # 删工作副本 → 强制重新加载（断边信息只在加载时打印）
    ws = os.path.join(WS, key + ".cpg")
    if os.path.isdir(ws):
        shutil.rmtree(ws, ignore_errors=True)
    rc, out, sec = run(Q.replace("__CPG__", cpg), key)
    # 保存原始输出：stderr 合并进 stdout 会让行首错位，解析要在原始文件上做
    open(os.path.join(OUT, f"raw_{key}.log"), "w", encoding="utf-8").write(out or "")
    if rc == "timeout":
        open(RESULTS, "a", encoding="utf-8").write(
            json.dumps(dict(key=key, error="timeout"), ensure_ascii=False) + "\n")
        log(f"{key} 超时")
        return
    # 断边：加载时打印的 "Could not create edge ... dstNodeType=MEMBER"
    broken_member = 0
    broken_other = 0
    for ln in (out or "").split("\n"):
        if "Could not create edge" in ln:
            if "dstNodeType=MEMBER" in ln:
                broken_member += 1
            else:
                broken_other += 1
    mem = g(out, "@@MEMBER_NODES")
    crt = g(out, "@@CALL_REF_TOTAL")
    crm = g(out, "@@CALL_REF_MEMBER")
    rec = dict(key=key, project=proj, pin=pin, elapsed_sec=round(sec, 1),
               member_nodes=int(mem[0]) if mem else None,
               call_ref_total=int(crt[0]) if crt else None,
               call_ref_member=int(crm[0]) if crm else None,
               broken_member=broken_member, broken_other=broken_other)
    # 断边占"所有 CALL→MEMBER 引用" = 断 / (断 + 成功)
    if rec["call_ref_member"] is not None:
        den = broken_member + rec["call_ref_member"]
        rec["broken_pct"] = round(100.0 * broken_member / den, 2) if den else None
    open(RESULTS, "a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False) + "\n")
    log(f"{key}: MEMBER={rec['member_nodes']} 成功CALL→MEMBER={rec['call_ref_member']} "
        f"断={broken_member} (其它型断边={broken_other}) 断占比={rec.get('broken_pct')}% {sec:.0f}s")


def main():
    os.makedirs(OUT, exist_ok=True)
    d = done()
    log(f"续跑：已完成 {len(d)}；待测 {len(CPGS)}")
    for proj, pin in CPGS:
        if f"{proj}_{pin}" in d:
            continue
        measure(proj, pin)
    log("完成")


if __name__ == "__main__":
    main()
