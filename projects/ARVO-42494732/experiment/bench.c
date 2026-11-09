#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
size_t LLVMFuzzerMutate(uint8_t *D, size_t S, size_t M) { (void)D; (void)M; return S; }
size_t V2MutatorIMPL(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed);
int main(int argc, char **argv) {
  const char *seed_path = argv[1];
  int iters = argc > 2 ? atoi(argv[2]) : 20000;
  FILE *f = fopen(seed_path, "rb");
  if (!f) { perror("open"); return 1; }
  static uint8_t buf[1 << 20], work[1 << 20];
  size_t n = fread(buf, 1, sizeof(buf), f);
  fclose(f);
  size_t changed = 0, grew = 0, sum_ret = 0;
  clock_t t0 = clock();
  unsigned int s = 1;
  for (int i = 0; i < iters; i++) {
    memcpy(work, buf, n);
    size_t r = V2MutatorIMPL(work, n, sizeof(work), s++);
    if (r != n) grew++;
    if (r != n || memcmp(work, buf, n) != 0) changed++;
    sum_ret += r;
  }
  clock_t t1 = clock();
  double ms = (double)(t1 - t0) * 1000.0 / CLOCKS_PER_SEC;
  printf("  seed=%s  size=%zu  iters=%d\n", seed_path, n, iters);
  printf("  总耗时 %.1f ms  → 每次 %.4f ms\n", ms, ms / iters);
  printf("  改动过的次数: %zu (%.1f%%)   长度变化: %zu  平均返回长度: %.0f\n",
         changed, 100.0 * changed / iters, grew, (double)sum_ret / iters);
  return 0;
}
