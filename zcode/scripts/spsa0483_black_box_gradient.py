# -*- coding: utf-8 -*-
"""
Task 0483: Simultaneous Perturbation Stochastic Approximation (SPSA) Zero-Order Gradient Reconstruction
- Black-box evaluation of 6-stage QUIC pacing parameters theta in R^6
- Simultaneous perturbation via symmetric Rademacher/Bernoulli vector Delta in {-1, +1}^6
- 2-query gradient estimator: g_hat = (y^+ - y^-) / (2 * c) * Delta^(-1)
- Replicated SPSA gradient alignment against true analytical gradient
- Target: Cosine alignment >= 0.95, Convergence rate 100.0%
"""

import sys
import json
import numpy as np

class BlackBoxPacingObjective:
    def __init__(self, p=6, seed=42):
        np.random.seed(seed)
        self.p = p
        # Quadratic loss: L(theta) = 0.5 * (theta - theta*)^T A (theta - theta*) + noise
        M = np.random.randn(p, p)
        self.A = 0.5 * (M.T @ M) + 2.0 * np.eye(p)
        self.theta_star = np.array([40.0, 40.0, 40.0, 37.0, 36.0, 36.0])
        
    def evaluate(self, theta, noise_std=0.01):
        diff = theta - self.theta_star
        val = 0.5 * float(diff @ self.A @ diff)
        noise = np.random.normal(0.0, noise_std) if noise_std > 0 else 0.0
        return val + noise
    
    def true_gradient(self, theta):
        return self.A @ (theta - self.theta_star)

def spsa_gradient_estimate(obj, theta, c=0.01, num_replications=35):
    p = len(theta)
    g_accum = np.zeros(p)
    
    for _ in range(num_replications):
        delta = 2.0 * np.random.randint(0, 2, size=p) - 1.0
        
        theta_plus = theta + c * delta
        theta_minus = theta - c * delta
        
        y_plus = obj.evaluate(theta_plus, noise_std=0.01)
        y_minus = obj.evaluate(theta_minus, noise_std=0.01)
        
        g_rep = ((y_plus - y_minus) / (2.0 * c)) * (1.0 / delta)
        g_accum += g_rep
        
    return g_accum / num_replications

def test_spsa_accuracy_and_convergence(seed=2026):
    np.random.seed(seed)
    obj = BlackBoxPacingObjective(p=6, seed=seed)
    
    # 1. Cosine alignment test across random points
    alignments = []
    for _ in range(20):
        theta_test = obj.theta_star + np.random.uniform(-4.0, 4.0, size=6)
        true_g = obj.true_gradient(theta_test)
        
        est_g = spsa_gradient_estimate(obj, theta_test, c=0.01, num_replications=60)
        
        norm_true = np.linalg.norm(true_g)
        norm_est = np.linalg.norm(est_g)
        
        if norm_true > 1e-6 and norm_est > 1e-6:
            cos_sim = float(np.dot(true_g, est_g) / (norm_true * norm_est))
            alignments.append(cos_sim)
            
    mean_alignment = float(np.mean(alignments))
    min_alignment = float(np.min(alignments))
    
    # 2. Optimization convergence test
    theta = np.array([35.0, 36.0, 38.0, 34.0, 33.0, 38.0])
    a_0 = 0.08
    A_stab = 15.0
    c_0 = 0.05
    
    for k in range(1, 400):
        a_k = a_0 / ((k + A_stab) ** 0.60)
        c_k = c_0 / (k ** 0.10)
        
        g_hat = spsa_gradient_estimate(obj, theta, c=c_k, num_replications=10)
        theta -= a_k * g_hat
        
    final_error = float(np.linalg.norm(theta - obj.theta_star))
    converged = bool(final_error < 1.0)
    
    passed = (mean_alignment >= 0.95) and converged
    
    return {
        "mean_cosine_alignment": mean_alignment,
        "min_cosine_alignment": min_alignment,
        "final_parameter_distance": final_error,
        "converged": converged,
        "passed": passed
    }

def main():
    print("=== Task 0483: SPSA Zero-Order Gradient Reconstruction ===")
    
    runs = 15
    alignments = []
    conv_flags = []
    
    for r in range(runs):
        res = test_spsa_accuracy_and_convergence(seed=100 + r)
        alignments.append(res["mean_cosine_alignment"])
        conv_flags.append(res["converged"] and res["passed"])
        
    mean_cos = float(np.mean(alignments))
    min_cos = float(np.min(alignments))
    conv_rate = (sum(conv_flags) / runs) * 100.0
    
    passed = (mean_cos >= 0.95) and (conv_rate == 100.0)
    
    summary = {
        "runs": runs,
        "mean_cosine_alignment": mean_cos,
        "min_cosine_alignment": min_cos,
        "target_cosine_threshold": 0.95,
        "convergence_rate": conv_rate,
        "passed": bool(passed)
    }
    
    print(json.dumps(summary, indent=2))
    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    main()


