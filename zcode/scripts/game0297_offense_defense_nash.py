# -*- coding: utf-8 -*-
"""
game0297_offense_defense_nash.py — 任务 0297 验证脚本 (v2)
Shot 3 进攻/防守动态权重博弈分配：2×2 零和纳什均衡 + 官方噪声分解双模型 + δ 扫描

模型:
  我方动作  OFF = crown-pert(41,40,40,37,36,36)  本地 n=10, mean 135.85, σ 8.63（0105 §二）
            DEF = fortress(40x4,37,37)           本地 n=10, mean 134.74, σ 5.41（0105 §二）
  出分      X = local_draw + δ；local_draw ~ N(μ_local, σ_local)；δ ~ N(μ_δ, δ_noise)
  模型A(0105口径)  σ_local=0, δ_noise=场景σ（S1 7.4 / S2 13.0 / S3 14.2）——本地方差被吸收
  模型B(加性拆分)  σ_local 取各构型实测值，δ_noise 为自由参数；实测锚点:
                   asym-fast14 同构型官方对 [140.0247,155.1607] → σ̂_off=15.14/1.128=13.42
                   fast14 族本地 n=9: mean 141.31, σ 7.32（runs/results.jsonl, 'fast14' 片段）
                   → δ̂ = sqrt(13.42² − 7.32²) = 11.25（n=2 官方样本, 方差估计极不精确, 仅作点估计）
  对手状态  STAY / PUSH（各队最优下降 Δ~TruncN(5.99,3.05,[0.5,15]), 近平台期实证 n=5）
            过夜改进率 q̂ = 8/9 = 0.889（快照逐发历史）
  效用      U = E[排名积分] − λ·σ_tot/√3（复测回撤厌恶）；积分 {1:100,2:85,3:70,4:50,5:35,6:25,≥7:10}
  均衡      von Neumann 2×2 零和（对手对抗式）+ q̂ 加权贝叶斯期望（非对抗式）双读法

只读输入: intel/raw/leaderboard_20261106T1515.json, runs/results.jsonl, runs/sequential_adaptive_log.jsonl
输出:     zcode/scripts/out/0297_nash_weights.json
"""
import json
import math
import os
import statistics
import sys
from collections import defaultdict
from datetime import datetime

import numpy as np
from scipy.stats import truncnorm

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(ROOT, "zcode", "scripts", "out")
os.makedirs(OUT_DIR, exist_ok=True)

RNG = np.random.default_rng(20261107)
N_MC = 200_000

# ---------------------------------------------------------------- 实证锚点
# 1) 对手动态（快照逐发历史）
snap = json.load(open(os.path.join(ROOT, "intel", "raw", "leaderboard_20261106T1515.json"),
                      encoding="utf-8"))
LEADER_BAND = ["光明未来", "Catnet", "hashkimi", "我不想写实验报告", "大肥鱼"]
improvements, team_days, improved_days = [], 0, 0
for entry in snap["leaderboard"]["problems"][0]["submissions"]:
    team = entry["team"]
    if team not in LEADER_BAND:
        continue
    by_date = defaultdict(list)
    for a in entry["attempts"]:
        by_date[a["submitted_at"][:10]].append(float(a["download_seconds"]))
    best_so_far = None
    for d in sorted(by_date):
        day_best = min(by_date[d])
        if best_so_far is not None:
            team_days += 1
            if day_best < best_so_far - 0.5:
                improved_days += 1
                improvements.append({"team": team, "date": d, "from": round(best_so_far, 4),
                                     "to": round(day_best, 4), "delta": round(best_so_far - day_best, 4)})
        best_so_far = day_best if best_so_far is None else min(best_so_far, day_best)
q_hat = improved_days / team_days
late_deltas = [r["delta"] for r in improvements if r["from"] <= 135.0]
push_mu = float(np.mean(late_deltas))
push_sigma = float(np.std(late_deltas, ddof=1))

# 2) fast14 族本地统计（官方同构型对的本地对应族）
res_rows = [json.loads(l) for l in open(os.path.join(ROOT, "runs", "results.jsonl"),
                                        encoding="utf-8") if l.strip()]
