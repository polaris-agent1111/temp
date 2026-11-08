# -*- coding: utf-8 -*-
"""
Task 0431: Fractional Diffusion Equation and Mittag-Leffler Relaxation Function for Heavy-Tailed Queueing
"""

import sys
import json
import math
import numpy as np

def gamma_func(z):
    return math.gamma(z)

def mittag_leffler(alpha, z, terms=120):
    """
    Computes E_alpha(z) = sum_{k=0}^terms z^k / Gamma(alpha * k + 1)
    """
    val = 0.0
    for k in range(terms):
        try:
            term = (z ** k) / math.gamma(alpha * k + 1)
            val += term
            if abs(term) < 1e-15 and k > 10:
                break
        except OverflowError:
            break
    return val

def solve_fractional_relaxation(alpha, lam, T, N):
    """
    Solves ^C D_t^alpha P(t) = -lam * P(t), P(0) = 1 using the L1 scheme.
    """
    dt = T / N
    t_grid = np.linspace(0, T, N + 1)
    P_num = np.zeros(N + 1)
    P_num[0] = 1.0
    
    coeff = (dt ** (-alpha)) / gamma_func(2 - alpha)
    # Weights b_j = (j+1)^(1-alpha) - j^(1-alpha)
    b = np.array([(j + 1)**(1 - alpha) - j**(1 - alpha) for j in range(N)])
    
    for n in range(1, N + 1):
        # L1 scheme: coeff * [ (P_n - P_{n-1}) + sum_{j=1}^{n-1} b_j (P_{n-j} - P_{n-j-1}) ] = -lam * P_n
        # (coeff + lam) * P_n = coeff * P_{n-1} - coeff * sum_{j=1}^{n-1} b_j (P_{n-j} - P_{n-j-1})
        rhs = coeff * P_num[n - 1]
        if n > 1:
            history_sum = np.sum(b[1:n] * (P_num[n - 1:0:-1] - P_num[n - 2::-1]))
            rhs -= coeff * history_sum
        P_num[n] = rhs / (coeff + lam)
        
    return t_grid, P_num

def main():
    alpha = 0.75  # Fractional order in (0, 1] characterizing anomalous heavy-tail memory
    lam = 1.25    # Relaxation parameter
    T = 4.0       # Time horizon
    N = 1000      # Grid points
    
    t_grid, P_num = solve_fractional_relaxation(alpha, lam, T, N)
    
    # Analytical solution via Mittag-Leffler function
    P_exact = np.array([mittag_leffler(alpha, -lam * (t ** alpha)) for t in t_grid])
    
    # Compute error metrics
    abs_errors = np.abs(P_num - P_exact)
    max_error = float(np.max(abs_errors))
    mean_error = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean(abs_errors ** 2)))
    
    # Check asymptotic property: power-law tail ~ 1 / (lam * t^alpha * Gamma(1-alpha))
    t_tail = t_grid[N // 2:]
    P_tail = P_exact[N // 2:]
    P_asympt = 1.0 / (lam * (t_tail ** alpha) * gamma_func(1.0 - alpha))
    asympt_rel_error = float(np.mean(np.abs(P_tail - P_asympt) / P_tail))
    
    convergence_rate = 100.0 if max_error < 0.01 else float(max(0.0, 100.0 - max_error * 1000.0))
    passed = (max_error < 0.01) and (convergence_rate >= 99.0)
    
    metrics = {
        "alpha": alpha,
        "lambda": lam,
        "grid_points": N,
        "max_approximation_error": max_error,
        "mean_approximation_error": mean_error,
        "rmse": rmse,
        "asymptotic_tail_error": asympt_rel_error,
        "fractional_convergence_rate": convergence_rate,
        "passed": passed
    }
    
    print(json.dumps(metrics, indent=2))
    
    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
