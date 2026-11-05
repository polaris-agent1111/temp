#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在云主机上开/关 CPU 争抢负载，用来模拟「官方评测机被并发抢占」的场景。

用法：
  python tools/vm_load.py start 4     # 开 4 个满载 bash 循环
  python tools/vm_load.py stop
  python tools/vm_load.py status
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "client"))
from vmssh import VmShell  # noqa: E402

START = (
    "for i in 1 2 3 4 5 6; do "
    "if [ $i -le {n} ]; then "
    "setsid nohup bash -c 'exec -a cpuhog bash -c \"while :; do :; done\"' "
    ">/dev/null 2>&1 < /dev/null & fi; done; sleep 2; "
    "echo hog_count=$(pgrep -c -f cpuhog); uptime"
)
STOP = "pkill -f cpuhog; sleep 2; echo hog_count=$(pgrep -c -f cpuhog || true); uptime"
STATUS = "echo hog_count=$(pgrep -c -f cpuhog || true); uptime; free -m | head -2"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["start", "stop", "status"])
    ap.add_argument("n", nargs="?", type=int, default=4)
    args = ap.parse_args(argv)

    vm = VmShell()
    vm.connect()
    if args.action == "start":
        code, out = vm.run(START.format(n=args.n), timeout=120)
    elif args.action == "stop":
        code, out = vm.run(STOP, timeout=120)
    else:
        code, out = vm.run(STATUS, timeout=120)
    print(f"rc={code}\n{out}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
