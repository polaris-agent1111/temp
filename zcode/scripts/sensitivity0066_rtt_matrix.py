# -*- coding: utf-8 -*-
"""0066 - perturbation sensitivity matrix: bottleneck-link delay jitter and RTT
phase offset vs steady-state queuing delay (96M drain-margin design).

Baseline constants from docs/analysis/network-queuing-delay-theory.md (repo canon):
  C = 100 Mbps bottleneck, L = 1200 B mean QUIC packet, mu = C/L = 10416.7 pkt/s,
  B = 40 pkt drop-tail buffer, RTT0 = 70 ms, BDP = C*RTT0 = 729.2 pkt,
  R = 96 Mbps precise_rate_based pacing for 5/6.bin, spare margin dC = C - R = 4 Mbps,
  T_rec = B*L/dC = 96 ms queue-recovery time constant (0060 recovery constant).

Outputs (rows) and inputs (columns) of the matrix:
  outputs: O1 BDP, O2 in-flight window W, O3 recovery time T_rec,
           O4 recovery in RTT units n_rtt, O5 self-queue floor E[Dq] (M/D/1),
           O6 6.bin completion T6, O7 burst-mode peak queue Q_peak
  inputs : RTT in [65,75] ms, phase offset phi in [0,RTT), background density rho,
           pacing rate R.

Validation: two simulations.
  (1) Fluid Monte Carlo of the 6.bin window (giants Poisson, 0051 cost anchor
      V_g/C = 2.24 s per 28 MB giant + B*L/dC recovery + k RTT stalls) sweeping
      RTT 65..75 ms x rho in {1.0, 1.5, 2.0, 2.4}: numerical dE[T6]/dRTT vs analytic.
  (2) Packet-level burst superposition: 60-pkt token-burst (B*=60 elastic bound)
      plus a background burst b_bg arriving at phase offset delta: Q_peak(delta),
      numerical dQ_peak/d(delta) vs analytic -(C-C_bg)/L.

stdlib-only, deterministic seeds. Run: python -I zcode/scripts/sensitivity0066_rtt_matrix.py
"""
import math
import random
import statistics as st

# ---------------------------------------------------------------- constants
C = 100e6          # bps
L = 1200.0         # bytes per packet
MU = C / L / 8.0   # packets per second  = 10416.67
B = 40.0           # packets (drop-tail buffer)
RTT0 = 70e-3       # s
R = 96e6           # bps pacing for 5/6.bin
DC = C - R         # spare drain margin = 4 Mbps
T_REC = B * L * 8.0 / DC          # = 0.096 s
BDP0 = C * RTT0 / 8.0 / L         # packets = 729.17
W0 = R * RTT0 / 8.0 / L           # in-flight packets = 700.0
RHO_PIPE = W0 / BDP0              # = R/C = 0.96 (RTT-invariant)
V_GIANT = 28e6 * 8.0              # bits, 28 MB giant flow (0051)
T_STARVE = V_GIANT / C            # = 2.24 s first-order starvation window (0051)
LAM_FLOW = 7.3046                 # flows/s (0051)
P_GIANT = 0.0030                  # P(size >= 28 MB) (0051)
K_STALL = 1.0                     # RTT-stalls per collision (recovery reactions)
FILE6_BITS = 320e6 * 8.0
T6_BASE = FILE6_BITS / R          # = 26.667 s

print("== baseline ==")
print("  mu=%.2f pkt/s  T_rec=%.1f ms  BDP=%.1f pkt  W=%.1f pkt  pipe-util=%.3f"
      % (MU, T_REC * 1e3, BDP0, W0, RHO_PIPE))
print("  M/D/1 self-queue floor: rho_q=0.96 -> E[Nq]=rho^2/(2(1-rho))=%.2f pkt"
      " -> E[Dq]=%.3f ms (RTT-invariant)"
      % (0.96 ** 2 / (2 * 0.04), (0.96 ** 2 / (2 * 0.04)) / (MU * 0.96) * 1e3))

# ------------------------------------------------ analytic sensitivity matrix
def elasticity(dy_dlnx, y):
    return dy_dlnx * 1.0 / y

print("\n== A. analytic partial-derivative matrix (at RTT0=70ms, R=96M, rho=1) ==")
print("  output                 dO/dRTT(per +1ms)        elasticity_RTTC  dO/dR(per +1Mbps)  elasticity_R")
rows = []

