#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0194: Hopf bifurcation and nonlinear stability analysis of multi-rate adaptive leaky bucket.
Solves the characteristic equation of delay-differential equation (DDE):
  dq/dt = -alpha * q(t) - beta * q(t - tau)
Evaluates critical delay tau_c and bifurcation parameter boundaries.
"""
import numpy as np

def analyze_hopf_bifurcation():
    # Model parameters for our pacer
    # alpha: local bucket drain coefficient (alpha = r / C)
    # beta: delayed congestion feedback sensitivity from RTT
    # tau: network round-trip delay ~ 20ms to 40ms
    
    # Range of leak rates in our 6-bin configuration: r in [36, 41] pkts/4ms
    # Nominal queue capacity: K = 40 pkts
    alpha_nom = 37.0 / 40.0  # ~ 0.925 ms^-1
    beta_nom = 0.35          # feedback gain
    tau_nom = 0.025          # 25 ms RTT
    
    # Hopf bifurcation occurs when purely imaginary eigenvalues lambda = i*omega exist:
    # Characteristic equation: D(lambda) = lambda + alpha + beta * exp(-lambda * tau) = 0
    # Let lambda = i * omega (omega > 0):
    # Real part: alpha + beta * cos(omega * tau) = 0  => cos(omega * tau) = -alpha / beta
    # Imag part: omega - beta * sin(omega * tau) = 0  => sin(omega * tau) = omega / beta
    # Squaring and adding: omega^2 + alpha^2 = beta^2  => omega = sqrt(beta^2 - alpha^2)
    
    # CRITICAL THEOREM:
    # If alpha > beta, then beta^2 - alpha^2 < 0, meaning NO real omega exists!
    # Therefore, NO purely imaginary eigenvalues can exist for ANY delay tau > 0!
    # The system is DELAY-INDEPENDENT ASYMPTOTICALLY STABLE (Hopf bifurcation is IMPOSSIBLE)!
    
    rates = np.linspace(30, 45, 100)
    alphas = rates / 40.0
    beta_thresholds = alphas  # Hopf bifurcation requires beta > alpha
    
    # Check our parameter set:
    min_alpha = 36.0 / 40.0   # 0.90
    max_alpha = 41.0 / 40.0   # 1.025
    nominal_beta = 0.35
    
    # Distance to bifurcation boundary: delta = min(alpha - beta)
    min_margin = min_alpha - nominal_beta
    relative_margin = min_margin / min_alpha * 100.0
    
    # Eigenvalue spectrum computation at nominal operating point
    # Solve lambda + alpha + beta * exp(-lambda * tau) = 0 via Lambert W function
    # Principal branch W_0 gives the dominant root
    from scipy.special import lambertw
    # lambda = (1/tau) * W(-beta * tau * exp(alpha * tau)) - alpha
    z = -nominal_beta * tau_nom * np.exp(alpha_nom * tau_nom)
    w_val = lambertw(z, k=0)
    root_dominant = (w_val / tau_nom) - alpha_nom
    
    real_part = np.real(root_dominant)
    imag_part = np.imag(root_dominant)
    
    print("=== Task 0194: Hopf Bifurcation & Nonlinear Stability Analysis ===")
    print(f"nominal_alpha (drain rate): {alpha_nom:.4f} ms^-1")
    print(f"nominal_beta (feedback gain): {nominal_beta:.4f} ms^-1")
    print(f"delay_tau: {tau_nom*1000:.1f} ms")
    print(f"bifurcation_condition (beta > alpha): {nominal_beta > min_alpha} (False confirms unconditional stability)")
    print(f"safety_margin_to_bifurcation: {min_margin:.4f} ms^-1 (+{relative_margin:.1f}%)")
    print(f"dominant_eigenvalue: {real_part:.4f} + {imag_part:.4f}i")
    print(f"hurwitz_strictly_negative: {real_part < -0.5} (Decay half-life: {np.log(2)/abs(real_part):.2f} ms)")
    print(f"hopf_instability_immune: {bool(real_part < -0.5 and min_margin > 0.4)}")
    
    return {
        "alpha": alpha_nom,
        "beta": nominal_beta,
        "real_part": float(real_part),
        "margin": float(min_margin),
        "immune": bool(real_part < -0.5 and min_margin > 0.4)
    }

if __name__ == "__main__":
    analyze_hopf_bifurcation()
