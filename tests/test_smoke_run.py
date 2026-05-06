"""Integration smoke: run.py --synthetic completes <60s and meets G3."""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_smoke_synthetic_run():
    artifacts = ROOT / "artifacts"
    if (artifacts / "anchor_scores.json").exists():
        (artifacts / "anchor_scores.json").unlink()
    t0 = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(ROOT / "run.py"), "--synthetic"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    elapsed = time.perf_counter() - t0
    assert proc.returncode == 0, f"run.py exit={proc.returncode}\nSTDERR:\n{proc.stderr}"
    assert elapsed < 60, f"smoke {elapsed:.1f}s exceeds G2 60s"
    with open(artifacts / "anchor_scores.json") as f:
        scores = json.load(f)
    assert set(scores.keys()) == {"none", "volcano_scan", "beer_lambert", "lambert_albedo"}
    with open(artifacts / "ranking.json") as f:
        rank = json.load(f)
    assert "ranking" in rank
    assert len(rank["winners_vs_none"]) >= 1


def test_smoke_real_dry_run(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(ROOT / "run.py"),
         "--real", "--dry-run",
         "--crism", str(tmp_path / "no_c"),
         "--mastcamz", str(tmp_path / "no_m")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, f"dry-run exit={proc.returncode}\nSTDERR:\n{proc.stderr}"
    assert "Missing input dirs" in (proc.stdout + proc.stderr)
