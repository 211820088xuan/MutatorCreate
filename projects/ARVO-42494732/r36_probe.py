p = "/src/libredwg_cov/src/in_dxf.c"
L = open(p, encoding="utf-8", errors="replace").read().split("\n")
# 找 dxf_objects_read 的函数体开头
for i, ln in enumerate(L):
    if ln.startswith("dxf_objects_read (Bit_Chain"):
        j = i
        while L[j].strip() != "{":
            j += 1
        L.insert(j + 1, '  fprintf (stderr, "REACHED_dxf_objects_read\\n");')
        open(p, "w", encoding="utf-8").write("\n".join(L))
        print(f"  插入到第 {j+2} 行（函数在第 {i+1} 行）")
        break
else:
    print("  ❌ 没找到函数")
