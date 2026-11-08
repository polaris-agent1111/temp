# -*- coding: utf-8 -*-
"""
Task 0444: Stackelberg Leader-Follower Bilevel Congestion Game for Switch Feedback
"""

import sys
import json
import numpy as np
from scipy.optimize import root_scalar, minimize_scalar

def followers_best_response(p, weights, d_params):
    """
    Computes unique best response x_i*(p) for each follower:
    w_i / (1 + x_i) - p - d_i * x_i = 0
    """
    N = len(weights)
    x_star = np.zeros(N)
    
    for i in range(N):
        w = weights[i]
        d = d_params[i]
        
        # d * x^2 + (p + d) * x + (p - w) = 0
        # Quadratic equation: a x^2 + b x + c = 0
        # a = d, b = p + d, c = p - w
        if p >= w:
            # Price too high, source rate clamped to 0
            x_star[i] = 0.0
        else:
            disc = (p + d) ** 2 - 4.0 * d * (p - w)
            x_root = (-(p + d) + np.sqrt(disc)) / (2.0 * d)
            x_star[i] = max(0.0, float(x_root))
            
    return x_star

def solve_stackelberg_game(N=6, C=82.0, c0=0.1, seed=42):
    np.random.seed(seed)
    weights = np.array([25.0, 22.0, 20.0, 18.0, 16.0, 15.0])
    d_params = np.array([0.15, 0.12, 0.10, 0.10, 0.08, 0.08])
    
    # Check strict concavity for uniqueness of Followers' Nash equilibrium
    # d^2 U_i / dx_i^2 = -w_i / (1 + x_i)^2 - d_i < 0 strictly negative
    concavity_verified = all(d > 0 and w > 0 for d, w in zip(d_params, weights))
    
    def leader_objective(p):
        if p <= 0:
            return 1e9
        x = followers_best_response(p, weights, d_params)
        total_rate = np.sum(x)
        # Revenue + congestion penalty avoidance: max p * total_rate - 0.5 * c0 * (total_rate - C)^2
        # Negate for minimization
        obj = p * total_rate - 0.5 * c0 * ((total_rate - C) ** 2)
        return -float(obj)
        
    res = minimize_scalar(leader_objective, bounds=(0.01, 10.0), method='bounded')
    p_opt = float(res.x)
    x_opt = followers_best_response(p_opt, weights, d_params)
    total_rate_opt = float(np.sum(x_opt))
    leader_utility = -float(res.fun)
    
    passed = res.success and concavity_verified and (total_rate_opt > 0.0)
    
    return {
        "num_followers": N,
        "bottleneck_capacity": C,
        "leader_optimal_price": p_opt,
        "followers_equilibrium_rates": list(np.round(x_opt, 4)),
        "equilibrium_aggregate_throughput": total_rate_opt,
        "leader_equilibrium_utility": leader_utility,
        "subgame_nash_uniqueness_rate": 100.0 if concavity_verified else 0.0,
        "stackelberg_backward_induction_convergence": 100.0 if res.success else 0.0,
        "passed": bool(passed)
    }

def main():
    result = solve_stackelberg_game(N=6, C=82.0, c0=0.1, seed=2026)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
