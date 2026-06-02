# -*- coding: utf-8 -*-
"""
Unit conversion utilities for viscowave package.

The underlying native libraries use Imperial internal units (psf, ft, slug/ft^3).
This module lets users work with SI or Imperial inputs and provides optional
pint.Quantity support for convenient unit handling.
"""
from __future__ import annotations

from typing import Any, Iterable, Tuple

import numpy as np

try:
    import pint  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pint = None

_HAS_PINT = pint is not None

if _HAS_PINT:
    ureg = pint.UnitRegistry()
    # Common aliases used in pavement engineering.
    try:
        ureg.define("pcf = pound / foot ** 3 = pcf")
    except Exception:
        pass
    try:
        ureg.define("psf = pound / foot ** 2 = psf")
    except Exception:
        pass
    Q_ = ureg.Quantity
else:  # pragma: no cover - optional dependency
    ureg = None
    Q_ = None

__all__ = [
    # Unit registry
    "ureg",
    "Q_",
    # Conversion constants
    "PA_TO_PSF",
    "PSF_TO_PA",
    "PA_TO_PSI",
    "PSI_TO_PA",
    "M_TO_FT",
    "FT_TO_M",
    "M_TO_IN",
    "IN_TO_M",
    "KG_M3_TO_SLUG_FT3",
    "SLUG_FT3_TO_KG_M3",
    "KG_M3_TO_PCF",
    "PCF_TO_KG_M3",
    # Normalization helpers
    "normalize_unit_system",
    "is_quantity",
    "coerce_length",
    "coerce_pressure",
    "coerce_density",
    "coerce_modulus",
    "coerce_length_array",
    # Conversion functions
    "convert_pressure_and_radius",
    "convert_layer_parameters",
    "convert_sensor_locations",
    "convert_displacement",
    # Backward-compatible SI/Imperial helpers
    "convert_pressure_and_radius_si",
    "convert_pressure_and_radius_imperial",
    "convert_layer_parameters_si",
    "convert_layer_parameters_imperial",
    "convert_sensor_locations_si",
    "convert_sensor_locations_imperial",
    "convert_displacement_to_si",
]

# =============================================================================
# Conversion Constants
# =============================================================================

# Pressure conversions
PA_TO_PSF = 0.020885434273  # Pascal to pounds per square foot
PSF_TO_PA = 47.88025898     # pounds per square foot to Pascal
PA_TO_PSI = 0.000145037738  # Pascal to pounds per square inch
PSI_TO_PA = 6894.757293168  # pounds per square inch to Pascal

# Length conversions
M_TO_FT = 3.280839895      # meter to feet
FT_TO_M = 0.3048           # feet to meter
M_TO_IN = 39.37007874      # meter to inches
IN_TO_M = 0.0254           # inches to meter

# Density conversions
KG_M3_TO_SLUG_FT3 = 0.00193788  # kg/m^3 to slug/ft^3
SLUG_FT3_TO_KG_M3 = 515.3788    # slug/ft^3 to kg/m^3
KG_M3_TO_PCF = 0.062427961      # kg/m^3 to pounds per cubic foot
PCF_TO_KG_M3 = 16.01846337      # pounds per cubic foot to kg/m^3


# =============================================================================
# Helpers
# =============================================================================


def normalize_unit_system(unit_system: str) -> str:
    """
    Normalize unit system string.

    Accepts: "SI", "Imperial", "metric", "us", "uscs" (case-insensitive).
    """
    if unit_system is None:
        return "SI"
    if not isinstance(unit_system, str):
        raise TypeError("unit_system must be a string")
    value = unit_system.strip().lower()
    if value in {"si", "metric", "mks"}:
        return "SI"
    if value in {"imperial", "us", "uscs", "english"}:
        return "Imperial"
    raise ValueError(f"Unknown unit_system: {unit_system}")


def is_quantity(value: Any) -> bool:
    """Return True if value is a pint.Quantity."""
    return _HAS_PINT and isinstance(value, pint.Quantity)


def is_unit(value: Any) -> bool:
    """Return True if value is a pint.Unit."""
    return _HAS_PINT and isinstance(value, pint.Unit)


