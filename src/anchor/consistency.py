"""Mastcam-Z anchor consistency: project corrected CRISM cube to Mastcam-Z bands + score."""
from __future__ import annotations

import numpy as np

from ..constants import MASTCAMZ_BAND_CENTERS_NM


def project_to_mastcamz(
    cube: np.ndarray,
    crism_lambda_nm: np.ndarray,
    target_centers_nm: np.ndarray = MASTCAMZ_BAND_CENTERS_NM,
) -> np.ndarray:
    """Linear-interp every pixel from K CRISM bands to 11 Mastcam-Z centers."""
    if cube.ndim != 3:
        raise ValueError("cube must be (H, W, K)")
    if cube.shape[-1] != len(crism_lambda_nm):
        raise ValueError(
            f"cube K={cube.shape[-1]} != crism_lambda len={len(crism_lambda_nm)}"
        )
    H, W, _ = cube.shape
    flat = cube.reshape(-1, cube.shape[-1])
    out = np.stack([
        np.interp(target_centers_nm, crism_lambda_nm, flat[i, :])
        for i in range(flat.shape[0])
    ], axis=0)
    return out.reshape(H, W, len(target_centers_nm)).astype(np.float32)


def cosine_consistency(
    corrected_cube: np.ndarray,
    crism_lambda_nm: np.ndarray,
    anchor_xy: np.ndarray,
    anchor_spec_mz: np.ndarray,
) -> dict:
    if anchor_xy.shape[0] == 0:
        return {"cos_mean": float("nan"), "rmse_mean": float("nan"), "n_anchors": 0}
    projected = project_to_mastcamz(corrected_cube, crism_lambda_nm)
    rows = anchor_xy[:, 0]
    cols = anchor_xy[:, 1]
    pred = projected[rows, cols, :]
    if pred.shape != anchor_spec_mz.shape:
        raise ValueError(f"shape mismatch pred={pred.shape} truth={anchor_spec_mz.shape}")
    dot = (pred * anchor_spec_mz).sum(axis=1)
    np_ = np.linalg.norm(pred, axis=1) + 1e-9
    nt = np.linalg.norm(anchor_spec_mz, axis=1) + 1e-9
    cos = np.clip(dot / (np_ * nt), -1.0, 1.0)
    rmse = np.sqrt(((pred - anchor_spec_mz) ** 2).mean(axis=1))
    return {
        "cos_mean": float(cos.mean()),
        "cos_per_anchor": cos.astype(np.float32).tolist(),
        "rmse_mean": float(rmse.mean()),
        "rmse_per_anchor": rmse.astype(np.float32).tolist(),
        "n_anchors": int(anchor_xy.shape[0]),
    }
