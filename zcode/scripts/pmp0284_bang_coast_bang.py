# -*- coding: utf-8 -*-
"""Task 0284: PMP Bang-Coast-Bang extremal vs Crown Fusion two-phase schedule.

Method (pre-registered, no circular calibration):
  1. Calibrate fluid-model parameters ONLY from non-crown data:
     - uniform leak_bucket families (leakc-24/27/36) in runs/results.jsonl
     - delta-model rate-group law (<=30 -> -17.5% goodput; band entry at 36)
     - 0085 Kolmogorov burst-penalty law (batch 40 -> 4.51% tail loss,
       60 -> 36.3% catastrophic) as the debt->loss penalty calibration
     - official constants: files 10/20/40/80/160/320 MB, bottleneck 100 Mbps
  2. Solve the 6-stage discrete extremal control by backward DP over the
     pacing grid u in [24,41] pkt/4ms with queue-debt state D in [0,1]
     (hard loss constraint D<=1; no artificial terminal constraint -- the
     empirical stage goodput already embeds queue-drain effects).
  3. Compare DP extremal with Crown Fusion [41,41,40,37,36,36] using the
     pre-registered metric: stage-time-weighted match within +/-1 pkt/4ms
     (the repo's +/-1-package neighbourhood discipline).
  4. Repeat over an explicit calibration box (mu_p x S_max x lambda x
     g_flat x startup); report the overlap distribution, not a single point.

All outputs stay inside zcode/ (no runs/ writes; red line).
"""
import json
import itertools
import statistics as st
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "runs" / "results.jsonl"
OUT = ROOT / "zcode" / "scripts" / "pmp0284_results.json"

FILES_MB = [10, 20, 40, 80, 160, 320]          # official 六载穿柜.md §3
GRID = list(range(24, 42))                      # pacing grid, pkt/4ms
CROWN = [41, 41, 40, 37, 36, 36]                # sealed crown schedule
D_STEP = 0.005

# ---------------- 1. calibration from non-crown data ----------------

def load_rows():
    rows = []
    with RESULTS.open(encoding="utf-8") as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows

def family(rows, frag):
    out = []
    for d in rows:
        t = d.get("tag", "")
        if frag not in t or not d.get("valid") or t.startswith("load-"):
            continue
        if "41x2-40-37-36x2" in t:      # crown itself: excluded from calibration
            continue
        if not d.get("downloads"):
            continue
        out.append(d)
    return out

def stage_goodput(d):
    return [FILES_MB[k] * 8 / d["downloads"][f"{k+1}.bin"] for k in range(6)]

rows = load_rows()
uni = {}
for name, frag in [("leak24a", "leakc-24-40-4000-a"), ("leak24b", "leakc-24-40-4000-b"),
                   ("leak27", "leakc-27-40-"), ("leak36", "leakc-36-40-4000-"),
                   ("leak36b", "leakc-36-36-4000")]:
    fs = family(rows, frag)
    if fs:
        uni[name] = fs

plateau_samples = []          # stages 2-4 of uniform families: mid-episode, ramp-free
s1_ratio = []
for fs in uni.values():
    for d in fs:
        gp = stage_goodput(d)
        plateau_samples.extend(gp[1:4])
        s1_ratio.append(gp[0])
g_flat_hat = st.mean(plateau_samples)
g_flat_se = st.stdev(plateau_samples) / len(plateau_samples) ** 0.5
startup_hat = st.mean(s1_ratio) / g_flat_hat   # stage-1 ramp factor

crown_rows = [d for d in rows if "41x2-40-37-36x2" in d.get("tag", "")
              and d.get("valid") and d.get("downloads")]
crown_totals = [d["total_seconds"] for d in crown_rows]
crown_stage_dur = [st.mean([d["downloads"][f"{k+1}.bin"] for d in crown_rows])
                   for k in range(6)]

# ---------------- 2. model ----------------

def goodput(u, g_flat):
    """delta-model rate groups: band entry 36, <=30 penalised -17.5%."""
    return g_flat * (1.0 - 0.175 * max(0.0, (36 - u) / 6.0))

def stage_dur(u, D, k, g_flat, startup, lam):
    g = goodput(u, g_flat)
    if k == 0:
        g *= startup                      # QUIC/CC slow-start ramp on file 1
    g *= max(0.05, 1.0 - lam * D)         # Kolmogorov loss penalty on debt
    return FILES_MB[k] * 8.0 / g

