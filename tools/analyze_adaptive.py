"""读取自适应逐发结果 + 本地样本，输出 δ 表与阶段结论。纯读，不碰云主机。

用法: python tools/analyze_adaptive.py [--date 2026-11-06]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "runs" / "results.jsonl"
ADAPTIVE = ROOT / "runs" / "adaptive_log.jsonl"


def norm_cfg(c: dict):
    if not c:
        return None
    try:
        if c.get("pacer_mode") == "leak_bucket" or "leak_rate" in c:
            return ("leak", int(c["leak_rate"]), int(c.get("bucket_cap", -1)), int(c.get("leak_interval_us", -1)))
    except Exception:
        return None
    return None


def local_stats():
    """按 (rate,cap,interval) 聚合本地 valid 样本。"""
    agg = {}
    if not RESULTS.exists():
        return agg
    for line in RESULTS.read_text("utf-8").splitlines():
        try:
            r = json.loads(line)
        except Exception:
            continue
        if not r.get("valid") or not r.get("downloads"):
            continue
        cfg = r.get("config") or {}
        vals = {json.dumps(v, sort_keys=True) for v in cfg.values()} if cfg else set()
        if len(vals) != 1:
            continue
        c = norm_cfg(next(iter(cfg.values())))
        if not c:
            continue
        agg.setdefault(c, []).append(float(r["total_seconds"]))
    return agg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    args = ap.parse_args()

    events = []
    if ADAPTIVE.exists():
        for line in ADAPTIVE.read_text("utf-8").splitlines():
            try:
                events.append(json.loads(line))
            except Exception:
                continue
    if args.date:
        events = [e for e in events if e.get("ts", "").startswith(args.date)]

    scored = [e for e in events if e.get("event") == "scored"]
    if not scored:
        print("暂无已出分的自适应记录（可先跑 tools/official_log.py 或等出分）")
        return 0

    loc = local_stats()
    print(f"{'slot':>4} {'config':<22} {'official':>9} {'local_mean':>10} {'n':>3} {'delta':>8}")
    deltas = []
    for e in scored:
        c = e["cfg"]
        key = ("leak", int(c["leak_rate"]), int(c["bucket_cap"]), int(c["leak_interval_us"]))
        vals = loc.get(key, [])
        mean = sum(vals) / len(vals) if vals else None
        off = float(e["score"])
        d = (off / mean - 1) * 100 if mean else None
        if d is not None:
            deltas.append(d)
        print(f"{e['slot']:>4} {e['tag']:<22} {off:>9.3f} "
              f"{(f'{mean:.2f}' if mean else '—'):>10} {len(vals):>3} "
              f"{(f'{d:+.1f}%' if d is not None else '—'):>8}")
    if deltas:
        print(f"\nδ: mean={sum(deltas)/len(deltas):+.1f}%  min={min(deltas):+.1f}%  max={max(deltas):+.1f}%")
    best = min(scored, key=lambda e: float(e["score"]))
    print(f"本轮最好: {best['tag']} = {float(best['score']):.3f} s")

    to = [e for e in events if e.get("event") == "timeout"]
    if to:
        print(f"\n超时未取到成绩: {[e.get('tag') for e in to]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
