#!/usr/bin/env python3
"""How much of an official score difference is noise?

1. Repeat noise: identical configs submitted more than once (ours and other teams', from the docs).
2. Config-to-config noise: residual sd of a smooth quadratic-in-rate fit to the uniform leak_bucket
   4000 us points (a model with no per-config freedom; residual sd is an upper bound on noise).
3. Significance of the staircase comparisons S1/S2/S3 under those noise levels.
"""
import json
import math
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# identical-config official repeats (docs: timer-granularity.md, bottleneck-and-40shot-plan.md)
REPEATS = {
    "ours v1/v1b leak9/30/1000": [245.995, 243.9583],
    "大肥鱼 same config x4 (11-05/06)": [129.5917, 128.9750, 129.8170, 129.2400],
}


def pooled_cv(groups):
    num = den = 0
    for xs in groups.values():
        m = st.mean(xs)
        num += sum(((x - m) / m) ** 2 for x in xs)
        den += len(xs) - 1
    return math.sqrt(num / den)


def ols(X, y):
    # normal equations, tiny k
    k = len(X[0])
    A = [[sum(r[i] * r[j] for r in X) for j in range(k)] for i in range(k)]
    b = [sum(r[i] * yy for r, yy in zip(X, y)) for i in range(k)]
    for i in range(k):
        p = max(range(i, k), key=lambda r: abs(A[r][i]))
        A[i], A[p] = A[p], A[i]
        b[i], b[p] = b[p], b[i]
        for r in range(k):
            if r != i:
                f = A[r][i] / A[i][i]
                A[r] = [a - f * c for a, c in zip(A[r], A[i])]
                b[r] -= f * b[i]
    return [b[i] / A[i][i] for i in range(k)]


def main():
    out = {}
    cv = pooled_cv(REPEATS)
    out["repeat_cv"] = cv
    print("repeat noise (identical config, 3-run official average):")
    for k, xs in REPEATS.items():
        print(f"  {k}: mean {st.mean(xs):.2f}  sd {st.stdev(xs):.2f}  cv {st.stdev(xs) / st.mean(xs):.2%}")
    print(f"  pooled CV {cv:.2%}  -> sd at 122 s = {cv * 122:.2f} s")

    pts = json.loads((ROOT / "research/data/official_points.json").read_text("utf-8"))["points"]
    U = []
    for p in pts:
        c = p["cfg"].get("all")
        if c and c[0] == "leak_bucket" and c[1]["leak_interval_us"] == 4000:
            U.append((c[1]["leak_rate"], c[1]["bucket_cap"], st.mean(p["official"])))
    X = [[1, r, r * r, cap] for r, cap, _ in U]
    y = [t for *_, t in U]
    beta = ols(X, y)
    res = [t - sum(b * x for b, x in zip(beta, row)) for row, t in zip(X, y)]
    dof = len(U) - len(beta)
    s_res = math.sqrt(sum(e * e for e in res) / dof)
    out["ufit"] = {"beta": beta, "n": len(U), "resid_sd": s_res}
    print(f"\nU-fit T = a + b*rate + c*rate^2 + d*cap on {len(U)} uniform 4000us points: "
          f"beta={[round(b, 4) for b in beta]}  residual sd = {s_res:.2f} s (dof {dof})")

    S1, S2, S3 = 122.0463, 124.6603, 124.7830
    for name, sd in [("repeat-only", cv * 123), ("fit-residual", s_res)]:
        sdd = sd * math.sqrt(2)
        print(f"\nnoise model {name}: sd per score {sd:.2f} s, sd of a difference {sdd:.2f} s")
        for lab, d in [("S2-S1 (41 on dirs 1-2)", S2 - S1), ("S3-S1 (pert)", S3 - S1),
                       ("uniform36/40 - S1", 133.086 - S1)]:
            z = d / sdd
            p = math.erfc(abs(z) / math.sqrt(2))
            print(f"  {lab:26s} diff {d:+6.2f} s  z={z:5.2f}  two-sided p={p:.3f}")
        out[name] = {"sd": sd}
    print("\nminimum detectable difference (2 sd of a difference): "
          f"{2 * cv * 123 * math.sqrt(2):.1f} s (repeat-only) .. {2 * s_res * math.sqrt(2):.1f} s (fit residual)")
    dest = ROOT / "research/experiments/H2-official-noise/results/noise.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2), "utf-8")


if __name__ == "__main__":
    main()
