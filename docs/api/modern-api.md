# ViscoWave 2.0 Modern API Guide

## Overview

ViscoWave 2.0 introduces a completely redesigned API focused on ease of use, type safety, and automatic unit handling. The new API is fully backward compatible with the legacy API.

**Version:** 2.0.0

## What's New in 2.0

✨ **Modern Features:**
- **Fluent/Chainable API** - Clean, readable builder pattern
- **Automatic Unit Handling** - SI and Imperial units with seamless conversion (pint Quantity compatible)
- **Type-Safe Configuration** - Full type hints and dataclasses
- **Preset Configurations** - Common pavement structures ready to use
- **Smart Result Access** - Easy unit conversion on results
- **Quick Analysis Functions** - One-line analysis for simple cases
- **Enhanced Validation** - Better error messages and input checking
- **100% Backward Compatible** - Legacy API still available

## Quick Start

### Installation

```bash
pip install -e .
```

### Your First Analysis (Modern API)

```python
from viscowave import AnalysisBuilder

# Fluent API with automatic unit handling
result = (
    AnalysisBuilder(unit_system="SI")
    .add_layer(modulus=3e9, poisson_ratio=0.35, density=2400, thickness=0.10)
    .add_layer(modulus=103e6, poisson_ratio=0.40, density=2200, thickness=0.30)
    .set_load(pressure=550e3, radius=0.15)  # 550 kPa, 15 cm
    .set_sensors(0, 0.2, 0.5, 1.0)  # meters
    .run()
)

print(f"Max displacement: {result.max_displacement('mm'):.3f} mm")
```

### Using `pint.Quantity` for Units

```python
from viscowave import AnalysisBuilder, units

ureg = units.ureg

result = (
    AnalysisBuilder(unit_system="SI")
    .add_layer(modulus=3 * ureg.GPa, poisson_ratio=0.35, density=2400 * ureg.kg / ureg.m**3, thickness=0.10 * ureg.m)
    .add_layer(modulus=103 * ureg.MPa, poisson_ratio=0.40, density=2200 * ureg.kg / ureg.m**3, thickness=0.30 * ureg.m)
    .set_load(pressure=550 * ureg.kPa, radius=0.15 * ureg.m)
    .set_sensors(0 * ureg.m, 0.2 * ureg.m, 0.5 * ureg.m, 1.0 * ureg.m)
    .run()
)
```

Compare this to the legacy API - much simpler!

## API Levels

ViscoWave 2.0 provides three levels of API to suit different needs:

1. **Quick Functions** - One-line analysis for simple cases
2. **Fluent Builder** - Chainable API for custom configurations
3. **Preset Configs** - Pre-configured common scenarios
4. **Legacy API** - Original low-level API (still available)

## 1. Quick Functions

For simple analyses, use the minimal one-call interface:

### `analyze()`

```python
from viscowave import analyze

# Define layers as simple tuples: (E, nu, rho, h)
layers = [
    (3e9, 0.35, 2400, 0.10),     # AC: 3 GPa, 10 cm
    (103e6, 0.40, 2200, 0.30),   # Base: 103 MPa, 30 cm
]

result = analyze(
    layers=layers,
    load_pressure=550e3,         # 550 kPa
    load_radius=0.15,            # 15 cm
    sensor_locations=[0, 0.2, 0.5, 1.0],
    unit_system="SI"
)

print(f"Max: {result.max_displacement('mm'):.3f} mm")
```

> Note: `quick_analysis()` remains available as a compatibility alias, but `analyze()` is the recommended minimal API.

### `analyze_flexible_pavement()`

```python
from viscowave import analyze_flexible_pavement

# Quick flexible pavement analysis
result = analyze_flexible_pavement(
    ac_thickness=0.10,           # 10 cm
    base_thickness=0.30,         # 30 cm
    subgrade_modulus=69e6,       # 69 MPa
    load_pressure=550e3,         # 550 kPa
    load_radius=0.15,            # 15 cm
    unit_system="SI"
)
```

### `analyze_rigid_pavement()`

```python
from viscowave import analyze_rigid_pavement

# Quick rigid pavement analysis
result = analyze_rigid_pavement(
    pcc_thickness=0.25,          # 25 cm
    pcc_modulus=28e9,            # 28 GPa
    base_thickness=0.15,         # 15 cm
    subgrade_modulus=69e6,       # 69 MPa
    load_pressure=550e3,
    load_radius=0.15,
    unit_system="SI"
)
```

## 2. Fluent Builder API

For full control with clean syntax:

### AnalysisBuilder

