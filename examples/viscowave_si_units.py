#!/usr/bin/env python3
"""
ViscoWave SI Units Example - Modern API

This example demonstrates the modern viscowave API with SI (metric) units.
The modern API has built-in SI unit support - no manual conversions needed!

SI Units Used:
    - Pressure: Pascal (Pa), typically kPa or MPa
    - Length: meter (m), or mm
    - Density: kg/m³
    - Time: seconds (s)
    - Displacement output: meters (m), typically mm
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt

from viscowave import (
    AnalysisBuilder,
    ViscoWaveError,
    get_platform_info,
    __version__,
)


def main():
    """Run ViscoWave analysis using SI units."""
    print("=" * 70)
    print("ViscoWave SI Units Example - Modern API")
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
    # 1. Define Analysis Parameters in SI Units
    # ========================================================================
    print("Step 1: Building analysis with SI units...")

    # Sensor locations in SI units (meters from load center)
    sensor_locations = [0, 0.2032, 0.3048, 0.4572, 0.6096, 0.9144, 1.2192, 1.5240, 1.8288]
    # Corresponding to 0, 8, 12, 18, 24, 36, 48, 60, 72 inches

    print(f"  - Sensors: {len(sensor_locations)}")
    print(f"  - Pavement layers: 3 (viscoelastic AC, base, subgrade)")
    print(f"  - Load: 551.6 kPa, radius: 15.24 cm")
    print()

    # ========================================================================
    # 2. Run Analysis with Modern API (SI Units)
    # ========================================================================
    print("Step 2: Running analysis with SI units (no conversions needed!)...")

    try:
        # Modern API: automatic SI unit handling!
        result = (
            AnalysisBuilder(unit_system="SI")
            # Layer 1: Viscoelastic AC layer (SI units)
            .add_viscoelastic_layer(
                poisson_ratio=0.35,
                density=2243,          # kg/m³
                thickness=0.3048,      # meters (~12 inches)
                damping=0.1,
                sigmoid=[3.123, 3.446, -0.128, 0.554]
            )
            # Layer 2: Base layer
            .add_layer(
                modulus=103.4e6,       # Pa (103.4 MPa = 15000 psi)
                poisson_ratio=0.40,
                density=1922,          # kg/m³
                thickness=0.3048,      # meters (~12 inches)
                damping=0.1
            )
            # Layer 3: Subgrade
            .add_layer(
                modulus=68.95e6,       # Pa (68.95 MPa = 10000 psi)
                poisson_ratio=0.45,
                density=1602,          # kg/m³
                thickness=3.0988,      # meters (semi-infinite)
                damping=0.1
            )
            # Load configuration (SI units) with half-sine load history
            .set_load(pressure=551.58e3, radius=0.1524, start_time=0.005, end_time=0.03)  # Pa, meters
            # Sensor locations (meters)
            .set_sensors(*sensor_locations)
            # Time settings
            .set_time(duration=0.06, steps=300, dt=0.0002)
            # Run analysis
            .run()
        )

        print("  OK: Analysis complete!")
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
    # 3. Display Results (Automatic SI unit conversion)
    # ========================================================================
    print("Step 3: Processing results...")

    # Modern API: easy unit conversion on results
    displacement_mm = result.get_displacement('mm')

    print(f"  - Max displacement: {result.max_displacement('mm'):.3f} mm")
    print(f"  - Min displacement: {result.min_displacement('mm'):.3f} mm")
    print()

    # ========================================================================
    # 4. Plot Results
    # ========================================================================
    print("Step 4: Plotting results...")

    plt.figure(figsize=(12, 8))

    # Plot displacement for each sensor
    for i in range(result.num_sensors):
        plt.plot(
            result.time * 1000,  # Convert to milliseconds for x-axis
            displacement_mm[i, :],
            label=f'Sensor {i+1} ({sensor_locations[i]*100:.1f} cm)',
            linewidth=1.5
        )

    plt.xlabel('Time (ms)', fontsize=12)
    plt.ylabel('Displacement (mm)', fontsize=12)
    plt.title('ViscoWave 2.0 with SI Units: Surface Displacement', fontsize=14, fontweight='bold')
    plt.legend(loc='best', fontsize=9, ncol=2)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Save figure
    output_path = Path(__file__).parent / "viscowave_si_results.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  OK: Figure saved: {output_path}")

    plt.show()

    # ========================================================================
    # 5. Summary
    # ========================================================================
    print()
    print("=" * 70)
    print("Analysis completed successfully!")
    print()
    print("Modern API Benefits with SI Units:")
    print("  OK: No manual unit conversions required")
    print("  OK: Cleaner, more readable code")
    print("  OK: Type-safe with full IDE support")
    print("  OK: Automatic result unit conversion")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
