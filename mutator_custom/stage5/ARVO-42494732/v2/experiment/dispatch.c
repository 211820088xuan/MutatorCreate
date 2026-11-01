/* A/B 分发层（不改生成的 mutator.c）：
 * 编译 mutator.c 时用 -DLLVMFuzzerCustomMutator=V2MutatorIMPL 把它改名，
 * 这里再提供真正的 LLVMFuzzerCustomMutator，按环境变量切换。
 * LIBREDWG_MUTATOR_OFF=1 → 100% default；否则走 V2 算子。
 */
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);
size_t V2MutatorIMPL(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed);

size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize,
                               unsigned int Seed) {
  const char *off = getenv("LIBREDWG_MUTATOR_OFF");
  if (off && off[0] == '1')
    return LLVMFuzzerMutate(Data, Size, MaxSize);
  return V2MutatorIMPL(Data, Size, MaxSize, Seed);
}
