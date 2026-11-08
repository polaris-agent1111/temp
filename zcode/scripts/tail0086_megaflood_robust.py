# -*- coding: utf-8 -*-
"""0086 — 极端高压重尾背景流下长连接吞吐衰减鲁棒性压力测试与最恶劣工况下确界.

纯本地闭门计算（numpy，无网络；seed 固定可复现）。
口径继承（全部出自仓库既有审计）：B=40 drop-tail、mu=10416.667 pkt/s（100Mbps/1200B）、
RTT=70ms、背景流长 11 节点分段线性 CDF（0→30MB，E[S]=1,711,250B，lambda=7.3046 flows/s）、
我方 pacer g=9000 pkt/s（leak 36/4ms，Shot2 冠军 bins5-6）。

分层设计：
  解析层   CDF 复核 + 窗口巨流命中概率 + E[最大流]。
  仿真层   逐 RTT 流体步进（delta=RTT，向量化 across seeds），我方闭环 cwnd +
           背景聚合速率控制器。子 RTT 批量结构由 0085 覆盖，本层回答长窗口吞吐。
  确界层   与仿真无关的三明治：cmin 钉死上界 / 排队份额地板 / 经验地板 / 仿真对抗值。

我方 CC 三风味（官方客户端 CC 族不可知 → 最坏确界按族条件化）：
  reno  : SS 倍增 → CA +1 MSS/RTT，丢包减半（最悲观）
  cubic : SS 倍增 → CA +max(1, 10%*cwnd)/RTT（CUBIC 大窗口近似）
  bbr   : 纯开环 pacing，loss 不闭环（对 我方 最有利 → 完成时间下界书挡）

背景情景：
  grid{rho}          非响应 Poisson 聚合，强度 rho*mu（0085 §5 语义 + 我方闭环）
  mega_resp          开局 2.4s 一条 30MB 巨流按线速 mu 泵入、响应式（有丢包减半），其后 N~Poisson(1) 响应式
  mega_fire          开局 2.4s 非响应火龙（rho=1.0 恒定），其后 rho=0.44 定态非响应
  saturate           永久非响应 rho=1.0（连续 30MB 巨流链极限）
输出: zcode/scripts/_0086_out.md
"""
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

OUT = r"E:/Download/iDSN/zcode/scripts/_0086_out.md"

# ---------- 常量（继承仓库口径） ----------
C_BPS = 12.5e6
MSS = 1200.0
MU = C_BPS / MSS          # 10416.667 pkt/s
RTT = 0.070
B = 40.0
G = 9000.0
IW = 10.0
CMIN = 2.0
SIZES = {5: 160e6, 6: 320e6}
SEED = 42
NSEED = 4000
T_MAX = 600.0

CDF_X = np.array([0, 1e4, 2e4, 3e4, 5e4, 8e4, 2e5, 1e6, 2e6, 5e6, 1e7, 3e7], float)
CDF_F = np.array([0, .15, .20, .30, .40, .53, .60, .70, .80, .90, .97, 1.00])
LAMBDA_F = 7.3046


def cdf_checks():
    seg_p = np.diff(CDF_F)
    seg_mid = (CDF_X[:-1] + CDF_X[1:]) / 2
    e_s = float((seg_p * seg_mid).sum())
    p10 = 1 - float(np.interp(10e6, CDF_X, CDF_F))
    p28 = 1 - float(np.interp(28e6, CDF_X, CDF_F))
    rows = [("E[S] (B)", f"{e_s:,.0f}", "解析口径 1,711,250"),
            ("P(S>=10MB) / 条", f"{p10:.4f}", "解析口径 0.0300"),
            ("P(S>=28MB) / 条", f"{p28:.4f}", "解析口径 0.00300")]
    win = []
    for b, size in SIZES.items():
        for label, win_t in (("满速窗", size / C_BPS), ("实测份额窗(0.42C)", size / (0.42 * C_BPS))):
            n_f = LAMBDA_F * win_t
            p_hit28 = 1 - (1 - p28) ** n_f
            xs = np.linspace(0, 30e6, 3001)
            Fs = np.interp(xs, CDF_X, CDF_F)
            emax = float(np.trapezoid(1 - Fs ** n_f, xs))
            win.append((f"{b}.bin {label}", f"{win_t:.1f}", f"{n_f:.0f}",
                        f"{p_hit28*100:.1f}%", f"{emax/1e6:.2f}"))
    return rows, win