```python
from viscowave import AnalysisBuilder

# SI Units
builder = AnalysisBuilder(unit_system="SI")

# Add layers (chainable)
builder.add_layer(
    modulus=3e9,           # Pa (3 GPa)
    poisson_ratio=0.35,
    density=2400,          # kg/m³
    thickness=0.10,        # meters (10 cm)
    damping=0.1            # percent
)

# Or chain everything
result = (
    AnalysisBuilder(unit_system="SI")
    .add_layer(modulus=3e9, poisson_ratio=0.35, density=2400, thickness=0.10)
    .add_layer(modulus=103e6, poisson_ratio=0.40, density=2200, thickness=0.30)
    .add_layer(modulus=69e6, poisson_ratio=0.45, density=1600, thickness=10.0)
    .set_load(pressure=550e3, radius=0.15)
    .set_sensors(0, 0.2, 0.5, 1.0, 1.5)
    .set_time(duration=0.06, steps=300, dt=0.0002)
    .run()
)
```

### Imperial Units

```python
# Imperial units - just change unit_system parameter
result = (
    AnalysisBuilder(unit_system="Imperial")
    .add_layer(modulus=15000, poisson_ratio=0.40, density=120, thickness=12)
    .add_layer(modulus=10000, poisson_ratio=0.45, density=100, thickness=48)
    .set_load(pressure=80, radius=6)  # psi, inches
    .set_sensors(0, 12, 24, 36)       # inches
    .run()
)
```

### Viscoelastic Layers

```python
result = (
    AnalysisBuilder(unit_system="SI")
    .add_viscoelastic_layer(
        poisson_ratio=0.35,
        density=2400,
        thickness=0.10,
        sigmoid=[3.123, 3.446, -0.128, 0.554]
    )
    .add_layer(modulus=103e6, poisson_ratio=0.40, density=2200, thickness=0.30)
    .set_load(pressure=550e3, radius=0.15)
    .set_sensors(0, 0.2, 0.5)
    .run()
)
```

## 3. Preset Configurations

Pre-configured common scenarios:

### Pavement Presets

```python
from viscowave.presets import Pavements

# Standard flexible pavement (SI)
result = (
    Pavements.flexible_3layer_si()
    .set_load(pressure=550e3, radius=0.15)
    .set_sensors(0, 0.2, 0.5, 1.0)
    .run()
)

# Rigid PCC pavement (SI)
result = (
    Pavements.rigid_pcc_si(pcc_thickness=0.25)
    .set_load(pressure=550e3, radius=0.15)
    .set_sensors(0, 0.2, 0.5)
    .run()
)

# Full-depth asphalt
result = (
    Pavements.full_depth_asphalt_si(ac_thickness=0.40)
    .set_load(pressure=550e3, radius=0.15)
    .set_sensors(0, 0.2, 0.5)
    .run()
)

# Thin overlay
result = (
    Pavements.thin_overlay_si(overlay_thickness=0.05)
    .set_load(pressure=550e3, radius=0.15)
    .set_sensors(0, 0.2, 0.5)
    .run()
)
```

### Load Presets

```python
from viscowave.presets import Loads

# Standard truck load
load_config = Loads.standard_truck_si()
# pressure=550 kPa, radius=15 cm

# Heavy truck
load_config = Loads.heavy_truck_si()
# pressure=700 kPa, radius=17 cm

# Aircraft
load_config = Loads.aircraft_si()
# pressure=1400 kPa, radius=20 cm

# Passenger car
load_config = Loads.passenger_car_si()
# pressure=220 kPa, radius=10 cm
```

## Result Access

The `AnalysisResult` class provides convenient methods:

```python
# Run analysis
result = builder.run()

# Access properties
print(result.num_sensors)      # Number of sensors
print(result.num_time_steps)   # Number of time steps
print(result.time)             # Time vector

# Get displacement in any unit
disp_m = result.get_displacement('m')    # meters
disp_mm = result.get_displacement('mm')  # millimeters
disp_ft = result.get_displacement('ft')  # feet
disp_in = result.get_displacement('in')  # inches

# Get maximum displacement
max_mm = result.max_displacement('mm')
max_in = result.max_displacement('in')

# Get minimum displacement
min_mm = result.min_displacement('mm')

# Get specific sensor data
sensor_0 = result.get_sensor_displacement(0, unit='mm')

# Plot
import matplotlib.pyplot as plt
plt.plot(result.time * 1000, sensor_0)
plt.xlabel('Time (ms)')
plt.ylabel('Displacement (mm)')
plt.show()
```

## Type Hints

Full type safety with modern Python:

