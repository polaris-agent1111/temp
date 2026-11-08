# -*- coding: utf-8 -*-
"""0075 - Pareto efficiency boundary of the drain-margin gradient for the
long steady-state files 5.bin (160 MB) and 6.bin (320 MB).

Question: with drain margin m = (C - R)/C in 2%..10% (R = 98..90 Mbps), what
is the Pareto frontier between transfer latency X and packet-loss risk Y?

Repo-canon constants (0066/0068/0072 audits):
  C = 100 Mbps, L = 1200 B, mu = 10416.67 pkt/s, B = 40 pkt drop-tail,
  RTT = 70 ms. Background giants: lambda_g = 0.0219*rho per s, one-collision
  first-order cost = T_starve (2.24 s) + T_rec(m) + kappa*RTT (0051/0060/0066).
  T_rec(m) = B*L*8/(C-R) = 96 ms at 4% margin (0060 fitted).

Arms:
  X(m): wire time at pace R + expected collision penalty
        = F/R*8 + (lambda_g*rho*T_win) * (T_starve + rho_q*T_rec + kappa*RTT)
        with T_win = F*8/R, rho_q = R/C. Note the recovery term diverges as
        m -> 0 (T_rec = B*L*8/dC): at R = C the queue never drains while we
        keep pacing at line rate, so m = 0 is excluded from the numeric
        frontier (recovery becomes background-duration-bound).
  Y(m): self-queue overflow probability from the exact M/D/1 embedded chain
        at departures (arrivals Poisson(rho_q) per 96 us service, buffer 40),
        plus expected packets lost per session from collision-full windows:
        n_coll * rho_q * mu * T_rec.

Measured section: runs/results.jsonl (read-only) grouped by exact
(max_pacing_rate 5.bin, 6.bin) pairs; Welch tests with explicit batch-rho
confound warning (0065: session-level sigma enters scores).

stdlib-only, deterministic. Run: python -I zcode/scripts/pareto0075_drain_margin.py
"""
import math
import json
import re
import statistics as st

C = 100e6          # bps
L = 1200.0
MU = C / 8.0 / L   # pkt/s
B = 40.0           # pkt buffer
RTT = 70e-3
T_STARVE = 2.24    # s per giant collision (0051)
LAM = 0.0219       # giants/s at rho=1 (0051)
KAPPA = 1.0
F5, F6 = 160e6, 320e6   # bytes

print("== canon ==")
print("  mu=%.2f pkt/s  B=40  RTT=70ms  T_starve=2.24s  lambda_g=0.0219*rho/s" % MU)


# ------------------------------------------- M/D/1 embedded chain (buffer B)
def md1_tail(rho, b=B):
    """stationary queue at departures for M/D/1 with finite buffer b (total
    system). A ~ Poisson(rho) arrivals per deterministic service.
    returns (mean_N, P(arriving pkt finds system full))."""
    from math import exp

    def pois(k, lam):
        return exp(-lam + k * math.log(lam) - math.lgamma(k + 1)) if k else exp(-lam)

    n = int(b)
    pmf = [pois(k, rho) for k in range(60)]
    pmf[59] += 1.0 - sum(pmf)
    # transition matrix: S = max(Q-1,0)+A ; Q' = min(S, n-1)
    T = [[0.0] * n for _ in range(n)]
    for q in range(n):
        base = max(q - 1, 0)
        row = T[q]
        for a, pa in enumerate(pmf):
            s = base + a
            row[s if s < n else n - 1] += pa
    pi = [1.0 / n] * n
    for _ in range(5000):
        nxt = [0.0] * n
        for q in range(n):
            piq = pi[q]
            if piq == 0.0:
                continue
            row = T[q]
            for s in range(n):
                nxt[s] += piq * row[s]
        delta = sum(abs(a - b2) for a, b2 in zip(pi, nxt))
        pi = nxt
        if delta < 1e-14:
            break
    mean = sum(q * p for q, p in enumerate(pi))
    p_full = 0.0
    for q in range(n):
        need = int(b) - q       # arrivals that would overflow
        p_full += pi[q] * (1.0 - sum(pmf[:max(need, 0)]))
    return mean, p_full


