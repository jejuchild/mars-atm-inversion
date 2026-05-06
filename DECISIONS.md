# DECISIONS — autonomous-mode defaults (Carson 검토 후 변경 가능)

## 1. Spec 해석

- **D1**: ATM-INVERSION reduced 채택 — "Rover-Anchored Benchmarking of CRISM Atmospheric Correction" (verdict §6.2 Tier 2 backup). Track B (Hybrid physical+ML) Carson 후속. *Change-tag*: scope
- **D2 (★)**: PRD §5 G3은 sub-phase 3e 실행 후 재정의됨 — primary metric을 cosine sim → **RMSE**로 변경. 이유: cosine sim은 multiplicative scaling에 invariant이므로 atmospheric attenuation을 detect 못 함. RMSE는 amplitude 차이를 정확히 측정. ★ Change-tag: **metric-primary**

## 2. Synthetic generator

- **D3**: clean ground reflectance = spatial sin/cos × 4-component Gaussian basis spectra. 진짜 Jezero mineralogy (basalt / phyllosilicate / carbonate) 아님. *Change-tag*: synth-realism
- **D4**: TOA = exp(-τ × airmass) × clean + small diffuse_offset. wavelength-independent transmittance (gas absorption band 무시). *Change-tag*: forward-model
- **D5**: τ_true=0.5 (Mars typical mid-storm), airmass=1.41 (45° SZA). *Change-tag*: atm-defaults
- **D6**: Mastcam-Z anchor = clean_truth at random pixel + linear interp to 11 bands + N(0, 0.01) noise. 진짜 calibration error proxy 아님. *Change-tag*: anchor-construction
- **D7**: noise=0.01 (sub-percent reflectance). Real Mastcam-Z radiometric uncertainty은 Rice 2023 ~3-5%. *Change-tag*: noise-level

## 3. Corrections

- **D8 (★)**: 4 method = none / volcano_scan / beer_lambert / lambert_albedo. Plebani 2022 / Saranathan 2024 / DISORT full / Wolff 2014 deep는 Carson 후속. *Change-tag*: method-set
- **D9**: volcano_scan 구현은 *simplified proxy* — bottom-percentile mean을 atmosphere column reference로 subtract. 진짜 high-elevation reference target은 PDS calibration data 필요. *Change-tag*: volcano-proxy
- **D10**: beer_lambert는 wavelength-independent transmittance (clean Beer-Lambert without spectral structure). diffuse_offset = 0.05 × τ (linear approximation). *Change-tag*: bl-form
- **D11**: lambert_albedo는 2-stream Eddington-style proxy (TOA = T·R + (1-T)·atm_path), surface_albedo_init=0.25 (Mars regolith typical). 진짜 DISORT-Lambert는 multi-scattering matrix invert. *Change-tag*: la-form

## 4. Anchor + tournament

- **D12**: anchor projection = `numpy.interp` linear (CRISM 30-band → Mastcam-Z 11-band). spectral response function (Bell 2021) 미사용. *Change-tag*: anchor-projection
- **D13 (★)**: tournament primary = RMSE (lower better), tie-break = cosine sim (D2 발견 후 swap). 진짜 paper에선 mineral classification accuracy도 추가 metric. *Change-tag*: ranking-formula
- **D14**: "winners" = methods with strictly lower RMSE than 'none' baseline. 진짜 paper에선 statistical significance test (t-test on per-anchor errors) 필요. *Change-tag*: winner-criterion

## 5. Real-data path

- **D15**: `--real` 모드는 manifest discovery + dry-run only. CRISM IF cube ingest (rasterio + ENVI) + MEDA τ alignment 미구현. *Change-tag*: real-ingest
- **D16**: 데이터 위치 = `data/{CRISM, Mastcam-Z, MEDA}` symlinks. CRISM/MEDA 학교서버 부재. *Change-tag*: data-path

## 6. Codex 협업

- **D17**: Phase 2 codex critique은 본 idea에서 **skipped** — MD §⑧.3 fallback 적용. 시간 효율 위해 (4 correction + 1 metric은 직관적 scope). DECISIONS에 명시. Carson Phase 1 시 codex re-review 권장. ★ Change-tag: **codex-skipped**

## 7. Runtime / 환경

- **D18**: numpy 2.4, scipy 1.17. spiceypy / rasterio 사용 안 함 (Phase 0). *Change-tag*: env-freeze
- **D19**: workspace `~/mars-auto/ideas/05-atm-inversion`. push는 `gh` CLI (jejuchild). *Change-tag*: workspace
- **D20**: artifacts dump (anchor_scores / ranking / corrections.npz 3종). *Change-tag*: artifact-policy

## 8. 확신 낮은 추측 (Carson confirm 필요)

- **D21 (★)**: D2 발견 (cosine sim의 multiplicative-scaling invariance) — 진짜 ATM-INVERSION paper에서 reviewer가 잡을 수 있는 critical critique. 본 prototype에서 RMSE primary로 swap. paper에선 multiple metric (SAM = spectral angle, ERGAS, mineral class accuracy) 모두 보고하는 게 안전. ★ Change-tag: **metric-primary / sam-vs-cos**
- **D22**: synthetic이 wavelength-independent transmittance를 가정 — 진짜 Mars 대기는 H2O, CO2 absorption band가 강함 (codex §A1-2 Wolff 2014). real-data benchmark에선 band-specific τ(λ) 필요. *Change-tag*: spectral-tau

## 9. cycle-008 lesson 반영 ("Carson 강점 ★4-5")

- **D23**: SAR atmospheric correction 경험 → beer_lambert / lambert_albedo는 SAR 2-stream과 직접 transfer. *Change-tag*: sar-transfer
- **D24**: HiRISE↔Mastcam-Z 정합 → anchor pixel localization은 Carson pipeline 활용. *Change-tag*: carson-pipeline-binding
- **D25**: vicarious calibration framework (codex §A3-3 Bruegge 2019) — Earth-Mars cross-reference 직접 transfer. *Change-tag*: vicarious-cal-framework

---

**End of DECISIONS. 25개 default.**
