"""هسته محاسباتی شبیه‌سازی خط انتقال"""
import numpy as np


def reflection_coefficient(ZL, Z0):
    denom = ZL + Z0
    if abs(denom) < 1e-12:
        return -1.0 + 0j
    return (ZL - Z0) / denom


def vswr(Gamma):
    g = abs(Gamma)
    if g >= 0.9999:
        return float('inf')
    return (1 + g) / (1 - g)


def input_impedance(Z0, ZL, beta_l):
    tl = np.tan(beta_l)
    denom = Z0 + 1j * ZL * tl
    if abs(denom) < 1e-12:
        return 1e12 + 0j
    return Z0 * (ZL + 1j * Z0 * tl) / denom


def standing_wave_pattern(Z0, ZL, length, freq, vp, n_points=600):
    lam = vp / freq
    beta = 2 * np.pi / lam
    z = np.linspace(0, length, n_points)
    GL = reflection_coefficient(ZL, Z0)
    V = np.exp(-1j * beta * z) + GL * np.exp(-1j * beta * (2 * length - z))
    I = (np.exp(-1j * beta * z) - GL * np.exp(-1j * beta * (2 * length - z))) / Z0
    return z, V, I, lam


def bounce_simulate(Z0, ZL, Zs, Vs, length, vp,
                    n_reflections=20, n_frames=200, n_z=300):
    GL = reflection_coefficient(ZL, Z0)
    GS = reflection_coefficient(Zs, Z0)
    Vplus = Vs * Z0 / (Zs + Z0) if abs(Zs + Z0) > 1e-12 else Vs / 2

    T = length / vp
    t_max = n_reflections * 2 * T
    t_arr = np.linspace(0, t_max, n_frames)
    z_arr = np.linspace(0, length, n_z)
    V_t = np.zeros((n_frames, n_z))
    I_t = np.zeros((n_frames, n_z))

    for i, t in enumerate(t_arr):
        vfwd = np.zeros(n_z)
        vbwd = np.zeros(n_z)
        for k in range(n_reflections):
            ak = Vplus * (GS * GL) ** k
            bk = Vplus * GL * (GS * GL) ** k
            tfwd = z_arr / vp + 2 * k * T
            tbwd = (2 * length - z_arr) / vp + 2 * k * T
            vfwd += ak * (t >= tfwd)
            vbwd += bk * (t >= tbwd)
        V_t[i] = vfwd + vbwd
        I_t[i] = (vfwd - vbwd) / Z0

    return z_arr, t_arr, V_t, I_t, GL, GS