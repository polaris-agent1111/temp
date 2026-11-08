#!/usr/bin/env python3
"""
Task 0263: HMM-based Channel State Adaptive Inference Model
Evaluates hidden Markov model inference accuracy across 3 bottleneck channel states:
- S1: IDLE (buffer empty, minimal RTT, zero loss)
- S2: STABLE (buffer optimal, normal queuing, zero loss)
- S3: CONGESTED (buffer saturated, RTT inflation, packet loss)
"""

import sys
import json
import math
import random
import numpy as np
from pathlib import Path

def gaussian_pdf(x, mean, std):
    """Compute 1D Gaussian probability density."""
    var = std * std
    denom = math.sqrt(2.0 * math.pi * var)
    num = math.exp(-0.5 * ((x - mean) ** 2) / var)
    return max(num / denom, 1e-12)

def simulate_and_infer():
    np.random.seed(42)
    random.seed(42)

    states = ["IDLE", "STABLE", "CONGESTED"]
    n_states = 3

    # Transition probability matrix A (rows sum to 1)
    # [IDLE, STABLE, CONGESTED]
    A = np.array([
        [0.86, 0.12, 0.02],
        [0.08, 0.84, 0.08],
        [0.03, 0.15, 0.82]
    ])

    # Initial prior distribution pi
    pi = np.array([0.333, 0.334, 0.333])

    # Emission parameters: [mean_rtt, std_rtt, loss_prob]
    # In ms: Base RTT = 10.0 ms
    emissions = {
        0: {"rtt_mean": 10.15, "rtt_std": 0.35, "loss_p": 0.000},  # IDLE
        1: {"rtt_mean": 11.45, "rtt_std": 0.65, "loss_p": 0.001},  # STABLE
        2: {"rtt_mean": 14.80, "rtt_std": 1.40, "loss_p": 0.085}   # CONGESTED
    }

    # Generate synthetic trace of T = 5,000 steps
    T = 5000
    true_states = np.zeros(T, dtype=int)
    obs_rtt = np.zeros(T, dtype=float)
    obs_loss = np.zeros(T, dtype=int)

    current_state = np.random.choice(n_states, p=pi)
    for t in range(T):
        true_states[t] = current_state
        # Emit observation
        ep = emissions[current_state]
        rtt_sample = np.random.normal(ep["rtt_mean"], ep["rtt_std"])
        loss_sample = 1 if np.random.random() < ep["loss_p"] else 0
        obs_rtt[t] = max(rtt_sample, 9.8)
        obs_loss[t] = loss_sample

        # Transition to next state
        current_state = np.random.choice(n_states, p=A[current_state])

    # Online Forward Filtering Inference (real-time causal prediction)
    # alpha_t(j) = P(S_t = j | O_1:t)
    pred_states = np.zeros(T, dtype=int)
    alpha = pi.copy()

    def emission_prob(j, rtt, loss):
        ep = emissions[j]
        p_rtt = gaussian_pdf(rtt, ep["rtt_mean"], ep["rtt_std"])
        p_loss = ep["loss_p"] if loss == 1 else (1.0 - ep["loss_p"])
        return p_rtt * max(p_loss, 1e-6)

    # First step
    for j in range(n_states):
        alpha[j] = pi[j] * emission_prob(j, obs_rtt[0], obs_loss[0])
    alpha /= np.sum(alpha)
    pred_states[0] = np.argmax(alpha)

    # Online filtering loop
    detection_latencies = []
    congest_onset_steps = []

    for t in range(1, T):
        # Predict step (prior)
        prior = np.dot(alpha, A)
        # Update step (posterior)
        likelihood = np.array([emission_prob(j, obs_rtt[t], obs_loss[t]) for j in range(n_states)])
        alpha = prior * likelihood
        s = np.sum(alpha)
        if s > 0:
            alpha /= s
        else:
            alpha = np.ones(n_states) / n_states
        
        pred_states[t] = np.argmax(alpha)

        # Track congestion state transition detection latency
        if true_states[t] == 2 and true_states[t-1] != 2:
            congest_onset_steps.append(t)

    # Measure transition latency for congestion events
    for step in congest_onset_steps:
        lat = 0
        detected = False
        while (step + lat) < T and true_states[step + lat] == 2:
            if pred_states[step + lat] == 2:
                detected = True
                break
            lat += 1
        if detected:
            detection_latencies.append(lat)

    # Metrics computation
    correct = np.sum(pred_states == true_states)
    overall_accuracy = float(correct) / T

    confusion = np.zeros((n_states, n_states), dtype=int)
    for t in range(T):
        confusion[true_states[t], pred_states[t]] += 1

    per_class_recall = {}
    per_class_precision = {}
    for i, s_name in enumerate(states):
        tp = confusion[i, i]
        fn = np.sum(confusion[i, :]) - tp
        fp = np.sum(confusion[:, i]) - tp
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        per_class_recall[s_name] = round(float(recall), 4)
        per_class_precision[s_name] = round(float(prec), 4)

    mean_detection_delay_ticks = float(np.mean(detection_latencies)) if detection_latencies else 0.0

    result = {
        "task_id": "0263",
        "sample_size": T,
        "overall_accuracy": round(overall_accuracy, 4),
        "target_accuracy_gate": 0.92,
        "pass_gate": bool(overall_accuracy >= 0.92),
        "mean_congestion_detection_latency_steps": round(mean_detection_delay_ticks, 2),
        "confusion_matrix": confusion.tolist(),
        "per_class_recall": per_class_recall,
        "per_class_precision": per_class_precision
    }

    out_file = Path("runs/hmm0263_channel_state_infer.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2))
    return result["pass_gate"]

if __name__ == "__main__":
    passed = simulate_and_infer()
    if not passed:
        sys.exit(1)
