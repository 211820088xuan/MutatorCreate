/* 按指定 Seed 调一次算子，输出完整结果（用于逐策略检查） */
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
size_t LLVMFuzzerMutate(uint8_t *D, size_t S, size_t M) { (void)D; (void)M; return S; }
#define LLVMFuzzerCustomMutator PLAN_MUT
#include "gen.c"
int main(int argc, char **argv) {
  if (argc < 3) return 2;
  FILE *f = fopen(argv[1], "rb");
  if (!f) return 3;
  static uint8_t a[8 << 20], b[8 << 20];
  size_t n = fread(a, 1, sizeof a, f);
  fclose(f);
  memcpy(b, a, n);
  unsigned seed = (unsigned)strtoul(argv[2], NULL, 10);
  size_t m = PLAN_MUT(b, n, sizeof b, seed);
  fwrite(b, 1, m, stdout);
  return 0;
}
