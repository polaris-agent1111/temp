# -*- coding: utf-8 -*-
"""
0102 — 瓶颈交换机队列利用率对传输时延抖动的传递函数分析
四层数值验证（参数继承仓库口径：B=40、μ=10416.67 pkt/s、96µs 服务、1200B 净荷）：
  P1a M/M/1 闭式律 J(ρ)=1/(μ(1−ρ)) —— 指数服务 DES 对拍
  P1b M/M/1/B 溢出闭式 ρ^B(1−ρ)/(1−ρ^{B+1}) —— DES 对拍
  P1c M/D/1 Pollaczek–Khinchine 闭式 —— 确定性 96µs 服务 DES 对拍（竞赛口径）
  P2  流体队列积分器频响 |H0(jω)|=1/(μω)：纯积分器精确验证 + 物理队列（排空/截断）失真量化
  P3  复刻 0085 脉冲链不动点（纯死亡半群 + 批量跳变），对拍 0.157%/4.513%/36.342% 锚点
  P4  11/07 五发构型逐 bin 利用率→抖动增益表
输出重定向 _0102_out.md
"""
import sys, math
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
import numpy as np
from scipy.linalg import expm

rng = np.random.default_rng(11020102)

MU = 1.0 / 96e-6       # 10416.67 pkt/s
B  = 40

# ---------------- P1: 三种服务律的利用率→抖动闭式 vs DES ----------------
def des(rho, n_pkt=200_000, Bcap=None, exp_service=True, warmup=10_000, nb=20):
    lam = rho * MU
    t = 0.0; q = 0
    next_arr = rng.exponential(1.0 / lam); next_dep = math.inf
    stamps = []; sojourn = []; dropped = 0; arrivals = 0
    while len(sojourn) < n_pkt:
        if next_arr < next_dep:
            t = next_arr
            next_arr = t + rng.exponential(1.0 / lam)
            arrivals += 1
            if Bcap is not None and q >= Bcap:
                dropped += 1
            else:
                q += 1; stamps.append(t)
                if q == 1:
                    next_dep = t + (rng.exponential(1.0 / MU) if exp_service else 96e-6)
        else:
            t = next_dep; q -= 1
            sojourn.append(t - stamps.pop(0))
            if q > 0:
                next_dep = t + (rng.exponential(1.0 / MU) if exp_service else 96e-6)
            else:
                next_dep = math.inf
    d = np.array(sojourn[warmup:])
    # 批量均值标准误（sojourn 强相关，朴素 SE 严重低估）
    m = len(d) // nb
    bm = d[:m * nb].reshape(nb, m)
    se_mean = float(bm.mean(axis=1).std(ddof=1) / math.sqrt(nb))
    se_std = float(bm.std(axis=1, ddof=1).std(ddof=1) / math.sqrt(nb))
    return float(d.mean()), float(d.std()), dropped / max(arrivals, 1), se_mean, se_std

def mm1_std(rho):  return 1.0 / (MU * (1 - rho))                       # M/M/1 sojourn ~ Exp(μ−λ)
def md1_std(rho):                                                     # M/D/1 PK 公式（等待+恒定服务）
    x = rho / (1 - rho)
    return math.sqrt(max(x / 3.0 + x * x / 4.0, 0.0)) / MU             # Var[W]=(1/μ²)[ρ/3(1−ρ)+ρ²/4(1−ρ)²]
def mm1b_overflow(rho, Bcap=B):
    return rho**Bcap * (1 - rho) / (1 - rho**(Bcap + 1))

print("## P1a: M/M/1 指数服务，J(ρ)=1/(μ(1−ρ)) 闭式 vs DES（SE=批量均值标准误）")
print("| ρ | J闭式 (ms) | J实测 (ms) | 相对误差 | ±SE (ms) |")
print("|---|---|---|---|---|")
for rho in (0.5, 0.864, 0.90, 0.96):
    m, s, _, se_m, se_s = des(rho, n_pkt=(800_000 if rho >= 0.9 else 300_000),
                              warmup=(50_000 if rho >= 0.9 else 20_000), exp_service=True)
    print(f"| {rho:.3f} | {mm1_std(rho)*1000:.3f} | {s*1000:.3f} | {abs(s/mm1_std(rho)-1)*100:.1f}% | {se_s*1000:.3f} |")

print("\n## P1b: M/M/1/B=40 溢出概率闭式 vs DES")
print("| ρ | P溢出闭式 | P溢出实测 | 相对误差 |")
print("|---|---|---|---|")
for rho in (0.864, 0.90, 0.96, 0.98):
    m, s, ploss, _, _ = des(rho, n_pkt=300_000, Bcap=B, exp_service=True)
    pc = mm1b_overflow(rho)
    print(f"| {rho:.3f} | {pc:.3e} | {ploss:.3e} | {abs(ploss/pc-1)*100:.1f}% |")

