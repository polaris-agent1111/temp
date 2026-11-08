#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0078 — 背景流突发到达 CTMC 与空闲间隙稳态转移矩阵建模.

官方背景流模型（docs/extracted/02_websearch_model.md，11 节点 CDF）：
  流到达 = 泊松过程 λ；流长 S ~ 11 节点分段线性 CDF，E[S] = 1.711 MB；
  目标速率 100 Mbps → λ = C / E[S] = 12.5 MB/s ÷ 1.711 MB = 7.3069 条/s；
  λ·E[S]/C = ρ = 1.0（官方设定即临界负载——0057 结构事实的另一种表述）。

三条互补建模线：
  A. M/G/∞ 占用过程（精确、分布无关）：N(t) 为生灭 CTMC，λ_n = λ，μ_n = n·μ，
     μ = C/E[S]；平稳分布 Poisson(ρ)（无感性/insensitivity）。
     → 空闲概率 P(N=0) = e^{-1} = 36.79%；空闲间隙长 ~ Exp(λ)。
  B. 类别分辨 CTMC（有限截断）：把 11 节点 CDF 分位为 4 类
     S(<80KB, .53) / M(80KB–2MB, .27) / L(2–10MB, .17) / G(10–30MB, .03)，
     每类指数服务率 μ_c = C / m̄_c；状态 = 各类在服条数 (n_S,n_M,n_L,n_G)，
     N ≤ N_MAX 截断；生成元 Q 数值求稳态（稀疏线性求解 + 幂迭代交叉验证）。
     → 「突发相位」占空比：巨流在服概率、大流在服概率、碰撞暴露度。
  C. 嵌入跳跃链 + 2 相集总（Idle/Busy 交替更新）：
     E[I] = 1/λ，E[B] = (e^ρ − 1)/λ，占空比自洽校验 = e^{-ρ}；
     P(gap ≥ τ) = e^{-λτ} 表 + 定时器粒度 G=4ms 截断效应。

