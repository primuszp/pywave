# -*- coding: utf-8 -*-
"""
Builder pattern and fluent API for viscowave package.

This module provides a modern, chainable API for building and running
pavement analysis with minimal boilerplate.
"""
from __future__ import annotations

from typing import List, Optional, Union, Any

import numpy as np
from numpy.typing import NDArray

from .types import (
    PavementLayer,
    LoadConfig,
    TimeConfig,
    SigmoidParams,
    UnitSystem,
    LengthUnit,
)
from .validation import (
    validate_layers,
    validate_load,
    validate_sensors,
    validate_time_config,
    validate_sigmoid,
    validate_analysis_consistency,
)
from . import units as unit_utils
from .api import (
    ViscoWaveModel,
    update_sigmoidal_coefficients,
    half_sine_values,
)

__all__ = [
    "AnalysisBuilder",
    "AnalysisResult",
]


class AnalysisResult:
    """
    Unit-aware result container for analysis output.

    This class wraps the displacement output and provides convenient
    methods for unit conversion and result access.

    Attributes:
        displacement: Displacement array of shape (num_sensors, num_time)
        unit_system: Unit system used in the analysis
        time: Time vector (seconds)
        sensor_locations: Sensor locations in original units

    Example:
        >>> result = builder.run()
        >>> print(f"Max: {result.max_displacement('mm'):.3f} mm")
        >>> disp_mm = result.get_displacement('mm')
    """

    def __init__(
        self,
        displacement: NDArray[np.float64],
        unit_system: UnitSystem,
        time: NDArray[np.float64],
        sensor_locations: NDArray[np.float64],
    ):
        """
        Initialize analysis result.

        Args:
            displacement: Displacement array (in feet, internal units)
            unit_system: Original unit system
            time: Time vector
            sensor_locations: Sensor locations in original units
        """
        self.displacement = displacement
        self.unit_system = unit_system
        self.time = time
        self.sensor_locations = sensor_locations

    def get_displacement(
        self, unit: Optional[LengthUnit | Any] = None
    ) -> NDArray[np.float64]:
        """
        Get displacement in specified units.

        Args:
            unit: Desired length unit. If None, uses default for unit_system.
                  Options: 'm', 'mm', 'cm', 'ft', 'in'

        Returns:
            Displacement array in specified units

        Example:
            >>> disp_m = result.get_displacement('m')
            >>> disp_mm = result.get_displacement('mm')
            >>> disp_in = result.get_displacement('in')
        """
        # Displacement is always in feet (internal units)
        return unit_utils.convert_displacement(self.displacement, unit, self.unit_system)

    def max_displacement(self, unit: Optional[LengthUnit] = None) -> float:
        """
        Get maximum absolute displacement.

        Args:
            unit: Desired length unit (default: m for SI, ft for Imperial)

        Returns:
            Maximum displacement magnitude

        Example:
            >>> max_mm = result.max_displacement('mm')
            >>> print(f"Max displacement: {max_mm:.3f} mm")
        """
        disp = self.get_displacement(unit)
        return float(np.max(np.abs(disp)))

    def min_displacement(self, unit: Optional[LengthUnit] = None) -> float:
        """
        Get minimum displacement (most negative).

        Args:
            unit: Desired length unit (default: m for SI, ft for Imperial)

        Returns:
            Minimum displacement value

        Example:
            >>> min_mm = result.min_displacement('mm')
        """
        disp = self.get_displacement(unit)
        return float(np.min(disp))

    def get_sensor_displacement(
        self, sensor_index: int, unit: Optional[LengthUnit] = None
    ) -> NDArray[np.float64]:
        """
        Get displacement time history for a specific sensor.

        Args:
            sensor_index: Sensor index (0-based)
            unit: Desired length unit

        Returns:
            1D array of displacement vs time

        Example:
            >>> sensor_0 = result.get_sensor_displacement(0, 'mm')
            >>> import matplotlib.pyplot as plt
            >>> plt.plot(result.time, sensor_0)
        """
        if sensor_index < 0 or sensor_index >= self.displacement.shape[0]:
            raise ValueError(
                f"Sensor index {sensor_index} out of range [0, {self.displacement.shape[0]})"
            )

        disp = self.get_displacement(unit)
        return disp[sensor_index, :]

    @property
    def num_sensors(self) -> int:
        """Number of sensors."""
        return self.displacement.shape[0]

    @property
    def num_time_steps(self) -> int:
        """Number of time steps."""
        return self.displacement.shape[1]

    def __repr__(self) -> str:
        """String representation."""
        unit = "m" if self.unit_system == "SI" else "ft"
        max_disp = self.max_displacement(unit)
        return (
            f"AnalysisResult(sensors={self.num_sensors}, "
            f"time_steps={self.num_time_steps}, "
            f"max_displacement={max_disp:.6e} {unit})"
        )


