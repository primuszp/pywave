# -*- coding: utf-8 -*-
"""Internal ctypes utilities for viscowave."""
from __future__ import annotations

import ctypes as ct
from typing import Sequence

import numpy as np

from .exceptions import ViscoWaveError

__all__ = [
    "c_int",
    "c_double",
    "as_c_double_array",
    "check_ok",
]



c_int = ct.c_int
c_double = ct.c_double


def as_c_double_array(seq: Sequence) -> ct.POINTER(c_double):
    arr = np.asarray(seq, dtype=np.float64)
    if not arr.flags["C_CONTIGUOUS"]:
        arr = np.ascontiguousarray(arr, dtype=np.float64)
    return arr.ctypes.data_as(ct.POINTER(c_double))


def check_ok(ret: int, where: str) -> None:
    code = int(ret)
    if code != 0:
        raise ViscoWaveError(where, code)
