import numpy as np
import pytest

from src.data.synthetic import make_atm_scene
from src.data.real_reader import discover_atm_inputs


def test_scene_shapes():
    s = make_atm_scene(height=32, width=32, n_bands=12, n_anchors=4, seed=0)
    assert s.clean_truth.shape == (32, 32, 12)
    assert s.toa_cube.shape == (32, 32, 12)
    assert s.tau_field.shape == (32, 32)
    assert s.crism_lambda_nm.shape == (12,)
    assert s.anchor_xy.shape == (4, 2)
    assert s.anchor_spec_mz.shape == (4, 11)


def test_attenuation_reduces_signal():
    s = make_atm_scene(height=32, width=32, n_bands=12, tau_true=0.8, airmass=1.5, seed=1)
    assert (s.toa_cube.mean() < s.clean_truth.mean() + 1e-3)


def test_zero_tau_recovers_clean():
    s = make_atm_scene(height=32, width=32, n_bands=12, tau_true=0.0, airmass=1.0, noise=0.0, seed=2)
    np.testing.assert_allclose(s.toa_cube, s.clean_truth, atol=1e-3)


def test_scene_deterministic():
    a = make_atm_scene(height=16, width=16, n_bands=8, seed=3)
    b = make_atm_scene(height=16, width=16, n_bands=8, seed=3)
    np.testing.assert_array_equal(a.clean_truth, b.clean_truth)
    np.testing.assert_array_equal(a.toa_cube, b.toa_cube)


def test_invalid_args():
    with pytest.raises(ValueError):
        make_atm_scene(height=2)
    with pytest.raises(ValueError):
        make_atm_scene(n_bands=0)
    with pytest.raises(ValueError):
        make_atm_scene(tau_true=-0.1)
    with pytest.raises(ValueError):
        make_atm_scene(airmass=0)


def test_real_reader_dry_run(tmp_path):
    m = discover_atm_inputs(
        crism_dir=tmp_path / "no_c",
        mastcamz_dir=tmp_path / "no_m",
        meda_dir=tmp_path / "no_e",
    )
    assert len(m.missing_dirs) == 3
    assert not m.crism_present
    assert not m.meda_present
