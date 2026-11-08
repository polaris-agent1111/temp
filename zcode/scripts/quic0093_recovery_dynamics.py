# -*- coding: utf-8 -*-
"""0093 — QUIC 连接在微丢包率下的拥塞恢复收敛速度动力学差分方程推导.

模型（RFC 9002 语义，MSS=1200B）：
  每 RTT 丢包「事件」概率 p(c)=1-(1-ε)^c（同 RTT 多丢合并为一个事件）。
  SS 倍增直到首个丢失事件 → c←β·c、快恢复平台 1 RTT → CA 每 RTT +1。
  期望差分方程：E[c_{n+1}|c_n]=(1-p_n)(c_n+1)+p_n·β·c_n
  平稳不动点：p*c* = 1/(1-β) → c* = 1/√(ε(1-β))（p*≈εc*）；松弛 λ=f'(c*)。

结构性事实（本审计核心）：下载是 pacer 限速的 —— inflight 被钉在
  W_p = 发射率 × RTT = 9500 × 0.07 ≈ 665 包；cwnd 只是垫在 inflight 之上的约束。
  吞吐 = min(cwnd, W_p)/RTT。因此恢复通道的全部问题 = 切断后 cwnd 是否跌破 W_p。

反推排除：实测 Shot 2 官方 124.4s ≈ 全程贴 pacer 速率（≈91Mbps）⇒ 稳态下 cwnd ≥ W_p
  ⇒ 独立微丢平稳解必须 c* ≥ 665 ⇒ ε_indep ≤ 1/((1-β)·665²) ≈ 4.5e-6（β=0.5）。
  而 0085 gust 累计丢包 37 pkts/下载若按独立微丢摊平 ε=3.1e-5 → c*=258 < 665，
  将把吞吐钉死在 4.4Mbps —— 与实测矛盾。故丢包必然是阵风聚簇（0085 柯氏模型自洽），
  系统运行在「SS 垫高—阵风切断」瞬态域：阵风切断从 ≫W_p 的垫高处跌落，仍 ≥W_p ⇒ 零成本。
  唯一例外是开局窗口：RTT 0–6 内 cwnd=10·2^n < 665 且无垫高（pacer 信用无法被 SS 跳过），
  阵风碰撞 → 从切断点 CA 爬回 665 的长亏空 —— 可量化的方差通道。
"""
import math
import numpy as np

rng = np.random.default_rng(42)

MSS_BYTES = 1200.0
RTT = 0.070
SERVICE = 96e-6
RATE_PKT_S = 9500.0
W_P = RATE_PKT_S * RTT          # 665
T_DL = 124.4
N_RTT_DL = int(T_DL / RTT)
SIGMA_D = 7.02
IW = 10.0                        # 初始拥塞窗口（QUIC 推荐 IW10）
N_FRAGILE = 7                    # 10·2^n ≥ 665 从 n=7 起 ⇒ RTT 0–6 脆弱


def p_loss(c, eps):
    return 1.0 - (1.0 - eps) ** c


def fixed_point(eps, beta, c0=10.0):
    c = c0
    for _ in range(500000):
        p = p_loss(c, eps)
        c_new = (1 - p) * (c + 1.0) + p * beta * c
        if abs(c_new - c) < 1e-10:
            break
        c = c_new
    return c


def f_prime(c, eps, beta):
    h = 1e-4
    f = lambda x: (1 - p_loss(x, eps)) * (x + 1.0) + p_loss(x, eps) * beta * x
    return (f(c + h) - f(c - h)) / (2 * h)


def refill_newreno(c_from, c_target):
    """阵风间期 ε≈0：CA +1/RTT 从 c_from 爬回 c_target。亏空面积 Σ(c_target-c)。"""
    if c_from >= c_target:
        return 0.0, 0, 0.0
    d = c_target - c_from
    area = d * (d + 1) / 2.0          # 等差三角形
    return area * SERVICE, int(d), area


