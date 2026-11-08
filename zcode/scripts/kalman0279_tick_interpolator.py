#!/usr/bin/env python3
"""
Task 0279: Adaptive Pacing Tick Dynamic Interpolation Filter Under Extreme Jitter
Simulates user-space 4ms tick scheduling jitter (OS context switches, DPC/ISR interruptions)
and evaluates a 1D Kalman filter tick interpolator for microsecond-smooth packet release.
"""

import sys
import json
import random
import numpy as np
from pathlib import Path

def test_kalman_tick_filter():
    np.random.seed(42)
    random.seed(42)

    n_ticks = 5000
    nominal_interval_us = 4000.0 # 4ms

    # True drift / walk
    Q = 0.5 # Process noise variance
    # Observation jitter (OS scheduling slack, sleep overshoot)
    R = 250.0 ** 2 # (250us std)^2 = 62500 us^2

    # Generate noisy measurement trace
    true_intervals = np.zeros(n_ticks)
    measured_intervals = np.zeros(n_ticks)
    filtered_intervals = np.zeros(n_ticks)

    current_interval = nominal_interval_us
    for k in range(n_ticks):
        current_interval += np.random.normal(0, np.sqrt(Q))
        true_intervals[k] = current_interval
        # Heavy-tailed OS jitter
        noise = np.random.normal(0, 250.0)
        if np.random.random() < 0.05:
            # 5% chance of scheduling spike (+600us)
            noise += np.random.exponential(400.0)
        measured_intervals[k] = current_interval + noise

    # Kalman Filter implementation
    x_hat = nominal_interval_us
    P = 100.0

    for k in range(n_ticks):
        # Predict
        x_pred = x_hat
        P_pred = P + Q

        # Update
        K = P_pred / (P_pred + R)
        x_hat = x_pred + K * (measured_intervals[k] - x_pred)
        P = (1.0 - K) * P_pred

        filtered_intervals[k] = x_hat

    # Evaluate post burn-in (after 100 ticks)
    burn_in = 100
    var_raw = float(np.var(measured_intervals[burn_in:]))
    var_filtered = float(np.var(filtered_intervals[burn_in:]))
    var_reduction_percent = ((var_raw - var_filtered) / var_raw) * 100.0

    std_raw_us = float(np.std(measured_intervals[burn_in:]))
    std_filtered_us = float(np.std(filtered_intervals[burn_in:]))
    jitter_smoothing_ratio = ((std_raw_us - std_filtered_us) / std_raw_us) * 100.0

    pass_gate = bool(var_reduction_percent >= 70.0 and jitter_smoothing_ratio >= 75.0)

    result = {
        "task_id": "0279",
        "sample_ticks": n_ticks,
        "nominal_tick_us": nominal_interval_us,
        "raw_scheduling_jitter": {
            "std_us": round(std_raw_us, 2),
            "variance_us2": round(var_raw, 2)
        },
        "kalman_filtered_tick": {
            "std_us": round(std_filtered_us, 2),
            "variance_us2": round(var_filtered, 2)
        },
        "variance_reduction_percent": round(var_reduction_percent, 2),
        "target_var_reduction_gate_percent": 70.0,
        "jitter_smoothing_ratio_percent": round(jitter_smoothing_ratio, 2),
        "target_smoothing_gate_percent": 75.0,
        "pass_gate": pass_gate
    }

    out_file = Path("runs/kalman0279_tick_interpolator.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2))
    return pass_gate

if __name__ == "__main__":
    passed = test_kalman_tick_filter()
    if not passed:
        sys.exit(1)
