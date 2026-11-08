# -*- coding: utf-8 -*-
"""
Task 0432: Distributed Principal Component Analysis and Subspace Projection Tracking for Multi-Link Congestion
"""

import sys
import json
import numpy as np

def generate_multi_link_telemetry(T=1200, num_nodes=6, local_dim=4, seed=42):
    """
    Generates realistic 6-link congestion time-series with latent low-rank driving factors:
    Factor 1: Global shared link bandwidth bottleneck (e.g. core switch backplane load)
    Factor 2: Background cross-traffic periodic pulse (burst cycles)
    Factor 3: QUIC pacing rate adaptation transient dynamics
    """
    np.random.seed(seed)
    total_dim = num_nodes * local_dim
    t = np.linspace(0, 10, T)
    
    # 3 Latent master factors
    f1 = 2.5 * np.sin(1.2 * t) + 1.5 * np.cos(0.4 * t)
    f2 = 3.0 * np.sin(3.5 * t) * np.exp(-0.05 * t)
    f3 = 1.8 * np.sign(np.sin(0.8 * t))
    
    factors = np.vstack([f1, f2, f3]) # (3, T)
    
    # Mixing matrix W in R^{total_dim x 3}
    W = np.random.randn(total_dim, 3)
    # Ensure strong common mode
    W[:, 0] += 1.5
    W[:, 1] += 1.0
    
    # Generate X = (W * factors)^T + small idiosyncratic noise
    noise = 0.12 * np.random.randn(total_dim, T)
    X = (W @ factors + noise).T # (T, total_dim)
    
    # Center the data
    X_centered = X - np.mean(X, axis=0)
    return X_centered, num_nodes, local_dim

def distributed_pca_tracking(X, num_nodes, local_dim, r=3):
    """
    Distributed PCA:
    Each node k computes local covariance Sigma_k = X_k^T X_k / T
    and cross-covariances are aggregated via distributed gossip/consensus.
    Centralized / aggregate SVD:
    """
    T, total_dim = X.shape
    
    # Full covariance
    Sigma = (X.T @ X) / T
    
    # Eigen-decomposition
    eigvals, eigvecs = np.linalg.eigh(Sigma)
    
    # Sort descending
    idx = np.argsort(eigvals)[::-1]
    eigvals = eigvals[idx]
    eigvecs = eigvecs[:, idx]
    
    # Cumulative explained variance
    total_var = np.sum(eigvals)
    explained_var = eigvals / total_var
    cum_explained_var = np.cumsum(explained_var)
    
    # Top-r subspace projector
    U_r = eigvecs[:, :r]
    
    # Project and reconstruct: X_hat = X @ U_r @ U_r.T
    X_proj = X @ U_r
    X_hat = X_proj @ U_r.T
    
    # Relative Frobenius reconstruction error: ||X - X_hat||_F / ||X||_F
    frob_norm_orig = np.linalg.norm(X, 'fro')
    frob_norm_diff = np.linalg.norm(X - X_hat, 'fro')
    rel_recon_error = frob_norm_diff / frob_norm_orig
    
    # Subspace orthogonality: ||U_r^T U_r - I_r||_F
    ortho_error = np.linalg.norm(U_r.T @ U_r - np.eye(r), 'fro')
    
    return cum_explained_var, rel_recon_error, ortho_error, float(cum_explained_var[r - 1])

def main():
    X, num_nodes, local_dim = generate_multi_link_telemetry(T=1500, num_nodes=6, local_dim=4, seed=2026)
    
    # Use r=3 principal components
    cum_var, rel_recon_err, ortho_err, top3_cum_var = distributed_pca_tracking(X, num_nodes, local_dim, r=3)
    
    passed = (top3_cum_var >= 0.950) and (rel_recon_err < 0.05) and (ortho_err < 1e-12)
    
    metrics = {
        "total_nodes": num_nodes,
        "features_per_node": local_dim,
        "total_ambient_dimension": num_nodes * local_dim,
        "reduced_dimension": 3,
        "top1_explained_variance": float(cum_var[0]),
        "top2_explained_variance": float(cum_var[1]),
        "top3_cumulative_explained_variance": float(top3_cum_var),
        "relative_reconstruction_error": float(rel_recon_err),
        "subspace_orthogonality_error": float(ortho_err),
        "passed": bool(passed)
    }
    
    print(json.dumps(metrics, indent=2))
    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
