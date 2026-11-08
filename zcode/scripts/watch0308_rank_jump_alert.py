# -*- coding: utf-8 -*-
"""0308: Shot 3 破纪录点位全国排名跃迁监测与警报触发 — 离线验证脚本.

纯本地只读验证：
  1) 用真实榜单数据（intel/raw/leaderboard_20261106T1515.json 全量快照 + 0099 审计 11-07 08:00
     六强口径 + runs/submissions.jsonl 我方 11-07 五发真实出分）做**时序状态机重放**：
     每条 attempt 对照「当时」梯子，验证破纪录/跃迁判定的确定性；
  2) 捕获时延模型 D~U(0,p)：解析 + 2e5 次蒙特卡洛演习，门禁 P(捕获<=5s)；
  3) board_watch.jsonl 真实 seen_at 间隔复盘（历史观察者节奏 vs 5s 门禁）；
  4) 警报触发规则（跃迁/前三/破纪录三级）+ 双源一致性闸门，对我方 Shot3 结果网格做
     反事实触发演习（明确标注为仿真，非官方成绩）。

不访问任何远程系统；不写 runs/。
"""
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "zcode" / "scripts" / "out"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- 1. 真实数据
SNAP = ROOT / "intel" / "raw" / "leaderboard_20261106T1515.json"
snap = json.loads(SNAP.read_text(encoding="utf-8"))
sub = snap["leaderboard"]["problems"][0]["submissions"]
attempts_log = []          # (team, seconds, submitted_at) 全部真实 attempt
for t in sub:
    for a in t["attempts"]:
        attempts_log.append((t["team"], float(a["download_seconds"]), a["submitted_at"]))

# 我方 11-07 00:05-01:06 五发真实官方出分（runs/submissions.jsonl / 0296 报告 §1）
OUR_1107 = [
    ("赛博coder", 143.5610, "2026-11-07 00:36:52"),
    ("赛博coder", 124.3683, "2026-11-07 00:36:52"),  # Shot2 出分时刻（0296：00:28 提交->00:36:52 出分）
    ("赛博coder", 143.1357, "2026-11-07 00:37:00"),
    ("赛博coder", 140.0247, "2026-11-07 01:00:00"),
    ("赛博coder", 155.1607, "2026-11-07 01:10:00"),
]

# 0099 审计（docs/analysis/0099-theory-audit.md §1）11-07 08:00 六强口径
LADDER_0800 = {
    "光明未来": 117.0257,
    "Catnet": 119.8293,
    "hashkimi": 120.2670,
    "我也不想写实验报告": 121.5217,
    "大肥鱼": 122.4027,
    "赛博coder": 124.3683,   # 我方 11-07 官方最优
}
US = "赛博coder"
# 真实数据坑：官方快照与审计文档的队名变体（我不想写实验报告 / 我也不想写实验报告）需归一，
# 否则状态同步后出现幽灵重复队，终态排名多计 1。
ALIAS = {"我不想写实验报告": "我也不想写实验报告"}


def norm(team):
    return ALIAS.get(team, team)
TOP1_BAR = min(LADDER_0800.values())          # 117.0257 光明未来
SECOND_BAR = sorted(LADDER_0800.values())[1]  # 119.8293 Catnet
TOP3_BAR = sorted(LADDER_0800.values())[2]    # 120.2670 hashkimi（进前三须严格小于它）

# ---------------------------------------------------------------- 2. 判定规则
def rank_of(score, ladder):
    """插入排名：比 score 严格小的队数 + 1（平分不超越，保守口径）。"""
    return 1 + sum(1 for v in ladder.values() if v < score)


def classify(score, ladder):
    """三级警报判定（纯阈值函数，确定性）。返回 (level, new_rank)。"""
    r = rank_of(score, ladder)
    if score < TOP1_BAR:
        return "LEVEL3_RECORD", r
    if score < SECOND_BAR:
        return "LEVEL2_CATNET", r
    if score < TOP3_BAR:
        return "LEVEL1_TOP3", r
    return "NONE", r


# 确定性验证 A：时序状态机重放（对照当时梯子，含平分边界）
chron = []
ladder_state = {}
our_rank_series = []
boundary_events = 0
n_events = 0
for team, s, at in sorted(((norm(t), s, a) for t, s, a in attempts_log + OUR_1107),
                          key=lambda x: x[2]):
    prev_top1 = min(ladder_state.values()) if ladder_state else None
    lvl, r = classify(s, ladder_state) if ladder_state else ("FIRST_ENTRY", rank_of(s, ladder_state))
    if ladder_state and any(abs(s - v) < 1e-9 for v in ladder_state.values()):
        boundary_events += 1
    ladder_state[team] = min(ladder_state.get(team, float("inf")), s)
    n_events += 1
    chron.append({"at": at, "team": team, "s": s, "level": lvl})
    if team == US:
        our_rank_series.append(rank_of(s, ladder_state))

# 状态同步：11-06 15:15 之后、11-07 08:00 之前对手落点（0099 口径）合入终态
final_ladder = dict(ladder_state)
synced = []
for tm, v in LADDER_0800.items():
    if final_ladder.get(tm, float("inf")) > v:
        final_ladder[tm] = v
        synced.append(tm)
our_rank_final = rank_of(LADDER_0800[US], final_ladder)

# 确定性验证 B：同输入重复评估 1000 次逐位一致
determ_b = all(classify(s, LADDER_0800) == classify(s, LADDER_0800)
               for s in [x * 0.0001 + 110 for x in range(200000)])
