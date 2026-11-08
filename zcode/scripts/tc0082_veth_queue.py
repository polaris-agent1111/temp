# -*- coding: utf-8 -*-
"""0082 — Containernet veth-pair + Linux TC 排队微基准的解析解构与确定性仿真.

红线声明：不探测官方系统。本脚本 = 公开内核语义的解析分解 + 本侧确定性离散事件仿真。

内容：
  A. veth-pair + TC 数据路径逐跳微延迟预算表（公开内核语义/文献锚）；
  B. 确定性离散事件仿真：单瓶颈 100 Mbps，drop-tail B=40，服务=串行化+固定路径；
     我方源 = 令牌桶节奏的爆发（k 包/4ms，k 受 CC 需求调制），背景源 = Poisson；
  C. 场景：S1 运行点（我方均值 ≈41 Mbps，k~N(17,3)）× 背景强度；S2 满需求压力（k=r）；
  D. TC shaper 计时后端枚举 → 与 0081 共振结论对接。

输出写入 zcode/scripts/_0082_out.md（UTF-8）。
"""
import random
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

random.seed(42)
OUT = Path(__file__).resolve().parent / "_0082_out.md"

# ---------- A. 逐跳微延迟预算（µs，公开内核语义锚） ----------
HOPS = [
    ("QUIC sendmsg → UDP 栈（syscall+校验和）", 1.0, 3.0),
    ("dev_queue_xmit → qdisc enqueue（无锁快速路径）", 0.5, 2.0),
    ("qdisc dequeue（tbf/netem 定时器驱动时另计 hrtimer 精度项）", 0.5, 5.0),
    ("veth_xmit：sk_buff 复制/转发到对端（~1.3KB）", 1.0, 3.0),
    ("对端 netif_rx → NAPI/softirq 调度（空闲态）", 2.0, 30.0),
    ("softirq 背载态退化项（CPU 争用时）", 0.0, 200.0),
    ("IP/UDP 解栈 + socket 分发", 1.0, 5.0),
]
W_SKB = 1271                    # B（skb 域，0080 主估计）
SER_US = W_SKB * 8 / 1e8 * 1e6  # 100 Mbps 单包串行化 ≈ 101.7 µs

# ---------- B/C. 离散事件仿真 ----------
PERIOD_S = 4e-3
LINK_BPS = 1e8
QCAP = 40
SERIAL_OVERHEAD_US = 3.0   # qdisc+发侧开销，与串行化逐包相加（消耗瓶颈容量）
RX_PATH_US = 12.0          # 接收侧固定路径（中位），与瓶颈服务并行，只加端到端延迟
SIM_S = 8.0

