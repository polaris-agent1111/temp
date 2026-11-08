#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""任务 0071 — 官方 WebSearch 流长分布三阶矩与重尾极值定理严格解析推导（验证脚本）

对象分布：官方 12 节点分段线性 CDF（docs/extracted/websearch背景流量模型.md），
顶段 [10MB, 30MB] 恰好线性 => 上端点 ω=30MB 处 1-F(ω-t)=c·t^α（α=1, c=0.0015/MB），
属于反 Weibull（type-III，ξ=-1）最大值吸引域 —— 有限 n 恒等式在顶段**精确成立**。

本脚本全部使用 stdlib，确定性种子，输出供 docs/analysis/0071-theory-audit.md 引用。
运行：python -I zcode/scripts/evt0071_websearch_moments.py
"""

import math
import random
import json

random.seed(20261107)

# ---------- 官方 CDF（字节） ----------
KNOTS = [0, 10_000, 20_000, 30_000, 50_000, 80_000, 200_000,
         1_000_000, 2_000_000, 5_000_000, 10_000_000, 30_000_000]
PROBS = [0.0, 0.15, 0.20, 0.30, 0.40, 0.53, 0.60, 0.70, 0.80, 0.90, 0.97, 1.00]
OMEGA = KNOTS[-1]

MB = 1_000_000.0


def cdf(x):
    """分段线性 CDF 精确插值（官方规则：相邻节点线性插值）。"""
    if x <= 0:
        return 0.0
    if x >= OMEGA:
        return 1.0
    for a, b, fa, fb in zip(KNOTS, KNOTS[1:], PROBS, PROBS[1:]):
        if a <= x <= b:
            if b == a:
                return fb
            return fa + (fb - fa) * (x - a) / (b - a)
    return 1.0


def seg_raw_moment(k):
    """E[X^k] 精确值：每段密度均匀 s_j/(b-a)，闭式积分。"""
    total = 0.0
    for a, b, fa, fb in zip(KNOTS, KNOTS[1:], PROBS, PROBS[1:]):
        s = fb - fa
        if s <= 0 or b <= a:
            continue
        dens = s / (b - a)
        total += dens * (b ** (k + 1) - a ** (k + 1)) / (k + 1)
    return total


def abs_central_third(mu):
    """E|X-mu|^3 精确值：每段在 mu 处劈开，闭式积分。"""
    total = 0.0
    for a, b, fa, fb in zip(KNOTS, KNOTS[1:], PROBS, PROBS[1:]):
        s = fb - fa
        if s <= 0 or b <= a:
            continue
        dens = s / (b - a)

        def integ(lo, hi, sign):
            # ∫ sign*(x-mu)^3 dx on [lo,hi]
            F = lambda x: ((x - mu) ** 4) / 4.0
            return sign * (F(hi) - F(lo))

        if b <= mu:
            total += dens * integ(a, b, -1.0)
        elif a >= mu:
            total += dens * integ(a, b, 1.0)
        else:
            total += dens * (integ(a, mu, -1.0) + integ(mu, b, 1.0))
    return total


def mean_residual_life(x):
    """e(x) = E[X-x | X>x] = ∫_x^ω (1-F(t))dt / (1-F(x))，解析分段积分。"""
    sup = 1.0 - cdf(x)
    if sup <= 0:
        return 0.0
    acc = 0.0
    for a, b in zip(KNOTS, KNOTS[1:]):
        if b <= x:
            continue
        la = max(a, x)
        n_pts = 200
        h = (b - la) / n_pts
        seg = (cdf(la) - 1.0) / 2.0 + (cdf(b) - 1.0) / 2.0
        for i in range(1, n_pts):
            seg += cdf(la + i * h) - 1.0
        acc += seg * h          # 每段先乘步长再加总，累加器不做整体缩放
    return -acc / sup


def sample_flow(rng):
    """官方采样规则：U~Unif(0,1)，CDF 反插值。"""
    u = rng.random()
    for a, b, fa, fb in zip(KNOTS, KNOTS[1:], PROBS, PROBS[1:]):
        if u <= fb or b == OMEGA:
            if b == a:
                return b
            return a + (b - a) * (u - fa) / (fb - fa)
    return OMEGA


def expected_max(n):
    """E[M_n] = ∫_0^ω (1 - F(x)^n) dx（分段梯形，网格在节点处对齐）。
    顶段线性 => 有限 n 恒等式 1-(1-c(ω-x))^n 精确成立。"""
    total = 0.0
    for a, b in zip(KNOTS, KNOTS[1:]):
        m = 400
        h = (b - a) / m
        g = lambda x: 1.0 - cdf(x) ** n
        seg = g(a) / 2.0 + g(b) / 2.0
        for i in range(1, m):
            seg += g(a + i * h)
        total += seg * h        # 每段独立缩放
    return total


def main():
    out = {}
    mu = seg_raw_moment(1)
    m2 = seg_raw_moment(2)
    m3 = seg_raw_moment(3)
    m4 = seg_raw_moment(4)
    var = m2 - mu * mu
    sd = math.sqrt(var)
    mu3c = m3 - 3 * mu * m2 + 2 * mu ** 3          # 三阶中心矩
    gamma1 = mu3c / sd ** 3                          # 偏度
    mu4c = m4 - 4 * mu * m3 + 6 * mu * mu * m2 - 3 * mu ** 4
    gamma2 = mu4c / var ** 2 - 3.0                   # 超额峰度
    et3 = abs_central_third(mu)
    rho_be = et3 / sd ** 3                           # Berry-Esseen 比率

    print("== §2 精确矩（解析闭式） ==")
    print(f"E[S]        = {mu:,.0f} B = {mu/MB:.6f} MB   (0051 正典 1,711,250 B 校验: {'OK' if abs(mu-1711250)<1 else 'MISMATCH'})")
    print(f"E[S^2]      = {m2:.4e} B^2")
    print(f"E[S^3]      = {m3:.4e} B^3   <- 三阶（原点）矩")
    print(f"E[S^4]      = {m4:.4e} B^4")
    print(f"Var[S]      = {var:.4e} B^2,  SD = {sd/MB:.4f} MB,  CV = {sd/mu:.3f}")
    print(f"mu3 central = {mu3c:.4e} B^3   <- 三阶中心矩")
    print(f"偏度 gamma1 = {gamma1:.4f}")
    print(f"超额峰度    = {gamma2:.4f}")
    print(f"E|S-mu|^3   = {et3:.4e} B^3,  rho_BE = {rho_be:.3f}")
    out["moments"] = dict(mean=mu, m2=m2, m3=m3, m4=m4, var=var, sd=sd,
                          mu3=mu3c, gamma1=gamma1, gamma2=gamma2,
                          e_abs3=et3, rho_be=rho_be)

    print("\n== §3 重尾诊断 ==")
    print("局部 Pareto 指数（相邻节点 log-log 斜率, alpha = -d ln(1-F)/d ln x）:")
    for a, b, fa, fb in zip(KNOTS, KNOTS[1:], PROBS, PROBS[1:]):
        sa, sb = 1 - fa, 1 - fb
        if sa > 0 and sb > 0 and a > 0:
            alpha_loc = -(math.log(sb) - math.log(sa)) / (math.log(b) - math.log(a))
            print(f"  [{a/MB:7.3f},{b/MB:7.3f}] MB: 1-F {sa:.3f}->{sb:.3f},  alpha_local = {alpha_loc:+.3f}")
    print("平均剩余寿命 e(x)（真重尾应单调增；顶段必须衰减到 0 => 有界伪重尾）:")
    for x_mb in [0.1, 1.0, 2.0, 5.0, 10.0, 20.0, 28.0, 29.0]:
        x = x_mb * MB
        print(f"  e({x_mb:5.1f} MB) = {mean_residual_life(x)/MB:7.3f} MB   (1-F = {1-cdf(x):.4f})")
    print(f"P(X>10MB) = {1-cdf(10*MB):.3f};  E[S|S>10MB] = {_tail_contrib(10*MB)/(1-cdf(10*MB))/MB:.3f} MB")
    # 顶部字节占比 = (x·P + e(x)·P)/mu = E[S·1{S>x}]/mu
    tail10 = _tail_contrib(10 * MB)
    print(f"顶部 3%（≥10MB）流承载字节占比 = {tail10/mu*100:.1f}%")
    top5 = _tail_contrib(5 * MB)
    print(f"顶部 10%（≥5MB）流承载字节占比  = {top5/mu*100:.1f}%")
    out["tail"] = dict(p10=1 - cdf(10 * MB), tail10_share=tail10 / mu, top5_share=top5 / mu,
                       e10=mean_residual_life(10 * MB) / MB, e28=mean_residual_life(28 * MB) / MB)

    print("\n== §4 极值定理（上端点反 Weibull, ξ=-1） ==")
    lam = 12.5 / (mu / MB)   # 12.5 MB/s 占需求 / 均长
    print(f"lambda = 12.5MB/s / {mu/MB:.4f}MB = {lam:.4f} 条/s   (0051 正典 7.3046 校验: {'OK' if abs(lam-7.3046)<0.01 else 'MISMATCH'})")
    c_top = 0.03 / 20.0      # 顶段 1-F(x) = c·(30-x_MB), 单位 MB^-1
    print(f"顶段尾常数 c = {c_top} /MB,  alpha = 1  =>  xi = -1/alpha = -1（精确）")
    print(f"渐近标度: (ω-M_n)·c·n -> Exp(1);  b_n = 30 - 1/(c n) MB,  a_n = 1/(c n) MB")
    print(f"{'window(s)':>10} {'n=l·T':>8} {'E[M_n]解析(MB)':>14} {'b_n(MB)':>9} {'a_n(MB)':>9} {'P(M>=10M)':>10} {'P(M>=28M)':>10} {'E[#>=28M]':>10}")
    win = [2.30, 3.52, 5.14, 14.7, 33.2, 70.9, 129.7]
    table = []
    for T in win:
        n = lam * T
        em = expected_max(n)
        an = 1.0 / (c_top * n)
        bn = 30.0 - an
        p10 = 1 - (1 - 0.03) ** n
        p28 = 1 - (1 - 0.003) ** n
        print(f"{T:10.2f} {n:8.1f} {em/MB:14.3f} {bn:9.3f} {an:9.3f} {p10:10.4f} {p28:10.4f} {n*0.003:10.3f}")
        table.append(dict(T=T, n=n, Emax=em / MB, bn=bn, an=an, p10=p10, p28=p28, Ec28=n * 0.003))
    out["evt"] = dict(lam=lam, c=c_top, windows=table)

    print("\n== §5 Monte-Carlo 交叉验证（确定性种子 20261107） ==")
    rng = random.Random(20261107)
    N_MC = 400_000
    s1 = s2 = s3 = s4 = 0.0
    for _ in range(N_MC):
        x = sample_flow(rng)
        s1 += x; s2 += x * x; s3 += x ** 3; s4 += x ** 4
    emc = s1 / N_MC; v2 = s2 / N_MC; v3 = s3 / N_MC; v4 = s4 / N_MC
    v_m3c = v3 - 3 * emc * v2 + 2 * emc ** 3
    sd_mc = math.sqrt(v2 - emc ** 2)
    print(f"MC E[S]      = {emc:,.0f} B   解析 {mu:,.0f} B   偏差 {abs(emc-mu)/mu*100:.3f}%")
    print(f"MC E[S^3]    = {v3:.4e}     解析 {m3:.4e}     偏差 {abs(v3-m3)/m3*100:.3f}%")
    print(f"MC mu3(中心) = {v_m3c:.4e}     解析 {mu3c:.4e}     偏差 {abs(v_m3c-mu3c)/abs(mu3c)*100:.3f}%")
    print(f"MC 偏度      = {v_m3c/sd_mc**3:.4f}   解析 {gamma1:.4f}")
    # E[M_n] 验证：n=947（129.7s 全程窗口）
    n_check = 947
    m_max = 0.0
    p28_hit = 0
    reps = 40_000
    for _ in range(reps):
        mx = max(sample_flow(rng) for _ in range(n_check))
        m_max += mx
        if mx >= 28 * MB:
            p28_hit += 1
    em_mc = m_max / reps
    em_an = expected_max(n_check)
    print(f"MC E[M_{n_check}] = {em_mc/MB:.3f} MB   解析积分 {em_an/MB:.3f} MB   偏差 {abs(em_mc-em_an)/em_an*100:.2f}%")
    print(f"MC P(M>=28MB)     = {p28_hit/reps:.4f}   解析 1-(0.997)^{n_check} = {1-0.997**n_check:.4f}")
    # Hill 估计不稳定性：m 个最大次序统计量
    samples = sorted((sample_flow(rng) for _ in range(200_000)), reverse=True)
    hill = {}
    for m in [10, 50, 100, 500, 1000]:
        top = samples[:m]
        ref = samples[m]     # X_(m+1)
        alpha_h = m / sum(math.log(s / ref) for s in top if s > 0 and s > ref)
        hill[m] = alpha_h
        print(f"Hill alpha_hat(m={m:5d}) = {alpha_h:6.3f}   （顶段真 alpha=1；小 m 抖动大 => 有界分布上 Hill 不可辨识）")
    out["mc"] = dict(emc=emc, v3=v3, vm3c=v_m3c, g1mc=v_m3c / sd_mc ** 3,
                     em947_mc=em_mc / MB, em947_an=em_an / MB, p28mc=p28_hit / reps,
                     hill=hill)

    print("\n== §6 Berry-Esseen：窗口聚合字节正态近似误差界 ==")
    for T in [33.2, 70.9, 129.7]:
        n = lam * T
        be = 0.4748 * rho_be / math.sqrt(n)
        print(f"T={T:6.1f}s  n={n:7.1f}  BE 上界 = 0.4748·{rho_be:.2f}/√{n:.0f} = {be:.4f}"
              f"  （正态近似最大绝对误差 ≤ {be*100:.1f}%）")
    out["be"] = dict(T332=0.4748 * rho_be / math.sqrt(lam * 33.2),
                     T709=0.4748 * rho_be / math.sqrt(lam * 70.9),
                     T1297=0.4748 * rho_be / math.sqrt(lam * 129.7))

    with open(__file__.replace(".py", "_out.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\n[saved]", __file__.replace(".py", "_out.json"))


def _tail_contrib(x):
    """E[S·1{S>x}]（用于条件均值），解析分段。"""
    acc = 0.0
    for a, b, fa, fb in zip(KNOTS, KNOTS[1:], PROBS, PROBS[1:]):
        lo, hi = max(a, x), b
        if hi <= lo:
            continue
        s = fb - fa
        if s <= 0 or b <= a:
            continue
        dens = s / (b - a)
        acc += dens * (hi * hi - lo * lo) / 2.0
    return acc


if __name__ == "__main__":
    main()
