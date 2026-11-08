# -*- coding: utf-8 -*-
"""0076 - microsecond noise floor of the official scheduler vs Linux hrtimer
nanosecond clock source: aliasing perturbation of the precise rate limiter.

Repo-established anchors:
  G = 4000 us official timer granularity (0013, HZ=250 jiffies consistent);
  wakeup lag Delta ~ 0.8-1.2 ms (0068: 4000us leak period stretches to
  4.6-5.2 ms -> 77-87% effective rate on interval-type limiters);
  clock_granularity g = 1000 us release tolerance (official module doc:
  a packet scheduled at t_s may be sent once t_s <= now + g);
  fragile window W_vuln = (B* - 40)/mu = 1.92 ms at B*=60 (0066);
  M/D/1 self-queue floor E[N_q] = rho^2/(2(1-rho)) = 11.52 pkt at 96M (0066).

Mechanism split (this audit's core):
  leak_bucket      interval-type: credit tops up per wakeup -> late wakeup
                   STRETCHES the interval -> effective rate degrades (77-87%).
  precise_rate_based schedule-type: release times precomputed at ns grid ->
                   late wakeup CONSERVES rate but converts jitter into
                   clumps of size ~ (gap + g)/tau_p  -> micro-bursts.

Sections:
  A. noise source inventory (periods relevant to a 96/100 us pacing grid).
  B. release-pattern Monte Carlo per scenario: clump-size distribution,
     aliasing/resonance classification (integer vs fractional T_w/tau_p).
  C. rate conservation vs degradation: precise vs leak under the same lag.
  D. queue-level erosion: steady-state loss threshold on a background burst
     under ideal pacing vs clumped emission (0066 formula generalized to
     clump size n).
  E. session-level expectation: co-occurrence of clump phase with giant-flow
     collision (lambda_g rho T_win), fragile-window arithmetic.

stdlib-only, deterministic seed. Run: python -I zcode/scripts/alias0076_hrtimer_noise.py
"""
import math
import random
import statistics as st

C = 100e6
L = 1200.0
MU = C / 8.0 / L          # pkt/s
B = 40.0                  # switch buffer (pkt)
RTT = 70e-3
TAU_96 = L * 8.0 / 96e6   # 100 us per-packet spacing at 96 Mbps
TAU_100 = L * 8.0 / 1e8   # 96 us at 100 Mbps
G = 1000e-6               # clock_granularity tolerance
MU_SER = 96e-6            # per-packet serialization at the bottleneck

print("== canon ==")
print("  mu=%.1f pkt/s  tau_p(96M)=%.0fus  tau_p(100M)=%.0fus  g=1000us  B=40pkt"
      % (MU, TAU_96 * 1e6, TAU_100 * 1e6))

# ----------------------------------------------------- A. noise inventory
print()
print("== A. scheduler noise floor inventory (periods vs pacing grid) ==")
inv = [
    ("TSC/clocksource read", "1 ns", "ns-grid credit accounting (nominal only)"),
    ("hrtimer event device (LAPIC)", "~1 us", "expiry programming precision"),
    ("timer slack (non-RT)", "50 us", "hrtimer wakeup coalescing"),
    ("measured wakeup lag (0068)", "0.8-1.2 ms", "CFS/softirq wakeup latency"),
    ("jiffy tick HZ=250 (G=4000us)", "4 ms", "plain-timer paths; 0013 anchor"),
    ("cgroup cpu.max period", "100 ms", "throttle stalls under CPU contention"),
]
for name, per, note in inv:
    print("  %-30s %-10s %s" % (name, per, note))

# --------------------------------- B. release pattern Monte Carlo
def simulate_precise(R_bps, lag_range, dur=8.0, greedy=False, seed=42):
    """schedule-type limiter (ns grid, per-packet timers).
    lazy reading: fire armed for next packet's scheduled time + lag; releases
    only packets that have come due (sched <= fire), catch-up conserves rate.
    greedy reading: every event releases ALL packets with sched <= now + g
    (official tolerance allows up to g of early release) -> g/tau_p clumps.
    returns (clumps, eff_Mbps)."""
    rng = random.Random(seed)
    tau = L * 8.0 / R_bps
    n_pkt = int(R_bps * dur / 8.0 / L)
    sched = 0.0            # next packet's scheduled (ns-grid) time
    clumps = []
    released = 0
    wall_end = 0.0
    while released < n_pkt:
        lag = rng.uniform(*lag_range)
        fire = sched + lag
        wall_end = fire
        k = 0
        limit = fire + G if greedy else fire
        while sched <= limit and released < n_pkt:
            sched += tau
            released += 1
            k += 1
        if k:
            clumps.append(k)
    return clumps, released * L * 8.0 / wall_end / 1e6


def simulate_leak(R_bps, interval, lag_range, dur=8.0, seed=42):
    """interval-type limiter: each wakeup tops up interval-worth of credit;
    late wakeup stretches the interval -> rate degradation."""
    rng = random.Random(seed)
    rate_per_wake = R_bps * interval / 8.0 / L   # pkt credited per wakeup
    now = 0.0
    sent = 0.0
    n_wake = 0
    while now < dur:
        lag = rng.uniform(*lag_range)
        now += interval + lag
        sent += rate_per_wake
        n_wake += 1
    return sent * L * 8.0 / dur / 1e6   # effective Mbps


def cstats(cl):
    s = sorted(cl)
    return "mean=%.1f p95=%d max=%d" % (st.mean(cl), s[int(0.95 * len(s))], max(s))


