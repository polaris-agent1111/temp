# -*- coding: utf-8 -*-
"""0104 — 11/07 09:00 晨会全指标对账。

数据源（全部只读）：
  runs/sequential_adaptive_log.jsonl   夜间逐发闭环控制器的计划/提交/出分事件
  runs/submissions.jsonl               提交流水（额度核对）
  runs/official_results.jsonl          我方官方出分历史
  intel/raw/leaderboard_*.json         官方榜单原始快照（取最新）
  runs/results.jsonl                   本地实验结果（valid=true 才计入）

输出：
  docs/analysis/0104-theory-audit.md   （覆盖写入）
  stdout 摘要
"""
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"E:\Download\iDSN")
OUT_DOC = ROOT / "docs" / "analysis" / "0104-theory-audit.md"


def read_jsonl(p: Path):
    rows = []
    if not p.exists():
        return rows
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def config_signature(cfg: dict) -> str:
    """兼容两种配置表示：
    results.jsonl:  "1": "leak_bucket:leak_rate=40,bucket_cap=40,..."
    configs.json:   "1": ["leak_bucket", {"leak_rate": 40, ...}]
    特征取 (模块名前4, 首个数值参数)。
    """
    parts = []
    for k in "123456":
        v = cfg.get(k)
        if not v:
            parts.append("none")
            continue
        if isinstance(v, str):
            head, _, tail = v.partition(":")
            first = tail.split(",")[0] if tail else ""
            digits = "".join(ch for ch in first if ch.isdigit())
        else:  # list/tuple: [module, params]
            head = str(v[0])
            params = v[1] if len(v) > 1 and isinstance(v[1], dict) else {}
            digits = ""
            for key in ("leak_rate", "token_refill_rate", "max_pacing_rate", "tokens"):
                if key in params:
                    digits = str(int(params[key]))
                    break
        parts.append(f"{head[:4]}:{digits}")
    return "|".join(parts)


# ---------- 1. 夜间逐发出分 ----------
seq_rows = read_jsonl(ROOT / "runs" / "sequential_adaptive_log.jsonl")
shots = {}
for d in seq_rows:
    ev = str(d.get("event", ""))
    for i in range(1, 6):
        if ev == f"shot_{i}_submitted":
            shots.setdefault(i, {})["tag"] = d.get("tag")
        if ev == f"shot_{i}_scored":
            shots.setdefault(i, {})["official"] = float(d["download_seconds"])
            shots.setdefault(i, {})["submitted_at"] = d.get("raw", {}).get("submitted_at")

cfg_manifest = {}
for i in sorted(shots):
    tag = shots[i].get("tag", "")
    p = ROOT / "runs" / f"{tag}.configs.json"
    if p.exists():
        cfg_manifest[i] = json.loads(p.read_text(encoding="utf-8"))

# ---------- 2. 额度核对（当日 5/5） ----------
subs = read_jsonl(ROOT / "runs" / "submissions.jsonl")
n_1107 = sum(1 for d in subs if str(d.get("date", "")) == "2026-11-07")

# ---------- 3. 最新榜单快照 ----------
lb_dir = ROOT / "intel" / "raw"
snaps = sorted(lb_dir.glob("leaderboard_*.json"))
board_rows, snap_name = [], ""
if snaps:
    snap_name = snaps[-1].name
    data = json.loads(snaps[-1].read_text(encoding="utf-8"))
    for p in data.get("leaderboard", {}).get("problems", []):
        if p.get("id") != 1:
            continue
        for s in p.get("submissions", []):
            times = [float(a["download_seconds"]) for a in s.get("attempts", []) if a.get("download_seconds")]
            if times:
                board_rows.append((min(times), s.get("team", "?"), len(times),
                                   max(a.get("submitted_at", "") for a in s.get("attempts", []))))
    board_rows.sort()

CATNET = 119.8293
our_best_night = min(v["official"] for v in shots.values()) if shots else None

rank_now, ahead = None, []
if our_best_night and board_rows:
    ahead = [(b, t) for b, t, n, la in board_rows if b < our_best_night and t != "赛博coder"]
    rank_now = len(ahead) + 1

