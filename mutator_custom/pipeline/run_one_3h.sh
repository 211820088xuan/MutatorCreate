#!/bin/bash
# 启动单次 3 小时 fork fuzz
# usage: run_one_3h.sh <mode> <suffix>   （mode=default|custom，suffix=1..5）
set -u
MODE="$1"
SUFFIX="$2"
BIN=/root/gyx/mutator_create/mutator_custom/blosc2_bins/decompress_chunk_nocov
SEEDDIR=/root/gyx/cblosc2_build/c-blosc2/compat
BASE=/root/gyx/mutator_create/mutator_custom/fuzz_exp_3h
SO=/root/gyx/mutator_create/mutator_custom/pipeline/tools/intercept_unlink.so

if [ "$MODE" = "custom" ]; then MUTOFF=0; else MUTOFF=1; fi

RUN_DIR="$BASE/${MODE}_${SUFFIX}"
rm -rf "$RUN_DIR"
mkdir -p "$RUN_DIR/corpus" "$RUN_DIR/capture" "$RUN_DIR/art"
cp "$SEEDDIR"/*.cdata "$RUN_DIR/corpus/"

echo "[$(date '+%F %T')] 启动 ${MODE}_${SUFFIX} seed=1 3h"

export MERGE_CAPTURE_DIR="$RUN_DIR/capture"
LD_PRELOAD="$SO" BLOSC2_MUTATOR_OFF="$MUTOFF" "$BIN" \
  -max_total_time=10800 -fork=1 -len_control=0 -seed=1 \
  -timeout=25 -rss_limit_mb=2560 \
  -ignore_crashes=1 -ignore_ooms=1 -ignore_timeouts=1 \
  -print_final_stats=1 -artifact_prefix="$RUN_DIR/art/" \
  "$RUN_DIR/corpus/" > "$RUN_DIR/run.log" 2>&1

echo "[$(date '+%F %T')] ${MODE}_${SUFFIX} 结束"
