# -*- coding: utf-8 -*-
"""
Task 0440: Higher-Order Tucker Tensor Decomposition for Spatio-Temporal Microburst Covariance
"""

import sys
import json
import numpy as np

def generate_spatiotemporal_covariance_tensor(I1=6, I2=4, I3=20, seed=42):
    """
    Generates a 3rd-order spatio-temporal covariance tensor:
    Mode 1: 6 network nodes/links
    Mode 2: 4 metrics (queue, pacing, RTT, loss)
    Mode 3: 20 lag time steps
    Driven by low-rank latent subspace (R1=3, R2=2, R3=4) + slight noise
    """
    np.random.seed(seed)
    R1, R2, R3 = 3, 2, 4
    
    # Core tensor G
    G = np.random.randn(R1, R2, R3)
    G[0, 0, 0] = 12.0
    G[1, 1, 1] = 8.0
    G[2, 0, 2] = 6.0
    G[0, 1, 3] = 4.0
    
    # Factor matrices
    U1, _ = np.linalg.qr(np.random.randn(I1, R1))
    U2, _ = np.linalg.qr(np.random.randn(I2, R2))
    U3, _ = np.linalg.qr(np.random.randn(I3, R3))
    
    # Synthesize clean tensor: X_clean = G x1 U1 x2 U2 x3 U3
    # G in (R1, R2, R3), U1 in (I1, R1), U2 in (I2, R2), U3 in (I3, R3)
    X_clean = np.einsum('ijk,ai,bj,ck->abc', G, U1, U2, U3)
    
    # Add slight background noise
    noise = 0.015 * np.random.randn(I1, I2, I3)
    X = X_clean + noise
    
    return X, (R1, R2, R3)

def mode_n_unfolding(tensor, mode):
    """
    Unfolds 3D tensor along mode (0-indexed).
    Mode 0: (I1, I2 * I3)
    Mode 1: (I2, I1 * I3)
    Mode 2: (I3, I1 * I2)
    """
    return np.rollaxis(tensor, mode, 0).reshape((tensor.shape[mode], -1))

def tucker_hooi(X, ranks, max_iter=25, tol=1e-8):
    """
    Higher-Order Orthogonal Iteration (HOOI) algorithm for Tucker decomposition
    """
    I1, I2, I3 = X.shape
    R1, R2, R3 = ranks
    
    # Initialize factor matrices with HOSVD
    A1 = mode_n_unfolding(X, 0)
    U1, _, _ = np.linalg.svd(A1, full_matrices=False)
    U1 = U1[:, :R1]
    
    A2 = mode_n_unfolding(X, 1)
    U2, _, _ = np.linalg.svd(A2, full_matrices=False)
    U2 = U2[:, :R2]
    
    A3 = mode_n_unfolding(X, 2)
    U3, _, _ = np.linalg.svd(A3, full_matrices=False)
    U3 = U3[:, :R3]
    
    # Alternating least squares iterations
    for it in range(max_iter):
        # Update U1: project X onto U2 and U3
        # Y1 has shape (I1, R2, R3)
        Y1 = np.einsum('abc,bj,ck->ajk', X, U2, U3)
        Y1_unfold = mode_n_unfolding(Y1, 0)
        U1, _, _ = np.linalg.svd(Y1_unfold, full_matrices=False)
        U1 = U1[:, :R1]
        
        # Update U2: project X onto U1 and U3
        # Y2 has shape (R1, I2, R3)
        Y2 = np.einsum('abc,ai,ck->ibk', X, U1, U3)
        Y2_unfold = mode_n_unfolding(Y2, 1)
        U2, _, _ = np.linalg.svd(Y2_unfold, full_matrices=False)
        U2 = U2[:, :R2]
        
        # Update U3: project X onto U1 and U2
        # Y3 has shape (R1, R2, I3)
        Y3 = np.einsum('abc,ai,bj->ijc', X, U1, U2)
        Y3_unfold = mode_n_unfolding(Y3, 2)
        U3, _, _ = np.linalg.svd(Y3_unfold, full_matrices=False)
        U3 = U3[:, :R3]
        
    # Core tensor G = X x1 U1^T x2 U2^T x3 U3^T
    G = np.einsum('abc,ai,bj,ck->ijk', X, U1, U2, U3)
    
    # Reconstructed tensor
    X_hat = np.einsum('ijk,ai,bj,ck->abc', G, U1, U2, U3)
    
    # Metrics
    norm_X = np.linalg.norm(X)
    norm_G = np.linalg.norm(G)
    energy_retention = (norm_G ** 2) / (norm_X ** 2) * 100.0
    rel_error = np.linalg.norm(X - X_hat) / norm_X
    
    return G, U1, U2, U3, float(energy_retention), float(rel_error)

def main():
    X, ranks = generate_spatiotemporal_covariance_tensor(I1=6, I2=4, I3=20, seed=2026)
    G, U1, U2, U3, energy_ret, rel_err = tucker_hooi(X, ranks, max_iter=30)
    
    passed = (energy_ret >= 95.0) and (rel_err < 0.05)
    
    result = {
        "tensor_shape": list(X.shape),
        "tucker_ranks": list(ranks),
        "core_tensor_shape": list(G.shape),
        "energy_retention_percent": energy_ret,
        "relative_reconstruction_error": rel_err,
        "orthogonality_U1_error": float(np.linalg.norm(U1.T @ U1 - np.eye(ranks[0]))),
        "orthogonality_U2_error": float(np.linalg.norm(U2.T @ U2 - np.eye(ranks[1]))),
        "orthogonality_U3_error": float(np.linalg.norm(U3.T @ U3 - np.eye(ranks[2]))),
        "passed": bool(passed)
    }
    
    print(json.dumps(result, indent=2))
    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
