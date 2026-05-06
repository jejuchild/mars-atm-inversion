import numpy as np
import pytest

from src.constants import MASTCAMZ_BAND_CENTERS_NM
from src.data.synthetic import make_atm_scene
from src.anchor.consistency import project_to_mastcamz, cosine_consistency


def test_project_band_count():
    s = make_atm_scene(height=16, width=16, n_bands=12, seed=0)
    proj = project_to_mastcamz(s.clean_truth, s.crism_lambda_nm)
    assert proj.shape == (16, 16, 11)


def test_project_band_count_mismatch_raises():
    bad = np.zeros((4, 4, 7), dtype=np.float32)
    crism = np.linspace(440, 2500, 12)
    with pytest.raises(ValueError):
        project_to_mastcamz(bad, crism)


def test_anchor_self_consistency_high():
    s = make_atm_scene(height=16, width=16, n_bands=12, n_anchors=4, noise=0.005, seed=1)
    res = cosine_consistency(
        corrected_cube=s.clean_truth,
        crism_lambda_nm=s.crism_lambda_nm,
        anchor_xy=s.anchor_xy,
        anchor_spec_mz=s.anchor_spec_mz,
    )
    assert res["n_anchors"] == 4
    assert res["cos_mean"] > 0.9
    assert res["rmse_mean"] < 0.05


def test_anchor_handles_empty():
    cube = np.zeros((4, 4, 12), dtype=np.float32)
    crism = np.linspace(440, 2500, 12)
    res = cosine_consistency(
        corrected_cube=cube,
        crism_lambda_nm=crism,
        anchor_xy=np.zeros((0, 2), dtype=np.int64),
        anchor_spec_mz=np.zeros((0, 11), dtype=np.float32),
    )
    assert res["n_anchors"] == 0


def test_anchor_corrupted_data_lower_cos():
    s = make_atm_scene(height=16, width=16, n_bands=12, n_anchors=4, seed=2)
    res_truth = cosine_consistency(s.clean_truth, s.crism_lambda_nm, s.anchor_xy, s.anchor_spec_mz)
    rng = np.random.default_rng(0)
    corrupted = s.clean_truth + rng.normal(0, 0.5, size=s.clean_truth.shape).astype(np.float32)
    corrupted = np.clip(corrupted, 0, 1)
    res_corrupted = cosine_consistency(corrupted, s.crism_lambda_nm, s.anchor_xy, s.anchor_spec_mz)
    assert res_corrupted["cos_mean"] < res_truth["cos_mean"]
