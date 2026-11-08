# -*- coding: utf-8 -*-
"""
Task 0461: Logarithmic Dynamic Quantizer Design and Sector Bounded Feedback Stabilization
"""

import sys
import json
import numpy as np

def logarithmic_quantizer(x, rho=0.85, u0=20.0, num_levels=30):
    """
    Logarithmic quantizer q(x):
    Thresholds: t_i = (1 + rho) / 2 * u_i
    Levels: u_i = rho^i * u0
    Sector bound: |q(x) - x| <= delta * |x|, where delta = (1 - rho) / (1 + rho)
    """
    delta = (1.0 - rho) / (1.0 + rho)
    sgn = np.sign(x)
    mag = np.abs(x)
    
    # Vectorized quantization
    q_mag = np.zeros_like(mag, dtype=float)
    nonzero = mag > 1e-6
    
    if np.any(nonzero):
        m = mag[nonzero]
        # Exact arithmetic threshold quantization
        # t_i = (1 + rho) / 2 * u0 * rho^i
        # i = ceil( log( m / ( (1+rho)/2 * u0 ) ) / log(rho) )
        scaled_m = m / (((1.0 + rho) / 2.0) * u0)
        i_idx = np.ceil(np.log(scaled_m) / np.log(rho))
        i_idx = np.clip(i_idx, 0, num_levels)
        q_mag[nonzero] = u0 * (rho ** i_idx)
        
    return sgn * q_mag, delta

def simulate_quantized_feedback(A=0.85, B=0.4, K=-1.2, rho=0.85, steps=60, seed=42):
    """
    x_{k+1} = A * x_k + B * K * q(x_k)
    """
    np.random.seed(seed)
    delta = (1.0 - rho) / (1.0 + rho)
    
    # Dynamic range [0.05, 15.0] fully covered by u0=25.0, num_levels=50
    x_test = np.linspace(-15.0, 15.0, 1000)
    q_test, _ = logarithmic_quantizer(x_test, rho=rho, u0=25.0, num_levels=50)
    
    valid_range = (np.abs(x_test) >= 0.05) & (np.abs(x_test) <= 15.0)
    errors = np.abs(q_test[valid_range] - x_test[valid_range])
    bounds = delta * np.abs(x_test[valid_range])
    
    sector_bounded = bool(np.all(errors <= bounds + 1e-5))
    sector_compliance_rate = float(np.mean(errors <= bounds + 1e-5)) * 100.0
    
    # Closed loop trajectory
    x = 12.5  # initial state
    traj = [x]
    for k in range(steps):
        q_x, _ = logarithmic_quantizer(np.array([x]), rho=rho, u0=25.0, num_levels=50)
        x_next = A * x + B * K * float(q_x[0])
        traj.append(x_next)
        x = x_next
        
    final_state = float(abs(traj[-1]))
    asymptotically_stable = bool(final_state < 0.05)
    
    max_sector_residual = float(np.max(np.maximum(0.0, errors - bounds)))
    
    passed = (sector_compliance_rate >= 99.9) and asymptotically_stable and (max_sector_residual < 0.005)
    
    return {
        "quantizer_density_rho": rho,
        "sector_bound_delta": delta,
        "sector_bounded_holds": sector_bounded,
        "sector_compliance_rate": sector_compliance_rate,
        "max_sector_residual": max_sector_residual,
        "initial_state": traj[0],
        "final_state_after_steps": final_state,
        "asymptotically_stable": asymptotically_stable,
        "passed": bool(passed)
    }

def main():
    result = simulate_quantized_feedback(A=0.85, B=0.4, K=-1.2, rho=0.85, steps=60, seed=2026)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
