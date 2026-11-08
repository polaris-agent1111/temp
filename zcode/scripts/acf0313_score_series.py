# -*- coding: utf-8 -*-
"""
acf0313_score_series.py — 任务 0313 验证脚本
官方排行榜出分序列时序相关性分析 + 随机游走假设检验

只读输入（不修改）:
  runs/official_results.jsonl          我方官方出分历史（11-05 ~ 11-06，10 条）
  runs/sequential_adaptive_log.jsonl   夜间逐发闭环事件（取 dry_run=false 真实段，11-07 5 发）
  runs/leaderboard/ledger.csv          榜单头部快照（作描述性背景，不参与 ACF）

输出（只写 zcode/）:
  stdout 全量文本结果
  zcode/scripts/out/0313_acf_results.json

口径说明:
  - 官方出分序列 = 按 submitted_at 升序的我方全部真实官方成绩（n=15）。
  - 绝不引用 sequential_1108_state.json / dry-run 段的 118.0x mock 分
    （uniform(117.5,123.5) 指纹，非官方成绩）。
  - v1/v1b 两发 245s 为 v1 配置失效期（结构断点），主分析同时报告
    全序列 n=15 与断点后 n=13 两种口径。
  - 方法：ACF（Bartlett 带）、PACF（Durbin-Levinson）、Ljung-Box、
    AR(p) 条件最小二乘 + AIC/BIC 定阶、ADF（常数项，手工实现，临界值
    为 MacKinnon 近似，小样本功效有限——如实报告）、差分序列 WN 检验
    （随机游走零假设下增量应为白噪声）、白噪声 MC 校准（max|r_k| 分布）。
  - n=15 属极小样本，一切结论按「未能拒绝」而非「证明」陈述。
"""
import csv
import json
import math
import os
import sys
from datetime import datetime

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(ROOT, "zcode", "scripts", "out")
os.makedirs(OUT_DIR, exist_ok=True)

Z95 = 1.959963984540054


# ---------------------------------------------------------------- data load
def load_official_results():
    rows = []
    path = os.path.join(ROOT, "runs", "official_results.jsonl")
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_night_scores():
    """真实段（最后一个 dry_run=false init 之后）的 shot_N_scored 事件。"""
    path = os.path.join(ROOT, "runs", "sequential_adaptive_log.jsonl")
    events = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    real_starts = [
        i
        for i, d in enumerate(events)
        if d.get("event") == "init_sequential_controller" and d.get("dry_run") is False
    ]
    if not real_starts:
        return []
    seg = events[real_starts[-1]:]
    return [
        {
            "submitted_at": d["raw"]["submitted_at"],
            "official_seconds": float(d["download_seconds"]),
            "note": "night-seq " + str(d.get("event", "")),
        }
        for d in seg
        if d.get("event", "").endswith("_scored") and "download_seconds" in d
    ]


def build_series():
    rows = load_official_results() + load_night_scores()
    rows.sort(key=lambda r: r["submitted_at"])
    ts = [datetime.strptime(r["submitted_at"], "%Y-%m-%d %H:%M:%S") for r in rows]
    y = np.array([float(r["official_seconds"]) for r in rows])
    notes = [r.get("note", "")[:40] for r in rows]
    return ts, y, notes, rows


# ---------------------------------------------------------------- core stats
def acf(x, kmax):
    x = np.asarray(x, dtype=float)
    n = len(x)
    xc = x - x.mean()
    c0 = np.dot(xc, xc) / n
    out = []
    for k in range(1, kmax + 1):
        ck = np.dot(xc[:-k], xc[k:]) / n
        out.append(ck / c0)
    return np.array(out), c0