class AnalysisBuilder:
    """
    Fluent API builder for pavement analysis.

    This class provides a chainable interface for setting up and running
    viscoelastic pavement analysis with automatic unit handling.

    Example:
        >>> # SI units example
        >>> result = (
        ...     AnalysisBuilder(unit_system="SI")
        ...     .add_layer(modulus=3e9, poisson_ratio=0.35, density=2400, thickness=0.10)
        ...     .add_layer(modulus=103e6, poisson_ratio=0.40, density=2200, thickness=0.30)
        ...     .set_load(pressure=550e3, radius=0.15)
        ...     .set_sensors(0, 0.2, 0.5, 1.0)
        ...     .run()
        ... )
        >>> print(f"Max: {result.max_displacement('mm'):.3f} mm")

        >>> # Imperial units example
        >>> result = (
        ...     AnalysisBuilder(unit_system="Imperial")
        ...     .add_layer(modulus=15000, poisson_ratio=0.40, density=120, thickness=12)
        ...     .set_load(pressure=80, radius=6)
        ...     .set_sensors(0, 12, 24, 36)
        ...     .run()
        ... )
    """

    def __init__(self, unit_system: UnitSystem = "SI"):
        """
        Initialize analysis builder.

        Args:
            unit_system: Unit system to use ("SI" or "Imperial")
        """
        self.unit_system = unit_utils.normalize_unit_system(unit_system)
        self._layers: List[PavementLayer] = []
        self._load: Optional[LoadConfig] = None
        self._sensors: Optional[NDArray[np.float64]] = None
        self._time_config: TimeConfig = TimeConfig()
        self._sigmoid: Optional[Union[SigmoidParams, NDArray[np.float64]]] = None

    def add_layer(
        self,
        modulus: float,
        poisson_ratio: float,
        density: float,
        thickness: float,
        damping: float = 0.1,
        is_viscoelastic: bool = False,
    ) -> AnalysisBuilder:
        """
        Add a pavement layer (chainable).

        Args:
            modulus: Young's modulus (E)
                     SI: Pa (e.g., 3e9 for 3 GPa)
                     Imperial: psi (e.g., 15000)
            poisson_ratio: Poisson's ratio (dimensionless, 0-0.5)
            density: Material density
                     SI: kg/m³ (e.g., 2400)
                     Imperial: pcf (e.g., 120)
            thickness: Layer thickness
                       SI: meters (e.g., 0.10 for 10 cm)
                       Imperial: inches (e.g., 12)
            damping: Damping ratio in % (default: 0.1)
            is_viscoelastic: Whether this is a viscoelastic layer (default: False)

        Returns:
            Self for chaining

        Example:
            >>> builder = (
            ...     AnalysisBuilder("SI")
            ...     .add_layer(modulus=3e9, poisson_ratio=0.35, density=2400, thickness=0.10)
            ...     .add_layer(modulus=103e6, poisson_ratio=0.40, density=2200, thickness=0.30)
            ... )
        """
        modulus_val = unit_utils.coerce_modulus(modulus, self.unit_system)
        density_val = unit_utils.coerce_density(density, self.unit_system)
        thickness_val = unit_utils.coerce_length(thickness, self.unit_system)

        layer = PavementLayer(
            modulus=modulus_val,
            poisson_ratio=poisson_ratio,
            density=density_val,
            thickness=thickness_val,
            damping=damping,
            unit_system=self.unit_system,
            is_viscoelastic=is_viscoelastic,
        )
        self._layers.append(layer)
        return self

    def add_viscoelastic_layer(
        self,
        poisson_ratio: float,
        density: float,
        thickness: float,
        sigmoid: Union[SigmoidParams, List[float], NDArray[np.float64]],
        damping: float = 0.1,
    ) -> AnalysisBuilder:
        """
        Add a viscoelastic layer with sigmoid parameters (chainable).

        For viscoelastic layers, modulus is 0 and defined by sigmoid parameters.

        Args:
            poisson_ratio: Poisson's ratio
            density: Material density (kg/m³ for SI, pcf for Imperial)
            thickness: Layer thickness (m for SI, in for Imperial)
            sigmoid: Sigmoid parameters [a, b, c, d] or SigmoidParams object
            damping: Damping ratio in % (default: 0.1)

        Returns:
            Self for chaining

        Example:
            >>> builder = (
            ...     AnalysisBuilder("SI")
            ...     .add_viscoelastic_layer(
            ...         poisson_ratio=0.35,
            ...         density=2400,
            ...         thickness=0.10,
            ...         sigmoid=[3.123, 3.446, -0.128, 0.554]
            ...     )
            ... )
        """
        # Store sigmoid parameters
        if isinstance(sigmoid, SigmoidParams):
            sigmoid_array = sigmoid.to_array()
        else:
            sigmoid_array = np.asarray(sigmoid, dtype=np.float64)

        if self._sigmoid is None:
            self._sigmoid = sigmoid_array.reshape(1, 4)
        else:
            if isinstance(self._sigmoid, np.ndarray):
                self._sigmoid = np.vstack([self._sigmoid, sigmoid_array.reshape(1, 4)])

        # Add layer with modulus=0
        density_val = unit_utils.coerce_density(density, self.unit_system)
        thickness_val = unit_utils.coerce_length(thickness, self.unit_system)

        layer = PavementLayer(
            modulus=0.0,
            poisson_ratio=poisson_ratio,
            density=density_val,
            thickness=thickness_val,
            damping=damping,
            unit_system=self.unit_system,
            is_viscoelastic=True,
        )
        self._layers.append(layer)
        return self

    def set_load(
        self,
        pressure: float,
        radius: float,
        start_time: float = 0.005,
        end_time: float = 0.03,
        amplitude: float = 1.0,
    ) -> AnalysisBuilder:
        """
        Set load configuration (chainable).

        Args:
            pressure: Load pressure
                      SI: Pa (e.g., 550e3 for 550 kPa)
                      Imperial: psi (e.g., 80)
            radius: Load radius
                    SI: meters (e.g., 0.15)
                    Imperial: inches (e.g., 6)
            start_time: Load start time in seconds (default: 0.005)
            end_time: Load end time in seconds (default: 0.03)
            amplitude: Load amplitude multiplier (default: 1.0)

        Returns:
            Self for chaining

        Example:
            >>> builder.set_load(pressure=550e3, radius=0.15)
        """
        pressure_val = unit_utils.coerce_pressure(pressure, self.unit_system)
        radius_val = unit_utils.coerce_length(radius, self.unit_system)

        self._load = LoadConfig(
            pressure=pressure_val,
            radius=radius_val,
            unit_system=self.unit_system,
            start_time=start_time,
            end_time=end_time,
            amplitude=amplitude,
        )
        return self

    def set_sensors(self, *locations: float) -> AnalysisBuilder:
        """
        Set sensor locations (chainable).

        Args:
            *locations: Sensor locations from load center
                        SI: meters (e.g., 0, 0.2, 0.5, 1.0)
                        Imperial: inches (e.g., 0, 8, 12, 24)

        Returns:
            Self for chaining

        Example:
            >>> # SI: sensors at 0, 20, 50, 100 cm
            >>> builder.set_sensors(0, 0.2, 0.5, 1.0)
            >>> # Imperial: sensors at 0, 12, 24 inches
            >>> builder.set_sensors(0, 12, 24)
        """
        raw: Any
        if len(locations) == 1:
            first = locations[0]
            if isinstance(first, (list, tuple, np.ndarray)) or (
                unit_utils.is_quantity(first)
                and np.ndim(getattr(first, "magnitude", first)) > 0
            ):
                raw = first
            else:
                raw = list(locations)
        else:
            raw = list(locations)

        locations_arr = unit_utils.coerce_length_array(raw, self.unit_system)
        self._sensors = validate_sensors(locations_arr, self.unit_system)
        return self

    def set_time(
        self, duration: float = 0.06, steps: int = 300, dt: float | None = None
    ) -> AnalysisBuilder:
        """
        Set time configuration (chainable).

        Args:
            duration: Total analysis duration in seconds (default: 0.06)
            steps: Number of time steps (default: 300)
            dt: Time step for integration in seconds (optional; inferred from duration/steps if None)

        Returns:
            Self for chaining

        Example:
            >>> builder.set_time(duration=0.08, steps=400)
        """
        self._time_config = TimeConfig(duration=duration, steps=steps, dt=dt)
        return self

    def run(self) -> AnalysisResult:
        """
        Run the analysis and return results.

        Returns:
            AnalysisResult object with displacement data

        Raises:
            ValueError: If configuration is incomplete or invalid

        Example:
            >>> result = builder.run()
            >>> print(result.max_displacement('mm'))
        """
        # Validate configuration
        if not self._layers:
            raise ValueError("At least one layer is required. Use add_layer().")

        if self._load is None:
            raise ValueError("Load configuration is required. Use set_load().")

        if self._sensors is None:
            raise ValueError("Sensor locations are required. Use set_sensors().")

        validate_layers(self._layers)
        validate_load(self._load)
        validate_time_config(self._time_config)

        # Count viscoelastic layers
        num_ve_layer = sum(1 for layer in self._layers if layer.is_viscoelastic)

        # Handle sigmoid parameters
        if num_ve_layer > 0:
            if self._sigmoid is None:
                raise ValueError(
                    f"Sigmoid parameters required for {num_ve_layer} viscoelastic layers. "
                    f"Use add_viscoelastic_layer() instead of add_layer()."
                )
            sigmoid = validate_sigmoid(self._sigmoid)
            validate_analysis_consistency(self._layers, num_ve_layer, sigmoid)
        else:
            # No viscoelastic layers, create dummy sigmoid
            sigmoid = np.array([[0.0, 0.0, 0.0, 0.0]], dtype=np.float64)
            num_ve_layer = 0

        # Convert layers to array
        pavement = np.array([layer.to_array() for layer in self._layers], dtype=np.float64)

        # Convert to internal units
        pavement_conv = unit_utils.convert_layer_parameters(pavement, self.unit_system)
        pressure, radius = unit_utils.convert_pressure_and_radius(
            self._load.pressure, self._load.radius, self.unit_system
        )
        sensors_conv = unit_utils.convert_sensor_locations(self._sensors, self.unit_system)

        # Update sigmoid coefficients if needed
        if num_ve_layer > 0:
            sigmoid_conv = update_sigmoidal_coefficients(sigmoid, pavement_conv)
        else:
            sigmoid_conv = np.empty((0, 4), dtype=np.float64)

        # Generate time vector and load history
        time = self._time_config.get_time_vector()
        if self._time_config.dt is not None:
            dt_used = self._time_config.dt
        elif self._time_config.steps > 0:
            dt_used = self._time_config.duration / self._time_config.steps
        else:
            dt_used = 0.0002
        timehistory = half_sine_values(
            self._load.start_time,
            self._load.end_time,
            self._load.amplitude,
            time,
        )

        # Run analysis
        model = ViscoWaveModel()
        displacement = model.compute(
            sigmoid=sigmoid_conv,
            pavement=pavement_conv,
            load_pressure=pressure,
            load_radius=radius,
            sensor_location=sensors_conv,
            time=time,
            timehistory=timehistory,
            dt=dt_used,
            num_ve_layer=num_ve_layer,
        )

        # Return result
        return AnalysisResult(
            displacement=displacement,
            unit_system=self.unit_system,
            time=time,
            sensor_locations=self._sensors,
        )
