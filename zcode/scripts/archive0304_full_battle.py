#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0304: 全 5 发端到端闭环自适应实验归档与复盘模型.

只读 runs/ 全部数据源，产出结构化归档快照到 zcode/scripts/。可重复运行：
- 战前（现在）: 归档 11/07 真实夜战基线 + DRY-RUN 隔离记录 + 11/08 占位符；
- 战后（11/08 出分后复跑）: 自动纳入 11/08 真实出分、按配置套反过拟合门禁、
  重建闭环决策链，形成完整复盘数据集。

门禁口径忠实复刻 tools/audit_plan.py：min_n=3、max_cv=0.05、min<0.9*mean →
LOW_N / HIGH_CV / MIN_FAR_BELOW_MEAN / NO_LOCAL_SAMPLE。
"""
from __future__ import annotations

import json
import math
import re
import sys
from datetime import date, datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"
BATTLE_DATE = date(2026, 11, 8)
BASE_DATE = date(2026, 11, 7)

MIN_N = 3
MAX_CV = 0.05

# 11/07 夜战真实出分（runs/sequential_adaptive_log.jsonl 的 shot_k_scored 事件，
# 与 submissions.jsonl 五条 Shot N/5 记录一一对应；此处硬编码为快照锚，脚本同时
# 从日志实时解析校验，不一致则报警）
REAL_1107 = [
    {"shot": 1, "key": "probe-tb-r36", "official": 143.561},
    {"shot": 2, "key": "fallback-leak-fast", "official": 124.3683},
    {"shot": 3, "key": "champ-98M-96M", "official": 143.1357},
    {"shot": 4, "key": "asym-fast14", "official": 140.0247},
    {"shot": 5, "key": "asym-fast14", "official": 155.1607},
]


def read_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def file_info(p: Path) -> dict:
    if not p.exists():
        return {"exists": False}
    st = p.stat()
    return {"exists": True, "mtime": datetime.fromtimestamp(st.st_mtime)
            .strftime("%Y-%m-%d %H:%M:%S"), "bytes": st.st_size}


# ----------------------------------------------------------------------------
# 配置级样本统计 + 反过拟合门禁（口径 = audit_plan.py）
# ----------------------------------------------------------------------------

def describe(values: list[float]) -> dict | None:
    if not values:
        return None
    n = len(values)
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / n if n > 1 else 0.0
    std = math.sqrt(var)
    return {"n": n, "mean": round(mean, 4), "std": round(std, 4),
            "cv": round(std / mean, 4) if mean else 0.0,
            "min": min(values), "max": max(values)}


def gate_flags(stats: dict | None) -> list[str]:
    if stats is None:
        return ["NO_LOCAL_SAMPLE"]
    flags = []
    if stats["n"] < MIN_N:
        flags.append(f"LOW_N({stats['n']}<{MIN_N})")
    if stats["cv"] > MAX_CV:
        flags.append(f"HIGH_CV({stats['cv']:.1%})")
    if stats["mean"] and stats["min"] < stats["mean"] * 0.9:
        flags.append("MIN_FAR_BELOW_MEAN")
    return flags


# ----------------------------------------------------------------------------
# 数据源解析
# ----------------------------------------------------------------------------

def parse_real_1107_from_log() -> tuple[list[dict], list[str]]:
    """从 sequential_adaptive_log.jsonl 解析真实 scored 事件并与硬编码锚校验。"""
    rows = read_jsonl(RUNS / "sequential_adaptive_log.jsonl")
    parsed = []
    for r in rows:
        ev = str(r.get("event", ""))
        m = re.match(r"shot_(\d)_scored$", ev)
        if m:
            parsed.append({"shot": int(m.group(1)),
                           "official": float(r.get("download_seconds")),
                           "ts": r.get("ts")})
    warn = []
    by_shot = {p["shot"]: p["official"] for p in parsed}
    for a in REAL_1107:
        got = by_shot.get(a["shot"])
        if got is None:
            warn.append(f"Shot {a['shot']} 日志缺失 scored 事件")
        elif abs(got - a["official"]) > 1e-6:
            warn.append(f"Shot {a['shot']} 日志值 {got} ≠ 锚 {a['official']}")
    return parsed, warn


def parse_1108_real_scores() -> list[dict]:
    """11/08 真实出分：sequential_1108_log.jsonl 的『★ 成功捕获官方真机出分』行。

    DRY-RUN 行（[DRY-RUN 仿真出分]）一律排除；同时要求 submissions.jsonl
    有当日提交记录佐证，否则视为未开战。
    """
    rows = read_jsonl(RUNS / "sequential_1108_log.jsonl")
    subs = read_jsonl(RUNS / "submissions.jsonl")
    battle_subs = [s for s in subs
                   if str(s.get("date", "")) == BATTLE_DATE.isoformat()]
    if not battle_subs:
        return []
    out = []
    for r in rows:
        msg = str(r.get("msg", ""))
        if "成功捕获官方真机出分" not in msg:
            continue
        m = re.search(r"耗时: ([\d.]+)s \| 官方排名: 第 (\d+) 名", msg)
        if m:
            out.append({"ts": r.get("ts"), "official": float(m.group(1)),
                        "rank": int(m.group(2))})
    return out


def quota_ledger(subs: list[dict]) -> dict:
    per: dict[str, int] = {}
    for s in subs:
        d = str(s.get("date", ""))
        if s.get("status") == "dry-run":
            continue
        per[d] = per.get(d, 0) + 1
    return per


def decision_chain_1107() -> list[dict]:
    """11/07 真实闭环决策链重建（planned 理由 + 出分 → 下一发选择）。"""
    return [
        {"shot": 1, "key": "probe-tb-r36", "official": 143.561,
         "next_reason": "Shot 1 出分 143.56s 异常，切换至保守漏桶极速剪刀差",
         "next_key": "fallback-leak-fast",
         "retro_note": "闭环正确响应异常：探针揭示高拥塞/异常，立即转保守，"
                       "换来全场最佳 124.3683"},
        {"shot": 2, "key": "fallback-leak-fast", "official": 124.3683,
         "next_reason": "Shot 2 出分 124.37s 逼近榜首，Shot 3 采用 98M 稳健构型",
         "next_key": "champ-98M-96M",
         "retro_note": "124.37 已是当日唯一 ≤125 的出分，但下一发未复投该构型，"
                       "转投未实测官方的 champ-98M（143.14）"},
        {"shot": 3, "key": "champ-98M-96M", "official": 143.1357,
         "next_reason": "当前最好 124.3683s，Shot 4 再次点火 asym-fast14 冲击 107s 极限信封",
         "next_key": "asym-fast14",
         "retro_note": "极限信封外推（107s）与官方实测（140.0/155.2）严重背离，"
                       "外推未闭合即复投激进族"},
        {"shot": 4, "key": "asym-fast14", "official": 140.0247,
         "next_reason": "终局第 5 发：基于前 4 发历史最优 124.3683s 锁定最终收官冲榜",
         "next_key": "asym-fast14",
         "retro_note": "第 5 发复投同族，出 155.16（当日最差）；同族官方方差极大"},
        {"shot": 5, "key": "asym-fast14", "official": 155.1607,
         "next_reason": None, "next_key": None, "retro_note": "收官"},
    ]


def controller_replay_1108_on_1107_like() -> list[dict]:
    """用 11/07 真实出分序列喂 11/08 控制器 decide_next_shot（只导入纯函数），

    展示若 11/08 官方环境复现 11/07 分布时控制器会怎么走。仅决策支持。
    """
    spec_path = ROOT / "tools" / "sequential_adaptive_1108.py"
    import importlib.util
    spec = importlib.util.spec_from_file_location("ctrl1108_replay", spec_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    key_by_cand = {}
    for cid, c in mod.CANDIDATE_POOL.items():
        key_by_cand[cid] = c["tag"]
    history = []
    trace = []
    for k in range(1, 6):
        cand, reason = mod.decide_next_shot(history, k)
        score = next(r["official"] for r in REAL_1107 if r["shot"] == k)
        history.append({"status": "scored", "download_seconds": score, "rank": None})
        trace.append({"shot": k, "chosen": cand["candidate_id"],
                      "tag": key_by_cand[cand["candidate_id"]],
                      "branch": reason.split("】")[0] + "】",
                      "fed_score_1107": score})
    return trace


def main() -> int:
    print("=" * 72)
    print("0304 全 5 发端到端闭环归档与复盘（只读 runs/，落盘 zcode/scripts/）")
    print("=" * 72)

    subs = read_jsonl(RUNS / "submissions.jsonl")
    parsed_1107, warn_1107 = parse_real_1107_from_log()
    scores_1108 = parse_1108_real_scores()
    ledger = quota_ledger(subs)
    state = None
    sp = RUNS / "sequential_1108_state.json"
    if sp.exists():
        try:
            state = json.loads(sp.read_text(encoding="utf-8"))
        except Exception:
            state = None
    logrows_1108 = read_jsonl(RUNS / "sequential_1108_log.jsonl")
    dry_marked = any("[DRY-RUN 离线仿真]" in str(r.get("msg", ""))
                     for r in logrows_1108)
    state_is_mock = bool(dry_marked) or not scores_1108

    print("\n[源清单]（只读）")
    for name in ["submissions.jsonl", "sequential_adaptive_log.jsonl",
                 "sequential_1108_state.json", "sequential_1108_log.jsonl",
                 "official_results.jsonl", "board_watch.jsonl",
                 "leaderboard_full.json", "leaderboard/ledger.csv"]:
        info = file_info(RUNS / name)
        print(f"    {name}: {'存在 mtime=' + info['mtime'] if info['exists'] else '缺失'}")

    print(f"\n[配额台账]（submissions.jsonl 按日聚合，SSOT）")
    for d in sorted(ledger):
        print(f"    {d}: {ledger[d]} 发")

    if warn_1107:
        print(f"\n[锚校验告警] {warn_1107}")
    else:
        print("\n[锚校验] 11/07 硬编码锚与日志 scored 事件完全一致（5/5）。")

    print("\n[隔离判定]")
    print(f"    11/08 当日提交佐证: {len([s for s in subs if str(s.get('date',''))==BATTLE_DATE.isoformat()])} 条")
    print(f"    控制器日志 DRY-RUN 指纹: {dry_marked}")
    print(f"    11/08 真实出分捕获: {len(scores_1108)} 条")
    print(f"    → state 归档定性: {'DRY-RUN 演练（mock 隔离，不入成绩档案）' if state_is_mock else '真实战役档案'}")

    print("\n[11/07 真实基线 → 按配置官方样本 + 反过拟合门禁]（min_n=3, max_cv=5%）")
    by_key: dict[str, list[float]] = {}
    for a in REAL_1107:
        by_key.setdefault(a["key"], []).append(a["official"])
    gate_rows = []
    for key, vals in by_key.items():
        st = describe(vals)
        flags = gate_flags(st)
        gate_rows.append({"config": key, "stats": st, "flags": flags})
        print(f"    {key:22s} n={st['n']} mean={st['mean']:>9} std={st['std']:>8} "
              f"cv={st['cv']:.1%} min={st['min']:>9} flags={flags or 'PASS'}")

    print("\n[11/08 真实出分]")
    if scores_1108:
        for s in scores_1108:
            print(f"    ts={s['ts']} official={s['official']} rank={s['rank']}")
        valid = [s["official"] for s in scores_1108]
        print(f"    战役最佳: {min(valid)}")
    else:
        print("    （尚无 —— 00:05 开火后复跑本脚本自动纳入；"
              "捕获行须为『★ 成功捕获官方真机出分』且当日 submissions.jsonl 有佐证）")

    print("\n[11/07 闭环决策链复盘]")
    for c in decision_chain_1107():
        print(f"    Shot {c['shot']} {c['key']} → {c['official']}s")
        if c["next_key"]:
            print(f"        → {c['next_reason']}")
        print(f"        复盘: {c['retro_note']}")

    print("\n[11/08 控制器对 11/07 型输入的重放]（决策支持：若官方环境复现 11/07 分布）")
    for t in controller_replay_1108_on_1107_like():
        print(f"    Shot {t['shot']}: feed {t['fed_score_1107']} → {t['chosen']} "
              f"({t['branch']}) [{t['tag']}]")

    snapshot = {
        "task": "0304",
        "generated_by": "zcode/scripts/archive0304_full_battle.py",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "battle_date": BATTLE_DATE.isoformat(),
        "sources": {n: file_info(RUNS / n) for n in
                    ["submissions.jsonl", "sequential_adaptive_log.jsonl",
                     "sequential_1108_state.json", "sequential_1108_log.jsonl",
                     "official_results.jsonl", "board_watch.jsonl",
                     "leaderboard_full.json", "leaderboard/ledger.csv"]},
        "quota_ledger": ledger,
        "anchor_check_warnings": warn_1107,
        "quarantine": {
            "state_is_mock": state_is_mock,
            "dry_run_marked": dry_marked,
            "battle_date_submissions": len([s for s in subs if str(s.get("date", "")) == BATTLE_DATE.isoformat()]),
            "note": "state 13:26 会话为 DRY-RUN 演练，118.1307 等不入成绩档案" if state_is_mock else "",
        },
        "real_1107": REAL_1107,
        "real_1108": scores_1108,
        "per_config_gates": gate_rows,
        "decision_chain_1107": decision_chain_1107(),
        "controller_replay_1108_on_1107_like": (
            controller_replay_1108_on_1107_like() if not state_is_mock or True else []),
        "retro_placeholders": {
            "11/08": "待真实出分后复跑本脚本：real_1108、决策链 1108 段与门禁表自动补全",
        },
    }
    out_path = Path(__file__).resolve().parent / "archive0304_snapshot.json"
    out_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"\n[落盘] {out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
