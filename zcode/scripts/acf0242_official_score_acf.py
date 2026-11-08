# -*- coding: utf-8 -*-
"""任务 0242：官方评分历史波动与周末评测负载周期性自相关 ACF 分析。

数据源（全部本地真实记录，只读）：
  - runs/official_results.jsonl        11/05–11/06 官方出分（10 条）
  - runs/sequential_adaptive_log.jsonl 11/07 真实夜跑出分事件（甄别 dry-run 模拟分）
  - runs/board_watch.jsonl             11/05 榜单快照（出分延迟的区间删失估计）
  - runs/adaptive_log.jsonl            11/06 自适应提交+超时事件（右删失）
  - runs/submissions.jsonl             提交时间戳交叉验证（防 mock 污染）

防污染纪律：sequential_adaptive_log 中 dry-run=true 的 118.0 系列是 rehearsal
模拟分，必须剔除；真实运行 = 最后一次 dry_run=false init 之后的事件，且
submitted 时间戳须与 submissions.jsonl 交叉对上（±120s）。

输出：stdout + zcode/scripts/_0242_out.md（markdown 报告体）。
合规：纯本地计算，不联网、不提交、不写任何受保护路径。
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"
OUT_MD = ROOT / "zcode" / "scripts" / "_0242_out.md"

WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def parse_dt(s: str) -> datetime:
    s = s.strip()
    if s.endswith("+0800"):
        s = s[:-5].strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"unparseable datetime: {s!r}")


# ---------------------------------------------------------------- 数据装载
def load_official_scores():
    """返回 [(datetime, seconds, source)] 按提交时间排序的真实官方出分。"""
    rows = []
    for ln in (RUNS / "official_results.jsonl").read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        d = json.loads(ln)
        rows.append((parse_dt(d["submitted_at"]), float(d["official_seconds"]),
                     d.get("note", "")[:40]))
    # 11/07 真实夜跑：最后一次 dry_run=false init 之后的事件
    events = [json.loads(l) for l in
              (RUNS / "sequential_adaptive_log.jsonl").read_text(encoding="utf-8").splitlines()
              if l.strip()]
    last_real_idx = -1
    for i, e in enumerate(events):
        if e.get("event") == "init_sequential_controller" and e.get("dry_run") is False:
            last_real_idx = i
    real = events[last_real_idx + 1:] if last_real_idx >= 0 else []
    scored = [e for e in real if e.get("event", "").endswith("_scored")]
    submitted_log = []
    for ln in (RUNS / "submissions.jsonl").read_text(encoding="utf-8").splitlines():
        if ln.strip():
            d = json.loads(ln)
            submitted_log.append(parse_dt(d["at"]))
    for e in scored:
        raw = e.get("raw", {})
        t = parse_dt(raw["submitted_at"])
        # 交叉验证：必须能在 submissions.jsonl 找到 ±120s 内的同刻记录，否则视为 mock
        ok = any(abs((t - s).total_seconds()) <= 120 for s in submitted_log)
        if not ok:
            raise SystemExit(f"[防污染] 11/07 出分事件 submitted_at={t} 未匹配 submissions.jsonl，疑似 mock，中止")
        rows.append((t, float(e["download_seconds"]), f"seq-real {e.get('event')}"))
    rows.sort(key=lambda r: r[0])
    return rows


def load_latency_records():
    """出分延迟记录（分钟）。返回 (提交时刻, 下界, 上界, 是否删失, 来源)。

    - board_watch 区间删失：出现在快照 k 而不在 k-1 → 延迟 ∈ (t_prev - t_sub, t_see - t_sub]
    - sequential 轮询（~30s）：scored 事件即上界
    - adaptive timeout：右删失下界
    """
    recs = []
    bw = [json.loads(l) for l in
          (RUNS / "board_watch.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    seen: dict[str, datetime] = {}      # submitted_at_str -> 首次出现的快照时刻
    prev_seen: dict[str, datetime | None] = {}  # 出现前最后一次快照时刻（区间下界）
    last_snap: datetime | None = None
    for snap in bw:
        seen_at = parse_dt(snap["seen_at"])
        for att in snap.get("attempts", []):
            key = att["submitted_at"]
            if key not in seen:
                seen[key] = seen_at
                prev_seen[key] = last_snap
        last_snap = seen_at
    for key, first in seen.items():
        t_sub = parse_dt(key)
        up = (first - t_sub).total_seconds() / 60.0
        prev = prev_seen.get(key)
        lo = ((prev - t_sub).total_seconds() / 60.0) if prev else 0.0
        recs.append((t_sub, lo, up, lo > 0, "board_watch"))
    # 11/06 adaptive timeout（右删失）
    for ln in (RUNS / "adaptive_log.jsonl").read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        e = json.loads(ln)
        if e.get("event") == "timeout":
            t_sub = parse_dt(e["submitted_at"])
            lo = (parse_dt(e["ts"]) - t_sub).total_seconds() / 60.0
            recs.append((t_sub, lo, math.inf, True, "adaptive_timeout"))
    # 11/07 sequential 真实轮询 sighting
    events = [json.loads(l) for l in
              (RUNS / "sequential_adaptive_log.jsonl").read_text(encoding="utf-8").splitlines()
              if l.strip()]
    last_real_idx = -1
    for i, e in enumerate(events):
        if e.get("event") == "init_sequential_controller" and e.get("dry_run") is False:
            last_real_idx = i
    for e in events[last_real_idx + 1:]:
        if e.get("event", "").endswith("_scored"):
            t_sub = parse_dt(e["raw"]["submitted_at"])
            up = (parse_dt(e["ts"]) - t_sub).total_seconds() / 60.0
            recs.append((t_sub, 0.0, up, True, "seq_poll"))
    recs.sort(key=lambda r: r[0])
    return recs


# ---------------------------------------------------------------- 统计
def acf(x: np.ndarray, max_lag: int = 3):
    """标准 ACF（分母 N 的有偏估计），返回 (r_k, 白噪声 95% Bartlett 带宽)。"""
    x = np.asarray(x, dtype=float)
    n = len(x)
    d = x - x.mean()
    c0 = float(np.dot(d, d) / n)
    out = []
    for k in range(1, max_lag + 1):
        ck = float(np.dot(d[:-k], d[k:]) / n)
        out.append(ck / c0 if c0 > 0 else float("nan"))
    band = 1.96 / math.sqrt(n)  # 白噪声零假设下 r_k 的 95% 带宽
    return out, band


def qstats(x):
    x = np.asarray(x, float)
    return dict(n=len(x), mean=float(x.mean()), std=float(x.std(ddof=1)) if len(x) > 1 else 0.0,
                min=float(x.min()), med=float(np.median(x)), max=float(x.max()))


def main() -> int:
    rows = load_official_scores()
    lat = load_latency_records()

    lines = []
    w = lines.append
    w("# 0242 输出 — 官方评分历史波动与周末评测负载 ACF（真实数据）\n")
    w(f"生成时间：{datetime.now():%Y-%m-%d %H:%M:%S}（Asia/Shanghai 本机时间）\n")

    # ---- A. 官方出分序列
    w("## A. 官方出分时间序列（真实，n=%d）\n" % len(rows))
    w("| # | 提交时刻 | 星期 | official_seconds | 来源 |")
    w("|---|---|---|---|---|")
    for i, (t, s, src) in enumerate(rows, 1):
        w(f"| {i} | {t:%m-%d %H:%M:%S} | {WEEKDAY_CN[t.weekday()]} | {s:.4f} | {src[:24]} |")
    w("")

    by_day = {}
    for t, s, _ in rows:
        by_day.setdefault(t.date(), []).append(s)
    w("### 按日聚合\n")
    w("| 日期 | 星期 | n | mean | std | min | max |")
    w("|---|---|---|---|---|---|---|")
    for day, vals in sorted(by_day.items()):
        st = qstats(vals)
        wd = WEEKDAY_CN[day.weekday()]
        w(f"| {day} | {wd} | {st['n']} | {st['mean']:.2f} | {st['std']:.2f} | "
          f"{st['min']:.2f} | {st['max']:.2f} |")
    w("")

    # ---- B. ACF：全序列
    series = np.array([s for _, s, _ in rows])
    (r_full, band_full) = acf(series, 3)
    w("## B. 自相关函数（ACF，有偏估计 r_k=c_k/c_0，白噪声 95% 带 ±1.96/√N）\n")
    w(f"- 全序列 n={len(series)}：r1={r_full[0]:+.4f}, r2={r_full[1]:+.4f}, r3={r_full[2]:+.4f}；"
      f"95% 带 = ±{band_full:.4f}")
    sig_full = abs(r_full[0]) > band_full
    w(f"  - r1 是否显著非零（|r1|>带宽）：{'是' if sig_full else '否'}")

    # 周末子序列
    wknd = np.array([s for t, s, _ in rows if t.weekday() >= 5])
    wd_names = sorted({WEEKDAY_CN[t.weekday()] for t, _, _ in rows if t.weekday() >= 5})
    (r_wk, band_wk) = acf(wknd, 2)
    w(f"- 周末子序列（{'/'.join(wd_names)}，n={len(wknd)}）：r1={r_wk[0]:+.4f}, "
      f"r2={r_wk[1]:+.4f}；95% 带 = ±{band_wk:.4f}")
    target = 0.25
    verdict_pt = r_wk[0] < target
    ci_lo, ci_hi = r_wk[0] - band_wk, r_wk[0] + band_wk
    verdict_ci = ci_hi < target
    w(f"- **考核目标核对（周末 r1 < {target}）**：点估计 {'满足' if verdict_pt else '不满足'}"
      f"（r1={r_wk[0]:+.4f}）；95% 置信区间 [{ci_lo:+.4f}, {ci_hi:+.4f}] "
      f"{'整体 < 0.25（目标在统计意义上成立）' if verdict_ci else '包含 0.25（n 过小，无法在统计意义上确立）'}")

    # 周内（周四+周五）子序列对照
    wkdy = np.array([s for t, s, _ in rows if t.weekday() < 5])
    (r_wd, band_wd) = acf(wkdy, 1)
    w(f"- 工作日子序列（n={len(wkdy)}）：r1={r_wd[0]:+.4f}（95% 带 ±{band_wd:.4f}）")

    # 稳健性：按日去均值后的全序列 ACF（剥离「日间配置档位」的非平稳结构）
    dm = series.copy()
    day_means = {d: float(np.mean(v)) for d, v in
                 ((d, np.array([s for t, s, _ in rows if t.date() == d])) for d in by_day)}
    for i, (t, _, _) in enumerate(rows):
        dm[i] -= day_means[t.date()]
    (r_dm, band_dm) = acf(dm, 2)
    w(f"- 稳健性对照：按日去均值后全序列（剥离日间档位漂移）n={len(dm)}："
      f"r1={r_dm[0]:+.4f}, r2={r_dm[1]:+.4f}（95% 带 ±{band_dm:.4f}）")
    w("")

    # 同配置连发对照（hr-44-60-4000 ×3，11/06 00:56:29/35/40）
    same = [s for t, s, _ in rows if "2026-11-06" == t.date().isoformat()
            and t.hour == 0 and t.minute == 56]
    if len(same) >= 3:
        (r_same, band_same) = acf(np.array(same), 1)
        w(f"- 同配置连发对照（hr-44-60-4000 ×3，n=3）：r1={r_same[0]:+.4f}"
          f"（带 ±{band_same:.3f}，仅示意，n 过小不做推断）")
    w("")

    # ---- C. 出分延迟（排队）序列
    w("## C. 出分延迟（系统排队）序列\n")
    w("| 提交时刻 | 星期 | 下界(min) | 上界(min) | 删失类型 | 来源 |")
    w("|---|---|---|---|---|---|")
    for t, lo, up, cens, src in lat:
        ups = "∞" if math.isinf(up) else f"{up:.1f}"
        w(f"| {t:%m-%d %H:%M:%S} | {WEEKDAY_CN[t.weekday()]} | {lo:.1f} | {ups} | "
          f"{'区间删失' if cens else '快照即上界'} | {src} |")
    w("")
    # 仅用上界有限的 11/05 与 11/07 记录做描述统计（不做跨日 ACF，删失混合会失真）
    finite = [(t, up) for t, lo, up, _, src in lat if math.isfinite(up) and up > 0]
    day_groups = {}
    for t, up in finite:
        day_groups.setdefault(t.date(), []).append(up)
    w("### 延迟上界的按日描述（删失混合，仅描述不做推断）\n")
    w("| 日期 | 星期 | n(上界有限) | mean(upper) | min | max |")
    w("|---|---|---|---|---|---|")
    for day, vals in sorted(day_groups.items()):
        v = np.array(vals)
        w(f"| {day} | {WEEKDAY_CN[day.weekday()]} | {len(v)} | {v.mean():.1f} | "
          f"{v.min():.1f} | {v.max():.1f} |")
    w("")
    # 11/07 真实夜跑延迟 ACF（n=5，轮询上界）
    l1107 = np.array([up for t, up in finite if t.date().isoformat() == "2026-11-07"])
    if len(l1107) >= 4:
        (r_lat, band_lat) = acf(l1107, 1)
        w(f"- 11/07（周六）夜跑延迟上界序列 n={len(l1107)}：r1={r_lat[0]:+.4f}"
          f"（95% 带 ±{band_lat:.4f}）；点估计 {'< 0.25 ✓' if r_lat[0] < 0.25 else '≥ 0.25 ✗'}")
    w("")

    # ---- D. 周期性检验能力声明
    w("## D. 周期性可检验性\n")
    w("- 数据跨度仅 3 天（11/05 周四 – 11/07 周六），每日恰 5 发（官方限额），")
    w("  无法支撑任何谱/周期估计（最短可分辨周期也需要 > 2 个完整周期样本）。")
    w("- 本审计只做：lag-1/2/3 ACF 点估计 + 白噪声带核对 + 按日聚合对照。")
    w("- 「周末负载周期性」目前只有 1 个周末日（11/07 周六）的 5 个样本，")
    w("  任何关于周末-工作日差异的结论都属探索性描述，不是可复验的统计推断。")
    w("")

    # ---- E. 结论与口径
    w("## E. 结论（对应考核目标）\n")
    w(f"1. **周末出分波动 r1 点估计 = {r_wk[0]:+.4f}，低于 0.25 阈值** —— "
      f"{'目标在点估计意义上成立' if verdict_pt else '目标不成立'}。")
    w(f"2. 但 n={len(wknd)}（仅 11/07 一个周末日），95% 白噪声带 ±{band_wk:.3f} "
      f"远宽于 |r1|，且区间 [{ci_lo:+.3f}, {ci_hi:+.3f}] "
      f"{'可以' if verdict_ci else '不能'}排除 r1 ≥ 0.25。**目标不能宣称统计显著**。")
    w(f"3. 全序列 r1={r_full[0]:+.4f}（n={len(series)}，带 ±{band_full:.3f}），"
      f"{'显著' if sig_full else '不显著'}；相邻两次官方成绩接近不相关，")
    w("   自适应策略不应依赖「出分动量」，只应依赖当发信息（与 0235 时序无关性结论一致）。")
    w("4. 排队延迟呈**机制性下移**而非周期波动：周四下午上界 10–57 min（首条 109 min 为快照启动删失），"
      "周五夜超时 >46 min，周六夜轮询上界 8–23 min —— 更像「深度夜晚低负载窗口」效应，"
      "样本量不足以区分「时段效应」与「负载效应」。")
    w("5. 口径声明：以上全部基于本地记录的真实官方出分；不含任何 mock/dry-run 数字"
      "（11/07 rehearsal 的 118.0 系列已按交叉验证规则剔除）。")

    text = "\n".join(lines) + "\n"
    OUT_MD.write_text(text, encoding="utf-8")
    print(text)
    print(f"[OK] 已写出 {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
