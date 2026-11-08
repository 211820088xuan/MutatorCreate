p = "/src/libredwg_cov/src/in_dxf.c"
L = open(p, encoding="utf-8", errors="replace").read().split("\n")
# 倒序插：先 12284（1-based）再 12267
# 插在 12284 之前：free 即将发生
assert "dxf_free_pair (pair);" in L[12283], L[12283]
L.insert(12283, '              fprintf (stderr, "REACHED_s001_free\\n");')
# 此时 12267 已后移 1 位 -> 索引 12266
assert "while (pair != NULL" in L[12266], L[12266]
L.insert(12266, '      fprintf (stderr, "REACHED_s001_use\\n");')
open(p, "w", encoding="utf-8").write("\n".join(L))
print("  已插两点（倒序）：free@12284, use@12267")
