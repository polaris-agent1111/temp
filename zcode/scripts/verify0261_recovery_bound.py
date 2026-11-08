# -*- coding: utf-8 -*-
"""verify0261_recovery_bound.py — 0261: 突发重置后恢复时延下限的两态验证.

目标命题（任务单考核目标）: 突发丢包致窗口乘性减后, 恢复时间 <= 2.5 RTT。

两态分解:
  态 A（vanilla RFC 9002 ACK-clock）: cwnd 值回升由加性增控制,
      T_A ≈ (1-β)·W0 / a 个 RTT（a = 每 RTT 加性增量, MSS 单位）。
      该态下命题一般不成立（数量级 10+ RTT）。
  态 B（准开环桶控发送, enable_n_in_flight 旁路）: 发送时钟由漏桶驱动而非 ACK 自时钟,
      恢复 = 检测/重传确认 T_det ∈ [1, 1.125] RTT + 桶补齐缺口 T_refill = G·(W0-W1)/r,
      其中 G=4ms 粒度, r = leak_rate(pkt/G), W1 = β·W0。
      该态下命题成立, 条件是旁路生效（cwnd 不约束释放路径）。

参数网格取自真实候选族（configs/ + 任务单背景）: leak r ∈ {36,38,40,42,44} pkt/4ms,
cap W0 ∈ {40,50,60} pkt, RTT ∈ {4,10} ms（4ms=定时器粒度口径, 10ms=广域口径）, β=0.7。

只打印 stdout, 零写入。
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

BETA = 0.7
G_MS = 4.0           # 漏桶粒度（G≈4000µs, 官方定时器口径）
RATES = [36, 38, 40, 42, 44]   # pkt/4ms, 候选族实际使用区间
CAPS = [40, 50, 60]            # 桶容量 = 稳态在途峰值 W0 的代理
RTTS = [4.0, 10.0]             # ms
AIMD_A = 1.0                   # 每 RTT +1 MSS（vanilla, 无突发解耦）
GATE_RTT = 2.5


def regime_b(r, cap, rtt):
    """态 B: 检测+桶补齐。返回 (T_det_lo, T_det_hi, T_refill_ms, T_total_rtt_hi)."""
    w1 = max(2.0, BETA * cap)
    deficit = cap - w1
    refill_ms = G_MS * deficit / r
    t_det = (1.0, 1.125)          # RACK 下限 1 RTT; 含抖动上限 1.125
    total_hi_rtt = (t_det[1] * rtt + refill_ms) / rtt
    return deficit, refill_ms, total_hi_rtt


def main():
    print("# 0261 原始输出：两态恢复下界验证")
    print("> 脚本: zcode/scripts/verify0261_recovery_bound.py  只打印, 零写入。")

    print("\n## 1. 态 A（vanilla RFC 9002 ACK-clock, 加性增 a=1 MSS/RTT）")
    print("cwnd 值回升耗时 T_A = (1-β)·W0 / a (RTT):")
    for cap in CAPS:
        t_a = (1 - BETA) * cap / AIMD_A
        verdict = "≤2.5 ✓" if t_a <= GATE_RTT else ">2.5 ✗（命题在纯 AIMD 下不成立）"
        print(f"  W0={cap}: T_A = {t_a:.1f} RTT  {verdict}")
    print("  → 命题的成立必须依赖非 ACK-clock 的释放机制, 否则按 AIMD 回升需 11–18 RTT。")

    print("\n## 2. 态 B（准开环桶控 + 在途旁路）: T_rec = T_det + G·(W0-β·W0)/r")
    print(f"{'r(pkt/4ms)':>10} {'W0':>4} {'RTT(ms)':>8} {'缺口(包)':>9} {'补齐(ms)':>9} {'T_total(RTT)':>13}  门禁")
    worst = 0.0
    for r in RATES:
        for cap in CAPS:
            for rtt in RTTS:
                deficit, refill_ms, t_hi = regime_b(r, cap, rtt)
                worst = max(worst, t_hi)
                ok = "PASS" if t_hi <= GATE_RTT else "FAIL"
                print(f"{r:>10} {cap:>4} {rtt:>8.1f} {deficit:>9.1f} {refill_ms:>9.2f} {t_hi:>13.3f}  {ok}")
    print(f"\n- 全网格最坏 T_total = {worst:.3f} RTT ≤ {GATE_RTT} RTT → {'PASS' if worst <= GATE_RTT else 'FAIL'}")

    print("\n## 3. 与 sibling 脚本 quic0261_cwnd_reset_recovery.py 的关系")
    print("- 该脚本可复现（P99=1.244 RTT 等), 但其『恢复』定义为 1 RTT ACK + 硬编码 0.128 RTT 补齐,")
    print("  门禁通过属构造保证; 且 W0=38 标注为『BDP + 浅缓冲』与 RTT=10ms 混搭（38 包是 RTT=4ms 口径的 BDP,")
    print("  10ms 口径 BDP=93.75 包）。本脚本在真实候选族网格上给出显式机制分解, 取代其作为证明依据。")
    print("- 本地实证交叉引用: 0087 审计的 cwnd 模式切换连续性 ≤0.47s（完成期切换, 非丢包恢复, 口径不同勿混）;")
    print("  0253 PTO 仿真（缺 §6.2.1 reset-on-ACK 时 100% 死锁 → 旁路是生死机制, 与态 B 前提一致）。")

    print("\n## 4. 结论口径")
    print("- 『恢复 ≤ 2.5 RTT』在**桶控旁路生效**（我方全部提交构型的默认机制）下成立, 全参数网格最坏")
    print(f"  {worst:.2f} RTT; 在纯 AIMD ACK-clock 下不成立（需 {(1-BETA)*max(CAPS):.0f}+ RTT）。")
    print("- 该对比本身就是答辩要点: 准开环架构把『丢包恢复』从 AIMD 时间尺度（10+ RTT）压缩到")
    print("  『1 次检测 + 桶补齐』时间尺度（≤1.9 RTT）。")


if __name__ == "__main__":
    main()
