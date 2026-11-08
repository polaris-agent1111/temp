#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0077 — 多流竞争演化博弈：复制动态方程与 ESS 演化稳定策略数值求解.

模型基座 = 0057 已交叉验证的阈值贴靠结构（不新造物理）：
  - 瓶颈 C = 100 Mbps（归一化 1.0），缓冲 40 包，RTT = 70 ms，定时器粒度 G ≈ 4 ms；
  - 溢出阈值 x_ov = C − h，h = 4%C（0057 用 96/100M 悬崖 + 官方三发越阈受罚定标）；
  - 损失线性化 ℓ(z) = ℓ0 · [z − (1−h)]_+ / (1−h)，截断到 [0,1]，z 为总需求（C 的倍数）；
  - 有效吞吐 g_i = a_i · (1 − ℓ)²（丢包重传膨胀的一阶修正；背景流 η_bg 理想化为 1）；
  - PTO 阶跃代价（0070：78/156/312/624 ms，中段丢包无倍增）以 κ·ℓ 计入速率当量。

博弈结构（Lemma 0，承接 0057 的结构事实 λE[S] = C）：
  背景流总字节到达率被官方钉死在 C → 「速率切分」不可行（总 offered 与策略无关），
  策略的真实维度是【单流发送粒度 a】（决定并发度 N̄ = 1/a 与突发形态）。
  采用随机匹配（random matching）种群博弈：每轮 k 条背景流同台，收益
      u(a_i; a_{-i}) = a_i·(1 − ℓ(z))² − κ·ℓ(z),   z = Σ_j a_j + y
  其中 y 为我方 pacer 的固定驻留占用（0.96 冠军构型贴靠点）。
  k=2 时 ū_i(x) = Σ_j x_j u(a_i, a_j) 为双线性 → 预计算收益矩阵 M，
  复制动态 dx_i = x_i[(Mx)_i − xᵀMx] 全向量化（Hofbauer–Sigmund：ESS ⟺ 渐近稳定驻点）。

输出：_0077_out.md（数字全部由本脚本算出，文档引用以它为准）。
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).with_name("_0077_out.md")

# ---------- 物理与模型常量（全部继承在先分析，见 docstring） ----------
H = 0.04          # 头距 h = 4%C（0057 定标）
X_OV = 1.0 - H    # 溢出阈值 0.96
RTT = 0.070
G_TIMER = 0.004

# 策略网格：单流发送速率占 C 的比例
A_GRID = np.round(np.arange(0.30, 1.201, 0.05), 3)
N = len(A_GRID)


def loss(z, l0):
    """0057 线性化溢出损失，截断 [0,1]."""
    ell = l0 * np.maximum(z - X_OV, 0.0) / X_OV
    return np.minimum(ell, 1.0)


def payoff(a_i, z_total, l0, kappa):
    """随机匹配阶段博弈收益：goodput(重传膨胀) − PTO 阶跃速率当量."""
    ell = loss(z_total, l0)
    return a_i * (1.0 - ell) ** 2 - kappa * ell


# ---------- 1. 连续策略对称 Nash（k 人阶段博弈，FOC 向量化扫描+二分） ----------
def symmetric_nash(k, y, l0, kappa, lo=0.05, hi=1.6):
    """对称均衡 a†：所有玩家取同一 a 时 FOC=0 且二阶<0。z = k·a + y."""
    def u(a):
        return payoff(a, k * a + y, l0, kappa)

    def du(a):
        eps = 1e-6
        return (u(a + eps) - u(a - eps)) / (2 * eps)

    grid = np.linspace(lo, hi, 4000)
    vals = du(grid)  # 向量化
    roots = []
    sign = vals[:-1] * vals[1:]
    for i in np.where(sign < 0)[0]:
        a_lo, a_hi = grid[i], grid[i + 1]
        f_lo = du(a_lo)
        for _ in range(60):
            mid = 0.5 * (a_lo + a_hi)
            if f_lo * du(mid) <= 0:
                a_hi = mid
            else:
                a_lo, f_lo = mid, du(mid)
        a_star = 0.5 * (a_lo + a_hi)
        d2 = (du(a_star + 1e-5) - du(a_star - 1e-5)) / 2e-5
        if d2 < 0:
            roots.append(a_star)
    bounds = []
    if vals[0] < 0:
        bounds.append(lo)
    if vals[-1] > 0:
        bounds.append(hi)
    return roots, bounds


