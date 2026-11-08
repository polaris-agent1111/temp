#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 0516: 奇异摄动边界层匹配渐近展开速率调制 (Singularly Perturbed Boundary Layer Matched Asymptotic Pacing Modulation)
-------------------------------------------------------------------------------------------------------------------
核心数理机制:
1. 建立双时间尺度奇异摄动方程:
   ε d^2 y / dt^2 + a_0 dy/dt + b_0 y = u_0
   小参数 ε = 0.002 << 1 刻画微秒级快速脉冲层与毫秒级宏观流速动力学的解耦。
2. 匹配渐近展开法 (Matched Asymptotic Expansions, MAE):
   - 外层解 (Outer Solution): y_out(t) = y_0(t) + ε y_1(t) + ε^2 y_2(t) (满足宏观慢变动力学)
   - 内层解 (Inner Boundary Layer): 引入拉伸时间尺度 τ = t / ε
     d^2 Y_in / dτ^2 + a_0 dY_in / dτ = 0
   - 普朗特匹配原理 (Prandtl Matching Condition):
     lim_{t -> 0} y_out(t) = lim_{τ -> ∞} Y_in(τ)
   - 复合一致渐近展开通式:
     y_comp(t) = y_steady * [ 1 + (λ_slow / (λ_fast - λ_slow)) exp(λ_fast * t)
                              - (λ_fast / (λ_fast - λ_slow)) exp(λ_slow * t) ]
3. 验证指标:
   - 匹配渐近展开残差 sup |y_exact(t) - y_comp(t)| < 1e-5
   - 内层边界层过渡时间 (Transition Duration) < 10 ms
   - 浅缓冲溢出丢包数 (Buffer Drops) = 0
   - 峰值排队深度 Peak Queue < 36.0 pkts
"""

import sys
import numpy as np
import json
from pathlib import Path

def run_boundary_layer_expansion():
    np.random.seed(42)
    
    # 1. 奇异摄动系统参数配置
    eps = 0.002       # 摄动小参数 (微秒级快时间尺度)
    a_0 = 3.0         # 慢变阻尼系数
    b_0 = 1.0         # 慢变弹性系数
    u_0 = 2.0         # 阶跃稳态输入
    
    T_total = 1.0     # 1 秒宏观时间跨度
    N = 10000
    t_span = np.linspace(0, T_total, N)
    
    # 2. 真实解析解 (Exact Analytical Baseline Solution)
    # 准确特征根: ε λ^2 + a_0 λ + b_0 = 0
    disc = np.sqrt(a_0**2 - 4.0 * eps * b_0)
    r1 = (- a_0 + disc) / (2.0 * eps)
    r2 = (- a_0 - disc) / (2.0 * eps)
    
    y_steady = u_0 / b_0
    y_exact = y_steady * (1.0 + (r1 / (r2 - r1)) * np.exp(r2 * t_span) - (r2 / (r2 - r1)) * np.exp(r1 * t_span))
    
    # 3. 构造二阶匹配渐近展开复合一致解 (Composite Uniform Expansion)
    # 慢变外层渐近特征根展开:
    # λ_slow = - b_0/a_0 - ε b_0^2/a_0^3 - 2 ε^2 b_0^3/a_0^5
    lam_slow = - b_0 / a_0 - eps * (b_0**2) / (a_0**3) - 2.0 * (eps**2) * (b_0**3) / (a_0**5)
    # 快变内层边界层特征根展开:
    # λ_fast = - a_0/ε - λ_slow
    lam_fast = - a_0 / eps - lam_slow
    
    c_fast = lam_slow / (lam_fast - lam_slow)
    c_slow = - lam_fast / (lam_fast - lam_slow)
    
    y_comp = y_steady * (1.0 + c_fast * np.exp(lam_fast * t_span) + c_slow * np.exp(lam_slow * t_span))
    
    # 4. 计算全局匹配渐近残差
    asymptotic_residuals = np.abs(y_exact - y_comp)
    max_asymptotic_residual = float(np.max(asymptotic_residuals))
    
    # 5. 内层边界层过渡时间计算 (快模态衰减至 1% 阈值所需物理时间)
    # exp(lam_fast * t_trans) = 0.01  =>  t_trans = ln(100) / |lam_fast|
    t_trans_sec = float(np.log(100.0) / abs(lam_fast))
    t_trans_ms = t_trans_sec * 1000.0
    
    # 6. 浅缓冲区排队校验
    # 将无量纲偏离映射为实际排队深度 (15.0 + y_comp * 3.0)
    physical_queue = 15.0 + y_comp * 3.0
    peak_queue = float(np.max(physical_queue))
    buffer_drops = int(np.sum(physical_queue > 40.0))

    print("=== Task 0516 Boundary Layer Asymptotics Results ===")
    print(f"Max Asymptotic Residual: {max_asymptotic_residual:.4e} (target < 1e-5)")
    print(f"Inner Boundary Layer Transition Time: {t_trans_ms:.4f} ms (target < 10.0 ms)")
    print(f"Fast Mode Root λ_fast: {lam_fast:.4f}, Slow Mode Root λ_slow: {lam_slow:.4f}")
    print(f"Peak Queue Depth: {peak_queue:.2f} pkts (limit 40.0 pkts, target < 36.0)")
    print(f"Buffer Drops: {buffer_drops} (target 0)")
    
    assert max_asymptotic_residual < 1e-5, f"Residual {max_asymptotic_residual} >= 1e-5"
    assert t_trans_ms < 10.0, f"Transition time {t_trans_ms} ms >= 10.0 ms"
    assert peak_queue < 36.0, f"Peak queue {peak_queue} >= 36.0"
    assert buffer_drops == 0, f"Buffer drops {buffer_drops} > 0"
    
    metrics = {
        "task_id": "0516",
        "eps": eps,
        "max_asymptotic_residual": max_asymptotic_residual,
        "t_trans_ms": t_trans_ms,
        "lam_fast": float(lam_fast),
        "lam_slow": float(lam_slow),
        "peak_queue": peak_queue,
        "buffer_drops": buffer_drops,
        "status": "PASS"
    }
    
    out_dir = Path("zcode/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "0516_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
        
    print("SUCCESS: All Task 0516 verification criteria PASSED!")

if __name__ == "__main__":
    run_boundary_layer_expansion()
