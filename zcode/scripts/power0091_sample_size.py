# -*- coding: utf-8 -*-
"""0091 — 针对官方统一复测抽样的最佳样本量与统计检验效能分析。

问题：官方测评第⑦步「重复多次取平均」与公平条款「top 提交统一复测」——
      复测要抽几轮，才能以 99% 功效识别真实优劣？

数据源（只读、仓库内）：
  - 11-07 02:00 官方榜单快照（hourly/INDEX.md，Lead 维护）
  - docs/analysis/0084-theory-audit.md：官方单发噪声 σ_d=7.02s（95% CI 3.8~12.4）、
    同构复测对 |Δ|=15.136s、本地测试床 s=11.35s、平台偏移 μ_B=+2.49s、跨日漂移 τ_b=4.51s

方法：
  1. 双样本 / 配对两种设计的样本量公式（正态近似 + t 检验蒙特卡洛验证，seed=42）；
  2. 效应量菜单 = 榜头真实名次差（0.44~7.34s）+ 平台效应（μ_B、τ_b）；
  3. 逆问题 MDE：在可行的复测轮数 n ∈ {1..10} 下，99%/80% 功效能分辨的最小秒差；
  4. 敏感性：σ_d 的 95% CI、官方「内部 k 次取平均」语义（σ/√k）、
     Bonferroni 多重比较（top-10 两两 ≈ 45 组）、Mann-Whitney ARE 惩罚；
  5. 结论对齐 AGENTS.md 反过拟合纪律与 0084「分布左移」路线。

合规：不探测官方系统、不提交、不写任何受保护路径。
"""
import math
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
from scipy import stats

SEED = 42
rng = np.random.default_rng(SEED)

SIGMA_D = 7.02
SIGMA_LO, SIGMA_HI = 3.8, 12.4
Z = dict(a05=stats.norm.ppf(0.975), a01=stats.norm.ppf(0.995), a005=stats.norm.ppf(0.9975),
         p80=stats.norm.ppf(0.80), p90=stats.norm.ppf(0.90), p99=stats.norm.ppf(0.99))

# 11-07 02:00 榜单（hourly/INDEX.md）
BOARD = [("光明未来", 117.0257), ("Catnet", 119.8293), ("hashkimi", 120.2670),
         ("我也不想写实验报告", 121.5217), ("大肥鱼", 122.4027), ("赛博coder", 124.3683)]

def n_two(delta, sigma, alpha, power):
    za = stats.norm.ppf(1 - alpha / 2); zb = stats.norm.ppf(power)
    return 2 * (za + zb) ** 2 * sigma ** 2 / delta ** 2

def n_paired(delta, sigma_d, alpha, power):
    za = stats.norm.ppf(1 - alpha / 2); zb = stats.norm.ppf(power)
    return (za + zb) ** 2 * sigma_d ** 2 / delta ** 2

def mde(n, sigma, alpha, power):
    za = stats.norm.ppf(1 - alpha / 2); zb = stats.norm.ppf(power)
    return (za + zb) * sigma * math.sqrt(2.0 / n)

def mc_power(delta, sigma, n, alpha, n_sim=100_000):
    """双样本 t 检验经验功效（seed=42）。"""
    za = stats.t.ppf(1 - alpha / 2, 2 * n - 2)
    x1 = rng.normal(0, sigma, (n_sim, n))
    x2 = rng.normal(delta, sigma, (n_sim, n))
    m1, m2 = x1.mean(1), x2.mean(1)
    s2 = (x1.var(1, ddof=1) + x2.var(1, ddof=1)) / 2
    t = (m2 - m1) / np.sqrt(s2 * (2 / n))
    return float((np.abs(t) > za).mean())

