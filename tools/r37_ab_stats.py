"""R37 A/B 统计：崩溃次数 / 去重 / per-exec 率 / 覆盖率 / 独立性。"""
import json, os, re, sys, hashlib
from collections import Counter

def parse_log(p):
    """fork 模式下没有 stat:: 行 —— 从最后一条进度行取 #execs / cov / crash 计数。"""
    t = open(p, encoding="utf-8", errors="replace").read()
    ex = cov = cr = 0
    for m in re.finditer(r"#(\d+): cov: (\d+) ft: (\d+) corp: (\d+) exec/s (\d+) "
                         r"oom/timeout/crash: (\d+)/(\d+)/(\d+) time: (\d+)s", t):
        ex, cov, cr = int(m.group(1)), int(m.group(2)), int(m.group(8))
    return dict(execs=ex, cov=cov, crashes=cr,
                saved_crashes=len([f for f in os.listdir(os.path.dirname(p) + "/crash")
                                   if os.path.isfile(os.path.join(os.path.dirname(p), "crash", f))])
                if os.path.isdir(os.path.dirname(p) + "/crash") else 0)

def crash_points(d):
    """从 crash/ 目录里每个文件读 ASan 报告的首行 SUMMARY。"""
    out = []
    for fn in sorted(os.listdir(d)):
        p = os.path.join(d, fn)
        if not os.path.isfile(p): continue
        b = open(p, "rb").read(4096)
        out.append((fn, hashlib.sha1(open(p,'rb').read()).hexdigest(), len(open(p,'rb').read())))
    return out

def main(root):
    rows = []
    for rep in sorted(os.listdir(root)):
        rd = os.path.join(root, rep)
        if not os.path.isdir(rd): continue
        for arm in sorted(os.listdir(rd)):
            ad = os.path.join(rd, arm)
            if not os.path.isdir(ad): continue
            lg = os.path.join(ad, "run.log")
            if not os.path.exists(lg): continue
            st = parse_log(lg)
            cr = os.path.join(ad, "crash")
            n = len([f for f in os.listdir(cr) if os.path.isfile(os.path.join(cr,f))]) if os.path.isdir(cr) else 0
            st.update(rep=rep, arm=arm, crash_files=n,
                      rate=(st["crashes"] / st["execs"] * 1e6 if st["execs"] else 0),
                      cov100k=(st["cov"] / st["execs"] * 1e5 if st["execs"] else 0))
            rows.append(st)
    return rows

if __name__ == "__main__":
    rows = main(sys.argv[1])
    for r in rows:
        print(f"  {r['rep']}/{r['arm']}: execs={r['execs']:>7} crashes={r['crashes']:>4} "
              f"(files {r['crash_files']:>3}) rate/1e6={r['rate']:>7.2f} cov={r['cov']:>5} "
              f"cov/100k={r['cov100k']:>7.3f}")
