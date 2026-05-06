"""Common correction interface."""
from __future__ import annotations

import numpy as np


def validate_cube(toa_cube: np.ndarray) -> None:
    if toa_cube.ndim != 3:
        raise ValueError(f"toa_cube must be (H, W, K), got {toa_cube.shape}")


def correct(method_name: str, toa_cube: np.ndarray, **kwargs) -> np.ndarray:
    """Dispatch to a registered correction by name."""
    from . import REGISTRY
    if method_name not in REGISTRY:
        raise KeyError(f"unknown method {method_name!r}, choose from {sorted(REGISTRY)}")
    return REGISTRY[method_name](toa_cube=toa_cube, **kwargs)
