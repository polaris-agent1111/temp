#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0079 — 官方榜单历史提交记录的时间序列谱密度分析（纯本地数据，零联网）.

数据源（全部为本地已存快照，不触碰远程）：
  1. runs/leaderboard_full.json   —— 11-05 16:26 官方榜单快照：7 队 42 条出分尝试
                                     （时间戳+秒数）+ submission_log 30 条（含失败记录）
  2. runs/board_watch.jsonl       —— 赛博coder（我方）榜单轮询 10 帧
  3. runs/submissions.jsonl       —— 我方 15 条提交台账（11-05~11-06）
  4. runs/leaderboard/ledger.csv  —— 3 次榜单快照（核对 n_attempts 用）

⚠ 任务标题「16 支队伍 100+ 次提交」超出本地离线数据覆盖（实际 9 个队名、
   ~72 条去重事件、跨度 11-03 20:46 → 11-06 13:40）。红线禁止联网补抓，
   本分析在完整本地覆盖上执行，并给出分辨率/功效边界。

分析方法：
  A. 事件时间轴：到达间隔分布（均值/CV/Goyal-Variya 突发度 B）、Fano 因子曲线
  B. 点过程周期图：P(f) = |Σ_k e^{-2πi f t_k}|² / N，指数分布零假设（|S|²~Exp(1)，
     95% 门限 −ln 0.05 = 2.996），Bonferroni × 频点数
  C. 昼周期：hour-of-day 直方图 + 卡方均匀性；1/day 谱线功率
  D. 同队连发节奏：同队间隔分布（5 发/日配额结构）、45/60 min 危险率（对应
     adaptive WAIT_MIN 45→60 的经验基础）
  E. 出分序列谱：各队 per-team 出分 vs 时间 —— lag-1 自相关、shuffle 检验
     （白噪声零假设）、趋势回归（学习/收敛判定）
输出：_0079_out.md
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).with_name("_0079_out.md")


def parse_ts(s: str) -> float:
    s = s.strip().replace("+08:00", "").replace("+0800", "")
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).timestamp()
        except ValueError:
            continue
    raise ValueError(s)


