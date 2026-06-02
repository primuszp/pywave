# pywave — Python Wrapper and Analysis Tools for ViscoWave

**pywave** is a professional Python library for pavement structure analysis using
Falling Weight Deflectometer (FWD) data. It wraps the **ViscoWave** dynamic Finite
Layer Method (FLM) engine and adds pure-Python equivalents of all ViscoWave Excel
analyses: FWD data import, deflection basin indices, backcalculation, and dynamic
modulus master curves.

---

## Attribution and License

**ViscoWave** (the C/C++ computational engine, Excel workbook, and precompiled
binaries) was developed by **H.S. Lee** and is the original and primary work.
The ViscoWave engine is available at:

- Original repository: [leehyu20/ViscoWave](https://github.com/leehyu20/ViscoWave)
- Fork used as base: [primuszp/ViscoWave](https://github.com/primuszp/ViscoWave)

**References:**
- Lee, H.S. (2013). *Development of a New Solution for Viscoelastic Wave
  Propagation of Pavement Structures and Its Use in Dynamic Backcalculation.*
  PhD Dissertation, North Carolina State University.
- Lee, H.S. (2014). *ViscoWave-II: A New Solution for Viscoelastic Wave
  Propagation of Pavement Structures.* International Journal of Pavement Engineering.

The precompiled ViscoWave and Relaxation_Sig_to_Prony libraries included in this
package are part of the original ViscoWave project and remain © H.S. Lee,
released under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

**pywave** (this Python wrapper and all new Python modules) extends ViscoWave with
a modern Python API and is released under **AGPL-3.0-or-later** in compliance with
the terms of the upstream project.

```
ViscoWave engine © H.S. Lee — GNU Affero General Public License v3.0
pywave Python wrapper © 2024–2026 — GNU Affero General Public License v3.0-or-later
```

See [LICENSE](LICENSE) for the full license text.

---

## What pywave adds on top of ViscoWave

| Feature | ViscoWave (original) | pywave |
|---|---|---|
| Pavement forward analysis | Excel + VBA | Python fluent builder API |
| FWD file import | — | Pure Python (`fwd_io` module) |
| JILS *.DAT reader | — | `read_jils()` |
| JILS *.THY time history reader | — | `read_jils_thy()`, auto-loaded with DAT |
| Dynatest Access database reader | R/ODBC script | `read_dynatest_access()` |
| Dynatest *.FWD text reader | — | `read_dynatest()` |
| Kuab *.fwd peak reader | R script | `read_kuab()` |
| Kuab *.HST + *.fwd folder workflow | R script | `read_kuab_folder()` |
| Automatic FWD format detection | — | `read_fwd()` |
| Tabular FWD export | — | `FWDDataset.to_records()`, `FWDDataset.to_dataframe()` |
| Deflection basin indices (SCI, BDI, BCI, AREA) | Excel formulas | `indices.DeflectionBasin` |
| Subgrade modulus estimate (Boussinesq) | Excel | `compute_subgrade_modulus()` |
| AASHTO Structural Number estimate | Excel | `compute_structural_number_fwd()` |
| Backcalculation (layer moduli) | Excel iterative | `backcalc.backcalculate()` (scipy L-BFGS-B) |
| Batch backcalculation | Excel macro | `backcalculate_batch()` |
| Dynamic modulus master curve | Excel worksheet | `dynmod.SigmoidModel` |
| WLF / Arrhenius shift factors | Excel | `wlf_shift_factor()` / `arrhenius_shift_factor()` |
| Prony series conversion | ViscoWave DLL | `RelaxationPronyModel` (Python wrapper) |
| SI **and** Imperial unit handling | Imperial only | Automatic via `units` module |
| pint.Quantity input support | None | Optional (`pip install viscowave[units]`) |
| Type-safe API | None | Full type hints (PEP 561) |

---

## Installation

```bash
# Core package (forward analysis + FWD data tools)
pip install viscowave

# With backcalculation and pandas support
pip install "viscowave[analysis]"

# With plotting
pip install "viscowave[plot]"

# All optional dependencies
pip install "viscowave[all]"
```

**For development / install from source:**
```bash
git clone https://github.com/primuszp/pywave.git
cd pywave
pip install -e ".[dev]"
```

**Requirements:**
- Python 3.9–3.12
- numpy >= 1.20
- scipy >= 1.7 *(optional, required for backcalculation)*
- pandas >= 1.3 *(optional)*
- matplotlib >= 3.4 *(optional)*
- pint >= 0.21 *(optional, for unit-aware inputs)*

**Platform support:** Windows x64 and macOS (Intel x86\_64 + Apple Silicon ARM64) with packaged native libraries. Linux source-build support is documented, but Linux binaries are not included in the current release bundle.

Dynatest Access database import requires the optional Access/ODBC dependency:

```bash
pip install "viscowave[access]"
```

---

## Quick Start

### 1. Forward pavement analysis

```python
from viscowave import AnalysisBuilder

# 3-layer flexible pavement (SI units)
result = (
    AnalysisBuilder(unit_system="SI")
    .add_layer(modulus=3e9,   poisson_ratio=0.35, density=2400, thickness=0.10)  # AC 10 cm
    .add_layer(modulus=200e6, poisson_ratio=0.40, density=2200, thickness=0.30)  # base 30 cm
    .add_layer(modulus=60e6,  poisson_ratio=0.45, density=1600, thickness=10.0)  # subgrade
    .set_load(pressure=550e3, radius=0.15)          # 550 kPa, 150 mm plate
    .set_sensors(0, 0.2, 0.3, 0.45, 0.6, 0.9)      # sensor offsets in m
    .run()
)

print(f"Max deflection: {result.max_displacement('mm'):.3f} mm")
# Access time history for sensor 0
import matplotlib.pyplot as plt
plt.plot(result.time * 1000, result.get_sensor_displacement(0, 'mm'))
plt.xlabel("Time (ms)"); plt.ylabel("Deflection (mm)")
```

### 2. Load FWD data (with time histories)

```python
from viscowave.fwd_io import read_fwd, read_jils, read_kuab_folder

# Load JILS FWD survey — THY time history file auto-loaded if present
ds = read_jils(
    "sample/JILS_Sample.DAT",
    sensor_offsets_mm=[0, 200, 300, 450, 600, 900, 1200, 1500, 1800],
)
print(ds)  # FWDDataset(device='JILS', stations=10, drops=30)

# Or let pywave choose the reader from the file extension/header
ds_auto = read_fwd("sample/JILS_Sample.DAT")
rows = ds_auto.to_records()  # plain dictionaries, ready for reporting/export

# Kuab ViscoWave V3 folders can be loaded as a peak + time-history workflow
kuab_ds = read_kuab_folder("path/to/kuab_folder")

# Iterate representative drops (drop 2 = first test drop after seating)
for drop in ds.representative_drops(drop_number=2):
    print(f"Station {drop.station}: D0={drop.deflections_mm[0]:.3f} mm, "
          f"load={drop.load_kN:.1f} kN, temp={drop.pavement_temp_C:.1f}°C")
    if drop.time_history:
        th = drop.time_history
        print(f"  Time history: {th.n_samples} samples, "
              f"peak force = {th.peak_force_kN:.1f} kN")
```

### 3. Deflection basin indices

```python
from viscowave.indices import DeflectionBasin

basin = DeflectionBasin(
    deflections_mm=[0.800, 0.510, 0.350, 0.245, 0.175, 0.118],
    offsets_mm=[0, 200, 300, 450, 600, 900],
    load_kN=40.0,
    normalise_load=True,
    reference_load_kN=40.0,
)

print(f"D0   = {basin.D0:.3f} mm")
print(f"SCI  = {basin.SCI:.3f} mm  (D0 − D300, surface layer condition)")
print(f"BDI  = {basin.BDI:.3f} mm  (D300 − D600, base layer condition)")
print(f"BCI  = {basin.BCI:.3f} mm  (D600 − D900, upper subgrade condition)")
print(f"AREA = {basin.AREA:.1f} mm")
print(f"E_sg = {basin.subgrade_modulus_MPa:.0f} MPa (estimated subgrade modulus)")
print(f"SN   = {basin.structural_number:.1f} (estimated AASHTO structural number)")
```

### 4. Backcalculation

```python
from viscowave.backcalc import backcalculate, BackcalcLayer

result = backcalculate(
    measured_deflections_mm=[0.800, 0.510, 0.350, 0.245, 0.175, 0.118],
    sensor_offsets_mm=[0, 200, 300, 450, 600, 900],
    layer_structure=[
        BackcalcLayer(3000, bounds=(500, 30000), poisson_ratio=0.35,
                      thickness=0.10, label="AC"),
        BackcalcLayer(200,  bounds=(50, 2000),   poisson_ratio=0.40,
                      thickness=0.30, label="Base"),
        BackcalcLayer(60,   bounds=(10, 500),    poisson_ratio=0.45,
                      label="Subgrade"),
    ],
    load_kN=40.0,
    load_radius_mm=150.0,
)

print(result)
# BackcalcResult(moduli=[2873, 187, 61] MPa, RMSE=0.0052 mm, converged=True)
for lyr, E in zip(["AC", "Base", "Subgrade"], result.moduli_MPa):
    print(f"  {lyr}: {E:.0f} MPa  ({E/1000:.2f} GPa)")
```

### 5. Dynamic modulus master curve

```python
from viscowave.dynmod import SigmoidModel

# Sigmoid parameters from laboratory |E*| testing (MEPDG Level 1)
model = SigmoidModel(delta=3.123, alpha=3.446, beta=-0.128, gamma=0.554, Tref_C=20.0)

print(f"|E*| at 20°C, 10 Hz = {model.modulus(temp_C=20, freq_Hz=10):.0f} MPa")
print(f"|E*| at 40°C,  1 Hz = {model.modulus(temp_C=40, freq_Hz=1):.0f} MPa")

# Master curve for plotting
mc = model.master_curve(
    freqs_Hz=[0.1, 0.5, 1, 5, 10, 25],
    temps_C=[5, 20, 40],
    Tref_C=20.0,
).sorted()

import matplotlib.pyplot as plt
plt.semilogx(mc.reduced_freqs_Hz, mc.moduli_MPa, 'o')
plt.xlabel("Reduced frequency (Hz)")
plt.ylabel("|E*| (MPa)")
plt.title("Dynamic Modulus Master Curve (Tref = 20°C)")
```

### 6. Viscoelastic analysis with Prony series

```python
from viscowave import AnalysisBuilder
from viscowave.api import RelaxationPronyModel
import numpy as np

# Convert sigmoid parameters to Prony series
sigmoid = np.array([[3.123, 3.446, -0.128, 0.554]])
prony_model = RelaxationPronyModel()
prony = prony_model.compute(sigmoid)

# Run viscoelastic forward analysis
result = (
    AnalysisBuilder(unit_system="SI")
    .add_viscoelastic_layer(
        poisson_ratio=0.35,
        density=2400,
        thickness=0.10,
        sigmoid=[3.123, 3.446, -0.128, 0.554],
    )
    .add_layer(modulus=200e6, poisson_ratio=0.40, density=2200, thickness=0.30)
    .add_layer(modulus=60e6,  poisson_ratio=0.45, density=1600, thickness=10.0)
    .set_load(pressure=550e3, radius=0.15)
    .set_sensors(0, 0.2, 0.3, 0.45, 0.6, 0.9)
    .run()
)
print(f"Viscoelastic max deflection: {result.max_displacement('mm'):.3f} mm")
```

---

## API Overview

```
viscowave/
├── __init__.py          # Public API, version 2.3.0
│
├── FORWARD ANALYSIS (core — wraps ViscoWave C++ library by H.S. Lee)
├── builders.py          # AnalysisBuilder (fluent API), AnalysisResult
├── highlevel.py         # analyze(), quick_analysis(), analyze_flexible_pavement()
├── presets.py           # Pavements.*(), Loads.*() preset configurations
├── api.py               # Low-level: ViscoWaveModel, RelaxationPronyModel
│
├── PYTHON ANALYSIS TOOLS (new in pywave — Python equivalents of Excel worksheets)
├── fwd_io.py            # FWD readers: read_jils(), read_jils_thy(),
│                        #   read_dynatest(), read_kuab()
│                        #   FWDDrop, FWDTimeHistory, FWDDataset
├── indices.py           # DeflectionBasin, SCI/BDI/BCI/AREA/SN indices
├── backcalc.py          # backcalculate(), backcalculate_batch() (scipy L-BFGS-B)
├── dynmod.py            # SigmoidModel, MasterCurveData, WLF/Arrhenius shift factors
│
├── INFRASTRUCTURE
├── types.py             # PavementLayer, LoadConfig, TimeConfig, SigmoidParams
├── units.py             # Unit conversion: SI ↔ Imperial ↔ internal ft/psf/slug
├── validation.py        # Input validation with ViscoWave C++ limits
├── exceptions.py        # ViscoWaveError, ViscoWaveLibraryNotFoundError
├── _dylib.py            # Platform-specific DLL/dylib loader
└── _lowlevel.py         # ctypes bindings to ViscoWave C++ functions
```

---

## ViscoWave C++ engine constraints

The underlying ViscoWave library imposes the following hard limits (enforced by
pywave with informative error messages):

| Parameter | Limit |
|---|---|
| Pavement layers | max 6 |
| Viscoelastic layers | max 3 (must be at the top of the stack) |
| Deflection sensors | max 9 |
| Time step (dt) | 0.0002 s (0.2 ms) |
| Analysis duration | 0.06 s (300 steps default) |

---

## Building the C++ libraries from source

The precompiled binaries for Windows (x64) and macOS (Intel x86\_64 + ARM64 universal)
are included in the package. To recompile from source:

- [BUILD_WINDOWS.md](csrc/ViscoWave_portable/BUILD_WINDOWS.md)
- [BUILD_MACOS.md](csrc/ViscoWave_portable/BUILD_MACOS.md)
- [BUILD_LINUX.md](csrc/ViscoWave_portable/BUILD_LINUX.md)

---

## Documentation

- [docs/getting-started/installation.md](docs/getting-started/installation.md)
- [docs/getting-started/quickstart.md](docs/getting-started/quickstart.md)
- [docs/api/modern-api.md](docs/api/modern-api.md)
- [docs/api/legacy-api.md](docs/api/legacy-api.md)
- [docs/development/changelog.md](docs/development/changelog.md)
- [examples/](examples/) — Working code examples

---

## References

- Lee, H.S. (2013). *Development of a New Solution for Viscoelastic Wave
  Propagation of Pavement Structures and Its Use in Dynamic Backcalculation.*
  PhD Dissertation, North Carolina State University.
- Lee, H.S. (2014). *ViscoWave-II: A New Solution for Viscoelastic Wave
  Propagation of Pavement Structures.* International Journal of Pavement Engineering.
- AASHTO (1993). *AASHTO Guide for Design of Pavement Structures.*
- Witczak, M.W. & Fonseca, O.A. (1996). *Revised Predictive Model for Dynamic
  (Complex) Modulus of Asphalt Mixtures.* Transportation Research Record 1540.
- Horak, E. (2008). *Benchmarking Deflection Basin Parameters.* TRB Annual Meeting.
- Shahin, M.Y. (2005). *Pavement Management for Airports, Roads, and Parking Lots.*
  Springer.
