import numpy as np

DEFAULT_SEED = 42

CRISM_BAND_CENTERS_NM = np.linspace(440.0, 2500.0, 30, dtype=np.float32)
N_CRISM_BANDS = 30

MASTCAMZ_BAND_CENTERS_NM = np.array(
    [442, 528, 567, 605, 686, 754, 800, 866, 910, 939, 978], dtype=np.float32
)
N_MASTCAMZ_BANDS = 11

DEFAULT_TAU = 0.5
DEFAULT_AIRMASS = 1.0 / np.cos(np.deg2rad(45.0))

CORRECTION_METHODS = ("none", "volcano_scan", "beer_lambert", "lambert_albedo")
