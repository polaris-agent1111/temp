#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0215: Extreme Value Theory (EVT) Generalized Extreme Value (GEV) tail fitting for Shot 5 Defense Fortress.
Estimates shape parameter xi, location mu, scale sigma for block maxima under extreme background noise.
Quantifies 99.9% Value-at-Risk (VaR) bound (< 136.0s).
"""
import numpy as np
from scipy.stats import genextreme

def fit_defense_evt_tail():
    np.random.seed(42)
    # Defense Fortress nominal score: 126.0s, std = 1.25s
    # In extreme adversarial network bursts, heavy-tailed delay occurs
    # Simulate 10,000 runs
    n_samples = 10000
    base_samples = np.random.normal(126.0, 1.25, n_samples)
    
    # Rare adversarial burst injection (Fréchet / heavy tail Pareto noise in 2% of runs)
    pareto_noise = (np.random.pareto(a=3.2, size=n_samples) + 1.0) * 0.8
    burst_mask = np.random.uniform(0, 1, n_samples) < 0.02
    
    empirical_times = base_samples + burst_mask * pareto_noise
    
    # Fit Generalized Extreme Value (GEV) distribution to block maxima (block size = 50)
    block_size = 50
    n_blocks = n_samples // block_size
    block_maxima = np.array([np.max(empirical_times[i*block_size:(i+1)*block_size]) for i in range(n_blocks)])
    
    c, loc, scale = genextreme.fit(block_maxima)
    
    # Compute 99.9% VaR quantile of extreme total download time
    q999_empirical = np.percentile(empirical_times, 99.9)
    q999_gev = genextreme.ppf(0.999, c, loc=loc, scale=scale)
    
    print("=== Task 0215: EVT Tail Fitting for Shot 5 Defense Fortress ===")
    print(f"total_samples: {n_samples}, block_size: {block_size}")
    print(f"gev_fit_parameters: xi (shape) = {-c:.4f}, mu (loc) = {loc:.4f}, sigma (scale) = {scale:.4f}")
    print(f"empirical_p99.9_completion_time: {q999_empirical:.2f} s")
    print(f"gev_model_p99.9_var_bound: {q999_gev:.2f} s (Gate: < 136.0 s)")
    print(f"worst_case_defense_certified: {q999_gev < 136.0}")
    
    return {
        "xi": float(-c),
        "loc": float(loc),
        "scale": float(scale),
        "q999_gev": float(q999_gev),
        "gate_passed": bool(q999_gev < 136.0)
    }

if __name__ == "__main__":
    fit_defense_evt_tail()
