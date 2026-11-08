#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0204: Microsecond-level token bucket reset and queue drain transition dynamics.
Analyzes the boundary between consecutive file downloads (Bin N to Bin N+1).
Quantifies queue settling and drain time to guarantee zero Head-of-Line (HoL) blocking (< 2.1 ms).
"""
import numpy as np

def simulate_interstage_transition():
    # Simulation at microsecond resolution
    dt_us = 10.0  # 10us step
    sim_time_ms = 10.0
    steps = int(sim_time_ms * 1000 / dt_us)
    
    # At t = 0 (boundary of Bin transition):
    # Previous bin left behind a worst-case residual queue: Q_0 = 18 packets
    # Pacer parameters in new bin: r = 37 pkts / 4000us, bucket_cap = 40
    # Service rate per microsecond: mu = 37.0 / 4000.0 = 0.00925 pkts/us
    # Physical egress capacity: C = 90 Mbps / (1200 * 8 bits) = 0.009375 pkts/us
    
    Q_0 = 18.0
    drain_rate_pkts_per_us = 37.0 / 4000.0
    
    # Differential equation: dQ/dt = -mu (since arrival paused briefly at socket boundary)
    # Time to completely drain queue: t_drain = Q_0 / mu
    t_drain_us = Q_0 / drain_rate_pkts_per_us
    t_drain_ms = t_drain_us / 1000.0
    
    # Detailed dynamic simulation with token refill
    queue = np.zeros(steps)
    tokens = np.zeros(steps)
    
    q_curr = Q_0
    tok_curr = 0.0  # Tokens start from reset
    
    settling_step = -1
    for i in range(steps):
        t_us = i * dt_us
        # Token refill: 37 tokens every 4000us
        tok_curr += (37.0 / 4000.0) * dt_us
        if tok_curr > 40.0:
            tok_curr = 40.0
            
        # Queue drain
        drained = min(q_curr, (37.0 / 4000.0) * dt_us)
        q_curr -= drained
        
        queue[i] = q_curr
        tokens[i] = tok_curr
        
        if q_curr <= 0.01 and settling_step == -1:
            settling_step = i
            
    settling_time_ms = (settling_step * dt_us) / 1000.0 if settling_step != -1 else t_drain_ms
    
    print("=== Task 0204: Inter-Stage Queue Drain Dynamics ===")
    print(f"initial_residual_queue: {Q_0:.1f} packets")
    print(f"drain_rate: {drain_rate_pkts_per_us * 1000:.2f} pkts/ms ({drain_rate_pkts_per_us * 1000 * 1200 * 8 / 1e6:.2f} Mbps)")
    print(f"theoretical_drain_time: {t_drain_ms:.3f} ms")
    print(f"simulated_settling_time: {settling_time_ms:.3f} ms (Gate: < 2.1 ms)")
    print(f"head_of_line_blocking_eliminated: {settling_time_ms < 2.1}")
    
    return {
        "residual_q": Q_0,
        "drain_time_ms": float(settling_time_ms),
        "gate_passed": bool(settling_time_ms < 2.1)
    }

if __name__ == "__main__":
    simulate_interstage_transition()
