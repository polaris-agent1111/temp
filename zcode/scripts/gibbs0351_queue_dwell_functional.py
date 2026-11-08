# -*- coding: utf-8 -*-
"""0351: 非对称排队网络吉布斯采样与瓶颈路由器驻留时间泛函推演.

真实数据锚点
------------
- 观测: runs/results.jsonl 中 tag 全匹配 ^test-anchor-shot2-pert-40x3-37-36-36-r\\d+$
  且 valid=true 的 n=15 场本地逐轮下载时长 (6 轮, 秒)。
- 文件大小 (官方 docs/extracted/六载穿柜.md): 10/20/40/80/160/320 MB。
- 瓶颈: 100 Mbps 汇聚链路, 与目标速率 100 Mbps 的搜索背景流共享 (官方文档)。
- 整形速率 (真实配置): 1-3 轮 leak_rate=40 pkt/4ms, 4 轮 37, 5-6 轮 36;
  1 pkt/4ms = 2.4 Mbps -> 各轮 pacing 上限 96/96/96/88.8/86.4/86.4 Mbps。

模型 (贝叶斯层次, Gibbs 逐块采样)
--------------------------------
观测方程:  y_im = S_i / s_im + eps_im,  eps_im ~ N(0, sigma2)
容量分解:  s_im = C - b_im  (b_im = 第 i 轮第 m 场的背景负荷, Mbps)
层次先验:  b_im ~ TruncN(beta_i, omega2; 0, C-5)
           beta_i ~ TruncN(mu_b, tau2; 0, C-5)
           mu_b ~ N(60, 20^2);  sigma2, omega2, tau2 ~ InvGamma(弱信息)
pacing 约束: 有效服务率 min(s_im, lambda_i) — 后验中 s<<lambda_i, 约束不激活 (脚本内验证)。

驻留时间泛函:  F = sum_i S_i / (C - beta_i)  (六轮下载比特在瓶颈处累计驻留秒数)
收敛: 4 链 x 8000 步 (burn 3000), split-R-hat + 相对半链差 (门禁 <=2%)。
稳态: Geweke 批均值平稳性 |z|<1.96 通过率 (门禁 >=95%); 附每轮后验预测-实测重叠系数。

只读 runs/results.jsonl; 写 zcode/reports/0351_result.json (任务单授权)。
"""
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "runs" / "results.jsonl"
OUT = ROOT / "zcode" / "reports" / "0351_result.json"

C = 100.0                      # 瓶颈带宽 Mbps (官方)
S_MBIT = np.array([80.0, 160.0, 320.0, 640.0, 1280.0, 2560.0])   # 10..320 MB
LAMBDA = np.array([96.0, 96.0, 96.0, 88.8, 86.4, 86.4])          # pacing 上限
TAG_RE = re.compile(r"^test-anchor-shot2-pert-40x3-37-36-36-r\d+$")

N_CHAINS, N_ITER, N_BURN = 4, 8000, 3000
S_LO, S_HI = 5.0, 95.0        # s = C-b 的支撑 (b in (5,95))
GRID = np.linspace(S_LO, S_HI, 320)

rng = np.random.default_rng(20261108)


def load_observations():
    rows = []
    with RESULTS.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if not TAG_RE.match(d.get("tag", "")):
                continue
            if not d.get("valid", False):
                continue
            dl = d.get("downloads", {})
            if len(dl) != 6:
                continue
            rows.append([float(dl[f"{i}.bin"]) for i in range(1, 7)])
    return np.array(rows)  # (M, 6)


def trunc_norm_grid(mean, sd, lo, hi, n, rand):
    """支撑截断正态的精确网格采样 (返回 n 个样本)."""
    g = np.linspace(lo, hi, 512)
    lp = -0.5 * ((g - mean) / sd) ** 2
    p = np.exp(lp - lp.max())
    p /= p.sum()
    return rand.choice(g, size=n, replace=True, p=p)


def ig_draw(a0, b0, sse, rand):
    """InvGamma(a0 + n/2, b0 + SS/2) 的采样, SS = 残差平方和 (scale 参数化)."""
    a = a0 + sse.size / 2.0
    b = b0 + 0.5 * float(np.square(sse).sum())
    return b / rand.gamma(a, 1.0)


