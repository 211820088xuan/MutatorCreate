#!/bin/bash
# 重复对照：**所有 run 同时启动**（16 核 / 10 个 run，各占一个核）。
# 这样两臂共享同一时间窗，时间漂移对它们影响一致；配对比较更干净。
set -u
DUR="${1:-150}"
REPS="${2:-5}"
EXP=/exp/v2/experiment
BIN=$EXP/llvmfuzz
SEEDS=/exp/seeds
ROOT=$EXP/reps
rm -rf "$ROOT"; mkdir -p "$ROOT"

pids=()
for r in $(seq 1 "$REPS"); do
  for arm in default custom; do
    OUT=$ROOT/rep$(printf %02d "$r")/$arm
    mkdir -p "$OUT/corpus" "$OUT/crash"
    cp "$SEEDS"/*.dxf "$OUT/corpus"/ 2>/dev/null || true
    cp "$SEEDS"/*.dwg "$OUT/corpus"/ 2>/dev/null || true
    [ "$arm" = default ] && MO=1 || MO=0
    (
      LIBREDWG_MUTATOR_OFF="$MO" ASAN_OPTIONS=detect_leaks=0 LSAN_OPTIONS=detect_leaks=0 \
        "$BIN" -max_total_time="$DUR" -fork=1 -detect_leaks=0 -seed=1 \
          -timeout=25 -rss_limit_mb=1200 \
          -ignore_crashes=1 -ignore_ooms=1 -ignore_timeouts=1 \
          -print_final_stats=1 -artifact_prefix="$OUT/crash/" \
          "$OUT/corpus/" > "$OUT/run.log" 2>&1
    ) &
    pids+=($!)
  done
done
echo "[$(date '+%T')] 已启动 ${#pids[@]} 个 run，每个 ${DUR}s"
wait
echo "[$(date '+%T')] 全部完成"
