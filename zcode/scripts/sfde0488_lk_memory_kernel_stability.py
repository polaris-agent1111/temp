# -*- coding: utf-8 -*-
"""
Task 0488: Stochastic Functional Differential Equation with Infinite-Delay
Memory Kernel -- Lyapunov-Krasovskii Functional Stability Bound for Queueing.

Model (stylized queue with infinite memory of past backlog):
    dq/dt = -a*q(t) + b*C(t) + sigma*q(t)*xi(t),     C(t) = int_0^inf K(s) q(t-s) ds
    K(s) = lambda * exp(-lambda * s)                  (infinite support, int K = 1)

Infinite delay is handled EXACTLY (no truncation) by the linear chain trick:
    dC/dt = lambda * (q(t) - C(t))
Augmented state (q, C, P, J):
    dP/dt = lambda*(q^2 - P),  P(t) = int K(s) q(t-s)^2 ds
    dJ/dt = q^2 - P,           J(t) = int K(s) int_{t-s}^t q(u)^2 du ds

Lyapunov-Krasovskii functional:
    V(t) = q(t)^2 / 2 + (b/2) * J(t)
Dissipation identity (deterministic part):
    dV/dt = -(a-b)*q^2 - (b/2) * int K(s) [q(t)-q(t-s)]^2 ds  <=  0   for a >= b
Stochastic (Ito, multiplicative noise): E[V] decays strictly iff a > b + sigma^2/2.

Checks (targets: LK monotone decay rate 100.0%, memory convolution residual < 1e-4):
  1. Kernel integral residual: Gauss-Laguerre quadrature of int K ds vs 1.
  2. Chain-vs-quadrature convolution residual: C_chain(t) vs direct quadrature.
  3. Dissipation-identity residual: numeric dV/dt vs closed form.
  4. Exact-solution residual: numerical V(t) vs analytic V(t).
  5. LK monotone decay: deterministic V strictly decreasing at 100% of steps;
     Monte-Carlo E[V] strictly decreasing at 100% of checkpoints.
Writes nothing; prints JSON verdict only.
"""

import sys
import json
import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

A, B, SIGMA, LAM = 2.0, 1.0, 0.6, 4.0
Q0 = 1.0
DT = 1e-3
T_DET = 3.0
T_STO = 2.0
N_PATHS = 16000
CHECK_STRIDE = 0.05          # checkpoint spacing for E[V] monotonicity
SEED = 20261108
S1 = -3.0 + np.sqrt(5.0)     # dominant characteristic root for (a,b,lam)=(2,1,4)


def phi(theta):
    """Infinite past history: q(theta) = exp(s1*theta), theta <= 0."""
    return np.exp(S1 * theta)


def laguerre_nodes(n=64):
    """Nodes/weights for int_0^inf lambda*exp(-lambda*s) f(s) ds ~ sum w_i f(x_i/lam)."""
    from scipy.special import roots_genlaguerre
    x, w = roots_genlaguerre(n, 0.0)
    return x / LAM, w  # s_i, weight in s-domain (sum w_i = 1)


def rhs_det(q, C, P, J):
    return (-A * q + B * C, LAM * (q - C), LAM * (q * q - P), q * q - P)


def rk4_step(state, h):
    q, C, P, J = state
    k1 = rhs_det(q, C, P, J)
    k2 = rhs_det(*(s + 0.5 * h * d for s, d in zip(state, k1)))
    k3 = rhs_det(*(s + 0.5 * h * d for s, d in zip(state, k2)))
    k4 = rhs_det(*(s + h * d for s, d in zip(state, k3)))
    return tuple(s + (h / 6.0) * (d1 + 2 * d2 + 2 * d3 + d4)
                 for s, d1, d2, d3, d4 in zip(state, k1, k2, k3, k4))


def vfun(q, J):
    return 0.5 * q * q + 0.5 * B * J


def dvdt_closed(q, C, P):
    """-(a-b) q^2 - (b/2) (q^2 - 2 q C + P)."""
    return -(A - B) * q * q - 0.5 * B * (q * q - 2.0 * q * C + P)