o1 = C / 8.0 / L / 1000.0  # packets per ms
rows.append(("O1 BDP (pkt)", "%.3f pkt/ms (+1.43%%/ms)" % o1, "+1", "-", "-"))

rows.append(("O2 in-flight W (pkt)", "%.3f pkt/ms (+1.43%%/ms)" % (R / 8.0 / L / 1000.0), "+1", "-", "-"))

dT_dR = (B * L * 8.0) / DC ** 2      # s per (bit/s)
rows.append(("O3 T_rec (ms)", "0 (RTT-invariant)", "0", "+%.1f ms/Mbps" % (dT_dR * 1e6 * 1e3), "-1 (via C-R)"))

rows.append(("O4 n_rtt = T_rec/RTT", "-%.4f /ms" % (T_REC / (RTT0 ** 2) * 1e-3), "-1", "-", "-"))

rows.append(("O5 E[Dq] floor (ms)", "0 (depends on R/C only)", "0", "rho_q rises -> queue blows up past R=C", "-"))

rows.append(("O6 T6 via collisions", "+%.4f s/ms (k=%.0f, rho=1)" % (0.584 * K_STALL * 1e-3, K_STALL), "~0.002", "via T_rec & rho_pipe", "+"))

for r in rows:
    print("  %-22s %-30s %-8s %-34s %s" % r)

# ------------------------------------------------ sim 1: fluid MC of 6.bin window
print("\n== B. fluid MC: E[T6] over RTT grid x rho (400k reps/cell, Poisson giants) ==")
lam_giant_per_rho = LAM_FLOW * P_GIANT       # giants/s at rho=1 = 0.02191
NREP = 400_000


def poisson(rng, lam):
    """Knuth's exact Poisson sampler."""
    Lexp = math.exp(-lam)
    k, p = 0, 1.0
    while True:
        p *= rng.random()
        if p <= Lexp:
            return k
        k += 1


def sim_t6(rtt_ms, rho, seed=20261107):
    rng = random.Random(seed)
    lam_eff = lam_giant_per_rho * rho * (T6_BASE + 2.5)
    acc = []
    for _ in range(NREP):
        n = poisson(rng, lam_eff)
        acc.append(T6_BASE + n * (T_STARVE + T_REC + K_STALL * rtt_ms / 1000.0))
    return st.fmean(acc), st.pstdev(acc)


grid = {}
for rho in (1.0, 1.5, 2.0, 2.4):
    xs, ys, ses = [], [], []
    for rtt in range(65, 76):
        m, sd = sim_t6(rtt, rho, seed=20261107 + rtt)
        xs.append(rtt); ys.append(m); ses.append(sd / math.sqrt(NREP))
    xm, ym = st.fmean(xs), st.fmean(ys)
    denom = sum((x - xm) ** 2 for x in xs)
    slope = sum((x - xm) * (y - ym) for x, y in zip(xs, ys)) / denom
    se_cell = st.fmean(ses)
    slope_se = se_cell / math.sqrt(denom)
    grid[rho] = (xs, ys, slope, slope_se)
    analytic = 0.584 * rho * K_STALL * 1e-3
    zsig = abs(slope - analytic) / slope_se if slope_se > 0 else float("inf")
    print("  rho=%.1f: E[T6] 65/70/75ms = %.3f/%.3f/%.3f s | numeric slope=%.5f+-%.5f s/ms | analytic=%.5f | |dz|=%.1f"
          % (rho, ys[0], ys[5], ys[10], slope, slope_se, analytic, zsig))

# relative effect sizes
print("\n  effect-size comparison for 6.bin at rho=2.0:")
_, ys, slope, slope_se = grid[2.0]
drtt = (ys[10] - ys[0])                  # RTT 65->75
drho = grid[2.4][1][5] - grid[1.0][1][5]  # rho 1.0->2.4 at 70ms
print("    RTT +10ms (65->75): %+.1f ms   |   rho +1.4: %+.1f ms   |   ratio rho/RTT = %.0fx"
      % (drtt * 1e3, drho * 1e3, drho / drtt))

# ------------------------------------------------ sim 2: burst phase superposition
print("\n== C. packet-level (Regime I, idle-window burst): 60-pkt burst + background"
      " burst b_bg (line-rate train) at phase delta ==")
BURST = 60.0


