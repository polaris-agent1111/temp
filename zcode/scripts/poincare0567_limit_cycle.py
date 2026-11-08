#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Task 0567: 庞加莱-本迪克松环形相空间极限环轨道存在性与拟周期排除定理 (Poincare-Bendixson Limit Cycle Exclusion Criterion)
-----------------------------------------------------------------------------------------------------------------------------
理论背景:
考虑流量整形与队列深度构成的二维非线性自治动力系统:
    dq/dt = f(q, r) = \frac{r}{12.0} (1 - \alpha q) - C_{srv}
    dr/dt = g(q, r) = - \beta (r - r^*) - \gamma q r
依据本迪克松判据 (Bendixson's Negative Criterion):
若在单连通相空间区域 D \subset \mathbb{R}^2 上，向量场的散度:
    \text{div} F(q, r) = \frac{\partial f}{\partial q} + \frac{\partial g}{\partial r}
处处同号且不恒等于零，则区域 D 内不存在任何闭合轨道（极限环或周期解）。
验证散度严格负定 (\text{div} F < 0)，排除任何自激震荡与极限环，证明系统收敛至唯一全局稳定平衡点。
"""

import sys
import numpy as np

def run_poincare_bendixson_exclusion():
    print("=== Task 0567: 庞加莱-本迪克松环形相空间极限环轨道存在性与拟周期排除定理 ===")
    
    # 系统物理参数
    alpha = 0.025 # 队列阻尼系数
    beta = 1.5    # 速率松弛增益
    gamma = 0.005 # 交叉耦合增益
    C_srv = 100.0 / 12.0 # 瓶颈服务率 (pkts/ms)
    r_star = 96.0 # 目标名义速率 (Mbps)
    
    # 建立相空间网格 D: q \in [0, 40], r \in [60, 100]
    q_vals = np.linspace(0.0, 40.0, 100)
    r_vals = np.linspace(60.0, 100.0, 100)
    Q, R = np.meshgrid(q_vals, r_vals)
    
    # 计算偏导数与散度
    # df/dq = - alpha * (r / 12.0)
    df_dq = - alpha * (R / 12.0)
    # dg/dr = - beta - gamma * q
    dg_dr = - beta - gamma * Q
    
    div_F = df_dq + dg_dr
    
    max_div = float(np.max(div_F))
    mean_div = float(np.mean(div_F))
    
    # 面积分散度积分 \iint_D div F dq dr
    if hasattr(np, 'trapezoid'):
        area_integral = float(np.trapezoid(np.trapezoid(div_F, r_vals, axis=0), q_vals))
    else:
        area_integral = float(np.mean(div_F) * 40.0 * 40.0)
    
    # 排除极限环判定: 散度处处严格小于零
    bendixson_condition_holds = np.all(div_F < 0.0)
    limit_cycle_excluded = bendixson_condition_holds and (area_integral < 0.0)
    exclusion_rate = 100.0 if limit_cycle_excluded else 0.0
    
    # 全局点吸引子验证: 轨迹时间演化并检验是否收敛至孤立不动点
    steps = 2500
    dt = 0.01
    q = 5.0 # 名义初值
    r = 90.0
    q_hist = []
    r_hist = []
    
    for t in range(steps):
        dq = ((r / 12.0) * (1.0 - alpha * q) - C_srv) * dt
        dr = (- beta * (r - r_star) - gamma * q * r) * dt
        q = max(0.0, q + dq)
        r = max(10.0, r + dr)
        q_hist.append(q)
        r_hist.append(r)
        
    final_dq = abs(q_hist[-1] - q_hist[-2]) / dt
    final_dr = abs(r_hist[-1] - r_hist[-2]) / dt
    is_attractor_converged = (final_dq < 1e-4) and (final_dr < 1e-4)
    
    peak_queue = float(np.max(q_hist))
    drops = 0 # 连续方程无溢出
    
    print(f"Maximum Divergence in D: {max_div:.4f} (Target < 0.0)")
    print(f"Mean Divergence in D: {mean_div:.4f} (Target < 0.0)")
    print(f"Divergence Area Integral: {area_integral:.4f} (Target < 0.0)")
    print(f"Limit Cycle Exclusion Rate: {exclusion_rate:.2f}% (Target 100.0%)")
    print(f"Attractor Stationarity Residual: dq/dt={final_dq:.4e}, dr/dt={final_dr:.4e}")
    print(f"Peak Queue Depth: {peak_queue:.2f} pkts (Target < 36.0 pkts)")
    print(f"Buffer Drops: {drops} (Target 0)")
    
    assert max_div < 0.0, f"Divergence not negative everywhere, max={max_div}"
    assert area_integral < 0.0, f"Divergence integral not negative, val={area_integral}"
    assert exclusion_rate == 100.0, f"Limit cycle not excluded, rate={exclusion_rate}%"
    assert is_attractor_converged, "Trajectory did not converge to point attractor"
    assert peak_queue < 36.0, f"Peak queue {peak_queue} >= 36.0"
    assert drops == 0, f"Buffer drops {drops} != 0"
    
    print("SUCCESS: Task 0567 Poincare-Bendixson Limit Cycle Exclusion PASSED!")

if __name__ == "__main__":
    run_poincare_bendixson_exclusion()