def main():
    res = {}

    # ---- 1. kernel integral residual (Gauss-Laguerre) --------------------
    # int_0^inf K(s) ds = int_0^inf lambda e^{-lambda s} ds = int_0^inf e^{-x} dx ~ sum w_i
    s_nodes, w_nodes = laguerre_nodes(64)
    ker_int = float(np.sum(w_nodes))
    ker_res = abs(ker_int - 1.0)
    res["kernel_integral_value"] = ker_int
    res["kernel_integral_residual"] = ker_res

    # ---- deterministic trajectory (RK4) ----------------------------------
    n_det = int(round(T_DET / DT))
    state = (Q0 * np.ones(()), phi(0.0) * 0 + LAM / (LAM + S1),  # C(0) = lam/(lam+s1)
             LAM / (LAM + 2.0 * S1),                             # P(0)
             1.0 / (LAM + 2.0 * S1))                             # J(0) (b=1 case)
    # note: analytic J(0) = int K(s) int_{-s}^0 e^{2 s1 u} du ds = 1/(lam+2 s1)
    qs, Cs, Ps, Js = [state[0]], [state[1]], [state[2]], [state[3]]
    for _ in range(n_det):
        state = rk4_step(state, DT)
        qs.append(state[0]); Cs.append(state[1]); Ps.append(state[2]); Js.append(state[3])
    qs = np.asarray(qs); Cs = np.asarray(Cs); Ps = np.asarray(Ps); Js = np.asarray(Js)
    ts = np.arange(n_det + 1) * DT
    Vs = vfun(qs, Js)

    # ---- 5a. deterministic LK monotone decay rate -------------------------
    dec = np.diff(Vs)
    det_monotone_rate = float(np.mean(dec < 0.0) * 100.0)
    res["det_lk_monotone_decay_rate_pct"] = det_monotone_rate
    res["det_lk_strict_decrease_steps"] = int(np.sum(dec < 0.0))
    res["det_lk_total_steps"] = int(len(dec))

    # ---- 3. dissipation-identity residual (central difference) ------------
    h = 1e-5
    idx = np.arange(1, n_det, 50)
    dv_num = (Vs[idx + 1] - Vs[idx - 1]) / (2 * DT)
    dv_frm = dvdt_closed(qs[idx], Cs[idx], Ps[idx])
    dissip_res = float(np.max(np.abs(dv_num - dv_frm)))
    res["dissipation_identity_max_residual"] = dissip_res
    res["dissipation_identity_max_dvdt"] = float(np.max(dv_frm))
    res["dissipation_identity_negative_frac_pct"] = float(np.mean(dv_frm < 0) * 100.0)

    # ---- 4. exact-solution residual ---------------------------------------
    # V_exact(t) = exp(2 s1 t) * (1/2 + (b/2) / (lam + 2 s1))
    v_exact = np.exp(2 * S1 * ts) * (0.5 + 0.5 * B / (LAM + 2.0 * S1))
    exact_res = float(np.max(np.abs(Vs - v_exact)))
    q_exact = Q0 * np.exp(S1 * ts)
    q_res = float(np.max(np.abs(qs - q_exact)))
    res["exact_solution_V_max_residual"] = exact_res
    res["exact_solution_q_max_residual"] = q_res

    # ---- 2. chain-vs-quadrature convolution residual ----------------------
    # C_quad(t) = sum w_i q(t - s_i), s_i = x_i / lam, using exact history for
    # t-s_i <= 0 and linear interpolation of the numerical trajectory otherwise.
    conv_res = 0.0
    for t_chk in np.arange(0.5, T_DET + 1e-9, 0.5):
        k = int(round(t_chk / DT))
        past_t = t_chk - s_nodes
        qv = np.where(past_t <= 0.0, phi(past_t), np.interp(past_t, ts, qs))
        c_quad = float(np.sum(w_nodes * qv))
        conv_res = max(conv_res, abs(c_quad - float(Cs[k])))
    res["chain_vs_quadrature_conv_max_residual"] = conv_res

    # ---- 5b. stochastic Monte Carlo: E[V] monotone decay -------------------
    rng = np.random.default_rng(SEED)
    n_sto = int(round(T_STO / DT))
    q = np.full(N_PATHS, Q0)
    C = np.full(N_PATHS, LAM / (LAM + S1))
    P = np.full(N_PATHS, LAM / (LAM + 2.0 * S1))
    J = np.full(N_PATHS, 1.0 / (LAM + 2.0 * S1))
    sqdt = np.sqrt(DT)
    chk_every = int(round(CHECK_STRIDE / DT))
    eV_prev = float(np.mean(vfun(q, J)))
    eV_trace = [eV_prev]
    increases = 0
    for step in range(1, n_sto + 1):
        dW = rng.standard_normal(N_PATHS) * sqdt
        q, C, P, J = (q + (-A * q + B * C) * DT + SIGMA * q * dW,
                      C + LAM * (q - C) * DT,
                      P + LAM * (q * q - P) * DT,
                      J + (q * q - P) * DT)
        if step % chk_every == 0:
            eV = float(np.mean(vfun(q, J)))
            if eV >= eV_prev:
                increases += 1
            eV_prev = eV
            eV_trace.append(eV)
    n_chk = len(eV_trace) - 1
    mc_monotone_rate = (1.0 - increases / n_chk) * 100.0
    res["mc_paths"] = N_PATHS
    res["mc_checkpoints"] = n_chk
    res["mc_E_V_monotone_decay_rate_pct"] = mc_monotone_rate
    res["mc_E_V_first"] = eV_trace[0]
    res["mc_E_V_last"] = eV_trace[-1]
    res["ito_stability_margin_a_b_sigma2"] = A - B - 0.5 * SIGMA ** 2

    # ---- gates -------------------------------------------------------------
    max_conv_res = max(ker_res, conv_res, dissip_res, exact_res, q_res)
    res["memory_convolution_residual_max"] = max_conv_res
    res["lk_monotone_decay_rate_pct_min"] = min(det_monotone_rate, mc_monotone_rate)
    res["passed"] = bool(
        res["lk_monotone_decay_rate_pct_min"] == 100.0
        and max_conv_res < 1e-4
        and res["dissipation_identity_negative_frac_pct"] == 100.0
    )
    print(json.dumps(res, indent=2))
    if not res["passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
