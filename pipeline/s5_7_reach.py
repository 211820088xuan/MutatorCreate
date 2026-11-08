"""R36 改动 ④：执行门禁 —— 一次全插、跑一次 fuzzing，拿到所有站点的 ratio。

## 判据

**存在一对 `free@<line>` 在某次 `use` 之前** —— 也就是"这个变异让执行走出了『先释放后使用』的序列"。

## 为什么不用覆盖率

R33/R36-② 查明：`llvmfuzz_cov` 的 `-print_coverage` 在两个应该相反的输入上给出相同的 4965
（常数，无信息量）；而 `libredwg.a` 原本只有 ASan、没有覆盖插桩。
**所以改用"在源码里插标记"**：`llvmfuzz_probe` 打 `REACHED_*` / `SEQ_*`，百分百准。

## 插桩规则（R36-② 实测）

| 规则 | 内容 |
|---|---|
| free 点 | 该函数的**所有**释放调用点全插，标记带行号 |
| use 点 | 条件头（`while`/`if`/`for`）用**逗号表达式**塞进条件；普通语句插**前一行** |
| 插入顺序 | **倒序**（行号大的先），否则前一次插入会让后面的行号移位 |
| 计数 | **按 free 点分别计数**（不能合并 —— `12275` 是 1.04×、`12284` 是 92×） |

## 批量测法

58 个站点**全插进一个二进制**，跑两臂各 n 次，一次拿到所有 ratio。
成本 2×n，不是 58×2×n。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTAINER = "libredwg-exp"
COV_SRC = "/src/libredwg_cov"
PROBE_DIR = "/tmp/r36probe"

# ── C 侧辅助（注入到每个被插桩文件的顶部）─────────────────────────────
HELPERS = r"""
/* R36 执行门禁插桩（由 s5_7_reach.py 注入） */
#include <stdio.h>
#define R36_MAXSITE 256
__attribute__((weak)) int g_r36_free[256];
static int __attribute__((unused)) r36_chk(int s) {
  if (g_r36_free[s]) {
    fprintf (stderr, "SEQ_%d\n", s);
    g_r36_free[s] = 0;
  }
  return 1;
}
/* free 点分两种：
   R36_OWN  = 站点自己的 free_line，**置位**（后面的 use 才可能是 UAF）
   R36_OTHER= 同函数里其它 free 点，**只计数**（R36-② 的教训：12275(安全) 和 12284(危险)
              必须分开，混在一起 ratio 就变成 1.0，没有区分力） */
#define R36_OWN(s, ln)   do { g_r36_free[s] = 1; \
                             fprintf (stderr, "FRI_%d@%d\n", (s), (ln)); } while (0)
