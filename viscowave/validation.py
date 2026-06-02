# -*- coding: utf-8 -*-
"""
Input validation utilities for viscowave package.

This module provides validation functions to ensure input parameters
are valid and within reasonable ranges.
"""
from __future__ import annotations

from typing import List, Union

import numpy as np
from numpy.typing import NDArray

from .types import PavementLayer, LoadConfig, TimeConfig

__all__ = [
    "validate_layers",
    "validate_load",
    "validate_sensors",
    "validate_time_config",
    "validate_sigmoid",
]


def validate_layers(layers: List[PavementLayer]) -> None:
    """
    Validate a list of pavement layers.

    Args:
        layers: List of PavementLayer objects

    Raises:
        ValueError: If layers are invalid

    Example:
        >>> from viscowave.types import PavementLayer
        >>> layers = [
        ...     PavementLayer(3e9, 0.35, 2400, 0.10, unit_system="SI"),
        ...     PavementLayer(103e6, 0.40, 2200, 0.30, unit_system="SI")
        ... ]
        >>> validate_layers(layers)  # OK
    """
    if not layers:
        raise ValueError("At least one layer is required")

    if len(layers) > 6:
        raise ValueError(
            f"Too many layers ({len(layers)}). ViscoWave supports a maximum of 6 layers."
        )

    # Check that all layers use the same unit system
    unit_systems = {layer.unit_system for layer in layers}
    if len(unit_systems) > 1:
        raise ValueError(
            f"All layers must use the same unit system. Found: {unit_systems}"
        )

    # Validate individual layers (already done in __post_init__, but double-check)
    for i, layer in enumerate(layers):
        if layer.modulus == 0 and not layer.is_viscoelastic:
            raise ValueError(f"Layer {i}: Zero modulus requires is_viscoelastic=True")

    # ViscoWave requires viscoelastic layers to precede elastic layers
    ve_seen = False
    elastic_seen = False
    for i, layer in enumerate(layers):
        if layer.is_viscoelastic or layer.modulus == 0:
            ve_seen = True
            if elastic_seen:
                raise ValueError(
                    f"Layer {i}: Viscoelastic layers must come before elastic layers. "
                    "ViscoWave requires all viscoelastic layers at the top of the stack."
                )
        else:
            elastic_seen = True

    # Check viscoelastic layer limit
    ve_count = sum(1 for layer in layers if layer.is_viscoelastic or layer.modulus == 0)
    if ve_count > 3:
        raise ValueError(
            f"Too many viscoelastic layers ({ve_count}). ViscoWave supports a maximum of 3."
        )


def validate_load(load: LoadConfig) -> None:
    """
    Validate load configuration.

    Args:
        load: LoadConfig object

    Raises:
        ValueError: If load configuration is invalid

    Example:
        >>> from viscowave.types import LoadConfig
        >>> load = LoadConfig(pressure=550e3, radius=0.15, unit_system="SI")
        >>> validate_load(load)  # OK
    """
    # Basic validation is done in LoadConfig.__post_init__
    # Add additional checks here if needed

    # Check for reasonable values (order of magnitude checks)
    if load.unit_system == "SI":
        # SI units: Pa, m
        if load.pressure > 10e6:  # 10 MPa is very high
            raise ValueError(
                f"Pressure seems too high: {load.pressure/1e6:.1f} MPa. "
                f"Did you mean kPa instead of Pa?"
            )
        if load.pressure < 1e3:  # Less than 1 kPa is very low
            raise ValueError(
                f"Pressure seems too low: {load.pressure:.1f} Pa. "
                f"Did you mean kPa or MPa?"
            )
        if load.radius > 1.0:  # More than 1 meter is unusual
            raise ValueError(
                f"Radius seems too large: {load.radius:.2f} m. "
                f"Did you mean cm or mm?"
            )
        if load.radius < 0.01:  # Less than 1 cm is very small
            raise ValueError(
                f"Radius seems too small: {load.radius*100:.2f} cm"
            )
    else:
        # Imperial units: psi, inches
        if load.pressure > 500:  # More than 500 psi is very high
            raise ValueError(f"Pressure seems too high: {load.pressure:.1f} psi")
        if load.pressure < 1:  # Less than 1 psi is very low
            raise ValueError(f"Pressure seems too low: {load.pressure:.1f} psi")
        if load.radius > 24:  # More than 24 inches is unusual
            raise ValueError(
                f"Radius seems too large: {load.radius:.1f} inches. "
                f"Did you mean feet?"
            )
        if load.radius < 0.1:  # Less than 0.1 inch is very small
            raise ValueError(f"Radius seems too small: {load.radius:.2f} inches")

    # Check time parameters
    if load.end_time > 10.0:
        raise ValueError(
            f"Load duration seems too long: {load.end_time:.2f} seconds. "
            f"Typical values are 0.01-0.1 seconds."
        )


