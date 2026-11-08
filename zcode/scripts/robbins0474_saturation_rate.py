# -*- coding: utf-8 -*-
"""
Task 0474: Robbins-Monro Stochastic Approximation for Bottleneck Saturation Rate Identification
- Solve unknown root M(theta*) = 0 where M(theta) = E[Y(theta)]
- Monotonic Lipschitz queuing delay response with heavy observation noise
- Projected Robbins-Monro stochastic recursion: theta_{k+1} = Pi_{[theta_min, theta_max]}(theta_k - a_k Y_k)
- Stepsize conditions: sum(a_k) = inf, sum(a_k^2) < inf
- Polyak-Ruppert averaging to achieve optimal asymptotic efficiency
- Target: Relative error < 1.0%, Convergence rate 100.0%
"""

import sys
import json
import numpy as np

class ShallowBufferSystem:
    def __init__(self, true_theta_star=40.0, slope=0.8, noise_std=1.0, seed=42):
        np.random.seed(seed)
        self.theta_star = true_theta_star
        self.slope = slope
        self.noise_std = noise_std
        
    def query(self, theta):
        delta = theta - self.theta_star
        # Monotonic Lipschitz response
        m = self.slope * delta / (1.0 + 0.02 * abs(delta))
        noise = np.random.normal(0.0, self.noise_std)
        return m + noise

def robbins_monro_identify(system, theta_init=25.0, K=2500, a0=0.8, gamma=0.65, bounds=(10.0, 70.0)):
    theta = theta_init
    thetas = []
    
    for k in range(1, K + 1):
        a_k = a0 / (k ** gamma)
        y_k = system.query(theta)
        # Projected stochastic gradient step
        theta = float(np.clip(theta - a_k * y_k, bounds[0], bounds[1]))
        thetas.append(theta)
        
    # Polyak-Ruppert averaging over final 40% of trajectory
    burn_in = int(K * 0.6)
    theta_polyak = float(np.mean(thetas[burn_in:]))
    theta_final = float(theta)
    
    rel_error = abs(theta_polyak - system.theta_star) / system.theta_star * 100.0
    return theta_polyak, theta_final, rel_error

def main():
    print("=== Task 0474: Robbins-Monro Stochastic Approximation ===")
    
    runs = 30
    rel_errors = []
    success_count = 0
    
    for r in range(runs):
        sys_obj = ShallowBufferSystem(true_theta_star=40.0, slope=1.0, noise_std=1.2, seed=200 + r)
        theta_est, _, err = robbins_monro_identify(
            sys_obj,
            theta_init=float(np.random.uniform(15.0, 65.0)),
            K=3000,
            a0=0.9,
            gamma=0.65
        )
        rel_errors.append(err)
        if err < 1.0:
            success_count += 1
            
    convergence_rate = (success_count / runs) * 100.0
    max_err = float(np.max(rel_errors))
    mean_err = float(np.mean(rel_errors))
    
    passed = (convergence_rate == 100.0) and (max_err < 1.0)
    
    summary = {
        "runs": runs,
        "success_runs": success_count,
        "convergence_rate": convergence_rate,
        "mean_relative_error_percent": mean_err,
        "max_relative_error_percent": max_err,
        "target_error_threshold_percent": 1.0,
        "passed": bool(passed)
    }
    
    print(json.dumps(summary, indent=2))
    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