def pacf_via_levinson(r_full_x, kmax):
    """Durbin-Levinson 递推求样本 PACF。"""
    x = np.asarray(r_full_x, dtype=float)
    n = len(x)
    xc = x - x.mean()
    c0 = np.dot(xc, xc) / n
    rho = [np.dot(xc[:-k], xc[k:]) / n / c0 for k in range(1, kmax + 1)]
    pacf = []
    phi = np.zeros(0)
    for k in range(1, kmax + 1):
        if k == 1:
            phi = np.array([rho[0]])
        else:
            # phi_new[k-1] = (rho[k-1] - sum(phi_j * rho[k-1-j])) / (1 - sum(phi_j*rho_j))
            num = rho[k - 1] - np.dot(phi, rho[k - 2 :: -1][: len(phi)]) if k > 1 else rho[0]
            den = 1.0 - np.dot(phi, rho[: len(phi)])
            new = num / den if abs(den) > 1e-12 else 0.0
            phi = np.append(phi * 1.0, 0.0)  # grow
            phi_new = phi.copy()
            phi_new[:-1] = phi[:-1] - new * phi[::-1][1:]
            phi_new[-1] = new
            phi = phi_new
        pacf.append(phi[-1])
    return np.array(pacf)


def ljung_box(x, K):
    x = np.asarray(x, dtype=float)
    n = len(x)
    r, _ = acf(x, K)
    Q = n * (n + 2) * float(np.sum(r**2 / (n - np.arange(1, K + 1))))
    p = float(stats.chi2.sf(Q, K))
    return Q, p, r


def fit_ar_ols(x, p):
    """条件最小二乘 AR(p)；返回 (aic, bic, rss, coef, intercept, n_eff)。"""
    x = np.asarray(x, dtype=float)
    n = len(x)
    n_eff = n - p
    Y = x[p:]
    X = np.column_stack([x[p - j : n - j] for j in range(1, p + 1)])
    Xc = np.column_stack([np.ones(n_eff), X])
    coef, *_ = np.linalg.lstsq(Xc, Y, rcond=None)
    resid = Y - Xc @ coef
    rss = float(np.dot(resid, resid))
    sigma2 = rss / n_eff
    k = p + 1
    aic = n_eff * math.log(sigma2) + 2 * k
    bic = n_eff * math.log(sigma2) + k * math.log(n_eff)
    return aic, bic, rss, coef[1:], coef[0], n_eff


def adf_stat(x, lags):
    """ADF：Δy_t = c + γ y_{t-1} + Σ ψ_i Δy_{t-i}；返回 γ 的 t 统计量。"""
    x = np.asarray(x, dtype=float)
    dy = np.diff(x)
    n = len(dy)
    rows = []
    for t in range(lags, n):
        row = [1.0, x[t]]  # constant, y_{t-1}（dy[t] 对应 x[t]→x[t+1] 的差分）
        for j in range(1, lags + 1):
            row.append(dy[t - j])
        rows.append(row)
    Y = dy[lags:]
    X = np.array(rows)
    coef, *_ = np.linalg.lstsq(X, Y, rcond=None)
    resid = Y - X @ coef
    dof = len(Y) - X.shape[1]
    sigma2 = float(np.dot(resid, resid)) / dof
    se = np.sqrt(np.diag(sigma2 * np.linalg.inv(X.T @ X)))
    tstat = float(coef[1] / se[1])
    return tstat, dof


def loo_cv_ar(x, pmax):
    """留一交叉验证：一步向前预测 MSE，比较 p=0..pmax（小样本定阶仲裁）。"""
    x = np.asarray(x, dtype=float)
    n = len(x)
    out = {}
    for p in range(0, pmax + 1):
        errs = []
        for t in range(max(p + 1, 2), n + 1):  # 测试点 = 第 t 个观测（1-indexed）
            train = x[: t - 1]
            if len(train) <= p + 1:
                continue
            if p == 0:
                pred = train.mean()
            else:
                tn = len(train)
                Y = train[p:]
                X = np.column_stack([train[p - j : tn - j] for j in range(1, p + 1)])
                Xc = np.column_stack([np.ones(len(Y)), X])
                try:
                    coef, *_ = np.linalg.lstsq(Xc, Y, rcond=None)
                    pred = coef[0] + float(np.dot(coef[1:], x[t - 1 - p : t - 1][::-1]))
                except np.linalg.LinAlgError:
                    continue
            errs.append(x[t - 1] - pred)
        errs = np.array(errs)
        out[p] = float(np.mean(errs**2))
    return out


# MacKinnon 近似临界值（含常数项，无趋势；n 较小时取更保守的表值）
ADF_CRIT = {  # (1%, 5%, 10%)
    0: (-3.75, -3.00, -2.63),  # n=15 小样本近似（大样本 -3.43/-2.86/-2.57）
    1: (-3.80, -3.09, -2.69),
}


