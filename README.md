# mars-atm-inversion — Phase 0 prototype

CPU-only **rover-anchored benchmarking** of CRISM atmospheric correction methods, with Mastcam-Z as vicarious calibration ground truth.

> *"Idea 05 — ATM-INVERSION reduced. ★3.5 / Tier 2 backup (Icarus benchmark)"* (`CARSON_FINAL_5IDEA_VERDICT.md` §6.2).
> Phase 0 prototype = pipeline skeleton + 4 correction tournament on synthetic CRISM. Real Jezero CRISM ingest + Plebani 2022 / Saranathan 2024 deep unmixing 비교는 Carson 후속 (390-520h).

## Status

| Gate | Target | Result |
|---|---|---|
| G1 unit + integration tests | ≥10 pass | **28 pass** |
| G2 synthetic smoke wall-clock | <60s | **~2s** |
| G3 ≥1 correction beats 'none' baseline | binding | **2 winners (beer_lambert + lambert_albedo)** |
| G4 src coverage | >60% | **69%** |
| G5 real dry-run handles missing dirs | graceful | **OK** |

### Tournament 결과 (synthetic, τ_true=0.5, airmass=1.41)

| rank | method | RMSE ↓ | cos ↑ |
|---:|---|---:|---:|
| **1** | **beer_lambert**   | **0.0180** | 0.988 |
| 2 | lambert_albedo  | 0.0232 | 0.983 |
| 3 | none (baseline) | 0.0721 | 0.992 |
| 4 | volcano_scan    | 0.0808 | 0.983 |

**중요한 finding**: cosine sim은 atmospheric attenuation (multiplicative)에 invariant이라 `none`이 cos=0.992로 최상으로 보임. 하지만 RMSE에선 beer_lambert가 4× 낮음 — atmospheric correction의 *amplitude* 효과를 정확히 측정하려면 RMSE primary 사용. tournament에 binding.

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

CPU-only — no DISORT 풀 RT, no deep unmixing (Plebani 2022 / Saranathan 2024 OOS Phase 0).

## Run

```bash
# synthetic (default)
python run.py --synthetic

# real dry-run
python run.py --real --dry-run \
    --crism    /disk1/cspark/mastcam/data/CRISM \
    --mastcamz /disk1/cspark/mastcam/coregister_data/output/mastcamz
```

Output:
- `artifacts/anchor_scores.json` — per-method cosine + RMSE
- `artifacts/ranking.json` — tournament + winners vs 'none'
- `artifacts/corrections.npz` — clean_truth, toa_cube, corrected per method
- `logs/atm_inversion.log`

## Layout

```
src/
├── constants.py        CRISM/Mastcam-Z bands, default τ/airmass
├── data/
│   ├── synthetic.py    clean ground reflectance + Beer-Lambert TOA + anchor
│   └── real_reader.py  Carson-pipeline manifest (Phase 0: dry-run)
├── corrections/
│   ├── base.py         uniform interface + dispatcher
│   ├── none.py         control: pass-through
│   ├── volcano_scan.py column-ratio proxy (McGuire 2009 simplified)
│   ├── beer_lambert.py R = (TOA - diffuse) / exp(-τ × airmass)
│   └── lambert_albedo.py 2-stream Eddington proxy
├── anchor/
│   └── consistency.py  CRISM cube → Mastcam-Z 11-band projection + cos + RMSE
├── eval/
│   └── tournament.py   rank by RMSE primary (cos invariant to atmospheric scaling)
└── utils/              seed, io, logging, cpu-only guard
```

See `ARCHITECTURE.md`, `PRD.md`, `DECISIONS.md`, `TODO.md`.

## What this is *not*

- **Not paper-ready**. Synthetic CRISM scene is a smooth Gaussian-basis spectra, not real Jezero mineralogy.
- volcano_scan은 McGuire 2009 *simplified proxy* (column-ratio reference subtraction), 진짜 column-ratio는 Carson 후속.
- lambert_albedo는 2-stream Eddington *proxy*, 진짜 DISORT-Lambert는 multi-scattering chain 필요 (codex §A1-2).
- Real CRISM IF cube ingest + Plebani 2022 unmixing 비교는 Carson Phase 1.

## Spec sources

1. `~/mars-auto/context/CARSON_FINAL_5IDEA_VERDICT.md` §6.2 — Tier 2 backup
2. `~/mars-auto/context/ATM_INVERSION_DESIGN.md` §4 Track A + §6 PRD
3. `~/mars-auto/context/codex-atm-inversion-deepdive.md` Phase A — full prior art (McGuire 2009, Wolff 2014, Plebani 2022)
4. `/disk1/cspark/mastcam/research/{00..09}_*.md` + `SUMMARY.md` — Carson 도메인

License: research prototype.