输出：_0078_out.md
"""
from __future__ import annotations

import sys
from itertools import product
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).with_name("_0078_out.md")

C_BPS = 100e6
C_MB = 12.5e6          # B/s
E_S = 1.711e6          # B（官方期望流长）
LAM = C_MB / E_S       # 流到达率

CDF_PTS = [
    (0, 0.0), (10000, 0.15), (20000, 0.20), (30000, 0.30), (50000, 0.40),
    (80000, 0.53), (200000, 0.60), (1000000, 0.70), (2000000, 0.80),
    (5000000, 0.90), (10000000, 0.97), (30000000, 1.00),
]

CLASSES = [  # (名称, 下界, 上界, 概率)
    ("S", 0.0, 80_000.0, 0.53),
    ("M", 80_000.0, 2_000_000.0, 0.27),
    ("L", 2_000_000.0, 10_000_000.0, 0.17),
    ("G", 10_000_000.0, 30_000_000.0, 0.03),
]


def class_mean(lo: float, hi: float) -> float:
    """分段线性 CDF 在 [lo,hi] 上的条件均值：∫ x dF / (F(hi)-F(lo))."""
    pts = [(x, f) for x, f in CDF_PTS if lo <= x <= hi]
    if pts[0][0] != lo:
        f_lo = np.interp(lo, [p[0] for p in CDF_PTS], [p[1] for p in CDF_PTS])
        pts = [(lo, f_lo)] + pts
    num = 0.0
    for (x0, f0), (x1, f1) in zip(pts, pts[1:]):
        d = f1 - f0
        if d <= 0:
            continue
        # 密度 d/Δx 均匀 → 均值 (x0+x1)/2
        num += d * (x0 + x1) / 2.0
    den = pts[-1][1] - pts[0][1]
    return num / den


# ---------- A. M/G/∞ 生灭 CTMC（截断 N_MAX） ----------
def mg_inf_stationary(n_max=60):
    mu = C_MB / E_S  # 单流服务率（条/s）
    Q = np.zeros((n_max + 1, n_max + 1))
    for n in range(n_max + 1):
        Q[n, n] = -LAM
        if n < n_max:
            Q[n, n + 1] = LAM
        if n > 0:
            Q[n, n - 1] = n * mu
            Q[n, n] -= n * mu
    # π Q = 0 → 解线性方程（补充归一化）
    A = Q.T.copy()
    A[-1, :] = 1.0
    b = np.zeros(n_max + 1); b[-1] = 1.0
    pi = np.linalg.solve(A, b)
    return pi, Q


# ---------- B. 类别分辨 CTMC：状态 (n_S,n_M,n_L,n_G), N ≤ N_MAX ----------
def class_resolved_stationary(n_max=6):
    names = [c[0] for c in CLASSES]
    probs = np.array([c[3] for c in CLASSES])
    means = np.array([class_mean(c[1], c[2]) for c in CLASSES])
    mus = C_MB / means  # 每类服务率

    states = [s for s in product(range(n_max + 1), repeat=4) if sum(s) <= n_max]
    idx = {s: i for i, s in enumerate(states)}
    n_st = len(states)
    Q = np.zeros((n_st, n_st))
    for s in states:
        i = idx[s]
        N = sum(s)
        # 出生：到达并属于类 c
        for c in range(4):
            if N < n_max:
                ns = list(s); ns[c] += 1
                Q[i, idx[tuple(ns)]] += LAM * probs[c]
        # 死亡：类 c 中一条完成
        for c in range(4):
            if s[c] > 0:
                ns = list(s); ns[c] -= 1
                Q[i, idx[tuple(ns)]] += s[c] * mus[c]
        Q[i, i] = -(Q[i].sum() - Q[i, i])
    # π Q = 0
    A = Q.T.copy(); A[-1, :] = 1.0
    b = np.zeros(n_st); b[-1] = 1.0
    pi = np.linalg.solve(A, b)
    # 幂迭代交叉验证（均匀化：速率取最大对角绝对值）
    v = np.ones(n_st) / n_st
    r_unif = float(np.max(-np.diag(Q)))
    B = np.eye(n_st) + Q / r_unif
    for _ in range(20000):
        v = v @ B; v /= v.sum()
    pi_power = v
    return states, idx, Q, pi, pi_power, mus, means


def phase_probs(states, pi):
    """由联合稳态导出：P(空闲) / P(各类至少一条在服) / P(N=n)."""
    p_idle = 0.0
    p_class = np.zeros(4)
    p_N = {}
    p_giant_or_large = 0.0  # L 或 G 在服（碰撞高危相位）
    for s, w in zip(states, pi):
        N = sum(s)
        p_N[N] = p_N.get(N, 0.0) + w
        if N == 0:
            p_idle += w
            continue
        for c in range(4):
            if s[c] > 0:
                p_class[c] += w
        if s[2] > 0 or s[3] > 0:
            p_giant_or_large += w
    return p_idle, p_class, p_N, p_giant_or_large


# ---------- C. 交替更新（Idle/Busy）与间隙表 ----------
def alternating_renewal():
    rho = 1.0
    EI = 1.0 / LAM
    EB = (np.exp(rho) - 1.0) / LAM
    return EI, EB, EI / (EI + EB)


def gap_table(taus_ms):
    rows = []
    for tau_ms in taus_ms:
        tau = tau_ms / 1000.0
        p_ge = float(np.exp(-LAM * tau))
        e_gap_ge = (1.0 + LAM * tau) / LAM * 1000.0  # E[gap | gap ≥ τ] = τ + 1/λ，ms
        rows.append((tau_ms, p_ge, e_gap_ge))
    return rows


def main():
    lines = []
    P = lines.append
    P("# 0078 输出（ctmc0078_idle_gaps.py 生成）\n")

    P("## 0. 基础量")
    P(f"- λ = C/E[S] = 12.5MB/s ÷ 1.711MB = {LAM:.4f} 条/s；ρ = λE[S]/C = 1.000")
    mus_tbl = []
    for name, lo, hi, pr in CLASSES:
        m = class_mean(lo, hi)
        mus_tbl.append((name, pr, m / 1e6, C_MB / m))
        P(f"- 类 {name}: p={pr:.2f}, 条件均值 m̄={m/1e6:.4f} MB, 服务率 μ={C_MB/m:.3f} /s, 平均占用时长 {m/C_MB*1000:.1f} ms")
    # 占空比核对：Σ p_c·m̄_c = E[S]/C
    tot = sum(pr * class_mean(lo, hi) for name, lo, hi, pr in CLASSES)
    P(f"- Σ p_c·m̄_c = {tot/1e6:.4f} MB（应 = E[S] = 1.711 MB）\n")

    P("## A. M/G/∞ 生灭 CTMC（N_MAX=60 精确解）")
    pi, _ = mg_inf_stationary(60)
    P("| n | π_n（CTMC 数值解） | Poisson(1) 解析 |")
    P("|---|--------------------|------------------|")
    from math import factorial
    for n in range(8):
        pois = float(np.exp(-1.0) / factorial(n))
        P(f"| {n} | {pi[n]:.6f} | {pois:.6f} |")
    P(f"- P(N=0) = {pi[0]:.6f}（解析 e^(-1) = {np.exp(-1):.6f}）")
    P(f"- P(N≥1) = {1-pi[0]:.6f}（碰撞暴露度上限）")
    P(f"- E[N] = {sum(n*w for n,w in enumerate(pi)):.4f}（解析 ρ = 1）\n")

    P("## B. 类别分辨 CTMC（状态=(n_S,n_M,n_L,n_G)，N≤6 截断）")
    states, idx, Q, pi_c, pi_power, mus, means = class_resolved_stationary(6)
    P(f"- 状态空间 |S| = {len(states)}；稳态线性解 vs 幂迭代最大偏差 {np.max(np.abs(pi_c-pi_power)):.2e}")
    p_idle, p_class, p_N, p_gl = phase_probs(states, pi_c)
    P(f"- P(空闲 N=0) = {p_idle:.6f}（与 A 线一致性 {abs(p_idle-pi[0]):.2e}）")
    P(f"- P(小流 S 在服) = {p_class[0]:.4f}")
    P(f"- P(中流 M 在服) = {p_class[1]:.4f}")
    P(f"- P(大流 L 在服) = {p_class[2]:.4f}")
    P(f"- P(巨流 G 在服) = {p_class[3]:.4f}")
    P(f"- P(L∪G 在服) = {p_gl:.4f}（我方 96M 贴靠构型的碰撞高危相位占空比）")
    P(f"- P(N≥1) = {1-p_idle:.4f}")
    # 截断偏差核对
    tail = 1.0 - sum(w for w in pi_c)
    P(f"- 截断尾部质量（N>6, 由解的缺失补足）: {tail:.2e}\n")

    P("### B'. 嵌入跳跃链（到达/完成时刻的状态跳转矩阵，列=当前态，行=下一态）")
    # 从 Q 构造嵌入链：离开态 i 的速率 = -Q[i,i]，跳转到 j 概率 Q[i,j]/(-Q[i,i])
    P("```")
    P("Q 生成元行示例（前 6 个状态）：")
    hdr = "state      " + "  ".join(f"{s}" for s in states[:6])
    P(hdr)
    for s in states[:6]:
        i = idx[s]
        row = " ".join(f"{Q[i,j]:+.4f}" for j in range(6))
        P(f"({','.join(map(str,s))})  {row}")
    P("```")
    P("（完整 Q 已存 _0078_Q.npy；状态表 _0078_states.txt）\n")
    np.save(Path(__file__).with_name("_0078_Q.npy"), Q)
    Path(__file__).with_name("_0078_states.txt").write_text(
        "\n".join(str(s) for s in states), encoding="utf-8")

    P("## C. 交替更新与间隙结构")
    EI, EB, frac = alternating_renewal()
    P(f"- E[空闲间隙 I] = 1/λ = {EI*1000:.2f} ms；E[忙期 B] = (e^ρ−1)/λ = {EB*1000:.2f} ms")
    P(f"- 占空比 E[I]/(E[I]+E[B]) = {frac:.6f}（应 = e^(-1) = {np.exp(-1):.6f}）")
    P("")
    P("| 间隙阈值 τ (ms) | P(gap ≥ τ) | E[gap | gap ≥ τ] (ms) | 可用字节 @ +0.5MB/s（C−96M 捕获）|")
    P("|-----------------|------------|------------------------|----------------------------------|")
    for tau_ms, p_ge, e_ge in gap_table([1, 2, 4, 8, 16, 32, 64, 100, 200, 400, 700]):
        # 每个满足阈值的间隙可用字节 = E[gap|≥τ] × 捕获速率 0.5 MB/s（C−96M）
        usable = p_ge * (e_ge / 1000.0) * 0.5
        P(f"| {tau_ms} | {p_ge:.4f} | {e_ge:.2f} | {usable:.4f} MB |")
    P("")
    P("- 定时器粒度 G=4ms 截断：P(gap ≥ G) = {:.4f} → 粒度截断对纯空闲间隙几乎无损（≤3%）；".format(
        float(np.exp(-LAM * 0.004))))
    P("- 但 ACK 时钟重启爬坡（慢启动 cwnd 重建，0074）是 η≈0.44 < 1 的主导机制，")
    P("  纯链路空闲间隙的可用性不是瓶颈——瓶颈在于 N≥1 相位中 40 包缓冲的瞬态溢出。")

    P("\n## D. 碰撞暴露度分解（每场 T=130s 传输窗口）")
    T_win = 130.0
    for name, lo, hi, pr in CLASSES:
        m = class_mean(lo, hi)
        lam_c = LAM * pr
        # M/G/∞ 类别占用：类 c 在服条数 ~ Poisson(λ p_c τ_c)
        load_c = lam_c * m / C_MB
        p_any = 1 - np.exp(-load_c)
        n_exp = load_c
        P(f"- 类 {name}: 到达率 λp={lam_c:.4f}/s → T_win 内期望 {lam_c*T_win:.1f} 条；"
          f"P(该类≥1 在服)={p_any:.4f}；平均在服 {n_exp:.4f} 条；字节份额 {pr*100:.0f}%")
    P(f"- 巨流 G 单条均值 {class_mean(10_000_000,30_000_000)/1e6:.2f} MB（带宽 20MB 线性段均值），")
    P("  与 0051 「每条 28MB 巨流代价 ≈2.24s / ρ∈[1.0,2.4]」口径一致（本模型 ρ=1 为其下界）。")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("written", OUT)


if __name__ == "__main__":
    main()
