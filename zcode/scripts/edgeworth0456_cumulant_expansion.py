# -*- coding: utf-8 -*-
"""
Task 0456: Higher-Order Cumulants and Edgeworth Expansion for Queuing Latency Distribution
"""

import sys
import json
import numpy as np
from scipy.stats import norm, skew, kurtosis

def hermite_poly(k, x):
    """
    Probabilists' Hermite polynomials:
    H2(x) = x^2 - 1
    H3(x) = x^3 - 3*x
    H5(x) = x^5 - 10*x^3 + 15*x
    """
    if k == 2:
        return x ** 2 - 1.0
    elif k == 3:
        return x ** 3 - 3.0 * x
    elif k == 5:
        return x ** 5 - 10.0 * (x ** 3) + 15.0 * x
    else:
        raise ValueError(f"Hermite polynomial H{k} not implemented")

def generate_queuing_sums(N=35000, n=16, seed=42):
    """
    Generates sum of n independent queuing delays with positive skewness and kurtosis
    (Gamma distribution with shape k=3.0, scale theta=2.0)
    """
    np.random.seed(seed)
    shape_k = 3.5
    scale_theta = 2.0
    
    # Each sample is the sum of n packet latencies
    samples = np.random.gamma(shape=shape_k, scale=scale_theta, size=(N, n))
    sums = np.sum(samples, axis=1)
    
    # Ground truth single-packet cumulants:
    # Mean = k * theta, Var = k * theta^2, Skewness = 2 / sqrt(k), Kurtosis = 6 / k
    gamma1_single = 2.0 / np.sqrt(shape_k)
    gamma2_single = 6.0 / shape_k
    
    mu_total = n * shape_k * scale_theta
    sigma_total = np.sqrt(n * shape_k * (scale_theta ** 2))
    
    # Normalized standard variable Z
    Z = (sums - mu_total) / sigma_total
    
    return Z, n, gamma1_single, gamma2_single

def compute_edgeworth_cdf(x_grid, n, gamma1, gamma2):
    """
    F_edge(x) = Phi(x) - phi(x) * [ (gamma1 / (6*sqrt(n))) * H2(x) + (gamma2 / (24*n)) * H3(x) + (gamma1^2 / (72*n)) * H5(x) ]
    """
    phi_x = norm.pdf(x_grid)
    Phi_x = norm.cdf(x_grid)
    
    term1 = (gamma1 / (6.0 * np.sqrt(n))) * hermite_poly(2, x_grid)
    term2 = (gamma2 / (24.0 * n)) * hermite_poly(3, x_grid)
    term3 = ((gamma1 ** 2) / (72.0 * n)) * hermite_poly(5, x_grid)
    
    correction = phi_x * (term1 + term2 + term3)
    F_edge = Phi_x - correction
    return np.clip(F_edge, 0.0, 1.0)

def main():
    Z, n, g1, g2 = generate_queuing_sums(N=40000, n=16, seed=2026)
    
    # Empirical CDF evaluation on grid
    x_grid = np.linspace(-3.5, 3.5, 500)
    F_emp = np.array([np.mean(Z <= x) for x in x_grid])
    F_norm = norm.cdf(x_grid)
    F_edge = compute_edgeworth_cdf(x_grid, n, g1, g2)
    
    # Errors
    ks_norm = float(np.max(np.abs(F_norm - F_emp)))
    ks_edge = float(np.max(np.abs(F_edge - F_emp)))
    
    ks_goodness_of_fit = (1.0 - ks_edge) * 100.0
    cumulant_error = float(abs(kurtosis(Z) - g2 / n))
    
    passed = (ks_goodness_of_fit >= 99.0) and (ks_edge < 0.01) and (ks_edge < ks_norm)
    
    result = {
        "packets_per_burst_n": n,
        "single_packet_skewness": g1,
        "single_packet_kurtosis": g2,
        "standard_normal_ks_distance": ks_norm,
        "edgeworth_expansion_ks_distance": ks_edge,
        "edgeworth_goodness_of_fit": ks_goodness_of_fit,
        "cumulant_expansion_residual": cumulant_error,
        "ks_improvement_ratio": float(ks_norm / max(1e-6, ks_edge)),
        "passed": bool(passed)
    }
    
    print(json.dumps(result, indent=2))
    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