def mc_wn_calibration(n, kmax, reps=200_000, seed=20261107):
    """白噪声零假设下 max|r_k| 的分布（小样本精确校准）。"""
    rng = np.random.default_rng(seed)
    mx = np.empty(reps)
    for i in range(reps):
        z = rng.standard_normal(n)
        r, _ = acf(z, kmax)
        mx[i] = np.max(np.abs(r))
    return mx


def bootstrap_acf_ci(x, kmax, reps=50_000, seed=20261108):
    """iid bootstrap（对 (y_t, y_{t-1}) 成对重采样）给 r_k 的 95% 区间。"""
    x = np.asarray(x, dtype=float)
    n = len(x)
    rng = np.random.default_rng(seed)
    idx = rng.integers(1, n, size=(reps, n - 1))  # 允许 (y_t, y_{t-1}) 对断裂，稳健近似
    out = np.empty((reps, kmax))
    for b in range(reps):
        sel = idx[b]
        xs = np.concatenate([[x[sel[0] - 1]], x[sel]])
        r, _ = acf(xs, kmax)
        out[b] = r
    lo = np.percentile(out, 2.5, axis=0)
    hi = np.percentile(out, 97.5, axis=0)
    return lo, hi


def welch(a, b):
    t, p = stats.ttest_ind(a, b, equal_var=False)
    return float(t), float(p)