def simulate(k_mean: float, k_std: float, r_cap: int, bg_mbps: float):
    """我方源：每 4ms 爆发 k~N(k_mean,k_std) clip[0,r_cap] 包（爆发内按线速背靠背）；
    背景源：Poisson(bg_mbps)。返回 (n_acc, drops%, qmax, qmean, p50/p95/p99 µs)。"""
    ser = W_SKB * 8 / LINK_BPS
    svc = ser + SERIAL_OVERHEAD_US * 1e-6
    bg_rate = bg_mbps * 1e6 / 8 / W_SKB

    arrivals = []
    t = 0.0
    while t < SIM_S:
        k = int(round(random.gauss(k_mean, k_std)))
        k = max(0, min(r_cap, k))
        for i in range(k):
            arrivals.append(t + i * ser)
        t += PERIOD_S
    if bg_rate > 0:
        bg_t = random.expovariate(bg_rate)
        while bg_t < SIM_S:
            arrivals.append(bg_t)
            bg_t += random.expovariate(bg_rate)
    arrivals.sort()

    departures = []          # FIFO → 完成时刻非降
    finish = 0.0
    drops = 0
    accepted = 0
    dep_ptr = 0
    qmax = 0
    qsum = 0
    delays = []
    for a in arrivals:
        while dep_ptr < len(departures) and departures[dep_ptr] <= a:
            dep_ptr += 1
        q = accepted - dep_ptr          # 在系统内未完成数
        if q >= QCAP:
            drops += 1
            continue
        accepted += 1
        fin = max(a, finish) + svc
        departures.append(fin)
        finish = fin
        delays.append((fin - a) * 1e6)
        qsum += q
        qmax = max(qmax, q + 1)
    delays.sort()
    return (accepted, drops / len(arrivals) * 100, qmax,
            qsum / max(1, accepted),
            delays[len(delays) // 2],
            delays[int(len(delays) * 0.95)],
            delays[int(len(delays) * 0.99)])

# ---------- 输出 ----------
L = []
L.append("# 0082 计算输出 — veth+TC 微延迟解构与瓶颈队列仿真\n")

L.append("## A. 逐跳微延迟预算（公开内核语义锚，µs）\n")
L.append("| 跳 | 下界 | 上界 |")
L.append("|---|---|---|")
tot_lo = tot_hi = 0.0
for name, lo, hi in HOPS:
    tot_lo += lo
    tot_hi += hi
    L.append(f"| {name} | {lo:.1f} | {hi:.1f} |")
L.append(f"| **固定路径合计** | **{tot_lo:.1f}** | **{tot_hi:.1f}** |")
L.append(f"| 单包串行化 @100Mbps（W={W_SKB}B，skb 域） | {SER_US:.1f} | {SER_US:.1f} |")
L.append("")
L.append(f"**量级结论**：veth+TC 固定路径 {tot_lo:.0f}–{tot_hi:.0f} µs（其中仅 ~3µs 发侧开销与瓶颈串行化相加，"
         f"接收侧 µs–百 µs 项与瓶颈服务并行）；单包串行化 {SER_US:.1f} µs 才是逐包硬成本。"
         "µs 级路径延迟对 4ms refill 网格 / 100µs pacing 网格均 <2%；"
         "**排队物理由串行化 + 爆发动态主导，veth 路径成本不构成瓶颈**——官方实测 133s≈本地（0013）与此一致。\n")

L.append("## B/C. 共享瓶颈队列仿真（drop-tail B=40，seed=42，8s 场景）\n")
L.append("我方源：tb 节奏爆发 k/4ms（k 受 CC 需求调制）；背景源：Poisson；"
         "瓶颈服务 = 101.7µs 串行化 + 3µs 发侧开销（接收侧 12–200µs 与瓶颈并行，只加端到端延迟）。"
         "S1=运行点（均值 41 Mbps：k~N(17,3)），S2=满需求压力（k=r，bg=0 隔离检验 0080 占空比结论）。\n")
L.append("| 场景 | r | 背景份额 (Mbps) | 接收/到达 | 丢包率 | qmax | q̄ | p50 (µs) | p95 (µs) | p99 (µs) |")
L.append("|---|---|---|---|---|---|---|---|---|---|")
for scen, k_mean, k_std in (("S1 运行点", 17, 3), ("S2 满需求", None, 0)):
    for r in (36, 38, 40):
        bgs = (35, 50, 59) if scen == "S1 运行点" else (0, 50)
        for bg in bgs:
            km = k_mean if k_mean is not None else r
            n, dr, qmax, qm, p50, p95, p99 = simulate(km, k_std, r, bg)
            L.append(f"| {scen} | {r} | {bg} | {n:,} | {dr:.2f}% | {qmax} | {qm:.1f} "
                     f"| {p50:.0f} | {p95:.0f} | {p99:.0f} |")
L.append("")
L.append("S1 读法：运行点 41 Mbps 我方 + 背景 35 Mbps（总需求 76 Mbps）→ 丢包 0、q̄≈4、p95≈1ms；bg=50（总需求 91 Mbps，ρ≈0.91）→ "
         "爆发峰值瞬触缓冲（丢包 0.05–0.09%、qmax=40 瞬态、p95≈2.6–2.9ms）——冠军爆发结构与 B=40 缓冲基本自洽但已见峰值触碰；"
         "bg=59（总需求 102 Mbps 过载）→ 丢包 4.8–5.3%、q̄≈30 饱和 → 份额挤压的临界形态。S2/bg=0（隔离检验）："
         "**r=40/4ms 无背景也持续丢包 4.42%（ρ≈1.05）、qmax=40；r=38 边缘稳定（ρ≈0.995，本窗口 0 丢）；r=36 稳定（ρ≈0.94，q̄≈1）**"
         "——0080 占空比结论（40/4ms 线速不可持续、38/36 可持续）在队列级直接复现。S2/bg=50：满需求 + 份额挤压 → 持续丢包 31–36% → "
         "CC 被迫退避回份额——「名义速率高于物理天花板的部分自动转化为丢包+退避」的队列级演示（0080 §二口径表、0075 膝点同向）。\n")

L.append("## D. TC shaper 计时后端与 0081 对接\n")
L.append("| shaper | 计时后端 | 粒度 | 对接结论 |")
L.append("|---|---|---|---|")
L.append("| tbf | 老内核 jiffies 粗定时器 → 新内核 hrtimer | 4ms / ns | 若官方 jiffies 后端：瓶颈限速本身锁 4ms 网格 → 与我方 refill 同相位共振（0081 §一）|")
L.append("| netem | hrtimer + rbtree 延迟出队 | ns | 限速精度足够；排队延迟由延迟出队队列决定，同 B 表 |")
L.append("| htb | 内部令牌 + 类量子调度（500µs~10ms） | 类量子 | 41 Mbps 份额与 htb class 量子化行为相关 |")
L.append("| fq/fq_codel | EDT + hrtimer | ns | pacing 网格由 EDT 决定 |")
L.append("")
L.append("**核心交叉发现**：若官方瓶颈限速器为 jiffies 后端（tbf/htb），则**瓶颈服务节拍与我方 refill 同时锁在 4ms tick 相位**——"
         "0081 的相位锁定不仅作用于我方发射，也作用于瓶颈；两相位差恒定 → B/C 表的延迟/丢包是确定性周期模式，"
         "官方「重复多次取平均」的方差因此可预测（服务稳定时段 → 方差小；相位冲突时段 → 方差放大）。\n")

txt = "\n".join(L)
OUT.write_text(txt, encoding="utf-8")
print(f"written: {OUT} ({len(txt)} chars)")
