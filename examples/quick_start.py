#!/usr/bin/env python3
"""
Quick Start Example - Modern API

This is the simplest possible example showing the modern viscowave API.
Perfect for getting started or testing your installation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from viscowave import AnalysisBuilder, get_platform_info
from viscowave.api import RelaxationPronyModel

# Display platform info
print("Quick Start Example - Modern API")
print("-" * 40)
info = get_platform_info()
print(f"Platform: {info['system']} {info['architecture']}")
print(f"Status: {info['library_status']}")
print()

# =============================================================================
# Example 1: Relaxation_Sig_to_Prony
# =============================================================================
print("1. Relaxation_Sig_to_Prony Example:")
print("-" * 40)

# Define sigmoid parameters
sigmoid = np.array([[3.123, 3.446, -0.128, 0.554]], dtype=np.float64)

# Convert to Prony series
model_rel = RelaxationPronyModel()
prony = model_rel.compute(sigmoid)

print(f"Input: {sigmoid.shape[0]} sigmoid sets")
print(f"Output: {prony.num_prony_elements} Prony elements")
print(f"First coefficient: {prony.matrix[0, 0]:.6f}")
print()

# =============================================================================
# Example 2: ViscoWave (Modern API - Much Simpler!)
# =============================================================================
print("2. ViscoWave Example (Modern API):")
print("-" * 40)

# Simple analysis with fluent API - no manual conversions needed!
result = (
    AnalysisBuilder(unit_system="Imperial")
    .add_viscoelastic_layer(
        poisson_ratio=0.35,
        density=140,
        thickness=12,
        sigmoid=[3.123, 3.446, -0.128, 0.554]
    )
    .add_layer(modulus=15000, poisson_ratio=0.40, density=120, thickness=12)
    .set_load(pressure=80, radius=6)  # psi, inches
    .set_sensors(0, 6, 12)  # 3 sensors at 0, 6, 12 inches
    .set_time(duration=0.02, steps=50)
    .run()
)

print(f"Analysis complete!")
print(f"Sensors: {result.num_sensors}")
print(f"Time steps: {result.num_time_steps}")
print(f"Max displacement: {result.max_displacement('in'):.4f} inches")
print()

print("=" * 40)
print("OK: Both examples completed successfully!")
print("=" * 40)
