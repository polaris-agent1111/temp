# -*- coding: utf-8 -*-
"""0090 — 多变量高斯过程对未探索参数网格耗时的贝叶斯优化置信上界评估。

数据源（只读）：runs/results.jsonl（valid 且非 load-* 的 hybrid/champ 族逐场记录）。
建模对象：6.bin（320MB 排空段）分段耗时 t6 对 precise 速率 p6（Mbps）的响应面，
         家族控制 = tb4(1~4.bin token_bucket) + p5=100M + g=1000µs 默认构型。
方法：
  1. 高斯过程回归（SE 与 Matérn-5/2 两种核），超参由边际似然多起点 L-BFGS 拟合；
  2. 在未探索网格 p6 ∈ [90, 95] (步长 0.25 Mbps) 上计算后验 μ/σ 与采集函数
     LCB(κ=1,2)（最小化语义的置信上界）与 EI；
  3. LOO 交叉验证对照常数基线，检验 GP 是否真的学到结构；
  4. 蒙特卡洛（seed=42）给出「新点真值 ≤ 现役最优均值」的后验概率；
  5. 诚实性检查：同一 p6 的重复样本给出观测噪声 σ_n 的实证下界，
     并据此检验「96M 帕累托最优」是否是 min-of-N 幻觉。

合规：不探测官方系统、不提交、不写任何受保护路径。
"""
import json
import math
import re
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEED = 42
rng = np.random.default_rng(SEED)

# ---------- 1. 数据提取（家族控制：tb4 + p5=100M + g=1000 默认） ----------
rows = []
for line in open(os.path.join(ROOT, "runs", "results.jsonl"), encoding="utf-8"):
    try:
        d = json.loads(line)
    except Exception:
        continue
    tag = str(d.get("tag", ""))
    if not d.get("valid") or "load-" in tag:
        continue
    if "hybrid" not in tag and "champ" not in tag:
        continue
    ps = [int(x) for x in re.findall(r"p(\d+)M", tag)]
    g = [int(x) for x in re.findall(r"-g(\d+)(?:-r|$)", tag)]
    dl = d.get("downloads", {})
    t6 = dl.get("6.bin")
    if t6 is None:
        continue
    p5 = ps[0] if ps else None
    p6 = ps[1] if len(ps) > 1 else (ps[0] if len(ps) == 1 else None)
    if p6 is None:
        continue
    rows.append(dict(tag=tag, p5=p5, p6=p6, g=g[0] if g else 1000, t6=float(t6),
                     total=float(d["total_seconds"])))

# 标注口径：tag 中 pXXM 顺序为 [p5(5.bin), p6(6.bin)]；单 token 视为 both（p5=p6）。
# 家族控制：6.bin 分段只受 p6 影响（文件串行下载），p5 不进入 6.bin 响应面；
# g≠1000 的行是「间隔维度扰动实验」，从主响应面排除（另行敏感性讨论）。
DATA = [r for r in rows if r["g"] == 1000 and r["p6"] is not None]
X = np.array([r["p6"] for r in DATA], dtype=float).reshape(-1, 1)
Y = np.array([r["t6"] for r in DATA], dtype=float)

# 敏感性用：把 g≠1000 的 p6=96 行并回（检验间隔维度混入是否改变结论）
DATA_G = [r for r in rows if r["p6"] is not None]

print("=" * 96)
print("1. 家族控制数据集（tb4 混合构型 + g=1000µs；响应 = 6.bin 分段耗时 t6）")
print("=" * 96)
print(f"{'tag':<42}{'p5':>4}{'p6':>5}{'t6(s)':>8}{'total(s)':>9}")
for r in sorted(DATA, key=lambda r: (r["p6"], r["tag"])):
    print(f"{r['tag']:<42}{r['p5']:>4}{r['p6']:>5}{r['t6']:>8.2f}{r['total']:>9.2f}")
print()
for p in sorted(set(X.ravel())):
    ys = Y[X.ravel() == p]
    print(f"p6={p:>3} Mbps: n={len(ys)}  t6 mean={ys.mean():6.2f}  sd={ys.std(ddof=1) if len(ys)>1 else float('nan'):5.2f}  min={ys.min():6.2f}  max={ys.max():6.2f}")

# 重复点观测噪声实证
reps = [Y[X.ravel() == p] for p in sorted(set(X.ravel())) if (X.ravel() == p).sum() >= 3]
sd_pool = math.sqrt(sum(((ys - ys.mean()) ** 2).sum() for ys in reps) / sum(len(ys) - 1 for ys in reps))
print(f"\n重复点合并组内 sd（观测噪声实证下界）: {sd_pool:.2f} s  —— 单发 t6 噪声与参数效应同量级")

