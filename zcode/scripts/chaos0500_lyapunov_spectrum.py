#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0500: 李雅普诺夫指数谱确定性混沌分岔抑制 (Lyapunov Exponent Spectrum Chaos Bifurcation Suppression)

验证目标:
1. 稳定化控制后最大李雅普诺夫指数 MLE < 0.0 (彻底消除混沌边缘发散)
2. 相空间相体积耗散收缩率 100.0% (Tr(J) < 0 恒成立)
3. 混沌抑制成功率 100.0% (25/25 独立随机初始扰动全部收敛至稳定平衡点)
"""

import sys
import numpy as np


def run_lyapunov_chaos_analysis():
    np.random.seed(500)
    
    # 物理系统参数
    mu = 10.0            # 瓶颈服务率 pkts/ms
    D0 = 5.0             # 传播时延 5 ms
    B_thresh = 15.0      # 浅缓冲区非线性门限
    k_c = 0.8            # S型拥塞跃迁陡度
    T_f = 2.0            # 时延滤波时间常数
    alpha_inc = 2.0      # 加法增加增益
    beta_dec = 0.25      # 乘法减小增益
    
    # 目标稳态平衡点: r* = mu = 10.0, q* = 16.732868
    q_star = 16.732868
    Kp = 0.5             # 比例排队抑制增益
    Kd = 2.0             # 微分动量抑制增益
    
    # S 型非线性拥塞标记函数
    def sigmoid_phi(q_val):
        z = np.clip(k_c * (q_val - B_thresh), -50.0, 50.0)
        return 1.0 / (1.0 + np.exp(-z))
        
    def d_sigmoid_phi(q_val):
        s = sigmoid_phi(q_val)
        return k_c * s * (1.0 - s)
        
    def dynamics(x_state):
        r, q, tau = x_state
        tau_safe = max(0.5, tau)
        u_stab = -Kp * (q - q_star) - Kd * (r - mu)
        dr = (alpha_inc - beta_dec * r * sigmoid_phi(q) + u_stab) / tau_safe
        dq = r - mu
        dtau = (D0 + q / mu - tau_safe) / T_f
        return np.array([dr, dq, dtau])
        
    def jacobian(x_state):
        r, q, tau = x_state
        tau_safe = max(0.5, tau)
        phi = sigmoid_phi(q)
        dphi = d_sigmoid_phi(q)
        u_stab = -Kp * (q - q_star) - Kd * (r - mu)
        
        J = np.zeros((3, 3))
        # d(dr)/dr
        J[0, 0] = (-beta_dec * phi - Kd) / tau_safe
        # d(dr)/dq
        J[0, 1] = (-beta_dec * r * dphi - Kp) / tau_safe
        # d(dr)/dtau
        J[0, 2] = -(alpha_inc - beta_dec * r * phi + u_stab) / (tau_safe**2)
        
        # d(dq)
        J[1, 0] = 1.0
        J[1, 1] = 0.0
        J[1, 2] = 0.0
        
        # d(dtau)
        J[2, 0] = 0.0
        J[2, 1] = (1.0 / mu) / T_f
        J[2, 2] = -1.0 / T_f
        return J

    # ---------------- 1. Gram-Schmidt 正交化计算李雅普诺夫指数谱 ----------------
    dt = 0.005
    T_sim = 20.0
    N_steps = int(T_sim / dt)
    qr_interval = 10     # 每 10 步执行一次 QR 重正交化
    
    x = np.array([12.0, 18.0, 6.0])
    Q_orth = np.eye(3)
    lyap_sums = np.zeros(3)
    qr_count = 0
    
    trace_negative_count = 0
    total_trace_count = 0
    
    for step in range(N_steps):
        dx = dynamics(x)
        x += dt * dx
        
        J = jacobian(x)
        tr = np.trace(J)
        total_trace_count += 1
        if tr < 0.0:
            trace_negative_count += 1
            
        Q_orth += dt * (J @ Q_orth)
        
        if (step + 1) % qr_interval == 0:
            Q_orth, R = np.linalg.qr(Q_orth)
            diag_r = np.abs(np.diag(R))
            lyap_sums += np.log(np.maximum(1e-12, diag_r))
            qr_count += 1
            
    lyap_spectrum = lyap_sums / (qr_count * qr_interval * dt)
    max_lyapunov_exponent = float(lyap_spectrum[0])
    volume_contraction_rate = (trace_negative_count / total_trace_count) * 100.0
    
    # ---------------- 2. 独立扰动混沌分岔抑制率检验 ----------------
    n_scenarios = 25
    chaos_suppressed_count = 0
    
    for sc in range(n_scenarios):
        x_rand = np.array([
            10.0 + np.random.uniform(-4.0, 4.0),
            15.0 + np.random.uniform(-4.0, 4.0),
            5.0 + np.random.uniform(-1.0, 1.0)
        ])
        
        for _ in range(5000):
            d_x = dynamics(x_rand)
            x_rand += 0.01 * d_x
            
        # 稳态判断: 速率与排队均严格收敛至目标平衡点
        if abs(x_rand[0] - mu) < 0.1 and abs(x_rand[1] - q_star) < 0.2:
            chaos_suppressed_count += 1
            
    suppression_rate = (chaos_suppressed_count / n_scenarios) * 100.0
    
    print(f"=== Task 0500: Lyapunov Exponent Spectrum Chaos Suppression ===")
    print(f"Full Lyapunov Spectrum: {lyap_spectrum}")
    print(f"Maximal Lyapunov Exponent (MLE): {max_lyapunov_exponent:.6f} (Target: < 0.0)")
    print(f"Phase Volume Dissipative Contraction Rate: {volume_contraction_rate:.2f}% (Target: 100.0%)")
    print(f"Chaos Suppression Success Rate: {suppression_rate:.2f}% (Target: 100.0%)")
    
    assert max_lyapunov_exponent < 0.0, f"System has positive Lyapunov exponent (chaotic): {max_lyapunov_exponent}"
    assert volume_contraction_rate >= 100.0, f"Phase volume not strictly dissipative: {volume_contraction_rate}%"
    assert suppression_rate >= 100.0, f"Chaos suppression failed: {suppression_rate}%"
    print(">>> All Task 0500 criteria PASSED successfully! <<<")


if __name__ == "__main__":
    run_lyapunov_chaos_analysis()
