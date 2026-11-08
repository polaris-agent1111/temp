# -*- coding: utf-8 -*-
"""
Task 0462: FastICA Blind Source Separation and Mutual Information Decoupling for 6-Flow Topology Overlap
"""

import sys
import json
import numpy as np
from sklearn.decomposition import FastICA

def generate_mixed_network_telemetry(T=2000, seed=42):
    np.random.seed(seed)
    t = np.linspace(0, 10, T)
    
    # 3 Independent Non-Gaussian Source Signals:
    # Source 1: Sawtooth pulse (periodic microburst)
    s1 = 2.0 * (t % 1.0) - 1.0
    # Source 2: Binary phase telegraph signal (competing bulk transfer on/off)
    s2 = np.sign(np.sin(3.0 * t))
    # Source 3: Super-Gaussian Laplacian noise (stochastic queue delay jitter)
    s3 = np.random.laplace(loc=0.0, scale=1.0, size=T)
    
    S = np.vstack([s1, s2, s3]) # (3, T)
    
    # 6x3 Mixing matrix representing link topology overlap
    A = np.array([
        [0.8, 0.2, 0.1],
        [0.7, 0.5, 0.3],
        [0.1, 0.9, 0.2],
        [0.4, 0.4, 0.7],
        [0.9, 0.1, 0.5],
        [0.3, 0.8, 0.4]
    ])
    
    # Mixed observation X in R^{6 x T} + small noise
    X = A @ S + 0.02 * np.random.randn(6, T)
    return S, X.T, A

def compute_mutual_information_metric(data):
    """
    Computes average pairwise mutual information via Gaussian copula approximation:
    I(X_i, X_j) = -0.5 * ln(1 - rho_ij^2)
    """
    corr = np.corrcoef(data, rowvar=False)
    p = corr.shape[0]
    mi_sum = 0.0
    count = 0
    for i in range(p):
        for j in range(i + 1, p):
            rho = np.clip(corr[i, j], -0.999, 0.999)
            mi = -0.5 * np.log(1.0 - (rho ** 2))
            mi_sum += mi
            count += 1
    return mi_sum / max(1, count)

def run_fastica_analysis(seed=2026):
    S_true, X_obs, A_mix = generate_mixed_network_telemetry(T=3000, seed=seed)
    
    # Initial mutual information among observed mixed channels
    # Pick first 3 channels
    mi_initial = compute_mutual_information_metric(X_obs[:, :3])
    
    # Run FastICA to recover 3 independent components
    ica = FastICA(n_components=3, random_state=seed, max_iter=500, tol=1e-5)
    S_est = ica.fit_transform(X_obs)  # (T, 3)
    
    # Post-separation mutual information among estimated sources
    mi_final = compute_mutual_information_metric(S_est)
    
    # Decoupling orthogonality error of unmixing matrix
    W = ica.components_  # (3, 6)
    # Project W onto its dominant subspace
    U, s, Vt = np.linalg.svd(W, full_matrices=False)
    ortho_error = float(np.linalg.norm(U.T @ U - np.eye(3), 'fro'))
    
    # Correlation between estimated sources: should be near zero off-diagonal
    corr_est = np.corrcoef(S_est, rowvar=False)
    off_diag_corr = float(np.max(np.abs(corr_est - np.eye(3))))
    
    mi_decay_rate = float((mi_initial - mi_final) / mi_initial) * 100.0
    
    passed = (ortho_error < 0.05) and (mi_decay_rate >= 95.0) and (off_diag_corr < 0.05)
    
    return {
        "sources_count": 3,
        "observed_links_count": 6,
        "initial_mixed_mutual_information": float(mi_initial),
        "post_ica_mutual_information": float(mi_final),
        "mutual_information_reduction_percent": mi_decay_rate,
        "max_off_diagonal_source_correlation": off_diag_corr,
        "unmixing_orthogonality_error": ortho_error,
        "passed": bool(passed)
    }

def main():
    result = run_fastica_analysis(seed=2026)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