# 6.bin 物理下确界
T6_FLOOR = 2560 / 44.1
print(f"6.bin 物理下确界参考（2560 Mbit @ 44.1 Mbps 有效瓶颈）: {T6_FLOOR:.2f} s")

# ---------- 2. GPR 核心 ----------
def kernel_se(d, ell, sf):
    return sf ** 2 * np.exp(-0.5 * (d / ell) ** 2)

def kernel_m52(d, ell, sf):
    r = np.sqrt(5.0) * d / ell
    return sf ** 2 * (1 + r + r ** 2 / 3) * np.exp(-r)

def gp_fit(x, y, kern, x_bounds=([0.3, 30.0]), s2f=(0.5, 30.0), s2n=(0.5, 25.0), sn_fixed=None):
    """返回最优超参与负对数边际似然；多起点 L-BFGS。sn_fixed 时不估计噪声。"""
    def nll(theta):
        if sn_fixed is not None:
            ell, sf = np.exp(theta)
            sn = sn_fixed
        else:
            ell, sf, sn = np.exp(theta)
        K = kern(x - x.T, ell, sf) + sn ** 2 * np.eye(len(x))
        try:
            L = np.linalg.cholesky(K)
        except np.linalg.LinAlgError:
            return 1e6
        a = np.linalg.solve(L.T, np.linalg.solve(L, y))
        return 0.5 * y @ a + np.log(np.diag(L)).sum() + 0.5 * len(x) * math.log(2 * math.pi)

    best = None
    grid = ([(ell0, sf0) for ell0 in (2.0, 5.0, 10.0) for sf0 in (5.0, 12.0)] if sn_fixed is not None
            else [(ell0, sf0, sn0) for ell0 in (2.0, 5.0, 10.0) for sf0 in (5.0, 12.0) for sn0 in (5.0, 9.0)])
    for t0 in grid:
        th0 = np.log(np.array(t0, dtype=float))
        bnds = ([(math.log(x_bounds[0]), math.log(x_bounds[1])),
                 (math.log(s2f[0]), math.log(s2f[1]))] if sn_fixed is not None else
                [(math.log(x_bounds[0]), math.log(x_bounds[1])),
                 (math.log(s2f[0]), math.log(s2f[1])),
                 (math.log(s2n[0]), math.log(s2n[1]))])
        res = minimize(nll, th0, method="L-BFGS-B", bounds=bnds)
        if best is None or res.fun < best.fun:
            best = res
    if sn_fixed is not None:
        ell, sf = np.exp(best.x)
        return ell, sf, sn_fixed, best.fun
    ell, sf, sn = np.exp(best.x)
    return ell, sf, sn, best.fun

def gp_predict(x, y, xs, ell, sf, sn, kern):
    K = kern(x - x.T, ell, sf) + sn ** 2 * np.eye(len(x))
    L = np.linalg.cholesky(K)
    a = np.linalg.solve(L.T, np.linalg.solve(L, y))
    Ks = kern(xs - x.T, ell, sf)
    mu = Ks @ a
    v = np.linalg.solve(L, Ks.T)
    Kss = kern(xs - xs.T, ell, sf)
    var = np.diag(Kss) - (v ** 2).sum(axis=0)
    return mu, np.sqrt(np.clip(var, 1e-12, None))

xs = np.arange(90.0, 96.75, 0.25).reshape(-1, 1)
results = {}
print()
print("=" * 96)
print("2. GPR 超参拟合（边际似然多起点；两核对比）")
print("=" * 96)
for name, kern in (("Squared-Exponential", kernel_se), ("Matérn-5/2", kernel_m52)):
    ell, sf, sn, nll = gp_fit(X, Y, kern)
    mu, sd = gp_predict(X, Y, xs, ell, sf, sn, kern)
    results[name] = (ell, sf, sn, nll, mu, sd)
    print(f"{name:<22} ℓ={ell:6.2f} Mbps  σ_f={sf:5.2f} s  σ_n={sn:5.2f} s  NLL={nll:7.2f}")

