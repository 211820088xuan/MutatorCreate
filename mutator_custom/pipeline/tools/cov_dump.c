// cov_dump.c —— 自定义覆盖率 dumper：输出被覆盖的「计数器索引」（边编号 0..N-1）
//
// 原理：fuzz target 用 -fsanitize-coverage=inline-8bit-counters 编译，启动时会调用
//   __sanitizer_cov_8bit_counters_init(start, stop) 登记 8-bit 计数器数组。
// 我们自己定义这个回调拿到数组起止，跑完所有输入后，把非零计数器的下标打出来。
//
// 用法： ./cov_dump <输入文件1> <输入文件2> ...
//   stderr 输出 TOTAL_COUNTERS=<N>；stdout 每行一个"被覆盖的边索引"。
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

// 由 fuzz_decompress_chunk.c 提供
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size);

static uint8_t *g_start = NULL;
static uint8_t *g_stop = NULL;

// sanitizer coverage 启动时调用，登记 8-bit 计数器数组的起止地址
void __sanitizer_cov_8bit_counters_init(uint8_t *start, uint8_t *stop) {
    g_start = start;
    g_stop = stop;
}

int main(int argc, char **argv) {
    // 逐文件喂给被测入口（累加覆盖，不做清零 → 得到所有文件的并集覆盖）
    for (int i = 1; i < argc; i++) {
        FILE *f = fopen(argv[i], "rb");
        if (!f) { fprintf(stderr, "skip %s\n", argv[i]); continue; }
        fseek(f, 0, SEEK_END);
        long sz = ftell(f);
        fseek(f, 0, SEEK_SET);
        uint8_t *buf = (uint8_t *)malloc(sz > 0 ? (size_t)sz : 1);
        if (buf && fread(buf, 1, (size_t)sz, f) == (size_t)sz) {
            LLVMFuzzerTestOneInput(buf, (size_t)sz);
        }
        free(buf);
        fclose(f);
    }

    if (g_start && g_stop && g_stop > g_start) {
        size_t n = (size_t)(g_stop - g_start);
        fprintf(stderr, "TOTAL_COUNTERS=%zu\n", n);
        for (size_t i = 0; i < n; i++) {
            if (g_start[i] != 0)          // 非零 = 被覆盖过
                printf("%zu\n", i);        // 输出边索引
        }
    } else {
        fprintf(stderr, "ERROR: no counters registered\n");
        return 1;
    }
    return 0;
}
