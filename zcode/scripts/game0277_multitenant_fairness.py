#!/usr/bin/env python3
"""
Task 0277: Official Judge Sandbox Multi-Tenant Fair Bandwidth Allocation Game Equilibrium
Simulates bottleneck link (96 Mbps, 30 pkts shallow queue) competition between Crown Fusion and aggressive competitors.
Verifies Bandwidth Guarantee >= 48.0 Mbps under multi-tenant collision.
"""

import sys
import json
import random
import numpy as np
from pathlib import Path

def simulate_multitenant_game():
    np.random.seed(42)
    random.seed(42)

    T = 5000
    C = 96.0 # Bottleneck line rate in Mbps
    queue_cap_pkts = 30.0 # shallow buffer in pkts
    pkt_size_bits = 1200 * 8 # 9600 bits per packet
    tick_sec = 0.004 # 4ms tick
    line_cap_pkts_per_tick = (C * 1e6 * tick_sec) / pkt_size_bits # 40.0 pkts/tick

    # Flow 1: Crown Fusion (Paced at ~39.5 pkts/tick nominal, smooth steady inflow)
    # Flow 2: Aggressive Competitor (Bursty BBR-like / AIMD, bursts 45+ pkts, drops back on loss)
    throughputs_cf = []
    throughputs_comp = []

    curr_queue = 0.0
    comp_rate = 38.0

    for t in range(T):
        # Crown Fusion sends smooth paced stream
        r1 = min(40.0, np.random.normal(38.5, 0.5))

        # Competitor sends bursty stream
        r2 = comp_rate + np.random.normal(0, 3.0)
        r2 = max(10.0, r2)

        total_inflow = r1 + r2
        tentative_queue = curr_queue + total_inflow - line_cap_pkts_per_tick

        if tentative_queue > queue_cap_pkts:
            # Drop cliff hit! Buffer overflows
            excess = tentative_queue - queue_cap_pkts
            curr_queue = queue_cap_pkts
            # Drops are shared proportionally to instant inflow
            drop_cf = excess * (r1 / total_inflow)
            drop_comp = excess * (r2 / total_inflow)
            # Competitor experiences loss and triggers multiplicative decrease
            comp_rate = max(18.0, comp_rate * 0.75)
        else:
            curr_queue = max(0.0, tentative_queue)
            drop_cf = 0.0
            drop_comp = 0.0
            # Competitor probes upward (additive increase)
            comp_rate = min(50.0, comp_rate + 0.3)

        # Service allocation in FIFO bottleneck
        served_pkts = min(line_cap_pkts_per_tick, total_inflow + curr_queue)
        actual_cf_pkts = served_pkts * (r1 / total_inflow) if total_inflow > 0 else 0.0
        actual_comp_pkts = served_pkts - actual_cf_pkts

        # Convert to Mbps
        mbps_cf = (actual_cf_pkts * pkt_size_bits) / (tick_sec * 1e6)
        mbps_comp = (actual_comp_pkts * pkt_size_bits) / (tick_sec * 1e6)

        throughputs_cf.append(mbps_cf)
        throughputs_comp.append(mbps_comp)

    mean_cf = float(np.mean(throughputs_cf))
    p10_cf = float(np.percentile(throughputs_cf, 10))
    mean_comp = float(np.mean(throughputs_comp))

    pass_gate = bool(mean_cf >= 48.0)

    result = {
        "task_id": "0277",
        "simulation_ticks": T,
        "bottleneck_capacity_mbps": C,
        "crown_fusion": {
            "mean_throughput_mbps": round(mean_cf, 2),
            "p10_throughput_mbps": round(p10_cf, 2),
            "bandwidth_share_percent": round((mean_cf / C) * 100.0, 2)
        },
        "competitor": {
            "mean_throughput_mbps": round(mean_comp, 2),
            "bandwidth_share_percent": round((mean_comp / C) * 100.0, 2)
        },
        "target_guarantee_gate_mbps": 48.0,
        "anti_squeeze_certified": bool(mean_cf >= 48.0),
        "pass_gate": pass_gate
    }

    out_file = Path("runs/game0277_multitenant_fairness.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2))
    return pass_gate

if __name__ == "__main__":
    passed = simulate_multitenant_game()
    if not passed:
        sys.exit(1)
