# -*- coding: utf-8 -*-
"""
High-level convenience functions for quick analysis.

This module provides simple, one-function interfaces for common
analysis scenarios without requiring builder setup.
"""
from __future__ import annotations

from typing import List, Tuple, Optional, Iterable, Any

import numpy as np
from .builders import AnalysisBuilder, AnalysisResult
from .types import UnitSystem, PavementLayer, SigmoidParams

__all__ = [
    "analyze",
    "quick_analysis",
    "analyze_flexible_pavement",
    "analyze_rigid_pavement",
]


def _is_sigmoid_like(value: Any) -> bool:
    if isinstance(value, SigmoidParams):
        return True
    if isinstance(value, (list, tuple, np.ndarray)):
        arr = np.asarray(value, dtype=np.float64)
        return arr.shape == (4,)
    return False


def _consume_sigmoid(sigmoid_iter: Optional[Iterable[Any]]) -> Any:
    if sigmoid_iter is None:
        raise ValueError("Sigmoid parameters required for viscoelastic layer.")
    try:
        return next(sigmoid_iter)
    except StopIteration:
        raise ValueError("Not enough sigmoid parameter sets for viscoelastic layers.")


def _add_layer_from_object(
    builder: AnalysisBuilder, layer: PavementLayer, sigmoid_iter: Optional[Iterable[Any]]
):
    is_ve = layer.is_viscoelastic or layer.modulus == 0
    if is_ve:
        sig = _consume_sigmoid(sigmoid_iter)
        builder.add_viscoelastic_layer(
            poisson_ratio=layer.poisson_ratio,
            density=layer.density,
            thickness=layer.thickness,
            sigmoid=sig,
            damping=layer.damping,
        )
    else:
        builder.add_layer(
            modulus=layer.modulus,
            poisson_ratio=layer.poisson_ratio,
            density=layer.density,
            thickness=layer.thickness,
            damping=layer.damping,
        )


def _add_layer_from_dict(
    builder: AnalysisBuilder, layer: dict, sigmoid_iter: Optional[Iterable[Any]]
):
    if "sigmoid" in layer:
        builder.add_viscoelastic_layer(
            poisson_ratio=layer["poisson_ratio"],
            density=layer["density"],
            thickness=layer["thickness"],
            sigmoid=layer["sigmoid"],
            damping=layer.get("damping", 0.1),
        )
    elif layer.get("is_viscoelastic") or layer.get("modulus", 0) == 0:
        sig = _consume_sigmoid(sigmoid_iter)
        builder.add_viscoelastic_layer(
            poisson_ratio=layer["poisson_ratio"],
            density=layer["density"],
            thickness=layer["thickness"],
            sigmoid=sig,
            damping=layer.get("damping", 0.1),
        )
    else:
        builder.add_layer(
            modulus=layer["modulus"],
            poisson_ratio=layer["poisson_ratio"],
            density=layer["density"],
            thickness=layer["thickness"],
            damping=layer.get("damping", 0.1),
        )


def _add_layer_from_sequence(
    builder: AnalysisBuilder, layer: tuple | list, sigmoid_iter: Optional[Iterable[Any]]
):
    seq = list(layer)
    if len(seq) < 4:
        raise ValueError("Layer tuple/list must have at least 4 elements.")

    if len(seq) in {5, 6} and _is_sigmoid_like(seq[-1]):
        # (..., damping?, sigmoid)
        damping = 0.1
        if len(seq) == 6:
            damping = float(seq[4])
        builder.add_viscoelastic_layer(
            poisson_ratio=seq[1],
            density=seq[2],
            thickness=seq[3],
            sigmoid=seq[-1],
            damping=damping,
        )
    else:
        # (E, nu, rho, h[, damping])
        damping = float(seq[4]) if len(seq) >= 5 else 0.1
        if float(seq[0]) == 0:
            sig = _consume_sigmoid(sigmoid_iter)
            builder.add_viscoelastic_layer(
                poisson_ratio=seq[1],
                density=seq[2],
                thickness=seq[3],
                sigmoid=sig,
                damping=damping,
            )
        else:
            builder.add_layer(
                modulus=seq[0],
                poisson_ratio=seq[1],
                density=seq[2],
                thickness=seq[3],
                damping=damping,
            )


