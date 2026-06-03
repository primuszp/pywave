from pathlib import Path

import numpy as np

import viscowave
from viscowave.dynmod import SigmoidModel, reduced_frequency, wlf_shift_factor
from viscowave.fwd_io import read_fwd, read_jils, read_kuab_folder
from viscowave.indices import DeflectionBasin, compute_area


ROOT = Path(__file__).resolve().parents[1]


def test_package_imports_and_native_libraries_load():
    info = viscowave.get_platform_info()

    assert viscowave.__version__ == "2.3.0"
    assert info["library_status"] == "loaded"


def test_jils_reader_loads_dat_and_time_histories():
    ds = read_jils(ROOT / "sample" / "JILS_Sample.DAT")

    assert ds.device_type == "JILS"
    assert ds.num_stations == 10
    assert ds.num_drops == 30
    assert ds.deflection_matrix(drop_number=2).shape == (10, 9)
    assert ds.load_vector(drop_number=2).shape == (10,)
    assert ds.representative_drops(drop_number=2)[0].time_history is not None


def test_jils_reader_applies_station_metadata_to_all_drops(tmp_path):
    dat = tmp_path / "survey.DAT"
    dat.write_text(
        "\n".join(
            [
                "M5",
                "1 1 0.000 1 1 1 1 1 1 1 1 1 1 4.0 70.0",
                "1 2 0.000 1 2 2 2 2 2 2 2 2 2 4.1 70.0",
                "GPS: Quality : DGPS Fix   Latitude = 34 deg58.140780  N   Longitude = 89 deg49.043990   W   PDOP = 0.00",
                "Note: station two",
                "2 1 10.000 1 3 3 3 3 3 3 3 3 3 4.2 71.0",
                "2 2 10.000 1 4 4 4 4 4 4 4 4 4 4.3 71.0",
            ]
        ),
        encoding="latin-1",
    )

    ds = read_jils(dat, load_thy=False)

    assert ds.drops[0].gps_lat is None
    assert ds.drops[2].notes == "station two"
    assert ds.drops[3].notes == "station two"
    assert ds.drops[2].gps_lat == ds.drops[3].gps_lat
    assert ds.drops[2].gps_lon == ds.drops[3].gps_lon


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


def test_kuab_folder_reader_parses_utf16_peak_and_history(tmp_path):
    fwd = tmp_path / "survey.fwd"
    fwd.write_text(
        "\n".join(
            [
                "IKUAB",
                "Station JDistance Imp Load D0 D1 D2 Air Pave Time",
                "1 10.0 1 9000 10 8 6 20 25 12 30 00",
                "1 10.0 2 9500 11 9 7 21 26 12 31 00",
            ]
        ),
        encoding="utf-16le",
    )
    hst = tmp_path / "station1.HST"
    hst.write_text(
        "\n".join(
            [
                "Station : 1",
                "Impact Number : 2",
                "Time Load D0 D1 D2",
                "0.0 0.0 0.0 0.0 0.0",
                "0.2 9500.0 11.0 9.0 7.0",
                "59.8 0.0 0.0 0.0 0.0",
            ]
        ),
        encoding="utf-16le",
    )

    ds = read_kuab_folder(tmp_path)
    ds_auto = read_fwd(tmp_path)

    assert ds.device_type == "Kuab"
    assert ds.num_drops == 2
    assert ds_auto.device_type == "Kuab"
    assert np.isclose(ds.drops[1].load_kN, 9500 * 0.0044482216152605)
    assert np.allclose(ds.drops[1].deflections_mm, np.array([11, 9, 7]) * 0.0254)
    assert ds.drops[1].time_history is not None
    assert ds.drops[1].time_history.n_samples == 300
