# -*- coding: utf-8 -*-
"""High-level API for ViscoWave and Relaxation_Sig_to_Prony."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple

import ctypes as ct

import numpy as np

from ._ctypes_utils import check_ok
from . import units as unit_utils
from ._lowlevel import relaxation_sig_to_prony, visco_wave

__all__ = [
    "convert_pressure_and_radius",
    "convert_layer_parameters",
    "update_sigmoidal_coefficients",
    "half_sine_values",
    "PronyResult",
    "RelaxationPronyModel",
    "ViscoWaveModel",
]


def convert_pressure_and_radius(pressure_psi: float, radius_in: float) -> Tuple[float, float]:
    """Convert load pressure (psi) and radius (in) to internal psf and ft."""
    return unit_utils.convert_pressure_and_radius_imperial(pressure_psi, radius_in)


def convert_layer_parameters(layerpara: np.ndarray) -> np.ndarray:
    """
    Convert pavement layer parameters to internal units.

    Expects array of shape (N, 5): [E, nu, rho, h, damping] with Imperial inputs:
      - E: psi
      - rho: pcf (lb/ft^3)
      - h: inches
      - damping: percent
    """
    return unit_utils.convert_layer_parameters_imperial(layerpara)


def update_sigmoidal_coefficients(sigmoid: np.ndarray, layerpara: np.ndarray) -> np.ndarray:
    """
    Apply unit-conversion correction to sigmoid a-coefficient for viscoelastic layers.

    ViscoWave expects the sigmoid a-coefficient in terms of shear modulus G (psf),
    not Young's modulus E (psi). This function adjusts a0 for each viscoelastic
    layer (those with G=0 in layerpara after unit conversion).

    Viscoelastic layers must appear first in layerpara (they have G=0 at index [:, 0]).
    """
    sigmoid = np.array(sigmoid, dtype=np.float64, copy=True)
    if sigmoid.ndim != 2 or sigmoid.shape[1] != 4:
        raise ValueError("sigmoid must be shape (N,4).")
    num_ve = int(np.sum(layerpara[:, 0] == 0))
    for j in range(num_ve):
        sigmoid[j, 0] += np.log10(144.0 / (2.0 * (1.0 + layerpara[j, 1])))
    return sigmoid


def half_sine_values(start: float, end: float, amplitude: float, time: Sequence[float]) -> np.ndarray:
    """Generate half-sine values on a time vector."""
    time = np.asarray(time, dtype=np.float64)
    values = np.zeros_like(time)
    mask = (time >= start) & (time <= end)
    values[mask] = amplitude * np.sin(np.pi / (end - start) * (time[mask] - start))
    return values


@dataclass(frozen=True)
class PronyResult:
    """Result container for relaxation_sig_to_prony."""

    flat: np.ndarray
    matrix: np.ndarray
    num_sigmoid: int
    num_prony_elements: int


class RelaxationPronyModel:
    """High-level wrapper for relaxation_sig_to_prony."""

    def compute(self, sigmoid: np.ndarray) -> PronyResult:
        sigmoid = np.asarray(sigmoid, dtype=np.float64)
        if sigmoid.ndim == 2 and sigmoid.shape[1] == 4:
            num_sigmoid = int(sigmoid.shape[0])
            sigmoid_flat = np.ascontiguousarray(sigmoid.reshape(-1), dtype=np.float64)
        elif sigmoid.ndim == 1 and sigmoid.size % 4 == 0:
            num_sigmoid = int(sigmoid.size // 4)
            sigmoid_flat = np.ascontiguousarray(sigmoid, dtype=np.float64)
        else:
            raise ValueError("sigmoid must be shape (N,4) or flat length 4*N.")

        num_prony_elements = 15
        flat = np.zeros((num_sigmoid + 1) * num_prony_elements, dtype=np.float64)

        rc = relaxation_sig_to_prony(
            flat.ctypes.data_as(ct.POINTER(ct.c_double)),
            sigmoid_flat.ctypes.data_as(ct.POINTER(ct.c_double)),
            int(num_sigmoid),
        )
        check_ok(rc, "relaxation_sig_to_prony")

        # Stored as prony-major blocks of size (num_sigmoid + 1)
        matrix = flat.reshape((num_prony_elements, num_sigmoid + 1))
        return PronyResult(flat=flat, matrix=matrix, num_sigmoid=num_sigmoid, num_prony_elements=num_prony_elements)


class ViscoWaveModel:
    """High-level wrapper for ViscoWave."""

    def compute(
        self,
        sigmoid: np.ndarray,
        pavement: np.ndarray,
        load_pressure: float,
        load_radius: float,
        sensor_location: np.ndarray,
        time: np.ndarray,
        timehistory: np.ndarray,
        dt: float,
        num_ve_layer: int,
    ) -> np.ndarray:
        sigmoid = np.asarray(sigmoid, dtype=np.float64)
        if sigmoid.ndim == 2 and sigmoid.shape[1] == 4:
            num_sigmoid_sets = int(sigmoid.shape[0])
            sigmoid_flat = np.ascontiguousarray(sigmoid.reshape(-1), dtype=np.float64)
        elif sigmoid.ndim == 1 and sigmoid.size % 4 == 0:
            num_sigmoid_sets = int(sigmoid.size // 4)
            sigmoid_flat = np.ascontiguousarray(sigmoid, dtype=np.float64)
        else:
            raise ValueError("sigmoid must be shape (N,4) or flat length 4*N.")

        if num_sigmoid_sets != num_ve_layer:
            raise ValueError(f"num_ve_layer ({num_ve_layer}) must match sigmoid sets ({num_sigmoid_sets}).")

        pavement = np.ascontiguousarray(pavement, dtype=np.float64)
        if pavement.ndim != 2 or pavement.shape[1] != 5:
            raise ValueError("pavement must be shape (Num_Pavt_Layers, 5).")
        num_pavt_layers = int(pavement.shape[0])

        sensor_location = np.ascontiguousarray(sensor_location, dtype=np.float64)
        time = np.ascontiguousarray(time, dtype=np.float64)
        timehistory = np.ascontiguousarray(timehistory, dtype=np.float64)
        if time.shape != timehistory.shape:
            raise ValueError("time and timehistory must have the same shape.")

        num_sensors = int(sensor_location.size)
        num_time = int(time.size)
        displacement = np.zeros(num_sensors * num_time, dtype=np.float64)

        rc = visco_wave(
            displacement.ctypes.data_as(ct.POINTER(ct.c_double)),
            sigmoid_flat.ctypes.data_as(ct.POINTER(ct.c_double)),
            pavement.ctypes.data_as(ct.POINTER(ct.c_double)),
            float(load_pressure),
            float(load_radius),
            sensor_location.ctypes.data_as(ct.POINTER(ct.c_double)),
            time.ctypes.data_as(ct.POINTER(ct.c_double)),
            timehistory.ctypes.data_as(ct.POINTER(ct.c_double)),
            float(dt),
            int(num_sigmoid_sets),
            int(num_pavt_layers),
            int(num_sensors),
            int(num_time),
            int(num_ve_layer),
        )
        check_ok(rc, "visco_wave")

        return displacement.reshape((num_sensors, num_time))