fast14 = [r["total_seconds"] for r in res_rows if r.get("valid", True) and "fast14" in r.get("tag", "")]
fast14_mean = statistics.mean(fast14)
fast14_sigma = statistics.stdev(fast14)

# 3) 官方同构型对（11/07 夜间 Shot4/Shot5, sequential_adaptive_log）
OFFICIAL_PAIR = [140.0247, 155.1607]
sigma_off_meas = (max(OFFICIAL_PAIR) - min(OFFICIAL_PAIR)) / 1.128   # n=2 极差期望 = 1.128σ
delta_hat = math.sqrt(max(0.0, sigma_off_meas ** 2 - fast14_sigma ** 2))

# ---------------------------------------------------------------- 博弈参数
ACTIONS = {
    "OFF(crown-pert)": {"mean": 135.85, "sigma_local": 8.63},
    "OFF2(champ1107)": {"mean": 134.53, "sigma_local": 13.51},   # 实际产出 124.3683 的族; HIGH_CV 10.0% 贴线
    "DEF(fortress)":   {"mean": 134.74, "sigma_local": 5.41},
}
OFFENSE_ARMS = ["OFF(crown-pert)", "OFF2(champ1107)"]
SCENARIOS = {
    "S1_prior(+2.5,7.4)":     {"mu": 2.5, "sigma": 7.4},
    "S2_1107exp(-10,13)":     {"mu": -10.0, "sigma": 13.0},
    "S3_posterior(+0.6,14.2)": {"mu": 0.6, "sigma": 14.2},
}
POINTS = {1: 100, 2: 85, 3: 70, 4: 50, 5: 35, 6: 25}
OPP_STAY = [117.0257, 119.8293, 120.2670, 121.5217, 122.4027]
OUR_PRE_BEST = 124.3683
RETEST_M = 3
PUSH_A, PUSH_B = 0.5, 15.0


def expected_utility(action, push, mu_delta, delta_noise, sigma_local,
                     pre_best=OUR_PRE_BEST, lam=0.0, n=N_MC):
    a = ACTIONS[action]
    sl = a["sigma_local"] if sigma_local else 0.0
    x = a["mean"] + RNG.normal(0, sl, size=n) + RNG.normal(mu_delta, delta_noise, size=n)
    final_best = np.minimum(pre_best, x)
    opp = np.array(OPP_STAY, dtype=float)
    if push:
        a_, b_ = (PUSH_A - push_mu) / push_sigma, (PUSH_B - push_mu) / push_sigma
        deltas = truncnorm.rvs(a_, b_, loc=push_mu, scale=push_sigma,
                               size=(n, len(OPP_STAY)), random_state=RNG)
        opp = opp[None, :] - deltas
    rank = 1 + (opp < final_best[:, None]).sum(axis=1)
    pts = np.vectorize(lambda r: POINTS.get(r, 10))(rank)
    sigma_tot = math.sqrt(sl ** 2 + delta_noise ** 2)
    return float(pts.mean()) - lam * sigma_tot / math.sqrt(RETEST_M)


def solve_2x2(M):
    M = np.asarray(M, float)
    row_min, col_max = M.min(axis=1), M.max(axis=0)
    maximin, minimax = row_min.max(), col_max.min()
    if maximin == minimax:
        return float(row_min.argmax() == 0), float(col_max.argmin() == 0), float(maximin), "pure_saddle"
    a, b, c, d = M[0, 0], M[0, 1], M[1, 0], M[1, 1]
    den = (a - c) - (b - d)
    p_star = (d - c) / den
    V = p_star * a + (1 - p_star) * c
    return float(np.clip(p_star, 0, 1)), float(np.clip((b - d) / den, 0, 1)), float(V), "mixed"


def bayes_u(action, mu_delta, delta_noise, sigma_local, lam=0.0, pre_best=OUR_PRE_BEST):
    us = [expected_utility(action, push, mu_delta, delta_noise, sigma_local, pre_best, lam)
          for push in (False, True)]
    return (1 - q_hat) * us[0] + q_hat * us[1]