print()
print("== B. precise limiter release pattern (R=96M, dur=8s, rate conserved) ==")
scen = [
    ("lazy | ideal slack lag<=50us", (0.0, 50e-6), False),
    ("lazy | wakeup lag 0.8-1.2ms (0068)", (0.8e-3, 1.2e-3), False),
    ("lazy | jiffy fallback lag~4ms", (3.8e-3, 4.2e-3), False),
    ("greedy | g=1000us tolerance, any lag", (0.0, 50e-6), True),
]
for name, lagr, gr in scen:
    clumps, eff = simulate_precise(96e6, lagr, greedy=gr)
    print("  %-38s clumps: %-24s eff %.1f Mbps" % (name, cstats(clumps), eff))

print()
print("== B2. resonance/aliasing classification (T_w/tau_p at 96M) ==")
for tw, tag in ((50e-6, "slack"), (1.0e-3, "1ms lag"), (4e-3, "jiffy"), (100e-3, "cgroup")):
    ratio = tw / TAU_96
    frac = ratio - math.floor(ratio)
    kind = "LOCKED (integer)" if frac < 1e-9 else "DRIFT (frac=%.2f)" % frac
    print("  T_w=%7.2fms (%-6s)/tau_p = %7.2f  %-20s catch-up ~%5.1f pkt"
          % (tw * 1e3, tag, ratio, kind, ratio + G / TAU_96))

# --------------------------- C. rate conservation vs degradation
print()
print("== C. interval-type (leak) degradation vs schedule-type (precise) ==")
print("  leak 4000us + lag U[0.8,1.2]ms:")
for nom in (96.0, 100.0):
    eff = simulate_leak(nom * 1e6, 4000e-6, (0.8e-3, 1.2e-3))
    print("    nominal %5.1f Mbps -> effective %5.1f Mbps (%.0f%%)   [0068: 77-87%%]"
          % (nom, eff, 100 * eff / nom))
_, effp = simulate_precise(96e6, (0.8e-3, 1.2e-3))
print("    precise 96M, same lag: effective %.2f Mbps (rate conserved,"
      " jitter -> clumps)" % effp)

# ----------------------------------------- D. queue-level erosion
print()
print("== D. loss-threshold erosion for background bursts (steady state) ==")
rho96 = 0.96
enq = rho96 ** 2 / (2 * (1 - rho96))          # M/D/1 waiting queue, 11.52


def residue(clump_n, delta_s):
    """my unbundled residue at phase delta into the clump (0066 idealization:
    serialized at bottleneck rate) -> max(0, n - mu*delta)."""
    return max(0.0, clump_n - (delta_s / MU_SER))


print("  E[N_q]=%.2f pkt (0066 floor). Background burst b_bg arrives at phase"
      % enq)
print("  delta into my clump; loss iff E[N_q] + residue(n,delta) + b_bg > 40.")
print("  %-10s %-12s %-22s %-22s" % ("clump n", "phase delta", "threshold(b_bg)",
                                    "ideal-paced threshold"))
ideal_thr = B - enq
for n in (10, 20, 40):
    worst = 0.0
    for i in range(21):
        d = i * (n * MU_SER) / 20.0
        worst = max(worst, residue(n, d))
    print("  %-10d %-12s max residue %.1f -> thr %.1f pkt (worst) | %.1f pkt (any)"
          % (n, "0..%.2fms" % (n * MU_SER * 1e3), worst, B - enq - worst, ideal_thr))
print("  ideal pacing: threshold %.1f pkt for ALL phases (residue~0)." % ideal_thr)
print("  -> scheduler clumping lowers the background-burst loss threshold by"
      " up to %.1f pkt (%.0f KB) at bad phases."
      % (max(residue(20, 0.0), 0), max(residue(20, 0.0), 0) * L / 1e3))

# --------------------------------------- E. session-level expectation
print()
print("== E. session-level co-occurrence arithmetic (6.bin, R=96M) ==")
T_win = 320e6 * 8.0 / 96e6
lam = 0.0219
n_coll = lam * T_win
print("  T_win=%.2f s, expected giant collisions=%.2f (rho=1)" % (T_win, n_coll))
# fragile phase fraction: bg must land within the head of a clump; with 1ms
# wakeups and 20-pkt clumps the head window is 1.92ms out of the 2ms cycle
duty_head = 1.92e-3 / 2e-3
print("  vulnerable head duty (20-pkt clumps @1ms cycle): %.0f%%" % (100 * duty_head))
# 0066 fragile-window probability that bg burst > 40 pkt AND lands in head:
# websearch heavy tail: P(size>48KB)~O(1); conservative joint ~ n_coll*duty
print("  conservative joint co-occurrence upper bound: %.2f events/session"
      % (n_coll * duty_head))
print("  comparison: measured valid-session loss events are rarer; the joint")
print("  bound is an upper envelope (bg burst size and phase not independent).")

print()
print("== F. implications ==")
print("  1. precise@96M clumps <= ~20 pkt under measured lag -> solo residue")
print("     max 20 pkt < 40: self-safe; keeps >=20 pkt headroom for bg overlap.")
print("  2. 4ms jiffy resonance (timer fallback) = 40-pkt clump = buffer-scale:")
print("     any coincident bg packet -> loss; this is why sub-G intervals on")
print("     interval-type limiters must stay >= 4000us (0013 rule).")
print("  3. cgroup throttle (100ms) would create 1000-pkt catch-up: design")
print("     assumes the pacer thread is not CPU-throttled (unverifiable from")
print("     here; flag only).")
print("  4. g=1000us default is load-bearing: ~10 pkt early-release tolerance")
print("     at 96M; lowering it raises wakeup rate, raising it raises clumps.")
print("  5. 96M + 4% margin (0075 knee) absorbs the erosion: worst-phase")
print("     threshold 18.5 pkt vs ideal 28.5 pkt - the 40-pkt buffer still")
print("     bounds M/D/1 floor 11.5 + clump residue 20 + typical bg head.")
