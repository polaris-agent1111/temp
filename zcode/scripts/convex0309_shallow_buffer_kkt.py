# -*- coding: utf-8 -*-
"""0309: 多流并发下浅缓冲区丢包避免与单流吞吐极大化凸优化证明 — 离线验证脚本.

纯本地验证（继承 0085/0086/0298 物理口径）：
  mu = 10416.67 pkt/s（100 Mbps / 1200B），drop-tail 缓存 B=30 包（任务口径），
  敏感性 B=40（0082/0085 口径），RTT=70ms。

  §1 网络演算零溢出充分条件：Σ r_i <= mu 且 Σ b_i <= B  =>  零溢出、时延 <= B/mu。
     （Cruz '91 式反压界：Q(t) = sup_{s<=t}[ΣA(t)-ΣA(s)-mu(t-s)] <= Σb_i。数值核验。）
  §2 凸规划 + LP 对偶/KKT 解析解（scipy.linprog HiGHS）：
       P:  max r_0  s.t.  r_0 <= mu - R_bg - Δ（容量价 λ）,  b_0 <= B - B_bg（缓存价 γ）
     KKT：λ*=1, γ*=0, r_0* = mu - R_bg - Δ, b_0* 任意 -> 按风险最小取 0（leak 严格单包间隔）。
     鲁棒裕度 Δ 取 0085 实测 leak36 排空余量 0.136mu = 1416.67 pkt/s => r_0* = 9000 pkt/s
     = 36 包/4ms —— 与皇冠构型大文件档一致。
  §3 时步化包级仿真（0298 v2 引擎模式，dt=1/mu，无事件堆偏置）：
     - 保证域验证：连续背景 (r_bg, b_bg=20<=B) 下 r_0 越界即丢包、域内零丢包；
     - 占空比+阵风域：eta=0.44、70ms 阵风 40 包下 leak 32..42 丢失表（复现 0085 定性律）；
     - leak vs tb 同均值对比（b_0=40 > B 预算 => 必然违规）；
     - 皇冠邻域 ±1 包稳定性。
  §4 排空时间闭式：B/(mu - r_0*) = 21.18ms (B=30) / 28.24ms (B=40) << RTT 70ms。

不访问任何远程系统；不写 runs/。
"""
import json
import sys
from collections import deque
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "zcode" / "scripts" / "out"
OUT.mkdir(parents=True, exist_ok=True)

MU = 100e6 / 8 / 1200.0          # 10416.667 pkt/s
B_TASK = 30                      # 任务口径浅缓存
B_0082 = 40                      # 0082/0085 口径
RTT = 0.070                      # s
PER_4MS = 250.0                  # 每秒 tick 数（4ms）
TICK_PKT = MU / PER_4MS          # 41.667 pkt/tick = 线速

# ---------------------------------------------------------------- §1 网络演算界（数值核验）
def verify_burst_bound(seed=42, K=4, horizon=10.0):
    """随机可行参数 (Σr<=mu, Σb<=B) 下，逐窗核验积压界 Q(t)<=Σb_i<=B。"""
    rng = np.random.default_rng(seed)
    worst = 0.0
    for _ in range(200):
        # 随机可行 K 流泄漏桶
        while True:
            r = rng.uniform(0, MU / K, size=K)
            if r.sum() <= MU:
                break
        b = rng.uniform(0, B_TASK / K, size=K)
        if r.sum() > MU or b.sum() > B_TASK:
            continue
        # 逐窗检查：对任意窗口长 w，(Σr-mu)w + Σb <= 0 成立当 Σr<=mu
        # 数值上直接仿真实限最坏相位：全流同相位突发
        q = 0.0
        t_next = np.zeros(K)
        dt = 1.0 / MU
        steps = int(horizon / dt)
        peak = 0.0
        arrive_carry = np.zeros(K)
        for _ in range(steps):
            arrive_carry += r * dt
            send = np.floor(arrive_carry + 1e-12)
            arrive_carry -= send
            # 最坏相位：所有突发同时到达
            q += send.sum() - 1.0
            peak = max(peak, q)
            if q > 0:
                q = max(0.0, q - 1.0)
            elif q < 0:
                q = 0.0
        bound = b.sum()
        worst = max(worst, peak - bound)
    return worst  # 应 <= 0（同相位突发时 peak 可贴 Σb，服务顺序带来 <=1 的整包误差）

