# -*- coding: utf-8 -*-
"""0074 - slow-start completion degree and unused-bandwidth integral loss for
files 1-4.bin (10/20/40/80 MB sprint phase), across initial windows.

Repo-canon constants (docs/analysis/network-queuing-delay-theory.md):
  C = 100 Mbps bottleneck, L = 1200 B mean QUIC packet,
  mu = C/L = 10416.67 pkt/s (96 us serialization), B = 40 pkt drop-tail,
  RTT0 = 70 ms, BDP = 729.2 pkt.
Pace canon for token_bucket (0072 rate table, I=4000us main region):
  r/I tokens -> packets/s; r=40/4ms = 96 Mbps.

Sections:
  A. closed-form slow-start ramp: saturation time t*, ramp deficit integral
     U_ramp(W0, R) = R*t* - L*(W_ss - W0)/ln2  (continuous exponential growth),
     verified against a discrete per-RTT round simulator.
  B. per-file slow-start completion degrees (time share d_i, byte share) and
     unused-bandwidth integral decomposition  U_i = C*T_i - S_i  into
     {ramp tax, fair-share structural deficit, residual (collision/starvation)}.
  C. initial-window sweep W_eff0 in {12,24,32,40,60,100}: delta-T and delta-U
     per file; consistency check: W0=12 reproduces the 4plus2 doc round table
     (10/11/12/13 rounds for files 1-4).
  D. pace semantics discriminator for token_bucket refill I=2000us:
     G=4000us ceil-quantization vs nominal r/I, tested against measured
     per-file throughput (falsification arithmetic on tb4-2k-champ-r1 3.bin).
  E. measured extraction from runs/results.jsonl (read-only): tb families,
     per-file achieved throughput, unused-integral decomposition.

stdlib-only, deterministic. Run: python -I zcode/scripts/ss0074_slowstart_integral.py
"""
import math
import json
import re
import statistics as st

# ---------------------------------------------------------------- constants
C = 100e6            # bps
L = 1200.0           # bytes / packet
MU = C / 8.0 / L     # pkt/s = 10416.67
B = 40.0             # pkt drop-tail buffer
RTT = 70e-3          # s
BDP = C * RTT / 8.0 / L     # 729.17 pkt
SIZES_MB = [10.0, 20.0, 40.0, 80.0]
NAMES = ["1.bin", "2.bin", "3.bin", "4.bin"]
LN2 = math.log(2.0)

print("== canon ==")
print("  C=100Mbps  L=1200B  mu=%.1f pkt/s  B=40pkt  RTT=70ms  BDP=%.1f pkt" % (MU, BDP))


# ------------------------------------------------------------- A. ramp model
def ramp_closed(W0, R_bps):
    """continuous slow-start ramp against pace R_bps (R < C).
    returns (t_sat [s], U_ramp [bytes], bytes_sent_during_ramp)."""
    Wss = R_bps * RTT / 8.0 / L          # steady-state window (pkt)
    if W0 >= Wss:
        return 0.0, 0.0, 0.0
    t_sat = RTT * math.log2(Wss / W0)
    sent = L * (Wss - W0) / LN2          # integral of exponential rate
    U = R_bps / 8.0 * t_sat - sent       # deficit vs pace
    return t_sat, U, sent


def simulate_file(n_pkt, W0, R_bps, use_line_cap=True, bucket=B):
    """discrete per-RTT-round slow start with pace R and (optional) line cap.
    round k: sent = min(cwnd, tokens_avail, line_cap); cwnd += sent (slow-start
    ACK gain); tokens refill at R into a bucket capped at `bucket`.
    deficit = integral of (pace_rate - actual_rate) dt over the transfer.
    returns dict of metrics."""
    rate_pkt = R_bps / 8.0 / L           # pkt/s accrual
    line_cap = MU * RTT if use_line_cap else float("inf")   # pkt per round
    cap = min(rate_pkt * RTT, line_cap)  # pkt ceiling per full round
    cwnd = W0
    tokens = float(W0)
    cum = 0.0
    t = 0.0
    deficit = 0.0                        # pkt below pace
    sent_at_sat = None
    sat_rtt = None
    while cum < n_pkt and t < 60.0:
        avail = tokens + rate_pkt * RTT  # stored + accrued over the round
        sent = min(cwnd, avail, cap)
        sent = min(sent, n_pkt - cum)
        tokens = min(bucket, tokens + rate_pkt * RTT - sent)
        cum += sent
        cwnd += sent
        file_done = cum >= n_pkt - 1e-9
        # deficit: pace-underuse while the file is in flight. A full round that
        # ends window-limited contributes (cap - sent); a round truncated by
        # file exhaustion contributes nothing beyond the file's own tail.
        if sent < cap - 1e-9 and not file_done:
            deficit += cap - sent
        # round duration: full RTT while in flight; truncated tail otherwise
        t += RTT if not file_done else max(RTT / 2.0, sent / (cap / RTT))
        if sat_rtt is None and cwnd >= cap:
            sat_rtt = t
            sent_at_sat = cum
    return {"T": t, "U_ramp": deficit * L, "sat_s": sat_rtt if sat_rtt else t,
            "sent_at_sat": sent_at_sat if sent_at_sat else cum,
            "rounds": t / RTT}


