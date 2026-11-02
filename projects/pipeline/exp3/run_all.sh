#!/bin/bash
# run_all.sh —— fuzz_exp3 全流程：fuzz → 重放分析 → 汇总
#
# 设计要求：
#   1) 可重入：已完成的 run（存在 .done）会跳过，避免服务器再关机后全部重来
#   2) 每个 run 的 merge 前清空控制文件（analyze_run.py 已修）
#   3) 两臂：default = 100% 默认变异；custom = 80% 默认 + 20% 自定义
set -u
BASE=/exp/fuzz_exp3
BIN=$BASE/llvmfuzz
SEED=$BASE/corpus
PIPE=$BASE/pipeline
REPS=5
DUR=10800          # 3 小时
MAXLEN=131072

echo "=== 配置 ==="
echo "  reps=$REPS  duration=${DUR}s  max_len=$MAXLEN"
echo -n "  sancov: "; nm "$BIN" | grep -c sancov
echo -n "  种子  : "; ls "$SEED"/*.dxf 2>/dev/null | wc -l
echo -n "  磁盘  : "; df -h / | tail -1 | awk '{print $4}'
echo ""

# ---------------- 1. fuzz ----------------
echo "=== [1/3] fuzz 阶段 ($(date '+%T')) ==="
for arm in default custom; do
  case "$arm" in
    default) pct=0 ;;
    custom)  pct=20 ;;
  esac
  for i in $(seq 1 "$REPS"); do
    d="$BASE/${arm}_${i}"
    if [ -f "$d/.done" ]; then
      echo "  [skip] ${arm}_${i} 已完成"
      continue
    fi
    rm -rf "$d"
    mkdir -p "$d/corpus" "$d/art"
    cp "$SEED"/*.dxf "$d/corpus/" 2>/dev/null
    echo "  [start $(date '+%T')] ${arm}_${i}  (CUSTOM_PCT=$pct)"
    (
      ASAN_OPTIONS=detect_leaks=0 LSAN_OPTIONS=detect_leaks=0 \
      LIBREDWG_CUSTOM_PCT="$pct" "$BIN" \
        -max_total_time="$DUR" -max_len="$MAXLEN" \
        -fork=1 -detect_leaks=0 -seed=1 \
        -timeout=120 -rss_limit_mb=2048 \
        -ignore_crashes=1 -ignore_ooms=1 -ignore_timeouts=1 \
        -print_final_stats=1 -artifact_prefix="$d/art/" \
        "$d/corpus/" > "$d/run.log" 2>&1
      if grep -q "exiting:" "$d/run.log" 2>/dev/null; then
        touch "$d/.done"
      fi
    ) &
  done
done
wait
echo "  [$(date '+%T')] fuzz 阶段结束: 完成 $(find "$BASE" -maxdepth 2 -name .done | wc -l)/10"
echo ""

# ---------------- 2. 重放分析 ----------------
echo "=== [2/3] 重放分析 ($(date '+%T')) ==="
n=0
for arm in default custom; do
  for i in $(seq 1 "$REPS"); do
    [ -f "$BASE/${arm}_${i}/.done" ] || { echo "  [skip] ${arm}_${i} 无有效结果"; continue; }
    echo "  [analyze $(date '+%T')] ${arm}_${i}"
    python3 "$PIPE/analyze_run.py" "$arm" "$i" &
    n=$((n + 1))
    if [ $((n % 5)) -eq 0 ]; then wait; fi
  done
done
wait
echo "  [$(date '+%T')] 分析完成"
echo ""

# ---------------- 3. 汇总 ----------------
echo "=== [3/3] 汇总 ($(date '+%T')) ==="
python3 "$PIPE/summary_exp3.py"
echo "[$(date '+%T')] 全部完成"
