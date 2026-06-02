# -*- coding: utf-8 -*-
"""
Type definitions and protocols for viscowave package.

This module provides type hints, protocols, and typed dictionaries
for improved IDE support and type checking.
"""
from __future__ import annotations

from typing import Literal, Protocol, TypedDict, Union
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from . import units as unit_utils
__all__ = [
    "UnitSystem",
    "LengthUnit",
    "PressureUnit",
    "DensityUnit",
    "PavementLayer",
    "LoadConfig",
    "TimeConfig",
    "SigmoidParams",
    "AnalysisParams",
]

# ============================================================================
# Unit Type Aliases
# ============================================================================

UnitSystem = Literal["SI", "Imperial"]
LengthUnit = Literal["m", "mm", "cm", "ft", "in"]
PressureUnit = Literal["Pa", "kPa", "MPa", "psi", "psf"]
DensityUnit = Literal["kg/m3", "pcf", "slug/ft3"]


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class PavementLayer:
    """
    Represents a single pavement layer with unit-aware properties.

    Attributes:
        modulus: Young's modulus (E)
        poisson_ratio: Poisson's ratio (dimensionless, typically 0.15-0.50)
        density: Material density
        thickness: Layer thickness
        damping: Damping ratio (%, typically 0.1-5.0)
        unit_system: Unit system for the layer parameters
        is_viscoelastic: Whether this layer is viscoelastic (default: False)

    Example:
        >>> # SI units
        >>> layer = PavementLayer(
        ...     modulus=3e9,      # 3 GPa
        ...     poisson_ratio=0.35,
        ...     density=2400,     # kg/m³
        ...     thickness=0.10,   # 10 cm
        ...     damping=0.1,      # 0.1%
        ...     unit_system="SI"
        ... )

        >>> # Imperial units
        >>> layer = PavementLayer(
        ...     modulus=15000,    # psi
        ...     poisson_ratio=0.40,
        ...     density=120,      # pcf
        ...     thickness=12,     # inches
        ...     damping=0.1,
        ...     unit_system="Imperial"
        ... )
    """

    modulus: float
    poisson_ratio: float
    density: float
    thickness: float
    damping: float = 0.1
    unit_system: UnitSystem = "SI"
    is_viscoelastic: bool = False

    def to_array(self) -> NDArray[np.float64]:
        """
        Convert to numpy array format expected by the API.

        Returns:
            Array of [E, nu, rho, h, damping]
        """
        return np.array([
            self.modulus,
            self.poisson_ratio,
            self.density,
            self.thickness,
            self.damping
        ], dtype=np.float64)

    def __post_init__(self):
        """Validate layer parameters."""
        self.unit_system = unit_utils.normalize_unit_system(self.unit_system)
        if self.modulus < 0:
            raise ValueError(f"Modulus must be non-negative, got {self.modulus}")
        if not 0 <= self.poisson_ratio <= 0.5:
            raise ValueError(f"Poisson's ratio must be between 0 and 0.5, got {self.poisson_ratio}")
        if self.density <= 0:
            raise ValueError(f"Density must be positive, got {self.density}")
        if self.thickness <= 0:
            raise ValueError(f"Thickness must be positive, got {self.thickness}")
        if self.damping < 0:
            raise ValueError(f"Damping must be non-negative, got {self.damping}")


