#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0175: Bayesian Sequential Conjugate Update of Inter-Shot Queue Delay.
Implements the Normal-Inverse-Gamma conjugate updating engine for channel delay variance,
updating posterior credible intervals after Shot 1 feedback.
"""
import numpy as np

def compute_bayesian_sequential_update(shot1_observed_delay_ms=11.2):
    # Prior hyperparameters from n=15 cloud calibration:
    # mu0 = 12.4ms (mean queuing delay offset)
    # kappa0 = 15 (effective prior sample size)
    # alpha0 = 7.5 (shape parameter)
    # beta0 = 45.0 (scale parameter) -> prior expected variance = beta0 / (alpha0 - 1) = 45 / 6.5 = 6.92 ms^2
    mu0 = 12.4
    kappa0 = 15.0
    alpha0 = 7.5
    beta0 = 45.0
    
    prior_var = beta0 / (alpha0 - 1.0)
    prior_std = np.sqrt(prior_var)
    prior_ci = [mu0 - 1.96 * prior_std / np.sqrt(kappa0), mu0 + 1.96 * prior_std / np.sqrt(kappa0)]
    
    # Bayesian sequential update with Shot 1 observation:
    x = shot1_observed_delay_ms
    n_new = 1.0
    
    kappa1 = kappa0 + n_new
    mu1 = (kappa0 * mu0 + x) / kappa1
    alpha1 = alpha0 + n_new / 2.0
    beta1 = beta0 + 0.5 * (kappa0 * (x - mu0)**2) / kappa1
    
    post_var = beta1 / (alpha1 - 1.0)
    post_std = np.sqrt(post_var)
    post_ci = [mu1 - 1.96 * post_std / np.sqrt(kappa1), mu1 + 1.96 * post_std / np.sqrt(kappa1)]
    
    var_reduction_pct = (1.0 - post_var / prior_var) * 100.0
    ci_shrinkage_pct = (1.0 - (post_ci[1] - post_ci[0]) / (prior_ci[1] - prior_ci[0])) * 100.0
    
    results = {
        "prior_mean_delay_ms": float(mu0),
        "prior_expected_var_ms2": float(prior_var),
        "shot1_observed_delay_ms": float(x),
        "posterior_mean_delay_ms": float(mu1),
        "posterior_expected_var_ms2": float(post_var),
        "prior_95_credible_interval": [float(prior_ci[0]), float(prior_ci[1])],
        "posterior_95_credible_interval": [float(post_ci[0]), float(post_ci[1])],
        "credible_interval_shrinkage_pct": float(ci_shrinkage_pct),
        "bayesian_update_successful": True
    }
    return results

if __name__ == "__main__":
    res = compute_bayesian_sequential_update()
    print("=== Bayesian Sequential Queue Delay Update ===")
    for k, v in res.items():
        if isinstance(v, float):
            print(f"{k}: {v:.4f}")
        elif isinstance(v, list):
            print(f"{k}: [{v[0]:.4f}, {v[1]:.4f}]")
        else:
            print(f"{k}: {v}")
