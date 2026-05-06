"""Discover real atm-inversion inputs (Phase 0 dry-run only)."""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AtmManifest:
    crism_dir: Path
    mastcamz_dir: Path
    meda_dir: Path | None
    crism_present: bool
    mastcamz_files: int
    meda_present: bool
    missing_dirs: list


def discover_atm_inputs(crism_dir, mastcamz_dir, meda_dir=None) -> AtmManifest:
    c = Path(crism_dir)
    m = Path(mastcamz_dir)
    md = Path(meda_dir) if meda_dir else None
    missing = []
    if not c.exists():
        missing.append(str(c))
    if not m.exists():
        missing.append(str(m))
    if md is not None and not md.exists():
        missing.append(str(md))

    def _present(p):
        if p is None:
            return False
        try:
            return Path(p).exists()
        except OSError:
            return False

    return AtmManifest(
        crism_dir=c,
        mastcamz_dir=m,
        meda_dir=md,
        crism_present=_present(crism_dir),
        mastcamz_files=sum(1 for _ in m.rglob("*") if _.is_file()) if m.exists() else 0,
        meda_present=_present(meda_dir),
        missing_dirs=missing,
    )