def load_events():
    """汇总本地全部提交事件（出分尝试 + 台账日志），按 (来源, 时间, 队伍, 秒数)."""
    events = []  # (ts, team, seconds_or_None, source, status)

    d = json.loads((ROOT / "runs" / "leaderboard_full.json").read_text(encoding="utf-8"))
    for p in d["leaderboard"]["problems"]:
        for t in p["submissions"]:
            for a in t["attempts"]:
                events.append((parse_ts(a["submitted_at"]), t["team"],
                               float(a["download_seconds"]), "board_attempts", "成功出分"))
    for e in d["submission_log"]:
        events.append((parse_ts(e["submitted_at"]), e["team"], None,
                       "board_log", e["status"]))

    for line in (ROOT / "runs" / "board_watch.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        for a in r.get("attempts", []):
            events.append((parse_ts(a["submitted_at"]), r["team"],
                           float(a["download_seconds"]), "board_watch", "成功出分"))

    for line in (ROOT / "runs" / "submissions.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        ts = parse_ts(r["at"])
        sec = None
        try:
            sec = float(r.get("score")) if r.get("score") else None
        except (TypeError, ValueError):
            pass
        events.append((ts, "赛博coder", sec, "own_ledger", r.get("status", "?")))

    # 我方官方出分台账（含 11-06 夜间五发）
    for line in (ROOT / "runs" / "official_results.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        events.append((parse_ts(r["submitted_at"]), "赛博coder",
                       float(r["official_seconds"]), "official_results", "成功出分"))
    return events


def dedupe(events):
    """同一 (队, 时间戳≤2s, 秒数) 视为同一事件；跨来源合并，保留信息最全的。"""
    events.sort(key=lambda e: e[0])
    out = []
    for e in events:
        if out and out[-1][1] == e[1] and abs(out[-1][0] - e[0]) < 2.0:
            old = out[-1]
            merged_sec = e[2] if e[2] is not None else old[2]
            out[-1] = (old[0], old[1], merged_sec, old[3] if old[2] is not None else e[3], old[4])
            continue
        out.append(e)
    return out


def point_periodogram(times: np.ndarray, fmin, fmax, n_f=4000):
    """点过程周期图 P(f)=|Σ e^{-2πift_k}|²/N；指数零假设。"""
    freqs = np.linspace(fmin, fmax, n_f)
    t0 = times.mean()
    tt = times - t0
    E = np.exp(-2j * np.pi * np.outer(freqs, tt))
    S = E.sum(axis=1)
    P = (S.real**2 + S.imag**2) / len(times)
    return freqs, P


def goyal_bursty(ivals: np.ndarray):
    m = ivals.mean(); s2 = ivals.var(ddof=0)
    cv2 = s2 / m**2
    return (cv2 - 1) / (cv2 + 1), cv2


def main():
    L = []
    P = L.append
    P("# 0079 输出（spectral0079_submissions.py 生成）\n")

    events = dedupe(load_events())
    events.sort(key=lambda e: e[0])
    times = np.array([e[0] for e in events])
    teams = sorted({e[1] for e in events})
    t0, t1 = times[0], times[-1]
    span_h = (t1 - t0) / 3600
    scored = [e for e in events if e[2] is not None]
    P("## 0. 数据覆盖（本地离线全集）")
    P(f"- 去重后事件数 N = {len(events)}（其中出分 {len(scored)} 条）；队名数 = {len(teams)}")
    P(f"- 时间跨度：{datetime.fromtimestamp(t0):%m-%d %H:%M} → {datetime.fromtimestamp(t1):%m-%d %H:%M}（{span_h:.1f} h）")
    P(f"- 队名：{'、'.join(teams)}")
    per_team = defaultdict(list)
    for e in events:
        per_team[e[1]].append(e)
    P("| 队伍 | 事件数 | 出分数 | 首次 | 末次 |")
    P("|---|---|---|---|---|")
    for t in teams:
        ev = per_team[t]
        sc = sum(1 for e in ev if e[2] is not None)
        P(f"| {t} | {len(ev)} | {sc} | {datetime.fromtimestamp(ev[0][0]):%m-%d %H:%M} | {datetime.fromtimestamp(ev[-1][0]):%m-%d %H:%M} |")
    P(f"- ⚠ 任务标题的「16 队 100+ 次」超出本地覆盖：本分析以 {len(teams)} 队 / {len(events)} 事件执行，"
      f"最低可分辨周期 ≈ 2×中位间隔，最高可信周期 ≈ {span_h/2:.1f} h。\n")

    # A. 到达间隔
    ivals = np.diff(times) / 60.0
    B, cv2 = goyal_bursty(ivals)
    P("## A. 聚合到达间隔（点过程强度结构）")
    P(f"- 均值间隔 = {ivals.mean():.1f} min；中位 = {np.median(ivals):.1f} min；CV² = {cv2:.2f}；"
      f"Goyal-Variya 突发度 B = {B:.3f}（0=泊松，1=极端突发）")
    fanos = []
    for w_min in (5, 10, 30, 60, 120, 240):
        w = w_min * 60
        nb = int((t1 - t0) / w)
        counts = np.histogram(times, bins=nb, range=(t0, t0 + nb * w))[0]
        fanos.append((w_min, float(counts.var(ddof=1) / counts.mean())))
    P("- Fano 因子（方差/均值，泊松=1）：")
    P("| 窗口 (min) | " + " | ".join(str(w) for w, _ in fanos) + " |")
    P("|---|" + "---|" * len(fanos))
    P("| F | " + " | ".join(f"{f:.2f}" for _, f in fanos) + " |")
    P("")

    # B. 点过程周期图
    span_s = t1 - t0
    fmin = 2 / span_s               # 排除超窗趋势段（周期 > 跨度/2 不可分辨）
    fmax = 1 / (10 * 60)            # 10 min 上限（低于中位间隔无意义）
    freqs, Pw = point_periodogram(times, fmin, fmax)
    n_f = len(freqs)
    thr95 = -np.log(0.05)
    thr_bonf = -np.log(0.05 / n_f)
    top = np.argsort(Pw)[::-1][:12]
    P("## B. 点过程周期图（P(f)=|Σe^{-2πift_k}|²/N；Exp(1) 零假设）")
    P(f"- 频点数 {n_f}，95% 单点门限 = {thr95:.3f}，Bonferroni(α=0.05) 门限 = {thr_bonf:.3f}")
    P("| 排名 | 周期 (h) | 频率 (1/h) | 功率 | 超 Bonferroni 门限 | 段属性 |")
    P("|---|---|---|---|---|---|")
    for r, i in enumerate(top, 1):
        f = freqs[i]
        per_h = 1.0 / f / 3600.0
        if abs(per_h - 24) <= 2.0:
            seg = "≈1/day 昼线"
        elif abs(per_h - 12) <= 1.5:
            seg = "≈12h 谐波"
        elif abs(per_h - 8) <= 1.0:
            seg = "≈8h 谐波"
        else:
            seg = "低频簇段（突发结构，非周期）"
        P(f"| {r} | {per_h:.2f} | {f*3600:.4f} | {Pw[i]:.3f} | "
          f"{'✓' if Pw[i] > thr_bonf else '✗'} | {seg} |")
    # 1/day 谱线专项
    f_day = 1 / 86400
    i0 = int(np.argmin(np.abs(freqs - f_day)))
    # 带限检验：3h–48h 周期带内最大值（剔除低频趋势主导）
    band = (freqs >= 1 / (48 * 3600)) & (freqs <= 1 / (3 * 3600))
    band_max = float(Pw[band].max())
    P(f"- 1/day 谱线（f={f_day*3600:.5f}/h）功率 = {Pw[i0]:.3f}，"
      f"vs 单点门限 {thr95:.3f} → {'显著' if Pw[i0] > thr95 else '不显著'}")
    P(f"- 带限（周期 3–48h）最大功率 = {band_max:.3f}（{1/freqs[int(np.argmax(np.where(band, Pw, -1)))]/3600:.1f} h）→ "
      f"{'超' if band_max > thr_bonf else '未超'} Bonferroni 门限："
      f"{'中等周期段存在显著结构（会话型节律），具体峰位 ≈12h 即每日两次活动会话的成像' if band_max > thr_bonf else '中等周期上无显著谱线'}")
    P("")

    # C. 昼周期（按本地北京时间 = 榜单时间戳时区）
    hours = np.array([datetime.fromtimestamp(t).hour for t in times])
    hist, _ = np.histogram(hours, bins=24, range=(0, 24))
    chi2 = float(((hist - len(times) / 24) ** 2 / (len(times) / 24)).sum())
    P("## C. 昼周期（hour-of-day）")
    P(f"- 24 桶计数：{list(hist)}")
    P(f"- 卡方（均匀性, df=23）= {chi2:.1f}；α=0.05 临界值 35.17 → {'拒绝均匀（存在昼节律）' if chi2 > 35.17 else '不能拒绝均匀'}")
    night = hist[:6].sum() + hist[22:].sum()  # 22:00-06:00
    P(f"- 深夜桶（22-06 时）占比 = {night/len(times)*100:.1f}%\n")

    # D. 同队连发节奏
    P("## D. 同队连发间隔与 5 发/日配额结构")
    P("| 队伍 | 同队间隔中位 (min) | ≤10min 占比 | ≥45min 占比 | ≥60min 占比 | 单日最大连发 |")
    P("|---|---|---|---|---|---|")
    wait45 = wait60 = n_tot = 0
    for t in teams:
        ev = per_team[t]
        if len(ev) < 2:
            continue
        iv = np.diff([e[0] for e in ev]) / 60.0
        # 同队间隔里剔除跨天（>12h 视为隔日活动）
        iv_same = iv[iv < 720]
        if len(iv_same) == 0:
            continue
        days = defaultdict(int)
        for e in ev:
            days[datetime.fromtimestamp(e[0]).date()] += 1
        mx = max(days.values())
        wait45 += (iv_same >= 45).sum(); wait60 += (iv_same >= 60).sum(); n_tot += len(iv_same)
        P(f"| {t} | {np.median(iv_same):.1f} | {(iv_same<=10).mean()*100:.0f}% | "
          f"{(iv_same>=45).mean()*100:.0f}% | {(iv_same>=60).mean()*100:.0f}% | {mx} |")
    if n_tot:
        P(f"- 全体同队间隔 n={n_tot}：P(≥45min) = {wait45/n_tot*100:.1f}%，P(≥60min) = {wait60/n_tot*100:.1f}%"
          f"（对照 adaptive WAIT_MIN 45→60 的经验基础）\n")

    # E. 出分序列谱（白噪声零假设 shuffle 检验）
    P("## E. 出分时间序列谱（按队，n≥5）")
    P("| 队伍 | n | 均值 | σ | lag-1 自相关 | shuffle p | 趋势 slope (s/h) | 判读 |")
    P("|---|---|---|---|---|---|---|---|")
    for t in teams:
        ev = [e for e in per_team[t] if e[2] is not None]
        if len(ev) < 5:
            continue
        x = np.array([e[2] for e in ev])
        th = np.array([e[0] for e in ev]) / 3600
        xz = x - x.mean()
        lag1 = float((xz[:-1] * xz[1:]).sum() / (xz**2).sum())
        rng = np.random.default_rng(11)
        obs = abs(lag1)
        pval = float(np.mean([abs((lambda y: ((y[:-1]-y.mean())*(y[1:]-y.mean())).sum()/((y-y.mean())**2).sum())(rng.permutation(x))) > obs
                              for _ in range(2000)]))
        sl = float(np.polyfit(th - th[0], x, 1)[0])
        # 去趋势 lag-1（区分「趋势主导」与「真 AR 结构」）
        resid = x - np.polyval(np.polyfit(th - th[0], x, 1), th - th[0])
        rz = resid - resid.mean()
        lag1_res = float((rz[:-1] * rz[1:]).sum() / (rz**2).sum())
        pval_res = float(np.mean([abs((lambda y: ((y[:-1]-y.mean())*(y[1:]-y.mean())).sum()/((y-y.mean())**2).sum())(rng.permutation(resid))) > abs(lag1_res)
                                  for _ in range(2000)]))
        if pval > 0.05:
            verdict = "白噪声（无自相关）"
        elif pval_res > 0.05:
            verdict = f"趋势主导（去趋势后白噪声, lag1′={lag1_res:+.3f}, p′={pval_res:.3f}）"
        else:
            verdict = ("负自相关（振荡/回归均值）" if lag1 < 0 else "真自相关（漂移/时段效应）")
        P(f"| {t} | {len(x)} | {x.mean():.2f} | {x.std(ddof=1):.2f} | {lag1:+.3f} | {pval:.3f} | {sl:+.3f} | {verdict} |")
    P("")
    P("## F. 结论要点（数字以本文件为准）")
    P("- 事件流偏离泊松的程度用 B 与 Fano 曲线双重刻画；")
    P("- 昼节律/配额结构是否在谱上成像，以 Bonferroni 门限判定，不做事后画线；")
    P("- 出分序列以 shuffle 检验判白噪声，避免把小样本噪声读成「趋势」。")

    OUT.write_text("\n".join(L), encoding="utf-8")
    print("written", OUT)


if __name__ == "__main__":
    main()