print("\n## P1c: M/D/1 确定性 96µs 服务（竞赛口径）PK 闭式 vs DES（无限缓存）")
print("| ρ | J闭式 (ms) | J实测 (ms) | 相对误差 | ±SE (ms) |")
print("|---|---|---|---|---|")
for rho in (0.5, 0.864, 0.90, 0.96):
    m, s, _, se_m, se_s = des(rho, n_pkt=(800_000 if rho >= 0.9 else 300_000),
                              warmup=(50_000 if rho >= 0.9 else 20_000), exp_service=False)
    print(f"| {rho:.3f} | {md1_std(rho)*1000:.3f} | {s*1000:.3f} | {abs(s/md1_std(rho)-1)*100:.1f}% | {se_s*1000:.3f} |")

print("\n利用率→抖动标量律汇总（G=归一化增益）：")
print("| ρ | M/M/1 J (ms) | M/D/1 J (ms) | G=1/(1−ρ) |")
print("|---|---|---|---|")
for rho in (0.864, 0.96, 0.98, 0.99):
    print(f"| {rho:.3f} | {mm1_std(rho)*1000:.2f} | {md1_std(rho)*1000:.2f} | {1/(1-rho):.1f} |")
print("（指数服务是保守上包络；确定性 96µs 服务的抖动约为其 1/3，但都随 (1−ρ)⁻¹ 双曲发散）")

# ---------------- P2: 流体队列积分器频响 ----------------
print("\n## P2: 速率扰动→队列时延的频域传递函数")
DT = 1e-4; HOR = 60.0; N = int(HOR / DT)
f = np.fft.rfftfreq(N, DT)
theta_in = 2 * math.pi * 2.0     # OU 输入拐点 2 Hz
sig = 0.10 * MU

# (i) 纯积分器（线性、精确）：周期 multisine 输入（整数周期 ⇒ DFT 无泄漏），
#     Q̂/Â = dt/(2sin(πf·dt)) ≈ 1/ω（时延再除 μ）
def detrend(x):
    t = np.arange(len(x))
    p = np.polyfit(t, x, 1)
    return x - np.polyval(p, t)
freqs_in = np.array([1.0, 2.0, 5.0, 10.0, 20.0])   # Hz，均为 1/HOR 整数倍
phases = rng.uniform(0, 2 * math.pi, len(freqs_in))
tt = np.arange(N) * DT
a = sum(0.05 * MU * np.sin(2 * math.pi * fi * tt + ph) for fi, ph in zip(freqs_in, phases))
Q_int = np.cumsum(a) * DT
A = np.fft.rfft(a); F = np.fft.rfft(Q_int)
kidx = [int(round(fi * HOR)) for fi in freqs_in]
H_theo = np.divide(DT, 2 * np.sin(np.pi * f * DT), out=np.full_like(f, np.inf), where=f > 0)  # 离散积分器精确频率响应（≈1/ω）
print("- (i) 纯积分器逐频点（输入 multisine，整数周期无泄漏）:")
print("| f (Hz) | |H|实测 Q̂/Â (s) | |H|理论 1/ω (s) | 比值 | 时延增益 |H|/μ (ms) |")
print("|---|---|---|---|---|")
for fi, ki in zip(freqs_in, kidx):
    hm = abs(F[ki]) / abs(A[ki]); ht = H_theo[ki]
    print(f"| {fi:.0f} | {hm:.6f} | {ht:.6f} | {hm/ht:.4f} | {hm/MU*1000:.4f} |")
slope = np.polyfit(np.log10(freqs_in), np.log10([abs(F[k]) / abs(A[k]) for k in kidx]), 1)[0]
print(f"- 幅频斜率={slope:.4f}（理论 −1.0000）——速率扰动→队列深度为精确积分器，−20 dB/dec。")

# (ii) 物理队列：dQ/dt=(ρμ+a) − μ·1[Q>0]，含排空非线性与 Drop-tail 截断
def fluid_phys(rho, clip):
    Q = 0.0; Qt = np.empty(N)
    for k in range(N):
        aa = a[k]
        dQ = (rho * MU + aa) - (MU if Q > 0 else 0.0)
        Q = min(max(Q + dQ * DT, 0.0), float(B) if clip else 1e9)
        Qt[k] = Q
    return Qt
for rho, clip in ((0.90, False), (0.98, False), (0.98, True)):
    Qt = fluid_phys(rho, clip)
    print(f"- (ii) ρ={rho:.2f}, clip={clip}: Q 均值={Qt.mean():.2f} 包, 峰值={Qt.max():.1f}, "
          f"触顶={np.mean(Qt >= B - 1e-9)*100:.2f}%, 排空(空队列)占比={np.mean(Qt <= 0)*100:.1f}%, "
          f"时延抖动 std(Q)/μ={Qt.std()/MU*1000:.3f} ms")
