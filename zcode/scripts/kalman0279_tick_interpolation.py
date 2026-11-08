#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0279: Adaptive pacing-tick dynamic interpolation filter (Kalman).

Offline Monte-Carlo of send-time scheduling under scheduler jitter, at the
official tick G = 4000 us (repo anchor: G~4000us; 0248 audit measured
relative-sleep drift +318 us/tick and absolute-deadline+spin residual 0.1 us).

Jitter model (documented assumptions, anchored where possible):
    wake_k = k*T0 + bias_k + sigma_w*z_k + spike_k
    bias_k = 318 + 0.02*k us      (0248 relative-sleep drift + slow thermal drift)
    sigma_w = 150 us               (timer-slack wake jitter, assumption)
    spike_k ~ 1% chance of U(500, 3000) us   (preemption bursts, assumption)

Policies compared (all send one packet per tick):
    A  naive relative sleep: send at wake time (jitter passes through)
    B  Kalman dynamic interpolation: scalar Kalman estimates the slowly
       drifting bias from wake observations with 3-sigma innovation gating
       (spike rejection); sends at the absolute interpolated deadline
       k*T0 + bias_hat_k with execution residual sigma_exec = 20 us
    B2 static absolute deadline: bias calibrated once from first 200 clean
       ticks, then fixed absolute schedule, same execution residual
    C  Kalman WITHOUT gating (ablation): spikes corrupt the bias estimate

Metrics (us^2, bias-removed for the absolute metric so a constant offset
never inflates either policy):
    m1: variance of inter-send interval minus T0   ("发包间隔时序方差")
    m2: variance of send_k - k*T0 after removing the policy's own mean
Gate (task target): B vs A variance reduction >= 70% on both metrics.