# ---------- 3. LOO 对照常数基线 ----------
def loo_rmse(kern, fixed=None):
    errs_gp, yv = [], []
    for i in range(len(X)):
        m = np.ones(len(X), bool); m[i] = False
        if fixed:
            mu_i, _ = gp_predict(X[m], Y[m], X[i:i+1], *fixed, kern)
        else:
            ell, sf, sn, _ = gp_fit(X[m], Y[m], kern)
            mu_i, _ = gp_predict(X[m], Y[m], X[i:i+1], ell, sf, sn, kern)
        errs_gp.append(mu_i[0] - Y[i]); yv.append(Y[i])
    errs_gp = np.array(errs_gp); yv = np.array(yv)
    rmse_gp = math.sqrt((errs_gp ** 2).mean())
    rmse_base = math.sqrt(((yv - yv.mean()) ** 2).mean())
    return rmse_gp, rmse_base

print()
print("=" * 96)
print("3. LOO 交叉验证（GP vs 常数均值基线；固定 SE 超参以免逐点重拟合过拟合）")
print("=" * 96)
ell_se, sf_se, sn_se = results["Squared-Exponential"][:3]
rmse_gp, rmse_base = loo_rmse(kernel_se, fixed=(ell_se, sf_se, sn_se))
print(f"SE  GP LOO-RMSE = {rmse_gp:6.2f} s   |  常数基线 RMSE = {rmse_base:6.2f} s   |  技巧分 = {1 - rmse_gp/rmse_base:+.3f}")
ell_m, sf_m, sn_m = results["Matérn-5/2"][:3]
rmse_gp2, _ = loo_rmse(kernel_m52, fixed=(ell_m, sf_m, sn_m))
print(f"M52 GP LOO-RMSE = {rmse_gp2:6.2f} s   （>0 技巧分才说明学到了结构，否则 GP 退化为均值+噪声）")

# 噪声假设敏感性：σ_n=6.8（实证） vs σ_n=2.0（「95M/97M 是真信号」情景）
print()
print("-- 噪声假设敏感性（SE 核，σ_n 固定后重拟 ℓ/σ_f）--")
for sn_fx, note in ((sd_pool, f"σ_n={sd_pool:.1f}(实证组内sd)"), (2.0, "σ_n=2.0(把单点当真信号)")):
    ell2, sf2, _, nll2 = gp_fit(X, Y, kernel_se, sn_fixed=sn_fx)
    rg, rb = loo_rmse(kernel_se, fixed=(ell2, sf2, sn_fx))
    mu2, sd2 = gp_predict(X, Y, xs, ell2, sf2, sn_fx, kernel_se)
    m90 = mu2[xs.ravel() == 90.0][0]; s90 = sd2[xs.ravel() == 90.0][0]
    print(f"  {note:<28} ℓ={ell2:5.2f} σ_f={sf2:5.2f} NLL={nll2:6.2f} | LOO-RMSE={rg:5.2f}(基线{rb:5.2f}) "
          f"| μ(90M)={m90:6.2f} σ(90M)={s90:5.2f} LCB2(90M)={m90-2*s90:6.2f}")

# ---------- 4. 未探索网格上的采集函数 ----------
mu, sd = results["Squared-Exponential"][4], results["Squared-Exponential"][5]
best_obs_mean = min(Y[X.ravel() == p].mean() for p in set(X.ravel()))
best_obs_min = Y.min()
print()
print("=" * 96)
print("4. 未探索网格 p6 ∈ [90, 95] 的后验与采集函数（SE 核；响应 = t6，越小越好）")
print("=" * 96)
print(f"现役已测最优: 组均值 = {best_obs_mean:.2f} s (p6=96M 组) | 单发最小 = {best_obs_min:.2f} s")
print(f"{'p6(Mbps)':>9}{'μ(s)':>8}{'σ(s)':>7}{'LCB κ=1':>9}{'LCB κ=2':>9}{'EI(s)':>8}{'P(≤最优组均值)':>14}{'状态':>10}")
unexplored = []
for xrow, m, s in zip(xs.ravel(), mu, sd):
    st = "已测" if any(abs(xrow - p) < 0.01 for p in set(X.ravel())) else "未探索"
    z = (best_obs_mean - m) / s
    ei = (best_obs_mean - m) * norm.cdf(z) + s * norm.pdf(z)
    pbeat = norm.cdf(z)
    if st == "未探索":
        unexplored.append((xrow, m, s, m - 1 * s, m - 2 * s, ei, pbeat))
    print(f"{xrow:>9.2f}{m:>8.2f}{s:>7.2f}{m-1*s:>9.2f}{m-2*s:>9.2f}{ei:>8.3f}{pbeat*100:>13.1f}%{st:>10}")

