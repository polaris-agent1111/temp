#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把云主机上的 question/ 目录提交到官方评测服务器（消耗每日 5 次额度之一）。

安全约束：
- 每日硬上限 5 次（官方超过 8 次会封号），本地计数在 runs/submissions.jsonl。
- 提交前自动跑一次 format_check_client，不通过则不提交。
- 默认 dry-run，必须显式 --yes 才真正提交。

用法：
  python client/submit_vm.py                 # 预检（dry-run）
  python client/submit_vm.py --yes           # 真提交
  python client/submit_vm.py --yes --note "precise 12.5MB/s v1"
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "client"))
from vmssh import VmShell  # noqa: E402

SECRETS = ROOT / "client" / "secrets.json"
SUBMISSIONS = ROOT / "runs" / "submissions.jsonl"
LIMIT = 5


def today_count() -> int:
    if not SUBMISSIONS.exists():
        return 0
    today = dt.datetime.now().astimezone().date()
    n = 0
    for line in SUBMISSIONS.read_text("utf-8").splitlines():
        try:
            rec = json.loads(line)
            if dt.date.fromisoformat(rec["date"]) == today and rec.get("status") != "dry-run":
                n += 1
        except Exception:  # noqa: BLE001
            continue
    return n


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true", help="真正提交")
    ap.add_argument("--note", default="")
    ap.add_argument("--timeout", type=float, default=900)
    args = ap.parse_args(argv)

    secrets = json.loads(SECRETS.read_text("utf-8-sig"))
    guid = secrets.get("guid")
    if not guid:
        print("[ERR] secrets.json 缺少 guid")
        return 2

    used = today_count()
    print(f"今日已提交：{used}/{LIMIT}")
    if used >= LIMIT:
        print("[BLOCK] 今日额度已用完")
        return 3

    vm = VmShell()
    vm.connect()
    try:
        code, out = vm.run("cd /home/openlab/Desktop && find question -name pacer.txt | sort | "
                           "xargs -r -I{} sh -c 'echo \"-- {} --\"; cat {}'", timeout=120)
        print("=== 当前 question 配置 ===")
        print(out[:2000])

        code, out = vm.run("cd /home/openlab/Desktop && ./format_check_client 2>&1 | tail -10",
                           timeout=120)
        print("=== 格式检查 ===")
        print(out[-800:])
        if "检查结果: 通过" not in out:
            print("[BLOCK] 格式检查未通过，不提交")
            return 4

        if not args.yes:
            print("[DRY-RUN] 预检通过。确认提交请加 --yes（会消耗 1 次额度）")
            return 0

        print("=== 开始提交（可能需 1-3 分钟）===", flush=True)
        code, out = vm.run(f"cd /home/openlab/Desktop && ./local_send_client --token {guid} 2>&1",
                           timeout=args.timeout)
        print(out[-3000:])
        today = dt.datetime.now().astimezone().date().isoformat()
        rec = {
            "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "date": today,
            "note": args.note,
            "exit_code": code,
            "status": "submitted" if code == 0 else "failed",
            "output_tail": out[-1500:],
        }
        SUBMISSIONS.parent.mkdir(parents=True, exist_ok=True)
        with SUBMISSIONS.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"[{'OK' if code == 0 else 'FAIL'}] 已记录到 runs/submissions.jsonl（今日 {used + 1}/{LIMIT}）")
        return 0 if code == 0 else 1
    finally:
        vm.close()


if __name__ == "__main__":
    sys.exit(main())
