# -*- coding: utf-8 -*-
"""
Backcalculation of pavement layer moduli from FWD deflection data.

Backcalculation finds the set of layer moduli that minimises the difference
between measured FWD deflections and the deflections computed by the ViscoWave
forward model.

The optimisation uses L-BFGS-B (bounded quasi-Newton) from scipy.  Moduli are
optimised in log-space to enforce positivity and improve numerical conditioning.

Requires ``scipy`` (optional dependency).  Install with::

    pip install viscowave[analysis]

Typical usage::

    from viscowave.backcalc import backcalculate, BackcalcLayer

    layers = [
        BackcalcLayer(modulus_initial=3000, bounds=(500, 30000)),   # AC (MPa)
        BackcalcLayer(modulus_initial=200,  bounds=(50,  2000)),    # Base (MPa)
        BackcalcLayer(modulus_initial=60,   bounds=(10,  500)),     # Subgrade (MPa)
    ]

    result = backcalculate(
        measured_deflections_mm=[0.800, 0.510, 0.350, 0.245, 0.175, 0.118],
        sensor_offsets_mm=[0, 200, 300, 450, 600, 900],
        layer_structure=layers,
        load_kN=40.0,
        load_radius_mm=150.0,
    )
    print(result.moduli_MPa)       # [E_AC, E_base, E_sg] in MPa
    print(result.rmse_mm)          # RMS error between measured/computed deflections
    print(result.converged)        # True if optimisation converged
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

import numpy as np

__all__ = [
    "BackcalcLayer",
    "BackcalcResult",
    "backcalculate",
    "backcalculate_batch",
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class BackcalcLayer:
    """
    Layer specification for backcalculation.

    Args:
        modulus_initial:  Starting guess for Young's modulus (MPa).
        bounds:           (min, max) modulus bounds in MPa.
        poisson_ratio:    Poisson's ratio (default inferred by layer order:
                          0.35 AC, 0.40 base, 0.45 subgrade).
        density:          Density in kg/m³ (default 2000).
        thickness:        Layer thickness in m.  The last layer is assumed
                          semi-infinite (thickness is set to 10 m internally).
        fixed:            If True, modulus is held constant at modulus_initial.
        label:            Descriptive name for reporting.

    Example::

        ac_layer = BackcalcLayer(
            modulus_initial=3000,
            bounds=(500, 30000),
            thickness=0.10,
            label="Asphalt Concrete",
        )
    """

    modulus_initial: float
    bounds: Tuple[float, float] = (1.0, 1e6)
    poisson_ratio: float = 0.40
    density: float = 2000.0
    thickness: float = 1.0
    fixed: bool = False
    label: str = ""

    def __post_init__(self) -> None:
        if self.modulus_initial <= 0:
            raise ValueError("modulus_initial must be positive")
        lo, hi = self.bounds
        if lo <= 0 or hi <= 0 or lo >= hi:
            raise ValueError(f"bounds must be (positive_min, max) with min < max, got {self.bounds}")


@dataclass
class BackcalcResult:
    """
    Result of a backcalculation run.

    Attributes:
        moduli_MPa:           Best-fit layer moduli in MPa.
        moduli_GPa:           Best-fit layer moduli in GPa (for reference).
        moduli_psi:           Best-fit layer moduli in psi (imperial).
        computed_deflections_mm: Deflections from forward model at best-fit moduli.
        measured_deflections_mm: Input measured deflections.
        rmse_mm:              Root-mean-squared error between measured and computed.
        relative_error_pct:   Per-sensor relative error (%).
        converged:            True if the optimiser reported convergence.
        iterations:           Number of optimiser iterations.
        message:              Optimiser status message.
        seed_moduli_MPa:      Initial moduli used to start optimisation.
    """

    moduli_MPa: np.ndarray
    computed_deflections_mm: np.ndarray
    measured_deflections_mm: np.ndarray
    rmse_mm: float
    relative_error_pct: np.ndarray
    converged: bool
    iterations: int = 0
    message: str = ""
    seed_moduli_MPa: Optional[np.ndarray] = None

    @property
    def moduli_GPa(self) -> np.ndarray:
        return self.moduli_MPa / 1000.0

    @property
    def moduli_psi(self) -> np.ndarray:
        return self.moduli_MPa * 145.038

    def __repr__(self) -> str:
        mods = ", ".join(f"{e:.0f}" for e in self.moduli_MPa)
        return (
            f"BackcalcResult(moduli=[{mods}] MPa, "
            f"RMSE={self.rmse_mm:.4f} mm, converged={self.converged})"
        )


# ---------------------------------------------------------------------------
# Main backcalculation function
# ---------------------------------------------------------------------------


def backcalculate(
    measured_deflections_mm: Sequence[float],
    sensor_offsets_mm: Sequence[float],
    layer_structure: Sequence[BackcalcLayer],
    load_kN: float,
    load_radius_mm: float = 150.0,
    time_duration: float = 0.06,
    time_steps: int = 300,
    load_start: float = 0.005,
    load_end: float = 0.030,
    method: str = "L-BFGS-B",
    tol: float = 1e-6,
    max_iter: int = 500,
    use_peak: bool = True,
) -> BackcalcResult:
    """
    Backcalculate layer moduli from measured FWD peak deflections.

    The optimisation minimises the sum of squared relative errors between
    measured and ViscoWave-computed deflections:

        objective = sum_i [ (D_meas_i - D_comp_i) / D_meas_i ]^2

    Moduli are parameterised in log10-space so that the solver sees a
    well-conditioned unconstrained problem, with bounds enforced via
    variable transformation.

    Args:
        measured_deflections_mm: Measured FWD peak deflections (mm).
        sensor_offsets_mm:       Sensor offsets from load centre (mm).
        layer_structure:         List of BackcalcLayer objects.  The last layer
                                 is treated as semi-infinite (thickness = 10 m).
        load_kN:                 Peak impact load (kN).
        load_radius_mm:          Load plate radius (mm).
        time_duration:           Analysis duration (s, default 0.06).
        time_steps:              Number of time steps (default 300).
        load_start:              Load pulse start time (s, default 0.005).
        load_end:                Load pulse end time (s, default 0.030).
        method:                  scipy.optimize method (default 'L-BFGS-B').
        tol:                     Optimiser tolerance.
        max_iter:                Maximum iterations.
        use_peak:                If True, compare peak deflection from time history;
                                 if False, compare deflection at the load peak time.

    Returns:
        BackcalcResult

    Raises:
        ImportError: If scipy is not installed.
        ValueError:  If inputs are inconsistent.

    Example::

        layers = [
            BackcalcLayer(3000, (500, 30000), poisson_ratio=0.35, thickness=0.10),
            BackcalcLayer(200,  (50, 2000),   poisson_ratio=0.40, thickness=0.30),
            BackcalcLayer(60,   (10, 500),    poisson_ratio=0.45, thickness=10.0),
        ]
        result = backcalculate(
            measured_deflections_mm=[0.800, 0.510, 0.350, 0.245, 0.175, 0.118],
            sensor_offsets_mm=[0, 200, 300, 450, 600, 900],
            layer_structure=layers,
            load_kN=40.0,
        )
    """
    try:
        from scipy.optimize import minimize  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "scipy is required for backcalculation. "
            "Install it with: pip install viscowave[analysis]"
        ) from exc

    from .highlevel import analyze

    d_meas = np.asarray(measured_deflections_mm, dtype=np.float64)
    offsets_m = np.asarray(sensor_offsets_mm, dtype=np.float64) / 1000.0  # mm → m

    if len(d_meas) != len(offsets_m):
        raise ValueError("measured_deflections_mm and sensor_offsets_mm must have equal length")
    if len(layer_structure) < 2:
        raise ValueError("At least 2 layers are required for backcalculation")
    if len(layer_structure) > 6:
        raise ValueError("ViscoWave supports a maximum of 6 layers")

    # Identify free (non-fixed) layers
    free_idx = [i for i, lyr in enumerate(layer_structure) if not lyr.fixed]
    if not free_idx:
        raise ValueError("All layers are fixed; nothing to optimise")

    # Collect bounds for free layers in log10-space
    lo_log = np.array([np.log10(layer_structure[i].bounds[0]) for i in free_idx])
    hi_log = np.array([np.log10(layer_structure[i].bounds[1]) for i in free_idx])
    x0_log = np.array([np.log10(layer_structure[i].modulus_initial) for i in free_idx])
    x0_log = np.clip(x0_log, lo_log, hi_log)

    bounds_scipy = list(zip(lo_log, hi_log))

    # Convert load
    load_pressure_Pa = (load_kN * 1000.0) / (np.pi * (load_radius_mm / 1000.0) ** 2)
    load_radius_m = load_radius_mm / 1000.0

    # Make semi-infinite last layer
    layers_copy = list(layer_structure)
    layers_copy[-1] = BackcalcLayer(
        modulus_initial=layers_copy[-1].modulus_initial,
        bounds=layers_copy[-1].bounds,
        poisson_ratio=layers_copy[-1].poisson_ratio,
        density=layers_copy[-1].density,
        thickness=10.0,
        fixed=layers_copy[-1].fixed,
        label=layers_copy[-1].label,
    )

    call_count = [0]

    def objective(x_log: np.ndarray) -> float:
        call_count[0] += 1
        # Reconstruct layer moduli
        current_moduli_MPa = np.array(
            [layer_structure[i].modulus_initial for i in range(len(layer_structure))],
            dtype=np.float64,
        )
        for k, i in enumerate(free_idx):
            current_moduli_MPa[i] = 10.0 ** x_log[k]

        # Build layer tuples: (E_Pa, nu, rho, h_m)
        layer_tuples = []
        for j, lyr in enumerate(layers_copy):
            E_Pa = current_moduli_MPa[j] * 1e6
            layer_tuples.append((E_Pa, lyr.poisson_ratio, lyr.density, lyr.thickness))

        try:
            res = analyze(
                layers=layer_tuples,
                load_pressure=load_pressure_Pa,
                load_radius=load_radius_m,
                sensor_locations=list(offsets_m),
                unit_system="SI",
                time_duration=time_duration,
                time_steps=time_steps,
                load_start=load_start,
                load_end=load_end,
            )
        except Exception:
            return 1e10

        if use_peak:
            d_comp_ft = np.max(np.abs(res.displacement), axis=1)
        else:
            t_peak_idx = np.argmin(np.abs(res.time - (load_start + load_end) / 2.0))
            d_comp_ft = np.abs(res.displacement[:, t_peak_idx])

        d_comp_mm = d_comp_ft * 304.8  # ft → mm (1 ft = 304.8 mm)
        # Clip to avoid division by zero
        d_meas_safe = np.where(d_meas > 0, d_meas, 1e-6)
        rel_err = (d_meas_safe - d_comp_mm) / d_meas_safe
        return float(np.sum(rel_err ** 2))

    opt = minimize(
        objective,
        x0_log,
        method=method,
        bounds=bounds_scipy,
        options={"maxiter": max_iter, "ftol": tol},
    )

    # Reconstruct best-fit moduli
    best_moduli_MPa = np.array(
        [layer_structure[i].modulus_initial for i in range(len(layer_structure))],
        dtype=np.float64,
    )
    for k, i in enumerate(free_idx):
        best_moduli_MPa[i] = 10.0 ** opt.x[k]

    # Compute forward model at best-fit
    layer_tuples_best = []
    for j, lyr in enumerate(layers_copy):
        E_Pa = best_moduli_MPa[j] * 1e6
        layer_tuples_best.append((E_Pa, lyr.poisson_ratio, lyr.density, lyr.thickness))

    try:
        res_best = analyze(
            layers=layer_tuples_best,
            load_pressure=load_pressure_Pa,
            load_radius=load_radius_m,
            sensor_locations=list(offsets_m),
            unit_system="SI",
            time_duration=time_duration,
            time_steps=time_steps,
            load_start=load_start,
            load_end=load_end,
        )
        if use_peak:
            d_comp_ft = np.max(np.abs(res_best.displacement), axis=1)
        else:
            t_peak_idx = np.argmin(np.abs(res_best.time - (load_start + load_end) / 2.0))
            d_comp_ft = np.abs(res_best.displacement[:, t_peak_idx])
        d_comp_mm = d_comp_ft * 304.8  # ft → mm
    except Exception:
        d_comp_mm = np.full_like(d_meas, np.nan)

    rmse = float(np.sqrt(np.mean((d_meas - d_comp_mm) ** 2)))
    d_meas_safe = np.where(d_meas > 0, d_meas, 1e-6)
    rel_err_pct = (d_meas - d_comp_mm) / d_meas_safe * 100.0

    return BackcalcResult(
        moduli_MPa=best_moduli_MPa,
        computed_deflections_mm=d_comp_mm,
        measured_deflections_mm=d_meas,
        rmse_mm=rmse,
        relative_error_pct=rel_err_pct,
        converged=opt.success,
        iterations=opt.nit,
        message=opt.message,
        seed_moduli_MPa=np.array(
            [layer_structure[i].modulus_initial for i in range(len(layer_structure))],
            dtype=np.float64,
        ),
    )


def backcalculate_batch(
    fwd_dataset,
    layer_structure: Sequence[BackcalcLayer],
    load_radius_mm: float = 150.0,
    drop_number: int = 2,
    **kwargs,
) -> List[Tuple[str, Optional[BackcalcResult]]]:
    """
    Run backcalculation for all stations in a FWDDataset.

    Args:
        fwd_dataset:     FWDDataset object (from fwd_io module).
        layer_structure: List of BackcalcLayer objects.
        load_radius_mm:  Load plate radius in mm.
        drop_number:     Which drop to use per station (default 2).
        **kwargs:        Additional keyword arguments passed to :func:`backcalculate`.

    Returns:
        List of (station_id, BackcalcResult | None) tuples.
        None indicates a failed/skipped analysis for that station.

    Example::

        from viscowave.fwd_io import read_jils
        from viscowave.backcalc import backcalculate_batch, BackcalcLayer

        ds = read_jils("survey.DAT")
        layers = [
            BackcalcLayer(3000, (500, 30000), poisson_ratio=0.35, thickness=0.10),
            BackcalcLayer(200,  (50, 2000),   poisson_ratio=0.40, thickness=0.30),
            BackcalcLayer(60,   (10, 500),    poisson_ratio=0.45, thickness=10.0),
        ]
        results = backcalculate_batch(ds, layers)
        for station, res in results:
            if res:
                print(station, res.moduli_MPa)
    """
    results = []
    representative = fwd_dataset.representative_drops(drop_number)
    for drop in representative:
        try:
            res = backcalculate(
                measured_deflections_mm=drop.deflections_mm.tolist(),
                sensor_offsets_mm=drop.sensor_offsets_mm.tolist(),
                layer_structure=layer_structure,
                load_kN=drop.load_kN,
                load_radius_mm=load_radius_mm,
                **kwargs,
            )
            results.append((drop.station, res))
        except Exception as exc:
            results.append((drop.station, None))
    return results
