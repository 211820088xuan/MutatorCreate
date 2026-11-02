#!/bin/bash
# 在容器内构建带自定义变异算子的 llvmfuzz
# 用法（容器内）: bash /exp/build_fuzzer.sh
set -e
SRC=/src/libredwg
EXP=/exp
BIN=$EXP/fuzz_exp/llvmfuzz
MUT=$EXP/mutator.c

mkdir -p "$EXP/fuzz_exp"

echo "=== 编译器 ==="
clang --version | head -1

echo "=== 检查依赖 ==="
[ -f "$MUT" ] || { echo "缺少 $MUT"; exit 1; }
[ -f "$SRC/src/.libs/libredwg.a" ] || { echo "缺少静态库"; exit 1; }

echo "=== 检查静态库的 ASan 插桩 ==="
asan_n=$(nm "$SRC/src/.libs/libredwg.a" 2>/dev/null | grep -c "__asan" || true)
echo "  libredwg.a 的 __asan 符号数: $asan_n  （期望 426）"
[ "$asan_n" -gt 100 ] || { echo "静态库没有 ASan 插桩，拒绝构建"; exit 1; }

echo "=== 编译 ==="
cd "$SRC"
clang \
  -O1 -fno-omit-frame-pointer -gline-tables-only \
  -DFUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION \
  examples/llvmfuzz.c "$MUT" \
  -o "$BIN" \
  src/.libs/libredwg.a \
  -I./include -I./src \
  -fsanitize=address -fsanitize=fuzzer \
  2>&1 | tee /tmp/build.log

echo "=== 验证产物 ==="
ls -lh "$BIN"
sancov=$(nm "$BIN" 2>/dev/null | grep -c "sancov" || true)
echo "  sancov 符号数: $sancov  （期望 3151）"
[ "$sancov" -gt 1000 ] || { echo "插桩数量不足"; exit 1; }

echo "=== 确认自定义变异算子已链接 ==="
nm "$BIN" | grep -q "LLVMFuzzerCustomMutator" && echo "  ✅ 找到 LLVMFuzzerCustomMutator 符号"

echo "=== 冒烟测试（两个模式各跑 1000 次） ==="
cd "$EXP"
for mode in 0 1; do
  LIBREDWG_MUTATOR_OFF=$mode ASAN_OPTIONS=detect_leaks=0 \
    "$BIN" -runs=1000 -seed=1 "$EXP/seeds" >/tmp/smoke_$mode.log 2>&1 || true
  cov=$(grep -oE "cov: [0-9]+" /tmp/smoke_$mode.log | tail -1)
  echo "  LIBREDWG_MUTATOR_OFF=$mode -> $cov"
done

echo "=== 构建完成: $BIN ==="
