# -*- coding: utf-8 -*-
"""
FWD (Falling Weight Deflectometer) data file readers.

Supported formats:
  - JILS  : *.DAT + *.THY file pairs (JILS FWD devices)
  - Dynatest: Access *.mdb/*.accdb databases and *.FWD text files
  - Kuab  : UTF-16 *.fwd peak files plus optional *.HST time histories

All readers return FWDDataset objects with consistent field names and SI units
(deflections in mm, load in kN, offsets in mm).

Typical usage::

    from viscowave.fwd_io import read_fwd, read_jils, read_kuab_folder

    ds = read_jils("survey.DAT", sensor_offsets_mm=[0, 200, 300, 450, 600, 900, 1200, 1500, 1800])
    for drop in ds.drops:
        print(drop.station, drop.deflections_mm)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

__all__ = [
    "FWDDrop",
    "FWDTimeHistory",
    "FWDDataset",
    "read_fwd",
    "read_jils",
    "read_jils_thy",
    "read_dynatest",
    "read_dynatest_access",
    "read_kuab",
    "read_kuab_folder",
]

_DEFAULT_OFFSETS_MM = np.array([0, 200, 300, 450, 600, 900, 1200, 1500, 1800], dtype=np.float64)
_MILS_TO_MM = 0.0254
_LB_TO_KN = 0.0044482216152605
_KIP_TO_KN = 4.44822

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class FWDTimeHistory:
    """
    Time history record for a single FWD drop (from a JILS *.THY file).

    Attributes:
        time_ms:          Time vector in milliseconds.
        force_kN:         Force time history in kilonewtons.
        displacements_mm: Displacement time histories, shape (n_sensors, n_samples), mm.
        n_samples:        Number of time samples.
        station:          Station identifier.
        drop_number:      Drop/energy-level number (1-based).
    """

    time_ms: np.ndarray
    force_kN: np.ndarray
    displacements_mm: np.ndarray
    station: str = ""
    drop_number: int = 1

    @property
    def n_samples(self) -> int:
        return len(self.time_ms)

    @property
    def peak_force_kN(self) -> float:
        """Peak force in kN."""
        return float(np.max(self.force_kN))

    @property
    def peak_deflections_mm(self) -> np.ndarray:
        """Peak (maximum absolute) deflection per sensor in mm."""
        return np.max(np.abs(self.displacements_mm), axis=1)

    def __repr__(self) -> str:
        return (
            f"FWDTimeHistory(station={self.station!r}, drop={self.drop_number}, "
            f"samples={self.n_samples}, peak_force={self.peak_force_kN:.1f} kN)"
        )


@dataclass
class FWDDrop:
    """
    A single FWD drop (impact) record.

    Attributes:
        station:          Station identifier (string label or numeric)
        drop_number:      Drop sequence number within station (1-based)
        distance_m:       Distance along the road alignment in metres
        load_kN:          Peak impact load in kilonewtons
        load_radius_mm:   Equivalent circular load plate radius in mm (if known)
        deflections_mm:   Surface deflections at each sensor in mm (downward = positive)
        sensor_offsets_mm: Radial offsets of sensors from load centre in mm
        pavement_temp_C:  Pavement surface temperature in °C
        air_temp_C:       Air temperature in °C (None if unavailable)
        gps_lat:          GPS latitude (decimal degrees, None if unavailable)
        gps_lon:          GPS longitude (decimal degrees, None if unavailable)
        notes:            Free-text notes for the measurement point
    """

    station: str
    drop_number: int
    distance_m: float
    load_kN: float
    deflections_mm: np.ndarray
    sensor_offsets_mm: np.ndarray
    load_radius_mm: float = 150.0
    pavement_temp_C: Optional[float] = None
    air_temp_C: Optional[float] = None
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None
    notes: str = ""
    time_history: Optional[FWDTimeHistory] = None

    @property
    def num_sensors(self) -> int:
        return len(self.deflections_mm)

    @property
    def load_pressure_kPa(self) -> float:
        """Equivalent contact pressure in kPa (assumes circular plate, 1 kN/m² = 1 kPa)."""
        r_m = self.load_radius_mm / 1000.0
        area_m2 = np.pi * r_m ** 2
        return float(self.load_kN / area_m2)

    def __repr__(self) -> str:
        d_str = ", ".join(f"{d:.3f}" for d in self.deflections_mm)
        return (
            f"FWDDrop(station={self.station!r}, drop={self.drop_number}, "
            f"load={self.load_kN:.2f} kN, deflections=[{d_str}] mm)"
        )


@dataclass
class FWDDataset:
    """
    Collection of FWD drops loaded from a single survey file.

    Attributes:
        source_file:      Path to the original data file
        device_type:      FWD device type ('JILS', 'Dynatest', 'Kuab', 'Unknown')
        survey_date:      Survey date string (ISO format if possible)
        operator:         Operator name
        location:         Project/road location label
        drops:            All FWD drop records in the file
        sensor_offsets_mm: Default sensor offsets used in this file
    """

    source_file: Optional[str] = None
    device_type: str = "Unknown"
    survey_date: str = ""
    operator: str = ""
    location: str = ""
    drops: List[FWDDrop] = field(default_factory=list)
    sensor_offsets_mm: Optional[np.ndarray] = None

    @property
    def num_drops(self) -> int:
        return len(self.drops)

    @property
    def num_stations(self) -> int:
        return len({d.station for d in self.drops})

    @property
    def stations(self) -> List[str]:
        seen = []
        for d in self.drops:
            if d.station not in seen:
                seen.append(d.station)
        return seen

    def get_station_drops(self, station: str) -> List[FWDDrop]:
        return [d for d in self.drops if d.station == station]

    def representative_drops(self, drop_number: int = 2) -> List[FWDDrop]:
        """Return one representative drop per station (default: drop 2, skipping seating drop)."""
        result = []
        for s in self.stations:
            candidates = [d for d in self.get_station_drops(s) if d.drop_number == drop_number]
            if not candidates:
                candidates = self.get_station_drops(s)
            if candidates:
                result.append(candidates[0])
        return result

    def deflection_matrix(self, drop_number: int = 2) -> np.ndarray:
        """
        Return deflections as a 2D array (stations x sensors) for a given drop number.

        Rows correspond to `stations`, columns to sensor indices.
        """
        reps = self.representative_drops(drop_number)
        if not reps:
            return np.empty((0, 0))
        n_sensors = max(d.num_sensors for d in reps)
        out = np.full((len(reps), n_sensors), np.nan)
        for i, drop in enumerate(reps):
            out[i, : drop.num_sensors] = drop.deflections_mm
        return out

    def load_vector(self, drop_number: int = 2) -> np.ndarray:
        """Return representative peak loads in kN, one value per station."""
        return np.asarray([d.load_kN for d in self.representative_drops(drop_number)], dtype=np.float64)

    def to_records(self, drop_number: int | None = None) -> List[dict]:
        """
        Convert drops to plain Python dictionaries.

        Args:
            drop_number: If given, include only that drop number.  If None, include
                         every parsed drop.
        """
        rows = []
        selected = self.drops if drop_number is None else [d for d in self.drops if d.drop_number == drop_number]
        for drop in selected:
            row = {
                "station": drop.station,
                "drop_number": drop.drop_number,
                "distance_m": drop.distance_m,
                "load_kN": drop.load_kN,
                "load_radius_mm": drop.load_radius_mm,
                "pavement_temp_C": drop.pavement_temp_C,
                "air_temp_C": drop.air_temp_C,
                "gps_lat": drop.gps_lat,
                "gps_lon": drop.gps_lon,
                "notes": drop.notes,
            }
            for i, offset in enumerate(drop.sensor_offsets_mm):
                row[f"D{int(round(float(offset)))}_mm"] = float(drop.deflections_mm[i])
            rows.append(row)
        return rows

    def to_dataframe(self, drop_number: int | None = None):
        """
        Return a pandas DataFrame of parsed FWD drops.

        pandas is optional; install with ``pip install viscowave[analysis]``.
        """
        try:
            import pandas as pd  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "pandas is required for FWDDataset.to_dataframe(). "
                "Install it with: pip install viscowave[analysis]"
            ) from exc
        return pd.DataFrame.from_records(self.to_records(drop_number=drop_number))

    def __repr__(self) -> str:
        return (
            f"FWDDataset(device={self.device_type!r}, "
            f"stations={self.num_stations}, drops={self.num_drops})"
        )


def read_fwd(
    file: str | Path,
    sensor_offsets_mm: Optional[Sequence[float]] = None,
    load_plate_radius_mm: float = 150.0,
    skip_seating: bool = False,
    **kwargs,
) -> FWDDataset:
    """
    Read an FWD measurement file with automatic format detection.

    Supported inputs:
      - JILS ``*.DAT`` with optional companion ``*.THY``
      - Dynatest Access databases ``*.mdb`` / ``*.accdb``
      - Dynatest ``*.FWD`` text files
      - Kuab UTF-16 ``*.fwd`` text files

    For ambiguous ``*.fwd`` files, a lightweight header/content heuristic is used.
    Pass the format-specific reader directly when you need strict control.
    """
    path = Path(file)
    if path.is_dir():
        return read_kuab_folder(
            path,
            sensor_offsets_mm=sensor_offsets_mm,
            load_plate_radius_mm=load_plate_radius_mm,
            skip_seating=skip_seating,
            **kwargs,
        )

    suffix = path.suffix.lower()
    common = {
        "sensor_offsets_mm": sensor_offsets_mm,
        "load_plate_radius_mm": load_plate_radius_mm,
        "skip_seating": skip_seating,
    }
    common.update(kwargs)

    if suffix == ".dat":
        return read_jils(path, **common)

    if suffix in {".mdb", ".accdb"}:
        return read_dynatest_access(path, **common)

    if suffix == ".fwd":
        try:
            head = "\n".join(_read_text_lines(path)[:40]).lower()
        except FileNotFoundError:
            raise
        except Exception as exc:
            raise IOError(f"Cannot read FWD file header: {exc}") from exc

        if "ikuab" in head:
            return read_kuab(path, **common)
        if any(marker in head for marker in ("dynatest", "elmod", "geophone", "geoph")):
            return read_dynatest(path, **common)
        if any(marker in head for marker in ("kuab", "sensors", "operator:")):
            return read_kuab(path, **common)

        # Dynatest text records are the most common uppercase/lowercase .FWD export.
        return read_dynatest(path, **common)

    raise ValueError(
        f"Unsupported FWD file extension {path.suffix!r}. "
        "Use read_jils(), read_dynatest(), or read_kuab() for custom formats."
    )


def _float_or_nan(value) -> float:
    if value is None or value == "":
        return np.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def _first_present(row: dict, *names: str, default=None):
    lower_map = {str(k).lower(): v for k, v in row.items()}
    for name in names:
        if name in row:
            return row[name]
        value = lower_map.get(name.lower())
        if value is not None:
            return value
    return default


def _standard_time_seconds(duration: float = 0.0598, dt: float = 0.0002) -> np.ndarray:
    count = int(round(duration / dt)) + 1
    return np.linspace(0.0, duration, count, dtype=np.float64)


def _resample_columns(
    time_s: Sequence[float],
    force: Sequence[float],
    displacements: Sequence[Sequence[float]],
    *,
    station: str,
    drop_number: int,
    force_scale: float,
    displacement_scale: float,
    target_time_s: Optional[np.ndarray] = None,
) -> FWDTimeHistory:
    source_t = np.asarray(time_s, dtype=np.float64)
    order = np.argsort(source_t)
    source_t = source_t[order]
    target_t = _standard_time_seconds() if target_time_s is None else np.asarray(target_time_s, dtype=np.float64)

    force_arr = np.asarray(force, dtype=np.float64)[order]
    force_out = np.interp(target_t, source_t, force_arr, left=force_arr[0], right=force_arr[-1]) * force_scale

    disp_arr = np.asarray(displacements, dtype=np.float64)
    if disp_arr.ndim == 1:
        disp_arr = disp_arr.reshape(1, -1)
    disp_arr = disp_arr[:, order]
    disp_out = np.vstack(
        [
            np.interp(target_t, source_t, row, left=row[0], right=row[-1])
            for row in disp_arr
        ]
    ) * displacement_scale

    return FWDTimeHistory(
        time_ms=target_t * 1000.0,
        force_kN=force_out,
        displacements_mm=disp_out,
        station=station,
        drop_number=drop_number,
    )


# ---------------------------------------------------------------------------
# JILS reader
# ---------------------------------------------------------------------------

# JILS DAT data line: station  drop  distance  drop_type  d1..d9  load  temp
_JILS_DATA_RE = re.compile(
    r"^\s*(\d+)\s+(\d+)\s+([\d.]+)\s+(\d+)"  # station drop dist type
    r"((?:\s+[\d.]+){9,11})"                   # 9-11 floats: d1-d9 [load [temp]]
    r"\s*$"
)
_JILS_GPS_RE = re.compile(
    r"Latitude\s*=\s*([\d.]+)\s*deg\s*([\d.]+)\s*([NS]).*"
    r"Longitude\s*=\s*([\d.]+)\s*deg\s*([\d.]+)\s*([EW])",
    re.IGNORECASE,
)


def read_jils(
    dat_file: str | Path,
    sensor_offsets_mm: Optional[Sequence[float]] = None,
    load_plate_radius_mm: float = 150.0,
    skip_seating: bool = False,
    load_thy: bool = True,
) -> FWDDataset:
    """
    Read a JILS FWD *.DAT file (and optionally its companion *.THY time history file).

    JILS deflections are stored in mils (0.001 inch); load in kips.
    This reader converts them to mm and kN.

    If a *.THY file with the same stem exists next to the *.DAT, it is loaded
    automatically and time histories are attached to each FWDDrop (set
    ``load_thy=False`` to suppress this).

    Args:
        dat_file:            Path to the *.DAT file.
        sensor_offsets_mm:   Radial sensor offsets in mm. If None, a default set
                             of nine standard offsets is used.
        load_plate_radius_mm: Load plate radius in mm (default 150 mm = 300 mm diameter).
        skip_seating:        If True, drop number 1 is excluded (seating drop).
        load_thy:            If True (default), auto-load the companion *.THY file.

    Returns:
        FWDDataset with all drops (and time histories if THY is available).

    Example::

        ds = read_jils("survey.DAT",
                       sensor_offsets_mm=[0, 200, 300, 450, 600, 900, 1200, 1500, 1800])
        for drop in ds.representative_drops():
            print(drop.station, drop.deflections_mm)
            if drop.time_history:
                print("  peak force:", drop.time_history.peak_force_kN, "kN")
    """
    dat_path = Path(dat_file)
    if not dat_path.exists():
        raise FileNotFoundError(f"JILS DAT file not found: {dat_path}")

    _default_offsets = np.array([0, 200, 300, 450, 600, 900, 1200, 1500, 1800], dtype=np.float64)
    offsets = np.asarray(sensor_offsets_mm, dtype=np.float64) if sensor_offsets_mm is not None else _default_offsets

    ds = FWDDataset(
        source_file=str(dat_path),
        device_type="JILS",
        sensor_offsets_mm=offsets,
    )

    try:
        with open(dat_path, encoding="latin-1") as fh:
            lines = fh.readlines()
    except Exception as exc:
        raise IOError(f"Cannot read JILS DAT file: {exc}") from exc

    _parse_jils_header(lines, ds)

    pending_gps: Optional[tuple] = None
    pending_note: str = ""
    current_gps: Optional[tuple] = None
    current_note: str = ""
    current_station: Optional[str] = None

    for line in lines:
        stripped = line.strip()

        # GPS annotation
        gps_m = _JILS_GPS_RE.search(stripped)
        if gps_m:
            pending_gps = _parse_jils_gps(gps_m)
            continue

        if stripped.lower().startswith("note:"):
            pending_note = stripped[5:].strip()
            continue

        # Data line
        dm = _JILS_DATA_RE.match(stripped)
        if not dm:
            continue

        station_id = dm.group(1)
        drop_num = int(dm.group(2))
        distance_ft = float(dm.group(3))
        values = [float(v) for v in dm.group(5).split()]

        if station_id != current_station:
            current_station = station_id
            current_gps = pending_gps
            current_note = pending_note
            pending_gps = None
            pending_note = ""

        if skip_seating and drop_num == 1:
            continue

        n = len(values)
        if n >= 11:
            deflections_mils = np.asarray(values[:9], dtype=np.float64)
            load_kips = values[9]
            temp_f = values[10]
        elif n == 10:
            deflections_mils = np.asarray(values[:9], dtype=np.float64)
            load_kips = values[9]
            temp_f = None
        else:
            deflections_mils = np.asarray(values[:n], dtype=np.float64)
            load_kips = np.nan
            temp_f = None

        deflections_mm = deflections_mils * 0.0254  # 1 mil = 0.0254 mm
        load_kN = load_kips * 4.44822  # kip -> kN
        distance_m = distance_ft * 0.3048  # ft -> m
        temp_c = (temp_f - 32) * 5.0 / 9.0 if temp_f is not None else None

        drop_offsets = offsets[: len(deflections_mm)]

        lat, lon = current_gps if current_gps else (None, None)

        drop = FWDDrop(
            station=station_id,
            drop_number=drop_num,
            distance_m=distance_m,
            load_kN=load_kN,
            deflections_mm=deflections_mm,
            sensor_offsets_mm=drop_offsets,
            load_radius_mm=load_plate_radius_mm,
            pavement_temp_C=temp_c,
            gps_lat=lat,
            gps_lon=lon,
            notes=current_note,
        )
        ds.drops.append(drop)

    # Auto-load companion THY file
    if load_thy:
        thy_path = dat_path.with_suffix(".THY")
        if not thy_path.exists():
            thy_path = dat_path.with_suffix(".thy")
        if thy_path.exists():
            try:
                _attach_thy_to_dataset(ds, thy_path)
            except Exception:
                pass  # THY loading is best-effort; don't fail the whole read

    return ds


def _attach_thy_to_dataset(ds: FWDDataset, thy_path: Path) -> None:
    """Parse a JILS THY file and attach time histories to matching drops in ds."""
    thy_records = _parse_jils_thy(thy_path)
    # Build lookup: (station, drop_number) -> FWDTimeHistory
    for drop in ds.drops:
        key = (drop.station, drop.drop_number)
        if key in thy_records:
            drop.time_history = thy_records[key]


def _parse_jils_header(lines: List[str], ds: FWDDataset) -> None:
    for line in lines[:20]:
        s = line.strip()
        if s.lower().startswith("date-time:"):
            ds.survey_date = s[10:].strip()
        elif s.lower().startswith("location:"):
            ds.location = s[9:].strip()
        elif s.lower().startswith("operator:"):
            ds.operator = s[9:].strip()


def _parse_jils_gps(m: re.Match) -> tuple:
    lat_d, lat_m_frac, lat_hemi = float(m.group(1)), float(m.group(2)), m.group(3)
    lon_d, lon_m_frac, lon_hemi = float(m.group(4)), float(m.group(5)), m.group(6)
    lat = lat_d + lat_m_frac / 60.0
    lon = lon_d + lon_m_frac / 60.0
    if lat_hemi.upper() == "S":
        lat = -lat
    if lon_hemi.upper() == "W":
        lon = -lon
    return lat, lon


# THY parsing helpers
_THY_STATION_RE = re.compile(
    r"Station:\s*(\S+)\s+Lane:\s*\S+\s+Milepost:\s*([\d.]+)", re.IGNORECASE
)
_THY_DROP_RE = re.compile(r"Drop\s*#\s*(\d+)", re.IGNORECASE)
_THY_DATA_RE = re.compile(
    r"^\s*([\d.]+)\s+([-\d.]+)((?:\s+[-\d.]+){1,9})\s*$"
)


def _parse_jils_thy(
    thy_path: Path,
) -> Dict[Tuple[str, int], FWDTimeHistory]:
    """
    Parse a JILS *.THY time history file.

    Returns a dict keyed by (station_id, drop_number) → FWDTimeHistory.

    Units in THY files:
      - Time:          milliseconds (ms)
      - Force:         kips  →  converted to kN (1 kip = 4.44822 kN)
      - Displacements: mils (0.001 inch)  →  converted to mm (1 mil = 0.0254 mm)
    """
    with open(thy_path, encoding="latin-1") as fh:
        lines = fh.readlines()

    records: Dict[Tuple[str, int], FWDTimeHistory] = {}

    current_station: str = ""
    current_drop: int = 1
    times: List[float] = []
    forces: List[float] = []
    disps: List[List[float]] = []
    in_data = False

    def _flush() -> None:
        if times and current_station:
            key = (current_station, current_drop)
            t_arr = np.asarray(times, dtype=np.float64)
            f_arr = np.asarray(forces, dtype=np.float64) * 4.44822  # kip → kN
            if disps:
                n_s = max(len(row) for row in disps)
                d_mat = np.full((n_s, len(times)), np.nan, dtype=np.float64)
                for col_idx, row in enumerate(disps):
                    for row_idx, val in enumerate(row):
                        d_mat[row_idx, col_idx] = val
                d_mat *= 0.0254  # mils → mm
            else:
                d_mat = np.empty((0, len(times)), dtype=np.float64)
            records[key] = FWDTimeHistory(
                time_ms=t_arr,
                force_kN=f_arr,
                displacements_mm=d_mat,
                station=current_station,
                drop_number=current_drop,
            )

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Station header
        sm = _THY_STATION_RE.search(stripped)
        if sm:
            _flush()
            times, forces, disps = [], [], []
            in_data = False
            current_station = sm.group(1)
            continue

        # Drop header
        dm = _THY_DROP_RE.search(stripped)
        if dm:
            _flush()
            times, forces, disps = [], [], []
            in_data = False
            current_drop = int(dm.group(1))
            continue

        # Skip column header and "Impact:" lines
        if stripped.lower().startswith(("time ", "impact:", "sensors:")):
            in_data = True
            continue

        if not in_data:
            continue

        # Data rows: time force d1 [d2 ... d9]
        tokens = stripped.split()
        if len(tokens) < 3:
            continue
        try:
            row_floats = [float(t) for t in tokens]
        except ValueError:
            in_data = False
            continue

        times.append(row_floats[0])
        forces.append(row_floats[1])
        disps.append(row_floats[2:])

    _flush()
    return records


def read_jils_thy(
    thy_file: str | Path,
) -> Dict[Tuple[str, int], FWDTimeHistory]:
    """
    Read a standalone JILS *.THY time history file.

    Returns a dictionary keyed by ``(station_id, drop_number)`` with
    :class:`FWDTimeHistory` values.  All values are converted to SI:
    time in ms, force in kN, displacements in mm.

    Args:
        thy_file: Path to the *.THY file.

    Returns:
        Dictionary of FWDTimeHistory objects.

    Example::

        from viscowave.fwd_io import read_jils_thy

        records = read_jils_thy("survey.THY")
        th = records[("1", 1)]
        print(th.peak_force_kN, "kN peak")
        print(th.peak_deflections_mm)
    """
    thy_path = Path(thy_file)
    if not thy_path.exists():
        raise FileNotFoundError(f"JILS THY file not found: {thy_path}")
    return _parse_jils_thy(thy_path)


# ---------------------------------------------------------------------------
# Dynatest reader
# ---------------------------------------------------------------------------

def read_dynatest_access(
    access_file: str | Path,
    sensor_offsets_mm: Optional[Sequence[float]] = None,
    load_plate_radius_mm: float = 150.0,
    skip_seating: bool = False,
    load_histories: bool = True,
) -> FWDDataset:
    """
    Read a Dynatest Access database exported by the ViscoWave V3 workflow.

    The original ViscoWave R script reads ``Drops``, ``Stations`` and
    ``Histories`` tables through ODBC.  This Python implementation follows the
    same table contract and converts the result to :class:`FWDDataset`.

    Expected native units in the database are the same as the R export:
    peak/time-history force in pounds, deflections in mils, and history time in
    milliseconds.  Values are converted to kN, mm, and ``FWDTimeHistory``.

    Requires ``pyodbc`` and a Microsoft Access ODBC driver.
    """
    db_path = Path(access_file)
    if not db_path.exists():
        raise FileNotFoundError(f"Dynatest Access file not found: {db_path}")

    try:
        import pyodbc  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "pyodbc and the Microsoft Access ODBC driver are required for "
            "read_dynatest_access(). Install pyodbc and retry."
        ) from exc

    def _rows(table: str) -> List[dict]:
        cursor = con.cursor()
        cursor.execute(f"SELECT * FROM [{table}]")
        columns = [c[0] for c in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    conn_str = (
        "DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        f"DBQ={db_path};"
    )
    try:
        con = pyodbc.connect(conn_str)
    except Exception as exc:
        raise IOError(f"Cannot open Dynatest Access database via ODBC: {exc}") from exc

    try:
        drops_rows = _rows("Drops")
        stations_rows = _rows("Stations")
        history_rows = _rows("Histories") if load_histories else []
    finally:
        con.close()

    offsets = np.asarray(sensor_offsets_mm, dtype=np.float64) if sensor_offsets_mm is not None else _DEFAULT_OFFSETS_MM
    stations_by_id = {
        str(_first_present(row, "StationID")): row
        for row in stations_rows
    }

    ds = FWDDataset(
        source_file=str(db_path),
        device_type="Dynatest",
        sensor_offsets_mm=offsets,
    )

    drops_sorted = sorted(
        drops_rows,
        key=lambda r: (
            _float_or_nan(_first_present(r, "StationID", default=0)),
            _float_or_nan(_first_present(r, "DropID", default=0)),
        ),
    )
    station_counts: Dict[str, int] = {}
    drop_no_by_id: Dict[str, int] = {}

    for row in drops_sorted:
        station_id = str(_first_present(row, "StationID", default=""))
        station_row = stations_by_id.get(station_id, {})
        drop_id = str(_first_present(row, "DropID", default=""))
        station_counts[station_id] = station_counts.get(station_id, 0) + 1
        drop_no = station_counts[station_id]
        drop_no_by_id[drop_id] = drop_no

        if skip_seating and drop_no == 1:
            continue

        deflections = []
        for i in range(1, 10):
            value = _first_present(row, f"D{i}", default=None)
            if value is None:
                continue
            deflections.append(_float_or_nan(value) * _MILS_TO_MM)
        defl_arr = np.asarray(deflections, dtype=np.float64)

        station_label = str(_first_present(station_row, "Station", default=station_id))
        load_lb = _float_or_nan(_first_present(row, "Force", "Load", default=np.nan))
        drop = FWDDrop(
            station=station_label,
            drop_number=drop_no,
            distance_m=_float_or_nan(_first_present(station_row, "Station", default=station_id)),
            load_kN=load_lb * _LB_TO_KN,
            deflections_mm=defl_arr,
            sensor_offsets_mm=offsets[: len(defl_arr)],
            load_radius_mm=load_plate_radius_mm,
            pavement_temp_C=_float_or_nan(
                _first_present(row, "Surface", "SurfaceTemperature", default=_first_present(station_row, "SurfaceTemperature", "Surface"))
            ),
            air_temp_C=_float_or_nan(
                _first_present(row, "Air", "AirTemperature", default=_first_present(station_row, "AirTemperature", "Air"))
            ),
        )
        ds.drops.append(drop)

    if load_histories and history_rows:
        _attach_dynatest_histories(ds, history_rows, drop_no_by_id)

    return ds


def _attach_dynatest_histories(ds: FWDDataset, history_rows: List[dict], drop_no_by_id: Dict[str, int]) -> None:
    grouped: Dict[Tuple[str, int], List[dict]] = {}
    for row in history_rows:
        drop_id = str(_first_present(row, "DropID", default=""))
        drop_no = drop_no_by_id.get(drop_id)
        if drop_no is None:
            continue
        station_id = str(_first_present(row, "StationID", default=""))
        grouped.setdefault((station_id, drop_no), []).append(row)

    station_order = {str(i + 1): d.station for i, d in enumerate(ds.representative_drops(drop_number=1))}
    drops_by_key = {(d.station, d.drop_number): d for d in ds.drops}

    for (station_id, drop_no), rows in grouped.items():
        station = station_order.get(station_id, station_id)
        drop = drops_by_key.get((station, drop_no))
        if drop is None:
            continue
        time_s = [_float_or_nan(_first_present(row, "Time", default=0.0)) / 1000.0 for row in rows]
        force = [_float_or_nan(_first_present(row, "Force", "Load", default=np.nan)) for row in rows]
        disp_cols = []
        for i in range(1, 10):
            values = [_first_present(row, f"D{i}", default=None) for row in rows]
            if all(v is None for v in values):
                continue
            disp_cols.append([_float_or_nan(v) for v in values])
        if not disp_cols:
            continue
        drop.time_history = _resample_columns(
            time_s,
            force,
            disp_cols,
            station=drop.station,
            drop_number=drop.drop_number,
            force_scale=_LB_TO_KN,
            displacement_scale=_MILS_TO_MM,
        )

def read_dynatest(
    fwd_file: str | Path,
    sensor_offsets_mm: Optional[Sequence[float]] = None,
    load_plate_radius_mm: float = 150.0,
    skip_seating: bool = False,
) -> FWDDataset:
    """
    Read a Dynatest FWD plain-text *.FWD file.

    Dynatest FWD files are whitespace-delimited with a multi-line header section
    followed by data records.  Deflections are in micrometres (μm); load in kN.

    Args:
        fwd_file:            Path to the *.FWD file.
        sensor_offsets_mm:   Sensor offsets in mm.  If None, read from file header.
        load_plate_radius_mm: Load plate radius (default 150 mm).
        skip_seating:        Skip drop 1 (seating drop) if True.

    Returns:
        FWDDataset

    Example::

        ds = read_dynatest("survey.FWD")
    """
    fwd_path = Path(fwd_file)
    if not fwd_path.exists():
        raise FileNotFoundError(f"Dynatest FWD file not found: {fwd_path}")

    try:
        with open(fwd_path, encoding="latin-1") as fh:
            content = fh.read()
    except Exception as exc:
        raise IOError(f"Cannot read Dynatest FWD file: {exc}") from exc

    lines = content.splitlines()
    ds = FWDDataset(
        source_file=str(fwd_path),
        device_type="Dynatest",
        sensor_offsets_mm=(
            np.asarray(sensor_offsets_mm, dtype=np.float64)
            if sensor_offsets_mm is not None
            else None
        ),
    )

    file_offsets: Optional[np.ndarray] = None
    data_started = False
    drop_count: dict = {}  # station -> drop_number counter

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Header fields
        low = stripped.lower()
        if low.startswith("date"):
            parts = stripped.split(None, 1)
            if len(parts) > 1:
                ds.survey_date = parts[1].strip()
            continue
        if low.startswith("operator"):
            parts = stripped.split(None, 1)
            if len(parts) > 1:
                ds.operator = parts[1].strip()
            continue
        if low.startswith("project") or low.startswith("road"):
            parts = stripped.split(None, 1)
            if len(parts) > 1:
                ds.location = parts[1].strip()
            continue
        if low.startswith("geoph") or low.startswith("offset") or low.startswith("sensor"):
            nums = re.findall(r"[\d.]+", stripped)
            if len(nums) >= 2:
                file_offsets = np.asarray([float(x) for x in nums], dtype=np.float64)
            continue

        # Try to parse as a data record
        tokens = stripped.split()
        if len(tokens) < 5:
            continue

        # Typical Dynatest record: station  distance  load  d1..dn  [temp]
        try:
            first = float(tokens[0])
        except ValueError:
            # Non-numeric first token — still in header
            data_started = False
            continue

        data_started = True
        station_raw = tokens[0]

        try:
            floats = [float(t) for t in tokens]
        except ValueError:
            continue

        if len(floats) < 4:
            continue

        # Heuristic column detection based on number of sensors
        n_sensors = (len(file_offsets) if file_offsets is not None else
                     len(sensor_offsets_mm) if sensor_offsets_mm is not None else 9)

        # Layout: [station, distance, load, d1..dn, (temp)]
        if len(floats) >= 3 + n_sensors:
            dist_raw = floats[1]
            load_raw = floats[2]
            defl_raw = floats[3: 3 + n_sensors]
            temp_raw = floats[3 + n_sensors] if len(floats) > 3 + n_sensors else None
        else:
            dist_raw = floats[1] if len(floats) > 1 else 0.0
            load_raw = floats[2] if len(floats) > 2 else np.nan
            defl_raw = floats[3:] if len(floats) > 3 else []
            temp_raw = None

        station_key = station_raw
        drop_count[station_key] = drop_count.get(station_key, 0) + 1
        drop_num = drop_count[station_key]

        if skip_seating and drop_num == 1:
            continue

        # Dynatest deflections are in μm → mm
        deflections_mm = np.asarray(defl_raw, dtype=np.float64) / 1000.0
        # Distance in metres (Dynatest stores km or m depending on version)
        distance_m = dist_raw if dist_raw < 1000 else dist_raw / 1000.0
        temp_c = temp_raw

        used_offsets = (
            sensor_offsets_mm
            if sensor_offsets_mm is not None
            else file_offsets
            if file_offsets is not None
            else np.arange(len(deflections_mm), dtype=np.float64) * 200.0
        )
        used_offsets = np.asarray(used_offsets, dtype=np.float64)[: len(deflections_mm)]

        drop = FWDDrop(
            station=station_raw,
            drop_number=drop_num,
            distance_m=distance_m,
            load_kN=float(load_raw),
            deflections_mm=deflections_mm,
            sensor_offsets_mm=used_offsets,
            load_radius_mm=load_plate_radius_mm,
            pavement_temp_C=temp_c,
        )
        ds.drops.append(drop)

    if ds.sensor_offsets_mm is None and file_offsets is not None:
        ds.sensor_offsets_mm = file_offsets

    return ds


# ---------------------------------------------------------------------------
# Kuab reader
# ---------------------------------------------------------------------------

def read_kuab(
    fwd_file: str | Path,
    sensor_offsets_mm: Optional[Sequence[float]] = None,
    load_plate_radius_mm: float = 150.0,
    skip_seating: bool = False,
) -> FWDDataset:
    """
    Read a Kuab FWD plain-text *.fwd file.

    Kuab files typically store deflections in units of 0.001 mm (μm); loads in kN.
    The exact column layout varies by firmware version; this reader uses heuristics.

    Args:
        fwd_file:            Path to the *.fwd file.
        sensor_offsets_mm:   Sensor offsets in mm.
        load_plate_radius_mm: Load plate radius (default 150 mm).
        skip_seating:        Skip seating drops if True.

    Returns:
        FWDDataset

    Example::

        ds = read_kuab("survey.fwd")
    """
    fwd_path = Path(fwd_file)
    if not fwd_path.exists():
        raise FileNotFoundError(f"Kuab FWD file not found: {fwd_path}")

    try:
        lines = _read_text_lines(fwd_path)
    except Exception as exc:
        raise IOError(f"Cannot read Kuab FWD file: {exc}") from exc

    if any(("IKUAB" in line or line.strip().startswith("Distance")) for line in lines[:80]):
        return _read_kuab_peak_lines(
            fwd_path,
            lines,
            sensor_offsets_mm=sensor_offsets_mm,
            load_plate_radius_mm=load_plate_radius_mm,
            skip_seating=skip_seating,
        )

    ds = FWDDataset(
        source_file=str(fwd_path),
        device_type="Kuab",
        sensor_offsets_mm=(
            np.asarray(sensor_offsets_mm, dtype=np.float64)
            if sensor_offsets_mm is not None
            else None
        ),
    )

    file_offsets: Optional[np.ndarray] = None
    drop_count: dict = {}

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        low = stripped.lower()
        # Header fields
        if "date" in low and ":" in stripped:
            ds.survey_date = stripped.split(":", 1)[-1].strip()
            continue
        if low.startswith("operator"):
            ds.operator = stripped.split(":", 1)[-1].strip() if ":" in stripped else stripped[8:].strip()
            continue
        if low.startswith("sensors") or low.startswith("geoph"):
            nums = re.findall(r"[\d.]+", stripped)
            if len(nums) >= 2:
                file_offsets = np.asarray([float(x) for x in nums], dtype=np.float64)
            continue

        tokens = stripped.split()
        if len(tokens) < 5:
            continue

        try:
            floats = [float(t) for t in tokens]
        except ValueError:
            continue

        n_sensors = (len(file_offsets) if file_offsets is not None else
                     len(sensor_offsets_mm) if sensor_offsets_mm is not None else 9)

        if len(floats) < 3 + n_sensors:
            continue

        station_raw = tokens[0]
        dist_raw = floats[1]
        load_raw = floats[2]
        defl_raw = floats[3: 3 + n_sensors]
        temp_raw = floats[3 + n_sensors] if len(floats) > 3 + n_sensors else None

        station_key = station_raw
        drop_count[station_key] = drop_count.get(station_key, 0) + 1
        drop_num = drop_count[station_key]

        if skip_seating and drop_num == 1:
            continue

        # Kuab deflections: 0.001 mm -> mm
        deflections_mm = np.asarray(defl_raw, dtype=np.float64) / 1000.0
        distance_m = dist_raw

        used_offsets = (
            sensor_offsets_mm if sensor_offsets_mm is not None
            else file_offsets if file_offsets is not None
            else np.arange(len(deflections_mm), dtype=np.float64) * 200.0
        )
        used_offsets = np.asarray(used_offsets, dtype=np.float64)[: len(deflections_mm)]

        drop = FWDDrop(
            station=station_raw,
            drop_number=drop_num,
            distance_m=distance_m,
            load_kN=float(load_raw),
            deflections_mm=deflections_mm,
            sensor_offsets_mm=used_offsets,
            load_radius_mm=load_plate_radius_mm,
            pavement_temp_C=temp_raw,
        )
        ds.drops.append(drop)

    if ds.sensor_offsets_mm is None and file_offsets is not None:
        ds.sensor_offsets_mm = file_offsets

    return ds


def read_kuab_folder(
    folder: str | Path,
    sensor_offsets_mm: Optional[Sequence[float]] = None,
    load_plate_radius_mm: float = 150.0,
    skip_seating: bool = False,
    load_histories: bool = True,
) -> FWDDataset:
    """
    Read a Kuab ViscoWave V3 folder containing one ``*.fwd`` peak file and
    optional ``*.HST`` time-history files.

    This is the Python counterpart of the ViscoWave ``Kuab.r`` workflow.  Kuab
    files are commonly UTF-16LE.  Peak forces are interpreted as pounds and
    deflections as mils, matching the labels and exports in the original script.
    """
    folder_path = Path(folder)
    if not folder_path.exists():
        raise FileNotFoundError(f"Kuab folder not found: {folder_path}")

    fwd_files = sorted(folder_path.glob("*.fwd")) + sorted(folder_path.glob("*.FWD"))
    if not fwd_files:
        raise FileNotFoundError(f"No Kuab .fwd file found in {folder_path}")

    ds = read_kuab(
        fwd_files[0],
        sensor_offsets_mm=sensor_offsets_mm,
        load_plate_radius_mm=load_plate_radius_mm,
        skip_seating=skip_seating,
    )
    ds.source_file = str(folder_path)

    if not load_histories:
        return ds

    histories: Dict[Tuple[str, int], FWDTimeHistory] = {}
    for hst_file in sorted(folder_path.glob("*.HST")) + sorted(folder_path.glob("*.hst")):
        histories.update(_parse_kuab_hst_file(hst_file))

    for drop in ds.drops:
        key = (drop.station, drop.drop_number)
        if key in histories:
            drop.time_history = histories[key]
    return ds


def _read_text_lines(path: Path) -> List[str]:
    for enc in ("utf-16", "utf-16le", "latin-1"):
        try:
            with open(path, encoding=enc) as fh:
                return fh.readlines()
        except UnicodeError:
            continue
    with open(path, encoding="latin-1") as fh:
        return fh.readlines()


def _header_tokens(line: str) -> List[str]:
    return re.findall(r"[A-Za-z][A-Za-z0-9()]*", line)


def _number_tokens(line: str) -> List[float]:
    return [float(x) for x in re.findall(r"-?(?:\d+(?:\.\d*)?|\.\d+)", line)]


def _read_kuab_peak_lines(
    fwd_path: Path,
    lines: List[str],
    *,
    sensor_offsets_mm: Optional[Sequence[float]],
    load_plate_radius_mm: float,
    skip_seating: bool,
) -> FWDDataset:
    header: List[str] = []
    rows: List[List[float]] = []
    in_data = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if "Distance" in stripped:
            header = _header_tokens(stripped)
            in_data = True
            continue
        if not in_data:
            continue
        nums = _number_tokens(stripped)
        if len(nums) >= 6:
            rows.append(nums)

    if not rows:
        raise ValueError(f"No Kuab peak rows found in {fwd_path}")

    if header and len(rows[0]) == len(header) + 2:
        header = header[:-1] + ["Time(H)", "Time(M)", "Time(S)"]
    if not header or len(header) != len(rows[0]):
        header = _default_kuab_peak_header(len(rows[0]))

    offsets = np.asarray(sensor_offsets_mm, dtype=np.float64) if sensor_offsets_mm is not None else _DEFAULT_OFFSETS_MM
    ds = FWDDataset(
        source_file=str(fwd_path),
        device_type="Kuab",
        sensor_offsets_mm=offsets,
    )

    for values in rows:
        row = dict(zip(header, values))
        station_value = _first_present(row, "Station", default=values[0])
        station_num = _float_or_nan(station_value)
        station = str(int(station_num)) if np.isfinite(station_num) and station_num.is_integer() else str(station_value)
        drop_no = int(_float_or_nan(_first_present(row, "Imp", "Impact", "Drop", default=1)))
        if skip_seating and drop_no == 1:
            continue

        d_items = []
        for name, value in row.items():
            m = re.fullmatch(r"D(\d+)", str(name))
            if m:
                d_items.append((int(m.group(1)), value))
        d_items.sort(key=lambda item: item[0])
        deflections_mm = np.asarray([_float_or_nan(v) * _MILS_TO_MM for _, v in d_items[:9]], dtype=np.float64)

        drop = FWDDrop(
            station=station,
            drop_number=drop_no,
            distance_m=_float_or_nan(_first_present(row, "Milepost", "JDistance", "Distance", default=0.0)),
            load_kN=_float_or_nan(_first_present(row, "Load", "Force", default=np.nan)) * _LB_TO_KN,
            deflections_mm=deflections_mm,
            sensor_offsets_mm=offsets[: len(deflections_mm)],
            load_radius_mm=load_plate_radius_mm,
            pavement_temp_C=_float_or_nan(_first_present(row, "Pave", "Pavement", "Surface", default=np.nan)),
            air_temp_C=_float_or_nan(_first_present(row, "Air", default=np.nan)),
        )
        ds.drops.append(drop)

    return ds


def _default_kuab_peak_header(n_cols: int) -> List[str]:
    base = ["Station", "Milepost", "Imp", "Load"]
    remaining = max(n_cols - len(base) - 5, 0)
    sensors = [f"D{i}" for i in range(remaining)]
    tail = ["Air", "Pave", "Time(H)", "Time(M)", "Time(S)"]
    return (base + sensors + tail)[:n_cols]


def _parse_kuab_hst_file(hst_file: Path) -> Dict[Tuple[str, int], FWDTimeHistory]:
    lines = _read_text_lines(hst_file)
    records: Dict[Tuple[str, int], FWDTimeHistory] = {}
    station = ""
    drop_no = 1
    header: List[str] = []
    rows: List[dict] = []

    def flush() -> None:
        if not station or not rows or not header:
            return
        time_s = [_float_or_nan(_first_present(row, "Time", default=0.0)) / 1000.0 for row in rows]
        force = [_float_or_nan(_first_present(row, "Load", "Force", default=np.nan)) for row in rows]

        d_items = []
        for name in header:
            m = re.fullmatch(r"D(\d+)", name)
            if m:
                d_items.append((int(m.group(1)), name))
        d_items.sort(key=lambda item: item[0])
        if not d_items:
            return
        disps = [[_float_or_nan(row.get(name)) for row in rows] for _, name in d_items[:9]]
        records[(station, drop_no)] = _resample_columns(
            time_s,
            force,
            disps,
            station=station,
            drop_number=drop_no,
            force_scale=_LB_TO_KN,
            displacement_scale=_MILS_TO_MM,
        )

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if "Station" in stripped:
            flush()
            rows = []
            m = re.search(r"Station\s*:\s*(\d+)", stripped, re.IGNORECASE)
            station = m.group(1) if m else station
            continue
        if "Impact Number" in stripped:
            flush()
            rows = []
            m = re.search(r"Impact Number\s*:\s*(\d+)", stripped, re.IGNORECASE)
            drop_no = int(m.group(1)) if m else drop_no
            continue
        if re.search(r"\bTime\s+Load\b", stripped, re.IGNORECASE):
            header = _header_tokens(stripped)
            rows = []
            continue
        if header:
            nums = _number_tokens(stripped)
            if len(nums) >= len(header):
                rows.append(dict(zip(header, nums[: len(header)])))

    flush()
    return records
