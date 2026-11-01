#!/bin/bash
# run_all_resume.sh —— 断点续跑（服务器关机/容器重启后用）
#
# 与 run_all.sh 的区别：
#   run_all.sh        对未完成的 run 会**清空重来**（再花 3 小时）
#   run_all_resume.sh 对未完成的 run **保留已有 corpus，只补剩余时间**
#
# 原理：libFuzzer 一直在往 corpus/ 里写文件，corpus 本身就是检查点，
#       所以从现有 corpus 继续不丢任何已完成的工作。
set -u
BASE=/exp/fuzz_exp3
BIN=$BASE/llvmfuzz
SEED=$BASE/corpus
PIPE=$BASE/pipeline
REPS=5
DUR=10800
MAXLEN=131072
LOCK=/tmp/fuzz_exp3.lock

# 单实例锁：避免开机自启与手工启动同时跑
exec 9>"$LOCK"
if ! flock -n 9; then
  echo "已有实例在跑，退出"
  exit 0
fi

echo "=== 断点续跑 $(date '+%F %T') ==="
for arm in default custom; do
  case "$arm" in default) pct=0 ;; custom) pct=20 ;; esac
  for i in $(seq 1 "$REPS"); do
    d="$BASE/${arm}_${i}"
    if [ -f "$d/.done" ]; then
      echo "  [skip] ${arm}_${i} 已完成"
      continue
    fi

    if [ -d "$d/corpus" ] && [ "$(ls "$d/corpus" 2>/dev/null | wc -l)" -gt 6 ]; then
      # 有残局：算已用时间，续跑剩余
      elapsed=$(grep -oE "time: [0-9]+s" "$d/run.log" 2>/dev/null | tail -1 | grep -oE "[0-9]+" || true)
      elapsed=${elapsed:-0}
      remain=$((DUR - elapsed))
      if [ "$remain" -le 60 ]; then
        touch "$d/.done"
        echo "  [done] ${arm}_${i} 已达时长(${elapsed}s)"
        continue
      fi
      echo "  [resume $(date '+%T')] ${arm}_${i}  已用 ${elapsed}s，再跑 ${remain}s"
    else
      rm -rf "$d"
      mkdir -p "$d/corpus" "$d/art"
      cp "$SEED"/*.dxf "$d/corpus/" 2>/dev/null
      remain=$DUR
      echo "  [fresh $(date '+%T')] ${arm}_${i}  跑 ${remain}s"
    fi

    (
      ASAN_OPTIONS=detect_leaks=0 LSAN_OPTIONS=detect_leaks=0 \
      LIBREDWG_CUSTOM_PCT="$pct" "$BIN" \
        -max_total_time="$remain" -max_len="$MAXLEN" \
        -fork=1 -detect_leaks=0 -seed=1 \
        -timeout=120 -rss_limit_mb=2048 \
        -ignore_crashes=1 -ignore_ooms=1 -ignore_timeouts=1 \
        -print_final_stats=1 -artifact_prefix="$d/art/" \
        "$d/corpus/" >> "$d/run.log" 2>&1
      if grep -q "exiting:" "$d/run.log" 2>/dev/null; then
        touch "$d/.done"
      fi
    ) &
  done
done
wait
echo "=== fuzz 阶段结束 $(date '+%T')，完成 $(find "$BASE" -maxdepth 2 -name .done | wc -l)/10 ==="

# 只要有全部 10 个完成，就继续分析和汇总
if [ "$(find "$BASE" -maxdepth 2 -name .done | wc -l)" -eq 10 ]; then
  echo "=== 重放分析 $(date '+%T') ==="
  n=0
  for arm in default custom; do
    for i in $(seq 1 "$REPS"); do
      python3 "$PIPE/analyze_run.py" "$arm" "$i" &
      n=$((n + 1))
      if [ $((n % 5)) -eq 0 ]; then wait; fi
    done
  done
  wait
  echo "=== 汇总 $(date '+%T') ==="
  python3 "$PIPE/summary_exp3.py"
  touch "$BASE/.all_done"
fi
echo "=== 全部完成 $(date '+%T') ==="
