#!/usr/bin/env python3
"""Score an offline simulator against the official calibration points.

Usage:
  python research/src/fidelity.py --sim v1 --seeds 100
  python research/src/fidelity.py --sim v2 --seeds 60 --opt queue=40 --opt cc=bbr

Metric (locked in research/experiments/H0-baseline-fidelity/protocol.md):
  primary   = LOO-RMSE of offset-corrected predictions over the gated official points
  secondary = Spearman rho, and the staircase gap  pred(S1) - pred(leak36_40)  (official: -11.04 s)
"""
from __future__ import annotations

import argparse
import importlib
import json
import math
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "local-eval" / "tools"))
sys.path.insert(0, str(ROOT / "research" / "src"))

POINTS_FILE = ROOT / "research" / "data" / "official_points.json"
# v1 trap is used as a gate (must be > 200 s), not in RMSE: its magnitude is dominated by the
# timer model and would swamp the residuals of the interesting 120-150 s region.
GATE_ONLY = {"v1_leak9_1000"}


def expand(cfg):
    if "all" in cfg:
        return {str(i): cfg["all"] for i in range(1, 7)}
    return {str(k): v for k, v in cfg.items()}


def load_points():
    data = json.loads(POINTS_FILE.read_text("utf-8"))
    out = []
    for p in data["points"]:
        out.append({"id": p["id"], "target": statistics.mean(p["official"]), "cfg": expand(p["cfg"])})
    return out


def _sim_backend(name):
    if name == "v1":
        mod = importlib.import_module("offline_pacer_sim")

        def run(cfg, seed, opts):
            r = mod.simulate_run(cfg, seed, opts.get("regime", "official"), opts.get("cc", "cubic"))
            return r["total"], r["per_file"], r["valid"]
        return run
    mod = importlib.import_module(f"sim_{name}")

    def run(cfg, seed, opts):
        r = mod.simulate_run(cfg, seed, **opts)
        return r["total"], r["per_file"], r["valid"]
    return run


def _job(args):
    sim, cfg, seed, opts = args
    return _sim_backend(sim)(cfg, seed, opts)


def evaluate_cfg(sim, cfg, seeds, seed0, opts, pool):
    jobs = [(sim, cfg, s, opts) for s in range(seed0, seed0 + seeds)]
    res = list(pool.map(_job, jobs, chunksize=max(1, seeds // 32)))
    tot = [r[0] for r in res if r[2]]
    pf = [statistics.mean(r[1][i] for r in res if r[2]) for i in range(6)] if tot else [None] * 6
    return {"mean": statistics.mean(tot) if tot else float("inf"),
            "std": statistics.stdev(tot) if len(tot) > 1 else 0.0,
            "n": len(tot), "per_file": pf}


def spearman(a, b):
    def ranks(x):
        order = sorted(range(len(x)), key=lambda i: x[i])
        r = [0.0] * len(x)
        for k, i in enumerate(order):
            r[i] = k
        return r
    ra, rb = ranks(a), ranks(b)
    ma, mb = statistics.mean(ra), statistics.mean(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return num / den if den else 0.0


def score(sim, seeds, seed0, opts, workers=None, verbose=True):
    pts = load_points()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for p in pts:
            p["sim"] = evaluate_cfg(sim, p["cfg"], seeds, seed0, opts, pool)
    fit = [p for p in pts if p["id"] not in GATE_ONLY]
    resid = [p["target"] - p["sim"]["mean"] for p in fit]
    offset = statistics.mean(resid)
    loo = []
    for i, p in enumerate(fit):
        off_i = statistics.mean(r for j, r in enumerate(resid) if j != i)
        loo.append(p["target"] - (p["sim"]["mean"] + off_i))
    rmse = math.sqrt(statistics.mean((r - offset) ** 2 for r in resid))
    loo_rmse = math.sqrt(statistics.mean(e * e for e in loo))
    rho = spearman([p["target"] for p in fit], [p["sim"]["mean"] for p in fit])
    byid = {p["id"]: p for p in pts}
    gap = byid["S1_stair_40x3_37_36x2"]["sim"]["mean"] - byid["leak36_40"]["sim"]["mean"]
    trap = byid["v1_leak9_1000"]["sim"]["mean"] + offset
    out = {"sim": sim, "opts": opts, "seeds": seeds, "offset": offset, "rmse": rmse,
           "loo_rmse": loo_rmse, "spearman": rho, "stair_gap": gap, "stair_gap_official": -11.04,
           "trap_pred": trap, "trap_gate": trap > 200,
           "points": [{"id": p["id"], "target": p["target"], "pred": p["sim"]["mean"] + offset,
                       "sim_std": p["sim"]["std"], "n": p["sim"]["n"],
                       "per_file": p["sim"]["per_file"]} for p in pts]}
    if verbose:
        print(f"sim={sim} opts={opts} seeds={seeds} offset={offset:+.2f}")
        print(f"{'point':28} {'target':>8} {'pred':>8} {'err':>7} {'std':>6}  per_file")
        for q in out["points"]:
            pf = "/".join(f"{x:.1f}" for x in q["per_file"]) if q["per_file"][0] is not None else "-"
            print(f"{q['id']:28} {q['target']:8.2f} {q['pred']:8.2f} {q['pred'] - q['target']:+7.2f} {q['sim_std']:6.2f}  {pf}")
        print(f"RMSE={rmse:.2f}  LOO-RMSE={loo_rmse:.2f}  spearman={rho:.3f}  "
              f"stair_gap={gap:+.2f} (official -11.04)  trap={trap:.1f} gate={'PASS' if trap > 200 else 'FAIL'}")
    return out


def parse_opts(items):
    opts = {}
    for it in items or []:
        k, v = it.split("=", 1)
        try:
            v = int(v)
        except ValueError:
            try:
                v = float(v)
            except ValueError:
                pass
        opts[k] = v
    return opts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", default="v1")
    ap.add_argument("--seeds", type=int, default=100)
    ap.add_argument("--seed0", type=int, default=42)
    ap.add_argument("--opt", action="append")
    ap.add_argument("--workers", type=int)
    ap.add_argument("--json-out")
    a = ap.parse_args()
    out = score(a.sim, a.seeds, a.seed0, parse_opts(a.opt), a.workers)
    if a.json_out:
        Path(a.json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json_out).write_text(json.dumps(out, indent=2, ensure_ascii=False), "utf-8")


if __name__ == "__main__":
    main()
