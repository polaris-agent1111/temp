#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实测数据全维度 ANOVA 方差分解与参数敏感度分析脚本.

读取 runs/results.jsonl 中的实测记录：
1. 过滤 valid=true 的有效样本；
2. 提取 1~4.bin 控制模式、5.bin 稳态速率、6.bin 排空速率与时钟粒度；
3. 执行多因素方差分解 (ANOVA)，计算自由度 df、平方和 SS、均方 MS、F 统计量与贡献度 eta^2；
4. 输出各构型族（champ-100M-96M, champ-92M-96M, fast14, asym40-60 等）的置信区间与下确界信封。
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[2]
RESULTS_FILE = ROOT / "runs" / "results.jsonl"


def parse_pacer_cfg(cfg_str: str) -> tuple[str, dict]:
    """解析如 'token_bucket:tokens=40,burst=60...' 格式。"""
    if ":" not in cfg_str:
        return cfg_str, {}
    mode, param_part = cfg_str.split(":", 1)
    params = {}
    for item in param_part.split(","):
        if "=" in item:
            k, v = item.split("=", 1)
            try:
                params[k] = int(v)
            except ValueError:
                try:
                    params[k] = float(v)
                except ValueError:
                    params[k] = v
    return mode, params


def compute_anova(groups: list[list[float]]) -> dict:
    """单因素方差分析。"""
    k = len(groups)
    all_vals = [val for g in groups for val in g]
    N = len(all_vals)
    if N == 0 or k <= 1:
        return {"df_b": 0, "df_w": 0, "SS_b": 0.0, "SS_w": 0.0, "MS_b": 0.0, "MS_w": 0.0, "F": 0.0, "eta2": 0.0}
    
    grand_mean = np.mean(all_vals)
    SS_total = np.sum((np.array(all_vals) - grand_mean) ** 2)
    
    SS_between = sum(len(g) * ((np.mean(g) - grand_mean) ** 2) for g in groups if len(g) > 0)
    SS_within = sum(sum((x - np.mean(g)) ** 2 for x in g) for g in groups if len(g) > 0)
    
    df_between = k - 1
    df_within = N - k
    
    MS_between = SS_between / df_between if df_between > 0 else 0.0
    MS_within = SS_within / df_within if df_within > 0 else 0.0
    
    F_stat = MS_between / MS_within if MS_within > 0 else 0.0
    eta2 = SS_between / SS_total if SS_total > 0 else 0.0
    
    return {
        "k": k,
        "N": N,
        "grand_mean": float(grand_mean),
        "SS_total": float(SS_total),
        "SS_between": float(SS_between),
        "SS_within": float(SS_within),
        "df_between": df_between,
        "df_within": df_within,
        "MS_between": float(MS_between),
        "MS_within": float(MS_within),
        "F": float(F_stat),
        "eta2": float(eta2)
    }


def main() -> int:
    if not RESULTS_FILE.exists():
        print(f"File not found: {RESULTS_FILE}")
        return 1
        
    records = []
    for line in RESULTS_FILE.read_text("utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
            if r.get("valid") and "downloads" in r and "1.bin" in r["downloads"]:
                records.append(r)
        except Exception:
            continue
            
    print(f"=== ANOVA 方差分解与敏感度分析 (有效样本量 N={len(records)}) ===")
    
    # 1. 因素 A：1~4.bin 限速模式 (token_bucket vs leak_bucket vs origin)
    groups_mode = {"token_bucket": [], "leak_bucket": [], "origin": [], "other": []}
    for r in records:
        c1 = r["config"].get("1", "")
        mode1, _ = parse_pacer_cfg(c1)
        tot = r["total_seconds"]
        if mode1 in groups_mode:
            groups_mode[mode1].append(tot)
        else:
            groups_mode["other"].append(tot)
            
    valid_groups_mode = [g for g in groups_mode.values() if len(g) > 0]
    anova_mode = compute_anova(valid_groups_mode)
    print("\n【因素 A：1~4.bin 限速模式 (token_bucket / leak_bucket / origin)】")
    for k, v in groups_mode.items():
        if v:
            print(f"  - {k} (n={len(v)}): Mean={np.mean(v):.2f}s, Min={np.min(v):.2f}s, Std={np.std(v):.2f}s")
    print(f"  >> SS_b={anova_mode['SS_between']:.1f}, df_b={anova_mode['df_between']}, MS_b={anova_mode['MS_between']:.1f}")
    print(f"  >> SS_w={anova_mode['SS_within']:.1f}, df_w={anova_mode['df_within']}, MS_w={anova_mode['MS_within']:.1f}")
    print(f"  >> F-stat = {anova_mode['F']:.2f}, 贡献度 eta^2 = {anova_mode['eta2']*100:.2f}%")

    # 2. 因素 B：6.bin 时钟粒度 clock_granularity
    groups_gran = {}
    for r in records:
        c6 = r["config"].get("6", "")
        mode6, p6 = parse_pacer_cfg(c6)
        gran = p6.get("clock_granularity", 4000)
        tot = r["total_seconds"]
        groups_gran.setdefault(gran, []).append(tot)
        
    anova_gran = compute_anova(list(groups_gran.values()))
    print("\n【因素 B：6.bin 时钟粒度 clock_granularity】")
    for k in sorted(groups_gran.keys()):
        v = groups_gran[k]
        print(f"  - gran={k}µs (n={len(v)}): Mean={np.mean(v):.2f}s, Min={np.min(v):.2f}s, Std={np.std(v):.2f}s")
    print(f"  >> F-stat = {anova_gran['F']:.2f}, 贡献度 eta^2 = {anova_gran['eta2']*100:.2f}%")

    # 3. 统计各文件历史单项最优与下确界信封
    min_files = {f"{i}.bin": (999.0, "") for i in range(1, 7)}
    for r in records:
        tag = r["tag"]
        dls = r["downloads"]
        for k, v in dls.items():
            if k in min_files and v < min_files[k][0]:
                min_files[k] = (v, tag)
                
    print("\n=== 分文件历史单项最低耗时与极值信封 ===")
    env_sum = 0.0
    for k in sorted(min_files.keys()):
        val, tag = min_files[k]
        env_sum += val
        print(f"  - {k}: {val:.4f}s ({tag})")
    print(f"  ★ 全局理论下确界极限信封 (Lower Envelope): {env_sum:.4f}s")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
