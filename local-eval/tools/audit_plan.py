#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提交前计划审计：检查本地样本数、方差、min/mean 差距和过拟合话术。

官方按「重复多次取平均」计分，top 提交会统一复测。本工具在提交前回答：
- 这个计划里的配置有没有足够的本地样本？
- 方差是否可控？
- 是否把某次最小值当成了预期？
- note 里是否出现 min-of-N / 极值红利 / 破纪录等过拟合话术？

用法：
  python tools/audit_plan.py --plan runs/submit_plan_1107_wave2_bypass.json
  python tools/audit_plan.py --plan <plan> --results runs/results.jsonl --min-n 3 --max-cv 0.05
  python tools/audit_plan.py --plan <plan> --json

退出码：0=无风险，1=有风险，2=输入错误。
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = ROOT / "runs" / "results.jsonl"
SLOTS = [str(i) for i in range(1, 7)]
INHERIT = "(inherit/default)"
OVERFITTING_WORDS = (
    "min-of-n", "min of n", "best-of-n", "极值红利",
    "历史最高分", "破纪录",
)


def norm_plan_value(value) -> str:
    if value is None:
        return INHERIT
    if not isinstance(value, list) or not value:
        return "<invalid>"
    mode = str(value[0])
    params = value[1] if len(value) > 1 and value[1] else {}
    if not isinstance(params, dict):
        return f"{mode}:<invalid>"
    pairs = [f"{k}={v}" for k, v in sorted(params.items())]
    return f"{mode}:{','.join(pairs)}"


def plan_signature(item: dict) -> tuple:
    if "all" in item:
        raw = {slot: item["all"] for slot in SLOTS}
    else:
        raw = item.get("configs") or {}
        if not isinstance(raw, dict):
            raw = {}
    return tuple(norm_plan_value(raw.get(slot)) for slot in SLOTS)


def norm_result_value(value) -> str:
    if not value or str(value).startswith("(inherit"):
        return INHERIT
    mode, _, body = str(value).partition(":")
    pairs = [part for part in body.split(",") if part]
    return f"{mode}:{','.join(sorted(pairs))}"


def result_signature(rec: dict) -> tuple:
    cfg = rec.get("config") or {}
    if not isinstance(cfg, dict):
        cfg = {}
    return tuple(norm_result_value(cfg.get(slot, INHERIT)) for slot in SLOTS)


def usable(rec: dict) -> bool:
    tag = str(rec.get("tag", "")).lower()
    note = str(rec.get("note", "")).lower()
    if rec.get("valid", True) is False:
        return False
    return not (tag.startswith("load") or "load-" in tag
                or "cpu 争抢" in note or "cpu contention" in note)


def describe(values: list[float]) -> dict | None:
    if not values:
        return None
    n = len(values)
    mean = statistics.mean(values)
    std = statistics.stdev(values) if n > 1 else 0.0
    return {
        "n": n,
        "min": min(values),
        "mean": mean,
        "std": std,
        "cv": std / mean if mean else 0.0,
        "se": std / math.sqrt(n) if n > 1 else 0.0,
    }


def audit(plan: list[dict], records: list[dict], min_n: int, max_cv: float) -> list[dict]:
    if len(plan) > 5:
        plan_flag = ["PLAN_EXCEEDS_DAILY_LIMIT(>5)"]
    else:
        plan_flag = []
    tags = [str(item.get("tag", "")) for item in plan if isinstance(item, dict)]
    dup_tags = {tag for tag in tags if tag and tags.count(tag) > 1}

    by_signature: dict[tuple, list[dict]] = defaultdict(list)
    for rec in records:
        if usable(rec):
            by_signature[result_signature(rec)].append(rec)

    findings = []
    for index, item in enumerate(plan):
        if not isinstance(item, dict):
            findings.append({"tag": f"#{index}", "flags": ["INVALID_PLAN_ITEM"]})
            continue
        tag = str(item.get("tag", f"#{index}"))
        note = str(item.get("note", ""))
        stats = describe([float(r["total_seconds"]) for r in by_signature.get(plan_signature(item), [])
                          if isinstance(r.get("total_seconds"), (int, float))])
        flags = list(plan_flag)
        if tag in dup_tags:
            flags.append("DUPLICATE_TAG")
        if stats is None:
            flags.append("NO_LOCAL_SAMPLE")
        else:
            if stats["n"] < min_n:
                flags.append(f"LOW_N({stats['n']}<{min_n})")
            if stats["cv"] > max_cv:
                flags.append(f"HIGH_CV({stats['cv']:.1%})")
            if stats["mean"] and stats["min"] < stats["mean"] * 0.9:
                flags.append("MIN_FAR_BELOW_MEAN")
        lowered = note.lower()
        for word in OVERFITTING_WORDS:
            if word in lowered:
                flags.append(f"OVERFITTING_LANGUAGE({word})")
                break
        findings.append({"tag": tag, "note": note, "stats": stats, "flags": flags})
    return findings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--results", default=str(DEFAULT_RESULTS))
    ap.add_argument("--min-n", type=int, default=3)
    ap.add_argument("--max-cv", type=float, default=0.05)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    try:
        plan = json.loads(Path(args.plan).read_text("utf-8"))
    except (OSError, ValueError) as exc:
        print(f"[ERROR] 读取 plan 失败: {exc}", file=sys.stderr)
        return 2
    if not isinstance(plan, list):
        print("[ERROR] plan 必须是数组", file=sys.stderr)
        return 2

    records = []
    results = Path(args.results)
    if results.exists():
        for line in results.read_text("utf-8").splitlines():
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except ValueError:
                continue
    else:
        print(f"[WARN] 本地结果不存在: {results}；所有配置都会标记 NO_LOCAL_SAMPLE")

    findings = audit(plan, records, args.min_n, args.max_cv)
    risky = [f for f in findings if f["flags"]]

    if args.json:
        print(json.dumps(findings, ensure_ascii=False, indent=1))
    else:
        print(f"{'tag':<40} {'n':>3} {'mean':>8} {'std':>7} {'CV':>7} {'min':>8}  flags")
        print("-" * 100)
        for finding in findings:
            stats = finding.get("stats")
            if stats:
                cells = (f"{stats['n']:>3} {stats['mean']:>8.3f} {stats['std']:>7.2f} "
                         f"{stats['cv']:>6.1%} {stats['min']:>8.3f}")
            else:
                cells = f"{'-':>3} {'-':>8} {'-':>7} {'-':>7} {'-':>8}"
            print(f"{finding['tag']:<40} {cells}  {'; '.join(finding['flags']) or 'OK'}")
        print()
        if risky:
            print(f"[RISK] {len(risky)}/{len(findings)} 个配置未过门禁；先补样本或修正说明再提交")
        else:
            print("[OK] 计划通过门禁；仍需人工确认每日额度与官方复测口径")

    return 1 if risky else 0


if __name__ == "__main__":
    raise SystemExit(main())
