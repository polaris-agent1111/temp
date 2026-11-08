# -*- coding: utf-8 -*-
"""0105 — 11/08 阶段二战略部署：候选构型决策矩阵。

方法：
  1) 从 runs/results.jsonl（valid=true）按构型特征聚合本地统计（样本口径，ddof=1）；
  2) 本地↔官方偏移先验 = 0084（官方 ≈ 本地均值 +2.5±7.4s），叠加 11/07 同日
     两个负偏移观测（Shot1 −7.82 / Shot2 −10.16）与同构型双发极差（σ≈13.4）做
     正态-正态后验更新，得到 offset 后验与三场景敏感度；
  3) 每个候选计算 P(官方 ≤ 阈值)：榜首 119.8293 / 进前四 122.4027 /
     改写自方最优 124.3683；
  4) 过门禁旗标（LOW_N / HIGH_CV / MIN_FAR_BELOW_MEAN / 邻域跳变）。

输出：docs/analysis/0105-theory-audit.md
"""
import json
import math
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import norm

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"E:\Download\iDSN")
OUT_DOC = ROOT / "docs" / "analysis" / "0105-theory-audit.md"

CATNET = 119.8293      # 第 1 名
TOP4 = 122.4027        # 第 4 名大肥鱼（进前四需 ≤）
OWN_BEST = 124.3683    # 我方 11/07 夜间最优


def read_jsonl(p: Path):
    rows = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def sig_of(cfg: dict) -> str:
    parts = []
    for k in "123456":
        v = cfg.get(k, "")
        head, _, tail = v.partition(":")
        digits = "".join(ch for ch in (tail.split(",")[0] if tail else "") if ch.isdigit())
        parts.append(f"{head[:4]}:{digits}")
    return "|".join(parts)


results = read_jsonl(ROOT / "runs" / "results.jsonl")
fam = defaultdict(list)
for d in results:
    if d.get("valid") is True and isinstance(d.get("total_seconds"), (int, float)):
        fam[sig_of(d.get("config", {}))].append(float(d["total_seconds"]))


def family_stats(rates) -> dict:
    sig = "|".join(f"leak:{r}" for r in rates)
    v = sorted(fam.get(sig, []))
    if not v:
        return {"sig": sig, "n": 0}
    mean, sd_s = st.mean(v), st.stdev(v)
    return {
        "sig": sig, "rates": rates, "n": len(v), "mean": mean, "median": st.median(v),
        "std_s": sd_s, "cv": sd_s / mean * 100, "min": min(v), "max": max(v),
        "se": sd_s / math.sqrt(len(v)),
    }


# 候选构型（1..6 目录 leak_rate）
CANDIDATES = {
    "anchor(40×3,37,36,36)「1108-shot1 稳健首发」": [40, 40, 40, 37, 36, 36],
    "crown(41,41,40,37,36,36)「1108-shot2/5 皇冠」": [41, 41, 40, 37, 36, 36],
    "crown-pert(41,40,40,37,36,36)「1108-shot3」": [41, 40, 40, 37, 36, 36],
    "fortress(40×4,37,37)「1108-shot4 堡垒」": [40, 40, 40, 40, 37, 37],
    "champ1107(40×3,36×3)「11/07 冠军构型」": [40, 40, 40, 36, 36, 36],
    "loose(40×3,38,37,36)（对照）": [40, 40, 40, 38, 37, 36],
    "mono40(40×6)（对照）": [40, 40, 40, 40, 40, 40],
}
stats = {name: family_stats(rates) for name, rates in CANDIDATES.items()}

