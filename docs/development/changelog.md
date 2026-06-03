# Changelog

All notable changes to the ViscoWave project.

---

## [2.3.1] - 2026-06-03

### Fixed
- Corrected JILS DAT metadata handling so GPS coordinates and notes apply to
  every drop in the intended station block.
- Made example scripts runnable directly from a source checkout on Windows.
- Replaced Windows-console-incompatible status symbols in example output.

### Changed
- Updated the README feature list to describe only the implemented package API.
- Refreshed example descriptions to avoid outdated release wording.

---

## [2.0.0] - 2026-02-16

### 🎉 Major Release: Modern API

#### Added
- **Modern Fluent API** - Builder pattern with chainable methods
- **Automatic unit handling** - SI and Imperial units with automatic conversion
- **pint support** - Optional physical quantity units
- **Type hints** - Full type safety and IDE support (PEP 561 compatible)
- **Preset configurations** - Common pavement structures pre-configured
- **Helper functions** - `quick_analysis()`, `analyze_flexible_pavement()`, etc.
- **Comprehensive validation** - Input parameter validation with helpful error messages
- **Unit-aware results** - Easy conversion between units

#### Changed
- **pint is now optional** - No longer a required dependency
- **Improved error messages** - More descriptive validation errors
- **Better documentation** - Reorganized and expanded
- **Python 3.9+ required** - Dropped Python 3.8 support

#### Fixed
- README.md escape character in example code
- Missing `.gitignore` file
- pyproject.toml configuration improvements
- MANIFEST.in updates for proper package data inclusion

#### Developer Improvements
- Added `py.typed` marker for PEP 561 compliance
- Improved project structure with `docs/` directory
- Added development dependencies in pyproject.toml
- Created installation helper scripts
- Documentation reorganization and consolidation

### API Improvements
- **90% less code** compared to legacy API
- Backward compatible - old API still works
- Three API levels: Quick functions, Builder, Presets

---

## [1.0.0] - Previous

### Initial Release
- Legacy low-level API
- Manual unit conversion required
- Windows and macOS support
- Basic documentation

---

## Migration Guide: v1.0 → v2.0

### Old Code (v1.0):
```python
import numpy as np
from viscowave import units
from viscowave.api import ViscoWaveModel

pavement_si = np.array([[3e9, 0.35, 2400, 0.10, 0.1]])
pavement = units.convert_layer_parameters_si(pavement_si)
pressure, radius = units.convert_pressure_and_radius_si(550e3, 0.15)
sensors = units.convert_sensor_locations_si(np.array([0, 0.2, 0.5]))
# ... many more lines ...
model = ViscoWaveModel()
displacement = model.compute(...)
max_mm = np.max(np.abs(units.convert_displacement_to_si(displacement))) * 1000
```

### New Code (v2.0):
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

### Breaking Changes:
None - v1.0 API is still fully supported!

---

## Recent Fixes (2026-02-16)

### Documentation Reorganization
- ✅ Created unified `docs/` structure
- ✅ Merged duplicate installation guides
- ✅ Consolidated C++ build documentation
- ✅ Removed redundant files

### Project Hygiene
- ✅ Added comprehensive `.gitignore`
- ✅ Added `py.typed` for type checking support
- ✅ Updated `MANIFEST.in` for proper packaging
- ✅ Made pint an optional dependency

### Build System
- ✅ Verified CMake build process
- ✅ Tested macOS universal binaries
- ✅ Confirmed library loading works

---

**Format:** This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) principles.

**Versioning:** This project uses [Semantic Versioning](https://semver.org/).
