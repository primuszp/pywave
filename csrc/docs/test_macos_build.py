#!/usr/bin/env python3
"""
Test script for macOS universal binary libraries.
Verifies that both ViscoWave and Relaxation_Sig_to_Prony libraries load correctly.
"""

import sys
import platform
import numpy as np

def test_imports():
    """Test that the modules can be imported."""
    print("=" * 60)
    print("Testing viscowave module on macOS")
    print("=" * 60)
    print()

    # System info
    print("System Information:")
    print(f"  Platform: {platform.system()} {platform.release()}")
    print(f"  Architecture: {platform.machine()}")
    print(f"  Python: {sys.version.split()[0]}")
    print()

    # Import test
    print("Testing imports...")
    try:
        from viscowave.api import ViscoWaveModel, RelaxationPronyModel
        print("  ✓ viscowave module imported successfully")
    except ImportError as e:
        print(f"  ✗ Failed to import viscowave: {e}")
        return False

    # Create instances
    print("\nCreating model instances...")
    try:
        vw = ViscoWaveModel()
        print("  ✓ ViscoWaveModel instance created")
    except Exception as e:
        print(f"  ✗ Failed to create ViscoWaveModel: {e}")
        return False

    try:
        rel = RelaxationPronyModel()
        print("  ✓ RelaxationPronyModel instance created")
    except Exception as e:
        print(f"  ✗ Failed to create RelaxationPronyModel: {e}")
        return False

    return True


def test_relaxation():
    """Test Relaxation_Sig_to_Prony computation."""
    print("\nTesting Relaxation_Sig_to_Prony computation...")
    try:
        from viscowave.api import RelaxationPronyModel

        # Sample sigmoid parameters
        sigmoid = np.array([[3.123, 3.446, -0.128, 0.554]], dtype=np.float64)

        rel = RelaxationPronyModel()
        result = rel.compute(sigmoid)

        print(f"  ✓ Computation successful")
        print(f"  ✓ Result shape: {result.matrix.shape}")
        print(f"  ✓ First Prony coefficient: {result.matrix[0, 0]:.6f}")

        return True
    except Exception as e:
        print(f"  ✗ Computation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_viscowave():
    """Test ViscoWave computation (minimal test)."""
    print("\nTesting ViscoWave computation...")
    try:
        from viscowave.api import (
            ViscoWaveModel,
            convert_layer_parameters,
            convert_pressure_and_radius,
            update_sigmoidal_coefficients,
            half_sine_values,
        )

        # Minimal test parameters
        Num_Sensors = 3
        Num_Time = 50
        Num_VE_Layer = 1

        sigmoid = np.array([[3.123, 3.446, -0.128, 0.554]], dtype=np.float64)
        pavement = np.array([
            [0.000, 0.35, 140, 12.00, 0.1],
            [15000, 0.40, 120, 12.00, 0.1],
            [10000, 0.45, 100, 122.2, 0.1]
        ], dtype=np.float64)

        pavement = convert_layer_parameters(pavement)
        sigmoid = update_sigmoidal_coefficients(sigmoid, pavement)

        load_pressure, load_radius = convert_pressure_and_radius(80.0, 6.0)
        sensor_location = np.array([0, 8, 12], dtype=np.float64) / 12
        time = np.linspace(0, 0.06, Num_Time, dtype=np.float64)
        timehistory = half_sine_values(0.005, 0.03, 1.0, time)

        vw = ViscoWaveModel()
        displacement = vw.compute(
            sigmoid=sigmoid,
            pavement=pavement,
            load_pressure=load_pressure,
            load_radius=load_radius,
            sensor_location=sensor_location,
            time=time,
            timehistory=timehistory,
            dt=0.0002,
            num_ve_layer=Num_VE_Layer,
        )

        print(f"  ✓ Computation successful")
        print(f"  ✓ Displacement shape: {displacement.shape}")
        print(f"  ✓ Max displacement: {np.max(np.abs(displacement)):.6e}")

        return True
    except Exception as e:
        print(f"  ✗ Computation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    tests_passed = 0
    tests_total = 3

    if test_imports():
        tests_passed += 1

    if test_relaxation():
        tests_passed += 1

    if test_viscowave():
        tests_passed += 1

    print()
    print("=" * 60)
    print(f"Test Results: {tests_passed}/{tests_total} passed")
    print("=" * 60)

    if tests_passed == tests_total:
        print("\n✅ All tests passed! The macOS universal binaries are working correctly.")
        return 0
    else:
        print(f"\n❌ {tests_total - tests_passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
