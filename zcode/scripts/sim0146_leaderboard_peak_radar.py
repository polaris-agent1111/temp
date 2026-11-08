#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0146: Leaderboard Peak Radar and Retest Monte Carlo Simulation.
Evaluates official leaderboard top competitors vs our 11/08 sequential adaptive strategy
under both best-of-N leaderboard standing and official multi-run retest conditions.
"""
import numpy as np

def run_simulation(n_trials=100000, seed=42):
    rng = np.random.default_rng(seed)

    # Competitor parameters estimated from order statistics & local calibration
    # 光明未来 (15 submissions, best 117.0257) -> est true mean=135.2, std=12.5
    # Catnet (22 submissions, best 119.8293) -> est true mean=142.5, std=16.8
    # 大肥鱼 (20 submissions, best 122.4027) -> est true mean=140.2, std=14.5
    # 我也不想写实验报告 (8 submissions, best 121.5217) -> est true mean=138.5, std=13.0
    
    # Our candidates (11/08):
    # Steady Champion: mean=133.86, std=8.37
    # Crown Fusion: mean=132.21, std=7.89
    # Plateau A: mean=135.85, std=8.63
    # Fortress: mean=136.20, std=5.41

    # Official calibration offset: local mean - 11.52s = official expected mean
    cal_offset = 11.52

    our_steady_mean = 133.86 - cal_offset
    our_steady_std = 8.37
    our_crown_mean = 132.21 - cal_offset
    our_crown_std = 7.89

    catnet_retest_mean = 142.5 - cal_offset
    catnet_retest_std = 16.8
    gm_retest_mean = 135.2 - cal_offset
    gm_retest_std = 12.5

    # 1. Official Final Retest Simulation (Official Rule 7: average of N=10 retests)
    retest_n = 10
    catnet_retest_scores = rng.normal(catnet_retest_mean, catnet_retest_std / np.sqrt(retest_n), n_trials)
    gm_retest_scores = rng.normal(gm_retest_mean, gm_retest_std / np.sqrt(retest_n), n_trials)
    our_crown_retest = rng.normal(our_crown_mean, our_crown_std / np.sqrt(retest_n), n_trials)
    our_steady_retest = rng.normal(our_steady_mean, our_steady_std / np.sqrt(retest_n), n_trials)

    our_best_retest = np.minimum(our_crown_retest, our_steady_retest)

    win_vs_catnet_retest = np.mean(our_best_retest < catnet_retest_scores)
    win_vs_gm_retest = np.mean(our_best_retest < gm_retest_scores)
    rank1_retest = np.mean((our_best_retest < catnet_retest_scores) & (our_best_retest < gm_retest_scores))

    # 2. Daily Leaderboard Best-of-5 Simulation (11/08 dynamic 5-shot campaign)
    # Shot 1: Steady Champion
    s1 = rng.normal(our_steady_mean, our_steady_std, n_trials)
    # Adaptive branch:
    # if s1 <= 122.5 - cal_offset: shoot Crown Fusion (aggressive)
    # else if s1 <= 125.0 - cal_offset: shoot Crown Fusion & Plateau A
    # else: shoot Fortress
    s2 = np.where(s1 <= 122.5 - cal_offset,
                  rng.normal(our_crown_mean, our_crown_std, n_trials),
                  rng.normal(our_steady_mean, our_steady_std, n_trials))
    s3 = rng.normal(our_crown_mean, our_crown_std, n_trials)
    s4 = rng.normal(our_crown_mean, our_crown_std, n_trials)
    s5 = rng.normal(our_crown_mean, our_crown_std, n_trials)

    our_daily_best = np.minimum.reduce([s1, s2, s3, s4, s5])

    # Probability of beating GM's current record (117.0257s)
    beat_gm_record = np.mean(our_daily_best < 117.0257)
    beat_catnet_record = np.mean(our_daily_best < 119.8293)
    beat_our_record = np.mean(our_daily_best < 124.3683)

    results = {
        "n_trials": n_trials,
        "retest_win_vs_catnet": float(win_vs_catnet_retest),
        "retest_win_vs_gm": float(win_vs_gm_retest),
        "retest_rank1_prob": float(rank1_retest),
        "daily_best_mean": float(np.mean(our_daily_best)),
        "daily_best_median": float(np.median(our_daily_best)),
        "daily_best_min": float(np.min(our_daily_best)),
        "daily_best_p10": float(np.percentile(our_daily_best, 10)),
        "beat_gm_record_prob": float(beat_gm_record),
        "beat_catnet_record_prob": float(beat_catnet_record),
        "beat_our_record_prob": float(beat_our_record),
    }
    return results

if __name__ == "__main__":
    res = run_simulation()
    print("=== Simulation Results ===")
    for k, v in res.items():
        if isinstance(v, float):
            print(f"{k}: {v:.4f}")
        else:
            print(f"{k}: {v}")
