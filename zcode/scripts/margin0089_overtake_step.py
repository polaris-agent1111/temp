# -*- coding: utf-8 -*-
"""0089 — 榜首成绩抗扰动裕度与追赶队伍反超所需最小带宽提升阶差分析。

数据源（全部只读、仓库内）：
  - runs/hourly INDEX 快照（11-07 02:00 官方榜单，Lead 维护，此处硬编码并注明来源）
  - runs/leaderboard_full.json（逐发 attempt 历史，快照截至 11-05 13:38）
  - docs/analysis/0084-theory-audit.md 的分层贝叶斯噪声后验（σ_d、μ_B、τ_b）
  - docs/extracted/六载穿柜.md 的文件体积（10/20/40/80/160/320 MB，合计 630 MB）

方法：
  A. 裕度矩阵：秒差 / 百分比 / 等效平均净荷吞吐（goodput）差 / σ_d 单位。
  B. 抗扰动概率：官方复测两种语义（复测均分替换 / best-of 累积）下的排名反转概率，
     解析 Φ + 蒙特卡洛（seed=42）双重验证；噪声取 0084 后验 σ_d 及其 95% CI 端点。
  C. 反超最小阶差：t(r)=B/r 的等效吞吐标尺 + 边际律 d t/dr = -B/r²（s/Mbps），
     给出每支追赶队达到第 1 名所需的最小等效净荷吞吐阶跃。
  D. 历史逐发分布经验自举：各队「下一发击穿榜首线」的历史外推概率（明示机制跃迁低估）。

合规：不探测官方系统、不提交、不写任何受保护路径。
"""
import json
import math
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEED = 42
rng = np.random.default_rng(SEED)

# ---------- 常量 ----------
B_MBIT = 630 * 8  # 630 MB = 5040 Mbit（官方 docs/extracted/六载穿柜.md 文件表）
SIGMA_D = 7.02     # 0084 官方单发噪声后验均值 (s)
SIGMA_D_LO, SIGMA_D_HI = 3.8, 12.4  # 0084 95% CI
MU_B = 2.49        # 0087 11/07 平台偏移（同日语义）
TOP_LINE = 117.0257  # 光明未来 11-07 02:00 榜首

# 11-07 02:00 官方快照（来源 hourly/INDEX.md，Lead 维护）
BOARD = [
    ("光明未来", 117.0257, 15),
    ("Catnet", 119.8293, 19),
    ("hashkimi", 120.2670, 7),
    ("我也不想写实验报告", 121.5217, 7),
    ("大肥鱼", 122.4027, 15),
    ("赛博coder", 124.3683, 15),
    ("ResearchSN", 125.0620, 3),
    ("无法导入", 126.1927, 7),
    ("七只大肥猪", 128.0283, 6),
    ("小土豆", 132.6513, 8),
]

# ---------- A. 裕度矩阵 ----------
print("=" * 100)
print("A. 头部裕度矩阵（对榜首 117.0257；1 Mbps 边际律以 r 等效吞吐计）")
print("=" * 100)
hdr = f"{'队伍':<12}{'成绩(s)':>10}{'秒差':>9}{'%差':>8}{'等效吞吐(Mbps)':>15}{'吞吐差(Mbps)':>13}{'吞吐差%':>9}{'σ_d 单位':>10}"
print(hdr)
r_top = B_MBIT / TOP_LINE
for team, t, n in BOARD:
    dt = t - TOP_LINE
    r = B_MBIT / t
    print(f"{team:<12}{t:>10.4f}{dt:>9.4f}{dt/t*100:>7.2f}%{r:>15.3f}{r-r_top:>13.3f}{(r-r_top)/r_top*100:>8.2f}%{dt/SIGMA_D:>10.2f}")

# 边际律：dT/dr = -B/r^2 (s per Mbps)，在榜首吞吐附近
for r0 in (42.0, 43.06):
    print(f"边际律 dT/dr @ {r0:.2f} Mbps = {-B_MBIT/r0**2:.3f} s/Mbps")