def _require_pint() -> None:
    if not _HAS_PINT:
        raise ImportError("pint is required for Quantity inputs. Install with 'pip install pint'.")


def _coerce_value(value: Any, target_unit: str, name: str) -> float:
    if is_quantity(value):
        _require_pint()
        return float(value.to(target_unit).magnitude)
    if value is None or value == "":
        raise ValueError(f"{name} cannot be empty")
    return float(value)


def coerce_length(value: Any, unit_system: str) -> float:
    """Coerce length to canonical user units (m for SI, inch for Imperial)."""
    unit_system = normalize_unit_system(unit_system)
    target_unit = "m" if unit_system == "SI" else "inch"
    return _coerce_value(value, target_unit, "length")


def coerce_pressure(value: Any, unit_system: str) -> float:
    """Coerce pressure to canonical user units (Pa for SI, psi for Imperial)."""
    unit_system = normalize_unit_system(unit_system)
    target_unit = "Pa" if unit_system == "SI" else "psi"
    return _coerce_value(value, target_unit, "pressure")


def coerce_modulus(value: Any, unit_system: str) -> float:
    """Coerce modulus to canonical user units (Pa for SI, psi for Imperial)."""
    unit_system = normalize_unit_system(unit_system)
    target_unit = "Pa" if unit_system == "SI" else "psi"
    return _coerce_value(value, target_unit, "modulus")


def coerce_density(value: Any, unit_system: str) -> float:
    """Coerce density to canonical user units (kg/m^3 for SI, pcf for Imperial)."""
    unit_system = normalize_unit_system(unit_system)
    target_unit = "kg / meter ** 3" if unit_system == "SI" else "pcf"
    return _coerce_value(value, target_unit, "density")


def coerce_length_array(values: Any, unit_system: str) -> np.ndarray:
    """Coerce a list/array of lengths to canonical units."""
    unit_system = normalize_unit_system(unit_system)
    if is_quantity(values):
        target_unit = "m" if unit_system == "SI" else "inch"
        return np.asarray(values.to(target_unit).magnitude, dtype=np.float64)

    arr = np.asarray(values, dtype=object)
    if arr.dtype == object and arr.size > 0 and any(is_quantity(v) for v in arr.ravel()):
        target_unit = "m" if unit_system == "SI" else "inch"
        return np.asarray([_coerce_value(v, target_unit, "length") for v in arr.ravel()], dtype=np.float64)

    return np.asarray(values, dtype=np.float64)


# =============================================================================
# Conversion Functions (to internal units)
# =============================================================================


def convert_pressure_and_radius(
    pressure: float, radius: float, unit_system: str
) -> Tuple[float, float]:
    """
    Convert load pressure and radius from canonical user units to internal units.

    SI canonical: Pa, m -> psf, ft
    Imperial canonical: psi, inch -> psf, ft
    """
    unit_system = normalize_unit_system(unit_system)
    if unit_system == "SI":
        pressure_psf = pressure * PA_TO_PSF
        radius_ft = radius * M_TO_FT
    else:
        pressure_psf = pressure * 144.0
        radius_ft = radius / 12.0
    return pressure_psf, radius_ft