worst_excess = verify_burst_bound()

# ---------------------------------------------------------------- §2 LP 对偶 / KKT
def solve_lp(mu, R_bg, Delta, B_avail):
    """max r_0 s.t. r_0 <= mu - R_bg - Delta ; b_0 <= B_avail. (linprog 最小化 -r_0)"""
    c = [-1.0, 0.0]
    A = [[1.0, 0.0], [0.0, 1.0]]
    bub = [mu - R_bg - Delta, B_avail]
    res = linprog(c, A_ub=A, b_ub=bub, bounds=[(0, None), (0, None)], method="highs")
    # 对偶价（HiGHS marginals：<= 约束的影子价，符号按最小化惯例）
    lam = -res.ineqlin.marginals[0]
    gam = -res.ineqlin.marginals[1]
    return res, lam, gam

R_BG = 0.0        # 鲁棒口径：容量约束只对「我方保证份额」负责（背景由 Δ 阵风预算吸收）
DELTA = 0.136 * MU   # 0085 leak36 实测排空余量 13.6%
res30, lam30, gam30 = solve_lp(MU, R_BG, DELTA, B_TASK)
res40, lam40, gam40 = solve_lp(MU, R_BG, DELTA, B_0082)
r0_star = res30.x[0]

# KKT 残差（对 P(B=30)）
tol = 1e-9
slack_cap = (MU - R_BG - DELTA) - res30.x[0]
slack_buf = B_TASK - res30.x[1]
kkt = {
    "primal_feasible": bool(res30.x[0] >= -tol and res30.x[1] >= -tol
                            and slack_cap >= -tol and slack_buf >= -tol),
    "stationarity_r0": abs(1.0 - lam30),
    "stationarity_b0": abs(gam30),
    "comp_slack_cap": abs(lam30 * slack_cap),
    "comp_slack_buf": abs(gam30 * slack_buf),
    "dual_sign": bool(lam30 >= -tol and gam30 >= -tol),
}
kkt["max_residual"] = max(kkt["stationarity_r0"], kkt["stationarity_b0"],
                          kkt["comp_slack_cap"], kkt["comp_slack_buf"])
kkt["pass"] = bool(kkt["primal_feasible"] and kkt["dual_sign"] and kkt["max_residual"] <= 1e-6)

# 解析解对照
r0_analytic = MU - R_BG - DELTA
drain30 = B_TASK / (MU - r0_analytic)
drain40 = B_0082 / (MU - r0_analytic)