```python
from viscowave import AnalysisBuilder, AnalysisResult, PavementLayer, LoadConfig

def run_analysis() -> AnalysisResult:
    """Type-safe analysis function."""
    result: AnalysisResult = (
        AnalysisBuilder(unit_system="SI")
        .add_layer(modulus=3e9, poisson_ratio=0.35, density=2400, thickness=0.10)
        .set_load(pressure=550e3, radius=0.15)
        .set_sensors(0, 0.2, 0.5)
        .run()
    )
    return result
```

## Unit Systems

### SI Units (Default)

- **Pressure**: Pa (Pascal)
  - Typical: 550e3 Pa = 550 kPa = 0.55 MPa
- **Length**: m (meters)
  - Typical: 0.10 m = 10 cm
- **Density**: kg/m³
  - AC: ~2400 kg/m³
  - Base: ~2200 kg/m³
- **Modulus**: Pa
  - AC: 2-4 GPa = 2e9-4e9 Pa
  - Base: 50-200 MPa = 50e6-200e6 Pa

### Imperial Units

- **Pressure**: psi (pounds per square inch)
  - Typical: 80 psi
- **Length**: inches
  - Typical: 12 inches
- **Density**: pcf (pounds per cubic foot)
  - AC: ~150 pcf
  - Base: ~120-140 pcf
- **Modulus**: psi
  - AC: 10000-20000 psi
  - Base: 10000-25000 psi

## Examples

See the [examples/](examples/) directory:

- `modern_api_demo.py` - Comprehensive demo of all modern API features
- `viscowave_si_units.py` - SI units example
- `viscowave_basic.py` - Legacy API example

## Comparison: Old vs New

### Old API (Still Works!)

```python
import numpy as np
from viscowave import units
from viscowave.api import ViscoWaveModel, convert_layer_parameters

# Define pavement
pavement_si = np.array([[3e9, 0.35, 2400, 0.10, 0.1]])
pavement = units.convert_layer_parameters_si(pavement_si)

# Convert load
pressure, radius = units.convert_pressure_and_radius_si(550e3, 0.15)

# Convert sensors
sensors = units.convert_sensor_locations_si(np.array([0, 0.2, 0.5]))

# Time setup
time = np.linspace(0, 0.06, 300, dtype=np.float64)

# ... more boilerplate ...

# Run
model = ViscoWaveModel()
displacement_ft = model.compute(...)

# Convert results
displacement_m = units.convert_displacement_to_si(displacement_ft)
```

### New API (Much Simpler!)

```python
from viscowave import AnalysisBuilder

result = (
    AnalysisBuilder(unit_system="SI")
    .add_layer(modulus=3e9, poisson_ratio=0.35, density=2400, thickness=0.10)
    .set_load(pressure=550e3, radius=0.15)
    .set_sensors(0, 0.2, 0.5)
    .run()
)

max_mm = result.max_displacement('mm')
```

## Migration Guide

### If you're using the old API:

1. **No changes required** - Old API still works
2. **Gradual migration** - Update code module by module
3. **New features** - Use modern API for new code

### Simple Migration:

```python
# OLD
import numpy as np
from viscowave import units
from viscowave.api import ViscoWaveModel

pavement_si = np.array([[3e9, 0.35, 2400, 0.10, 0.1]])
pavement = units.convert_layer_parameters_si(pavement_si)
# ... lots more code ...

# NEW
from viscowave import AnalysisBuilder

result = (
    AnalysisBuilder(unit_system="SI")
    .add_layer(modulus=3e9, poisson_ratio=0.35, density=2400, thickness=0.10)
    # ... cleaner code ...
)
```

## Error Handling

Better error messages in 2.0:

```python
try:
    result = (
        AnalysisBuilder(unit_system="SI")
        .add_layer(modulus=-1000, poisson_ratio=0.35, density=2400, thickness=0.10)
        .run()
    )
except ValueError as e:
    print(e)  # "Modulus must be non-negative, got -1000"
```

## Performance

The modern API has the same performance as the legacy API - it's just a better interface to the same underlying C++ libraries.

## Support

- Documentation: This guide + [LEGACY_API.md](LEGACY_API.md) for legacy API
- Examples: [examples/](examples/) directory
- Issues: Report bugs and feature requests on the project repository

## Summary

**Modern API Benefits:**

✅ **90% less boilerplate** - Simple, clean code
✅ **Type-safe** - Full IDE support and type checking
✅ **Unit-aware** - Automatic conversions, no manual math
✅ **Chainable** - Fluent, readable builder pattern
✅ **Validated** - Better error messages
✅ **Presets** - Common configurations ready to use
✅ **Backward compatible** - Old code still works

Start using the modern API today for cleaner, safer, and more maintainable code!
