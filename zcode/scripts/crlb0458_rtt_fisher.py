# -*- coding: utf-8 -*-
"""
Task 0458: Cramér-Rao Lower Bound (CRLB) and Fisher Information for Nanosecond RTT Delay Estimation
"""

import sys
import json
import numpy as np

def compute_crlb_rtt_estimation(N=200, sigma=12.5, num_mc=6000, seed=42):
    """
    N: number of RTT probe packets
    sigma: measurement noise standard deviation in microseconds
    theta_0 = 15000.0 us (base RTT)
    theta_1 = 0.002 us/s (drift rate)
    """
    np.random.seed(seed)
    theta_true = np.array([15000.0, 0.002])
    
    # Elapsed time vector Delta t_k over 10 seconds
    dt_vec = np.linspace(0.0, 10.0, N)
    X = np.column_stack([np.ones(N), dt_vec])
    
    # Analytical Fisher Information Matrix FIM = X^T X / sigma^2
    FIM = (X.T @ X) / (sigma ** 2)
    CRLB = np.linalg.inv(FIM)
    crlb_theta0 = float(CRLB[0, 0])
    crlb_theta1 = float(CRLB[1, 1])
    
    # Monte Carlo simulation of MLE estimator
    # y = X @ theta + noise
    noise = sigma * np.random.randn(num_mc, N)
    y_all = X @ theta_true + noise # (num_mc, N)
    
    # OLS / MLE estimates: theta_hat = (X^T X)^-1 X^T y
    XtX_inv_Xt = np.linalg.inv(X.T @ X) @ X.T # (2, N)
    theta_hats = (XtX_inv_Xt @ y_all.T).T # (num_mc, 2)
    
    # Empirical bias and variance
    mean_theta0 = float(np.mean(theta_hats[:, 0]))
    bias_theta0 = float(abs(mean_theta0 - theta_true[0]))
    var_emp_theta0 = float(np.var(theta_hats[:, 0], ddof=1))
    
    mean_theta1 = float(np.mean(theta_hats[:, 1]))
    bias_theta1 = float(abs(mean_theta1 - theta_true[1]))
    var_emp_theta1 = float(np.var(theta_hats[:, 1], ddof=1))
    
    ratio_theta0 = var_emp_theta0 / crlb_theta0
    ratio_theta1 = var_emp_theta1 / crlb_theta1
    
    efficiency_theta0 = float(min(1.0, 1.0 / ratio_theta0)) * 100.0
    
    # Check if ratio in [0.95, 1.05]
    passed = (0.95 <= ratio_theta0 <= 1.05) and (efficiency_theta0 >= 95.0) and (bias_theta0 < 0.1)
    
    return {
        "probe_packets_N": N,
        "noise_std_us": sigma,
        "monte_carlo_trials": num_mc,
        "analytical_crlb_variance_theta0": crlb_theta0,
        "empirical_variance_theta0": var_emp_theta0,
        "crlb_ratio_theta0": ratio_theta0,
        "estimator_efficiency_percent": efficiency_theta0,
        "mle_bias_theta0_us": bias_theta0,
        "mle_bias_theta1_drift": bias_theta1,
        "unbiased_efficiency_target_met": passed,
        "passed": bool(passed)
    }

def main():
    result = compute_crlb_rtt_estimation(N=250, sigma=10.0, num_mc=8000, seed=2026)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