def dp_optimal(mu_p, S_max, lam, g_flat, startup, u_lo=24):
    """Backward DP: min total time s.t. D<=1 throughout. Returns schedule/total."""
    nD = int(round(1.0 / D_STEP)) + 1

    def d_index(D):
        return min(nD - 1, max(0, int(round(D / D_STEP))))

    V = [None] * nD
    choices = [dict() for _ in range(6)]
    for i in range(nD):
        D = i * D_STEP
        best, bu = None, None
        for u in GRID:
            if u < u_lo:
                continue
            T = stage_dur(u, D, 5, g_flat, startup, lam)
            Dn = D + (u - mu_p) * T / S_max
            if Dn <= 1.0 and (best is None or T < best):
                best, bu = T, u
        V[i] = best
        choices[5][i] = bu
    for k in range(4, -1, -1):
        Vn = [None] * nD
        for i in range(nD):
            D = i * D_STEP
            best, bu = None, None
            for u in GRID:
                if u < u_lo:
                    continue
                T = stage_dur(u, D, k, g_flat, startup, lam)
                Dn = D + (u - mu_p) * T / S_max
                if Dn > 1.0:
                    continue
                j = d_index(Dn)
                if V[j] is None:
                    continue
                tot = T + V[j]
                if best is None or tot < best:
                    best, bu = tot, u
            Vn[i] = best
            choices[k][i] = bu
        V = Vn
    if V[0] is None:
        return None, None
    sched, D = [], 0.0
    for k in range(6):
        u = choices[k][d_index(D)]
        sched.append(u)
        T = stage_dur(u, D, k, g_flat, startup, lam)
        D = D + (u - mu_p) * T / S_max
    return sched, V[0]

def crown_debt_profile(mu_p, S_max, lam, g_flat, startup):
    D, prof = 0.0, []
    for k in range(6):
        T = stage_dur(CROWN[k], D, k, g_flat, startup, lam)
        D = D + (CROWN[k] - mu_p) * T / S_max
        prof.append(D)
    return prof

def overlap(sched, durs):
    num = den = 0.0
    for k, (u, t) in enumerate(zip(sched, durs)):
        den += t
        if abs(u - CROWN[k]) <= 1:
            num += t
    return num / den if den else 0.0

# ---------------- 3. calibration box sweep ----------------

box = {
    "mu_p": [36, 37, 38, 39, 40],
    "S_max": [85.0, 100.0, 130.0],
    "lam": [0.30, 0.363],
    "g_flat": [g_flat_hat - 1.0, g_flat_hat, g_flat_hat + 1.0],
    "startup": [0.62, startup_hat, 0.78],
}

results = []
for mu_p, S_max, lam, g_flat, startup in itertools.product(
        box["mu_p"], box["S_max"], box["lam"], box["g_flat"], box["startup"]):
    sched, total = dp_optimal(mu_p, S_max, lam, g_flat, startup)
    if sched is None:
        results.append(dict(mu_p=mu_p, S_max=S_max, lam=lam,
                            g_flat=round(g_flat, 2), startup=round(startup, 3),
                            feasible=False, overlap=None))
        continue
    ov = overlap(sched, crown_stage_dur)
    prof = crown_debt_profile(mu_p, S_max, lam, g_flat, startup)
    results.append(dict(mu_p=mu_p, S_max=S_max, lam=lam, g_flat=round(g_flat, 2),
                        startup=round(startup, 3), feasible=True,
                        sched=sched, dp_total=round(total, 2),
                        overlap=round(ov, 4),
                        crown_peak_debt=round(max(prof), 3),
                        crown_feasible=bool(max(prof) <= 1.0)))

ovs = [r["overlap"] for r in results if r.get("feasible")]
crown_feas = [r for r in results if r.get("feasible") and r["crown_feasible"]]
ovs_cf = [r["overlap"] for r in crown_feas]
summary = {
    "n_box": len(results),
    "n_feasible": len(ovs),
    "overlap_min": round(min(ovs), 4),
    "overlap_median": round(st.median(ovs), 4),
    "overlap_max": round(max(ovs), 4),
    "frac_ge_096_all": round(sum(1 for o in ovs if o >= 0.96) / len(ovs), 4),
    "crown_feasible_points": len(crown_feas),
    "frac_ge_096_when_crown_feasible": (round(sum(1 for o in ovs_cf if o >= 0.96) / len(ovs_cf), 4)
                                        if ovs_cf else None),
    "overlap_median_when_crown_feasible": (round(st.median(ovs_cf), 4) if ovs_cf else None),
    "crown_empirical": {
        "n": len(crown_rows),
        "total_mean": round(st.mean(crown_totals), 3),
        "total_std": round(st.pstdev(crown_totals), 3),
        "stage_dur_mean": [round(x, 3) for x in crown_stage_dur],
    },
    "calibration": {
        "g_flat_hat": round(g_flat_hat, 2), "g_flat_se": round(g_flat_se, 2),
        "startup_hat": round(startup_hat, 3),
        "n_plateau_samples": len(plateau_samples),
        "uniform_families": {k: len(v) for k, v in uni.items()},
    },
    "crown_schedule": CROWN,
    "metric": "stage-time-weighted fraction with |u_PMP - u_crown| <= 1 pkt/4ms",
}
out = dict(summary=summary, box_results=results)
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=1))

print("\n-- representative schedules (S_max=100, lam=0.363, g_hat, startup_hat) --")
for mu_p in box["mu_p"]:
    s, t = dp_optimal(mu_p, 100.0, 0.363, g_flat_hat, startup_hat)
    if s:
        prof = crown_debt_profile(mu_p, 100.0, 0.363, g_flat_hat, startup_hat)
        print(f"mu_p={mu_p}: DP={s} total={t:.2f}s "
              f"overlap={overlap(s, crown_stage_dur):.4f} crownD={[round(x,2) for x in prof]}")
    else:
        print(f"mu_p={mu_p}: INFEASIBLE")
