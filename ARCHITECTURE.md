# ARCHITECTURE — `mars-atm-inversion` Phase 0 prototype

작성: 2026-05-06 (Phase 2)
Codex Phase 2 critique: **skipped this round** (DECISIONS D24). 본 prototype scope (4 closed-form correction + 1 anchor metric)는 충분히 구체적이라 solo로 진행. MD §⑧.3 fallback 적용. Carson Phase 1에선 codex re-review 권장.

## 1. CRITICAL self-check

- ✅ no DISORT 풀 RT 학습 (MD §⑥.5 명시 금지)
- ✅ no deep unmixing (Plebani / Saranathan은 Carson 후속)
- ✅ synthetic primary, real dry-run only
- ✅ 4 correction은 numpy/scipy closed-form
- ✅ Mastcam-Z anchor 일관성으로 tournament

## 2. Module tree

```
ideas/05-atm-inversion/
├── PRD.md / ARCHITECTURE.md / README.md / DECISIONS.md / TODO.md / requirements.txt
├── configs/
│   └── phase0.yaml
├── src/
│   ├── __init__.py
│   ├── constants.py      # CRISM band centers (synth), Mastcam-Z bands, default τ/airmass
│   ├── data/
│   │   ├── __init__.py
│   │   ├── synthetic.py  # PRIMARY: clean ground + atmospheric attenuation + Mastcam-Z anchors
│   │   └── real_reader.py# Carson-pipeline manifest (dry-run)
│   ├── corrections/
│   │   ├── __init__.py
│   │   ├── base.py       # uniform interface: correct(toa_cube, params) -> corrected_cube
│   │   ├── none.py       # control: pass-through
│   │   ├── volcano_scan.py
│   │   ├── beer_lambert.py
│   │   └── lambert_albedo.py
│   ├── anchor/
│   │   ├── __init__.py
│   │   └── consistency.py# CRISM cube → Mastcam-Z 11-band projection + cos sim + RMSE
│   ├── eval/
│   │   ├── __init__.py
│   │   └── tournament.py # rank methods by anchor metric
│   └── utils/
│       ├── seed.py / io.py / logging.py / checks.py
├── tests/
└── run.py
```

## 3. Data flow

### Synthetic (primary)

```
configs/phase0.yaml
  → utils.seed.set_global_seed(42)
  → data.synthetic.make_atm_scene(
        H=64, W=64, K=30, n_anchors=5, tau_true=0.5, airmass=1.41, seed=42)
       returns:
         clean_truth     (H, W, K)        ground reflectance ground truth
         toa_cube        (H, W, K)        observed at top-of-atmosphere (attenuated)
         tau_field       (H, W) or scalar atmospheric optical depth
         airmass_field   scalar
         crism_lambda    (K,)             band centers
         anchor_xy       (N, 2)           int row, col
         anchor_spec_mz  (N, 11)          Mastcam-Z 11-band ground truth
  → for method in [none, volcano_scan, beer_lambert, lambert_albedo]:
       corrected = corrections.method.correct(toa_cube, tau_field, airmass)
       projected_at_anchor = anchor.consistency.project_and_sample(corrected, anchor_xy, crism_lambda)
       cos, rmse = anchor.consistency.score(projected_at_anchor, anchor_spec_mz)
       record(method, cos, rmse)
  → eval.tournament.rank(records) → sorted table; 'none' baseline 비교
  → io: corrections.npz + anchor_scores.json + ranking.json
```

### Real (dry-run inventory)

```
data.real_reader.discover_atm_inputs(crism, mastcamz, meda)
  → manifest dict
  → if --dry-run: print + exit 0
```

## 4. CPU-only guards

1. `assert_cpu_only()`
2. config-level whitelist: methods ∈ {none, volcano_scan, beer_lambert, lambert_albedo}
3. K (band count) cap 100
4. H × W cap 256 (CPU memory)
5. no torch.cuda usage anywhere

## 5. Sub-phase split

| sub-phase | 모듈 | acceptance | tag |
|---|---|---|---|
| **3a** | `data/{synthetic,real_reader}.py`, `constants.py`, `utils/*.py`, `configs/phase0.yaml` | `pytest tests/test_synthetic.py -v` ≥3 pass | -3a-done |
| **3b** | `corrections/{base,none,volcano_scan,beer_lambert,lambert_albedo}.py` | `pytest tests/test_corrections.py -v` ≥4 pass (1/method) | -3b-done |
| **3c** | `anchor/consistency.py` | `pytest tests/test_anchor.py -v` ≥3 pass | -3c-done |
| **3d** | `eval/tournament.py` | `pytest tests/test_tournament.py -v` ≥3 pass | -3d-done |
| **3e** | `run.py` integration + `tests/test_smoke_run.py` | smoke <60s, ≥1 correction의 anchor cos > none baseline | -3-done |

## 6. configs/phase0.yaml schema

```yaml
seed: 42
data:
  mode: synthetic
  synthetic:
    height: 64
    width: 64
    n_bands: 30
    n_anchors: 5
    tau_true: 0.5
    airmass: 1.41
    noise: 0.01
  real:
    crism_dir: ../../data/CRISM
    mastcamz_dir: ../../data/Mastcam-Z
    meda_dir: ../../data/MEDA
corrections:
  enabled: [none, volcano_scan, beer_lambert, lambert_albedo]
  beer_lambert:
    tau_estimate: 0.5
    airmass: 1.41
  lambert_albedo:
    tau_estimate: 0.5
    airmass: 1.41
    surface_albedo_init: 0.25
  volcano_scan:
    reference_pixels: corner   # one of: corner | percentile
    reference_percentile: 5    # bottom 5% mean used as atmosphere column proxy
anchor:
  metric: cosine
runtime:
  cpu_only: true
  budget_seconds: 60
output:
  artifacts_dir: artifacts
  log_dir: logs
```

## 7. Test coverage (G4 ≥60%)

| 모듈 | tests | boundary |
|---|---|---|
| data/synthetic | shapes, determinism, attenuation > 0 | n_bands=1 |
| data/real_reader | dry-run | missing dirs |
| corrections/* | each correct() preserves shape + finite | edge τ=0 |
| anchor/consistency | self-cos = 1 + RMSE = 0 | empty anchor |
| eval/tournament | rank stable + 'none' as baseline | ties handled |
| run.py | smoke <60s + ≥1 correction beats none | dry-run |

## 8. Out-of-scope reaffirm

- No DISORT / Wolff 2014 / Plebani 2022 / Saranathan 2024
- No real CRISM IF cube ingest
- No MEDA τ time series
- No mineral unmixing accuracy comparison
- No Gale crater out-of-Jezero transfer

---

**End of ARCHITECTURE.**
