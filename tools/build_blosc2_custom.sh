#!/bin/bash
# 构建 c-blosc2（漏洞版 commit 4e231e35）+ 带 blosc2_mutator.c 的 decompress_chunk_fuzzer
# 用途：Phase 3 T4.4 / T5 —— 产出 default 与 custom 两个二进制做 A/B
set -uo pipefail

PIN=4e231e35d1a72ccb6025e0f4a45327f0f5a3e28b   # OSV-2021-1645 (ndlz 亚型B) fixed~1
WORK=/root/gyx/cblosc2_build
SRC="$WORK/c-blosc2"
MUT=/root/gyx/mutator_create/mutator_custom/blosc2_mutator.c
OUT=/root/gyx/mutator_create/mutator_custom/blosc2_bins
LOG="$WORK/build.log"
mkdir -p "$WORK" "$OUT"
exec >> "$LOG" 2>&1

echo "=== [$(TZ=Asia/Shanghai date '+%F %T')] 开始构建 c-blosc2 custom mutator ==="

# 1. clone（浅）并 checkout 到漏洞版 commit
if [ ! -d "$SRC/.git" ]; then
  echo "clone c-blosc2 ..."
  git clone --filter=blob:none https://github.com/Blosc/c-blosc2.git "$SRC" || exit 1
fi
cd "$SRC"
git fetch --depth 1 origin "$PIN" || echo "fetch 失败（可能已有该 commit）"
git checkout -f "$PIN" 2>&1 | tail -2 || { echo "checkout 失败"; exit 1; }
echo "HEAD=$(git rev-parse HEAD)"

# 2. cmake 构建静态库 + 默认 fuzzer（不链 mutator，作为对照组）
echo "=== cmake ==="
rm -rf build && mkdir build && cd build
cmake .. \
  -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
  -DBUILD_FUZZERS=ON -DBUILD_TESTS=OFF -DBUILD_BENCHMARKS=OFF \
  -DBUILD_EXAMPLES=OFF -DBUILD_STATIC=ON -DBUILD_SHARED=OFF \
  -DCMAKE_C_FLAGS="-fsanitize=fuzzer-no-link,address -O1 -g" \
  -DCMAKE_CXX_FLAGS="-fsanitize=fuzzer-no-link,address -O1 -g" \
  >> "$LOG" 2>&1 || { echo "cmake 失败"; exit 1; }

echo "=== make ==="
make -j"$(nproc)" >> "$LOG" 2>&1 || { echo "make 失败"; tail -30 "$LOG"; exit 1; }
echo "make 完成"

# 3. 定位 decompress_chunk_fuzzer 目标与库
echo "=== 产物定位 ==="
find . -name 'decompress_chunk_fuzzer' -o -name 'libblosc2*.a' 2>/dev/null | head -20
ls -la *.a 2>/dev/null | head

# 4. 手动链 custom 版：fuzzer 源码 + mutator + 静态库
FUZZ_SRC=$(find .. -path '*fuzz*decompress_chunk*.c' | head -1)
echo "FUZZ_SRC=$FUZZ_SRC"
if [ -n "${FUZZ_SRC:-}" ]; then
  clang -fsanitize=fuzzer-no-link,address -O1 -g -I.. -I. -c "$FUZZ_SRC" -o /tmp/fuzz_dc.o
  clang -fsanitize=fuzzer-no-link,address -O1 -g -c "$MUT" -o /tmp/mut.o
  # 收集静态库（blosc2 主库 + 内部 complibs）
  LIBS=$(find . -name '*.a' | tr '\n' ' ')
  echo "LIBS=$LIBS"
  clang -fsanitize=fuzzer,address -O1 -g /tmp/fuzz_dc.o /tmp/mut.o $LIBS -lm -o "$OUT/decompress_chunk_custom" 2>&1 | tail -20
fi

echo "=== [$(TZ=Asia/Shanghai date '+%F %T')] 构建结束 ==="
ls -la "$OUT" 2>/dev/null
