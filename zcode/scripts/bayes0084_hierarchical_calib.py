# -*- coding: utf-8 -*-
"""0084 分层贝叶斯回归与校准：5 发官方真机出分 × 测试床离线预测值.

模型（两层层级 + 测量误差协变量）：
  官方运行   y_{c,j} | θ_c        ~ N(α + β·θ_c, σ_w²)          j=1..J_c（同配置官方重复共享 θ_c）
  配置真值   θ_c | 本地样本        ~ N(m_c, se_c² + τ₀²)         本地均值为带噪先验，τ₀=测试床-官方环境分歧尺度
  超参数     α, β, σ_w             弱先验；网格精确后验（无 MCMC，全可复现）
  θ_c 解析边缘化（rank-1 Sherman-Morrison），σ_w 网格积分。

数据来源（全部本仓库既有记录，零远程探测）：
  - runs/results.jsonl：本地测试床（valid=true 且非 load-* 污染；截止 2026-11-07 05:27 为标题口径「293 场」近似）
  - runs/official_results.jsonl + runs/submissions.jsonl：11/05–11/06 官方 10 发
  - runs/sequential_adaptive_log.jsonl：11/07 五发官方出分
  - runs/*.configs.json + runs/configs/<tag>/：提交构型与本地锚点构型一致性核对
输出：zcode/scripts/_0084_out.md
"""
import json
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
rng = np.random.default_rng(42)

OUT = []
def P(s=""):
    OUT.append(s)
    print(s)

CUTOFF = "2026-11-07T05:27"
S_POOL_FALLBACK = 7.0   # n=1 配置的本地单场 sd 兜底（取自各配置 sd 中位数）
TAU0 = 5.0              # 测试床-官方协变量分歧尺度（敏感性：2 / 8）

# ---------- A. 本地测试床加载 ----------
def parse_cfg(c):
    out = {}
    if not isinstance(c, dict):
        return out
    for k, v in c.items():
        if not isinstance(v, str) or ":" not in v:
            out[str(k)] = ("?", {})
            continue
        m, ps = v.split(":", 1)
        d = {}
        for kv in ps.split(","):
            if "=" in kv:
                a, b = kv.split("=", 1)
                try:
                    d[a] = float(b) if "." in b else int(b)
                except ValueError:
                    d[a] = b
        out[str(k)] = (m, d)
    return out

def L(p, i, mode, **kw):
    t = p.get(str(i))
    if not t or t[0] != mode:
        return False
    return all(t[1].get(k) == v for k, v in kw.items())

def leak(i, r, cap, itv):   return lambda p: L(p, i, "leak_bucket", leak_rate=r, bucket_cap=cap, leak_interval_us=itv)
def tb(i, tok, bur, r, itv): return lambda p: L(p, i, "token_bucket", tokens=tok, burst=bur, token_refill_rate=r, token_refill_interval_us=itv)
def prec(i, rate):          return lambda p: L(p, i, "precise_rate_based", max_pacing_rate=rate)
def ALL(*fs):               return lambda p: all(f(p) for f in fs)

