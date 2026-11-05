#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""汇总 runs/results.jsonl：按配置分组统计（均值/标准差），并给出与基线的对比。"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "runs" / "results.jsonl"
SIZES_MB = {"1.bin": 10, "2.bin": 20, "3.bin": 40, "4.bin": 80, "5.bin": 160, "6.bin": 320}


def load() -> list[dict]:
    if not RESULTS.exists():
        return []
    out = []
    for line in RESULTS.read_text("utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def group_key(rec: dict) -> str:
    cfg = rec.get("config") or {}
    vals = [v for v in cfg.values() if v and not v.startswith("(inherit")]
    if not vals:
        return "(baseline/default)"
    uniq = sorted(set(vals))
    return uniq[0] if len(uniq) == 1 else "mixed:" + "|".join(uniq)[:80]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--tag", nargs="*", help="只看这些 tag")
    ap.add_argument("--include-invalid", action="store_true", help="包含无效跑")
    args = ap.parse_args()

    recs = load()
    if args.tag:
        recs = [r for r in recs if r["tag"] in args.tag]
    # 默认只看有效跑
    if not args.include_invalid:
        recs = [r for r in recs if r.get("valid", True)]
    if not recs:
        print("暂无结果")
        return 0

    groups: dict[str, list[dict]] = defaultdict(list)
    for r in recs:
        groups[group_key(r)].append(r)

    rows = []
    for key, items in groups.items():
        totals = [i["total_seconds"] for i in items]
        per_file = defaultdict(list)
        for it in items:
            for fn, sec in (it.get("downloads") or {}).items():
                per_file[fn].append(sec)
        rows.append({
            "config": key,
            "n": len(items),
            "mean": statistics.mean(totals),
            "std": statistics.stdev(totals) if len(totals) > 1 else 0.0,
            "min": min(totals),
            "max": max(totals),
            "per_file": {fn: statistics.mean(v) for fn, v in per_file.items()},
        })
    rows.sort(key=lambda r: r["mean"])

    base = next((r for r in rows if r["config"].startswith("(baseline")), None)
    base_mean = base["mean"] if base else None

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return 0

    print(f"共 {len(recs)} 次评测，{len(rows)} 种配置\n")
    header = f"{'配置':<58}{'n':>2}{'均值':>9}{'标准差':>8}{'最快':>9}{'vs基线':>9}"
    print(header)
    print("-" * len(header))
    for r in rows:
        delta = f"{(r['mean'] - base_mean) / base_mean * 100:+.1f}%" if base_mean else "-"
        print(f"{r['config'][:56]:<58}{r['n']:>2}{r['mean']:>9.2f}{r['std']:>8.2f}{r['min']:>9.2f}{delta:>9}")

    print("\n分文件平均耗时（秒）与有效速率（Mbps）：")
    files = [f"{i}.bin" for i in range(1, 7)]
    print(f"{'配置':<40}" + "".join(f"{f:>13}" for f in files))
    for r in rows:
        cells = []
        for f in files:
            sec = r["per_file"].get(f)
            if sec:
                mbps = SIZES_MB[f] * 8 / sec
                cells.append(f"{sec:5.1f}s/{mbps:4.0f}")
            else:
                cells.append("-")
        print(f"{r['config'][:38]:<40}" + "".join(f"{c:>13}" for c in cells))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
