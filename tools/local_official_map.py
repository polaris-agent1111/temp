#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""local_official_map.py — 本地评测 ↔ 官方成绩映射分析（纯分析，只读）

数据源（全部只读，不写 runs/ 任何文件）:
  runs/results.jsonl           本地评测记录（tag/valid/total_seconds/config/downloads）
  runs/submissions.jsonl       提交台账（at/date/note/status）
  runs/official_results.jsonl  本地留存的官方成绩（submitted_at/official_seconds/note）
  GET http://47.120.64.152:5000/api/leaderboard
                               官方榜单（team=赛博coder 的 attempts[]）；
                               API 打不开时打印警告并降级为只用本地文件历史点。

模型（自己实现最小二乘，不用 sklearn）:
  M0: 官方 = 本地 + c
  M1: 官方 = a*本地 + b
  M2: 官方 = a*本地 + b + c*rate
       rate 取配置原始 rate 参数：leak_bucket→leak_rate，token_bucket→token_refill_rate

拟合集:
  S_all   全部已配对官方点（含 1ms 陷阱 bug 点，仅作对照展示）
  S_clean 剔除配置 bug（leak_interval_us < 4000，官方 4ms 粒度下失效）
  S_noano S_clean 再剔除异常放大点（|δ| ≥ 10%）

用法:
  python tools/local_official_map.py                      # 打印全部分析
  python tools/local_official_map.py --predict 30,50,5000 # 该配置官方预测 + 80% 区间
  python tools/local_official_map.py --offline            # 跳过 API，只用本地文件

