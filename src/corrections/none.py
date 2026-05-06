"""Pass-through control: no correction applied."""
import numpy as np

from .base import validate_cube


def none_correct(toa_cube: np.ndarray, **kwargs) -> np.ndarray:
    validate_cube(toa_cube)
    return toa_cube.astype(np.float32).copy()
