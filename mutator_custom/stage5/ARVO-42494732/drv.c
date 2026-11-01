/* drv.c —— 单独调用 LLVMFuzzerCustomMutator，把变异结果写出来
 * 用法: drv <输入文件> <输出文件> <seed>
 * 编译: clang -O1 drv.c mutator.c -o drv
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

/* 提供 LLVMFuzzerMutate 的桩，避免链接 libFuzzer */
size_t LLVMFuzzerMutate(uint8_t *d, size_t s, size_t m) { (void)d; (void)m; return s; }

extern size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size,
                                      size_t MaxSize, unsigned int Seed);

int main(int argc, char **argv) {
    if (argc < 4) { fprintf(stderr, "usage: %s <in> <out> <seed>\n", argv[0]); return 1; }

    FILE *f = fopen(argv[1], "rb");
    if (!f) { perror("open"); return 2; }
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);

    size_t cap = (size_t)n + 65536;
    uint8_t *buf = (uint8_t *)malloc(cap);
    size_t sz = fread(buf, 1, (size_t)n, f);
    fclose(f);

    uint8_t *out = (uint8_t *)malloc(cap);
    memcpy(out, buf, sz);

    size_t osz = LLVMFuzzerCustomMutator(out, sz, cap, (unsigned)atoi(argv[3]));

    FILE *g = fopen(argv[2], "wb");
    if (!g) { perror("write"); return 3; }
    fwrite(out, 1, osz, g);
    fclose(g);

    fprintf(stderr, "in=%zu out=%zu delta=%+ld\n", sz, osz, (long)osz - (long)sz);
    return 0;
}