def run_chain(y, seed):
    rand = np.random.default_rng(seed)
    M, R = y.shape                      # 15 场 x 6 轮
    s = np.clip(S_MBIT[None, :] / y, S_LO, S_HI)     # 初始: 好吞吐
    beta = s.mean(axis=0).copy()
    mu_b = float(beta.mean())
    sigma2 = 4.0
    omega2 = 9.0
    tau2 = 25.0
    keep_F = np.empty(N_ITER - N_BURN)
    keep_beta = np.empty((N_ITER - N_BURN, R))
    keep_sigma2 = np.empty(N_ITER - N_BURN)
    F_full = np.empty(N_ITER)            # 全程留迹 (Geweke 用)
    beta_full = np.empty((N_ITER, R))

    Sb = np.repeat(S_MBIT, M)            # 90 向量, 轮次堆叠
    idx = np.repeat(np.arange(R), M)
    yv = y.T.reshape(-1)                 # 90, 顺序 [轮1的15场, 轮2的15场, ...]
    sv = s.T.reshape(-1).copy()

    for it in range(N_ITER):
        # --- b_im | rest : 1-D 精确网格采样 ---
        # 先验 b ~ N(beta_i, omega2) 截断 -> s = C-b
        lp = -0.5 * ((yv[:, None] - Sb[:, None] / GRID[None, :]) ** 2) / sigma2
        lp += -0.5 * ((C - GRID[None, :]) - beta[idx][:, None]) ** 2 / omega2
        p = np.exp(lp - lp.max(axis=1, keepdims=True))
        p /= p.sum(axis=1, keepdims=True)
        pick = (rand.random(sv.size)[:, None] > np.cumsum(p, axis=1)).sum(axis=1)
        pick = np.clip(pick, 0, GRID.size - 1)
        sv = GRID[pick]

        # --- beta_i | b_im : 截断网格采样 ---
        bmean = C - sv                       # b 样本
        cnt = np.bincount(idx, minlength=R)
        bsum = np.bincount(idx, weights=bmean, minlength=R)
        prec_lik = cnt / omega2
        mean_lik = bsum / np.maximum(cnt, 1)
        for i in range(R):
            post_prec = prec_lik[i] + 1.0 / tau2
            post_mean = (prec_lik[i] * mean_lik[i] + mu_b / tau2) / post_prec
            g = np.linspace(S_LO, S_HI, 512)          # beta 支撑同 s
            lp = -0.5 * post_prec * (g - post_mean) ** 2
            w = np.exp(lp - lp.max())
            w /= w.sum()
            beta[i] = rand.choice(g, p=w)

        # --- mu_b | beta (共轭正态) ---
        pr_v, pr_m = 400.0, 60.0
        post_v = 1.0 / (1.0 / pr_v + R / tau2)
        post_m = post_v * (pr_m / pr_v + beta.sum() / tau2)
        mu_b = post_m + math.sqrt(post_v) * rand.standard_normal()

        # --- 方差块 (共轭逆伽马) ---
        eps = yv - Sb / sv
        sigma2 = ig_draw(2.0, 4.0, eps, rand)
        eta = bmean - beta[idx]
        omega2 = ig_draw(2.0, 9.0, eta, rand)
        dev = beta - mu_b
        tau2 = ig_draw(2.0, 25.0, dev, rand)

        F_full[it] = float(np.sum(S_MBIT / np.clip(C - beta, 1e-6, None)))
        beta_full[it] = beta
        if it >= N_BURN:
            k = it - N_BURN
            keep_F[k] = F_full[it]
            keep_beta[k] = beta
            keep_sigma2[k] = sigma2

    return keep_F, keep_beta, keep_sigma2, F_full, beta_full


