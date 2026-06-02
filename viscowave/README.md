# viscowave – Python wrapper for visco_wave and relaxation_sig_to_prony

This module includes platform-specific libraries:

**Windows:**
- `ViscoWave_x64.dll`
- `Relaxation_Sig_to_Prony_x64.dll`
- `libwinpthread-1.dll` (required by MinGW-built DLLs)

**macOS (Universal Binary - Intel + Apple Silicon):**
- `ViscoWave.dylib`
- `Relaxation_Sig_to_Prony.dylib`

The module automatically detects your platform and loads the appropriate library.

## Quick start (ViscoWave)
```python
import numpy as np
from viscowave.api import ViscoWaveModel, convert_layer_parameters, convert_pressure_and_radius
from viscowave.api import update_sigmoidal_coefficients, half_sine_values

model = ViscoWaveModel()

sigmoid = np.array([[3.123, 3.446, -0.128, 0.554]], dtype=np.float64)
pavement = np.array([
    [0.000, 0.35, 140, 12.00, 0.1],
    [15000, 0.40, 120, 12.00, 0.1],
    [10000, 0.45, 100, 122.2, 0.1],
], dtype=np.float64)

pavement = convert_layer_parameters(pavement)
sigmoid = update_sigmoidal_coefficients(sigmoid, pavement)

load_pressure, load_radius = convert_pressure_and_radius(80.0, 6.0)
sensor_location = np.array([0, 8, 12, 18, 24, 36, 48, 60, 72], dtype=np.float64) / 12
time = np.linspace(0, 0.06, 300, dtype=np.float64)
timehistory = half_sine_values(0.005, 0.03, 1.0, time)

disp = model.compute(
    sigmoid=sigmoid,
    pavement=pavement,
    load_pressure=load_pressure,
    load_radius=load_radius,
    sensor_location=sensor_location,
    time=time,
    timehistory=timehistory,
    dt=0.0002,
    num_ve_layer=1,
)
```

## Quick start (Relaxation -> Prony)
```python
import numpy as np
from viscowave.api import RelaxationPronyModel

sigmoid = np.array([[3.123, 3.446, -0.128, 0.554]], dtype=np.float64)
prony_model = RelaxationPronyModel()
prony_result = prony_model.compute(sigmoid)
print(prony_result.matrix)  # shape: (15, num_sigmoid+1)
```