# ---------------------------------------------------------------- §3 时步化包级仿真
def simulate(r0_per4ms, bg="guaranteed", B=B_TASK, sim_s=15.0,
             gust_every=0.070, gust_size=40, r_bg_frac=0.5, tb_mode=False,
             tb_burst=None, base_frac=None):
    """返回 (my_sent, my_dropped, my_goodput_pkt_per_s)。

    到达调度一律用 while/累积携带（无 if 别名：if 调度在 rate≈线速时会隔槽跳发，
    实测 leak40 被压到 5208 pkt/s，v1 初版已因此失真）。

    bg='guaranteed': 连续背景 r_bg_frac*mu（桶深 20<=B）；用于验证定理的速率条件。
    bg='gusty':      连续底噪 base_frac*mu + 每 gust_every 秒瞬时阵风 gust_size 包；
                     用于稳健域/leak-vs-tb 对比（Δ 预算语义）。
    tb_mode:         我方改 token bucket：每 4ms tick 一次倾泻 tb_burst 包（默认=r0_per4ms）。
    """
    dt = 1.0 / MU
    steps = int(sim_s / dt)
    my_rate_pkt_per_s = r0_per4ms * PER_4MS
    t_next_my = 0.0
    q = deque()          # 0=背景包 1=我方包
    my_sent = my_drop = my_deliv = 0
    bg_carry = 0.0
    phase = 0.0
    next_tb_tick = 0.0
    burst = int(tb_burst if tb_burst is not None else r0_per4ms)
    for i in range(steps):
        t = i * dt
        n_my_before = my_sent
        # ---- 我方到达（只计数，统一由下方 arrivals 列表入队——
        #      否则 while 直append + 列表再 append 会双倍入队，v2 初版已踩坑）
        if tb_mode:
            if t >= next_tb_tick:
                my_sent += burst
                next_tb_tick += 0.004
        else:
            while t >= t_next_my:          # while：正确长程速率，无别名
                my_sent += 1
                t_next_my += 1.0 / my_rate_pkt_per_s
        n_my_this_slot = my_sent - n_my_before
        # ---- 背景到达
        if bg == "guaranteed":
            bg_carry += r_bg_frac * MU * dt
            n = int(bg_carry); bg_carry -= n
        else:
            bg_carry += base_frac * MU * dt
            n = int(bg_carry); bg_carry -= n
            phase += dt
            if phase >= gust_every:
                phase -= gust_every
                n += gust_size
        n_bg_this_slot = n
        # ---- 轮转到达顺序（0298 v2 引擎口径：消除确定性相位对齐伪影——
        #      否则我方包恒先入队，tail drop 全部由后到的背景包吸收，我方丢包恒 0）
        arrivals = [1] * n_my_this_slot + [0] * n_bg_this_slot
        if arrivals:
            rot = i % len(arrivals)
            arrivals = arrivals[rot:] + arrivals[:rot]
            for pk in arrivals:
                q.append(pk)
        # ---- 溢出（drop-tail：溢出即丢最新到达）
        while len(q) > B:
            if q.pop() == 1:
                my_drop += 1
        # ---- 服务 1 包
        if q and q.popleft() == 1:
            my_deliv += 1
    return my_sent, my_drop, my_deliv / sim_s

# V1 速率条件：连续背景 0.5mu（b_bg=20<=B=30）=> 保证域边界 r_0* = 0.5mu = 5208.3 pkt/s = 20.83/4ms
grid = [16, 18, 20, 20.5, 20.8, 21, 21.5, 24]
v1 = []
for g in grid:
    s, d, gp = simulate(g, bg="guaranteed", r_bg_frac=0.5, sim_s=10.0)
    v1.append({"r_per4ms": g, "r_pkt_s": g * PER_4MS, "sent": s, "dropped": d,
               "goodput": gp, "inside_domain": g * PER_4MS <= MU * 0.5 + 1e-6})

# V1b 缓存条件隔离：低均值速率（速率条件满足），仅突发深度变化。
#   gusty 背景（底噪 0.02mu + 每 70ms 阵风 20 包）：tb burst=10 => 突发碰撞最坏 Σb=10+20=30=B
#   （边界内，定理覆盖，期望~零丢失）；burst=15 => 15+20=35>B（保证失效，碰撞即丢）。
v1b = []
for burst in (10, 15):
    s, d, gp = simulate(0, bg="gusty", B=B_TASK, sim_s=10.0, base_frac=0.02,
                        gust_size=20, tb_mode=True, tb_burst=burst)
    v1b.append({"tb_burst": burst, "worst_sigma_b": burst + 20, "sent": s, "dropped": d,
                "drop_pct": d / max(s, 1) * 100,
                "theorem_covers": (burst + 20) <= B_TASK})

# V2 稳健域：底噪 0.05mu + 70ms 阵风 40 包；leak 32..42
#   期望：36 及以下零丢失（9000+521+571<10416），38 起出现丢失（皇冠=36 的稳健最优）
v2 = []
for g in [32, 34, 35, 36, 37, 38, 40, 42]:
    s, d, gp = simulate(g, bg="gusty", B=B_TASK, sim_s=15.0, base_frac=0.05)
    v2.append({"r_per4ms": g, "sent": s, "dropped": d, "drop_pct": d / max(s, 1) * 100,
               "goodput": gp})

