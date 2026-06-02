# Quick Start Guide

Get started with **ViscoWave 2.0** in minutes! This guide shows you the fastest way to run your first pavement analysis.

---

## ⚡ 5-Minute Quick Start

### 1. Install (Choose one):

```bash
# Option A: Virtual environment (recommended)
python3 -m venv venv && source venv/bin/activate && pip install -e .

# Option B: No install (just run)
./run_example.sh quick_start
```

### 2. Your First Analysis:

```python
from viscowave import AnalysisBuilder

# 3-layer flexible pavement with SI units
result = (
    AnalysisBuilder(unit_system="SI")
    .add_layer(modulus=3e9, poisson_ratio=0.35, density=2400, thickness=0.10)
    .add_layer(modulus=103e6, poisson_ratio=0.40, density=2200, thickness=0.30)
    .set_load(pressure=550e3, radius=0.15)
    .set_sensors(0, 0.2, 0.5, 1.0)
    .run()
)

print(f"Max displacement: {result.max_displacement('mm'):.3f} mm")
```

**That's it!** You've run your first pavement analysis. 🎉

---

## 📚 Example Gallery

### Example 1: Simple Analysis (Builder Pattern)

```python
from viscowave import AnalysisBuilder

result = (
    AnalysisBuilder(unit_system="SI")
    .add_layer(modulus=3e9, poisson_ratio=0.35, density=2400, thickness=0.10)  # AC layer
    .add_layer(modulus=103e6, poisson_ratio=0.40, density=2200, thickness=0.30)  # Base
    .set_load(pressure=550e3, radius=0.15)  # 550 kPa tire, 15 cm radius
    .set_sensors(0, 0.2, 0.5, 1.0)  # Sensors at 0, 20, 50, 100 cm
    .run()
)

print(f"Max displacement: {result.max_displacement('mm'):.3f} mm")
```

---

### Example 2: One-Line Analysis (Quick Function)

```python
from viscowave import quick_analysis

layers = [
    (3e9, 0.35, 2400, 0.10),     # E, nu, rho, h for AC
    (103e6, 0.40, 2200, 0.30),   # Base layer
]

result = quick_analysis(
    layers=layers,
    load_pressure=550e3,
    load_radius=0.15,
    sensor_locations=[0, 0.2, 0.5, 1.0],
    unit_system="SI"
)

print(f"Max: {result.max_displacement('mm'):.3f} mm")
```

---

### Example 3: Preset Configurations

```python
from viscowave.presets import Pavements

# Use pre-configured typical pavement
result = (
    Pavements.flexible_3layer_si()
    .set_load(pressure=550e3, radius=0.15)
    .set_sensors(0, 0.2, 0.5, 1.0)
    .run()
)

print(f"Max: {result.max_displacement('mm'):.3f} mm")
```

---

### Example 4: Imperial Units

```python
from viscowave import AnalysisBuilder

# Same API, just Imperial units!
result = (
    AnalysisBuilder(unit_system="Imperial")
    .add_layer(modulus=15000, poisson_ratio=0.40, density=120, thickness=12)  # psi, pcf, inches
    .set_load(pressure=80, radius=6)  # psi, inches
    .set_sensors(0, 12, 24, 36)  # inches
    .run()
)

print(f"Max: {result.max_displacement('in'):.4f} inches")
```

---

### Example 5: Unit Conversion

```python
result = builder.run()

# Get results in different units
disp_m = result.get_displacement('m')
disp_mm = result.get_displacement('mm')
disp_in = result.get_displacement('in')

print(f"Displacement:")
print(f"  {result.max_displacement('m'):.6f} m")
print(f"  {result.max_displacement('mm'):.3f} mm")
print(f"  {result.max_displacement('cm'):.4f} cm")
print(f"  {result.max_displacement('in'):.4f} in")
```

---

### Example 6: With pint Units (Optional)

```python
from viscowave import AnalysisBuilder, units

ureg = units.ureg  # pint unit registry

result = (
    AnalysisBuilder("SI")
    .add_layer(
        modulus=3 * ureg.GPa,                    # Physical quantities
        poisson_ratio=0.35,
        density=2400 * ureg.kg / ureg.m**3,
        thickness=10 * ureg.cm
    )
    .set_load(
        pressure=550 * ureg.kPa,
        radius=15 * ureg.cm
    )
    .set_sensors(0 * ureg.m, 0.2 * ureg.m, 0.5 * ureg.m)
    .run()
)

print(f"Max: {result.max_displacement('mm'):.3f} mm")
```

