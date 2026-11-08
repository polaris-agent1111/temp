#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0302: Shot 4 真机出分捕获与全国第一绝杀点位校验.

只读本地 runs/ 数据，零网络、零提交。可重复运行：
- 战前（现在）: 输出绝杀边界灵敏度表 + 状态机推演（决策支持）；
- 战后（Shot 4 真机出分落盘后）: 自动捕获 Shot 4 真机出分并给出
  「已登顶→护城河」/「绝杀→Shot 5 概率」裁决。

关键纪律：
- runs/sequential_1108_state.json 的 13:26 会话是 DRY-RUN 演练
  (mock ~ uniform(117.5, 123.5))，其 118.1307 等绝不可当官方成绩引用；
  本脚本用「submissions.jsonl 佐证 + 日志 DRY-RUN 指纹」双重隔离 mock 数据。
"""
from __future__ import annotations

import json
import math
import sys
from datetime import date
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"
KILL_LINE = 117.0257          # 现任第一名成绩（光明未来），任务单给定的绝杀线
CATNET_LINE = 119.8293        # 前任第一名（口径参考）
BATTLE_DATE = date(2026, 11, 8)


def phi(z: float) -> float:
    """标准正态 CDF，仅用 math.erf，避免额外依赖。"""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


# ----------------------------------------------------------------------------
# 1) 真实数据捕获（本地文件，含 mock 隔离）
# ----------------------------------------------------------------------------

def load_submissions() -> list[dict]:
    p = RUNS / "submissions.jsonl"
    if not p.exists():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def load_state() -> dict | None:
    p = RUNS / "sequential_1108_state.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_controller_log() -> list[dict]:
    p = RUNS / "sequential_1108_log.jsonl"
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


def quarantine_check(state: dict | None, subs: list[dict], logrows: list[dict]) -> dict:
    """mock 指纹隔离：DRY-RUN 日志指纹 + submissions.jsonl 佐证缺失。"""
    if not state:
        return {"quarantined": True, "reason": "state 文件不存在（尚无任何会话）"}
    dry_marks = [r for r in logrows if "DRY-RUN" in str(r.get("msg", ""))]
    reason_bits = []
    if any("[DRY-RUN 离线仿真]" in str(r.get("msg", "")) for r in logrows):
        reason_bits.append("控制器日志含 [DRY-RUN 离线仿真] 会话指纹")
    scores = [h.get("download_seconds") for h in state.get("history", [])
              if h.get("download_seconds")]
    if scores and all(117.5 <= s <= 123.5 for s in scores):
        reason_bits.append(f"全部 {len(scores)} 个出分落入 mock 均匀带 [117.5,123.5]")
    battle_sub = [r for r in subs
                  if str(r.get("date", "")) == BATTLE_DATE.isoformat()]
    if not battle_sub:
        reason_bits.append(f"submissions.jsonl 无 {BATTLE_DATE} 当日提交记录佐证")
    quarantined = bool(reason_bits)
    return {
        "quarantined": quarantined,
        "reason": "；".join(reason_bits) if reason_bits else "通过佐证核验",
        "dry_run_log_lines": len(dry_marks),
        "battle_date_submissions": len(battle_sub),
    }


def real_shot4_score(subs: list[dict]) -> dict | None:
    """从 submissions.jsonl 捕获 11/08 Shot 4 的真实提交记录（有则返回）。"""
    hits = [r for r in subs
            if str(r.get("date", "")) == BATTLE_DATE.isoformat()
            and "Shot 4" in str(r.get("note", ""))]
    return hits[-1] if hits else None


# ----------------------------------------------------------------------------
# 2) 绝杀边界数学
# ----------------------------------------------------------------------------

def p_single_kill(mu: float, sigma: float, line: float = KILL_LINE) -> float:
    if sigma <= 0:
        return 1.0 if mu < line else 0.0
    return phi((line - mu) / sigma)


def p_best_of_n_kill(mu: float, sigma: float, n: int, line: float = KILL_LINE) -> float:
    p = p_single_kill(mu, sigma, line)
    return 1.0 - (1.0 - p) ** n


def sensitivity_table() -> list[dict]:
    rows = []
    mus = [116.0, 116.5, 117.0, 117.25, 117.5, 118.0, 119.0, 120.0, 121.0]
    sigmas = [1.0, 1.5, 2.0, 3.0, 4.5, 13.4]
    for mu in mus:
        for sg in sigmas:
            rows.append({
                "mu_official": mu,
                "sigma_official": sg,
                "p_single_kill": round(p_single_kill(mu, sg), 4),
                "p_best_of_2": round(p_best_of_n_kill(mu, sg, 2), 4),
                "p_best_of_5": round(p_best_of_n_kill(mu, sg, 5), 4),
            })
    return rows


NAMED_SCENARIOS = [
    {
        "name": "S1 乐观（Lead 计划口径：crown 官方预期 116.5~118s 取中）",
        "mu": 117.25, "sigma": 1.5,
        "basis": "任务单/候选池 note 自述「官方预期 116.5~118s」，取中值 117.25、窄方差",
    },
    {
        "name": "S2 中性（0235 先验：固定 champ P(top1)≈11%）",
        "mu": None, "sigma": None, "fixed_p": 0.11,
        "basis": "batch_0235 时序不变性定理下的 P(top1)≈11%（champ 族代理锚点）",
    },
    {
        "name": "S3 悲观大方差（0297 Model B：官方残差 σ≈13.4，μ 沿用计划中值）",
        "mu": 117.25, "sigma": 13.4,
        "basis": "fast14 官方对 (140.02, 155.16) 隐含 σ̂≈13.4；μ 仍取计划中值",
    },
]


def named_scenario_table() -> list[dict]:
    out = []
    for sc in NAMED_SCENARIOS:
        if sc.get("fixed_p") is not None:
            p1 = sc["fixed_p"]
        else:
            p1 = p_single_kill(sc["mu"], sc["sigma"])
        out.append({
            "name": sc["name"],
            "assumption": sc["basis"],
            "p_single_kill": round(p1, 4),
            "p_two_shot_kill": round(1.0 - (1.0 - p1) ** 2, 4),
            "p_five_shot_kill": round(1.0 - (1.0 - p1) ** 5, 4),
        })
    return out


# ----------------------------------------------------------------------------
# 3) 决策状态机推演（与 tools/sequential_adaptive_1108.py 的门限一致）
# ----------------------------------------------------------------------------

def gate_replay() -> list[dict]:
    """对 Shot 4 官方出分 s4 网格，重放控制器门限并给出裁决语义。"""
    rows = []
    for s4 in [116.5, 117.0, 117.0257, 117.5, 118.0, 119.8293, 120.0, 121.0,
               122.0, 124.37, 130.0, 143.56]:
        if s4 <= KILL_LINE:
            action = "已登顶全国第一 → Shot 4/5 转入护城河（稳健标杆/平台自检）"
            p_final = 1.0
        elif s4 <= 121.0:
            # crown_fusion 绝杀：P(X5 < 117.0257)，给 S1/S3 两种口径
            p_s1 = p_single_kill(117.25, 1.5)
            p_s3 = p_single_kill(117.25, 13.4)
            action = (f"绝杀窗口（距榜首 {s4 - KILL_LINE:.2f}s）→ Shot 5 crown_fusion；"
                      f"补刀命中概率 S1={p_s1:.3f} / S3={p_s3:.3f}")
            p_final = None
        else:
            action = ">121s → 防守堡垒拉均值中位数，放弃绝杀保顺位"
            p_final = None
        rows.append({"s4_official": s4, "controller_branch": action,
                     "p_final_top1": p_final})
    return rows


def main() -> int:
    subs = load_submissions()
    state = load_state()
    logrows = load_controller_log()

    shot4 = real_shot4_score(subs)
    quar = quarantine_check(state, subs, logrows)

    print("=" * 72)
    print("0302 Shot 4 真机出分捕获与绝杀点位校验（本地只读，零网络）")
    print("=" * 72)
    print(f"[数据甄别] state 源: runs/sequential_1108_state.json")
    print(f"[数据甄别] 隔离判定: quarantined={quar['quarantined']}")
    print(f"[数据甄别] 理由: {quar['reason']}")
    if quar["quarantined"]:
        print("[数据甄别] → 现存 state 为 DRY-RUN 演练，其出分一律不得引用为官方成绩。")
    if shot4:
        print(f"[捕获] 11/08 Shot 4 真实提交记录: at={shot4.get('at')} "
              f"note={shot4.get('note')} exit={shot4.get('exit_code')}")
        print("[捕获] 真机出分需以官方榜单 API 出分为准（poll_for_new_score 捕获），")
        print("       本脚本只做提交记录佐证；出分写入 state 后重跑即自动裁决。")
    else:
        print(f"[捕获] {BATTLE_DATE} Shot 4 尚无真实提交记录 —— 战役未开始（00:05 开火），")
        print("       以下输出为战前决策支持（绝杀边界灵敏度），全部基于真实 11/07 数据与明确标注的假设。")

    print()
    print("[11/07 真实基线] 夜战五发官方出分（runs/sequential_adaptive_log.jsonl）:")
    real_scores = {
        "Shot1 probe-tb-r36": 143.561,
        "Shot2 fallback-leak-fast": 124.3683,
        "Shot3 champ-98M-96M": 143.1357,
        "Shot4 asym-fast14": 140.0247,
        "Shot5 asym-fast14": 155.1607,
    }
    for k, v in real_scores.items():
        print(f"    {k}: {v}s")
    best_1107 = min(real_scores.values())
    print(f"    当日最佳 {best_1107}s（距绝杀线 {KILL_LINE} 差 {best_1107 - KILL_LINE:.2f}s）")

    print()
    print("[绝杀边界] 单发命中概率 p = Phi((117.0257 - mu)/sigma)：")
    print(f"{'mu\\sig':>8}", *[f"{s:>8.1f}" for s in [1.0, 1.5, 2.0, 3.0, 4.5, 13.4]])
    for mu in [116.0, 116.5, 117.0, 117.25, 117.5, 118.0, 119.0, 120.0, 121.0]:
        cells = [f"{p_single_kill(mu, s):8.4f}" for s in [1.0, 1.5, 2.0, 3.0, 4.5, 13.4]]
        print(f"{mu:>8.2f}", *cells)
    print("    （σ=13.4 列对应 0297 Model B 官方残差口径；大 σ 下「漏网」概率同样上升，")
    print("      但榜单按最好一发展示，差发不扣分，故 top1 目标下方差友好看待两头发。）")

    print()
    print("[三场景命名锚点]")
    for row in named_scenario_table():
        print(f"    {row['name']}")
        print(f"        单发 p={row['p_single_kill']}, 两发 1-(1-p)^2={row['p_two_shot_kill']}, "
              f"五发 1-(1-p)^5={row['p_five_shot_kill']}")
        print(f"        依据: {row['assumption']}")

    print()
    print("[门限重放] Shot 4 官方出分 s4 → 控制器分支与裁决语义：")
    for row in gate_replay():
        print(f"    s4={row['s4_official']:>9} → {row['controller_branch']}")

    print()
    print("[结论要点]")
    print("  1) 绝杀硬门限: 官方出分 < 117.0257s（光明未来现任榜首）。")
    print("  2) S1 乐观口径下两发 crown 合计命中概率 ~0.68；S2 中性口径 ~0.21；")
    print("     绝杀是「概率事件」而非「确定事件」，任何『已夺第一』表述在真机出分前均不成立。")
    print("  3) 榜首线是移动目标：若光明未来/Catnet 复测走低，绝杀线相应下移，")
    print("     需在 Shot 4/5 出分窗口内以 ≤10s 级轮询确认实时榜首（0296 结论：30s 轮询会漏 10s 级窗口）。")
    print("  4) 本脚本战后可复跑：state 出现 11/08 真实记录（submissions.jsonl 佐证 + 无 DRY-RUN 指纹）")
    print("     时自动切换到「捕获→裁决」模式。")

    # 落盘结构化结果（写入 zcode/scripts/，不触碰 runs/）
    out = {
        "task": "0302",
        "generated_by": "zcode/scripts/capture0302_shot4_killline.py",
        "kill_line": KILL_LINE,
        "catnet_reference": CATNET_LINE,
        "battle_date": BATTLE_DATE.isoformat(),
        "quarantine": quar,
        "real_1107_night_scores": real_scores,
        "battle_date_shot4_submission_found": bool(shot4),
        "sensitivity": sensitivity_table(),
        "named_scenarios": named_scenario_table(),
        "gate_replay": gate_replay(),
    }
    out_path = Path(__file__).resolve().parent / "capture0302_output.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[落盘] {out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
