import sys
p = '/src/libredwg_cov/src/in_dxf.c'
HELP = '\n/* R36 执行门禁插桩（由 s5_7_reach.py 注入） */\n#include <stdio.h>\n#define R36_MAXSITE 256\n__attribute__((weak)) int g_r36_free[256];\nstatic int __attribute__((unused)) r36_chk(int s) {\n  if (g_r36_free[s]) {\n    fprintf (stderr, "SEQ_%d\\n", s);\n    g_r36_free[s] = 0;\n  }\n  return 1;\n}\n/* free 点分两种：\n   R36_OWN  = 站点自己的 free_line，**置位**（后面的 use 才可能是 UAF）\n   R36_OTHER= 同函数里其它 free 点，**只计数**（R36-② 的教训：12275(安全) 和 12284(危险)\n              必须分开，混在一起 ratio 就变成 1.0，没有区分力） */\n#define R36_OWN(s, ln)   do { g_r36_free[s] = 1; \\\n                             fprintf (stderr, "FRI_%d@%d\\n", (s), (ln)); } while (0)\n/* 循环体开头探针（宽判据）：use 点在循环条件里时额外插一个，\n   测"循环至少迭代两次（第 1 次释放 → 回边读）" —— R36 实测这条比 free 点更早触发 */\n#define R36_LOOP(s)      do { g_r36_free[s] = 1; \\\n                             fprintf (stderr, "LPI_%d\\n", (s)); } while (0)\n#define R36_OTHER(s, ln) do { fprintf (stderr, "FRX_%d@%d\\n", (s), (ln)); } while (0)\n'
L = open(p, encoding='utf-8', errors='replace').read().split(chr(10))
if any('R36_MAXSITE' in x for x in L):
    print('SKIP_ALREADY'); raise SystemExit(0)
k = 0
for i, x in enumerate(L):
    if x.lstrip().startswith('#include'):
        k = i + 1; break
L[k:k] = HELP.split(chr(10))
open(p, 'w', encoding='utf-8').write(chr(10).join(L))
print('HDR_OK')
