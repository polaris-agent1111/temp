#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统计 Hybrid 混合构型实验数据并生成选型报告。

官方口径是「重复多次取平均」，且 top 提交会统一复测。因此本报告：
- 过滤 valid=false 和 load-* 污染样本；
- 按均值排序，而不是按最小值排序；
- 同时给出 min / median / mean / std / CV / 95% CI；
- 把「最小值远低于均值」标成疑似尖点，不当作可预期成绩。
"""
from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = ROOT / "runs" / "results.jsonl"
DEFAULT_OUT = ROOT / "docs" / "analysis" / "hybrid-statistical-summary.md"

# 95% t 临界值（双尾），df 超出表范围时用正态近似。
T95 = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
    6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
    11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131,
    16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
    21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060,
    26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042,
}


def is_valid(rec: dict) -> bool:
    return rec.get("valid", True) is not False


def is_contaminated(rec: dict) -> bool:
    tag = str(rec.get("tag", "")).lower()
    note = str(rec.get("note", "")).lower()
    return (tag.startswith("load") or "load-" in tag
            or "cpu 争抢" in note or "cpu contention" in note)


def usable(rec: dict) -> bool:
    return is_valid(rec) and not is_contaminated(rec)


def base_tag(tag: str) -> str:
    return re.sub(r"-r\d+$", "", str(tag))


def t95(n: int) -> float:
    if n <= 1:
        return float("nan")
    return T95.get(n - 1, 1.96)


def describe(values: list[float]) -> dict:
    n = len(values)
    if n == 0:
        return {"n": 0, "min": 0.0, "median": 0.0, "mean": 0.0, "max": 0.0,
                "std": 0.0, "se": 0.0, "ci": 0.0, "cv": 0.0}
    mean = statistics.mean(values)
    std = statistics.stdev(values) if n > 1 else 0.0
    se = std / math.sqrt(n) if n > 1 else 0.0
    return {
        "n": n,
        "min": min(values),
        "median": statistics.median(values),
        "mean": mean,
        "max": max(values),
        "std": std,
        "se": se,
        "ci": t95(n) * se if n > 1 else 0.0,
        "cv": std / mean if mean else 0.0,
    }


def segment_stats(items: list[dict]) -> dict:
    one_to_four, five, six = [], [], []
    for rec in items:
        dl = rec.get("downloads") or {}
        if all(f"{i}.bin" in dl for i in range(1, 5)):
            one_to_four.append(sum(float(dl[f"{i}.bin"]) for i in range(1, 5)))
        if "5.bin" in dl:
            five.append(float(dl["5.bin"]))
        if "6.bin" in dl:
            six.append(float(dl["6.bin"]))

    def pair(values: list[float]) -> str:
        if not values:
            return "-"
        return f"{min(values):.2f}s ({statistics.mean(values):.2f}s)"

    return {
        "one_to_four": pair(one_to_four),
        "five": pair(five),
        "six": pair(six),
        "min_one_to_four": min(one_to_four) if one_to_four else None,
        "min_five": min(five) if five else None,
        "min_six": min(six) if six else None,
    }


def group_records(records: list[dict]) -> tuple[dict[str, list[dict]], int, int]:
    groups: dict[str, list[dict]] = {}
    invalid = 0
    contaminated = 0
    for rec in records:
        tag = str(rec.get("tag", ""))
        if "hybrid" not in tag.lower() and "champ" not in tag.lower():
            continue
        if not is_valid(rec):
            invalid += 1
            continue
        if is_contaminated(rec):
            contaminated += 1
            continue
        groups.setdefault(base_tag(tag), []).append(rec)
    return groups, invalid, contaminated


def row_for(base: str, items: list[dict], min_n: int, max_cv: float) -> dict:
    totals = [float(r["total_seconds"]) for r in items
              if isinstance(r.get("total_seconds"), (int, float))]
    stats = describe(totals)
    seg = segment_stats(items)
    flags = []
    if stats["n"] < min_n:
        flags.append(f"LOW_N({stats['n']}<{min_n})")
    if stats["cv"] > max_cv:
        flags.append(f"HIGH_CV({stats['cv']:.1%})")
    if stats["mean"] and stats["min"] < stats["mean"] * 0.9:
        flags.append("MIN_FAR_BELOW_MEAN")
    return {
        "base": base,
        "note": str(items[0].get("note", ""))[:40],
        **stats,
        **seg,
        "flags": flags,
    }


def md_escape(text: str) -> str:
    return (text.replace("|", "&#124;").replace("\n", " ")
            .replace("\r", " ").replace("`", "&#96;"))


def render(rows: list[dict], total_records: int, invalid: int,
           contaminated: int, min_n: int, max_cv: float) -> str:
    rows = sorted(rows, key=lambda r: r["mean"])
    lines = [
        "# Hybrid 混合构型统计总览与选型口径",
        "",
        f"> **数据源**：`runs/results.jsonl` ｜ **候选构型**：{len(rows)} 种 ｜ "
        f"**原始场次**：{total_records} ｜ **排除 invalid**：{invalid} ｜ **排除 load**：{contaminated}",
        "> **口径**：官方按「重复多次取平均」计分，top 提交会统一复测。"
        "本表按**均值**排序；`Min` 只是本地单场最好，**不是官方预期**。",
        "",
        "## 一、各构型统计（按均值升序）",
        "",
        "| 构型 (Base Tag) | n | Min | Median | **Mean** | Std | CV | 95% CI | 1~4.bin Min (Mean) | 5.bin Min (Mean) | 6.bin Min (Mean) | 状态 |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|---|---|---|",
    ]
    for r in rows:
        status = "OK" if not r["flags"] else "; ".join(r["flags"])
        ci = f"±{r['ci']:.2f}s" if r["n"] > 1 else "-"
        lines.append(
            f"| `{md_escape(r['base'])}` | {r['n']} | **{r['min']:.3f}s** | {r['median']:.3f}s | "
            f"**{r['mean']:.3f}s** | {r['std']:.2f}s | {r['cv']:.1%} | {ci} | "
            f"{r['one_to_four']} | {r['five']} | {r['six']} | {status} |"
        )

    flagged = [r for r in rows if r["flags"]]
    lines += ["", "## 二、选型提示", ""]
    if flagged:
        lines.append("以下构型在官方复测口径下证据不足，不建议直接作为主推：")
        for r in flagged:
            lines.append(f"- `{md_escape(r['base'])}`：{'; '.join(r['flags'])}")
    else:
        lines.append("当前构型均满足最低样本与方差门槛；仍需补足 n≥8–10 后再定主推。")

    lines += [
        "",
        "## 三、跨构型理论下界（不是单次可达成绩）",
        "",
    ]
    min_1_4 = min((r["min_one_to_four"] for r in rows if r["min_one_to_four"] is not None), default=None)
    min_5 = min((r["min_five"] for r in rows if r["min_five"] is not None), default=None)
    min_6 = min((r["min_six"] for r in rows if r["min_six"] is not None), default=None)
    if None not in (min_1_4, min_5, min_6):
        envelope = min_1_4 + min_5 + min_6
        lines += [
            f"- 1~4.bin 跨构型最小：`{min_1_4:.3f}s`",
            f"- 5.bin 跨构型最小：`{min_5:.3f}s`",
            f"- 6.bin 跨构型最小：`{min_6:.3f}s`",
            f"- 合成下界：**{envelope:.3f}s**",
            "",
            "这三项来自不同构型的不同单场，合成值只是理论下界，不能写成冲冠目标或官方预期。",
        ]
    else:
        lines.append("数据不足，无法合成跨构型下界。")

    lines += [
        "",
        "## 四、选型门槛",
        "",
        f"- 候选：n≥{min_n}，报告 mean/median/std/CV；不足 {min_n} 次只记为探索点。",
        f"- 主推：n≥8–10，CV≤{max_cv:.0%}，均值相对锚点有明确优势，且邻域扰动仍稳定。",
        "- 禁止 min-of-N / 极值红利；重复实验用于估计方差，不是抽低分。",
        "- 本地与官方分开陈述：`local_best`、`local_mean`、`official_score` 不得混用。",
        "",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(DEFAULT_RESULTS))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--min-n", type=int, default=3)
    ap.add_argument("--max-cv", type=float, default=0.05)
    args = ap.parse_args(argv)

    results = Path(args.results)
    if not results.exists():
        print(f"Results file not found: {results}")
        return 1

    records = []
    for line in results.read_text("utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except ValueError:
            continue

    groups, invalid, contaminated = group_records(records)
    rows = [row_for(base, items, args.min_n, args.max_cv) for base, items in groups.items()]
    if not rows:
        print("没有可用的 hybrid/champ 有效样本")
        return 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(rows, len(records), invalid, contaminated, args.min_n, args.max_cv),
                   encoding="utf-8")
    print(f"Generated {out} ({len(rows)} 构型, 排除 invalid={invalid}, load={contaminated})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
