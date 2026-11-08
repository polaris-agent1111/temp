#!/usr/bin/env python3
"""
Task 0283: Leaderboard Score Latency & Anti-Throttling Adaptive Polling Policy
Evaluates piecewise non-linear adaptive polling against official score delay distribution and HTTP 429 rate limits.
"""

import sys
import json
import random
import numpy as np
from pathlib import Path

def evaluate_polling_policy():
    np.random.seed(42)
    random.seed(42)

    n_campaigns = 1000

    # Rate limit constraints:
    # Max requests allowed in 60 min: 120 requests (avg 1 req per 30s)
    # Min interval between requests: 10s (prevents burst 429)

    detection_delays_sec = []
    total_requests_list = []
    rate_limit_violations = 0

    def get_poll_interval_sec(elapsed_sec):
        elapsed_min = elapsed_sec / 60.0
        if elapsed_min < 7.0:
            return 120.0 # Dormant phase (0-7 min): poll every 2 min
        elif elapsed_min < 26.0:
            return 20.0 # Prime release window (7-26 min): poll every 20s
        elif elapsed_min < 50.0:
            return 45.0 # Tail window (26-50 min): poll every 45s
        else:
            return 60.0 # Pre-timeout window (50-60 min): poll every 60s

    for _ in range(n_campaigns):
        # Sample official score publication time (in seconds)
        # Bimodal/log-normal: 80% normal (8-22 min), 18% delayed (22-45 min), 2% heavy queue (45-55 min)
        r = np.random.random()
        if r < 0.80:
            score_ready_sec = np.random.normal(14.0 * 60.0, 3.0 * 60.0)
        elif r < 0.98:
            score_ready_sec = np.random.normal(32.0 * 60.0, 6.0 * 60.0)
        else:
            score_ready_sec = np.random.normal(50.0 * 60.0, 3.0 * 60.0)
        
        score_ready_sec = max(7.0 * 60.0, min(59.0 * 60.0, score_ready_sec))

        # Simulate polling loop
        current_time_sec = 0.0
        req_count = 0
        detected = False
        detection_delay = 0.0

        while current_time_sec < 3600.0: # 60 min
            interval = get_poll_interval_sec(current_time_sec)
            
            # Check rate limit violation
            if interval < 10.0:
                rate_limit_violations += 1

            current_time_sec += interval
            req_count += 1

            if current_time_sec >= score_ready_sec:
                detected = True
                detection_delay = current_time_sec - score_ready_sec
                break

        total_requests_list.append(req_count)
        if detected:
            detection_delays_sec.append(detection_delay)

    mean_requests = float(np.mean(total_requests_list))
    max_requests = int(np.max(total_requests_list))
    mean_delay_sec = float(np.mean(detection_delays_sec))
    p95_delay_sec = float(np.percentile(detection_delays_sec, 95))

    pass_gate = bool(
        max_requests <= 120 and
        rate_limit_violations == 0 and
        mean_delay_sec <= 15.0
    )

    result = {
        "task_id": "0283",
        "campaigns_simulated": n_campaigns,
        "mean_requests_per_shot": round(mean_requests, 1),
        "max_requests_observed": max_requests,
        "target_max_requests_gate": 120,
        "rate_limit_429_violations_count": rate_limit_violations,
        "mean_score_detection_latency_sec": round(mean_delay_sec, 2),
        "target_mean_latency_gate_sec": 15.0,
        "p95_score_detection_latency_sec": round(p95_delay_sec, 2),
        "pass_gate": pass_gate
    }

    out_file = Path("runs/poll0283_anti_throttle.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2))
    return pass_gate

if __name__ == "__main__":
    passed = evaluate_polling_policy()
    if not passed:
        sys.exit(1)
