# -*- coding: utf-8 -*-
"""fit0260_judge_queue_delay.py — 0260: 官方判分队列排队延迟非参数拟合.

数据源（只读，零写入）:
  runs/board_watch.jsonl             本队 11-05 五发: 不规则轮询 → 区间删失
  runs/sequential_adaptive_log.jsonl 本队 11-07 五发: 30s 轮询 → 窄区间
  runs/adaptive_night_log.jsonl      本队 11-06 slot1: 45min 超时 → 右删失
  runs/submissions.jsonl             本队 15 发全量提交时间
  runs/official_results.jsonl        官方侧回执时间与成绩（上下文）
  runs/leaderboard/ledger.csv        跨队快照 → 松上界
  runs/leaderboard_full.json         全队到达过程（λ 估计）

方法:
  1) Turnbull NPMLE（区间删失自洽 EM）拟合出分延迟分布;
  2) 冷启动 vs 热管道对比 + lull 相关性;
  3) M/D/1 反演一致性检验（负载乘数情景表）;
  4) Bootstrap 置信区间 + 对 5 发串行作战的预测。

只打印到 stdout（重定向为 zcode/scripts/_0260_out.md），不写任何数据文件。
"""
import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"

POLL_SEQ_SEC = 30.0          # sequential_adaptive_night.wait_for_new_score(poll_sec=30)
GRID_MAX_MIN = 240.0         # 右删失质量截断假设（所有观测最终均出分）
POLL_BOARD_GAP_MAX_MIN = 180.0  # 跨队松上界保留阈值


def parse_ts(s):
    s = s.strip()
    if s.endswith("+0800"):
        s = s[:-5]
    if s.endswith("+08:00"):
        s = s[:-6]
    return datetime.fromisoformat(s)


def minutes(a, b):
    return (b - a).total_seconds() / 60.0


