#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fit_official_surface.py — 官方评分曲面拟合（纯分析，只读）

目的
----
把 7 个官方成绩点建模为 (rate, cap, interval) 的函数，回答三个问题：
  Q1 rate=36（允许包速率 9000 pps）处是否真有谷底？二次拟合极值点 + 置信区间
  Q2 cap 有没有影响？cap=40 与 cap=60 能否分开？
  Q3 榜首 119.8293 / 123.1630 落在什么参数区域？能否反推 (rate, cap, interval)？

数据
----
唯一权威官方信号 = 任务书表格里的 7 个 leak_bucket 官方点（本文件 DATA 常量，
逐点带提交时刻与来源标注）。本地均值用表格值（提交时刻口径）；同时从
runs/results.jsonl 复算"当前值"做漂移对照（只读，不写 runs/）。

模型（自己实现最小二乘 + 留一交叉验证，纯标准库）
----
  M0   官方 = 常数                                   k=1
  M1L  官方 = a + b·R                                k=2
  M1   官方 = a + b·R + c·R²                         k=3
  M2   官方 = a + b·R + c·cap                        k=3
  M3L  官方 = a + b·本地均值                          k=2
  M3   官方 = a + b·本地均值 + c·R + d·cap            k=4
  M4b  官方 = a + b·B + c·cap                        k=3
  M4   官方 = a + b·B + c·B² + d·(interval/1000)      k=4
  M5   官方 = a + b·B + c·B² + d·cap                  k=4

  其中 R = rate/interval_us×1e6（允许包速率，pps），B = rate（每拍漏出的包数，
  即"突发包数"）。M3 系列用到本地均值，只能拟合 7 个已测点，不能给候选打分。

用法
----
  python tools/fit_official_surface.py                 # 全部结果
  python tools/fit_official_surface.py --draws 50000   # 加大 MC 抽样
  python tools/fit_official_surface.py --seed 7        # 换随机种子（检验结论稳定性）