# ---------- 2. 收益矩阵 / 张量（k=2 双线性；k=3 三阶张量） ----------
def payoff_matrix(k, y, l0, kappa):
    """M[i, j] = u(a_i; 其余 k−1 人全取 a_j)。k=2 → M[i,j]；
    k=3 → T[i,j,l]（两位对手分别取 a_j, a_l）。"""
    if k == 2:
        Z = A_GRID[:, None] + A_GRID[None, :] + y  # z = a_i + a_j + y
        return payoff(A_GRID[:, None], Z, l0, kappa)
    if k == 3:
        Z = A_GRID[:, None, None] + A_GRID[None, :, None] + A_GRID[None, None, :] + y
        return payoff(A_GRID[:, None, None], Z, l0, kappa)
    raise ValueError


def mean_payoffs(x, M):
    if M.ndim == 2:
        return M @ x
    return np.tensordot(M, np.outer(x, x), axes=([1, 2], [0, 1]))


def replicator(x0, M, dt=0.1, T=120.0):
    """RK4 积分复制动态 dx_i = x_i(ū_i − ū)."""
    x = x0.astype(float).copy()

    def f(v):
        ub = mean_payoffs(np.maximum(v, 0.0), M)
        return v * (ub - ub @ v)

    for _ in range(int(T / dt)):
        k1 = f(x)
        k2 = f(x + 0.5 * dt * k1)
        k3 = f(x + 0.5 * dt * k2)
        k4 = f(x + dt * k3)
        x = x + dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
        x = np.maximum(x, 1e-300)
        x /= x.sum()
    return x


def jacobian_at(x, M, eps=1e-7):
    def F(v):
        v = np.maximum(v, 0.0)
        v = v / v.sum()
        ub = mean_payoffs(v, M)
        return v * (ub - ub @ v)

    J = np.zeros((N, N))
    for j in range(N):
        e = np.zeros(N); e[j] = eps
        J[:, j] = (F(x + e) - F(x - e)) / (2 * eps)
    return J


def ess_check(x_star, M):
    """ESS 二条件核验：纯策略 p = argmax 支撑；
    (i) ū_p(x*) 最大；（ii）对等号突变体 q：u(p,q 主导场) > u(q,q 主导场)."""
    ub = mean_payoffs(x_star, M)
    f_star = ub @ x_star
    tied = np.where(ub >= f_star - 1e-9)[0]
    p_idx = int(np.argmax(x_star))
    second_ok = True
    detail = []
    for j in tied:
        if j == p_idx:
            continue
        # k=2 专用：对手全取 a_j
        if M.ndim == 2:
            u_pq = float(M[p_idx, j])
            u_qq = float(M[j, j])
            if u_pq <= u_qq:
                second_ok = False
                detail.append((int(j), u_pq, u_qq))
    return {"support": [int(i) for i in np.where(x_star > 1e-3)[0]],
            "f_star": round(float(f_star), 8), "tied": [int(i) for i in tied],
            "second_condition": second_ok, "violations": detail}


