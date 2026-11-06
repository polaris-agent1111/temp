#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""delta_model.py — 官方 δ 建模：官方 = 本地 × (1 + δ)，δ = f(rate, cap, interval)

数据：11-06 06:40 看板给出的 8 个官方点（含 1ms 陷阱点作为**域边界**，见 §3）。

模型（OLS，至少三种形式）：
  A. δ ~ rate            —— rate 线性样条（单结点，结点由 LOOCV 选定）
  B. δ ~ rate + cap      —— 线性
  C. δ ~ ln(pps_eff)     —— 包速率 pps_eff = rate×1e6 / eff_int，
                             eff_int = ceil(interval/G)×G（G=4000，0013 定时器粒度）

报告：残差表 + 留一交叉验证（LOOCV）误差；7 点正常档拟合为主，8 点全量拟合对照。
输出：docs/analysis/delta-model.md（默认覆盖写）；--predict 单点查询。

用法：
  python tools/delta_model.py                       # 生成分析文档
  python tools/delta_model.py --predict 36,36,4000  # 单点预测（rate,cap,interval）
  python tools/delta_model.py --no-write            # 只打印不写文件

仅标准库。置信度警示：官方点只有 8 个，LOOCV 误差 ±5 s 量级，排序可信度低。
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "runs", "results.jsonl")
OUT_MD = os.path.join(ROOT, "docs", "analysis", "delta-model.md")

G = 4000.0                      # 官方定时器粒度（0013 反推值）
TRAP_RATE = 50.0                # δ > +50% 视为陷阱/边界点

# 8 个官方点：rate, cap, interval, 本地均值, 官方成绩, 本地口径备注
POINTS = [
    (9, 30, 1000, 125.47, 245.995,   "leak9 族 n=8 全量均值（含 1 个 load 样本）"),
    (24, 60, 4000, 123.13, 150.6757, "n=12（剔 load-* CPU 争抢样本）"),
    (27, 40, 4000, 123.41, 141.7273, "n=1（leakc-27-40-4000）"),
    (30, 50, 5000, 121.83, 140.4793, "11-05 提交时 n=6 均值"),
    (36, 40, 4000, 130.32, 133.086,  "pre-1106 n=5 均值（现全量 n=8=133.6，含今日污染样本）"),
    (40, 60, 4000, 126.75, 137.384,  "pre-1106 n=1（hi-40-60-4000）"),
    (42, 60, 4000, 131.00, 137.091,  "无本地样本 → 40/60↔44/60 线性插值（看板 ~131）"),
    (44, 60, 4000, 135.67, 142.7837, "pre-1106 n=1（hi-44-60-4000）"),
]


# ---------- 数值工具 ----------

def solve(A, b):
    """高斯消元解线性方程组（部分主元），奇异返回 None。"""
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(M[r][c]))
        if abs(M[piv][c]) < 1e-12:
            return None
        M[c], M[piv] = M[piv], M[c]
        for r in range(n):
            if r == c:
                continue
            f = M[r][c] / M[c][c]
            for k in range(c, n + 1):
                M[r][k] -= f * M[c][k]
    return [M[i][n] / M[i][i] for i in range(n)]


def ols_fit(X, y):
    """最小二乘：解 (XᵀX)b = Xᵀy。返回系数向量或 None。"""
    p = len(X[0])
    XtX = [[sum(X[r][i] * X[r][j] for r in range(len(X))) for j in range(p)] for i in range(p)]
    Xty = [sum(X[r][i] * y[r] for r in range(len(X))) for i in range(p)]
    return solve(XtX, Xty)


def predict(beta, x):
    return sum(b * xi for b, xi in zip(beta, x))


# ---------- 特征工程 ----------

def eff_interval(interval_us, g=G):
    return math.ceil(interval_us / g) * g


def feat_A(rate, cap, interval, knot):
    return [1.0, float(rate), max(0.0, rate - knot)]


def feat_B(rate, cap, interval):
    return [1.0, float(rate), float(cap)]


def feat_C(rate, cap, interval):
    pps_eff = rate * 1e6 / eff_interval(interval)
    return [1.0, math.log(pps_eff)]


# ---------- 模型评估 ----------

def residuals(pts, beta, feat):
    out = []
    for rate, cap, itv, local, official, _ in pts:
        d_hat = predict(beta, feat(rate, cap, itv))
        d_act = official / local - 1.0
        out.append((rate, cap, itv, d_act * 100, d_hat * 100,
                    (d_hat - d_act) * 100, local * (1 + d_hat)))
    return out


