#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0096 — 跨进程共享内存与网络命名空间在评测容器环境中的隔离度审查.

只读仓库既有口径 + 公开 Linux 内核语义，闭门解析/仿真：
  §0 隔离度矩阵：7 类 namespace × 评测拓扑角色（公开语义，非探测）
  §1 设计耦合通道：瓶颈队列唯一性（netns 隔离 ⇒ 仅在 s1-s2 交汇）
  §2 残余耦合通道量化：进程间 IPC 税 / 页缓存回收 / softirq 忙闲尾 / 内核锁面
  §3 对既有审计假设的影响（0082/0085/0086 队列唯一耦合假设有效性）
  §4 合规边界结论
输出 zcode/scripts/_0096_out.md（UTF-8，seed=96 可复现）。
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OUT = Path(__file__).with_name("_0096_out.md")
RNG = np.random.default_rng(96)

# 仓库既有口径（0082/0085/0086/0092）
G_US = 4000.0          # pacer tick 4000µs
TE_US = 111.1          # 单包间隔（leak 36/4ms）
MU_US = 96.0           # 出口单包服务 96µs
SAFE_MARGIN = TE_US - MU_US   # 15.1µs 排队安全余量
N_TICKS_PER_DOWNLOAD = 31000  # 0092 口径（~124s × 250 tick/s）
SIGMA_D = 7.02         # 官方单发噪声（0084）


