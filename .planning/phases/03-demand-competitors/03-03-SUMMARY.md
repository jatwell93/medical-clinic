---
phase: 03-demand-competitors
plan: 03
subsystem: data
tags: [demand-model, age-adjusted-demand, aihw, mbs-sa3, market-share, capacity-range, amwac, transparent-arithmetic, no-ml]

# Dependency graph
requires:
  - phase: 03-demand-competitors
    provides: "Places API (New) client with saturation subdivision, MBS SA3 20604 Yarra loader, AIHW age-band rates loader (4-band structure), Phase 3 BASE_ASSUMPTIONS keys"
  - phase: 03-demand-competitors
    provides: "Competitor classification, fuzzy-dedupe, GeoJSON persistence, per-ring competitor counts, peer competitor table"
  - phase: 02-catchment-demographics
    provides: "Geocoded site, catchment buffers, SA1-apportioned population, ERP-scaled ring population (ring_pops_erp), G04 age data (g04_df)"
  - phase: 01-scaffolding-data-pipeline
    provides: "CachedSession, BASE_ASSUMPTIONS dict, PROJECT_ROOT/CACHE_DIR paths"
provides:
  - "aggregate_age_bands() function mapping ABS 5-year age bands to AIHW SA3 4 bands (0-24, 25-44, 45-64, 65+) — Correction 2"
  - "compute_demand() function — transparent arithmetic: sum(pop_band × rate_band), no ML (DEMAND-04, Pitfall 14)"
  - "SA3 20604 MBS total-attendance cross-check (±15% tolerance, D-03)"
  - "estimate_gp_capacity_range() function — two-method range (clinic-derived × 4.0 FTE, AMWAC 110.4/100k × population) — D-10"
  - "compute_required_market_share() function — three framings (share_of_total, share_of_unmet, share_of_pop) — D-13"
  - "label_market_share() function — low/moderate/high labels (<5% low, 5-15% moderate, >15% high) — D-14"
  - "Plain-language interpretation with NO go/no-go verdict (verdict deferred to Phase 5) — D-14"
  - "No-ML Assertion markdown cell (DEMAND-04, Pitfall 14)"
  - "Validator extended with Phase 3 DEMAND-01..03 + strengthened DEMAND-04 checks"
affects: [04-financial-model, 05-report-scenarios]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Transparent arithmetic demand model: sum(population_band × attendance_rate_band) — no ML, every input traceable to cited source"
    - "ABS 5-year age band aggregation to AIHW SA3 4 bands (0-24, 25-44, 45-64, 65+) via band_map dict"
    - "Two-method GP FTE capacity range: clinic-derived (count × 4.0 FTE) vs benchmark-derived (AMWAC 110.4/100k × pop) — variance IS the caveat"
    - "Three market-share framings side-by-side: share_of_total, share_of_unmet, share_of_pop — D-13"
    - "Market-share labels: <5% low, 5-15% moderate, >15% high — heuristic, no official benchmark (D-14)"
    - "Verdict deferral: plain-language interpretation quantifies required share but does NOT judge achievability — go/no-go is Phase 5"

key-files:
  modified:
    - "scripts/extend_v2_notebook_phase3.py — extended with demand_cells() function (9 §5 cells) and cell-replacement idempotency for §5"
    - "Johnston_St_v2.ipynb — extended from 55 to 66 cells with §5 Demand Model"
    - "scripts/validate_v2_notebook.py — extended with DEMAND-01..03 checks + strengthened DEMAND-04 (no RandomForest)"

key-decisions:
  - "Removed 'sklearn' from markdown teaching commentary — acceptance criteria requires zero occurrences (blunt string search). Replaced with 'No ML libraries' to maintain teaching point without triggering negative assertion."
  - "Used POA 3067 G04 age data as the age template for all rings, scaled proportionally to each ring's ERP-scaled population — catchment is centred on Abbotsford, inner-Melbourne age profiles are similar across rings."
  - "Computed market share with both capacity methods (method_a + method_b), then averaged for 'mid' values used in the plain-language interpretation — the range IS the caveat (D-12)."
  - "Used regular strings (not f-strings) in generator for all notebook code lines containing curly braces — f-strings in the generator would try to evaluate notebook variables in the generator scope (same lesson as 03-02)."

patterns-established:
  - "Pattern: Transparent arithmetic demand model — sum(pop_band × rate_band), no ML, every input cited"
  - "Pattern: Age band aggregation — ABS 5-year → AIHW 4 bands via band_map dict with fuzzy column matching"
  - "Pattern: Two-method capacity range — clinic-derived vs benchmark-derived, variance IS the caveat"
  - "Pattern: Three market-share framings — share_of_total, share_of_unmet, share_of_pop side-by-side"
  - "Pattern: Verdict deferral — quantifies required share, does NOT judge achievability (go/no-go is Phase 5)"

requirements-completed:
  - DEMAND-02
  - DEMAND-03
  - DEMAND-04

# Metrics
duration: 12min
completed: 2026-07-06
---

# Phase 3 Plan 03: Demand Model Summary

