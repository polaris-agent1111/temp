# -*- coding: utf-8 -*-
"""
Task 0447: Continuous-Time Kalman-Bucy Filter and Continuous Algebraic Riccati Equation (CARE) Solver
"""

import sys
import json
import numpy as np
from scipy.linalg import solve_continuous_are

def solve_kalman_bucy_care(dim=4):
    """
    State dimension 4:
    x1: Queue backlog
    x2: Pacing rate error
    x3: Channel RTT delay
    x4: Background cross-traffic intensity
    """
    np.random.seed(42)
    
    # System matrix A (asymptotically stable open loop with inter-state coupling)
    A = np.array([
        [-1.2,  0.8, -0.4,  0.5],
        [ 0.0, -2.5,  0.0,  0.0],
        [ 0.3,  0.0, -1.8,  0.2],
        [ 0.0,  0.0,  0.0, -0.8]
    ])
    
    # Measurement matrix C (observing queue and RTT)
    C = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0]
    ])
    
    # Process noise covariance Q (positive definite)
    Q = np.diag([0.5, 0.2, 0.4, 0.8])
    
    # Measurement noise covariance R (positive definite)
    R = np.diag([0.1, 0.15])
    
    # Solve CARE: A*P + P*A^T - P*C^T*R^(-1)*C*P + Q = 0
    # In scipy notation for CARE: A_care^T * P + P * A_care - P * B * R^-1 * B^T * P + Q = 0
    # For filter duality: A_care = A^T, B_care = C^T, Q_care = Q, R_care = R
    P_star = solve_continuous_are(A.T, C.T, Q, R)
    
    # Verify Riccati Residual: A*P + P*A^T + Q - P*C^T*inv(R)*C*P
    R_inv = np.linalg.inv(R)
    quad_term = P_star @ C.T @ R_inv @ C @ P_star
    care_residual_matrix = A @ P_star + P_star @ A.T + Q - quad_term
    care_residual = float(np.linalg.norm(care_residual_matrix, 'fro'))
    
    # Optimal Kalman gain: K = P * C^T * R^-1
    K_star = P_star @ C.T @ R_inv
    
    # Closed loop error dynamics: A_cl = A - K * C
    A_cl = A - K_star @ C
    cl_eigvals = np.linalg.eigvals(A_cl)
    max_real_eig = float(np.max(np.real(cl_eigvals)))
    
    is_stable = bool(max_real_eig < -1e-4)
    is_pos_def = bool(np.all(np.linalg.eigvalsh(P_star) > 0))
    
    passed = (care_residual < 1e-6) and is_stable and is_pos_def
    
    return {
        "state_dimension": dim,
        "care_frobenius_residual": care_residual,
        "riccati_solution_min_eig": float(np.min(np.linalg.eigvalsh(P_star))),
        "is_positive_definite": is_pos_def,
        "closed_loop_max_real_eigenvalue": max_real_eig,
        "asymptotic_stability_rate": 100.0 if is_stable else 0.0,
        "kalman_gain_norm": float(np.linalg.norm(K_star, 'fro')),
        "passed": passed
    }

def main():
    result = solve_kalman_bucy_care(dim=4)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