results = {
    "task": "0297 Shot 3 进攻/防守动态权重博弈分配",
    "executed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "empirical_anchors": {
        "q_hat_push_prob": round(q_hat, 4), "team_days": team_days, "improved": improved_days,
        "push_mu": round(push_mu, 3), "push_sigma": round(push_sigma, 3),
        "improvement_log": improvements,
        "fast14_local": {"n": len(fast14), "mean": round(fast14_mean, 2),
                         "sigma": round(fast14_sigma, 2)},
        "official_pair": OFFICIAL_PAIR,
        "sigma_off_meas_n2": round(sigma_off_meas, 3),
        "delta_hat": round(delta_hat, 3),
        "caveat": "n=2 官方样本的 σ 估计置信区间极宽（χ²），δ̂ 仅作点估计用于模型示范",
    },
}

# ---------------------------------------------------------------- 模型A（0105 口径: σ_local=0, δ=场景σ）
model_a = {}
for sc_name, sc in SCENARIOS.items():
    for arm in OFFENSE_ARMS:
        M = [[expected_utility(act, push, sc["mu"], sc["sigma"], sigma_local=False)
              for push in (False, True)] for act in (arm, "DEF(fortress)")]
        p_star, q_star, V, kind = solve_2x2(M)
        u_def_pure = min(M[1])
        gain = (V - u_def_pure) / u_def_pure * 100
        model_a[f"{sc_name}|{arm}"] = {"M": [[round(v, 3) for v in row] for row in M],
                                       "p_star_off": round(p_star, 4), "V": round(V, 3), "kind": kind,
                                       "gain_vs_pureDEF_pct": round(gain, 2)}
results["model_A_0105_common_noise"] = model_a

# ---------------------------------------------------------------- 模型B（加性拆分, S3 μδ, δ 扫描）
s3_mu = SCENARIOS["S3_posterior(+0.6,14.2)"]["mu"]
sweep = {arm: [] for arm in OFFENSE_ARMS}
delta_star = {arm: None for arm in OFFENSE_ARMS}
for arm in OFFENSE_ARMS:
    for d in np.arange(0, 15.01, 0.5):
        u_off = bayes_u(arm, s3_mu, d, sigma_local=True)
        u_def = bayes_u("DEF(fortress)", s3_mu, d, sigma_local=True)
        sweep[arm].append({"delta": round(float(d), 2), "U_OFF": round(u_off, 3),
                           "U_DEF": round(u_def, 3), "diff": round(u_off - u_def, 3)})
    for i in range(1, len(sweep[arm])):
        if sweep[arm][i - 1]["diff"] < 0 <= sweep[arm][i]["diff"]:
            a, b = sweep[arm][i - 1], sweep[arm][i]
            t = -a["diff"] / (b["diff"] - a["diff"])
            delta_star[arm] = round(a["delta"] + t * (b["delta"] - a["delta"]), 2)
            break

# δ = δ̂ 处的完整博弈矩阵与均衡（进攻臂 × 防守）
model_b_arms = {}
for arm in OFFENSE_ARMS:
    M_hat = [[expected_utility(act, push, s3_mu, delta_hat, sigma_local=True)
              for push in (False, True)] for act in (arm, "DEF(fortress)")]
    p_hat, q_hat_star, V_hat, kind_hat = solve_2x2(M_hat)
    u_def_pure_hat = min(M_hat[1])
    gain_hat_arm = (V_hat - u_def_pure_hat) / u_def_pure_hat * 100
    M0 = [[expected_utility(act, push, s3_mu, 0.0, sigma_local=True)
           for push in (False, True)] for act in (arm, "DEF(fortress)")]
    p0, _, V0, kind0 = solve_2x2(M0)
    u_def_pure0 = min(M0[1])
    gain0_arm = (V0 - u_def_pure0) / u_def_pure0 * 100
    model_b_arms[arm] = {
        "at_delta_hat": {"delta": round(delta_hat, 2),
                         "M": [[round(v, 3) for v in row] for row in M_hat],
                         "p_star_off": round(p_hat, 4), "V": round(V_hat, 3), "kind": kind_hat,
                         "gain_vs_pureDEF_pct": round(gain_hat_arm, 2)},
        "at_delta_0": {"M": [[round(v, 3) for v in row] for row in M0],
                       "p_star_off": round(p0, 4), "V": round(V0, 3), "kind": kind0,
                       "gain_vs_pureDEF_pct": round(gain0_arm, 2)},
        "delta_sweep": sweep[arm],
        "delta_star_equilibrium_flip": delta_star[arm],
    }