CFGS = {
    "v1_leak9/30/1000":  ALL(*[leak(i, 9, 30, 1000) for i in range(1, 7)]),
    "S3_tb100/200/20@1k": ALL(*[tb(i, 100, 200, 20, 1000) for i in range(1, 7)]),
    "S4_leak36/40/4000": ALL(*[leak(i, 36, 40, 4000) for i in range(1, 7)]),
    "S5_leak27/40/4000": ALL(*[leak(i, 27, 40, 4000) for i in range(1, 7)]),
    "ADP1_leak30/50/5000": ALL(*[leak(i, 30, 50, 5000) for i in range(1, 7)]),
    "ADP2_leak24/60/4000": ALL(*[leak(i, 24, 60, 4000) for i in range(1, 7)]),
    "HR1_leak40/60/4000": ALL(*[leak(i, 40, 60, 4000) for i in range(1, 7)]),
    "HR2_leak42/60/4000": ALL(*[leak(i, 42, 60, 4000) for i in range(1, 7)]),
    "HR3_leak44/60/4000": ALL(*[leak(i, 44, 60, 4000) for i in range(1, 7)]),
    "shot1_probeTBr36":  ALL(*[tb(i, 40, 40, 36, 4000) for i in range(1, 7)]),
    "shot2_leak40x3_36x3": ALL(leak(1, 40, 40, 4000), leak(2, 40, 40, 4000), leak(3, 40, 40, 4000),
                               leak(4, 36, 36, 4000), leak(5, 36, 36, 4000), leak(6, 36, 36, 4000)),
    "shot3_tb4p98M":     ALL(tb(1, 40, 40, 40, 4000), tb(2, 40, 40, 40, 4000), tb(3, 40, 40, 38, 4000),
                             tb(4, 40, 40, 36, 4000), prec(5, 12250000), prec(6, 12000000)),
    "shot45_fast14asym": ALL(tb(1, 40, 60, 40, 4000), tb(2, 40, 60, 40, 4000), tb(3, 40, 60, 40, 4000),
                             tb(4, 40, 60, 38, 4000), prec(5, 12500000), prec(6, 12000000)),
}