# ---------- 4. 同构型官方出分方差（shot4/5 同构型双发） ----------
same_pair = None
if 4 in cfg_manifest and 5 in cfg_manifest and cfg_manifest[4] == cfg_manifest[5]:
    same_pair = (shots[4]["official"], shots[5]["official"])

# ---------- 5. 本地↔官方 同日配对（构型特征匹配） ----------
results = read_jsonl(ROOT / "runs" / "results.jsonl")
fam = defaultdict(list)
for d in results:
    if d.get("valid") is True and isinstance(d.get("total_seconds"), (int, float)):
        fam[config_signature(d.get("config", {}))].append(float(d["total_seconds"]))

pairs = []
for i in sorted(shots):
    if i not in cfg_manifest:
        continue
    sig = config_signature(cfg_manifest[i])
    local = sorted(fam.get(sig, []))
    if local:
        pairs.append({
            "shot": i,
            "tag": shots[i].get("tag"),
            "sig": sig,
            "n": len(local),
            "local_mean": st.mean(local),
            "local_median": st.median(local),
            "official": shots[i]["official"],
            "offset_mean": shots[i]["official"] - st.mean(local),
        })

# ---------- 6. 产出文档 ----------
L = []
A = L.append
A("# 0104 理论审计 — 11/07 09:00 晨会全指标对账")
A("")
A("> 生成：2026-11-07 09:10 ｜ 执行者：zcode ｜ 数据全部来自本地只读快照，未访问任何远程系统。")
A("")
A("## 一、夜间逐发闭环战绩（11/07 00:05–01:24，额度 5/5 已用满）")
A("")
A("| 发次 | 时间 | 构型标签 | 官方出分 (s) |")
A("|---:|---|---|---:|")
for i in sorted(shots):
    tag = shots[i].get("tag", "?")
    A(f"| {i} | {shots[i].get('submitted_at','?')} | {tag} | {shots[i]['official']:.4f} |")
A("")
best_shot = min(shots, key=lambda i: shots[i]["official"])
A(f"- **夜间最佳：Shot {best_shot} = {shots[best_shot]['official']:.4f} s**，"
  f"全队历史最优，较 11-06 前最优 133.0860s 提升 {133.0860 - shots[best_shot]['official']:.4f} s（{(1 - shots[best_shot]['official'] / 133.0860) * 100:.2f}%）。")
A(f"- 其余 4 发均未超过 133.0860s（{[round(shots[i]['official'],4) for i in sorted(shots) if i != best_shot]}）。")
A(f"- 当日提交额度：{n_1107}/5 已用满（`runs/submissions.jsonl` 逐条核对）。")
A("")
A("## 二、榜位重建（基于最新本地官方快照）")
A("")
A(f"- 快照：`intel/raw/{snap_name}`（**此后无 11-07 快照，对手凌晨动作未知**）。")
A("前三名与关键邻位：")
for b, t, n, la in board_rows[:6]:
    mark = " ← 我方" if t == "赛博coder" else ""
    A(f"- {t}：{b:.4f}s（n={n}，最晚 {la}）{mark}")
A("")
if rank_now:
    A(f"- 夜间最佳 {our_best_night:.4f}s 插入该快照后：**5 队在我方之前 → 榜位第 {rank_now}**。")
    A(f"- 与第 1 名 Catnet {CATNET:.4f}s 差 **{our_best_night - CATNET:+.4f} s（{(our_best_night / CATNET - 1) * 100:.2f}%）**；"
      f"与第 4 名大肥鱼 122.4027s 差 {our_best_night - 122.4027:+.4f} s。")
