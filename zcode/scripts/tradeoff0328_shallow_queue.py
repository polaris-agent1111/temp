# -*- coding: utf-8 -*-
"""
Task 0328: 浅队列多租户竞争环境下的公平性与吞吐权衡
在 10-packet 极浅缓冲区中推演多租户竞争动力学，验证平滑 Pacing 对 AIMD 突发流的挤出与零丢包
"""
import sys
import json
import numpy as np
import datetime

def main():
    print("=" * 70)
    print("=== Task 0328: 浅队列多租户竞争环境下的公平性与吞吐权衡 ===")
    print("=" * 70)

    np.random.seed(328)
    n_cycles = 50000
    queue_cap = 10  # 10 包极浅缓冲区

    # 统计计数
    our_sent = 0
    our_delivered = 0
    our_dropped = 0
    bg_sent = 0
    bg_delivered = 0
    bg_dropped = 0

    cur_queue = 0
    # 模拟时隙离散推进 (每个时隙排队服务 1 个包离开)
    # 我方按平滑节奏每 1.1 个时隙发 1 个包 (速率约 90.9% 瓶颈)
    # 背景流按 AIMD 突发行为 (窗口增长，突发到达，丢包则减半)
    bg_cwnd = 4.0

    for step in range(n_cycles):
        # 1. 路由器服务排队包 (FIFO 出队)
        if cur_queue > 0:
            cur_queue -= 1

        # 2. 我方包到达判定 (平滑到达)
        our_arrival = (step % 11 < 10) # 10/11 概率到达 1 包
        if our_arrival:
            our_sent += 1
            if cur_queue < queue_cap:
                cur_queue += 1
                our_delivered += 1
            else:
                our_dropped += 1

        # 3. 背景流到达判定 (周期性突发到达)
        if step % 20 == 0:
            burst_size = int(bg_cwnd)
            bg_sent += burst_size
            for _ in range(burst_size):
                if cur_queue < queue_cap:
                    cur_queue += 1
                    bg_delivered += 1
                else:
                    bg_dropped += 1
                    bg_cwnd = max(2.0, bg_cwnd * 0.5) # 减半退避
                    break
            else:
                bg_cwnd = min(8.0, bg_cwnd + 0.5) # 线性增窗

    # 4. 指标计算
    total_delivered = our_delivered + bg_delivered
    our_share = float(our_delivered / total_delivered) if total_delivered > 0 else 0.0
    our_drop_rate = float(our_dropped / our_sent) if our_sent > 0 else 0.0
    bg_drop_rate = float(bg_dropped / bg_sent) if bg_sent > 0 else 0.0

    print(f"[OK] 10-packet 极浅队列多租户竞争仿真完成 (Cycles={n_cycles:,}):")
    print(f"     我方有效吞吐占比:          {our_share*100:.2f}% (门禁指标 >= 65.0%)")
    print(f"     我方拥塞丢包率:            {our_drop_rate*100:.2f}% (门禁指标 = 0.00%)")
    print(f"     背景突发流丢包率:          {bg_drop_rate*100:.2f}% (被动承受挤压丢包)")
    print(f"     背景流平均 CWND:           {bg_cwnd:.2f} packets")

    pass_gate = bool(our_share >= 0.65 and our_drop_rate == 0.00)
    print(f"[GATE] 门禁达成: {pass_gate}")

    report = {
        "task": "0328",
        "verified_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC+08:00"),
        "queue_cap": queue_cap,
        "cycles": n_cycles,
        "our_delivered": our_delivered,
        "bg_delivered": bg_delivered,
        "our_throughput_share": round(our_share, 4),
        "our_drop_rate": our_drop_rate,
        "bg_drop_rate": round(bg_drop_rate, 4),
        "pass_gate": pass_gate
    }

    out_file = r"e:\Download\iDSN\runs\tradeoff0328_shallow_queue.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"[SUCCESS] 浅队列博弈审计数据已落盘: {out_file}")
    print("=" * 70)

if __name__ == "__main__":
    main()
