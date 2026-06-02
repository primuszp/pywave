#!/usr/bin/env python3
"""
Relaxation_Sig_to_Prony Basic Example - Production Ready

This example demonstrates conversion of relaxation sigmoid parameters
to Prony series representation with proper error handling.
"""

import sys

import numpy as np
import matplotlib.pyplot as plt

from viscowave import ViscoWaveError, get_platform_info, __version__
from viscowave.api import RelaxationPronyModel


def main():
    """Convert sigmoid parameters to Prony series and display results."""
    print("=" * 70)
    print("Relaxation_Sig_to_Prony Example - Production Ready")
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
    # 1. Define Sigmoid Parameters
    # ========================================================================
    print("Step 1: Defining sigmoid parameters...")

    # Sigmoid parameters for relaxation modulus: [a, b, c, d]
    # E(t) = 10^(a + b / (1 + exp(-(log(t) - c) / d)))
    sigmoid = np.array([
        [3.123, 3.446, -0.128, 0.554],  # Sigmoid set 1
    ], dtype=np.float64)

    print(f"  - Number of sigmoid sets: {len(sigmoid)}")
    print(f"  - Sigmoid parameters:")
    for i, params in enumerate(sigmoid):
        print(f"    Set {i+1}: a={params[0]:.3f}, b={params[1]:.3f}, c={params[2]:.3f}, d={params[3]:.3f}")
    print()

    # ========================================================================
    # 2. Convert to Prony Series
    # ========================================================================
    print("Step 2: Converting to Prony series...")

    try:
        model = RelaxationPronyModel()
        result = model.compute(sigmoid)

        print(f"  ✓ Conversion complete!")
        print(f"  - Prony elements: {result.num_prony_elements}")
        print(f"  - Output shape: {result.matrix.shape}")
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
    print("Step 3: Analyzing Prony series coefficients...")

    prony_matrix = result.matrix  # Shape: (15, num_sigmoid+1)

    # First column is time constants, rest are moduli for each sigmoid set
    time_constants = prony_matrix[:, 0]
    moduli = prony_matrix[:, 1:]  # Moduli for each sigmoid set

    print(f"  Prony Series Components:")
    print(f"  {'Index':<8} {'Time τ (s)':<15} {'Modulus E':<15}")
    print(f"  {'-' * 40}")
    for i in range(result.num_prony_elements):
        print(f"  {i+1:<8} {time_constants[i]:<15.6e} {moduli[i, 0]:<15.6f}")

    print()
    print(f"  Statistics:")
    print(f"  - Time range: {time_constants.min():.2e} to {time_constants.max():.2e} s")
    print(f"  - Modulus range: {moduli.min():.2f} to {moduli.max():.2f}")
    print(f"  - Total E∞: {np.sum(moduli[:, 0]):.2f}")
    print()

    # ========================================================================
    # 4. Plot Results
    # ========================================================================
    print("Step 4: Plotting Prony series...")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Plot 1: Prony moduli vs time constants
    ax1.stem(time_constants, moduli[:, 0], basefmt=' ')
    ax1.set_xlabel('Time Constant τ (s)', fontsize=11)
    ax1.set_ylabel('Prony Modulus E (psi)', fontsize=11)
    ax1.set_title('Prony Series: Moduli vs Time Constants', fontsize=12, fontweight='bold')
    ax1.set_xscale('log')
    ax1.grid(True, alpha=0.3)

    # Plot 2: Relaxation modulus reconstruction
    time_eval = np.logspace(-6, 2, 200)  # Evaluation times

    # Reconstruct E(t) from Prony series
    # E(t) = E∞ + Σ Ei * exp(-t/τi)
    E_infinity = moduli[0, 0]  # Assuming first term is E∞
    E_t = np.ones_like(time_eval) * E_infinity

    for i in range(1, result.num_prony_elements):
        tau = time_constants[i]
        E_i = moduli[i, 0]
        E_t += E_i * np.exp(-time_eval / tau)

    ax2.semilogx(time_eval, E_t, 'b-', linewidth=2)
    ax2.set_xlabel('Time (s)', fontsize=11)
    ax2.set_ylabel('Relaxation Modulus E(t) (psi)', fontsize=11)
    ax2.set_title('Reconstructed Relaxation Modulus', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save figure
    from pathlib import Path
    output_path = Path(__file__).parent / "relaxation_results.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  ✓ Figure saved: {output_path}")

    plt.show()

    print()
    print("=" * 70)
    print("Conversion completed successfully! ✓")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
