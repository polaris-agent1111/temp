# -*- coding: utf-8 -*-
"""
Task 0443: Inexact Accelerated Proximal Gradient (FISTA) for Non-Smooth Traffic Rate Smoothing
"""

import sys
import json
import numpy as np

def soft_thresholding(v, threshold):
    """
    prox_{threshold * ||.||_1}(v) = sign(v) * max(0, |v| - threshold)
    """
    return np.sign(v) * np.maximum(0.0, np.abs(v) - threshold)

def run_fista_comparison(dim=24, lam=0.25, max_iter=1500, tol=1e-6, seed=42):
    """
    Minimizes F(x) = 0.5 * x^T A x - b^T x + lam * ||x||_1
    """
    np.random.seed(seed)
    
    # Generate ill-conditioned matrix A (condition number ~ 200) to demonstrate acceleration
    eigvals = np.logspace(0, 2.3, dim)  # from 1 to 200
    Q, _ = np.linalg.qr(np.random.randn(dim, dim))
    A = Q @ np.diag(eigvals) @ Q.T
    L = float(np.max(eigvals))  # Lipschitz constant
    alpha = 1.0 / L  # Step size
    
    # Ground truth sparse rate vector
    x_true = np.zeros(dim)
    sparse_indices = np.random.choice(dim, size=dim // 3, replace=False)
    x_true[sparse_indices] = 2.0 * np.random.randn(dim // 3)
    b = A @ x_true
    
    def objective(x):
        return 0.5 * float(x.T @ A @ x) - float(b.T @ x) + lam * float(np.sum(np.abs(x)))
        
    def grad_f(x):
        return A @ x - b
        
    # --- 1. Classical ISTA (Proximal Gradient) ---
    x_ista = np.zeros(dim)
    ista_steps = 0
    for k in range(1, max_iter + 1):
        x_prev = x_ista.copy()
        grad = grad_f(x_ista)
        x_ista = soft_thresholding(x_ista - alpha * grad, alpha * lam)
        ista_steps = k
        if np.linalg.norm(x_ista - x_prev) < tol:
            break
            
    # --- 2. Accelerated FISTA with Inexact Proximal Error ---
    x_fista = np.zeros(dim)
    x_prev = np.zeros(dim)
    t_k = 1.0
    fista_steps = 0
    
    for k in range(1, max_iter + 1):
        # Nesterov momentum extrapolation
        beta_k = (t_k - 1.0) / ( (1.0 + np.sqrt(1.0 + 4.0 * (t_k ** 2))) / 2.0 )
        y_k = x_fista + beta_k * (x_fista - x_prev)
        
        # Inexact proximal evaluation: add diminishing truncation noise e_k = O(1 / k^2.2)
        grad = grad_f(y_k)
        inexact_noise = (0.001 / (k ** 2.2)) * np.random.randn(dim)
        x_next = soft_thresholding(y_k - alpha * grad, alpha * lam) + inexact_noise
        
        # Standard adaptive momentum restart (O'Donoghue & Candes)
        if (y_k - x_next) @ (x_next - x_fista) > 0:
            t_k = 1.0
            x_prev = x_next
        else:
            t_prev = t_k
            t_k = (1.0 + np.sqrt(1.0 + 4.0 * (t_k ** 2))) / 2.0
            x_prev = x_fista
            
        fista_steps = k
        if np.linalg.norm(x_next - x_fista) < tol and k > 10:
            x_fista = x_next
            break
            
        x_fista = x_next
        
    # Compute proximal residual mapping G_alpha(x) = (x - prox(x - alpha * grad)) / alpha
    grad_final = grad_f(x_fista)
    prox_mapped = soft_thresholding(x_fista - alpha * grad_final, alpha * lam)
    prox_residual = float(np.linalg.norm(x_fista - prox_mapped) / alpha)
    
    speedup = float(ista_steps) / float(max(1, fista_steps))
    passed = (speedup >= 3.0) and (prox_residual < 0.005) and (fista_steps < ista_steps)
    
    return {
        "dimension": dim,
        "lipschitz_constant_L": L,
        "ista_iterations_to_converge": ista_steps,
        "fista_iterations_to_converge": fista_steps,
        "acceleration_speedup_ratio": speedup,
        "final_proximal_residual": prox_residual,
        "fista_objective_value": objective(x_fista),
        "ista_objective_value": objective(x_ista),
        "passed": bool(passed)
    }

def main():
    result = run_fista_comparison(dim=24, lam=0.25, max_iter=2000, tol=1e-6, seed=2026)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
