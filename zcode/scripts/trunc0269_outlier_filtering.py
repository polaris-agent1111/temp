#!/usr/bin/env python3
"""
Task 0269: Official Scoring Mechanism Truncation & Variance Suppression Against Extreme Outliers
Evaluates official repeating average mechanism (N=3..5) against heavy-tailed network jitter and outlier spikes.
"""

import sys
import json
import numpy as np
from pathlib import Path

def test_outlier_suppression():
    np.random.seed(42)
    n_simulations = 2000
    base_mean = 120.0
    nominal_std = 2.5

    # Scenario: Official evaluation repeats n=5 times, with 10% chance of an outlier spike (e.g. cross-traffic burst +15s)
    single_shot_samples = []
    mean_of_3_samples = []
    mean_of_5_samples = []
    trimmed_mean_5_samples = [] # 20% trimmed mean (dropping min and max)

    for _ in range(n_simulations):
        # Draw 5 runs
        runs = []
        for _ in range(5):
            is_outlier = np.random.random() < 0.10
            spike = np.random.exponential(12.0) if is_outlier else 0.0
            val = np.random.normal(base_mean, nominal_std) + spike
            runs.append(val)
        
        single_shot_samples.append(runs[0])
        mean_of_3_samples.append(np.mean(runs[:3]))
        mean_of_5_samples.append(np.mean(runs))
        
        # Trimmed mean (drop lowest and highest of 5)
        sorted_runs = sorted(runs)
        trimmed_mean_5_samples.append(np.mean(sorted_runs[1:4]))

    std_single = float(np.std(single_shot_samples))
    std_mean3 = float(np.std(mean_of_3_samples))
    std_mean5 = float(np.std(mean_of_5_samples))
    std_trimmed5 = float(np.std(trimmed_mean_5_samples))

    var_suppression_ratio_5 = (1.0 - (std_mean5 ** 2) / (std_single ** 2)) * 100.0
    outlier_mean_shift_5 = abs(float(np.mean(mean_of_5_samples)) - base_mean)

    pass_gate = bool(var_suppression_ratio_5 >= 60.0 and outlier_mean_shift_5 <= 1.5)

    result = {
        "task_id": "0269",
        "n_simulations": n_simulations,
        "single_shot_std_sec": round(std_single, 3),
        "mean_of_3_std_sec": round(std_mean3, 3),
        "mean_of_5_std_sec": round(std_mean5, 3),
        "trimmed_mean_5_std_sec": round(std_trimmed5, 3),
        "variance_suppression_ratio_percent": round(var_suppression_ratio_5, 2),
        "target_suppression_gate_percent": 60.0,
        "mean_shift_due_to_outliers_sec": round(outlier_mean_shift_5, 3),
        "target_shift_gate_sec": 1.5,
        "pass_gate": pass_gate
    }

    out_file = Path("runs/trunc0269_outlier_filtering.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2))
    return pass_gate

if __name__ == "__main__":
    passed = test_outlier_suppression()
    if not passed:
        sys.exit(1)
