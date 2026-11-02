#!/bin/bash
# 单次 fuzz 运行
# 用法（容器内）: bash /exp/run_one.sh <default|custom> <rep> [秒数]
set -u
MODE=${1:?usage: run_one.sh default|custom <rep> [secs]}
REP=${2:?}
SECS=${3:-1800}

EXP=/exp
BIN=$EXP/fuzz_exp/llvmfuzz
OUT=$EXP/fuzz_exp/${MODE}_${REP}
SEEDS=$EXP/seeds

mkdir -p "$OUT/corpus" "$OUT/crash"
cp -n "$SEEDS"/*.dxf "$OUT/corpus"/ 2>/dev/null || true

export ASAN_OPTIONS=detect_leaks=0
export LSAN_OPTIONS=detect_leaks=0

if [ "$MODE" = "default" ]; then
  export LIBREDWG_MUTATOR_OFF=1
else
  export LIBREDWG_MUTATOR_OFF=0
  export LIBREDWG_CUSTOM_PCT=${LIBREDWG_CUSTOM_PCT:-40}
fi

echo "=== mode=$MODE rep=$REP secs=$SECS"
echo "=== OFF=${LIBREDWG_MUTATOR_OFF} PCT=${LIBREDWG_CUSTOM_PCT:-n/a}"
echo "=== 种子 $(ls -1 "$OUT/corpus" | wc -l) 个"

"$BIN" \
  -max_total_time="$SECS" \
  -fork=1 \
  -seed=1 \
  -timeout=25 \
  -rss_limit_mb=2560 \
  -ignore_crashes=1 \
  -ignore_ooms=1 \
  -ignore_timeouts=1 \
  -print_final_stats=1 \
  -artifact_prefix="$OUT/crash/" \
  "$OUT/corpus" \
  > "$OUT/run.log" 2>&1

echo "=== 退出码 $? ==="
grep -E "^stat::|cov: |crash: " "$OUT/run.log" | tail -10