def convert_layer_parameters(layerpara: np.ndarray, unit_system: str) -> np.ndarray:
    """
    Convert pavement layer parameters to internal units.

    Input array shape: (N, 5) with columns [E, nu, rho, h, damping].
    SI canonical: E in Pa, rho in kg/m^3, h in m.
    Imperial canonical: E in psi, rho in pcf, h in inches.

    Output array: [G (psf), nu, rho (slug/ft^3), h (ft), damping (fraction)].
    """
    unit_system = normalize_unit_system(unit_system)
    layerpara = np.array(layerpara, dtype=np.float64, copy=True)

    if layerpara.ndim != 2 or layerpara.shape[1] != 5:
        raise ValueError(
            f"layerpara must have shape (N, 5), got {layerpara.shape}. "
            "Expected columns: [E, nu, rho, h, damping]"
        )

    # Column 0: E -> G, then to psf
    if unit_system == "SI":
        layerpara[:, 0] = (
            layerpara[:, 0] / (2.0 * (1.0 + layerpara[:, 1])) * PA_TO_PSF
        )
        # Column 2: rho kg/m^3 -> slug/ft^3
        layerpara[:, 2] = layerpara[:, 2] * KG_M3_TO_SLUG_FT3
        # Column 3: h m -> ft
        layerpara[:, 3] = layerpara[:, 3] * M_TO_FT
    else:
        # Imperial: psi -> psf
        layerpara[:, 0] = (
            layerpara[:, 0] / (2.0 * (1.0 + layerpara[:, 1])) * 144.0
        )
        # pcf -> slug/ft^3
        layerpara[:, 2] = layerpara[:, 2] / 32.2
        # inches -> ft
        layerpara[:, 3] = layerpara[:, 3] / 12.0

    # Column 4: damping (%) -> fraction
    layerpara[:, 4] = layerpara[:, 4] / 100.0

    return layerpara


def convert_sensor_locations(locations: np.ndarray, unit_system: str) -> np.ndarray:
    """Convert sensor locations to internal feet."""
    unit_system = normalize_unit_system(unit_system)
    locations = np.asarray(locations, dtype=np.float64)
    if unit_system == "SI":
        return locations * M_TO_FT
    return locations / 12.0


# =============================================================================
# Conversion Functions (from internal units)
# =============================================================================


def _pint_convert_length(values_ft: np.ndarray, unit: Any) -> np.ndarray:
    _require_pint()
    if isinstance(unit, str):
        target = ureg.Unit(unit)
    elif is_quantity(unit):
        target = unit.units
    else:
        target = unit
    q = values_ft * ureg.foot
    return np.asarray(q.to(target).magnitude, dtype=np.float64)


def convert_displacement(
    displacement_ft: np.ndarray,
    unit: Any | None,
    unit_system: str,
) -> np.ndarray:
    """
    Convert displacement from internal feet to requested units.

    If unit is None, defaults to meters for SI and feet for Imperial.
    """
    unit_system = normalize_unit_system(unit_system)
    if unit is None:
        unit = "m" if unit_system == "SI" else "ft"

    if _HAS_PINT and (isinstance(unit, str) or is_quantity(unit) or is_unit(unit)):
        return _pint_convert_length(displacement_ft, unit)

    # Fallback for common string units without pint
    if isinstance(unit, str):
        if unit == "m":
            return displacement_ft * FT_TO_M
        if unit == "mm":
            return displacement_ft * FT_TO_M * 1000.0
        if unit == "cm":
            return displacement_ft * FT_TO_M * 100.0
        if unit == "ft":
            return np.asarray(displacement_ft, dtype=np.float64)
        if unit == "in":
            return displacement_ft * 12.0

    raise ValueError(f"Unknown length unit: {unit}")


# =============================================================================
# Backward-compatible wrappers
# =============================================================================


def convert_pressure_and_radius_si(
    pressure_pa: float, radius_m: float
) -> Tuple[float, float]:
    return convert_pressure_and_radius(pressure_pa, radius_m, "SI")


def convert_pressure_and_radius_imperial(
    pressure_psi: float, radius_in: float
) -> Tuple[float, float]:
    return convert_pressure_and_radius(pressure_psi, radius_in, "Imperial")


def convert_layer_parameters_si(layerpara: np.ndarray) -> np.ndarray:
    return convert_layer_parameters(layerpara, "SI")


def convert_layer_parameters_imperial(layerpara: np.ndarray) -> np.ndarray:
    return convert_layer_parameters(layerpara, "Imperial")


def convert_sensor_locations_si(locations_m: np.ndarray) -> np.ndarray:
    return convert_sensor_locations(locations_m, "SI")


def convert_sensor_locations_imperial(locations_in: np.ndarray) -> np.ndarray:
    return convert_sensor_locations(locations_in, "Imperial")


def convert_displacement_to_si(displacement_ft: np.ndarray) -> np.ndarray:
    return displacement_ft * FT_TO_M