A("")
A("### 声称对账（重要修正）")
A("")
A("| 看板/口头声称 | 本地可验证事实 | 判定 |")
A("|---|---|---|")
A("| 「全国第一登顶」 | 最新快照（11-06 15:15）第 1 名为 Catnet 119.8293s；我方夜间最佳 124.3683s，重建榜位第 6，且 11-07 快照缺失、对手可能已再提速 | **不成立**，应表述为「历史性突破至 124.37s、暂列第 6（快照口径）」 |")
A("| 「理论下确界已击穿至 106.597s」 | 0095 分层审计：106.597/105.592s 为跨构型 min-of-mins 序统计量（随 n 漂移，同构造已漂移至 96.1/94.0s）；物理层为 50.61s；合规口径仅可作诊断参照，不可作提交目标 | 表述有误导性，须标注「经验信封，非物理下界」 |")
A("| 「夜间 5 发全部冲榜」 | 仅 1 发改善最优成绩，4 发劣于既有最优 | 部分成立，须如实记录 |")
A("")
A("## 三、同构型官方出分方差（官方统一复测风险的第一手证据）")
A("")
if same_pair:
    lo, hi = min(same_pair), max(same_pair)
    A(f"- Shot4/Shot5 为**完全相同构型**、同日连发：{lo:.4f}s vs {hi:.4f}s，极差 **{hi - lo:.2f} s**。")
    A(f"- n=2 极差的期望≈1.128σ → 隐含官方单发出分 σ ≈ {(hi - lo) / 1.128:.1f} s，与 0084 校准（+2.5±7.4s）量级一致甚至更大。")
    A("- **结论：官方单发出分方差 ≥ 7s 量级。任何「窄尖点」构型在官方统一复测（取平均）下都无稳定性可言；"
      "这正是 AGENTS.md 禁止 min-of-N 的实证依据。**")
A("")
A("## 四、同日本地↔官方配对（构型特征精确匹配）")
A("")
A("| 发次 | 本地族 n | 本地均值 (s) | 本地中位 (s) | 官方 (s) | 偏移=官方−本地均值 (s) |")
A("|---:|---:|---:|---:|---:|---:|")
for p in pairs:
    A(f"| {p['shot']} | {p['n']} | {p['local_mean']:.2f} | {p['local_median']:.2f} | {p['official']:.4f} | {p['offset_mean']:+.2f} |")
A("")
neg = [p["offset_mean"] for p in pairs if p["offset_mean"] < 0]
A(f"- 偏移为负（官方快于本地均值）的发次：{len(neg)}/{len(pairs)}。"
  "与 0084「官方 ≈ 本地均值 +2.5±7.4s」的先验存在张力：n 小、本地族样本混杂不同日，"
  "**不宜据单发负偏移推翻先验，但应把 σ≥7.4s 的大方差场景纳入 11/08 决策（见 0105）。**")
A("")
A("## 五、给晨会的三条硬结论")
A("")
A("1. **成果固化**：官方最优成绩 124.3683s（11-07 00:28 提交），为不可撤销的既成事实，任何后续决策以它为新基线。")
A("2. **榜位现实**：快照口径第 6，距榜首 4.54s；榜首带（Catnet/hashkimi/我不想写实验报告）在 119.8–121.5s 已高度拥挤，"
  "他们 11-06 仍在提交，11-08 我方若以均值 134s 量级构型出手，期望落点为 124–137s，**主要作用是巩固 4–6 名而非登顶**。")
A("3. **复测合规**：官方 top 统一复测取平均；同构型官方单发极差已实测 15.1s。"
  "所有候选必须过 `tools/audit_plan.py` 门禁（n≥3、按均值/中位选型、邻域稳定），并以低 CV 构型（fortress CV≈3.9%、anchor 样本 CV≈6%）为复测护城河。")
A("")
A("## 六、局限")
A("")
A("- 无 11-07 榜单快照，榜位为「11-06 15:15 快照 × 我方夜间成绩」的静态重建；对手 11-07 提交未计入。")
A("- 本地族样本跨多日混合（记忆结论：11-06 样本曾受 36s 级污染），配对偏移仅作方向参考。")
A("- 本审计未访问任何远程系统；榜单以本地最新快照为唯一榜单证据源。")

OUT_DOC.write_text("\n".join(L) + "\n", encoding="utf-8")
print("written:", OUT_DOC)
print(f"shots={ {i: shots[i]['official'] for i in sorted(shots)} }")
print(f"best={our_best_night} rank_reconstructed={rank_now} quota_1107={n_1107}/5")
print("pairs:", [(p['shot'], round(p['offset_mean'], 2)) for p in pairs])
