# -*- coding: utf-8 -*-
"""
Task 0467: Generalized Nash Equilibrium Problem (GNEP) Variational Inequality Projection Dynamics
- 6-flow shallow buffer competition with shared capacity constraint sum(x_i) <= C_buf
- Strongly monotone pseudo-gradient mapping F(x)
- Korpelevich extragradient projection method onto simplex/polyhedron
- Target: Convergence rate 100.0%, projection residual < 1e-6
"""

import sys
import json
import numpy as np

def project_onto_capacity_simplex(v, C_buf):
    """
    Computes Euclidean projection of vector v onto {x in R_+^n : sum(x_i) <= C_buf}.
    """
    v_pos = np.maximum(0.0, v)
    if np.sum(v_pos) <= C_buf:
        return v_pos
    
    # Projection onto simplex sum(x) = C_buf with x >= 0
    u = np.sort(v_pos)[::-1]
    cssv = np.cumsum(u)
    rho = np.nonzero(u * np.arange(1, len(u) + 1) > (cssv - C_buf))[0][-1]
    theta = (cssv[rho] - C_buf) / (rho + 1.0)
    w = np.maximum(v_pos - theta, 0.0)
    return w

class GNEPNetworkGame:
    def __init__(self, n=6, C_buf=60.0, seed=42):
        np.random.seed(seed)
        self.n = n
        self.C_buf = C_buf
        # Player cost parameters: J_i(x_i, x) = 0.5 * d_i * x_i^2 - w_i * ln(x_i + 1) + c * sum(x_j)
        self.d = np.random.uniform(1.0, 3.0, size=n)
        self.w = np.random.uniform(10.0, 30.0, size=n)
        self.c = 0.5
        
    def F(self, x):
        # Marginal gradient: nabla_{x_i} J_i = d_i * x_i - w_i / (x_i + 1.0) + c
        return self.d * x - self.w / (x + 1.0) + self.c
    
    def project(self, x):
        return project_onto_capacity_simplex(x, self.C_buf)

def solve_gnep_extragradient(game, gamma=0.02, max_iter=2000, tol=1e-8):
    x = np.ones(game.n) * (game.C_buf / (2.0 * game.n))
    
    for it in range(max_iter):
        # Korpelevich step 1: Predictor
        y = game.project(x - gamma * game.F(x))
        # Korpelevich step 2: Corrector
        x_next = game.project(x - gamma * game.F(y))
        
        # Fixed point residual ||x - project(x - gamma * F(x))||
        res = np.linalg.norm(x - game.project(x - gamma * game.F(x)))
        if res < tol:
            return x_next, res, it + 1, True
            
        x = x_next
        
    res = np.linalg.norm(x - game.project(x - gamma * game.F(x)))
    return x, res, max_iter, res < 1e-6

def main():
    print("=== Task 0467: GNEP Variational Inequality Projection Dynamics ===")
    
    runs = 30
    success_count = 0
    residuals = []
    
    for seed in range(runs):
        game = GNEPNetworkGame(n=6, C_buf=60.0, seed=2026 + seed)
        x_star, res, iters, passed = solve_gnep_extragradient(game, gamma=0.03)
        residuals.append(res)
        # Check capacity constraint
        cap_violation = max(0.0, float(np.sum(x_star) - game.C_buf))
        if res < 1e-6 and cap_violation < 1e-8 and passed:
            success_count += 1
            
    convergence_rate = (success_count / runs) * 100.0
    max_res = float(np.max(residuals))
    mean_res = float(np.mean(residuals))
    
    overall_passed = (convergence_rate == 100.0) and (max_res < 1e-6)
    
    result = {
        "runs": runs,
        "success_count": success_count,
        "convergence_rate": convergence_rate,
        "max_projection_residual": max_res,
        "mean_projection_residual": mean_res,
        "target_threshold": 1e-6,
        "passed": bool(overall_passed)
    }
    
    print(json.dumps(result, indent=2))
    if not overall_passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
