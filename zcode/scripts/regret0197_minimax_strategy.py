#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0197: Minimax Regret (Savage criterion) analysis for Shot 2 candidate selection.
Constructs the regret matrix across environmental states (Fair-weather, Baseline, Adversarial)
and calculates minimax regret optimal strategy.
"""
import numpy as np

def calculate_minimax_regret():
    # Environmental States (Nature):
    # theta_1: Fair-weather (Low background load, RTT jitter < 2ms)
    # theta_2: Baseline Nominal (Standard background load, RTT jitter ~ 5ms)
    # theta_3: Adversarial Congestion (Heavy background bursts, RTT jitter > 12ms)
    
    # Candidate Action Space for Shot 2:
    # a_1: Crown Fusion (Aggressive 41-41-41-37-36-36)
    # a_2: Plateau A (Stable Peak 37-37-37-37-36-36)
    # a_3: Defense Fortress (Conservative 36-36-36-36-36-36)
    
    # Loss Matrix L(a_i, theta_j) in seconds (Total download time):
    loss_matrix = np.array([
        [116.5, 117.8, 126.2],  # a_1 (Crown Fusion)
        [119.2, 119.8, 122.4],  # a_2 (Plateau A)
        [125.0, 125.8, 126.0],  # a_3 (Defense Fortress)
    ])
    
    # Best possible loss under each state theta_j:
    min_loss_per_state = np.min(loss_matrix, axis=0)  # [116.5, 117.8, 122.4]
    
    # Regret Matrix R(a_i, theta_j) = L(a_i, theta_j) - min_k L(a_k, theta_j)
    regret_matrix = loss_matrix - min_loss_per_state
    
    # Maximum regret for each action:
    max_regrets = np.max(regret_matrix, axis=1)
    
    # Minimax Regret Action:
    best_action_idx = np.argmin(max_regrets)
    action_names = ["Crown Fusion", "Plateau A", "Defense Fortress"]
    
    # State-conditional regret thresholding
    # If S1 score <= 138s -> P(theta_1 or theta_2) ~ 0.95:
    # Under benign states {theta_1, theta_2}, Crown Fusion max regret is 0.0s!
    regret_benign = np.max(regret_matrix[:, :2], axis=1)
    
    print("=== Task 0197: Minimax Regret Decision Analysis ===")
    print("Loss Matrix L(a, theta) [rows=actions, cols=states]:")
    print(loss_matrix)
    print("\nRegret Matrix R(a, theta):")
    print(regret_matrix)
    print("\nMaximum Regret per Action:")
    for i, name in enumerate(action_names):
        print(f"  {name}: {max_regrets[i]:.2f}s (Benign sub-regret: {regret_benign[i]:.2f}s)")
        
    print(f"\nGlobal Minimax Regret Strategy: {action_names[best_action_idx]} (Max Regret: {max_regrets[best_action_idx]:.2f}s)")
    print(f"Benign-conditioned Optimal Strategy: Crown Fusion (Max Regret: {regret_benign[0]:.2f}s)")
    
    return {
        "regret_matrix": regret_matrix.tolist(),
        "max_regrets": max_regrets.tolist(),
        "optimal_action": action_names[best_action_idx]
    }

if __name__ == "__main__":
    calculate_minimax_regret()
