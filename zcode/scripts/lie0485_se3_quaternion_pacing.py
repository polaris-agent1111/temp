# -*- coding: utf-8 -*-
"""
Task 0485: Lie Group SE(3) Rigid Manifold Quaternion Geodesic Pacing Trajectory Interpolation
- Parameter transitions between 6 stages modeled as geodesics on SE(3) = SO(3) x R^3
- Unit quaternion Spherical Linear Interpolation (Slerp)
- Exponential and logarithmic maps on Lie algebra so(3) within injectivity radius ||w|| < pi
- Target: Orthogonal determinant residue |det(R) - 1| < 1e-12, Lie log map error < 1e-6
"""

import sys
import json
import numpy as np

def skew_symmetric(w):
    return np.array([
        [0.0, -w[2], w[1]],
        [w[2], 0.0, -w[0]],
        [-w[1], w[0], 0.0]
    ])

def unskew(W):
    return np.array([W[2, 1], W[0, 2], W[1, 0]])

def exp_so3(w):
    theta = np.linalg.norm(w)
    if theta < 1e-12:
        return np.eye(3)
    W = skew_symmetric(w)
    return np.eye(3) + (np.sin(theta) / theta) * W + ((1.0 - np.cos(theta)) / (theta ** 2)) * (W @ W)

def log_so3(R):
    cos_theta = np.clip((np.trace(R) - 1.0) * 0.5, -1.0, 1.0)
    theta = np.arccos(cos_theta)
    if theta < 1e-12:
        return np.zeros(3)
    sin_theta = np.sin(theta)
    W = (theta / (2.0 * sin_theta)) * (R - R.T)
    return unskew(W)

def quaternion_to_rotation_matrix(q):
    q = q / np.linalg.norm(q)
    w, x, y, z = q
    return np.array([
        [1.0 - 2.0*(y**2 + z**2), 2.0*(x*y - w*z), 2.0*(x*z + w*y)],
        [2.0*(x*y + w*z), 1.0 - 2.0*(x**2 + z**2), 2.0*(y*z - w*x)],
        [2.0*(x*z - w*y), 2.0*(y*z + w*x), 1.0 - 2.0*(x**2 + y**2)]
    ])

def slerp(q1, q2, t):
    q1 = q1 / np.linalg.norm(q1)
    q2 = q2 / np.linalg.norm(q2)
    dot = np.dot(q1, q2)
    if dot < 0.0:
        q2 = -q2
        dot = -dot
    dot = np.clip(dot, -1.0, 1.0)
    theta = np.arccos(dot)
    if theta < 1e-10:
        return q1
    sin_theta = np.sin(theta)
    return (np.sin((1.0 - t) * theta) / sin_theta) * q1 + (np.sin(t * theta) / sin_theta) * q2

def test_lie_group_properties(seed=2026):
    np.random.seed(seed)
    
    det_errors = []
    ortho_errors = []
    log_exp_errors = []
    
    # Generate 50 random Lie algebra elements w in so(3) within injectivity radius ||w|| <= 0.9 * pi
    for _ in range(50):
        direction = np.random.randn(3)
        direction /= np.linalg.norm(direction)
        angle = np.random.uniform(0.01, np.pi * 0.92)
        w_true = direction * angle
        
        R = exp_so3(w_true)
        
        # Check determinant det(R) = 1
        det_val = float(np.linalg.det(R))
        det_errors.append(abs(det_val - 1.0))
        
        # Check orthogonality R^T R = I
        ortho_err = float(np.linalg.norm(R.T @ R - np.eye(3), 'fro'))
        ortho_errors.append(ortho_err)
        
        # Check round-trip log(exp(w)) = w
        w_recovered = log_so3(R)
        log_exp_errors.append(float(np.linalg.norm(w_recovered - w_true)))
        
    # Test Slerp geodesic interpolation along stages
    q_start = np.random.randn(4)
    q_end = np.random.randn(4)
    q_start /= np.linalg.norm(q_start)
    q_end /= np.linalg.norm(q_end)
    
    slerp_det_errors = []
    for t_step in np.linspace(0, 1, 30):
        q_interp = slerp(q_start, q_end, t_step)
        R_interp = quaternion_to_rotation_matrix(q_interp)
        slerp_det_errors.append(abs(np.linalg.det(R_interp) - 1.0))
        
    max_det_err = max(float(np.max(det_errors)), float(np.max(slerp_det_errors)))
    max_log_err = float(np.max(log_exp_errors))
    max_ortho_err = float(np.max(ortho_errors))
    
    passed = (max_det_err < 1e-12) and (max_log_err < 1e-6) and (max_ortho_err < 1e-12)
    
    return {
        "max_determinant_residue": max_det_err,
        "max_orthogonality_error": max_ortho_err,
        "max_log_exp_mapping_error": max_log_err,
        "target_det_threshold": 1e-12,
        "target_log_threshold": 1e-6,
        "passed": bool(passed)
    }

def main():
    print("=== Task 0485: Lie Group SE(3) Quaternion Pacing Interpolation ===")
    
    runs = 20
    det_res = []
    log_errs = []
    passed_flags = []
    
    for r in range(runs):
        res = test_lie_group_properties(seed=500 + r)
        det_res.append(res["max_determinant_residue"])
        log_errs.append(res["max_log_exp_mapping_error"])
        passed_flags.append(res["passed"])
        
    mean_det = float(np.mean(det_res))
    max_det = float(np.max(det_res))
    mean_log = float(np.mean(log_errs))
    max_log = float(np.max(log_errs))
    pass_rate = (sum(passed_flags) / runs) * 100.0
    
    overall_passed = (pass_rate == 100.0)
    
    summary = {
        "runs": runs,
        "max_determinant_residue": max_det,
        "mean_determinant_residue": mean_det,
        "max_log_exp_error": max_log,
        "mean_log_exp_error": mean_log,
        "pass_rate": pass_rate,
        "passed": bool(overall_passed)
    }
    
    print(json.dumps(summary, indent=2))
    if not overall_passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
