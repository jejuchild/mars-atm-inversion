"""Real-data Mastcam-Z radiance variability diagnostic across sols.

Honest framing per codex plan: no CRISM, no MEDA, no THEMIS locally. The
original 4-correction tournament can't run on real data. Reduced scope:
diagnostic table of per-sol Mastcam-Z LEFT radiance variability (mean, median,
IQR, robust coefficient of variation = IQR/median). This is a pre-step for any
future atmospheric correction work, not the correction itself.

Inputs:  /disk1/cspark/mastcam/coregister_data/pds_cache/mastcamz/sol{N}/ZLF_*RASLN*.IMG
Outputs: artifacts_real/real_radiance_diagnostic.json + figure
"""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.utils.io import ensure_dir, write_json
from src.utils.logging import setup_logging

DEFAULT_MASTCAMZ = "/disk1/cspark/mastcam/coregister_data/pds_cache/mastcamz"


def parse_pds4_xml(xml_path: Path) -> dict:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    info = {"path": str(xml_path), "axes": []}

    def find_text(name: str):
        for el in root.iter():
            tag = el.tag.split("}")[-1]
            if tag == name:
                return (el.text or "").strip()
        return None

    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag == "Axis_Array":
            axis = {}
            for c in el:
                ctag = c.tag.split("}")[-1]
                axis[ctag] = (c.text or "").strip()
            info["axes"].append(axis)
    info["data_type"] = find_text("data_type")
    info["offset"] = int(find_text("offset") or 0)
    return info


