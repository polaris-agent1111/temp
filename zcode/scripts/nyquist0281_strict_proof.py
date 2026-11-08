#!/usr/bin/env python3
"""
Task 0281: Generalized Nyquist Stability Criterion Analytical Proof in Delayed Network Flow Control
Evaluates Nyquist contour mapping, encirclements of critical point (-1, j0), and Cauchy argument principle.
"""

import sys
import json
import math
import numpy as np
from pathlib import Path

def prove_nyquist_stability():
    K = 28.0 # Controller loop gain
    tau = 0.010 # Delay tau = 10ms (RTT)

    # 1. Frequency sweep omega from 0.1 to 1000 rad/s
    omegas = np.logspace(-1, 3, 2000)
    L_real = []
    L_imag = []

    for w in omegas:
        # L(jw) = (K / w) * exp(-j * (w * tau + pi/2))
        mag = K / w
        phase = -0.5 * math.pi - (w * tau)
        re = mag * math.cos(phase)
        im = mag * math.sin(phase)
        L_real.append(re)
        L_imag.append(im)

    L_real = np.array(L_real)
    L_imag = np.array(L_imag)

    # 2. Find negative real axis intercept (where phase = -pi, or imag = 0 and real < 0)
    omega_pc = math.pi / (2.0 * tau) # 157.079 rad/s
    mag_at_pc = K / omega_pc # 28.0 / 157.08 = 0.17825
    real_axis_intercept = -mag_at_pc # -0.17825

    distance_to_critical_point = abs(-1.0 - real_axis_intercept) # 1 - 0.17825 = 0.82175

    # 3. Calculate encirclement count N of (-1, j0) via winding number
    # Shift origin to (-1, j0)
    shifted_re = L_real - (-1.0)
    shifted_im = L_imag - 0.0
    angles = np.arctan2(shifted_im, shifted_re)
    # Unwrapped phase difference along contour
    unwrapped = np.unwrap(angles)
    total_angle_sweep_rad = float(unwrapped[-1] - unwrapped[0])
    encirclements_N = round(total_angle_sweep_rad / (2.0 * math.pi))

    open_loop_unstable_poles_P = 0
    closed_loop_unstable_poles_Z = encirclements_N + open_loop_unstable_poles_P

    is_asymptotically_stable = bool(closed_loop_unstable_poles_Z == 0 and distance_to_critical_point >= 0.50)

    result = {
        "task_id": "0281",
        "loop_gain_K": K,
        "feedback_delay_tau_sec": tau,
        "phase_crossover_freq_rad_s": round(omega_pc, 3),
        "real_axis_intercept": round(real_axis_intercept, 4),
        "distance_to_minus_one_point": round(distance_to_critical_point, 4),
        "target_distance_gate": 0.50,
        "encirclements_count_N": encirclements_N,
        "open_loop_unstable_poles_P": open_loop_unstable_poles_P,
        "closed_loop_unstable_poles_Z": closed_loop_unstable_poles_Z,
        "asymptotically_stable_certified": is_asymptotically_stable,
        "pass_gate": is_asymptotically_stable
    }

    out_file = Path("runs/nyquist0281_strict_proof.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2))
    return is_asymptotically_stable

if __name__ == "__main__":
    passed = prove_nyquist_stability()
    if not passed:
        sys.exit(1)
