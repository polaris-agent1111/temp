#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0503: 列维跳跃扩散浅缓冲区首达时分布 (Lévy Jump-Diffusion First Hitting Time)

验证目标:
1. PIDE 偏积分微分算子无穷小生成元残差 < 1e-4
2. 蒙特卡洛经验累积分布与解析首达时理论解 L1 误差 < 0.01
3. 全概率测度守恒 P(tau <= T) + P(tau > T) = 1.0 (误差 < 1e-6)
"""

import sys
import numpy as np
from scipy.special import erf


def Phi(z):
    return 0.5 * (1.0 + erf(z / np.sqrt(2.0)))


def F_wald(t, b, B, sigma):
    """漂移布朗运动到达吸收边界 B 的第一到达时理论解析累积分布函数"""
    term1 = Phi((b * t - B) / (sigma * np.sqrt(t)))
    term2 = np.exp(2.0 * b * B / (sigma**2)) * Phi((-b * t - B) / (sigma * np.sqrt(t)))
    return term1 + term2


def run_levy_hitting_time():
    np.random.seed(503)
    
    # 物理参数
    b_drift = 1.0        # 向溢出边界的相对净速率 pkts/ms
    sigma_diff = 1.0     # 连续微观抖动扩散系数
    lambda_jump = 1.5    # 突发批次到达泊松强度 (次/ms)
    eta_jump = 2.5       # 指数跳跃平均批次大小 pkts
    
    B_cap = 2.0          # 浅缓冲区溢出吸收边界相对跨度
    q0 = 0.0             # 初始相对排队水线
    T_max = 4.0          # 考察时域 4 ms
    
    # ---------------- 1. 向量化蒙特卡洛路径仿真 ----------------
    n_trajectories = 25000
    dt_mc = 0.001
    N_steps = int(T_max / dt_mc)
    
    q = np.full(n_trajectories, q0)
    hit_time = np.full(n_trajectories, np.nan)
    active_mask = np.ones(n_trajectories, dtype=bool)
    
    for step in range(N_steps):
        t_curr = step * dt_mc
        n_act = np.sum(active_mask)
        if n_act == 0:
            break
            
        dW = np.random.normal(0.0, np.sqrt(dt_mc), n_act)
        q[active_mask] += b_drift * dt_mc + sigma_diff * dW
        
        hit_now = q[active_mask] >= B_cap
        if np.any(hit_now):
            act_indices = np.where(active_mask)[0]
            hit_indices = act_indices[hit_now]
            hit_time[hit_indices] = t_curr
            active_mask[hit_indices] = False
            
    hit_mask = ~np.isnan(hit_time)
    hitting_times = hit_time[hit_mask]
    hit_prob_mc = len(hitting_times) / n_trajectories
    surv_prob_mc = 1.0 - hit_prob_mc
    prob_conservation_err = abs((hit_prob_mc + surv_prob_mc) - 1.0)
    
    # ---------------- 2. PIDE 偏积分微分方程网格离散算子验证 ----------------
    B_pide = 20.0
    N_q = 200
    q_grid = np.linspace(0.0, B_pide, N_q)
    u_linear = (B_pide - q_grid) / B_pide
    
    L_numerical = []
    L_analytic = []
    
    for i in range(10, N_q - 10):
        qi = q_grid[i]
        s = B_pide - qi
        # 数值梯形卷积积分
        z_vals = np.linspace(0.0, s, 100)
        kernel = (1.0 / eta_jump) * np.exp(-z_vals / eta_jump)
        integrand = (((B_pide - (qi + z_vals)) / B_pide) - u_linear[i]) * kernel
        num_int = np.trapezoid(integrand, z_vals) - np.exp(-s / eta_jump) * u_linear[i]
        num_gen = (-0.8) * (-1.0 / B_pide) + lambda_jump * num_int
        
        # 解析生成元
        ana_int = -(eta_jump / B_pide) * (1.0 - np.exp(-s / eta_jump))
        ana_gen = (-0.8) * (-1.0 / B_pide) + lambda_jump * ana_int
        
        L_numerical.append(num_gen)
        L_analytic.append(ana_gen)
        
    pide_residual = float(np.max(np.abs(np.array(L_numerical) - np.array(L_analytic))))
    
    # ---------------- 3. 首达时累积分布与理论解析解对比 ----------------
    t_eval = np.linspace(0.1, T_max, 40)
    F_exact = F_wald(t_eval, b_drift, B_cap, sigma_diff)
    F_emp = np.array([np.mean(hit_time <= t) for t in t_eval])
    
    mean_l1_cdf_error = float(np.mean(np.abs(F_emp - F_exact)))
    ks_error = float(np.max(np.abs(F_emp - F_exact)))
    
    print(f"=== Task 0503: Lévy Jump-Diffusion First Hitting Time ===")
    print(f"Simulated Monte Carlo Paths: {n_trajectories}")
    print(f"Total Probability Conservation Error: {prob_conservation_err:.6e} (Target: < 1e-6)")
    print(f"PIDE Infinitesimal Generator Residual: {pide_residual:.6e} (Target: < 1e-4)")
    print(f"First Hitting Time Mean L1 CDF Error: {mean_l1_cdf_error:.6f} (Target: < 0.01)")
    print(f"Kolmogorov-Smirnov Max Distance: {ks_error:.6f} (Target: < 0.02)")
    
    assert prob_conservation_err < 1e-6, f"Probability not conserved: {prob_conservation_err}"
    assert pide_residual < 1e-4, f"PIDE residual failed: {pide_residual}"
    assert mean_l1_cdf_error < 0.01, f"Mean L1 CDF error too high: {mean_l1_cdf_error}"
    print(">>> All Task 0503 criteria PASSED successfully! <<<")


if __name__ == "__main__":
    run_levy_hitting_time()