print()
print("== Y1. M/D/1 self-queue tail vs utilization rho_q = R/C (buffer=40) ==")
print("  %-6s %-9s %-11s" % ("R", "rho_q", "P(overflow)"))
pmap = {}
for R_mbps in (90, 92, 94, 96, 97, 98, 99, 100):
    rho = R_mbps / 100.0
    if rho >= 0.999:
        print("  %-6d %-9.2f %-11s" % (R_mbps, rho, "divergent (rho>=1)"))
        continue
    mean, pfull = md1_tail(rho)
    pmap[R_mbps] = pfull
    print("  %-6d %-9.2f %-11.3e  (E[N]=%.2f)" % (R_mbps, rho, pfull, mean))


# ------------------------------------------------------- X(m) latency arm
def t_rec(m):
    return B * L * 8.0 / (C * m) if m > 0 else float("inf")


def latency(R_mbps, rho=1.0):
    R = R_mbps * 1e6
    wire = (F5 + F6) * 8.0 / R
    out = {}
    xtot = 0.0
    for name, Fb in (("5.bin", F5), ("6.bin", F6)):
        T_win = Fb * 8.0 / R
        n_coll = LAM * rho * T_win
        cost = T_STARVE + (R / C) * t_rec(m_of(R_mbps)) + KAPPA * RTT
        x = T_win + n_coll * cost
        out[name] = (T_win, n_coll, x)
        xtot += x
    return xtot, out


def m_of(R_mbps):
    return (100.0 - R_mbps) / 100.0


print()
print("== X(m). latency arm: wire + expected collision penalty (rho=1) ==")
print("  m     R    T5w     T6w    n_coll5+6  T_rec    E[coll penalty]  X_total")
frontier = []
for R_mbps in (99, 98, 97, 96, 94, 92, 90):
    m = m_of(R_mbps)
    _, out = latency(R_mbps)
    n5, n6 = out["5.bin"][1], out["6.bin"][1]
    x5, x6 = out["5.bin"][2], out["6.bin"][2]
    frontier.append((m, R_mbps, x5 + x6, pmap.get(R_mbps, float("inf"))))
    print("  %4.0f%% %3dM %6.2fs %6.2fs  %5.3f     %5.0fms  %5.2fs          %6.2fs"
          % (m * 100, R_mbps, out["5.bin"][0], out["6.bin"][0], n5 + n6,
             t_rec(m) * 1e3, (x5 + x6) - (F5 + F6) * 8.0 / (R_mbps * 1e6), x5 + x6))
print("  m=0 (R=100M): T_rec = B*L/dC -> divergent; recovery becomes bounded"
      " only by background burst duration -> excluded from numeric frontier.")
print("  reference wire floors: (F5+F6)*8/C = %.1f s" % ((F5 + F6) * 8.0 / C))

# ----------------------------------------------------- Pareto presentation
print()
print("== Pareto frontier (X = session latency of 5+6.bin, Y = loss risk) ==")
print("  m      R     X(s)     P_of       reading")
for m, R, X, Y in frontier:
    if Y > 1e-2:
        reading = "self-congestive risk zone"
    elif Y > 1e-4:
        reading = "tail-risk zone"
    else:
        reading = "safe plateau"
    print("  %4.0f%% %3dM %8.2f  %.3e   %s" % (m * 100, R, X, Y, reading))
# knee: maximize risk reduction per latency cost
print()
print("  knee analysis: X(98)-X(92) = %.2f s buys P_of %.1e->%.1e (x%.0f);"
      % (frontier[1][2] - frontier[5][2], pmap[98], pmap[92], pmap[98] / max(pmap[92], 1e-30)))
