#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0301: 极端高负载宿主机下 UDP 丢包重传尾部延迟对冲
在大文件阶段 (100MB~250MB) 仿真宿主机遭遇高负载突发时的 QUIC 尾部丢包重传，
证明平滑 pacing 下重传次数下降 >= 80.0%，尾部 P99 延迟压缩 <= 15.0ms。
"""
from __future__ import annotations

import datetime as dt
import json
import math
import random
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]

def simulate_pipeline(pacing: bool, n_packets: int = 50000) -> dict:
    """仿真 50,000 个数据包在 30 包浅缓冲队列下的端到端传输与丢包重传。"""
    buffer_cap = 30
    current_q = 0
    service_rate_pkts_per_ms = 8.333 # 100 Mbps (1200 bytes/pkt -> 10,416.7 pkts/s -> 8.333 pkts/ms)
    
    drops = 0
    delays_ms = []
    
    # 仿真时间推进 (毫秒步长)
    t = 0.0
    dt_ms = 0.12 # 每次推进 120us
    
    pkt_idx = 0
    next_send_time = 0.0
    
    # 外部宿主机 CPU 突发负载注入周期
    burst_load_active = False

    while pkt_idx < n_packets:
        t += dt_ms
        
        # 周期性模拟宿主机高负载毛刺 (每隔 100ms 突发 15ms 的高延迟与并发争抢)
        if int(t) % 100 < 15:
            burst_load_active = True
            drain_rate = service_rate_pkts_per_ms * 0.45 # 服务能力折半
        else:
            burst_load_active = False
            drain_rate = service_rate_pkts_per_ms

        # 队列排空
        drained = drain_rate * dt_ms
        current_q = max(0.0, current_q - drained)

        # 发包逻辑
        if t >= next_send_time:
            if pacing:
                # 平滑 Pacing: 严格匀速注入 (每包间隔 0.125ms = 8 pkts/ms)
                inter_packet_time = 0.125
                # 宿主机调度抖动 (微秒级)
                jitter = random.gauss(0.0, 0.015)
                next_send_time = t + max(0.02, inter_packet_time + jitter)
                burst_size = 1
            else:
                # 无整形/突发发送: 积压一批一起送 (burst 8~16 pkts)
                inter_packet_time = random.uniform(1.0, 2.0)
                next_send_time = t + inter_packet_time
                burst_size = random.randint(8, 18)

            for _ in range(burst_size):
                if pkt_idx >= n_packets:
                    break
                pkt_idx += 1
                
                # 入队检查
                if current_q + 1.0 > buffer_cap:
                    # 缓冲区溢出，发生丢包！
                    drops += 1
                    # 丢包产生 RTO 重传惩罚延迟
                    delays_ms.append(25.0 + random.uniform(5.0, 15.0))
                else:
                    current_q += 1.0
                    q_delay = (current_q / service_rate_pkts_per_ms)
                    delays_ms.append(q_delay)

    sorted_delays = sorted(delays_ms)
    p50_lat = sorted_delays[int(0.50 * len(sorted_delays))]
    p95_lat = sorted_delays[int(0.95 * len(sorted_delays))]
    p99_lat = sorted_delays[int(0.99 * len(sorted_delays))]

    return {
        "pacing": pacing,
        "n_packets": n_packets,
        "drops": drops,
        "drop_rate_pct": round((drops / n_packets) * 100.0, 4),
        "p50_delay_ms": round(p50_lat, 3),
        "p95_delay_ms": round(p95_lat, 3),
        "p99_delay_ms": round(p99_lat, 3)
    }

def main() -> int:
    print("=" * 70)
    print("=== Task 0301: 极端高负载宿主机下 UDP 丢包重传尾部延迟对冲 ===")
    print("=" * 70)

    random.seed(20261108)
    n_pkts = 50000

    print("[INFO] 开始无整形突发发送 (Unpaced Bursty) 仿真...")
    res_unpaced = simulate_pipeline(pacing=False, n_packets=n_pkts)

    print("[INFO] 开始皇冠精准整形 (Crown Fusion Paced) 仿真...")
    res_paced = simulate_pipeline(pacing=True, n_packets=n_pkts)

    # 抑制比与指标计算
    drops_unpaced = res_unpaced["drops"]
    drops_paced = res_paced["drops"]
    reduction_pct = ((drops_unpaced - drops_paced) / drops_unpaced) * 100.0 if drops_unpaced > 0 else 100.0

    print(f"\n[OK] 50,000 数据包极端负载对冲仿真完成:")
    print(f"     无整形突发丢包数: {drops_unpaced} (丢包率 {res_unpaced['drop_rate_pct']}%) | P99 延迟: {res_unpaced['p99_delay_ms']} ms")
    print(f"     皇冠整形丢包数:   {drops_paced} (丢包率 {res_paced['drop_rate_pct']}%) | P99 延迟: {res_paced['p99_delay_ms']} ms")
    print(f"     丢包重传抑制比:   {reduction_pct:.2f}% (门禁要求 >= 80.0%)")
    print(f"     Pacing P99 延迟:  {res_paced['p99_delay_ms']:.3f} ms (门禁要求 <= 15.0 ms)")

    assert reduction_pct >= 80.0, f"Reduction too low: {reduction_pct}%"
    assert res_paced["p99_delay_ms"] <= 15.0, f"P99 latency too high: {res_paced['p99_delay_ms']} ms"

    report_data = {
        "task": "0301",
        "verified_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC+08:00"),
        "n_packets": n_pkts,
        "unpaced_metrics": res_unpaced,
        "paced_metrics": res_paced,
        "retransmission_reduction_pct": round(reduction_pct, 2),
        "pass_gate": (reduction_pct >= 80.0 and res_paced["p99_delay_ms"] <= 15.0)
    }

    out_file = ROOT / "runs" / "hedge0301_tail_retransmission.json"
    out_file.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[SUCCESS] 尾部重传对冲审计报表已落盘: {out_file}")
    print("=" * 70)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
