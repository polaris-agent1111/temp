#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""官方 WebSearch 流长分布重尾碰撞高阶蒙特卡洛仿真模拟器.

严格复刻官方文档《背景流量模型说明》（02_websearch_model.md）：
- 11 节点累积概率分布（CDF）分段线性插值；
- 目标速率 100 Mbps (12.5 MB/s)，期望流长 1.711 MB；
- 复合泊松流过程 (Compound Poisson Process) 抽样；
- 统计 1~6.bin 各文件下载时间窗口内遭遇重流的碰撞概率；
- 模拟 5 发提交下的极值胜率 (min-of-N distribution)。
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
import numpy as np

# 官方 11 节点累积分布 (Bytes, Cumulative Probability)
CDF_POINTS = [
    (0, 0.0),
    (10000, 0.15),
    (20000, 0.20),
    (30000, 0.30),
    (50000, 0.40),
    (80000, 0.53),
    (200000, 0.60),
    (1000000, 0.70),
    (2000000, 0.80),
    (5000000, 0.90),
    (10000000, 0.97),
    (30000000, 1.00)
]

TARGET_RATE_BYTES_PER_SEC = 12500000.0  # 100 Mbps = 12.5 MB/s


def sample_flow_sizes(n: int, rng: np.random.Generator) -> np.ndarray:
    """逆变换采样（分段线性插值）。"""
    u = rng.uniform(0.0, 1.0, size=n)
    sizes = np.zeros(n, dtype=np.float64)
    
    for i in range(len(CDF_POINTS) - 1):
        x0, f0 = CDF_POINTS[i]
        x1, f1 = CDF_POINTS[i + 1]
        mask = (u >= f0) & (u < f1 if i < len(CDF_POINTS) - 2 else u <= f1)
        if np.any(mask):
            frac = (u[mask] - f0) / (f1 - f0)
            sizes[mask] = x0 + frac * (x1 - x0)
            
    return sizes


def compute_theoretical_mean() -> float:
    mean_val = 0.0
    for i in range(len(CDF_POINTS) - 1):
        x0, f0 = CDF_POINTS[i]
        x1, f1 = CDF_POINTS[i + 1]
        prob = f1 - f0
        mid = (x0 + x1) / 2.0
        mean_val += prob * mid
    return mean_val


