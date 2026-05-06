"""Simple Beer-Lambert atmospheric correction.

Assumes:
  TOA(λ) ≈ T(λ) · R_surf(λ) + diffuse_offset
  T(λ) ≈ exp(-τ · airmass)  (wavelength-independent in this simplification)
Then:
  R_surf(λ) ≈ (TOA - diffuse_offset) / T

Diffuse offset: small constant (Phase 0 prototype skips wavelength-dependent
Rayleigh / aerosol scattering; codex §A1-2 has the full DISORT treatment, OOS).
"""
import numpy as np

from .base import validate_cube


def beer_lambert(
    toa_cube: np.ndarray,
    tau_estimate: float,
    airmass: float,
    diffuse_offset: float | None = None,
    **kwargs,
) -> np.ndarray:
    validate_cube(toa_cube)
    if airmass <= 0:
        raise ValueError("airmass must be positive")
    if tau_estimate < 0:
        raise ValueError("tau_estimate must be >= 0")
    if diffuse_offset is None:
        diffuse_offset = 0.05 * float(tau_estimate)
    transmittance = float(np.exp(-tau_estimate * airmass))
    transmittance = max(transmittance, 1e-3)
    corrected = (toa_cube.astype(np.float32) - diffuse_offset) / transmittance
    return np.clip(corrected, 0.0, 1.0).astype(np.float32)
