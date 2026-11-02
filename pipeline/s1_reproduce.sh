#!/bin/bash
# s1_reproduce.sh —— 阶段1（漏洞复现）入口
#
# 为什么是一层包装而不把脚本搬进来：
#   reproduce_crash/ 自带 artifacts/ / binaries/ 目录树，路径全部基于 __file__，
#   搬进 pipeline/ 会让所有路径失效。所以这里只做「切目录 + 转发」。
#
# 当前实现：arvo_repro.py —— 从 ARVO 的 docker 镜像批量复现。
#   原来那条「从 OSS-Fuzz 源码在 HEAD/钉版上构建再跑 testcase」的路径
#   （run_repro.py / build_orchestrator.py / repro_runner.py 等 13 个脚本 + preflight/）
#   已于 2026-11-02 移除；需要时从 commit f31ba99e 取回。
#
# 用法：
#   bash s1_reproduce.sh --limit 20 --jobs 4
#   bash s1_reproduce.sh --help                     # 透传 arvo_repro.py 的帮助
#
# 数据源：只从 ARVO 复现（docker pull n132/arvo:<id>-vul → 抠 /tmp/poc /out /src → 验证崩溃）。
# 原来那条"从 OSS-Fuzz 源码在 HEAD/钉版上构建再跑 testcase"的路径已移除。
set -u
PIPE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$PIPE")"          # mutator_create/
RC="$ROOT/reproduce_crash"

if [ ! -f "$RC/arvo_repro.py" ]; then
  echo "找不到 $RC/arvo_repro.py"
  exit 1
fi

cd "$RC" || exit 1
echo "=== 阶段1 入口（ARVO）: $RC/arvo_repro.py"
exec python3 arvo_repro.py "$@"
