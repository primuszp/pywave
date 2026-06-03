#!/usr/bin/env python3
"""
Modern API Demo - viscowave

This example demonstrates the fluent viscowave API.
The modern API provides:
- Automatic unit handling (SI and Imperial)
- Chainable builder pattern
- Type-safe configuration
- Simplified result access
- Preset configurations

Compare this to the legacy API examples to see the improvement in usability.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import matplotlib.pyplot as plt

from viscowave import (
    AnalysisBuilder,
    quick_analysis,
    analyze_flexible_pavement,
    __version__,
)
from viscowave.presets import Pavements, Loads


def example_1_fluent_api():
    """
    Example 1: Fluent API with Builder Pattern

    The modern API uses a chainable builder pattern for clean, readable code.
    """
    print("=" * 70)
    print("Example 1: Fluent API with Builder Pattern")
    print("=" * 70)
    print()

    # SI Units - Clean and simple!
    result = (
        AnalysisBuilder(unit_system="SI")
        .add_layer(modulus=3e9, poisson_ratio=0.35, density=2400, thickness=0.10)
        .add_layer(modulus=103e6, poisson_ratio=0.40, density=2200, thickness=0.30)
        .add_layer(modulus=69e6, poisson_ratio=0.45, density=1600, thickness=10.0)
        .set_load(pressure=550e3, radius=0.15)
        .set_sensors(0, 0.2, 0.5, 1.0)
        .set_time(duration=0.06, steps=300)
        .run()
    )

    print(f"Analysis complete!")
    print(f"  - Sensors: {result.num_sensors}")
    print(f"  - Time steps: {result.num_time_steps}")
    print(f"  - Max displacement: {result.max_displacement('mm'):.3f} mm")
    print(f"  - Max displacement: {result.max_displacement('in'):.4f} in")
    print()

    return result


def example_2_quick_analysis():
    """
    Example 2: Quick Analysis Function

    For simple cases, use the quick_analysis function with minimal parameters.
    """
    print("=" * 70)
    print("Example 2: Quick Analysis Function")
    print("=" * 70)
    print()

    # Define layers as simple tuples: (E, nu, rho, h)
    layers = [
        (3e9, 0.35, 2400, 0.10),     # AC layer
        (103e6, 0.40, 2200, 0.30),   # Base
        (69e6, 0.45, 1600, 10.0),    # Subgrade
    ]

    # Run analysis with one function call
    result = quick_analysis(
        layers=layers,
        load_pressure=550e3,  # 550 kPa
        load_radius=0.15,     # 15 cm
        sensor_locations=[0, 0.2, 0.5, 1.0],
        unit_system="SI"
    )

    print(f"Analysis complete!")
    print(f"  - Max displacement: {result.max_displacement('mm'):.3f} mm")
    print()

    return result


def example_3_preset_configurations():
    """
    Example 3: Preset Configurations

    Use pre-configured pavement structures and loading conditions.
    """
    print("=" * 70)
    print("Example 3: Preset Configurations")
    print("=" * 70)
    print()

    # Use preset flexible pavement structure
    result = (
        Pavements.flexible_3layer_si()
        .set_load(pressure=550e3, radius=0.15)
        .set_sensors(0, 0.2, 0.5, 1.0, 1.5)
        .run()
    )

    print(f"Flexible pavement analysis:")
    print(f"  - Max displacement: {result.max_displacement('mm'):.3f} mm")
    print()

    # Use preset rigid pavement
    result_rigid = (
        Pavements.rigid_pcc_si(pcc_thickness=0.25)
        .set_load(pressure=550e3, radius=0.15)
        .set_sensors(0, 0.2, 0.5)
        .run()
    )

    print(f"Rigid pavement analysis:")
    print(f"  - Max displacement: {result_rigid.max_displacement('mm'):.3f} mm")
    print()

    return result


def example_4_imperial_units():
    """
    Example 4: Imperial Units

    The API seamlessly handles Imperial units as well.
    """
    print("=" * 70)
    print("Example 4: Imperial Units")
    print("=" * 70)
    print()

    result = (
        AnalysisBuilder(unit_system="Imperial")
        .add_layer(modulus=15000, poisson_ratio=0.40, density=120, thickness=12)
        .add_layer(modulus=10000, poisson_ratio=0.45, density=100, thickness=48)
        .set_load(pressure=80, radius=6)  # psi, inches
        .set_sensors(0, 12, 24, 36)       # inches
        .run()
    )

    print(f"Imperial units analysis:")
    print(f"  - Max displacement: {result.max_displacement('in'):.4f} in")
    print(f"  - Max displacement: {result.max_displacement('mm'):.3f} mm")
    print()

    return result


def example_5_helper_functions():
    """
    Example 5: Helper Functions for Common Cases

    Use specialized helper functions for typical scenarios.
    """
    print("=" * 70)
    print("Example 5: Helper Functions")
    print("=" * 70)
    print()

    # Analyze a flexible pavement with minimal parameters
    result = analyze_flexible_pavement(
        ac_thickness=0.10,        # 10 cm
        base_thickness=0.30,      # 30 cm
        subgrade_modulus=69e6,    # 69 MPa
        load_pressure=550e3,      # 550 kPa
        load_radius=0.15,         # 15 cm
        unit_system="SI"
    )

    print(f"Flexible pavement helper:")
    print(f"  - Max displacement: {result.max_displacement('mm'):.3f} mm")
    print()

    return result


def example_6_result_access():
    """
    Example 6: Easy Result Access

    The new AnalysisResult class provides convenient methods for accessing results.
    """
    print("=" * 70)
    print("Example 6: Easy Result Access")
    print("=" * 70)
    print()

    result = (
        AnalysisBuilder(unit_system="SI")
        .add_layer(modulus=3e9, poisson_ratio=0.35, density=2400, thickness=0.10)
        .add_layer(modulus=103e6, poisson_ratio=0.40, density=2200, thickness=0.30)
        .set_load(pressure=550e3, radius=0.15)
        .set_sensors(0, 0.2, 0.5)
        .run()
    )

    # Access results in different units - no manual conversion needed!
    print("Displacement in different units:")
    print(f"  - Meters: {result.max_displacement('m'):.6f} m")
    print(f"  - Millimeters: {result.max_displacement('mm'):.3f} mm")
    print(f"  - Centimeters: {result.max_displacement('cm'):.4f} cm")
    print(f"  - Feet: {result.max_displacement('ft'):.6f} ft")
    print(f"  - Inches: {result.max_displacement('in'):.4f} in")
    print()

    # Get displacement for a specific sensor
    sensor_0_disp = result.get_sensor_displacement(0, unit='mm')
    print(f"Sensor 0 max: {np.max(np.abs(sensor_0_disp)):.3f} mm")
    print()

    return result


def plot_comparison(results_dict):
    """
    Plot results comparison.

    Args:
        results_dict: Dictionary of {label: AnalysisResult}
    """
    print("=" * 70)
    print("Plotting Comparison")
    print("=" * 70)
    print()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    for label, result in results_dict.items():
        # Plot time history at first sensor
        disp_mm = result.get_sensor_displacement(0, unit='mm')
        time_ms = result.time * 1000  # Convert to milliseconds

        ax1.plot(time_ms, disp_mm, label=label, linewidth=2)

    ax1.set_xlabel('Time (ms)', fontsize=12)
    ax1.set_ylabel('Displacement (mm)', fontsize=12)
    ax1.set_title('Displacement at Load Center (Sensor 0)', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot maximum displacement vs configuration
    labels = list(results_dict.keys())
    max_disps = [result.max_displacement('mm') for result in results_dict.values()]

    ax2.bar(range(len(labels)), max_disps, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'][:len(labels)])
    ax2.set_xticks(range(len(labels)))
    ax2.set_xticklabels(labels, rotation=45, ha='right')
    ax2.set_ylabel('Max Displacement (mm)', fontsize=12)
    ax2.set_title('Maximum Displacement Comparison', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    # Save figure
    output_path = Path(__file__).parent / "modern_api_results.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Figure saved: {output_path}")

    plt.show()


def main():
    """Run all examples."""
    print("=" * 70)
    print(f"ViscoWave Modern API Demo (v{__version__})")
    print("=" * 70)
    print()

    # Run examples
    result1 = example_1_fluent_api()
    result2 = example_2_quick_analysis()
    result3 = example_3_preset_configurations()
    result4 = example_4_imperial_units()
    result5 = example_5_helper_functions()
    result6 = example_6_result_access()

    # Plot comparison
    results_dict = {
        'Fluent API': result1,
        'Quick Analysis': result2,
        'Preset Config': result3,
        'Helper Function': result5,
    }

    plot_comparison(results_dict)

    print()
    print("=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
    print()
    print("Key API features:")
    print("  OK: Fluent/chainable API for better readability")
    print("  OK: Automatic unit handling (SI and Imperial)")
    print("  OK: Type-safe configuration with dataclasses")
    print("  OK: Convenient result access methods")
    print("  OK: Preset configurations for common cases")
    print("  OK: Helper functions for quick analysis")
    print("  OK: Backward compatible with legacy API")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
