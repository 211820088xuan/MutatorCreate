#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LLM API 高峰护栏：北京时间 9:00-12:00、14:00-18:00 为 DeepSeek API 高峰时段。

⚠ 语义（2026-10-12 用户澄清）：
   * 高峰期间**仅禁止调用 LLM API**（价格贵，控制成本）；
   * **纯计算/脚本任务（Docker、ddmin、敏感性扫描等）不受限，任何时段可跑**。
   因此本脚本只用于「准备调用 LLM API 之前」的自检，不要用在纯计算任务上。

用法：
    python3 tools/tz_gate.py            # 非高峰 exit 0（可调 API）；高峰 exit 3 并打印 BLOCKED
    python3 tools/tz_gate.py next       # 打印下一个非高峰窗口的起始时间(epoch秒) 与 还需 sleep 秒数
    python3 tools/tz_gate.py wait       # 阻塞直到进入非高峰（供后台 API 任务前对齐）
    python3 tools/tz_gate.py until HH:MM  # 打印到下一个指定时刻(北京)还需 sleep 的秒数

设计要点：高峰窗口按北京时间(Asia/Shanghai)判断，与宿主机的本地时区无关。
"""
from __future__ import annotations

import datetime
import sys
import time


def _tz():
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("Asia/Shanghai")
    except Exception:
        return datetime.timezone(datetime.timedelta(hours=8))


def beijing_now() -> datetime.datetime:
    return datetime.datetime.now(_tz())


def is_peak(dt: datetime.datetime) -> bool:
    """9:00-12:00 或 14:00-18:00 为高峰。"""
    hm = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    return (9.0 <= hm < 12.0) or (14.0 <= hm < 18.0)


def next_nonpeak(dt: datetime.datetime) -> datetime.datetime:
    """返回 dt 之后（含）的第一个非高峰时刻。"""
    d = dt.replace(second=0, microsecond=0)
    # 遍历未来 48 小时，逐分钟找第一个非高峰点（简单可靠）
    for i in range(0, 48 * 60 + 1):
        cand = d + datetime.timedelta(minutes=i)
        if not is_peak(cand):
            return cand
    raise RuntimeError("unreachable")


def main(argv) -> int:
    now = beijing_now()
    peak = is_peak(now)
    print(f"{now:%Y-%m-%d %H:%M:%S} Beijing  peak={peak}")
    if argv and argv[0] == "next":
        nxt = next_nonpeak(now)
        wait = max(0, (nxt - now).total_seconds())
        print(f"next_nonpeak={nxt:%Y-%m-%d %H:%M:%S}  epoch={int(nxt.timestamp())}  sleep_s={int(wait)}")
        return 0
    if argv and argv[0] == "wait":
        while is_peak(beijing_now()):
            time.sleep(30)
        print(f"{beijing_now():%Y-%m-%d %H:%M:%S} Beijing  non-peak reached")
        return 0
    if argv and argv[0] == "until":
        # until HH:MM —— 输出到下一个该时刻（北京）还需 sleep 的秒数
        try:
            hh, mm = (int(x) for x in argv[1].split(":"))
        except Exception:
            print("用法: tz_gate.py until HH:MM", file=sys.stderr)
            return 2
        now = beijing_now()
        tgt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if tgt <= now:
            tgt += datetime.timedelta(days=1)
        wait = int((tgt - now).total_seconds())
        print(f"target={tgt:%Y-%m-%d %H:%M:%S} Beijing  sleep_s={wait}")
        return 0
    if peak:
        print("BLOCKED: LLM API peak (09:00-12:00 / 14:00-18:00 Beijing), do not call the API.")
        return 3
    print("OK: non-peak, LLM API allowed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
