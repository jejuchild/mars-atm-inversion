"""Lambert albedo (DISORT-Lambert proxy, 2-stream approximation).

Simplified 2-stream: TOA ≈ T · R + (1-T) · A_atm
where A_atm is a small atmospheric path radiance constant. Solve for R:
  R = (TOA - (1-T)·A_atm) / T
This is McGuire 2009 §A1-2's Lambert albedo idea, without the full DISORT
multi-scattering chain (which would be Phase 1+ Carson follow-up).
"""
import numpy as np

from .base import validate_cube


def lambert_albedo(
    toa_cube: np.ndarray,
    tau_estimate: float,
    airmass: float,
    surface_albedo_init: float = 0.25,
    atm_path_radiance: float | None = None,
    **kwargs,
) -> np.ndarray:
    validate_cube(toa_cube)
    if airmass <= 0:
        raise ValueError("airmass must be positive")
    if tau_estimate < 0:
        raise ValueError("tau_estimate must be >= 0")
    transmittance = float(np.exp(-tau_estimate * airmass))
    transmittance = max(transmittance, 1e-3)
    if atm_path_radiance is None:
        atm_path_radiance = 0.5 * surface_albedo_init * (1.0 - transmittance)
    corrected = (toa_cube.astype(np.float32) - (1.0 - transmittance) * atm_path_radiance) / transmittance
    return np.clip(corrected, 0.0, 1.0).astype(np.float32)
