#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""任务 0073 — 全网拓扑丢尾队列在突发流涌入下的瞬态积压演化偏微分方程求解

模型（§一）：两层耦合的连续化流体模型。
  (PDE)  瓶颈上游链路管道：∂ρ/∂t + ∂F(ρ)/∂x = 0，Greenshields 归一化通量 F(ρ)=2ρ−ρ²，
         ρ∈[0,2]（ρ=1 为满线速容量点，ρ=2 堵塞），x∈[0,1] 以 BDP=729.2pkt 管道为单位，
         时间单位 = BDP/μ = 70ms（RTT₀ 正典）。
  (ODE)  交换机丢尾缓冲（0-D 质量平衡，即运动学波 PDE 的储罐极限）：
         dq/dt = λ(t) − μ·1{q>0}，服务 μ=C；丢尾吸收边界 q ≤ B_q=40pkt（0066 正典）。
突发涌入 = 边界需求阶跃；需求 g=λ/C>1 时管道上游形成堵塞激波（激波速 σ<0 向上游回传）。

解析结果：
  (i)   激波速 σ=(F(ρ_R)−F(ρ_L))/(ρ_R−ρ_L)（Rankine–Hugoniot），上游回传时间 = 1/|σ| 时间单位；
  (ii)  缓冲增长段 dQ/dt=λ_tot−C；溢出时间 T_ovf=(B_q−q₀)/(λ_tot−C)⁺；
        丢包量 D=(λ_tot−C)(t_b−T_ovf)⁺；峰值 Q_peak=min(B_q, q₀+(λ_tot−C)t_b)；
  (iii) 排空段 dQ/dt=−(1−α)C；满队列恢复 T_rec=B_q·L/((1−α)C)=96 ms（α=0.96，0066 一致）。

