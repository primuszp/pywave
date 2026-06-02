# ViscoWave Legacy API Reference (v1.0)

> ⚠️ **Note**: This is the legacy API documentation. For new projects, please use the [Modern API (v2.0)](MODERN_API_GUIDE.md) which is simpler and more user-friendly.

## Overview

The `viscowave` package provides a modern, production-ready Python interface to the ViscoWave pavement response analysis engine and Relaxation_Sig_to_Prony Prony series conversion tool.

This document describes the **legacy low-level API (v1.0)**. The legacy API is still fully supported and will continue to work, but the modern API offers significant advantages:

- ✨ 90% less code
- 🌍 Automatic unit handling
- ✅ Type-safe with full IDE support
- 🔗 Chainable/fluent builder pattern

**For new projects, see [MODERN_API_GUIDE.md](MODERN_API_GUIDE.md)**

**Version:** 1.0.0 (Legacy)

## Platform Support

✅ **Windows** - x64 (tested)
✅ **macOS** - Intel (x86_64) + Apple Silicon (ARM64) universal binary
✅ **Linux** - x64 (library support ready)

## Installation

```bash
pip install -e .
```

Or from the project root:

```bash
cd /path/to/pywave
pip install -e .
```

## Quick Start

```python
import numpy as np
from viscowave.api import ViscoWaveModel, convert_layer_parameters

# Define pavement layers
pavement = np.array([
    [0.0, 0.35, 140, 12.0, 0.1],      # Elastic modulus, Poisson, density, height, damping
    [15000, 0.40, 120, 12.0, 0.1],
], dtype=np.float64)

# Convert to internal units
pavement = convert_layer_parameters(pavement)

# Run analysis
model = ViscoWaveModel()
displacement = model.compute(...)
```

## API Reference

### High-Level Classes

#### `ViscoWaveModel`

Main class for pavement response analysis.

```python
from viscowave.api import ViscoWaveModel

model = ViscoWaveModel()
displacement = model.compute(
    sigmoid=sigmoid,          # np.ndarray, shape (N, 4) or flat
    pavement=pavement,        # np.ndarray, shape (M, 5)
    load_pressure=pressure,   # float (psf)
    load_radius=radius,       # float (ft)
    sensor_location=sensors,  # np.ndarray (ft)
    time=time,                # np.ndarray (seconds)
    timehistory=history,      # np.ndarray (load multiplier)
    dt=0.0002,                # float (seconds)
    num_ve_layer=1,           # int
)
```

**Returns:** `np.ndarray` of shape `(num_sensors, num_time)` containing displacement values.

**Raises:**
- `ViscoWaveInputError`: Invalid input parameters
- `ViscoWaveConfigError`: Incompatible configuration
- `ViscoWaveError`: Computational error from C++ library

#### `RelaxationPronyModel`

Converts relaxation sigmoid parameters to Prony series.

```python
from viscowave.api import RelaxationPronyModel

model = RelaxationPronyModel()
result = model.compute(sigmoid=sigmoid)

print(result.matrix)  # shape: (15, num_sigmoid+1)
print(result.num_prony_elements)  # 15
```

**Returns:** `PronyResult` dataclass with:
- `flat`: Flattened array
- `matrix`: 2D array of Prony coefficients
- `num_sigmoid`: Number of sigmoid sets
- `num_prony_elements`: Number of Prony elements (15)

### Helper Functions

#### `convert_layer_parameters(layerpara: np.ndarray) -> np.ndarray`

Convert pavement layer parameters to internal units.

```python
from viscowave.api import convert_layer_parameters

# Input: [G (psi), nu, rho (pcf), h (in), damping (%)]
pavement = np.array([
    [0.0, 0.35, 140, 12.0, 0.1],
    [15000, 0.40, 120, 12.0, 0.1],
], dtype=np.float64)

pavement_conv = convert_layer_parameters(pavement)
# Output: [G (psf), nu, rho (slugs/ft³), h (ft), damping (fraction)]
```

#### `convert_pressure_and_radius(pressure_psi: float, radius_in: float) -> tuple[float, float]`

Convert load pressure and radius to internal units.

```python
from viscowave.api import convert_pressure_and_radius

pressure, radius = convert_pressure_and_radius(80.0, 6.0)
# Returns: (11520.0 psf, 0.5 ft)
```

#### `update_sigmoidal_coefficients(sigmoid: np.ndarray, layerpara: np.ndarray) -> np.ndarray`

Update sigmoid coefficients for non-viscous layers.

```python
from viscowave.api import update_sigmoidal_coefficients

sigmoid = np.array([[3.123, 3.446, -0.128, 0.554]], dtype=np.float64)
sigmoid_updated = update_sigmoidal_coefficients(sigmoid, pavement)
```

