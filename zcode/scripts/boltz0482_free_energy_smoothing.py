# -*- coding: utf-8 -*-
"""
Task 0482: Generalized Boltzmann Machine Free Energy Minimization for Traffic Smoothing
- Microscopic packet arrivals as spin states s in {0, 1}^N
- Repulsive coupling matrix W (smoothing penalty)
- Variational Helmholtz Free Energy: F(m) = -0.5 m^T W m - b^T m - T * S(m)
- Mean-field fixed point: m_i* = sigmoid((W m* + b)_i / T)
- Target: Free energy dissipation monotonicity rate 100.0%, thermodynamic equilibrium relative error < 1.0%
"""

import sys
import json
import numpy as np

def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -25.0, 25.0)))

class BoltzmannTrafficSmoother:
    def __init__(self, N=6, T_temp=1.5, seed=42):
        np.random.seed(seed)
        self.N = N
        self.T = T_temp
        
        # Repulsive coupling W: negative off-diagonal entries (penalizes simultaneous bursts)
        A = np.random.uniform(0.2, 0.8, size=(N, N))
        self.W = -0.5 * (A + A.T)
        np.fill_diagonal(self.W, 0.0)
        
        # Bias vector b: traffic demand drive
        self.b = np.random.uniform(1.0, 3.0, size=N)
        
    def free_energy(self, m):
        # F(m) = -0.5 * m^T W m - b^T m + T * sum( m*ln(m) + (1-m)*ln(1-m) )
        m_safe = np.clip(m, 1e-12, 1.0 - 1e-12)
        internal_energy = -0.5 * float(m @ self.W @ m) - float(self.b @ m)
        entropy = -float(np.sum(m_safe * np.log(m_safe) + (1.0 - m_safe) * np.log(1.0 - m_safe)))
        return internal_energy - self.T * entropy
    
    def free_energy_gradient(self, m):
        # dF/dm_i = -(W m)_i - b_i + T * ln( m_i / (1 - m_i) )
        m_safe = np.clip(m, 1e-12, 1.0 - 1e-12)
        grad = -(self.W @ m) - self.b + self.T * np.log(m_safe / (1.0 - m_safe))
        return grad
    
    def mean_field_map(self, m):
        return sigmoid((self.W @ m + self.b) / self.T)

def run_free_energy_relaxation(smoother, dt=0.02, max_steps=1000):
    m = np.random.uniform(0.1, 0.9, size=smoother.N)
    
    free_energies = []
    dissipation_rates = []
    
    for step in range(max_steps):
        F_curr = smoother.free_energy(m)
        free_energies.append(F_curr)
        
        grad = smoother.free_energy_gradient(m)
        # Gradient flow: dm/dt = -grad
        m_next = np.clip(m - dt * grad, 1e-6, 1.0 - 1e-6)
        
        # Time derivative of Free energy: dF/dt ~ (F_next - F_curr) / dt
        F_next = smoother.free_energy(m_next)
        dF_dt = (F_next - F_curr) / dt
        dissipation_rates.append(dF_dt)
        
        m = m_next
        if np.linalg.norm(grad) < 1e-5:
            break
            
    # Check fixed point condition: ||m - mean_field_map(m)||_inf
    m_target = smoother.mean_field_map(m)
    eq_error = float(np.max(np.abs(m - m_target))) * 100.0
    
    # Monotonic dissipation: dF/dt <= 1e-6 everywhere
    monotonic = bool(np.all(np.array(dissipation_rates) <= 1e-6))
    
    return {
        "equilibrium_error_percent": eq_error,
        "monotonic_dissipation": monotonic,
        "final_free_energy": float(free_energies[-1]),
        "steps": len(free_energies)
    }

def main():
    print("=== Task 0482: Boltzmann Machine Free Energy Minimization ===")
    
    runs = 25
    eq_errors = []
    mono_flags = []
    
    for r in range(runs):
        smoother = BoltzmannTrafficSmoother(N=6, T_temp=2.0, seed=100 + r)
        res = run_free_energy_relaxation(smoother, dt=0.015)
        eq_errors.append(res["equilibrium_error_percent"])
        mono_flags.append(res["monotonic_dissipation"])
        
    mean_eq_err = float(np.mean(eq_errors))
    max_eq_err = float(np.max(eq_errors))
    mono_rate = (sum(mono_flags) / runs) * 100.0
    
    passed = (max_eq_err < 1.0) and (mono_rate == 100.0)
    
    summary = {
        "runs": runs,
        "mean_equilibrium_error_percent": mean_eq_err,
        "max_equilibrium_error_percent": max_eq_err,
        "target_error_threshold_percent": 1.0,
        "free_energy_monotonic_dissipation_rate": mono_rate,
        "passed": bool(passed)
    }
    
    print(json.dumps(summary, indent=2))
    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
