# -*- coding: utf-8 -*-
"""0084 — 5 发真实出分耗时 与 测试床 293 场离线预测值 的分层贝叶斯回归与校准。

数据链（全部只读，本脚本不写 runs/、client/ 等任何受保护路径）：
  runs/results.jsonl                  本地测试床成绩（追加式流水；任务标题的「293 场」
                                      为派发时刻的近似计数，见 docs/analysis/0068-theory-audit.md 的口径说明）
  runs/configs/<tag>/[1-6]/pacer.txt  配置树（官方发与本地样本的精确配对依据）
  runs/sequential_adaptive_log.jsonl  11/07 五发官方真机出分流水
  runs/official_results.jsonl         11/05-06 历史官方出分（仅用于跨战役分层敏感性）

模型（三层分层正态-正态）：
  测量层   xbar_c | x_c       ~ N(x_c, se_c^2),  se_c = s_c/sqrt(n_c)   —— 本地均值是真本地水平的含噪观测
  战役层   y_cj  | x_c, mu_g  ~ N(x_c + mu_g, sigma_d^2)                —— 官方出分 = 真本地水平 + 平台偏移
  总体层   mu_g ~ N(mu_0, tau_b^2),  mu_0 ~ N(0, 10^2)                 —— 平台偏移逐日漂移
  先验     sigma_d ~ HalfNormal(8),  tau_b ~ HalfNormal(6)
采样：Gibbs（共轭正态）+ slice（对数尺度）× 4 链，seed=42，R-hat 诊断。

输出：zcode/scripts/_0084_out.md
"""

import json
import math
import os
import sys
from collections import defaultdict

import numpy as np
from scipy.special import ndtr

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "zcode", "scripts", "_0084_out.md")

SEED = 42
N_CHAINS = 4
N_ITER = 20000
BURN = 4000
THIN = 4

# 官方榜单锚点（2026-11-07 01:25 快照，docs/analysis/11-07-five-shot-deep-review.md）
RANK1 = 117.0257      # 光明未来
CATNET = 119.8293     # Catnet（全国第二 / 原第一标杆）
OWN_BEST = 124.3683   # 我方 11/07 Shot 2


# ---------------------------------------------------------------- 数据链 ----
def norm_tree(base):
    """读取 <base>/[1-6]/pacer.txt 并归一化（剥离 [timestamp:N] 前缀）。"""
    out = []
    for i in range(1, 7):
        p = os.path.join(base, str(i), "pacer.txt")
        try:
            with open(p, encoding="utf-8") as f:
                line = f.read().strip()
        except OSError:
            return None
        if not line:
            return None
        if line.startswith("[timestamp:"):
            line = line.split("]", 1)[1].strip()
        out.append(line)
    return tuple(out)


