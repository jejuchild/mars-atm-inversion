"""End-to-end Phase 0 pipeline: synthetic CRISM atm-correction tournament + Mastcam-Z anchor."""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.anchor.consistency import cosine_consistency
from src.corrections import REGISTRY
from src.corrections.base import correct
from src.data.real_reader import discover_atm_inputs
from src.data.synthetic import make_atm_scene
from src.eval.tournament import beats_baseline, rank_methods
from src.utils.checks import RuntimeBudget, assert_allowed_method, assert_cpu_only
from src.utils.io import dump_npz, ensure_dir, read_yaml, write_json
from src.utils.logging import setup_logging
from src.utils.seed import set_global_seed


def parse_args():
    p = argparse.ArgumentParser(description="mars-atm-inversion Phase 0 pipeline")
    p.add_argument("--config", default="configs/phase0.yaml")
    p.add_argument("--synthetic", action="store_true")
    p.add_argument("--real", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--crism", default=None)
    p.add_argument("--mastcamz", default=None)
    p.add_argument("--seed", type=int, default=None)
    return p.parse_args()


def run_synthetic(cfg: dict, log) -> int:
    budget = RuntimeBudget(cfg["runtime"]["budget_seconds"])
    syn = cfg["data"]["synthetic"]
    log.info("Generating synthetic CRISM scene H=%d W=%d K=%d τ=%.2f airmass=%.2f",
             syn["height"], syn["width"], syn["n_bands"], syn["tau_true"], syn["airmass"])
    scene = make_atm_scene(
        height=syn["height"], width=syn["width"],
        n_bands=syn["n_bands"], n_anchors=syn["n_anchors"],
        tau_true=syn["tau_true"], airmass=syn["airmass"],
        noise=syn["noise"], seed=cfg["seed"],
    )

    cubes = {}
    records = {}
    for method in cfg["corrections"]["enabled"]:
        assert_allowed_method(method)
        kwargs = cfg["corrections"].get(method, {}) or {}
        log.info("Running correction=%s ...", method)
        t0 = time.perf_counter()
        corrected = correct(method, scene.toa_cube, **kwargs)
        elapsed = time.perf_counter() - t0
        score = cosine_consistency(
            corrected_cube=corrected,
            crism_lambda_nm=scene.crism_lambda_nm,
            anchor_xy=scene.anchor_xy,
            anchor_spec_mz=scene.anchor_spec_mz,
        )
        cubes[method] = corrected
        records[method] = {
            "cos_mean": score["cos_mean"],
            "rmse_mean": score["rmse_mean"],
            "n_anchors": score["n_anchors"],
            "elapsed_s": round(elapsed, 3),
        }
        log.info("  %s: cos=%.3f rmse=%.4f t=%.3fs",
                 method, score["cos_mean"], score["rmse_mean"], elapsed)
        budget.check()

    ranking = rank_methods(records)
    winners = beats_baseline(records, baseline="none")
    log.info("Tournament ranking: %s", [r["method"] for r in ranking])
    log.info("Methods beating 'none' baseline: %s", winners)

    artifacts = ensure_dir(ROOT / cfg["output"]["artifacts_dir"])
    write_json(records, artifacts / "anchor_scores.json")
    write_json({"ranking": ranking, "winners_vs_none": winners}, artifacts / "ranking.json")
    dump_npz(
        artifacts / "corrections.npz",
        clean_truth=scene.clean_truth,
        toa_cube=scene.toa_cube,
        crism_lambda=scene.crism_lambda_nm,
        anchor_xy=scene.anchor_xy,
        anchor_spec_mz=scene.anchor_spec_mz,
        **{f"corrected_{k}": v for k, v in cubes.items()},
    )
    log.info("Wrote artifacts to %s", artifacts)

    g3_finite = all(np.isfinite(records[m]["cos_mean"]) for m in records)
    g3_winners = len(winners) >= 1
    if g3_finite and g3_winners:
        log.info("PASS: 4 methods finite + %d correction(s) beat 'none' baseline (%s)",
                 len(winners), winners)
        return 0
    log.error("G3 FAIL: finite=%s winners=%s", g3_finite, winners)
    return 1


def run_real(cfg: dict, args, log) -> int:
    real = cfg["data"]["real"]
    c = args.crism or real["crism_dir"]
    m = args.mastcamz or real["mastcamz_dir"]
    log.info("Real-data manifest discovery: crism=%s mastcamz=%s", c, m)
    manifest = discover_atm_inputs(crism_dir=c, mastcamz_dir=m, meda_dir=real.get("meda_dir"))
    log.info("Manifest: crism_present=%s mastcamz_files=%d meda_present=%s",
             manifest.crism_present, manifest.mastcamz_files, manifest.meda_present)
    if manifest.missing_dirs:
        log.warning("Missing input dirs: %s", manifest.missing_dirs)
    if args.dry_run:
        log.info("Dry-run only — full real ingest is Carson follow-up (Phase 1+).")
        return 0
    log.error("Real-data full pipeline not implemented in Phase 0.")
    raise NotImplementedError("Phase 0: real ingest is Carson follow-up; pass --dry-run.")


def main() -> int:
    assert_cpu_only()
    args = parse_args()
    cfg_path = ROOT / args.config
    cfg = read_yaml(cfg_path)
    if args.seed is not None:
        cfg["seed"] = args.seed
    set_global_seed(cfg["seed"])
    log_dir = ROOT / cfg["output"]["log_dir"]
    log = setup_logging(log_dir=log_dir, name="atm_inversion")
    log.info("config=%s seed=%d", cfg_path.name, cfg["seed"])
    if args.real:
        cfg["data"]["mode"] = "real"
        return run_real(cfg, args, log)
    cfg["data"]["mode"] = "synthetic"
    return run_synthetic(cfg, log)


if __name__ == "__main__":
    raise SystemExit(main())
