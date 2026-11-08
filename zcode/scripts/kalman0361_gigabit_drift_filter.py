# -*- coding: utf-8 -*-
"""
0361: 端到端纳秒级单调时钟漂移在千兆交换机下的自适应卡尔曼滤波
Adaptive Kalman Filter for End-to-End Clock Drift & On-Time Departure Under Gigabit Switches
"""
import numpy as np
import json
from pathlib import Path

def main():
    np.random.seed(361)
    
    n_steps = 30000
    dt = 0.0001 # 100 us 步长 (0.1 ms)
    
    # 真实物理时钟漂移过程: 初始频偏 15 ppm (0.000015 s/s), 包含微弱随机游走
    true_skew = 15.0e-6 # s/s
    true_offset = 0.0
    true_offsets = []
    
    for _ in range(n_steps):
        true_skew += np.random.normal(0, 1e-9)
        true_offset += true_skew * dt
        true_offsets.append(true_offset * 1e6) # us
        
    true_offsets = np.array(true_offsets)
    
    # 测量噪声 (千兆交换机排队抖动带来的时间戳噪声: std = 18 us)
    meas_noise_std = 18.0 # us
    measurements = true_offsets + np.random.normal(0, meas_noise_std, n_steps)
    
    # 二阶卡尔曼滤波器设计
    # 状态向量 x = [offset (us), skew (us/step)]^T
    F = np.array([[1.0, 1.0], [0.0, 1.0]])
    H = np.array([[1.0, 0.0]])
    
    Q = np.diag([1e-4, 1e-7])
    R = np.array([[meas_noise_std**2]])
    
    x_hat = np.array([0.0, 0.0])
    P_mat = np.eye(2) * 10.0
    
    estimated_offsets = []
    
    for y in measurements:
        # 预测步
        x_pred = F @ x_hat
        P_pred = F @ P_mat @ F.T + Q
        
        # 更新步
        y_innov = y - (H @ x_pred)[0]
        S_innov = (H @ P_pred @ H.T)[0, 0] + R[0, 0]
        K_gain = (P_pred @ H.T) / S_innov
        
        x_hat = x_pred + K_gain.flatten() * y_innov
        P_mat = (np.eye(2) - K_gain @ H) @ P_pred
        
        estimated_offsets.append(x_hat[0])
        
    estimated_offsets = np.array(estimated_offsets)
    
    # 稳态误差 (丢弃前 2,000 步瞬态阶段)
    steady_errors = np.abs(true_offsets[2000:] - estimated_offsets[2000:])
    steady_state_error = float(np.mean(steady_errors))
    p95_error = float(np.percentile(steady_errors, 95.0))
    
    # 发包准时率 (误差在 25us 容限内的比例)
    on_time_rate = float(np.mean(steady_errors <= 25.0))
    
    print(f"Raw Measurement Noise Std:     {meas_noise_std:.2f} us")
    print(f"Kalman Steady-State Mean Err:  {steady_state_error:.4f} us (Gate: <= 15.0 us)")
    print(f"Kalman P95 Steady-State Err:   {p95_error:.4f} us")
    print(f"Packet On-Time Departure Rate: {on_time_rate*100:.3f}% (Gate: >= 99.8%)")
    
    assert steady_state_error <= 15.0, f"Error {steady_state_error:.4f} above 15us"
    assert on_time_rate >= 0.998, f"On-time rate {on_time_rate*100:.3f}% below 99.8%"
    
    result = {
        "status": "PASS",
        "steady_state_error": steady_state_error,
        "p95_error": p95_error,
        "on_time_rate": on_time_rate
    }
    
    out_path = Path("zcode/reports/0361_result.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("SUCCESS: 0361 verification completed.")

if __name__ == "__main__":
    main()