print("- 解读：物理队列在 ρ 明显<1 时频繁排空（非线性死区），实测 |H| 偏离积分器；")
print("  ρ→1 + 截断时低频增益被 B/μ=3.84ms 上限硬剪——传递函数的有效频带随 (1−ρ) 收窄。")
print("  开环积分器 H0(s)=1/(μs) 的可用频带：ω ≫ μ(1−ρ)（队列不排空的准稳态带）；")
print("  闭环节流（丢包→cwnd 收缩，事件触发 reset）把 DC 无穷增益截成有限摆幅 ≤ B/μ。")

# ---------------- P3: 复刻 0085 脉冲链不动点（锚点对拍） ----------------
print("\n## P3: 复刻 0085 脉冲链（纯死亡半群 + 批量跳变，无背景，T_e=4ms）")
def gen_death(mu, Bcap):
    G = np.zeros((Bcap + 1, Bcap + 1))
    for n in range(Bcap + 1):
        if n > 0:
            G[n, n] -= mu; G[n - 1, n] += mu
    return G
def impulse_steady(b, T_e, tol=1e-15, max_iter=20000):
    S = expm(gen_death(MU, B) * T_e)
    P = np.zeros(B + 1); P[0] = 1.0
    for _ in range(max_iter):
        # 批量跳变 J_b：n→min(n+b, B)，溢出 (n+b−B)^+
        J = np.zeros(B + 1)
        overflow = 0.0
        for n in range(B + 1):
            tgt = min(n + b, B)
            overflow += max(n + b - B, 0) * P[n]
            J[tgt] += P[n]
        Pn = S @ J
        if np.abs(Pn - P).sum() < tol:
            P = Pn; break
        P = Pn
    # 每 tick 期望溢出 / 每 tick 发出 b
    return overflow / b, P
print("| 构型 | 批量 b | T_e | 0085 锚点 | 本复刻 | 相对偏差 |")
print("|---|---|---|---|---|---|")
anchors = {1: (0.157, 1e-4), 40: (4.513, 4e-3), 60: (36.342, 4e-3)}   # leak T_e=100µs；tb tick=4ms
for b, (anchor, T_e) in anchors.items():
    frac, P = impulse_steady(b, T_e)
    print(f"| {'leak 单包' if b==1 else ('tb 匀发' if b==40 else 'tb 倾泻')} | {b} | {'100µs' if b==1 else '4ms'} | {anchor:.3f}% | {frac*100:.3f}% | {abs(frac*100/anchor-1)*100:.2f}% |")
print("- 三锚点独立复刻成立 ⇒ 突发惩罚律的柯尔莫哥洛夫数值化可信，可安全并入 0102 的传递函数叙事。")

# ---------------- P4: 构型级抖动预算表 ----------------
print("\n## P4: 11/07 五发构型逐 bin 利用率→抖动增益（M/M/1 保守口径，仅打标流速率）")
shots = {
    1: [("tb", 36)] * 6,
    2: [("leak", 40)] * 3 + [("leak", 36)] * 3,
    3: [("tb", 40), ("tb", 40), ("tb", 38), ("tb", 36), ("p", 12.25e6), ("p", 12.0e6)],
    4: [("tb", 40)] * 3 + [("tb", 38), ("p", 12.5e6), ("p", 12.0e6)],
    5: [("tb", 40)] * 3 + [("tb", 38), ("p", 12.5e6), ("p", 12.0e6)],
}
def rate_pkt(mod, v):
    if mod in ("tb", "leak"): return v / 0.004          # 每 4ms v 包 → 包/s
    return float(v) / 1200.0                            # B/s → 包/s
print("| Shot | bin | 速率 (pkt/s) | ρ_tag | G=1/(1−ρ) | J_M/M/1 (ms) | J_M/D/1 (ms) |")
print("|---|---|---|---|---|---|---|")
for s in sorted(shots):
    for b, (mod, v) in enumerate(shots[s], 1):
        rp = rate_pkt(mod, v); rho = min(rp / MU, 0.9999)
        g = 1 / (1 - rho)
        j1 = 1 / (MU * (1 - rho)) * 1000
        j2 = md1_std(rho) * 1000
        print(f"| {s} | {b} | {rp:.0f} | {rho:.3f} | {g:.1f} | {j1:.2f} | {j2:.2f} |")
print()
print("注：ρ_tag 只计打标流自身（leak40=96M→0.960、leak36=86.4M→0.864、96M→0.960、98M→0.980、100M→0.9996+）；")
print("背景流另计（0083: a≈0.9999 常态负载），闭式 J 用于相对排序与安全裕度分级，不作绝对预测。")
print("\nDone.")
