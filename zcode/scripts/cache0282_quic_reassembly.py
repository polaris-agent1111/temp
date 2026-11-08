#!/usr/bin/env python3
"""
Task 0282: QUIC Stream Reassembly Sliding Window CPU Cache Miss & Memory Bandwidth Evaluation
Simulates CPU L1/L2/L3 cache line accesses (64B lines) for reassembly metadata control block
and sliding window pointer structures under 15% out-of-order packet conditions.
"""

import sys
import json
import random
import numpy as np
from pathlib import Path

def evaluate_reassembly_cache():
    np.random.seed(42)
    random.seed(42)

    n_packets = 10000
    cache_line_size = 64 # bytes
    l1_cache_lines = 512 # 32 KB L1 data cache (512 lines of 64B)
    reorder_prob = 0.15 # 15% packets reordered

    # Stream arrival sequence with 15% reordering
    seq = list(range(n_packets))
    for i in range(n_packets):
        if random.random() < reorder_prob:
            swap_with = min(n_packets - 1, max(0, i + random.randint(-15, 15)))
            seq[i], seq[swap_with] = seq[swap_with], seq[i]

    # 4-way set associative cache simulation
    n_sets = l1_cache_lines // 4 # 128 sets
    l1_tags = [[] for _ in range(n_sets)]

    l1_hits = 0
    l1_misses = 0

    def access_address(addr):
        nonlocal l1_hits, l1_misses
        line_addr = addr // cache_line_size
        set_idx = line_addr % n_sets
        tag = line_addr // n_sets

        if tag in l1_tags[set_idx]:
            l1_hits += 1
            l1_tags[set_idx].remove(tag)
            l1_tags[set_idx].append(tag)
            return True
        else:
            l1_misses += 1
            if len(l1_tags[set_idx]) >= 4:
                l1_tags[set_idx].pop(0)
            l1_tags[set_idx].append(tag)
            return False

    # Warm up cache with control block (4KB located at base address 0x10000)
    cb_base = 0x10000
    for offset in range(0, 4096, cache_line_size):
        access_address(cb_base + offset)

    # Process packet stream
    # Each packet touches:
    # 1. Stream Control Block (8 hot accesses to cb_base)
    # 2. Window Ring Descriptor (2 accesses to ring table at 0x18000)
    # 3. If out of order: 2 scattered accesses to interval tree nodes at 0x30000 + (pkt_idx * 64)
    extra_miss_cycles = 0
    baseline_cycles_per_pkt = 180

    for pkt_idx in seq:
        # Hot control block accesses
        for _ in range(8):
            access_address(cb_base + (pkt_idx % 8) * cache_line_size)

        # Window ring descriptor
        access_address(0x18000 + (pkt_idx % 32) * cache_line_size)
        access_address(0x18000 + ((pkt_idx + 1) % 32) * cache_line_size)

        # Check out-of-order penalty
        is_ooo = abs(pkt_idx - seq[min(n_packets - 1, pkt_idx)]) > 0
        if is_ooo:
            # Tree node lookup (cold pointer chase)
            node_addr = 0x30000 + (pkt_idx % 1024) * cache_line_size
            miss1 = not access_address(node_addr)
            miss2 = not access_address(node_addr + 64)
            if miss1 or miss2:
                extra_miss_cycles += 12 # 12 cycles L2 penalty

    total_accesses = l1_hits + l1_misses
    l1_miss_rate_percent = (l1_misses / total_accesses) * 100.0

    total_baseline_cycles = n_packets * baseline_cycles_per_pkt
    total_cycles = total_baseline_cycles + extra_miss_cycles
    throughput_degradation_percent = (extra_cycles := extra_miss_cycles) / total_cycles * 100.0

    pass_gate = bool(l1_miss_rate_percent <= 4.5 and throughput_degradation_percent <= 1.5)

    result = {
        "task_id": "0282",
        "packets_processed": n_packets,
        "reorder_probability": reorder_prob,
        "l1_cache_size_kb": 32,
        "total_memory_accesses": total_accesses,
        "l1_hits_count": l1_hits,
        "l1_misses_count": l1_misses,
        "l1_miss_rate_percent": round(l1_miss_rate_percent, 2),
        "target_miss_rate_gate_percent": 4.5,
        "throughput_degradation_percent": round(throughput_degradation_percent, 2),
        "target_degradation_gate_percent": 1.5,
        "pass_gate": pass_gate
    }

    out_file = Path("runs/cache0282_quic_reassembly.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2))
    return pass_gate

if __name__ == "__main__":
    passed = evaluate_reassembly_cache()
    if not passed:
        sys.exit(1)