#### `half_sine_values(start: float, end: float, amplitude: float, time: np.ndarray) -> np.ndarray`

Generate half-sine load history.

```python
from viscowave.api import half_sine_values

time = np.linspace(0, 0.06, 300, dtype=np.float64)
load = half_sine_values(start=0.005, end=0.03, amplitude=1.0, time=time)
```

### SI Unit Support (units module)

The `units` module provides conversion functions for working with SI (metric) units. The underlying library uses Imperial units internally (psi, ft, pcf), but you can use SI units (Pa, m, kg/m³) for input and output.

#### Available Conversion Functions

```python
from viscowave import units

# SI conversion functions
units.convert_layer_parameters_si(layerpara)      # [E (Pa), nu, rho (kg/m³), h (m), %] -> internal
units.convert_pressure_and_radius_si(pa, m)       # Pa, m -> psf, ft
units.convert_sensor_locations_si(locations_m)     # m -> ft
units.convert_displacement_to_si(displacement_ft)  # ft -> m
```

#### Conversion Constants

```python
from viscowave import units

# Pressure
units.PA_TO_PSF      # 0.020885  (Pascal to psf)
units.PA_TO_PSI      # 0.000145  (Pascal to psi)
units.PSI_TO_PA      # 6894.76   (psi to Pascal)

# Length
units.M_TO_FT        # 3.28084   (meter to feet)
units.M_TO_IN        # 39.3701   (meter to inches)
units.FT_TO_M        # 0.3048    (feet to meter)
units.IN_TO_M        # 0.0254    (inches to meter)

# Density
units.KG_M3_TO_SLUG_FT3    # 0.00194   (kg/m³ to slug/ft³)
units.KG_M3_TO_PCF         # 0.06243   (kg/m³ to pcf)
```

#### SI Units Example

```python
import numpy as np
from viscowave import units
from viscowave.api import ViscoWaveModel, update_sigmoidal_coefficients, half_sine_values

# Define pavement in SI units: [E (Pa), nu, rho (kg/m³), h (m), damping (%)]
pavement_si = np.array([
    [3e9, 0.35, 2400, 0.10, 0.1],      # AC: 3 GPa, 2400 kg/m³, 10 cm
    [103e6, 0.40, 2200, 0.30, 0.1],    # Base: 103 MPa, 2200 kg/m³, 30 cm
], dtype=np.float64)

# Sigmoid parameters
sigmoid = np.array([[3.123, 3.446, -0.128, 0.554]], dtype=np.float64)

# Convert to internal units
pavement = units.convert_layer_parameters_si(pavement_si)
sigmoid_conv = update_sigmoidal_coefficients(sigmoid, pavement)

# Load: 550 kPa pressure, 15 cm radius
pressure, radius = units.convert_pressure_and_radius_si(550e3, 0.15)

# Sensors at 0, 20, 50 cm from load center
sensors = units.convert_sensor_locations_si(np.array([0, 0.2, 0.5]))

# Time and load history
time = np.linspace(0, 0.06, 300, dtype=np.float64)
timehistory = half_sine_values(0.005, 0.03, 1.0, time)

# Run analysis
model = ViscoWaveModel()
displacement_ft = model.compute(
    sigmoid=sigmoid_conv,
    pavement=pavement,
    load_pressure=pressure,
    load_radius=radius,
    sensor_location=sensors,
    time=time,
    timehistory=timehistory,
    dt=0.0002,
    num_ve_layer=1,
)

# Convert output to SI units
displacement_m = units.convert_displacement_to_si(displacement_ft)
displacement_mm = displacement_m * 1000  # Convert to millimeters

print(f"Max displacement: {np.max(np.abs(displacement_mm)):.3f} mm")
```

### Utility Functions

#### `get_platform_info() -> dict[str, str]`

Get platform and library information.

```python
from viscowave import get_platform_info

info = get_platform_info()
print(info)
# {
#     'system': 'Darwin',
#     'architecture': 'x86_64',
#     'python_version': '3.9.6',
#     'library_status': 'loaded'
# }
```

## Exception Handling

### Exception Types

#### `ViscoWaveError`

Base exception for library computation errors.

```python
try:
    displacement = model.compute(...)
except ViscoWaveError as e:
    print(f"Error in {e.func}: code {e.code}")
```

#### `ViscoWaveLibraryNotFoundError`

Raised when native library cannot be loaded.

```python
try:
    from viscowave.api import ViscoWaveModel
except ViscoWaveLibraryNotFoundError as e:
    print(f"Library '{e.library_name}' not found")
    print(f"Platform: {e.platform}")
    print(f"Searched in: {e.search_paths}")
```

#### `ViscoWaveInputError`

