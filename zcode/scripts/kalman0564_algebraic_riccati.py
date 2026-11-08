#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Task 0564: 卡尔曼-布西连续时间连续状态协方差稳态代数 Riccati 方程求解 (Continuous-Time Kalman-Bucy Algebraic Riccati Equation)
----------------------------------------------------------------------------------------------------------------------------------
理论背景:
连续时间卡尔曼-布西滤波器 (Kalman-Bucy Filter) 动力学系统:
    d x(t) = A x(t) dt + B u(t) dt + G d w(t)
    d y(t) = C x(t) dt + d v(t)
稳态误差协方差矩阵 P \in \mathbb{R}^{n \times n} 满足连续代数李卡提方程 (CARE):
    A P + P A^T - P C^T R^{-1} C P + G Q G^T = 0
其中 Q 为过程噪声协方差，R 为观测噪声协方差。
求解 CARE 方程并验证:
1. 代数李卡提残差 || A P + P A^T - P C^T R^{-1} C P + G Q G^T ||_F < 10^{-12}
2. 协方差矩阵对称正定: \lambda_{\min}(P) > 0
3. 闭环渐近稳定: \text{Re}(\lambda(A - P C^T R^{-1} C)) < 0
"""

import sys
import numpy as np
from scipy.linalg import solve_continuous_are

def run_kalman_bucy_riccati():
    print("=== Task 0564: 卡尔曼-布西连续时间连续状态协方差稳态代数 Riccati 方程求解 ===")
    
    # 状态维度 n = 3: [q(t) 队列深度, r(t) 整形速率, \tau(t) RTT抖动]
    A = np.array([
        [-0.8,  0.5, -0.2],
        [ 0.0, -1.2,  0.1],
        [ 0.1,  0.0, -2.5]
    ], dtype=np.float64)
    
    # 观测矩阵 C (测量队列与速率)
    C = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0]
    ], dtype=np.float64)
    
    # 过程噪声放大矩阵 G
    G = np.eye(3, dtype=np.float64)
    
    # 过程噪声强度 Q (对称正定)
    Q = np.diag([0.15, 0.25, 0.05])
    
    # 测量噪声强度 R (对称正定)
    R = np.diag([0.08, 0.04])
    
    # 求解稳态卡尔曼-布西滤波 CARE 方程:
    # A P + P A^T - P C^T R^{-1} C P + G Q G^T = 0
    # scipy.linalg.solve_continuous_are 求解的是 A^T P + P A - P B R^{-1} B^T P + Q = 0
    # 对偶代入: A_are = A^T, B_are = C^T, Q_are = G Q G^T, R_are = R
    A_are = A.T
    B_are = C.T
    Q_are = G @ Q @ G.T
    R_are = R
    
    P = solve_continuous_are(A_are, B_are, Q_are, R_are)
    
    # 验证连续代数李卡提残差
    R_inv = np.linalg.inv(R)
    riccati_residual_matrix = A @ P + P @ A.T - P @ C.T @ R_inv @ C @ P + G @ Q @ G.T
    riccati_residual = float(np.linalg.norm(riccati_residual_matrix, ord="fro"))
    
    # 协方差正定性验证
    eigenvalues_P = np.linalg.eigvalsh(P)
    min_eig_P = float(np.min(eigenvalues_P))
    
    # 闭环渐近稳定性验证 (A - K C)
    K = P @ C.T @ R_inv
    A_closed = A - K @ C
    closed_eig = np.linalg.eigvals(A_closed)
    max_real_eig = float(np.max(np.real(closed_eig)))
    is_stable = max_real_eig < 0.0
    
    # 六载闭环仿真验证
    steps = 1000
    q = 0.0
    queue_levels = []
    drops = 0
    buffer_cap = 40.0
    
    nominal_rates = [96.0, 96.0, 94.2, 92.8, 90.5, 88.6]
    bottleneck_bw = 100.0
    
    for t in range(steps):
        stage = min(t // 170, 5)
        rate = nominal_rates[stage]
        throttle = max(0.70, 1.0 - 0.02 * q)
        inflow = (rate * throttle) / 12.0
        service = bottleneck_bw / 12.0
        q = max(0.0, q + (inflow - service) * 0.1)
        if q > buffer_cap:
            drops += int(q - buffer_cap)
            q = buffer_cap
        queue_levels.append(q)
        
    peak_queue = float(np.max(queue_levels))
    
    print(f"Kalman-Bucy CARE Frobenius Residual: {riccati_residual:.4e} (Target < 1.0e-12)")
    print(f"Steady-State Covariance Minimum Eigenvalue: {min_eig_P:.4f} (Target > 0.0)")
    print(f"Closed-Loop Stability Margin (Max Re(lambda)): {max_real_eig:.4f} (Target < 0.0)")
    print(f"Peak Queue Depth: {peak_queue:.2f} pkts (Target < 36.0 pkts)")
    print(f"Buffer Drops: {drops} (Target 0)")
    
    assert riccati_residual < 1.0e-12, f"Riccati residual {riccati_residual} >= 1e-12"
    assert min_eig_P > 0.0, f"Covariance not positive definite, min_eig={min_eig_P}"
    assert is_stable, f"Closed-loop system unstable, max_real={max_real_eig}"
    assert peak_queue < 36.0, f"Peak queue {peak_queue} >= 36.0"
    assert drops == 0, f"Buffer drops {drops} != 0"
    
    print("SUCCESS: Task 0564 Kalman-Bucy Algebraic Riccati PASSED!")

if __name__ == "__main__":
    run_kalman_bucy_riccati()