loc = {k: [] for k in CFGS}
n_all = n_valid = n_load = 0
n_cutoff = 0
for line in open("runs/results.jsonl", encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    d = json.loads(line)
    n_all += 1
    tag = d.get("tag", "")
    if tag.startswith("load-"):
        n_load += 1
        continue
    if str(d.get("valid")).lower() != "true":
        continue
    n_valid += 1
    if d.get("at", "")[:16] <= CUTOFF:
        n_cutoff += 1
    p = parse_cfg(d.get("config"))
    if not p:
        continue
    try:
        v = float(d.get("total_seconds"))
    except (TypeError, ValueError):
        continue
    for name, f in CFGS.items():
        try:
            if f(p):
                loc[name].append((v, d.get("at", "")[:16], tag))
        except Exception:
            pass

P("# 0084 数值输出 — 分层贝叶斯回归与校准")
P(f"## A. 测试床样本库")
P(f"- results.jsonl 共 {n_all} 行；load-* 污染 {n_load} 行；valid=true {n_valid} 行；"
  f"**截止派发时刻（2026-11-07 05:27）valid={n_cutoff} 行（任务标题「293 场」为派发时点近似计数，0068 同口径先例）**。")
P("")

# ---------- B. 各构型本地统计 ----------
P("## B. 官方已评测构型的本地协变量（strict 构型匹配）")
P("| 构型 | n | 本地均 m_c | sd | se_c | 样本跨度 | 说明 |")
P("|---|---|---|---|---|---|---|")
stats = {}
for name, rows in loc.items():
    vals = [v for v, _, _ in sorted(rows, key=lambda x: x[1])]
    if vals:
        m = float(np.mean(vals))
        sd = float(np.std(vals, ddof=1)) if len(vals) > 1 else float("nan")
        se = S_POOL_FALLBACK if len(vals) == 1 else max(sd / np.sqrt(len(vals)), S_POOL_FALLBACK / np.sqrt(len(vals)))
        stats[name] = (len(vals), m, sd, se)
        span = f"{sorted(rows, key=lambda x: x[1])[0][1]}→{sorted(rows, key=lambda x: x[1])[-1][1]}"
        note = ""
        if name == "v1_leak9/30/1000":
            note = "1ms 网格坏域（排除出校准）"
        if name == "HR2_leak42/60/4000":
            note = "无本地样本→插补"
        P(f"| {name} | {len(vals)} | {m:.2f} | {sd:.2f} | {se:.2f} | {span} | {note} |")
    else:
        stats[name] = (0, float("nan"), float("nan"), 10.0)
        P(f"| {name} | 0 | — | — | 10.0(插补) | — | 无本地样本 |")
sds = [s[2] for s in stats.values() if s[0] > 2 and np.isfinite(s[2])]
P(f"\n- 本地单场 sd 中位数 = {float(np.median(sds)):.2f}s（n=1 配置兜底 {S_POOL_FALLBACK}s 的依据）。")
P("")

# 插补协变量（明示）：
m_HR1 = stats["HR1_leak40/60/4000"][1]
m_HR3 = stats["HR3_leak44/60/4000"][1]
imput = {
    # HR2（42/60）介于 HR1（40/60，n=3）与 HR3（44/60，n=2）之间：线性插值 + 中点 se
    "HR2_leak42/60/4000": ((m_HR1 + m_HR3) / 2, max(abs(m_HR1 - m_HR3) / 2 + S_POOL_FALLBACK / np.sqrt(2), 5.0)),
}
for k, (m, se) in imput.items():
    stats[k] = (0, m, float("nan"), se)
    P(f"- 插补：{k}: m_c={m:.2f}（来源见上），se_c={se:.2f}")

# ---------- C. 官方出分数据 ----------
# 提交序 → 构型映射依据 runs/submissions.jsonl（顺序）与 runs/sequential_adaptive_log.jsonl（11/07 出分）
OFFICIAL = [
    # (config, official_seconds, 日期)   v1/v1b 同配置重复
    ("v1_leak9/30/1000", 245.995, "11/05"), ("v1_leak9/30/1000", 243.9583, "11/05"),
    ("S3_tb100/200/20@1k", 140.927, "11/05"),
    ("S4_leak36/40/4000", 133.086, "11/05"),
    ("S5_leak27/40/4000", 141.7273, "11/05"),
    ("ADP1_leak30/50/5000", 140.4793, "11/06"),
    ("ADP2_leak24/60/4000", 150.6757, "11/06"),
    ("HR1_leak40/60/4000", 137.384, "11/06"),
    ("HR2_leak42/60/4000", 137.091, "11/06"),
    ("HR3_leak44/60/4000", 142.7837, "11/06"),
    ("shot1_probeTBr36", 143.5610, "11/07"),
    ("shot2_leak40x3_36x3", 124.3683, "11/07"),
    ("shot3_tb4p98M", 143.1357, "11/07"),
    ("shot45_fast14asym", 140.0247, "11/07"),
    ("shot45_fast14asym", 155.1607, "11/07"),
]
EXCLUDE = {"v1_leak9/30/1000"}   # 1ms 网格坏域：官方 2× 塌方（0013 G=4000µs 结论），结构离群不进线性校准
data = [(c, y) for c, y, _ in OFFICIAL if c not in EXCLUDE]
P(f"\n## C. 官方观测：{len(OFFICIAL)} 发，剔除 v1/v1b（1ms 坏域 {len([1 for c,_,_ in OFFICIAL if c in EXCLUDE])} 发）→ 校准用 {len(data)} 发、{len(set(c for c,_ in data))} 个构型；"
  f"同构型重复：v1×2（已剔）、HR3×1、shot45×2。")

# ---------- D. 网格精确后验 ----------
keys = sorted(set(c for c, _ in data))
y_by = {c: np.array([y for cc, y in data if cc == c]) for c in keys}
def V_c(c):
    n, m, sd, se = stats[c]
    return se ** 2 + TAU0 ** 2
def m_c(c):
    return stats[c][1]

ALPHA = np.arange(95.0, 135.0 + 1e-9, 0.5)
BETA = np.arange(0.0, 1.2 + 1e-9, 0.01)
SIGW = np.arange(3.0, 25.0 + 1e-9, 0.25)
PRIOR_A = (115.0, 20.0)   # 弱
PRIOR_B = (0.6, 0.4)      # 弱
lp = np.full((len(ALPHA), len(BETA), len(SIGW)), -np.inf)
for ia, a in enumerate(ALPHA):
    for ib, b in enumerate(BETA):
        for iw, w in enumerate(SIGW):
            ll = 0.0
            for c in keys:
                y = y_by[c]
                J = len(y)
                r = y - a - b * m_c(c)
                # Σ = σ²I + β²V 11ᵀ（rank-1）→ Sherman-Morrison
                s2 = w * w
                V = V_c(c)
                k = b * b * V
                quad = (r @ r) / s2 - (k * (r.sum()) ** 2) / (s2 * s2 * (1 + k * J / s2))
                logdet = J * np.log(s2) + np.log1p(k * J / s2)
                ll += -0.5 * (J * np.log(2 * np.pi) + logdet + quad)
            lp[ia, ib, iw] = ll + (-0.5 * ((a - PRIOR_A[0]) / PRIOR_A[1]) ** 2
                                   - 0.5 * ((b - PRIOR_B[0]) / PRIOR_B[1]) ** 2)
lp -= lp.max()
post = np.exp(lp)
post /= post.sum()

def marg(axis):  # 边缘均值与 95% 区间
    pm = post.sum(axis=tuple(i for i in range(3) if i != axis))
    mean = float((pm * [ALPHA, BETA, SIGW][axis]).sum())
    cdf = np.cumsum(pm)
    lo = [ALPHA, BETA, SIGW][axis][int(np.searchsorted(cdf, 0.025))]
    hi = [ALPHA, BETA, SIGW][axis][min(int(np.searchsorted(cdf, 0.975)), len(cdf) - 1)]
    return mean, lo, hi

ma, la, ha = marg(0)
mb, lb, hb = marg(1)
mw, lw, hw = marg(2)
P(f"\n## D. 校准映射 y_off = α + β·θ_c（θ_c 已边缘化；τ₀={TAU0}s）")
P(f"- α = {ma:.2f}  [{la:.1f}, {ha:.1f}]；β = {mb:.3f}  [{lb:.2f}, {hb:.2f}]；σ_w = {mw:.2f}s  [{lw:.1f}, {hw:.1f}]")
P(f"- **β≪1：本地构型间差异传到官方只剩 {mb*100:.0f}%**——本地排序信息在官方尺度强烈压缩（反过拟合纪律的定量根据）。")

# τ₀ 敏感性（粗网格，只看边缘均值）
AG = np.arange(95.0, 135.0, 1.0); BG = np.arange(0.0, 1.2, 0.02); WG = np.arange(3.0, 25.0, 0.5)
def coarse_means(tau0):
    lpc = np.full((len(AG), len(BG), len(WG)), -np.inf)
    for ia, a in enumerate(AG):
        for ib, b in enumerate(BG):
            for iw, w in enumerate(WG):
                ll = 0.0
                for c in keys:
                    y = y_by[c]; J = len(y)
                    r = y - a - b * m_c(c)
                    s2 = w * w; V = stats[c][3] ** 2 + tau0 ** 2
                    k = b * b * V
                    quad = (r @ r) / s2 - (k * (r.sum()) ** 2) / (s2 * s2 * (1 + k * J / s2))
                    logdet = J * np.log(s2) + np.log1p(k * J / s2)
                    ll += -0.5 * (J * np.log(2 * np.pi) + logdet + quad)
                lpc[ia, ib, iw] = ll + (-0.5 * ((a - PRIOR_A[0]) / PRIOR_A[1]) ** 2
                                        - 0.5 * ((b - PRIOR_B[0]) / PRIOR_B[1]) ** 2)
    lpc -= lpc.max()
    pc = np.exp(lpc); pc /= pc.sum()
    out = []
    for ax, grid in ((0, AG), (1, BG), (2, WG)):
        pm = pc.sum(axis=tuple(i for i in range(3) if i != ax))
        out.append(float((pm * grid).sum()))
    return out
for t in (2.0, 8.0):
    a2, b2, w2 = coarse_means(t)
    P(f"- 敏感性 τ₀={t:.0f}s（粗网格）：α≈{a2:.1f}，β≈{b2:.3f}，σ_w≈{w2:.2f}s")

# 后验抽样（网格多项 + θ 条件正态）
flat = post.ravel()
idx = rng.choice(flat.size, size=40000, p=flat)
IA, IB, IW = np.unravel_index(idx, post.shape)
A_s, B_s, W_s = ALPHA[IA], BETA[IB], SIGW[IW]
TH = {}
for c in keys:
    y = y_by[c]
    J = len(y)
    V = V_c(c)
    prec_p = 1 / V + J * B_s ** 2 / W_s ** 2
    mean_p = (m_c(c) / V + (y.sum() - J * A_s) * B_s / W_s ** 2) / prec_p
    TH[c] = rng.normal(mean_p, np.sqrt(1 / prec_p))

def predict(cfg_key, n=40000):
    """新官方单发的预测分布（含 θ 不确定 + σ_w）"""
    if cfg_key in TH:
        th = TH[cfg_key]
    else:
        n_, m, sd, se = stats[cfg_key]
        th = rng.normal(m, np.sqrt(se ** 2 + TAU0 ** 2), n)
    return rng.normal(A_s + B_s * th, W_s)

P("\n## E. 五发后验官方均值 vs 实际（全量拟合）")
P("| 构型 | 官方发数 | 本地协变量 m_c (se) | 后验 μ̂_off [95%] | 官方均值 | 残差 z |")
P("|---|---|---|---|---|---|")
for c in keys:
    mu_q = np.quantile(A_s + B_s * TH[c], [0.025, 0.5, 0.975])
    ybar = np.mean(y_by[c])
    J = len(y_by[c])
    sd_mu = np.std(A_s + B_s * TH[c])
    z = (ybar - np.median(A_s + B_s * TH[c])) / np.sqrt(sd_mu ** 2 + np.median(W_s) ** 2 / J)
    n_, m, sd, se = stats[c]
    day = next(d for cc, _, d in OFFICIAL if cc == c)
    P(f"| {day} {c} | {J} | {m:.1f} ({se:.1f}) | {mu_q[1]:.1f} [{mu_q[0]:.1f}, {mu_q[2]:.1f}] | {ybar:.4f} | {z:+.2f} |")

P("\n## F. 历史-only 拟合对 11/07 五发的先验外推（LOO 诚实性检验）")
hist_keys = [c for c in keys if not c.startswith("shot")]
lp2 = np.full_like(lp, -np.inf)
for ia, a in enumerate(ALPHA):
    for ib, b in enumerate(BETA):
        for iw, w in enumerate(SIGW):
            ll = 0.0
            for c in hist_keys:
                y = y_by[c]
                J = len(y)
                r = y - a - b * m_c(c)
                s2 = w * w
                k = b * b * V_c(c)
                quad = (r @ r) / s2 - (k * (r.sum()) ** 2) / (s2 * s2 * (1 + k * J / s2))
                logdet = J * np.log(s2) + np.log1p(k * J / s2)
                ll += -0.5 * (J * np.log(2 * np.pi) + logdet + quad)
            lp2[ia, ib, iw] = ll + (-0.5 * ((a - PRIOR_A[0]) / PRIOR_A[1]) ** 2
                                    - 0.5 * ((b - PRIOR_B[0]) / PRIOR_B[1]) ** 2)
lp2 -= lp2.max()
post2 = np.exp(lp2)
post2 /= post2.sum()
flat2 = post2.ravel()
idx2 = rng.choice(flat2.size, size=40000, p=flat2)
IA2, IB2, IW2 = np.unravel_index(idx2, post2.shape)
A2, B2, W2 = ALPHA[IA2], BETA[IB2], SIGW[IW2]
P("| 发 | 预测中位 [95%PI] | 实际 | PI 覆盖 |")
P("|---|---|---|---|")
for c, y, day in OFFICIAL:
    if c in EXCLUDE or not c.startswith("shot"):
        continue
    n_, m, sd, se = stats[c]
    if c in ("shot1_probeTBr36", "HR2_leak42/60/4000"):
        th2 = rng.normal(m, np.sqrt(se ** 2 + TAU0 ** 2), 40000)
    else:
        prec_p = 1 / V_c(c) + len(y_by[c]) * B2 ** 2 / W2 ** 2
        mean_p = (m / V_c(c) + (y_by[c].sum() - len(y_by[c]) * A2) * B2 / W2 ** 2) / prec_p
        th2 = rng.normal(mean_p, np.sqrt(1 / prec_p))
    pred = rng.normal(A2 + B2 * th2, W2)
    q = np.quantile(pred, [0.025, 0.5, 0.975])
    ybar = np.mean(y_by[c])
    cov = "✓" if q[0] <= ybar <= q[2] else "✗"
    P(f"| {day} {c} | {q[1]:.1f} [{q[0]:.1f}, {q[2]:.1f}] | {ybar:.4f} | {cov} |")

P("\n## G. 复测风险信封（Shot2 / Shot45 构型新官方单发的预测分布）")
for c, anchor in [("shot2_leak40x3_36x3", 124.3683), ("shot45_fast14asym", 140.0247)]:
    pred = predict(c)
    q = np.quantile(pred, [0.05, 0.25, 0.5, 0.75, 0.95])
    P(f"- {c}: 复测分位 [5,25,50,75,95]% = {q[0]:.1f} / {q[1]:.1f} / {q[2]:.1f} / {q[3]:.1f} / {q[4]:.1f} s；"
      f"P(≤{anchor}) = {(pred <= anchor).mean()*100:.1f}%；"
      f"P(≤119.8293=Catnet) = {(pred <= 119.8293).mean()*100:.1f}%；P(≤117.0257=榜首) = {(pred <= 117.0257).mean()*100:.1f}%")
P("- **口径声明**：以上为「官方统一复测下的方差信封」估计（合规分析），非抽低分计划；P(≤锚点) 是复测风险量化，不是预期成绩。")

P("\n## H. 出分延迟（次要遥测）")
P("- 11/07 五发评测耗时：23.1 / 8.2 / 18.4 / 9.6 / 17.8 min（中位 17.8，最大 23.1）；"
  "11/05–11/06 批量齐发时段（00:56:29/35/40 三连发）出分同批到达。既有 WAIT_MIN=45–60min 建议相对观测最大值 23.1min 有 ≥2× 安全余量。")

P("\n## I. 汇总")
P(f"1. 校准映射：官方 ≈ {ma:.1f} + {mb:.2f}×本地（95% 区间 α[{la:.0f},{ha:.0f}]、β[{lb:.2f},{hb:.2f}]）；"
  f"同构型官方单发 σ_w={mw:.1f}s。同构官方重复仅两组：shot45×2（140.025/155.161，极差 15.14s，进校准）"
  "与 v1×2（sd 1.4s，坏域剔除仅作参考）——σ_w 后验主要由 shot45 对与总散布共同决定。")
P("2. β≪1 + σ_w≈8–10s ⇒ 本地均值排序对官方排序的传递性弱：**本地 ±5s 内的构型差异在官方不可分辨**——选型必须按邻域稳定+均值，min-of-N 无效。")
P("3. 残差审计：① shot2 官方 124.37 落在后验均值 95% 区间外（z=−1.8，约 3–4% 分位）——"
  "属低分尾部抽样；复测信封 P(≤124.37)≈4.2%，官方「取平均」规则下必须按均值口径管理预期。"
  "② tb 突发惩罚在本地测试床已可见：tb-r36 探针本地 146.9s vs 同放行 leak-36 本地 134.0s（+12.9s），"
  "官方 143.6 vs 133.1（+10.5s）同向复现——本地/官方机理一致，非校准失灵。")
P("4. 合规：全部数据取自本仓库 runs/ 既有记录；推断为闭门网格后验（seed=42，无 MCMC 收敛问题）；零远程探测、零提交。")

with open("zcode/scripts/_0084_out.md", "w", encoding="utf-8") as f:
    f.write("\n".join(OUT) + "\n")
print("\n[saved] _0084_out.md")
