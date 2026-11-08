# -*- coding: utf-8 -*-
"""
Task 0470: Pontryagin Maximum/Minimum Principle (PMP) Energy-Delay Pareto Optimal Trajectory
- Formulate continuous-time shallow buffer dynamics: dq/dt = r(t) - C
- Minimize J = int_0^T [ 0.5 * r(t)^2 + alpha * q(t) ] dt
- Derive exact costate dynamics p(t) and Hamiltonian conservation
- Sweep alpha to verify strictly monotonic Pareto frontier
- Target: Hamiltonian conservation error < 1e-6, Pareto monotonicity 100.0%
"""

import sys
import json
import numpy as np

def compute_pmp_trajectory(alpha=1.0, q0=5.0, qT=0.0, C=10.0, T=5.0, N=500):
    t = np.linspace(0, T, N)
    dt = T / (N - 1)
    
    # Analytical costate initial value from boundary condition q(T) = qT
    p0 = (q0 - qT) / T + 0.5 * alpha * T - C
    
    # Costate p(t) = p0 - alpha * t
    p_t = p0 - alpha * t
    
    # Optimal control r*(t) = -p(t)
    r_t = -p_t
    
    # State trajectory q(t) = q0 + 0.5 * alpha * t^2 - (p0 + C) * t
    q_t = q0 + 0.5 * alpha * (t ** 2) - (p0 + C) * t
    
    # Hamiltonian H(t) = 0.5 * r(t)^2 + alpha * q(t) + p(t) * (r(t) - C)
    # H = 0.5 * r^2 + alpha * q + (-r) * (r - C) = -0.5 * r^2 + alpha * q + r * C
    H_t = 0.5 * (r_t ** 2) + alpha * q_t + p_t * (r_t - C)
    
    # Conservation error
    h_error = float(np.max(np.abs(H_t - H_t[0])))
    
    # Boundary error
    bc_error = float(abs(q_t[-1] - qT))
    
    # Objective components: Energy and Delay
    energy = float(np.trapezoid(0.5 * (r_t ** 2), t))
    delay = float(np.trapezoid(q_t, t))
    
    return {
        "alpha": alpha,
        "energy": energy,
        "delay": delay,
        "hamiltonian_error": h_error,
        "boundary_error": bc_error
    }

def main():
    print("=== Task 0470: PMP Energy-Delay Pareto Optimal Trajectory ===")
    
    alphas = np.logspace(-1, 1, 20)
    results = []
    h_errors = []
    bc_errors = []
    
    for a in alphas:
        res = compute_pmp_trajectory(alpha=a)
        results.append(res)
        h_errors.append(res["hamiltonian_error"])
        bc_errors.append(res["boundary_error"])
        
    max_h_error = float(np.max(h_errors))
    max_bc_error = float(np.max(bc_errors))
    
    # Check Pareto monotonicity: as alpha increases, delay must decrease and energy must increase
    energies = [r["energy"] for r in results]
    delays = [r["delay"] for r in results]
    
    # Difference checks
    energy_diffs = np.diff(energies)
    delay_diffs = np.diff(delays)
    
    energy_strictly_increasing = bool(np.all(energy_diffs > 0))
    delay_strictly_decreasing = bool(np.all(delay_diffs < 0))
    pareto_monotonic = energy_strictly_increasing and delay_strictly_decreasing
    
    passed = (max_h_error < 1e-6) and (max_bc_error < 1e-6) and pareto_monotonic
    
    summary = {
        "alpha_sample_count": len(alphas),
        "max_hamiltonian_conservation_error": max_h_error,
        "max_boundary_condition_error": max_bc_error,
        "energy_strictly_increasing": energy_strictly_increasing,
        "delay_strictly_decreasing": delay_strictly_decreasing,
        "pareto_monotonic_rate": 100.0 if pareto_monotonic else 0.0,
        "target_h_threshold": 1e-6,
        "passed": bool(passed)
    }
    
    print(json.dumps(summary, indent=2))
    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    main()