Raised for invalid input parameters.

```python
try:
    pavement = convert_layer_parameters(np.array([1, 2, 3]))
except ViscoWaveInputError as e:
    print(f"Invalid input: {e}")
```

#### `ViscoWaveConfigError`

Raised for configuration errors.

```python
try:
    displacement = model.compute(num_ve_layer=2, sigmoid=single_sigmoid)
except ViscoWaveConfigError as e:
    print(f"Configuration error: {e}")
```

## Complete Example

```python
import numpy as np
from viscowave.api import (
    ViscoWaveModel,
    convert_layer_parameters,
    convert_pressure_and_radius,
    update_sigmoidal_coefficients,
    half_sine_values,
)

# Define pavement
pavement = np.array([
    [0.0, 0.35, 140, 12.0, 0.1],
    [15000, 0.40, 120, 12.0, 0.1],
    [10000, 0.45, 100, 122.2, 0.1],
], dtype=np.float64)

# Sigmoid parameters
sigmoid = np.array([[3.123, 3.446, -0.128, 0.554]], dtype=np.float64)

# Convert to internal units
pavement_conv = convert_layer_parameters(pavement)
sigmoid_conv = update_sigmoidal_coefficients(sigmoid, pavement_conv)
pressure, radius = convert_pressure_and_radius(80.0, 6.0)

# Sensor locations (inches -> feet)
sensor_location = np.array([0, 8, 12, 18, 24], dtype=np.float64) / 12

# Time and load history
time = np.linspace(0, 0.06, 300, dtype=np.float64)
timehistory = half_sine_values(0.005, 0.03, 1.0, time)

# Run analysis
model = ViscoWaveModel()
displacement = model.compute(
    sigmoid=sigmoid_conv,
    pavement=pavement_conv,
    load_pressure=pressure,
    load_radius=radius,
    sensor_location=sensor_location,
    time=time,
    timehistory=timehistory,
    dt=0.0002,
    num_ve_layer=1,
)

print(f"Displacement shape: {displacement.shape}")  # (5 sensors, 300 time steps)
print(f"Max displacement: {np.max(np.abs(displacement)):.6e} ft")
```

## Logging

The package uses Python's `logging` module. To enable logging:

```python
import logging

# Enable debug logging for viscowave
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('viscowave')
logger.setLevel(logging.DEBUG)

# Now library loading will log details
from viscowave.api import ViscoWaveModel
```

## Type Hints

The API is fully typed for IDE support:

```python
from viscowave.api import ViscoWaveModel
import numpy as np
from numpy.typing import NDArray

def analyze_pavement(
    pavement: NDArray[np.float64],
    load: float
) -> NDArray[np.float64]:
    model = ViscoWaveModel()
    displacement = model.compute(...)
    return displacement
```

## Thread Safety

The underlying C++ libraries are **not thread-safe**. For parallel processing:

```python
from multiprocessing import Pool
from viscowave.api import ViscoWaveModel

def run_analysis(params):
    # Each process gets its own library instance
    model = ViscoWaveModel()
    return model.compute(**params)

# Safe: each process has separate library instance
with Pool(4) as pool:
    results = pool.map(run_analysis, parameter_list)
```

## Performance Tips

1. **Pre-allocate arrays**: Use `np.zeros()` for large output arrays
2. **Use contiguous arrays**: Ensure `arr.flags['C_CONTIGUOUS']` is True
3. **Minimize conversions**: Convert units once, reuse arrays
4. **Batch processing**: Process multiple scenarios in sequence rather than reloading libraries

## Troubleshooting

### Library not found

```
ViscoWaveLibraryNotFoundError: Failed to load library 'ViscoWave' on Darwin x86_64
```

**Solutions:**
1. Check library files exist in `viscowave/` directory
2. Verify architecture matches (x86_64 vs ARM64)
3. On macOS, check library with: `lipo -info viscowave/ViscoWave.dylib`
4. On Linux, check dependencies: `ldd viscowave/ViscoWave.so`

### Import errors

```
ImportError: cannot import name 'ViscoWaveModel'
```

**Solutions:**
1. Ensure package is installed: `pip install -e .`
2. Check Python version >= 3.9
3. Verify NumPy is installed: `pip install numpy>=1.20`

## Support

- Documentation: [README.md](README.md)
- Examples: [viscowave_example.py](viscowave_example.py)
- Build guide: [csrc/docs/BUILD_MACOS.md](csrc/docs/BUILD_MACOS.md)

## Version History

**1.0.0** (2025-02-03)
- Production-ready API
- Full type hints
- Enhanced error handling
- Comprehensive logging
- Cross-platform support (Windows, macOS, Linux)
- Modern exception hierarchy
- Platform detection utilities