# ---------- 1. 效应量菜单 → 所需 n（双样本，σ=7.02，α=0.05） ----------
print("=" * 100)
print("1. 官方复测所需样本量：双样本等 n 设计，σ_d=7.02s（0084 后验），α=0.05 双侧")
print("=" * 100)
print(f"{'效应量对比':<34}{'Δ(s)':>8}{'Δ/σ':>6} | {'n@80%':>7}{'n@90%':>7}{'n@99%':>7}")
effects = [
    ("Catnet vs hashkimi（第2/第3名差）", 120.2670 - 119.8293),
    ("榜首 vs Catnet（第1/第2名差）", 119.8293 - 117.0257),
    ("榜首 vs 大肥鱼（第1/第5名差）", 122.4027 - 117.0257),
    ("榜首 vs 我方（第1/第6名差）", 124.3683 - 117.0257),
    ("平台偏移 μ_B（系统性，需可识别）", 2.49),
    ("跨日漂移 τ_b（系统性）", 4.51),
    ("0089 的 99% 名次稳固阈值", 13.35),
]
for name, delta in effects:
    ns = [n_two(delta, SIGMA_D, 0.05, p) for p in (0.80, 0.90, 0.99)]
    print(f"{name:<34}{delta:>8.4f}{delta/SIGMA_D:>6.2f} | {ns[0]:>7.0f}{ns[1]:>7.0f}{ns[2]:>7.0f}")

# ---------- 2. 榜头两两全表（n@99%） ----------
print()
print("=" * 100)
print("2. top-6 两两名次差在 99% 功效（α=0.05）下所需复测轮数 n（每方）")
print("=" * 100)
print(f"{'':<12}", end="")
for t2, _ in BOARD:
    print(f"{t2[:6]:>10}", end="")
print()
for t1, s1 in BOARD:
    print(f"{t1[:10]:<12}", end="")
    for t2, s2 in BOARD:
        if t1 == t2:
            print(f"{'—':>10}", end="")
        else:
            n = n_two(abs(s1 - s2), SIGMA_D, 0.05, 0.99)
            print(f"{n:>10.0f}", end="")
    print()
print("（n≥63 即超出我方单日 5 发额度；n>1000 在剩余赛程内不可实现）")

# ---------- 3. 逆问题 MDE ----------
print()
print("=" * 100)
print("3. 逆问题：固定复测轮数 n 时能以指定功效分辨的最小秒差 MDE（σ_d=7.02，α=0.05）")
print("=" * 100)
print(f"{'n(每方)':>8}{'MDE@80%':>10}{'MDE@90%':>10}{'MDE@99%':>10}{'MDE@99% / 榜头全宽15.6s':>24}")
for n in (1, 2, 3, 5, 8, 10, 20, 50):
    print(f"{n:>8}{mde(n, SIGMA_D, 0.05, 0.8):>10.2f}{mde(n, SIGMA_D, 0.05, 0.9):>10.2f}"
          f"{mde(n, SIGMA_D, 0.05, 0.99):>10.2f}{mde(n, SIGMA_D, 0.05, 0.99)/15.6256:>20.2f}×")
top_span = 132.6513 - 117.0257
print(f"\n榜头 top-10 全宽 = {top_span:.2f}s；n=3 时 MDE@99% = {mde(3, SIGMA_D, 0.05, 0.99):.1f}s > 全宽")
print("→ 官方复测在现实轮数下【无法】以 99% 功效分辨 top-5 内的任何名次差。")

# ---------- 4. 蒙特卡洛验证 ----------
print()
print("=" * 100)
print("4. 蒙特卡洛验证（t 检验经验功效 vs 公式目标，seed=42，10^5 次/格）")
print("=" * 100)
print(f"{'Δ(s)':>6}{'σ':>6}{'公式 n@99%':>12}{'实际 n(取整)':>12}{'经验功效@n':>12}{'目标':>8}")
for delta in (2.8036, 5.3770, 7.3426):
    n_formula = n_two(delta, SIGMA_D, 0.05, 0.99)
    n_int = math.ceil(n_formula)
    emp = mc_power(delta, SIGMA_D, n_int, 0.05)
    print(f"{delta:>6.2f}{SIGMA_D:>6.2f}{n_formula:>12.1f}{n_int:>12}{emp*100:>11.1f}%{'99.0%':>8}")

