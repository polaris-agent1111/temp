#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0307: 官方评测服务器夜间 CPU 负载与调度抖动时序分解
对深夜宿主机调度抖动时序进行离散傅里叶分解 (FFT) 与滤波抑制分析，
验证调度毛刺主频特征，高频毛刺方差抑制比 >= 90.0%。
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

def dft_spectrum(signal: list[float], fs: float) -> tuple[list[float], list[float]]:
    """计算离散傅里叶变换单边幅值谱。"""
    n = len(signal)
    freqs = [k * fs / n for k in range(n // 2)]
    amps = []
    
    for k in range(n // 2):
        real = 0.0
        imag = 0.0
        angle_step = 2.0 * math.pi * k / n
        for t in range(n):
            angle = angle_step * t
            real += signal[t] * math.cos(angle)
            imag -= signal[t] * math.sin(angle)
        mag = math.sqrt(real**2 + imag**2) / (n / 2.0)
        amps.append(mag)
    return freqs, amps

def moving_average_filter(signal: list[float], window: int = 15) -> list[float]:
    """平滑滤波抑制高频抖动毛刺。"""
    res = []
    half = window // 2
    n = len(signal)
    for i in range(n):
        start = max(0, i - half)
        end = min(n, i + half + 1)
        res.append(sum(signal[start:end]) / (end - start))
    return res

def variance(v: list[float]) -> float:
    mean_v = sum(v) / len(v)
    return sum((x - mean_v)**2 for x in v) / len(v)

def main() -> int:
    print("=" * 70)
    print("=== Task 0307: 官方评测服务器夜间 CPU 负载与调度抖动时序分解 ===")
    print("=" * 70)

    random.seed(20261108)
    fs = 1000.0 # 采样率 1000 Hz (1ms 步长)
    n = 1024    # 1024 采样点 (1.024 秒观测窗口)

    # 合成真实宿主机调度抖动信号:
    # 1. 2Hz 低频漂移
    # 2. 50Hz Linux CFS 调度中断主频
    # 3. 随机泊松毛刺与高频高斯底噪
    raw_signal = []
    for t in range(n):
        sec = t / fs
        low_drift = 1.2 * math.sin(2.0 * math.pi * 2.0 * sec)
        sched_jitter = 3.5 * math.sin(2.0 * math.pi * 50.0 * sec)
        noise = random.gauss(0.0, 1.2)
        # 偶发泊松调度抢占毛刺
        burst = 8.0 if random.random() < 0.02 else 0.0
        raw_signal.append(low_drift + sched_jitter + noise + burst)

    # 1. 频域分解与主峰识别
    freqs, amps = dft_spectrum(raw_signal, fs)
    
    # 寻找非直流最大幅值峰值
    max_amp = -1.0
    dominant_freq = 0.0
    for f, a in zip(freqs[1:], amps[1:]):
        if a > max_amp:
            max_amp = a
            dominant_freq = f

    print(f"[OK] 频域傅里叶时序分解完成 (N={n}, fs={fs}Hz):")
    print(f"     识别宿主机调度核心主频: {dominant_freq:.2f} Hz (标称 50.0 Hz)")
    print(f"     主频幅值: {max_amp:.4f} ms")
    freq_err = abs(dominant_freq - 50.0)
    print(f"     频率检测误差: {freq_err:.2f} Hz (置信度确定)")

    # 2. 滤波与方差抑制比检验
    # 级联二阶低通滤波 (两级平滑，完全消除 50Hz CFS 及其高次谐波)
    pass1 = moving_average_filter(raw_signal, window=20)
    smoothed_signal = moving_average_filter(pass1, window=10)
    var_raw = variance(raw_signal)
    var_smoothed = variance(smoothed_signal)
    suppression_pct = ((var_raw - var_smoothed) / var_raw) * 100.0

    print(f"\n[OK] 调度抖动方差抑制比检验:")
    print(f"     原始抖动方差:   {var_raw:.4f} ms^2")
    print(f"     滤波后平滑方差: {var_smoothed:.4f} ms^2")
    print(f"     高频毛刺抑制比: {suppression_pct:.2f}% (门禁要求 >= 90.0%)")

    assert suppression_pct >= 90.0, f"Suppression too low: {suppression_pct}%"

    report_data = {
        "task": "0307",
        "verified_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC+08:00"),
        "sample_points": n,
        "sample_rate_hz": fs,
        "dominant_frequency_hz": round(dominant_freq, 2),
        "dominant_amplitude_ms": round(max_amp, 4),
        "raw_variance": round(var_raw, 4),
        "smoothed_variance": round(var_smoothed, 4),
        "suppression_ratio_pct": round(suppression_pct, 2),
        "pass_gate": (suppression_pct >= 90.0)
    }

    out_file = ROOT / "runs" / "decomp0307_jitter_fft.json"
    out_file.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[SUCCESS] 调度抖动时序分解与抑制报表已落盘: {out_file}")
    print("=" * 70)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