CC_ID = {"reno": 1, "cubic": 2, "bbr": 3}
SC_ID = {"mega_resp": 10, "mega_fire": 11, "saturate": 12,
         "grid0.25": 21, "grid0.50": 22, "grid0.75": 23, "grid1.00": 24}


def simulate(bin_no, cc, scenario, nseed=NSEED, seed=SEED, t_max=T_MAX):
    rng = np.random.default_rng(seed * 1_000_003 + bin_no * 1000 + CC_ID[cc] * 97 + SC_ID[scenario])
    n = nseed
    q = np.zeros(n)
    cw = np.full(n, IW)
    ss = np.ones(n, bool)
    rb = np.zeros(n)
    delivered = np.zeros(n)
    t_done = np.full(n, np.nan)
    target = SIZES[bin_no]
    dt = RTT
    if scenario.startswith("grid"):
        rho = float(scenario[4:])
        sat0, mega_resp, rho_after = 0.0, False, rho
    elif scenario == "mega_resp":
        sat0, mega_resp, rho_after = 2.40, True, None
    elif scenario == "mega_fire":
        sat0, mega_resp, rho_after = 2.40, False, 0.44
    elif scenario == "saturate":
        sat0, mega_resp, rho_after = 1e9, False, 1.00
    else:
        raise ValueError(scenario)
    sat = np.full(n, sat0)
    rb = np.where(sat > 0, MU, 0.0)   # 对抗巨流开局即按线速压顶（最恶劣）
    t = 0.0
    while t < t_max and np.isnan(t_done).any():
        in_sat = sat > 0
        if mega_resp or rho_after is None:
            n_active = rng.poisson(1.0, n)
            demand = np.where(in_sat, MU, n_active * MU)
            rb = np.minimum(demand, rb + 0.5 * (demand - rb))
            bg_resp = True
        else:
            rb_eff = np.where(in_sat, MU, rho_after * MU)
            bg_resp = False
        off_o = (G * dt) if cc == "bbr" else np.minimum(G, cw / RTT) * dt
        off_b = rb_eff * dt if not bg_resp else rb * dt
        tot = off_o + off_b
        cap = MU * dt + np.maximum(0.0, B - q)
        overflow = np.maximum(0.0, tot - cap)
        accepted = tot - overflow
        share = accepted / np.maximum(tot, 1e-12)
        acc_o = off_o * share
        q = np.clip(q + accepted - MU * dt, 0.0, B)
        # 我方丢包事件：期望丢包数（泊松稀释）→ 事件概率（0.99 分位封顶避免过触发）
        exp_loss_o = off_o * overflow / np.maximum(tot, 1e-12)
        loss_o = rng.random(n) < (1.0 - np.exp(-exp_loss_o))
        if cc != "bbr":
            # 丢包响应（每 RTT 至多一次乘性减；SS 丢包同样减半并永久退出慢启动）
            cw = np.where(loss_o, np.maximum(CMIN, cw * 0.5), cw)
            ss = ss & (~loss_o)
            # 无损 RTT 增长；cwnd 达 pacer 不再受限阈值即自然退出慢启动
            ss = ss & (cw < 2.0 * G * RTT)
            cw = np.where(ss & ~loss_o, cw * 2.0, cw)
            if cc == "reno":
                cw = np.where(~ss & ~loss_o, cw + 1.0, cw)
            elif cc == "cubic":
                cw = np.where(~ss & ~loss_o, cw + np.maximum(1.0, 0.1 * cw), cw)
        if bg_resp:
            rb = np.where((overflow > 1e-12) & (off_b > 0), np.maximum(50.0, rb * 0.5), rb)
        delivered += acc_o * MSS
        t += dt
        sat = np.maximum(0.0, sat - dt)
        fresh = np.isnan(t_done) & (delivered >= target)
        if fresh.any():
            prev = delivered - acc_o * MSS
            frac = (target - prev) / np.maximum(acc_o * MSS, 1e-9)
            t_done = np.where(fresh, t - dt + np.clip(frac, 0, 1) * dt, t_done)
    return t_done


