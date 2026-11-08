# -*- coding: utf-8 -*-
"""
Task 0449: LMI-based H-infinity Robust Stabilization for Networked Control Systems with Packet Dropouts
"""

import sys
import json
import numpy as np
from scipy.optimize import minimize

def build_ncs_matrices(dim=3):
    """
    State x_k in R^3: [queue_deviation, rate_tracking_error, RTT_variation]
    Control u_k in R^1: pacing rate adjustment
    Disturbance w_k in R^1: background traffic shock
    """
    A = np.array([
        [0.85, 0.20, -0.10],
        [0.00, 0.75,  0.05],
        [0.10, 0.00,  0.60]
    ])
    B = np.array([
        [0.30],
        [0.50],
        [0.10]
    ])
    B_w = np.array([
        [0.15],
        [0.25],
        [0.10]
    ])
    C_z = np.array([
        [0.50, 0.00, 0.00],
        [0.00, 0.40, 0.00]
    ])
    D_z = np.array([
        [0.20],
        [0.10]
    ])
    return A, B, B_w, C_z, D_z

def solve_lmi_hinf(theta_bar=0.85, gamma=0.75):
    A, B, B_w, C_z, D_z = build_ncs_matrices()
    n = A.shape[0]
    m = B.shape[1]
    p = C_z.shape[0]
    nw = B_w.shape[1]
    
    sigma_theta = np.sqrt(theta_bar * (1.0 - theta_bar))
    
    # We solve for X = X^T > 0 in R^{3x3} and Y in R^{1x3}
    # Parameterize X via Cholesky factor L: X = L L^T + 0.05 * I
    # Total params: 6 for L + 3 for Y = 9 params
    
    def unpack(params):
        L_mat = np.zeros((n, n))
        L_mat[0, 0] = params[0]
        L_mat[1, 0] = params[1]
        L_mat[1, 1] = params[2]
        L_mat[2, 0] = params[3]
        L_mat[2, 1] = params[4]
        L_mat[2, 2] = params[5]
        X = L_mat @ L_mat.T + 0.05 * np.eye(n)
        Y = params[6:9].reshape((m, n))
        return X, Y
        
    def lmi_loss(params):
        X, Y = unpack(params)
        
        # Block row 1: [X, 0, X A^T + theta_bar Y^T B^T, sigma_theta Y^T B^T, X C_z^T + Y^T D_z^T]
        blk11 = X
        blk12 = np.zeros((n, nw))
        blk13 = X @ A.T + theta_bar * (Y.T @ B.T)
        blk14 = sigma_theta * (Y.T @ B.T)
        blk15 = X @ C_z.T + Y.T @ D_z.T
        
        # Block row 2: [*, gamma^2 I, B_w^T, 0, 0]
        blk22 = (gamma ** 2) * np.eye(nw)
        blk23 = B_w.T
        blk24 = np.zeros((nw, n))
        blk25 = np.zeros((nw, p))
        
        # Block row 3: [*, *, X, 0, 0]
        blk33 = X
        blk34 = np.zeros((n, n))
        blk35 = np.zeros((n, p))
        
        # Block row 4: [*, *, *, X, 0]
        blk44 = X
        blk45 = np.zeros((n, p))
        
        # Block row 5: [*, *, *, *, I]
        blk55 = np.eye(p)
        
        M = np.block([
            [blk11, blk12, blk13, blk14, blk15],
            [blk12.T, blk22, blk23, blk24, blk25],
            [blk13.T, blk23.T, blk33, blk34, blk35],
            [blk14.T, blk24.T, blk34.T, blk44, blk45],
            [blk15.T, blk25.T, blk35.T, blk45.T, blk55]
        ])
        
        # We require M > 0. Penalize minimum eigenvalue if not positive enough
        eigvals = np.linalg.eigvalsh(M)
        min_eig = np.min(eigvals)
        # Minimize: trace(X) - 100 * min(0, min_eig - 0.01)
        penalty = 0.0 if min_eig > 0.02 else (0.02 - min_eig) ** 2 * 1e4
        return 0.1 * np.trace(X) + penalty
        
    init_params = np.array([1.0, 0.0, 1.0, 0.0, 0.0, 1.0, -0.5, -0.5, -0.2])
    res = minimize(lmi_loss, init_params, method='BFGS', tol=1e-7)
    
    X_opt, Y_opt = unpack(res.x)
    K_opt = Y_opt @ np.linalg.inv(X_opt)
    
    # Reconstruct LMI matrix M_opt and check eigenvalues
    blk11 = X_opt
    blk12 = np.zeros((n, nw))
    blk13 = X_opt @ A.T + theta_bar * (Y_opt.T @ B.T)
    blk14 = sigma_theta * (Y_opt.T @ B.T)
    blk15 = X_opt @ C_z.T + Y_opt.T @ D_z.T
    
    blk22 = (gamma ** 2) * np.eye(nw)
    blk23 = B_w.T
    blk24 = np.zeros((nw, n))
    blk25 = np.zeros((nw, p))
    
    blk33 = X_opt
    blk34 = np.zeros((n, n))
    blk35 = np.zeros((n, p))
    
    blk44 = X_opt
    blk45 = np.zeros((n, p))
    
    blk55 = np.eye(p)
    
    M_opt = np.block([
        [blk11, blk12, blk13, blk14, blk15],
        [blk12.T, blk22, blk23, blk24, blk25],
        [blk13.T, blk23.T, blk33, blk34, blk35],
        [blk14.T, blk24.T, blk34.T, blk44, blk45],
        [blk15.T, blk25.T, blk35.T, blk45.T, blk55]
    ])
    
    m_eigvals = np.linalg.eigvalsh(M_opt)
    min_lmi_eig = float(np.min(m_eigvals))
    lmi_feasible = bool(min_lmi_eig > 0.0)
    
    # Closed loop mean stability
    A_mean = A + theta_bar * (B @ K_opt)
    mean_spec_rad = float(np.max(np.abs(np.linalg.eigvals(A_mean))))
    
    # Second-moment Kronecker stability
    # M_2 = (A + theta_bar B K) (x) (A + theta_bar B K) + sigma_theta^2 (B K) (x) (B K)
    BK = B @ K_opt
    M_kron = np.kron(A_mean, A_mean) + (sigma_theta ** 2) * np.kron(BK, BK)
    mean_square_spec_rad = float(np.max(np.abs(np.linalg.eigvals(M_kron))))
    
    passed = lmi_feasible and (mean_spec_rad < 1.0) and (mean_square_spec_rad < 1.0) and (gamma <= 0.85)
    
    return {
        "packet_success_rate_theta_bar": theta_bar,
        "h_infinity_gamma_target": gamma,
        "lmi_minimum_eigenvalue": min_lmi_eig,
        "lmi_strict_feasibility": lmi_feasible,
        "controller_gain_K": list(np.round(K_opt.flatten(), 4)),
        "mean_closed_loop_spectral_radius": mean_spec_rad,
        "mean_square_stability_spectral_radius": mean_square_spec_rad,
        "lmi_solution_success_rate": 100.0 if lmi_feasible else 0.0,
        "passed": bool(passed)
    }

def main():
    result = solve_lmi_hinf(theta_bar=0.85, gamma=0.75)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