# ---------- B. 抗扰动概率 ----------
def inversion_prob(delta, sigma, n_avg):
    """复测语义 A：双方各取 n 发平均重记成绩，追赶方(均值高 delta)反转的概率。
    追赶方新成绩 ~ N(m+delta, sigma^2/n)，榜首 ~ N(m, sigma^2/n)。
    P(invert) = Phi(-delta / (sigma*sqrt(2/n)))。"""
    return 0.5 * math.erfc(delta * math.sqrt(n_avg) / (sigma * math.sqrt(2)) / math.sqrt(2))

def inversion_prob_mc(delta, sigma, n_avg, n_sim=200_000):
    m0 = rng.normal(0, sigma, (n_sim, n_avg)).mean(axis=1)      # 榜首
    m1 = rng.normal(delta, sigma, (n_sim, n_avg)).mean(axis=1)  # 追赶方
    return float((m1 < m0).mean())

print()
print("=" * 100)
print("B. 复测反转概率（语义 A：复测重记成绩；delta=榜首领先第2名的秒差）")
print("=" * 100)
gaps = [("榜首 vs Catnet(第2)", TOP_LINE - 119.8293),
        ("榜首 vs hashkimi(第3)", TOP_LINE - 120.2670),
        ("榜首 vs 大肥鱼(第5)", TOP_LINE - 122.4027),
        ("榜首 vs 我方(第6)", TOP_LINE - 124.3683)]
print(f"{'对阵':<24}{'delta(s)':>9} | " + " | ".join(f"n={n:>2}" for n in (1, 2, 3, 5, 10)))
for name, delta in gaps:
    delta = abs(delta)
    ps_an = [inversion_prob(delta, SIGMA_D, n) for n in (1, 2, 3, 5, 10)]
    ps_mc = [inversion_prob_mc(delta, SIGMA_D, n) for n in (1, 2, 3, 5, 10)]
    print(f"{name:<24}{delta:>9.4f} | " + " | ".join(f"{p*100:4.1f}%" for p in ps_an)
          + f"   [MC 校验: " + " ".join(f"{p*100:4.1f}%" for p in ps_mc) + "]")

print()
print("-- σ_d 敏感性（榜首 vs Catnet, delta=2.8036s, n=3 复测）--")
for s, tag in ((SIGMA_D_LO, "σ_d=3.8(CI下界)"), (SIGMA_D, "σ_d=7.02(后验)"), (SIGMA_D_HI, "σ_d=12.4(CI上界)")):
    print(f"  {tag:<20}: P(反转) = {inversion_prob(2.8036, s, 3)*100:.1f}%")

print()
print("-- 语义 B（best-of 累积：复测只增不改）下榜首被击穿概率 --")
print("   榜首已记录成绩不可变差，追赶方需在复测中单发打出 < 117.0257：")
for name, delta in gaps:
    delta = abs(delta)
    p1 = 0.5 * math.erfc(delta / (SIGMA_D * math.sqrt(2)))
    print(f"  单发击穿 P({name.split('vs ')[1]} < 榜首) = {p1*100:.1f}%   (k 发独立尝试后至少一次击穿 ≈ 1-(1-p)^k)")

# ---------- C. 反超最小阶差 ----------
print()
print("=" * 100)
print("C. 追赶队伍反超榜首所需最小等效吞吐阶差（t = B/r 标尺，B=5040 Mbit）")
print("=" * 100)
print(f"{'队伍':<12}{'现成绩':>10}{'需达到':>9}{'需提速(s)':>10}{'现等效吞吐':>11}{'目标吞吐':>10}{'阶差(Mbps)':>11}{'阶差%':>8}{'差多少σ_d':>10}")
for team, t, n in BOARD[1:6]:
    dt = t - TOP_LINE
    r_now, r_tgt = B_MBIT / t, B_MBIT / TOP_LINE
    print(f"{team:<12}{t:>10.4f}{TOP_LINE:>9.4f}{dt:>10.4f}{r_now:>11.3f}{r_tgt:>10.3f}{r_tgt-r_now:>11.3f}{(r_tgt-r_now)/r_now*100:>7.2f}%{dt/SIGMA_D:>10.2f}")

# 分文件边际视角：6.bin (320MB=2560Mbit) 是最大杠杆
print()
print("分文件边际视角（单文件提速 10% 对总成绩的贡献）:")
for f, mb in ((1, 10), (2, 20), (3, 40), (4, 80), (5, 160), (6, 320)):
    print(f"  {f}.bin ({mb:>3}MB): 10% 单文件提速 = 全局 -{mb*0.1/630*100:.2f}%  ≈ 全局 -{mb*0.1/630*TOP_LINE:.2f} s")

