#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""official_analysis.py — 官方探测分析（配置→官方成绩配对、参数趋势、次日候选）

数据链路（只读，除 submit_plan_*.json 外不写任何文件）:
  runs/submissions.jsonl        每次提交一行（note 中竖线前为 tag，旧记录无 tag）
  runs/configs/<tag>/1..6/...   tag 对应的实际配置
  runs/official_results.jsonl   官方成绩（submitted_at / official_seconds / note）
  intel/raw/leaderboard_*.json  榜单快照（取当前榜首）

用法:
  python tools/official_analysis.py            # 打印 markdown 分析（可粘贴进 report/官方探测分析.md）
  python tools/official_analysis.py --plan     # 额外生成次日候选计划（非破坏：目标已存在则写 *_auto.json）

退出码: 0（含「暂无数据」的优雅退出）；仅标准库。
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
SUBS = os.path.join(ROOT, "runs", "submissions.jsonl")
OFF = os.path.join(ROOT, "runs", "official_results.jsonl")
CONFIGS = os.path.join(ROOT, "runs", "configs")
RESULTS = os.path.join(ROOT, "runs", "results.jsonl")
SNAP_DIR = os.path.join(ROOT, "intel", "raw")
PLAN_DIR = os.path.join(ROOT, "runs")

MODULES = ["token_bucket", "coarse_grained_rate_based", "precise_rate_based", "origin", "leak_bucket"]
DEFAULTS = {
    "token_bucket": {"tokens": 20, "burst": 40, "token_refill_rate": 10,
                     "token_refill_interval_us": 100, "enable_n_in_flight": 1},
    "coarse_grained_rate_based": {"max_pacing_rate": 0, "clock_granularity": 1000, "enable_n_in_flight": 1},
    "precise_rate_based": {"max_pacing_rate": 0, "clock_granularity": 1000, "enable_n_in_flight": 1},
    "origin": {"burst_tokens": 10, "max_pacing_rate": 0, "clock_granularity": 1000},
    "leak_bucket": {"leak_rate": 10, "bucket_cap": 30, "leak_interval_us": 1000},
}


def load_jsonl(path):
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
            except Exception:
                continue
    return out


def parse_dt(s):
    """兼容 '2026-11-05 15:55:45' 与 '2026-11-05T15:25:38+0800'；统一为 naive 本地时间。"""
    s = s.strip()
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


def extract_tag(note):
    """note 形如 's6-leak-22-50-4000 | S6: ...' → 竖线前为 tag；旧记录无竖线 → None。"""
    if "|" in note:
        tag = note.split("|", 1)[0].strip()
        if tag:
            return tag
    return None


def parse_config_from_note(note, prev_params):
    """从 note 文本解析 (mode, params)；解析不出时继承上一条（按时间序），如 '同 v1 配置重投'。"""
    mode = next((m for m in MODULES if m in note), None)
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
    if params is None and mode:
        kv = dict(re.findall(r"([a-z_]+)=(\d+)", note))
        if kv:
            params = {k: int(v) for k, v in kv.items()}
    if mode and params:
        return mode, params, "note解析"
    if prev_params:
        return prev_params[0], prev_params[1], "继承上一条"
    return None, None, "未解析"


def canon(mode, params):
    """归一化：剔除与文档默认值相同的参数 → 可比签名。"""
    d = DEFAULTS.get(mode, {})
    kept = {}
    for k, v in params.items():
        if k in d and d[k] == v:
            continue
        kept[k] = v
    return mode, tuple(sorted(kept.items()))


def fmt_cfg(mode, params):
    if not mode:
        return "（未解析）"
    body = ",".join(f"{k}={v}" for k, v in sorted(params.items()))
    return f"{mode}:{body}" if body else f"{mode}:(全默认)"


def local_stats(mode, params):
    """在 results.jsonl 中找 6 目录全等于该配置的 valid 记录 → (n, mean, std)。"""
    if not mode:
        return 0, None, None
    target = canon(mode, params)
    recs = load_jsonl(RESULTS)
    vals = []
    for r in recs:
        if r.get("valid") is not True:
            continue
        dirs = []
        ok = True
        for i in range(1, 7):
            spec = r.get("config", {}).get(str(i), "")
            if not spec or spec.startswith("("):
                ok = False
                break
            if ":" not in spec:
                ok = False
                break
            m, _, p = spec.partition(":")
            ps = {}
            if p.strip():
                for kv in p.split(","):
                    if "=" in kv:
                        k, _, v = kv.partition("=")
                        try:
                            ps[k.strip()] = int(v)
                        except ValueError:
                            ok = False
                            break
            dirs.append(canon(m.strip(), ps))
        if ok and all(d == target for d in dirs):
            vals.append(float(r["total_seconds"]))
    if not vals:
        return 0, None, None
    return len(vals), mean(vals), (pstdev(vals) if len(vals) > 1 else 0.0)


