# -*- coding: utf-8 -*-
"""
Dynamic modulus utilities for viscoelastic asphalt characterisation.

This module provides:

1. **Sigmoid (MEPDG) model** — compute |E*| at any temperature and frequency
   from the four Witczak sigmoid coefficients (δ, α, β, γ).

2. **Time–Temperature Superposition (TTS)** — WLF and Arrhenius shift factors
   to construct the dynamic modulus master curve.

3. **Prony series utilities** — connect to the ViscoWave relaxation solver
   for converting sigmoid parameters to Prony series.

These tools replicate the *Dynamic_Modulus_Calc* worksheet functionality of
the ViscoWave Excel template in pure Python.

References:
  - Witczak, M.W. & Fonseca, O.A. (1996). Revised Predictive Model for
    Dynamic (Complex) Modulus of Asphalt Mixtures. TRB.
  - Christensen, D.W., Pellinen, T. & Bonaquist, R.F. (2003). Hirsch Model.
  - AASHTO TP62 / MEPDG Level 1 material characterisation.

Typical usage::

    from viscowave.dynmod import SigmoidModel, wlf_shift_factor

    # Sigmoid parameters from MEPDG Level 1 testing
    model = SigmoidModel(delta=3.123, alpha=3.446, beta=-0.128, gamma=0.554)

    # Modulus at 20°C and 10 Hz
    E_star = model.modulus(temp_C=20.0, freq_Hz=10.0)
    print(f"|E*| = {E_star:.0f} MPa at 20°C, 10 Hz")

    # Master curve at reference temperature 20°C
    freqs = [0.1, 0.5, 1, 5, 10, 25]
    temps = [5, 20, 40]
    mc = model.master_curve(freqs, temps, Tref_C=20.0)
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import numpy as np

__all__ = [
    "SigmoidModel",
    "wlf_shift_factor",
    "arrhenius_shift_factor",
    "reduced_frequency",
    "master_curve_data",
]

# ---------------------------------------------------------------------------
# Shift factor functions
# ---------------------------------------------------------------------------


def wlf_shift_factor(
    T_C: float,
    Tref_C: float,
    C1: float = 19.0,
    C2: float = 92.0,
) -> float:
    """
    Williams–Landel–Ferry (WLF) time–temperature shift factor.

    log10(aT) = -C1 * (T - Tref) / (C2 + T - Tref)

    Default constants C1=19, C2=92 are typical for asphalt (Pellinen, 2001).

    Args:
        T_C:    Test temperature (°C).
        Tref_C: Reference temperature (°C).
        C1:     WLF constant (default 19.0).
        C2:     WLF constant (default 92.0).

    Returns:
        Log10 of the shift factor (dimensionless).

    Example::

        log_aT = wlf_shift_factor(T_C=40, Tref_C=20)
        aT = 10 ** log_aT   # < 1 at high temperature (shorter reduced time)
    """
    dT = T_C - Tref_C
    denom = C2 + dT
    if abs(denom) < 1e-12:
        raise ValueError(f"WLF denominator is zero at T={T_C}°C, Tref={Tref_C}°C, C2={C2}")
    return -C1 * dT / denom


def arrhenius_shift_factor(
    T_C: float,
    Tref_C: float,
    Ea_kJ_mol: float = 150.0,
) -> float:
    """
    Arrhenius time–temperature shift factor.

    log10(aT) = Ea / (R * ln(10)) * (1/T_K - 1/Tref_K)

    Args:
        T_C:         Test temperature (°C).
        Tref_C:      Reference temperature (°C).
        Ea_kJ_mol:   Activation energy (kJ/mol, default 150 typical for AC).

    Returns:
        Log10 of the shift factor.
    """
    R = 8.314e-3  # kJ/(mol·K)
    T_K = T_C + 273.15
    Tref_K = Tref_C + 273.15
    return (Ea_kJ_mol / (R * math.log(10))) * (1.0 / T_K - 1.0 / Tref_K)


def reduced_frequency(
    freq_Hz: float,
    log_shift_factor: float,
) -> float:
    """
    Compute reduced frequency from test frequency and shift factor.

    f_r = f * 10^(log_aT)

    Args:
        freq_Hz:          Test frequency (Hz).
        log_shift_factor: log10(aT) from a shift factor function.

    Returns:
        Reduced frequency (Hz).
    """
    return freq_Hz * (10.0 ** log_shift_factor)


# ---------------------------------------------------------------------------
# Sigmoid (Witczak MEPDG) model
# ---------------------------------------------------------------------------


@dataclass
class SigmoidModel:
    """
    MEPDG (Witczak) sigmoid model for dynamic modulus of asphalt mixtures.

    The model computes log10(|E*|) in MPa as::

        log10(|E*|) = delta + alpha / (1 + exp(beta - gamma * log10(f_r)))

    where f_r is the reduced frequency (Hz) at the reference temperature.

    For a *shifted* form used in ViscoWave, the model uses::

        log10(|E*|) = a0 + a1 / (1 + exp(a2 - a3 * log10(f_r)))

    The coefficients a0, a1, a2, a3 correspond to δ, α, β, γ respectively.

    Attributes:
        delta:  Lower asymptote of log(|E*|) (= a0 in ViscoWave notation).
        alpha:  Span of the sigmoid (= a1).
        beta:   Shape parameter (= a2, controls position of inflection).
        gamma:  Shape parameter (= a3, controls slope at inflection).
        Tref_C: Reference temperature for the master curve (°C, default 20).
        shift:  Shift factor model: 'WLF' (default) or 'Arrhenius'.
        wlf_C1: WLF constant C1 (default 19.0).
        wlf_C2: WLF constant C2 (default 92.0).
        Ea:     Activation energy for Arrhenius model (kJ/mol, default 150).

    Example::

        # Typical dense-graded AC parameters
        model = SigmoidModel(delta=3.123, alpha=3.446, beta=-0.128, gamma=0.554)
        E_MPa = model.modulus(temp_C=20, freq_Hz=10)
    """

    delta: float
    alpha: float
    beta: float
    gamma: float
    Tref_C: float = 20.0
    shift: str = "WLF"
    wlf_C1: float = 19.0
    wlf_C2: float = 92.0
    Ea: float = 150.0

    def log_shift_factor(self, T_C: float) -> float:
        """Compute log10(aT) for temperature T_C relative to reference."""
        if self.shift.upper() == "WLF":
            return wlf_shift_factor(T_C, self.Tref_C, self.wlf_C1, self.wlf_C2)
        elif self.shift.upper() == "ARRHENIUS":
            return arrhenius_shift_factor(T_C, self.Tref_C, self.Ea)
        else:
            raise ValueError(f"Unknown shift model: {self.shift!r}. Use 'WLF' or 'Arrhenius'.")

    def log_modulus(self, log_fr: float) -> float:
        """
        Compute log10(|E*| / MPa) from log10 of reduced frequency.

        Args:
            log_fr: log10 of reduced frequency in Hz.

        Returns:
            log10(|E*|) in MPa.
        """
        return self.delta + self.alpha / (1.0 + math.exp(self.beta - self.gamma * log_fr))

    def modulus(self, temp_C: float, freq_Hz: float) -> float:
        """
        Compute dynamic modulus |E*| in MPa at a given temperature and frequency.

        Args:
            temp_C:  Temperature (°C).
            freq_Hz: Loading frequency (Hz).

        Returns:
            |E*| in MPa.

        Example::

            E_MPa = model.modulus(temp_C=20, freq_Hz=10)
        """
        if freq_Hz <= 0:
            raise ValueError("freq_Hz must be positive")
        log_aT = self.log_shift_factor(temp_C)
        fr = reduced_frequency(freq_Hz, log_aT)
        return 10.0 ** self.log_modulus(math.log10(fr))

    def modulus_array(
        self,
        temps_C: Sequence[float],
        freqs_Hz: Sequence[float],
    ) -> np.ndarray:
        """
        Compute |E*| (MPa) for arrays of temperatures and frequencies.

        Args:
            temps_C:  Temperatures in °C (1D array).
            freqs_Hz: Frequencies in Hz (1D array, same length as temps_C).

        Returns:
            |E*| array in MPa, same shape as inputs.
        """
        T = np.asarray(temps_C, dtype=np.float64)
        f = np.asarray(freqs_Hz, dtype=np.float64)
        if T.shape != f.shape:
            raise ValueError("temps_C and freqs_Hz must have the same shape")
        return np.array(
            [self.modulus(t, fi) for t, fi in zip(T.ravel(), f.ravel())],
            dtype=np.float64,
        ).reshape(T.shape)

    def master_curve(
        self,
        freqs_Hz: Sequence[float],
        temps_C: Sequence[float],
        Tref_C: Optional[float] = None,
    ) -> "MasterCurveData":
        """
        Construct the dynamic modulus master curve.

        Returns a MasterCurveData object with reduced frequencies and moduli
        for all (temperature, frequency) combinations, shifted to Tref_C.

        Args:
            freqs_Hz: Test frequencies in Hz.
            temps_C:  Test temperatures in °C.
            Tref_C:   Reference temperature for the master curve.
                      If None, uses self.Tref_C.

        Returns:
            MasterCurveData

        Example::

            mc = model.master_curve(
                freqs_Hz=[0.1, 1, 10, 25],
                temps_C=[5, 20, 40],
                Tref_C=20.0,
            )
            import matplotlib.pyplot as plt
            plt.semilogx(mc.reduced_freqs_Hz, mc.moduli_MPa, 'o')
        """
        Tref = Tref_C if Tref_C is not None else self.Tref_C
        points_f: List[float] = []
        points_E: List[float] = []
        points_T: List[float] = []

        for T in temps_C:
            log_aT = wlf_shift_factor(T, Tref, self.wlf_C1, self.wlf_C2) if self.shift.upper() == "WLF" else \
                     arrhenius_shift_factor(T, Tref, self.Ea)
            for f in freqs_Hz:
                fr = reduced_frequency(f, log_aT)
                E = self.modulus(T, f)
                points_f.append(fr)
                points_E.append(E)
                points_T.append(T)

        return MasterCurveData(
            reduced_freqs_Hz=np.asarray(points_f),
            moduli_MPa=np.asarray(points_E),
            temperatures_C=np.asarray(points_T),
            Tref_C=Tref,
            model=self,
        )

    def to_viscowave_sigmoid(self) -> np.ndarray:
        """
        Return sigmoid parameters as a 1×4 array in ViscoWave convention [a0, a1, a2, a3].

        Returns:
            np.ndarray of shape (1, 4): [[delta, alpha, beta, gamma]]
        """
        return np.array([[self.delta, self.alpha, self.beta, self.gamma]], dtype=np.float64)

    @classmethod
    def from_viscowave_array(cls, arr: np.ndarray, **kwargs) -> "SigmoidModel":
        """
        Create SigmoidModel from a ViscoWave sigmoid array [a0, a1, a2, a3].

        Args:
            arr:     1D array of length 4 or 2D array of shape (1, 4).
            **kwargs: Additional keyword arguments passed to SigmoidModel.

        Returns:
            SigmoidModel
        """
        flat = np.asarray(arr, dtype=np.float64).ravel()
        if flat.size != 4:
            raise ValueError(f"Expected 4 sigmoid coefficients, got {flat.size}")
        return cls(delta=flat[0], alpha=flat[1], beta=flat[2], gamma=flat[3], **kwargs)

    def __repr__(self) -> str:
        return (
            f"SigmoidModel(δ={self.delta:.4f}, α={self.alpha:.4f}, "
            f"β={self.beta:.4f}, γ={self.gamma:.4f}, Tref={self.Tref_C}°C)"
        )


@dataclass
class MasterCurveData:
    """
    Container for dynamic modulus master curve data.

    Attributes:
        reduced_freqs_Hz: Reduced (shifted) frequencies at Tref.
        moduli_MPa:       Dynamic modulus |E*| values in MPa.
        temperatures_C:   Original temperatures for each data point.
        Tref_C:           Reference temperature for the master curve.
        model:            The SigmoidModel used to generate the curve.
    """

    reduced_freqs_Hz: np.ndarray
    moduli_MPa: np.ndarray

    temperatures_C: np.ndarray
    Tref_C: float
    model: SigmoidModel

    def sorted(self) -> "MasterCurveData":
        """Return a copy with data sorted by reduced frequency."""
        idx = np.argsort(self.reduced_freqs_Hz)
        return MasterCurveData(
            reduced_freqs_Hz=self.reduced_freqs_Hz[idx],
            moduli_MPa=self.moduli_MPa[idx],
            temperatures_C=self.temperatures_C[idx],
            Tref_C=self.Tref_C,
            model=self.model,
        )

    def __repr__(self) -> str:
        return (
            f"MasterCurveData({len(self.reduced_freqs_Hz)} points, "
            f"Tref={self.Tref_C}°C, "
            f"|E*| range=[{self.moduli_MPa.min():.0f}, {self.moduli_MPa.max():.0f}] MPa)"
        )


# ---------------------------------------------------------------------------
# Standalone helper
# ---------------------------------------------------------------------------


def master_curve_data(
    delta: float,
    alpha: float,
    beta: float,
    gamma: float,
    freqs_Hz: Sequence[float],
    temps_C: Sequence[float],
    Tref_C: float = 20.0,
    shift: str = "WLF",
) -> MasterCurveData:
    """
    Convenience function to compute a master curve without creating a SigmoidModel.

    Args:
        delta, alpha, beta, gamma: Sigmoid parameters.
        freqs_Hz:  Test frequencies in Hz.
        temps_C:   Test temperatures in °C.
        Tref_C:    Reference temperature for the master curve.
        shift:     Shift factor model ('WLF' or 'Arrhenius').

    Returns:
        MasterCurveData

    Example::

        mc = master_curve_data(3.123, 3.446, -0.128, 0.554,
                               freqs_Hz=[0.1, 1, 10, 25],
                               temps_C=[5, 20, 40])
    """
    model = SigmoidModel(
        delta=delta, alpha=alpha, beta=beta, gamma=gamma, Tref_C=Tref_C, shift=shift
    )
    return model.master_curve(freqs_Hz, temps_C, Tref_C)