def loocv(pts, feat):
    """留一交叉验证，返回 (MAE%, RMSE%, per-point errs%)。"""
    errs = []
    n = len(pts)
    for i in range(n):
        train = [pts[j] for j in range(n) if j != i]
        X = [feat(r, c, t) for r, c, t, *_ in train]
        y = [o / l - 1.0 for _, _, _, l, o, _ in train]
        beta = ols_fit(X, y)
        if beta is None:
            return None, None, []
        rate, cap, itv, local, official, _ = pts[i]
        d_hat = predict(beta, feat(rate, cap, itv))
        d_act = official / local - 1.0
        errs.append((rate, cap, (d_hat - d_act) * 100))
    mae = sum(abs(e[2]) for e in errs) / len(errs)
    rmse = math.sqrt(sum(e[2] ** 2 for e in errs) / len(errs))
    return mae, rmse, errs


def fit_all(pts, name, feat, knots=None):
    """拟合 + 残差 + LOOCV；A 形式对结点扫描取 LOOCV 最小。"""
    results = {}
    if knots:
        best = None
        for k in knots:
            mae, rmse, _ = loocv(pts, lambda r, c, t, _k=k: feat(r, c, t, _k))
            if mae is not None and (best is None or mae < best[0]):
                best = (mae, k)
        knot = best[1] if best else knots[0]
        results["knot"] = knot
        feat_k = lambda r, c, t: feat(r, c, t, knot)
    else:
        feat_k = feat
    X = [feat_k(r, c, t) for r, c, t, *_ in pts]
    y = [o / l - 1.0 for _, _, _, l, o, _ in pts]
    beta = ols_fit(X, y)
    results["beta"] = beta
    if beta is None:
        return results
    results["resid"] = residuals(pts, beta, feat_k)
    results["mae"], results["rmse"], results["errs"] = loocv(pts, feat_k)
    results["feat"] = feat_k
    in_sse = sum(r[5] ** 2 for r in results["resid"])
    results["in_rmse"] = math.sqrt(in_sse / len(pts))
    return results


# ---------- 本地数据（区域预测用） ----------

