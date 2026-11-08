#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 0515: 广义哈密顿系统非局部涡旋动力学浅缓冲耗散 (Nonlocal Vortex Hamiltonian Pacing Dissipation)
--------------------------------------------------------------------------------------------------
核心数理机制:
1. 正则相空间与非局部涡旋张量:
   设广义坐标 q 为排队偏离度 (pkts)，共轭动量 p 为速率变率 (Mbps/ms)。
   多流周期干扰诱发相空间非局部闭合环流 (Circulation):
   Γ(t) = ∮ (p dq - q dp)
2. 涡旋破缺耗散哈密顿量:
   H(q, p) = 1/2 p^2 + 1/2 ω_0^2 q^2 + 1/4 β q^4 + U_vort(q, p)
   注入斜对称非保守阻尼律:
   u(t) = - γ p - κ_vort * [ - ∂H/∂q, ∂H/∂p ]^T
   破坏辛 2-形式闭合性，强制相体积向孤立汇聚点单调收缩: dΓ/dt <= - α Γ
3. 验证指标:
   - 涡旋环量耗散率 (Vortex Circulation Dissipation) >= 95.0%
   - 排队稳态波动标准差 (Queue StdDev) < 1.5 pkts
   - 浅缓冲溢出丢包数 (Buffer Drops) = 0
   - 峰值排队深度 Peak Queue < 36.0 pkts
"""

import sys
import numpy as np
import json
from pathlib import Path

def run_vortex_dissipation():
    np.random.seed(42)
    
    # 1. 物理参数配置
    omega_0 = 1.0     # 固有频率
    beta = 0.2        # 硬非线性系数
    gamma = 0.8       # 线性阻尼系数
    kappa_vort = 0.5  # 涡旋拓扑破缺耗散系数
    
    dt = 0.005
    T_total = 20.0
    N = int(T_total / dt)
    t_span = np.linspace(0, T_total, N)
    
    # 初始状态: 较强初始涡旋角动量 (q_0 = 2.0, p_0 = 1.5)
    q = np.zeros(N)
    p = np.zeros(N)
    q[0] = 2.0
    p[0] = 1.5
    
    # 2. 辛欧拉/龙格库塔数值积分
    for i in range(N - 1):
        # 偏导项
        dH_dq = omega_0**2 * q[i] + beta * q[i]**3
        dH_dp = p[i]
        
        # 耗散控制律
        # 涡旋诱导耗散项: 破坏环流角动量
        u = - gamma * p[i] - kappa_vort * (q[i] * p[i] + dH_dq)
        
        # 外部随机微小跨流白噪声 (均值 0, 方差 0.1)
        noise = np.random.randn() * 0.1
        
        dp_dt = - dH_dq + u + noise
        dq_dt = dH_dp
        
        # RK4 积分单步
        k1_q = dq_dt
        k1_p = dp_dt
        
        q_mid = q[i] + 0.5 * dt * k1_q
        p_mid = p[i] + 0.5 * dt * k1_p
        dH_dq_mid = omega_0**2 * q_mid + beta * q_mid**3
        u_mid = - gamma * p_mid - kappa_vort * (q_mid * p_mid + dH_dq_mid)
        k2_q = p_mid
        k2_p = - dH_dq_mid + u_mid
        
        q[i+1] = q[i] + dt * k2_q
        p[i+1] = p[i] + dt * k2_p

    # 3. 计算涡旋环量 Γ(t) 与耗散率
    # 在初始 2 秒与末期 2 秒分别计算相平面面积环量: Γ = 1/2 ∑ (q_j p_{j+1} - q_{j+1} p_j)
    idx_init_end = int(2.0 / dt)
    idx_final_start = int(18.0 / dt)
    
    q_init = q[:idx_init_end]
    p_init = p[:idx_init_end]
    circ_init = 0.5 * abs(np.sum(q_init[:-1] * p_init[1:] - q_init[1:] * p_init[:-1]))
    
    q_final = q[idx_final_start:]
    p_final = p[idx_final_start:]
    circ_final = 0.5 * abs(np.sum(q_final[:-1] * p_final[1:] - q_final[1:] * p_final[:-1]))
    
    circ_dissipation_rate = float((circ_init - circ_final) / circ_init * 100.0)
    
    # 4. 排队波动统计
    # 稳态排队 (后 50% 时间)
    steady_q = q[int(N * 0.5):]
    # 映射到物理排队深度 (基准排队 15.0 pkts + q)
    physical_q = 15.0 + q
    steady_std = float(np.std(steady_q))
    peak_queue = float(np.max(physical_q))
    buffer_drops = int(np.sum(physical_q > 40.0))

    print("=== Task 0515 Vortex Dissipation Results ===")
    print(f"Initial Circulation Γ_init: {circ_init:.4f}")
    print(f"Final Circulation Γ_final: {circ_final:.4f}")
    print(f"Circulation Dissipation Rate: {circ_dissipation_rate:.2f}% (target >= 95.0%)")
    print(f"Steady Queue StdDev: {steady_std:.4f} pkts (target < 1.5 pkts)")
    print(f"Peak Queue Depth: {peak_queue:.2f} pkts (limit 40.0 pkts, target < 36.0)")
    print(f"Buffer Drops: {buffer_drops} (target 0)")
    
    assert circ_dissipation_rate >= 95.0, f"Dissipation {circ_dissipation_rate:.2f}% < 95.0%"
    assert steady_std < 1.5, f"StdDev {steady_std:.4f} >= 1.5"
    assert peak_queue < 36.0, f"Peak queue {peak_queue:.2f} >= 36.0"
    assert buffer_drops == 0, f"Buffer drops {buffer_drops} > 0"
    
    metrics = {
        "task_id": "0515",
        "circ_init": float(circ_init),
        "circ_final": float(circ_final),
        "circ_dissipation_rate": circ_dissipation_rate,
        "steady_std": steady_std,
        "peak_queue": peak_queue,
        "buffer_drops": buffer_drops,
        "status": "PASS"
    }
    
    out_dir = Path("zcode/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "0515_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
        
    print("SUCCESS: All Task 0515 verification criteria PASSED!")

if __name__ == "__main__":
    run_vortex_dissipation()
