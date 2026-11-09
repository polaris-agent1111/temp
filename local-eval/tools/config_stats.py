#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""config_stats.py — 本地评测记录统计分析（可重复运行）

数据源: runs/results.jsonl (只读)
输出:   report/实验结果-统计.md (整体覆盖重写; 第 5-7 节由人工维护,
        本脚本只重写第 1-4 节, 用 AUTOGEN 标记包裹)

用法:   python tools/config_stats.py
依赖:   仅标准库; 若可 import scipy 则用 Welch t 检验, 否则用正态近似。
"""
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from statistics import mean, median, pstdev

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "runs", "results.jsonl")
OUT_MD = os.path.join(ROOT, "report", "实验结果-统计.md")

# 文档默认值 (docs/extracted/流量整形模块使用说明.md): 归一化时剔除与默认值相同的参数
DEFAULTS = {
    "token_bucket": {
        "tokens": 20, "burst": 40, "token_refill_rate": 10,
        "token_refill_interval_us": 100, "enable_n_in_flight": 1,
    },
    "coarse_grained_rate_based": {
        "max_pacing_rate": 0, "clock_granularity": 1000, "enable_n_in_flight": 1,
    },
    "precise_rate_based": {
        "max_pacing_rate": 0, "clock_granularity": 1000, "enable_n_in_flight": 1,
    },
    "origin": {"burst_tokens": 10, "max_pacing_rate": 0, "clock_granularity": 1000},
    "leak_bucket": {"leak_rate": 10, "bucket_cap": 30, "leak_interval_us": 1000},
}
FILES = ["1.bin", "2.bin", "3.bin", "4.bin", "5.bin", "6.bin"]


def norm_spec(spec):
    """把 'mode:k=v,...' 归一化成 'mode:k=v,...' (剔除等于默认值的参数)。"""
    spec = (spec or "").strip()
    if spec in ("", "(inherit/default)", "(空/默认)"):
        return "inherit/平台默认"
    if ":" not in spec:
        return spec
    mode, _, params = spec.partition(":")
    mode = mode.strip()
    kept = []
    if params.strip():
        for kv in params.split(","):
            if "=" not in kv:
                kept.append(kv.strip())
                continue
            k, _, v = kv.partition("=")
            k, v = k.strip(), v.strip()
            d = DEFAULTS.get(mode, {})
            if k in d:
                try:
                    if float(d[k]) == float(v):
                        continue  # 与默认值相同 → 剔除
                except ValueError:
                    pass
            kept.append(f"{k}={v}")
    kept.sort()
    return mode + (":" + ",".join(kept) if kept else ": (全默认)")


def load():
    """返回 (valid_records, stats_dict)。stats 记录清洗情况。"""
    stats = {"total": 0, "unreadable": 0, "invalid": 0, "valid": 0}
    recs = []
    if not os.path.exists(RESULTS):
        sys.exit(f"missing {RESULTS}")
    with open(RESULTS, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            stats["total"] += 1
            try:
                r = json.loads(line)
            except Exception:
                stats["unreadable"] += 1
                continue
            if r.get("valid") is not True:
                stats["invalid"] += 1
                continue
            try:
                total = float(r["total_seconds"])
                cfg = r["config"]
                dls = {k: float(r["downloads"][k]) for k in FILES}
                dirs = tuple(norm_spec(cfg.get(str(i), cfg.get(i, ""))) for i in range(1, 7))
            except (KeyError, TypeError, ValueError):
                stats["unreadable"] += 1
                continue
            recs.append({"tag": r.get("tag", "?"), "at": r.get("at", ""),
                         "total": total, "dirs": dirs, "dls": dls,
                         "note": r.get("note", "")})
            stats["valid"] += 1
    return recs, stats


def family_label(dirs):
    uniq = []
    for d in dirs:
        if d not in uniq:
            uniq.append(d)
    if len(uniq) == 1:
        return uniq[0]
    return "混搭: " + " ‖ ".join(uniq)


def fmt(x, nd=2):
    return f"{x:.{nd}f}"


def group_stats(recs):
    """按 6 目录配置元组分组。"""
    g = defaultdict(list)
    for r in recs:
        g[r["dirs"]].append(r)
    rows = []
    for dirs, rs in g.items():
        totals = [r["total"] for r in rs]
        row = {
            "dirs": dirs,
            "label": family_label(dirs),
            "n": len(rs),
            "mean": mean(totals),
            "std": pstdev(totals) if len(totals) > 1 else 0.0,
            "min": min(totals),
            "max": max(totals),
            "median": median(totals),
            "tags": sorted({r["tag"] for r in rs}),
            "per_file": {f: [r["dls"][f] for r in rs] for f in FILES},
        }
        rows.append(row)
    rows.sort(key=lambda x: x["mean"])
    return rows


def welch(a, b):
    """Welch t 检验: 返回 (t, df, p_two_sided)。优先 scipy, 否则正态近似。"""
    n1, n2 = len(a), len(b)
    if n1 < 2 or n2 < 2:
        return None
    m1, m2 = mean(a), mean(b)
    v1, v2 = pstdev(a) ** 2, pstdev(b) ** 2
    se2 = v1 / n1 + v2 / n2
    if se2 == 0:
        return (0.0, 1, 1.0) if m1 == m2 else (math.inf, 1, 0.0)
    t = (m1 - m2) / math.sqrt(se2)
    df = se2 ** 2 / ((v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1))
    try:
        from scipy import stats as _s
        p = 2 * _s.t.sf(abs(t), df)
    except Exception:
        p = math.erfc(abs(t) / math.sqrt(2))  # 正态近似
    return t, df, p


def sig_mark(p):
    if p is None:
        return "样本不足"
    if p < 0.01:
        return "**显著 (p<0.01)**"
    if p < 0.05:
        return "**显著 (p<0.05)**"
    return f"不显著 (p={p:.2f})"


def main():
    recs, stats = load()
    rows = group_stats(recs)
    if not recs:
        sys.exit("no valid records")

    L = []
    A = L.append
    A("# 实验结果统计分析（自动生成）")
    A("")
    A(f"- 生成：`python tools/config_stats.py`（可重复运行，整体覆盖本文件第 1-4 节）")
    A(f"- 数据源：`runs/results.jsonl`")
    A("")
    A("<!-- AUTOGEN:BEGIN 由 tools/config_stats.py 生成/覆盖，勿手改此行到 END 之间 -->")
    A("")

    # ---- 1. 数据清洗 ----
    A("## 1. 数据清洗说明")
    A("")
    A(f"- 记录总数 **{stats['total']}**；剔除 `valid=false/非 true` **{stats['invalid']}** 条"
      f"（下载失败/被判定无效，如 CRLF 假成功的 80 s 类与 10.00 s 钳位类）；")
    A(f"- 字段读不通（缺 total_seconds/downloads/config 等）**{stats['unreadable']}** 条，跳过并计数；")
    A(f"- 保留有效记录 **{stats['valid']}** 条。")
    A("- 同一配置的重复运行合并为一族：先按文档默认值归一化"
      "（剔除与默认值相同的参数，如 `enable_n_in_flight=1`、`leak_interval_us=1000`），"
      "再按 6 个目录的实际配置元组合并（不同 tag、相同有效配置 → 同族）。")
    A("- 分组键 = `1..6` 目录配置元组；混搭配置按「出现过的去重规格」标注。")
    A("")

    # ---- 2. 家族总表 ----
    A("## 2. 按配置族分组统计（总耗时，按 mean 升序）")
    A("")
    A("| # | 配置族 | n | mean | std | min | max | median | 备注 | tags |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        note = "样本不足" if r["n"] < 3 else ""
        A(f"| {i} | `{r['label']}` | {r['n']} | {fmt(r['mean'])} | {fmt(r['std'])} "
          f"| {fmt(r['min'])} | {fmt(r['max'])} | {fmt(r['median'])} | {note} "
          f"| {', '.join(r['tags'][:4])}{'…' if len(r['tags']) > 4 else ''} |")
    A("")
    A("> n<3 的族标注「样本不足」，其排名仅为点估计，不可作为优劣依据。")
    A("")

    # ---- 3. 分文件位置 ----
    A("## 3. 按文件位置的统计（mean ± std，秒）")
    A("")
    # 只展示 n>=2 的族 + n=1 但进过前 10 的族, 避免表爆炸; 全量见上表
    shown = [r for r in rows if r["n"] >= 2] or rows[:10]
    hdr = "| 配置族 | n | " + " | ".join(f"{f}" for f in FILES) + " |"
    A(hdr)
    A("|---" * 8 + "|")
    for r in shown:
        cells = []
        for f in FILES:
            v = r["per_file"][f]
            if len(v) >= 2:
                cells.append(f"{fmt(mean(v))} ± {fmt(pstdev(v))}")
            else:
                cells.append(f"{fmt(v[0])} (n=1)")
        A(f"| `{r['label'][:60]}` | {r['n']} | " + " | ".join(cells) + " |")
    A("")
    # 每个位置的最优族 (优先 n>=2, 其次 n=1 但标注)
    A("### 每个位置的最优配置族")
    A("")
    A("| 位置 | 最优族 (n≥2 优先) | mean±std | 次优 | 是否显著优于次优 |")
    A("|---|---|---|---|---|")
    for idx, f in enumerate(FILES):
        cands = sorted(rows, key=lambda r: mean(r["per_file"][f]))
        c2 = [r for r in cands if r["n"] >= 2] or cands
        best = c2[0]
        runner = next((r for r in c2[1:] if r["label"] != best["label"]), None)
        bv = best["per_file"][f]
        bcell = (f"{fmt(mean(bv))} ± {fmt(pstdev(bv))}" if len(bv) >= 2 else f"{fmt(bv[0])} (n=1)")
        if runner:
            rv = runner["per_file"][f]
            w = welch(bv, rv)
            sig = sig_mark(w[2]) if w else "样本不足，无法检验"
            rcell = f"`{runner['label'][:40]}` ({fmt(mean(rv))}, n={runner['n']})"
        else:
            sig, rcell = "—", "—"
        A(f"| {f} | `{best['label'][:44]}` (n={best['n']}) | {bcell} | {rcell} | {sig} |")
    A("")

    # ---- 4. 显著性 ----
    A("## 4. 差距是否显著（Welch t 检验，双侧）")
    A("")
    testable = [r for r in rows if r["n"] >= 2][:3]
    all_top = rows[:3]
    top_desc = "；".join("`%s`(%s,n=%d)" % (r["label"][:36], fmt(r["mean"]), r["n"]) for r in all_top)
    A("- 总榜前 3（按 mean）：" + top_desc)
    A("- 其中 n≥2、可做检验的前 3 族进入两两比较：")
    A("")
    if len(testable) >= 2:
        A("| 对比 | Δmean (s) | t | df | p | 结论 |")
        A("|---|---|---|---|---|---|")
        for i in range(len(testable)):
            for j in range(i + 1, len(testable)):
                a, b = testable[i], testable[j]
                av = [r["total"] for r in recs if r["dirs"] == a["dirs"]]
                bv = [r["total"] for r in recs if r["dirs"] == b["dirs"]]
                w = welch(av, bv)
                if w is None:
                    A(f"| {a['label'][:30]} vs {b['label'][:30]} | {fmt(a['mean']-b['mean'])} "
                      f"| — | — | — | 样本不足 |")
                    continue
                t, df, p = w
                A(f"| `{a['label'][:30]}` vs `{b['label'][:30]}` | {fmt(a['mean']-b['mean'])} "
                  f"| {t:.2f} | {df:.1f} | {p:.3f} | {sig_mark(p)} |")
        A("")
    A("**必须写明的不显著/不可检验对比**：")
    A("")
    # 明确列出哪些看似好的对比其实不显著
    lines = []
    for i, r in enumerate(rows):
        if r["n"] >= 3 and i < 8:
            lines.append(f"- `{r['label'][:50]}` (n={r['n']}, {fmt(r['mean'])}±{fmt(r['std'])})")
    A("\n".join(lines) if lines else "- （无 n≥3 的前排族）")
    A("")
    n1_leaders = [r for r in rows[:10] if r["n"] < 3]
    if n1_leaders:
        A("以下前排族 **n<3，样本不足，与任何族的差异都无法声称显著**"
          "（点估计领先完全可能来自背景流量随机性）：")
        A("")
        for r in n1_leaders:
            A(f"- `{r['label'][:60]}` (n={r['n']}, {fmt(r['mean'])})")
        A("")
    A("解释：单配置 std 约 6–12 s，族间均值差 <10 s 的对比基本落在噪声内；"
      "只有 Δmean 明显大于合并标准误的对比才可信。")
    A("")
    A("<!-- AUTOGEN:END -->")
    A("")

    md = "\n".join(L)
    # 若人工第 5-7 节已存在, 保留之
    if os.path.exists(OUT_MD):
        old = open(OUT_MD, encoding="utf-8").read()
        m = re.search(r"<!-- AUTOGEN:END -->\s*(.*)$", old, re.S)
        if m and m.group(1).strip():
            md = md + "\n" + m.group(1).rstrip() + "\n"
        elif not re.search(r"<!-- AUTOGEN:BEGIN", old):
            md = md + "\n" + old  # 旧文件无标记 → 全量替换, 不拼接
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(md)
    print(f"[ok] records total={stats['total']} valid={stats['valid']} "
          f"invalid={stats['invalid']} unreadable={stats['unreadable']} "
          f"families={len(rows)} -> {OUT_MD}")


if __name__ == "__main__":
    main()
