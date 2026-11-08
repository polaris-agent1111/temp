# -*- coding: utf-8 -*-
"""
Task 0486: Hybrid Automata Reachability Set Verification for Shallow Buffer Pacing
- Hybrid dynamics: Discrete packet dispatch/ACK events + continuous fluid queue drainage
- Modes: {Normal Pacing, Microburst, Backoff, Recovery}
- Invariant set: Safe Set S = { (m, q) : q <= B_cap }
- Unsafe Set: U = { q > B_cap }
- Target: Unsafe reachability probability 0.0%, Invariant violation rate 0.0%
"""

import sys
import json
import numpy as np

class ShallowBufferHybridAutomaton:
    def __init__(self, B_cap=50.0, C_drain=10.0, Q_thresh=35.0, seed=42):
        np.random.seed(seed)
        self.B_cap = B_cap          # Maximum shallow buffer capacity
        self.C_drain = C_drain      # Switch continuous drain rate (pkts/ms)
        self.Q_thresh = Q_thresh    # Threshold to switch to Backoff mode
        
        # Pacing rates in different discrete modes (pkts/ms)
        self.rates = {
            "Normal": 10.0,         # Line rate matching drain
            "Microburst": 14.0,     # Transient burst
            "Backoff": 6.0,         # Protective drainage
            "Recovery": 8.5
        }
        
    def simulate_hybrid_trajectory(self, T=100.0, dt=0.01, burst_prob=0.08):
        # Initial state
        mode = "Normal"
        q = np.random.uniform(2.0, 10.0)
        
        time_steps = int(T / dt)
        q_history = []
        mode_history = []
        unsafe_violations = 0
        
        for step in range(time_steps):
            # 1. Continuous flow in current mode
            r = self.rates[mode]
            dq_dt = r - self.C_drain
            q = max(0.0, q + dq_dt * dt)
            
            # 2. Check safety invariant
            if q > self.B_cap:
                unsafe_violations += 1
                
            # 3. Discrete Guard Transitions
            if mode == "Microburst":
                # If queue exceeds threshold, immediately guard switch to Backoff
                if q >= self.Q_thresh:
                    mode = "Backoff"
                elif np.random.rand() < 0.05:  # Burst naturally ends
                    mode = "Normal"
            elif mode == "Backoff":
                # Once queue drains below safety level, transition to Recovery
                if q <= 15.0:
                    mode = "Recovery"
            elif mode == "Recovery":
                if q <= 8.0:
                    mode = "Normal"
            elif mode == "Normal":
                # Stochastic cross-traffic microburst triggers burst mode
                if np.random.rand() < burst_prob:
                    mode = "Microburst"
                    
            q_history.append(q)
            mode_history.append(mode)
            
        q_history = np.array(q_history)
        max_q = float(np.max(q_history))
        mean_q = float(np.mean(q_history))
        
        # Invariant preserved if max_q <= B_cap
        is_safe = (unsafe_violations == 0) and (max_q <= self.B_cap)
        
        return {
            "max_queue": max_q,
            "mean_queue": mean_q,
            "unsafe_violations": unsafe_violations,
            "is_safe": bool(is_safe)
        }

def main():
    print("=== Task 0486: Hybrid Automata Reachability Verification ===")
    
    runs = 30
    safe_flags = []
    max_queues = []
    violations = []
    
    for r in range(runs):
        ha = ShallowBufferHybridAutomaton(B_cap=50.0, C_drain=10.0, Q_thresh=35.0, seed=100 + r)
        res = ha.simulate_hybrid_trajectory(T=200.0, dt=0.01, burst_prob=0.10)
        safe_flags.append(res["is_safe"])
        max_queues.append(res["max_queue"])
        violations.append(res["unsafe_violations"])
        
    safety_rate = (sum(safe_flags) / runs) * 100.0
    overall_violations = sum(violations)
    max_observed_q = float(np.max(max_queues))
    
    # Reachability of unsafe set: probability of reaching q > B_cap (50.0)
    unsafe_prob = float(overall_violations > 0)
    
    passed = (safety_rate == 100.0) and (overall_violations == 0) and (max_observed_q <= 50.0)
    
    summary = {
        "runs": runs,
        "invariant_set_compliance_rate": safety_rate,
        "unsafe_set_reachability_prob": unsafe_prob,
        "max_observed_queue_pkts": max_observed_q,
        "buffer_capacity_limit": 50.0,
        "total_overflow_events": overall_violations,
        "passed": bool(passed)
    }
    
    print(json.dumps(summary, indent=2))
    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
