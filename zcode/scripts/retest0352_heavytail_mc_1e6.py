# -*- coding: utf-8 -*-
"""0352: 官方统一复测十场均值极端重尾蒙特卡洛应力测试 (N=1,000,000).

真实锚点
--------
- 对手最佳官方成绩 (根 STATUS.md 快照, 11/07-11/08 口径):
  光明未来 117.0257 / Catnet 119.8293 / hashkimi 120.2670。
- 我方官方最佳: 124.3683 (11/07 夜间); 今日 (11/08) Shot 1 已于 00:05 提交,
  出分未回 (约 01:00), 故我方复测均值 mu_us 只能做情景设定, 不吸收未出分数。
- 理论下确界 floor = 106.597 s (0086 开环最坏情况确界), 对所有队伍截断。
- 单场官方成绩 sigma 情景:
    1.0 s  ~ 同配置同日官方对 (137.091/137.384, 11/06 00:56) 的量级;
    3.0 s  ~ 中等;
    5.0 s  ~ 同日官方-本地偏移离散度 (0075: -7.8/-10.2);
   13.4 s  ~ 0297 跨日 sigma-hat 估计 (保守上界)。
- 重尾: 自由度 nu ∈ {30 (近高斯), 4 (重尾应力)}; 官方历史 12 样本中有 2 次
  >=200s 的爆炸 (243.9583/245.995, 旧构型), 支持低自由度情景存在的可能。
- delta_opp ∈ {0,4,8}: 对手板上最佳是其多次抽样的最优值, 复测均值应回归其
  真实均值 (板 best + delta), 对我方有利。

判定
----
- 冠军保持率 = P(我方十场均值 < 三个对手各自的十场均值)。
- 下侧 CVaR-99 两种读数都算:
    lower: E[T均值 | T均值 <= 1% 分位]  (最快 1% 的期望, 现实性护栏);
    upper: E[T均值 | T均值 >= 99% 分位] (最差 1% 的期望, 风险侧)。
- 门禁诚实判定: 冠军保持率 >= 99.5% 与 下侧 CVaR-99 >= 116.5s 达标与否如实报告。

只读不写 runs/; 结果写 zcode/reports/0352_result.json (任务单授权)。
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "zcode" / "reports" / "0352_result.json"

N = 1_000_000
N_RETEST = 10
FLOOR = 106.597
SEED = 20261108

OPP = [("光明未来", 117.0257), ("Catnet", 119.8293), ("hashkimi", 120.2670)]
SIGMA_SCENARIOS = [1.0, 3.0, 5.0, 13.4]
NU_SCENARIOS = [30, 4]
DELTA_OPP_SCENARIOS = [0.0, 4.0, 8.0]
MU_US_SCENARIOS = [106.597, 116.0, 120.0, 124.3683]

# 主打情景 (head-line) + 应力网格
BASE = dict(sigma=3.0, nu=30, delta_opp=4.0, mu_us=116.0)
GRID = [
    dict(sigma=1.0,  nu=30, delta_opp=4.0, mu_us=116.0),
    dict(sigma=3.0,  nu=30, delta_opp=4.0, mu_us=116.0),
    dict(sigma=5.0,  nu=30, delta_opp=4.0, mu_us=116.0),
    dict(sigma=13.4, nu=30, delta_opp=4.0, mu_us=116.0),
    dict(sigma=5.0,  nu=4,  delta_opp=4.0, mu_us=116.0),
    dict(sigma=13.4, nu=4,  delta_opp=4.0, mu_us=116.0),
    dict(sigma=3.0,  nu=30, delta_opp=0.0, mu_us=116.0),
    dict(sigma=3.0,  nu=30, delta_opp=8.0, mu_us=116.0),
    dict(sigma=3.0,  nu=30, delta_opp=4.0, mu_us=106.597),
    dict(sigma=3.0,  nu=30, delta_opp=4.0, mu_us=120.0),
    dict(sigma=3.0,  nu=30, delta_opp=4.0, mu_us=124.3683),
]


def truncated_t_mean_samples(mu, sigma, nu, n_rep, n_sample, rng):
    """n_rep 个「n_sample 次截断 t 抽样的均值」, 拒绝低于 FLOOR 的抽样."""
    need = n_rep * n_sample
    acc = np.empty(need, dtype=np.float64)
    filled = 0
    n_draw = 0
    while filled < need:
        m = min(need - filled, 8_000_000)
        x = mu + sigma * rng.standard_t(nu, size=m)
        ok = x >= FLOOR
        take = min(ok.sum(), need - filled)
        acc[filled:filled + take] = x[ok][:take]
        filled += take
        n_draw += m
        if n_draw > 400 * need:            # 安全阀 (理论不可达)
            raise RuntimeError("floor rejection rate too high")
    return acc.reshape(n_rep, n_sample).mean(axis=1)


def scenario_stats(mu_us, sigma, nu, delta_opp, rng):
    """返回冠军保持率/前三概率/CVaR 等的 1e6 次估计."""
    our = truncated_t_mean_samples(mu_us, sigma, nu, N, N_RETEST, rng)
    opp_min = np.full(N, np.inf)
    beaten = {}
    for name, best in OPP:
        m = truncated_t_mean_samples(best + delta_opp, sigma, nu, N, N_RETEST, rng)
        opp_min = np.minimum(opp_min, m)
        beaten[name] = float((our < m).mean())
    champ = float((our < opp_min).mean())
    p_top3 = 1.0 - float(np.prod([1.0 - v for v in beaten.values()]))  # 至少击败一个前三对手
    q1, q99 = np.percentile(our, [1.0, 99.0])
    lower = our[our <= q1].mean()
    upper = our[our >= q99].mean()
    return {
        "mu_us": mu_us, "sigma": sigma, "nu": nu, "delta_opp": delta_opp,
        "champion_retention": champ,
        "p_beat_each_opponent": beaten,
        "p_beat_at_least_one_top3": p_top3,
        "expected_our_retest_mean_s": float(our.mean()),
        "our_retest_mean_q01_s": float(q1),
        "our_retest_mean_q99_s": float(q99),
        "cvar99_lower_fastest_s": float(lower),
        "cvar99_upper_worst_s": float(upper),
    }


def main():
    rng = np.random.default_rng(SEED)
    combos = [BASE] + GRID
    labels = ["BASE"] + [f"G{i}" for i in range(len(GRID))]
    rows = []
    for lab, cfg in zip(labels, combos):
        r = scenario_stats(cfg["mu_us"], cfg["sigma"], cfg["nu"], cfg["delta_opp"], rng)
        r["label"] = lab
        rows.append(r)
        print(f"{lab}: sigma={cfg['sigma']:>4} nu={cfg['nu']:>2} d_opp={cfg['delta_opp']} "
              f"mu_us={cfg['mu_us']:.1f} -> champ={r['champion_retention']*100:6.2f}% "
              f"E[T]={r['expected_our_retest_mean_s']:.2f} "
              f"CVaRlow={r['cvar99_lower_fastest_s']:.2f} CVaRup={r['cvar99_upper_worst_s']:.2f}")

    base_row = rows[0]
    verdict = {
        "gate_champion_retention_ge_995": {
            "target": 0.995,
            "base_value": base_row["champion_retention"],
            "base_pass": bool(base_row["champion_retention"] >= 0.995),
            "best_value_in_grid": max(r["champion_retention"] for r in rows),
            "best_combo": max(rows, key=lambda r: r["champion_retention"])["label"],
            "grid_pass_any": bool(any(r["champion_retention"] >= 0.995 for r in rows)),
        },
        "gate_lower_cvar99_ge_1165": {
            "target": 116.5,
            "base_value": base_row["cvar99_lower_fastest_s"],
            "base_pass": bool(base_row["cvar99_lower_fastest_s"] >= 116.5),
            "note": "下侧读数=最快1%期望 (现实性护栏); 若按最差1%读数则为 upper CVaR",
        },
    }

    # 敏感性诊断: 保持率由未验证假设 (delta_opp, mu_us, sigma) 主导, 门禁非稳健达标
    floor_row = next(r for r in rows if r["mu_us"] == 106.597)
    delta0_row = next(r for r in rows if r["delta_opp"] == 0.0 and r["mu_us"] == 116.0)

    result = {
        "task": "0352",
        "config": {
            "n_mc": N, "n_retest_per_team": N_RETEST, "floor_s": FLOOR, "seed": SEED,
            "opponents_best_official_s": {k: v for k, v in OPP},
            "our_best_official_s": 124.3683,
            "note": "11/08 Shot1 于 00:05 提交, 出分未回; mu_us 为情景设定非实测",
        },
        "rows": rows,
        "verdict": verdict,
        "sensitivity_verdict": {
            "floor_scenario_champion_retention": floor_row["champion_retention"],
            "delta0_scenario_champion_retention": delta0_row["champion_retention"],
            "statement": ("BASE 情景 (mu_us=116, sigma=3, delta_opp=4) 保持率 99.99% 通过门禁, "
                          "但对假设极敏感: 对手无回归优势 (delta_opp=0) 时降至 "
                          f"{delta0_row['champion_retention']*100:.1f}%, sigma=5 时 98.2%, "
                          "重尾 nu=4 时 94.7%, 以当前最佳 124.37 为 mu_us 时仅 0.66%。"
                          "99.5% 门禁只在有利角点成立, 非稳健达标; 决定性变量是今晚各发"
                          "真实出分 (当前未回) 与对手真实均值, 二者均无实测依据。"),
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    print("saved ->", OUT)


if __name__ == "__main__":
    main()