验证（§三/§四）：Godunov 有限体积（熵安全 Riemann 通量）验证激波运动学；
包级离散事件仿真（确定性种子）验证缓冲丢包质量平衡。
运行：python -I zcode/scripts/pde0073_droptail_backlog.py
"""

import math
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")

# ---------- 正典常数（0066/0051） ----------
C = 1.25e7                 # 100 Mbps (B/s)
L_PKT = 1200.0
MU_PKT = C / L_PKT         # 10416.7 pkt/s 线速服务率
B_Q = 40.0                 # 丢尾缓冲 (pkt)
BDP = C * 0.070 / L_PKT    # 729.2 pkt 管道容量（RTT0=70ms）
T_UNIT = BDP / MU_PKT      # 时间单位 = 70 ms
ALPHA_BG = 0.96            # 背景巨流占用份额（96M 稳态设计场景）

random.seed(20261107)

F = lambda r: 2 * r - r * r            # 归一化 Greenshields 通量（容量 1 @ ρ*=1）
DF = lambda r: 2 - 2 * r               # 特征速度


def godunov_flux(a, b):
    """凹通量 F(ρ)=2ρ−ρ² 的熵安全 Godunov 数值通量（Riemann 问题精确解通量）。"""
    if a == b:
        return F(a)
    if a < b:                                # 凹通量 + 状态上升 → 激波
        sigma = (F(b) - F(a)) / (b - a)
        return F(b) if sigma < 0 else F(a)   # 界面状态：σ>0 激波右移露出左状态 a；σ<0 反之
    # a > b → 稀疏波：扇形边缘速度 f'(a)（左）< f'(b)（右）
    if DF(a) > 0:                            # 扇形整体右移 → 界面见左状态
        return F(a)
    if DF(b) < 0:                            # 扇形整体左移 → 界面见右状态
        return F(b)
    return F(1.0)                            # 界面落在扇形内 → 容量点 ρ*=1


def godunov_riemann(rho_l, rho_r, T_units=1.0, nx=500, x0=0.5):
    """域内 Riemann 问题：ρ(x,0)=ρ_L (x<x0), ρ_R (x≥x0)，Godunov 推进，
    返回 (t, 波前位置 x_f) 轨迹与解析波速（激波 σ 或稀疏波右缘 f'(ρ_R)）。"""
    dx = 1.0 / nx
    dt = 0.4 * dx / 2.0                      # CFL：|F'|≤2
    nsteps = int(T_units / dt)
    i0 = int(x0 * nx)
    rho = [rho_l if i < i0 else rho_r for i in range(nx)]
    if rho_l < rho_r:                        # 凹通量 + 状态上升 → 激波
        speed_an = (F(rho_r) - F(rho_l)) / (rho_r - rho_l)
        kind = "shock"
    else:                                    # 状态下降 → 稀疏波，右缘速度 f'(ρ_R)
        speed_an = DF(rho_r)
        kind = "rarefaction"
    traj = []
    thr = rho_r + 0.25 * (rho_l - rho_r) if rho_l > rho_r else rho_l + 0.25 * (rho_r - rho_l)
    for step in range(nsteps):
        flux = [0.0] * (nx + 1)
        flux[0] = F(rho[0])                  # 左边界自由流出
        for i in range(1, nx):
            flux[i] = godunov_flux(rho[i - 1], rho[i])
        flux[nx] = F(rho[nx - 1])            # 右边界自由流出
        new = [0.0] * nx
        for i in range(nx):
            new[i] = rho[i] - dt / dx * (flux[i + 1] - flux[i])
        rho = new
        if step % max(1, nsteps // 50) == 0:
            t = step * dt
            mid = 0.5 * (rho_l + rho_r)
            xf = x0
            if kind == "shock":              # 右行激波：前沿 = 首个状态仍处高位（>中点）的格子左缘
                for i in range(i0, nx):
                    if rho[i] > mid:
                        xf = (i - 0.5) * dx
                        break
            else:                            # 稀疏波：阈值只追特征线，交由剖面自相似检验
                xf = x0
            traj.append((t, xf))
    return traj, speed_an, kind, rho


def analytic_buffer(burst_pkt, t_b_s, alpha_bg, q0_pkt=0.0, T_ms=260.0):
    """缓冲 ODE 分段线性解析解（§一(ii)(iii)）。"""
    lam_o = burst_pkt / t_b_s
    lam_tot = lam_o + alpha_bg * MU_PKT
    t1 = min(t_b_s, T_ms / 1000.0)
    dropped = 0.0
    q = q0_pkt
    t_ovf = float("inf")
    if lam_tot > MU_PKT:
        rate = lam_tot - MU_PKT
        if B_Q > q0_pkt:
            t_ovf = (B_Q - q0_pkt) / rate
        if t_ovf < t1:
            dropped = rate * (t1 - t_ovf)
            q = B_Q
        else:
            q = q0_pkt + rate * t1
    else:
        q = max(0.0, q0_pkt + (lam_tot - MU_PKT) * t1)
    q_peak = q
    drain_rate = (1.0 - alpha_bg) * MU_PKT
    t2 = T_ms / 1000.0
    if q > 0 and drain_rate > 0:
        q = max(0.0, q - drain_rate * (t2 - t1))
    t_rec = (q_peak - q0_pkt) / drain_rate if drain_rate > 0 else float("inf")
    return dropped, q_peak, t_rec, t_ovf


def packet_sim(burst_pkt, t_b_s, alpha_bg, q0_pkt=0.0, T_ms=260.0,
               poisson_bg=True, seed=20261107):
    """包级离散事件仿真，丢尾缓冲。poisson_bg=False 时背景为确定性等间隔
    （流体等价，直接与质量平衡闭式解对比）；True 时为泊松（配对差分用）。"""
    rng = random.Random(seed)
    lam_bg = alpha_bg * MU_PKT
    T = T_ms / 1000.0
    ev = []
    if lam_bg > 0:
        if poisson_bg:
            t = 0.0
            while True:                       # 背景泊松（时间反转法）
                t += rng.expovariate(lam_bg)
                if t > T:
                    break
                ev.append(t)
        else:
            n_bg = int(lam_bg * T)
            ev = [(i + 0.5) / lam_bg for i in range(n_bg)]
    if burst_pkt > 0:
        ev += [t_b_s * (i + 0.5) / burst_pkt for i in range(burst_pkt)]   # 我方突发均匀注入
    ev.sort()
    q, dropped, peak, last = q0_pkt, 0.0, q0_pkt, 0.0
    for a in ev:
        q = max(0.0, q - MU_PKT * (a - last))
        q += 1.0
        if q > B_Q:
            dropped += q - B_Q
            q = B_Q
        peak = max(peak, q)
        last = a
    return dropped, peak


def main():
    print(f"正典常数: C=100Mbps, μ={MU_PKT:.1f} pkt/s, B_q={B_Q:.0f}pkt, BDP={BDP:.1f}pkt, "
          f"时间单位={T_UNIT*1000:.1f}ms, 缓冲/BDP={B_Q/BDP:.4f}")

    # ---------- §二 激波/稀疏波运动学（PDE 层解析 vs Godunov） ----------
    print("\n== §二 管道波运动学：Rankine–Hugoniot/特征线 解析 vs Godunov 数值 ==")
    cases = [
        ("拥塞激波 (ρ_L,ρ_R)=(0.5,1.2)：突发涌入低载链路", 0.5, 1.2),
        ("驻波接触间断 (0.5,1.5)：等通量 F=0.75", 0.5, 1.5),
        ("拥塞回溢扇形 (2.0,0.8)：堵塞区侵入 96% 负载管", 2.0, 0.8),
    ]
    for name, rl, rr in cases:
        traj, speed_an, kind, rho_fin = godunov_riemann(rl, rr)
        t_last, x_last = traj[-1]
        if kind == "shock":
            x_an = 0.5 + speed_an * t_last
            err = abs(x_last - x_an) / max(abs(x_an - 0.5), 1e-9) * 100 if abs(speed_an) > 1e-12 else 0.0
            print(f"{name}")
            print(f"  解析激波速 = {speed_an:+.3f} 管道/单位(70ms)")
            print(f"  Godunov: t={t_last*T_UNIT*1000:.0f}ms  x_num={x_last:.3f}  x_an={x_an:.3f}  偏差 {err:.1f}%")
        else:
            # 稀疏波：自相似剖面 ρ(x/t)=1−x/(2t)（扇形 [f'(ρ_L), f'(ρ_R)] 内）逐格对比
            nx = len(rho_fin)
            dx = 1.0 / nx
            e_inf = e1 = 0.0
            for i in range(nx):
                x = (i + 0.5) * dx
                s = (x - 0.5) / t_last              # Riemann 坐标（间断在 x0=0.5）
                if s >= speed_an:
                    ra = rr
                elif s <= DF(rl):
                    ra = rl
                else:
                    ra = (2.0 - s) / 2.0            # DF(ρ)=s ⇒ ρ=(2−s)/2
                d = abs(rho_fin[i] - ra)
                e_inf = max(e_inf, d)
                e1 += d * dx
            print(f"{name}")
            print(f"  解析右缘速 = {speed_an:+.3f}（=f'(ρ_R) 特征），左缘速 = {DF(rl):+.3f}")
            print(f"  Godunov 剖面 vs 自相似解：L∞ = {e_inf:.4f}，L1 = {e1:.4f}（一阶格式 ~O(dx) 属正常扩散）")

    # ---------- §三 缓冲闭式解（ODE 层） ----------
    print("\n== §三 缓冲瞬态闭式解（丢尾质量平衡） ==")
    scen = [
        ("S1 纯我方60包突发(α=0) q0=0", 60, 0.004, 0.0, 0.0),
        ("S2 96%背景+60包突发 q0=0", 60, 0.004, ALPHA_BG, 0.0),
        ("S3 96%背景+60包突发 q0=20", 60, 0.004, ALPHA_BG, 20.0),
        ("S4 96%背景+40包突发 q0=20", 40, 0.004, ALPHA_BG, 20.0),
        ("S5 96%背景+40包突发 q0=0", 40, 0.004, ALPHA_BG, 0.0),
    ]
    print(f"{'场景':30s} {'λ_tot/s':>8} {'T_ovf(ms)':>10} {'D解析(pkt)':>11} {'Q_peak':>7} {'T_rec(ms)':>10}")
    res_an = {}
    for name, b, tb, al, q0 in scen:
        D, qp, trec, tovf = analytic_buffer(b, tb, al, q0)
        res_an[name] = (D, qp, trec)
        lam_tot = b / tb + al * MU_PKT
        print(f"{name:30s} {lam_tot:8.0f} {tovf*1000:10.2f} {D:11.2f} {qp:7.2f} {trec*1000:10.1f}")
    print(f"校验：T_rec(满队列, α=0.96) = 40pkt·1200B / 0.96Mbps = {B_Q*L_PKT/((1-ALPHA_BG)*C)*1000:.1f} ms（0066 正典 96.0 ms）")

    # ---------- §四 包级仿真真值 ----------
    print("\n== §四 包级离散事件仿真 vs 解析（确定性种子 20261107） ==")
    print(f"{'场景':30s} {'D_流体间隔':>10} {'D_解析':>9} {'D_泊松差分':>10} {'Q_peak流间':>11} {'Q_peak解析':>11}")
    for name, b, tb, al, q0 in scen:
        D_fluid, qp_fluid = packet_sim(b, tb, al, q0, poisson_bg=False)
        D_an, qp_an, _ = res_an[name]
        # 泊松背景下的边际突发丢包 = 有突发 − 无突发（同一随机流配对）
        D_with, _ = packet_sim(b, tb, al, q0, poisson_bg=True, seed=20261107)
        D_wo, _ = packet_sim(0, tb, al, q0, poisson_bg=True, seed=20261107)
        D_marg = D_with - D_wo
        print(f"{name:30s} {D_fluid:10.2f} {D_an:9.2f} {D_marg:10.2f} {qp_fluid:11.2f} {qp_an:11.2f}")
    # 背景自排队丢包地板（M/D/1 涨落，无我方突发）
    D_floor, _ = packet_sim(0, 0.004, ALPHA_BG, 0.0, poisson_bg=True, seed=20261107)
    print(f"\n无突发对照（泊松背景 α=0.96、260ms 窗）: D_floor = {D_floor:.2f} pkt（本窗经验值为 0）")
    print("泊松放大机制：突发把队列顶到满位后，排空期（~96ms）内到达的背景包在满位钉扎期被逐包削减，")
    print("边际丢包（含背景侧）≈ 解析值的 ~2×（S2: 37.97 vs 18.33）——突发对我方均值不利、对背景公平性亦不利。")

    # ---------- §五 工程结论 ----------
    print("\n== §五 工程结论 ==")
    D60_0, D40_0 = res_an["S2 96%背景+60包突发 q0=0"][0], res_an["S5 96%背景+40包突发 q0=0"][0]
    D60_20, D40_20 = res_an["S3 96%背景+60包突发 q0=20"][0], res_an["S4 96%背景+40包突发 q0=20"][0]
    print(f"饱和碰撞(α=0.96)我方丢包：B=60 vs B=40 → q0=0: {D60_0:.1f} vs {D40_0:.1f} pkt；q0=20: {D60_20:.1f} vs {D40_20:.1f} pkt")
    print("=> 大突发在饱和碰撞中丢包更多（PDE 机制层解释 0072 实测 B=60 均值 +4.8s 方向）")
    print("=> 碰撞后一次性整管回填降低场间方差（0072 F=3.99 p≈0.023）——均值/方差权衡的物理根源")
    print(f"=> 抗抖动杠杆是排空余量：T_rec=B_q·L/((1−α)C)：α=0.96→96ms，α=0.92→192ms（余量每减半，恢复翻倍）")
    print(f"=> 缓冲只占管道 {B_Q/BDP*100:.1f}%：积压主体在 BDP 管道与在途窗口（~700pkt），丢尾只在 40pkt 缓冲上触发")


if __name__ == "__main__":
    main()
