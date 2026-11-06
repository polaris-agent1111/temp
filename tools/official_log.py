#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""官方成绩台账：把榜单 attempts 与我方 submissions 配对，落盘成一张「配置 → 官方成绩」表。

用途：官方评测对同一配置近似确定，所以每投一次就是一个「配置 × 官方环境」的观测点。
本脚本把观测点整理成表，用来回答「哪个配置族在官方环境最好」。

用法：
  python tools/official_log.py            # 拉榜单、配对、写 runs/official_results.jsonl、打印表
  python tools/official_log.py --cached   # 只用已有快照（榜单站挂了时）
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
SUBMISSIONS = ROOT / "runs" / "submissions.jsonl"
OUT = ROOT / "runs" / "official_results.jsonl"
RAW_DIR = ROOT / "intel" / "raw"
BOARD_URL = "http://47.120.64.152:5000/api/leaderboard"
TEAM = "赛博coder"


def norm_time(text: str) -> str:
    """把各种时间写法归一成 'YYYY-MM-DD HH:MM'（只到分钟）。"""
    text = str(text).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            return dt.datetime.strptime(text[:len(dt.datetime.now().strftime(fmt))], fmt).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            continue
    try:  # 2026-11-05T13:25:18+0800
        return dt.datetime.strptime(text, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return text[:16].replace("T", " ")


def load_submissions() -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not SUBMISSIONS.exists():
        return out
    for line in SUBMISSIONS.read_text("utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("status") != "submitted":
            continue
        out[norm_time(rec.get("at", ""))] = rec
    return out


def fetch_board(cached: bool) -> dict | None:
    if not cached:
        try:
            r = requests.get(BOARD_URL, timeout=20)
            if r.status_code == 200 and r.text.strip().startswith("{"):
                RAW_DIR.mkdir(parents=True, exist_ok=True)
                stamp = dt.datetime.now().strftime("%Y%m%dT%H%M")
                (RAW_DIR / f"leaderboard_{stamp}.json").write_text(r.text, encoding="utf-8")
                return r.json()
            print(f"[warn] 榜单站返回 {r.status_code}，尝试用已有快照")
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] 拉榜单失败：{type(exc).__name__}，尝试用已有快照")
    snaps = sorted(RAW_DIR.glob("leaderboard_*.json"))
    for path in reversed(snaps):
        try:
            data = json.loads(path.read_text("utf-8-sig"))
        except Exception:  # noqa: BLE001
            continue
        for p in (data.get("leaderboard") or {}).get("problems") or []:
            for s in p.get("submissions") or []:
                if s.get("team") == TEAM and s.get("attempts"):
                    print(f"[cached] 用快照 {path.name}")
                    return data
    return None


def attempts_of(data: dict, team: str) -> list[dict]:
    for p in (data.get("leaderboard") or {}).get("problems") or []:
        for s in p.get("submissions") or []:
            if s.get("team") == team:
                return list(s.get("attempts") or [])
    return []


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cached", action="store_true")
    args = ap.parse_args(argv)

    data = fetch_board(args.cached)
    if data is None:
        print("[ERR] 没有可用的榜单数据")
        return 1
    subs = load_submissions()
    atts = attempts_of(data, TEAM)

    def match_sub(when: str) -> dict:
        """按分钟最近匹配（提交记录与服务器时间可能差几秒，甚至跨分钟）。"""
        if when in subs:
            return subs[when]
        try:
            target = dt.datetime.strptime(when, "%Y-%m-%d %H:%M")
        except ValueError:
            return {}
        best, best_gap = {}, None
        for key, rec in subs.items():
            try:
                gap = abs((dt.datetime.strptime(key, "%Y-%m-%d %H:%M") - target).total_seconds())
            except ValueError:
                continue
            if gap <= 120 and (best_gap is None or gap < best_gap):
                best, best_gap = rec, gap
        return best

    rows = []
    for att in atts:
        when = norm_time(att.get("submitted_at", ""))
        rec = match_sub(when)
        rows.append({
            "submitted_at": att.get("submitted_at"),
            "official_seconds": float(att["download_seconds"]),
            "note": rec.get("note", "(未匹配到提交记录)"),
        })
    rows.sort(key=lambda r: r["official_seconds"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"{'官方秒':>9}  {'提交时刻':19}  配置")
    for row in rows:
        print(f"{row['official_seconds']:9.3f}  {row['submitted_at']:19}  {row['note']}")
    print(f"\n共 {len(rows)} 条，已写 {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
