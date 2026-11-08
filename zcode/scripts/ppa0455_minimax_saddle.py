# -*- coding: utf-8 -*-
"""
Task 0455: Proximal Point Algorithm (PPA) for Minimax Saddle Point Convergence in Pacing Game
"""

import sys
import json
import numpy as np

def build_minimax_game(n=6, m=4, seed=42):
    np.random.seed(seed)
    # Positive definite A and C
    Q_A, _ = np.linalg.qr(np.random.randn(n, n))
    A = Q_A @ np.diag(np.linspace(1.5, 4.0, n)) @ Q_A.T
    
    Q_C, _ = np.linalg.qr(np.random.randn(m, m))
    C = Q_C @ np.diag(np.linspace(1.2, 3.5, m)) @ Q_C.T
    
    # Interaction coupling matrix B
    B = 1.8 * np.random.randn(n, m)
    
    # Target offsets
    b_x = np.random.randn(n)
    b_y = np.random.randn(m)
    
    # Phi(x, y) = 0.5 x^T A x - b_x^T x + x^T B y - (0.5 y^T C y - b_y^T y)
    # Saddle point conditions:
    # A x* + B y* = b_x
    # B^T x* - C y* = -b_y  => -B^T x* + C y* = b_y
    # In block form:
    # [ A    B ] [ x* ] = [ b_x ]
    # [ B^T -C ] [ y* ] = [ -b_y ]
    M_saddle = np.block([
        [A, B],
        [B.T, -C]
    ])
    rhs_saddle = np.concatenate([b_x, -b_y])
    z_star = np.linalg.solve(M_saddle, rhs_saddle)
    x_star = z_star[:n]
    y_star = z_star[n:]
    
    return A, B, C, b_x, b_y, x_star, y_star

def run_ppa(A, B, C, b_x, b_y, x_star, y_star, eta=0.5, steps=60):
    n = len(b_x)
    m = len(b_y)
    
    # Block matrix for PPA subproblem:
    # [ A + 1/eta I     B       ] [ x_{k+1} ] = [ 1/eta x_k + b_x ]
    # [ B^T          -(C+1/eta I)] [ y_{k+1} ] = [ -1/eta y_k - b_y ]
    M_ppa = np.block([
        [A + (1.0 / eta) * np.eye(n), B],
        [B.T, -(C + (1.0 / eta) * np.eye(m))]
    ])
    
    # Initial point far from optimum
    x_k = x_star + 5.0 * np.random.randn(n)
    y_k = y_star + 5.0 * np.random.randn(m)
    z_star = np.concatenate([x_star, y_star])
    
    distances = [float(np.linalg.norm(np.concatenate([x_k, y_k]) - z_star))]
    monotonic_checks = []
    
    for k in range(steps):
        rhs = np.concatenate([
            (1.0 / eta) * x_k + b_x,
            -(1.0 / eta) * y_k - b_y
        ])
        z_next = np.linalg.solve(M_ppa, rhs)
        x_next = z_next[:n]
        y_next = z_next[n:]
        
        dist_next = float(np.linalg.norm(z_next - z_star))
        monotonic_checks.append(dist_next <= distances[-1] + 1e-12)
        distances.append(dist_next)
        
        x_k, y_k = x_next, y_next
        
    # Stationarity residual:
    grad_x = A @ x_k + B @ y_k - b_x
    grad_y = B.T @ x_k - C @ y_k + b_y
    stat_residual = float(np.sqrt(np.sum(grad_x ** 2) + np.sum(grad_y ** 2)))
    
    monotonic_rate = float(np.mean(monotonic_checks)) * 100.0
    passed = (stat_residual < 0.005) and (monotonic_rate >= 99.9) and (distances[-1] < 1e-4)
    
    return {
        "proximal_stepsize_eta": eta,
        "total_ppa_steps": steps,
        "initial_saddle_distance": distances[0],
        "final_saddle_distance": distances[-1],
        "stationarity_residual_norm": stat_residual,
        "monotonic_convergence_rate": monotonic_rate,
        "passed": bool(passed)
    }

def main():
    A, B, C, b_x, b_y, x_star, y_star = build_minimax_game(n=6, m=4, seed=2026)
    result = run_ppa(A, B, C, b_x, b_y, x_star, y_star, eta=0.4, steps=50)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
