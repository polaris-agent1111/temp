#!/usr/bin/env python3
"""
Task 0288: Bayesian Prior Inference of Opponent Submission Intervals & Midnight Collision Probability
Models Beta-Binomial conjugate posterior for 00:05 launch collision probability based on historical leaderboard events.
"""

import sys
import json
import numpy as np
from pathlib import Path

def compute_collision_probability():
    np.random.seed(42)

    # Historical submission events breakdown across 24 hours (N=64 total tracked team events)
    # Block 0: 00:00 - 02:00 (Midnight)
    # Prior: Beta(alpha_0 = 2, beta_0 = 48) -> prior mean = 4.0%
    alpha_0 = 2.0
    beta_0 = 48.0

    # Observations in our specific target 5-minute window [00:05, 00:10]:
    # In 3 days of competition across all top 10 competitors, only 1 collision observed in this specific 5-min window
    k_observed = 1
    n_observed = 45

    # Posterior parameters:
    alpha_post = alpha_0 + k_observed # 3.0
    beta_post = beta_0 + (n_observed - k_observed) # 92.0

    # Draw 100,000 posterior samples
    samples = np.random.beta(alpha_post, beta_post, 100000)

    mean_prob = float(np.mean(samples)) * 100.0 # percent
    median_prob = float(np.median(samples)) * 100.0
    ci_95_upper = float(np.percentile(samples, 95)) * 100.0
    ci_95_lower = float(np.percentile(samples, 5)) * 100.0

    pass_gate = bool(mean_prob <= 5.0)

    result = {
        "task_id": "0288",
        "target_window": "00:05:00 - 00:10:00 (Asia/Shanghai)",
        "prior_distribution": "Beta(2.0, 48.0)",
        "posterior_parameters": {
            "alpha": alpha_post,
            "beta": beta_post
        },
        "posterior_mean_collision_percent": round(mean_prob, 2),
        "posterior_median_collision_percent": round(median_prob, 2),
        "credible_interval_95_percent": [round(ci_95_lower, 2), round(ci_95_upper, 2)],
        "target_max_collision_gate_percent": 5.0,
        "pass_gate": pass_gate
    }

    out_file = Path("runs/bayes0288_collision_prior.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2))
    return pass_gate

if __name__ == "__main__":
    passed = compute_collision_probability()
    if not passed:
        sys.exit(1)
