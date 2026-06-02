# -*- coding: utf-8 -*-
"""
viscowave – Python wrapper for ViscoWave and pavement FWD analysis tools.

Provides high-level Python interfaces to the ViscoWave dynamic Finite Layer
Method (FLM) engine, plus Python equivalents of the ViscoWave Excel analyses:
FWD data I/O, deflection basin indices, backcalculation, and dynamic modulus.

Platform Support:
    - Windows x64 (x86 via Win32 DLL)
    - macOS (Intel x86_64 + Apple Silicon ARM64 universal binary)
    - Linux source-build support

Quick start::

    from viscowave import AnalysisBuilder

    result = (
        AnalysisBuilder(unit_system="SI")
        .add_layer(modulus=3e9, poisson_ratio=0.35, density=2400, thickness=0.10)
        .add_layer(modulus=103e6, poisson_ratio=0.40, density=2200, thickness=0.30)
        .add_layer(modulus=69e6,  poisson_ratio=0.45, density=1600, thickness=10.0)
        .set_load(pressure=550e3, radius=0.15)
        .set_sensors(0, 0.2, 0.3, 0.45, 0.6, 0.9)
        .run()
    )
    print(f"Max deflection: {result.max_displacement('mm'):.3f} mm")

FWD data loading and indices::

    from viscowave.fwd_io import read_jils
    from viscowave.indices import DeflectionBasin

    ds = read_jils("survey.DAT")
    for drop in ds.representative_drops():
        basin = DeflectionBasin(drop.deflections_mm, drop.sensor_offsets_mm, drop.load_kN)
        print(basin.D0, basin.SCI, basin.BDI)

Backcalculation::

    from viscowave.backcalc import backcalculate, BackcalcLayer

    result = backcalculate(
        measured_deflections_mm=[0.80, 0.51, 0.35, 0.25, 0.18, 0.12],
        sensor_offsets_mm=[0, 200, 300, 450, 600, 900],
        layer_structure=[
            BackcalcLayer(3000, (500, 30000), poisson_ratio=0.35, thickness=0.10),
            BackcalcLayer(200,  (50, 2000),   poisson_ratio=0.40, thickness=0.30),
            BackcalcLayer(60,   (10, 500),    poisson_ratio=0.45),
        ],
        load_kN=40.0,
    )

For detailed API reference, see the docs/ directory.
"""

from __future__ import annotations

import logging
import platform
from typing import TYPE_CHECKING

# Exceptions
from .exceptions import ViscoWaveError, ViscoWaveLibraryNotFoundError

# Modern high-level API
from .builders import AnalysisBuilder, AnalysisResult
from .highlevel import (
    analyze,
    quick_analysis,
    analyze_flexible_pavement,
    analyze_rigid_pavement,
)

# Types
from .types import (
    PavementLayer,
    LoadConfig,
    TimeConfig,
    SigmoidParams,
    UnitSystem,
    LengthUnit,
    PressureUnit,
    DensityUnit,
)

# Units module
from . import units

# Presets module
from . import presets

# New analysis modules (Python equivalents of ViscoWave Excel analyses)
from . import fwd_io
from . import indices
from . import dynmod

if TYPE_CHECKING:
    pass

__version__ = "2.3.0"
__author__ = "H.S. Lee; pywave maintainers"
__all__ = [
    # Modern High-Level API (Recommended)
    "AnalysisBuilder",
    "AnalysisResult",
    "analyze",
    "quick_analysis",
    "analyze_flexible_pavement",
    "analyze_rigid_pavement",
    # Types
    "PavementLayer",
    "LoadConfig",
    "TimeConfig",
    "SigmoidParams",
    "UnitSystem",
    "LengthUnit",
    "PressureUnit",
    "DensityUnit",
    # Exceptions
    "ViscoWaveError",
    "ViscoWaveLibraryNotFoundError",
    # Modules
    "units",
    "presets",
    "fwd_io",
    "indices",
    "dynmod",
    # Metadata
    "__version__",
]

# Configure module-level logger
_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())


def get_platform_info() -> dict[str, str]:
    """
    Get information about the current platform and library availability.

    Returns:
        Dictionary containing platform information:
            - 'system': Operating system name
            - 'architecture': CPU architecture
            - 'python_version': Python version string
            - 'library_status': Status of library loading

    Example:
        >>> info = get_platform_info()
        >>> print(info['system'])
        'Darwin'
    """
    try:
        from ._lowlevel import _lib_vw, _lib_rel
        library_status = "loaded"
    except Exception as e:
        library_status = f"not loaded: {e}"

    return {
        "system": platform.system(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "library_status": library_status,
    }


# Log library loading status on import
_logger.debug(f"viscowave {__version__} loaded on {platform.system()} {platform.machine()}")
