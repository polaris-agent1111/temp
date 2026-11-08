# -*- coding: utf-8 -*-
"""
Task 0326: Shot 3 出分成绩吸收与前三名位次敏感度分析
评估吸收第 3 发出分后全国前三名 (Top 3) 的锁定概率与边界位次弹性
"""
import sys
import json
import numpy as np
import datetime

def main():
    print("=" * 70)
    print("=== Task 0326: Shot 3 出分成绩吸收与前三名位次敏感度分析 ===")
    print("=" * 70)

    np.random.seed(326)
    n_sims = 100000

    # 官方基准线
    t_podium = 120.2670 # hashkimi 稳坐第 3 名阈值
    t_catnet = 119.8293 # Catnet 第 2 名

    # 前三发联合分布 (Shot 1 ~ 3)
    s1 = np.random.normal(loc=116.90, scale=0.85, size=n_sims)
    s2 = np.random.normal(loc=116.30, scale=0.75, size=n_sims)
    s3 = np.random.normal(loc=115.95, scale=0.65, size=n_sims)
    our_3shot_best = np.minimum.reduce([s1, s2, s3])

    # 1. 计算稳固前三名概率
    p_podium = float(np.mean(our_3shot_best < t_podium))
    p_top2 = float(np.mean(our_3shot_best < t_catnet))

    # 2. 位次弹性分析 (位次对基准线扰动的敏感性)
    # 模拟外部竞争对手成绩波动 delta = +/- 1.0 s
    delta_t = 0.50 # 秒
    p_podium_plus = float(np.mean(our_3shot_best < (t_podium + delta_t)))
    p_podium_minus = float(np.mean(our_3shot_best < (t_podium - delta_t)))

    # 弹性系数 E = (delta_P / P) / (delta_T / T)
    rel_change_p = (p_podium_plus - p_podium_minus) / p_podium
    rel_change_t = (2.0 * delta_t) / t_podium
    elasticity = float(rel_change_p / rel_change_t)

    print(f"[OK] 前三发联合出分与敏感度蒙特卡洛仿真完成 (N={n_sims:,}):")
    print(f"     前 3 发最优成绩期望:      {float(np.mean(our_3shot_best)):.4f} s")
    print(f"     锁定全国前三名概率:        {p_podium*100:.2f}% (门禁指标 >= 99.0%)")
    print(f"     锁定全国前二名概率:        {p_top2*100:.2f}%")
    print(f"     位次弹性系数 |E|:          {abs(elasticity):.4f} (门禁指标 <= 0.20)")

    pass_gate = bool(p_podium >= 0.99 and abs(elasticity) <= 0.20)
    print(f"[GATE] 门禁达成: {pass_gate}")

    report = {
        "task": "0326",
        "verified_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC+08:00"),
        "best_mean_3shots_s": round(float(np.mean(our_3shot_best)), 4),
        "p_podium": round(p_podium, 4),
        "p_top2": round(p_top2, 4),
        "elasticity": round(elasticity, 4),
        "pass_gate": pass_gate
    }

    out_file = r"e:\Download\iDSN\runs\sens0326_podium_elasticity.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"[SUCCESS] 领奖台弹性审计数据已落盘: {out_file}")
    print("=" * 70)

if __name__ == "__main__":
    main()
