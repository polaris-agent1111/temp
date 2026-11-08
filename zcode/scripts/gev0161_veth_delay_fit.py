#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0161: GEV Extreme Value Distribution Fitting of veth Pair Latency.
Analyzes microsecond virtualization jitter overhead in Containernet testbeds,
fitting shape (xi), scale (sigma), and location (mu) parameters.
"""
import numpy as np
import scipy.stats as stats

def fit_gev_veth_delay():
    # Simulated 10,000 latency measurements across veth pair under 100 Mbps load
    rng = np.random.default_rng(42)
    
    # Base latency = 12 microseconds, with heavy-tailed scheduling/interrupt jitter
    # Modeled via Fréchet / GEV with shape parameter xi > 0 (heavy tail)
    true_xi = 0.18
    true_mu = 14.5  # us
    true_sigma = 3.2  # us
    
    delays_us = stats.genextreme.rvs(c=-true_xi, loc=true_mu, scale=true_sigma, size=10000, random_state=rng)
    delays_us = np.maximum(5.0, delays_us)
    
    # Fit GEV distribution
    fit_params = stats.genextreme.fit(delays_us)
    fit_xi = -fit_params[0]  # Scipy convention has opposite sign
    fit_mu = fit_params[1]
    fit_sigma = fit_params[2]
    
    p95_delay = float(np.percentile(delays_us, 95))
    p99_delay = float(np.percentile(delays_us, 99))
    max_delay = float(np.max(delays_us))
    
    # Overhead on pacing interval (pacing interval = 4000us):
    # Jitter ratio = p99_delay / 4000us
    jitter_ratio = (p99_delay - fit_mu) / 4000.0
    
    results = {
        "fitted_shape_xi": float(fit_xi),
        "fitted_location_mu_us": float(fit_mu),
        "fitted_scale_sigma_us": float(fit_sigma),
        "p95_latency_us": p95_delay,
        "p99_latency_us": p99_delay,
        "max_latency_us": max_delay,
        "jitter_impact_on_4ms_pacing_pct": float(jitter_ratio * 100.0),
        "virtualization_overhead_tolerated": bool(jitter_ratio < 0.01)
    }
    return results

if __name__ == "__main__":
    res = fit_gev_veth_delay()
    print("=== veth Pair GEV Latency Distribution Fitting ===")
    for k, v in res.items():
        if isinstance(v, float):
            print(f"{k}: {v:.4f}")
        else:
            print(f"{k}: {v}")
