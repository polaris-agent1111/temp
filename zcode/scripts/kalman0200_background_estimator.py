#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0200: Online 1D Kalman Filter estimator for background traffic congestion intensity.
Recursively estimates true network congestion state from noisy official test duration feedbacks.
Validates >= 40% MSE reduction relative to raw noisy measurements.
"""
import numpy as np

def run_kalman_filter_simulation():
    np.random.seed(2026)
    # Number of sequential steps (observations across tests)
    T = 20
    
    # Ground truth background cross-traffic load (arbitrary units, e.g. delay contribution in seconds)
    # Underlying slow drift with sudden step shift at t=10
    true_state = np.zeros(T)
    for t in range(T):
        if t < 10:
            true_state[t] = 15.0 + 0.2 * t
        else:
            true_state[t] = 22.0 - 0.15 * (t - 10)
            
    # Measurement noise: heavy random jitter due to random seeds and cross-traffic burstiness
    measurement_noise_std = 3.5
    measurements = true_state + np.random.normal(0, measurement_noise_std, T)
    
    # 1D Kalman Filter parameters
    # State equation: x_t = x_{t-1} + w_t, w_t ~ N(0, Q)
    # Measurement equation: z_t = x_t + v_t, v_t ~ N(0, R)
    Q = 0.5**2       # Process variance (slow system drift)
    R = measurement_noise_std**2  # Measurement variance
    
    # Initial state estimate
    x_hat = 15.0
    P = 10.0  # Initial estimation error variance
    
    estimates = np.zeros(T)
    estimated_vars = np.zeros(T)
    
    for t in range(T):
        # 1. Prediction step:
        x_hat_minus = x_hat
        P_minus = P + Q
        
        # 2. Update step:
        K = P_minus / (P_minus + R)  # Kalman Gain
        x_hat = x_hat_minus + K * (measurements[t] - x_hat_minus)
        P = (1.0 - K) * P_minus
        
        estimates[t] = x_hat
        estimated_vars[t] = P
        
    # Compute Mean Squared Errors (MSE)
    raw_mse = np.mean((measurements - true_state)**2)
    kalman_mse = np.mean((estimates - true_state)**2)
    mse_reduction_pct = (raw_mse - kalman_mse) / raw_mse * 100.0
    
    print("=== Task 0200: Online Kalman Filter Background Estimator ===")
    print(f"steps_simulated: {T}")
    print(f"raw_measurement_mse: {raw_mse:.4f} s^2")
    print(f"kalman_estimated_mse: {kalman_mse:.4f} s^2")
    print(f"mse_reduction: {mse_reduction_pct:.2f}% (Gate: >= 40%)")
    print(f"final_kalman_gain: {K:.4f}")
    print(f"final_state_error_std: {np.sqrt(P):.4f} s")
    print(f"estimator_gate_passed: {mse_reduction_pct >= 40.0}")
    
    return {
        "raw_mse": float(raw_mse),
        "kalman_mse": float(kalman_mse),
        "mse_reduction_pct": float(mse_reduction_pct),
        "gate_passed": bool(mse_reduction_pct >= 40.0)
    }

if __name__ == "__main__":
    run_kalman_filter_simulation()