**Transparent arithmetic demand model (sum(pop_band × rate_band)) replacing v1's 3-row Random Forest, with AIHW 4-band age aggregation, two-method GP capacity range, three market-share framings, and plain-language interpretation with NO go/no-go verdict**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-07-05T23:12:00Z
- **Completed:** 2026-07-05T23:24:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Extended `scripts/extend_v2_notebook_phase3.py` with `demand_cells()` function generating 9 §5 cells: age band aggregation (ABS 5-year → AIHW 4 bands), demand computation (transparent arithmetic), SA3 MBS cross-check (D-03), GP FTE capacity range (D-10 two methods), required market share (D-13 three framings), plain-language interpretation (D-14, no verdict), No-ML Assertion (DEMAND-04), and Next Steps (Phase 4)
- Extended `Johnston_St_v2.ipynb` from 55 to 66 cells with §5 Demand Model: `aggregate_age_bands()` maps ABS 5-year bands to AIHW SA3 4 bands (0-24, 25-44, 45-64, 65+ — Correction 2); `compute_demand()` implements `sum(pop_band × rate_band)` — pure arithmetic, no ML (Pitfall 14, DEMAND-04); SA3 20604 MBS cross-check with ±15% tolerance (D-03); `estimate_gp_capacity_range()` uses two methods (clinic-derived × 4.0 FTE, AMWAC 110.4/100k × population — D-10); `compute_required_market_share()` produces three framings (share_of_total, share_of_unmet, share_of_pop — D-13); `label_market_share()` returns low/moderate/high (<5% low, 5-15% moderate, >15% high — D-14); plain-language interpretation with NO go/no-go verdict (deferred to Phase 5 — D-14)
- Extended `scripts/validate_v2_notebook.py` with DEMAND-01 (SA3 MBS + state fallback warning), DEMAND-02 (compute_demand + aggregate_age_bands + AIHW 4 bands), DEMAND-03 (capacity range + market share + three framings + interpretation + Phase 5 deferral), and strengthened DEMAND-04 (no sklearn + no scikit-learn + no RandomForest + no random_forest) — all pass
- Validator OVERALL: PASS — 28 checks, 0 failures, no Phase 1/2 regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend generator with §5 Demand Model cells** - `b43b31c` (feat)
2. **Task 2: Extend validator with Phase 3 DEMAND-01..03 checks + strengthen DEMAND-04** - `f7139c7` (test)

## Files Created/Modified
- `scripts/extend_v2_notebook_phase3.py` - Extended with `demand_cells()` function (9 §5 cells) and cell-replacement idempotency for §5 (marker: "# §5 Demand Model")
- `Johnston_St_v2.ipynb` - Extended from 55 to 66 cells with §5 Demand Model (age aggregation, demand computation, cross-check, capacity range, three framings, interpretation, No-ML assertion, Next Steps)
- `scripts/validate_v2_notebook.py` - Extended with DEMAND-01..03 checks + strengthened DEMAND-04 (no RandomForest), Phase 3 labels in report(), structural-failure filter updated

## Decisions Made
- **Removed "sklearn" from markdown teaching commentary:** The acceptance criteria requires zero occurrences of "sklearn" in the notebook (blunt string search). Replaced "No `sklearn`" with "No ML libraries" in both the §5 header and §5.7 No-ML Assertion markdown cells to maintain the teaching point without triggering the negative assertion.
- **Used POA 3067 G04 age data as age template for all rings:** The catchment is centred on Abbotsford (3067). POA-level age profile is a reasonable proxy for all rings (inner-Melbourne age profiles are similar). Scaled proportionally to each ring's ERP-scaled population.
- **Computed market share with both capacity methods, then averaged for 'mid' values:** The plain-language interpretation uses `share_of_total_mid` (average of method_a and method_b). The range IS the caveat (D-12) — both methods are printed in the detailed table.
- **Used regular strings in generator:** All notebook code lines containing curly braces (dict literals, f-strings) use regular Python strings in the generator, not f-strings — same lesson as 03-02.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Removed "sklearn" from markdown teaching commentary**
- **Found during:** Task 1 (§5 cell generation)
- **Issue:** The plan's acceptance criteria requires zero occurrences of "sklearn" in the notebook, but the plan's own §5 header and §5.7 No-ML Assertion markdown cells contain "No `sklearn`" in teaching commentary
- **Fix:** Replaced "No `sklearn`" with "No ML libraries" in both markdown cells to maintain the teaching point without triggering the blunt negative assertion
- **Files modified:** scripts/extend_v2_notebook_phase3.py
- **Verification:** `'sklearn' not in s` passes (zero occurrences)
- **Committed in:** b43b31c (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Auto-fix necessary for acceptance criteria compliance. No scope creep — the teaching point is preserved with reworded language.

## Issues Encountered
- Windows stdout encoding with Unicode characters (⚠, ×) required `PYTHONIOENCODING=utf-8` environment variable for script output. Does not affect script functionality — the notebook is written correctly with `ensure_ascii=False`.

## User Setup Required

None - no external service configuration required. The §5 Demand Model uses data loaded by §1.5 (MBS SA3 + AIHW age-band rates) and §3 (G04 age data, ERP-scaled ring population). All manual downloads are documented in `.env.example` (updated in Plan 03-01).

## Next Phase Readiness
- §5 Demand Model is complete — the required-market-share headline metric (DEMAND-03) is computed in three framings with a plain-language interpretation
- The demand-vs-capacity gap is quantified per ring (1/3/5 km) with both capacity methods
- Phase 4 (Financial Model) can use `market_share_results`, `ring_demand`, `existing_capacity_range`, and `clinic_capacity` to build the P&L
- The go/no-go verdict is explicitly deferred to Phase 5 (after P&L + scenarios + sensitivity)
- Deferred: Colab Restart & Run All with API key + MBS SA3 + AIHW files to confirm §5 runs end-to-end with real data

---
*Phase: 03-demand-competitors*
*Completed: 2026-07-06*
