# -*- coding: utf-8 -*-
"""
Task 0465: Dirichlet Process Mixture Model (DPMM) Unsupervised Microburst Phase Clustering
- Non-parametric Bayesian clustering of telemetry burst phases without predefining K
- Stick-breaking prior Dirichlet Process / Variational Gibbs inference
- Target: Convergence rate 100.0%, Adjusted Rand Index (ARI) >= 0.90
"""

import sys
import json
import numpy as np
from sklearn.mixture import BayesianGaussianMixture
from sklearn.metrics import adjusted_rand_score

def generate_synthetic_burst_telemetry(n_samples_per_mode=300, seed=42):
    np.random.seed(seed)
    
    # Mode 0: Idle pacing phase (low throughput, small jitter)
    x0 = np.random.normal(loc=[10.0, 1.2], scale=[1.0, 0.2], size=(n_samples_per_mode, 2))
    
    # Mode 1: Steady linear ramp (medium throughput, medium delay)
    x1 = np.random.normal(loc=[50.0, 3.5], scale=[3.0, 0.4], size=(n_samples_per_mode, 2))
    
    # Mode 2: Microburst peak saturation (high throughput, queue buildup)
    x2 = np.random.normal(loc=[95.0, 8.0], scale=[4.0, 0.6], size=(n_samples_per_mode, 2))
    
    # Mode 3: Post-burst drain / backoff dissipation
    x3 = np.random.normal(loc=[25.0, 5.5], scale=[2.5, 0.5], size=(n_samples_per_mode, 2))
    
    X = np.vstack([x0, x1, x2, x3])
    y_true = np.concatenate([
        np.zeros(n_samples_per_mode, dtype=int),
        np.ones(n_samples_per_mode, dtype=int),
        np.full(n_samples_per_mode, 2, dtype=int),
        np.full(n_samples_per_mode, 3, dtype=int)
    ])
    
    indices = np.random.permutation(len(X))
    return X[indices], y_true[indices]

def run_dpmm_experiment(seed=2026):
    X, y_true = generate_synthetic_burst_telemetry(n_samples_per_mode=400, seed=seed)
    
    # Fit Dirichlet Process Gaussian Mixture Model with stick-breaking prior
    dpgmm = BayesianGaussianMixture(
        n_components=10,  # Upper bound truncation
        covariance_type='full',
        weight_concentration_prior_type='dirichlet_process',
        weight_concentration_prior=0.5,
        max_iter=300,
        random_state=seed
    )
    
    dpgmm.fit(X)
    y_pred = dpgmm.predict(X)
    
    # Count active clusters (weights > 0.05)
    active_clusters = int(np.sum(dpgmm.weights_ > 0.05))
    
    # Clustering accuracy via Adjusted Rand Index
    ari = float(adjusted_rand_score(y_true, y_pred))
    
    converged = bool(dpgmm.converged_)
    
    passed = converged and (ari >= 0.90) and (active_clusters == 4)
    
    return {
        "converged": converged,
        "n_iter": int(dpgmm.n_iter_),
        "discovered_active_clusters": active_clusters,
        "true_clusters_count": 4,
        "adjusted_rand_index": ari,
        "weights": [float(w) for w in dpgmm.weights_ if w > 0.01],
        "passed": bool(passed)
    }

def main():
    print("=== Task 0465: DPMM Unsupervised Microburst Phase Clustering ===")
    
    runs = 10
    aris = []
    converged_count = 0
    
    for r in range(runs):
        res = run_dpmm_experiment(seed=100 + r)
        aris.append(res["adjusted_rand_index"])
        if res["converged"] and res["passed"]:
            converged_count += 1
            
    mean_ari = float(np.mean(aris))
    min_ari = float(np.min(aris))
    convergence_rate = (converged_count / runs) * 100.0
    
    overall_passed = (convergence_rate == 100.0) and (min_ari >= 0.90)
    
    summary = {
        "runs": runs,
        "converged_runs": converged_count,
        "convergence_rate": convergence_rate,
        "mean_adjusted_rand_index": mean_ari,
        "min_adjusted_rand_index": min_ari,
        "ari_target_threshold": 0.90,
        "passed": bool(overall_passed)
    }
    
    print(json.dumps(summary, indent=2))
    if not overall_passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
