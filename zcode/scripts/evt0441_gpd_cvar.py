# -*- coding: utf-8 -*-
"""
Task 0441: Extreme Value Theory (EVT) Generalized Pareto Distribution and CVaR-99 Estimation
"""

import sys
import json
import numpy as np
from scipy.optimize import minimize

def generate_tail_queue_delays(N=25000, seed=42):
    """
    Generates heavy-tailed queue latency samples matching iDSN cloud experiments:
    Baseline lognormal latency + Pareto extreme tail spikes
    """
    np.random.seed(seed)
    # Baseline normal download component
    base = np.random.normal(loc=122.0, scale=1.5, size=N)
    
    # Heavy-tailed queuing spike (Pareto tail with shape alpha=3.0)
    # Pareto(a): p(x) = a * m^a / x^(a+1)
    spikes = (np.random.pareto(a=2.8, size=N)) * 0.8
    delays = base + spikes
    return delays

def fit_gpd_mle(excesses):
    """
    Fits GPD parameters (xi, sigma) on excesses y = x - u > 0 via MLE
    log L = -k * ln(sigma) - (1 + 1/xi) * sum ln(1 + xi * y / sigma)
    """
    k = len(excesses)
    # Initial guess via method of moments
    m = np.mean(excesses)
    v = np.var(excesses)
    # For GPD: mean = sigma / (1 - xi), var = sigma^2 / ((1 - xi)^2 * (1 - 2*xi))
    xi_init = 0.1
    sigma_init = m * (1.0 - xi_init)
    
    def neg_log_likelihood(params):
        xi, sigma = params
        if sigma <= 1e-6 or (1.0 - xi) <= 1e-4:
            return 1e12
        term = 1.0 + xi * excesses / sigma
        if np.any(term <= 0):
            return 1e12
        if abs(xi) < 1e-6:
            # Exponential limit
            return k * np.log(sigma) + np.sum(excesses) / sigma
        return k * np.log(sigma) + (1.0 + 1.0 / xi) * np.sum(np.log(term))
        
    res = minimize(neg_log_likelihood, [xi_init, sigma_init], method='Nelder-Mead', tol=1e-8)
    xi_mle, sigma_mle = res.x
    return float(xi_mle), float(sigma_mle), res.success

def compute_evt_cvar(delays, alpha=0.99, threshold_pct=95.0):
    N = len(delays)
    u = float(np.percentile(delays, threshold_pct))
    excesses = delays[delays > u] - u
    Nu = len(excesses)
    
    xi_hat, sigma_hat, success = fit_gpd_mle(excesses)
    
    # Analytical VaR_alpha via GPD
    prob_excess = Nu / N
    factor = (1.0 - alpha) / prob_excess
    var_alpha_gpd = u + (sigma_hat / xi_hat) * ((factor ** (-xi_hat)) - 1.0)
    
    # Analytical CVaR_alpha (Expected Shortfall)
    cvar_alpha_gpd = (var_alpha_gpd + sigma_hat - xi_hat * u) / (1.0 - xi_hat)
    
    # Empirical benchmark
    var_empirical = float(np.percentile(delays, alpha * 100.0))
    cvar_empirical = float(np.mean(delays[delays >= var_empirical]))
    
    rel_error = float(abs(cvar_alpha_gpd - cvar_empirical) / cvar_empirical)
    
    passed = success and (rel_error < 0.05) and (xi_hat > 0.0)
    
    return {
        "total_samples": N,
        "threshold_u": u,
        "excess_count": Nu,
        "gpd_shape_xi": xi_hat,
        "gpd_scale_sigma": sigma_hat,
        "mle_convergence": success,
        "empirical_var_99": var_empirical,
        "empirical_cvar_99": cvar_empirical,
        "analytical_evt_var_99": float(var_alpha_gpd),
        "analytical_evt_cvar_99": float(cvar_alpha_gpd),
        "cvar_relative_error": rel_error,
        "passed": bool(passed)
    }

def main():
    delays = generate_tail_queue_delays(N=30000, seed=2026)
    result = compute_evt_cvar(delays, alpha=0.99, threshold_pct=95.0)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
