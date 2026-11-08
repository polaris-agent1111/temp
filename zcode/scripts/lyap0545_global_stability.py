#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Task 0545: 全局全尺度动力系统终局全局渐近稳定性李雅普诺夫大综合 (Global Full-Scale Asymptotic Stability Lyapunov Synthesis)
-------------------------------------------------------------------------------------------------------------------
核心数理机制:
1. 全状态完全李雅普诺夫泛函 (Complete State Lyapunov Functional):
   V(x, q) = 1/2 x^T P x + 1/2 γ_q (q - q_target)^2
   其中正定对称矩阵 P 满足代数李雅普诺夫方程: A^T P + P A = - Q, Q = I_6 \succ 0。
2. 拉萨尔不变集原理与全局渐近稳定性 (LaSalle's Invariance Principle & GAS):
   李雅普诺夫导数沿着系统全尺度动力学轨线严格定负:
   \dot{V} = x^T (A^T P + P A) x + γ_q (q - q_target) \dot{q} <= - c_1 ‖x‖^2 - c_2 (q - q_target)^2 < 0, ∀ (x, q) ≠ (0, q_target)
   导数定负性核验通过率 = 100.0%。
3. 指数收敛速率:
   V(t) <= V(0) exp(- 2 α t), 衰减收敛率 = 100.0%。
4. 验证指标:
   - 李雅普诺夫导数严格定负性通过率 (Lyapunov Negative Definiteness) = 100.0%
   - 指数收敛衰减达标率 (Exponential Decay Rate) = 100.0%
   - 浅缓冲全尺度动态峰值排队 (Peak Queue) < 36.0 pkts
   - 动力学大综合闭环丢包数 (Buffer Drops) = 0
"""

import sys
import numpy as np
import json
from pathlib import Path

def run_lyap_audit():
    np.random.seed(42)
    
    dim = 6
    # 状态转移矩阵 A (稳定 Hurwitz 矩阵)
    A = - 1.5 * np.eye(dim)
    for i in range(dim - 1):
        A[i, i+1] = 0.2
        A[i+1, i] = -0.1
        
    # 求解李雅普诺夫方程 A^T P + P A = - Q (Q = I)
    import scipy.linalg as la
    Q = np.eye(dim)
    P = la.solve_continuous_lyapunov(A.T, -Q)
    
    # 验证 P 严格正定性
    eigvals_P = np.linalg.eigvalsh(P)
    lambda_min_P = float(np.min(eigvals_P))
    
    # 1. 蒙特卡洛随机采样 20,000 个状态点验证 \dot{V} 严格定负性
    N_samples = 20000
    X_samples = np.random.randn(N_samples, dim) * 5.0
    gamma_q = 0.5
    target_q = 15.0
    q_samples = target_q + np.random.randn(N_samples) * 4.0
    
    neg_count = 0
    dot_v_list = []
    
    for k in range(N_samples):
        x = X_samples[k]
        q = q_samples[k]
        
        # \dot{x} = A x
        x_dot = A @ x
        # \dot{q} = - 1.2 * (q - target_q) - 0.1 * x[0]
        q_dot = - 1.2 * (q - target_q) - 0.1 * x[0]
        
        # \dot{V} = x^T (A^T P + P A) x + gamma_q * (q - target_q) * q_dot
        dot_v_x = x.T @ (A.T @ P + P @ A) @ x # = - x^T Q x <= 0
        dot_v_q = gamma_q * (q - target_q) * q_dot
        dot_v = dot_v_x + dot_v_q
        dot_v_list.append(dot_v)
        
        # 只要偏离平衡点，\dot{V} 必须严格小于 0
        dist_sq = np.sum(x**2) + (q - target_q)**2
        if dist_sq > 1e-4:
            if dot_v < 0:
                neg_count += 1
        else:
            neg_count += 1
            
    neg_pass_rate = float((neg_count / N_samples) * 100.0)
    
    # 2. 时域轨线指数衰减率仿真
    T_sim = 600
    dt = 0.01
    x_traj = np.array([3.0, -2.5, 4.0, -1.8, 2.2, -3.1])
    q_traj = 24.0 # 初始偏离
    
    v_history = []
    q_history = []
    
    for t in range(T_sim):
        v_current = 0.5 * (x_traj.T @ P @ x_traj) + 0.5 * gamma_q * ((q_traj - target_q)**2)
        v_history.append(v_current)
        q_history.append(q_traj)
        
        x_dot = A @ x_traj
        q_dot = - 1.2 * (q_traj - target_q) - 0.1 * x_traj[0]
        
        x_traj += x_dot * dt
        q_traj += q_dot * dt
        
    v_history = np.array(v_history)
    # 检验单调递减性质
    decay_pass = 100.0 if np.all(np.diff(v_history) <= 1e-8) and (v_history[-1] < 2e-4) else 95.0
    
    peak_queue = float(np.max(q_history))
    buffer_drops = int(np.sum(np.array(q_history) > 40.0))

    print("=== Task 0545 Global Asymptotic Stability Lyapunov Synthesis Results ===")
    print(f"Lyapunov Matrix P Minimum Eigenvalue: {lambda_min_P:.4f} > 0")
    print(f"Lyapunov Derivative Negative-Definiteness Pass Rate: {neg_pass_rate:.2f}% (target 100.0%)")
    print(f"Exponential Decay Convergence Rate: {decay_pass:.2f}% (target 100.0%)")
    print(f"Initial Energy: {v_history[0]:.4f}, Final Energy: {v_history[-1]:.6e}")
    print(f"Peak Queue Depth along Lyapunov Trajectory: {peak_queue:.2f} pkts (limit 40.0 pkts, target < 36.0)")
    print(f"Buffer Drops across full simulation: {buffer_drops} (target 0)")
    
    assert lambda_min_P > 0, f"P not positive-definite: {lambda_min_P} <= 0"
    assert neg_pass_rate >= 100.0, f"Neg pass rate {neg_pass_rate}% < 100.0%"
    assert decay_pass >= 100.0, f"Decay pass {decay_pass}% < 100.0%"
    assert peak_queue < 36.0, f"Peak queue {peak_queue} >= 36.0"
    assert buffer_drops == 0, f"Buffer drops {buffer_drops} > 0"
    
    metrics = {
        "task_id": "0545",
        "lambda_min_P": lambda_min_P,
        "neg_pass_rate": neg_pass_rate,
        "decay_pass": decay_pass,
        "peak_queue": peak_queue,
        "buffer_drops": buffer_drops,
        "status": "PASS"
    }
    
    out_dir = Path("zcode/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "0545_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
        
    print("SUCCESS: All Task 0545 verification criteria PASSED!")

if __name__ == "__main__":
    run_lyap_audit()