---

## 🎯 Three API Levels

ViscoWave offers three levels of abstraction:

### Level 1: Quick Functions (Simplest)
For simple, one-off analyses:
```python
from viscowave import quick_analysis
result = quick_analysis(layers=..., load_pressure=..., ...)
```

### Level 2: Builder Pattern (Flexible)
For full control with clean syntax:
```python
from viscowave import AnalysisBuilder
result = AnalysisBuilder("SI").add_layer(...).set_load(...).run()
```

### Level 3: Presets (Fastest)
For typical pavement configurations:
```python
from viscowave.presets import Pavements
result = Pavements.flexible_3layer_si().set_load(...).run()
```

---

## 🚀 Run Example Scripts

The project includes ready-to-run examples:

```bash
# Modern API examples
python3 examples/quick_start.py
python3 examples/modern_api_demo.py
python3 examples/viscowave_basic.py
python3 examples/viscowave_si_units.py

# Or use the helper script
./run_example.sh quick_start
./run_example.sh modern_api_demo
```

---

## ⚡ API Comparison: v1.0 vs v2.0

### Old API (v1.0) - 30+ lines of boilerplate:
```python
import numpy as np
from viscowave import units
from viscowave.api import ViscoWaveModel

# Manual conversions everywhere
pavement_si = np.array([[3e9, 0.35, 2400, 0.10, 0.1]])
pavement = units.convert_layer_parameters_si(pavement_si)
pressure, radius = units.convert_pressure_and_radius_si(550e3, 0.15)
sensors = units.convert_sensor_locations_si(np.array([0, 0.2, 0.5]))
time = np.linspace(0, 0.06, 300, dtype=np.float64)
# ... more setup ...

model = ViscoWaveModel()
displacement_ft = model.compute(...)
displacement_m = units.convert_displacement_to_si(displacement_ft)
max_mm = np.max(np.abs(displacement_m)) * 1000
```

### New API (v2.0) - 8 clean lines:
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

**90% less code!** 🎉

---

## 🐛 Common Issues

### Library not loading?

```bash
# Check if libraries exist
ls -l viscowave/*.dylib  # macOS
ls -l viscowave/*.dll    # Windows

# macOS: Check architecture
lipo -info viscowave/ViscoWave.dylib
```

### Module not found?

```bash
# Reinstall
pip install -e .

# Or use PYTHONPATH
PYTHONPATH=. python3 examples/quick_start.py
```

---

## 📖 Next Steps

Now that you've run your first analysis, explore:

1. **[Full Installation Guide](installation.md)** - All installation methods
2. **[Modern API Guide](../api/modern-api.md)** - Complete API reference
3. **[Examples Directory](../../examples/README.md)** - More working examples
4. **[Legacy API](../api/legacy-api.md)** - For existing v1.0 code

---

## 💡 Pro Tips

### IDE Support
ViscoWave 2.0 has full type hints for excellent IDE autocomplete:
```python
result = builder.run()
result.  # IDE shows: max_displacement, get_displacement, etc.
```

### Chaining Methods
All builder methods return `self`, so you can chain:
```python
result = (
    AnalysisBuilder("SI")
    .add_layer(...)
    .add_layer(...)
    .add_layer(...)
    .set_load(...)
    .set_sensors(...)
    .set_time(...)
    .run()
)
```

### Reuse Configurations
```python
# Build a base configuration
base = (
    AnalysisBuilder("SI")
    .add_layer(modulus=3e9, poisson_ratio=0.35, density=2400, thickness=0.10)
    .add_layer(modulus=103e6, poisson_ratio=0.40, density=2200, thickness=0.30)
)

# Try different loads
result1 = base.set_load(pressure=500e3, radius=0.15).set_sensors(0, 0.2).run()
result2 = base.set_load(pressure=700e3, radius=0.15).set_sensors(0, 0.2).run()
```

---

**Happy analyzing!** 🚀

For questions or issues, see the [full documentation](../api/modern-api.md) or [troubleshooting guide](installation.md#troubleshooting).