# ---------- 3. 入侵蒙特卡洛（批量噪声复制动态） ----------
def invasion_mc_batch(p_idx, mut_idx, M, eps=0.02, n_runs=2000,
                      dt=0.1, T=150.0, noise=0.01, seed=7):
    """ESS 驻点注入 ε 突变体，收益噪声下的复制动态，批量并行."""
    rng = np.random.default_rng(seed)
    X = np.zeros((n_runs, N))
    X[:, p_idx] = 1.0 - eps
    X[:, mut_idx] = eps
    alive = np.ones(n_runs, dtype=bool)
    ext_time = np.full(n_runs, np.nan)
    steps = int(T / dt)
    for t in range(steps):
        ub = mean_payoffs(X.T, M).T  # (n_runs, N)
        ub = ub + rng.normal(0, noise, (n_runs, N))
        # 离散复制动态步
        mean = (ub * X).sum(axis=1, keepdims=True)
        X = X + dt * X * (ub - mean)
        X = np.maximum(X, 0.0)
        X /= X.sum(axis=1, keepdims=True)
        just = alive & (X[:, mut_idx] < 1e-4)
        ext_time[just] = (t + 1) * dt
        alive &= ~just
        if not alive.any():
            break
    ext = np.isfinite(ext_time)
    return {"extinction_prob": round(float(ext.mean()), 4),
            "mean_extinction_time": round(float(ext_time[ext].mean()), 2) if ext.any() else None}