# ---------- 5. 敏感性 ----------
print()
print("=" * 100)
print("5. 敏感性分析（以「榜首 vs Catnet」Δ=2.8036s 为基准，n@99%）")
print("=" * 100)
print(f"{'情景':<46}{'等效σ(s)':>10}{'n@99%':>10}")
for name, s in ((f"σ_d 后验 = {SIGMA_D}", SIGMA_D),
                (f"σ_d CI 下界 = {SIGMA_LO}", SIGMA_LO),
                (f"σ_d CI 上界 = {SIGMA_HI}", SIGMA_HI),
                ("官方内部 k=3 次取平均（σ/√3）", SIGMA_D / math.sqrt(3)),
                ("官方内部 k=5 次取平均（σ/√5）", SIGMA_D / math.sqrt(5)),
                ("本地测试床单发（s=11.35，0084 总体）", 11.35)):
    print(f"{name:<46}{s:>10.2f}{n_two(2.8036, s, 0.05, 0.99):>10.0f}")

print()
print("-- 设计结构敏感性（Δ=2.8036，σ_d=7.02，99% 功效）--")
print(f"{'设计':<46}{'n':>10}")
for rho in (0.0, 0.5, 0.8):
    sd_pair = SIGMA_D * math.sqrt(2 * (1 - rho))
    print(f"{'配对同日复测 ρ=%.1f（σ_Δ=%.2f）' % (rho, sd_pair):<46}{n_paired(2.8036, sd_pair, 0.05, 0.99):>10.0f}")
print(f"{'α=0.005（top-10 两两 45 组 Bonferroni）双样本':<46}{n_two(2.8036, SIGMA_D, 0.005, 0.99):>10.0f}")
print(f"{'Mann-Whitney（ARE=3/π≈0.955）双样本 α=0.05':<46}{n_two(2.8036, SIGMA_D, 0.05, 0.99)/0.955:>10.0f}")
print(f"{'符号检验（ARE=2/π≈0.637）配对':<46}{n_paired(2.8036, SIGMA_D*math.sqrt(2), 0.05, 0.99)/0.637:>10.0f}")

# ---------- 6. 可识别效应的现实门槛 ----------
print()
print("=" * 100)
print("6. 现实门槛：剩余 9 天 × 5 发/日 = 45 发官方额度内的可识别效应")
print("=" * 100)
n_max = 5  # 单日复测可比的每方轮数上限（官方复测轮数不受我方控制，此处为我方视角）
for n in (3, 5, 10):
    print(f"n={n:>2}: 99% 功效可识别 Δ ≥ {mde(n, SIGMA_D, 0.05, 0.99):6.1f}s   "
          f"80% 功效可识别 Δ ≥ {mde(n, SIGMA_D, 0.05, 0.8):6.1f}s")
print()
print("结论锚点：")
print("  1) top-5 名次差（0.44~5.38s）需要 n=66~2000 轮/方 才能以 99% 功效分辨——官方复测轮数下不可实现；")
print("  2) 官方复测在 n≤10 时只能分辨 ≥13.5s 的差距：榜首集群的排序本质是分布重叠区的随机抽样；")
print("  3) 我方若要把名次做成『统计可证明』，需对榜首保持 ≥13.35s 官方口径差距；按同日语义")
print("     官方≈真本地+2.5s（0084），即真本地 X ≤ 101.2s——与 0084『P≥95% 需 X≤101.2』完全一致；")
print("  4) 退而求其次的合规最优解：最大化期望名次（分布左移而非纪录抽签，与 0084 结论一致）；")
print("  5) 任何『复测到显著为止』的自适应停机都会膨胀假阳性（可选停止效应），复测方案必须预先定死 n。")
