#!/bin/bash
# run_one.sh —— 启动单次 fork fuzz（对应参考实现的 run_one_3h.sh）
# usage: run_one.sh <mode> <suffix> [duration_seconds]
#   mode = default|custom, suffix = 1..5
set -u
MODE="$1"
SUFFIX="$2"
DUR="${3:-1200}"

BIN=/exp/fuzz_exp/llvmfuzz
SEEDDIR=/exp/seeds
BASE=/exp/fuzz_exp

if [ "$MODE" = "custom" ]; then MUTOFF=0; else MUTOFF=1; fi

RUN_DIR="$BASE/${MODE}_${SUFFIX}"
rm -rf "$RUN_DIR"
mkdir -p "$RUN_DIR/corpus" "$RUN_DIR/crash"
cp "$SEEDDIR"/*.dxf "$RUN_DIR/corpus/"

echo "[$(date '+%F %T')] 启动 ${MODE}_${SUFFIX} seed=1 ${DUR}s (LIBREDWG_MUTATOR_OFF=$MUTOFF)"

LIBREDWG_MUTATOR_OFF="$MUTOFF" ASAN_OPTIONS=detect_leaks=0 LSAN_OPTIONS=detect_leaks=0 "$BIN" \
  -max_total_time="$DUR" -fork=1 -detect_leaks=0 -seed=1 \
  -timeout=25 -rss_limit_mb=2560 \
  -ignore_crashes=1 -ignore_ooms=1 -ignore_timeouts=1 \
  -print_final_stats=1 -artifact_prefix="$RUN_DIR/crash/" \
  "$RUN_DIR/corpus/" > "$RUN_DIR/run.log" 2>&1

echo "[$(date '+%F %T')] ${MODE}_${SUFFIX} 结束"
