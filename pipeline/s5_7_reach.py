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
/* 循环体开头探针（宽判据）：use 点在循环条件里时额外插一个，
   测"循环至少迭代两次（第 1 次释放 → 回边读）" —— R36 实测这条比 free 点更早触发 */
#define R36_LOOP(s)      do { g_r36_free[s] = 1; \
                             fprintf (stderr, "LPI_%d\n", (s)); } while (0)
#define R36_OTHER(s, ln) do { fprintf (stderr, "FRX_%d@%d\n", (s), (ln)); } while (0)
"""

# ── 判据：这一行是不是条件头 ─────────────────────────────────────────
COND_HEAD = re.compile(r"^\s*(?:\}\s*)?(while|if|for|else\s+if)\s*\(")


def _sh(cmd, timeout=1800):
    return subprocess.run(["docker", "exec", CONTAINER, "sh", "-c", cmd],
                          capture_output=True, text=True, timeout=timeout)


INSTR_VERSION = "v2"   # 插桩逻辑改了就要改这个，否则会复用旧二进制


def _hash(sites):
    h = hashlib.sha1(INSTR_VERSION.encode())
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

    # ② 每个文件：**逐站点插入 + 语法检查**，坏了就回滚跳过（比二分稳，60 个点约半分钟）
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
        # ① 先在**干净源码**上做自检（helpers 插进去会让后面行号全部位移）
        _src0 = _sh(f"cat -n /src/libredwg/{rel}").stdout.splitlines()
        def _line_of(n):
            return _src0[n - 1].split("\t", 1)[-1] if 1 <= n <= len(_src0) else ""
        FREE_FAMILY = re.compile(r"\b(?:\w*(?:free|Free|FREE)\w*|delete|realloc)\s*\(")
        good_items = []
        for i, s2 in items:
            pts0 = _free_points(s2, free_call_sites, s2.get("_fn_start"))
            badpt = None
            for ln in pts0:
                if not FREE_FAMILY.search(_line_of(ln)):
                    badpt = (ln, _line_of(ln).strip()[:60]); break
            # use 行**不该**是 free 调用（它是读取点），所以不查
            if badpt:
                skipped.append((i, f"insert_point_not_free@L{badpt[0]}: {badpt[1]}"))
            else:
                good_items.append((i, s2))
        if not good_items:
            continue
        items = good_items

        _sh(f"cp {path} {path}.bak_r36")
        # ③ **一趟构造输出**（R36：不要"插"，新行号是副产品）
        #    ins_by_line[原始行号] = [要插在这一行**前面**的语句]
        #    mod_at[原始行号]      = 这一行**本身**改写成什么（use 在条件头时用）
        #    HELPERS 也作为 ins_by_line[第一个 #include 的行号] 的一项 —— 位移自动算对
        _inc_line = next((k + 1 for k, x in enumerate(_src0)
                          if x.split("\t", 1)[-1].lstrip().startswith("#include")), 1)
        ins_by_line, mod_at = {}, {}
        ins_by_line.setdefault(_inc_line, []).extend(HELPERS.split("\n"))
        loop_slot = {}                 # site_idx -> 额外 slot
        _next_slot = len(sites)

        def _is_cond(txt):
            return bool(re.match(r"^\s*(?:\}\s*)?(?:while|if|for|else\s+if)\s*\(", txt))

        def _body_start(ln):
            """use 行是条件头时，找循环体第一行的行号。"""
            for k in range(ln, min(ln + 6, len(_src0))):
                t = _src0[k].split("\t", 1)[-1]
                if t.strip().startswith("{"):
                    return k + 2           # 1-based：'{' 的下一行
                if _src0[k].split("\t", 1)[-1].strip().endswith(")"):
                    return k + 2
            return None

        def _braceless(ln):
            """目标行上一行是不是不带 { 的 if/else/for/while 体头。"""
            k = ln - 2
            while k >= 0 and not _src0[k].split("\t", 1)[-1].strip():
                k -= 1
            if k < 0:
                return False
            prev = _src0[k].split("\t", 1)[-1]
            return bool(re.match(r"^\s*(?:if|else\s+if|for|while|else)\b", prev)) \
                and not prev.rstrip().endswith("{") and not prev.rstrip().endswith(")") is False

        for i2, s2 in items:
            pts = _free_points(s2, free_call_sites, s2.get("_fn_start"))
            # 静态检查：插在单语句 if/else/for/while 里会改控制流
            if any(_braceless(ln) for ln in pts + [s2["use_line"]]):
                skipped.append((i2, "insert_into_braceless_body"))
                continue
            for ln in pts:
                kind = "own" if ln == s2["free_line"] else "other"
                nm = "R36_OWN" if kind == "own" else "R36_OTHER"
                ins_by_line.setdefault(ln, []).append(f"{nm}({i2}, {ln});")
            u = s2["use_line"]
            src_u = _src0[u - 1].split("\t", 1)[-1]
            if _is_cond(src_u):
                # use 在条件头 → 改这一行本身（逗号/短路表达式）
                m = re.match(r"^(\s*(?:\}\s*)?(?:while|if|for|else\s+if)\s*\()", src_u)
                mod_at[u] = src_u.replace(m.group(1), m.group(1) + f"r36_chk({i2}) && ", 1)
                # 额外：循环体开头插一个宽判据探针
                bs = _body_start(u)
                if bs:
                    loop_slot[i2] = _next_slot
                    ins_by_line.setdefault(bs, []).append(f"R36_LOOP({_next_slot});")
                    _next_slot += 1
            else:
                ind = src_u[:len(src_u) - len(src_u.lstrip())]
                ins_by_line.setdefault(u, []).append(f"if (r36_chk({i2})) {{}}")

        out = []
        for n, raw in enumerate(_src0, 1):
            body = raw.split("\t", 1)[-1]
            for stmt in ins_by_line.get(n, []):
                out.append(stmt)
            out.append(mod_at.get(n, body))
        # 注意：这里是**宿主机**上的 Python，写不了容器里的 /src。
        # 先写到挂载目录再 cp 进去（R36 踩过：FileNotFoundError 就是这个原因）。
        _tmp = os.path.join(ROOT, "projects", "ARVO-42494732", "_out.c")
        open(_tmp, "w", encoding="utf-8").write("\n".join(out))
        _sh(f"cp /exp/_out.c {path}")
        chk = _sh(f"cd {COV_SRC} && clang -fsyntax-only -w -I./include -I./src "
                  f"-DFUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION {rel} 2>&1 | head -4")
        if chk.stdout.strip():
            _sh(f"cp {path}.bak_r36 {path}")
            skipped.append((None, f"syntax@{rel}: " + chk.stdout.strip().splitlines()[0][:95]))

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


def reach_all(probe_bin, slot_map, seed_path, n=1000, mutants_dir=None):
    """两臂各测 n 个输入，返回 {sid: {custom, default, ratio, free_points}}。

    **测法必须和 R36-② 一致**：喂**预生成的产物**（每个 `-runs=1`），
    而不是让 fuzzer 自己跑 n 次。R36-② 用前者测得 92×；用后者测出 0。
    `mutants_dir` 下若是 {"custom": dir, "default": dir} 就直接用；
    否则退回"让 probe 自己跑 n 次"（口径不同，仅作参考）。
    """
    inv = {v: k for k, v in slot_map.items()}
    # 循环体开头探针用了额外 slot，映射到同一个 sid
    inv = dict(inv)
    out = {sid: dict(custom=0, default=0, ratio=0.0, free_points={}, loop_start=0) for sid in slot_map}
    for arm, off in (("custom", "0"), ("default", "1")):
        binary = f"{probe_bin}_custom" if arm == "custom" else probe_bin
        d = (mutants_dir or {}).get(arm) if isinstance(mutants_dir, dict) else None
        if d:
            # 逐产物跑（和 R36-② 一致）
            cmd = (f"for f in $(ls {d}/*.bin | head -{n}); do "
                   f"LIBREDWG_MUTATOR_OFF={off} ASAN_OPTIONS=detect_leaks=0 "
                   f"timeout 30 {binary} -runs=1 \"$f\" 2>&1 | "
                   f"grep -oE 'SEQ_[0-9]+|FRI_[0-9]+@[0-9]+|FRX_[0-9]+@[0-9]+|LPI_[0-9]+'; done | "
                   f"sort | uniq -c")
        else:
            cmd = (f"cd {os.path.dirname(probe_bin)} && LIBREDWG_MUTATOR_OFF={off} "
                   f"ASAN_OPTIONS=detect_leaks=0 timeout 1800 {binary} -runs={n} "
                   f"{seed_path} 2>&1 | grep -oE 'SEQ_[0-9]+|FRI_[0-9]+@[0-9]+|FRX_[0-9]+@[0-9]+|LPI_[0-9]+' | "
                   f"sort | uniq -c")
        r = _sh(cmd, timeout=3000)
        for ln in (r.stdout or "").splitlines():
            parts = ln.split()
            if len(parts) != 2:
                continue
            cnt, tok = int(parts[0]), parts[1]
            if tok.startswith("SEQ_"):
                i = int(tok[4:])
                if i in inv:
                    out[inv[i]][arm] = cnt
            elif tok.startswith("LPI_"):
                i = int(tok[4:])
                if i in inv:
                    out[inv[i]]["loop_start"] = cnt
            elif tok.startswith(("FRI_", "FRX_")):
                body = tok[4:]
                if "@" in body:
                    i, line = body.split("@", 1)
                    i = int(i)
                    if i in inv:
                        out[inv[i]]["free_points"][line] = cnt
    for sid, d2 in out.items():
        d2["ratio"] = round(d2["custom"] / max(d2["default"], 1), 2)
    return out

# ─────────────────────────────────────────────────────────────────────
# default 代理（**固定口径，不要每次重新发明一个**）
#
# `LLVMFuzzerMutate` **不能脱离 libFuzzer 单独调用**（它依赖 fuzzer 内部初始化，
# 单独调会 SEGV）。所以 default 臂用这个**字节翻转代理**：
#   · 每生成一个产物，RNG 状态**前进一次**（逐产物递增，不用时间）
#   · 同一次实验的两臂都走这里 → ratio 可比
#   · **换一个代理，历史 ratio 就不能比了**
# ─────────────────────────────────────────────────────────────────────
PROXY_C = r"""
static uint32_t g_proxy_st = 12345u;
size_t LLVMFuzzerMutate(uint8_t *D, size_t S, size_t M) {
  (void)M;
  if (S < 1) return S;
  g_proxy_st = g_proxy_st * 1103515245u + 12345u;
  D[g_proxy_st % S] = (uint8_t)(g_proxy_st >> 16);
  return S;
}
"""

GEN_C = r"""
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
%s
#ifdef USE_CUSTOM
#define LLVMFuzzerCustomMutator PLAN_MUT
#include "gen.c"
#endif
int main(int argc, char **argv) {
  if (argc < 4) return 2;
  FILE *f = fopen(argv[1], "rb"); if (!f) return 3;
  static uint8_t base[8 << 20], buf[8 << 20];
  size_t n = fread(base, 1, sizeof base, f); fclose(f);
  int total = atoi(argv[2]), mode = atoi(argv[3]);
  const char *dir = argv[4];
  int wrote = 0;
  for (int s = 1; s <= total; s++) {
    size_t m;
#ifdef USE_CUSTOM
    if (mode) { memcpy(buf, base, n); m = PLAN_MUT(buf, n, sizeof buf, (unsigned)s); }
    else
#endif
    { memcpy(buf, base, n); m = LLVMFuzzerMutate(buf, n, sizeof buf); }
    char q[512]; snprintf(q, sizeof q, "%%s/m%%05d.bin", dir, s);
    FILE *o = fopen(q, "wb"); if (!o) continue;
    fwrite(buf, 1, m, o); fclose(o); wrote++;
  }
  printf("written %%d\n", wrote);
  return 0;
}
"""


def make_mutants(seed_path, outdir, n=1000, operator_path=None):
    """生成两臂产物（**只生成一次，两臂共享**）。

    custom 臂：用 `operator_path`（d7913b9e）生成
    default 臂：用上面的字节翻转代理生成
    返回 {"custom": dir, "default": dir}
    """
    out = {}
    for arm in ("custom", "default"):
        d = f"{outdir}/{arm}"
        _sh(f"rm -rf {d} && mkdir -p {d}")
        out[arm] = d
    # custom 臂
    if operator_path:
        _sh(f"cp {operator_path} {outdir}/gen.c")
        open(os.path.join(ROOT, "projects", "ARVO-42494732", "_gen.c"),
             "w").write(GEN_C % PROXY_C)
        _sh(f"cp /exp/_gen.c {outdir}/gm.c")
        r = _sh(f"cd {outdir} && clang -O1 -std=c11 -w -DUSE_CUSTOM gm.c -o gm_custom")
        if r.returncode != 0:
            return {}
        _sh(f"cd {outdir} && ./gm_custom {seed_path} {n} 1 {out['custom']}")
    # default 臂
    open(os.path.join(ROOT, "projects", "ARVO-42494732", "_gen2.c"),
         "w").write(GEN_C % PROXY_C)
    _sh(f"cp /exp/_gen2.c {outdir}/gm2.c")
    r = _sh(f"cd {outdir} && clang -O1 -std=c11 -w gm2.c -o gm_default")
    if r.returncode != 0:
        return {}
    _sh(f"cd {outdir} && ./gm_default {seed_path} {n} 0 {out['default']}")
    return out

def rebuild_probe_bisect(sites, free_call_sites=None, force=False, maxdepth=0):
    """编译失败时**二分定位坏站点**，跳过它重编（R36 要求：不许整轮失败）。

    返回 (bin, slots, skipped)。skipped 里每条带原因（含那行真实内容）。
    """
    b, slots, skipped = rebuild_probe(sites, free_call_sites, force=force)
    if b or len(sites) <= 1:
        return b, slots, skipped
    print(f"  [bisect] {len(sites)} 个站点编不过，二分...", flush=True)
    mid = len(sites) // 2
    left, right = sites[:mid], sites[mid:]
    ok_l, bad_l = [], []
    for group, keep in ((left, ok_l), (right, ok_l)):
        b2, s2, sk2 = rebuild_probe(group, free_call_sites, force=True)
        if b2:
            keep.extend(group)
        else:
            bad_l.extend(sk2)
    if ok_l and len(ok_l) == len(sites):
        return None, {}, skipped + bad_l
    if not ok_l:
        return None, {}, skipped + bad_l
    b3, s3, sk3 = rebuild_probe(ok_l, free_call_sites, force=True)
    return b3, s3, skipped + bad_l + sk3


def normalize(sites):
    """把 feature_pipeline 里的 site 规整成插桩需要的形状。"""
    out = []
    for i, s in enumerate(sites):
        ul = (s.get("use") or {}).get("line") if isinstance(s.get("use"), dict) else s.get("use_line")
        if not ul:
            continue
        out.append(dict(s, site_id=s.get("site_id") or f"q{i:03d}",
                        file=s["file"], free_line=int(s["free_line"]),
                        use_line=int(ul), _fn_start=s.get("_fn_start")))
    return out