# ---------------------------------------------------------------- main
def main():
    ts, y, notes, rows = build_series()
    n = len(y)
    print(f"n = {n} 官方出分（升序）")
    for i, (t, v) in enumerate(zip(ts, y)):
        print(f"  #{i+1:02d} {t}  {v:9.4f}  {notes[i]}")

    # 结构断点：v1/v1b（前 2 发 ~245s）→ S3 起为修正配置
    y_full = y
    y_post = y[2:]  # 断点后
    t_v1, t_post = y[:2], y[2:]
    tt, tp = welch(t_v1, t_post)
    print(f"\n[结构断点] v1 期均值 {t_v1.mean():.3f}s vs 后期 {t_post.mean():.3f}s "
          f"(Welch t={tt:.3f}, p={tp:.2e}) → 配置更替造成显著水平位移")

    results = {"n_full": n, "series": y.tolist(), "timestamps": [t.isoformat() for t in ts]}

    for label, x in (("full_n15", y_full), ("post_break_n13", y_post)):
        print(f"\n{'='*72}\n口径 {label}: n={len(x)}, mean={x.mean():.3f}, std={x.std(ddof=1):.3f}")
        K = min(4, len(x) // 4)
        kmax = K
        r, c0 = acf(x, kmax)
        band = Z95 / math.sqrt(len(x))
        pac = pacf_via_levinson(x, kmax)
        print(f"K = {K}（n/4 上限）")
        print("lag |   ACF    Bartlett95带        |   PACF   ±%.3f" % band)
        bart = None
        for k in range(1, kmax + 1):
            bart_band = Z95 / math.sqrt(len(x)) * math.sqrt(
                1 + 2 * float(np.sum(r[: k - 1] ** 2))
            )
            print(f"  {k} | {r[k-1]:+.4f}  ±{bart_band:.4f}  "
                  f"{'*' if abs(r[k-1]) > bart_band else ' '}   | {pac[k-1]:+.4f} "
                  f"{'*' if abs(pac[k-1]) > band else ' '}")
        Q, pQ, _ = ljung_box(x, K)
        print(f"Ljung-Box Q({K}) = {Q:.3f}, p = {pQ:.4f} "
              f"→ {'拒绝白噪声(95%)' if pQ < 0.05 else '不拒绝白噪声(95%)'}")

        # AR(p) 定阶
        print("AR(p) 条件最小二乘定阶：")
        best = None
        order_tbl = []
        for p in range(0, min(4, (len(x) - 1) // 2) + 1):
            if p == 0:
                n_eff = len(x)
                rss = float(np.dot(x - x.mean(), x - x.mean()))
                aic = n_eff * math.log(rss / n_eff) + 2 * 1
                bic = n_eff * math.log(rss / n_eff) + 1 * math.log(n_eff)
            else:
                aic, bic, rss, *_ , n_eff = fit_ar_ols(x, p)
            order_tbl.append((p, aic, bic))
            print(f"  AR({p}): AIC={aic:8.3f}  BIC={bic:8.3f}  (n_eff={n_eff})")
            if best is None or bic < best[2]:
                best = (p, aic, bic)
        print(f"  → BIC 选阶 AR({best[0]})；AIC 选阶 "
              f"AR({min(order_tbl, key=lambda t: t[1])[0]})")
        cv = loo_cv_ar(x, 4)
        cv_best = min(cv, key=cv.get)
        for p, mse in cv.items():
            print(f"  LOO-CV AR({p}): 预测MSE={mse:9.3f}")
        print(f"  → LOO-CV 选阶 AR({cv_best})（小样本下以 CV 为准，AIC/BIC 易过拟合）")

        # ADF（随机游走零假设：γ=0）
        for L in (0, 1):
            if len(x) < L + 4:
                continue
            tstat, dof = adf_stat(x, L)
            c1, c5, c10 = ADF_CRIT[L]
            verdict = "拒绝单位根" if tstat < c5 else "不能拒绝单位根"
            print(f"ADF(lag={L}): t(γ) = {tstat:.3f}  vs 5% 临界 {c5} → {verdict} "
                  f"（MacKinnon 小样本近似）")

        # 增量白噪声检验（RW 零假设下 Δy ~ WN）
        d = np.diff(x)
        Qd, pQd, rd = ljung_box(d, min(3, len(d) // 4))
        print(f"Δy 序列: mean(Δ)={d.mean():+.3f}s/发, Ljung-Box Q = {Qd:.3f}, "
              f"p = {pQd:.4f} → 增量{'可' if pQd < 0.05 else '不可'}拒绝白噪声")

        # 白噪声 MC 校准：max|r_k|
        mx = mc_wn_calibration(len(x), kmax)
        obs_max = float(np.max(np.abs(r)))
        crit95 = float(np.percentile(mx, 95))
        print(f"MC 白噪声校准（{len(mx):,} 次）: P(max|r_k|)95% = {crit95:.4f}, "
              f"观测 max|r_k| = {obs_max:.4f} → "
              f"{'拒绝' if obs_max > crit95 else '不拒绝'}整体白噪声（95%）")

        # bootstrap ACF CI
        lo, hi = bootstrap_acf_ci(x, kmax)
        for k in range(1, kmax + 1):
            sig = "不含0*" if lo[k - 1] > 0 or hi[k - 1] < 0 else "含 0"
            print(f"  r_{k} bootstrap95% [{lo[k-1]:+.4f}, {hi[k-1]:+.4f}] {sig}")

        results[label] = {
            "n": len(x),
            "mean": float(x.mean()),
            "std": float(x.std(ddof=1)),
            "acf": r.tolist(),
            "pacf": pac.tolist(),
            "ljung_box": {"K": K, "Q": Q, "p": pQ},
            "best_bic_p": best[0],
            "loo_cv_mse": cv,
            "best_loocv_p": cv_best,
            "adf": {str(L): adf_stat(x, L)[0] for L in (0, 1) if len(x) >= L + 4},
            "diff_ljung_box": {"Q": Qd, "p": pQd},
            "mc_wn_crit95": crit95,
            "obs_max_abs_acf": obs_max,
            "bootstrap_ci": {"lo": lo.tolist(), "hi": hi.tolist()},
        }

    # 榜单背景（描述性，不参与 ACF）
    print(f"\n{'='*72}\n[榜单背景] ledger.csv 头部轨迹（描述性）：")
    path = os.path.join(ROOT, "runs", "leaderboard", "ledger.csv")
    seen = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            seen.setdefault(row["team"], []).append(
                (row["checked_at"][:16], float(row["best_seconds"]))
            )
    for team, hist in seen.items():
        hist.sort()
        print(f"  {team}: " + " → ".join(f"{v}" for _, v in hist))

    out_path = os.path.join(OUT_DIR, "0313_acf_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[输出] {out_path}")


if __name__ == "__main__":
    main()