print()
print("== A. closed form vs round simulator (R=96Mbps pace, W0 sweep) ==")
R96 = 96e6
print("  %-6s | %-22s | %-22s" % ("W0", "closed: t*  U_ramp", "sim: t_sat  U_ramp"))
for W0 in (12, 24, 32, 40, 60):
    ts, U, _ = ramp_closed(W0, R96)
    sim = simulate_file(80e6 * 8.0 / L, W0, R96)   # long file: pure ramp region
    print("  %-6d | %6.1fms %8.3f MB | %6.1fms %8.3f MB"
          % (W0, ts * 1e3, U / 1e6, sim["sat_s"] * 1e3, sim["U_ramp"] / 1e6))

# consistency: 4plus2 doc round table uses W0=12, window-limited cumulative
print()
print("== A2. 4plus2-doc round table reproduction (W0=12, cumulative-window rule) ==")
for name, mb in zip(NAMES, SIZES_MB):
    n = mb * 8e6 / 8.0 / L
    k = 0
    while 12.0 * (2 ** (k + 1) - 1) < n:
        k += 1
    print("  %s  N=%6.0f pkt  rounds=%d  (%.0f ms)" % (name, n, k + 1, (k + 1) * RTT * 1e3))

# ------------------------------------------------- B. completion + integral
def file_metrics(name, mb, W0, R_bps, R_eff_bps):
    """metrics for one file: ramp tax at effective steady rate R_eff,
    ideal wire time, completion degrees."""
    n = mb * 8e6 / 8.0 / L
    sim = simulate_file(n, W0, R_eff_bps)
    t_sat = sim["sat_s"]
    T = sim["T"]
    S = mb * 1e6
    U_total = C / 8.0 * T - S            # measured-style unused integral (bytes)
    U_ramp = sim["U_ramp"]
    return {"name": name, "T": T, "t_sat": t_sat, "d_time": t_sat / T,
            "U_total": U_total, "U_ramp": U_ramp,
            "ramp_share": U_ramp / U_total if U_total > 0 else 0.0,
            "eta_bytes": sim["sent_at_sat"] / n}


print()
print("== B. per-file completion degrees and unused integral (W0=12, R_eff=50%% of pace) ==")
print("  file  R_eff   T_sim   t_sat  d_time(t_sat/T)  bytes_pre_sat  U_total(MB)  U_ramp(MB)  ramp_share")
for name, mb in zip(NAMES, SIZES_MB):
    m = file_metrics(name, mb, 12.0, R96, 0.5 * R96)
    print("  %s %5.1fM %6.2fs %5.2fs      %5.1f%%        %5.1f%%      %8.2f    %7.3f     %5.1f%%"
          % (m["name"], 48.0, m["T"], m["t_sat"], 100 * m["d_time"], 100 * m["eta_bytes"],
             m["U_total"] / 1e6, m["U_ramp"] / 1e6, 100 * m["ramp_share"]))

# --------------------------------------------- C. initial-window sensitivity
print()
print("== C. initial-window sweep: time SAVED vs W0=12 (positive = faster), R_eff=48M ==")
base = {n: file_metrics(n, mb, 12.0, R96, 48e6) for n, mb in zip(NAMES, SIZES_MB)}
print("  %-5s " % "W0" + " ".join("%-16s" % n for n in NAMES) + " | sum saved(s) sum dU(MB)")
for W0 in (12, 24, 32, 40, 60, 100):
    dts, dus = [], []
    cells = []
    for name, mb in zip(NAMES, SIZES_MB):
        m = file_metrics(name, mb, float(W0), R96, 48e6)
        dt = base[name]["T"] - m["T"]
        du = base[name]["U_ramp"] - m["U_ramp"]
        dts.append(dt); dus.append(du / 1e6)
        cells.append("%+5.2fs/%+5.2f" % (dt, du / 1e6))
    print("  %-5d %s | %+6.2f   %+6.2f" % (W0, " ".join(cells), sum(dts), sum(dus)))
print("  (cwnd-persistence scenario: if one QUIC connection spans files 1-4,"
      " only 1.bin pays the ramp -> multiply sum saved by ~1/4; per-file reset"
      " scenario pays it 4x. Measured 2.bin-vs-1.bin utilization gap favors"
      " substantial persistence or diluted tax — see audit doc §3.3.)")

