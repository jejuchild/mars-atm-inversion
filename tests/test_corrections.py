import numpy as np
import pytest

from src.data.synthetic import make_atm_scene
from src.corrections import REGISTRY
from src.corrections.base import correct


def _scene():
    return make_atm_scene(height=32, width=32, n_bands=12, tau_true=0.5, airmass=1.41, seed=0)


@pytest.mark.parametrize("method", ["none", "volcano_scan", "beer_lambert", "lambert_albedo"])
def test_each_correction_runs(method):
    s = _scene()
    kwargs = {"tau_estimate": 0.5, "airmass": 1.41} if method in ("beer_lambert", "lambert_albedo") else {}
    out = correct(method, s.toa_cube, **kwargs)
    assert out.shape == s.toa_cube.shape
    assert np.isfinite(out).all()
    assert out.dtype == np.float32


def test_registry_has_four():
    assert set(REGISTRY) == {"none", "volcano_scan", "beer_lambert", "lambert_albedo"}


def test_unknown_correction_raises():
    s = _scene()
    with pytest.raises(KeyError):
        correct("disort_full", s.toa_cube)


def test_beer_lambert_reverses_attenuation_at_known_tau():
    s = make_atm_scene(height=32, width=32, n_bands=12, tau_true=0.5, airmass=1.41, noise=0.0, seed=4)
    corrected = correct("beer_lambert", s.toa_cube, tau_estimate=0.5, airmass=1.41)
    rmse_corrected = np.sqrt(((corrected - s.clean_truth) ** 2).mean())
    rmse_toa = np.sqrt(((s.toa_cube - s.clean_truth) ** 2).mean())
    assert rmse_corrected < rmse_toa, f"BL should reduce RMSE: corrected={rmse_corrected:.4f} vs toa={rmse_toa:.4f}"


def test_beer_lambert_invalid_args():
    s = _scene()
    with pytest.raises(ValueError):
        correct("beer_lambert", s.toa_cube, tau_estimate=-0.5, airmass=1.0)
    with pytest.raises(ValueError):
        correct("beer_lambert", s.toa_cube, tau_estimate=0.5, airmass=0)


def test_volcano_scan_valid_pct_range():
    s = _scene()
    with pytest.raises(ValueError):
        correct("volcano_scan", s.toa_cube, reference_percentile=0)
    with pytest.raises(ValueError):
        correct("volcano_scan", s.toa_cube, reference_percentile=100)


def test_lambert_albedo_invalid_args():
    s = _scene()
    with pytest.raises(ValueError):
        correct("lambert_albedo", s.toa_cube, tau_estimate=0.5, airmass=0)


def test_none_pass_through():
    s = _scene()
    out = correct("none", s.toa_cube)
    np.testing.assert_array_equal(out, s.toa_cube)
