#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0293: Shot 1 真实出分榜单提取与信道拥塞度贝叶斯反演
通过实测下载时间 T1，后验反演信道拥塞度类别、等效交叉流突发强度与排队延迟，
后验反演准确率目标 >= 90.0%。
"""
from __future__ import annotations

import datetime as dt
import json
import math
import random
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]

# 状态先验与高斯似然参数
STATES = ["Clean", "Nominal", "Congested"]
PRIORS = {"Clean": 0.25, "Nominal": 0.55, "Congested": 0.20}
LIKELIHOOD_PARAMS = {
    "Clean": {"mu": 117.5, "sigma": 1.4, "bg_rate_mbps": 10.0, "queue_delay_ms": 2.5},
    "Nominal": {"mu": 124.0, "sigma": 1.6, "bg_rate_mbps": 28.5, "queue_delay_ms": 8.0},
    "Congested": {"mu": 133.0, "sigma": 2.5, "bg_rate_mbps": 48.0, "queue_delay_ms": 22.0},
}

def gaussian_pdf(x: float, mu: float, sigma: float) -> float:
    coeff = 1.0 / (sigma * math.sqrt(2.0 * math.pi))
    exponent = -0.5 * ((x - mu) / sigma) ** 2
    return coeff * math.exp(exponent)

def infer_channel_state(t1: float) -> dict:
    """给定实测下载时间 t1，计算贝叶斯后验概率分布与参数反演。"""
    unnorm = {}
    for st in STATES:
        p_prior = PRIORS[st]
        mu = LIKELIHOOD_PARAMS[st]["mu"]
        sigma = LIKELIHOOD_PARAMS[st]["sigma"]
        unnorm[st] = p_prior * gaussian_pdf(t1, mu, sigma)
    
    total = sum(unnorm.values())
    posteriors = {st: unnorm[st] / total if total > 0 else 1.0 / 3.0 for st in STATES}
    
    # MAP 状态估计
    best_state = max(posteriors.keys(), key=lambda s: posteriors[s])
    
    # 期望交叉流速率与排队延迟反演 (加权期望)
    expected_bg_rate = sum(posteriors[st] * LIKELIHOOD_PARAMS[st]["bg_rate_mbps"] for st in STATES)
    expected_queue_delay = sum(posteriors[st] * LIKELIHOOD_PARAMS[st]["queue_delay_ms"] for st in STATES)

    return {
        "t1_observed": t1,
        "map_state": best_state,
        "confidence": posteriors[best_state],
        "posteriors": posteriors,
        "inferred_bg_rate_mbps": round(expected_bg_rate, 2),
        "inferred_queue_delay_ms": round(expected_queue_delay, 2)
    }

def main() -> int:
    print("=" * 70)
    print("=== Task 0293: Shot 1 真实出分榜单提取与信道拥塞度贝叶斯反演 ===")
    print("=" * 70)

    # 1. 蒙特卡洛反演准确率验证 (n=2,000)
    random.seed(42)
    total_samples = 2000
    correct = 0

    for _ in range(total_samples):
        # 依先验生成真实状态
        r = random.random()
        if r < PRIORS["Clean"]:
            true_st = "Clean"
        elif r < PRIORS["Clean"] + PRIORS["Nominal"]:
            true_st = "Nominal"
        else:
            true_st = "Congested"
        
        # 依似然生成实测出分 T1
        params = LIKELIHOOD_PARAMS[true_st]
        t1_sim = random.gauss(params["mu"], params["sigma"])
        
        # 贝叶斯反演
        res = infer_channel_state(t1_sim)
        if res["map_state"] == true_st:
            correct += 1

    accuracy_pct = (correct / total_samples) * 100.0
    print(f"[OK] 2,000 次蒙特卡洛仿真贝叶斯反演准确率: {accuracy_pct:.2f}% (门禁要求 >= 90.0%)")
    assert accuracy_pct >= 90.0, f"Accuracy too low: {accuracy_pct}%"

    # 2. 典型实测出分案例推演
    test_cases = [118.2, 122.4, 124.3683, 127.5, 133.0]
    print("\n[INFO] 典型出分值反演推演:")
    inversion_results = []
    for tc in test_cases:
        out = infer_channel_state(tc)
        inversion_results.append(out)
        print(f"  T1 = {tc:7.4f}s -> MAP状态: {out['map_state']:<9} (置信度 {out['confidence']*100:5.1f}%) | "
              f"交叉流: {out['inferred_bg_rate_mbps']:4.1f} Mbps | 排队延迟: {out['inferred_queue_delay_ms']:4.1f} ms")

    # 3. 结果报表落盘
    report_data = {
        "task": "0293",
        "verified_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC+08:00"),
        "mc_samples": total_samples,
        "accuracy_pct": round(accuracy_pct, 2),
        "pass_gate": accuracy_pct >= 90.0,
        "priors": PRIORS,
        "test_cases": inversion_results
    }

    out_file = ROOT / "runs" / "bayes0293_congestion_inversion.json"
    out_file.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[SUCCESS] 贝叶斯反演审计结果已落盘: {out_file}")
    print("=" * 70)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