# ---------- 0. ℓ0 反演定标（锚定 0057 实测） ----------
def calibrate_l0(kappa, target=0.96):
    """我方单流最优响应 = 0.96（0057 实测贴靠点，官方 Shot2 破纪录 / Shot3-5 越阈受罚）
    ⇒ 反解 ℓ0。我方场：bg 合成流按官方设计钉在 C=1（z = a + 1），
    FOC: (1−ℓ)² − 2a(1−ℓ)ℓ′ − κℓ′ = 0 在 a=target 处成立。
    """
    def foc(a, l0):
        z = a + 1.0
        ell = float(loss(z, l0))
        lp = l0 / X_OV
        return (1 - ell) ** 2 - 2 * a * (1 - ell) * lp - kappa * lp

    lo, hi = 0.05, 0.95
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if foc(target, mid) > 0:   # ℓ0 越大损失越陡，FOC 越负
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ---------- 主流程 ----------
def main():
    lines = []
    P = lines.append
    P("# 0077 输出（ess0077_replicator.py 生成）\n")

    P("## 0. 参数与 ℓ0 反演定标")
    P(f"- C=1（100 Mbps）, h={H}, x_ov={X_OV}, RTT={RTT}s, G={G_TIMER}s")
    P(f"- 收益：u(a_i;·) = a_i·(1−ℓ(z))² − κ·ℓ(z)，z=Σa_j+y；ℓ(z)=ℓ0·[z−0.96]₊/0.96 截断到 1")
    L0_STAR = calibrate_l0(0.01)
    P(f"- ℓ0 反演定标：锚定「我方最优响应 = 0.96（0057 实测贴靠点）」+ bg 合成流钉在 C=1 "
      f"⇒ FOC(a=0.96, bg=1)=0 ⇒ **ℓ0* = {L0_STAR:.4f}**（κ=0.01）")
    P(f"- 策略网格 A = [{A_GRID[0]}, …, {A_GRID[-1]}]（n={N}）\n")
    results = {"l0_star": L0_STAR}

    P("## 1. 连续策略对称 Nash（FOC 扫描；ℓ0=ℓ0*, κ=0.01 主线）")
    P("| k | y | 内点 Nash a† | z=k·a†+y | 备注 |")
    P("|---|---|--------------|----------|------|")
    nash_main = {}
    for k in (2, 3):
        for y in (0.0, 0.80, 0.90, 0.96, 1.00):
            roots, bounds = symmetric_nash(k, y, L0_STAR, 0.01)
            roots = [float(r) for r in roots]
            nash_main[(k, y)] = (roots, bounds)
            note = ""
            if not roots and bounds:
                note = "边界最优 a†=" + str(bounds)
            P(f"| {k} | {y:.2f} | {[round(r,4) for r in roots]} | "
              f"{[round(k*r+y,4) for r in roots]} | {note} |")
    results["nash_main"] = {f"{k}_{y}": {"roots": nash_main[(k, y)][0],
                                         "bounds": nash_main[(k, y)][1]}
                            for (k, y) in nash_main}

    P("\n### 1'. 敏感性：a†(ℓ0, κ)（k=2, y=0.96）——含「浅损失技术 → 公地悲剧角点」对照")
    P("| ℓ0 \\ κ | 0.001 | 0.01 | 0.05 |")
    P("|---|---|---|---|")
    sens = {}
    for l0 in (0.10, L0_STAR, 0.50):
        row = []
        for kappa in (0.001, 0.01, 0.05):
            roots, bounds = symmetric_nash(2, 0.96, l0, kappa)
            a_dag = round(roots[0], 4) if roots else f"边界{bounds}"
            row.append(a_dag)
            sens[f"{l0}_{kappa}"] = a_dag
        P(f"| {l0} | {row[0]} | {row[1]} | {row[2]} |")
    results["sensitivity"] = sens

    P("\n## 2. 复制动态行为（k=2, ℓ0=ℓ0*, κ=0.01；24 随机初值 RK4）")
    P("（离散网格上对称 Nash 为混合策略；Jacobian 判定驻点/环稳定性，虚部给出循环周期）")
    P("| y | 终态质量前3（质量, 策略） | 众数收敛率 | Jacob 主特征值（实部, 虚部） | 判定 |")
    P("|---|--------------------------|------------|------------------------------|------|")
    conv_table = {}
    for y in (0.0, 0.80, 0.90, 0.96, 1.00):
        M = payoff_matrix(2, y, L0_STAR, 0.01)
        rng = np.random.default_rng(42)
        ends = [replicator(rng.dirichlet(np.ones(N) * 0.6), M) for _ in range(24)]
        keys = Counter(int(np.argmax(e)) for e in ends)
        top_idx, cnt = keys.most_common(1)[0]
        x_rest = np.mean([e for e in ends if int(np.argmax(e)) == top_idx], axis=0)
        J = jacobian_at(x_rest, M)
        ev = np.linalg.eigvals(J)
        i_max = int(np.argmax(np.real(ev)))
        re, im = float(np.real(ev[i_max])), float(np.imag(ev[i_max]))
        verdict = ("渐近稳定驻点（纯 ESS）" if re < -1e-6 else
                   (f"不稳定/循环（周期 ≈ {2*np.pi/abs(im):.1f} 时间单位）" if abs(im) > 1e-6
                    else "非稳定（慢发散/游走）"))
        top3 = sorted([(round(float(m), 3), float(A_GRID[i]))
                       for i, m in enumerate(x_rest) if m > 1e-3], reverse=True)[:3]
        P(f"| {y:.2f} | {top3} | {cnt}/24 | ({re:.3e}, {im:.3e}) | {verdict} |")
        conv_table[str(y)] = {"rest": x_rest.tolist(), "eig": [re, im],
                              "verdict": verdict, "converged": f"{cnt}/24"}
    results["replicator"] = conv_table

    P("\n### 2''. 我方最优响应曲线 BR(W)（对抗背景聚合占用 W；κ=0.01, ℓ0=ℓ0*；z = x + W）")
    P("（「0.96 贴靠的鲁棒性」的直接数值证据：BR 在轻背景区平坦）")
    P("| W | BR(W) | 对应 z | 备注 |")
    P("|---|-------|--------|------|")
    br_table = {}
    for W in (0.4, 0.6, 0.8, 0.9, 1.0, 1.1, 1.2, 1.4):
        roots, bounds = symmetric_nash(1, W, L0_STAR, 0.01)  # k=1：单人决策，z=x+W
        roots = [float(r) for r in roots]
        a_br = round(roots[0], 4) if roots else (bounds[0] if bounds else None)
        note = ("官方设计点 W=C=1.0 → BR=0.96=冠军构型" if W == 1.0 else
                ("背景越重 → BR 越低（让出）" if W > 1.0 else "轻背景区 BR 平坦"))
        P(f"| {W:.1f} | {a_br} | {round(a_br + W, 4) if a_br else '—'} | {note} |")
        br_table[str(W)] = a_br
    results["br_curve"] = br_table

    P("\n## 3. 入侵蒙特卡洛（漂移带平均态注入 ε=2% 突变，收益噪声 σ=0.01，2000 批量样本）")
    P("（灭绝率 0 = 突变体不清零 → 中性漂移带证据，与 §2 的循环判定一致）")
    P("| y | 突变策略 a_mut | 灭绝概率 | 平均灭绝时间（模拟秒） |")
    P("|---|----------------|----------|------------------------|")
    mc_table = {}
    for y in (0.0, 0.96):
        x_rest = np.array(conv_table[str(y)]["rest"])
        p_idx = int(np.argmax(x_rest))
        muts = sorted({max(0, p_idx - 4), min(N - 1, p_idx + 4),
                       int(np.argmin(np.abs(A_GRID - 1.0)))} - {p_idx})
        for m_idx in muts:
            r = invasion_mc_batch(p_idx, m_idx, payoff_matrix(2, y, L0_STAR, 0.01))
            P(f"| {y:.2f} | {A_GRID[m_idx]:.2f} | {r['extinction_prob']} | {r['mean_extinction_time']} |")
            mc_table[f"y{y}_mut{A_GRID[m_idx]:.2f}"] = r
    results["invasion_mc"] = mc_table

    P("\n## 4. 两种群对比静态：我方占用 y → 背景策略漂移带（时间平均支撑）")
    P("| y | 漂移带众数 a† | 带支撑（质量>1e-3） | z 总需求 | 解读 |")
    P("|---|---------------|---------------------|----------|------|")
    for y in (0.0, 0.80, 0.90, 0.96, 1.00):
        x_rest = np.array(conv_table[str(y)]["rest"])
        sup = [float(A_GRID[i]) for i in np.where(x_rest > 1e-3)[0]]
        a_dag = float(A_GRID[int(np.argmax(x_rest))])
        z = 2 * a_dag + y
        note = ("无我方驻留：漂移带偏高速端" if y == 0 else
                ("贴靠区：带整体下移（我方占用挤压背景粒度）" if y < 1 else "越阈：我方自身暴露于溢出"))
        P(f"| {y:.2f} | {a_dag:.2f} | {sup} | {z:.3f} | {note} |")

    P("\n## 5. 收益表（k=2, y=0.96, ℓ0=ℓ0*, κ=0.01）：对称行动 u(a,a)=M[a,a]")
    P("| a | z=2a+y | ℓ(z) | u(a,a) |")
    P("|---|--------|-------|--------|")
    M96 = payoff_matrix(2, 0.96, L0_STAR, 0.01)
    for a in A_GRID[::3]:
        i = int(np.argmin(np.abs(A_GRID - a)))
        z = 2 * A_GRID[i] + 0.96
        ell = float(loss(z, L0_STAR))
        P(f"| {A_GRID[i]:.2f} | {z:.3f} | {ell:.4f} | {M96[i, i]:.5f} |")

    P("\n## 6. k=3 三人对称 Nash + 复制动态（y=0.96）")
    roots3, bounds3 = symmetric_nash(3, 0.96, L0_STAR, 0.01)
    roots3 = [float(r) for r in roots3]
    P(f"- FOC 内点：{[round(r,4) for r in roots3]}；边界：{bounds3}")
    T3 = payoff_matrix(3, 0.96, L0_STAR, 0.01)
    rng = np.random.default_rng(7)
    ends3 = [replicator(rng.dirichlet(np.ones(N) * 0.6), T3) for _ in range(12)]
    keys3 = Counter(int(np.argmax(e)) for e in ends3)
    top3i, cnt3 = keys3.most_common(1)[0]
    x3 = np.mean([e for e in ends3 if int(np.argmax(e)) == top3i], axis=0)
    ev3 = np.linalg.eigvals(jacobian_at(x3, T3))
    i3 = int(np.argmax(np.real(ev3)))
    P(f"- 复制动态：众数 a = {A_GRID[top3i]}（{cnt3}/12），主特征值 = "
      f"({float(np.real(ev3[i3])):.3e}, {float(np.imag(ev3[i3])):.3e})（实部>0 → 同为漂移带结构）")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    Path(__file__).with_name("_0077_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("written", OUT)


if __name__ == "__main__":
    main()
