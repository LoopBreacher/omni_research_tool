import numpy as np

OMEGA = 7.8243e21
M_REF = 61.5          # Solar masses - GW150914 reference
F0_REF = 255.0        # Hz
TAU0_REF = 4.5        # ms

def compute_omni_qnm_waveform(M_f=61.5, a_f=0.68, t_max_ms=60.0, dt_ms=0.05):
    """Fully dynamic: scales with both final mass and final spin."""
    # Mass scaling (inverse for frequency, linear for damping)
    f0 = F0_REF * (M_REF / M_f)
    tau0 = TAU0_REF * (M_f / M_REF)
    
    # Weak spin correction (higher spin → higher frequency, slower damping)
    spin_factor_f = 1.0 + 0.25 * a_f          # approximate (2,2) mode dependence
    spin_factor_tau = 1.0 - 0.35 * a_f        # higher spin rings longer
    f0 *= spin_factor_f
    tau0 *= spin_factor_tau
    
    t = np.arange(0, t_max_ms, dt_ms) / 1000.0
    h = np.zeros_like(t)
    
    modes = [
        {"amp": 1.00, "f_scale": 1.00, "tau_scale": 1.00},   # fundamental
        {"amp": 0.40, "f_scale": 1.12, "tau_scale": 0.42},
        {"amp": 0.25, "f_scale": 1.49, "tau_scale": 0.24},
        {"amp": 0.15, "f_scale": 1.25, "tau_scale": 0.24},
        {"amp": 0.08, "f_scale": 2.00, "tau_scale": 0.16},
    ]
    
    for mode in modes:
        fn = f0 * mode["f_scale"]
        taun = (tau0 * mode["tau_scale"]) / 1000.0
        amp = mode["amp"]
        envelope = amp * np.exp(-t / taun)
        oscillation = np.sin(2 * np.pi * fn * t)
        h += envelope * oscillation
    
    return t, h, f0, tau0   # also return scaled values for display in the app

def get_qnm_table(M_f=61.5, a_f=0.68):
    """Returns dynamic QNM table for the selected event."""
    f0 = F0_REF * (M_REF / M_f)
    tau0 = TAU0_REF * (M_f / M_REF)
    spin_factor_f = 1.0 + 0.25 * a_f
    spin_factor_tau = 1.0 - 0.35 * a_f
    f0 *= spin_factor_f
    tau0 *= spin_factor_tau
    return [
        {"mode": "(2,2,0)", "f_hz": round(f0, 1),         "tau_ms": round(tau0, 1),       "amp": 1.00},
        {"mode": "(2,2,1)", "f_hz": round(f0 * 1.12, 1),  "tau_ms": round(tau0 * 0.42, 1), "amp": 0.40},
        {"mode": "(3,3,0)", "f_hz": round(f0 * 1.49, 1),  "tau_ms": round(tau0 * 0.24, 1), "amp": 0.25},
        {"mode": "(2,2,2)", "f_hz": round(f0 * 1.25, 1),  "tau_ms": round(tau0 * 0.24, 1), "amp": 0.15},
        {"mode": "(4,4,0)", "f_hz": round(f0 * 2.00, 1),  "tau_ms": round(tau0 * 0.16, 1), "amp": 0.08},
    ]