results["model_B_additive_split"] = model_b_arms
gain_hat = model_b_arms["OFF(crown-pert)"]["at_delta_hat"]["gain_vs_pureDEF_pct"]
gain0 = model_b_arms["OFF(crown-pert)"]["at_delta_0"]["gain_vs_pureDEF_pct"]

# ---------------------------------------------------------------- 动态权重（模型B, δ=δ̂）
lam_grid = [round(x, 2) for x in np.arange(0, 2.01, 0.5)]
weight_curve = []
for lam in lam_grid:
    uo = bayes_u("OFF(crown-pert)", s3_mu, delta_hat, sigma_local=True, lam=lam)
    ud = bayes_u("DEF(fortress)", s3_mu, delta_hat, sigma_local=True, lam=lam)
    weight_curve.append({"lam": lam, "U_OFF": round(uo, 3), "U_DEF": round(ud, 3),
                         "w_offense": 1.0 if uo >= ud else 0.0})

state_table = {}
for state, pre in [("未改善(124.3683)", 124.3683), ("已入A段(122.0)", 122.0),
                   ("已进前四(121.0)", 121.0), ("已登顶区(119.0)", 119.0)]:
    uo = bayes_u("OFF(crown-pert)", s3_mu, delta_hat, sigma_local=True, pre_best=pre)
    ud = bayes_u("DEF(fortress)", s3_mu, delta_hat, sigma_local=True, pre_best=pre)
    state_table[state] = {"U_OFF": round(uo, 3), "U_DEF": round(ud, 3),
                          "w_offense": 1.0 if uo >= ud else 0.0}
results["dynamic_weights_modelB_delta_hat"] = {
    "lambda_curve": weight_curve, "state_table_lambda0": state_table}

# ---------------------------------------------------------------- 门禁
gate_a = {arm: model_a[f"S3_posterior(+0.6,14.2)|{arm}"]["gain_vs_pureDEF_pct"] for arm in OFFENSE_ARMS}
gate_b = {arm: model_b_arms[arm]["at_delta_hat"]["gain_vs_pureDEF_pct"] for arm in OFFENSE_ARMS}
gate_b0 = {arm: model_b_arms[arm]["at_delta_0"]["gain_vs_pureDEF_pct"] for arm in OFFENSE_ARMS}
best_arm = max(gate_b, key=gate_b.get)
results["gates"] = {
    "utility_gain_ge_15pct": {
        "target": ">=15.0%",
        "model_A_0105": {arm: {"gain_pct": gate_a[arm],
                               "verdict": "PASS" if gate_a[arm] >= 15 else "FAIL"} for arm in OFFENSE_ARMS},
        "model_B_at_delta_hat": {arm: {"gain_pct": gate_b[arm],
                                       "verdict": "PASS" if gate_b[arm] >= 15 else "FAIL"} for arm in OFFENSE_ARMS},
        "model_B_at_delta_0": {arm: {"gain_pct": gate_b0[arm],
                                     "verdict": "PASS" if gate_b0[arm] >= 15 else "FAIL"} for arm in OFFENSE_ARMS},
        "best_arm_model_B": best_arm,
        "note": "基线=对手最优反制下纯防守效用（对抗式读法）；模型B下进攻价值随官方噪声分解 δ 变化；"
                "OFF2(champ1107) 带 HIGH_CV 10.0% 门禁旗标，且官方 n=1",
    },
}

