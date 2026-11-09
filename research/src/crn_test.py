#!/usr/bin/env python3
"""H3: common-random-numbers sensitivity test on sim_v2 (see experiments/H3-crn-sensitivity/protocol.md)."""
import json
import statistics as st
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/src"))
import sim_v2  # noqa: E402

BASE = dict(queue=400, cc="bbr", bg_rto=0.5, warmup=5.0, start_jitter_ms=20)


def leak(rates):
    return {str(i): ["leak_bucket", {"leak_rate": r, "bucket_cap": r, "leak_interval_us": 4000}]
            for i, r in enumerate(rates, 1)}


S1 = [40, 40, 40, 37, 36, 36]
PERTS = [[41, 40, 40, 37, 36, 36], [40, 39, 40, 37, 36, 36], [40, 40, 40, 36, 36, 36],
         [40, 40, 40, 38, 36, 36], [40, 40, 40, 37, 37, 36], [40, 40, 40, 37, 36, 35]]


def job(a):
    rates, seed, js = a
    r = sim_v2.simulate_run(leak(rates), seed, jitter_seed=js, **BASE)
    return r["total"]


def main(K=6, J=6):
    seeds = list(range(100, 100 + K))
    jobs = {}
    for s in seeds:
        jobs[("base", s, 0)] = (S1, s, 0)
        for j in range(1, J):
            jobs[("rep", s, j)] = (S1, s, j)
        for k, pr in enumerate(PERTS):
            jobs[("pert", s, k)] = (pr, s, 0)
    keys = list(jobs)
    with ProcessPoolExecutor() as pool:
        vals = dict(zip(keys, pool.map(job, [jobs[k] for k in keys])))
    base = [vals[("base", s, 0)] for s in seeds]
    rep_sd = [st.stdev([vals[("base", s, 0)]] + [vals[("rep", s, j)] for j in range(1, J)]) for s in seeds]
    pert_sd = [st.stdev([vals[("base", s, 0)]] + [vals[("pert", s, k)] for k in range(len(PERTS))]) for s in seeds]
    out = {"bg_seed_sd": st.stdev(base), "repeat_sd_mean": st.mean(rep_sd), "pert_sd_mean": st.mean(pert_sd),
           "per_seed": [{"seed": s, "base": vals[("base", s, 0)], "rep_sd": a, "pert_sd": b}
                        for s, a, b in zip(seeds, rep_sd, pert_sd)],
           "raw": {"|".join(map(str, k)): v for k, v in vals.items()}}
    print(f"(a) bg-seed sd       {out['bg_seed_sd']:.2f} s   (base totals {[round(x, 1) for x in base]})")
    print(f"(b) repeat sd        {out['repeat_sd_mean']:.2f} s   per seed {[round(x, 1) for x in rep_sd]}")
    print(f"(c) perturbation sd  {out['pert_sd_mean']:.2f} s   per seed {[round(x, 1) for x in pert_sd]}")
    dest = ROOT / "research/experiments/H3-crn-sensitivity/results/crn.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1), "utf-8")


if __name__ == "__main__":
    main()