def validate_sensors(
    sensors: Union[List[float], NDArray[np.float64]],
    unit_system: str = "SI"
) -> NDArray[np.float64]:
    """
    Validate and convert sensor locations to numpy array.

    Args:
        sensors: Sensor locations (list or array)
        unit_system: Unit system ("SI" or "Imperial")

    Returns:
        Validated sensor array

    Raises:
        ValueError: If sensors are invalid

    Example:
        >>> sensors = validate_sensors([0, 0.2, 0.5, 1.0], unit_system="SI")
        >>> print(sensors.shape)
        (4,)
    """
    from . import units as unit_utils

    unit_system = unit_utils.normalize_unit_system(unit_system)
    sensors = np.asarray(sensors, dtype=np.float64)

    if sensors.ndim != 1:
        raise ValueError(f"Sensors must be 1D array, got shape {sensors.shape}")

    if len(sensors) == 0:
        raise ValueError("At least one sensor is required")

    if len(sensors) > 9:
        raise ValueError(
            f"Too many sensors ({len(sensors)}). ViscoWave supports a maximum of 9 sensors."
        )

    if np.any(sensors < 0):
        raise ValueError("Sensor locations must be non-negative")

    # Check for reasonable values
    if unit_system == "SI":
        # SI units: meters
        if np.max(sensors) > 100:
            raise ValueError(
                f"Sensor location seems too far: {np.max(sensors):.1f} m. "
                f"Did you mean cm or mm?"
            )
    else:
        # Imperial units: feet or inches (depends on context)
        if np.max(sensors) > 1000:
            raise ValueError(
                f"Sensor location seems too far: {np.max(sensors):.1f}"
            )

    return sensors


def validate_time_config(config: TimeConfig) -> None:
    """
    Validate time configuration.

    Args:
        config: TimeConfig object

    Raises:
        ValueError: If time configuration is invalid

    Example:
        >>> from viscowave.types import TimeConfig
        >>> config = TimeConfig(duration=0.06, steps=300, dt=0.0002)
        >>> validate_time_config(config)  # OK
    """
    # Basic validation is done in TimeConfig.__post_init__

    if config.steps < 10:
        raise ValueError(f"Too few time steps ({config.steps}). Minimum is 10.")

    if config.steps > 100000:
        raise ValueError(
            f"Too many time steps ({config.steps}). Maximum is 100000. "
            f"This may cause memory issues."
        )

    # Check that dt is reasonable for the duration
    # TimeConfig.get_time_vector() uses dt = duration/steps
    if config.steps > 1:
        implied_dt = config.duration / config.steps
        if config.dt is not None and config.dt > implied_dt * 10:
            raise ValueError(
                f"Time step dt={config.dt:.6f} is too large for duration={config.duration} "
                f"and steps={config.steps}. Consider reducing dt or increasing steps."
            )


def validate_sigmoid(
    sigmoid: Union[NDArray[np.float64], List[List[float]]]
) -> NDArray[np.float64]:
    """
    Validate sigmoid parameters.

    Args:
        sigmoid: Sigmoid parameters as array or list

    Returns:
        Validated sigmoid array of shape (N, 4)

    Raises:
        ValueError: If sigmoid parameters are invalid

    Example:
        >>> sigmoid = validate_sigmoid([[3.123, 3.446, -0.128, 0.554]])
        >>> print(sigmoid.shape)
        (1, 4)
    """
    sigmoid = np.asarray(sigmoid, dtype=np.float64)

    # Accept both 1D and 2D arrays
    if sigmoid.ndim == 1:
        if sigmoid.size % 4 != 0:
            raise ValueError(
                f"Sigmoid array size must be multiple of 4, got {sigmoid.size}"
            )
        sigmoid = sigmoid.reshape(-1, 4)
    elif sigmoid.ndim == 2:
        if sigmoid.shape[1] != 4:
            raise ValueError(
                f"Sigmoid array must have 4 columns [a,b,c,d], got {sigmoid.shape[1]}"
            )
    else:
        raise ValueError(
            f"Sigmoid must be 1D or 2D array, got {sigmoid.ndim}D"
        )

    if sigmoid.shape[0] == 0:
        raise ValueError("At least one sigmoid set is required")

    if sigmoid.shape[0] > 100:
        raise ValueError(
            f"Too many sigmoid sets ({sigmoid.shape[0]}). Maximum is 100."
        )

    return sigmoid


def validate_analysis_consistency(
    layers: List[PavementLayer],
    num_ve_layer: int,
    sigmoid: NDArray[np.float64]
) -> None:
    """
    Validate consistency between layers, viscoelastic layers, and sigmoid parameters.

    Args:
        layers: List of pavement layers
        num_ve_layer: Number of viscoelastic layers
        sigmoid: Sigmoid parameters

    Raises:
        ValueError: If configuration is inconsistent

    Example:
        >>> from viscowave.types import PavementLayer
        >>> layers = [PavementLayer(0, 0.35, 2400, 0.10, unit_system="SI", is_viscoelastic=True)]
        >>> sigmoid = np.array([[3.123, 3.446, -0.128, 0.554]])
        >>> validate_analysis_consistency(layers, num_ve_layer=1, sigmoid=sigmoid)  # OK
    """
    # Count viscoelastic layers
    ve_count = sum(1 for layer in layers if layer.is_viscoelastic or layer.modulus == 0)

    if ve_count != num_ve_layer:
        raise ValueError(
            f"Number of viscoelastic layers in layer list ({ve_count}) "
            f"does not match num_ve_layer ({num_ve_layer})"
        )

    # Check sigmoid count matches
    sigmoid_count = sigmoid.shape[0] if sigmoid.ndim == 2 else sigmoid.size // 4

    if sigmoid_count != num_ve_layer:
        raise ValueError(
            f"Number of sigmoid sets ({sigmoid_count}) "
            f"must match num_ve_layer ({num_ve_layer})"
        )
