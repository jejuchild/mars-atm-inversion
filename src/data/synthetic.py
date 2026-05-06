"""Deterministic synthetic atmospheric inversion scene.

Clean ground reflectance + atmospheric attenuation (Beer-Lambert + diffuse
component) + Mastcam-Z 11-band anchor at random pixels (representing the
ground-truth measurement under near-zero atmosphere correction error, since
Mastcam-Z is on-ground).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..constants import (
    CRISM_BAND_CENTERS_NM,
    DEFAULT_AIRMASS,
    DEFAULT_TAU,
    MASTCAMZ_BAND_CENTERS_NM,
)


@dataclass
class AtmScene:
    clean_truth: np.ndarray   # (H, W, K)
    toa_cube: np.ndarray      # (H, W, K) attenuated
    tau_field: np.ndarray     # (H, W) atmospheric optical depth
    airmass: float
    crism_lambda_nm: np.ndarray  # (K,)
    anchor_xy: np.ndarray     # (n, 2) int row, col
    anchor_spec_mz: np.ndarray  # (n, 11) Mastcam-Z 11-band ground truth


def _ground_reflectance(H: int, W: int, K: int, rng: np.random.Generator) -> np.ndarray:
    centers = CRISM_BAND_CENTERS_NM[:K] if K <= len(CRISM_BAND_CENTERS_NM) else np.linspace(440, 2500, K, dtype=np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    spatial = (
        0.10 + 0.05 * np.sin(2 * np.pi * xx / max(W // 4, 1))
        + 0.05 * np.cos(2 * np.pi * yy / max(H // 4, 1))
    ).astype(np.float32)

    n_components = 4
    peaks = rng.uniform(centers.min(), centers.max(), size=n_components)
    widths = rng.uniform(150.0, 500.0, size=n_components)
    basis = np.stack([
        np.exp(-0.5 * ((centers - peaks[i]) / widths[i]) ** 2)
        for i in range(n_components)
    ], axis=0)
    basis = (basis / basis.max(axis=1, keepdims=True)).astype(np.float32)

    weight_maps = np.stack([
        0.5 * np.sin(2 * np.pi * (xx + i * W / 4) / max(W // 2, 1)) +
        0.5 * np.cos(2 * np.pi * (yy + i * H / 4) / max(H // 2, 1))
        for i in range(n_components)
    ], axis=-1)
    weight_maps = weight_maps - weight_maps.min(axis=(0, 1), keepdims=True)
    weight_maps = weight_maps / (weight_maps.sum(axis=-1, keepdims=True) + 1e-6)

    spectra = (weight_maps @ basis).astype(np.float32)
    cube = spatial[..., None] + 0.5 * spectra
    return np.clip(cube, 0.05, 0.95).astype(np.float32)


def make_atm_scene(
    height: int = 64,
    width: int = 64,
    n_bands: int = 30,
    n_anchors: int = 5,
    tau_true: float = DEFAULT_TAU,
    airmass: float = DEFAULT_AIRMASS,
    noise: float = 0.01,
    seed: int = 42,
) -> AtmScene:
    if height < 4 or width < 4:
        raise ValueError("height/width must be >= 4")
    if n_bands < 1:
        raise ValueError("n_bands must be >= 1")
    if tau_true < 0:
        raise ValueError("tau_true must be >= 0")
    if airmass <= 0:
        raise ValueError("airmass must be positive")
    rng = np.random.default_rng(seed)

    clean = _ground_reflectance(height, width, n_bands, rng)
    transmittance = float(np.exp(-tau_true * airmass))
    diffuse = 0.05 * tau_true
    toa = transmittance * clean + diffuse
    toa += rng.normal(0.0, noise, size=toa.shape).astype(np.float32)
    toa = np.clip(toa, 0.0, 1.0).astype(np.float32)

    tau_field = np.full((height, width), tau_true, dtype=np.float32)

    crism_lambda = CRISM_BAND_CENTERS_NM[:n_bands] if n_bands <= len(CRISM_BAND_CENTERS_NM) else np.linspace(440, 2500, n_bands, dtype=np.float32)

    anchor_rows = rng.integers(0, height, size=n_anchors)
    anchor_cols = rng.integers(0, width, size=n_anchors)
    anchor_xy = np.stack([anchor_rows, anchor_cols], axis=1).astype(np.int64)

    anchor_spec_mz = np.zeros((n_anchors, len(MASTCAMZ_BAND_CENTERS_NM)), dtype=np.float32)
    for i in range(n_anchors):
        clean_spec = clean[anchor_rows[i], anchor_cols[i], :]
        anchor_spec_mz[i] = np.interp(
            MASTCAMZ_BAND_CENTERS_NM, crism_lambda, clean_spec,
        ).astype(np.float32)
    anchor_spec_mz += rng.normal(0.0, noise, size=anchor_spec_mz.shape).astype(np.float32)
    anchor_spec_mz = np.clip(anchor_spec_mz, 0.0, 1.0).astype(np.float32)

    return AtmScene(
        clean_truth=clean,
        toa_cube=toa,
        tau_field=tau_field,
        airmass=float(airmass),
        crism_lambda_nm=crism_lambda.astype(np.float32),
        anchor_xy=anchor_xy,
        anchor_spec_mz=anchor_spec_mz,
    )