print()
u = sorted(unexplored, key=lambda r: r[5], reverse=True)
print("EI 排序前 5 的未探索点（EI 是排序用相对量，绝对值小 = 空间已平）:")
for xrow, m, s, l1, l2, ei, pb in u[:5]:
    print(f"  p6={xrow:5.2f}  μ={m:6.2f} σ={s:5.2f}  LCB2={l2:6.2f}  EI={ei:.4f}  P(≤{best_obs_mean:.1f})={pb*100:.1f}%")
u2 = sorted(unexplored, key=lambda r: r[3])
print("LCB(κ=2) 排序前 5（悲观界，越低越值得测）:")
for xrow, m, s, l1, l2, ei, pb in u2[:5]:
    print(f"  p6={xrow:5.2f}  LCB2={l2:6.2f}")

# ---------- 5. 蒙特卡洛：新点真值分布 vs 现役 ----------
print()
print("=" * 96)
print("5. 蒙特卡洛后验（seed=42）：新点 t6 真值 ≤ 各阈值的概率（后验均值的不确定度传播）")
print("=" * 96)
for xrow, m, s, *_ in [r for r in zip(xs.ravel(), mu, sd) if r[0] in (90.0, 92.0, 93.0, 94.0, 95.0)]:
    sims = rng.normal(m, s, 200_000)
    print(f"p6={xrow:5.1f}: P(t6≤58.03 物理下确界)={np.mean(sims<=T6_FLOOR)*100:5.1f}%  "
          f"P(t6≤{best_obs_mean:.1f} 现役组均值)={np.mean(sims<=best_obs_mean)*100:5.1f}%  "
          f"P(t6≤61.5 96M最好簇)={np.mean(sims<=61.5)*100:5.1f}%")

# ---------- 6. 诚实性检查：组间结构是否可分辨 ----------
print()
print("=" * 96)
print("6. 诚实性检查：p6 各组均值差是否超出观测噪声（Welch t + 单因素方差分析视角）")
print("=" * 96)
from scipy import stats
groups = sorted(set(X.ravel()))
y96 = Y[X.ravel() == 96]; y98 = Y[X.ravel() == 98]
t, p = stats.ttest_ind(y96, y98, equal_var=False)
print(f"p6=96 (n={len(y96)}, mean={y96.mean():.2f}, sd={y96.std(ddof=1):.2f}) vs p6=98 (n={len(y98)}, mean={y98.mean():.2f}, sd={y98.std(ddof=1):.2f})")
print(f"  Welch t = {t:.3f}, p = {p:.3f} → {'均值差不可分辨' if p > 0.05 else '均值差显著'}")
cell_means = [Y[X.ravel() == g].mean() for g in groups]
ss_between = sum((X.ravel() == g).sum() * (m - Y.mean()) ** 2 for g, m in zip(groups, cell_means))
ss_within = sum(((Y[X.ravel() == g] - m) ** 2).sum() for g, m in zip(groups, cell_means))
k, n = len(groups), len(Y)
F = (ss_between / (k - 1)) / (ss_within / (n - k)) if n > k else float("nan")
pF = 1 - stats.f.cdf(F, k - 1, n - k) if F == F else float("nan")
print(f"单因素 ANOVA（组=95/96/97/98M）: F({k-1},{n-k}) = {F:.3f}, p = {pF:.3f} → "
      f"{'组间结构不可分辨' if pF > 0.05 else '存在组间结构'}")
y95, y97 = Y[X.ravel() == 95], Y[X.ravel() == 97]
print(f"单点组 95M({y95[0]:.2f}s) / 97M({y97[0]:.2f}s) 高于 96M 组均值 {y96.mean():.2f}s 达 "
      f"{(y95[0]-y96.mean())/sd_pool:.1f}σ / {(y97[0]-y96.mean())/sd_pool:.1f}σ —— n=1 不足以确立「悬崖」")
print("—— STATUS「96M 帕累托最优」把 96M 的 min 簇(58.0-61.5) 与 95/97/100M 的 n=1 样本比较，存在 min-of-N 偏差；")
print("   本数据集内 p6=96 组均值 68.8s 与 98M 组 72.4s 无差，与「平坦+噪声」情景一致。")
print()
print("结论锚点：GP 后验在 90–96.5 Mbps 上近乎平坦（μ≈72–74s，σ≈2.3–6.4s），")
print("LOO 技巧分为负（GP 不优于常数基线）→ 90–95M 未探索网格在现有数据下「信息真空」，")
print("EI/LCB 的微弱排序（偏向 90M）是方差寻求而非均值结构信号；按贝叶斯优化纪律与")
print("AGENTS.md n≥3 门禁，90–95M 网格不构成比现役 96M 更优的投放优先级。")