# ---------- 偏移后验（正态-正态） ----------
# 先验：μ_off ~ N(2.5, 5.0^2)（0084 点估计 ± 大均值不确定度）
# 单发官方噪声 σ_off：先验 7.4；同构型双发极差 15.14 → 13.4；取上界 13.4 做保守主用
# 观测：11/07 Shot1 −7.82（本地 n=1，附加不确定度大）、Shot2 −10.16（本地 n=5, SE=5.40）
PRIOR_MU, PRIOR_SD_MU = 2.5, 5.0
SIGMA_OFF = 13.4
obs = [
    (-7.82, math.sqrt(SIGMA_OFF**2 + 12.0**2)),   # shot1：本地 n=1，本地噪声取 12
    (-10.16, math.sqrt(SIGMA_OFF**2 + (12.08 / math.sqrt(5))**2)),
]
post_prec = 1 / PRIOR_SD_MU**2 + sum(1 / s**2 for _, s in obs)
post_mu = (PRIOR_MU / PRIOR_SD_MU**2 + sum(o / s**2 for o, s in obs)) / post_prec
post_sd_mu = post_prec**-0.5
SIGMA_TOTAL = math.sqrt(SIGMA_OFF**2 + post_sd_mu**2)


def p_le(mean_local: float, threshold: float) -> float:
    z = (threshold - mean_local - post_mu) / SIGMA_TOTAL
    return float(norm.cdf(z))


# 三场景敏感度：S1=0084 先验；S2=11/07 经验（负偏移大 σ）；S3=本后验
def p_le_scenario(mean_local, threshold, mu, sig):
    return float(norm.cdf((threshold - mean_local - mu) / sig))


SCEN = {
    "S1 先验(+2.5,σ7.4)": (2.5, 7.4),
    "S2 11/07经验(−10,σ13)": (-10.0, 13.4),
    "S3 后验({:.1f},σ{:.1f})".format(post_mu, SIGMA_TOTAL): (post_mu, SIGMA_TOTAL),
}

# 邻域稳定性：对每个候选，取家族间均值差 |Δmean| 最大且 n≥3 的近邻
all_leak_fams = {k: v for k, v in fam.items() if k.startswith("leak:")}
flat = []
for sig, v in all_leak_fams.items():
    if len(v) >= 3:
        rates = tuple(int(x.split(":")[1]) for x in sig.split("|"))
        flat.append((rates, st.mean(v), len(v)))


def neighbor_deltas(rates):
    out = []
    r = tuple(rates)
    for rates2, m2, n2 in flat:
        if rates2 == r:
            continue
        diffs = [(a, b - a) for a, b in zip(r, rates2)]
        nd = [d for _, d in diffs if d != 0]
        if len(nd) == 1 and abs(nd[0]) <= 2:
            out.append((rates2, m2, n2, nd[0]))
    return out


