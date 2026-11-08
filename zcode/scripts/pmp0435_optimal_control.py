# -*- coding: utf-8 -*-
"""
Task 0435: Pontryagin Minimum Principle and Costate Equation Solver for Optimal Dynamic Pacing Control
"""

import sys
import json
import numpy as np

def solve_pmp_tpbvp(x0=25.0, xf=0.0, T=5.0, q=2.0, r=0.5, s=10.0, u_target=40.0, mu0=38.0, N=1000):
    """
    State: dx/dt = u - mu0
    Costate: dp/dt = -q * x
    Optimal control: u*(t) = u_target - p(t) / r
    Hamiltonian: H = 0.5 * q * x^2 + 0.5 * r * (u - u_target)^2 + p * (u - mu0)
    
    Coupled linear system:
    dx/dt = -p / r + (u_target - mu0)
    dp/dt = -q * x
    
    Second order ODE for x(t):
    d^2 x / dt^2 = -1/r dp/dt = (q/r) * x
    General solution:
    x(t) = c1 * cosh(omega * t) + c2 * sinh(omega * t) + x_eq
    where omega = sqrt(q / r), and for autonomous system x_eq = 0 (since d^2 x / dt^2 - omega^2 x = 0).
    Wait, dx/dt = -p/r + v0 where v0 = u_target - mu0.
    d^2 x / dt^2 = -1/r dp/dt = (q/r) x = omega^2 x.
    So x(t) = c1 * cosh(omega * t) + c2 * sinh(omega * t).
    Then p(t) = r * (v0 - dx/dt) = r * (v0 - omega * (c1 * sinh(omega * t) + c2 * cosh(omega * t))).
    
    Boundary conditions:
    1) x(0) = c1 = x0
    2) Transversality: p(T) = s * (x(T) - xf)
       r * (v0 - omega * (x0 * sinh(omega * T) + c2 * cosh(omega * T))) = s * (x0 * cosh(omega * T) + c2 * sinh(omega * T) - xf)
       Rearranging for c2:
       c2 * [ r * omega * cosh(omega * T) + s * sinh(omega * T) ] = r * v0 - r * omega * x0 * sinh(omega * T) - s * (x0 * cosh(omega * T) - xf)
    """
    v0 = u_target - mu0
    omega = np.sqrt(q / r)
    
    # Boundary solve
    c1 = x0
    denom = r * omega * np.cosh(omega * T) + s * np.sinh(omega * T)
    numer = r * v0 - r * omega * x0 * np.sinh(omega * T) - s * (x0 * np.cosh(omega * T) - xf)
    c2 = numer / denom
    
    # Grid evaluation
    t_grid = np.linspace(0, T, N + 1)
    x = c1 * np.cosh(omega * t_grid) + c2 * np.sinh(omega * t_grid)
    dx_dt = omega * (c1 * np.sinh(omega * t_grid) + c2 * np.cosh(omega * t_grid))
    p = r * (v0 - dx_dt)
    u_star = u_target - p / r
    
    # Verify costate equation dp/dt = -q * x numerically
    dp_dt_analytical = -q * x
    dp_dt_numeric = np.gradient(p, t_grid)
    costate_error = float(np.max(np.abs(dp_dt_numeric[1:-1] - dp_dt_analytical[1:-1])))
    
    # Verify boundary conditions
    bc_x0_err = float(abs(x[0] - x0))
    bc_terminal_err = float(abs(p[-1] - s * (x[-1] - xf)))
    
    # Compute Hamiltonian along trajectory
    # H = 0.5 * q * x^2 + 0.5 * r * (u_star - u_target)^2 + p * (u_star - mu0)
    H = 0.5 * q * (x ** 2) + 0.5 * r * ((u_star - u_target) ** 2) + p * (u_star - mu0)
    H_mean = float(np.mean(H))
    H_var = float(np.max(np.abs(H - H_mean)))
    
    return {
        "x0": x0,
        "xf": xf,
        "T": T,
        "omega": float(omega),
        "c1": float(c1),
        "c2": float(c2),
        "bc_initial_error": bc_x0_err,
        "bc_transversality_error": bc_terminal_err,
        "costate_ode_error": costate_error,
        "hamiltonian_mean": H_mean,
        "hamiltonian_conservation_error": H_var,
        "tpbvp_convergence_rate": 100.0 if (bc_x0_err < 1e-8 and bc_terminal_err < 1e-8) else 0.0,
        "passed": bool((bc_x0_err < 1e-8) and (bc_terminal_err < 1e-8) and (H_var < 0.001))
    }

def main():
    result = solve_pmp_tpbvp(x0=25.0, xf=0.0, T=5.0, q=2.0, r=0.5, s=10.0, u_target=40.0, mu0=38.0, N=1000)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
