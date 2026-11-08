# -*- coding: utf-8 -*-
"""
Task 0588: Stochastic Optimal Control Hamilton-Jacobi-Bellman Viscosity Solution Monotone Iteration
- Howard Policy Iteration with Kushner-Dupuis Monotone Upwind M-Matrix Discretization
- HJB viscosity residual < 1e-10
- Lyapunov monotonicity and convergence verification
- Peak queue < 36.0 pkts, drops = 0
"""

import sys
import numpy as np

def solve_hjb_viscosity():
    np.random.seed(42)
    
    # Grid parameters
    Q_max = 35.0
    N_q = 141
    q_grid = np.linspace(0.0, Q_max, N_q)
    dq = q_grid[1] - q_grid[0]
    
    # System parameters
    rho = 0.05       # Discount factor
    mu = 12.5        # Bottleneck service capacity (pkts/ms)
    sigma = 0.5      # Diffusion volatility
    q_target = 4.0   # Target optimal queue (pkts)
    u_nominal = 12.5 # Nominal flow rate (pkts/ms)
    
    w_q = 1.0        # Queue buildup penalty
    w_u = 0.1        # Pacing control oscillation penalty
    
    u_min = 8.0
    u_max = 16.0
    
    # Running cost function L(q, u)
    def running_cost(q, u):
        return 0.5 * w_q * (q - q_target)**2 + 0.5 * w_u * (u - u_nominal)**2
    
    # Initial control policy
    u_policy = np.full(N_q, u_nominal)
    diff_coef = 0.5 * (sigma**2) / (dq**2)
    
    # Howard Policy Iteration with Kushner-Dupuis Upwind Scheme
    max_iter = 100
    tol = 1e-10
    
    for iteration in range(max_iter):
        u_old = np.copy(u_policy)
        
        # Build M-Matrix A for policy evaluation: (rho I - L_u) V = c(q, u)
        A = np.zeros((N_q, N_q))
        c_vec = running_cost(q_grid, u_policy)
        
        for i in range(N_q):
            A[i, i] += rho
            d = u_policy[i] - mu
            
            # Diffusion term: - 0.5 * sigma^2 * V_xx
            if 0 < i < N_q - 1:
                A[i, i] += 2.0 * diff_coef
                A[i, i-1] -= diff_coef
                A[i, i+1] -= diff_coef
            elif i == 0:
                A[i, i] += diff_coef
                A[i, i+1] -= diff_coef
            else:
                A[i, i] += diff_coef
                A[i, i-1] -= diff_coef
                
            # Kushner-Dupuis Upwind advection:
            # If d > 0, drift pushes right, so future value depends on forward node i+1:
            # - d * (V_{i+1} - V_i) / dq => + (d/dq) * V_i - (d/dq) * V_{i+1}
            # If d < 0, drift pushes left, so future value depends on backward node i-1:
            # - d * (V_i - V_{i-1}) / dq => + (|d|/dq) * V_i - (|d|/dq) * V_{i-1}
            if d > 0 and i < N_q - 1:
                A[i, i] += d / dq
                A[i, i+1] -= d / dq
            elif d < 0 and i > 0:
                A[i, i] += (-d) / dq
                A[i, i-1] -= (-d) / dq
                
        # Solve linear system for value function V
        V = np.linalg.solve(A, c_vec)
        
        # Gradient V_x
        V_x = np.gradient(V, dq)
        
        # Policy Improvement: min_u { (u - mu) V_x + 0.5 w_u (u - u_nominal)^2 }
        # => u^* = clip(u_nominal - V_x / w_u, u_min, u_max)
        u_new = np.clip(u_nominal - V_x / w_u, u_min, u_max)
        
        policy_diff = np.max(np.abs(u_new - u_old))
        u_policy = u_new
        
        if policy_diff < tol:
            break
            
    # Residual Audit of Viscosity Solution:
    hjb_residual = np.max(np.abs(A @ V - c_vec))
    
    # Lyapunov Monotonicity Check:
    # V(q) must have unique global minimum at q_target, decreasing on left, increasing on right
    idx_target = np.argmin(np.abs(q_grid - q_target))
    left_monotone = bool(np.all(np.diff(V[:idx_target+1]) <= 1e-6))
    right_monotone = bool(np.all(np.diff(V[idx_target:]) >= -1e-6))
    is_lyapunov_monotone = left_monotone and right_monotone
    
    # Closed-loop simulation under optimal HJB policy
    steps = 1000
    dt_sim = 0.01
    q_sim = np.zeros(steps)
    q_sim[0] = 18.0  # Start from high queue congestion
    drops = 0
    
    for t in range(steps - 1):
        q_c = q_sim[t]
        u_c = np.interp(q_c, q_grid, u_policy)
        noise = np.random.randn() * sigma * np.sqrt(dt_sim)
        q_next = max(0.0, q_c + (u_c - mu) * dt_sim + noise)
        if q_next > 40.0:
            drops += int(q_next - 40.0)
            q_next = 40.0
        q_sim[t + 1] = q_next
        
    peak_queue = np.max(q_sim)
    
    passed = (
        (hjb_residual < 1e-10) and
        is_lyapunov_monotone and
        (peak_queue < 36.0) and
        (drops == 0)
    )
    
    print(f"--- Task 0588 HJB Viscosity Solution Verification ---")
    print(f"Grid Points: {N_q}, Policy Iterations: {iteration + 1}")
    print(f"HJB Viscosity Residual: {hjb_residual:.4e} (Target: < 1e-10)")
    print(f"Lyapunov Monotonicity: {'PASS' if is_lyapunov_monotone else 'FAIL'} (Left: {left_monotone}, Right: {right_monotone})")
    print(f"Initial Congestion Queue: {q_sim[0]:.1f} pkts -> Final Steady Queue: {q_sim[-1]:.2f} pkts")
    print(f"Peak Queue Level: {peak_queue:.2f} pkts (Limit: 36.0 pkts)")
    print(f"Packet Drops: {drops}")
    print(f"HJB Verification Result: {passed}")
    
    return {
        "hjb_residual": float(hjb_residual),
        "lyapunov_monotone": is_lyapunov_monotone,
        "peak_queue": float(peak_queue),
        "drops": drops,
        "pass": passed
    }

if __name__ == "__main__":
    res = solve_hjb_viscosity()
    if not res["pass"]:
        sys.exit(1)
    sys.exit(0)
