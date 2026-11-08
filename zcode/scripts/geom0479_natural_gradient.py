# -*- coding: utf-8 -*-
"""
Task 0479: Information Geometry Natural Gradient on Fisher Information Manifold
- Pacing rate policy distribution p_theta(a) = N(mu, sigma^2), theta = [mu, ln(sigma)]
- Fisher Information Matrix (FIM) F(theta) = E[ nabla ln p * nabla ln p^T ]
- Ill-conditioned loss landscape representing shallow buffer delay vs pacing rate
- Natural gradient: d_theta = F(theta)^(-1) * nabla J(theta)
- Target: Convergence speedup >= 3.0x, FIM positive definiteness 100.0%
"""

import sys
import json
import numpy as np

def loss_function(mu, log_sigma):
    """
    Anisotropic ill-conditioned loss landscape:
    J(mu, log_sigma) = 100.0 * (mu - 40.0)^2 + 2.0 * (log_sigma - (-1.0))^2
    Condition number ~ 50.
    """
    return 100.0 * ((mu - 40.0) ** 2) + 2.0 * ((log_sigma - (-1.0)) ** 2)

def gradient(mu, log_sigma):
    d_mu = 200.0 * (mu - 40.0)
    d_log_sigma = 4.0 * (log_sigma - (-1.0))
    return np.array([d_mu, d_log_sigma])

def fisher_information_matrix(mu, log_sigma):
    """
    Analytical FIM for Gaussian policy theta = [mu, log_sigma]:
    F = diag( 1 / sigma^2, 2 )
    """
    sigma = np.exp(log_sigma)
    return np.diag([1.0 / (sigma ** 2), 2.0])

def run_standard_gradient_descent(init_theta, max_iter=3000, lr=0.003, tol=1e-3):
    theta = init_theta.copy()
    for it in range(max_iter):
        loss = loss_function(theta[0], theta[1])
        if loss < tol:
            return it + 1, loss
        g = gradient(theta[0], theta[1])
        theta -= lr * g
    return max_iter, loss_function(theta[0], theta[1])

def run_natural_gradient_descent(init_theta, max_iter=3000, lr=0.05, tol=1e-3):
    theta = init_theta.copy()
    for it in range(max_iter):
        loss = loss_function(theta[0], theta[1])
        if loss < tol:
            return it + 1, loss
        g = gradient(theta[0], theta[1])
        F = fisher_information_matrix(theta[0], theta[1])
        nat_g = np.linalg.solve(F, g)
        theta -= lr * nat_g
    return max_iter, loss_function(theta[0], theta[1])

def main():
    print("=== Task 0479: Natural Gradient on Fisher Information Manifold ===")
    
    runs = 25
    speedups = []
    fim_pd_flags = []
    
    for r in range(runs):
        np.random.seed(300 + r)
        mu_0 = np.random.uniform(25.0, 32.0)
        log_sig_0 = np.random.uniform(0.5, 1.5)
        init_theta = np.array([mu_0, log_sig_0])
        
        # Test FIM positive definiteness
        F = fisher_information_matrix(mu_0, log_sig_0)
        eigvals = np.linalg.eigvalsh(F)
        fim_pd = bool(np.all(eigvals > 0))
        fim_pd_flags.append(fim_pd)
        
        iters_std, _ = run_standard_gradient_descent(init_theta, lr=0.003)
        iters_nat, _ = run_natural_gradient_descent(init_theta, lr=0.04)
        
        speedup = float(iters_std) / max(1.0, float(iters_nat))
        speedups.append(speedup)
        
    mean_speedup = float(np.mean(speedups))
    min_speedup = float(np.min(speedups))
    fim_pd_rate = (sum(fim_pd_flags) / runs) * 100.0
    
    passed = (mean_speedup >= 3.0) and (fim_pd_rate == 100.0)
    
    summary = {
        "runs": runs,
        "mean_natural_gradient_speedup": mean_speedup,
        "min_natural_gradient_speedup": min_speedup,
        "target_speedup_threshold": 3.0,
        "fim_positive_definiteness_rate": fim_pd_rate,
        "passed": bool(passed)
    }
    
    print(json.dumps(summary, indent=2))
    if not overall_passed if 'overall_passed' in locals() else not passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
