#!/bin/bash
# wait_and_analyze_3h.sh —— 等 10 个 fuzz 全部结束后，自动重放 + 记录 + 汇总
set -u
BASE=/root/gyx/mutator_create/mutator_custom/fuzz_exp_3h
# 用 -f 匹配完整命令行；本脚本命令行不含该模式，不会自匹配
while pgrep -f "max_total_time=10800" > /dev/null 2>&1; do
  sleep 30
done
echo "[$(date '+%F %T')] 10 个 fuzz 全部结束，开始重放分析"

for m in default custom; do
  for i in 1 2 3 4 5; do
    python3 /root/gyx/mutator_create/mutator_custom/pipeline/analyze_run_3h.py "$m" "$i"
  done
done

python3 /root/gyx/mutator_create/mutator_custom/pipeline/summarize_3h.py > "$BASE/summary_stdout.txt" 2>&1
echo "[$(date '+%F %T')] 分析与汇总完成"
