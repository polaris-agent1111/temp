#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0306: Shot 2 实时信道状态迁移矩阵更新与转移概率马尔可夫链稳态求解
更新三状态马尔可夫转移矩阵 P，求解夜间低负载稳态概率分布 pi*，
证明几何收敛性，次大特征值谱半径 |lambda_2| < 1.0，求解精度 <= 1e-4。
"""
from __future__ import annotations

import datetime as dt
import json
import math
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]

# 夜间实战信道马尔可夫转移矩阵 (基于历史观测与午夜先验校准)
# 状态定义: 0: Clean, 1: Nominal, 2: Congested
P_MATRIX = [
    [0.72, 0.23, 0.05], # 从 Clean 状态出发
    [0.28, 0.60, 0.12], # 从 Nominal 状态出发
    [0.20, 0.55, 0.25], # 从 Congested 状态出发
]

def matrix_vector_mul(p: list[list[float]], v: list[float]) -> list[float]:
    """计算 v * P (行向量左乘转移矩阵)"""
    n = len(v)
    res = [0.0] * n
    for j in range(n):
        for i in range(n):
            res[j] += v[i] * p[i][j]
    return res

def l1_norm(v1: list[float], v2: list[float]) -> float:
    return sum(abs(a - b) for a, b in zip(v1, v2))

def solve_steady_state_power_iteration(p: list[list[float]], max_iter: int = 100, tol: float = 1e-6) -> tuple[list[float], int, list[float]]:
    """幂迭代法求解稳态分布 pi*，并跟踪每步误差。"""
    n = len(p)
    pi = [1.0 / n] * n # 初始均匀分布
    errors = []

    for it in range(1, max_iter + 1):
        pi_next = matrix_vector_mul(p, pi)
        err = l1_norm(pi_next, pi)
        errors.append(err)
        pi = pi_next
        if err < tol:
            return pi, it, errors

    return pi, max_iter, errors

def compute_eigenvalues_3x3(p: list[list[float]]) -> list[float]:
    """解析求解 3x3 转移矩阵特征值 (主特征值 lambda_1 = 1.0)。"""
    # 迹 (Trace) 与 主子式求特征方程
    tr = p[0][0] + p[1][1] + p[2][2]
    # 行列式 det(P)
    det = (p[0][0]*(p[1][1]*p[2][2] - p[1][2]*p[2][1])
         - p[0][1]*(p[1][0]*p[2][2] - p[1][2]*p[2][0])
         + p[0][2]*(p[1][0]*p[2][1] - p[1][1]*p[2][0]))
    
    # 由于 lambda_1 = 1.0，特征方程可降次: (lambda - 1)(lambda^2 - b*lambda + c) = 0
    # 其中 b = tr - 1, c = det
    b = tr - 1.0
    c = det
    disc = b**2 - 4.0 * c
    if disc >= 0:
        l2 = (b + math.sqrt(disc)) / 2.0
        l3 = (b - math.sqrt(disc)) / 2.0
    else:
        # 复特征值模长
        l2 = math.sqrt(c)
        l3 = l2
    return [1.0, abs(l2), abs(l3)]

def main() -> int:
    print("=" * 70)
    print("=== Task 0306: Shot 2 实时信道状态迁移矩阵更新与稳态分布求解 ===")
    print("=" * 70)

    # 1. 验证转移矩阵概率守恒 (每行之和为 1.0)
    for idx, row in enumerate(P_MATRIX):
        s = sum(row)
        assert abs(s - 1.0) < 1e-9, f"Row {idx} sum is not 1.0: {s}"
    print(f"[OK] 马尔可夫转移矩阵 P 满足概率守恒公理 (各行求和为 1.0000)")

    # 2. 特征值谱分析与谱半径检验
    eigs = compute_eigenvalues_3x3(P_MATRIX)
    lambda_2 = max(eigs[1], eigs[2])
    spectral_gap = 1.0 - lambda_2
    print(f"[OK] 特征值谱结构: lambda_1={eigs[0]:.4f}, |lambda_2|={eigs[1]:.4f}, |lambda_3|={eigs[2]:.4f}")
    print(f"     次大特征值谱半径: {lambda_2:.4f} (门禁要求 < 1.0000)")
    print(f"     谱间隙 (Spectral Gap): {spectral_gap:.4f} (正谱间隙保障指数级收敛)")
    assert lambda_2 < 1.0, f"Spectral radius too large: {lambda_2}"

    # 3. 幂迭代稳态分布求解
    pi_star, iters, err_seq = solve_steady_state_power_iteration(P_MATRIX, tol=1e-5)
    final_err = err_seq[-1]
    print(f"\n[OK] 幂迭代法在第 {iters} 轮精确收敛 (收敛残差 {final_err:.2e} <= 1e-4 门禁)")
    print(f"     夜间信道稳态分布 pi*:")
    print(f"       Clean (低负载畅通):      {pi_star[0]*100:5.2f}%")
    print(f"       Nominal (常态名义负载):  {pi_star[1]*100:5.2f}%")
    print(f"       Congested (重尾拥塞):    {pi_star[2]*100:5.2f}%")
    assert final_err <= 1e-4, f"Final error too high: {final_err}"

    report_data = {
        "task": "0306",
        "verified_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC+08:00"),
        "transition_matrix": P_MATRIX,
        "eigenvalues": [round(x, 4) for x in eigs],
        "spectral_radius_lambda2": round(lambda_2, 4),
        "spectral_gap": round(spectral_gap, 4),
        "convergence_iterations": iters,
        "final_residual_error": final_err,
        "steady_state_distribution": {
            "clean_pct": round(pi_star[0] * 100.0, 2),
            "nominal_pct": round(pi_star[1] * 100.0, 2),
            "congested_pct": round(pi_star[2] * 100.0, 2),
        },
        "pass_gate": (lambda_2 < 1.0 and final_err <= 1e-4)
    }

    out_file = ROOT / "runs" / "markov0306_transition_steady_state.json"
    out_file.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[SUCCESS] 马尔可夫稳态分布报表已落盘: {out_file}")
    print("=" * 70)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
