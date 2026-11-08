# -*- coding: utf-8 -*-
"""0081 — token_refill_interval_us=4000 与 250Hz/1000Hz 时钟中断的相位同步机理.

确定性仿真（stdlib random，seed=42）：
  A. 粗定时器（jiffies 向上取整）自重装模型：实际周期 = ceil(T/J)×J，速率因子表；
  B. 相位锁定验证：T=J 整数倍 → 自重装周期精确 = T（MC 验证零漂移）；
  C. hrtimer + 唤醒迟滞 δ∈[0.8,1.2]ms（0068/0076 锚）→ 有效速率因子；
  D. 全 HZ 网格鲁棒性：T∈{1000,4000} × HZ∈{100,250,300,500,1000} 的因子与 41Mbps 份额安全带；
  E. 相位碰撞：4ms 爆发窗口占空比 × 背景事件到达相位 → 碰撞概率。

输出写入 zcode/scripts/_0081_out.md（UTF-8）。
"""
import math
import random
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

random.seed(42)
OUT = Path(__file__).resolve().parent / "_0081_out.md"
US = 1e6
PKT_PAYLOAD = 1200  # B（0013 拟合锚）
SHARE_MBPS = 41.0   # 运行点份额

# ---------- A. 粗定时器量化因子 ----------
def coarse_factor(T_us: float, hz: int) -> float:
    J = US / hz
    return T_us / (math.ceil(T_us / J) * J)

TS = [100, 400, 1000, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 8000, 10000]
HZS = [250, 1000]

# ---------- B. 相位锁定 MC（粗定时器自重装） ----------
def sim_coarse(T_us: float, hz: int, n: int = 2500):
    """自重装粗定时器：回调在 tick+ε 处重装，expires 向上取整到下一格。
    返回 (mean_period_us, std_period_us, n)。ε=均匀[0,0.5]µs 模拟 IRQ 迟延。"""
    J = US / hz
    periods = []
    for _ in range(n):
        eps = random.uniform(0.0, 0.5)
        periods.append(math.ceil(T_us / J) * J - eps)  # 从 tick+ε 起算到目标 tick
    m = sum(periods) / len(periods)
    var = sum((p - m) ** 2 for p in periods) / len(periods)
    return m, var ** 0.5, n

# ---------- C. hrtimer + 唤醒迟滞 ----------
DELTA_LO, DELTA_HI = 800.0, 1200.0  # µs（0068/0076 锚）
def sim_hrtimer(T_us: float, n: int = 10000):
    periods = [T_us + random.uniform(DELTA_LO, DELTA_HI) for _ in range(n)]
    m = sum(periods) / len(periods)
    return m, (sum((p - m) ** 2 for p in periods) / len(periods)) ** 0.5

# ---------- D. 全 HZ 网格：有效速率与安全带 ----------
def eff_rate_mbps(r: float, T_eff_us: float) -> float:
    return r / T_eff_us * US * PKT_PAYLOAD * 8 / 1e6

HZ_ALL = [100, 250, 300, 500, 1000]

# ---------- E. 相位碰撞 ----------
def collision_prob(burst_wire_ms: float, period_ms: float, n: int = 100000):
    """背景事件在 [0,period) 均匀相位到达，落在爆发窗口 [0,burst) 即碰撞。"""
    hits = sum(1 for _ in range(n) if random.uniform(0, period_ms) < burst_wire_ms)
    return hits / n

# ---------- 输出 ----------
L = []
L.append("# 0081 计算输出 — refill 周期与时钟中断相位同步\n")

L.append("## A. 粗定时器量化因子（自重装，ceil 语义）\n")
L.append("| T (µs) | HZ=250 因子 | HZ=1000 因子 |")
L.append("|---|---|---|")
for T in TS:
    L.append(f"| {T} | {coarse_factor(T,250)*100:.1f}% | {coarse_factor(T,1000)*100:.1f}% |")
L.append("")
L.append("零损失点 = J 的整数倍：HZ=250 → {4,8,...}ms；HZ=1000 → {1,2,3,4,...}ms。"
         "**4000µs 同时是两网格整数倍 → 双网格零损失（共振点）**。\n")

L.append("## B. 相位锁定 MC 验证（seed=42，n=2500）\n")
L.append("| T (µs) | HZ | mean period (µs) | std (µs) | 判定 |")
L.append("|---|---|---|---|---|")
for T in (1000, 2500, 4000, 6000, 10000):
    for hz in HZS:
        m, s, _ = sim_coarse(T, hz)
        verdict = "LOCKED" if abs(m - T) < 1.0 else "QUANTIZED（确定性降速）"
        L.append(f"| {T} | {hz} | {m:.1f} | {s:.3f} | {verdict} |")
