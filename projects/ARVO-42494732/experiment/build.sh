#!/bin/bash
# 在容器内构建 V2 实验二进制：/exp/v2/experiment/llvmfuzz
set -e
SRC=/src/libredwg
EXP=/exp
V2=$EXP
BIN=$V2/experiment/llvmfuzz
MUT=$V2/mutator.c
DISP=$V2/experiment/dispatch.c

mkdir -p "$V2/experiment"
[ -f "$MUT" ] || { echo "缺少 $MUT"; exit 1; }
[ -f "$DISP" ] || { echo "缺少 $DISP"; exit 1; }
[ -f "$SRC/src/.libs/libredwg.a" ] || { echo "缺少静态库"; exit 1; }

echo "=== 编译 mutator（改名为 V2MutatorIMPL）==="
cd "$SRC"
clang -O1 -fno-omit-frame-pointer -gline-tables-only \
  -DFUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION \
  -DLLVMFuzzerCustomMutator=V2MutatorIMPL \
  -c "$MUT" -o /tmp/v2_mutator.o \
  -I./include -I./src -fsanitize=address

echo "=== 链接 ==="
clang -O1 -fno-omit-frame-pointer -gline-tables-only \
  -DFUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION \
  examples/llvmfuzz.c "$DISP" /tmp/v2_mutator.o \
  -o "$BIN" src/.libs/libredwg.a \
  -I./include -I./src -fsanitize=address -fsanitize=fuzzer

ls -lh "$BIN"
echo -n "  sancov 符号: "; nm "$BIN" | grep -c sancov
nm "$BIN" | grep -q "V2MutatorIMPL" && echo "  ✅ V2MutatorIMPL 已链接"
nm "$BIN" | grep -q "LLVMFuzzerCustomMutator" && echo "  ✅ 分发层已链接"
