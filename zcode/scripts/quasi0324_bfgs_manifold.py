# -*- coding: utf-8 -*-
"""
Task 0324: 非凸参数流形上的拟牛顿割线步长加速探索
在六轮次传输参数空间中验证 BFGS 拟牛顿算法的高阶梯度快速收敛
"""
import sys
import json
import time
import numpy as np
from scipy.optimize import minimize
import datetime

def main():
    print("=" * 70)
    print("=== Task 0324: 非凸参数流形上的拟牛顿割线步长加速探索 ===")
    print("=" * 70)

    # 六维参数流形 (代表 1 至 6 轮次的 Pacing 目标速率, 80 Mbps ~ 100 Mbps)
    np.random.seed(324)
    dim = 6
    x_star = np.array([96.0, 96.0, 98.0, 98.0, 100.0, 100.0])
    # 模拟瓶颈耦合正定 Hessian 矩阵
    A = np.random.randn(dim, dim)
    Hess = A.T @ A + 2.0 * np.eye(dim)

    # 目标函数: 综合时延损失流形
    def loss_func(x):
        diff = x - x_star
        return 0.5 * float(diff.T @ Hess @ diff) + np.sum(np.sin(0.1 * x)**2)

    def grad_func(x):
        diff = x - x_star
        return Hess @ diff + 0.2 * np.sin(0.1 * x) * np.cos(0.1 * x)

    # 初始点 (远端点位)
    x0 = np.array([80.0, 82.0, 85.0, 85.0, 90.0, 90.0])
    g0 = grad_func(x0)
    g0_norm = float(np.linalg.norm(g0))

    # 执行 BFGS 拟牛顿探索并计时
    t_start = time.perf_counter()
    res = minimize(loss_func, x0, method='BFGS', jac=grad_func, options={'maxiter': 25, 'gtol': 1e-4})
    t_elapsed_ms = (time.perf_counter() - t_start) * 1000.0

    x_final = res.x
    g_final = grad_func(x_final)
    g_final_norm = float(np.linalg.norm(g_final))

    # 梯度模长收缩比例
    grad_reduction_ratio = float(1.0 - (g_final_norm / g0_norm))

    print(f"[OK] 六维参数流形 BFGS 优化收敛测试完成:")
    print(f"     初始梯度模长 ||g0||:       {g0_norm:.4f}")
    print(f"     收敛梯度模长 ||g_final||:  {g_final_norm:.6f}")
    print(f"     梯度模长收缩率:            {grad_reduction_ratio*100:.2f}% (门禁指标 >= 80.0%)")
    print(f"     算法计算用时:              {t_elapsed_ms:.4f} ms (门禁指标 <= 5.0 ms)")
    print(f"     收敛轮次:                  {res.nit} iterations")

    pass_gate = bool(grad_reduction_ratio >= 0.80 and t_elapsed_ms <= 5.0)
    print(f"[GATE] 门禁达成: {pass_gate}")

    report = {
        "task": "0324",
        "verified_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC+08:00"),
        "dimensions": dim,
        "g0_norm": round(g0_norm, 4),
        "g_final_norm": round(g_final_norm, 6),
        "grad_reduction_ratio": round(grad_reduction_ratio, 4),
        "elapsed_ms": round(t_elapsed_ms, 4),
        "iterations": int(res.nit),
        "pass_gate": pass_gate
    }

    out_file = r"e:\Download\iDSN\runs\quasi0324_bfgs_manifold.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"[SUCCESS] 拟牛顿流形审计数据已落盘: {out_file}")
    print("=" * 70)

if __name__ == "__main__":
    main()