def parse_mastcamz_array(xml_path: Path) -> dict:
    """Parse Mars2020 Mastcam-Z PDS4 Array_3D_Image block.

    Returns dict with bands, lines, samples, dtype, offset, scaling_factor, value_offset.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    info = {"bands": None, "lines": None, "samples": None,
            "dtype": ">i2", "offset": 0, "scaling_factor": 1.0, "value_offset": 0.0}
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag == "Array_3D_Image":
            for c in el.iter():
                ctag = c.tag.split("}")[-1]
                if ctag == "offset" and c.text:
                    info["offset"] = int(c.text.strip())
                elif ctag == "Element_Array":
                    for cc in c:
                        cct = cc.tag.split("}")[-1]
                        if cct == "data_type":
                            info["dtype_str"] = (cc.text or "").strip()
                        elif cct == "scaling_factor" and cc.text:
                            info["scaling_factor"] = float(cc.text.strip())
                        elif cct == "value_offset" and cc.text:
                            info["value_offset"] = float(cc.text.strip())
                elif ctag == "Axis_Array":
                    name = ""
                    elems = 0
                    for cc in c:
                        cct = cc.tag.split("}")[-1]
                        if cct == "axis_name":
                            name = (cc.text or "").strip().lower()
                        elif cct == "elements":
                            elems = int((cc.text or "0").strip())
                    if name == "band":
                        info["bands"] = elems
                    elif name == "line":
                        info["lines"] = elems
                    elif name == "sample":
                        info["samples"] = elems
            break
    dt_str = info.get("dtype_str", "")
    if dt_str == "SignedMSB2":
        info["dtype"] = ">i2"
    elif dt_str == "SignedLSB2":
        info["dtype"] = "<i2"
    elif dt_str == "UnsignedMSB2":
        info["dtype"] = ">u2"
    elif dt_str == "IEEE754MSBSingle":
        info["dtype"] = ">f4"
    return info


def read_radiance_img(img_path: Path) -> np.ndarray | None:
    """Read RASLN 3-band radiance, return float32 (B, L, S) in physical units."""
    xml_path = img_path.with_suffix(".xml")
    if not xml_path.exists():
        return None
    meta = parse_mastcamz_array(xml_path)
    bands, lines, samples = meta["bands"], meta["lines"], meta["samples"]
    if not (bands and lines and samples):
        return None
    n = bands * lines * samples
    try:
        raw = np.fromfile(img_path, dtype=meta["dtype"], count=n, offset=meta["offset"])
        if raw.size != n:
            return None
        arr = raw.reshape(bands, lines, samples).astype(np.float32)
        arr = arr * float(meta["scaling_factor"]) + float(meta["value_offset"])
        return arr
    except Exception:
        return None


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--mastcamz", default=DEFAULT_MASTCAMZ)
    p.add_argument("--max-files-per-sol", type=int, default=2)
    p.add_argument("--max-sols", type=int, default=40)
    p.add_argument("--artifacts", default=str(ROOT / "artifacts_real"))
    return p.parse_args()


def main() -> int:
    args = parse_args()
    log = setup_logging(log_dir=ROOT / "logs", name="atm_inversion_real")

    sol_dirs = sorted(Path(args.mastcamz).glob("sol*"))
    log.info("Found %d Mastcam-Z sol directories", len(sol_dirs))

    per_file = []
    per_sol = {}
    for sd in sol_dirs[: args.max_sols]:
        sol_id = sd.name
        rasln_files = sorted(sd.glob("ZLF_*RASLN*.IMG"))[: args.max_files_per_sol]
        sol_means = []
        for f in rasln_files:
            arr = read_radiance_img(f)  # (B, L, S) for 3-band Bayer R/G/B
            if arr is None:
                continue
            cube_mean = arr.mean(axis=0)  # collapse 3 bands → average radiance per pixel
            valid = cube_mean[(cube_mean > 0) & np.isfinite(cube_mean)]
            if len(valid) < 1000:
                continue
            mn = float(valid.mean())
            md = float(np.median(valid))
            std = float(valid.std())
            q25 = float(np.percentile(valid, 25))
            q75 = float(np.percentile(valid, 75))
            iqr = q75 - q25
            cv_robust = float(iqr / max(abs(md), 1e-9))
            per_band = []
            for b in range(arr.shape[0]):
                bv = arr[b][(arr[b] > 0) & np.isfinite(arr[b])]
                if len(bv) > 100:
                    per_band.append({"band": b, "mean": float(bv.mean()), "median": float(np.median(bv))})
            per_file.append({
                "file": f.name,
                "sol": sol_id,
                "shape": list(arr.shape),
                "n_valid": int(len(valid)),
                "mean": mn,
                "median": md,
                "std": std,
                "p25": q25,
                "p75": q75,
                "iqr": iqr,
                "robust_cv": cv_robust,
                "per_band": per_band,
            })
            sol_means.append(mn)
        if sol_means:
            per_sol[sol_id] = {
                "n_files": len(sol_means),
                "mean_radiance": float(np.mean(sol_means)),
                "std_across_files": float(np.std(sol_means)) if len(sol_means) > 1 else 0.0,
            }

    if not per_file:
        log.error("no RASLN files successfully read")
        return 1

    means = np.array([r["mean"] for r in per_file], dtype=np.float64)
    medians = np.array([r["median"] for r in per_file], dtype=np.float64)
    iqrs = np.array([r["iqr"] for r in per_file], dtype=np.float64)
    cvs = np.array([r["robust_cv"] for r in per_file], dtype=np.float64)

    summary = {
        "n_files_total": len(per_file),
        "n_sols_with_files": len(per_sol),
        "radiance_unit": "W/m²/sr/nm (Mastcam-Z RASLN, calibrated)",
        "global_stats": {
            "mean_of_means": float(means.mean()),
            "std_of_means": float(means.std()),
            "median_of_medians": float(np.median(medians)),
            "mean_iqr": float(iqrs.mean()),
            "mean_robust_cv": float(cvs.mean()),
            "std_robust_cv": float(cvs.std()),
            "min_robust_cv": float(cvs.min()),
            "max_robust_cv": float(cvs.max()),
        },
        "per_sol": per_sol,
        "per_file_top10_lowest_cv": sorted(per_file, key=lambda d: d["robust_cv"])[:10],
        "per_file_top10_highest_cv": sorted(per_file, key=lambda d: -d["robust_cv"])[:10],
        "honesty_note": (
            "CRISM is not locally available, so the 4-method correction tournament "
            "cannot run on real data. This diagnostic reports per-image radiance "
            "variability (robust_cv = IQR / |median|) across Mastcam-Z LEFT RASLN "
            "products, which is a precondition signal for atmospheric correction "
            "(high CV across sols hints at illumination/atmospheric variation that "
            "any future correction would need to handle)."
        ),
    }
    artifacts = ensure_dir(args.artifacts)
    write_json(summary, artifacts / "real_radiance_diagnostic.json")
    log.info("Files=%d, sols=%d, mean robust_cv=%.3f, std robust_cv=%.3f",
             summary["n_files_total"], summary["n_sols_with_files"],
             summary["global_stats"]["mean_robust_cv"],
             summary["global_stats"]["std_robust_cv"])
    log.info("Wrote %s", artifacts / "real_radiance_diagnostic.json")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        sols_chrono = sorted(per_sol.keys())
        sol_means_chrono = [per_sol[s]["mean_radiance"] for s in sols_chrono]
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        axes[0].plot(range(len(sols_chrono)), sol_means_chrono, "o-", color="darkorange")
        axes[0].set_xticks(range(len(sols_chrono)))
        axes[0].set_xticklabels([s.replace("sol", "") for s in sols_chrono], rotation=45, fontsize=7)
        axes[0].set_xlabel("sol")
        axes[0].set_ylabel("Mean radiance (W/m²/sr/nm)")
        axes[0].set_title(f"Per-sol mean Mastcam-Z LEFT radiance ({len(sols_chrono)} sols)")
        axes[0].grid(alpha=0.3)

        axes[1].hist(cvs, bins=20, color="purple", edgecolor="black")
        axes[1].axvline(cvs.mean(), color="red", linestyle="--", label=f"mean={cvs.mean():.3f}")
        axes[1].set_xlabel("Robust CV (IQR/|median|)")
        axes[1].set_ylabel("# files")
        axes[1].set_title(f"Robust CV distribution ({len(per_file)} files)")
        axes[1].legend()

        fig.tight_layout()
        fig.savefig(artifacts / "real_radiance_diagnostic.png", dpi=120, bbox_inches="tight")
        plt.close(fig)
        log.info("Wrote figure: %s", artifacts / "real_radiance_diagnostic.png")
    except Exception as e:
        log.warning("figure failed: %s", e)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