L.append("")
L.append("T=4000 在两个 HZ 下 mean=4000µs（|mean−T|<1µs）→ **周期精确锁死在 tick 网格**，"
         "无平均偏置、无漂移；非整数倍 T 的 mean 恰为 ceil(T/J)×J（确定性降速而非抖动，std<0.2µs）——"
         "这是「量化灾难」与「共振免检」的分水岭。\n")

L.append("## C. hrtimer + 唤醒迟滞（δ∈[0.8,1.2]ms 均匀，seed=42）\n")
L.append("| T (µs) | mean T_eff (µs) | std (µs) | 有效速率因子 |")
L.append("|---|---|---|---|")
for T in (1000, 2000, 4000, 8000):
    m, s = sim_hrtimer(T)
    L.append(f"| {T} | {m:.1f} | {s:.1f} | {T/m*100:.1f}% |")
L.append("")
L.append("T=4000 → 80%（复现 0068 的 77–87% 与 0076 的 76.8% 锚）；T 越小相对折损越重"
         "（1000µs → 50%）——大周期对唤醒迟滞不敏感，是 interval 型模块抗噪的另一重理由。\n")

L.append("## D. 全 HZ 网格鲁棒性：有效速率（r tokens/T_eff）与 41 Mbps 份额安全带\n")
L.append("| HZ | J (µs) | T=1000 因子 | T=1000 eff (r=40) | T=4000 因子 | T=4000 eff (r=40) | T=4000 eff (r=38) | T=4000 eff (r=36) |")
L.append("|---|---|---|---|---|---|---|---|")
for hz in HZ_ALL:
    f1 = coarse_factor(1000, hz) * 100
    f4 = coarse_factor(4000, hz) * 100
    e1 = eff_rate_mbps(40, math.ceil(1000 / (US / hz)) * (US / hz))
    e4a = eff_rate_mbps(40, math.ceil(4000 / (US / hz)) * (US / hz))
    e4b = eff_rate_mbps(38, math.ceil(4000 / (US / hz)) * (US / hz))
    e4c = eff_rate_mbps(36, math.ceil(4000 / (US / hz)) * (US / hz))
    L.append(f"| {hz} | {US/hz:.0f} | {f1:.1f}% | {e1:.1f} | {f4:.1f}% | {e4a:.1f} | {e4b:.1f} | {e4c:.1f} |")
L.append("")
L.append(f"(eff 单位 Mbps，名义桶上限口径 P=1200B。安全带 = eff > {SHARE_MBPS:.0f} Mbps 份额。\n"
         "T=4000 在 HZ∈{250,500,1000} 全部 100% 因子（1.2 倍份额余量以上）；HZ=100/300 时 4ms 不是整数倍 → "
         "因子 40%/60%，但仍须看绝对值：HZ=300 下 r=40 eff=57.6 Mbps 仍 > 份额，只有 HZ=100（38.4 Mbps）跌破份额——"
         "即「leak 9/1000 塌方」型风险只在 HZ≤300 且 T<J 的组合出现，与 0013 的 G=4000 反推一致（官方应为 250Hz 系）。\n")

L.append("## E. 4ms 爆发窗口的相位碰撞概率（seed=42）\n")
L.append("| 场景 | 爆发线上时长 | 占空比 | 背景事件碰撞概率 |")
L.append("|---|---|---|---|")
for name, bw, duty in (("满需求 r=40（物理域）", 4.144, 4.144/4.0),
                       ("满需求 r=38（物理域）", 3.937, 3.937/4.0),
                       ("满需求 r=36（物理域）", 3.730, 3.730/4.0),
                       ("运行点 41 Mbps（r≈17/4ms）", 17*1295*8/1e8*1000, 17*1295*8/1e8*1000/4.0)):
    p = collision_prob(bw, 4.0)
    L.append(f"| {name} | {bw:.3f} ms | {duty*100:.1f}% | {p*100:.1f}% |")
L.append("")
L.append("相位锁定把碰撞从「随机抽奖」变成「确定性窗口重叠」：爆发占空比即碰撞概率上界。"
         "满需求下占空比 93–104% → 背景事件几乎必撞（与 0080 D 节占空比表同构）；运行点 44.0% → "
         "每次背景突发约 44% 概率落在我方爆发相位——0076 的坏相位侵蚀（阈值 28.5→18.5 包）在此获得相位概率口径。\n")

txt = "\n".join(L)
OUT.write_text(txt, encoding="utf-8")
print(f"written: {OUT} ({len(txt)} chars)")
