# -*- coding: utf-8 -*-
"""
Task 0438: Finite-State Time-Delayed MDP and Bellman Contraction Mapping Solver
"""

import sys
import json
import numpy as np

def build_delayed_queue_mdp(S_states=15, A_actions=5, gamma=0.88, seed=42):
    """
    Constructs an augmented delay-state queue MDP:
    State s in {0, ..., S-1} (representing effective backlog including in-flight delays)
    Action a in {0, ..., A-1} (pacing adjustments)
    """
    np.random.seed(seed)
    
    # Transition probability tensor P(s' | s, a) of shape (S, A, S)
    P = np.zeros((S_states, A_actions, S_states))
    for s in range(S_states):
        for a in range(A_actions):
            # Drift depends on action (pacing rate) minus service rate
            drift = (a - 2) * 1.0
            probs = np.zeros(S_states)
            for s_next in range(S_states):
                # Gaussian-like transition around s + drift
                dist = (s_next - (s + drift)) ** 2
                probs[s_next] = np.exp(-0.5 * dist / 2.0)
            probs /= np.sum(probs)
            P[s, a, :] = probs
            
    # Reward matrix R(s, a) = - (delay penalty + pacing jitter penalty)
    R = np.zeros((S_states, A_actions))
    for s in range(S_states):
        for a in range(A_actions):
            # Target queue is low (e.g. 2), pacing deviation penalized
            R[s, a] = -0.5 * (s ** 1.5) - 0.2 * ((a - 2) ** 2)
            
    return S_states, A_actions, gamma, P, R

def bellman_operator(V, P, R, gamma):
    """
    T(V)(s) = max_a [ R(s, a) + gamma * sum_{s'} P(s'|s,a) * V(s') ]
    """
    # Expected future value for each (s, a): shape (S, A)
    Q = R + gamma * np.tensordot(P, V, axes=(2, 0))
    V_next = np.max(Q, axis=1)
    policy = np.argmax(Q, axis=1)
    return V_next, policy

def verify_banach_contraction(S_states, A_actions, gamma, P, R, num_pairs=1000):
    """
    Directly tests ||T(V1) - T(V2)||_infty <= gamma * ||V1 - V2||_infty
    """
    np.random.seed(2026)
    contraction_ratios = []
    strictly_contractive = []
    
    for _ in range(num_pairs):
        V1 = 100.0 * np.random.randn(S_states)
        V2 = 100.0 * np.random.randn(S_states)
        dist_orig = np.max(np.abs(V1 - V2))
        if dist_orig < 1e-8:
            continue
            
        TV1, _ = bellman_operator(V1, P, R, gamma)
        TV2, _ = bellman_operator(V2, P, R, gamma)
        dist_next = np.max(np.abs(TV1 - TV2))
        
        ratio = dist_next / dist_orig
        contraction_ratios.append(ratio)
        strictly_contractive.append(ratio <= gamma + 1e-12)
        
    max_ratio = float(np.max(contraction_ratios))
    mean_ratio = float(np.mean(contraction_ratios))
    compliance_rate = float(np.mean(strictly_contractive)) * 100.0
    
    # Also test value iteration convergence
    V = np.zeros(S_states)
    residuals = []
    for k in range(100):
        V_next, _ = bellman_operator(V, P, R, gamma)
        res = np.max(np.abs(V_next - V))
        residuals.append(res)
        V = V_next
        
    monotonic = all(residuals[i+1] <= residuals[i] + 1e-12 for i in range(len(residuals)-1))
    
    passed = (max_ratio <= gamma + 1e-10) and (max_ratio < 1.0) and monotonic
    
    return {
        "discount_factor_gamma": gamma,
        "tested_vector_pairs": num_pairs,
        "max_empirical_contraction_ratio": max_ratio,
        "mean_empirical_contraction_ratio": mean_ratio,
        "banach_contraction_compliance_rate": compliance_rate,
        "value_iteration_monotonic_convergence": 100.0 if monotonic else 0.0,
        "passed": bool(passed)
    }

def main():
    S_states, A_actions, gamma, P, R = build_delayed_queue_mdp(S_states=16, A_actions=5, gamma=0.88, seed=42)
    result = verify_banach_contraction(S_states, A_actions, gamma, P, R, num_pairs=1000)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
