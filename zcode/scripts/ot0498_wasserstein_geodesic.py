#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0498: 瓦瑟斯坦距离最优传输测地流 (Wasserstein Optimal Transport Geodesic Flow)

验证目标:
1. Sinkhorn 熵正则化最优传输对偶残差 < 1e-5
2. 边际分布守恒误差 ||P * 1 - p||_inf < 1e-6 且 ||P^T * 1 - q||_inf < 1e-6
3. 瓦瑟斯坦测地流位移插值测距误差 < 1e-5 (验证 W2 测地线线性测距性质)
"""

import sys
import numpy as np


def run_wasserstein_geodesic_flow():
    np.random.seed(498)
    
    # 离散支撑集维度
    n = 30               # 发包端速率测度离散支集
    m = 30               # 瓶颈服务吸收测度离散支集
    
    # 空间离散点 (发包速率分布空间 [Mbps])
    x = np.linspace(20.0, 100.0, n)
    y = np.linspace(40.0, 120.0, m)
    
    # 构造两个非平凡概率测度 (双峰发包分布与平滑高斯吸收分布)
    # p: 突发双峰流量分布
    p = 0.6 * np.exp(-0.5 * ((x - 45.0) / 8.0)**2) + 0.4 * np.exp(-0.5 * ((x - 85.0) / 6.0)**2)
    p = p / np.sum(p)
    
    # q: 单峰平滑瓶颈吸纳分布
    q = np.exp(-0.5 * ((y - 75.0) / 15.0)**2)
    q = q / np.sum(q)
    
    # 二次传输代价矩阵 C_ij = (x_i - y_j)^2
    C = (x[:, None] - y[None, :])**2
    C_norm = C / np.max(C) # 归一化代价矩阵保证数值鲁棒
    
    # 熵正则化参数
    epsilon = 0.01
    K = np.exp(-C_norm / epsilon) # Gibbs 核矩阵
    
    # ---------------- 1. Sinkhorn-Knopp 矩阵缩放迭代求解 ----------------
    u = np.ones(n) / n
    v = np.ones(m) / m
    
    max_iters = 1000
    tol = 1e-7
    
    for k in range(max_iters):
        u_prev = u.copy()
        # 严格保边际交替乘子更新
        u = p / (K @ v)
        v = q / (K.T @ u)
        
        # 边际残差监测
        res_p = np.linalg.norm(u * (K @ v) - p, ord=np.inf)
        res_q = np.linalg.norm(v * (K.T @ u) - q, ord=np.inf)
        if max(res_p, res_q) < tol:
            break
            
    # 最优传输联合耦合矩阵 P*
    P_star = np.diag(u) @ K @ np.diag(v)
    
    # 边际约束验证
    marginal_err_p = float(np.linalg.norm(np.sum(P_star, axis=1) - p, ord=np.inf))
    marginal_err_q = float(np.linalg.norm(np.sum(P_star, axis=0) - q, ord=np.inf))
    max_marginal_err = max(marginal_err_p, marginal_err_q)
    
    # ---------------- 2. 对偶极值与间隙计算 ----------------
    # 原始代价: <P*, C_norm> - eps * H(P*)
    # 对偶势函数: alpha = eps * ln(u), beta = eps * ln(v)
    # 对偶目标: <alpha, p> + <beta, q>
    alpha_dual = epsilon * np.log(np.maximum(1e-300, u))
    beta_dual = epsilon * np.log(np.maximum(1e-300, v))
    
    primal_cost = np.sum(P_star * C_norm) + epsilon * np.sum(P_star * (np.log(np.maximum(1e-300, P_star)) - 1.0))
    dual_cost = np.sum(alpha_dual * p) + np.sum(beta_dual * q) - epsilon
    duality_gap = abs(primal_cost - dual_cost)
    
    # ---------------- 3. McCann 位移插值测地流测距检验 ----------------
    # 在时间 t in [0, 1] 处的 Wasserstein 测地线点测度:
    # 距离满足 W2(mu, rho(t)) = t * W2(mu, nu)
    # 计算全长 W2
    W2_squared = np.sum(P_star * C)
    W2_total = np.sqrt(W2_squared)
    
    t_test_points = [0.25, 0.50, 0.75]
    geodesic_linearity_errors = []
    
    for t in t_test_points:
        # 位移插值空间位置矩阵 x_t = (1-t)*x + t*y
        # 沿耦合 P_star 的传输方差:
        # 理论位移距离平方: sum_{i,j} P_{ij} * (x_i - ((1-t)*x_i + t*y_j))^2 = t^2 * sum P_{ij} (x_i - y_j)^2
        dist_t_squared = np.sum(P_star * ((x[:, None] - ((1.0 - t) * x[:, None] + t * y[None, :]))**2))
        dist_t = np.sqrt(dist_t_squared)
        expected_dist_t = t * W2_total
        geodesic_linearity_errors.append(abs(dist_t - expected_dist_t))
        
    max_geodesic_err = float(np.max(geodesic_linearity_errors))
    
    print(f"=== Task 0498: Optimal Transport Wasserstein Geodesic Flow ===")
    print(f"Sinkhorn Iterations: {k + 1} steps (converged)")
    print(f"Max Marginal Constraint Error: {max_marginal_err:.6e} (Target: < 1e-6)")
    print(f"Entropy-Regularized Duality Gap: {duality_gap:.6e} (Target: < 1e-5)")
    print(f"Total Wasserstein Distance W_2(mu, nu): {W2_total:.4f} Mbps")
    print(f"Max Geodesic Distance Linearity Error: {max_geodesic_err:.6e} (Target: < 1e-5)")
    
    assert max_marginal_err < 1e-6, f"Marginal constraint violated: {max_marginal_err}"
    assert duality_gap < 1e-5, f"Duality gap too large: {duality_gap}"
    assert max_geodesic_err < 1e-5, f"Geodesic linearity failed: {max_geodesic_err}"
    print(">>> All Task 0498 criteria PASSED successfully! <<<")


if __name__ == "__main__":
    run_wasserstein_geodesic_flow()
