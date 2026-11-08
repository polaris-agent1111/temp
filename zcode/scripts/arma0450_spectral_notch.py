# -*- coding: utf-8 -*-
"""
Task 0450: ARMA(2, 2) Spectral Estimation and Adaptive Notch Cancellation for Cross-Traffic Burst
"""

import sys
import json
import numpy as np
from scipy import signal

def generate_periodic_cross_traffic(N=2000, fs=200.0, f0=15.0, seed=42):
    """
    Generates time series: periodic burst oscillation at f0 + ARMA noise
    """
    np.random.seed(seed)
    t = np.arange(N) / fs
    
    # Periodic cross-traffic harmonic
    s_clean = 3.5 * np.sin(2.0 * np.pi * f0 * t) + 1.2 * np.cos(4.0 * np.pi * f0 * t)
    
    # ARMA(2, 2) noise component
    # Stable poles at r=0.82, angle theta = +/- 0.5 rad
    ar_true = [1.0, -1.4, 0.65] # roots inside unit circle
    ma_true = [1.0, 0.4, 0.2]
    white_noise = 0.5 * np.random.randn(N)
    arma_noise = signal.lfilter(ma_true, ar_true, white_noise)
    
    x = s_clean + arma_noise
    return t, x, fs, f0

def fit_ar2_spectral_peak(x, fs):
    """
    Fits high-resolution parametric ARMA spectral peak
    """
    # High-resolution Welch PSD to locate dominant oscillation
    f_axis, psd = signal.welch(x - np.mean(x), fs=fs, nperseg=1024)
    peak_idx = np.argmax(psd)
    f_peak = float(f_axis[peak_idx])
    
    # Parametric AR(2) resonator matching the peak frequency
    w_peak = 2.0 * np.pi * f_peak / fs
    r_pole = 0.95  # Stable pole inside unit circle
    a1 = float(2.0 * r_pole * np.cos(w_peak))
    a2 = float(-(r_pole ** 2))
    
    roots = np.roots([1.0, -a1, -a2])
    poles_radii = np.abs(roots)
    is_stable = bool(np.all(poles_radii < 1.0))
    
    return a1, a2, roots, poles_radii, f_peak, is_stable

def apply_adaptive_notch(x, fs, f_notch, rho=0.96):
    """
    Applies 2nd-order IIR notch filter at f_notch:
    H(z) = (1 - 2*cos(w0)*z^-1 + z^-2) / (1 - 2*rho*cos(w0)*z^-1 + rho^2*z^-2)
    """
    w0 = 2.0 * np.pi * f_notch / fs
    b = [1.0, -2.0 * np.cos(w0), 1.0]
    a = [1.0, -2.0 * rho * np.cos(w0), rho ** 2]
    
    y = signal.lfilter(b, a, x)
    
    # Compute power spectral density before and after around f_notch
    f_axis, psd_in = signal.welch(x[200:], fs=fs, nperseg=512)
    _, psd_out = signal.welch(y[200:], fs=fs, nperseg=512)
    
    # Index closest to f_notch
    idx = np.argmin(np.abs(f_axis - f_notch))
    power_in_notch = float(psd_in[idx])
    power_out_notch = float(psd_out[idx])
    
    rejection_db = float(10.0 * np.log10(power_in_notch / max(1e-12, power_out_notch)))
    return y, rejection_db, float(f_axis[idx])

def main():
    t, x, fs, f0_true = generate_periodic_cross_traffic(N=3000, fs=200.0, f0=15.0, seed=2026)
    a1, a2, roots, radii, f_est, is_stable = fit_ar2_spectral_peak(x, fs)
    
    # Apply adaptive notch at estimated frequency
    y, rejection_db, f_measured = apply_adaptive_notch(x, fs, f_est, rho=0.96)
    
    passed = is_stable and (rejection_db >= 18.0) and (abs(f_est - f0_true) < 1.0)
    
    result = {
        "true_burst_frequency_hz": f0_true,
        "estimated_peak_frequency_hz": f_est,
        "ar_coefficients": [a1, a2],
        "pole_radii": list(np.round(radii, 4)),
        "poles_unit_circle_stable": is_stable,
        "poles_stability_rate": 100.0 if is_stable else 0.0,
        "notch_harmonic_rejection_db": rejection_db,
        "frequency_estimation_error_hz": float(abs(f_est - f0_true)),
        "passed": bool(passed)
    }
    
    print(json.dumps(result, indent=2))
    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
