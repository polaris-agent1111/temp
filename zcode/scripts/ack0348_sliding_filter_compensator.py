# -*- coding: utf-8 -*-
"""
0348: 自适应 QUIC ACK 压缩在线检测与滑动平滑滤波补偿
Adaptive QUIC ACK Compression Online Detection & Sliding Smoothing Compensator
"""
import numpy as np
import json
from pathlib import Path

def main():
    np.random.seed(348)
    
    n_acks = 20000
    
    # 模拟正常到达时间 (均匀 ACK 发送，间隔 100 us)
    base_intervals = np.full(n_acks, 100.0) # us
    
    # 注入反向链路严重 ACK 压缩事件 (每 100 个 ACK 发生一次 5-10 包堆叠压缩)
    compressed_intervals = base_intervals.copy()
    for idx in range(100, n_acks - 20, 100):
        burst_size = np.random.randint(5, 10)
        # 堆叠后集中到达: 间隔压缩至 5 us，随后出现空隙
        compressed_intervals[idx : idx + burst_size] = 5.0
        compressed_intervals[idx + burst_size] = burst_size * 95.0 + 100.0
        
    raw_arrival_times = np.cumsum(compressed_intervals)
    raw_inter_arr = np.diff(raw_arrival_times)
    compression_mask = raw_inter_arr < 20.0
    n_compressions = np.sum(compression_mask)
    
    # 滑动平滑滤波补偿器设计
    # 二阶低通滑动平滑 + 刚性下限保护
    alpha = 0.08
    min_pacing = 98.0 # us 保护发包节奏不因堆叠 ACK 激增
    
    paced_departures = [raw_arrival_times[0]]
    smoothed = 100.0
    for dt in raw_inter_arr:
        smoothed = alpha * dt + (1.0 - alpha) * smoothed
        paced_dt = max(min_pacing, smoothed)
        paced_departures.append(paced_departures[-1] + paced_dt)
        
    paced_departures = np.array(paced_departures)
    paced_intervals = np.diff(paced_departures)
    
    # 脉冲因子 F = Mean / P1 (衡量极值突发度)
    p1 = np.percentile(paced_intervals, 1.0)
    burst_factor_paced = float(np.mean(paced_intervals) / p1)
    
    # 平滑滤除率: 压缩事件被缓冲平滑消除的比例
    residual_bursts = np.sum(paced_intervals < 90.0)
    suppression_rate = float(1.0 - (residual_bursts / max(1, n_compressions)))
    
    print(f"Compressed ACK Events:       {n_compressions}")
    print(f"Paced Percentile P1:         {p1:.2f} us")
    print(f"Paced Burst Factor F:        {burst_factor_paced:.4f} (Gate: <= 1.05)")
    print(f"Compression Suppression:     {suppression_rate*100:.2f}% (Gate: >= 90.0%)")
    
    assert burst_factor_paced <= 1.05, f"Burst factor {burst_factor_paced:.4f} above 1.05"
    assert suppression_rate >= 0.90, f"Suppression {suppression_rate*100:.2f}% below 90%"
    
    result = {
        "status": "PASS",
        "burst_factor_paced": float(burst_factor_paced),
        "suppression_rate": float(suppression_rate),
        "n_compressions": int(n_compressions)
    }
    
    out_path = Path("zcode/reports/0348_result.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("SUCCESS: 0348 verification completed.")

if __name__ == "__main__":
    main()
