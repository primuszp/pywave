# -*- coding: utf-8 -*-
"""
Preset configurations for common pavement analysis scenarios.

This module provides pre-configured builders for typical pavement
structures and loading conditions.
"""
from __future__ import annotations

from .builders import AnalysisBuilder
from .types import LoadConfig, UnitSystem

__all__ = [
    "Pavements",
    "Loads",
]


class Pavements:
    """
    Preset pavement configurations.

    These methods return pre-configured AnalysisBuilder objects
    for common pavement structures.
    """

    @staticmethod
    def flexible_3layer_si() -> AnalysisBuilder:
        """
        Standard 3-layer flexible pavement (SI units).

        Structure:
        - AC layer: 3 GPa, 10 cm thick
        - Base layer: 103 MPa, 30 cm thick
        - Subgrade: 69 MPa, 10 m thick (semi-infinite)

        Returns:
            Pre-configured AnalysisBuilder

        Example:
            >>> from viscowave.presets import Pavements
            >>> result = (
            ...     Pavements.flexible_3layer_si()
            ...     .set_load(pressure=550e3, radius=0.15)
            ...     .set_sensors(0, 0.2, 0.5, 1.0)
            ...     .run()
            ... )
        """
        return (
            AnalysisBuilder(unit_system="SI")
            .add_layer(modulus=3e9, poisson_ratio=0.35, density=2400, thickness=0.10)
            .add_layer(modulus=103e6, poisson_ratio=0.40, density=2200, thickness=0.30)
            .add_layer(modulus=69e6, poisson_ratio=0.45, density=1600, thickness=10.0)
        )

    @staticmethod
    def flexible_3layer_imperial() -> AnalysisBuilder:
        """
        Standard 3-layer flexible pavement (Imperial units).

        Structure:
        - AC layer: 15000 psi, 4 in thick
        - Base layer: 15000 psi, 12 in thick
        - Subgrade: 10000 psi, 400 in thick (semi-infinite)

        Returns:
            Pre-configured AnalysisBuilder

        Example:
            >>> result = (
            ...     Pavements.flexible_3layer_imperial()
            ...     .set_load(pressure=80, radius=6)
            ...     .set_sensors(0, 12, 24, 36)
            ...     .run()
            ... )
        """
        return (
            AnalysisBuilder(unit_system="Imperial")
            .add_layer(modulus=15000, poisson_ratio=0.35, density=150, thickness=4)
            .add_layer(modulus=15000, poisson_ratio=0.40, density=137, thickness=12)
            .add_layer(modulus=10000, poisson_ratio=0.45, density=100, thickness=400)
        )

    @staticmethod
    def rigid_pcc_si(pcc_thickness: float = 0.25) -> AnalysisBuilder:
        """
        Standard rigid PCC pavement (SI units).

        Structure:
        - PCC slab: 28 GPa, specified thickness (default: 25 cm)
        - Base: 200 MPa, 15 cm thick
        - Subgrade: 69 MPa, 10 m thick

        Args:
            pcc_thickness: PCC slab thickness in meters (default: 0.25)

        Returns:
            Pre-configured AnalysisBuilder

        Example:
            >>> result = (
            ...     Pavements.rigid_pcc_si(pcc_thickness=0.30)
            ...     .set_load(pressure=550e3, radius=0.15)
            ...     .set_sensors(0, 0.2, 0.5)
            ...     .run()
            ... )
        """
        return (
            AnalysisBuilder(unit_system="SI")
            .add_layer(modulus=28e9, poisson_ratio=0.15, density=2400, thickness=pcc_thickness)
            .add_layer(modulus=200e6, poisson_ratio=0.35, density=2200, thickness=0.15)
            .add_layer(modulus=69e6, poisson_ratio=0.45, density=1600, thickness=10.0)
        )

    @staticmethod
    def rigid_pcc_imperial(pcc_thickness: float = 10) -> AnalysisBuilder:
        """
        Standard rigid PCC pavement (Imperial units).

        Structure:
        - PCC slab: 4e6 psi, specified thickness (default: 10 in)
        - Base: 30000 psi, 6 in thick
        - Subgrade: 10000 psi, 400 in thick

        Args:
            pcc_thickness: PCC slab thickness in inches (default: 10)

        Returns:
            Pre-configured AnalysisBuilder

        Example:
            >>> result = (
            ...     Pavements.rigid_pcc_imperial(pcc_thickness=12)
            ...     .set_load(pressure=80, radius=6)
            ...     .set_sensors(0, 12, 24)
            ...     .run()
            ... )
        """
        return (
            AnalysisBuilder(unit_system="Imperial")
            .add_layer(modulus=4e6, poisson_ratio=0.15, density=150, thickness=pcc_thickness)
            .add_layer(modulus=30000, poisson_ratio=0.35, density=137, thickness=6)
            .add_layer(modulus=10000, poisson_ratio=0.45, density=100, thickness=400)
        )

    @staticmethod
    def thin_overlay_si(overlay_thickness: float = 0.05) -> AnalysisBuilder:
        """
        Thin asphalt overlay on existing pavement (SI units).

        Structure:
        - Overlay: 3 GPa, specified thickness (default: 5 cm)
        - Existing AC: 1.5 GPa, 8 cm thick (aged/weakened)
        - Base: 103 MPa, 30 cm thick
        - Subgrade: 69 MPa, 10 m thick

        Args:
            overlay_thickness: Overlay thickness in meters (default: 0.05)

        Returns:
            Pre-configured AnalysisBuilder

        Example:
            >>> result = (
            ...     Pavements.thin_overlay_si(overlay_thickness=0.04)
            ...     .set_load(pressure=550e3, radius=0.15)
            ...     .set_sensors(0, 0.2, 0.5)
            ...     .run()
            ... )
        """
        return (
            AnalysisBuilder(unit_system="SI")
            .add_layer(modulus=3e9, poisson_ratio=0.35, density=2400, thickness=overlay_thickness)
            .add_layer(modulus=1.5e9, poisson_ratio=0.35, density=2300, thickness=0.08)
            .add_layer(modulus=103e6, poisson_ratio=0.40, density=2200, thickness=0.30)
            .add_layer(modulus=69e6, poisson_ratio=0.45, density=1600, thickness=10.0)
        )

    @staticmethod
    def full_depth_asphalt_si(ac_thickness: float = 0.40) -> AnalysisBuilder:
        """
        Full-depth asphalt pavement (SI units).

        Structure:
        - AC layer: 3 GPa, specified thickness (default: 40 cm)
        - Subgrade: 69 MPa, 10 m thick

        Args:
            ac_thickness: AC layer thickness in meters (default: 0.40)

        Returns:
            Pre-configured AnalysisBuilder

        Example:
            >>> result = (
            ...     Pavements.full_depth_asphalt_si(ac_thickness=0.50)
            ...     .set_load(pressure=550e3, radius=0.15)
            ...     .set_sensors(0, 0.2, 0.5)
            ...     .run()
            ... )
        """
        return (
            AnalysisBuilder(unit_system="SI")
            .add_layer(modulus=3e9, poisson_ratio=0.35, density=2400, thickness=ac_thickness)
            .add_layer(modulus=69e6, poisson_ratio=0.45, density=1600, thickness=10.0)
        )