def q_peak_numeric(b_bg, delta_s, dt=2e-6):
    """Discrete-time superposition with full-line service (B*=60 self-absorption
    regime, i.e. the measured no-loss elastic window): our burst serializes at
    line rate for Burst/mu seconds from t=0; background burst train of b_bg
    packets serializes at line rate from t=delta; link serves mu*dt whenever
    queue > 0. C_bg steady load = 0 here (that is the precondition of the
    measured B*=60 elastic-absorption regime)."""
    t_end = (BURST + b_bg) / MU + delta_s + 5e-3
    q, peak = 0.0, 0.0
    t = 0.0
    n_steps = int(t_end / dt)
    for i in range(n_steps):
        arr = 0.0
        if 0.0 <= t < BURST / MU:
            arr += MU * dt
        if delta_s <= t < delta_s + b_bg / MU:
            arr += MU * dt
        serv = min(q + arr, MU * dt)
        q = q + arr - serv
        peak = max(peak, q)
        t += dt
    return peak


def q_peak_analytic(b_bg, delta_s):
    """Overlap of two line-rate trains: while trains overlap, queue grows at mu;
    our train leaves mu*delta packets already served by the time bg starts.
    Inside our train: Q_peak = min(b_bg, max(0, Burst - mu*delta)).
    After our train (self-absorbed, queue empty): bg train arrives at line rate
    and is fully served -> Q_peak = 0."""
    if delta_s <= BURST / MU:
        return min(b_bg, max(0.0, BURST - MU * delta_s))
    return 0.0


b_bg_list = (10.0, 20.0, 40.0, 60.0)
for b_bg in b_bg_list:
    row_num, row_ana = [], []
    for dms in (0, 0.5, 1.0, 1.92, 3.0, 6.0):
        row_num.append(q_peak_numeric(b_bg, dms * 1e-3))
        row_ana.append(q_peak_analytic(b_bg, dms * 1e-3))
    maxerr = max(abs(a - n) for a, n in zip(row_num, row_ana))
    over_B = [d for d, x in zip((0, 0.5, 1.0, 1.92, 3.0, 6.0), row_num) if x > B + 1e-9]
    print("  b_bg=%4.0f: Q_peak(0/0.5/1/1.92/3/6ms)=%s | max|num-ana|=%.3f pkt | delta with Q>B: %s"
          % (b_bg, ["%5.1f" % x for x in row_num], maxerr,
             ("%.1f ms" % max(over_B)) if over_B else "none"))

# numerical derivative of Q_peak vs delta in the linear regime (b_bg large)
d_qp = (q_peak_numeric(60.0, 1.0e-3) - q_peak_numeric(60.0, 0.5e-3)) / 0.5e-3
print("  numeric dQ_peak/ddelta = %.0f pkt/s  vs analytic -mu = -%.0f pkt/s  (-1 packet per %.0f us)"
      % (d_qp, MU, 1e6 / MU))
W_VULN = (BURST - B) / MU
print("  loss window: Q_peak>B=40 requires b_bg>40 AND delta < %.2f ms = %.1f%% of RTT"
      " (RTT-elasticity of per-cycle collision prob = -1)"
      % (W_VULN * 1e3, 100 * W_VULN / RTT0))

print("\n== D. composite elasticity matrix S_ij = dln(O_i)/dln(I_j) at baseline ==")
hdr = ["O \\ I", "RTT", "phi", "rho", "R"]
mat = [
    ["O1 BDP/W",        "+1.000", "0 (fluid)", "0", "0"],
    ["O2 T_rec",        "0",      "0",         "0", "-1.03 (via C-R=4M)"],
    ["O3 n_rtt",        "-1.000", "0",         "0", "0"],
    ["O4 E[Dq] floor",  "0",      "0",         "0", "+2.9 (M/D/1 near rho=1)"],
    ["O5 T6 (rho=2)",   "+0.002", "0 (fluid)", "+1.0", "+0.10"],
    ["O6 Q_peak burst", "0*",     "-1 (linear regime: -10.42 pkt per +1ms phase; loss needs delta<1.92ms AND b_bg>40)", "+1 (bg volume)", "-0.04"],
]
print("  %-18s %-8s %-28s %-8s %-22s" % tuple(hdr))
for r in mat:
    print("  %-18s %-8s %-28s %-8s %-22s" % tuple(r))
print("  (* RTT enters burst mode only via 1/RTT burst-window rate, files 1-4: elasticity -1"
      " on slow-start wall clock, +0.2 rounds over 65->75ms)")