print("  X(96)-X(92) = %.2f s buys P_of %.1e->%.1e. The steep risk gradient sits"
      % (frontier[3][2] - frontier[5][2], pmap[96], pmap[92]))
print("  between 98M and 96M; below 94M risk is flat while wire time grows")
print("  %.2f s per -2Mbps step." % ((F5 + F6) * 8.0 * (1 / 92e6 - 1 / 94e6)))

# --------------------------------------------------- measured extraction
rows = [json.loads(x) for x in open("runs/results.jsonl", encoding="utf-8") if x.strip()]
valid = [x for x in rows if x.get("valid") and not x.get("tag", "").startswith("load-")]


def rate_of(cfg_str):
    mm = re.search(r"max_pacing_rate=(\d+)", cfg_str or "")
    return round(int(mm.group(1)) / 1e6, 2) if mm else None


groups = {}
for r in valid:
    c5, c6 = r["config"].get("5", ""), r["config"].get("6", "")
    if c5.startswith("precise") and c6.startswith("precise"):
        groups.setdefault((rate_of(c5), rate_of(c6)), []).append(r)

print()
print("== measured (R5,R6) MB/s groups from results.jsonl (valid, non-load) ==")
print("  (R5,R6) Mbps  n    t5 mean/p10/min      t6 mean/p10/min      tot mean  sd6")
keep = {}
for k in sorted(groups, key=lambda x: -(x[0] or 0)):
    rs = groups[k]
    if len(rs) < 3:
        print("  %-12s n=%d  LOW_N  tot %s" % (str((k[0] * 8, k[1] * 8)), len(rs),
              [round(x["total_seconds"], 1) for x in rs]))
        continue
    t5 = sorted(r["downloads"]["5.bin"] for r in rs)
    t6 = sorted(r["downloads"]["6.bin"] for r in rs)
    tot = [r["total_seconds"] for r in rs]
    p10 = lambda a: a[max(0, int(0.1 * len(a)))]
    print("  %-12s n=%-3d %6.2f/%6.2f/%6.2f  %6.2f/%6.2f/%6.2f  %7.2f  %5.2f"
          % (str((k[0] * 8, k[1] * 8)), len(rs), st.mean(t5), p10(t5), t5[0],
             st.mean(t6), p10(t6), t6[0], st.mean(tot), st.pstdev(t6)))
    keep[k] = rs

print()
print("== Welch tests on total_seconds (explicit confound: batch rho, 0065) ==")
base_key = (12.5, 12.0)   # (100M, 96M) champ family
if base_key in keep:
    a = [x["total_seconds"] for x in keep[base_key]]
    for k, rs in sorted(keep.items()):
        if k == base_key:
            continue
        b = [x["total_seconds"] for x in rs]
        ma, mb = st.mean(a), st.mean(b)
        sa, sb = st.pstdev(a), st.pstdev(b)
        se = math.sqrt(sa * sa / len(a) + sb * sb / len(b))
        tstat = (mb - ma) / se if se > 0 else 0.0
        print("  (%s) n=%d vs champ(100M,96M) n=%d: dTot=%+7.2f s  t=%+5.2f"
              % (str((k[0] * 8, k[1] * 8)), len(b), len(a), mb - ma, tstat))
print("  n<=10 per group and batch-rho structure: NO causal read permitted;")
print("  direction consistency only.")

# ------------------------------------------------------------- synthesis
print()
print("== synthesis ==")
x96 = frontier[3][2]
for m, R, X, Y in frontier:
    print("  R=%dM: dX vs 96M = %+5.2f s ; P_of=%.1e" % (R, X - x96, Y))
print("  champion point (5=100M,6=96M) sits at m5=0 empirically (n=34):")
print("  its survival is bounded by background burst duration, not by T_rec;")
print("  the 4%%-margin knee (R=96M) is the variance-robust platform point")
print("  per 0072/0066; 92M and below pay wire time that the collision channel")
print("  does not need.")
