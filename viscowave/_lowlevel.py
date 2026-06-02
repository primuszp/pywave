# -*- coding: utf-8 -*-
"""
Low-level ctypes bindings for ViscoWave and Relaxation_Sig_to_Prony.

Note: return code 0 = success.
"""
from __future__ import annotations

import ctypes as ct

from ._ctypes_utils import c_int, c_double
from ._dylib import load_viscowave_lib, load_relaxation_lib

_lib_vw = load_viscowave_lib()
_lib_rel = load_relaxation_lib()


def _define_func(lib, name: str, restype, argtypes):
    func = getattr(lib, name)
    func.restype = restype
    func.argtypes = argtypes
    return func


visco_wave = _define_func(
    _lib_vw,
    "ViscoWave",
    c_int,
    [
        ct.POINTER(c_double),  # displacement
        ct.POINTER(c_double),  # Sigmoid
        ct.POINTER(c_double),  # Pavement
        c_double,              # Load_Pressure
        c_double,              # Load_Radius
        ct.POINTER(c_double),  # Sensor_Location
        ct.POINTER(c_double),  # Time
        ct.POINTER(c_double),  # Timehistory
        c_double,              # dt
        c_int,                 # num_sigmoid_sets
        c_int,                 # Num_Pavt_Layers
        c_int,                 # Num_Sensors
        c_int,                 # Num_Time
        c_int,                 # Num_VE_Layer
    ],
)


relaxation_sig_to_prony = _define_func(
    _lib_rel,
    "Relaxation_Sig_to_Prony",
    c_int,
    [
        ct.POINTER(c_double),
        ct.POINTER(c_double),
        c_int,
    ],
)


__all__ = ["visco_wave", "relaxation_sig_to_prony"]
