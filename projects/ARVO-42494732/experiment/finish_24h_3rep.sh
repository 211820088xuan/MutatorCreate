#!/bin/bash
# 24h × 3 rep 的收尾：等结束 → 快照 → 逐小时崩溃统计 → 目标崩溃站点分类
#
# 注意：pgrep -x 会把僵尸（<defunct>）也算进来，上一轮 watcher 就卡在这上面。
# 这里用 `ps -eo stat,comm` 排除 Z 状态。
set -u
EXP=/exp/experiment
ROOT=$EXP/reps
SNAP=$EXP/reps_24h_3rep

alive() {
  ps -eo stat,comm --no-headers 2>/dev/null \
    | awk '$2=="llvmfuzz" && $1 !~ /^Z/ {n++} END{print n+0}'
}

echo "[$(date '+%T')] 等待 llvmfuzz 退出（排除僵尸）..."
while [ "$(alive)" -gt 0 ]; do sleep 120; done
sleep 20
echo "[$(date '+%T')] 已无活跃 fuzz 进程"

if [ -d "$ROOT" ]; then
  if [ -d "$SNAP" ]; then SNAP="${SNAP}_$(date +%Y%m%d_%H%M)"; fi
  mv "$ROOT" "$SNAP"
  echo "[$(date '+%T')] 快照: $SNAP"
else
  echo "[$(date '+%T')] 没有找到 $ROOT"; exit 1
fi

echo "[$(date '+%T')] 1/2 逐小时崩溃统计..."
python3 "$EXP/hourly_crashes.py" --root "$SNAP" --link --link-corpus > "$SNAP/HOURLY.md" 2>&1
echo "  退出码 $?"

echo "[$(date '+%T')] 2/2 目标崩溃站点分类（逐文件回放，8 路并行）..."
python3 "$EXP/analyze_reps.py" "$SNAP" --binary "$EXP/llvmfuzz" > "$SNAP/ANALYSIS.md" 2>&1
echo "  退出码 $?"

touch "$SNAP/.all_done"
echo "[$(date '+%T')] 完成"