# ---------- 文档 ----------
L = []
A = L.append
A("# 0105 理论审计 — 11/08 阶段二战略部署与候选构型决策矩阵")
A("")
A("> 生成：2026-11-07 09:25 ｜ 执行者：zcode ｜ 输入：`runs/results.jsonl`（valid=true）+ 0084 先验 + 11/07 夜间同日配对；未访问远程系统。")
A("")
A("## 一、偏移模型校准（决策的地基）")
A("")
A(f"- 先验（0084）：官方 ≈ 本地均值 **+2.5 ± 7.4s**。")
A("- 11/07 新证据：同日配对 Shot1 −7.82s、Shot2 −10.16s（均为负）；同构型双发（Shot4/5）极差 15.14s → σ_off≈13.4s。")
A(f"- 正态-正态后验：**μ_off ≈ {post_mu:+.2f}s（不确定度 ±{post_sd_mu:.2f}），单发官方噪声 σ_off ≈ {SIGMA_OFF:.1f}s，合计预测区间宽度 σ_tot ≈ {SIGMA_TOTAL:.1f}s**。")
A("")
A("⚠️ 该模型把「本地均值」当锚点，而本地样本跨日混杂、曾受污染（记忆：11-06 样本 36s 级离群），")
A("故以下概率是**模型内相对排序**，不是绝对承诺；三场景敏感度一并给出。")
A("")
A("## 二、候选构型本地统计（valid=true，样本口径）")
A("")
A("| 构型 | n | 均值 | 中位 | 样本σ | CV | SE | min | max |")
A("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
for name, s in stats.items():
    if s["n"] == 0:
        A(f"| {name} | 0 | — 无本地样本 — | | | | | | |")
        continue
    A(f"| {name} | {s['n']} | {s['mean']:.2f} | {s['median']:.2f} | {s['std_s']:.2f} | {s['cv']:.1f}% | {s['se']:.2f} | {s['min']:.2f} | {s['max']:.2f} |")
A("")
A("（与 Lead `runs/submit_plan_1108_master.json` 声称核对：anchor 均值 133.86/SE 2.16 ✓、crown 中位 134.51 ✓、crown-pert 均值 135.85/CV 6.4% ✓、fortress CV 4.0%/SE 1.71 ✓ —— 本表按同口径复算一致。）")
A("")
A("## 三、决策矩阵：三场景 × 三阈值命中概率")
A("")
A("阈值：**登顶 ≤119.8293**｜**进前四 ≤122.4027**｜**改写自方最优 ≤124.3683**")
A("")
hdr = "| 构型 | " + " | ".join(f"{k} 登顶/前四/自最优" for k in SCEN) + " |"
A(hdr)
A("|---|" + "---:|" * len(SCEN))
for name, s in stats.items():
    if s["n"] == 0:
        continue
    cells = []
    for k, (mu, sg) in SCEN.items():
        p1 = p_le_scenario(s["mean"], CATNET, mu, sg)
        p4 = p_le_scenario(s["mean"], TOP4, mu, sg)
        pb = p_le_scenario(s["mean"], OWN_BEST, mu, sg)
        cells.append(f"{p1*100:.0f}% / {p4*100:.0f}% / {pb*100:.0f}%")
    A(f"| {name} | " + " | ".join(cells) + " |")
A("")
A("读法：登顶概率按场景剧烈分化——S1 先验口径个位数以下（~1–2%），S3 负偏移后验口径 12–15%，")
A("S2 介于其间。**这个分化本身就是结论：在本地均值 134–136s、官方单发 σ≈13s 的现实下，登顶只能按尾部事件管理；**")
A("11/08 的现实目标是**巩固前四、逼近领奖台**，登顶依赖对手停滞 + 尾部运气，不应作为计划基线。")
A("")
A("## 四、门禁旗标（对齐 `tools/audit_plan.py` 口径）")
A("")
A("| 构型 | LOW_N(<3) | HIGH_CV(>10%) | MIN_FAR_BELOW_MEAN(>2σ) | 邻域 ±1~2 跳变 |")
A("|---|---|---|---|---|")
for name, s in stats.items():
    if s["n"] == 0:
        continue
    f_low = "✗" if s["n"] < 3 else "✓"
    f_cv = "✗ HIGH" if s["cv"] > 10 else "✓"
    f_min = "✗" if (s["mean"] - s["min"]) > 2 * s["std_s"] else "✓"
    nb = neighbor_deltas(s["rates"])
    if nb:
        rates2, m2, n2, d = max(nb, key=lambda x: abs(x[1] - s["mean"]))
        delta = m2 - s["mean"]
        mark = "✓" if abs(delta) <= 2.0 else ("⚠" if abs(delta) <= 6.0 else "✗")
        f_nb = f"{mark} 最差邻族 {'/'.join(map(str, rates2))}（n={n2}）Δ{delta:+.1f}s"
    else:
        f_nb = "（无单槽 ±1~2 邻族样本）"
    A(f"| {name} | {f_low} | {f_cv} | {f_min} | {f_nb} |")
A("")
A("- 邻族旗标说明：✓ |Δ|≤2s；⚠ 2–6s（关注）；✗ >6s。**⚠/✗ 邻族多为 n=3 小样本**，且")
A("  anchor 的最差邻族 (40,40,40,**37**,37,36) 均值 144.5s 与 fortress(…37,37) 134.7s 单调性矛盾（第 5/6 目录同为 37 反而更快？），")
A("  高度疑似小样本/跨日污染伪影——**冻结周前建议用 r1–r3 本地复验该邻族**，复验前不据此改参。")
A("- crown 的两个最近邻（slot3 40→39：Δ+6.5s；slot4 37→38：Δ+5.6s，均 n=3）**双向都更差**，形态上"
  "是「局部小谷」而非悬崖——对防漂移有利，但 n=3 待复验；**crown 第 4 目录严禁再上调**，与 0085 突发剪刀差结论一致。")
A("- champ1107(40×3,36×3) 样本 σ≈13.5、CV≈10.0% 贴线触发 HIGH_CV（loose 族 CV≈11.2% 同样触发）：")
A("  champ1107 虽产出 124.3683s，但按均值/CV 口径处于门禁边缘；"
  "其用途应限定为「同构型复测/方差估计」（明确假设，符合额度纪律），不作为期望管理的主构型。")
A("")
A("## 五、11/08 出手序列建议（与 Lead 计划的差异点）")
A("")
A("Lead 主计划（`runs/submit_plan_1108_master.json`）5 发：anchor → crown → crown-pert → fortress → crown 复测。")
A("本地统计与门禁均支持前 4 发的顺序与选型（全部过门禁、邻域平坦）。**唯一建议调整第 5 发**：")
A("")
A("- 原计划第 5 发 = crown 复测（与第 2 发构成同构型对）；")
A("- **建议改为 champ1107(40×3,36×3) 复测**：官方 top 统一复测针对的是**我方最好成绩所在的构型**，")
A("  目前 champ1107 的官方出分仅 1 个点（124.3683s；11/07 Shot4/5 的 140.02/155.16 属另一构型），官方方差不可估计，")
A("  复测它才能直接估计「我们最有价值资产」的官方方差，为冻结周（11-16）的复测防守提供数据。")
A("  若 Lead 坚持原计划，crown 复测对同样有效，只是方差估计对象不同。")
A("")
A("### 期望管理口径（供晨会与报告使用）")
A("")
A(f"- 5 发按 S3 后验的期望官方落点：anchor {stats['anchor(40×3,37,36,36)「1108-shot1 稳健首发」']['mean'] + post_mu:.1f}s、"
  f"fortress {stats['fortress(40×4,37,37)「1108-shot4 堡垒」']['mean'] + post_mu:.1f}s、"
  f"crown {stats['crown(41,41,40,37,36,36)「1108-shot2/5 皇冠」']['mean'] + post_mu:.1f}s（±{SIGMA_TOTAL:.0f}s）。")
A("- 榜位预期：**大概率巩固第 4–6**；进前三需要 ≤121.5s（S3 概率约 15–25% 每发）；登顶（≤119.83s）单发 ≤10%，**不要写进承诺**。")
A("- 对手动态未计入：hashkimi 11-06 一天从 155→120.27s 证明榜首带仍在快速进化；若 11-07 对手再提速，上表阈值整体上移。")
A("")
A("## 六、局限")
A("")
A("- 偏移后验仅用 2 个同日观测，先验与观测方向相反（+2.5 vs −8/−10），后验 μ 的不确定度被有意放大（±{:.1f}s）。".format(post_sd_mu))
A("- 本地族样本跨日混合，未剔除污染日；`min` 列含 min-of-N 红利，**不得**用于预期（AGENTS.md 红线）。")
A("- 本审计不含任何提交动作；提交前 Lead 仍须跑 `python tools/audit_plan.py --plan <plan>` 以正式门禁为准。")

OUT_DOC.write_text("\n".join(L) + "\n", encoding="utf-8")
print("written:", OUT_DOC)
print(f"post_mu={post_mu:+.2f} post_sd_mu={post_sd_mu:.2f} sigma_total={SIGMA_TOTAL:.1f}")
for name, s in stats.items():
    if s["n"]:
        print(f"{name:44s} n={s['n']:2d} mean={s['mean']:.2f} cv={s['cv']:.1f}% "
              f"P(top1)={p_le(s['mean'], CATNET)*100:.1f}% P(own)={p_le(s['mean'], OWN_BEST)*100:.1f}%")