def build_pairs():
    """官方成绩 ↔ 提交记录 配对（±2 分钟最近匹配），按时间序解析配置（可继承）。"""
    official = sorted(load_jsonl(OFF), key=lambda x: x.get("submitted_at", ""))
    subs = load_jsonl(SUBS)
    sub_dts = [(parse_dt(s.get("at", "")), s) for s in subs]
    sub_dts = [(d, s) for d, s in sub_dts if d]
    pairs, prev = [], None
    for o in official:
        od = parse_dt(o.get("submitted_at", ""))
        if not od:
            continue
        best_sub, best_gap = None, None
        for sd, s in sub_dts:
            gap = abs((sd - od).total_seconds())
            if gap <= 120 and (best_gap is None or gap < best_gap):
                best_sub, best_gap = s, gap
        note = (best_sub or {}).get("note") or o.get("note", "")
        tag = extract_tag(note) or extract_tag(o.get("note", ""))
        mode, params, src = parse_config_from_note(o.get("note", ""), prev)
        if mode:
            prev = (mode, params)
        n, lm, ls = local_stats(mode, params)
        trap = (mode == "leak_bucket" and params and
                params.get("leak_interval_us", 4000) < 4000)
        pairs.append({
            "submitted_at": o["submitted_at"],
            "official": float(o["official_seconds"]),
            "note": o.get("note", ""),
            "tag": tag,
            "mode": mode, "params": params or {}, "cfg_src": src,
            "local_n": n, "local_mean": lm, "local_std": ls,
            "trap": trap,
        })
    return pairs


def latest_leader():
    files = glob.glob(os.path.join(SNAP_DIR, "leaderboard_*.json"))
    if not files:
        return None, None
    f = max(files, key=os.path.getmtime)
    try:
        d = json.load(open(f, encoding="utf-8-sig"))
        subs = d["leaderboard"]["problems"][0]["submissions"]
        best = min((min(float(a["download_seconds"]) for a in s["attempts"]), s["team"])
                   for s in subs if s.get("attempts"))
        return best[0], best[1]
    except Exception:
        return None, None


def section_pairing(pairs):
    print("## 配对表（官方成绩 ↔ 提交，±2 分钟最近匹配）\n")
    print("| 提交时刻 | tag | 官方 (s) | 配置 | 本地 mean±sd (n) | δ | 备注 |")
    print("|---|---|---|---|---|---|---|")
    for p in sorted(pairs, key=lambda x: x["submitted_at"]):
        loc = (f"{p['local_mean']:.2f}±{p['local_std']:.2f} (n={p['local_n']})"
               if p["local_n"] else "—")
        delta = (f"{(p['official']/p['local_mean']-1)*100:+.1f}%" if p["local_mean"] else "—")
        mark = " ⚠1ms陷阱" if p["trap"] else ""
        note = p["note"][:42].replace("|", "/")
        print(f"| {p['submitted_at']} | {p['tag'] or '—'}{mark} | {p['official']:.3f} "
              f"| `{fmt_cfg(p['mode'], p['params'])}` | {loc} | {delta} | {note} |")
    print()


def section_trend(pairs):
    leak = [p for p in pairs if p["mode"] == "leak_bucket" and not p["trap"]]
    traps = [p for p in pairs if p["trap"]]
    print("## 参数趋势（leak_bucket 官方成绩；1 ms 陷阱族排除）\n")
    if traps:
        print(f"> 异常点（已排除）：{len(traps)} 个 —— "
              + "、".join(f"{p['submitted_at']} {p['official']:.3f}s" for p in traps)
              + "（interval<4000，官方 ×2 腰斩族）\n")
    if not leak:
        print("（暂无有效 leak 官方点）\n")
        return None
    for key, label in (("leak_rate", "leak_rate"), ("bucket_cap", "bucket_cap")):
        groups = {}
        for p in leak:
            groups.setdefault(p["params"].get(key), []).append(p["official"])
        print(f"**按 {label} 分组**：\n")
        print(f"| {label} | n | 官方 mean | min | max | 极差 |")
        print("|---|---|---|---|---|---|")
        for k in sorted(groups):
            v = groups[k]
            print(f"| {k} | {len(v)} | {mean(v):.3f} | {min(v):.3f} | {max(v):.3f} "
                  f"| {max(v)-min(v):.3f} |")
        best_k = min(groups, key=lambda k: mean(groups[k]))
        worst_k = max(groups, key=lambda k: mean(groups[k]))
        print(f"\n→ 官方最好 {label}={best_k}（mean {mean(groups[best_k]):.3f}），"
              f"最差 {label}={worst_k}（mean {mean(groups[worst_k]):.3f}）。\n")
    return leak


