# TODO — Carson 다음 작업 (Phase 1~3, paper-ready)

본 Phase 0 prototype 위에 390-520h 추가 작업 (`ATM_INVERSION_DESIGN.md` §6 reduced timeline + verdict §6.2).

## 즉시 (week 1, ~10h)

- [ ] **DECISIONS.md 검토** — 25개 default. 특히 ★ D2 (metric-primary) + ★ D21 (sam-vs-cos critique) + D17 (codex skipped)
- [ ] **codex Phase 2 re-review** — 본 prototype (4 correction + tournament)에 대해 critique. 특히 D2 metric swap의 정당성 + Plebani 2022 unmixing accuracy를 binding metric으로 추가할지
- [ ] **CRISM Jezero overlap inventory** — FRT000047A3 / FRT00005C5E / HRL000040FF (codex §A1) 의 Mastcam-Z overlap patch 식별

## Phase 1 (week 2-4, ~25h) — Real-data POC on Jezero

- [ ] CRISM TOA reflectance ingest (ENVI / rasterio) — Viviano-Beck 2014 summary parameter 또는 raw cube
- [ ] MEDA τ 시계열 정합 (sol-level) — `data/MEDA/` 확보
- [ ] **Phase 1 gate** (`ATM_INVERSION_DESIGN.md` §6 4지선다):
  - hold-out unmixing 정확도 +5-10% → GO Track A+B (full ambition)
  - +2-5% → GO Track A only (IEEE TGRS short, ~350-400h)
  - +0-2% → PIVOT to "in-situ atmospheric retrieval at Jezero benchmark" (Icarus 부산물)
  - 향상 없음 → KILL

## Phase 2 (month 2-3, ~25h) — Plebani 2022 / Saranathan 2024 비교

- [ ] Plebani 2022 BLU-style spectral unmixing baseline (codex §A4-1)
- [ ] Saranathan 2024 deep unmixing (codex §A4-2) — CPU 가능한 작은 model 우선
- [ ] full DISORT (Wolff 2014 forward model) 추가 (Carson SAR 경험 transfer 강함)
- [ ] mineral classification accuracy를 binding metric으로 추가 (cosine sim alone 부족, D21)

## Phase 3 (month 4-9) — paper / submission

- [ ] paper draft (Icarus benchmark, ~390-520h)
  - title: "Rover-Anchored Benchmarking of CRISM Atmospheric Correction at Jezero"
  - method: 4-6 correction (본 prototype의 4 + DISORT + Plebani BLU) tournament
  - validation: Mastcam-Z anchor + mineral class agreement
  - mission framing: 미래 Mars Sample Return precision targeting

## Engineering follow-up

- [ ] wavelength-dependent τ(λ) (Wolff 2014 model fit) — H2O / CO2 / aerosol bands
- [ ] CRISM IF (radiance / I-over-F) calibration ingest
- [ ] Plebani 2022 BLU sklearn 구현 (codex §A4-1)
- [ ] out-of-Jezero transferability (Gale crater + MSL Mastcam analog)
- [ ] CI: GitHub Actions
- [ ] D9 진짜 column-ratio volcano scan (high-elevation reference target)

## 알려진 한계 (수정 안 함, 명시만)

- D2 cosine sim의 multiplicative-scaling invariance — Reviewer-critical critique
- D9 volcano_scan 단순 proxy. 진짜 column-ratio reference는 PDS data 필요
- D11 lambert_albedo는 2-stream proxy. 진짜 DISORT-Lambert는 multi-scattering chain
- Synthetic은 wavelength-independent transmittance. Real Mars는 H2O/CO2 absorption bands 강함
- 4 correction은 entry-level. paper-ready 단계에선 Plebani 2022 + Saranathan 2024 + DISORT 6+ correction tournament 필요

## 호들갑 금지

verdict §6.2 lesson:
- 1961 / SPECTRAL-SYNTH / PANSHARP-P2 가 우선순위. 본 idea는 **Tier 2 backup** (Tier 1 KILL 시 활성화)
- "Rover-Anchored Benchmarking" framing이 paper의 핵심. "새 보정 만들기"가 아니라 "기존 family 비교"
- ★4-5 Carson 강점 (HiRISE↔Mastcam-Z 정합 + SAR atm transfer + vicarious calibration framework) 활용
- Track B (Hybrid physical+ML) 진입은 advisor 협의 후 (`ATM_INVERSION_DESIGN.md` §4 timeline 길어짐 risk)
