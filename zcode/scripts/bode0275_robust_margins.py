#!/usr/bin/env python3
"""
Task 0275: Robust Gain & Phase Margins Under Burst Cross-Traffic in Bottleneck Links
Evaluates frequency response, Bode plot parameters, Gain Margin (GM), and Phase Margin (PM)
for the closed-loop delayed fluid flow control system across +/- 30% gain perturbations.
"""

import sys
import json
import math
import numpy as np
from pathlib import Path

def compute_bode_margins():
    # Delay tau = 10 ms (RTT)
    tau = 0.010
    
    # Controller proportional gain K
    nominal_K = 28.0
    perturbations = [-0.30, 0.0, 0.30]

    results = []
    for p in perturbations:
        K = nominal_K * (1.0 + p)
        # Gain crossover frequency: |L(j*omega_gc)| = 1 => omega_gc = K
        omega_gc = K
        # Phase at omega_gc: -90 deg - (omega_gc * tau * 180 / pi)
        phase_at_gc_deg = -90.0 - (omega_gc * tau * 180.0 / math.pi)
        pm_deg = 180.0 + phase_at_gc_deg # Phase margin

        # Phase crossover frequency: angle = -180 deg => omega_pc * tau = pi / 2
        omega_pc = math.pi / (2.0 * tau)
        # Magnitude at omega_pc: K / omega_pc
        mag_at_pc = K / omega_pc
        gm_linear = 1.0 / mag_at_pc
        gm_db = 20.0 * math.log10(gm_linear)

        results.append({
            "gain_perturbation_percent": int(p * 100),
            "effective_K": round(K, 2),
            "gain_crossover_freq_rad_s": round(omega_gc, 2),
            "phase_crossover_freq_rad_s": round(omega_pc, 2),
            "phase_margin_deg": round(pm_deg, 2),
            "gain_margin_db": round(gm_db, 2),
            "is_stable": bool(pm_deg >= 45.0 and gm_db >= 6.0)
        })

    # Worst-case evaluation
    worst_pm = min(r["phase_margin_deg"] for r in results)
    worst_gm = min(r["gain_margin_db"] for r in results)

    pass_gate = bool(worst_pm >= 45.0 and worst_gm >= 6.0)

    summary = {
        "task_id": "0275",
        "delay_tau_ms": tau * 1000.0,
        "nominal_K": nominal_K,
        "evaluations": results,
        "worst_phase_margin_deg": worst_pm,
        "target_pm_gate_deg": 45.0,
        "worst_gain_margin_db": worst_gm,
        "target_gm_gate_db": 6.0,
        "pass_gate": pass_gate
    }

    out_file = Path("runs/bode0275_robust_margins.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(json.dumps(summary, indent=2))
    return pass_gate

if __name__ == "__main__":
    passed = compute_bode_margins()
    if not passed:
        sys.exit(1)