@dataclass
class LoadConfig:
    """
    Load configuration for pavement analysis.

    Attributes:
        pressure: Load pressure
        radius: Load radius (circular load)
        unit_system: Unit system for pressure and radius
        start_time: Load start time (seconds)
        end_time: Load end time (seconds)
        amplitude: Load amplitude multiplier (default: 1.0)

    Example:
        >>> # SI units: 550 kPa tire pressure, 15 cm radius
        >>> load = LoadConfig(
        ...     pressure=550e3,  # Pa
        ...     radius=0.15,     # m
        ...     unit_system="SI"
        ... )

        >>> # Imperial units: 80 psi tire pressure, 6 inch radius
        >>> load = LoadConfig(
        ...     pressure=80,     # psi
        ...     radius=6,        # inches
        ...     unit_system="Imperial"
        ... )
    """

    pressure: float
    radius: float
    unit_system: UnitSystem = "SI"
    start_time: float = 0.005
    end_time: float = 0.03
    amplitude: float = 1.0

    def __post_init__(self):
        """Validate load parameters."""
        self.unit_system = unit_utils.normalize_unit_system(self.unit_system)
        if self.pressure <= 0:
            raise ValueError(f"Pressure must be positive, got {self.pressure}")
        if self.radius <= 0:
            raise ValueError(f"Radius must be positive, got {self.radius}")
        if self.start_time < 0:
            raise ValueError(f"Start time must be non-negative, got {self.start_time}")
        if self.end_time <= self.start_time:
            raise ValueError(f"End time must be greater than start time")
        if self.amplitude <= 0:
            raise ValueError(f"Amplitude must be positive, got {self.amplitude}")


@dataclass
class TimeConfig:
    """
    Time configuration for analysis.

    Attributes:
        duration: Total analysis duration (seconds)
        steps: Number of time steps
        dt: Time step size (seconds, for integration). If None, inferred from duration and steps.

    Example:
        >>> config = TimeConfig(duration=0.06, steps=300, dt=0.0002)
    """

    duration: float = 0.06
    steps: int = 300
    dt: float | None = None

    def get_time_vector(self) -> NDArray[np.float64]:
        """Generate time vector using dt-spaced points (0 to (steps-1)*dt)."""
        if self.steps == 1:
            return np.asarray([0.0], dtype=np.float64)
        dt = self.dt if self.dt is not None else (self.duration / self.steps)
        return np.arange(self.steps, dtype=np.float64) * dt

    def __post_init__(self):
        """Validate time parameters."""
        if self.duration <= 0:
            raise ValueError(f"Duration must be positive, got {self.duration}")
        if self.steps <= 0:
            raise ValueError(f"Steps must be positive, got {self.steps}")
        if self.dt is not None and self.dt <= 0:
            raise ValueError(f"dt must be positive, got {self.dt}")


@dataclass
class SigmoidParams:
    """
    Sigmoid parameters for viscoelastic materials.

    These parameters define the relaxation modulus curve using a sigmoid function.

    Attributes:
        a: Sigmoid parameter a
        b: Sigmoid parameter b
        c: Sigmoid parameter c
        d: Sigmoid parameter d

    Example:
        >>> # Typical asphalt concrete parameters
        >>> sigmoid = SigmoidParams(a=3.123, b=3.446, c=-0.128, d=0.554)
    """

    a: float
    b: float
    c: float
    d: float

    def to_array(self) -> NDArray[np.float64]:
        """Convert to numpy array [a, b, c, d]."""
        return np.array([self.a, self.b, self.c, self.d], dtype=np.float64)


# ============================================================================
# TypedDict for Flexible Params
# ============================================================================


class AnalysisParams(TypedDict, total=False):
    """
    Typed dictionary for analysis parameters.

    This provides type hints for dictionary-based parameter passing.
    """

    layers: list[PavementLayer]
    load: LoadConfig
    sensors: NDArray[np.float64]
    time_config: TimeConfig
    sigmoid: SigmoidParams | NDArray[np.float64]
    num_ve_layer: int
    unit_system: UnitSystem


# ============================================================================
# Protocols
# ============================================================================


class LayerProtocol(Protocol):
    """Protocol for layer-like objects."""

    modulus: float
    poisson_ratio: float
    density: float
    thickness: float
    damping: float

    def to_array(self) -> NDArray[np.float64]:
        """Convert to array representation."""
        ...


class ResultProtocol(Protocol):
    """Protocol for result objects."""

    displacement: NDArray[np.float64]
    unit_system: UnitSystem

    def max_displacement(self, unit: LengthUnit | None = None) -> float:
        """Get maximum displacement."""
        ...

    def get_displacement(self, unit: LengthUnit | None = None) -> NDArray[np.float64]:
        """Get displacement in specified units."""
        ...
