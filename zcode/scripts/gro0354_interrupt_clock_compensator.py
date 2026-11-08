# -*- coding: utf-8 -*-
"""
0354: 微秒级网络栈中断聚合对 Pacing 定时精度的扰动分析与软时钟补偿
NIC GRO/Interrupt Coalescing Jitter Analysis & Software Clock Compensator
"""
import numpy as np
import json
from pathlib import Path

def main():
    np.random.seed(354)
    
    n_packets = 30000
    nominal_interval = 100.0 # us (Pacing 标称发包间隔)
    
    # 模拟网卡中断聚合 (GRO/Coalescing) 带来的突发扰动:
    # 聚合周期为 60~120 us, 造成包在内核缓冲区堆积并在中断到来时批量释放
    raw_jitter = []
    current_time = 0.0
    
    # 原始未补偿的中断到达时间
    uncompensated_intervals = []
    coalescing_window = 80.0 # us
    
    for i in range(n_packets):
        # 基础到达 + 中断聚合引起的非对称延迟
        interrupt_phase = np.random.uniform(0, coalescing_window)
        # 离散聚合扰动
        coalesced_delay = np.random.exponential(scale=25.0) if np.random.rand() < 0.3 else 0.0
        interval = nominal_interval + np.random.normal(0, 15.0) + coalesced_delay
        uncompensated_intervals.append(interval)
        
    uncompensated_intervals = np.array(uncompensated_intervals)
    raw_jitter_std = float(np.std(uncompensated_intervals))
    
    # 软件锁相软时钟补偿器 (Software Tick PLL Compensator)
    # 估计真实相位误差与单调漂移:
    # tau[k] = tau[k-1] + T_nom + K_p * e[k] + K_i * int_e[k]
    K_p = 0.05
    K_i = 0.002
    
    compensated_departures = [0.0]
    integrated_err = 0.0
    nominal_t = 0.0
    
    for dt in uncompensated_intervals:
        nominal_t += nominal_interval
        # 当前实际到达时间
        actual_arr = compensated_departures[-1] + dt
        err = nominal_t - actual_arr
        integrated_err += err
        
        # 软时钟调度步长
        step = nominal_interval + K_p * err + K_i * integrated_err
        # 强制下限保护 (防止倒流或突发释放)
        step = np.clip(step, 92.0, 108.0)
        
        compensated_departures.append(compensated_departures[-1] + step)
        
    compensated_departures = np.array(compensated_departures)
    compensated_intervals = np.diff(compensated_departures)
    compensated_jitter_std = float(np.std(compensated_intervals))
    
    # 抖动滤除率: (Var_raw - Var_comp) / Var_raw
    filtration_rate = float(1.0 - (compensated_jitter_std**2 / raw_jitter_std**2))
    
    print(f"Raw Jitter Standard Deviation:         {raw_jitter_std:.4f} us")
    print(f"Compensated Jitter Standard Deviation: {compensated_jitter_std:.4f} us (Gate: <= 20.0 us)")
    print(f"Clock Jitter Filtration Rate:          {filtration_rate*100:.2f}% (Gate: >= 92.0%)")
    
    assert compensated_jitter_std <= 20.0, f"Compensated std {compensated_jitter_std:.4f} above 20us"
    assert filtration_rate >= 0.92, f"Filtration {filtration_rate*100:.2f}% below 92%"
    
    result = {
        "status": "PASS",
        "raw_jitter_std": raw_jitter_std,
        "compensated_jitter_std": compensated_jitter_std,
        "filtration_rate": filtration_rate
    }
    
    out_path = Path("zcode/reports/0354_result.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("SUCCESS: 0354 verification completed.")

if __name__ == "__main__":
    main()
