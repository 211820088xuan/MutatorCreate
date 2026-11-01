// pc_table_dump.c —— 直接 dump 全部 44119 条边的「边索引 -> PC 地址」，无需跑任何输入
#include <stdint.h>
#include <stdio.h>

static uintptr_t *g_pcs = NULL, *g_pcs_stop = NULL;
void __sanitizer_cov_pcs_init(uintptr_t *start, uintptr_t *stop) {
    g_pcs = start; g_pcs_stop = stop;
}

int main(void) {
    if (!g_pcs || !g_pcs_stop) { fprintf(stderr, "no pc table\n"); return 1; }
    size_t np = (size_t)(g_pcs_stop - g_pcs);   // word 数
    size_t n = np / 2;                          // 每 2 word 一个 PCTableEntry{PC,Flags}
    fprintf(stderr, "TOTAL_EDGES=%zu\n", n);
    for (size_t i = 0; i < n; i++)
        printf("%zu 0x%zx\n", i, (size_t)g_pcs[2 * i]);
    return 0;
}
