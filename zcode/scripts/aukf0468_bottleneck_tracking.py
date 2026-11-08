# -*- coding: utf-8 -*-
"""
Task 0468: Adaptive Unscented Kalman Filter (AUKF) Bottleneck Capacity Tracking
- Dual telemetry observation model: throughput delivery rate and RTT queuing delay
- Unscented Transform with 2n+1 sigma points
- Sage-Husa adaptive innovation covariance estimation
- Target: Relative tracking error < 2.0%, innovation orthogonality consistency 100.0%
"""

import sys
import json
import numpy as np

class AdaptiveUKFBottleneckTracker:
    def __init__(self, alpha=1e-2, beta=2.0, kappa=0.0):
        self.n = 2  # State: [C_t (capacity Mbps), q_t (queue length pkts)]
        self.m = 2  # Measurement: [throughput Mbps, queue pkts]
        self.alpha = alpha
        self.beta = beta
        self.kappa = kappa
        self.lam = (alpha ** 2) * (self.n + kappa) - self.n
        
        # Weights for mean and covariance
        self.Wm = np.zeros(2 * self.n + 1)
        self.Wc = np.zeros(2 * self.n + 1)
        self.Wm[0] = self.lam / (self.n + self.lam)
        self.Wc[0] = self.Wm[0] + (1.0 - alpha**2 + beta)
        for i in range(1, 2 * self.n + 1):
            self.Wm[i] = 1.0 / (2.0 * (self.n + self.lam))
            self.Wc[i] = self.Wm[i]
            
        # State estimate and covariance
        self.x = np.array([95.0, 8.0])
        self.P = np.diag([10.0, 4.0])
        self.Q = np.diag([1.5, 0.8])     # Process noise
        self.R = np.diag([0.25, 0.1])    # Measurement noise
        
    def generate_sigma_points(self, x, P):
        gamma = np.sqrt(self.n + self.lam)
        # Ensure P is positive definite
        P_sym = 0.5 * (P + P.T) + 1e-6 * np.eye(self.n)
        L = np.linalg.cholesky(P_sym)
        sigmas = np.zeros((2 * self.n + 1, self.n))
        sigmas[0] = x
        for i in range(self.n):
            sigmas[i + 1] = x + gamma * L[:, i]
            sigmas[self.n + i + 1] = x - gamma * L[:, i]
        return sigmas
    
    def state_transition(self, sigmas):
        # Capacity and queue follow continuous random drift
        return sigmas.copy()
    
    def observation_model(self, sigmas):
        num_pts = sigmas.shape[0]
        y_sigmas = np.zeros((num_pts, self.m))
        for i in range(num_pts):
            C = sigmas[i, 0]
            q = sigmas[i, 1]
            y_thru = C / (1.0 + 0.01 * max(0.0, q))
            y_q = q
            y_sigmas[i] = [y_thru, y_q]
        return y_sigmas
    
    def step(self, y_obs, b=0.98):
        # 1. Predict
        sigmas_k = self.generate_sigma_points(self.x, self.P)
        sigmas_pred = self.state_transition(sigmas_k)
        
        x_pred = np.sum(self.Wm[:, None] * sigmas_pred, axis=0)
        P_pred = self.Q.copy()
        for i in range(2 * self.n + 1):
            diff = sigmas_pred[i] - x_pred
            P_pred += self.Wc[i] * np.outer(diff, diff)
            
        # 2. Update
        sigmas_meas = self.generate_sigma_points(x_pred, P_pred)
        y_sigmas = self.observation_model(sigmas_meas)
        
        y_pred = np.sum(self.Wm[:, None] * y_sigmas, axis=0)
        P_yy = self.R.copy()
        P_xy = np.zeros((self.n, self.m))
        
        for i in range(2 * self.n + 1):
            diff_y = y_sigmas[i] - y_pred
            diff_x = sigmas_meas[i] - x_pred
            P_yy += self.Wc[i] * np.outer(diff_y, diff_y)
            P_xy += self.Wc[i] * np.outer(diff_x, diff_y)
            
        K = P_xy @ np.linalg.inv(P_yy)
        innovation = y_obs - y_pred
        
        self.x = x_pred + K @ innovation
        self.P = P_pred - K @ P_yy @ K.T
        
        # Adaptive R estimate
        self.R = b * self.R + (1.0 - b) * np.outer(innovation, innovation)
        # Ensure R remains well-conditioned
        self.R = 0.5 * (self.R + self.R.T) + 1e-4 * np.eye(self.m)
        
        return self.x, innovation

def simulate_tracking(T=1200, seed=42):
    np.random.seed(seed)
    
    t = np.linspace(0, 12, T)
    # Ground truth capacity trajectory with smooth variation and sudden step
    C_true = 95.0 + 8.0 * np.sin(0.5 * t)
    C_true[400:800] -= 10.0
    
    # Ground truth queue length
    q_true = 8.0 + 2.5 * np.cos(0.7 * t)
    
    # Dual telemetry measurements
    y_thru = (C_true / (1.0 + 0.01 * np.maximum(0.0, q_true))) + 0.3 * np.random.randn(T)
    y_q = q_true + 0.2 * np.random.randn(T)
    Y_meas = np.column_stack([y_thru, y_q])
    
    aukf = AdaptiveUKFBottleneckTracker()
    
    C_est = []
    innovations = []
    
    for k in range(T):
        est, innov = aukf.step(Y_meas[k])
        C_est.append(est[0])
        innovations.append(innov[0])
        
    C_est = np.array(C_est)
    innovations = np.array(innovations)
    
    # Ignore initial burn-in (first 100 steps)
    rel_error = np.mean(np.abs(C_est[100:] - C_true[100:]) / C_true[100:]) * 100.0
    
    # Innovation lag-1 autocorrelation
    innov_centered = innovations[100:] - np.mean(innovations[100:])
    autocorr = float(np.corrcoef(innov_centered[:-1], innov_centered[1:])[0, 1])
    orthogonality_passed = bool(abs(autocorr) < 0.25)
    
    passed = bool(rel_error < 2.0) and orthogonality_passed
    
    return {
        "mean_relative_error_percent": float(rel_error),
        "innovation_lag1_autocorr": autocorr,
        "orthogonality_passed": orthogonality_passed,
        "target_relative_error": 2.0,
        "passed": passed
    }

def main():
    print("=== Task 0468: Adaptive UKF Bottleneck Capacity Tracking ===")
    
    runs = 15
    rel_errors = []
    ortho_flags = []
    
    for r in range(runs):
        res = simulate_tracking(T=1200, seed=100 + r)
        rel_errors.append(res["mean_relative_error_percent"])
        ortho_flags.append(res["orthogonality_passed"])
        
    mean_err = float(np.mean(rel_errors))
    max_err = float(np.max(rel_errors))
    ortho_rate = float(np.mean(ortho_flags)) * 100.0
    
    overall_passed = (max_err < 2.0) and (ortho_rate == 100.0)
    
    summary = {
        "runs": runs,
        "mean_relative_error_percent": mean_err,
        "max_relative_error_percent": max_err,
        "innovation_orthogonality_rate": ortho_rate,
        "target_threshold_percent": 2.0,
        "passed": bool(overall_passed)
    }
    
    print(json.dumps(summary, indent=2))
    if not overall_passed:
        sys.exit(1)

if __name__ == "__main__":
    main()