def main() -> int:
    L: list[str] = []
    P = L.append

    P("# 0096 输出 — 共享内存与网络命名空间隔离度审查（seed=96 可复现）")
    P("- 依据：公开 Linux 内核 namespace/veth/IPC 语义 + 仓库既有口径（0082 veth 预算、0092 CPU 干扰谱）。")
    P("- 合规：纯闭门解析与本地仿真，无任何对评测环境的探测/访问。")
    P("")

    # ============ §0 隔离度矩阵 ============
    P("## §0 隔离度矩阵（Containernet 型拓扑：每主机 = 独立容器 + veth 接入网桥）")
    P("")
    P("| namespace | 容器间边界 | 对评测的含义 |")
    P("|---|---|---|")
    P("| **net** | 完全隔离：独立网卡/路由/qdisc/conntrack/iptables | 我方(d1-d2)与背景(d3-d4)无任何 socket 状态共享；唯一交汇点=网桥/上联的瓶颈队列 |")
    P("| **IPC** | 完全隔离：SysV shm/posix shm/memfd 不可跨容器引用 | 评测器与参赛容器之间**不存在共享内存对象**；跨容器数据必须走 socket/文件 |")
    P("| **PID** | 完全隔离：互不可见/不可 signal | 无法（也不得）感知或影响评测器进程 |")
    P("| **mnt** | 隔离：独立挂载表 | 数据交换只经显式挂载/网络；无文件系统侧信道 |")
    P("| **UTS/USER** | 隔离 | 无影响 |")
    P("| **cgroup** | 各容器独立资源上限 | CPU/内存配额约束我方进程本身（0092 已量化其抖动谱） |")
    P("| **time（新）** | 隔离/偏移可控 | 与 G=4000µs pacer 网格无交互 |")
    P("")
    P("**共享内存语义小结**：同一容器内的进程对（client ↔ pacer 模块/进程）可共享 shm/页缓存；")
    P("**跨容器（我方 ↔ 背景 ↔ 评测器）的共享内存为零**——任何「共享内存侧信道」假设不成立，")
    P("且探测评测器内存属官方红线，本审计仅从公开语义确认隔离充分，不做也不允许任何验证性访问。")
    P("")

    # ============ §1 设计耦合通道 ============
    P("## §1 设计耦合通道：netns 隔离 ⇒ 唯一物理交汇 = 瓶颈队列")
    P("")
    P("1. 我方 TX 路径（d1 容器内）全部状态（socket buf、pacing、本地 qdisc）都在我方 netns 内，")
    P("   背景流(d3→d4)在该 netns 中**不可见**；反向亦然。")
    P("2. 两路流量仅在 s1–s2 上联的**共享队列（drop-tail B=40, 100 Mbps）**相遇——")
    P("   0082/0085/0086 全部审计把耦合压缩为「瓶颈队列交互」，该假设在 netns 语义下**严格成立**，")
    P("   不是近似：不存在第二个共享状态点。")
    P("3. veth 数据路径固定税 6–248 µs，其中仅 ~3 µs 与瓶颈串行相加（0082）；")
    P("   对 4ms tick = 0.075%、对 T_e=111.1µs 单包间隔 ≈ 2.7%，均低于 ±1 包参数扰动粒度（8%）。")
    P("")

    # ============ §2 残余耦合通道量化 ============
    P("## §2 残余耦合通道量化（宿主机共享资源：CPU/缓存/内存/内核子系统）")
    P("")
    # --- A. 同容器进程间 IPC 税（若 pacer 与 client 为分离进程） ---
    P("### A. 同容器跨进程 IPC 税（pacer ↔ client 分离进程的最坏情形）")
    P("")
    per_msg = {"unix_dgram socket": 2.5, "pipe write/read": 1.8, "shm+eventfd": 0.8}
    P("| 通道 | 每消息成本 (µs) | 每包成本（1 msg/pkt） | 每 tick 折算 (36 包) | 对 T_e 占比 | 速率折损/下载 |")
    P("|---|---:|---:|---:|---:|---:|")
    for name, c in per_msg.items():
        per_tick = c * 36
        ratio = c / TE_US * 100
        loss = per_tick * N_TICKS_PER_DOWNLOAD / 1e6
        P(f"| {name} | {c} | {c} | {per_tick:.0f} | {ratio:.1f}% | {loss:.2f}s |")
    P("")
    P("- 上表为**最坏上界**（假设每包一次 IPC 往返）；实际 pacer 为漏桶按批放行（36 包/4ms），")
    P("  IPC 频率是 per-tick 而非 per-packet → 成本 ÷36：0.02–0.07µs/包，**完全可忽略**。")
    P(f"- 与 0092 安全余量对照：即使 per-packet IPC 最坏 2.5µs，间隔抖动 2.5µs < 15.1µs 排队安全余量 →")
    P("  不产生微队列、不触发 Drop-tail；pacer 与 client 同进程（模块化）时该项为零。")
    P("")
    # --- B. 页缓存回收（跨容器内存压力通道） ---
    P("### B. 页缓存回收：跨容器共享内存压力的量化")
    P("")
    total_mb = 630
    pages = total_mb * 1e6 / 4096
    minor_us = 0.5
    P(f"- 630MB 下载数据 ≈ {pages/1e3:.0f}k 个 4KB 页；隔离语义下页缓存条目按文件归属，无数据共享，")
    P("  但**回收压力是宿主机全局的**：背景/评测容器的内存活动可诱发我方 minor fault。")
    P(f"- 上界预算：全部页各 1 次 minor fault × {minor_us}µs = {pages*minor_us/1e6:.3f}s/下载周期，")
    P(f"  摊在 ~124s 上 = {pages*minor_us/1e6/124*100:.2f}% 时间轴，且只影响用户态拷贝路径（不进 T_e 间隔）→")
    P("  对 pacing 网格与瓶颈队列**双重无交互**；官方 σ_d=7.02s 面前不可分辨（<0.01σ_d）。")
    P("")
    # --- C. softirq/NAPI 忙闲尾（宿主 CPU 共享） ---
    P("### C. softirq/NAPI 忙闲尾（0082 上界 200µs + 0092 谱系复合）")
    P("")
    P("| 场景 | 注入到 tick 的尾延迟 | 每 tick P(δ>g=1000µs) | 速率折损 ΔT | 占 σ_d |")
    P("|---|---:|---:|---:|---:|")
    P("| 空闲宿主 | P99≈30µs | ~0 ppm | 0.28–0.36s | 4–5% |")
    P("| 中载 | P99≈200µs | ~0 ppm | 1.7–1.8s | 24–26% |")
    P("| 重载（ρ=0.9） | 谱系上界 | ≤97 ppm/tick | 3.2s | 45% |")
    P("| 公平轮转风暴 | E[δ]=10.7ms ≫ tick | 高 | 332s | 47σ_d |")
    P("")
    P("- 前三行来自 0092 CPU 谱系（本审计不重复仿真，直接引用其 seed 复现件 cpu0092_pacing_jitter.py）；")
    P("  第四行（唯一灾难通道）已被官方固定拓扑与 11-06 CPU 重载假说证伪排除（0092/hourly 0900）。")
    P("- softirq 忙闲尾与我方 netns RX 路径的核分配由宿主任意调度 → 属 0092 已覆盖的调度链，")
    P("  **无新增量级**：netns 不改变 softirq 的成本结构，只改变其归属 netns。")
    P("")
    # --- D. 内核锁面 ---
    P("### D. 内核锁面共享度")
    P("")
    P("- qdisc 锁：per-netdev → 我方 veth 与背景 veth 各自独立，**零争用**；")
    P("- netfilter/conntrack：per-netns → **零争用**；")
    P("- 全局共享仅剩：调度器 runqueue（0092）、页缓存回收（§B）、内存带宽（位宽充裕，")
    P("  2×12.5MB/s 线速 ≪ DDR 带宽 3 个数量级）、时钟 hrtimer 基（0092 δ_disp 中位 3µs 已含）。")
    P("")

    # ============ §3 对既有审计假设的影响 ============
    P("## §3 对既有审计体系的影响判定")
    P("")
    P("| 既有假设 | 依赖的隔离性质 | 本审查判定 |")
    P("|---|---|---|")
    P("| 0082「耦合=瓶颈队列交互」 | netns 完全隔离 | **严格成立**（强化：不是近似而是语义事实） |")
    P("| 0085 突发惩罚律的队列模型 | 背景仅经瓶颈队列作用于我方 | 成立（§1） |")
    P("| 0086 ρ=1 饱和工况的背景聚合 | 背景容器无共享状态，只有速率交互 | 成立 |")
    P("| 0092 CPU 干扰谱 = 唯一宿主级通道 | IPC/shm 跨容器为零 | 成立且完备（无第二通道遗漏） |")
    P("| 官方复测方差可预测性（0082 §三） | 顶层确定性 + 残余通道有界 | 成立：残余通道全部 « σ_d |")
    P("")
    # Monte Carlo 复核：把全部残余通道注入单发总耗时
    sim_n = 200000
    ipc = RNG.uniform(0, 0.07)           # pacer 同进程 0；分离进程 per-tick 折算 ≤0.07s
    pagefault = RNG.uniform(0, 0.26)     # 630MB minor fault 上界摊布
    cpu_idle = RNG.uniform(0.28, 0.36)   # 0092 空闲谱
    softirq = RNG.uniform(0, 0.1)        # 忙闲尾增量（上界）
    total_resid = ipc + pagefault + cpu_idle + softirq
    mc = np.array([RNG.uniform(0, 0.07) + RNG.uniform(0, 0.26) +
                   RNG.uniform(0.28, 0.36) + RNG.uniform(0, 0.1) for _ in range(sim_n)])
    P(f"### 残余通道合计 Monte Carlo（n={sim_n}，上界独立抽样）")
    P("")
    P(f"- 合计分布：中位 {np.median(mc):.2f}s，P95 {np.percentile(mc,95):.2f}s，最大 {mc.max():.2f}s")
    P(f"- 相对官方单发噪声 σ_d={SIGMA_D}s：中位 {np.median(mc)/SIGMA_D*100:.1f}%、P95 "
      f"{np.percentile(mc,95)/SIGMA_D*100:.1f}% —— **官方-本地校准面与复测方差均不可由隔离残差解释**")
    P("")

    # ============ §4 合规边界 ============
    P("## §4 合规边界结论")
    P("")
    P("1. 隔离充分性：netns/IPC/PID 三重隔离使「共享内存侧信道」「跨容器状态感知」在公开语义下不存在；")
    P("   任何试图访问评测器内存/进程/网络状态的行为既违反隔离边界也违反官方红线——本审计确认无需、")
    P("   不做、且不应有任何此类动作。")
    P("2. 测量有效性：官方与我方测得的时间量都只由「瓶颈队列交互 + 各自容器内计算」决定，")
    P("   无未建模的第三通道 → 0082-0092 审计体系的耦合假设完备。")
    P("3. 可行动作：**无**。残余通道（IPC/页回收/softirq）全部 « σ_d=7.02s 且提交侧不可控；")
    P("   唯一有量级的宿主级通道（公平轮转风暴 332s）已被官方拓扑排除。")
    P("")

    OUT.write_text("\n".join(L), encoding="utf-8")
    print(f"written {OUT} ({len(L)} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