def stat_line(t_done, target):
    ok = t_done[~np.isnan(t_done)]
    if len(ok) == 0:
        return f"0/{len(t_done)} 完成（>{t_max_show:.0f}s 截断）"
    ideal = target / C_BPS
    return (f"{len(ok)}/{len(t_done)}  mean={ok.mean():.1f}s  std={ok.std():.1f}  "
            f"p50={np.percentile(ok,50):.1f}  p95={np.percentile(ok,95):.1f}  "
            f"max={ok.max():.1f}  (满速 {ideal:.1f}s)")


t_max_show = T_MAX


def analytic_bounds():
    """与仿真无关的确界三明治。"""
    anchors = {5: 33.2, 6: 64.1}   # Shot2 冠军 124.37s 的 bin 分解锚点（非上界，仅参照）
    rows = []
    for b, size in SIZES.items():
        t_ideal = size / C_BPS
        # Tier-0 绝对上界：loss-based CC 被持续饱和钉死在 cmin（2 pkts/RTT）
        r_cmin = CMIN * MSS / RTT            # B/s
        t0 = size / r_cmin
        # Tier-1 开环/BBR 排队份额地板：drop-tail 份额 ≈ g/(g+rho*mu)*mu，rho=1 最恶劣
        r_share = MU * G / (G + MU)          # pkt/s
        t1 = size / (r_share * MSS)
        # Tier-2 经验锚点：Shot2 冠军分解（124.37 = 2.6+3.9+5.7+14.7+33.2+64.1）
        t2 = anchors[b]
        rows.append((f"{b}.bin", f"{t_ideal:.1f}s", f"{t0:,.0f}s",
                     f"{t1:.1f}s", f"{t2:.1f}s"))
    return rows


def main():
    out = []
    w = out.append
    w("# 0086 计算输出（tail0086_megaflood_robust.py）")
    w("")
    w("## 0. CDF 解析复核与窗口巨流命中")
    w("")
    rows, win_rows = cdf_checks()
    w("| 量 | 数值 | 对比 |")
    w("|---|---|---|")
    for r in rows:
        w(f"| {r[0]} | {r[1]} | {r[2]} |")
    w("")
    w("| 窗口 | 长度 s | 期望流数 | P(≥1 条≥28MB) | E[最大流] MB |")
    w("|---|---|---|---|---|")
    for r in win_rows:
        w("| " + " | ".join(r) + " |")
    w("")
    bounds = analytic_bounds()
    w("## 0b. 解析确界三明治（与 CC/情景仿真无关的框架值）")
    w("")
    w("| bin | 满速下界 | Tier-0 cmin 钉死上界 | Tier-1 排队份额地板(g/(g+mu)*mu) | Tier-2 官方经验 6.bin 锚点 |")
    w("|---|---|---|---|---|")
    for r in bounds:
        w("| " + " | ".join(r) + " |")
    w("")
    for bin_no in (5, 6):
        w(f"## {bin_no}.bin 闭环仿真（NSEED={NSEED}, seed={SEED}, Δ=RTT=70ms 流体步进）")
        w("")
        w("| 情景 | CC 风味 | 完成时间分布（s） |")
        w("|---|---|---|")
        for scenario in ("grid0.25", "grid0.50", "grid0.75", "grid1.00",
                         "mega_resp", "mega_fire", "saturate"):
            for cc in ("reno", "cubic", "bbr"):
                td = simulate(bin_no, cc, scenario)
                w(f"| {scenario} | {cc} | {stat_line(td, SIZES[bin_no])} |")
        w("")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("written", OUT)


if __name__ == "__main__":
    main()
