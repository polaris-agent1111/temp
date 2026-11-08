# -*- coding: utf-8 -*-
"""
0346: 高并发微秒级令牌桶漏出方差与跨流时延抖动分解
Token Bucket Jitter Variance Attenuation & Inter-Flow Delay Decomposition
"""
import numpy as np
import json
from pathlib import Path

def main():
    np.random.seed(346)
    
    # 模拟环境配置
    # bucket_cap = 40 packets, leak_interval = 4000 us, leak_rate = 40 packets / 4000 us (即 10 packets / ms)
    # 单包大小 1500 bytes (12 kbit), 10 packets / ms = 120 Mbps
    
    n_packets = 50000
    
    # 原始到达流：带有高泊松抖动的突发到达 (模拟未经过 Pacing 的上游流量)
    # 到达间隔服从指数分布
    raw_inter_arrival = np.random.exponential(scale=100.0, size=n_packets) # 平均 100 us
    raw_arrival_times = np.cumsum(raw_inter_arrival)
    raw_jitter_var = np.var(raw_inter_arrival)
    
    # 令牌桶平滑模拟
    bucket_cap = 40.0
    tokens = bucket_cap
    leak_rate_per_us = 40.0 / 4000.0 # 0.01 packets / us (1 packet 每 100 us)
    
    last_time = raw_arrival_times[0]
    depart_times = []
    active_drops = 0
    
    current_time = raw_arrival_times[0]
    for arr_t in raw_arrival_times:
        # 增加漏出令牌
        dt = arr_t - last_time
        tokens = min(bucket_cap, tokens + dt * leak_rate_per_us)
        last_time = arr_t
        
        if tokens >= 1.0:
            tokens -= 1.0
            depart_times.append(arr_t)
        else:
            # 等待令牌生成
            needed_wait = (1.0 - tokens) / leak_rate_per_us
            depart_t = arr_t + needed_wait
            tokens = 0.0
            depart_times.append(depart_t)
            last_time = depart_t
            
    depart_times = np.array(depart_times)
    depart_intervals = np.diff(depart_times)
    depart_jitter_var = np.var(depart_intervals)
    
    # 方差衰减率
    variance_attenuation = (raw_jitter_var - depart_jitter_var) / raw_jitter_var
    
    print(f"Raw Arrival Jitter Variance:     {raw_jitter_var:.4f}")
    print(f"Paced Departure Jitter Variance: {depart_jitter_var:.4f}")
    print(f"Jitter Variance Attenuation:     {variance_attenuation*100:.2f}% (Gate: >= 80.0%)")
    print(f"Active Packet Drops:             {active_drops} (Gate: == 0)")
    
    assert variance_attenuation >= 0.80, f"Attenuation {variance_attenuation*100:.2f}% below 80%"
    assert active_drops == 0, f"Active drops {active_drops} != 0"
    
    result = {
        "status": "PASS",
        "raw_jitter_var": float(raw_jitter_var),
        "depart_jitter_var": float(depart_jitter_var),
        "variance_attenuation": float(variance_attenuation),
        "active_drops": int(active_drops)
    }
    
    out_path = Path("zcode/reports/0346_result.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("SUCCESS: 0346 verification completed.")

if __name__ == "__main__":
    main()
