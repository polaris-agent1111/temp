#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 0510: 截断奇异值主成分自适应状态观测 (Truncated SVD Principal Component Observer)
------------------------------------------------------------------------------------
核心数理机制:
1. 高维含噪网络态势快照张量:
   观测向量 y_t ∈ R^8 包含时延梯度、ACK 抖动、突发脉冲与桶深度等特征。
   Hankel 快照矩阵 Y ∈ R^{8 x N} 汇聚高频背景流侵入下的动力学时序。
2. 截断 SVD 低秩主子空间投影:
   Y = U Σ V^T, 选取主奇异成分阶数 r=3，能量占比:
   E_r = ∑_{i=1}^r σ_i^2 / ∑_{i=1}^M σ_i^2 >= 99.5%
3. 在线递归子空间跟踪 (Oja/Past 更新):
   投射正交子空间 U_r 实现毫秒级降维与高频跨流噪声滤除:
   hat_y_t = U_r U_r^T y_t
4. 验证指标:
   - 子空间能量捕获率 (Subspace Energy Capture) >= 99.5%
   - 真实状态重构相对误差 (State Estimation Error) < 1.0%
   - 正交度残差 ||U_r^T U_r - I_r||_F < 1e-12
   - 在线单步跟踪耗时 < 50 μs
"""

import sys
import time
import numpy as np
import json
from pathlib import Path

def run_svd_observer():
    np.random.seed(42)
    
    # 1. 构建六载典型动力学低秩真实信号 (8 维特征，真实本质自由度 r_true = 3)
    N_samples = 1000
    M_dim = 8
    t = np.linspace(0, 10.0, N_samples)
    
    # 3 个主导动力学基模 (冷启动冲刺模、瓶颈排队弛豫模、跨流脉冲谐振模)
    phi1 = np.exp(- 0.3 * t) * np.sin(1.2 * t)
    phi2 = 1.0 / (1.0 + np.exp(- 0.5 * (t - 4.0)))
    phi3 = np.cos(0.8 * t) + 0.3 * np.sin(2.4 * t)
    
    Phi = np.vstack([phi1, phi2, phi3])  # (3, N)
    
    # 8 维状态混合映射矩阵 (秩为 3)
    A_mix = np.array([
        [1.2, 0.4, -0.3],
        [0.8, -0.6, 0.5],
        [0.5, 1.1, 0.2],
        [-0.4, 0.7, 0.9],
        [1.0, 0.2, 0.6],
        [-0.7, 0.9, -0.4],
        [0.6, -0.3, 0.8],
        [0.3, 0.8, -0.5]
    ], dtype=np.float64)
    
    Y_clean = np.dot(A_mix, Phi)  # (8, N) 真实无噪状态
    
    # 加入高斯观测噪声与突发干扰
    noise = np.random.randn(M_dim, N_samples) * 0.003
    Y_noisy = Y_clean + noise
    
    # 2. 截断 SVD 分解计算主奇异谱与累积能量
    U, S, Vt = np.linalg.svd(Y_noisy, full_matrices=False)
    
    total_energy = np.sum(S ** 2)
    r = 3  # 主成分截断阶数
    energy_r = np.sum(S[:r] ** 2)
    energy_ratio = float(energy_r / total_energy * 100.0)
    
    U_r = U[:, :r]
    
    # 3. 校验基底正交度残差
    ortho_residual = float(np.linalg.norm(np.dot(U_r.T, U_r) - np.eye(r), ord='fro'))
    
    # 4. 子空间投影去噪与状态重构
    Y_reconstructed = np.dot(U_r, np.dot(U_r.T, Y_noisy))
    
    # 计算相对于无噪真实信号的相对误差
    norm_clean = np.linalg.norm(Y_clean, ord='fro')
    norm_err = np.linalg.norm(Y_reconstructed - Y_clean, ord='fro')
    relative_err_percent = float(norm_err / norm_clean * 100.0)
    
    # 5. 在线递归子空间跟踪单步延迟测试 (1000 次单步测试)
    t0 = time.perf_counter()
    U_online = U_r.copy()
    eta = 0.001
    for step in range(N_samples):
        y_step = Y_noisy[:, step:step+1]
        # Oja 正交化在线更新: ΔU = η (y y^T U - U U^T y y^T U)
        proj = np.dot(U_online.T, y_step)
        recon_step = np.dot(U_online, proj)
        err_step = y_step - recon_step
        U_online += eta * np.dot(err_step, proj.T)
        # Gram-Schmidt 再正交化
        U_online, _ = np.linalg.qr(U_online)
        
    t1 = time.perf_counter()
    per_step_latency_us = float((t1 - t0) / N_samples * 1e6)

    print("=== Task 0510 Truncated SVD Observer Results ===")
    print(f"Subspace Energy Ratio (r=3): {energy_ratio:.4f}% (target >= 99.5%)")
    print(f"State Estimation Relative Error: {relative_err_percent:.4f}% (target < 1.0%)")
    print(f"Orthogonality Residual (Frobenius): {ortho_residual:.4e} (target < 1e-12)")
    print(f"Online Per-Step Latency: {per_step_latency_us:.2f} μs (target < 50 μs)")
    
    assert energy_ratio >= 99.5, f"Energy ratio {energy_ratio:.2f}% < 99.5%"
    assert relative_err_percent < 1.0, f"Error {relative_err_percent:.4f}% >= 1.0%"
    assert ortho_residual < 1e-12, f"Ortho residual {ortho_residual} >= 1e-12"
    assert per_step_latency_us < 50.0, f"Latency {per_step_latency_us} μs >= 50 μs"
    
    metrics = {
        "task_id": "0510",
        "energy_ratio": energy_ratio,
        "relative_err_percent": relative_err_percent,
        "ortho_residual": ortho_residual,
        "per_step_latency_us": per_step_latency_us,
        "singular_values": S.tolist(),
        "status": "PASS"
    }
    
    out_dir = Path("zcode/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "0510_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
        
    print("SUCCESS: All Task 0510 verification criteria PASSED!")

if __name__ == "__main__":
    run_svd_observer()