def batch_mean_z(x, batch=60):
    """Geweke 式平稳性: 首 10% vs 末 50%, 批均值方差估计."""
    a = x[: max(1, int(0.1 * x.size))]
    b = x[int(0.5 * x.size):]

    def bm(v):
        nb = max(1, v.size // batch)
        return v[: nb * batch].reshape(nb, batch).mean(axis=1)

    za, zb = bm(a), bm(b)
    va, vb = za.var(ddof=1), zb.var(ddof=1)
    z = (a.mean() - b.mean()) / math.sqrt(va / za.size + vb / zb.size + 1e-12)
    return float(z)


def overlap_coef(pred_samples, obs):
    """后验预测 vs 实测的归一化直方图重叠系数 (0-1)."""
    lo = min(pred_samples.min(), obs.min())
    hi = max(pred_samples.max(), obs.max())
    bins = np.linspace(lo, hi, 24)
    ph, _ = np.histogram(pred_samples, bins=bins, density=True)
    oh, _ = np.histogram(obs, bins=bins, density=True)
    w = np.diff(bins)
    ph, oh = ph * w, oh * w
    return float(np.minimum(ph, oh).sum())


def main():
    y = load_observations()
    M = y.shape[0]
    print(f"n_valid_runs = {M}; per-round mean = {y.mean(axis=0).round(2)}")

    Fs, Betas, Sig2s = [], [], []
    F_traces, Beta_traces = [], []
    for c in range(N_CHAINS):
        kF, kB, kS2, FF, BB = run_chain(y, 1000 + c)
        Fs.append(kF); Betas.append(kB); Sig2s.append(kS2)
        F_traces.append(FF); Beta_traces.append(BB)
        print(f"chain {c}: F post-mean = {kF.mean():.3f} s")

    Fs_a = np.concatenate(Fs)
    Betas_a = np.concatenate(Betas, axis=0)
    Sig2s_a = np.concatenate(Sig2s)

    # --- split-R-hat (F 与 beta_i) ---
    def split_rhat(chains):
        h = chains.shape[1] // 2
        parts = np.concatenate([chains[:, :h], chains[:, h:2 * h]], axis=0)
        W = parts.var(axis=1, ddof=1).mean()
        Bn = parts.mean(axis=1).var(ddof=1) * parts.shape[1]
        var_plus = (parts.shape[1] - 1) / parts.shape[1] * W + Bn / parts.shape[1]
        return math.sqrt(var_plus / W)

    Fs_ch = np.stack(Fs)                       # (chains, draws)
    Betas_ch = np.stack(Betas, axis=0)         # (chains, draws, 6)
    rhat_F = split_rhat(Fs_ch)
    rhat_beta = [split_rhat(Betas_ch[:, :, i]) for i in range(6)]

    # --- 收敛误差: 链间均值相对半差 (门禁 <=2%) ---
    chain_means = Fs_ch.mean(axis=1)
    half = chain_means.size // 2
    rel_half = abs(chain_means[:half].mean() - chain_means[half:].mean()) / chain_means.mean()
    conv_err = float(rel_half)

    # --- Geweke 平稳性 (全程留迹, 每链每参数) ---
    zF = [batch_mean_z(t) for t in F_traces]
    zB = [batch_mean_z(t[:, i]) for t in Beta_traces for i in range(6)]
    zs = np.array(zF + zB)
    stat_pass = float((np.abs(zs) < 1.96).mean())

    # --- 后验量 ---
    F_mean, F_sd = float(Fs_a.mean()), float(Fs_a.std(ddof=1))
    F_ci = np.percentile(Fs_a, [2.5, 97.5])
    beta_mean = Betas_a.mean(axis=0)
    beta_sd = Betas_a.std(axis=0, ddof=1)
    dwell_i = S_MBIT / np.clip(C - beta_mean, 1e-6, None)
    cap_i = C - beta_mean

    # pacing 约束是否激活
    cap_viol = float((cap_i > LAMBDA).mean())

    # --- 后验预测 vs 实测重叠 (逐轮, 含观测噪声 eps ~ N(0, sigma2)) ---
    ovl = []
    for i in range(6):
        mu_star = S_MBIT[i] / np.clip(C - Betas_a[:, i], 1e-6, None)
        pred = mu_star + rng.standard_normal(mu_star.size) * np.sqrt(Sig2s_a)
        ovl.append(overlap_coef(pred, y[:, i]))

    result = {
        "task": "0351",
        "data": {
            "source": "runs/results.jsonl",
            "tag_regex": TAG_RE.pattern,
            "n_runs": int(M),
            "per_round_obs_mean_s": y.mean(axis=0).round(3).tolist(),
            "per_round_obs_std_s": y.std(axis=0, ddof=1).round(3).tolist(),
        },
        "posterior": {
            "F_total_dwell_mean_s": F_mean,
            "F_total_dwell_sd_s": F_sd,
            "F_ci95_s": [float(F_ci[0]), float(F_ci[1])],
            "beta_bg_load_mean_Mbps": beta_mean.round(2).tolist(),
            "beta_bg_load_sd_Mbps": beta_sd.round(2).tolist(),
            "avail_capacity_mean_Mbps": cap_i.round(2).tolist(),
            "per_round_dwell_mean_s": dwell_i.round(2).tolist(),
            "pacing_cap_Mbps": LAMBDA.tolist(),
            "pacing_cap_active_frac": cap_viol,
            "mu_b_post_mean_Mbps": float(Betas_a.mean(axis=(0, 1)).mean()),
            "sigma_post_mean_s": float(np.sqrt(Sig2s_a).mean()),
        },
        "convergence": {
            "n_chains": N_CHAINS, "n_iter": N_ITER, "n_burn": N_BURN,
            "split_rhat_F": rhat_F,
            "split_rhat_beta": [round(v, 5) for v in rhat_beta],
            "relative_halfdiff_F": conv_err,
            "gate_conv_err_le_2pct": bool(conv_err <= 0.02),
        },
        "stationarity": {
            "geweke_z_F": [round(v, 3) for v in zF],
            "geweke_pass_frac_all_params": stat_pass,
            "n_params_tested": int(zs.size),
            "gate_stationarity_ge_95pct": bool(stat_pass >= 0.95),
            "pred_obs_overlap_per_round": [round(v, 4) for v in ovl],
        },
        "gates": {
            "functional_convergence_error_pct": round(conv_err * 100, 4),
            "functional_convergence_pass": bool(conv_err <= 0.02),
            "stationary_approx_pass_frac": round(stat_pass, 4),
            "stationary_approx_pass": bool(stat_pass >= 0.95),
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    print(json.dumps(result["gates"], ensure_ascii=False))
    print(f"saved -> {OUT}")


if __name__ == "__main__":
    main()
