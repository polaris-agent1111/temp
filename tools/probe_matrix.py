#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe_matrix.py — 官方探测矩阵（rate × interval），一条命令重跑。

数据源:
  runs/results.jsonl            本地评测（6 目录同配纯族 → 本地均值）
  runs/official_results.jsonl   官方成绩记录（official_log.py 产出）
  http://47.120.64.152:5000/api/leaderboard   官方 API（拉我方 attempts 补新分，失败自动回退）
  runs/adaptive_log.jsonl       自适应逐发日志（pick_next 标记；不存在则跳过）

输出: report/探测矩阵.md（覆盖写）
  - 矩阵: 行 = leak_rate 18..48，列 = leak_interval_us {4000,5000,6000,8000}
    格: 「官方成绩(/分隔) / 本地mean±sd(n) / δ」；无数据 = —
  - 已投配置清单（时间倒序，含 token_bucket 等非 leak 模块）
  - 覆盖率统计（rate 段 × interval）+ 最值得补测的空白格（本地均值 × 邻近 δ 推断）

用法: python tools/probe_matrix.py [--out report/探测矩阵.md] [--no-live]
"""
import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime
from statistics import mean, pstdev

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "runs", "results.jsonl")
OFFICIAL = os.path.join(ROOT, "runs", "official_results.jsonl")
SUBMISSIONS = os.path.join(ROOT, "runs", "submissions.jsonl")
ADAPTIVE = os.path.join(ROOT, "runs", "adaptive_log.jsonl")
SNAP_DIR = os.path.join(ROOT, "intel", "raw")
BOARD_URL = "http://47.120.64.152:5000/api/leaderboard"
TEAM = "赛博coder"

INTERVALS = [4000, 5000, 6000, 8000]
RATES = list(range(18, 49))          # 18..48
BANDS = [(18, 23), (24, 29), (30, 35), (36, 41), (42, 48)]
SHARE = 41.28                        # 本地实测有效份额 Mbps（0013）
TRAP_DELTA = 50.0                    # δ 超过 +50% 视为陷阱/异常点，排除出 δ̄


def parse_dt(s):
    try:
        dt = datetime.fromisoformat(s.strip())
        return dt.replace(tzinfo=None) if dt.tzinfo else dt
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(s.strip()[:19], fmt)
            except ValueError:
                continue
    return None


def cfg_tuple(spec):
    """'leak_bucket:leak_rate=24,...' → (mode, (k,v)...)，解析失败 None。"""
    if not spec or ":" not in spec:
        return None
    mode, _, p = spec.partition(":")
    mode = mode.strip()
    ps = {}
    for kv in p.split(","):
        if "=" in kv:
            k, _, v = kv.partition("=")
            try:
                ps[k.strip()] = int(v)
            except ValueError:
                return None
    return mode, tuple(sorted(ps.items()))


def load_local():
    """results.jsonl 纯 6 目录同配的 leak 族 → {(rate,cap,int): [totals]}。

    剔除 load-*/hog-*（CPU 争抢实验）与 11-06 当日起（同轮极差 36 s，本地标定
    停用，见 hourly/2026-11-06_0700.md）——与 delta_model/0037 口径一致。
    """
    fam = {}
    for r in load_jsonl(RESULTS):
        if r.get("valid") is not True:
            continue
        if str(r.get("tag", "")).startswith(("load-", "hog-")):
            continue
        if str(r.get("at", "")) >= "2026-11-06":
            continue
        cfg = r.get("config", {})
        specs = [cfg.get(str(i)) for i in range(1, 7)]
        if any(not s or s.startswith("(") for s in specs):
            continue
        tups = [cfg_tuple(s) for s in specs]
        if any(t is None or t[0] != "leak_bucket" for t in tups):
            continue
        if len(set(tups)) != 1:
            continue
        mode, items = tups[0]
        d = dict(items)
        try:
            key = (d["leak_rate"], d["bucket_cap"], d["leak_interval_us"])
        except KeyError:
            continue
        fam.setdefault(key, []).append(float(r["total_seconds"]))
    return {k: v for k, v in fam.items() if v}


def load_jsonl(path):
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
    return out


def parse_official_note(note, prev):
    """official_results 的 note → (mode, params) 或继承上一条。"""
    mode = next((m for m in ("token_bucket", "coarse_grained_rate_based",
                             "precise_rate_based", "origin", "leak_bucket") if m in note), None)
    params = None
    if mode == "leak_bucket":
        m = re.search(r"rate(\d+)/cap(\d+)/int(\d+)", note)
        if m:
            params = {"leak_rate": int(m.group(1)), "bucket_cap": int(m.group(2)),
                      "leak_interval_us": int(m.group(3))}
        else:
            m = re.search(r"leak_bucket\s+(\d+)/(\d+)/(\d+)", note)
            if m:
                params = {"leak_rate": int(m.group(1)), "bucket_cap": int(m.group(2)),
                          "leak_interval_us": int(m.group(3))}
    elif mode == "token_bucket":
        m = re.search(r"tokens=(\d+),\s*burst=(\d+),\s*refill=(\d+)/(\d+)us", note)
        if m:
            params = {"tokens": int(m.group(1)), "burst": int(m.group(2)),
                      "token_refill_rate": int(m.group(3)), "token_refill_interval_us": int(m.group(4))}
    if mode and params:
        return mode, params
    if prev:
        return prev
    return None, None


def fetch_live_attempts():
    """官方 API 拉 我方 attempts（失败返回 []，不影响主流程）。"""
    try:
        import requests
        r = requests.get(BOARD_URL, timeout=15)
        if r.status_code != 200:
            return [], f"API {r.status_code}"
        d = r.json()
        for s in d["leaderboard"]["problems"][0]["submissions"]:
            if s["team"] == TEAM:
                return sorted(s["attempts"], key=lambda a: a["submitted_at"]), "API"
        return [], "API(无我方记录)"
    except Exception as e:
        return [], f"API失败:{type(e).__name__}"


def cfg_from_submission_note(note):
    """submission note → (mode, params)。支持 tag 形如 leak-30-50-5000 / 正文 40/60/4000。"""
    if not note:
        return None, None
    tag = note.split("|", 1)[0].strip()
    m = re.search(r"(token_bucket|leak_bucket)[-_](\d+)-(\d+)-(\d+)", tag)
    if m:
        mode = m.group(1)
        if mode == "leak_bucket":
            return mode, {"leak_rate": int(m.group(2)), "bucket_cap": int(m.group(3)),
                          "leak_interval_us": int(m.group(4))}
    m = re.search(r"leak[_-](\d+)-(\d+)-(\d+)", tag)
    if m:
        return "leak_bucket", {"leak_rate": int(m.group(1)), "bucket_cap": int(m.group(2)),
                               "leak_interval_us": int(m.group(3))}
    m = re.search(r"leak(?:_bucket)?\s+(\d+)/(\d+)/(\d+)", note)
    if m:
        return "leak_bucket", {"leak_rate": int(m.group(1)), "bucket_cap": int(m.group(2)),
                               "leak_interval_us": int(m.group(3))}
    m = re.search(r"rate(\d+)/cap(\d+)/int(\d+)", note)
    if m:
        return "leak_bucket", {"leak_rate": int(m.group(1)), "bucket_cap": int(m.group(2)),
                               "leak_interval_us": int(m.group(3))}
    return None, None


def match_submission(at_str, subs):
    """attempts.submitted_at ↔ submissions.jsonl 按 ±120 s 最近匹配 → 该条 submission。"""
    dt = parse_dt(at_str)
    if not dt:
        return None
    best, best_gap = None, None
    for s in subs:
        sd = parse_dt(s.get("at", ""))
        if not sd:
            continue
        gap = abs((sd - dt).total_seconds())
        if gap <= 120 and (best_gap is None or gap < best_gap):
            best, best_gap = s, gap
    return best


def build_officials(use_live=True):
    """官方点列表: [{submitted_at, seconds, mode, params, src}]，按时间排序去重。

    official_results.jsonl 之外的 API 新分（如 11-06 五发）→ 用 submissions.jsonl
    按 ±120 s 匹配 note 解析配置（ADP-leak-30-50-5000 / hr-40-60-4000 等）。
    """
    recs = load_jsonl(OFFICIAL)
    subs = load_jsonl(SUBMISSIONS)
    seen_dt = set()
    out = []
    prev = None
    for o in sorted(recs, key=lambda x: x.get("submitted_at", "")):
        dt = parse_dt(o.get("submitted_at", ""))
        mode, params = parse_official_note(o.get("note", ""), prev)
        if mode:
            prev = (mode, params)
        if dt:
            seen_dt.add(dt.strftime("%Y-%m-%d %H:%M:%S"))
        out.append({"at": o.get("submitted_at", ""), "seconds": float(o["official_seconds"]),
                    "mode": mode, "params": params or {}, "src": "official_results"})
    if use_live:
        atts, src = fetch_live_attempts()
        for a in atts:
            key = a["submitted_at"]
            if key in seen_dt:
                continue
            mode, params = None, None
            sub = match_submission(key, subs)
            if sub:
                mode, params = cfg_from_submission_note(sub.get("note", ""))
            out.append({"at": key, "seconds": float(a["download_seconds"]),
                        "mode": mode, "params": params or {},
                        "src": f"API新增({src})" + ("" if mode else "+配置未解析)")})
        out.sort(key=lambda x: parse_dt(x["at"]) or datetime.min)
    return out


def fmt_cell(off_vals, loc):
    parts = []
    if off_vals:
        parts.append("/".join(f"{v:.3f}" for v in off_vals))
    else:
        parts.append("—")
    if loc:
        m, s, n = loc
        parts.append(f"{m:.1f}±{s:.1f}({n})" if n > 1 else f"{m:.1f}(1)")
        if off_vals:
            d = (mean(off_vals) / m - 1) * 100
            parts.append(f"{d:+.1f}%")
        else:
            parts.append("—")
    else:
        parts.append("—")
    return " / ".join(parts)


def main():
    ap = argparse.ArgumentParser(description="官方探测矩阵")
    ap.add_argument("--out", default=os.path.join(ROOT, "report", "探测矩阵.md"))
    ap.add_argument("--no-live", action="store_true", help="不访问官方 API，只用 official_results.jsonl")
    args = ap.parse_args()

    local = load_local()
    officials = build_officials(use_live=not args.no_live)
    adaptive = load_jsonl(ADAPTIVE)

    # 矩阵组织: {(rate,interval): {"officials":[...], "adaptive":bool}}
    cell_off = {}
    unoff_tagged = []
    for o in officials:
        if o["mode"] != "leak_bucket" or not o["params"]:
            unoff_tagged.append(o)
            continue
        try:
            key = (o["params"]["leak_rate"], o["params"]["leak_interval_us"])
        except KeyError:
            unoff_tagged.append(o)
            continue
        cell_off.setdefault(key, []).append((o["seconds"], o["at"], o.get("src", "")))
    adaptive_marks = set()
    for a in adaptive:
        tag = str(a.get("tag", "") or a.get("pick", "") or a.get("note", ""))
        m = re.search(r"leak[_-](\d+)[-_](\d+)[-_]?(\d+)?", tag)
        if not m:
            cfg = a.get("config") or a.get("params") or {}
            if isinstance(cfg, dict) and {"leak_rate", "leak_interval_us"} <= set(cfg):
                adaptive_marks.add((int(cfg["leak_rate"]), int(cfg["leak_interval_us"])))
                continue
        if m:
            itv = int(m.group(3) or 4000)
            adaptive_marks.add((int(m.group(1)), itv))

    # δ 表：有官方且有本地的 (rate,cap,int) 三元组
    per_point_delta = []
    for (r, itv), ov in cell_off.items():
        for cap in range(40, 121):
            key = (r, cap, itv)
            if key in local:
                for sec, at, src in ov:
                    d = (sec / mean(local[key]) - 1) * 100
                    if d <= TRAP_DELTA:
                        per_point_delta.append(d)
    normal = [d for d in per_point_delta if d <= 10.0]   # 0024：>10% 曾记异常；0025 后改读「低 rate 档」
    dbar = (sorted(normal)[len(normal) // 2] if normal
            else (sorted(per_point_delta)[len(per_point_delta) // 2] if per_point_delta else 3.0))
    anomalies = [d for d in per_point_delta if d > 10.0]

    L = []
    A = L.append
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    A(f"# 官方探测矩阵（rate × interval）\n")
    A(f"- 生成：`python tools/probe_matrix.py`（一条命令重跑，本文件覆盖写）——数据截至 **{stamp}**")
    A(f"- 本地源：`runs/results.jsonl` 纯 6 目录同配 leak 族；官方源：`runs/official_results.jsonl`"
      f"{' + 官方 API 实时补分' if not args.no_live else '（--no-live，未访问 API）'}")
    A(f"- δ 基准：**正常档中位数 = {dbar:+.1f}%**（δ≤+10% 的官方点 n={len(normal)}；"
      f"δ>{10}% 的点 n={len(anomalies)}——0025 起按「低 rate 档（rate≤30 → +15~22%）」解读，"
      f"不再一律当异常；陷阱 δ>+50% 亦剔除）")
    A("")
    A("<!-- AUTOGEN: probe_matrix.py 覆盖写整文件 -->")
    A("")

    # ---- 矩阵 ----
    A("## 1. 探测矩阵（格：官方 / 本地 mean±sd(n) / δ）\n")
    hdr = "| rate \\ interval | " + " | ".join(f"{i}" for i in INTERVALS) + " |"
    A(hdr)
    A("|" + "---|" * (len(INTERVALS) + 1))
    for r in RATES:
        cells = []
        for itv in INTERVALS:
            ov = cell_off.get((r, itv))
            locs = local.get((r, 0, 0))
            # 本地按 (rate, cap, int) 精确三元组，格内可能多 cap → 汇总展示
            caps = [(c, i2) for (rr, c, i2) in local if rr == r and i2 == itv]
            if caps:
                allv = [t for c, i2 in caps for t in local[(r, c, i2)]]
                loc = (mean(allv), pstdev(allv) if len(allv) > 1 else 0.0, len(allv))
            else:
                loc = None
            off_vals = [v for v, at, src in ov] if ov else []
            mark = "✱" if (r, itv) in adaptive_marks else ""
            if not ov and not caps:
                cells.append("—")
                continue
            body = fmt_cell(off_vals, loc)
            cells.append(f"{body}{mark}")
        A(f"| **{r}** | " + " | ".join(cells) + " |")
    A("")
    A("> 格式：`官方(/分隔) / 本地mean±sd(n) / δ`；`—`=未探测；`✱`=自适应计划已选中（adaptive_log）。"
      "rate9（v1/v1b，1ms 陷阱）不在矩阵行范围内，见已投清单。**本地 n 为该格（rate×interval）全部 cap 的合并样本数**"
      "（已剔 load-/hog- 争抢样本与 11-06 当日污染样本，与 delta_model 口径一致）；"
      "δ>+10% 的格（如 rate27@4000 的 +14.8%）按 0025 解读为**低 rate 档真实代价**，0024 的「异常点」定性已修。")
    A("")

    # ---- 已投清单 ----
    A("## 2. 已投配置清单（时间倒序）\n")
    A("| 提交时刻 | 模块 | 配置 | 官方 (s) | 来源 |")
    A("|---|---|---|---|---|")
    for o in sorted(officials, key=lambda x: parse_dt(x["at"]) or datetime.min, reverse=True):
        cfg = ",".join(f"{k}={v}" for k, v in sorted((o["params"] or {}).items())) or "未解析"
        A(f"| {o['at']} | {o['mode'] or '未知'} | `{cfg}` | {o['seconds']:.3f} | {o['src']} |")
    A("")

    # ---- 覆盖率 ----
    A("## 3. 覆盖率统计（官方已探测格 / 本地有样本格）\n")
    A("| rate 段 | " + " | ".join(f"{i}" for i in INTERVALS) + " | 合计 |")
    A("|" + "---|" * (len(INTERVALS) + 2))
    for lo, hi in BANDS:
        row = []
        tot_o = tot_l = 0
        for itv in INTERVALS:
            o = sum(1 for (r, i) in cell_off if lo <= r <= hi and i == itv)
            l = sum(1 for (r, c, i) in local if lo <= r <= hi and i == itv)
            row.append(f"{o}/{l}")
            tot_o += o
            tot_l += l
        A(f"| **{lo}–{hi}** | " + " | ".join(row) + f" | {tot_o}/{tot_l} |")
    A("")

    # ---- 空白区价值 ----
    A("## 4. 最值得补测的空白格（本地均值 × δ 模型推断）\n")
    # 推断模型：优先用 0036 delta_model（rate+cap 主模型），失败回退 δ̄ 中位数
    dm = None
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import delta_model as _dm
        pts_normal = [p for p in _dm.POINTS if p[0] != 9]
        _models = _dm.run_models(pts_normal)
        _prim = min((n for n, m in _models.items() if m.get("beta") is not None),
                    key=lambda n: _models[n]["mae"])
        dm = (_models[_prim], _models[_prim]["feat"], _prim, _models[_prim]["mae"])
    except Exception as e:
        dm = None
        dm_err = type(e).__name__
    if dm:
        _m, _feat, _pname, _pmae = dm

        def infer_delta(r, c, i):
            return _dm.predict(_m["beta"], _feat(r, c, i)) * 100
        A(f"> 推断模型：**delta_model 主模型 {_pname}**（LOOCV MAE {_pmae:.1f} pp，"
          f"`docs/analysis/delta-model.md`）；预测官方 = 本地 × (1 + δ̂(rate,cap,interval))。")
    else:
        def infer_delta(r, c, i):
            return dbar
        A(f"> 推断模型：δ̄={dbar:+.1f}% 中位数（delta_model 导入失败：{dm_err}，回退旧口径）。")
    A("")
    cands = []
    for (r, c, i), vals in local.items():
        if i not in INTERVALS or (r, i) in cell_off:
            continue
        if not (18 <= r <= 48):
            continue
        est = mean(vals) * (1 + infer_delta(r, c, i) / 100)
        same = [(abs(r - rr), itv, mean([v for v, at, src in cell_off[(rr, itv)]]))
                for (rr, itv) in cell_off if itv == i]
        nb = min(same) if same else None
        cands.append((est, r, c, i, len(vals), nb))
    cands.sort()
    if cands:
        A("| 排名 | 配置 | 本地 mean (n) | δ̂ | 推断官方 ≈ | 最近已测邻居 |")
        A("|---|---|---|---|---|---|")
        for k, (est, r, c, i, n, nb) in enumerate(cands[:8], 1):
            nb_s = (f"同 int 最近 rate 差 {nb[0]}（官方 {nb[2]:.3f}）"
                    if nb else "该 interval 暂无官方点")
            A(f"| {k} | `leak {r}/{c}/{i}` | {mean(local[(r,c,i)]):.2f} ({n}) "
              f"| {infer_delta(r, c, i):+.1f}% | {est:.1f} s | {nb_s} |")
        A("")
        A("> 推断口径：预测官方 = 本地均值 × (1 + δ̂)，δ̂ 来自 `tools/delta_model.py`"
          "（0036，rate+cap 主模型；interval<4000 域外不适用）。"
          "排序仅代表先验，**G=4000 咬合预警**未计入——rate 过低 × 大 interval 的格子"
          "咬合后会比推断差得多（见 `timer_model.py`）；δ 模型 LOOCV ±3 pp ≈ ±4 s，"
          "**名次间 <4 s 的差异无统计意义**。")
    else:
        A("（无符合条件的空白格）")
    A("")

    # ---- 自适应日志 ----
    A("## 5. 自适应逐发标记（adaptive_log）\n")
    if adaptive:
        A(f"- `runs/adaptive_log.jsonl` 共 {len(adaptive)} 条 pick 记录；矩阵中已选格标 ✱。")
        for a in adaptive[:10]:
            A(f"  - {a.get('at', a.get('seen_at', ''))}: {str(a.get('tag') or a.get('note') or a)[:90]}")
    else:
        A("- `runs/adaptive_log.jsonl` 尚不存在（自适应提交器 00:05 首跑后产生）——矩阵 ✱ 标记待首次运行后出现。")
    A("")

    # ---- 解读（规则生成） ----
    A("## 6. 解读与下一步（规则生成）\n")
    A(f"- **官方锚点**：`36/40/4000` = 133.086（δ +2.1%）；`27/40/4000` = 141.727（δ +14.8%——"
      f"0025 按低 rate 档解读，0024 的「异常点」定性已修）；11-06 新增 5 点见 §2。")
    A(f"- **覆盖率**：官方已探测 {len(cell_off)} 格（11-06 五发已并入，见 §2）；本地有样本但官方空白的格见 §4（按 delta_model 推断排序）。")
    A(f"- **读取规则**：本地均值仅作粗筛（sd≈6–8 s、跨时段漂移 ±10 s）；官方 δ 分层：rate≥36 正常档 +2~8%、rate≤30 档 +15~22%、1ms 陷阱 +96%；"
      f"新点推断官方 = 本地 × (1+δ̂)，**偏差 >±4 s 即触发 δ 模型修订**。")
    A(f"- **下一步对齐**：11-07 候选 10 个见 `runs/submit_plan_1107_candidates.md`（0039）；"
      f"cap/rate 因子判别设计见 `docs/analysis/min-cap-hypothesis.md`（0037）；每次新出分后重跑本脚本刷新矩阵。")
    A("")
    A("（本文件由 tools/probe_matrix.py 覆盖生成；重跑：`python tools/probe_matrix.py`）")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"[ok] officials={len(officials)} cells_off={len(cell_off)} "
          f"local_families={len(local)} adaptive={len(adaptive)} -> {args.out}")


if __name__ == "__main__":
    main()
