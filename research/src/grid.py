#!/usr/bin/env python3
"""Run fidelity.score over a grid of simulator options and write a CSV + JSON summary.

python research/src/grid.py --sim v2 --seeds 24 --out research/experiments/H1-sim2-mechanistic/results/grid1 \
    --axis queue=40,120,400 --axis bg_rto=0.5,1.0 --axis warmup=5,30 --axis lat=0,1000
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fidelity import parse_opts, score  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", default="v2")
    ap.add_argument("--seeds", type=int, default=24)
    ap.add_argument("--seed0", type=int, default=42)
    ap.add_argument("--axis", action="append", required=True)
    ap.add_argument("--fixed", action="append")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    axes = []
    for ax in a.axis:
        k, vals = ax.split("=", 1)
        axes.append([(k, v) for v in vals.split(",")])
    fixed = parse_opts(a.fixed)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for combo in itertools.product(*axes):
        opts = dict(fixed)
        opts.update(parse_opts([f"{k}={v}" for k, v in combo]))
        r = score(a.sim, a.seeds, a.seed0, opts, verbose=False)
        byid = {p["id"]: p for p in r["points"]}
        row = {**{k: v for k, v in opts.items()}, "loo_rmse": round(r["loo_rmse"], 3), "rmse": round(r["rmse"], 3),
               "spearman": round(r["spearman"], 3), "stair_gap": round(r["stair_gap"], 2),
               "trap": round(r["trap_pred"], 1), "offset": round(r["offset"], 2),
               "left_wall": round(byid["leak24_60"]["pred"] - byid["leak36_40"]["pred"], 2),
               "raw36_40": round(byid["leak36_40"]["pred"] - r["offset"], 2),
               "pf36_40": "/".join(f"{x:.1f}" for x in byid["leak36_40"]["per_file"])}
        rows.append((row, r))
        print(json.dumps(row), flush=True)
    keys = list(rows[0][0].keys())
    with open(out.with_suffix(".csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for row, _ in rows:
            w.writerow(row)
    out.with_suffix(".json").write_text(json.dumps([r for _, r in rows], indent=1, ensure_ascii=False), "utf-8")


if __name__ == "__main__":
    main()
