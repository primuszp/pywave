# pywave Examples

This directory contains example scripts demonstrating the usage of the `viscowave` Python package.

## Examples Overview

### 1. [quick_start.py](quick_start.py)
**Recommended for beginners!**

The simplest possible example showing both ViscoWave and Relaxation_Sig_to_Prony functionality. Perfect for:
- Testing your installation
- Learning the basic API
- Quick verification that everything works

**Run:**
```bash
python examples/quick_start.py
```

**No plotting dependencies required** - just NumPy.

---

### 2. [viscowave_basic.py](viscowave_basic.py)
**Complete ViscoWave analysis example**

Production-ready example showing:
- Full pavement response analysis
- Proper error handling
- Unit conversions
- Load history generation
- Results visualization
- Platform detection

**Features:**
- 9 sensors at various distances
- 300 time steps
- Half-sine load pulse
- 3-layer pavement system
- Matplotlib visualization

**Run:**
```bash
python examples/viscowave_basic.py
```

**Output:** Console output + `viscowave_results.png`

---

### 3. [relaxation_basic.py](relaxation_basic.py)
**Complete Relaxation_Sig_to_Prony example**

Production-ready example showing:
- Sigmoid to Prony series conversion
- Results analysis and statistics
- Prony series visualization
- Relaxation modulus reconstruction

**Features:**
- 15 Prony elements
- Statistical analysis
- Dual-panel plots
- Time constant visualization

**Run:**
```bash
python examples/relaxation_basic.py
```

**Output:** Console output + `relaxation_results.png`

---

### 4. [viscowave_si_units.py](viscowave_si_units.py)
**ViscoWave with SI (metric) units**

Shows how to use SI units instead of Imperial units:
- Input in Pa, m, kg/m³ (instead of psi, ft, pcf)
- Output in mm (instead of mils)
- Automatic unit conversion
- Conversion reference display

**Features:**
- SI unit conversion functions
- Same analysis as viscowave_basic.py
- Demonstrates `units` module
- Includes conversion reference table

**Run:**
```bash
python examples/viscowave_si_units.py
```

**Output:** Console output + `viscowave_si_results.png`

---

## Requirements

### Minimal (quick_start.py)
```bash
pip install numpy
```

### Full (all examples with plots)
```bash
pip install numpy matplotlib
```

## Installation

Before running examples, install the `viscowave` package:

```bash
# From project root
pip install -e .

# Or if you're in the examples directory
pip install -e ..
```

## Usage Patterns

### Basic Pattern
```python
from viscowave.api import ViscoWaveModel

model = ViscoWaveModel()
displacement = model.compute(...)
```

### With Error Handling
```python
from viscowave import ViscoWaveError
from viscowave.api import ViscoWaveModel

try:
    model = ViscoWaveModel()
    displacement = model.compute(...)
except ViscoWaveError as e:
    print(f"Error in {e.func}: code {e.code}")
```

### Platform Detection
```python
from viscowave import get_platform_info

info = get_platform_info()
print(f"Platform: {info['system']} {info['architecture']}")
print(f"Library: {info['library_status']}")
```

### Using SI Units
```python
from viscowave import units
from viscowave.api import ViscoWaveModel
import numpy as np

# Define pavement in SI units: [E (Pa), nu, rho (kg/m³), h (m), damping (%)]
pavement_si = np.array([
    [3e9, 0.35, 2400, 0.10, 0.1],     # AC layer: 3 GPa, 2400 kg/m³, 10 cm
    [103e6, 0.40, 2200, 0.30, 0.1],   # Base: 103 MPa, 2200 kg/m³, 30 cm
])

# Convert to internal units
pavement = units.convert_layer_parameters_si(pavement_si)

# Convert load parameters: 550 kPa, 15 cm radius
pressure, radius = units.convert_pressure_and_radius_si(550e3, 0.15)

# Convert sensor locations: 0, 20, 50 cm
sensors = units.convert_sensor_locations_si(np.array([0, 0.2, 0.5]))

# Run analysis
model = ViscoWaveModel()
displacement_ft = model.compute(...)

# Convert output to SI (meters)
displacement_m = units.convert_displacement_to_si(displacement_ft)
displacement_mm = displacement_m * 1000  # Convert to mm
```

## Example Complexity

| Example | Lines | Features | Output | Best For |
|---------|-------|----------|--------|----------|
| quick_start.py | ~60 | Basic usage | Console | Testing, learning |
| viscowave_basic.py | ~180 | Full analysis (Imperial) | Console + PNG | Production use |
| relaxation_basic.py | ~150 | Full conversion | Console + PNG | Production use |
| viscowave_si_units.py | ~200 | Full analysis (SI units) | Console + PNG | SI/metric users |

## Common Issues

### Import Error
```
ModuleNotFoundError: No module named 'viscowave'
```

**Solution:** Install the package first
```bash
pip install -e ..  # from examples directory
```

### Library Not Found
```
ViscoWaveLibraryNotFoundError: Failed to load library 'ViscoWave'
```

**Solution:** Check that library files exist
```bash
ls -l ../viscowave/*.dylib  # macOS
ls -l ../viscowave/*.dll    # Windows
ls -l ../viscowave/*.so     # Linux
```

### Matplotlib Not Found
```
ModuleNotFoundError: No module named 'matplotlib'
```

**Solution:** Install matplotlib (only needed for visualization examples)
```bash
pip install matplotlib
```

## Customization

All examples are designed to be easily modified:

1. **Change pavement layers:** Edit the `pavement` array
2. **Modify load:** Change `load_pressure` and `load_radius`
3. **Add sensors:** Extend `sensor_location` array
4. **Longer analysis:** Increase `num_time` or time range
5. **Different materials:** Modify sigmoid parameters

## Output Files

Examples generate output files in the `examples/` directory:
- `viscowave_results.png` - From viscowave_basic.py
- `relaxation_results.png` - From relaxation_basic.py

These files are not tracked in git (see `.gitignore`).

## Further Reading

- [API Guide](../API_GUIDE.md) - Complete API reference
- [README](../README.md) - Project overview
- [QUICKSTART](../QUICKSTART.md) - Installation guide

## Support

For issues or questions:
- Check the [API Guide](../API_GUIDE.md)
- Review the [Troubleshooting](../API_GUIDE.md#troubleshooting) section
- Open an issue on GitHub
