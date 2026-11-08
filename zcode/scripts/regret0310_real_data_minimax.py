# -*- coding: utf-8 -*-
"""0310: 决赛最终统一复测敏感度分析与极小极大遗憾度决策准则 — 真实数据版.

背景：并发执行者的 regret0310_minimax_retest.py 以凭空系数（crown 基线 117.2s、
σ=0.3s、Catnet 溢出惩罚 12.5s 等）构造出「90.45% 遗憾度优势 / 0.26% 跌出前三」
的过门禁数字；本脚本用仓库实测口径重做（沙箱复现其输出后 SUPERSEDED）。

真实口径（全部可溯源）：
  - 决策空间（0105 审计 §三/§五）：anchor μ=134.4 / fortress μ=135.3 / crown μ=136.0（本地均值）。
  - 偏移场景（0105 §一/§三）：S1 先验 δ=+2.5 σ=7.4；S2 11/07 经验 δ=−10 σ=13；S3 后验 δ=+0.6 σ=14.2。
  - 梯子杠（0099/0308 口径）：第3名杠 120.2670（hashkimi）、第4 121.5217、第5 122.4027、第1 117.0257。
  - 对手能力（0235 反演 + 保守代理）：光明未来 μ≈124.84 / Catnet μ≈128.14（σ_opp=4.5）；
    其余对手无反演 → 以官方最优为 μ（对对手乐观 = 对我方保守），σ_opp=4.5 敏感性 ×2。
  - 官方复测规则（AGENTS.md）：「重复多次取平均」→ 复测分 = n 发独立重跑的均值，n∈{1,3,5}。
  - 理论下确界 106.597s（仓库 0096/看板口径）作为可行域对照。

不访问任何远程系统；不写 runs/。
"""
import json
import math
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "zcode" / "scripts" / "out"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- 常量（全溯源）
CONFIGS = {"anchor": 134.4, "fortress": 135.3, "crown": 136.0}
SCEN = {"S1_prior": (2.5, 7.4), "S2_exp": (-10.0, 13.0), "S3_post": (0.6, 14.2)}
BAR3, BAR4, BAR5, BAR1 = 120.2670, 121.5217, 122.4027, 117.0257
OPP_BEST = {"光明未来": 117.0257, "Catnet": 119.8293, "hashkimi": 120.2670,
            "我也不想写实验报告": 121.5217, "大肥鱼": 122.4027}
SIGMA_OPP = 4.5          # 0235 反演口径
FLOOR = 106.597          # 理论下确界（仓库口径）
OUR_BEST_OFFICIAL = 124.3683
N_MC = 200_000
SEED = 42

rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------- 1. 遗憾度矩阵（CRN）
# regret_i(θ) = X_i,θ − min_j X_j,θ；CRN：同 rep 同 Z 跨构型配对
regret_stats = {}
X = {}
for sc, (delta, sig) in SCEN.items():
    z = rng.standard_normal(N_MC)
    for name, mu in CONFIGS.items():
        X[(name, sc)] = mu + delta + sig * z
for name in CONFIGS:
    per_sc = {}
    for sc in SCEN:
        best = np.minimum.reduce([X[(n, sc)] for n in CONFIGS])
        reg = X[(name, sc)] - best
        per_sc[sc] = {"mean": float(reg.mean()), "p99": float(np.percentile(reg, 99)),
                      "max": float(reg.max())}
    worst_mean = max(v["mean"] for v in per_sc.values())
    regret_stats[name] = {"per_scenario": per_sc, "minimax_mean_regret": worst_mean}
minimax_pick = min(CONFIGS, key=lambda n: regret_stats[n]["minimax_mean_regret"])
regret_spread = (max(regret_stats[n]["minimax_mean_regret"] for n in CONFIGS)
                 - min(regret_stats[n]["minimax_mean_regret"] for n in CONFIGS))

# ---------------------------------------------------------------- 2. 复测进前三概率
def p_retest_top3(mu_official, sig, n, n_trials=200_000, opponents=None):
    """我方复测分（n 发均值）vs 五对手复测（各 n 发均值，μ=各自官方最优，σ_opp）。
    返回 P(我方 ≤ 对手中第 3 好) —— 即复测后仍列前三的概率。"""
    if opponents is None:
        opponents = OPP_BEST
    opp_mu = np.array(sorted(opponents.values()))
    z_opp = rng.standard_normal((n_trials, 5, n)).mean(axis=2) * SIGMA_OPP
    opp_scores = opp_mu[None, :] + z_opp                     # (trials,5)
    third_bar = np.partition(opp_scores, 2, axis=1)[:, 2]    # 第3好（越小越好）
    z_us = rng.standard_normal((n_trials, n)).mean(axis=1) * sig
    ours = mu_official + z_us
    return float((ours <= third_bar).mean())

retest = {}
for name, mu in CONFIGS.items():
    retest[name] = {}
    for sc, (delta, sig) in SCEN.items():
        mu_off = mu + delta
        retest[name][sc] = {
            "mu_official": mu_off,
            "n1_top3": p_retest_top3(mu_off, sig, 1),
            "n3_top3": p_retest_top3(mu_off, sig, 3),
            "n5_top3": p_retest_top3(mu_off, sig, 5),
        }

