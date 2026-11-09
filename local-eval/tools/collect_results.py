#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""汇总本地官方评测结果（evaluation_results.json / result.json）。

官方评测器每次运行输出一个 result.json：
  {"question": [{"timestamp": "...", "total_seconds": 122.046,
                 "downloads": [{"order": 1, "filename": "1.bin", "seconds": 4.0}, ...]}]}

本脚本扫描一个目录下的所有 result.json，按“评测 tag”分组，输出：
  n / mean / std / min / max / 分文件平均耗时 / 有效速率
纯标准库，不依赖 runs/results.jsonl。

用法：
  python3 tools/collect_results.py --evals-dir evals
  python3 tools/collect_results.py --evals-dir evals --json
  python3 tools/collect_results.py --evals-dir evals --min-n 3
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

SIZES_MB = {"1.bin": 10, "2.bin": 20, "3.bin": 40,
            "4.bin": 80, "5.bin": 160, "6.bin": 320}
FLOOR = 50.4  # 630 MB @ 100 Mbps 的理论下限（秒）


def load_result(path: Path) -> list[dict]:
    data = json.loads(path.read_text("utf-8"))
    if isinstance(data, dict):
        runs = data.get("question") or data.get("runs") or []
    elif isinstance(data, list):
        runs = data
    else:
        runs = []
    out = []
    for r in runs:
        if not isinstance(r, dict):
            continue
        total = r.get("total_seconds")
        if total is None:
            continue
        downloads = {}
        for d in r.get("downloads") or []:
            fn = d.get("filename")
            sec = d.get("seconds")
            if fn and sec is not None:
                downloads[fn] = float(sec)
        out.append({
            "timestamp": r.get("timestamp", ""),
            "total_seconds": float(total),
            "downloads": downloads,
        })
    return out


def tag_of(path: Path, root: Path) -> str:
    """result.json 的 tag：run-* 子目录归并到父目录。"""
    parent = path.parent
    if parent.name.startswith("run-") and parent.parent != root:
        return parent.parent.name
    rel = parent.relative_to(root)
    return str(rel) if str(rel) != "." else root.name


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="汇总本地官方评测 result.json")
    ap.add_argument("--evals-dir", default="evals",
                    help="评测结果根目录（默认 ./evals）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--min-n", type=int, default=1, help="只显示样本数 >= N 的 tag")
    args = ap.parse_args(argv)

    root = Path(args.evals_dir).resolve()
    if not root.is_dir():
        print(f"目录不存在: {root}", file=sys.stderr)
        print("提示：官方评测器用 --output-dir 指定输出目录；"
              "本工具扫描其下的 result.json。", file=sys.stderr)
        return 2

    groups: dict[str, list[dict]] = defaultdict(list)
    for path in sorted(root.rglob("result.json")):
        try:
            runs = load_result(path)
        except (ValueError, OSError) as e:
            print(f"[skip] {path}: {e}", file=sys.stderr)
            continue
        if not runs:
            continue
        groups[tag_of(path, root)].extend(runs)

    rows = []
    for tag, runs in groups.items():
        totals = [r["total_seconds"] for r in runs]
        per_file = defaultdict(list)
        for r in runs:
            for fn, sec in r["downloads"].items():
                per_file[fn].append(sec)
        rows.append({
            "tag": tag,
            "n": len(totals),
            "mean": statistics.mean(totals),
            "std": statistics.stdev(totals) if len(totals) > 1 else 0.0,
            "min": min(totals),
            "max": max(totals),
            "invalid": sum(1 for t in totals if t < FLOOR),
            "per_file": {fn: statistics.mean(v) for fn, v in per_file.items()},
        })
    rows = [r for r in rows if r["n"] >= args.min_n]
    rows.sort(key=lambda r: r["mean"])

    if not rows:
        if groups:
            print(f"在 {root} 下找到 {len(groups)} 个 tag，但没有样本数 >= {args.min_n} 的 tag")
            print("提示：本地单次评测每个 tag 通常只有 1 个 result.json；"
                  "想看单次结果请用 --min-n 1。")
        else:
            print(f"在 {root} 下没有找到可用的 result.json")
        return 1

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    print(f"评测根目录: {root}")
    print(f"共 {sum(r['n'] for r in rows)} 次运行，{len(rows)} 个 tag\n")
    header = f"{'tag':<44}{'n':>3}{'均值':>10}{'标准差':>9}{'最快':>9}{'最慢':>9}{'无效':>5}"
    print(header)
    print("-" * len(header))
    for r in rows:
        print(f"{r['tag'][:42]:<44}{r['n']:>3}{r['mean']:>10.3f}"
              f"{r['std']:>9.3f}{r['min']:>9.3f}{r['max']:>9.3f}{r['invalid']:>5}")

    print("\n分文件平均耗时（秒）与有效速率（Mbps）：")
    files = [f"{i}.bin" for i in range(1, 7)]
    print(f"{'tag':<36}" + "".join(f"{f:>13}" for f in files))
    for r in rows:
        cells = []
        for f in files:
            sec = r["per_file"].get(f)
            cells.append(f"{sec:5.1f}s/{SIZES_MB[f] * 8 / sec:4.0f}" if sec else "-")
        print(f"{r['tag'][:34]:<36}" + "".join(f"{c:>13}" for c in cells))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