# ---------- D. 历史逐发分布经验自举 ----------
print()
print("=" * 100)
print("D. 追赶队「下一发击穿 117.0257」历史外推（逐发历史：runs/leaderboard_full.json，截至 11-05 13:38）")
print("=" * 100)
lb = json.load(open(os.path.join(ROOT, "runs", "leaderboard_full.json"), encoding="utf-8"))
subs = lb["leaderboard"]["problems"][0]["submissions"]
our_official = [245.995, 243.9583, 150.6757, 140.4793, 141.7273, 140.927, 137.091, 137.384, 142.7837, 133.086,
                143.561, 124.3683, 143.1357, 140.0247, 155.1607]  # runs/official_results.jsonl + sequential_adaptive_log.jsonl
hist = {s["team"]: [float(a["download_seconds"]) for a in s["attempts"]] for s in subs}
hist["赛博coder"] = our_official
print(f"{'队伍':<12}{'n':>3}{'best':>10}{'mean':>9}{'std':>8}{'截尾mean':>9}{'截尾std':>8}{'P(下一发<榜首)':>15}{'最近8发mean':>12}")
for team, t, n in BOARD[:6]:
    if team not in hist:
        continue
    att = np.array(hist[team])
    m, s = att.mean(), att.std(ddof=1)
    # 截尾（去 20% 双侧）稳健统计
    k = max(1, int(len(att) * 0.2))
    atr = np.sort(att)[k:-k] if len(att) - 2 * k >= 2 else att
    mr, sr = atr.mean(), atr.std(ddof=1)
    # P(下一发 < 榜首) = 0.5*erfc((m-TOP)/(s*sqrt(2)))
    p_full = 0.5 * math.erfc((m - TOP_LINE) / (s * math.sqrt(2))) if s > 0 and len(att) > 1 else float("nan")
    p_core = 0.5 * math.erfc((mr - TOP_LINE) / (sr * math.sqrt(2))) if sr > 0 and len(atr) > 1 else float("nan")
    recent = att[-8:].mean() if len(att) >= 8 else att.mean()
    print(f"{team:<12}{len(att):>3}{att.min():>10.4f}{m:>9.2f}{s:>8.2f}{mr:>9.2f}{sr:>8.2f}{p_full*100:>14.1f}%{recent:>12.2f}")
print()
print("注：hashkimi 11-06 单日 -35s、光明未来 11-06 单日 -10s 的机制跃迁使历史外推系统性低估反超能力；")
print("    外推概率只回答「不换结构靠抖动」的分支，不回答「换结构」的分支（结构性阶差见 C 表）。")

# ---------- E. 榜首自身抗扰动裕度（Catnet 核心簇稳健性）----------
print()
print("=" * 100)
print("E. 榜首线附近的核心簇内聚度（复测语义 A、n=3 时需 delta > 2.33*σ*sqrt(2/3)≈1.9σ 才算 99% 稳固）")
print("=" * 100)
cat = np.array(hist.get("Catnet", []))
if len(cat):
    core = cat[cat < 140]  # 去 load 污染长尾（146.98 / 186.99）
    print(f"Catnet 逐发 n={len(cat)}，剔除 >140s 污染后核心簇 n={len(core)}：mean {core.mean():.2f}，std {core.std(ddof=1):.2f}")
    print(f"  榜首 117.0257 低于 Catnet 历史核心簇均值 {core.mean():.1f} 达 {(core.mean()-TOP_LINE)/core.std(ddof=1):.1f} 个核心簇 σ —— 属结构跃迁而非抖动抽签")
print()
print("结论锚点：σ_d≈7.02s 下，头部 2.80s 裕度 = 0.40σ_d；n=3 复测反转概率仍 >30%。")
print("头部 5 队 117.03–122.40 全部落在 0.8σ_d 窗口内，官方复测下头部排序本质是分布重叠区的抽签，")
print("唯有把真分布左移 ≥1.9σ_d（≈13.3s，即等效吞吐 +10.8%）才能以 99% 功效锁定名次。")
