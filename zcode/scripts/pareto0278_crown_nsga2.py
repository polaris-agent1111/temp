#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0278: 6-stage file-transfer completion-time Pareto front via NSGA-II.

Surrogate model (all anchors from repo, no external data):
  - Stage sizes MB: harness/run_experiment.py:34  SIZES_MB = 10/20/40/80/160/320
  - Link: 100 Mbps = 12.5 MB/s (harness/run_experiment.py:35)
  - Packet 1200 B, tick G = 4000 us -> rate r [pkt/tick] = r * 2.4 Mbps = r * 0.3 MB/s
  - Local per-stage time model:
        T_loc_i(r) = size_i/(0.3 r) + c0 + q * size_i * max(0, u_i - u*)^gamma
    where u_i = 2.4 r / 100 (link utilization). The (u_i - u*)^gamma term models
    shallow-buffer loss/PTO recovery volume (docs 0085 burst-penalty law).
    (c0, q, u*, gamma) are calibrated by least squares on 7 real local anchors
    from docs/analysis/delta-model.md section 1 (uniform-rate configs).
  - Official prediction (delta-model.md form B, rate+cap, LOOCV MAE 2.9pp):
        delta_hat(r, cap) = 0.2510 - 0.0099 r + 0.0037 cap
        T_off_i = T_loc_i * (1 + delta_hat(r_i, cap_i)),  baseline cap_i = r_i

Objectives (minimize both):
    f1(r) = sum_i T_off_i                     [predicted official seconds]
    f2(r) = sum_i size_i * max(0, u_i - u*)^gamma   [volume-at-risk, MB]

Decision space: r_i in {20..41} integer. r=41 -> 98.4 Mbps < 100 Mbps link;
r >= 42 exceeds the physical link and is excluded as infeasible.

Verification: NSGA-II (pop 240, 1000 generations, seed 1108) over the full box,
plus EXACT exhaustive Pareto front over the high-rate sub-box r_i in {34..41}
(8^6 = 262144 points) to remove evolutionary noise from the membership claim.

