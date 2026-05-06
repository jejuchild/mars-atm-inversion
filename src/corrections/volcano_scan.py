"""Volcano-scan column-ratio proxy (McGuire 2009 simplified, codex §A1-1).

Original volcano-scan: divide CRISM observation by a reference spectrum
acquired at high elevation (lower atmospheric column) to remove gas absorption.

Phase 0 proxy: identify "atmosphere-dominated" reference pixels as the bottom
N-percentile of mean reflectance, then divide the cube by this column-mean as
a normalization. Not a real volcano scan, but exercises the column-ratio
interface.
"""
import numpy as np

from .base import validate_cube


def volcano_scan(
    toa_cube: np.ndarray,
    reference_percentile: float = 5.0,
    **kwargs,
) -> np.ndarray:
    validate_cube(toa_cube)
    if not (0 < reference_percentile < 100):
        raise ValueError("reference_percentile must be in (0, 100)")
    pixel_means = toa_cube.mean(axis=-1)
    threshold = float(np.percentile(pixel_means, reference_percentile))
    mask = pixel_means <= threshold
    if mask.sum() == 0:
        ref_spectrum = toa_cube.reshape(-1, toa_cube.shape[-1]).mean(axis=0)
    else:
        ref_spectrum = toa_cube[mask].mean(axis=0)
    ref_spectrum = np.where(ref_spectrum > 1e-6, ref_spectrum, 1.0)
    corrected = toa_cube.astype(np.float32) / ref_spectrum * float(ref_spectrum.mean())
    return np.clip(corrected, 0.0, 1.0).astype(np.float32)