def analyze(
    layers: Iterable[Any],
    load_pressure: Any,
    load_radius: Any,
    sensor_locations: Any,
    unit_system: UnitSystem = "SI",
    *,
    time_duration: float = 0.06,
    time_steps: int = 300,
    dt: float | None = None,
    load_start: float = 0.005,
    load_end: float = 0.03,
    load_amplitude: float = 1.0,
    sigmoid: Optional[Iterable[Any]] = None,
) -> AnalysisResult:
    """
    Minimal one-call analysis helper.

    Supports:
      - layers as PavementLayer objects
      - layers as tuples/lists: (E, nu, rho, h) or (E, nu, rho, h, damping)
      - viscoelastic layers via:
          * dict with 'sigmoid'
          * tuple where last element is sigmoid (len 5 or 6)
          * modulus == 0 with sigmoid provided via `sigmoid=` iterable
      - pint.Quantity inputs for units
    """
    builder = AnalysisBuilder(unit_system=unit_system)
    sigmoid_iter = iter(sigmoid) if sigmoid is not None else None

    for layer in layers:
        if isinstance(layer, PavementLayer):
            _add_layer_from_object(builder, layer, sigmoid_iter)
        elif isinstance(layer, dict):
            _add_layer_from_dict(builder, layer, sigmoid_iter)
        elif isinstance(layer, (list, tuple)):
            _add_layer_from_sequence(builder, layer, sigmoid_iter)
        else:
            raise TypeError(f"Unsupported layer type: {type(layer)}")

    builder.set_load(
        pressure=load_pressure,
        radius=load_radius,
        start_time=load_start,
        end_time=load_end,
        amplitude=load_amplitude,
    )
    builder.set_sensors(sensor_locations)
    builder.set_time(duration=time_duration, steps=time_steps, dt=dt)

    return builder.run()


def quick_analysis(
    layers: List[Tuple[float, float, float, float]],
    load_pressure: float,
    load_radius: float,
    sensor_locations: List[float],
    unit_system: UnitSystem = "SI",
    time_duration: float = 0.06,
    time_steps: int = 300,
) -> AnalysisResult:
    """
    Quick analysis with minimal parameters.

    This is the simplest way to run an analysis with default settings.

    Args:
        layers: List of layer tuples (modulus, poisson_ratio, density, thickness)
                For viscoelastic layers, use modulus=0
        load_pressure: Load pressure (Pa for SI, psi for Imperial)
        load_radius: Load radius (m for SI, in for Imperial)
        sensor_locations: List of sensor locations (m for SI, in for Imperial)
        unit_system: "SI" or "Imperial" (default: "SI")
        time_duration: Analysis duration in seconds (default: 0.06)
        time_steps: Number of time steps (default: 300)

    Returns:
        AnalysisResult object

    Example:
        >>> # SI units: 3 GPa AC layer, 103 MPa base
        >>> layers = [
        ...     (3e9, 0.35, 2400, 0.10),     # E, nu, rho, h
        ...     (103e6, 0.40, 2200, 0.30),
        ... ]
        >>> result = quick_analysis(
        ...     layers=layers,
        ...     load_pressure=550e3,  # 550 kPa
        ...     load_radius=0.15,     # 15 cm
        ...     sensor_locations=[0, 0.2, 0.5, 1.0],
        ...     unit_system="SI"
        ... )
        >>> print(f"Max: {result.max_displacement('mm'):.3f} mm")

        >>> # Imperial units
        >>> layers = [
        ...     (15000, 0.40, 120, 12),  # 15 ksi, 120 pcf, 12 in
        ...     (10000, 0.45, 100, 48),
        ... ]
        >>> result = quick_analysis(
        ...     layers=layers,
        ...     load_pressure=80,    # psi
        ...     load_radius=6,       # inches
        ...     sensor_locations=[0, 12, 24, 36],
        ...     unit_system="Imperial"
        ... )
    """
    return analyze(
        layers=layers,
        load_pressure=load_pressure,
        load_radius=load_radius,
        sensor_locations=sensor_locations,
        unit_system=unit_system,
        time_duration=time_duration,
        time_steps=time_steps,
    )


def analyze_flexible_pavement(
    ac_thickness: float,
    base_thickness: float,
    subgrade_modulus: float,
    load_pressure: float,
    load_radius: float,
    sensor_locations: Optional[List[float]] = None,
    unit_system: UnitSystem = "SI",
    ac_modulus: Optional[float] = None,
    base_modulus: Optional[float] = None,
) -> AnalysisResult:
    """
    Analyze a typical 3-layer flexible pavement structure.

    This function sets up a standard flexible pavement with:
    - Asphalt concrete (AC) surface layer
    - Aggregate base layer
    - Subgrade

    Default material properties are used unless specified.

    Args:
        ac_thickness: AC layer thickness (m for SI, in for Imperial)
        base_thickness: Base layer thickness (m for SI, in for Imperial)
        subgrade_modulus: Subgrade elastic modulus (Pa for SI, psi for Imperial)
        load_pressure: Load pressure (Pa for SI, psi for Imperial)
        load_radius: Load radius (m for SI, in for Imperial)
        sensor_locations: Sensor locations (default: [0, 0.2, 0.5, 1.0] m for SI)
        unit_system: "SI" or "Imperial" (default: "SI")
        ac_modulus: AC modulus (default: 3 GPa for SI, 15000 psi for Imperial)
        base_modulus: Base modulus (default: 103 MPa for SI, 15000 psi for Imperial)

    Returns:
        AnalysisResult object

    Example:
        >>> # SI units: 10 cm AC, 30 cm base, 69 MPa subgrade
        >>> result = analyze_flexible_pavement(
        ...     ac_thickness=0.10,
        ...     base_thickness=0.30,
        ...     subgrade_modulus=69e6,
        ...     load_pressure=550e3,
        ...     load_radius=0.15,
        ...     unit_system="SI"
        ... )
        >>> print(f"Max: {result.max_displacement('mm'):.3f} mm")

        >>> # Imperial units: 4 in AC, 12 in base, 10000 psi subgrade
        >>> result = analyze_flexible_pavement(
        ...     ac_thickness=4,
        ...     base_thickness=12,
        ...     subgrade_modulus=10000,
        ...     load_pressure=80,
        ...     load_radius=6,
        ...     unit_system="Imperial"
        ... )
    """
    # Default material properties
    if unit_system == "SI":
        # SI defaults
        ac_modulus = ac_modulus or 3e9  # 3 GPa
        base_modulus = base_modulus or 103e6  # 103 MPa
        ac_density = 2400  # kg/m³
        base_density = 2200  # kg/m³
        subgrade_density = 1600  # kg/m³
        subgrade_thickness = 10.0  # 10 m (semi-infinite approximation)
        default_sensors = [0, 0.2, 0.5, 1.0]  # meters
    else:
        # Imperial defaults
        ac_modulus = ac_modulus or 15000  # psi
        base_modulus = base_modulus or 15000  # psi
        ac_density = 150  # pcf
        base_density = 137  # pcf
        subgrade_density = 100  # pcf
        subgrade_thickness = 400  # inches (semi-infinite approximation)
        default_sensors = [0, 12, 24, 36]  # inches

    sensor_locations = sensor_locations or default_sensors

    layers = [
        (ac_modulus, 0.35, ac_density, ac_thickness),
        (base_modulus, 0.40, base_density, base_thickness),
        (subgrade_modulus, 0.45, subgrade_density, subgrade_thickness),
    ]

    return quick_analysis(
        layers=layers,
        load_pressure=load_pressure,
        load_radius=load_radius,
        sensor_locations=sensor_locations,
        unit_system=unit_system,
    )


