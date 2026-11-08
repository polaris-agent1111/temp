# -*- coding: utf-8 -*-
"""
Task 0452: Matrix-Geometric Method for Quasi-Birth-Death (QBD) Shallow-Buffer Queuing Process
"""

import sys
import json
import numpy as np

def build_qbd_blocks(m=2, lambda1=25.0, lambda2=45.0, mu=48.0, gamma12=2.0, gamma21=8.0):
    """
    Two-phase traffic arrival:
    Phase 1: Normal pacing (arrival rate lambda1 = 25)
    Phase 2: Microburst surge (arrival rate lambda2 = 45)
    Drain rate: mu = 48.0 (bottleneck line speed)
    Phase transition rates: 1->2 with gamma12, 2->1 with gamma21
    """
    # Arrival matrix A0 (dim m x m)
    A0 = np.diag([lambda1, lambda2])
    
    # Service matrix A2 (dim m x m)
    A2 = np.diag([mu, mu])
    
    # Internal phase matrix A1
    A1 = np.array([
        [-(lambda1 + mu + gamma12), gamma12],
        [gamma21, -(lambda2 + mu + gamma21)]
    ])
    
    # Boundary blocks B00, B01
    B01 = A0.copy()
    B00 = np.array([
        [-(lambda1 + gamma12), gamma12],
        [gamma21, -(lambda2 + gamma21)]
    ])
    
    return A0, A1, A2, B00, B01

def solve_rate_matrix_r(A0, A1, A2, max_iter=200, tol=1e-12):
    """
    Solves R^2 A2 + R A1 + A0 = 0 using successive substitution / functional iteration:
    R_{k+1} = - (A0 + R_k^2 A2) A1^-1
    """
    m = A0.shape[0]
    R = np.zeros((m, m))
    A1_inv = np.linalg.inv(A1)
    
    for it in range(max_iter):
        R_next = - (A0 + (R @ R @ A2)) @ A1_inv
        diff = np.linalg.norm(R_next - R, 'fro')
        R = R_next
        if diff < tol:
            break
            
    # Residual error: R^2 A2 + R A1 + A0
    residual_mat = (R @ R @ A2) + (R @ A1) + A0
    res_norm = float(np.linalg.norm(residual_mat, 'fro'))
    
    # Spectral radius rho(R)
    eigvals = np.linalg.eigvals(R)
    rho_R = float(np.max(np.abs(eigvals)))
    
    return R, res_norm, rho_R

def compute_stationary_distribution(R, A2, B00):
    """
    pi_0 * (B00 + R A2) = 0
    pi_0 * (I - R)^-1 * 1 = 1
    """
    m = R.shape[0]
    M_boundary = B00 + R @ A2
    # Find left null-vector: M_boundary^T * pi_0^T = 0
    u, s, vh = np.linalg.svd(M_boundary.T)
    pi0_raw = np.abs(vh[-1, :])
    
    # Normalization: pi0 * (I - R)^-1 * 1 = 1
    I_minus_R_inv = np.linalg.inv(np.eye(m) - R)
    norm_factor = np.sum(pi0_raw @ I_minus_R_inv)
    pi0 = pi0_raw / norm_factor
    
    # Total probability check
    total_prob = float(np.sum(pi0 @ I_minus_R_inv))
    prob_error = float(abs(total_prob - 1.0))
    
    # Average queue length L = sum_{i=1}^inf i * pi_i * 1 = pi0 * R (I - R)^-2 * 1
    I_minus_R_inv2 = I_minus_R_inv @ I_minus_R_inv
    mean_queue_len = float(np.sum(pi0 @ R @ I_minus_R_inv2))
    
    return pi0, total_prob, prob_error, mean_queue_len

def main():
    A0, A1, A2, B00, B01 = build_qbd_blocks(m=2, lambda1=25.0, lambda2=45.0, mu=48.0, gamma12=2.0, gamma21=8.0)
    R, res_norm, rho_R = solve_rate_matrix_r(A0, A1, A2)
    pi0, total_prob, prob_err, L_mean = compute_stationary_distribution(R, A2, B00)
    
    passed = (res_norm < 1e-6) and (rho_R < 1.0) and (prob_err < 1e-6)
    
    result = {
        "phases_m": 2,
        "rate_matrix_quadratic_residual": res_norm,
        "rate_matrix_spectral_radius": rho_R,
        "rate_matrix_stability": bool(rho_R < 1.0),
        "stationary_pi0": list(np.round(pi0, 6)),
        "total_probability_sum": total_prob,
        "probability_normalization_error": prob_err,
        "theoretical_mean_queue_length_packets": L_mean,
        "passed": bool(passed)
    }
    
    print(json.dumps(result, indent=2))
    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