# ------------------------------------------ D. pace semantics discriminator
print()
print("== D. token_bucket refill I=2000us: G-quantized vs nominal (measured test) ==")
# tb4-2k-champ-r1: dirs 1-2 r20/2ms, 3 r19/2ms, 4 r18/2ms; B=40, tau=40
rows = [json.loads(x) for x in open("runs/results.jsonl", encoding="utf-8") if x.strip()]
r1 = [x for x in rows if x.get("tag") == "test-hybrid-tb4-2k-champ-r1"]
if r1:
    dl = r1[0]["downloads"]
    print("  sample test-hybrid-tb4-2k-champ-r1 (valid=%s):" % r1[0].get("valid"))
    for i, mb in ((3, 40.0), (4, 80.0)):
        t = dl["%d.bin" % i]
        thr = mb / t
        pace_nom = {3: 19 / 0.002, 4: 18 / 0.002}[i] * L * 8 / 1e6      # Mbps
        pace_q = {3: 19 / 0.004, 4: 18 / 0.004}[i] * L * 8 / 1e6
        # elastic ceiling: quantized pace + one-time (tau+B) token grant spread
        # over the whole file (tau=40, B=40 -> 80 pkt = 96 KB)
        elastic_cap = pace_q + (40 + 40) * L * 8.0 / t / 1e6
        verdict = ("FALSIFIES quantization" if thr * 8 > elastic_cap else "consistent")
        print("   %d.bin t=%.2fs -> %.1f Mbps | nominal pace %.1f | quantized pace %.1f "
              "(elastic max %.1f)  -> %s"
              % (i, t, thr * 8, pace_nom, pace_q, elastic_cap, verdict))

# ------------------------------------------- E. measured extraction (tb families)
def tb_sig(cfg):
    sig = []
    for k in "1234":
        c = cfg.get(k, "")
        m = re.search(r"tokens=(\d+),burst=(\d+),token_refill_rate=(\d+),"
                      r"token_refill_interval_us=(\d+)", c)
        if not c.startswith("token_bucket") or not m:
            return None
        sig.append(tuple(int(g) for g in m.groups()))
    return tuple(sig)


valid = [x for x in rows if x.get("valid") and not x.get("tag", "").startswith("load-")]
fams = {}
for x in valid:
    s = tb_sig(x["config"])
    if s:
        fams.setdefault(s, []).append(x)
big = sorted(fams.items(), key=lambda kv: -len(kv[1]))[:3]

print()
print("== E. measured unused-bandwidth integral decomposition (top tb families) ==")
print("  U_i = C*T_i - S_i;  ramp share from model at calibrated R_eff = mean thr")
print("  family (tau,B,r,I) x4 | n")
for sig, rs in big:
    means = [st.mean([r["downloads"][n] for r in rs]) for n in NAMES]
    print("  %s | n=%d" % (sig, len(rs)))
    for name, mb, T in zip(NAMES, SIZES_MB, means):
        thr_bps = mb * 1e6 / T * 8.0
        U_total = C / 8.0 * T - mb * 1e6
        Wss = thr_bps * RTT / 8.0 / L
        W0 = min(sig[0][0], sig[0][1])
        ts, U_ramp, _ = ramp_closed(min(W0, Wss), thr_bps)
        print("    %s T=%.2fs thr=%.1fMbps (%.0f%% of pace) U_total=%6.2fMB "
              "U_ramp=%5.3fMB (%4.1f%% of U_total)"
              % (name, T, thr_bps / 1e6, 100 * thr_bps / {1: 96e6, 2: 96e6,
                 3: 91.2e6, 4: 86.4e6}[int(name[0])] if sig[0][3] == 4000 else 96e6,
                 U_total / 1e6, U_ramp / 1e6, 100 * U_ramp / U_total))

print()
print("== E2. clean-line reference: fastest measured per file (all valid runs) ==")
for name, mb in zip(NAMES, SIZES_MB):
    best = min(valid, key=lambda r: r["downloads"][name])
    t = best["downloads"][name]
    print("  %s  %.3fs -> %.1f Mbps (%.1f%% line)  [%s]"
          % (name, t, mb / t * 8, 100 * (mb / t * 8) / 100.0, best["tag"][:44]))

print()
print("== F. strategic synthesis ==")
tot_ramp_4 = sum(file_metrics(n, mb, 12.0, R96, 48e6)["U_ramp"] for n, mb in zip(NAMES, SIZES_MB))
tot_ramp_60 = sum(file_metrics(n, mb, 60.0, R96, 48e6)["U_ramp"] for n, mb in zip(NAMES, SIZES_MB))
print("  ramp tax sum over files 1-4: W0=12 -> %.2f MB (%.3f s line-rate); "
      "W0=60 -> %.2f MB (%.3f s)" % (tot_ramp_4 / 1e6, tot_ramp_4 * 8.0 / C,
                                     tot_ramp_60 / 1e6, tot_ramp_60 * 8.0 / C))
print("  i.e. the entire initial-window upside on the sprint phase is bounded by"
      " ~%.2f s of line-rate time; measured unused integral of the same phase"
      " is ~%.0f MB per session (fair share + collisions dominate)."
      % (tot_ramp_4 * 8.0 / C - tot_ramp_60 * 8.0 / C,
         sum(C / 8.0 * st.mean([r["downloads"][n] for r in big[0][1]]) - mb * 1e6
             for n, mb in zip(NAMES, SIZES_MB)) / 1e6))
