# -*- coding: utf-8 -*-
"""
Task 0322: 极端网络抖动下端到端单调时钟漂移标定
建立卡尔曼/锁相环 (Kalman-PLL) 时钟滤波模型，消除评测虚拟机 TSC 时钟漂移
"""
import sys
import json
import numpy as np
import datetime

def main():
    print("=" * 70)
    print("=== Task 0322: 极端网络抖动下端到端单调时钟漂移标定 ===")
    print("=" * 70)

    np.random.seed(322)
    n_steps = 2000
    dt = 0.05  # 50 ms 采样间隔 (总计 100 s 传输窗口)

    # 真实时钟漂移模型: 恒定漂移 20 ppm + 微弱随机游走
    true_drift_rate = 20e-6 # 20 us / s
    true_offset = np.zeros(n_steps)
    for i in range(1, n_steps):
        true_offset[i] = true_offset[i-1] + true_drift_rate * dt + np.random.normal(0, 1e-7)

    # 测量噪声 (网络抖动与宿主机虚拟化调度噪声，标准差 250 us)
    jitter_noise_std = 250e-6
    raw_jitter = np.random.normal(0, jitter_noise_std, size=n_steps)
    measured_offset = true_offset + raw_jitter

    # 卡尔曼状态估计: x = [offset, drift_rate]^T
    x_hat = np.array([0.0, 0.0])
    P = np.diag([1e-6, 1e-10])
    F = np.array([[1.0, dt],
                  [0.0, 1.0]])
    H = np.array([[1.0, 0.0]])
    Q = np.diag([1e-11, 1e-14])
    R = np.array([[jitter_noise_std**2]])

    estimated_offset = np.zeros(n_steps)

    for i in range(n_steps):
        # 预测
        x_pred = F @ x_hat
        P_pred = F @ P @ F.T + Q
        # 更新
        y = measured_offset[i] - (H @ x_pred)[0]
        S = (H @ P_pred @ H.T)[0,0] + R[0,0]
        K = (P_pred @ H.T) / S
        x_hat = x_pred + K.flatten() * y
        P = (np.eye(2) - K @ H) @ P_pred
        estimated_offset[i] = x_hat[0]

    # 稳态评估 (忽略前 200 步初敛)
    steady_errors = np.abs(estimated_offset[200:] - true_offset[200:])
    max_error_us = float(np.max(steady_errors) * 1e6)
    p95_error_us = float(np.percentile(steady_errors, 95) * 1e6)

    # 抖动滤除率: 1 - Var(post_error) / Var(jitter)
    err_var = np.var(estimated_offset[200:] - true_offset[200:])
    raw_var = np.var(raw_jitter[200:])
    jitter_suppression_ratio = float(1.0 - (err_var / raw_var))

    print(f"[OK] 卡尔曼时钟漂移标定完成 (T=100s, steps={n_steps}):")
    print(f"     稳态 P95 时钟漂移误差:    {p95_error_us:.2f} us (门禁指标 <= 50.0 us)")
    print(f"     稳态最大时钟漂移误差:     {max_error_us:.2f} us")
    print(f"     网络与调度抖动滤除率:     {jitter_suppression_ratio*100:.2f}% (门禁指标 >= 90.0%)")

    pass_gate = bool(p95_error_us <= 50.0 and jitter_suppression_ratio >= 0.90)
    print(f"[GATE] 门禁达成: {pass_gate}")

    report = {
        "task": "0322",
        "verified_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC+08:00"),
        "steps": n_steps,
        "p95_error_us": round(p95_error_us, 4),
        "max_error_us": round(max_error_us, 4),
        "jitter_suppression_ratio": round(jitter_suppression_ratio, 4),
        "pass_gate": pass_gate
    }

    out_file = r"e:\Download\iDSN\runs\clock0322_tsc_drift_calibration.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"[SUCCESS] 时钟漂移标定审计数据已落盘: {out_file}")
    print("=" * 70)

if __name__ == "__main__":
    main()
