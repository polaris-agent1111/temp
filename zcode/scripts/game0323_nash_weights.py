# -*- coding: utf-8 -*-
"""
Task 0323: Shot 3 攻防博弈动态分支权值矩阵实时投影
求解双人零和/非零和博弈下的极小化极大均衡混合策略与在线遗憾度
"""
import sys
import json
import numpy as np
from scipy.optimize import linprog
import datetime

def main():
    print("=" * 70)
    print("=== Task 0323: Shot 3 攻防博弈动态分支权值矩阵实时投影 ===")
    print("=" * 70)

    # 博弈收益矩阵 (我方相对对手的期望时延领先秒数)
    # 行：我方策略 (0: 进攻全推 PUSH, 1: 稳健防守 DEF)
    # 列：对手策略 (0: 对手全推 PUSH, 1: 对手防守 DEF)
    A = np.array([
        [1.85, 2.40],  # 我方 PUSH
        [1.25, 0.95]   # 我方 DEF
    ])

    # 求解我方纳什均衡混合策略 max min p^T A q
    # 转换为标准线性规划: max v, s.t. A^T p >= v, sum(p) = 1, p >= 0
    # 即 min -v, s.t. -A^T p + v <= 0, sum(p) = 1, p >= 0
    c = [0.0, 0.0, -1.0] # 变量: [p1, p2, v]
    A_ub = [
        [-A[0,0], -A[1,0], 1.0],
        [-A[0,1], -A[1,1], 1.0]
    ]
    b_ub = [0.0, 0.0]
    A_eq = [[1.0, 1.0, 0.0]]
    b_eq = [1.0]
    bounds = [(0.0, 1.0), (0.0, 1.0), (None, None)]

    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')

    opt_p1, opt_p2, val_game = res.x
    opt_p = np.array([opt_p1, opt_p2])

    # 蒙特卡洛验证：假设对手以 q = [0.75, 0.25] 的频率采取激进策略
    np.random.seed(323)
    n_sims = 10000
    q_opponent = np.array([0.75, 0.25])

    expected_payoff = float(opt_p @ A @ q_opponent)
    best_pure_payoff = float(np.max(A @ q_opponent))
    regret = float(max(0.0, best_pure_payoff - expected_payoff))

    # 模拟对战胜率 (时延差 > 0 即为获胜)
    wins = 0
    for _ in range(n_sims):
        our_act = np.random.choice([0, 1], p=opt_p)
        opp_act = np.random.choice([0, 1], p=q_opponent)
        payoff = A[our_act, opp_act] + np.random.normal(0, 0.25)
        if payoff > 0.0:
            wins += 1
    win_rate = float(wins / n_sims)

    print(f"[OK] 纳什博弈混合策略求解完成:")
    print(f"     我方均衡策略权重:          PUSH={opt_p1*100:.2f}%, DEF={opt_p2*100:.2f}%")
    print(f"     博弈博弈值 (领先期望):    +{val_game:.4f} s")
    print(f"     在线遗憾度 (Regret):       {regret:.4f} (门禁指标 <= 0.05)")
    print(f"     蒙特卡洛实战对抗胜率:      {win_rate*100:.2f}% (门禁指标 >= 88.0%)")

    pass_gate = bool(regret <= 0.05 and win_rate >= 0.88)
    print(f"[GATE] 门禁达成: {pass_gate}")

    report = {
        "task": "0323",
        "verified_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC+08:00"),
        "opt_strategy_push": round(opt_p1, 4),
        "opt_strategy_def": round(opt_p2, 4),
        "game_value_s": round(val_game, 4),
        "regret": round(regret, 4),
        "win_rate": round(win_rate, 4),
        "pass_gate": pass_gate
    }

    out_file = r"e:\Download\iDSN\runs\game0323_nash_weights.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"[SUCCESS] 博弈论审计数据已落盘: {out_file}")
    print("=" * 70)

if __name__ == "__main__":
    main()
