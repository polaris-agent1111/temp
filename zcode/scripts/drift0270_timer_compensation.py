#!/usr/bin/env python3
"""
Task 0270: Client User-space High-Precision Timer Drift Cumulative Compensation Over Long Sessions
Simulates 8-hour continuous operation (28,800s epoch steps) and evaluates PLL clock discipline compensation.
"""

import sys
import json
import random
import numpy as np
from pathlib import Path

def evaluate_timer_drift():
    np.random.seed(42)
    random.seed(42)

    total_seconds = 28800 # 8 hours
    oscillator_drift_ppm = 18.5 # parts per million (18.5 us per second drift)
    thermal_wander_std = 0.25 # ppm thermal wander

    # 1. Uncompensated Monotonic Clock
    uncomp_drifts_us = np.zeros(total_seconds)
    curr_uncomp_drift = 0.0

    # 2. Disciplined Clock with Phase-Locked Loop (PLL / FLL)
    # Dual-loop estimator: Frequency offset estimate (FLL) + Phase error correction (PLL)
    comp_phase_err_us = np.zeros(total_seconds)
    phase_error = 0.0
    freq_est_ppm = 0.0 # Frequency drift estimate

    Kp = 0.45 # Phase correction gain
    Ki = 0.08 # Frequency correction gain

    for t in range(total_seconds):
        # Physical hardware clock drift per second
        hw_drift_this_sec = oscillator_drift_ppm + np.random.normal(0, thermal_wander_std)
        curr_uncomp_drift += hw_drift_this_sec
        uncomp_drifts_us[t] = curr_uncomp_drift

        # Update physical clock increment relative to nominal
        phase_error += (hw_drift_this_sec - freq_est_ppm)
        
        # Disciplining loop:
        # FLL updates frequency drift estimate
        freq_est_ppm += Ki * phase_error
        # PLL applies phase correction
        correction = Kp * phase_error
        phase_error -= correction
        
        comp_phase_err_us[t] = phase_error

    max_uncomp_drift_ms = float(np.max(np.abs(uncomp_drifts_us))) / 1000.0
    final_uncomp_drift_ms = float(uncomp_drifts_us[-1]) / 1000.0
    
    # Evaluate post-convergence (after initial 200s lock-in)
    burn_in = 200
    max_comp_drift_us = float(np.max(np.abs(comp_phase_err_us[burn_in:])))
    rms_comp_drift_us = float(np.sqrt(np.mean(comp_phase_err_us[burn_in:] ** 2)))

    pass_gate = bool(max_comp_drift_us <= 15.0)

    result = {
        "task_id": "0270",
        "duration_hours": 8.0,
        "total_seconds_simulated": total_seconds,
        "hardware_oscillator_nominal_drift_ppm": oscillator_drift_ppm,
        "uncompensated_clock": {
            "max_drift_ms": round(max_uncomp_drift_ms, 3),
            "final_accumulated_drift_ms": round(final_uncomp_drift_ms, 3)
        },
        "compensated_disciplined_clock": {
            "max_residual_drift_us": round(max_comp_drift_us, 3),
            "rms_residual_drift_us": round(rms_comp_drift_us, 3),
            "target_gate_us": 15.0
        },
        "drift_suppression_ratio": round(float(np.max(np.abs(uncomp_drifts_us))) / max_comp_drift_us, 1),
        "pass_gate": pass_gate
    }

    out_file = Path("runs/drift0270_timer_compensation.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2))
    return pass_gate

if __name__ == "__main__":
    passed = evaluate_timer_drift()
    if not passed:
        sys.exit(1)