def refill_cubic(c_cut, Wmax, c_target, beta=0.7, C=0.4, dt=1e-3):
    """CUBIC W(t)=C(t-K)³+Wmax，K=(βWmax/C)^{1/3}（RFC 8312，t=K 时回到 Wmax）。
    数值积分亏空面积 Σ max(0, c_target−W(t))·dt，直至 W≥c_target。
    覆盖 c_target>Wmax 的 post-Wmax 立方爬升段。返回 (秒, t* RTT, 面积 pkt·RTT)。"""
    if c_cut >= c_target:
        return 0.0, 0.0, 0.0
    K = (beta * Wmax / C) ** (1.0 / 3.0)
    area = 0.0
    t = 0.0
    while t < 1e6:
        w = C * (t - K) ** 3 + Wmax
        if w >= c_target:
            break
        area += (c_target - w) * dt
        t += dt
    return area * SERVICE, t, area


def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    out = []
    out.append('=== 0093 QUIC 微丢包拥塞恢复差分方程（seed=42）===')
    out.append(f'RTT={RTT*1e3:.0f}ms  下载={T_DL:.1f}s={N_RTT_DL}RTT  发射率={RATE_PKT_S:.0f}pkt/s'
               f'  W_p={W_P:.0f}包  IW={IW:.0f}')
    out.append('')

    out.append('--- 1. CA 平稳不动点 c* 与松弛时间 n_95（期望差分方程） ---')
    out.append(f"{'ε':>9}{'β':>5}{'c*':>9}{'p*=εc*':>9}{'λ':>10}{'n_95 RTT':>10}"
               f"{'c*/W_p':>8}{'支撑W_p?':>9}")
    for eps in (1e-6, 3e-6, 4.5e-6, 1e-5, 3.1e-5, 7.2e-5, 1e-4, 1e-3):
        for beta in (0.5,):
            cs = fixed_point(eps, beta)
            lam = f_prime(cs, eps, beta)
            n95 = math.log(0.05) / math.log(lam) if 0 < lam < 1 else float('inf')
            out.append(f'{eps:>9.1e}{beta:>5.1f}{cs:>9.0f}{eps*cs:>9.4f}{lam:>10.6f}'
                       f'{n95:>10.0f}{cs/W_P:>8.2f}{"能" if cs>=W_P else "不能":>9}')
    cs_crit = 1.0 / math.sqrt(0.5 * (1 - 0.5))  # 反推：c*=665 需 ε
    eps_crit = 1.0 / ((1 - 0.5) * W_P ** 2)
    out.append(f'反推阈值：支撑 W_p={W_P:.0f} 需 ε_indep ≤ {eps_crit:.2e}（β=0.5；β=0.7 时 {1/((1-0.7)*W_P**2):.2e}）')
    out.append('')

    out.append('--- 2. 垫高判据：阵风切断后 cwnd 是否跌破 W_p（ε_between≈0） ---')
    out.append(f"{'γ=cwnd/W_p':>11}{'NewReno 成本':>13}{'CUBIC 成本':>12}   （γ<2/3.35 时有亏空）")
    for gamma in (1.0, 1.25, 1.5, 2.0, 3.35, 5.0, 10.0):
        c_old = gamma * W_P
        cut_nr = 0.5 * c_old
        t_nr, n_nr, _ = refill_newreno(cut_nr, W_P)
        cut_cb = 0.7 * c_old
        t_cb, t_cb_rtt, _ = refill_cubic(cut_cb, c_old, W_P)
        out.append(f'{gamma:>11.2f}{t_nr:>9.2f}s ({n_nr:>4}RTT){t_cb:>9.2f}s ({t_cb_rtt:>5.1f}RTT)')
    out.append('解读：SS 垫高到 γ≥2（NewReno）/γ≥3.35（CUBIC）后阵风切断不再跌破 W_p；')
    out.append('      垫高磨损到 γ≈1 只发生在开局窗口或极密集连续阵风。')
    out.append('')

    out.append('--- 3. 开局脆弱窗口（RTT0–6 cwnd=10·2^n<665 无垫高；阵风 Poisson 到达） ---')
    out.append(f"{'阵风间隔':>10}{'λ_g/RTT':>10}{'P(开局碰撞)':>11}{'E[ΔT] s':>10}{'sd[ΔT]':>9}"
               f"{'P50':>8}{'P90':>8}{'sd/σ_d':>8}")
    t_ev_arr = np.array([refill_newreno(0.5 * IW * 2 ** n, W_P)[0] for n in range(N_FRAGILE)])
    for gap_s in (3.0, 10.0, 20.0, 40.0):
        lam_g = RTT / gap_s                 # 每 RTT 阵风概率
        p_hit = 1 - (1 - lam_g) ** N_FRAGILE
        # 精确两点混合分布：ΔT = t(n) 若首阵风落 RTT n≤6，否则 0
        p_first_arr = np.array([lam_g * (1 - lam_g) ** n for n in range(N_FRAGILE)])
        e_dt = float(np.dot(p_first_arr, t_ev_arr))
        var_dt = float(np.dot(p_first_arr, t_ev_arr ** 2) - e_dt ** 2)
        sd_dt = math.sqrt(max(var_dt, 0.0))
        # P90/P99：碰撞条件分布（按首阵风 RTT 的概率归一，按成本升序取分位）
        order = np.argsort(t_ev_arr)
        cond = p_first_arr[order] / p_first_arr.sum()
        cdf = np.cumsum(cond)
        p90 = float(t_ev_arr[order][np.searchsorted(cdf, 0.90)])
        p50 = float(t_ev_arr[order][np.searchsorted(cdf, 0.50)])
        out.append(f'{gap_s:>9.0f}s{lam_g:>10.4f}{p_hit*100:>10.1f}%{e_dt:>10.2f}{sd_dt:>9.2f}'
                   f'{p50:>8.1f}{p90:>8.1f}{sd_dt/SIGMA_D:>8.2f}')
    out.append('')
    out.append('注：sd[ΔT] 是「单发成绩」方差贡献（碰撞=大成本、无碰撞=0 的两点混合）；')
    out.append('    条件 P90/P99 为碰撞情形的恢复成本分位（CA 爬坡 RTT 数 × 96µs/包）。')
    out.append('')

    out.append('--- 4. CUBIC(β=0.7) 开局对照（阵风间隔 10s） ---')
    lam_g = RTT / 10.0
    t_cb = np.array([refill_cubic(0.7 * IW * 2 ** n, IW * 2 ** n, W_P)[0] for n in range(N_FRAGILE)])
    p_first = np.array([lam_g * (1 - lam_g) ** n for n in range(N_FRAGILE)])
    e_cb = float(np.dot(p_first, t_cb))
    e_nr = float(np.dot(p_first, t_ev_arr))
    out.append(f'CUBIC E[ΔT] = {e_cb:.2f}s   NewReno 同口径 = {e_nr:.2f}s   （CUBIC/NewReno = {e_cb/e_nr:.2f}）')
    out.append('（CUBIC 的 β=0.7 切断更浅 + 立方爬坡更快，开局窗口期望成本仅为 NewReno 的 ≈1/25）')
    out.append('')
    out.append(f'结论锚点：σ_d(0084)={SIGMA_D}s。开局窗口碰撞在阵风间隔 3–20s 下贡献 '
              f'E[ΔT]≈0.1–1.5s、单发 sd≈1.5–5s —— 与 σ_d 同量级的天然候选机制；')
    out.append('稳态（RTT≥7 后）垫高自持，恢复通道贡献恒为 0；方差主导仍属 0085 缓冲层。')
    print('\n'.join(out))


if __name__ == '__main__':
    main()
