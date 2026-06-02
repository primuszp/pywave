from pathlib import Path

import numpy as np

import viscowave
from viscowave.dynmod import SigmoidModel, reduced_frequency, wlf_shift_factor
from viscowave.fwd_io import read_fwd, read_jils
from viscowave.indices import DeflectionBasin, compute_area


ROOT = Path(__file__).resolve().parents[1]


def test_package_imports_and_native_libraries_load():
    info = viscowave.get_platform_info()

    assert viscowave.__version__ == "2.2.0"
    assert info["library_status"] == "loaded"


def test_jils_reader_loads_dat_and_time_histories():
    ds = read_jils(ROOT / "sample" / "JILS_Sample.DAT")

    assert ds.device_type == "JILS"
    assert ds.num_stations == 10
    assert ds.num_drops == 30
    assert ds.deflection_matrix(drop_number=2).shape == (10, 9)
    assert ds.load_vector(drop_number=2).shape == (10,)
    assert ds.representative_drops(drop_number=2)[0].time_history is not None


def test_read_fwd_auto_detects_jils_dat():
    ds = read_fwd(ROOT / "sample" / "JILS_Sample.DAT")

    assert ds.device_type == "JILS"
    assert ds.num_drops == 30


def test_dataset_records_are_dataframe_ready():
    ds = read_jils(ROOT / "sample" / "JILS_Sample.DAT", load_thy=False)
    rows = ds.to_records()

    assert len(rows) == 30
    assert "D0_mm" in rows[0]
    assert "load_kN" in rows[0]


def test_deflection_basin_indices_are_numpy_2_compatible():
    basin = DeflectionBasin(
        deflections_mm=[0.800, 0.510, 0.350, 0.245, 0.175, 0.118],
        offsets_mm=[0, 200, 300, 450, 600, 900],
        load_kN=40.0,
    )

    assert np.isclose(basin.SCI, 0.450)
    assert np.isclose(basin.BDI, 0.175)
    assert np.isclose(basin.BCI, 0.057)
    assert np.isfinite(basin.AREA)
    assert np.isclose(basin.AREA, compute_area(basin.deflections_mm, basin.offsets_mm))


def test_dynamic_modulus_master_curve_helpers():
    model = SigmoidModel(delta=3.123, alpha=3.446, beta=-0.128, gamma=0.554)
    log_shift = wlf_shift_factor(T_C=20.0, Tref_C=20.0)

    assert log_shift == 0
    assert reduced_frequency(10.0, log_shift) == 10.0
    assert model.modulus(temp_C=20.0, freq_Hz=10.0) > 0
    assert len(model.master_curve([1, 10], [5, 20]).reduced_freqs_Hz) == 4