退出码: 0（含数据缺失时的优雅退出）；仅标准库（API 用 urllib）。
"""

import argparse
import json
import math
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from statistics import mean, pstdev

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_PATH = os.path.join(ROOT, "runs", "results.jsonl")
SUBS_PATH = os.path.join(ROOT, "runs", "submissions.jsonl")
OFFICIAL_PATH = os.path.join(ROOT, "runs", "official_results.jsonl")
API_URL = "http://47.120.64.152:5000/api/leaderboard"
TEAM = "赛博coder"
MATCH_WINDOW_S = 180          # 提交台账 ↔ 官方成绩 时间窗 ±3 分钟
ANOMALY_DELTA = 0.10          # |δ| ≥ 10% 视为异常点

MODULES = ("token_bucket", "coarse_grained_rate_based",
           "precise_rate_based", "origin", "leak_bucket")
DEFAULTS = {
    "token_bucket": {"tokens": 20, "burst": 40, "token_refill_rate": 10,
                     "token_refill_interval_us": 100, "enable_n_in_flight": 1},
    "coarse_grained_rate_based": {"max_pacing_rate": 0, "clock_granularity": 1000,
                                  "enable_n_in_flight": 1},
    "precise_rate_based": {"max_pacing_rate": 0, "clock_granularity": 1000,
                           "enable_n_in_flight": 1},
    "origin": {"burst_tokens": 10, "max_pacing_rate": 0, "clock_granularity": 1000},
    "leak_bucket": {"leak_rate": 10, "bucket_cap": 30, "leak_interval_us": 1000},
}

# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------

def load_jsonl(path):
    """读 JSONL；文件不存在或行损坏时跳过。"""
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except (ValueError, TypeError):
                continue
    return out


def parse_dt(s):
    """兼容 '2026-11-05 15:55:45' 与 '2026-11-05T15:25:38+0800'；统一 naive 本地时间。"""
    if not s:
        return None
    s = str(s).strip()
    dt = None
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                dt = datetime.strptime(s[:19], fmt)
                break
            except ValueError:
                continue
    if dt is not None and dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    return dt


def parse_spec(spec):
    """'leak_bucket:leak_rate=30,...' → (mode, params)；解析失败返回 None。"""
    if not spec or ":" not in spec:
        return None
    mode, _, body = spec.partition(":")
    mode = mode.strip()
    params = {}
    if body.strip():
        for kv in body.split(","):
            if "=" not in kv:
                return None
            k, _, v = kv.partition("=")
            try:
                params[k.strip()] = int(v)
            except ValueError:
                return None
    return mode, params


def canon(mode, params):
    """剔除与文档默认值相同的参数 → 可比签名。"""
    d = DEFAULTS.get(mode, {})
    kept = tuple(sorted((k, v) for k, v in params.items()
                        if k not in d or d[k] != v))
    return mode, kept


def fmt_cfg(mode, params):
    if not mode:
        return "（未解析）"
    if not params:
        return f"{mode}:(全默认)"
    body = ",".join(f"{k}={v}" for k, v in sorted(params.items()))
    return f"{mode}:{body}"


# ---------------------------------------------------------------------------
# 配置解析（note 文本 → mode/params）
# ---------------------------------------------------------------------------

def parse_config_from_note(note, prev):
    """从 note 解析 (mode, params, 来源)。解析不出时继承上一条（如「同 v1 重投」）。"""
    if not note:
        return (prev[0], dict(prev[1]), "继承上一条") if prev else (None, None, "未解析")
    mode = next((m for m in MODULES if m in note), None)
    params = None

    if mode == "leak_bucket":
        m = re.search(r"rate(\d+)\s*/\s*cap(\d+)\s*/\s*int(\d+)", note)
        if m:
            params = {"leak_rate": int(m.group(1)), "bucket_cap": int(m.group(2)),
                      "leak_interval_us": int(m.group(3))}
        if params is None:
            m = re.search(r"leak(?:_bucket)?\s+(\d+)\s*/\s*(\d+)\s*/\s*(\d+)", note)
            if m:
                params = {"leak_rate": int(m.group(1)), "bucket_cap": int(m.group(2)),
                          "leak_interval_us": int(m.group(3))}
        if params is None:
            m = re.search(r"leak_rate\s*=\s*(\d+)[,\s]+bucket_cap\s*=\s*(\d+)"
                          r"[,\s]+leak_interval_us\s*=\s*(\d+)", note)
            if m:
                params = {"leak_rate": int(m.group(1)), "bucket_cap": int(m.group(2)),
                          "leak_interval_us": int(m.group(3))}
    elif mode == "token_bucket":
        m = re.search(r"tokens\s*=\s*(\d+)\s*,\s*burst\s*=\s*(\d+)\s*,\s*refill\s*=\s*"
                      r"(\d+)\s*[@/]\s*(\d+)\s*us", note)
        if m:
            params = {"tokens": int(m.group(1)), "burst": int(m.group(2)),
                      "token_refill_rate": int(m.group(3)),
                      "token_refill_interval_us": int(m.group(4))}

    if params is None and mode:
        kv = dict(re.findall(r"([a-z_]+)\s*=\s*(\d+)", note))
        if kv:
            params = {k: int(v) for k, v in kv.items()}

    if mode and params:
        return mode, params, "note解析"
    if prev:
        return prev[0], dict(prev[1]), "继承上一条"
    return None, None, "未解析"


def rate_of(mode, params):
    """M2 的 rate 特征：配置里的原始 rate 参数。"""
    if not params:
        return None
    if mode == "leak_bucket":
        return params.get("leak_rate")
    if mode == "token_bucket":
        return params.get("token_refill_rate")
    return None


# ---------------------------------------------------------------------------
# 本地均值
# ---------------------------------------------------------------------------

def build_local_index(results):
    """(canon签名) → [total_seconds,...]（仅 valid=true 且 6 目录配置一致）。"""
    index = {}
    for r in results:
        if r.get("valid") is not True:
            continue
        cfg = r.get("config") or {}
        dirs = []
        ok = True
        for i in range(1, 7):
            parsed = parse_spec(cfg.get(str(i), ""))
            if not parsed:
                ok = False
                break
            dirs.append(canon(*parsed))
        if not ok or len(set(dirs)) != 1:
            continue
        try:
            index.setdefault(dirs[0], []).append(float(r["total_seconds"]))
        except (TypeError, ValueError):
            continue
    return index


def local_stats(mode, params, index):
    """(n, mean, pstdev)；无样本 → (0, None, None)。"""
    if not mode:
        return 0, None, None
    vals = index.get(canon(mode, params), [])
    if not vals:
        return 0, None, None
    return len(vals), mean(vals), (pstdev(vals) if len(vals) > 1 else 0.0)


# ---------------------------------------------------------------------------
# 官方成绩（API + 本地文件合并）
# ---------------------------------------------------------------------------

def fetch_leaderboard(timeout=8):
    """拉官方榜单 → [(submitted_at, official_seconds), ...]；失败返回 None。"""
    try:
        with urllib.request.urlopen(API_URL, timeout=timeout) as resp:
            data = json.load(resp)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            ValueError, OSError) as exc:
        print(f"⚠ 官方 API 拉取失败（{type(exc).__name__}: {exc}），"
              f"降级为只用 runs/official_results.jsonl 历史点。",
              file=sys.stderr)
        return None
    points = []
    try:
        problems = data["leaderboard"]["problems"]
    except (KeyError, TypeError):
        print("⚠ 官方 API 返回结构异常，降级为只用本地文件。", file=sys.stderr)
        return None
    for prob in problems:
        for sub in prob.get("submissions", []) or []:
            if sub.get("team") != TEAM:
                continue
            for att in sub.get("attempts", []) or []:
                try:
                    points.append((att["submitted_at"],
                                   float(att["download_seconds"])))
                except (KeyError, TypeError, ValueError):
                    continue
    return points


def load_official_points(use_api=True):
    """合并 API 与本地文件的官方成绩，按 submitted_at 去重，返回有序列表。"""
    merged = {}  # submitted_at -> official_seconds
    file_pts = load_jsonl(OFFICIAL_PATH)
    for rec in file_pts:
        at = rec.get("submitted_at")
        try:
            sec = float(rec.get("official_seconds"))
        except (TypeError, ValueError):
            continue
        if at:
            merged[str(at)] = sec
    src = "runs/official_results.jsonl"
    if use_api:
        api_pts = fetch_leaderboard()
        if api_pts is not None:
            for at, sec in api_pts:
                merged[str(at)] = sec
            src = f"API+{os.path.basename(OFFICIAL_PATH)}" if file_pts else "API"
    out = [{"submitted_at": k, "official": v, "source": src}
           for k, v in merged.items()]
    out.sort(key=lambda p: p["submitted_at"])
    return out

# ---------------------------------------------------------------------------
# 配对：官方成绩 ↔ 提交台账（±3 分钟 + note 配置描述）
# ---------------------------------------------------------------------------

def build_pairs(official_points, subs, index):
    sub_dts = []
    for s in subs:
        dt = parse_dt(s.get("at", ""))
        if dt:
            sub_dts.append((dt, s))

    pairs = []
    prev = None  # 时间序解析配置时的继承上下文
    for op in official_points:
        od = parse_dt(op.get("submitted_at", ""))
        best_sub, best_gap = None, None
        if od:
            for sd, s in sub_dts:
                gap = abs((sd - od).total_seconds())
                if gap <= MATCH_WINDOW_S and (best_gap is None or gap < best_gap):
                    best_sub, best_gap = s, gap
        note = (best_sub or {}).get("note") or ""
        mode, params, src = parse_config_from_note(note, prev)
        if mode and params:
            prev = (mode, params)
        n, lm, ls = local_stats(mode, params, index)
        rate = rate_of(mode, params)
        delta = (op["official"] / lm - 1.0) if lm else None
        bug = (mode == "leak_bucket" and params
               and params.get("leak_interval_us", 4000) < 4000)
        anomaly = (delta is not None and not bug
                   and abs(delta) >= ANOMALY_DELTA)
        pairs.append({
            "submitted_at": op["submitted_at"],
            "official": op["official"],
            "source": op.get("source", ""),
            "note": note,
            "match_gap_s": int(best_gap) if best_gap is not None else None,
            "mode": mode, "params": params or {}, "cfg_src": src,
            "rate": rate,
            "local_n": n, "local_mean": lm, "local_std": ls,
            "delta": delta,
            "bug": bool(bug), "anomaly": bool(anomaly),
        })
    return pairs


# ---------------------------------------------------------------------------
# 模型拟合（纯标准库最小二乘 + 留一交叉验证）
# ---------------------------------------------------------------------------

def _solve(A, b):
    """高斯消元解 A x = b（带部分主元）；奇异返回 None。"""
    n = len(A)
    m = [row[:] + [b[i]] for i, row in enumerate(A)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-9:
            return None
        m[col], m[piv] = m[piv], m[col]
        for r in range(col + 1, n):
            f = m[r][col] / m[col][col]
            for c in range(col, n + 1):
                m[r][c] -= f * m[col][c]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        s = m[r][n] - sum(m[r][c] * x[c] for c in range(r + 1, n))
        x[r] = s / m[r][r]
    return x


def _ols(features, y):
    """普通最小二乘：features 每行一个样本的特征向量。返回系数或 None。"""
    p = len(features[0])
    if len(features) < p:
        return None
    A = [[sum(row[i] * row[j] for row in features) for j in range(p)]
         for i in range(p)]
    b = [sum(row[i] * yi for row, yi in zip(features, y)) for i in range(p)]
    return _solve(A, b)


def fit_model(name, pts):
    """pts: [(local, official, rate)] → (coef, predict_fn) 或 (None, None)。"""
    if not pts:
        return None, None
    loc = [p[0] for p in pts]
    off = [p[1] for p in pts]
    rate = [p[2] for p in pts]
    if name == "M0":
        c = mean(o - l for l, o in zip(loc, off))
        return (c,), (lambda coef, l, r: l + coef[0])
    if name == "M1":
        coef = _ols([[l, 1.0] for l in loc], off)
        if coef is None:
            return None, None
        return tuple(coef), (lambda cf, l, r: cf[0] * l + cf[1])
    if name == "M2":
        if any(r is None for r in rate):
            return None, None
        coef = _ols([[l, 1.0, r] for l, r in zip(loc, rate)], off)
        if coef is None:
            return None, None
        return tuple(coef), (lambda cf, l, r: cf[0] * l + cf[1] + cf[2] * r)
    raise ValueError(name)


def evaluate_model(name, pts):
    """返回 dict：coef / residuals / rmse / loocv_rmse / loocv_errors / note。"""
    coef, pred = fit_model(name, pts)
    if coef is None:
        return {"name": name, "ok": False,
                "note": "样本不足或特征奇异，无法拟合"}
    residuals = [o - pred(coef, l, r) for l, o, r in pts]
    rmse = math.sqrt(mean(e * e for e in residuals))
    out = {
        "name": name, "ok": True, "coef": coef,
        "residuals": residuals, "rmse": rmse,
        "max_abs_resid": max(abs(e) for e in residuals),
        "note": "",
    }
    # 留一交叉验证
    n = len(pts)
    if n <= 1:
        out["loocv_rmse"] = None
        out["loocv_errors"] = []
        out["note"] = "n≤1，LOOCV 不可算"
    else:
        p = {"M0": 1, "M1": 2, "M2": 3}[name]
        if n - 1 < p:
            out["loocv_rmse"] = None
            out["loocv_errors"] = []
            out["note"] = f"留一后训练样本 {n-1} < 参数数 {p}，LOOCV 不可算"
        else:
            errs = []
            for i in range(n):
                train = pts[:i] + pts[i + 1:]
                c2, pr2 = fit_model(name, train)
                if c2 is None:
                    errs = None
                    break
                errs.append(pr2(c2, pts[i][0], pts[i][2]) - pts[i][1])
            if errs is None:
                out["loocv_rmse"] = None
                out["loocv_errors"] = []
                out["note"] = "留一子集拟合失败，LOOCV 不可算"
            else:
                out["loocv_errors"] = errs
                out["loocv_rmse"] = math.sqrt(mean(e * e for e in errs))
    return out


def fit_set(pairs, kind):
    """按集合规则筛选配对点 → [(local, official, rate), ...]。"""
    sel = []
    for p in pairs:
        if p["local_mean"] is None:
            continue
        if kind == "S_clean" and p["bug"]:
            continue
        if kind == "S_noano" and (p["bug"] or p["anomaly"]):
            continue
        # S_all 保留全部（含 bug），但 M2 需要 rate
        sel.append((p["local_mean"], p["official"], p["rate"]))
    return sel


# ---------------------------------------------------------------------------
# δ 分布统计
# ---------------------------------------------------------------------------

def delta_stats(deltas):
    if not deltas:
        return None
    return {
        "n": len(deltas),
        "mean": mean(deltas),
        "std": pstdev(deltas) if len(deltas) > 1 else 0.0,
        "min": min(deltas),
        "max": max(deltas),
        "range": max(deltas) - min(deltas),
    }


def group_deltas(pairs, key_fn, exclude_bug=False):
    groups = {}
    for p in pairs:
        if p["delta"] is None:
            continue
        if exclude_bug and p["bug"]:
            continue
        k = key_fn(p)
        if k is None:
            continue
        groups.setdefault(k, []).append(p["delta"])
    return groups


def pct(x, digits=2):
    return f"{x * 100:+.{digits}f}%" if x is not None else "—"

# ---------------------------------------------------------------------------
# 报告输出
# ---------------------------------------------------------------------------

def print_pairing(pairs):
    print("## 1. 配对表（官方成绩 ↔ 提交台账，±3 分钟最近匹配）\n")
    print("| 提交时刻 | 配置 | 官方 (s) | 本地 mean±sd (n) | δ | 标记 |")
    print("|---|---|---|---|---|---|")
    for p in sorted(pairs, key=lambda x: x["submitted_at"]):
        loc = (f"{p['local_mean']:.3f}±{p['local_std']:.3f} (n={p['local_n']})"
               if p["local_n"] else "—")
        marks = []
        if p["bug"]:
            marks.append("配置bug")
        if p["anomaly"]:
            marks.append("异常点")
        if p["cfg_src"] == "继承上一条":
            marks.append("配置继承")
        print(f"| {p['submitted_at']} | `{fmt_cfg(p['mode'], p['params'])}` "
              f"| {p['official']:.4f} | {loc} | {pct(p['delta'])} "
              f"| {'，'.join(marks) or '—'} |")
    print()


def print_delta_stats(pairs):
    print("## 2. δ 分布（δ = 官方/本地 − 1）\n")
    sets = [
        ("全部配对点", pairs),
        ("剔除配置 bug", [p for p in pairs if not p["bug"]]),
        ("剔除 bug + 异常点",
         [p for p in pairs if not p["bug"] and not p["anomaly"]]),
    ]
    print("| 集合 | n | δ 均值 | δ 标准差 | δ 最小 | δ 最大 | 极差 |")
    print("|---|---|---|---|---|---|---|")
    for label, sel in sets:
        st = delta_stats([p["delta"] for p in sel if p["delta"] is not None])
        if not st:
            print(f"| {label} | 0 | — | — | — | — | — |")
            continue
        print(f"| {label} | {st['n']} | {pct(st['mean'])} | {pct(st['std'])} "
              f"| {pct(st['min'])} | {pct(st['max'])} | {pct(st['range'])} |")
    print()

    def table(title, groups, key_name):
        print(f"**{title}**\n")
        print(f"| {key_name} | n | δ 列表 |")
        print("|---|---|---|")
        for k in sorted(groups, key=lambda x: (x is None, x)):
            ds = groups[k]
            lst = ", ".join(pct(d) for d in sorted(ds))
            print(f"| {k} | {len(ds)} | {lst} |")
        print()

    table("按 rate 分组（全部点）",
          group_deltas(pairs, lambda p: p["rate"]), "rate")
    table("按 leak_interval_us / token_refill_interval_us 分组（全部点）",
          group_deltas(pairs, lambda p: (p["params"] or {}).get(
              "leak_interval_us", (p["params"] or {}).get(
                  "token_refill_interval_us"))), "interval_us")
    table("按提交时段（小时）分组（全部点）",
          group_deltas(pairs, lambda p: (parse_dt(p["submitted_at"]) or
                                         datetime(1970, 1, 1)).hour),
          "小时")


def print_fits(pairs):
    print("## 3. 拟合结果（M0/M1/M2；残差与留一交叉验证）\n")
    print("> ⚠ 样本量极小（有效点仅 2–3 个），以下系数与误差**置信度很低**，"
          "只能当方向性参考，不能当规律。\n")
    sets = [
        ("S_all（含配置 bug 点，仅对照）", "S_all"),
        ("S_clean（剔除配置 bug）", "S_clean"),
        ("S_noano（剔除 bug + 异常点）", "S_noano"),
    ]
    results = {}
    for label, kind in sets:
        pts = fit_set(pairs, kind)
        print(f"### {label} — n={len(pts)}\n")
        if not pts:
            print("（无可用点）\n")
            continue
        print("| 模型 | 系数 | 残差 RMSE | 最大\\|残差\\| | LOOCV RMSE | 备注 |")
        print("|---|---|---|---|---|---|")
        for name in ("M0", "M1", "M2"):
            ev = evaluate_model(name, pts)
            results[(kind, name)] = ev
            if not ev["ok"]:
                print(f"| {name} | — | — | — | — | {ev['note']} |")
                continue
            coef_s = ", ".join(f"{c:.4f}" for c in ev["coef"])
            loo = (f"{ev['loocv_rmse']:.3f}"
                   if ev.get("loocv_rmse") is not None else "不可算")
            print(f"| {name} | {coef_s} | {ev['rmse']:.3f} "
                  f"| {ev['max_abs_resid']:.3f} | {loo} | {ev['note'] or '—'} |")
        print()
    return results


def print_core_question(results):
    print("## 4. 核心问题：本地均值降 1 秒，官方期望收益多少？\n")
    print("| 拟合集 | 模型 | 斜率 a（∂官方/∂本地） | 说明 |")
    print("|---|---|---|---|")
    notes = {
        ("S_clean", "M0"): "加性偏移模型，斜率恒为 1",
        ("S_clean", "M1"): "含异常点，斜率被单点拉平甚至变号",
        ("S_noano", "M1"): "剔除异常点后恰好过两点（残差 0）",
        ("S_clean", "M2"): "n=3、3 参数，恰好饱和",
        ("S_noano", "M2"): "n=2 < 3 参数，不可算",
    }
    for key, note in notes.items():
        kind, name = key
        ev = results.get(key)
        if not ev or not ev["ok"]:
            print(f"| {kind} | {name} | 不可算 | {ev['note'] if ev else '样本不足'} |")
            continue
        if name == "M0":
            slope, extra = 1.0, f"（偏移 c = {ev['coef'][0]:.4f} s）"
        else:
            slope, extra = ev["coef"][0], ""
        print(f"| {kind} | {name} | {slope:.4f} {extra} | {note} |")
    print()
    for kind, name in (("S_clean", "M0"), ("S_clean", "M1"), ("S_noano", "M1")):
        ev = results.get((kind, name))
        if not (ev and ev["ok"]):
            continue
        if name == "M0":
            claim = (f"斜率恒为 1（模型定义），偏移 c = {ev['coef'][0]:.4f} s → "
                     f"本地每降 1 s，官方期望降 1 s")
        else:
            a = ev["coef"][0]
            claim = (f"斜率 a = {a:.4f} → 本地每降 1 s，"
                     f"官方期望约降 {a:.2f} s")
        if ev.get("loocv_rmse") is not None:
            tail = f"（LOOCV RMSE = {ev['loocv_rmse']:.3f} s）"
        else:
            tail = f"（LOOCV 不可算：{ev['note']}）"
        print(f"- **{kind} / {name}**：{claim} {tail}")
    print()


def print_anomaly(pairs, results):
    print("## 5. 异常点讨论（leak 27/40/4000，δ = +14.8%）\n")
    ano = [p for p in pairs if p["anomaly"]]
    for p in ano:
        print(f"- {p['submitted_at']} `{fmt_cfg(p['mode'], p['params'])}` "
              f"官方 {p['official']:.4f}，本地 {p['local_mean']:.3f} "
              f"(n={p['local_n']})，δ = {pct(p['delta'])}")
    print()
    print("| 口径 | 集合 | n | M0 系数 c | M1 斜率 a | M1 LOOCV | M2 斜率 a |")
    print("|---|---|---|---|---|---|---|")
    for label, kind in (("纳入异常点", "S_clean"), ("剔除异常点", "S_noano")):
        pts = fit_set(pairs, kind)
        row = [label, kind, str(len(pts))]
        for name in ("M0", "M1", "M2"):
            ev = results.get((kind, name)) or evaluate_model(name, pts)
            if not ev["ok"]:
                row.append("—")
            else:
                row.append(f"{ev['coef'][0]:.4f}")
            if name == "M1":
                loo = (f"{ev['loocv_rmse']:.3f}"
                       if ev.get("loocv_rmse") is not None else "不可算")
                row.append(loo)
        print("| " + " | ".join(row) + " |")
    print()
    print("说明：纳入时 n=3、剔除后 n=2。n=2 下 M1 恰好过两点（残差 0、"
          "LOOCV 不可算），系数完全由两点决定；两种口径的斜率差异"
          "本身就说明样本量不足以区分「规律」与「噪声」。\n")


def print_conclusion(results):
    print("## 6. 一句话结论（工具自动生成的定性摘要）\n")
    ev = results.get(("S_clean", "M0"))
    ev1 = results.get(("S_noano", "M1"))
    bits = []
    if ev and ev["ok"]:
        bits.append(f"当前可用点下官方 ≈ 本地 + {ev['coef'][0]:.1f} s（M0）")
    if ev1 and ev1["ok"]:
        bits.append(f"剔异常后 M1 斜率 {ev1['coef'][0]:.2f}")
    if not bits:
        bits.append("有效配对点不足，无法给出方向性结论")
    print("、".join(bits)
          + "；但有效样本仅 2–3 个点，任何斜率都不可当规律——"
            "本地调参只能用于排除明显差的配置，"
            "官方成绩必须靠实测提交确认。")


# ---------------------------------------------------------------------------
# --predict
# ---------------------------------------------------------------------------

def cmd_predict(arg, pairs, index, results):
    try:
        parts = [int(x) for x in re.split(r"[,\s/]+", arg.strip()) if x]
    except ValueError:
        print(f"⚠ --predict 参数无法解析：{arg!r}（期望如 30,50,5000）",
              file=sys.stderr)
        return 1
    if len(parts) != 3:
        print("⚠ --predict 需要 3 个整数：rate,cap,interval_us", file=sys.stderr)
        return 1
    r, c, i = parts
    mode, params = "leak_bucket", {
        "leak_rate": r, "bucket_cap": c, "leak_interval_us": i}
    n, lm, ls = local_stats(mode, params, index)
    print(f"## 预测：`leak {r}/{c}/{i}`\n")
    if not n:
        print(f"本地无该配置的有效样本（results.jsonl 中 6 目录一致且 "
              f"valid=true 的记录为 0），无法给出预测。")
        return 1
    print(f"- 本地均值 {lm:.3f} ± {ls:.3f} s（n={n}）")
    bug = i < 4000
    if bug:
        print(f"- ⚠ interval={i} µs < 4000 µs：属 1ms 陷阱族，"
              f"官方 4ms 粒度下该配置已知失效（历史官方 ≈2×），"
              f"以下线性预测不适用。")

    # 80% 区间：用 S_clean 的 M0 残差分布经验分位
    pts = fit_set(pairs, "S_clean")
    ev = results.get(("S_clean", "M0")) or evaluate_model("M0", pts)
    print()
    print("| 模型 | 官方点预测 (s) | 系数来源 |")
    print("|---|---|---|")
    for name in ("M0", "M1", "M2"):
        e = results.get(("S_clean", name)) or evaluate_model(name, pts)
        if not e or not e["ok"]:
            print(f"| {name} | 不可算 | {e['note'] if e else '无拟合'} |")
            continue
        pred = None
        _, fn = fit_model(name, pts)
        if fn:
            pred = fn(e["coef"], lm, r)
        print(f"| {name} | {pred:.3f} | S_clean n={len(pts)} |")

    if ev and ev["ok"] and ev["residuals"]:
        res = sorted(ev["residuals"])
        # 线性插值经验分位（p10/p90 → 中间 80% 区间）
        def q(p):
            if len(res) == 1:
                return res[0]
            pos = p * (len(res) - 1)
            lo = int(math.floor(pos))
            hi = int(math.ceil(pos))
            return res[lo] + (pos - lo) * (res[hi] - res[lo])
        c0 = ev["coef"][0]
        point = lm + c0
        lo80, hi80 = point + q(0.10), point + q(0.90)
        print()
        print(f"**80% 预测区间（M0 + S_clean 残差经验分位 p10/p90）**："
              f"[{lo80:.3f}, {hi80:.3f}] s，点预测 {point:.3f} s")
        print(f"（残差 n={len(res)}，区间宽度 "
              f"{hi80 - lo80:.3f} s；样本极少，区间本身不可信，"
              f"仅作数量级参考。）")
    return 0


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(
        description="本地评测 ↔ 官方成绩映射分析（只读）")
    ap.add_argument("--predict", metavar="RATE,CAP,INTERVAL_US",
                    help="预测该 leak_bucket 配置的官方成绩区间，如 30,50,5000")
    ap.add_argument("--offline", action="store_true",
                    help="不访问官方 API，只用 runs/official_results.jsonl")
    args = ap.parse_args(argv)

    results_recs = load_jsonl(RESULTS_PATH)
    subs = load_jsonl(SUBS_PATH)
    index = build_local_index(results_recs)
    official_points = load_official_points(use_api=not args.offline)
    pairs = build_pairs(official_points, subs, index)

    if args.predict:
        return cmd_predict(args.predict, pairs, index, {})

    print("# 本地↔官方 映射分析（tools/local_official_map.py 输出）\n")
    print(f"- 本地评测记录：{len(results_recs)} 条 "
          f"（valid 且 6 目录一致的配置签名 {len(index)} 个）")
    print(f"- 提交台账：{len(subs)} 条；官方成绩点：{len(official_points)} 个"
          f"（来源 {official_points[0]['source'] if official_points else '无'}）")
    print(f"- 成功配对：{len(pairs)} 个（±{MATCH_WINDOW_S}s + note 配置描述）\n")
    if not pairs:
        print("（无配对点，分析结束）")
        return 0

    print_pairing(pairs)
    print_delta_stats(pairs)
    fit_results = print_fits(pairs)
    print_core_question(fit_results)
    print_anomaly(pairs, fit_results)
    print_conclusion(fit_results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
