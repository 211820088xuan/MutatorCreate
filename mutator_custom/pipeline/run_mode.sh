#!/bin/bash
# 启动一个模式的 fork fuzz（2小时），记录 corpus + merge 控制文件 + 日志
# usage: run_mode.sh <mode_name> <mutator_off>
set -u
MODE="$1"
MUTOFF="$2"
BIN=/root/gyx/mutator_create/mutator_custom/blosc2_bins/decompress_chunk_nocov
SEED=/root/gyx/cblosc2_build/c-blosc2/compat
BASE=/root/gyx/mutator_create/mutator_custom/fuzz_exp_2h
SO=/root/gyx/mutator_create/mutator_custom/pipeline/tools/intercept_unlink.so

MODE_DIR="$BASE/$MODE"
rm -rf "$MODE_DIR"
mkdir -p "$MODE_DIR/corpus" "$MODE_DIR/capture" "$MODE_DIR/art"
cp "$SEED"/*.cdata "$MODE_DIR/corpus/"

echo "[$(TZ=Asia/Shanghai date '+%F %T')] 启动 $MODE 模式 (BLOSC2_MUTATOR_OFF=$MUTOFF)，2h fork"

export MERGE_CAPTURE_DIR="$MODE_DIR/capture"
LD_PRELOAD="$SO" BLOSC2_MUTATOR_OFF="$MUTOFF" "$BIN" \
  -max_total_time=7200 -fork=1 -len_control=0 -seed=1 \
  -timeout=25 -rss_limit_mb=2560 \
  -ignore_crashes=1 -ignore_ooms=1 -ignore_timeouts=1 \
  -print_final_stats=1 -artifact_prefix="$MODE_DIR/art/" \
  "$MODE_DIR/corpus/" > "$MODE_DIR/run.log" 2>&1

echo "[$(TZ=Asia/Shanghai date '+%F %T')] $MODE 模式结束"
