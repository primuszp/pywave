#!/usr/bin/env python3
"""
ViscoWave Basic Example - Modern API 2.0

This example demonstrates the modern ViscoWave 2.0 API with fluent builder pattern.
Much simpler than the legacy API with automatic unit handling!
"""

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from viscowave import (
    AnalysisBuilder,
    ViscoWaveError,
    get_platform_info,
    __version__,
)


def main():
    """Run ViscoWave analysis and plot results."""
    print("=" * 70)
    print("ViscoWave Basic Example - Modern API 2.0")
    print("=" * 70)
    print()

    # Display platform info
    info = get_platform_info()
    print(f"Platform: {info['system']} {info['architecture']}")
    print(f"Python: {info['python_version']}")
    print(f"viscowave: {__version__}")
    print(f"Library: {info['library_status']}")
    print()

    # ========================================================================
    # 1. Define Analysis Parameters
    # ========================================================================
    print("Step 1: Building analysis with modern fluent API...")

    # Sensor locations (inches from load center)
    sensor_locations = [0, 8, 12, 18, 24, 36, 48, 60, 72]

    print(f"  - Sensors: {len(sensor_locations)}")
    print(f"  - Pavement layers: 3 (viscoelastic AC, base, subgrade)")
    print()

    # ========================================================================
    # 2. Run Analysis with Modern API
    # ========================================================================
    print("Step 2: Running analysis (no manual conversions needed!)...")

    try:
        # Modern API: chainable, type-safe, automatic unit handling
        result = (
            AnalysisBuilder(unit_system="Imperial")
            # Layer 1: Viscoelastic AC layer
            .add_viscoelastic_layer(
                poisson_ratio=0.35,
                density=140,          # pcf
                thickness=12,         # inches
                damping=0.1,
                sigmoid=[3.123, 3.446, -0.128, 0.554]
            )
            # Layer 2: Base layer
            .add_layer(
                modulus=15000,        # psi
                poisson_ratio=0.40,
                density=120,          # pcf
                thickness=12,         # inches
                damping=0.1
            )
            # Layer 3: Subgrade
            .add_layer(
                modulus=10000,        # psi
                poisson_ratio=0.45,
                density=100,          # pcf
                thickness=122.2,      # inches (semi-infinite)
                damping=0.1
            )
            # Load configuration with half-sine load history
            .set_load(pressure=80, radius=6, start_time=0.005, end_time=0.03)  # psi, inches
            # Sensor locations
            .set_sensors(*sensor_locations)
            # Time settings
            .set_time(duration=0.06, steps=300, dt=0.0002)
            # Run analysis
            .run()
        )

        print(f"  ✓ Analysis complete!")
        print(f"  - Sensors: {result.num_sensors}")
        print(f"  - Time steps: {result.num_time_steps}")
        print()

    except ViscoWaveError as e:
        print(f"ERROR: Computation failed in {e.func} (code {e.code})")
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return 1

    # ========================================================================
    # 3. Display Results
    # ========================================================================
    print("Step 3: Processing results...")

    # Modern API: easy unit conversion on results
    displacement_in = result.get_displacement('in')

    print(f"  - Max displacement: {result.max_displacement('in'):.4f} inches")
    print(f"  - Min displacement: {result.min_displacement('in'):.4f} inches")
    print()

    # ========================================================================
    # 4. Plot Results
    # ========================================================================
    print("Step 4: Plotting results...")

    plt.figure(figsize=(12, 8))

    # Plot displacement for each sensor
    for i in range(result.num_sensors):
        plt.plot(
            result.time,
            displacement_in[i, :],
            label=f'Sensor {i+1} ({sensor_locations[i]:.0f} in)',
            linewidth=1.5
        )

    plt.xlabel('Time (s)', fontsize=12)
    plt.ylabel('Displacement (inches)', fontsize=12)
    plt.title('ViscoWave 2.0 Analysis: Surface Displacement Time History', fontsize=14, fontweight='bold')
    plt.legend(loc='best', fontsize=9, ncol=2)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Save figure
    output_path = Path(__file__).parent / "viscowave_results.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  ✓ Figure saved: {output_path}")

    plt.show()

    print()
    print("=" * 70)
    print("Analysis completed successfully! ✓")
    print("Modern API is much simpler - compare with legacy API!")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