# ---------------------------------------------------------------- 1) 数据装载
def load_our_submissions():
    rows = []
    for line in open(RUNS / "submissions.jsonl", encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        rows.append(parse_ts(d["at"]))
    return sorted(rows)


def load_board_watch_intervals():
    """本队 11-05: 最后一次未含该提交的轮询 → 首次含该提交的轮询."""
    polls = []
    for line in open(RUNS / "board_watch.jsonl", encoding="utf-8", errors="replace"):
        d = json.loads(line)
        seen = parse_ts(d["seen_at"])
        subs = {parse_ts(a["submitted_at"]) for a in d.get("attempts", [])}
        polls.append((seen, subs))
    polls.sort()
    out = []
    for sub in sorted({s for _, subs in polls for s in subs}):
        last_without, first_with = None, None
        for seen, subs in polls:
            if sub <= seen:
                if sub in subs:
                    first_with = seen
                    break
                last_without = seen
        if first_with is None:
            continue
        lo = sub if last_without is None else last_without
        out.append(("赛博coder", sub, lo, first_with, "board_watch"))
    return out


def load_seq1107_intervals():
    """本队 11-07 逐发闭环（真实运行, ts 为 2026-11-07 的 shot_* 事件）."""
    submitted, scored = {}, {}
    for line in open(RUNS / "sequential_adaptive_log.jsonl", encoding="utf-8", errors="replace"):
        d = json.loads(line)
        ts = d.get("ts", "")
        if not ts.startswith("2026-11-07"):
            continue
        ev = d.get("event", "")
        if ev == "shot_1_submitted" or ev.startswith("shot_") and ev.endswith("_submitted"):
            idx = int(ev.split("_")[1])
            submitted[idx] = parse_ts(ts)
        elif ev.startswith("shot_") and ev.endswith("_scored"):
            idx = int(ev.split("_")[1])
            scored[idx] = parse_ts(ts)
    out = []
    for idx in sorted(set(submitted) & set(scored)):
        # scored = 首次轮询命中; 上一轮 30s 前未命中 → 真实出分 ∈ (scored-30s, scored]
        hi = scored[idx]
        lo = hi - timedelta(seconds=POLL_SEQ_SEC)
        lo = max(lo, submitted[idx])
        out.append(("赛博coder", submitted[idx], lo, hi, "seq1107(30s poll)"))
    return out


def load_night1106_censored():
    """11-06 slot1: 45min 等待无出分 → delay > 45.67 min（右删失）. 事件在 adaptive_log.jsonl."""
    out = []
    sub = None
    timeout = None
    for fn in ("adaptive_log.jsonl", "adaptive_night_log.jsonl"):
        for line in open(RUNS / fn, encoding="utf-8", errors="replace"):
            d = json.loads(line)
            if d.get("event") == "submit" and str(d.get("at", "")).startswith("2026-11-06 00:05"):
                sub = parse_ts(d["at"])
            if d.get("event") == "timeout" and str(d.get("ts", "")).endswith("00:50:49"):
                timeout = parse_ts(d["ts"])
    if sub and timeout:
        out.append(("赛博coder", sub, timeout, math.inf, "night1106(45min 超时右删失)"))
    return out


def load_cross_team_bounds():
    """ledger.csv 全局快照序列: 相对上一全局快照「新出现的队伍或更优成绩」→ 松上界（低置信）."""
    snaps = []  # 按时间排序的去重快照: (checked_at, {team: (best, subm)})
    for i, line in enumerate(open(RUNS / "leaderboard" / "ledger.csv", encoding="utf-8", errors="replace")):
        if i == 0:
            continue
        parts = line.strip().split(",")
        if len(parts) < 7:
            continue
        checked, _problem, _rank, team, best, _natt, subm = parts[:7]
        t = parse_ts(checked)
        for s in snaps:
            if abs((s[0] - t).total_seconds()) < 1:
                break
        else:
            snaps.append((t, {}))
        snaps[-1][1][team] = (float(best), parse_ts(subm))
    out = []
    for k in range(1, len(snaps)):
        prev_t, prev_m = snaps[k - 1]
        cur_t, cur_m = snaps[k]
        for team, (best, subm) in cur_m.items():
            pb = prev_m.get(team)
            new_score = pb is None or best < pb[0] - 1e-9
            if new_score and subm > prev_t:
                delay_hi = minutes(subm, cur_t)
                if 0 < delay_hi <= POLL_BOARD_GAP_MAX_MIN:
                    out.append((team, subm, subm, cur_t, "ledger 快照松上界"))
    return out


def load_arrival_census():
    """全队到达过程: leaderboard_full.json (他队 attempts/submission_log) ∪ 本队 submissions.jsonl.

    本队以 submissions.jsonl 为准（服务器回执口径），lb 快照中的本队条目跳过防双重计数；
    未授权用户 为无效尝试（判分系统拒绝），不计入判分到达，单独注明。
    """
    seen = {}
    skipped_unauth = 0
    try:
        d = json.load(open(RUNS / "leaderboard_full.json", encoding="utf-8"))
        for prob in d["leaderboard"]["problems"]:
            for row in prob.get("submissions", []):
                team = row.get("team", "?")
                if team == "赛博coder":
                    continue
                for a in row.get("attempts", []):
                    seen[(team, a["submitted_at"])] = parse_ts(a["submitted_at"])
        for r in d.get("submission_log", []):
            team = r.get("team", "?")
            if team == "赛博coder":
                continue
            if team == "未授权用户":
                skipped_unauth += 1
                continue
            seen[(team, r["submitted_at"])] = parse_ts(r["submitted_at"])
    except Exception as e:
        print(f"[warn] leaderboard_full.json 读取失败: {e}")
    for t in load_our_submissions():
        seen[("赛博coder", t.isoformat(sep=" "))] = t
    pairs = sorted(((team, t) for (team, _ts), t in seen.items()), key=lambda x: x[1])
    return pairs, skipped_unauth


# ------------------------------------------------------- 2) Turnbull NPMLE
def turnbull_npmle(intervals, n_grid=481, iters=3000, tol=1e-12):
    grid = np.linspace(0.0, GRID_MAX_MIN, n_grid)
    A = []
    for lo, hi in intervals:
        idx = np.where((grid > lo + 1e-12) & (grid <= hi))[0]
        if len(idx) == 0:  # 极窄区间保护：并入最近点
            idx = np.array([min(range(len(grid)), key=lambda j: abs(grid[j] - (lo + hi) / 2))])
        A.append(idx)
    n = len(intervals)
    p = np.full(len(grid), 1.0 / len(grid))
    for _ in range(iters):
        alpha = np.array([p[ix].sum() for ix in A])
        newp = np.zeros_like(p)
        for ix, a in zip(A, alpha):
            if a > 1e-15:
                newp[ix] += p[ix] / a
        newp /= n
        delta = np.max(np.abs(newp - p))
        p = newp
        if delta < tol:
            break
    return grid, p


def cdf_quantile(grid, p, q):
    c = np.cumsum(p)
    return float(np.interp(q, c, grid))


def turnbull_fit(intervals, label, boot=2000, seed=260):
    rng = np.random.default_rng(seed)
    grid, p = turnbull_npmle(intervals)
    q50 = cdf_quantile(grid, p, 0.50)
    q90 = cdf_quantile(grid, p, 0.90)
    mean = float((grid * p).sum())
    b50, b90, bm = [], [], []
    ints = np.array([[lo if math.isfinite(lo) else 0.0, hi if math.isfinite(hi) else GRID_MAX_MIN]
                     for lo, hi in intervals])
    for _ in range(boot):
        idx = rng.integers(0, len(ints), len(ints))
        g, pp = turnbull_npmle([tuple(ints[i]) for i in idx], n_grid=241, iters=1500)
        b50.append(cdf_quantile(g, pp, 0.50))
        b90.append(cdf_quantile(g, pp, 0.90))
        bm.append(float((g * pp).sum()))
    ci = lambda xs, a, b: (float(np.percentile(xs, a)), float(np.percentile(xs, b)))
    print(f"\n### Turnbull NPMLE（{label}, 观测 n={len(intervals)}）")
    print(f"- 均值 E[D] = {mean:.1f} min   95%CI {ci(bm,2.5,97.5)[0]:.1f}–{ci(bm,2.5,97.5)[1]:.1f}")
    print(f"- 中位数 P50 = {q50:.1f} min   95%CI {ci(b50,2.5,97.5)[0]:.1f}–{ci(b50,2.5,97.5)[1]:.1f}")
    print(f"- P90 = {q90:.1f} min   95%CI {ci(b90,2.5,97.5)[0]:.1f}–{ci(b90,2.5,97.5)[1]:.1f}")
    # 粗直方（每 15 min 质量桶）
    edges = np.arange(0, GRID_MAX_MIN + 15, 15)
    hist, _ = np.histogram(grid, bins=edges, weights=p)
    print("- 分布直方（15 min 桶质量）:")
    for m, w in zip(edges[:-1], hist):
        if w >= 0.005:
            bar = "#" * int(round(w * 60))
            print(f"    [{int(m):3d},{int(m)+15:3d}) {w*100:5.1f}% {bar}")
    return dict(mean=mean, q50=q50, q90=q90)


# ------------------------------------------------- 3) 冷/热对比与 M/D/1 反演
def md1_implied_service(wbar_min, lam_per_min, cap=120.0):
    """M/D/1: W = λτ²/(2(1-λτ)) → 在 (0, 1/λ) 内单调增, 数值解 τ; 不可行返回 None."""
    if lam_per_min <= 0:
        return None
    lo, hi = 1e-6, min(cap, 0.999 / lam_per_min)
    f = lambda t: lam_per_min * t * t / (2 * (1 - lam_per_min * t)) - wbar_min
    if f(hi) < 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(mid) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    print("# 0260 原始输出：官方判分队列排队延迟拟合")
    print(f"> 生成: {datetime.now().strftime('%Y-%m-%d %H:%M')}  脚本: zcode/scripts/fit0260_judge_queue_delay.py")
    print("> 只读 runs/*，零写入、零网络、零提交。")

    our_subs = load_our_submissions()
    census_pairs, n_unauth = load_arrival_census()
    arrivals = [t for _team, t in census_pairs]          # 全队到达（含本队）
    others_arr = [t for team, t in census_pairs if team != "赛博coder"]  # 他队到达
    print(f"\n## 1. 数据面\n- 本队提交 n={len(our_subs)}（{our_subs[0]:%m-%d %H:%M} → {our_subs[-1]:%m-%d %H:%M}）")
    print(f"- 全队到达普查（可观测并集, 已剔未授权用户 {n_unauth} 条无效尝试）n={len(arrivals)}"
          f"（{arrivals[0]:%m-%d %H:%M} → {arrivals[-1]:%m-%d %H:%M}）; 其中他队 n={len(others_arr)}")
    print(f"- official_results.jsonl 官方侧回执 n={sum(1 for _ in open(RUNS/'official_results.jsonl',encoding='utf-8',errors='replace'))}")

    obs = load_board_watch_intervals() + load_seq1107_intervals() + load_night1106_censored()
    cross = load_cross_team_bounds()

    print("\n## 2. 区间删失观测（本队, 分钟）")
    rows = []
    for team, sub, lo, hi, src in sorted(obs, key=lambda r: r[1]):
        d_lo = minutes(sub, lo)
        d_hi = minutes(sub, hi) if isinstance(hi, datetime) else GRID_MAX_MIN
        rows.append((sub, d_lo, d_hi, src))
        tag = f"({d_lo:.1f}, {d_hi:.1f}]" if isinstance(hi, datetime) else f"({d_lo:.1f}, ∞)"
        print(f"- {sub:%m-%d %H:%M}  delay ∈ {tag:>16}  [{src}]")
    # 非1发窗口特殊说明
    print("- 注: 11-05 13:25 一发无中途轮询 → 上界 109.4min 为「首见时间」而非真实延迟上确界（信息量低, NPMLE 中按宽区间处理）。")

    print("\n## 3. 跨队松上界（低置信，不进入本队 NPMLE）")
    for team, sub, lo, hi, src in sorted(cross, key=lambda r: r[1]):
        print(f"- {sub:%m-%d %H:%M} {team}: delay ≤ {minutes(lo,hi):.1f} min [{src}]")
    if not cross:
        print("- （无满足阈值的新增成绩上界）")

    # 分组: 判分为全队共享队列 → 用「该发前 60min 内可观测他队到达数」作拥挤度代理。
    #   高压 = s1(13:25, blueman 13:19 在 6min 前) + s2(14:23, YJDS 14:14 在 10min 前)
    #   低压 = s3,s4,s5 + shot1..shot5（前 60min 无他队可观测到达）
    #   slot1(11-06 00:05) 前无可观测到达但延迟 >45.7min（右删失）→ 单列离群
    #   （11-05 15:00 后他队活动处于观测盲区, 不能排除隐性积压）。
    print("\n## 4. 共享队列拥挤度分组（前 60min 他队可观测到达数）")
    high, low, outlier = [], [], []
    for sub, dlo, dhi, src in rows:
        others = [a for a in others_arr
                  if sub - timedelta(minutes=60) <= a < sub - timedelta(minutes=1)]
        n_press = len(others)
        is_slot1 = src.startswith("night1106")
        if is_slot1:
            grp, lst = "离群(右删失)", outlier
        elif n_press >= 1:
            grp, lst = "高压", high
        else:
            grp, lst = "低压", low
        recent = [a for a in others if a >= sub - timedelta(minutes=15)]
        tag_hi = f"{dhi:.1f}" if math.isfinite(dhi) else "∞"
        print(f"- {sub:%m-%d %H:%M} {grp}  前序到达={n_press}"
              f"{'（最近: ' + ', '.join(f'{a:%H:%M}' for a in recent) + '）' if recent else ''}"
              f"  delay ∈ ({dlo:.1f}, {tag_hi}]")
        lst.append((sub, dlo, dhi))
    cap = lambda iv: [(lo, hi if math.isfinite(hi) else GRID_MAX_MIN) for _, lo, hi in iv]
    tw = turnbull_fit(cap(low), "低压(热管道)") if len(low) >= 2 else None
    tc = turnbull_fit(cap(high), "高压(积压)") if len(high) >= 1 else None

    print("\n## 5. 全池 Turnbull NPMLE")
    pool = [(lo, hi if math.isfinite(hi) else GRID_MAX_MIN) for _, lo, hi, _ in rows]
    tp = turnbull_fit(pool, "全池(含离群右删失)")

    # 参数对照（中点近似，敏感性说明用）
    mids = np.array([min((lo + min(hi, GRID_MAX_MIN)) / 2, GRID_MAX_MIN) for lo, hi in pool])
    print(f"\n- 中点近似均值 = {mids.mean():.1f} min, std = {mids.std(ddof=1):.1f}, CV = {mids.std(ddof=1)/mids.mean()*100:.0f}%")

    print("\n## 6. M/D/1 一致性反演（λ 为可观测口径, τ 为反演解）")
    # 拥挤白天 λ: 11-05 10:00-17:00 可观测全队到达; 低载夜间 λ: 11-07 00:05-01:25
    day_win = [a for a in arrivals if datetime(2026, 11, 5, 10, 0) <= a <= datetime(2026, 11, 5, 17, 0)]
    night_win = [a for a in arrivals if datetime(2026, 11, 7, 0, 0) <= a <= datetime(2026, 11, 7, 2, 0)]
    lam_day = len(day_win) / 420.0
    lam_night = len(night_win) / 80.0
    print(f"- λ_day(11-05 10:00-17:00) = {lam_day:.4f}/min（观测 {len(day_win)} 发/7h, 他队为主）")
    print(f"- λ_night(11-07 00:05-01:25) ≥ {lam_night:.4f}/min（观测 {len(night_win)} 发/80min, 全为本队）")
    if tw:
        print(f"- 低压组 E[W]={tw['mean']:.1f} min → 反演单判分作业耗时 τ̂ 与利用率 ρ:")
        for lbl, lam in (("day", lam_day), ("night", lam_night)):
            for m in (1, 3):
                tau = md1_implied_service(tw["mean"], lam * m)
                if tau:
                    rho = lam * m * tau
                    print(f"    {lbl} m={m}: λ={lam*m:.3f}/min → τ̂={tau:.1f} min, ρ={rho:.2f} {'⚠ ρ>0.9' if rho>0.9 else 'OK'}")
                else:
                    print(f"    {lbl} m={m}: λ={lam*m:.3f}/min → 无可行解（λτ≥1, 该负载下 E[W] 必然 >{tw['mean']:.0f} min）")
    print("- 注: 官方判分多题并行、他队夜间到达不可观测 → λ 为下界, τ̂/ρ 只作数量级一致性检验, 不作点估计。")
    print("- 注2: 11-07 五发延迟 23.1/8.2/18.4/9.6/17.8 min 交替不恒定, 与定常 M/D/1 平稳等待不符 → 判分侧服务时间")
    print("  存在异质性（与官方『重复多次取平均』的多重复评测机制一致: 服务时间 ≈ k·T_eval, k 随批次波动）。")

    print("\n## 7. 作战预测（5 发串行闭环）")
    if tw:
        print(f"- 低压(会话内后续)单发: P50={tw['q50']:.1f} min, P90={tw['q90']:.1f} min, E[D]={tw['mean']:.1f} min")
        print(f"- 5 发串行判分等待期望 ≈ 5×E[D] = {5*tw['mean']:.0f} min（11-07 实测 77.0 min 落在该量级）")
    if tc:
        print(f"- 高压(积压)组: E[D]={tc['mean']:.1f} min, P50={tc['q50']:.1f} min, P90={tc['q90']:.1f} min（n=2, 宽区间, 仅量级参考）")
    r1107 = [r for r in rows if r[0].date() == datetime(2026, 11, 7).date()]
    total_1107 = sum(r[2] for r in r1107)  # r=(sub, dlo, dhi, src); dhi=首见出分时刻
    print(f"- 11-07 实测五发「提交→首见出分」等待总和（上界口径, n={len(r1107)}）= {total_1107:.1f} min")
    print("- 建议: 会话首发的 WAIT_MIN ≥ 60 min 维持不变（11-06 slot1 >45.7min 右删失 + 11-05 s2 ∈ (50.7,56.7]）；")
    print("  会话内后续发 WAIT_MIN=25-30 min 已覆盖低压组 P90；30s 轮询粒度对延迟测量偏差 ≤0.5 min，可忽略。")
    print("- 避峰推论: 拥挤度代理显示延迟由共享队列积压驱动 → 若前一发出分前他队仍在连发, 我方下一发预期延迟上移;") 
    print("  反之队列排空后（前 60min 无他队出分活动）出分最快（观测 8-10 min）。出分排队无法压缩, 只能预算管理。")

    print("\n## 8. 口径与局限")
    print("- n=10 信息性本队区间 + 1 条右删失；跨队仅 2 条松上界 → 统计功效有限，结论按区间/CI 陈述，不做单点断言；")
    print("- 右删失质量在 240 min 处截断（所有观测最终均出分, 官方侧 10/10 有成绩回执）；")
    print("- NPMLE 对宽区间 (0,109] 的质量分配不唯一（网格均匀初始化下的自洽解），已用 Bootstrap CI 反映该不确定性；")
    print("- λ 为可观测下界（他队不可见提交未计入），M/D/1 反演仅作数量级检验。")


if __name__ == "__main__":
    main()
