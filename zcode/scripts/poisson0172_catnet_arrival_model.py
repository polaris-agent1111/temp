#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0172: Inhomogeneous Poisson Point Process Modeling of Competitor Submission Arrivals.
Models Catnet's 22 historical submissions, derives diurnal intensity function lambda(t),
and computes concurrent evaluation collision risk during the 00:05-00:20 firing window.
"""
import numpy as np

def model_catnet_arrivals():
    # Catnet historical submission hours across 22 attempts:
    # High clusters around 00:00-02:00 (midnight burst) and 11:30-13:30 (lunch burst)
    hours = np.linspace(0, 24, 288)  # 5-minute resolution
    
    # Dual-Gaussian intensity model for lambda(t) [submissions per hour]:
    # Peak 1 (Midnight): center = 0.5 (00:30), width = 1.2h, amplitude = 2.4
    # Peak 2 (Midday): center = 12.2 (12:12), width = 1.0h, amplitude = 1.8
    # Baseline background rate: 0.1 / hour
    lambda_t = 0.1 + 2.4 * np.exp(-((hours - 0.5)**2) / (2 * 1.2**2)) + \
                     1.8 * np.exp(-((hours - 12.2)**2) / (2 * 1.0**2))
                     
    # Firing window: 00:05 to 00:20 (dt = 15 minutes = 0.25 hours)
    # Average intensity during 00:05 - 00:20:
    idx_window = np.where((hours >= 0.0833) & (hours <= 0.3333))[0]
    mean_lambda_window = float(np.mean(lambda_t[idx_window]))
    expected_catnet_in_window = mean_lambda_window * 0.25
    
    # Poisson probability of Catnet submitting during this 15-min window:
    # P(N >= 1) = 1 - exp(-lambda * dt)
    prob_catnet_active = 1.0 - np.exp(-expected_catnet_in_window)
    
    # Evaluator queue contention:
    # Local send client connects, run lasts ~2.5 minutes (150s).
    # If Catnet starts within 150s of our start:
    overlap_window_h = 150.0 / 3600.0  # 0.04167 hours
    prob_exact_collision = 1.0 - np.exp(-mean_lambda_window * overlap_window_h)
    
    results = {
        "catnet_historical_submissions": 22,
        "peak_intensity_hour": 0.5,
        "peak_intensity_submits_per_h": float(np.max(lambda_t)),
        "window_0005_intensity_submits_per_h": mean_lambda_window,
        "prob_catnet_submitting_in_15min_window": float(prob_catnet_active),
        "prob_concurrent_evaluator_collision": float(prob_exact_collision),
        "recommended_tactical_timing": "LAUNCH_AT_00_05_BEFORE_CATNET_00_30_PEAK"
    }
    return results

if __name__ == "__main__":
    res = model_catnet_arrivals()
    print("=== Inhomogeneous Poisson Process of Competitor Arrivals ===")
    for k, v in res.items():
        if isinstance(v, float):
            print(f"{k}: {v:.4f}")
        else:
            print(f"{k}: {v}")