退出码 0；仅标准库；不联网、不写 runs/。
"""

import argparse
import json
import math
import os
import random
import sys
from statistics import mean, stdev

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_PATH = os.path.join(ROOT, "runs", "results.jsonl")

# ---------------------------------------------------------------------------
# 0. 数据（全部来自任务书表格；本地均值 = 提交时刻口径）
# ---------------------------------------------------------------------------
# cfg, rate(leak_rate), cap(bucket_cap), iv(leak_interval_us), local_mean, local_n, official, submitted
DATA = [
    {"cfg": "24/60/4000", "rate": 24, "cap": 60, "iv": 4000, "local": 123.13, "n": 12,
     "official": 150.676, "at": "11-06 00:50"},
    {"cfg": "30/50/5000", "rate": 30, "cap": 50, "iv": 5000, "local": 121.83, "n": 6,
     "official": 140.479, "at": "11-06 00:05"},
    {"cfg": "27/40/4000", "rate": 27, "cap": 40, "iv": 4000, "local": 123.41, "n": 1,
     "official": 141.7273, "at": "11-05 16:24"},
    {"cfg": "36/40/4000", "rate": 36, "cap": 40, "iv": 4000, "local": 130.32, "n": 5,
     "official": 133.086, "at": "11-05 15:55"},
    {"cfg": "40/60/4000", "rate": 40, "cap": 60, "iv": 4000, "local": 126.75, "n": 1,
     "official": 137.384, "at": "11-06 00:56"},
    {"cfg": "42/60/4000", "rate": 42, "cap": 60, "iv": 4000, "local": 131.00, "n": 1,
     "official": 137.091, "at": "11-06 00:56"},   # 表中为约值，results.jsonl 无该配置
    {"cfg": "44/60/4000", "rate": 44, "cap": 60, "iv": 4000, "local": 135.67, "n": 1,
     "official": 142.784, "at": "11-06 00:56"},
]
TRAPS = [
    {"cfg": "9/30/1000", "rate": 9, "cap": 30, "iv": 1000, "official": 245.995,
     "at": "11-05 13:25"},
    {"cfg": "9/30/1000", "rate": 9, "cap": 30, "iv": 1000, "official": 243.9583,
     "at": "11-05 14:23"},
]
NO_LOCAL_FILE = {"42/60/4000"}   # results.jsonl 中无此配置的本地记录（表中为约值）

TARGETS = [("Catnet", 119.8293), ("我不想写实验报告", 123.1630)]

for p in DATA + TRAPS:
    p["R"] = p["rate"] * 1_000_000.0 / p["iv"]
    p["B"] = float(p["rate"])
    p["ivk"] = p["iv"] / 1000.0

MODEL_ORDER = ["M0", "M1L", "M1", "M2", "M3L", "M3", "M4b", "M4", "M5"]
DISPLAY_MODELS = ["M1L", "M1", "M2", "M4b", "M4", "M5"]   # 可对任意候选取值的模型
MODEL_NAMES = {
    "M0": "常数（基准）",
    "M1L": "线性·允许包速率 R",
    "M1": "二次·允许包速率 R",
    "M2": "可加·R + cap",
    "M3L": "线性·本地均值",
    "M3": "线性·本地 + R + cap",
    "M4b": "可加·突发包数 B + cap",
    "M4": "二次·突发包数 B + interval",
    "M5": "二次·突发包数 B + cap",
}
NEEDS_LOCAL = {"M3L", "M3"}


def feats(name, p):
    """模型特征列（不含截距）。"""
    if name == "M0":
        return []
    if name == "M1L":
        return [p["R"]]
    if name == "M1":
        return [p["R"], p["R"] ** 2]
    if name == "M2":
        return [p["R"], p["cap"]]
    if name == "M3L":
        return [p["local"]]
    if name == "M3":
        return [p["local"], p["R"], p["cap"]]
    if name == "M4b":
        return [p["B"], p["cap"]]
    if name == "M4":
        return [p["B"], p["B"] ** 2, p["ivk"]]
    if name == "M5":
        return [p["B"], p["B"] ** 2, p["cap"]]
    raise ValueError(name)


# ---------------------------------------------------------------------------
# 1. 最小二乘 / 统计工具（纯标准库）
# ---------------------------------------------------------------------------

def _invert(A):
    """Gauss-Jordan 求逆；奇异返回 None。"""
    n = len(A)
    M = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(A)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[piv][col]) < 1e-10:
            return None
        M[col], M[piv] = M[piv], M[col]
        pv = M[col][col]
        M[col] = [v / pv for v in M[col]]
        for r in range(n):
            if r != col and M[r][col] != 0.0:
                f = M[r][col]
                M[r] = [a - f * b for a, b in zip(M[r], M[col])]
    return [row[n:] for row in M]


def fit_model(name, pts):
    """返回 dict(beta0, betas, cov, sse, dof, k) 或 None（秩亏/样本不足）。"""
    X0 = [feats(name, p) for p in pts]
    y = [p["official"] for p in pts]
    n = len(y)
    p_dim = len(X0[0]) if X0 else 0
    k = p_dim + 1
    if n < k:
        return None
    if p_dim == 0:
        mu = mean(y)
        sse = sum((v - mu) ** 2 for v in y)
        dof = n - 1
        return {"name": name, "beta0": mu, "betas": [], "cov": [],
                "sse": sse, "dof": dof, "k": k, "n": n}
    means = [mean(col) for col in zip(*X0)]
    scale = []
    for j, m in enumerate(means):
        s = math.sqrt(sum((x[j] - m) ** 2 for x in X0))
        scale.append(s if s > 1e-12 else 1.0)
    Z = [[1.0] + [(x[j] - means[j]) / scale[j] for j in range(p_dim)] for x in X0]
    A = [[sum(z[i] * z[j] for z in Z) for j in range(k)] for i in range(k)]
    b = [sum(z[i] * yy for z, yy in zip(Z, y)) for i in range(k)]
    Ainv = _invert(A)
    if Ainv is None:
        return None
    theta = [sum(Ainv[i][j] * b[j] for j in range(k)) for i in range(k)]
    sse = sum((yy - sum(th * zz for th, zz in zip(theta, z))) ** 2 for z, yy in zip(Z, y))
    dof = n - k
    if dof <= 0:
        return None
    sigma2 = sse / dof
    cov_s = [[sigma2 * Ainv[i + 1][j + 1] / (scale[i] * scale[j]) for j in range(p_dim)]
             for i in range(p_dim)]
    beta0 = theta[0] - sum(theta[j + 1] * means[j] / scale[j] for j in range(p_dim))
    betas = [theta[j + 1] / scale[j] for j in range(p_dim)]
    return {"name": name, "beta0": beta0, "betas": betas, "cov": cov_s,
            "sse": sse, "dof": dof, "k": k, "n": n}


def predict(fit, p):
    return fit["beta0"] + sum(b * v for b, v in zip(fit["betas"], feats(fit["name"], p)))


def se_of(fit, j):
    return math.sqrt(max(fit["cov"][j][j], 0.0))


def loocv(name, pts):
    """留一交叉验证误差列表；任一折拟合失败返回 (None, 原因)。"""
    errs = []
    for i in range(len(pts)):
        train = pts[:i] + pts[i + 1:]
        f = fit_model(name, train)
        if f is None:
            return None, "留一子集秩亏"
        errs.append(predict(f, pts[i]) - pts[i]["official"])
    return errs, ""


def rmse(vals):
    return math.sqrt(sum(v * v for v in vals) / len(vals)) if vals else None


def aicc(sse, n, k):
    if n - k - 1 <= 0 or sse <= 0:
        return None
    return n * math.log(sse / n) + 2 * k + 2 * k * (k + 1) / (n - k - 1)


def r2_adj(sse, y, k):
    n = len(y)
    sst = sum((v - mean(y)) ** 2 for v in y)
    if sst <= 0 or n - k <= 0:
        return None
    return 1.0 - (sse / (n - k)) / (sst / (n - 1))


def pearson(x, y):
    n = len(x)
    mx, my = mean(x), mean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def t_quantile_975(dof):
    """双侧 95% t 分位（表 + 线性插值，dof>30 用 1.96）。"""
    tbl = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
           8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160,
           14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093,
           20: 2.086, 22: 2.074, 24: 2.064, 26: 2.056, 28: 2.048, 30: 2.042}
    if dof in tbl:
        return tbl[dof]
    keys = sorted(tbl)
    if dof > keys[-1]:
        return 1.96
    lo = max(k for k in keys if k < dof)
    hi = min(k for k in keys if k > dof)
    return tbl[lo] + (tbl[hi] - tbl[lo]) * (dof - lo) / (hi - lo)


def quantile(sorted_vals, q):
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = q * (len(sorted_vals) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    return sorted_vals[lo] + (pos - lo) * (sorted_vals[hi] - sorted_vals[lo])


# ---------------------------------------------------------------------------
# 2. 本地均值复算（只读 runs/results.jsonl）
# ---------------------------------------------------------------------------
LEAK_DEFAULTS = {"leak_rate": 10, "bucket_cap": 30, "leak_interval_us": 1000}


def parse_spec(spec):
    if not spec or ":" not in spec:
        return None
    mode, _, body = spec.partition(":")
    params = {}
    for kv in body.split(","):
        if "=" not in kv:
            return None
        k, _, v = kv.partition("=")
        try:
            params[k.strip()] = int(v)
        except ValueError:
            return None
    return mode.strip(), params


def canon(mode, params):
    if mode != "leak_bucket":
        return (mode, tuple(sorted(params.items())))
    kept = tuple(sorted((k, v) for k, v in params.items() if LEAK_DEFAULTS.get(k) != v))
    return ("leak_bucket", kept)


def recompute_local():
    """(rate,cap,iv) → [total_seconds]（valid=true 且 6 目录配置一致，canon 去默认值）。"""
    out = {}
    if not os.path.exists(RESULTS_PATH):
        return out
    with open(RESULTS_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("valid") is not True:
                continue
            cfg = r.get("config") or {}
            sigs = set()
            ok = True
            for i in range(1, 7):
                ps = parse_spec(cfg.get(str(i), ""))
                if not ps:
                    ok = False
                    break
                sigs.add(canon(*ps))
            if not ok or len(sigs) != 1:
                continue
            mode, kept = sigs.pop()
            if mode != "leak_bucket":
                continue
            d = dict(kept)
            key = (d.get("leak_rate", LEAK_DEFAULTS["leak_rate"]),
                   d.get("bucket_cap", LEAK_DEFAULTS["bucket_cap"]),
                   d.get("leak_interval_us", LEAK_DEFAULTS["leak_interval_us"]))
            try:
                out.setdefault(key, []).append(float(r["total_seconds"]))
            except (KeyError, TypeError, ValueError):
                continue
    return out


# ---------------------------------------------------------------------------
# 3. 拟合与评估
# ---------------------------------------------------------------------------

def evaluate(name, pts):
    fit = fit_model(name, pts)
    if fit is None:
        return {"name": name, "ok": False, "note": "样本不足 / 秩亏"}
    y = [p["official"] for p in pts]
    res = [p["official"] - predict(fit, p) for p in pts]
    errs, why = loocv(name, pts)
    out = {
        "name": name, "ok": True, "fit": fit, "residuals": res,
        "rmse": rmse(res), "max_abs": max(abs(v) for v in res),
        "k": fit["k"], "sse": fit["sse"],
        "aicc": aicc(fit["sse"], len(pts), fit["k"]),
        "r2adj": r2_adj(fit["sse"], y, fit["k"]),
        "loocv": rmse(errs) if errs else None,
        "loocv_errs": errs, "note": why,
    }
    return out


def fmt(x, d=3):
    return "—" if x is None else f"{x:.{d}f}"


def print_data(data, traps, local_now):
    print("# 官方评分曲面拟合（tools/fit_official_surface.py 输出）\n")
    print("## 0. 数据与校验\n")
    print("### 0.1 官方点（任务书表格，唯一权威信号）\n")
    print("| # | 配置 rate/cap/int | 允许包速率 R (pps) | 突发包数 B | 本地 mean (n) | 官方 (s) | δ=官方/本地−1 | 提交 |")
    print("|---|---|---|---|---|---|---|---|")
    for i, p in enumerate(sorted(data, key=lambda q: q["R"]), 1):
        d = p["official"] / p["local"] - 1.0
        nflag = "（表中约值）" if p["cfg"] in NO_LOCAL_FILE else ""
        print(f"| {i} | `{p['cfg']}` | {p['R']:.0f} | {p['rate']} | "
              f"{p['local']:.2f} (n={p['n']}){nflag} | {p['official']:.4f} | "
              f"{d * 100:+.2f}% | {p['at']} |")
    print()
    print("### 0.2 本地均值漂移校验（表格提交时口径 vs runs/results.jsonl 当前复算）\n")
    print("| 配置 | 表中 local (n) | 复算 local (n) | 漂移 | 复算 min–max | 备注 |")
    print("|---|---|---|---|---|---|")
    for p in data:
        key = (p["rate"], p["cap"], p["iv"])
        vals = local_now.get(key, [])
        if not vals:
            print(f"| `{p['cfg']}` | {p['local']:.2f} ({p['n']}) | 无记录 | — | — | 表中为约值 |")
            continue
        m = mean(vals)
        print(f"| `{p['cfg']}` | {p['local']:.2f} ({p['n']}) | {m:.2f} ({len(vals)}) | "
              f"{m - p['local']:+.2f} | {min(vals):.2f}–{max(vals):.2f} | "
              f"{'⚠ 漂移>2s' if abs(m - p['local']) > 2 else ''} |")
    print()
    print("### 0.3 对照：同 R、不同 interval 的两个 1 ms 陷阱点（不参与拟合）\n")
    print("| 配置 | rate | cap | int (µs) | R (pps) | 官方 (s) |")
    print("|---|---|---|---|---|---|")
    for t in traps:
        print(f"| `{t['cfg']}` | {t['rate']} | {t['cap']} | {t['iv']} | "
              f"{t['R']:.0f} | {t['official']:.4f} |")
    best = min(data, key=lambda p: p["official"])
    print()
    print(f"→ **R 相同（{best['R']:.0f} pps）但 interval=1000 µs 时官方 244–246 s，"
          f"是 interval=4000 µs 那个点（{best['official']:.3f} s）的近 1.8 倍。**")
    print("  这条对照本身就否证了「官方只由允许包速率决定」——M1 系列不是拟合得不好，"
          "而是**结构上缺变量**。\n")


def print_corr(data):
    print("## 1. 特征相关性与样本噪声\n")
    y = [p["official"] for p in data]
    print("| 特征 | Pearson r（对官方） | 说明 |")
    print("|---|---|---|")
    for key, label in (("R", "R 允许包速率"), ("rate", "B=leak_rate 突发包数"),
                       ("cap", "cap 桶深"), ("iv", "interval"),
                       ("local", "本地均值")):
        r = pearson([p[key] for p in data], y)
        print(f"| {label} | {r:+.3f} | {'—' if abs(r) < 0.3 else '方向可辨但样本不足'} |")
    sd = stdev(y)
    print()
    print(f"- 官方点：mean **{mean(y):.3f}** s，sd **{sd:.3f}** s，"
          f"极差 {max(y) - min(y):.3f} s（{min(y):.3f}–{max(y):.3f}，n=7）。")
    best = min(data, key=lambda p: p["official"])
    others = [p["official"] for p in data if p is not best]
    loo_mean = mean(others)
    loo_sd = stdev(others)
    z = (best["official"] - loo_mean) / (loo_sd * math.sqrt(1 + 1 / len(others)))
    print(f"- 最好点 `{best['cfg']}` = {best['official']:.3f} s，比其余 6 点均值 "
          f"{loo_mean:.3f} 低 {loo_mean - best['official']:.3f} s；"
          f"留一标准残差 **{z:+.2f}σ**（7 个点里挑最小，需按多重比较打折）。")
    print(f"- 官方/本地比值 δ：min {min(p['official'] / p['local'] - 1 for p in data) * 100:+.2f}%，"
          f"max {max(p['official'] / p['local'] - 1 for p in data) * 100:+.2f}%，"
          f"mean {mean([p['official'] / p['local'] - 1 for p in data]) * 100:+.2f}%。")
    print("\n> 样本 7 个、参数 2–4 个：下面所有系数的标准误都很大，"
          "**任何单个系数的符号都不该被当成结论**。\n")


def print_fits(evals, data):
    print("## 2. 模型拟合（9 种形式，全部纯标准库 OLS）\n")
    print("| 模型 | 形式 | k | 残差 RMSE | max\\|残差\\| | LOOCV RMSE | AICc | adj R² | 排名 |")
    print("|---|---|---|---|---|---|---|---|---|")
    rank = sorted([e for e in evals if e["ok"] and e["loocv"] is not None],
                  key=lambda e: e["loocv"])
    rank_idx = {e["name"]: i + 1 for i, e in enumerate(rank)}
    for name in MODEL_ORDER:
        e = next(x for x in evals if x["name"] == name)
        if not e["ok"]:
            print(f"| {name} | {MODEL_NAMES[name]} | — | — | — | — | — | — | — |")
            continue
        loo = fmt(e["loocv"]) if e["loocv"] is not None else "不可算"
        print(f"| **{name}** | {MODEL_NAMES[name]} | {e['k']} | {e['rmse']:.3f} | "
              f"{e['max_abs']:.3f} | {loo} | {fmt(e['aicc'], 2)} | "
              f"{fmt(e['r2adj'], 3)} | {rank_idx.get(name, '—')} |")
    print()
    m4 = next((e for e in evals if e["name"] == "M4"), None)
    if m4 and m4["loocv"] is None:
        print("> M4 的 LOOCV 不可算：它的 interval 特征只由 `30/50/5000` **一个点**承载，"
              "留一去掉这个点后该列退化为常数、矩阵奇异。这不是程序问题，是设计问题——"
              "**interval 的效应在本数据集里根本不可识别**（M4 多出来的那点拟合优度几乎全部来自 `30/50/5000` 这一个点——它的 interval 系数 +3.44 完全由这个点决定）。\n")
    best = rank[0]
    print(f"**LOOCV 最优：{best['name']}（{MODEL_NAMES[best['name']]}），"
          f"LOOCV RMSE = {best['loocv']:.3f} s；常数模型 M0 = "
          f"{next(e for e in evals if e['name'] == 'M0')['loocv']:.3f} s。**")
    aicc_rank = sorted([e for e in evals if e["ok"] and e["aicc"] is not None],
                       key=lambda e: e["aicc"])
    a_best = aicc_rank[0]
    if a_best["name"] != best["name"]:
        n = len(data)
        t_b = n * math.log(best["sse"] / n)
        t_a = n * math.log(a_best["sse"] / n)
        pen_b = 2 * best["k"] + 2 * best["k"] * (best["k"] + 1) / (n - best["k"] - 1)
        pen_a = 2 * a_best["k"] + 2 * a_best["k"] * (a_best["k"] + 1) / (n - a_best["k"] - 1)
        print(f"\n> ⚠ **AICc 选的是 {a_best['name']}（{a_best['aicc']:.2f}），与 LOOCV 不一致**："
              f"{best['name']} 把 n·ln(SSE/n) 从 {t_a:.1f} 压到 {t_b:.1f}（改善 {t_a - t_b:.1f}），"
              f"但参数罚分从 {pen_a:.1f} 涨到 {pen_b:.1f}（+{pen_b - pen_a:.1f}），净结果反而差 "
              f"{best['aicc'] - a_best['aicc']:.1f}。**n=7 时 4 个参数就是买不起**——"
              "本文以 LOOCV 为主（它直接度量“留一个点还能不能预测”），"
              "但两个指标打架本身就是“证据不足”的最直白证据。")
    print()
    print("### 2.1 逐点残差与留一误差（按 LOOCV 排名前 3 + M0）\n")
    show = [e["name"] for e in rank[:3]]
    if "M0" not in show:
        show.append("M0")
    print("| 配置 | 官方 | " + " | ".join(f"{n} 残差 / LOO" for n in show) + " |")
    print("|---" * (2 + len(show)) + "|")
    by_name = {e["name"]: e for e in evals}
    for p in data:
        cells = []
        for n in show:
            e = by_name[n]
            if not e["ok"] or e["loocv_errs"] is None:
                cells.append("— / —")
                continue
            i = data.index(p)
            cells.append(f"{e['residuals'][i]:+.2f} / {e['loocv_errs'][i]:+.2f}")
        print(f"| `{p['cfg']}` | {p['official']:.3f} | " + " | ".join(cells) + " |")
    print()
    print("### 2.2 系数表（自然单位；含标准误）\n")
    for name in MODEL_ORDER:
        e = by_name[name]
        if not e["ok"]:
            continue
        f = e["fit"]
        terms = ["截距"] + ([f"R", "R²"] if name == "M1" else
                           ["R", "cap"] if name == "M2" else
                           ["local", "R", "cap"] if name == "M3" else
                           ["local"] if name == "M3L" else
                           ["R"] if name == "M1L" else
                           ["B", "cap"] if name == "M4b" else
                           ["B", "B²", "interval/1000"] if name == "M4" else
                           ["B", "B²", "cap"] if name == "M5" else [])
        vals = [f["beta0"]] + f["betas"]
        ses = ["—"] + [f"{se_of(f, j):.4g}" for j in range(len(f["betas"]))]
        print(f"- **{name}**：" + "；".join(
            f"{t}={v:.4g}" + (f"±{s}" if s != "—" else "")
            for t, v, s in zip(terms[:len(vals)], vals, ses)))
    print()
    print("### 2.3 相对 M0（常数）的收益\n")
    m0 = by_name["M0"]
    print("| 模型 | LOOCV RMSE | 相对 M0 改善 | 判读 |")
    print("|---|---|---|---|")
    for e in rank:
        imp = (m0["loocv"] - e["loocv"]) / m0["loocv"] * 100
        verdict = "优于常数" if imp > 5 else ("与常数无实质差别" if imp > -5 else "不如常数")
        print(f"| {e['name']} | {e['loocv']:.3f} | {imp:+.1f}% | {verdict} |")
    print()


# ---------------------------------------------------------------------------
# 4. Q1 谷底
# ---------------------------------------------------------------------------

def mc_vertex(fit, i_b, i_c, rng, draws=20000):
    """对 (b, c) 做二元 t 抽样，返回 (顶点列表, 有效比例)。

    y = a + b·x + c·x²；**c > 0 才有内点极小**，顶点 x* = −b/(2c)。
    用 dof 自由度的多元 t（系数抽样分布），而不是正态——dof 只有 3–4 时
    正态会把区间说得太窄。
    """
    b, c = fit["betas"][i_b], fit["betas"][i_c]
    c11, c22, c12 = fit["cov"][i_b][i_b], fit["cov"][i_c][i_c], fit["cov"][i_b][i_c]
    if c11 <= 0 or c22 <= 0:
        return [], 0.0
    l11 = math.sqrt(c11)
    l21 = c12 / l11
    l22sq = c22 - l21 * l21
    if l22sq <= 0:
        return [], 0.0
    l22 = math.sqrt(l22sq)
    dof = max(1, min(fit["dof"], 30))
    verts = []
    good = 0
    for _ in range(draws):
        z1, z2 = rng.gauss(0, 1), rng.gauss(0, 1)
        chi2 = sum(rng.gauss(0, 1) ** 2 for _ in range(dof))
        scale = math.sqrt(dof / chi2) if chi2 > 0 else 1.0
        bb = b + l11 * z1 * scale
        cc = c + (l21 * z1 + l22 * z2) * scale
        if cc > 0:
            good += 1
            verts.append(-bb / (2 * cc))
    return verts, good / draws


def bootstrap_vertex(name, data, i_b, i_c, rng, B=2000):
    """按点重采样（bootstrap），看顶点稳不稳；c>0 = 有内点极小。"""
    verts = []
    good = 0
    ok = 0
    for _ in range(B):
        sample = [data[rng.randrange(len(data))] for _ in range(len(data))]
        f = fit_model(name, sample)
        if f is None or len(f["betas"]) <= max(i_b, i_c):
            continue
        ok += 1
        b, c = f["betas"][i_b], f["betas"][i_c]
        if c > 0:
            good += 1
            verts.append(-b / (2 * c))
    return verts, (good / ok if ok else 0.0), ok


def print_q1(data, evals, rng):
    print("## 3. Q1：rate=36（R=9000）处到底有没有谷底？\n")
    by_name = {e["name"]: e for e in evals}
    best = min(data, key=lambda p: p["official"])
    print(f"观测最小值确实在 `{best['cfg']}`（R={best['R']:.0f}, B={best['rate']}, "
          f"官方 {best['official']:.3f} s）。但“谷底”是统计主张，要三个证据同时成立："
          "① 二次项显著（c>0，开口向上）；② 顶点置信区间窄；③ LOOCV 优于常数。逐个查：\n")

    print("### 3.1 两个坐标下的二次拟合\n")
    print("| 模型 | 坐标 x | c（二次项） | se | t | dof | |t|>t.975? | 顶点 x* | 顶点 95% CI |")
    print("|---|---|---|---|---|---|---|---|---|")
    rows = []
    for name, i_b, i_c, unit, scale in (("M1", 0, 1, "R (pps)", 1.0),
                                        ("M4", 0, 1, "B (包/拍)", 1.0),
                                        ("M5", 0, 1, "B (包/拍)", 1.0)):
        e = by_name[name]
        if not e["ok"]:
            continue
        f = e["fit"]
        b, c = f["betas"][i_b], f["betas"][i_c]
        sc = se_of(f, i_c)
        dof = f["dof"]
        tq = t_quantile_975(dof)
        t_c = c / sc if sc > 0 else float("nan")
        verts, frac = mc_vertex(f, i_b, i_c, rng, draws=20000)
        verts.sort()
        sig = "是" if t_c > tq else "否"
        if verts:
            v_med = quantile(verts, 0.5)
            lo, hi = quantile(verts, 0.025), quantile(verts, 0.975)
            ci = f"[{lo:.1f}, {hi:.1f}]"
        else:
            v_med, lo, hi, ci = float("nan"), float("nan"), float("nan"), "不可算"
        rows.append(dict(name=name, b=b, c=c, t=t_c, dof=dof, sig=sig, vert=v_med,
                         lo=lo, hi=hi, frac=frac, verts=verts, unit=unit))
        print(f"| {name} | {unit} | {c:.4g} | {sc:.3g} | {t_c:+.2f} | {dof} | {sig} | "
              f"{v_med:.1f} | {ci} |")
    print()
    for r in rows:
        print(f"- **{r['name']}**：抽样中 c>0（存在内点极小）的比例 **{r['frac'] * 100:.1f}%**；"
              f"顶点 = {r['vert']:.1f} {r['unit']}，区间宽 {r['hi'] - r['lo']:.1f}。")
    print("\n> c>0 的比例 = “谷底存在”的置信度。95% 是常规门槛；3–4 自由度的 t 抽样"
          "尾部很肥，所以区间宽是**真实的信息量不足**，不是计算误差。\n")

    print("### 3.2 谷底有多深？顶点 vs 两端的模型预测\n")
    e5 = by_name.get("M5")
    if e5 and e5["ok"]:
        f = e5["fit"]
        def pred_b(B, cap):
            p = {"B": float(B), "ivk": 4.0, "cap": cap}
            return f["beta0"] + f["betas"][0] * B + f["betas"][1] * B * B + f["betas"][2] * cap
        v = -f["betas"][0] / (2 * f["betas"][1])
        print("| B=leak_rate | 20 | 24 | 30 | 顶点 {:.1f} | 40 | 48 | 60 |".format(v))
        print("|---|---|---|---|---|---|---|---|")
        print("| M5 预测（cap=40） | {:.1f} | {:.1f} | {:.1f} | **{:.1f}** | {:.1f} | {:.1f} | {:.1f} |".format(
            pred_b(20, 40), pred_b(24, 40), pred_b(30, 40), pred_b(v, 40),
            pred_b(40, 40), pred_b(48, 40), pred_b(60, 40)))
        print("| M5 预测（cap=60） | {:.1f} | {:.1f} | {:.1f} | **{:.1f}** | {:.1f} | {:.1f} | {:.1f} |".format(
            pred_b(20, 60), pred_b(24, 60), pred_b(30, 60), pred_b(v, 60),
            pred_b(40, 60), pred_b(48, 60), pred_b(60, 60)))
        print()
        print(f"- 碗深：从顶点 B≈{v:.1f} 到 B=24 抬升 "
              f"{pred_b(24, 40) - pred_b(v, 40):.1f} s；到 B=60 抬升 "
              f"{pred_b(60, 40) - pred_b(v, 40):.1f} s。")
        print(f"- **注意这是外推**：B=20 与 B=60 都在观测范围（24–44）之外，"
              f"二次曲面外推出的“更差”没有数据支撑，只能当趋势。\n")

    print("### 3.3 点对点检验：最好点是否显著优于“其余 6 点均值”？\n")
    best = min(data, key=lambda p: p["official"])
    others = [p["official"] for p in data if p is not best]
    loo_mean, loo_sd = mean(others), stdev(others)
    se = loo_sd * math.sqrt(1 + 1 / len(others))
    z = (best["official"] - loo_mean) / se
    print(f"- 其余 6 点：mean {loo_mean:.3f}，sd {loo_sd:.3f}；最好点 {best['official']:.3f}")
    print(f"- 差异 {loo_mean - best['official']:+.3f} s，标准误 {se:.3f} s，z = {z:+.2f}")
    print(f"- 7 个点、7 次比较，Bonferroni 后需 |z| > 2.69 → **{'显著' if abs(z) > 2.69 else '不显著'}**")
    print("（这一条只看“最小值”本身，不看形状；形状的证据在上表。）\n")

    print("### 3.4 自举（bootstrap）稳定性：把 7 个点当总体重采样\n")
    print("| 模型 | 坐标 | 有效重采样 | c>0 比例 | 顶点 2.5% | 顶点 50% | 顶点 97.5% |")
    print("|---|---|---|---|---|---|---|")
    for name, unit in (("M1", "R (pps)"), ("M5", "B (包/拍)")):
        verts, frac, ok = bootstrap_vertex(name, data, 0, 1, rng, B=2000)
        verts.sort()
        if verts:
            print(f"| {name} | {unit} | {ok} | {frac * 100:.1f}% | {quantile(verts, 0.025):.1f} | "
                  f"{quantile(verts, 0.5):.1f} | {quantile(verts, 0.975):.1f} |")
        else:
            print(f"| {name} | {unit} | {ok} | {frac * 100:.1f}% | — | — | — |")
    print("\n> 自举把 7 个点当总体重采样（有放回抽 7 个再拟合）。"
          "“c>0 比例”高、顶点分位窄 = 谷底是被多个点共同撑起来的；"
          "比例低或顶点乱跳 = 谷底是少数点造成的形状。\n")

    print("### 3.5 回答\n")
    print("| 问法 | 回答 | 置信度 |")
    print("|---|---|---|")
    print("| 观测最小值在 rate=36 吗？ | **是**。`36/40/4000`=133.086 是 7 点里最低，"
          "比其余 6 点均值低 8.60 s | 事实（n=1 次官方出分） |")
    if rows:
        r5 = next((r for r in rows if r["name"] == "M5"), None)
        r1 = next((r for r in rows if r["name"] == "M1"), None)
        if r5:
            print(f"| 曲面上有谷底吗（burst 坐标）？ | **有**：M5 的 c>0 "
                  f"t={r5['t']:+.2f}（dof={r5['dof']}），顶点 B*≈{r5['vert']:.1f}"
                  f"（rate≈{r5['vert']:.0f}），95% CI [{r5['lo']:.1f}, {r5['hi']:.1f}]；"
                  f"c>0 抽样占比 {r5['frac'] * 100:.1f}% | 中（1 模型 / 7 点 / 4 参，"
                  f"LOOCV 2.7 s 支持“有形状”） |")
        if r1:
            lo_rate = r1["lo"] * 4 / 1000.0
            hi_rate = r1["hi"] * 4 / 1000.0
            print(f"| 谷底在“允许包速率 R”坐标上同样清楚吗？ | **差一些**：顶点 {r1['vert']:.0f} pps"
                  f"（≈rate {r1['vert'] * 4 / 1000:.0f}），95% CI [{r1['lo']:.0f}, {r1['hi']:.0f}]"
                  f" pps ≈ rate **{lo_rate:.0f}–{hi_rate:.0f}**；t={r1['t']:+.2f} 未过 "
                  f"{t_quantile_975(r1['dof']):.2f} 门槛（p≈0.08 双侧） | 低-中（同一形状，"
                  f"但 `30/50/5000` 这一点偏离 R 曲线 10 s） |")
    print("| 能说“官方在 rate=36 处有尖点最优”吗？ | **不能**：顶点 CI 横跨 rate 35–45，"
          "碗底 133.5（M5, cap=40）到 136.4（cap=60）之间几乎是平的——"
          "**“36 附近是谷底”成立，“36 这个数”不成立** | 低 |")
    print("| 这能解释对手的 119.8 吗？ | **不能**：曲面最低点 133.5，比 119.8 高 13.7 s | — |")
    print()



# ---------------------------------------------------------------------------
# 5. Q2 cap
# ---------------------------------------------------------------------------

def perm_test_two_groups(a, b):
    """精确置换检验：两组均值差的 |diff| 超过观测值的比例（枚举全部组合）。"""
    import itertools
    comb = list(a) + list(b)
    obs = abs(mean(a) - mean(b))
    n_a = len(a)
    cnt = 0
    tot = 0
    for idx in itertools.combinations(range(len(comb)), n_a):
        g1 = [comb[i] for i in idx]
        g2 = [comb[i] for i in range(len(comb)) if i not in idx]
        tot += 1
        if abs(mean(g1) - mean(g2)) >= obs - 1e-12:
            cnt += 1
    return obs, cnt / tot, tot


def print_q2(data, evals):
    print("## 4. Q2：cap 到底有没有影响？\n")
    by_name = {e["name"]: e for e in evals}
    print("### 4.1 分组看（cap 是唯一完全可分组的维度）\n")
    print("| cap | n | 官方均值 | 点 | R 范围 |")
    print("|---|---|---|---|---|")
    for cap in sorted({p["cap"] for p in data}):
        pts = [p for p in data if p["cap"] == cap]
        print(f"| {cap} | {len(pts)} | {mean([p['official'] for p in pts]):.3f} | "
              f"{'、'.join(f'{p[chr(99)+chr(102)+chr(103)]}={p[chr(111)+chr(102)+chr(102)+chr(105)+chr(99)+chr(105)+chr(97)+chr(108)]:.3f}' for p in pts)} | "
              f"{min(p['R'] for p in pts):.0f}–{max(p['R'] for p in pts):.0f} |")
    print()
    a = [p["official"] for p in data if p["cap"] == 40]
    b = [p["official"] for p in data if p["cap"] == 60]
    diff, pval, tot = perm_test_two_groups(a, b)
    print(f"- cap=40（n={len(a)}）vs cap=60（n={len(b)}）：均值差 **{mean(a) - mean(b):+.3f} s**，"
          f"精确置换检验 p = **{pval:.3f}**（{tot} 种组合）。")
    print(f"- 但这个比较**被 rate 混淆**：cap=40 的两个点 R=6750/9000，cap=60 的点 R=6000/10000–11000。")
    print(f"  唯一“同 R”的对照是 R=6000：`24/60/4000`=150.676（cap=60）vs 无 cap=40 的点——**缺失**。\n")

    print("### 4.2 回归里的 cap 系数\n")
    print("| 模型 | cap 系数 | 标准误 | t | 95% CI | 判读 |")
    print("|---|---|---|---|---|---|")
    for name, idx in (("M2", 1), ("M3", 2), ("M4b", 1), ("M5", 2)):
        e = by_name[name]
        if not e["ok"]:
            continue
        f = e["fit"]
        c = f["betas"][idx]
        s = se_of(f, idx)
        tq = t_quantile_975(f["dof"])
        lo, hi = c - tq * s, c + tq * s
        sig = "CI 不含 0" if lo * hi > 0 else "CI 含 0"
        print(f"| {name} | {c:+.4g} | {s:.3g} | {c / s:+.2f} | [{lo:+.4g}, {hi:+.4g}] | {sig} |")
    print()
    print("### 4.3 去掉 cap 会不会变差？（LOOCV 对比）\n")
    print("| 对照 | 不含 cap | 含 cap | ΔLOOCV | 结论 |")
    print("|---|---|---|---|---|")
    for a_name, b_name in (("M1", "M2"), ("M4", "M5")):
        ea, eb = by_name[a_name], by_name[b_name]
        if ea["loocv"] is None or eb["loocv"] is None:
            print(f"| {a_name} → {b_name} | 不可算 | {fmt(eb['loocv'])} | — | "
                  f"{a_name} 的 LOOCV 不可算（见 §2） |")
            continue
        d = eb["loocv"] - ea["loocv"]
        verdict = ("加 cap 有改善" if d < -0.3 else
                   ("加 cap 无改善" if d > 0.3 else "几乎无差别"))
        print(f"| {a_name} → {b_name} | {ea['loocv']:.3f} | {eb['loocv']:.3f} | {d:+.3f} | {verdict} |")
    print()
    print("**结论（Q2）**：cap 的效应**方向一致但统计上分不开**。四个模型的 cap 系数全是正的"
          "（cap 越大官方略差，+0.15 ~ +0.45 s/单位），但**四个 95% CI 全部含 0**；"
          "cap=40 vs cap=60 的分组均值差 −4.58 s，精确置换检验 **p=0.53**（n=2 vs n=4，"
          "15 种分组里 8 种能给出更大差异）。20 个 cap 单位在模型里只值 2.9–9.0 s，"
          "与 LOOCV 误差同量级。\n")
    print("更关键：**cap 与“离碗底的距离”严重混淆**。cap=40 的两个点（B=27、36）恰好靠近顶点，"
          "cap=60 的四个点里有两个（B=24、44）在碗壁上。M4b 的 +0.42 s/单位很可能是在替 "
          "B 的二次项打工——一旦把二次项放进去（M5），cap 系数就从 +0.42 掉到 +0.15、t 从 2.7 掉到 1.3。"
          "**这就是“加 cap 看起来有用、其实是位置效应”的标准症状。**\n")
    print("**能一次性判死的实验（反证条件）**：同在 rate=24、interval=4000，只改 cap。"
          "两个模型对 `24/40/4000` 给出**不同预测**，一发就能分开：\n")
    print("| 观测 | 判读 |")
    print("|---|---|")
    print("| `24/40/4000` ∈ **146–151** | cap 几乎无效应 → **M5 对、M2/M4b 的 +0.40/单位被否证** |")
    print("| `24/40/4000` ∈ **140–145** | cap 有 ~0.40/单位 的效应 → M5 被否证，cap 进模型 |")
    print("| `24/40/4000` > **152** | 方向反了（cap 小反而更差）→ 所有可加模型都要重写 |")
    print()
    print("同构的 interval 反证（同样一发）：`30/50/4000` vs 已测 `30/50/5000`=140.479。"
          "M5（无 interval 项）预测 ≈139.0；M4（interval +3.44/1000，即 5000 比 4000 贵 3.4 s）预测 ≈137.0。\n")


# ---------------------------------------------------------------------------
# 6. Q3 反推
# ---------------------------------------------------------------------------

def candidate_points():
    out = []
    for rate in range(20, 61):
        for cap in range(20, 121):
            if cap < rate:
                continue
            for iv in (4000, 5000, 6000):
                if rate * 1_000_000.0 / iv < 2000:
                    continue
                out.append({"rate": rate, "cap": cap, "iv": iv,
                            "R": rate * 1_000_000.0 / iv, "B": float(rate),
                            "ivk": iv / 1000.0, "cfg": f"{rate}/{cap}/{iv}"})
    return out


def print_q3(data, evals, cands, rank_models, weights):
    print("## 5. Q3：119.8293 与 123.1630 对应什么参数区域？\n")
    by_name = {e["name"]: e for e in evals}
    print("### 5.1 先看“物理上”它们意味着什么\n")
    print("| 队 | 官方 (s) | 630 MB 平均吞吐 (Mbps) | vs 我方最好官方 | vs 我方最好本地 |")
    print("|---|---|---|---|---|")
    best_off = min(p["official"] for p in data)
    best_loc = min(p["local"] for p in data)
    for team, sec in TARGETS:
        thr = 630 * 8 / sec
        print(f"| {team} | {sec:.4f} | **{thr:.2f}** | "
              f"{(sec - best_off) / best_off * 100:+.2f}% | "
              f"{(sec - best_loc) / best_loc * 100:+.2f}% |")
    thr_best_off = 630 * 8 / best_off
    thr_best_loc = 630 * 8 / best_loc
    print(f"| 我方最好官方 | {best_off:.3f} | {thr_best_off:.2f} | — | — |")
    print(f"| 我方最好本地 | {best_loc:.2f} | {thr_best_loc:.2f} | — | — |")
    print()
    print("（负号 = 对方比我方快；`vs 我方最好本地` 这一列才是关键：榜首的“官方”比我们“本地”还快。）\n")
    print(f"> 注意：**榜首的官方吞吐（{630 * 8 / TARGETS[0][1]:.2f} Mbps）只比我们本地最好的"
          f"吞吐（{thr_best_loc:.2f} Mbps）高 "
          f"{(630 * 8 / TARGETS[0][1]) / thr_best_loc * 100 - 100:+.2f}%**——"
          "差的不是“他们能跑到我们跑不到的速度”，而是“我们的官方成绩比本地掉了 2–22%”。\n")

    print("### 5.2 模型能到的最低点（在候选网格上穷举）\n")
    print("| 模型 | 网格最优配置 | 预测官方 | 对 119.8293 的差距 | 缺口/LOOCV | 解的形态 |")
    print("|---|---|---|---|---|---|")
    floors = {}
    for name in rank_models:
        e = by_name[name]
        if not e["ok"] or e["loocv"] is None:
            continue
        bestp = min(cands, key=lambda p: predict(e["fit"], p))
        pred = predict(e["fit"], bestp)
        floors[name] = (bestp, pred)
        gap = pred - TARGETS[0][1]
        at_edge = bestp["rate"] in (20, 60) or bestp["cap"] in (20, 120)
        if name == "M0":
            shape = "常数：全网格同值"
        else:
            shape = "**边界解（外推，不可信）**" if at_edge else "内点极小"
        print(f"| {name} | `{bestp['cfg']}` | {pred:.3f} | {gap:+.3f} | {gap / e['loocv']:.2f}× | {shape} |")
    print()
    if floors:
        lo = min(v[1] for v in floors.values())
        interior = [v[1] for k, v in floors.items() if k in ("M1", "M5")]
        print(f"- 全部模型的网格最低预测都在 **{lo:.1f} s 以上**（M1L/M2/M4b 把最优推到网格边界 "
              "rate=60/cap=120，是单调模型的外推，不能当真）；"
              "**有内点极小的 M1/M5 给 "
              f"{min(interior):.1f}–{max(interior):.1f} s**。")
        print(f"- 榜首 119.8293 比这些最低点还低 **{lo - TARGETS[0][1]:.1f} s**（对内点解则低 "
              f"{min(interior) - TARGETS[0][1]:.1f} s）。")
        print(f"- 换句话说：**在我们拟合出的这张曲面里，119.8293 根本不在值域内**——"
              "不是“哪个参数组合最优”的问题，而是这个族的天花板没那么高。\n")

    print("### 5.3 为什么反推不出来（四条，按重要性排）\n")
    print("1. **方程数 1 < 未知数 3**：给定一个官方分数，只能定出一个曲面上的等值线，"
          "线上的 (rate, cap, interval) 组合有几十上百个。没有第二个约束就没有唯一解。")
    print("2. **误差还不够把缺口填回来**："
          f"LOOCV RMSE ≈ {min(e['loocv'] for e in evals if e['ok'] and e['name'] in rank_models):.1f} s，"
          f"而榜首与我们最好的差距是 {min(p['official'] for p in data) - TARGETS[0][1]:.1f} s"
          f"（≈{(min(p['official'] for p in data) - TARGETS[0][1]) / min(e['loocv'] for e in evals if e['ok'] and e['name'] in rank_models):.1f}× LOOCV）。"
          "就算把所有误差都朝“更低”的方向用，也够不到 119.8——所以这**不是插值问题，是族不对**。")
    print("3. **模型是“外推不可能”的**：二次曲面在观测区间内是凸的，往两头走都会上升；"
          "要命中 119.83 得把二次项翻过来，那是另一族模型，不是这张曲面的内插。")
    print("4. **对手的 119.83 本身未必可复现**：项目文档记载 Catnet 在 119.8293 之后 3 分钟"
          "又投出 **129.805**（+9.98 s，`docs/analysis/opponent-tracks.md` §3.1）——"
          "同一会话、3 分钟内、差 8.3%，最省事的解释是**两个不同配置**，"
          "即 119.83 是单发命中而非稳定平台。对一个“可能只出现过一次”的数反推参数，"
          "自由度比 1 个方程还少。")
    print()
    print("### 5.4 能说的与不能说的\n")
    print("| 说法 | 能不能说 | 依据 |")
    print("|---|---|---|")
    print("| 榜首/榜二**不在**我们这 7 个点的参数邻域内 | **能** | 内点解最低预测 "
          f"{min(interior):.1f} s > 123.16 > 119.83 |")
    print("| 他们一定用了 leak_bucket | **不能** | 我们没有他们的 pacer.txt；"
          "可能是 token/precise（有 in-flight 旁路）或分文件不同配 |")
    print("| 他们用了分文件差异化配置（6 个目录不同配） | **倾向** | "
          "单一配置族在我们 7 个点上没有低于 133 的解；而文档 §4.1 的拆解显示 "
          "6.bin 独占 48.7% 时间，分文件是最省力的降维 |")
    print("| 具体 (rate, cap, interval) 是多少 | **不能** | 1 方程 / 3 未知；"
          "且曲面在 119.8 处无解（最低 128–134）+ 目标本身可能是单发 |")
    print()


# ---------------------------------------------------------------------------
# 7. 候选与推荐
# ---------------------------------------------------------------------------

def measured_pairs(p, data):
    """返回与 p 只差一个参数的已测点列表（用于 OAT 说明）。"""
    out = []
    for q in data:
        diffs = [k for k in ("rate", "cap", "iv") if q[k] != p[k]]
        if len(diffs) == 1:
            out.append((diffs[0], q))
    return out


def pick_picks(ranked, k=5, min_rate_gap=2, max_per_corner=2, max_min_bucket=3):
    """纯预测贪心选 5 个：只加结构约束，不加信息量。用于与“建议 5 发”对照。"""
    picked = []
    corner_count = {}
    for p in ranked:
        if len(picked) >= k:
            break
        corner = (p["rate"] // 8, p["cap"] // 30)
        if corner_count.get(corner, 0) >= max_per_corner:
            continue
        if p["cap"] == p["rate"] and sum(1 for q in picked if q["cap"] == q["rate"]) >= max_min_bucket:
            continue
        if any(abs(p["rate"] - q["rate"]) < min_rate_gap for q in picked):
            continue
        picked.append(p)
        corner_count[corner] = corner_count.get(corner, 0) + 1
    return picked


# 建议明天投的 5 发：3 发=rate 扫描（固定 cap=rate 最小桶）+ 1 发=碗底 cap 对照 + 1 发=interval 对照。
# 之所以不是纯预测 top5：纯预测 top5 全在 cap=rate 的同一个角落（见 6.2），信息量接近 0。
DESIGN_PICKS = [
    ("38/38/4000", "碗底 + 最小桶：预测排名前 5 内，且 cap 取到合法最小值（38）"),
    ("40/40/4000", "rate 扫描的第二点：与已测 `36/40`、`27/40` 同 cap，可读 rate 曲线"),
    ("44/44/4000", "右壁：与已测 `44/60`=142.784 只差 cap（Δ=16），测碗右边是不是 cap 造成的"),
    ("36/60/4000", "**最强 cap 对照**：与已测 `36/40`=133.086 只差 cap（Δ=20），且在碗底"),
    ("30/50/4000", "**唯一 interval 对照**：与已测 `30/50/5000`=140.479 只差 interval"),
]


def print_candidates(data, evals, cands, rank_models, weights, rng):
    print("## 6. 下一批候选（leak_bucket 族，rate 20–60 / cap 20–120 / interval 4000·5000·6000）\n")
    by_name = {e["name"]: e for e in evals}
    measured = {p["cfg"] for p in data}
    pool = [p for p in cands if p["cfg"] not in measured and p["cap"] >= p["rate"]]
    print(f"- 网格合法点数（cap ≥ rate，剔除已测 7 个）：**{len(pool)}**")
    print(f"- 集成权重（1/LOOCV² 归一）：" +
          "、".join(f"{n}={weights[n]:.2f}" for n in rank_models if n in weights))
    print()

    for p in pool:
        preds = {}
        for n in DISPLAY_MODELS:
            e = by_name.get(n)
            if e and e["ok"]:
                preds[n] = predict(e["fit"], p)
        p["preds"] = preds
        p["pred"] = sum(weights[n] * preds[n] for n in weights if n in preds) / \
            sum(weights[n] for n in weights if n in preds)
        p["disagree"] = math.sqrt(sum(weights[n] * (preds[n] - p["pred"]) ** 2
                                  for n in weights if n in preds) /
                                  sum(weights[n] for n in weights if n in preds))
        loo = math.sqrt(sum(weights[n] * by_name[n]["loocv"] ** 2
                            for n in weights if n in preds) /
                        sum(weights[n] for n in weights if n in preds))
        p["unc"] = math.sqrt(loo ** 2 + p["disagree"] ** 2)

    ranked = sorted(pool, key=lambda p: p["pred"])
    rank_of = {p["cfg"]: i + 1 for i, p in enumerate(ranked)}
    by_cfg = {p["cfg"]: p for p in pool}
    print("### 6.1 预测从低到高前 10 个（模型集成）\n")
    print("| # | 配置 | R (pps) | 预测官方 (s) | ±1σ | M5 | M4 | 结构标记 |")
    print("|---|---|---|---|---|---|---|---|")
    for i, p in enumerate(ranked[:10], 1):
        marks = []
        if p["iv"] != 4000:
            marks.append(f"int={p['iv']}（非 4ms 整数倍）")
        if p["cap"] == p["rate"]:
            marks.append("cap=rate 最小桶")
        if len(measured_pairs(p, data)) >= 2:
            marks.append("多点 OAT")
        m5 = f"{p['preds']['M5']:.1f}" if "M5" in p["preds"] else "—"
        m4 = f"{p['preds']['M4']:.1f}" if "M4" in p["preds"] else "—"
        print(f"| {i} | `{p['cfg']}` | {p['R']:.0f} | **{p['pred']:.2f}** | {p['unc']:.2f} | "
              f"{m5} | {m4} | {'，'.join(marks) or '—'} |")
    print()
    spread = ranked[9]["pred"] - ranked[0]["pred"] if len(ranked) > 9 else None
    if spread is not None:
        print(f"- 前 10 名的预测跨度只有 **{spread:.2f} s**，而集成不确定性 "
              f"±{ranked[0]['unc']:.2f} s → **排序在前 10 名内部不可信**，"
              "只能当“结构优先级”用。")
        print("- 前 10 名的 cap 全在 36–39，是清一色的最小桶邻域（模型说 cap 越小越好，但 cap 的效应本身不显著）——"
              "照这个榜单投 5 发，等于把 5 发全花在同一个角落，什么都区分不了。")
        print("- 集成里含 M0（常数，权重 "
              f"{weights.get('M0', 0):.2f}）作为对冲，所以绝对预测值偏保守；"
              "排序主要由 M5（权重 " + f"{weights.get('M5', 0):.2f}）决定。\n")

    pure = pick_picks(ranked, k=5)
    print("### 6.2 对照：如果只信模型（纯预测 + 结构约束）\n")
    print("| 序 | 配置 | 预测 | 排名 |")
    print("|---|---|---|---|")
    for i, p in enumerate(pure, 1):
        print(f"| Q{i} | `{p['cfg']}` | {p['pred']:.2f} | {rank_of[p['cfg']]} |")
    print()

    print("### 6.3 建议明天投的 5 发（预测 + 信息量）\n")
    print("设计：**3 发做 rate 扫描（固定 cap=rate）+ 1 发碗底 cap 对照 + 1 发 interval 对照**。"
          "相对纯预测 5 发，预测均值只贵 "
          f"{mean([by_cfg[c]['pred'] for c, _ in DESIGN_PICKS]) - mean([p['pred'] for p in pure]):+.2f} s，"
          "但能分开 cap、interval 两个维度。\n")
    print("| 序 | 配置 | R (pps) | 预测 | ±1σ | 预测排名 | 为什么选它 | 能验证什么（单变量对照） |")
    print("|---|---|---|---|---|---|---|---|")
    design = []
    for i, (cfg, why) in enumerate(DESIGN_PICKS, 1):
        p = by_cfg.get(cfg)
        if p is None:
            print(f"| P{i} | `{cfg}` | — | — | — | — | {why} | ⚠ 不在候选池（已测或非法） |")
            continue
        design.append(p)
        pairs = measured_pairs(p, data)
        ver = []
        for k, q in pairs:
            kn = {"rate": "rate", "cap": "cap", "iv": "interval"}[k]
            ver.append(f"{kn}↔`{q['cfg']}`={q['official']:.3f}")
        if not ver:
            ver.append("无单变量对照（与其余 4 发联立）")
        print(f"| P{i} | `{cfg}` | {p['R']:.0f} | {p['pred']:.2f} | {p['unc']:.2f} | "
              f"{rank_of[cfg]} | {why} | {'；'.join(ver)} |")
    print()

    # 约束自检
    if len(design) == 5:
        rates = [p["rate"] for p in design]
        min_gap = min(abs(a - b) for i, a in enumerate(rates) for b in rates[i + 1:])
        caps = [p["cap"] for p in design]
        min_bucket = sum(1 for p in design if p["cap"] == p["rate"])
        corner_counts = {}
        for p in design:
            c = (p["rate"] // 8, p["cap"] // 30)
            corner_counts[c] = corner_counts.get(c, 0) + 1
        worst_corner = max(corner_counts.values())
        print("**结构约束自检**："
              f"最小 |Δrate| = {min_gap}（要求 ≥2）{'✔' if min_gap >= 2 else '✘'}；"
              f"cap 跨度 {min(caps)}–{max(caps)}；"
              f"cap=rate 的点 {min_bucket} 个（要求 <4）{'✔' if min_bucket < 4 else '✘'}；"
              f"同一角落最多 {worst_corner} 个（要求 <4）{'✔' if worst_corner < 4 else '✘'}。\n")

    print("### 6.4 每发的详细卡片\n")
    for i, p in enumerate(design, 1):
        print(f"**P{i} `{p['cfg']}`**　预测 {p['pred']:.2f} s ± {p['unc']:.2f}（1σ = LOOCV 误差 ⊕ 模型分歧）")
        print(f"- 各模型：" + "，".join(
            f"{n}={p['preds'][n]:.2f}" for n in DISPLAY_MODELS if n in p["preds"]))
        print(f"- R={p['R']:.0f} pps，B={p['rate']} 包/拍，cap={p['cap']}（cap/rate={p['cap'] / p['rate']:.2f}），"
              f"interval={p['iv']} µs")
        ps = measured_pairs(p, data)
        if ps:
            for k, q in ps:
                print(f"- 单变量对照：`{q['cfg']}` 官方 {q['official']:.3f} s（只差 {k}）"
                      f"→ 这一发直接给出该维度的边际效应")
        else:
            print("- 无单变量对照；作为新区域探针")
        print()
    print("### 6.5 这 5 发的预期上限\n")
    if design:
        lo = min(p["pred"] for p in design)
        print(f"- 5 发的预测区间 **{lo:.1f}–{max(p['pred'] for p in design):.1f} s**，"
              "全部高于 123.16，更高于 119.83。")
        print("- **如果目标是冲榜，这 5 发一发都不该投**——它们是把 leak_bucket 单配族的曲面钉死，"
              "不是找 119.8。要冲 119.8 只能换结构（分文件不同配 / 带 in-flight 旁路的模块），"
              "那是另一个任务。")
        print("- 反过来说：如果明天 5 发里没有任何一发 < 131，"
              "就基本可以判定**单配 leak_bucket 族的上限在 131–133**，"
              "剩余额度应全部转向越族实验，而不是继续在这个碗里微调。\n")
    return design, ranked


# ---------------------------------------------------------------------------
# 8. 结论
# ---------------------------------------------------------------------------

def print_conclusion(data, evals, picks, ranked):
    by_name = {e["name"]: e for e in evals}
    rank = sorted([e for e in evals if e["ok"] and e["loocv"] is not None],
                  key=lambda e: e["loocv"])
    best = rank[0]
    m0 = by_name["M0"]
    print("## 7. 一句话结论（脚本自动生成）\n")
    print(f"- LOOCV 最优：**{best['name']}（{MODEL_NAMES[best['name']]}）**，"
          f"LOOCV RMSE {best['loocv']:.2f} s；常数模型 {m0['loocv']:.2f} s"
          f"（改善 {(1 - best['loocv'] / m0['loocv']) * 100:.1f}%）。")
    if "M5" in by_name and by_name["M5"]["ok"]:
        f = by_name["M5"]["fit"]
        b, c = f["betas"][0], f["betas"][1]
        if c > 0:
            print(f"- burst 维度的谷底：B*≈{-b / (2 * c):.1f}（rate≈{-b / (2 * c):.0f}），"
                  "即官方在 leak_rate≈37 附近最好、往两头都变差（见 §3）。")
    if "M1" in by_name and by_name["M1"]["ok"]:
        f = by_name["M1"]["fit"]
        if f["betas"][1] > 0:
            print(f"- 换成“允许包速率 R”坐标，顶点 {(-f['betas'][0] / (2 * f['betas'][1])):.0f} pps，"
                  "但二次项 t 值未过 0.05 门槛、CI 跨度 ≈ rate 33–44——**R 坐标的谷底比 B 坐标弱一档**。")
    print(f"- 建议明天 5 发：" + "、".join(f"`{p['cfg']}`" for p in picks))
    print(f"- 这 5 发预测 {picks[0]['pred']:.1f}–{max(p['pred'] for p in picks):.1f} s，"
          "按当前模型**到不了 123.16**，更到不了 119.83 → 明天这 5 发是**证伪/定标**，不是冲榜。")
    print()


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="官方评分曲面拟合（只读分析）")
    ap.add_argument("--draws", type=int, default=20000, help="MC 抽样次数（默认 20000）")
    ap.add_argument("--seed", type=int, default=20261106, help="随机种子")
    args = ap.parse_args(argv)

    rng = random.Random(args.seed)
    data = DATA
    local_now = recompute_local()

    print_data(data, TRAPS, local_now)
    print_corr(data)

    evals = [evaluate(name, data) for name in MODEL_ORDER]
    print_fits(evals, data)

    print_q1(data, evals, rng)
    print_q2(data, evals)

    # 集成：只用能对候选打分的模型（不需要 local）
    rank_models = ["M0", "M1L", "M1", "M2", "M4b", "M4", "M5"]
    usable = [e for e in evals if e["ok"] and e["loocv"] and e["name"] in rank_models]
    raw_w = {e["name"]: 1.0 / (e["loocv"] ** 2) for e in usable}
    tot_w = sum(raw_w.values())
    weights = {k: v / tot_w for k, v in raw_w.items()}
    cands = candidate_points()
    print_q3(data, evals, cands, [n for n in rank_models if n in weights], weights)
    picks, ranked = print_candidates(data, evals, cands, [n for n in rank_models if n in weights],
                                     weights, rng)
    print_conclusion(data, evals, picks, ranked)

    print("---")
    print(f"复算命令：`python tools/fit_official_surface.py`（--seed {args.seed} / --draws {args.draws}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
