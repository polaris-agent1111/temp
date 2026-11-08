#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compare_routes.py - 对基准 (steady-40x3-37-36-36)、Route 1 (40x3-39-38-37) 和 Route 2 (40x4-38x2) 进行同种子配对仿真比较。
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.offline_pacer_sim import simulate_run, OFFSET

def make_cfg(rates):
    return {
        str(i): ["leak_bucket", {"bucket_cap": r, "leak_interval_us": 4000, "leak_rate": r}]
        for i, r in enumerate(rates, 1)
    }

BASE_RATES   = [40, 40, 40, 37, 36, 36]
ROUTE1_RATES = [40, 40, 40, 39, 38, 37]
ROUTE2_RATES = [40, 40, 40, 40, 38, 38]

def stats(values):
    n = len(values)
    m = statistics.mean(values)
    s = statistics.stdev(values) if n > 1 else 0.0
    se = s / (n ** 0.5) if n > 1 else 0.0
    return {"n": n, "mean": m, "median": statistics.median(values), "std": s, "se": se, "min": min(values), "max": max(values)}

def main():
    cfg_base = make_cfg(BASE_RATES)
    cfg_r1 = make_cfg(ROUTE1_RATES)
    cfg_r2 = make_cfg(ROUTE2_RATES)

    seeds = 50
    t_base = []
    t_r1 = []
    t_r2 = []

    for s in range(seeds):
        seed = 5000 + s
        rb = simulate_run(cfg_base, seed, regime="official", cc="cubic")["total"] + OFFSET
        r1 = simulate_run(cfg_r1, seed, regime="official", cc="cubic")["total"] + OFFSET
        r2 = simulate_run(cfg_r2, seed, regime="official", cc="cubic")["total"] + OFFSET
        t_base.append(rb)
        t_r1.append(r1)
        t_r2.append(r2)

    sb = stats(t_base)
    sr1 = stats(t_r1)
    sr2 = stats(t_r2)

    delta_r1 = [r1 - b for r1, b in zip(t_r1, t_base)]
    delta_r2 = [r2 - b for r2, b in zip(t_r2, t_base)]
    s_dr1 = stats(delta_r1)
    s_dr2 = stats(delta_r2)

    print("=== 配对仿真对比分析 (50 种子同源对齐) ===")
    print(f"基准 steady-40x3-37-36-36 : mean={sb['mean']:.3f}s, std={sb['std']:.3f}s, min={sb['min']:.3f}s, max={sb['max']:.3f}s")
    print(f"Route 1 (40x3-39-38-37)   : mean={sr1['mean']:.3f}s, std={sr1['std']:.3f}s, min={sr1['min']:.3f}s, max={sr1['max']:.3f}s")
    print(f"Route 2 (40x4-38x2)       : mean={sr2['mean']:.3f}s, std={sr2['std']:.3f}s, min={sr2['min']:.3f}s, max={sr2['max']:.3f}s")
    print("--- 相比基准的净差 (负数表示提升/缩短) ---")
    print(f"Route 1 vs Base 差值: mean={s_dr1['mean']:.3f}s (std={s_dr1['std']:.3f}s, se={s_dr1['se']:.3f}s)")
    print(f"Route 2 vs Base 差值: mean={s_dr2['mean']:.3f}s (std={s_dr2['std']:.3f}s, se={s_dr2['se']:.3f}s)")

if __name__ == "__main__":
    main()