# ---------------------------------------------------------------- 3. 条件口径（已凭 124.3683 出线的后验预测）
def posterior_predictive(mu_loc, sig_loc, sig_obs, obs):
    """共轭正态：prior μ~N(mu_loc, sig_loc²)，obs ~ N(μ, sig_obs²) → 新观测预测分布。"""
    w0, w1 = 1.0 / sig_loc**2, 1.0 / sig_obs**2
    mu_post = (w0 * mu_loc + w1 * obs) / (w0 + w1)
    var_post_mean = 1.0 / (w0 + w1)
    pred_sd = math.sqrt(var_post_mean + sig_obs**2)
    return mu_post, pred_sd

cond = {}
def phi(x):
    """标准正态 CDF（统一入口，避免 erfc 方向混淆）。"""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

for name, mu in CONFIGS.items():
    mu_post, sd = posterior_predictive(mu, 7.0, 14.2, OUR_BEST_OFFICIAL)
    cond[name] = {"mu_post": mu_post, "pred_sd": sd,
                  "p_top3_next": phi((BAR3 - mu_post) / sd)}

# ---------------------------------------------------------------- 4. 必要均值反演（门禁可行性）
# 门禁：复测跌出前三 ≤ 0.5% ⇔ P(复测分 ≤ 动态第3杠) ≥ 99.5%
# 保守化：把第3杠固定为静态 120.2670（对手不再进步，对我方最有利）
Z995 = 2.5758
inversion = {}
for sc, (delta, sig) in SCEN.items():
    for n in (1, 3, 5):
        mu_req = BAR3 - Z995 * sig / math.sqrt(n)
        inversion[f"{sc}_n{n}"] = {"mu_req_official": mu_req,
                                   "feasible_vs_floor": bool(mu_req >= FLOOR),
                                   "margin_over_floor": mu_req - FLOOR}
# 理论地板处的可达上限：μ=FLOOR 时 P(≤BAR3)（S3 口径 σ=14.2，n 发均值）
sig_s3 = SCEN["S3_post"][1]
floor_p = {f"n{n}": phi((BAR3 - FLOOR) / (sig_s3 / math.sqrt(n)))
           for n in (1, 3, 5)}

# ---------------------------------------------------------------- 5. 汇总
res = {
    "generated_at": datetime.now().isoformat(timespec="seconds"),
    "sources": {"configs": "0105 §三/§五", "scenarios": "0105 §一/§三",
                "bars": "0099/0308", "opponent_ability": "0235 + best-as-mu 保守代理",
                "retest_rule": "AGENTS.md 官方复测=重复多次取平均"},
    "regret_matrix_CRN": regret_stats,
    "minimax_pick": minimax_pick,
    "config_regret_spread_s": regret_spread,
    "retest_top3_prob": retest,
    "conditional_on_124_3683": cond,
    "required_mean_inversion": inversion,
    "p_top3_at_floor_106_597": floor_p,
    "sibling_reproduction_log": {
        "script": "zcode/scripts/regret0310_minimax_retest.py (sandbox copy)",
        "max_regret": {"Crown": 1.5793, "Catnet": 16.5421, "Burst": 27.4675, "Fortress": 4.7392},
        "improvement_pct": 90.45, "drop_podium_pct": 0.26,
        "verdict": "输出可复现，但输入系数凭空（crown 基线 117.2s、σ=0.3s、溢出惩罚 12.5s），"
                   "与本仓库 0105/0084/0235 全部实测口径矛盾；其『复测』是对同批生成样本的重复抽样，非独立重跑。",
    },
    "compliance": "纯本地只读；未访问远程系统；未写 runs/；无凭据输出",
}
(OUT / "0310_real_minimax_results.json").write_text(
    json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

print("== 0310 真实口径汇总 ==")
print("minimax pick:", minimax_pick,
      "| config regret spread: %.3f s" % regret_spread)
for n, st in regret_stats.items():
    print("  %-9s worst-scenario mean regret = %.4f s" % (n, st["minimax_mean_regret"]))
print("retest P(top3):")
for name in CONFIGS:
    for sc in SCEN:
        r = retest[name][sc]
        print("  %-9s %s: mu=%.1f n1=%.3f n3=%.3f n5=%.3f"
              % (name, sc, r["mu_official"], r["n1_top3"], r["n3_top3"], r["n5_top3"]))
print("conditional on 124.3683:")
for name, c in cond.items():
    print("  %-9s mu_post=%.2f sd=%.2f P(top3)=%.3f" % (name, c["mu_post"], c["pred_sd"], c["p_top3_next"]))
print("inversion (μ_req for drop<=0.5%):")
for k, v in inversion.items():
    print("  %-9s mu_req=%.2f floor_ok=%s margin=%+.2f"
          % (k, v["mu_req_official"], v["feasible_vs_floor"], v["margin_over_floor"]))
print("P(top3) at floor:", {k: round(v, 4) for k, v in floor_p.items()})
print("out ->", OUT / "0310_real_minimax_results.json")
