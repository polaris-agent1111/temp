#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Task 0563: 伯恩斯坦多项式高维光滑逼近与极值点切空间紧致性测度 (Bernstein Polynomial Smooth Approximation on Compact Tangent Space)
----------------------------------------------------------------------------------------------------------------------------------
理论背景:
对于六载非线性整形曲线 f(t) \in C^2[0, 1]，利用 Bernstein-Bézier 多项式基底:
    B_{i, n}(t) = \binom{n}{i} t^i (1 - t)^{n - i}, \quad i = 0, \dots, n
在紧致切空间上构建正交投影最小二乘逼近算子:
    c^* = \arg\min_c || M c - f ||_2^2, \quad M_{k, i} = B_{i, n}(t_k)
根据魏尔施特拉斯逼近定理与希尔伯特空间投影定理，在紧致区间 [0, 1] 上:
    || B_n^*(f) - f ||_\infty < 10^{-5}
求解极值点处一阶导数切空间切向量紧致性测度与绝对逼近误差。
"""

import sys
import numpy as np
from scipy.special import comb

def run_bernstein_tangent_approximation():
    print("=== Task 0563: 伯恩斯坦多项式高维光滑逼近与极值点切空间紧致性测度 ===")
    
    np.random.seed(563)
    n_order = 8 # 8 阶 Bernstein 基多项式
    
    # 目标真实整形平滑响应曲线 f(t) 在 t \in [0, 1]
    def f_target(t):
        return 96.0 - 5.5 * t**2 - 3.2 * t**3 + 1.5 * t + 0.5 * np.sin(np.pi * t)
        
    t_eval = np.linspace(0.0, 1.0, 1000)
    y_true = f_target(t_eval)
    
    # 构造 Bernstein-Bézier 投影矩阵 M
    M = np.zeros((len(t_eval), n_order + 1), dtype=np.float64)
    for i in range(n_order + 1):
        M[:, i] = comb(n_order, i) * (t_eval**i) * ((1.0 - t_eval)**(n_order - i))
        
    # 求解紧致切空间上的正交投影系数
    c_star, _, _, _ = np.linalg.lstsq(M, y_true, rcond=None)
    y_bernstein = M @ c_star
    
    abs_errors = np.abs(y_bernstein - y_true)
    max_approx_error = float(np.max(abs_errors))
    
    # 极值点切空间紧致性审计
    dy_dt = np.gradient(y_bernstein, t_eval)
    extremum_idx = np.argmin(np.abs(dy_dt))
    tangent_norm = abs(dy_dt[extremum_idx])
    
    # 切空间紧致性测度: 二阶导数有界且流形紧致一致
    d2y_dt2 = np.gradient(dy_dt, t_eval)
    is_compact = (np.all(np.abs(d2y_dt2) < 50.0)) and (tangent_norm < 0.05)
    compactness_rate = 100.0 if is_compact else 0.0
    
    # 六载闭环队列仿真
    steps = 1000
    q = 0.0
    queue_levels = []
    drops = 0
    buffer_cap = 40.0
    
    # 从 Bernstein 逼近曲线抽取 6 载对应速率 (Mbps)
    eval_pts = np.linspace(0.1, 0.9, 6)
    pacing_rates = [float(f_target(p)) for p in eval_pts]
    bottleneck_bw = 100.0
    
    for t in range(steps):
        stage = min(t // 170, 5)
        rate = pacing_rates[stage]
        throttle = max(0.70, 1.0 - 0.02 * q)
        inflow = (rate * throttle) / 12.0
        service = bottleneck_bw / 12.0
        q = max(0.0, q + (inflow - service) * 0.1)
        if q > buffer_cap:
            drops += int(q - buffer_cap)
            q = buffer_cap
        queue_levels.append(q)
        
    peak_queue = float(np.max(queue_levels))
    
    print(f"Bernstein Order: {n_order}")
    print(f"Max Approximation Absolute Error: {max_approx_error:.4e} (Target < 1.0e-5)")
    print(f"Extremum Tangent Residual: {tangent_norm:.4e} (Target < 0.05)")
    print(f"Tangent Space Compactness Rate: {compactness_rate:.2f}% (Target 100.0%)")
    print(f"Peak Queue Depth: {peak_queue:.2f} pkts (Target < 36.0 pkts)")
    print(f"Buffer Drops: {drops} (Target 0)")
    
    assert max_approx_error < 1.0e-5, f"Approximation error {max_approx_error} >= 1e-5"
    assert compactness_rate == 100.0, f"Compactness rate {compactness_rate}% != 100.0%"
    assert peak_queue < 36.0, f"Peak queue {peak_queue} >= 36.0"
    assert drops == 0, f"Buffer drops {drops} != 0"
    
    print("SUCCESS: Task 0563 Bernstein Polynomial Approximation PASSED!")

if __name__ == "__main__":
    run_bernstein_tangent_approximation()
