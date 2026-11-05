#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 runs/results.jsonl 生成实验结果汇总（markdown），供技术报告使用。"""
from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "runs" / "results.jsonl"
OUT = ROOT / "report" / "实验结果-数据表.md"
SIZES = {"1.bin": 10, "2.bin": 20, "3.bin": 40, "4.bin": 80, "5.bin": 160, "6.bin": 320}


def key(rec: dict) -> str:
    cfg = rec.get("config") or {}
    vals = [v for v in cfg.values() if v and not v.startswith("(inherit")]
    if not vals:
        return "(空配置/默认)"
    uniq = sorted(set(vals))
    return uniq[0] if len(uniq) == 1 else "混搭:" + " | ".join(uniq)


def main() -> int:
    recs = [json.loads(l) for l in RESULTS.read_text("utf-8").splitlines() if l.strip()]
    recs = [r for r in recs if r.get("valid", True)]
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in recs:
        groups[key(r)].append(r)

    rows = []
    for k, items in groups.items():
        totals = [i["total_seconds"] for i in items]
        per = defaultdict(list)
        for it in items:
            for f, s in (it.get("downloads") or {}).items():
                per[f].append(s)
        rows.append({
            "cfg": k, "n": len(items), "mean": statistics.mean(totals),
            "std": statistics.stdev(totals) if len(totals) > 1 else 0.0,
            "min": min(totals), "max": max(totals),
            "per": {f: statistics.mean(v) for f, v in per.items()},
        })
    rows.sort(key=lambda r: r["mean"])

    lines = ["# 实验结果数据表（自动生成）", "",
             f"- 数据来源：`runs/results.jsonl`，有效评测 {len(recs)} 次，配置 {len(rows)} 种",
             "- 说明：每次评测 = 本地 `competition_question1` 跑一遍完整场景（6 文件顺序下载，含背景流量）",
             "", "## 1. 各配置总耗时（按均值升序）", "",
             "| # | 配置 | n | 均值(s) | 标准差 | 最快 | 最慢 |", "|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        lines.append(f"| {i} | `{r['cfg']}` | {r['n']} | **{r['mean']:.2f}** | {r['std']:.2f} | {r['min']:.2f} | {r['max']:.2f} |")

    lines += ["", "## 2. 分文件平均耗时（秒 / 有效速率 Mbps）", ""]
    header = "| 配置 | " + " | ".join(f"{f}" for f in SIZES) + " | 合计 |"
    lines += [header, "|" + "---|" * (len(SIZES) + 2)]
    for r in rows[:12]:
        cells = []
        for f in SIZES:
            s = r["per"].get(f)
            cells.append(f"{s:.2f} / {SIZES[f]*8/s:.0f}" if s else "-")
        lines.append(f"| `{r['cfg']}` | " + " | ".join(cells) + f" | {r['mean']:.2f} |")

    lines += ["", "## 3. 理论下界参考", "",
              "| 文件 | 大小 | 100Mbps 全速 | 50Mbps 公平份额 |", "|---|---|---|---|"]
    for f, mb in SIZES.items():
        lines.append(f"| {f} | {mb} MB | {mb*8/100:.1f} s | {mb*8/50:.1f} s |")
    lines.append(f"| 合计 | 630 MB | {630*8/100:.1f} s | {630*8/50:.1f} s |")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", "utf-8")
    print(f"[OK] {OUT}")
    print("\n".join(lines[:20]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
