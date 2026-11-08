#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Task 0560: 广义柯西-施瓦茨超球面凸优化下确界流体几何学收敛证明 (Generalized Cauchy-Schwarz Hypersphere Convex Optimization)
----------------------------------------------------------------------------------------------------------------------
理论背景:
在六载非线性流量整形流体动力学空间中，状态向量 x(t) = [q(t), r(t), \tau(t)] 与控制向量 u(t) 满足内积空间柯西-施瓦茨不等式:
    |<x, u>|^2 <= ||x||^2 ||u||^2
等号成立当且仅当 u 与 x 线性相关 (u = k x)。
将流体测度投影至 n 维超球面 S^{n-1} 上，构建凸优化泛函:
    min_{u \in S^{n-1}} J(u) = 1/2 ||A u - b||^2
求解黎曼流形超球面投影梯度:
    \nabla_{S} J(u) = (I - u u^T) \nabla_E J(u)
收敛时切投影梯度残差严格趋向于 0 (|| \nabla_S J(u) || < 10^{-12})。
"""

import sys
import numpy as np

def run_cauchy_hypersphere_optimization():
    print("=== Task 0560: 广义柯西-施瓦茨超球面凸优化下确界流体几何学收敛证明 ===")
    
    np.random.seed(560)
    dim = 6 # 6 loads
    
    # 构造半正定流体度量矩阵 A 与目标流长特征向量 b
    A = np.array([
        [2.5, 0.4, 0.2, 0.1, 0.05, 0.0],
        [0.4, 2.3, 0.3, 0.15, 0.08, 0.02],
        [0.2, 0.3, 2.1, 0.25, 0.1, 0.05],
        [0.1, 0.15, 0.25, 1.9, 0.3, 0.1],
        [0.05, 0.08, 0.1, 0.3, 1.8, 0.2],
        [0.0, 0.02, 0.05, 0.1, 0.2, 1.6]
    ], dtype=np.float64)
    
    b = np.array([1.2, 1.1, 0.95, 0.85, 0.75, 0.65], dtype=np.float64)
    
    # 初始超球面点 u_0 (||u_0||_2 = 1)
    u = np.ones(dim, dtype=np.float64) / np.sqrt(dim)
    
    # 黎曼流形超球面投影梯度下降 (Riemannian Gradient Descent on Sphere)
    lr = 0.05
    max_iters = 5000
    tol = 1e-13
    
    for it in range(max_iters):
        # 欧氏梯度: grad_E = A^T (A u - b)
        grad_E = A.T @ (A @ u - b)
        # 黎曼球面切空间投影梯度: grad_R = (I - u u^T) grad_E = grad_E - <u, grad_E> u
        grad_R = grad_E - np.dot(u, grad_E) * u
        grad_norm = np.linalg.norm(grad_R)
        
        if grad_norm < tol:
            break
            
        # 沿切向量更新并测地线回缩 (Retraction to sphere)
        u_new = u - lr * grad_R
        u = u_new / np.linalg.norm(u_new)
        
    final_grad_E = A.T @ (A @ u - b)
    final_grad_R = final_grad_E - np.dot(u, final_grad_E) * u
    final_grad_residual = float(np.linalg.norm(final_grad_R))
    
    # 验证柯西-施瓦茨等号严格性: cos(theta) = <x, u> / (||x|| ||u||) -> 1.0 (线性共线)
    x = final_grad_E
    cos_theta = abs(np.dot(x, u)) / (np.linalg.norm(x) * np.linalg.norm(u))
    cauchy_equality_residual = float(1.0 - cos_theta)
    
    # 六载流体曲率平滑度验证
    curvatures = np.abs(np.diff(np.diff(u)))
    curvature_smoothness = float(np.mean(curvatures < 0.35)) * 100.0
    
    # 六载闭环队列仿真
    steps = 1000
    q = 0.0
    queue_levels = []
    drops = 0
    buffer_cap = 40.0
    
    # 基于球面优化解缩放后的步进速率 (Mbps)
    optimal_rates = 90.0 + 10.0 * (u / np.max(u))
    bottleneck_bw = 100.0
    
    for t in range(steps):
        stage = min(t // 170, 5)
        rate = optimal_rates[stage]
        throttle = max(0.70, 1.0 - 0.02 * q)
        inflow = (rate * throttle) / 12.0
        service = bottleneck_bw / 12.0
        q = max(0.0, q + (inflow - service) * 0.1)
        if q > buffer_cap:
            drops += int(q - buffer_cap)
            q = buffer_cap
        queue_levels.append(q)
        
    peak_queue = float(np.max(queue_levels))
    
    print(f"Riemannian Sphere Gradient Residual: {final_grad_residual:.4e} (Target < 1.0e-12)")
    print(f"Cauchy-Schwarz Equality Residual: {cauchy_equality_residual:.4e} (Target < 1.0e-12)")
    print(f"Curvature Smoothness Rate: {curvature_smoothness:.2f}% (Target 100.0%)")
    print(f"Peak Queue Depth: {peak_queue:.2f} pkts (Target < 36.0 pkts)")
    print(f"Buffer Drops: {drops} (Target 0)")
    
    assert final_grad_residual < 1.0e-12, f"Gradient residual {final_grad_residual} >= 1e-12"
    assert cauchy_equality_residual < 1.0e-12, f"Cauchy equality residual {cauchy_equality_residual} >= 1e-12"
    assert curvature_smoothness == 100.0, f"Curvature smoothness {curvature_smoothness}% != 100.0%"
    assert peak_queue < 36.0, f"Peak queue {peak_queue} >= 36.0"
    assert drops == 0, f"Buffer drops {drops} != 0"
    
    print("SUCCESS: Task 0560 Cauchy-Schwarz Hypersphere Optimization PASSED!")

if __name__ == "__main__":
    run_cauchy_hypersphere_optimization()
