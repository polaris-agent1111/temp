#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盯着官方榜单，等我们队的第 N 次成绩出现；出现即退出。

用法: python tools/watch_board.py [--team 赛博coder] [--interval 60] [--max-min 300]
输出: runs/board_watch.jsonl（每次发现新 attempts 追加一行）+ stdout
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "runs" / "board_watch.jsonl"


def fetch(board_url: str) -> dict:
    r = requests.get(board_url, timeout=30)
    r.raise_for_status()
    return r.json()


def attempts_of(data: dict, team: str) -> list:
    out = []
    for p in (data.get("leaderboard") or {}).get("problems") or []:
        for s in p.get("submissions") or []:
            if s.get("team") == team:
                out = list(s.get("attempts") or [])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://47.120.64.152:5000/api/leaderboard")
    ap.add_argument("--team", default="赛博coder")
    ap.add_argument("--interval", type=int, default=120)
    ap.add_argument("--max-min", type=int, default=300)
    ap.add_argument("--want", type=int, default=2, help="看到第几次 attempt 就退出")
    args = ap.parse_args()

    deadline = time.time() + args.max_min * 60
    last_n = 0
    while time.time() < deadline:
        try:
            data = fetch(args.url)
        except Exception as exc:  # 网络抖动不影响
            print(f"[{datetime.now():%H:%M:%S}] fetch failed: {exc}", flush=True)
            time.sleep(args.interval)
            continue
        atts = attempts_of(data, args.team)
        n = len(atts)
        if n != last_n:
            rec = {
                "seen_at": datetime.now().isoformat(timespec="seconds"),
                "team": args.team,
                "n": n,
                "attempts": atts,
                "submission_log": [e for e in (data.get("submission_log") or [])
                                   if e.get("team") == args.team],
            }
            LOG.parent.mkdir(parents=True, exist_ok=True)
            with LOG.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"[{rec['seen_at']}] NEW attempts n={n}: {atts}", flush=True)
            last_n = n
            if n >= args.want:
                return 0
        time.sleep(args.interval)
    print(f"[{datetime.now():%H:%M:%S}] timeout, last n={last_n}", flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
