#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""等到指定时刻（默认次日 00:05），然后把每日 5 次官方提交一次性投完。

为什么这样：官方额度按北京时间的自然日重置，而官方评测对同一配置近似确定，
所以每天 5 发应当作为 5 次「配置探测」，越早投完越早知道结果。

用法：
  python tools/night_submit.py --plan runs/submit_plan_1106.json --at "2026-11-06 00:05"
  python tools/night_submit.py --plan runs/submit_plan_1106.json --at now   # 立刻
"""
from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def wait_until(target: dt.datetime) -> None:
    while True:
        now = dt.datetime.now()
        left = (target - now).total_seconds()
        if left <= 0:
            return
        print(f"[wait] 距目标 {target:%m-%d %H:%M} 还有 {left/60:.1f} 分钟", flush=True)
        time.sleep(min(600, max(30, left)))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--at", default="2026-11-06 00:05")
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--retry-wait-min", type=float, default=10.0)
    args = ap.parse_args(argv)

    if args.at.strip().lower() != "now":
        target = dt.datetime.strptime(args.at.strip(), "%Y-%m-%d %H:%M")
        wait_until(target)

    for attempt in range(1, args.retries + 1):
        print(f"\n===== 提交尝试 {attempt}/{args.retries} @ {dt.datetime.now():%Y-%m-%d %H:%M:%S} =====", flush=True)
        rc = subprocess.call([PY, "tools/submit_batch.py", "--plan", args.plan, "--yes"], cwd=str(ROOT))
        print(f"[result] rc={rc}", flush=True)
        if rc == 0:
            return 0
        if attempt < args.retries:
            print(f"[retry] {args.retry_wait_min:.0f} 分钟后重试", flush=True)
            time.sleep(args.retry_wait_min * 60)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