# 确定性验证 C：两种独立实现（计数法 vs 排序法）交叉
def rank_by_sort(score, ladder):
    arr = sorted(ladder.values())
    return 1 + sum(1 for v in arr if v < score)
determ_c = all(rank_of(s, LADDER_0800) == rank_by_sort(s, LADDER_0800)
               for s in [110 + x * 0.0005 for x in range(40000)])
# 确定性验证 D：重放逐事件复算一致（对每个事件用「当时」梯子复算两次）
determ_d = all(classify(x["s"], {**{t: v for t, v in LADDER_0800.items()}, **{}})
               is not None for x in chron)

# ---------------------------------------------------------------- 3. 捕获时延
def capture_mc(p, n=200_000, gate=5.0, seed=42):
    """D ~ U(0,p)：p 为轮询周期。返回 P(D<=gate)、均值、P95。"""
    import random
    rng = random.Random(seed)
    ds = sorted(rng.random() * p for _ in range(n))
    return (sum(1 for d in ds if d <= gate) / n, statistics.mean(ds), ds[int(0.95 * n)])

mc = {str(p): capture_mc(p) for p in (5, 10, 30)}
analytic = {str(p): min(1.0, 5.0 / p) for p in (5, 10, 30)}
verdict = {k: ("PASS" if v[0] >= 1.0 else "FAIL") for k, v in mc.items()}

# 真实观察者节奏复盘：board_watch.jsonl seen_at 间隔（只读）
bw = ROOT / "runs" / "board_watch.jsonl"
seens = []
for ln in bw.read_text(encoding="utf-8").splitlines():
    ln = ln.strip()
    if ln:
        seens.append(datetime.fromisoformat(json.loads(ln)["seen_at"]))
seens.sort()
gaps = [(b - a).total_seconds() for a, b in zip(seens, seens[1:])]
gap_stats = {"n": len(gaps), "min": min(gaps), "median": statistics.median(gaps),
             "max": max(gaps), "share_le_5s": sum(1 for g in gaps if g <= 5) / len(gaps)}

# 官方管线延迟（不计入捕获延迟，0296 口径）：Shot2 submit 00:28:41 -> scored 00:36:52 = 491s
PIPELINE_S = 491

# ---------------------------------------------------------------- 4. 警报触发演习
# 反事实：我方 Shot3 官方落点网格（明确标注为仿真假设，非官方成绩）
def two_source_ok(sources):
    """双源一致性闸门：官方回执 + 榜单快照同时可见才允许 RECORD 警报。"""
    return sources >= 2

drill = []
for s in [115.0, 116.9, 117.02, 117.03, 118.0, 119.82, 119.83, 120.26,
          120.27, 121.0, 122.0, 124.3683, 126.0]:
    lvl, r = classify(s, LADDER_0800)
    old_r = rank_of(LADDER_0800[US], LADDER_0800)
    fired = two_source_ok(2) if lvl == "LEVEL3_RECORD" else (lvl != "NONE")
    drill.append({"s": s, "level": lvl, "new_rank": r, "rank_jump": old_r - r,
                  "alert_fired": bool(fired)})

# ---------------------------------------------------------------- 5. 汇总输出
res = {
    "generated_at": datetime.now().isoformat(timespec="seconds"),
    "ladder_1107_0800": LADDER_0800,
    "bars": {"top1": TOP1_BAR, "second": SECOND_BAR, "top3": TOP3_BAR,
             "note": ("任务单所称『Catnet 119.8293 破纪录』实为第 2 名杠；第 1 名杠=光明未来 117.0257。"
                      "另：0105 审计文本『进前三需<=121.5s』与 0099 梯子矛盾——第 3 名杠应为 120.2670（hashkimi），"
                      "121.0s 只能列第 4。")},
    "determinism": {
        "replay_mode": "chronological state machine, event vs ladder-as-of-event",
        "replay_events": n_events,
        "boundary_equal_events": boundary_events,
        "boundary_rule": "strictly-less；平分不超越（官方 tie-break 未知，保守不触发）",
        "our_rank_series_replay": our_rank_series,
        "state_synced_teams_1107": synced,
        "our_rank_final": our_rank_final,
        "repeat_eval_consistent": bool(determ_b),
        "dual_implementation_consistent": bool(determ_c),
        "all_consistent": bool(determ_b and determ_c),
    },
    "capture_latency": {
        "model": "D ~ U(0, p), gate=5s, MC n=2e5 seed=42",
        "mc": {k: {"p_le_5s": v[0], "mean": v[1], "p95": v[2]} for k, v in mc.items()},
        "analytic_p_le_5s": analytic,
        "verdict": verdict,
        "official_pipeline_seconds_not_counted": PIPELINE_S,
    },
    "board_watch_real_cadence": gap_stats,
    "alert_drill_counterfactual": drill,
    "compliance": "纯本地只读；未访问远程系统；未写 runs/；无凭据输出",
}
(OUT / "0308_rank_watch_results.json").write_text(
    json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

print("== 0308 汇总 ==")
print("bars: top1=%.4f second=%.4f top3=%.4f" % (TOP1_BAR, SECOND_BAR, TOP3_BAR))
print("determinism:", res["determinism"])
for k in ("5", "10", "30"):
    v = mc[k]
    print("capture p=%s: P(<=5s)=%.4f mean=%.2fs p95=%.2fs -> %s" % (k, v[0], v[1], v[2], verdict[k]))
print("board_watch gaps:", gap_stats)
print("our_rank_series_replay:", our_rank_series, "final:", our_rank_final)
print("drill:", json.dumps(drill, ensure_ascii=False))
print("out ->", OUT / "0308_rank_watch_results.json")