def load_local_cells():
    """pre-1106、int=4000、6 目录同配 leak、剔 load-/hog- 争抢标签 → {(r,c): (mean,n)}。"""
    cells = {}
    if not os.path.exists(RESULTS):
        return cells
    with open(RESULTS, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("valid") is not True:
                continue
            tag = str(r.get("tag", ""))
            if tag.startswith(("load-", "hog-")):
                continue
            at = str(r.get("at", ""))
            if at >= "2026-11-06":
                continue                      # 今日本地标定污染（0700 报告：同轮极差 36 s）
            cfg = r.get("config", {})
            specs = [cfg.get(str(i)) for i in range(1, 7)]
            if any(not s or ":" not in s for s in specs) or len(set(specs)) != 1:
                continue
            mode, _, p = specs[0].partition(":")
            if mode.strip() != "leak_bucket":
                continue
            ps = {}
            ok = True
            for kv in p.split(","):
                if "=" not in kv:
                    ok = False
                    break
                k, _, v = kv.partition("=")
                try:
                    ps[k.strip()] = int(v)
                except ValueError:
                    ok = False
                    break
            if not ok or ps.get("leak_interval_us") != 4000:
                continue
            key = (ps["leak_rate"], ps["bucket_cap"])
            cells.setdefault(key, []).append(float(r["total_seconds"]))
    return {k: (sum(v) / len(v), len(v)) for k, v in cells.items()}


def idw_local(rate, cap, cells):
    """反距离加权插值本地均值（d² 权重）；返回 (值, 来源说明)。"""
    if (rate, cap) in cells:
        m, n = cells[(rate, cap)]
        return m, f"实测 n={n}"
    num = den = 0.0
    for (r, c), (m, n) in cells.items():
        d2 = (r - rate) ** 2 + (c - cap) ** 2
        w = 1.0 / (d2 + 1.0)
        num += w * m
        den += w
    return (num / den if den else float("nan")), "IDW插值"


# ---------- 文档生成 ----------

def fmt_tbl(rows, headers):
    out = ["| " + " | ".join(headers) + " |",
           "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(str(x) for x in row) + " |" for row in rows]
    return "\n".join(out)


def build_doc(models, trap_check, region_rows, primary_name, band_pct, meta):
    L = []
    A = L.append
    A("# 官方 δ 模型：δ = f(rate, cap, interval)\n")
    A(f"- 生成：`python tools/delta_model.py`（一条命令重跑，本文件覆盖写）—— {meta['stamp']}")
    A("- 数据：11-06 06:40 看板 8 个官方点（`tools/delta_model.py` 内置，"
      "官方分来自 leaderboard attempts，本地分见各点口径备注）")
    A("- 关系：**官方 = 本地 × (1 + δ)**；δ 用小数拟合，展示用百分数")
    A("- ⚠ **置信度：官方点仅 8 个（正常档 7 个），LOOCV 误差 ±{:.0f}%（≈±{:.0f} s）量级，"
      "模型只能排优先级、不能做秒级结论**\n".format(meta["loocv_mae"], meta["loocv_mae_s"]))
    A("<!-- AUTOGEN: delta_model.py 覆盖写整文件 -->\n")

    # §1 数据
    A("## 1. 数据（8 个官方点）\n")
    rows = []
    for rate, cap, itv, local, official, note in POINTS:
        d = (official / local - 1) * 100
        rows.append([f"{rate}/{cap}/{itv}", f"{local:.2f}", f"{official:.3f}",
                     f"{d:+.1f}%", note])
    A(fmt_tbl(rows, ["配置 rate/cap/int", "本地 (s)", "官方 (s)", "δ", "本地口径"]))
    A("")
    A("> 42/60/4000 无本地样本，本地分为插值（看板「~131」）→ 其 δ 本身带 ±3% 级不确定度。"
      "30/50/5000 本地分取 11-05 提交时口径 121.83；若改用当前 noload 均值 124.07，"
      "δ 由 +15.3% 变 +13.1%（敏感性见 §5）。\n")

    # §2 三形式拟合
    A("## 2. 三种形式的拟合与 LOOCV\n")
    A("拟合集 = 7 个正常档点（δ≤+10% 带 + 42 插值点；陷阱点 9/30/1000 见 §3 边界检验）。\n")
    rows = []
    for name, m in models.items():
        if m.get("beta") is None:
            continue
        knot = f", 结点={m['knot']}" if "knot" in m else ""
        rows.append([name + knot,
                     ", ".join(f"{b:+.4f}" for b in m["beta"]),
                     f"{m['in_rmse']:.1f}%",
                     f"{m['mae']:.1f}%",
                     f"{m['rmse']:.1f}%"])
    A(fmt_tbl(rows, ["形式", "系数 β（截距起）", "样本内 RMSE", "LOOCV MAE", "LOOCV RMSE"]))
    A("")
    A("形式定义：")
    A("- **A** `δ = β0 + β1·rate + β2·max(0, rate−knot)`（rate 线性样条，结点在 {27,30,33,36} 中按 LOOCV 选）")
    A("- **B** `δ = β0 + β1·rate + β2·cap`")
    A("- **C** `δ = β0 + β1·ln(pps_eff)`，`pps_eff = rate×1e6/ceil(interval/4000)×4000`（G 咬合后的有效包速率）")
    A("")

    # 残差表
    A("### 逐点残差（拟合值 − 实测，百分点）\n")
    names = [n for n, m in models.items() if m.get("beta") is not None]
    rows = []
    for i, (rate, cap, itv, local, official, _) in enumerate(POINTS):
        if (rate, cap, itv) == (9, 30, 1000):
            continue
        act = (official / local - 1) * 100
        row = [f"{rate}/{cap}/{itv}", f"{act:+.1f}%"]
        for n in names:
            row.append(_resid_of(models[n], rate, cap, itv))
        rows.append(row)
    A(fmt_tbl(rows, ["配置", "实测 δ"] + [f"{n} 残差" for n in names]))
    A("")

    # LOOCV 逐点
    A("### LOOCV 逐点误差（预测 left-out 点，百分点）\n")
    rows = []
    for n in names:
        m = models[n]
        for (r, c, e) in m.get("errs", []):
            rows.append([n, f"{r}/{c}", f"{e:+.1f}"])
    A(fmt_tbl(rows, ["形式", "rate/cap", "误差 (pp)"]))
    A("")

    # §3 陷阱边界
    A("## 3. 陷阱点边界检验（9/30/1000，实测 δ=+96.1%）\n")
    A("用 7 点正常档模型**外推**陷阱点，检验模型是否知道「自己不知道」：\n")
    rows = []
    for n in names:
        m = models[n]
        if m.get("beta") is None:
            continue
        d_hat = predict(m["beta"], m["feat"](9, 30, 1000)) * 100
        rows.append([n, f"{d_hat:+.0f}%", "96.1%",
                     "严重低估 → 模型域外" if d_hat < 50 else "捕捉到"])
    A(fmt_tbl(rows, ["形式", "预测 δ", "实测 δ", "判定"]))
    A("")
    A("**结论**：正常档模型一律无法覆盖 1ms 陷阱（A/B 用 rate/cap 外推，C 用 pps_eff——"
      "陷阱点 pps_eff=2250 虽在 C 的定义域内，但 7 点拟合的斜率也拉不动 +96%）。"
      "与 0013 一致：**陷阱是 G 咬合的机制区，不是 δ 曲面的连续延伸** → "
      "所有预测仅在 `interval≥4000`（或带旁路模块）域内有效；`interval<4000` 一律禁止投递。\n")

    # §4 区域预测
    A("## 4. 区域预测：rate 34–40 × cap ≥rate–60 × interval 4000\n")
    A(f"- 主模型：**{primary_name}**（LOOCV MAE 最小）；预测 = 本地 × (1 + δ̂)")
    A("- 本地：pre-1106 实测均值（剔 load-/hog-/今日污染样本）；无实测格用 IDW 插值（实测格 {} 个）"
      .format(meta["n_cells"]))
    A(f"- 置信带：LOOCV MAE ±{meta['loocv_mae']:.1f} pp ≈ ±{meta['loocv_mae_s']:.1f} s"
      f"（按本地 {meta['local_ref']:.0f} s 折算）+ 本地插值误差\n")
    rows = []
    for rank, row in enumerate(region_rows, 1):
        (rate, cap, local, src, dA, dB, dC, pred, below, spread) = row
        rows.append([rank, f"{rate}/{cap}/4000", f"{local:.1f}", src,
                     f"{dA:+.1f}%", f"{dB:+.1f}%", f"{dC:+.1f}%",
                     f"**{pred:.1f}**" if below else f"{pred:.1f}",
                     "✅" if below else "", f"±{spread:.1f}"])
    A(fmt_tbl(rows, ["#", "配置", "本地", "本地来源", "δ̂A", "δ̂B", "δ̂C",
                     "预测官方", "<133.086?", "模型间差"]))
    A("")
    n_below = sum(1 for r in region_rows if r[7])
    A(f"Top-10 中预测低于现纪录 133.086 的格数：**{n_below}/10**。"
      "注意模型在样本内对已知点 36/40/4000（实测官方 133.086）就偏 +2.9 s，"
      "说明 **8 个官方点分辨不出 <3 s 的差异**（LOOCV 误差带 ±3.8 s 盖过 133 附近的全部候选）"
      "——本表用途是**排投递优先级**，不是判生死；「全部 ✅」只意味着区域值得打，"
      "不意味着哪个格必破纪录。\n")

    # §5 局限
    A("## 5. 敏感性与局限\n")
    for line in meta["notes"]:
        A(f"- {line}")
    A("")
    A("## 6. CLI\n")
    A("```")
    A("python tools/delta_model.py                        # 覆盖写本文件")
    A("python tools/delta_model.py --predict 36,36,4000   # 单点：本地/三模型 δ̂/预测官方")
    A("python tools/delta_model.py --no-write             # 只打印")
    A("```")
    return "\n".join(L) + "\n"


def _resid_of(m, rate, cap, itv):
    for r in m.get("resid", []):
        if r[0] == rate and r[1] == cap and r[2] == itv:
            return f"{r[5]:+.1f} pp"
    return "—"


# ---------- 主流程 ----------

def run_models(pts_normal):
    models = {}
    models["A(rate样条)"] = fit_all(pts_normal, "A", feat_A, knots=[27, 30, 33, 36])
    models["B(rate+cap)"] = fit_all(pts_normal, "B", feat_B)
    models["C(ln pps_eff)"] = fit_all(pts_normal, "C", feat_C)
    return models


def main():
    ap = argparse.ArgumentParser(description="官方 δ 建模")
    ap.add_argument("--predict", metavar="RATE,CAP,INT",
                    help="单点预测，如 36,36,4000")
    ap.add_argument("--no-write", action="store_true", help="不写文档")
    ap.add_argument("--out", default=OUT_MD)
    args = ap.parse_args()

    pts_all = POINTS
    pts_normal = [p for p in POINTS if (p[4] / p[3] - 1) * 100 <= TRAP_RATE
                  and p[0] != 9]          # 正常档 7 点（9/30/1000 为边界点）
    models = run_models(pts_normal)
    models_all = run_models(pts_all)      # 8 点全量对照（陷阱点强杠杆）

    if args.predict:
        parts = [int(x) for x in args.predict.split(",")]
        if len(parts) != 3:
            print("--predict 需要 rate,cap,interval 三个整数", file=sys.stderr)
            return 2
        rate, cap, itv = parts
        cells = load_local_cells()
        local, src = idw_local(rate, cap, cells)
        print(f"配置 leak {rate}/{cap}/{itv}")
        print(f"本地预测: {local:.2f} s（{src}）")
        for name, m in models.items():
            if m.get("beta") is None:
                continue
            d = predict(m["beta"], m["feat"](rate, cap, itv)) * 100
            print(f"  {name}: δ̂={d:+.1f}%  → 官方预测 {local * (1 + d / 100):.1f} s")
        prim = min((n for n, m in models.items() if m.get("beta") is not None),
                   key=lambda n: models[n]["mae"])
        m = models[prim]
        d = predict(m["beta"], m["feat"](rate, cap, itv)) * 100
        print(f"主模型 {prim}: 官方预测 {local * (1 + d / 100):.1f} s "
              f"（LOOCV MAE ±{m['mae']:.1f} pp ≈ ±{local * m['mae'] / 100:.1f} s）")
        if itv < 4000:
            print("⚠ interval<4000 = 1ms 陷阱域，模型不适用，禁止投递")
        return 0

    # 区域 Top-10
    cells = load_local_cells()
    primary = min((n for n, m in models.items() if m.get("beta") is not None),
                  key=lambda n: models[n]["mae"])
    region = []
    for rate in range(34, 41):
        for cap in range(max(rate, 30), 61):
            local, src = idw_local(rate, cap, cells)
            ds = {}
            for name, m in models.items():
                if m.get("beta") is None:
                    continue
                ds[name] = predict(m["beta"], m["feat"](rate, cap, 4000)) * 100
            pred = local * (1 + ds[primary] / 100)
            spread = (max(ds.values()) - min(ds.values())) * local / 100
            region.append((rate, cap, local, src,
                           ds.get("A(rate样条)", float("nan")),
                           ds.get("B(rate+cap)", float("nan")),
                           ds.get("C(ln pps_eff)", float("nan")),
                           pred, pred < 133.086, spread))
    region.sort(key=lambda r: r[7])
    top = region[:10]

    mae = models[primary]["mae"]
    meta = {
        "stamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "loocv_mae": mae,
        "loocv_mae_s": 130.0 * mae / 100.0,
        "n_cells": len(cells),
        "local_ref": 130.0,
        "notes": [
            f"主模型 {primary} 的 LOOCV MAE={mae:.1f} pp——8 点（正常档 7 点）下"
            "任何 <3 s 的预测差异都无统计意义。",
            "42/60/4000 本地为插值（±3 s 级误差直接进入 δ）；30/50/5000 本地口径取提交时 "
            "121.83，换当前 noload 124.07 则 δ 15.3%→13.1%，B 形式 cap 系数约变化 10%。",
            "区域本地分剔除了 11-06 当日样本（0700 报告：同轮极差 36 s，本地标定停用）；"
            "今日实测 36/50=128.4、40/40=128.4~141.3 波动过大未采用。",
            "陷阱点 9/30/1000 不参与拟合（域边界，§3）；8 点全量拟合对照见运行输出，"
            "系数被陷阱杠杆主导、区域预测更差，不采用。",
            "模型未包含官方时段负载、窗口竞争（0024 M4）等环境项——它们可能才是 δ 主因；"
            "本模型只是 8 点上的经验曲面。",
        ],
    }

    # 敏感性：30/50/5000 本地换 124.07 重跑 B
    alt = [(r, c, t, (124.07 if (r, c, t) == (30, 50, 5000) else l), o, n)
           for r, c, t, l, o, n in pts_normal]
    mB_alt = fit_all(alt, "B", feat_B)
    if mB_alt.get("beta"):
        meta["notes"].append(
            "敏感性（30/50/5000 本地 121.83→124.07）：B 形式系数 " +
            ", ".join(f"{b:+.3f}" for b in mB_alt["beta"]) +
            "（原 " + ", ".join(f"{b:+.3f}" for b in models["B(rate+cap)"]["beta"]) + "）。")

    doc = build_doc(models, None, top, primary, mae, meta)
    if not args.no_write:
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(doc)
        print(f"[write] {args.out}")
    print(doc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
