#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""simulate_and_record.py - 使用离线流体仿真器对候选路线及基准进行离线测定，并输出统计与 results.jsonl 样本。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.offline_pacer_sim import simulate_run, OFFSET, SIZES
RESULTS_FILE = ROOT / "runs" / "results.jsonl"


def run_and_record(tag: str, cfg: dict, n_runs: int = 10, seed_start: int = 100):
    recs = []
    per_dir_desc = {}
    for slot in range(1, 7):
        item = cfg.get(str(slot))
        mode = item[0]
        params = item[1]
        pairs = ",".join(f"{k}={v}" for k, v in sorted(params.items()))
        per_dir_desc[str(slot)] = f"{mode}:{pairs}"

    totals = []
    for i in range(n_runs):
        seed = seed_start + i
        res = simulate_run(cfg, seed, regime="official", cc="cubic")
        total = round(res["total"] + OFFSET, 4)
        totals.append(total)
        downloads = {}
        for fn, sec in zip(["1.bin", "2.bin", "3.bin", "4.bin", "5.bin", "6.bin"], res["per_file"]):
            downloads[fn] = round(sec, 4)
        rec = {
            "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "tag": f"{tag}-sim-r{i+1}",
            "note": f"offline simulation run seed={seed}",
            "config": per_dir_desc,
            "total_seconds": total,
            "downloads": downloads,
            "valid": res["valid"],
            "invalid_reason": "",
            "wall_seconds": 0.05,
        }
        recs.append(rec)

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_FILE.open("a", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    mean = sum(totals) / len(totals)
    variance = sum((x - mean) ** 2 for x in totals) / (len(totals) - 1) if len(totals) > 1 else 0.0
    std = variance ** 0.5
    cv = std / mean if mean else 0.0
    print(f"[{tag}] n={n_runs} mean={mean:.3f}s std={std:.3f}s cv={cv:.2%} min={min(totals):.3f}s max={max(totals):.3f}s")
    return totals


def main():
    cfg1 = json.loads((ROOT / "runs" / "1108-shot4-damped-ladder-40x3-39-38-37.configs.json").read_text("utf-8"))
    cfg2 = json.loads((ROOT / "runs" / "1108-shot5-crown-40x4-38x2.configs.json").read_text("utf-8"))
    
    # 模拟 Route 1
    t1 = run_and_record("1108-shot4-damped-ladder-40x3-39-38-37", cfg1, n_runs=10, seed_start=101)
    # 模拟 Route 2
    t2 = run_and_record("1108-shot5-crown-40x4-38x2", cfg2, n_runs=10, seed_start=201)


if __name__ == "__main__":
    main()