def analyze_rigid_pavement(
    pcc_thickness: float,
    pcc_modulus: float,
    base_thickness: float,
    subgrade_modulus: float,
    load_pressure: float,
    load_radius: float,
    sensor_locations: Optional[List[float]] = None,
    unit_system: UnitSystem = "SI",
    base_modulus: Optional[float] = None,
) -> AnalysisResult:
    """
    Analyze a typical rigid pavement (concrete) structure.

    This function sets up a standard rigid pavement with:
    - Portland cement concrete (PCC) surface
    - Aggregate base or stabilized subbase
    - Subgrade

    Args:
        pcc_thickness: PCC slab thickness (m for SI, in for Imperial)
        pcc_modulus: PCC elastic modulus (Pa for SI, psi for Imperial)
        base_thickness: Base layer thickness (m for SI, in for Imperial)
        subgrade_modulus: Subgrade elastic modulus (Pa for SI, psi for Imperial)
        load_pressure: Load pressure (Pa for SI, psi for Imperial)
        load_radius: Load radius (m for SI, in for Imperial)
        sensor_locations: Sensor locations (default: [0, 0.2, 0.5, 1.0] m for SI)
        unit_system: "SI" or "Imperial" (default: "SI")
        base_modulus: Base modulus (default: 200 MPa for SI, 30000 psi for Imperial)

    Returns:
        AnalysisResult object

    Example:
        >>> # SI units: 25 cm PCC, 28 GPa modulus
        >>> result = analyze_rigid_pavement(
        ...     pcc_thickness=0.25,
        ...     pcc_modulus=28e9,
        ...     base_thickness=0.15,
        ...     subgrade_modulus=69e6,
        ...     load_pressure=550e3,
        ...     load_radius=0.15,
        ...     unit_system="SI"
        ... )

        >>> # Imperial units: 10 in PCC
        >>> result = analyze_rigid_pavement(
        ...     pcc_thickness=10,
        ...     pcc_modulus=4e6,
        ...     base_thickness=6,
        ...     subgrade_modulus=10000,
        ...     load_pressure=80,
        ...     load_radius=6,
        ...     unit_system="Imperial"
        ... )
    """
    # Default material properties
    if unit_system == "SI":
        # SI defaults
        base_modulus = base_modulus or 200e6  # 200 MPa
        pcc_density = 2400  # kg/m³
        base_density = 2200  # kg/m³
        subgrade_density = 1600  # kg/m³
        subgrade_thickness = 10.0  # 10 m
        default_sensors = [0, 0.2, 0.5, 1.0]  # meters
    else:
        # Imperial defaults
        base_modulus = base_modulus or 30000  # psi
        pcc_density = 150  # pcf
        base_density = 137  # pcf
        subgrade_density = 100  # pcf
        subgrade_thickness = 400  # inches
        default_sensors = [0, 12, 24, 36]  # inches

    sensor_locations = sensor_locations or default_sensors

    layers = [
        (pcc_modulus, 0.15, pcc_density, pcc_thickness),  # PCC: lower Poisson's ratio
        (base_modulus, 0.35, base_density, base_thickness),
        (subgrade_modulus, 0.45, subgrade_density, subgrade_thickness),
    ]

    return quick_analysis(
        layers=layers,
        load_pressure=load_pressure,
        load_radius=load_radius,
        sensor_locations=sensor_locations,
        unit_system=unit_system,
    )
