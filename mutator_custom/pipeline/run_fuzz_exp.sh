#!/bin/bash
# 2 小时并行 fuzz 实验：default vs custom（同一二进制 decompress_chunk_nocov，mutator 不插覆盖率）
# 加 -ignore_crashes/-ignore_ooms/-ignore_timeouts，找到崩溃也不停，跑满 2 小时。
# 收集 corpus 供后续重放实验验证覆盖率。
set -u

BIN=/root/gyx/mutator_create/mutator_custom/blosc2_bins/decompress_chunk_nocov
SEED_SRC=/root/gyx/cblosc2_build/c-blosc2/compat
EXP=/root/gyx/mutator_create/mutator_custom/fuzz_exp

# 1. 前置校验
[ -x "$BIN" ] || { echo "❌ 二进制不存在: $BIN"; exit 1; }
[ -d "$SEED_SRC" ] || { echo "❌ 种子目录不存在: $SEED_SRC"; exit 1; }

# 2. 准备工作目录（清空重建）
rm -rf "$EXP"
mkdir -p "$EXP/corpus_default" "$EXP/corpus_custom" "$EXP/art_default" "$EXP/art_custom"
cp "$SEED_SRC"/*.cdata "$EXP/corpus_default/"
cp "$SEED_SRC"/*.cdata "$EXP/corpus_custom/"
NSEED=$(ls "$EXP/corpus_default" | wc -l)
echo "初始种子（两种模式相同）: $NSEED 个"

# 3. 启动 default 模式（BLOSC2_MUTATOR_OFF=1，走默认变异）
nohup env BLOSC2_MUTATOR_OFF=1 "$BIN" \
  -max_total_time=7200 -fork=1 -len_control=0 -seed=1 -timeout=25 -rss_limit_mb=2560 -ignore_crashes=1 -ignore_ooms=1 -ignore_timeouts=1 \
  -print_final_stats=1 -artifact_prefix="$EXP/art_default/" "$EXP/corpus_default/" \
  > "$EXP/default.log" 2>&1 &
echo $! > "$EXP/default.pid"

# 4. 启动 custom 模式（不设开关，走自定义变异）
nohup env "$BIN" \
  -max_total_time=7200 -fork=1 -len_control=0 -seed=1 -timeout=25 -rss_limit_mb=2560 -ignore_crashes=1 -ignore_ooms=1 -ignore_timeouts=1 \
  -print_final_stats=1 -artifact_prefix="$EXP/art_custom/" "$EXP/corpus_custom/" \
  > "$EXP/custom.log" 2>&1 &
echo $! > "$EXP/custom.pid"

# 5. 写元数据
{
  echo "binary=$BIN"
  echo "seed_corpus=$SEED_SRC ($NSEED files)"
  echo "start_time=$(TZ=Asia/Shanghai date '+%F %T')"
  echo "duration=7200s"
  echo "fork=1 ignore_crashes=1 ignore_ooms=1 ignore_timeouts=1"
  echo "len_control=0 seed=1 timeout=25 rss_limit_mb=2560"
  echo "default_pid=$(cat "$EXP/default.pid")"
  echo "custom_pid=$(cat "$EXP/custom.pid")"
  echo "note=两种模式用同一二进制、mutator不插覆盖率(44119计数器)，唯一差别=变异策略"
} > "$EXP/README.txt"

echo "default_pid=$(cat "$EXP/default.pid")  custom_pid=$(cat "$EXP/custom.pid")"
echo "日志: $EXP/default.log  /  $EXP/custom.log"
echo "corpus: $EXP/corpus_default/  /  $EXP/corpus_custom/"
