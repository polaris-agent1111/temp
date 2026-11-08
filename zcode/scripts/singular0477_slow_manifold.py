# -*- coding: utf-8 -*-
"""
Task 0477: Multi-Time-Scale Singular Perturbation Slow Invariant Manifold
- Pacer microsecond burst (fast z) vs RTT feedback window (slow x)
- Singular perturbation system: dx/dt = f(x, z), eps * dz/dt = g(x, z)
- High-order asymptotic expansion of slow invariant manifold: z = h0(x) + eps * h1(x) + eps^2 * h2(x)
- Target: Manifold invariance residual < 1e-4, Asymptotic stability rate 100.0%
"""

import sys
import json
import numpy as np

class SingularlyPerturbedPacingSystem:
    def __init__(self, eps=0.01, a=2.5, b=2.0, c=0.5):
        self.eps = eps
        self.a = a
        self.b = b
        self.c = c
        
    def f(self, x, z):
        return -self.c * x + z
    
    def g(self, x, z):
        return -self.a * z + self.b * x
    
    def h0(self, x):
        return (self.b / self.a) * x
    
    def dh0_dx(self):
        return self.b / self.a
    
    def h1(self, x):
        # Order eps: -a * h1 = dh0/dx * (-c*x + h0)
        # h1 = -(dh0/dx / a) * (b/a - c) * x
        k1 = -(self.dh0_dx() / self.a) * (self.b / self.a - self.c)
        return k1 * x
    
    def dh1_dx(self):
        return -(self.dh0_dx() / self.a) * (self.b / self.a - self.c)
    
    def h2(self, x):
        # Order eps^2: -a * h2 = dh0/dx * h1 + dh1/dx * (-c*x + h0)
        # h2 = -(1/a) * [ dh0_dx * k1 * x + k1 * (b/a - c) * x ]
        k1 = self.dh1_dx()
        k2 = -(1.0 / self.a) * (self.dh0_dx() * k1 + k1 * (self.b / self.a - self.c))
        return k2 * x
    
    def slow_manifold(self, x):
        return self.h0(x) + self.eps * self.h1(x) + (self.eps ** 2) * self.h2(x)
    
    def manifold_invariance_residual(self, x):
        h = self.slow_manifold(x)
        dh_dx = self.dh0_dx() + self.eps * self.dh1_dx() + (self.eps ** 2) * (-(1.0 / self.a) * (self.dh0_dx() * self.dh1_dx() + self.dh1_dx() * (self.b / self.a - self.c)))
        lhs = self.eps * (dh_dx * self.f(x, h))
        rhs = self.g(x, h)
        return abs(lhs - rhs)

def verify_system_stability_and_invariance(eps=0.01):
    sys_obj = SingularlyPerturbedPacingSystem(eps=eps, a=2.5, b=2.0, c=0.5)
    
    dg_dz = -sys_obj.a
    is_hurwitz = bool(dg_dz < -0.5)
    
    x_grid = np.linspace(1.0, 50.0, 100)
    residuals = [sys_obj.manifold_invariance_residual(x) for x in x_grid]
    
    max_res = float(np.max(residuals))
    mean_res = float(np.mean(residuals))
    
    # Trajectory integration
    dt = 1e-4
    T = 2.0
    steps = int(T / dt)
    
    x_curr = 20.0
    z_curr = 5.0
    
    traj_dist_to_manifold = []
    
    for _ in range(steps):
        dx = sys_obj.f(x_curr, z_curr) * dt
        dz = (sys_obj.g(x_curr, z_curr) / eps) * dt
        x_curr += dx
        z_curr += dz
        h_val = sys_obj.slow_manifold(x_curr)
        traj_dist_to_manifold.append(abs(z_curr - h_val))
        
    post_transient_dist = float(np.mean(traj_dist_to_manifold[1000:]))
    manifold_glued = bool(post_transient_dist < 1e-3)
    
    passed = is_hurwitz and (max_res < 1e-4) and manifold_glued
    
    return {
        "eps": eps,
        "is_hurwitz": is_hurwitz,
        "boundary_layer_eigenvalue": dg_dz,
        "max_invariance_residual": max_res,
        "mean_invariance_residual": mean_res,
        "post_transient_manifold_distance": post_transient_dist,
        "passed": bool(passed)
    }

def main():
    print("=== Task 0477: Singular Perturbation Slow Manifold Analysis ===")
    
    eps_values = [0.002, 0.005, 0.008, 0.01, 0.012]
    all_passed = []
    max_residuals = []
    
    for eps in eps_values:
        res = verify_system_stability_and_invariance(eps=eps)
        all_passed.append(res["passed"])
        max_residuals.append(res["max_invariance_residual"])
        
    stability_rate = (sum(all_passed) / len(eps_values)) * 100.0
    max_res = float(np.max(max_residuals))
    
    overall_passed = (stability_rate == 100.0) and (max_res < 1e-4)
    
    summary = {
        "tested_epsilons": eps_values,
        "asymptotic_stability_rate": stability_rate,
        "max_slow_manifold_residual": max_res,
        "target_residual_threshold": 1e-4,
        "passed": bool(overall_passed)
    }
    
    print(json.dumps(summary, indent=2))
    if not overall_passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
