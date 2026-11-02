#!/bin/bash
# V2 单特征对照：同一二进制，靠 LIBREDWG_MUTATOR_OFF 切换
set -u
DUR="${1:-180}"
EXP=/exp/v2/experiment
BIN=$EXP/llvmfuzz
SEEDS=/exp/seeds

for arm in default custom; do
  OUT=$EXP/$arm
  rm -rf "$OUT"; mkdir -p "$OUT/corpus" "$OUT/crash"
  cp "$SEEDS"/*.dxf "$OUT/corpus"/ 2>/dev/null || true
  cp "$SEEDS"/*.dwg "$OUT/corpus"/ 2>/dev/null || true
  [ "$arm" = default ] && MO=1 || MO=0
  echo "[$(date '+%T')] $arm  start  ${DUR}s  LIBREDWG_MUTATOR_OFF=$MO"
  LIBREDWG_MUTATOR_OFF="$MO" ASAN_OPTIONS=detect_leaks=0 LSAN_OPTIONS=detect_leaks=0 \
    "$BIN" -max_total_time="$DUR" -fork=1 -detect_leaks=0 -seed=1 \
      -timeout=25 -rss_limit_mb=2560 \
      -ignore_crashes=1 -ignore_ooms=1 -ignore_timeouts=1 \
      -print_final_stats=1 -artifact_prefix="$OUT/crash/" \
      "$OUT/corpus/" > "$OUT/run.log" 2>&1
  echo "[$(date '+%T')] $arm  done"
done
