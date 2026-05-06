# PRD — `mars-atm-inversion` Phase 0 prototype

작성: 2026-05-06 (overnight smoke test, idea 05)
참조 spec: `~/mars-auto/context/ATM_INVERSION_DESIGN.md` §6 Phase 0 + `codex-atm-inversion-deepdive.md` Phase A/B + MARS_AUTO_OVERNIGHT.md §⑥.5
범위: **Phase 0 prototype skeleton (CPU-only, classical correction comparison + Mastcam-Z anchor, 30분 phase budget cap)**

## 1. Problem statement

CRISM 대기 보정 family (volcano-scan / DISORT-Lambert / Plebani 2022 / Saranathan 2024 / ATREM)는 4-5종 존재하지만 정량 비교가 부족. **Mastcam-Z를 vicarious calibration anchor**로 두면 같은 Jezero patch에서 어느 보정 방법이 가장 정확한지 tournament 가능. 이게 paper의 본질.

> *"Rover-Anchored Benchmarking of CRISM Atmospheric Correction at Jezero"* — Icarus benchmark short paper (`CARSON_FINAL_5IDEA_VERDICT.md` §6.2). Tier 2 backup, ★3.5.

**Carson 강점 ★4-5**: HiRISE↔Mastcam-Z 정합 + SAR atmospheric correction transfer 직관 (codex §A3-3 Bruegge 2019 vicarious cal과 동일 framework).

## 2. Goals / Non-goals

### Goals (Phase 0 prototype, CPU-only synthetic)
- end-to-end pipeline: synthetic CRISM TOA + Mastcam-Z anchor → 4 correction → per-method anchor consistency tournament
- **4 correction methods** (모두 numpy/scipy):
  1. **none** (control: TOA reflectance 그대로)
  2. **volcano_scan** (column-ratio reference target subtraction proxy, McGuire 2009 §A1-1 simplified)
  3. **beer_lambert** (단순 Beer-Lambert: R_surf = R_TOA / exp(-τ × airmass))
  4. **lambert_albedo** (DISORT-Lambert proxy: 2-stream approximation closed-form)
- **anchor consistency**: corrected CRISM spectrum projected to Mastcam-Z bands → cosine sim + RMSE vs Mastcam-Z observation
- **per-method ranking**: tournament table with Mastcam-Z anchor as ground truth
- 모든 unit test pass (≥10)

### Non-goals (Phase 0)
- DISORT 풀 RT 학습 (MD §⑥.5 명시 금지, 계산 무거움)
- Plebani 2022 / Saranathan 2024 deep unmixing — Carson 후속 (Track B in design doc §4)
- Real CRISM IF cube ingest (학교서버 부재, synthetic fallback)
- MEDA τ 시계열 정합 (Carson 후속)
- Wolff 2014 atmospheric model 풀 implementation (codex §A1 reference만)
- Mineral unmixing accuracy improvement quantification (Phase 1 gate, OOS Phase 0)
- Out-of-Jezero transferability (Gale crater) — Phase 2

## 3. Inputs

| 입력 | 경로 | shape | optional |
|---|---|---|---|
| CRISM TOA reflectance cube | `data/CRISM/` (부재) | `(H, W, K)` float32 | required (synth) |
| Mastcam-Z 11-band anchor | `data/Mastcam-Z/` | `(N_a, 11)` float32 | required |
| Atmospheric τ (per-pixel or per-scene) | config or `data/MEDA/` (부재) | scalar or `(H, W)` | required |
| Solar / view geometry | config | airmass scalar | required |
| (option) HiRISE patch | `data/HiRISE/` | `(H, W, 3)` | optional |

## 4. Outputs

| 산출물 | 경로 | 형식 |
|---|---|---|
| corrected CRISM cubes per method | `artifacts/corrections.npz` | float32 `(H, W, K)` × N_methods |
| per-method anchor consistency | `artifacts/anchor_scores.json` | `{method: cos_sim, rmse, rank}` |
| tournament ranking | `artifacts/ranking.json` | sorted method list + tie-breaks |
| run log | `logs/atm_inversion.log` | text |

## 5. Success criteria (binding for Phase 0 prototype)

- [G1] `pytest -v` 모든 test pass (≥10 tests)
- [G2] `python run.py --synthetic` smoke run < 60s (CPU)
- [G3] **모든 4 correction이 finite spectrum 산출** + **at least one correction의 anchor cos sim > none baseline** (synthetic, true τ given)
- [G4] coverage > 60% (`pytest --cov=src`)
- [G5] `python run.py --real --dry-run` graceful (CRISM/MEDA 부재 OK)

## 6. Pipeline (5-step)

1. **Ingest**: synthetic scene generator (clean ground reflectance + atmospheric attenuation + Mastcam-Z anchor) 또는 real reader (dry-run only)
2. **Correct**: 4 method 적용 → per-method `corrected = f(TOA, τ, geometry)`
3. **Project**: corrected CRISM (K-band) → Mastcam-Z 11-band centers (linear interp)
4. **Score**: per-method cosine sim + RMSE vs Mastcam-Z anchor at anchor pixels
5. **Rank**: tournament table; "none" baseline은 reference, 적어도 한 correction이 이김

## 7. Architecture preview (Phase 2에서 정식)

```
ideas/05-atm-inversion/
├── src/
│   ├── data/         # synthetic + real_reader
│   ├── corrections/  # none, volcano_scan, beer_lambert, lambert_albedo
│   ├── anchor/       # Mastcam-Z 11-band projection + cosine + RMSE
│   ├── eval/         # tournament + ranking
│   └── utils/
├── tests/
├── configs/phase0.yaml
└── run.py
```

## 8. Out of scope (overnight prototype)

- DISORT 풀 RT 코드 (codex §A1-2 McGuire DISORT)
- Plebani 2022 deep unmixing / Saranathan 2024 BLU
- Real CRISM IF ingest (rasterio)
- MEDA τ 시계열 정합
- Out-of-Jezero transferability (Gale)
- Wolff 2014 multi-scattering full forward model

## 9. Carson 강점 sell (★4-5)

- **HiRISE↔Mastcam-Z 정합 → Mastcam-Z anchor 위치 정확**: real_reader가 Carson pipeline output 그대로 인식
- **SAR atmospheric correction 경험 → Beer-Lambert / 2-stream approx 직관**: `corrections/beer_lambert.py` SAR-style API
- **Vicarious calibration framework** (codex §A3-3 Bruegge 2019, codex §A5-4) — Earth-Mars cross-reference 직접 transfer

## 10. Open decisions (autonomous default → DECISIONS.md)

1. CRISM band count = 30 (synthetic, 400-2500 nm range)
2. atmospheric τ default 0.5 (Mars typical)
3. airmass default = 1 / cos(45°) ≈ 1.41 (mid-latitude)
4. anchor count = 5 (synthetic random patches)
5. lambert_albedo: 2-stream Eddington approximation (Liou 2002 §6.3 closed-form)
6. volcano_scan proxy: subtract median spectrum of "atmosphere reference" pixels (low-elevation atmosphere column proxy)

## 11. Risks (Phase 0 prototype 수준)

| Risk | 확률 | mitigation |
|---|---|---|
| 4 correction 모두 비슷한 결과 → tournament 무의미 | 중 | synthetic scene이 의도적으로 atmospheric attenuation 강하게 (τ=0.5+) |
| Mastcam-Z anchor projection 정확도 | 낮 | 단순 linear interp (idea 02와 동일 규약) |
| Beer-Lambert with airmass 부호 오류 | 낮 | unit test on known-τ recovery |

---

**End of PRD.**