out_path = os.path.join(OUT_DIR, "0297_nash_weights.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------- console
print("=" * 72)
print("0297 Shot 3 进攻/防守动态权重博弈分配 — 结果摘要")
print("=" * 72)
print(f"\n[实证] 对手过夜改进率 q̂={improved_days}/{team_days}={q_hat:.3f}; 近平台期 Δ μ={push_mu:.2f} σ={push_sigma:.2f} (n={len(late_deltas)})")
print(f"[实证] fast14 族本地: n={len(fast14)} σ={fast14_sigma:.2f}; 官方同构型对 σ̂_off={sigma_off_meas:.2f} (n=2)")
print(f"[实证] 加性分解 δ̂={delta_hat:.2f}s (n=2 极不精确, 仅点估计)")
print(f"\n[模型A 0105口径 σ_local=0, δ=场景σ]  (行=[进攻臂,DEF] 列=[STAY,PUSH])")
for sc_name in SCENARIOS:
    for arm in OFFENSE_ARMS:
        r = model_a[f"{sc_name}|{arm}"]
        print(f"  {sc_name:<24s} {arm:<17s} p*(OFF)={r['p_star_off']}  V={r['V']:>7.2f}  {r['kind']:<12s} gain={r['gain_vs_pureDEF_pct']:+.2f}%")
print(f"\n[模型B 加性拆分 S3] δ 扫描 (q̂ 加权期望效用):")
for arm in OFFENSE_ARMS:
    print(f"  --- {arm} ---")
    for s in sweep[arm][::4]:
        print(f"    δ={s['delta']:>5.2f}  U_OFF={s['U_OFF']:>7.2f}  U_DEF={s['U_DEF']:>7.2f}  diff={s['diff']:>+6.2f}")
    print(f"    均衡翻转点 δ*={delta_star[arm]}")
for arm in OFFENSE_ARMS:
    b = model_b_arms[arm]
    print(f"\n[模型B {arm} @δ̂={delta_hat:.2f}] M={b['at_delta_hat']['M']}")
    print(f"  p*(OFF)={b['at_delta_hat']['p_star_off']:.3f} V={b['at_delta_hat']['V']:.2f} {b['at_delta_hat']['kind']}  gain={b['at_delta_hat']['gain_vs_pureDEF_pct']:+.2f}%")
    print(f"[模型B {arm} @δ=0] M={b['at_delta_0']['M']}")
    print(f"  p*(OFF)={b['at_delta_0']['p_star_off']:.3f} V={b['at_delta_0']['V']:.2f} {b['at_delta_0']['kind']}  gain={b['at_delta_0']['gain_vs_pureDEF_pct']:+.2f}%")
print(f"\n[动态权重 λ 曲线 @δ̂, OFF=crown-pert] (w_off = argmax U)")
for w in weight_curve:
    print(f"  λ={w['lam']:<5} U_OFF={w['U_OFF']:>7.2f}  U_DEF={w['U_DEF']:>7.2f}  w_off={w['w_offense']}")
print(f"\n[状态换挡表 λ=0 @δ̂]")
for st, row in state_table.items():
    print(f"  {st:<18s} U_OFF={row['U_OFF']:>7.2f}  U_DEF={row['U_DEF']:>7.2f}  w_off={row['w_offense']}")
print("\n门禁 ≥15%:")
print(f"  模型A: crown-pert {gate_a['OFF(crown-pert)']:+.2f}% | champ1107 {gate_a['OFF2(champ1107)']:+.2f}%")
print(f"  模型B@δ̂: crown-pert {gate_b['OFF(crown-pert)']:+.2f}% | champ1107 {gate_b['OFF2(champ1107)']:+.2f}%")
print(f"  模型B@δ=0: crown-pert {gate_b0['OFF(crown-pert)']:+.2f}% | champ1107 {gate_b0['OFF2(champ1107)']:+.2f}%")
print(f"结果JSON: {os.path.relpath(out_path, ROOT)}")