#define R36_OTHER(s, ln) do { fprintf (stderr, "FRX_%d@%d\n", (s), (ln)); } while (0)
"""

# ── 判据：这一行是不是条件头 ─────────────────────────────────────────
COND_HEAD = re.compile(r"^\s*(?:\}\s*)?(while|if|for|else\s+if)\s*\(")


def _sh(cmd, timeout=1800):
    return subprocess.run(["docker", "exec", CONTAINER, "sh", "-c", cmd],
                          capture_output=True, text=True, timeout=timeout)


def _hash(sites):
    h = hashlib.sha1()
    for s in sorted(sites, key=lambda x: (x["file"], x["free_line"], x["use_line"])):
        h.update(f'{s["file"]}:{s["free_line"]}:{s["use_line"]};'.encode())
    return h.hexdigest()[:12]


def _free_points(site, free_call_sites, fn_start=None):
    """该站点的 free 行 + 同函数里其它释放调用点（R36-② 规则：全插）。

    `free_call_sites` 里的行号是**函数内相对行号**（`line_in_func`），
    要用函数起始行换算成绝对行。换算不出来就只用站点自己的 free_line。
    """
    pts = {site["free_line"]}
    if fn_start:
        for f in free_call_sites or []:
            k = f.get("line_in_func") or f.get("line")
            if isinstance(k, int) and k > 0:
                pts.add(int(fn_start) + k)
    return sorted(pts, reverse=True)          # 倒序


def rebuild_probe(sites, free_call_sites=None, force=False):
    """给定候选站点，倒序插桩、重编，返回 (二进制路径, {sid: slot})。

    候选集的 hash 做缓存键 —— 候选集没变就复用。
    """
    key = _hash(sites)
    out_bin = f"{PROBE_DIR}/llvmfuzz_probe_multi_{key}"
    r = _sh(f"test -x {out_bin} && echo YES || echo NO")
    if "YES" in r.stdout and not force:
        print(f"  [probe] 复用缓存 {out_bin}", flush=True)
        return out_bin, {s.get("site_id") or f"{s['file']}:{s['free_line']}": i
                         for i, s in enumerate(sites)}, []

    # ① 还原干净源码
    _sh(f"rm -rf {COV_SRC} && cp -a /src/libredwg {COV_SRC} && cd {COV_SRC} && make clean >/dev/null 2>&1")
    _sh(f"mkdir -p {PROBE_DIR}")

    # ② 每个文件：先倒序插探针，再在最后一个 #include 之后插 helpers
    by_file = {}
    for i, s2 in enumerate(sites):
        by_file.setdefault(s2["file"].lstrip("./"), []).append((i, s2))
    skipped = []
    script_path = os.path.join(ROOT, "projects", "ARVO-42494732", "_ins.py")
    for rel, items in by_file.items():
        path = f"{COV_SRC}/{rel}"
        r = _sh(f"test -f {path} && echo YES || echo NO")
        if "YES" not in r.stdout:
            skipped += [(i, "file_missing") for i, _ in items]
            continue
        ins = []
        for i, s2 in items:
            for ln in _free_points(s2, free_call_sites, s2.get("_fn_start")):
                ins.append([ln, i, "own" if ln == s2["free_line"] else "other"])
            ins.append([s2["use_line"], i, "use"])
        prog = (
            "import re\n"
            f"p = {path!r}\n"
            f"INS = {ins!r}\n"
            f"HELP = {HELPERS!r}\n"
            "L = open(p, encoding='utf-8', errors='replace').read().split(chr(10))\n"
            "if any('R36_MAXSITE' in x for x in L):\n"
            "    print('SKIP_ALREADY')\n"
            "    raise SystemExit(0)\n"
            "for ln, i, kind in sorted(INS, key=lambda t: -t[0]):\n"
            "    idx = ln - 1\n"
            "    if idx < 0 or idx >= len(L):  continue\n"
            "    src = L[idx]\n"
            "    ind = src[:len(src) - len(src.lstrip())]\n"
            "    if kind == 'own':\n"
            "        L.insert(idx, ind + f'R36_OWN({i}, {ln});')\n"
            "    elif kind == 'other':\n"
            "        L.insert(idx, ind + f'R36_OTHER({i}, {ln});')\n"
            "    else:\n"
            "        m = re.match(r'^(\\s*(?:\\}\\s*)?(?:while|if|for|else\\s+if)\\s*\\()', src)\n"
            "        if m:\n"
            "            L[idx] = src.replace(m.group(1), m.group(1) + f'r36_chk({i}) && ', 1)\n"
            "        else:\n"
            "            L.insert(idx, ind + f'if (r36_chk({i})) {{}}')\n"
            # 插在**第一个** #include 之后（最后一个可能落在文件中间的条件编译里）
            "k = 0\n"
            "for i, x in enumerate(L):\n"
            "    if x.lstrip().startswith('#include'):\n"
            "        k = i + 1\n"
            "        break\n"
            "L[k:k] = HELP.split(chr(10))\n"
            "open(p, 'w', encoding='utf-8').write(chr(10).join(L))\n"
            "print('INS_OK')\n"
        )
        open(script_path, "w", encoding="utf-8").write(prog)
        r = _sh("python3 /exp/_ins.py")
        if "INS_OK" not in r.stdout and "SKIP_ALREADY" not in r.stdout:
            skipped += [(i, "insert_failed") for i, _ in items]

    # ⑤ 编译（失败就二分定位，本轮先整体报错）
    r = _sh(f"""cd {COV_SRC} && rm -f src/*.lo src/.libs/*.o 2>/dev/null; \
make -j8 CFLAGS="-O1 -fno-omit-frame-pointer -gline-tables-only \
-DFUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION -fsanitize=address" > /tmp/r36_build.log 2>&1; \
echo BUILD=$?""")
    if "BUILD=0" not in r.stdout:
        tail = _sh(f"tail -25 /tmp/r36_build.log").stdout
        return None, {}, skipped + [(None, "build_failed\n" + tail)]

    r = _sh(f"""cd {COV_SRC} && clang -O1 -gline-tables-only -fsanitize=fuzzer,address \
examples/llvmfuzz.c -o {out_bin} src/.libs/libredwg.a -I./include -I./src 2>/tmp/r36_link.log; echo LINK=$?""")
    if "LINK=0" not in r.stdout:
        tail = _sh("tail -25 /tmp/r36_link.log").stdout
        return None, {}, skipped + [(None, "link_failed\n" + tail)]
    # custom 变体（链接 dispatch + d7913b9e 算子）
    r2 = _sh(f"""cd {COV_SRC} && clang -O1 -gline-tables-only -fsanitize=fuzzer,address \
examples/llvmfuzz.c /exp/v2/experiment/dispatch.c /tmp/m.o -o {out_bin}_custom \
src/.libs/libredwg.a -I./include -I./src 2>/tmp/r36_link2.log; echo LINK=$?""")
    if "LINK=0" not in r2.stdout:
        tail = _sh("tail -25 /tmp/r36_link2.log").stdout
        return None, {}, skipped + [(None, "link_custom_failed\n" + tail)]
    return out_bin, {s.get("site_id") or f"{s['file']}:{s['free_line']}": i
                     for i, s in enumerate(sites)}, skipped


def reach_all(probe_bin, slot_map, seed_path, n=1000, nsite=None):
    """跑两臂各 n 次，返回 {sid: {custom, default, ratio}}。"""
    inv = {v: k for k, v in slot_map.items()}
    out = {sid: dict(custom=0, default=0, ratio=0.0, free_points={}) for sid in slot_map}
    for arm, off in (("custom", "0"), ("default", "1")):
        binary = f"{probe_bin}_custom" if arm == "custom" else probe_bin
        r = _sh(f"cd {os.path.dirname(probe_bin)} && LIBREDWG_MUTATOR_OFF={off} "
                f"ASAN_OPTIONS=detect_leaks=0 timeout 1800 {binary} -runs={n} "
                f"{seed_path} 2>&1 | grep -oE 'SEQ_[0-9]+|FRI_[0-9]+@[0-9]+|FRX_[0-9]+@[0-9]+' | sort | uniq -c",
                timeout=2400)
        for ln in (r.stdout or "").splitlines():
            parts = ln.split()
            if len(parts) != 2:
                continue
            cnt, tok = int(parts[0]), parts[1]
            if tok.startswith("SEQ_"):
                i = int(tok[4:])
                if i in inv:
                    out[inv[i]][arm] = cnt
            elif tok.startswith(("FRI_", "FRX_")):
                body = tok[4:]
                if "@" in body:
                    i, line = body.split("@", 1)
                    i = int(i)
                    if i in inv:
                        out[inv[i]]["free_points"][line] = cnt
    for sid, d in out.items():
        d["ratio"] = round(d["custom"] / max(d["default"], 1), 2)
    return out
