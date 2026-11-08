# -*- coding: utf-8 -*-
"""0068 — 293 场实测数据下分文件吞吐与链路利用率全盘热力图生成（离线分析脚本）。

数据源（只读）: runs/results.jsonl
口径:
  - 文件大小: 1..6.bin = 10/20/40/80/160/320 MB（官方《六载穿柜》）
  - 线速 C = 100 Mbps = 12.5 MB/s；单包 1200 B -> 服务率 mu_s = 10.42 pkt/ms
  - 利用率 u_i = (size_i / t_i) / 12.5 * 100%
  - 场次间隙 gap = total_seconds - sum(t_i)
清洗:
  - 剔除 valid=false（官方判定不成立）与 tag 以 load- 开头的污染样本
  - 保留 valid 缺失的历史场次但单独标记
本脚本仅向 stdout 输出 markdown 片段，不写任何文件（写入由报告环节完成）。
"""
import json
import math
import re
from collections import defaultdict
from datetime import datetime

RESULTS = "runs/results.jsonl"
SIZES_MB = [10, 20, 40, 80, 160, 320]          # 1..6.bin
FILES = [f"{i}.bin" for i in range(1, 7)]
C_MBPS = 100.0                                 # 瓶颈线速
C_MBS = C_MBPS / 8.0                           # 12.5 MB/s
PKT_BYTES = 1200.0
MU_PKT_MS = C_MBS * 1024 * 1024 / PKT_BYTES / 1000.0   # ≈10.42 pkt/ms


