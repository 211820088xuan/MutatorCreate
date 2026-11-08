p = "/src/libredwg_cov/src/in_dxf.c"
L = open(p, encoding="utf-8", errors="replace").read().split("\n")

# 先改 while 条件（用逗号表达式塞进条件求值）—— 这一步不改变行数
i = 12266
assert "while (pair != NULL" in L[i], L[i]
L[i] = L[i].replace("while (pair != NULL",
                    'while ((fprintf (stderr, "REACHED_s001_use\\n"), 1) && pair != NULL')

# 三处 free 点，倒序插（行号大的先）—— 插的是"前一行"，所以用 1-based-1 作索引
for ln, tag in ((12287, "12287"), (12284, "12284"), (12275, "12275")):
    idx = ln - 1
    assert "dxf_free_pair (pair);" in L[idx], (ln, L[idx])
    indent = L[idx][:len(L[idx]) - len(L[idx].lstrip())]
    L.insert(idx, f'{indent}fprintf (stderr, "REACHED_s001_free@{tag}\\n");')

open(p, "w", encoding="utf-8").write("\n".join(L))
print("  已插：use(条件内) + 三处 free@12275/12284/12287")