Output is stdout only; nothing is written outside zcode/.
"""
import sys
import itertools
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

SIZES = np.array([10.0, 20.0, 40.0, 80.0, 160.0, 320.0])  # MB
PKT_MBPS = 2.4          # Mbps per pkt/tick (1200 B / 4 ms)
LINK_MBPS = 100.0
R_MIN, R_MAX = 20, 41

# 7 real local anchors (uniform-rate configs), docs/analysis/delta-model.md §1
ANCHORS = [(24, 123.13), (27, 123.41), (30, 121.83), (36, 130.32),
           (40, 126.75), (42, 131.00), (44, 135.67)]


def calibrate():
    """Grid-search (u*, gamma); linear least-squares for (c0_per_stage, q).

    Design matrix row = [6, risk_total]: the per-stage overhead c0 enters the
    uniform-rate local total as 6*c0, so the coefficient is per-stage.
    """
    best = None
    for u_star in (0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80):
        for gamma in (1, 2, 3, 4, 5, 6):
            A = []
            y = []
            for r, loc in ANCHORS:
                u = PKT_MBPS * r / LINK_MBPS
                total_transfer = sum(SIZES) / (0.3 * r)
                risk = sum(SIZES) * max(0.0, u - u_star) ** gamma
                A.append([6.0, risk])
                y.append(loc - total_transfer)
            A = np.array(A)
            y = np.array(y)
            coef, *_ = np.linalg.lstsq(A, y, rcond=None)
            pred = A @ coef
            sse = float(np.sum((pred - y) ** 2))
            if best is None or sse < best[0]:
                best = (sse, u_star, gamma, float(coef[0]), float(coef[1]))
    sse, u_star, gamma, c0, q = best
    sst = float(np.sum((np.array([a[1] for a in ANCHORS])
                        - np.mean([a[1] for a in ANCHORS])) ** 2))
    r2 = 1.0 - sse / sst
    return {"u_star": u_star, "gamma": gamma, "c0": c0, "q": q,
            "sse": sse, "r2": r2}


def calibrate_top3():
    """Return the 3 best (u*, gamma) grid combos by SSE (for robustness)."""
    combos = []
    for u_star in (0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80):
        for gamma in (1, 2, 3, 4, 5, 6):
            A = []
            y = []
            for r, loc in ANCHORS:
                u = PKT_MBPS * r / LINK_MBPS
                total_transfer = sum(SIZES) / (0.3 * r)
                risk = sum(SIZES) * max(0.0, u - u_star) ** gamma
                A.append([6.0, risk])
                y.append(loc - total_transfer)
            A = np.array(A)
            y = np.array(y)
            coef, *_ = np.linalg.lstsq(A, y, rcond=None)
            sse = float(np.sum((A @ coef - y) ** 2))
            combos.append((sse, u_star, gamma, float(coef[0]), float(coef[1])))
    combos.sort()
    return combos[:3]


CAL = calibrate()


def local_stage_times(rates):
    r = np.asarray(rates, dtype=float)
    u = PKT_MBPS * r / LINK_MBPS
    transfer = SIZES / (0.3 * r)
    risk = np.maximum(0.0, u - CAL["u_star"]) ** CAL["gamma"]
    return transfer + CAL["c0"] + CAL["q"] * SIZES * risk


def delta_hat(r, cap):
    return 0.2510 - 0.0099 * r + 0.0037 * cap


def objectives(pop, cap_mode="cap_eq_r"):
    """pop: (N,6) int array. Returns (f1, f2)."""
    r = pop.astype(float)
    if cap_mode == "cap_eq_r":
        cap = r
    elif cap_mode == "cap_plus":
        cap = r + 4.0
    else:
        raise ValueError(cap_mode)
    t_loc = local_stage_times(pop)
    t_off = t_loc * (1.0 + delta_hat(r, cap))
    u = PKT_MBPS * r / LINK_MBPS
    f1 = t_off.sum(axis=1)
    f2 = (SIZES * np.maximum(0.0, u - CAL["u_star"]) ** CAL["gamma"]).sum(axis=1)
    return f1, f2


# ---------------- NSGA-II core ----------------
def nondominated_sort(F):
    """M=2 fast non-dominated sort, O(n log n).

    Sort by (f1 asc, f2 asc); every dominator of a point precedes it in that
    order, so its rank is final at insert time.  Maintain the ascending list
    `mins[k]` = min f2 among processed points of front k.  A point p is
    dominated by front k iff mins[k] < f2_p, hence
        rank_p = 1 + #{k : mins[k] < f2_p}   (= bisect_left(mins, f2_p)).
    Inserting into front j only can lower mins[j] to f2_p, but j is the LAST
    front with min < f2_p under the ascending prefix property, so
    mins[j] < f2_p already held and the list stays ascending.
    """
    import bisect
    n = F.shape[0]
    order = np.lexsort((F[:, 1], F[:, 0]))
    rank = np.empty(n, dtype=int)
    fronts: list[list[int]] = []
    mins: list[float] = []
    for idx in order:
        f1p, f2p = F[idx, 0], F[idx, 1]
        j = bisect.bisect_left(mins, f2p)
        if j == len(mins):
            mins.append(f2p)
            fronts.append([])
        elif f2p < mins[j]:
            mins[j] = f2p
        rank[idx] = j
        fronts[j].append(int(idx))
    return fronts


def crowding_distance(F, front):
    m = len(front)
    d = np.zeros(m)
    if m <= 2:
        d[:] = np.inf
        return d
    for k in range(F.shape[1]):
        order = np.argsort(F[front, k])
        d[order[0]] = d[order[-1]] = np.inf
        span = F[front[order[-1]], k] - F[front[order[0]], k]
        if span == 0:
            continue
        for j in range(1, m - 1):
            d[order[j]] += (F[front[order[j + 1]], k]
                            - F[front[order[j - 1]], k]) / span
    return d


def nsga2(pop_size=240, gens=1000, seed=1108, cap_mode="cap_eq_r"):
    rng = np.random.default_rng(seed)
    lo, hi = R_MIN, R_MAX
    pop = rng.integers(lo, hi + 1, size=(pop_size, 6))
    F = np.column_stack(objectives(pop, cap_mode))

    def assign_rank_crowd(pop, F):
        fronts = nondominated_sort(F)
        rank = np.empty(len(pop), dtype=int)
        for k, fr in enumerate(fronts):
            rank[fr] = k
        crowd = np.zeros(len(pop))
        for fr in fronts:
            crowd[fr] = crowding_distance(F, fr)
        return rank, crowd

    rank, crowd = assign_rank_crowd(pop, F)
    for gen in range(gens):
        # binary tournament on (rank, crowding)
        idx = rng.integers(0, pop_size, size=(pop_size, 2))
        a, b = idx[:, 0], idx[:, 1]
        take_a = (rank[a] < rank[b]) | ((rank[a] == rank[b]) & (crowd[a] >= crowd[b]))
        winners = np.where(take_a, a, b)
        parents = pop[winners]
        cross = rng.random((pop_size, 6)) < 0.9
        mates = parents[rng.permutation(pop_size)]
        child = np.where(cross, parents, mates)
        mut = rng.random((pop_size, 6)) < 1.0 / 6
        step = rng.integers(-3, 4, size=(pop_size, 6))
        child = np.clip(child + np.where(mut, step, 0), lo, hi)
        # merge and truncate elitistically
        merged = np.vstack([pop, child])
        Fm = np.column_stack(objectives(merged, cap_mode))
        fronts = nondominated_sort(Fm)
        new = []
        for fr in fronts:
            if len(new) + len(fr) <= pop_size:
                new.extend(fr)
            else:
                cd = crowding_distance(Fm, fr)
                order = np.argsort(-cd)
                new.extend([fr[j] for j in order[: pop_size - len(new)]])
                break
        pop = merged[new]
        F = Fm[new]
        rank, crowd = assign_rank_crowd(pop, F)
    return pop, F


def exact_front(box_lo, box_hi, cap_mode="cap_eq_r"):
    """Exact Pareto front by exhaustive enumeration over the box.

    Same O(n log n) bisect sweep as nondominated_sort: points arrive in
    (f1 asc, f2 asc) order, every dominator precedes its dominated point,
    and a point is on the true front iff at its arrival no front has a
    smaller min-f2 (bisect_left(mins, f2_p) == 0).
    """
    import bisect
    grids = np.array(list(itertools.product(range(box_lo, box_hi + 1), repeat=6)))
    f1, f2 = objectives(grids, cap_mode)
    F = np.column_stack([f1, f2])
    order = np.lexsort((F[:, 1], F[:, 0]))
    mins: list[float] = []
    keep_idx = []
    for idx in order:
        j = bisect.bisect_left(mins, F[idx, 1])
        if j == 0:
            keep_idx.append(int(idx))
        if j == len(mins):
            mins.append(F[idx, 1])
        elif F[idx, 1] < mins[j]:
            mins[j] = F[idx, 1]
    return grids[keep_idx], F[keep_idx]


CROWN = np.array([41, 41, 40, 37, 36, 36])
CROWN_ALT = np.array([41, 41, 41, 37, 36, 36])   # 0272 doc variant
SHOT1 = np.array([40, 40, 40, 37, 36, 36])       # master-plan shot1


def eval_named(name, vec, cap_mode="cap_eq_r"):
    f1, f2 = objectives(vec.reshape(1, -1), cap_mode)
    return float(f1[0]), float(f2[0])


def dominates(a_f, b_f):
    """a dominates b (minimization)."""
    return bool(np.all(a_f <= b_f) and np.any(a_f < b_f))


def main():
    global CAL
    print("=== Task 0278: NSGA-II Pareto front, 6-dim rate space ===")
    print(f"calibration: u*={CAL['u_star']}, gamma={CAL['gamma']}, "
          f"c0={CAL['c0']:.3f}s, q={CAL['q']:.5f}, SSE={CAL['sse']:.2f}, "
          f"R2={CAL['r2']:.4f}")
    # per-anchor fit residuals (honesty check)
    for r, loc in ANCHORS:
        t = local_stage_times(np.full(6, r)).sum()
        print(f"  anchor uniform r={r}: model local {t:.2f}s vs real {loc:.2f}s "
              f"(res {t - loc:+.2f}s)")

    cap_mode = "cap_eq_r"
    pop, F = nsga2(cap_mode=cap_mode)
    fronts = nondominated_sort(F)
    rank0 = pop[fronts[0]]
    rank0F = F[fronts[0]]
    distinct_obj = len(np.unique(np.round(rank0F, 9), axis=0))
    print(f"\nNSGA-II: pop=240 gens=1000 seed=1108, final rank-0 size={len(rank0)} "
          f"(distinct objective pairs: {distinct_obj})")

    named = {"crown(41,41,40,37,36,36)": CROWN,
             "crown-alt(41,41,41,37,36,36)": CROWN_ALT,
             "shot1(40,40,40,37,36,36)": SHOT1,
             "uniform30": np.full(6, 30), "uniform36": np.full(6, 36),
             "uniform40": np.full(6, 40), "uniform41": np.full(6, 41)}
    print("\nnamed points (f1=predicted official s, f2=MB-at-risk):")
    namedF = {}
    for name, vec in named.items():
        f1, f2 = eval_named(name, vec, cap_mode)
        namedF[name] = (f1, f2)
        print(f"  {name:32s} f1={f1:8.3f}  f2={f2:9.3f}")

    # exact front over the rate region that contains all named points
    BOX_LO = 30
    grids, GF = exact_front(BOX_LO, 41, cap_mode)
    print(f"\nEXACT Pareto front over r_i in [{BOX_LO},41]^6: {len(grids)} points")
    print("named-point verdicts against the EXACT front:")
    for name, vec in named.items():
        member = any(np.array_equal(vec, row) for row in grids)
        f = np.array(namedF[name])
        doms = [g for g, gf in zip(grids, GF) if dominates(gf, f)]
        in_pop = any(np.array_equal(vec, row) for row in pop)
        ndom_pop = int(np.sum(np.all(F <= f, axis=1) & np.any(F < f, axis=1)))
        dom_str = "; ".join(str(list(int(x) for x in d)) for d in doms[:3]) \
            if doms else "-"
        print(f"  {name:32s} exact-front={member}  in-final-pop={in_pop} "
              f"dominated-by-pop-count={ndom_pop}")
        if doms:
            print(f"      dominated by (front): {dom_str}")

    # robustness: exact-front membership across cap sensitivity
    print("\nrobustness: crown exact-front membership under perturbations")
    for label, cm in [("cap=r (baseline)", "cap_eq_r"), ("cap=r+4", "cap_plus")]:
        grids2, GF2 = exact_front(BOX_LO, 41, cm)
        for name in ("crown(41,41,40,37,36,36)", "crown-alt(41,41,41,37,36,36)"):
            vec = named[name]
            f = np.array(eval_named(name, vec, cm))
            member = any(np.array_equal(vec, row) for row in grids2)
            ndoms = sum(1 for gf in GF2 if dominates(gf, f))
            print(f"  {label:18s} {name:32s} exact-front={member} "
                  f"dominators={ndoms}")

    # calibration-variant robustness: crown membership under top-3 (u*, gamma)
    print("\nrobustness: crown membership under top-3 calibration variants")
    saved = dict(CAL)
    for k, (sse, u_star, gamma, c0, q) in enumerate(calibrate_top3()):
        CAL = {"u_star": u_star, "gamma": gamma, "c0": c0, "q": q,
               "sse": sse, "r2": None}
        g3, GF3 = exact_front(BOX_LO, 41, "cap_eq_r")
        for name in ("crown(41,41,40,37,36,36)", "crown-alt(41,41,41,37,36,36)"):
            f = np.array(eval_named(name, named[name], "cap_eq_r"))
            member = any(np.array_equal(named[name], row) for row in g3)
            ndoms = sum(1 for gf in GF3 if dominates(gf, f))
            print(f"  variant{k+1} u*={u_star:.2f} gamma={gamma} SSE={sse:.1f}: "
                  f"{name:32s} exact-front={member} dominators={ndoms}")
    CAL = saved

    # gates
    crown_in_exact = any(np.array_equal(CROWN, row) for row in grids)
    crownalt_in_exact = any(np.array_equal(CROWN_ALT, row) for row in grids)
    shot1_in_exact = any(np.array_equal(SHOT1, row) for row in grids)
    print("\nGATES (honest):")
    print(f"  G1 crown in EXACT front r_i in [{BOX_LO},41]^6: {crown_in_exact}")
    print(f"  G2 crown-alt in EXACT front: {crownalt_in_exact}")
    print(f"  G3 shot1 in EXACT front: {shot1_in_exact}")
    print(f"  G4 exact front non-degenerate (>=2 distinct f2): "
          f"{len(set(np.round(GF[:, 1], 9))) >= 2}")
    print(f"  G5 surrogate calibration R2 >= 0.5: {CAL['r2'] >= 0.5} "
          f"(R2={CAL['r2']:.4f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
