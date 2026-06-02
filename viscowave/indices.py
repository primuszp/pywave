# -*- coding: utf-8 -*-
"""
Deflection basin indices and structural condition indicators from FWD data.

These indices are widely used in pavement engineering for rapid structural
assessment without full backcalculation.  All functions operate on peak
deflections in millimetres at specified sensor offsets.

References:
  - AASHTO Guide for Design of Pavement Structures (1993)
  - Shahin, M.Y. (2005). Pavement Management for Airports, Roads, and Parking Lots.
  - Horak, E. (2008). Benchmarking Deflection Basin Parameters, TRB.

Typical usage::

    from viscowave.indices import DeflectionBasin

    basin = DeflectionBasin(
        deflections_mm=[0.800, 0.500, 0.350, 0.250, 0.180, 0.120],
        offsets_mm=[0, 200, 300, 450, 600, 900],
        load_kN=40.0,
        load_radius_mm=150.0,
    )
    print(basin.SCI)    # Surface Curvature Index (mm)
    print(basin.BDI)    # Base Damage Index (mm)
    print(basin.BCI)    # Base Curvature Index (mm)
    print(basin.AREA)   # Area under normalised deflection basin (mm)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np

__all__ = [
    "DeflectionBasin",
    "normalise_deflections",
    "compute_area",
    "compute_sci",
    "compute_bdi",
    "compute_bci",
    "compute_bci300",
    "compute_structural_number_fwd",
    "compute_subgrade_modulus",
]

# Standard FWD sensor offsets used for index definitions (mm)
_D0_OFFSET = 0
_D200_OFFSET = 200
_D300_OFFSET = 300
_D450_OFFSET = 450
_D600_OFFSET = 600
_D900_OFFSET = 900
_D1200_OFFSET = 1200


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------


@dataclass
class DeflectionBasin:
    """
    Compute standard deflection basin indices for a single FWD drop.

    Args:
        deflections_mm:   Peak surface deflections in mm (downward positive).
                          The array must correspond to ``offsets_mm`` entries.
        offsets_mm:       Radial sensor offsets from load centre in mm.
        load_kN:          Peak impact load in kN (default 40 kN ≈ standard FWD).
        load_radius_mm:   Load plate radius in mm (default 150 mm).
        normalise_load:   If True, scale deflections to a reference load of
                          ``reference_load_kN`` before computing indices.
        reference_load_kN: Reference load for normalisation (default 40 kN).

    All index properties raise ``ValueError`` if the required sensor offsets are
    not present in *offsets_mm*.

    Example::

        basin = DeflectionBasin(
            deflections_mm=[0.800, 0.500, 0.350, 0.250, 0.180, 0.120],
            offsets_mm=[0, 200, 300, 450, 600, 900],
            load_kN=40.0,
        )
        print(f"SCI = {basin.SCI:.3f} mm")
        print(f"BDI = {basin.BDI:.3f} mm")
        print(f"AREA = {basin.AREA:.1f} mm")
    """

    deflections_mm: np.ndarray
    offsets_mm: np.ndarray
    load_kN: float = 40.0
    load_radius_mm: float = 150.0
    normalise_load: bool = False
    reference_load_kN: float = 40.0

    def __post_init__(self) -> None:
        self.deflections_mm = np.asarray(self.deflections_mm, dtype=np.float64)
        self.offsets_mm = np.asarray(self.offsets_mm, dtype=np.float64)
        if self.deflections_mm.shape != self.offsets_mm.shape:
            raise ValueError(
                f"deflections_mm ({len(self.deflections_mm)}) and "
                f"offsets_mm ({len(self.offsets_mm)}) must have the same length."
            )
        if self.normalise_load and self.load_kN > 0:
            factor = self.reference_load_kN / self.load_kN
            self.deflections_mm = self.deflections_mm * factor

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_d(self, offset_mm: float) -> float:
        """Interpolate (or look up) deflection at given offset."""
        idx = np.argmin(np.abs(self.offsets_mm - offset_mm))
        tol = 30.0  # mm tolerance for offset matching
        if abs(self.offsets_mm[idx] - offset_mm) > tol:
            # Fall back to linear interpolation
            if offset_mm < self.offsets_mm[0] or offset_mm > self.offsets_mm[-1]:
                raise ValueError(
                    f"Offset {offset_mm} mm is outside the sensor range "
                    f"[{self.offsets_mm[0]:.0f}, {self.offsets_mm[-1]:.0f}] mm."
                )
            return float(np.interp(offset_mm, self.offsets_mm, self.deflections_mm))
        return float(self.deflections_mm[idx])

    @property
    def D0(self) -> float:
        """Deflection at load centre (offset = 0 mm) in mm."""
        return self._get_d(0)

    @property
    def D200(self) -> float:
        """Deflection at 200 mm offset in mm."""
        return self._get_d(200)

    @property
    def D300(self) -> float:
        """Deflection at 300 mm offset in mm."""
        return self._get_d(300)

    @property
    def D450(self) -> float:
        """Deflection at 450 mm offset in mm."""
        return self._get_d(450)

    @property
    def D600(self) -> float:
        """Deflection at 600 mm offset in mm."""
        return self._get_d(600)

    @property
    def D900(self) -> float:
        """Deflection at 900 mm offset in mm."""
        return self._get_d(900)

    @property
    def D1200(self) -> float:
        """Deflection at 1200 mm offset in mm."""
        return self._get_d(1200)

    # ------------------------------------------------------------------
    # Standard indices
    # ------------------------------------------------------------------

    @property
    def SCI(self) -> float:
        """
        Surface Curvature Index (mm).

        SCI = D0 - D300

        Sensitive to AC layer condition.  High values indicate surface distress.
        """
        return self.D0 - self.D300

    @property
    def BDI(self) -> float:
        """
        Base Damage Index (mm).

        BDI = D300 - D600

        Sensitive to base/subbase layer condition.
        """
        return self.D300 - self.D600

    @property
    def BCI(self) -> float:
        """
        Base Curvature Index (mm).

        BCI = D600 - D900

        Sensitive to upper subgrade condition.
        """
        return self.D600 - self.D900

    @property
    def BCI300(self) -> float:
        """
        Alternative BCI using 300–450 mm sensors (Horak, 2008).

        BCI300 = D300 - D450
        """
        return self.D300 - self.D450

    @property
    def AREA(self) -> float:
        """
        AREA index (mm) — area under the normalised deflection basin.

        The basin is normalised by D0, then the area under the curve from
        0 to 1800 mm is computed using the trapezoidal rule.  A larger AREA
        indicates a stiffer structural response.

        Returns:
            AREA in mm.
        """
        return compute_area(self.deflections_mm, self.offsets_mm)

    @property
    def subgrade_modulus_MPa(self) -> float:
        """
        Estimate subgrade resilient modulus (MPa) from the outer sensor deflection.

        Uses the Boussinesq half-space formula:

            E_sg = (1 - nu^2) * q * a * F / D_r

        where D_r is the deflection at a distance r far enough to be outside the
        influence of upper layers (typically 900-1200 mm), q is contact pressure,
        a is plate radius, and F is a dimensionless factor.

        A simplified two-parameter approximation is used here:
            E_sg ≈ 0.24 * P / (D_r * r)

        (Deflection at 900 mm offset, P in kN, r in m, D_r in mm → E in MPa)
        """
        return compute_subgrade_modulus(
            deflection_outer_mm=self.D900,
            load_kN=self.load_kN,
            offset_mm=900.0,
        )

    @property
    def structural_number(self) -> float:
        """
        Estimate AASHTO Structural Number (SN) from FWD deflections.

        Uses the empirical equation from AASHTO (1993):
            SN = a1*h1 + a2*m2*h2 + ...

        A simplified equation based on D0 and subgrade modulus is used here.
        For detailed SN back-calculation, use the full backcalculation module.
        """
        return compute_structural_number_fwd(
            D0_mm=self.D0,
            load_kN=self.load_kN,
            load_radius_mm=self.load_radius_mm,
            subgrade_modulus_MPa=self.subgrade_modulus_MPa,
        )

    def summary(self) -> dict:
        """Return all computed indices as a dictionary."""
        result = {
            "D0_mm": self.D0,
            "AREA_mm": self.AREA,
            "subgrade_modulus_MPa": self.subgrade_modulus_MPa,
            "SN_est": self.structural_number,
        }
        try:
            result["SCI_mm"] = self.SCI
        except ValueError:
            pass
        try:
            result["BDI_mm"] = self.BDI
        except ValueError:
            pass
        try:
            result["BCI_mm"] = self.BCI
        except ValueError:
            pass
        return result

    def __repr__(self) -> str:
        return (
            f"DeflectionBasin(D0={self.D0:.3f} mm, load={self.load_kN:.1f} kN, "
            f"sensors={len(self.offsets_mm)})"
        )


# ---------------------------------------------------------------------------
# Standalone functions (mirror of property calculations)
# ---------------------------------------------------------------------------


def normalise_deflections(
    deflections_mm: Sequence[float],
    measured_load_kN: float,
    reference_load_kN: float = 40.0,
) -> np.ndarray:
    """
    Scale deflections to a reference load using linear normalisation.

    Args:
        deflections_mm:     Measured peak deflections in mm.
        measured_load_kN:   Actual peak load applied in kN.
        reference_load_kN:  Reference load to normalise to (default 40 kN).

    Returns:
        Normalised deflection array in mm.

    Example::

        d_norm = normalise_deflections([0.75, 0.48, 0.33], measured_load_kN=42.0)
    """
    arr = np.asarray(deflections_mm, dtype=np.float64)
    if measured_load_kN <= 0:
        raise ValueError("measured_load_kN must be positive")
    return arr * (reference_load_kN / measured_load_kN)


def compute_area(
    deflections_mm: Sequence[float],
    offsets_mm: Sequence[float],
) -> float:
    """
    Compute the AREA index under the normalised deflection basin.

    The basin is normalised by D0 (deflection at offset=0) before integration,
    so AREA is independent of load magnitude.

    Args:
        deflections_mm: Peak deflections at each sensor in mm.
        offsets_mm:     Corresponding radial offsets in mm.

    Returns:
        AREA in mm.
    """
    d = np.asarray(deflections_mm, dtype=np.float64)
    r = np.asarray(offsets_mm, dtype=np.float64)

    sort_idx = np.argsort(r)
    r = r[sort_idx]
    d = d[sort_idx]

    d0 = d[0]
    if d0 == 0:
        return 0.0
    d_norm = d / d0
    trapezoid = getattr(np, "trapezoid", None)
    if trapezoid is None:  # pragma: no cover - compatibility with older NumPy
        trapezoid = np.trapz
    return float(trapezoid(d_norm, r))


def compute_sci(d0_mm: float, d300_mm: float) -> float:
    """Surface Curvature Index = D0 - D300 (mm)."""
    return d0_mm - d300_mm


def compute_bdi(d300_mm: float, d600_mm: float) -> float:
    """Base Damage Index = D300 - D600 (mm)."""
    return d300_mm - d600_mm


def compute_bci(d600_mm: float, d900_mm: float) -> float:
    """Base Curvature Index = D600 - D900 (mm)."""
    return d600_mm - d900_mm


def compute_bci300(d300_mm: float, d450_mm: float) -> float:
    """Alternative Base Curvature Index = D300 - D450 (mm)."""
    return d300_mm - d450_mm


def compute_subgrade_modulus(
    deflection_outer_mm: float,
    load_kN: float,
    offset_mm: float = 900.0,
    poisson: float = 0.45,
) -> float:
    """
    Estimate subgrade resilient modulus from an outer-sensor deflection.

    Applies the Boussinesq point-load approximation at distance *offset_mm*:

        E_sg = (1 + nu) * (1 - 2*nu) * P / (pi * r * w_r)

    where P is load, r is sensor offset, w_r is deflection.

    Args:
        deflection_outer_mm: Deflection at offset (mm).
        load_kN:             Peak load (kN).
        offset_mm:           Sensor offset from load centre (mm).
        poisson:             Subgrade Poisson's ratio (default 0.45).

    Returns:
        Subgrade modulus in MPa.
    """
    if deflection_outer_mm <= 0:
        return np.nan
    r_m = offset_mm / 1000.0
    w_m = deflection_outer_mm / 1000.0
    P_N = load_kN * 1000.0
    E_Pa = (1.0 + poisson) * (1.0 - 2.0 * poisson) * P_N / (np.pi * r_m * w_m)
    return float(E_Pa / 1e6)


def compute_structural_number_fwd(
    D0_mm: float,
    load_kN: float,
    load_radius_mm: float = 150.0,
    subgrade_modulus_MPa: float = 50.0,
) -> float:
    """
    Estimate AASHTO Structural Number (SN) from FWD centre deflection.

    Uses the AASHTO (1993) equation:

        D0 = 1.5 * p * a^2 / (E_sg * a * [1 + (a/Ds)^2]^0.5)

    Solved for the equivalent structural depth Ds, then:

        SN_est = Ds / 25.4 / 3.0  (empirical approximation)

    Args:
        D0_mm:               Centre deflection in mm.
        load_kN:             Peak load in kN.
        load_radius_mm:      Load plate radius in mm.
        subgrade_modulus_MPa: Subgrade modulus in MPa.

    Returns:
        Estimated Structural Number (dimensionless).
    """
    if D0_mm <= 0 or subgrade_modulus_MPa <= 0:
        return np.nan
    r_m = load_radius_mm / 1000.0
    w0_m = D0_mm / 1000.0
    P_N = load_kN * 1000.0
    E_sg_Pa = subgrade_modulus_MPa * 1e6
    # Contact pressure
    p_Pa = P_N / (np.pi * r_m ** 2)
    # Estimate structural stiffness depth
    # D0 = 1.5 * p * r / E_sg * correction -> solve for correction factor
    D0_elastic = 1.5 * p_Pa * r_m / E_sg_Pa  # half-space without structure
    if D0_elastic <= 0:
        return np.nan
    ratio = w0_m / D0_elastic
    if ratio <= 0:
        return np.nan
    # depth parameter (empirical)
    depth_m = r_m * (ratio ** -2 - 1.0) ** 0.25 if ratio < 1 else 0.0
    # Convert to SN via layer equivalence (3 in/layer = 1 SN unit is rough rule)
    sn = depth_m * 100.0 / 7.62  # 7.62 cm per SN unit (approximate)
    return float(max(sn, 0.0))