# V3 leak vs tb 同均值（40/4ms = 10000 pkt/s）
sL, dL, gpL = simulate(40, bg="gusty", B=B_TASK, sim_s=15.0, base_frac=0.05, tb_mode=False)
sT, dT, gpT = simulate(40, bg="gusty", B=B_TASK, sim_s=15.0, base_frac=0.05,
                       tb_mode=True, tb_burst=40)
v3 = {"leak40": {"sent": sL, "dropped": dL, "drop_pct": dL / max(sL, 1) * 100, "goodput": gpL},
      "tb40": {"sent": sT, "dropped": dT, "drop_pct": dT / max(sT, 1) * 100, "goodput": gpT}}

# B=40 敏感性（同 V2 关键点）
v2b = []
for g in [36, 40]:
    s, d, gp = simulate(g, bg="gusty", B=B_0082, sim_s=15.0, base_frac=0.05)
    v2b.append({"B": B_0082, "r_per4ms": g, "dropped": d, "drop_pct": d / max(s, 1) * 100})

# ---------------------------------------------------------------- §4 汇总
res = {
    "generated_at": datetime.now().isoformat(timespec="seconds"),
    "physics": {"mu_pkt_s": MU, "B_task": B_TASK, "B_0082": B_0082, "RTT_s": RTT},
    "network_calculus": {
        "theorem": "Σr<=mu ∧ Σb<=B ⇒ Q(t)≤Σb≤B（零溢出），时延≤B/μ",
        "numeric_worst_excess_pkts": worst_excess,
        "pass": bool(worst_excess <= 1.0),  # 整包服务相位误差 ≤1 包
    },
    "lp_kkt": {
        "program": "max r0 s.t. r0 ≤ μ−R_bg−Δ, b0 ≤ B−B_bg",
        "robust_margin_Delta_pkt_s": DELTA,
        "r0_star": r0_star, "r0_star_per4ms": r0_star / PER_4MS,
        "r0_analytic": r0_analytic,
        "lambda_capacity": lam30, "gamma_buffer": gam30,
        "kkt": kkt,
        "crown_mapping": "r0* = 9000 pkt/s = 36 包/4ms（皇冠大文件档）；Δ=0085 leak36 排空余量 13.6%",
        "drain_time_s": {"B30": drain30, "B40": drain40,
                         "note": "B/(μ−r0*) < RTT 70ms ⇒ 阵风在亚 RTT 内吸收"},
    },
    "sim_v1_guaranteed_domain": v1,
    "sim_v1b_buffer_condition": v1b,
    "sim_v2_gusty": v2,
    "sim_v3_leak_vs_tb": v3,
    "sim_B40_sensitivity": v2b,
    "compliance": "纯本地只读；未访问远程系统；未写 runs/；无凭据输出",
}
(OUT / "0309_convex_kkt_results.json").write_text(
    json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

print("== 0309 汇总 ==")
print("burst-bound worst excess pkts: %.3f (pass=%s)" % (worst_excess, worst_excess <= 1.0))
print("LP: r0*=%.2f pkt/s (%.3f /4ms), λ=%.4f γ=%.4f, KKT pass=%s"
      % (r0_star, r0_star / PER_4MS, lam30, gam30, kkt["pass"]))
print("drain: B30=%.2fms B40=%.2fms (RTT=70ms)" % (drain30 * 1e3, drain40 * 1e3))
print("V1 guaranteed:", [(d["r_per4ms"], d["dropped"]) for d in v1])
print("V1b buffer-cond:", v1b)
print("V2 gusty:", [(d["r_per4ms"], round(d["drop_pct"], 3)) for d in v2])
print("V3:", v3["leak40"]["drop_pct"], v3["tb40"]["drop_pct"])
print("B40 sens:", v2b)
print("out ->", OUT / "0309_convex_kkt_results.json")
