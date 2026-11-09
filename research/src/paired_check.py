#!/usr/bin/env python3
"""Paired-seed sim_v2 comparison of candidate configs vs a reference (qualitative sanity check only).

python research/src/paired_check.py REF.json CAND1.json [CAND2.json ...] --seeds 16
"""
import argparse
import json
import statistics as st
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sim_v2  # noqa: E402

B = dict(queue=400, cc="bbr", bg_rto=0.5, warmup=5.0, start_jitter_ms=20)
CFGS = {}


def job(a):
    name, path, s = a
    r = sim_v2.simulate_run(json.loads(Path(path).read_text("utf-8")), s, **B)
    return r["total"], r["per_file"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--seeds", type=int, default=16)
    ap.add_argument("--seed0", type=int, default=200)
    a = ap.parse_args()
    seeds = range(a.seed0, a.seed0 + a.seeds)
    names = [Path(f).stem for f in a.files]
    keys = [(n, f, s) for n, f in zip(names, a.files) for s in seeds]
    with ProcessPoolExecutor() as p:
        v = dict(((k[0], k[2]), r) for k, r in zip(keys, p.map(job, keys)))
    ref = names[0]
    for n in names:
        tot = [v[(n, s)][0] for s in seeds]
        dd = [v[(n, s)][0] - v[(ref, s)][0] for s in seeds]
        pf = [st.mean(v[(n, s)][1][i] for s in seeds) for i in range(6)]
        se = st.stdev(dd) / len(dd) ** 0.5 if n != ref else 0.0
        print(f"{n:28s} mean {st.mean(tot):6.1f}  paired diff vs {ref} {st.mean(dd):+6.2f} +- {se:.2f} (se)  "
              + "/".join(f"{x:.1f}" for x in pf))


if __name__ == "__main__":
    main()
