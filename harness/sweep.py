#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量实验驱动器：按队列文件依次跑实验，每个配置可重复 N 次。

队列文件（JSON 数组）示例：
[
  {"tag": "A", "note": "precise 12.5MB/s", "all": ["precise_rate_based", {"max_pacing_rate": 12500000}], "repeat": 2},
  {"tag": "B", "note": "分文件配置", "configs": {"1": ["origin", {"burst_tokens": 100}], "2": ["origin", {"burst_tokens": 100}]}, "repeat": 2}
]

用法：python harness/sweep.py --queue runs/queue1.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "harness"))
from run_experiment import run_experiment  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", required=True)
    ap.add_argument("--only", nargs="*", help="只跑指定 tag")
    args = ap.parse_args(argv)

    queue = json.loads(Path(args.queue).read_text("utf-8"))
    if args.only:
        queue = [q for q in queue if q["tag"] in args.only]
    total = len(queue)
    print(f"[sweep] {total} configs, queue={args.queue}", flush=True)
    for i, item in enumerate(queue, 1):
        tag = item["tag"]
        repeat = int(item.get("repeat", 1))
        if "all" in item:
            mode, params = item["all"][0], item["all"][1] if len(item["all"]) > 1 else {}
            per_dir = {n: (mode, params) for n in range(1, 7)}
        else:
            per_dir = {int(k): (v[0], v[1] if len(v) > 1 and v[1] else {})
                       for k, v in item.get("configs", {}).items()}
        print(f"\n[sweep] ({i}/{total}) tag={tag} repeat={repeat} note={item.get('note','')}",
              flush=True)
        try:
            run_experiment(tag, per_dir, note=item.get("note", ""), repeat=repeat,
                           timeout=900, poll=10)
        except Exception as exc:  # noqa: BLE001
            print(f"[sweep][ERROR] tag={tag}: {exc}", flush=True)
            time.sleep(5)
    print("\n[sweep] ALL DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