Seeded (1108), deterministic, stdout only.
"""
import sys
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

T0 = 4000.0          # us
N = 20000
SIGMA_W = 150.0      # us wake jitter
SIGMA_EXEC = 20.0    # us absolute-deadline execution residual
DRIFT = 0.02         # us per tick slow bias drift
BIAS0 = 318.0        # us, 0248 relative-sleep drift anchor
SPIKE_P = 0.01
SPIKE_LO, SPIKE_HI = 500.0, 3000.0
Q_US2 = 10.0 ** 2    # process noise (bias random-walk) us^2
SEED = 1108


def make_jitter(rng):
    k = np.arange(N, dtype=float)
    bias = BIAS0 + DRIFT * k
    jitter = rng.normal(0.0, SIGMA_W, N)
    spikes = np.where(rng.random(N) < SPIKE_P,
                      rng.uniform(SPIKE_LO, SPIKE_HI, N), 0.0)
    wake = k * T0 + bias + jitter + spikes
    return wake, bias, jitter, spikes


def kalman_bias(wake, gated):
    """Scalar Kalman for the drifting bias with optional 3-sigma gating."""
    b = 0.0
    P = 1e6
    R = SIGMA_W ** 2
    Q = Q_US2
    bh = np.empty(N)
    gated_n = 0
    for k in range(N):
        y = wake[k] - k * T0
        inn = y - b
        if gated and abs(inn) > 3.0 * np.sqrt(P + R):
            gated_n += 1
            bh[k] = b
            continue
        P_pred = P + Q
        K = P_pred / (P_pred + R)
        b += K * inn
        P = (1.0 - K) * P_pred
        bh[k] = b
    return bh, gated_n


def stats(send):
    send = np.asarray(send)
    iv = np.diff(send) - T0
    m1 = float(np.var(iv))
    abs_err = send - np.arange(N, dtype=float) * T0
    m2 = float(np.var(abs_err - abs_err.mean()))
    return m1, m2, float(np.std(iv)), float(np.std(abs_err - abs_err.mean()))


def main():
    rng = np.random.default_rng(SEED)
    wake, bias_true, jitter, spikes = make_jitter(rng)
    n_spikes = int(np.count_nonzero(spikes))
    print(f"=== Task 0279: pacing-tick Kalman interpolation ({N} ticks, "
          f"T0={T0:.0f}us) ===")
    print(f"jitter: sigma_w={SIGMA_W}us, drift={DRIFT}us/tick, bias0={BIAS0}us, "
          f"spikes p={SPIKE_P} U({SPIKE_LO:.0f},{SPIKE_HI:.0f})us "
          f"[actual {n_spikes} = {n_spikes/N:.2%}]")

    # Policy A: send at wake
    A = stats(wake)

    # Policy B: gated Kalman + absolute interpolated deadline
    bh, gated_n = kalman_bias(wake, gated=True)
    exec_res = rng.normal(0.0, SIGMA_EXEC, N)
    B = stats(np.arange(N, dtype=float) * T0 + bh + exec_res)
    conv = next((k for k in range(N)
                 if abs(bh[k] - BIAS0) < 10.0), -1)

    # Policy B2: static bias (first 200 clean ticks: no spike in first window
    # is not guaranteed -> drop ticks whose innovation vs the window median
    # exceeds 3 sigma), then fixed absolute schedule
    y0 = wake[:200] - np.arange(200, dtype=float) * T0
    med = np.median(y0)
    mad = 1.4826 * np.median(np.abs(y0 - med))
    clean = y0[np.abs(y0 - med) <= 3.0 * max(mad, 1e-9)]
    b_static = float(clean.mean())
    B2 = stats(np.arange(N, dtype=float) * T0 + b_static + exec_res)

    # Policy C: Kalman WITHOUT gating (spike corruption ablation)
    bh_c, _ = kalman_bias(wake, gated=False)
    C = stats(np.arange(N, dtype=float) * T0 + bh_c + exec_res)

    red = lambda vb, va: 100.0 * (1.0 - vb / va)
    print("\nvariance of (interval - T0)  [m1, us^2] and of absolute send-time "
          "error [m2, us^2]:")
    print(f"  A  naive wake-send            m1={A[0]:12.1f}  m2={A[1]:12.1f}  "
          f"(std_iv={A[2]:.1f}us, std_abs={A[3]:.1f}us)")
    print(f"  B  Kalman+gate+abs-deadline   m1={B[0]:12.1f}  m2={B[1]:12.1f}  "
          f"(std_iv={B[2]:.1f}us, std_abs={B[3]:.1f}us)")
    print(f"  B2 static abs-deadline        m1={B2[0]:12.1f}  m2={B2[1]:12.1f}  "
          f"(std_iv={B2[2]:.1f}us, std_abs={B2[3]:.1f}us)")
    print(f"  C  Kalman no-gate (ablation)  m1={C[0]:12.1f}  m2={C[1]:12.1f}  "
          f"(std_iv={C[2]:.1f}us, std_abs={C[3]:.1f}us)")

    print("\nvariance reduction vs A [%]:")
    print(f"  B  m1: {red(B[0], A[0]):6.2f}   m2: {red(B[1], A[1]):6.2f}")
    print(f"  B2 m1: {red(B2[0], A[0]):6.2f}   m2: {red(B2[1], A[1]):6.2f}")
    print(f"  C  m1: {red(C[0], A[0]):6.2f}   m2: {red(C[1], A[1]):6.2f}")

    print(f"\nKalman diagnostics: spike-gated observations={gated_n}/{N}, "
          f"bias-hat reaches true bias0+-10us at tick {conv}, "
          f"final bias-hat={bh[-1]:.1f}us vs true final bias="
          f"{BIAS0 + DRIFT*(N-1):.1f}us, static-B2 bias={b_static:.1f}us "
          f"(stale by {BIAS0 + DRIFT*(N-1) - b_static:+.1f}us at end)")

    g1 = red(B[0], A[0]) >= 70.0
    g2 = red(B[1], A[1]) >= 70.0
    print("\nGATES (honest):")
    print(f"  G1 interval-variance reduction (B vs A) >= 70%: {g1}")
    print(f"  G2 absolute-variance reduction (B vs A) >= 70%: {g2}")
    print(f"  G3 gated B beats no-gate C on m2: {B[1] < C[1]}")
    print(f"  G4 Kalman B beats static B2 on m2 (drift tracking value): "
          f"{B[1] < B2[1]}")

    # ---- Scenario 2: the reference clock itself drifts (thermal) ----
    # true phase phi_k = k*T0 + 0.5*c*k^2, c = 5e-6 us/tick^2 (accumulates to
    # ~1000 us over 20k ticks).  Reference for error is the TRUE phase.
    c = 5e-6
    k_arr = np.arange(N, dtype=float)
    phi = k_arr * T0 + 0.5 * c * k_arr ** 2
    wake2 = phi + BIAS0 + jitter + spikes
    exec2 = rng.normal(0.0, SIGMA_EXEC, N)
    send_A2 = wake2
    send_B2s = k_arr * T0 + b_static + exec2                # static schedule
    bh1_s2, _ = kalman_bias(wake2, gated=True)
    send_B1s2 = k_arr * T0 + bh1_s2 + exec2                 # 1-state Kalman
    # (a 2-state [bias, rate] filter was tried and removed: its linear-in-k
    # observation model cannot represent the quadratic clock drift, and
    # subtracting the known drift inside the filter without adding it back
    # at send time left a quadratic residual.  The 1-state random-walk
    # filter with Q=(10us)^2 per tick absorbs the quadratic increment
    # (max ~c*k = 0.1 us/tick << 10 us) and is the correct tracker here.)

    err = lambda s: float(np.var((s - phi) - np.mean(s - phi)))
    print(f"\n--- Scenario 2: reference-clock drift c={c}us/tick^2 "
          f"(accum {0.5*c*(N-1)**2:.0f}us over {N} ticks) ---")
    print("variance of (send - true phase), mean-removed [us^2]:")
    print(f"  A  naive wake-send           {err(send_A2):12.1f}")
    print(f"  B2 static abs-deadline       {err(send_B2s):12.1f}   "
          f"(reduction vs A: {red(err(send_B2s), err(send_A2)):6.2f}%)")
    print(f"  B1 1-state Kalman            {err(send_B1s2):12.1f}   "
          f"(reduction vs A: {red(err(send_B1s2), err(send_A2)):6.2f}%)")
    print("reading: when the reference clock itself drifts, the static "
          "schedule goes stale (negative reduction) while the gated "
          "1-state random-walk Kalman tracks the phase.")
    print("\nGATES (honest) scenario 2:")
    print(f"  G5 1-state Kalman beats static on drifted reference: "
          f"{err(send_B1s2) < err(send_B2s)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