def run_simulation(trials: int = 100000, seed: int = 42) -> dict:
    rng = np.random.default_rng(seed)
    theo_mean = compute_theoretical_mean()
    flow_arrival_rate = TARGET_RATE_BYTES_PER_SEC / theo_mean  # ~7.3046 flows/sec
    
    # 典型文件下载耗时窗口（秒）
    windows = {
        "1.bin (10M)": 1.5,
        "2.bin (20M)": 2.9,
        "3.bin (40M)": 5.7,
        "4.bin (80M)": 12.0,
        "5.bin (160M)": 28.0,
        "6.bin (320M)": 58.0
    }
    
    results = {
        "theoretical_mean_bytes": theo_mean,
        "theoretical_arrival_rate_hz": flow_arrival_rate,
        "trials": trials,
        "windows": {}
    }
    
    print(f"=== WebSearch 蒙特卡洛高阶仿真 (N={trials:,} 轮次) ===")
    print(f"理论期望流长: {theo_mean/1e6:.4f} MB")
    print(f"背景流理论到达率 λ: {flow_arrival_rate:.4f} flows/s\n")
    
    for name, dur in windows.items():
        expected_flows = flow_arrival_rate * dur
        # 泊松分布生成到达流数
        flow_counts = rng.poisson(expected_flows, size=trials)
        total_flows = np.sum(flow_counts)
        
        # 批量抽样全部流
        all_sizes = sample_flow_sizes(total_flows, rng)
        
        # 切割为每轮仿真
        splits = np.cumsum(flow_counts)[:-1]
        trials_sizes = np.split(all_sizes, splits)
        
        hit_1m = np.zeros(trials, dtype=bool)
        hit_5m = np.zeros(trials, dtype=bool)
        hit_10m = np.zeros(trials, dtype=bool)
        hit_20m = np.zeros(trials, dtype=bool)
        hit_30m = np.zeros(trials, dtype=bool)
        max_flow_per_trial = np.zeros(trials, dtype=np.float64)
        
        for idx, s in enumerate(trials_sizes):
            if len(s) > 0:
                m = np.max(s)
                max_flow_per_trial[idx] = m
                hit_1m[idx] = np.any(s >= 1000000)
                hit_5m[idx] = np.any(s >= 5000000)
                hit_10m[idx] = np.any(s >= 10000000)
                hit_20m[idx] = np.any(s >= 20000000)
                hit_30m[idx] = np.any(s >= 28000000)
                
        p_1m = float(np.mean(hit_1m))
        p_5m = float(np.mean(hit_5m))
        p_10m = float(np.mean(hit_10m))
        p_20m = float(np.mean(hit_20m))
        p_30m = float(np.mean(hit_30m))
        
        results["windows"][name] = {
            "duration_sec": dur,
            "expected_flows": expected_flows,
            "p_hit_1M": p_1m,
            "p_hit_5M": p_5m,
            "p_hit_10M": p_10m,
            "p_hit_20M": p_20m,
            "p_hit_30M_near": p_30m,
            "median_max_flow_MB": float(np.median(max_flow_per_trial) / 1e6),
            "p90_max_flow_MB": float(np.percentile(max_flow_per_trial, 90) / 1e6)
        }
        
        print(f"[{name}] 窗口 {dur}s | 期望流数 {expected_flows:.1f} | 命中≥1M: {p_1m*100:.1f}% | 命中≥10M: {p_10m*100:.1f}% | 命中≥28M: {p_30m*100:.2f}% | 中位最大流: {np.median(max_flow_per_trial)/1e6:.2f}MB")

    # ---------------- 5 发冲榜极值胜率精算 ----------------
    print("\n=== 5 发提交极值分布精算 (Extreme Value Simulation) ===")
    # 一次评测的总时间约 108s ~ 135s
    # 模拟在 5 发提交中，至少有 1 发 5.bin 和 6.bin 都未遭遇超大碰撞 (流长 < 10MB)
    p_5_clean = 1.0 - results["windows"]["5.bin (160M)"]["p_hit_10M"]
    p_6_clean = 1.0 - results["windows"]["6.bin (320M)"]["p_hit_10M"]
    p_both_clean = p_5_clean * p_6_clean  # 假设连接间独立
    
    p_at_least_1_clean_in_5 = 1.0 - (1.0 - p_both_clean) ** 5
    p_at_least_2_clean_in_5 = sum(
        math.comb(5, k) * (p_both_clean ** k) * ((1.0 - p_both_clean) ** (5 - k))
        for k in range(2, 6)
    )
    
    print(f"单场 5.bin 未撞 ≥10MB 概率: {p_5_clean*100:.2f}%")
    print(f"单场 6.bin 未撞 ≥10MB 概率: {p_6_clean*100:.2f}%")
    print(f"单场 5.bin + 6.bin 双清洁黄金窗口概率: {p_both_clean*100:.2f}%")
    print(f"★ 5 发提交中至少 1 发撞入黄金窗口 (<116.5s 破纪录): {p_at_least_1_clean_in_5*100:.2f}%")
    print(f"★ 5 发提交中至少 2 发撞入黄金窗口 (多发冗余制胜): {p_at_least_2_clean_in_5*100:.2f}%")
    
    results["extreme_value_5_shots"] = {
        "p_single_clean": p_both_clean,
        "p_at_least_1_clean_in_5": p_at_least_1_clean_in_5,
        "p_at_least_2_clean_in_5": p_at_least_2_clean_in_5
    }
    
    return results


if __name__ == "__main__":
    res = run_simulation(trials=100000)
    out_path = Path(__file__).resolve().parents[1] / "docs" / "analysis" / "monte_carlo_results.json"
    out_path.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n结果已落盘: {out_path}")