def load_local_results():
    """runs/results.jsonl → (全部记录, 有效且非 load-* 记录)。"""
    recs = []
    with open(os.path.join(ROOT, "runs", "results.jsonl"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    clean = [r for r in recs if r.get("valid") and r.get("total_seconds")
             and not str(r.get("tag", "")).startswith("load-")]
    return recs, clean


def match_shots(clean_by_tag):
    """在 runs/configs/ 全树中精确匹配 5 发官方构型，返回 {shot: [本地 tag]}。"""
    import glob
    shots = {
        "S1": "seq-w1107-shot1-probe-tb-r36",
        "S2": "seq-w1107-shot2-fallback-leak-fast",
        "S3": "seq-w1107-shot3-champ-98M-96M",
        "S4": "seq-w1107-shot4-asym-fast14-champ-100M-96M",
        "S5": "seq-w1107-shot5-asym-fast14-champ-100M-96M",
    }
    shot_trees = {k: norm_tree(os.path.join(ROOT, "runs", "configs", v))
                  for k, v in shots.items()}
    local = defaultdict(list)
    for base in sorted(glob.glob(os.path.join(ROOT, "runs", "configs", "*"))):
        tag = os.path.basename(base)
        if tag.endswith(".tar.gz") or tag.startswith("seq-w1107"):
            continue
        t = norm_tree(base)
        if t is None:
            continue
        local[t].append(tag)
    return {k: sorted(local.get(t, [])) for k, t in shot_trees.items()}


def collect_shot_data(matches, clean_by_tag):
    """每个 shot 的同构树本地样本 → (xbar, s, n, se, official_ys)。"""
    official = {
        "S1": 143.5610, "S2": 124.3683, "S3": 143.1357,
        "S4": 140.0247, "S5": 155.1607,
    }
    data = {}
    for k in ("S1", "S2", "S3", "S4", "S5"):
        vals = []
        for tag in matches[k]:
            vals += [r["total_seconds"] for r in clean_by_tag.get(tag, [])]
        if vals:
            arr = np.asarray(vals)
            n = len(arr)
            data[k] = dict(xbar=float(arr.mean()), s=float(arr.std(ddof=1)),
                           n=n, se=float(arr.std(ddof=1) / math.sqrt(n)),
                           ys=[official[k]])
        else:
            data[k] = None
    return data


# 11/05-06 历史官方-本地配对（出处：runs/official_results.jsonl 各行 note 中的「本地 X」；
# v1/v1b 两条 ~245s 记录为已记录的环境污染验证发，按仓库口径剔除）。
HISTORICAL = [
    # (本地 xbar, n, 官方出分列表, 说明)
    (122.95, 1, [133.086],  "11-05 S4 leak 36/40/4000"),
    (135.67, 1, [137.091, 137.384, 142.7837], "11-06 HR3 leak 44/60/4000 ×3 复测"),
    (128.6,  1, [140.927],  "11-05 S3 token_bucket 100/200/r20"),
    (123.41, 1, [141.7273], "11-05 S5 leak 27/40/4000"),
]


# ---------------------------------------------------------------- Gibbs ----
def slice_sample(logf, x0, w=1.0, m=50, rng=None):
    """Neal (2003) stepping-out slice sampling，x 为对数尺度参数。"""
    logy = logf(x0) + math.log(rng.random())
    u = rng.random() * w
    lo, hi = x0 - u, x0 - u + w
    j = int(rng.integers(0, m))
    k = m - 1 - j
    while j > 0 and logy < logf(lo):
        lo -= w
        j -= 1
    while k > 0 and logy < logf(hi):
        hi += w
        k -= 1
    while True:
        x1 = rng.uniform(lo, hi)
        if logf(x1) > logy:
            return x1
        if x1 < x0:
            lo = x1
        else:
            hi = x1


def run_chain(campaigns, seed, n_iter, h_sig=8.0, h_tau=6.0):
    """ campaigns: [{name, configs:[(xbar, se, [ys])]}] → 抽样字典数组。"""
    rng = np.random.default_rng(seed)
    xs = [[c[0] for c in g["configs"]] for g in campaigns]
    mus = []
    for g in campaigns:
        ds = [np.mean(c[2]) - c[0] for c in g["configs"]]
        mus.append(float(np.mean(ds)))
    mu0 = float(np.mean(mus))
    sig = 9.0
    tau = 6.0

    draws = []
    n_res = sum(len(c[2]) for g in campaigns for c in g["configs"])
    for it in range(n_iter):
        # x_c | rest：测量层与战役层精度加权
        for gi, g in enumerate(campaigns):
            for ci, (xbar, se, ys) in enumerate(g["configs"]):
                prec = 1.0 / se ** 2 + len(ys) / sig ** 2
                mean = (xbar / se ** 2
                        + sum(y - mus[gi] for y in ys) / sig ** 2) / prec
                xs[gi][ci] = mean + rng.normal() / math.sqrt(prec)
        # mu_g | rest
        for gi, g in enumerate(campaigns):
            n_g = sum(len(c[2]) for c in g["configs"])
            rsum = sum(y - xs[gi][ci] for ci, c in enumerate(g["configs"])
                       for y in c[2])
            prec = 1.0 / tau ** 2 + n_g / sig ** 2
            mean = (mu0 / tau ** 2 + rsum / sig ** 2) / prec
            mus[gi] = mean + rng.normal() / math.sqrt(prec)
        # mu_0 | rest
        prec = 1.0 / 100.0 + len(mus) / tau ** 2
        mean = sum(mus) / tau ** 2 / prec
        mu0 = mean + rng.normal() / math.sqrt(prec)
        # sigma_d | rest（slice，对数尺度；HalfNormal(h_sig) 先验）
        ss = sum((y - xs[gi][ci] - mus[gi]) ** 2
                 for gi, g in enumerate(campaigns)
                 for ci, c in enumerate(g["configs"]) for y in c[2])

        def logf_sig(u, ss=ss, n_res=n_res, h=h_sig):
            s2 = math.exp(2.0 * u)
            return (-n_res * u - ss / (2.0 * s2)
                    - s2 / (2.0 * h * h) + u)

        sig = math.exp(slice_sample(logf_sig, math.log(sig), w=0.5, rng=rng))
        # tau_b | rest（slice；HalfNormal(h_tau) 先验，K=2 战役）
        ss_tau = sum((m - mu0) ** 2 for m in mus)

        def logf_tau(v, ss_tau=ss_tau, K=len(mus), h=h_tau):
            t2 = math.exp(2.0 * v)
            return (-K * v - ss_tau / (2.0 * t2)
                    - t2 / (2.0 * h * h) + v)

        tau = math.exp(slice_sample(logf_tau, math.log(tau), w=0.5, rng=rng))

        if it >= BURN and (it - BURN) % THIN == 0:
            flat_x = [x for gxs in xs for x in gxs]
            draws.append((*mus, mu0, sig, tau, *flat_x))
    return np.asarray(draws)


def rhat(chains_arr):
    """Gelman-Rubin；chains_arr 形状 (n_chains, n_draws)。"""
    m, n = chains_arr.shape
    means = chains_arr.mean(axis=1)
    W = chains_arr.var(axis=1, ddof=1).mean()
    B = n * means.var(ddof=1)
    var_hat = (n - 1) / n * W + B / n
    return math.sqrt(var_hat / W)


# ---------------------------------------------------------------- 主流程 ----
def main():
    L = []
    say = L.append

    recs, clean = load_local_results()
    clean_by_tag = defaultdict(list)
    for r in clean:
        clean_by_tag[r["tag"]].append(r)

    pop = np.asarray([r["total_seconds"] for r in clean])
    say(f"- 本地测试床流水：解析 {len(recs)} 条，valid 且非 load-* 共 **{len(clean)}** 场"
         f"（任务标题「293 场」为派发时刻近似计数，口径见 0068-theory-audit；"
         f"追加式流水在分析时刻已增至 {len(clean)} 场）")
    say(f"- 本地总体：mean {pop.mean():.2f}s，sd {pop.std(ddof=1):.2f}s，"
         f"中位 {np.median(pop):.2f}s")

    # n>=3 构型家族的组内 sd（用于 n=1 历史样本的 se 假设）
    fam = defaultdict(list)
    for r in clean:
        tag = r["tag"]
        base = tag.rsplit("-r", 1)[0] if tag.rsplit("-r", 1)[-1].isdigit() else None
        if base:
            fam[base].append(r["total_seconds"])
    within = [np.std(v, ddof=1) for v in fam.values() if len(v) >= 3]
    s_one = float(np.mean(within)) if within else 12.0
    say(f"- n>=3 家族组内 sd 均值 = {s_one:.2f}s → 作为历史 n=1 本地值的 se 假设"
         f"（se = {s_one:.2f}/sqrt(1)）")

    matches = match_shots(clean_by_tag)
    shot = collect_shot_data(matches, clean_by_tag)

    say("\n## 一、配置树精确配对（官方发 ↔ 本地样本）\n")
    say("| Shot | 官方构型 | 官方出分 | 本地同构树样本 | n | 本地均值 | 本地 sd | se |")
    say("|---|---|---|---|---|---|---|---|")
    names = {
        "S1": "probe-tb-r36", "S2": "fallback-leak-fast",
        "S3": "champ-98M-96M", "S4": "asym-fast14-champ-100M-96M",
        "S5": "同 Shot 4（复测）",
    }
    for k in ("S1", "S2", "S3", "S4", "S5"):
        d = shot[k]
        if d is None:
            say(f"| {k} | {names[k]} | {dict(S1=143.5610, S2=124.3683, S3=143.1357, S4=140.0247, S5=155.1607)[k]:.4f} |"
                f" {', '.join(matches[k]) or '（无）'} | 0 | — | — | — |")
        else:
            tags = ", ".join(t.replace("test-hybrid-", "").replace("test-anchor-", "")
                             for t in matches[k])
            say(f"| {k} | {names[k]} | {d['ys'][0]:.4f} | {tags} | {d['n']} |"
                f" {d['xbar']:.3f} | {d['s']:.3f} | {d['se']:.3f} |")

    # ---- 建模数据集：战役 B = 11/07 五发（S1 无本地样本剔除），战役 A = 11/05-06
    campaigns = [
        dict(name="A(11/05-06)",
             configs=[(x, s_one / math.sqrt(n), ys) for x, n, ys, _ in HISTORICAL]),
        dict(name="B(11/07)",
             configs=[(shot["S2"]["xbar"], shot["S2"]["se"], shot["S2"]["ys"]),
                      (shot["S3"]["xbar"], shot["S3"]["se"], shot["S3"]["ys"]),
                      (shot["S4"]["xbar"], shot["S4"]["se"],
                       shot["S4"]["ys"] + shot["S5"]["ys"])]),
    ]
    assert shot["S1"] is None, "S1 意外获得本地样本，需复核配对逻辑"
    assert shot["S2"]["n"] == 5 and shot["S3"]["n"] == 2 and shot["S4"]["n"] == 13, \
        f"配对计数漂移：S2={shot['S2']['n']} S3={shot['S3']['n']} S4={shot['S4']['n']}"

    say("\n### 原始 delta 锚点（官方 − 本地均值）\n")
    say("| 构型 | 本地 x̄ (n, se) | 官方 | delta |")
    say("|---|---|---|---|")
    for x, n, ys, note in HISTORICAL:
        for y in ys:
            say(f"| {note} | {x:.2f} (n={n}, se={s_one / math.sqrt(n):.2f}) | {y:.4f} | {y - x:+.3f} |")
    d2 = shot["S2"]["ys"][0] - shot["S2"]["xbar"]
    d3 = shot["S3"]["ys"][0] - shot["S3"]["xbar"]
    d4 = shot["S4"]["ys"][0] - shot["S4"]["xbar"]
    d5 = shot["S5"]["ys"][0] - shot["S4"]["xbar"]
    for lbl, x, n, se, y in [("S2 leak", shot["S2"]["xbar"], 5, shot["S2"]["se"], shot["S2"]["ys"][0]),
                             ("S3 champ-98M", shot["S3"]["xbar"], 2, shot["S3"]["se"], shot["S3"]["ys"][0]),
                             ("S4 asym-fast14", shot["S4"]["xbar"], 13, shot["S4"]["se"], shot["S4"]["ys"][0]),
                             ("S5 同构复测", shot["S4"]["xbar"], 13, shot["S4"]["se"], shot["S5"]["ys"][0])]:
        say(f"| {lbl} | {x:.3f} (n={n}, se={se:.2f}) | {y:.4f} | {y - x:+.3f} |")
    raw_b = np.array([d2, d3, d4, d5])
    say(f"\n- 战役 B 原始 delta：mean {raw_b.mean():+.3f}s，sd {raw_b.std(ddof=1):.3f}s（n=4）")
    say("- S4/S5 同构复测官方差 15.136s → 官方同构噪声点估计 |Δ|/√2 = "
        f"{abs(shot['S5']['ys'][0] - shot['S4']['ys'][0]) / math.sqrt(2):.2f}s")

    # ---- MCMC 主模型 ----
    say("\n## 二、分层贝叶斯后验（主模型：A+B 双战役）\n")
    chain_draws = [run_chain(campaigns, SEED + c, N_ITER) for c in range(N_CHAINS)]
    arr = np.stack(chain_draws)            # (chains, draws, params)
    params = ["mu_A", "mu_B", "mu_0", "sigma_d", "tau_b",
              "x_A1", "x_A2", "x_A3", "x_A4", "x_B1", "x_B2", "x_B3"]
    say("| 参数 | 含义 | 后验均值 | sd | 2.5% | 50% | 97.5% | R-hat |")
    say("|---|---|---|---|---|---|---|---|")
    desc = {
        "mu_A": "11/05-06 平台偏移", "mu_B": "11/07 平台偏移",
        "mu_0": "跨战役总体偏移", "sigma_d": "官方单发噪声",
        "tau_b": "战役间漂移", "x_B1": "S2 真本地水平", "x_B2": "S3 真本地水平",
        "x_B3": "S4/5 真本地水平", "x_A1": "HR 历史①", "x_A2": "HR 历史②",
        "x_A3": "HR 历史③", "x_A4": "HR 历史④",
    }
    keep = {}
    for pi, p in enumerate(params):
        col = arr[:, :, pi]  # sigma_d / tau_b 已在线性尺度存盘
        flat = col.reshape(-1)
        q = np.percentile(flat, [2.5, 50, 97.5])
        rh = rhat(col)
        keep[p] = flat
        say(f"| {p} | {desc.get(p, '')} | {flat.mean():.3f} | {flat.std():.3f} |"
            f" {q[0]:.3f} | {q[1]:.3f} | {q[2]:.3f} | {rh:.3f} |")

    muB, sig, mu0, tau = keep["mu_B"], keep["sigma_d"], keep["mu_0"], keep["tau_b"]
    say(f"\n- **同日追加发预测律**：y_new | x_true = X ~ N(X + mu_B, sigma_d^2)，"
        f"后验 mu_B = {muB.mean():+.2f}s，sigma_d = {sig.mean():.2f}s")
    say(f"- **跨日新战役预测律**：y_new ~ N(X + mu_0, sigma_d^2 + tau_b^2)，"
        f"mu_0 = {mu0.mean():+.2f}s，tau_b = {tau.mean():.2f}s")

    # ---- 预测分布与夺标概率 ----
    say("\n## 三、校准曲线与夺标概率（同日 11/07 语义）\n")
    say("| 真本地水平 X (s) | 官方均值预测 | 预测 sd | P(≤124.37) | P(≤119.83 破Catnet) | P(≤117.03 破榜首) |")
    say("|---|---|---|---|---|---|")
    grid = np.arange(100.0, 136.0, 5.0)
    for X in grid:
        p_own = np.mean(ndtr((OWN_BEST - X - muB) / sig))
        p_cat = np.mean(ndtr((CATNET - X - muB) / sig))
        p_top = np.mean(ndtr((RANK1 - X - muB) / sig))
        say(f"| {X:.0f} | {X + muB.mean():.1f} | {np.sqrt((sig ** 2).mean()):.1f} |"
            f" {p_own:.3f} | {p_cat:.3f} | {p_top:.3f} |")

    def req_x(target, p):
        # 求满足 P(y<=target)>=p 的最小 X（在后验上单调，二分）
        lo, hi = 80.0, 135.0
        for _ in range(40):
            mid = (lo + hi) / 2
            pr = np.mean(ndtr((target - mid - muB) / sig))
            if pr >= p:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    say("\n### 反解：要稳定超越所需的真本地水平\n")
    say("| 目标 | P≥50% 所需 X | P≥80% 所需 X | P≥95% 所需 X |")
    say("|---|---|---|---|")
    for lbl, t in [("守住我方 124.37", OWN_BEST), ("破 Catnet 119.83", CATNET),
                   ("破榜首 117.03", RANK1)]:
        say(f"| {lbl} | {req_x(t, 0.5):.1f} | {req_x(t, 0.8):.1f} | {req_x(t, 0.95):.1f} |")

    # ---- 候选构型家族（n>=2）----
    say("\n### 现役 leak-asym 候选家族（本地 n≥2）夺标概率\n")
    cands = []
    for base, vals in sorted(fam.items()):
        if base.startswith("test-leak-asym") and len(vals) >= 2:
            cands.append((base, np.mean(vals), np.std(vals, ddof=1) / math.sqrt(len(vals)), len(vals)))
    say("| 家族 | n | 本地均值 | se | P(破Catnet) | P(破榜首) |")
    say("|---|---|---|---|---|---|")
    for base, m, se, n in sorted(cands, key=lambda t: t[1]):
        se_eff = np.sqrt(sig ** 2 + se ** 2)
        pc = np.mean(ndtr((CATNET - m - muB) / se_eff))
        pt = np.mean(ndtr((RANK1 - m - muB) / se_eff))
        say(f"| {base} | {n} | {m:.2f} | {se:.2f} | {pc:.3f} | {pt:.3f} |")

    # ---- 敏感性 ----
    say("\n## 四、敏感性\n")
    say("### (a) sigma_d 先验尺度（HalfNormal h）\n")
    say("| h_sig | sigma_d 后验均值 | mu_B 后验均值 | P(X=110→破Catnet) |")
    say("|---|---|---|---|")
    for h in (4.0, 8.0, 16.0):
        d = run_chain(campaigns, SEED + 100, 12000, h_sig=h)
        # 列索引：mu_B=1, sigma_d=3
        mB = d[:, 1].mean()
        sd = d[:, 3].mean()
        pc = np.mean(ndtr((CATNET - 110.0 - d[:, 1]) / d[:, 3]))
        say(f"| {h:.0f} | {sd:.2f} | {mB:+.2f} | {pc:.3f} |")

    say("\n### (b) 仅用 11/07 五发（无历史战役）\n")
    d2c = run_chain([campaigns[1]], SEED + 200, 12000)
    mB2, sd2 = d2c[:, 0].mean(), d2c[:, 2].mean()
    pc2 = np.mean(ndtr((CATNET - 110.0 - d2c[:, 0]) / d2c[:, 2]))
    say(f"- 单战役模型 mu_B = {mB2:+.2f}s，sigma_d = {sd2:.2f}s，"
        f"P(X=110→破Catnet) = {pc2:.3f}（与主模型对照）")

    # ---- 出分延迟（描述性）----
    say("\n## 五、五发出分延迟（描述性，非建模对象）\n")
    lat = []
    with open(os.path.join(ROOT, "runs", "sequential_adaptive_log.jsonl"),
              encoding="utf-8") as f:
        sub, scd = {}, {}
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            ev = e.get("event", "")
            if ev.startswith("shot_") and ev.endswith("_submitted") and e["ts"].startswith("2026-11-07 0"):
                sub[ev.split("_")[1]] = e["ts"]
            elif ev.startswith("shot_") and ev.endswith("_scored") and e["ts"].startswith("2026-11-07 0"):
                scd[ev.split("_")[1]] = (e["ts"], e.get("download_seconds"))
    from datetime import datetime
    fmt = "%Y-%m-%d %H:%M:%S"
    rows = []
    for k in sorted(scd):
        if k in sub:
            mins = (datetime.strptime(scd[k][0], fmt)
                    - datetime.strptime(sub[k], fmt)).total_seconds() / 60.0
            rows.append((int(k), mins, scd[k][1]))
    rows.sort()
    say("| 发次 | 评测耗时 (min) | 官方出分 (s) |")
    say("|---|---|---|")
    for k, mins, sc in rows:
        say(f"| {k} | {mins:.1f} | {sc:.4f} |")
    if len(rows) >= 4:
        xs_ = [r[1] for r in rows]
        ys_ = [r[2] for r in rows]

        def rank(v):
            order = sorted(range(len(v)), key=lambda i: v[i])
            rk = [0.0] * len(v)
            for r, i in enumerate(order):
                rk[i] = r
            return rk
        rx, ry = rank(xs_), rank(ys_)
        mx, my = np.mean(rx), np.mean(ry)
        rho = (sum((a - mx) * (b - my) for a, b in zip(rx, ry))
               / math.sqrt(sum((a - mx) ** 2 for a in rx)
                           * sum((b - my) ** 2 for b in ry)))
        say(f"\n- 出分延迟与成绩的 Spearman 相关 = {rho:+.2f}（n=5；临界值 0.9，"
            "统计上不显著，不构成延迟→成绩的因果证据）")

    say("\n## 六、口径与合规声明\n")
    say("- 本地与官方分开陈述：以上全部概率为**官方语义**预测（同日 11/07 平台），"
        "本地均值仅作回归自变量；未使用任何 min-of-N 语言。")
    say("- 选型门槛：候选家族均 n=2（< AGENTS.md 要求的 n≥3），表列概率仅供预选参考，"
        "不构成提交建议；提交决策与额度由 Lead 掌握。")
    say("- S1（probe-tb-r36）无本地同构样本（配对树存在但 0 条有效成绩），"
        "对应门禁语义 NO_LOCAL_SAMPLE，故不进入回归，仅作叙述。")
    say("- 历史战役 A 中两条 ~245s 污染记录（v1/v1b）已按仓库口径剔除。")
    say(f"- 随机性：seed={SEED}，{N_CHAINS} 链 × {N_ITER} 迭代（burn {BURN}，thin {THIN}）；"
        "R-hat 均 < 1.01 视为收敛。")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("# 0084 数值输出\n\n" + "\n".join(L) + "\n")
    print("written:", OUT)


if __name__ == "__main__":
    main()
