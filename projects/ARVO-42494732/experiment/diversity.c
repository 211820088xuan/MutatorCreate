/* 质量度量：1000 个不同 Seed 下，算子产出多少个**互不相同**的输出 */
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
size_t LLVMFuzzerMutate(uint8_t *D, size_t S, size_t M) { (void)D; (void)M; return S; }
#define LLVMFuzzerCustomMutator PLAN_MUT
#include "gen.c"
static unsigned long fnv(const uint8_t *p, size_t n) {
  unsigned long h = 1469598103ul;
  for (size_t i = 0; i < n; i++) h = (h ^ p[i]) * 16777619ul;
  return h;
}
int main(int argc, char **argv) {
  if (argc < 2) return 2;
  FILE *f = fopen(argv[1], "rb");
  if (!f) return 3;
  static uint8_t a[8 << 20], b[8 << 20];
  size_t n = fread(a, 1, sizeof a, f);
  fclose(f);
  int total = (argc > 2) ? atoi(argv[2]) : 1000;
  static unsigned long seen[8192]; int nseen = 0;
  int changed = 0, unchanged = 0;
  for (int s = 0; s < total; s++) {
    memcpy(b, a, n);
    size_t m = PLAN_MUT(b, n, sizeof b, (unsigned)s);
    if (m == n && memcmp(b, a, n) == 0) { unchanged++; continue; }
    changed++;
    unsigned long h = fnv(b, m) ^ (unsigned long)m;
    int dup = 0;
    for (int i = 0; i < nseen; i++) if (seen[i] == h) { dup = 1; break; }
    if (!dup && nseen < 8192) seen[nseen++] = h;
  }
  printf("%d %d %d %d\n", total, changed, unchanged, nseen);
  return 0;
}