def section_ranking(pairs):
    print("## 按官方成绩排名\n")
    print("| # | 提交时刻 | 官方 (s) | 配置 | 是否陷阱 |")
    print("|---|---|---|---|---|")
    for i, p in enumerate(sorted(pairs, key=lambda x: x["official"]), 1):
        print(f"| {i} | {p['submitted_at']} | {p['official']:.3f} "
              f"| `{fmt_cfg(p['mode'], p['params'])}` | {'是' if p['trap'] else '否'} |")
    lead, team = latest_leader()
    if lead:
        ours = min(p["official"] for p in pairs)
        print(f"\n当前榜首（快照）：{team} {lead:.4f} s；我方最好 {ours:.3f} s"
              f"（差 {ours-lead:+.3f} s）。")
    else:
        print("\n（无本地榜单快照，榜首差距暂缺）")
    print()


def section_plan(pairs, write_plan):
    leak = [p for p in pairs if p["mode"] == "leak_bucket" and not p["trap"]]
    if not leak:
        print("## 次日候选\n\n（无有效 leak 官方点，无法按规则生成）")
        return
    best = min(leak, key=lambda p: p["official"])
    r0, c0, i0 = (best["params"].get("leak_rate"), best["params"].get("bucket_cap"),
                  best["params"].get("leak_interval_us", 4000))
    already = {(p["params"].get("leak_rate"), p["params"].get("bucket_cap"),
                p["params"].get("leak_interval_us")) for p in leak}
    cands = []
    for r in (r0 - 1, r0, r0 + 1):
        for c in (c0 - 10, c0, c0 + 10):
            if r < 1 or c < r:  # bucket_cap >= leak_rate 约束
                continue
            if (r, c, i0) in already:
                continue
            cands.append((abs(r - r0), abs(c - c0), r, c))
    cands.sort()
    cands = cands[:5]
    print("## 次日候选（规则：官方最好 rate±1 × cap±10，去重已投，确定性排序）\n")
    print(f"锚点：官方最好 `leak {r0}/{c0}/{i0}`（{best['official']:.3f} s，"
          f"{best['submitted_at']}）\n")
    start_id = len(load_jsonl(OFF)) + 1
    plan = []
    for i, (dr, dc, r, c) in enumerate(cands):
        tag = f"s{start_id + i}-leak-{r}-{c}-{i0}"
        note = (f"S{start_id + i}: leak {r}/{c}/{i0}"
                f"（官方邻域自动候选：Δrate={dr}, Δcap={dc}，由 tools/official_analysis.py 生成）")
        plan.append({"tag": tag, "note": note,
                     "all": ["leak_bucket", {"leak_rate": r, "bucket_cap": c,
                                              "leak_interval_us": i0}]})
        print(f"{i+1}. `{tag}` — leak {r}/{c}/{i0}（Δrate={dr}, Δcap={dc}）")
    print()
    if not write_plan:
        print("（加 --plan 参数可写入提交计划文件）")
        return
    import time
    nxt = time.strftime("%m%d", time.localtime(time.time() + 86400))
    path = os.path.join(PLAN_DIR, f"submit_plan_{nxt}.json")
    out = path
    if os.path.exists(path):
        out = os.path.join(PLAN_DIR, f"submit_plan_{nxt}_auto.json")
        print(f"⚠ 目标 {os.path.basename(path)} 已存在（Lead 手动版），"
              f"改为写入 {os.path.basename(out)} 供对照，不覆盖。")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(plan, fh, ensure_ascii=False, indent=2)
    print(f"✓ 已写入 {os.path.relpath(out, ROOT)}（{len(plan)} 个候选）")


def main():
    ap = argparse.ArgumentParser(description="官方探测分析")
    ap.add_argument("--plan", action="store_true", help="生成次日候选计划文件")
    args = ap.parse_args()

    official = load_jsonl(OFF)
    if not official:
        print("暂无数据（runs/official_results.jsonl 为空或不存在）。")
        return 0

    pairs = build_pairs()
    print(f"# 官方探测分析（工具输出，数据截至 {max(p['submitted_at'] for p in pairs)}）\n")
    section_pairing(pairs)
    section_trend(pairs)
    section_ranking(pairs)
    section_plan(pairs, args.plan)
    return 0


if __name__ == "__main__":
    sys.exit(main())