class Loads:
    """
    Preset loading configurations.

    These methods return LoadConfig objects for common loading scenarios.
    """

    @staticmethod
    def standard_truck_si() -> LoadConfig:
        """
        Standard truck tire load (SI units).

        Parameters:
        - Pressure: 550 kPa (80 psi equivalent)
        - Radius: 15 cm (6 inch equivalent)
        - Duration: 0.005 to 0.03 seconds (half-sine)

        Returns:
            LoadConfig object

        Example:
            >>> from viscowave.presets import Pavements, Loads
            >>> result = (
            ...     Pavements.flexible_3layer_si()
            ...     .set_load(**Loads.standard_truck_si().__dict__)
            ...     .set_sensors(0, 0.2, 0.5)
            ...     .run()
            ... )
        """
        return LoadConfig(
            pressure=550e3,  # 550 kPa
            radius=0.15,  # 15 cm
            unit_system="SI",
            start_time=0.005,
            end_time=0.03,
            amplitude=1.0,
        )

    @staticmethod
    def standard_truck_imperial() -> LoadConfig:
        """
        Standard truck tire load (Imperial units).

        Parameters:
        - Pressure: 80 psi
        - Radius: 6 inches
        - Duration: 0.005 to 0.03 seconds (half-sine)

        Returns:
            LoadConfig object
        """
        return LoadConfig(
            pressure=80,  # psi
            radius=6,  # inches
            unit_system="Imperial",
            start_time=0.005,
            end_time=0.03,
            amplitude=1.0,
        )

    @staticmethod
    def heavy_truck_si() -> LoadConfig:
        """
        Heavy truck tire load (SI units).

        Parameters:
        - Pressure: 700 kPa
        - Radius: 17 cm
        - Duration: 0.005 to 0.03 seconds

        Returns:
            LoadConfig object
        """
        return LoadConfig(
            pressure=700e3,  # 700 kPa
            radius=0.17,  # 17 cm
            unit_system="SI",
            start_time=0.005,
            end_time=0.03,
            amplitude=1.0,
        )

    @staticmethod
    def heavy_truck_imperial() -> LoadConfig:
        """
        Heavy truck tire load (Imperial units).

        Parameters:
        - Pressure: 100 psi
        - Radius: 6.7 inches

        Returns:
            LoadConfig object
        """
        return LoadConfig(
            pressure=100,  # psi
            radius=6.7,  # inches
            unit_system="Imperial",
            start_time=0.005,
            end_time=0.03,
            amplitude=1.0,
        )

    @staticmethod
    def aircraft_si() -> LoadConfig:
        """
        Aircraft tire load (SI units).

        Parameters:
        - Pressure: 1400 kPa (very high pressure)
        - Radius: 20 cm
        - Duration: 0.003 to 0.02 seconds (faster loading)

        Returns:
            LoadConfig object
        """
        return LoadConfig(
            pressure=1400e3,  # 1400 kPa
            radius=0.20,  # 20 cm
            unit_system="SI",
            start_time=0.003,
            end_time=0.02,
            amplitude=1.0,
        )

    @staticmethod
    def passenger_car_si() -> LoadConfig:
        """
        Passenger car tire load (SI units).

        Parameters:
        - Pressure: 220 kPa (32 psi equivalent)
        - Radius: 10 cm
        - Duration: 0.005 to 0.03 seconds

        Returns:
            LoadConfig object
        """
        return LoadConfig(
            pressure=220e3,  # 220 kPa
            radius=0.10,  # 10 cm
            unit_system="SI",
            start_time=0.005,
            end_time=0.03,
            amplitude=1.0,
        )
