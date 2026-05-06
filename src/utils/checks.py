import os
import time


def assert_cpu_only() -> None:
    if os.environ.get("CUDA_VISIBLE_DEVICES", "") not in ("", "-1"):
        raise RuntimeError("CUDA_VISIBLE_DEVICES is set; CPU-only required.")
    try:
        import torch
    except ImportError:
        return
    if torch.cuda.is_available():
        raise RuntimeError("CUDA available; refusing GPU.")


ALLOWED_METHODS = {"none", "volcano_scan", "beer_lambert", "lambert_albedo"}


def assert_allowed_method(name: str) -> None:
    if name not in ALLOWED_METHODS:
        raise ValueError(
            f"correction {name!r} not allowed in Phase 0. "
            f"Allowed: {sorted(ALLOWED_METHODS)}. DISORT / deep unmixing forbidden."
        )


class RuntimeBudget:
    def __init__(self, seconds: float):
        self.seconds = float(seconds)
        self.start = time.perf_counter()

    def check(self) -> None:
        if time.perf_counter() - self.start > self.seconds:
            raise RuntimeError(f"Runtime budget exceeded: {self.seconds:.1f}s")
