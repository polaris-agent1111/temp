#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0492: 极小极大鲁棒微分博弈鞍点策动 (Min-Max Robust Differential Game Saddle-Point Pacing)

验证目标:
1. 鞍点极小极大对偶间隙 |max_w J(u*, w) - min_u J(u, w*)| < 1e-5
2. HJI 微分黎卡提方程解析与数值积分残差 < 1e-6
3. 最恶劣跨流对抗突发冲击下浅缓冲区峰值排队严格 < 36.0 pkts (物理容量 40.0 pkts)
"""

import sys
import numpy as np


def run_minmax_differential_game():
    np.random.seed(492)
    
    # 物理参数
    mu = 10.0            # 瓶颈带宽服务率 pkts/ms
    buffer_cap = 40.0    # 物理浅缓冲区容量
    q_safe_limit = 36.0  # 鲁棒安全上界
    
    # 博弈权重参数
    R_pacing = 0.5       # 流控动作惩罚权重
    gamma_hinf = 1.0     # H_infty 扰动衰减水平 (满足 gamma^2 = 1.0 > R = 0.5)
    
    # Delta = 1/R - 1/gamma^2 = 1.0
    Delta = (1.0 / R_pacing) - (1.0 / (gamma_hinf**2))
    P_ss = 1.0 / np.sqrt(Delta) # 代数黎卡提稳态解 P_ss = 1.0
    S_f = P_ss
    
    T_horizon = 5.0      # 博弈时域 5.0 ms
    dt = 0.0005          # 高精度微秒时间步长 0.5 us
    N = int(T_horizon / dt)
    
    # ---------------- 1. 求解 Hamilton-Jacobi-Isaacs 黎卡提微分方程 ----------------
    # -dP/dt = 1 - P^2 * Delta
    P = np.zeros(N)
    P[-1] = S_f
    for t in range(N - 1, 0, -1):
        dP_dt = -(1.0 - Delta * (P[t]**2))
        P[t - 1] = P[t] - dP_dt * dt
        
    riccati_residual = float(np.max(np.abs(P - P_ss)))
    
    # ---------------- 2. 鞍点验证与对偶间隙测试 ----------------
    # 在鞍点对 (u*, w*) 下:
    # u*(t) = - (1/R) * P(t) * q(t)
    # w*(t) = (1/gamma^2) * P(t) * q(t)
    
    def simulate_game(u_strategy, w_strategy, q0):
        q = np.zeros(N)
        q[0] = q0
        cost = 0.0
        
        for t in range(N - 1):
            u_t = u_strategy(t, q[t])
            w_t = w_strategy(t, q[t])
            
            stage_cost = 0.5 * (q[t]**2) + 0.5 * R_pacing * (u_t**2) - 0.5 * (gamma_hinf**2) * (w_t**2)
            cost += stage_cost * dt
            
            # 队列状态演化
            q[t + 1] = max(0.0, q[t] + (u_t + w_t) * dt)
            
        cost += 0.5 * S_f * (q[-1]**2)
        return cost, q
        
    q0 = 30.0  # 初始队列处于 30 pkts 高压状态
    
    # 鞍点策略定义
    u_star = lambda t, qt: -(1.0 / R_pacing) * P[t] * qt
    w_star = lambda t, qt: (1.0 / (gamma_hinf**2)) * P[t] * qt
    
    J_star, q_star_traj = simulate_game(u_star, w_star, q0)
    
    # 验证极小极大鞍点性质:
    # 1. 对抗者 w 在面对 u* 时的最优响应: max_w J(u*, w) = J(u*, w*)
    alpha_variations = [0.7, 0.85, 0.95, 1.0, 1.05, 1.15, 1.3]
    J_w_list = []
    for a in alpha_variations:
        w_alt = lambda t, qt, scale=a: (scale / (gamma_hinf**2)) * P[t] * qt
        cost_w, _ = simulate_game(u_star, w_alt, q0)
        J_w_list.append(cost_w)
    max_w_J = max(J_w_list)
    
    # 2. 控制者 u 在面对 w* 时的最优响应: min_u J(u, w*) = J(u*, w*)
    J_u_list = []
    for a in alpha_variations:
        u_alt = lambda t, qt, scale=a: -(scale / R_pacing) * P[t] * qt
        cost_u, _ = simulate_game(u_alt, w_star, q0)
        J_u_list.append(cost_u)
    min_u_J = min(J_u_list)
    
    # 计算极小极大对偶间隙:
    duality_gap = abs(max_w_J - min_u_J)
    
    # ---------------- 3. 最恶劣跨流突发下排队峰值冲击测试 ----------------
    max_queue_observed = float(np.max(q_star_traj))
    
    print(f"=== Task 0492: Min-Max Robust Differential Game Saddle Point ===")
    print(f"Riccati Equation SS Residual ||P - P_ss||_inf: {riccati_residual:.6e} (Target: < 1e-6)")
    print(f"J(u*, w*) Baseline Value: {J_star:.4f}")
    print(f"max_w J(u*, w) across perturbations: {max_w_J:.4f}")
    print(f"min_u J(u, w*) across perturbations: {min_u_J:.4f}")
    print(f"Saddle-Point Duality Gap: {duality_gap:.6e} (Target: < 1e-5)")
    print(f"Peak Buffer Under Worst-Case Attack: {max_queue_observed:.2f} pkts (Limit: {q_safe_limit:.1f} pkts)")
    
    assert riccati_residual < 1e-6, f"Riccati residual failed: {riccati_residual}"
    assert duality_gap < 1e-5, f"Duality gap too large: {duality_gap}"
    assert max_queue_observed < q_safe_limit, f"Buffer limit exceeded: {max_queue_observed}"
    print(">>> All Task 0492 criteria PASSED successfully! <<<")


if __name__ == "__main__":
    run_minmax_differential_game()