def load_records():
    recs = []
    with open(RESULTS, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return recs


def clean(recs):
    """返回 (cleaned, stats)。cleaned: 场次字典列表（含 flag 说明）。"""
    stats = {"raw": len(recs), "valid_true": 0, "valid_false": 0,
             "valid_missing": 0, "load_polluted": 0, "incomplete": 0}
    out = []
    for r in recs:
        dl = r.get("downloads") or {}
        if any(f not in dl or dl[f] is None for f in FILES):
            stats["incomplete"] += 1
            continue
        tag = r.get("tag") or ""
        if tag.startswith("load-"):
            stats["load_polluted"] += 1
            continue
        v = r.get("valid", None)
        if v is True:
            stats["valid_true"] += 1
        elif v is False:
            stats["valid_false"] += 1
            continue            # 官方判定不成立，剔除
        else:
            stats["valid_missing"] += 1   # 历史无 valid 字段，保留并标记
        t = [float(dl[f]) for f in FILES]
        u = [SIZES_MB[i] / t[i] / C_MBS * 100.0 for i in range(6)]
        total = float(r.get("total_seconds") or sum(t))
        gap = total - sum(t)
        out.append({
            "at": r.get("at", ""), "tag": tag, "t": t, "u": u,
            "total": total, "gap": gap, "valid": v,
            "config": r.get("config") or {},
            "epoch": parse_at(r.get("at", "")),
        })
    return out, stats


def parse_at(s):
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z")
    except Exception:
        return None


def pct(sorted_vals, p):
    if not sorted_vals:
        return float("nan")
    k = (len(sorted_vals) - 1) * p
    lo = int(math.floor(k))
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


# ---------- 颜色梯度（10 档，文本热力图用） ----------
RAMP = "░▒▓"   # 兜底
GRAD = ["_", "░", "░", "▒", "▒", "▓", "▓", "█", "█", "█"]


def cell(u, umin=0, umax=100):
    x = (u - umin) / (umax - umin + 1e-9)
    x = max(0.0, min(1.0, x))
    idx = int(x * 9.999)
    return GRAD[idx]


def fmt_u(u):
    return f"{u:5.1f}"


def heatmap_band(rows, nband=12, label=""):
    """H1: 场次按总耗时升序分 nband 带，每带每文件平均利用率。"""
    rows = sorted(rows, key=lambda r: r["total"])
    n = len(rows)
    out = []
    out.append(f"### H1 {label}（场次按总耗时升序分 {nband} 带，单元=带内平均利用率 %，N={n}）")
    out.append("")
    out.append("| 耗时带 | 总耗时均值(s) | 1.bin | 2.bin | 3.bin | 4.bin | 5.bin | 6.bin | 带内会话利用率 |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    for b in range(nband):
        lo = int(b * n / nband)
        hi = max(lo + 1, int((b + 1) * n / nband))
        seg = rows[lo:hi]
        mu = [sum(r["u"][i] for r in seg) / len(seg) for i in range(6)]
        mt = sum(r["total"] for r in seg) / len(seg)
        # 会话利用率 = 总字节 / 总时间 / 线速
        sess = sum(SIZES_MB) / mt / C_MBS * 100.0
        band_lab = f"P{int(b*100/nband)}–P{int((b+1)*100/nband)}"
        cells = " | ".join(f"{cell(mu[i])}{mu[i]:6.1f}" for i in range(6))
        out.append(f"| {band_lab} | {mt:8.2f} | {cells} | {cell(sess)}{sess:6.1f} |")
    out.append("")
    return "\n".join(out)


def heatmap_density(rows):
    """H2: 分文件 × 利用率区间 的样本密度（占该文件样本数百分比）。"""
    bins = [0, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200]
    out = []
    out.append("### H2 分文件吞吐密度热力图（单元=该文件落入利用率区间的样本占比 %，行内合计=100%）")
    out.append("")
    head = "| 利用率区间(%) | " + " | ".join(FILES) + " |"
    out.append(head)
    out.append("|" + "---|" * 7)
    for bi in range(len(bins) - 1):
        lo, hi = bins[bi], bins[bi + 1]
        cells = []
        for i in range(6):
            vals = [r["u"][i] for r in rows]
            cnt = sum(1 for v in vals if lo <= v < hi)
            cells.append(f"{cell(cnt/len(vals)*100, 0, 100)}{cnt/len(vals)*100:6.1f}")
        lab = f"[{lo},{hi})" if bi < len(bins) - 2 else f"≥{lo}"
        out.append(f"| {lab:>10} | " + " | ".join(cells) + " |")
    out.append("")
    return "\n".join(out)


def heatmap_time(rows):
    """H3: 小时 × 分文件 平均利用率（时间演化）。"""
    byslot = defaultdict(list)
    for r in rows:
        if not r["epoch"]:
            continue
        slot = r["epoch"].strftime("%m-%d %H")
        byslot[slot].append(r)
    slots = sorted(byslot)
    out = []
    out.append("### H3 时间演化热力图（小时槽 × 分文件平均利用率 %，括号内为该槽场数）")
    out.append("")
    out.append("| 时段 | N | 1.bin | 2.bin | 3.bin | 4.bin | 5.bin | 6.bin | 会话利用率 |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    for s in slots:
        seg = byslot[s]
        mu = [sum(r["u"][i] for r in seg) / len(seg) for i in range(6)]
        mt = sum(r["total"] for r in seg) / len(seg)
        sess = sum(SIZES_MB) / mt / C_MBS * 100.0
        cells = " | ".join(f"{cell(mu[i])}{mu[i]:6.1f}" for i in range(6))
        out.append(f"| {s}h | {len(seg):3d} | {cells} | {cell(sess)}{sess:6.1f} |")
    out.append("")
    return "\n".join(out)


def profile(rows):
    """分文件利用率剖面 + 场次间隙剖面。"""
    out = []
    out.append("### P1 分文件利用率剖面（%）与分文件耗时极值")
    out.append("")
    out.append("| 文件 | 大小(MB) | 理论最短(s) | 利用率 min | P10 | 中位 | 均值 | P90 | max | 实测最快(s) |")
    out.append("|---|---|---|---|---|---|---|---|---|---|")
    for i in range(6):
        us = sorted(r["u"][i] for r in rows)
        ts = sorted(r["t"][i] for r in rows)
        floor = SIZES_MB[i] / C_MBS
        out.append(
            f"| {FILES[i]} | {SIZES_MB[i]} | {floor:.1f} | {pct(us,0):.1f} | {pct(us,.1):.1f} "
            f"| {pct(us,.5):.1f} | {sum(us)/len(us):.1f} | {pct(us,.9):.1f} | {pct(us,1):.1f} | {ts[0]:.3f} |")
    out.append("")
    gaps = sorted(r["gap"] for r in rows)
    sess = sorted(sum(SIZES_MB) / r["total"] / C_MBS * 100.0 for r in rows)
    max_gap = gaps[-1]
    out.append("### P2 场次间隙口径核验 gap = total − Σt_i")
    out.append("")
    if max_gap < 1e-6:
        out.append(f"实测 gap 在全部 {len(rows)} 场中均为 0（最大 |gap| = {max_gap:.2e} s）："
                   "`total_seconds` 恒等于六段下载耗时之和。这与官方口径一致"
                   "（《六载穿柜》：场景总时间 = 六次下载耗时相加，配置写入生效时间不计入下载耗时），"
                   "因此**不存在可优化的场次级间隙项**，所有优化杠杆都在六段下载内部的链路利用率上。")
    else:
        out.append(f"检测到非零间隙，最大 {max_gap:.3f} s，需人工核查。")
    out.append("")
    out.append("### P3 会话级链路利用率（Σ630MB / total / 12.5MBps）")
    out.append("")
    out.append("| 指标 | min | P10 | 中位 | 均值 | P90 | max |")
    out.append("|---|---|---|---|---|---|---|")
    out.append(f"| 会话利用率(%) | {pct(sess,0):.1f} | {pct(sess,.1):.1f} | {pct(sess,.5):.1f} "
               f"| {sum(sess)/len(sess):.1f} | {pct(sess,.9):.1f} | {pct(sess,1):.1f} |")
    out.append("")
    return "\n".join(out)


def correlation(rows):
    """各文件利用率与总耗时的 Pearson 相关（找出主导文件）。"""
    n = len(rows)
    mt = sum(r["total"] for r in rows) / n
    out = []
    out.append("### P4 各文件利用率与场景总耗时的 Pearson 相关（N=%d）" % n)
    out.append("")
    out.append("| 文件 | r(利用率,总耗时) | 主导度排序 |")
    out.append("|---|---|---|")
    rs = []
    for i in range(6):
        mu_ = sum(r["u"][i] for r in rows) / n
        sxy = sum((r["u"][i] - mu_) * (r["total"] - mt) for r in rows)
        sxx = math.sqrt(sum((r["u"][i] - mu_) ** 2 for r in rows))
        syy = math.sqrt(sum((r["total"] - mt) ** 2 for r in rows))
        r_ = sxy / (sxx * syy) if sxx > 0 and syy > 0 else float("nan")
        rs.append((FILES[i], r_))
    order = sorted(range(6), key=lambda i: rs[i][1])
    for rank, i in enumerate(order):
        out.append(f"| {FILES[i]} | {rs[i][1]:+.3f} | {rank+1} |")
    out.append("")
    out.append("> r 为负且绝对值越大 = 该文件利用率对总耗时的解释力越强（利用率每提升 1%，总耗时下降越多）。")
    out.append("")
    return "\n".join(out)


def top_sessions(rows, k=8):
    """最快的 k 场的分文件明细（含各文件利用率）。"""
    rows = sorted(rows, key=lambda r: r["total"])[:k]
    out = []
    out.append(f"### T1 最快 {k} 场分文件明细")
    out.append("")
    out.append("| # | 时间 | 标签 | 总耗时(s) | 1..6.bin 耗时(s) | 1..6.bin 利用率(%) | 会话利用率(%) |")
    out.append("|---|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        ts = "/".join(f"{v:.2f}" for v in r["t"])
        us = "/".join(f"{v:.1f}" for v in r["u"])
        sess = sum(SIZES_MB) / r["total"] / C_MBS * 100.0
        tag = r["tag"][:28] if r["tag"] else "(no tag)"
        out.append(f"| {i} | {r['at'][:16].replace('T',' ')} | {tag} | {r['total']:.3f} | {ts} | {us} | {sess:.1f} |")
    out.append("")
    out.append("> 参照：官方最好 133.086 s 会话利用率 37.9%；榜首 Catnet 119.8293 s → 42.0%；EVT 下界 106.597 s → 47.3%。")
    out.append("")
    return "\n".join(out)


def config_family(rows):
    """按 pacer 模块族聚合的利用率对比（config 里第一目录的模块名）。"""
    fam_map = defaultdict(list)
    for r in rows:
        c = r.get("config") or {}
        p1 = c.get("1") or "(inherit/default)"
        m = re.match(r"([a-z_]+):", p1)
        fam = m.group(1) if m else ("default" if p1 == "(inherit/default)" else "other")
        fam_map[fam].append(r)
    out = []
    out.append("### P5 按 1.bin pacer 模块族聚合（模块族 × 分文件平均利用率 %）")
    out.append("")
    out.append("| 模块族 | N | 1.bin | 2.bin | 3.bin | 4.bin | 5.bin | 6.bin | 会话利用率 | 中位总耗时(s) |")
    out.append("|---|---|---|---|---|---|---|---|---|---|")
    for fam, seg in sorted(fam_map.items(), key=lambda kv: -len(kv[1])):
        mu = [sum(r["u"][i] for r in seg) / len(seg) for i in range(6)]
        mt = sum(r["total"] for r in seg) / len(seg)
        med_t = pct(sorted(r["total"] for r in seg), .5)
        sess = sum(SIZES_MB) / mt / C_MBS * 100.0
        cells = " | ".join(f"{mu[i]:5.1f}" for i in range(6))
        out.append(f"| {fam} | {len(seg):3d} | {cells} | {sess:5.1f} | {med_t:8.2f} |")
    out.append("")
    return "\n".join(out)


def main():
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    recs = load_records()
    rows, stats = clean(recs)
    print(f">> 数据源 runs/results.jsonl：原始 {stats['raw']} 行")
    print(f">> 清洗：valid=true {stats['valid_true']}，valid=false 剔除 {stats['valid_false']}，"
          f"load-* 污染剔除 {stats['load_polluted']}，字段缺失补录 {stats['valid_missing']}，"
          f"下载不完整剔除 {stats['incomplete']}")
    n = len(rows)
    print(f">> 最终分析集 N={n}（对齐任务标题口径：派发时刻约 293 场，jsonl 为追加式流水，N 随时间漂移）")
    print()
    print(heatmap_band(rows, 12, "全量场次利用率热力图"))
    print(heatmap_density(rows))
    print(heatmap_time(rows))
    print(profile(rows))
    print(correlation(rows))
    print(top_sessions(rows, 8))
    print(config_family(rows))
    # 关键统计摘要
    tt = sorted(r["total"] for r in rows)
    print(">> 总耗时分布：min %.3f / P10 %.2f / 中位 %.2f / 均值 %.2f / P90 %.2f / max %.2f s"
          % (pct(tt, 0), pct(tt, .1), pct(tt, .5), sum(tt) / n, pct(tt, .9), pct(tt, 1)))
    floor_total = sum(SIZES_MB) / C_MBS
    print(">> 理论下界：Σsize/C = %.1f s（零背景零间隙）；当前官方最好 133.086 s 的会话利用率 = %.1f%%"
          % (floor_total, sum(SIZES_MB) / 133.086 / C_MBS * 100))


if __name__ == "__main__":
    main()
