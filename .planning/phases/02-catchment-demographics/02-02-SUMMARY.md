---
phase: 02-catchment-demographics
plan: 02
subsystem: demographics
tags: [abs-data-api, census, g01, g02, g04, sa1, erp-scaling, peer-benchmarking, matplotlib, pandas]

# Dependency graph
requires:
  - phase: 02-catchment-demographics
    provides: "Plan 02-01: site_lat/site_lon, EPSG:7855 buffers, apportion_ring() function, compare_v1_v2() function, sa1_in_5k GeoDataFrame, BASE_ASSUMPTIONS with erp_vintage_year + catchment_pop_plausible_range"
  - phase: 01-scaffolding-data-pipeline
    provides: "CachedSession HTTP boundary, BASE_ASSUMPTIONS params cell, PROJECT_ROOT/CACHE_DIR paths, PEER_POSTCODES"
provides:
  - "§3 demographics: ABS G01/G02/G04 fetch for POA 3067 + 9 peers with local GCP fallback (DEMO-01)"
  - "SA1 total persons wired into §2.3 apportionment function → v2 catchment population totals per ring (D-03)"
  - "compare_v1_v2() called with real v2 totals → v1-vs-v2 comparison table + chart (D-06 completion)"
  - "ERP scaling via ABS_ANNUAL_ERP_ASGS2021 to 2024 vintage (DEMO-04, D-19..D-24)"
  - "Peer benchmarking table with placeholder GP/pharmacy columns for Phase 3 (D-26)"
  - "2×2 peer comparison chart grid with POA 3067 highlighted (D-29)"
  - "Extended validator with Phase 2 DEMO-01..04 + D-03/D-06/D-09b/D-11 checks"
affects: [03-demand-competitors, 05-scenarios-report]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Runtime dataflow verification via check_dataflow_exists() — D-11 pattern for unverified ABS dataflows", "Source-agnostic tidy DataFrame schema (D-17) — API and GCP fallback emit same columns", "ERP growth rate scaling applied to both catchment pop and peer table (D-24)", "Placeholder columns for downstream phases (gp_count/pharmacy_count = '— Phase 3')"]

key-files:
  created:
    - scripts/extend_v2_notebook_demographics.py
  modified:
    - Johnston_St_v2.ipynb
    - scripts/validate_v2_notebook.py

key-decisions:
  - "fetch_abs_csv() returns both DataFrame and response object (for from_cache inspection) — plan's pseudocode had a scoping bug where resp was referenced outside its try block"
  - "ERP growth rate defaults to 1.0 (no scaling) when ERP API unavailable — peer table falls back to unscaled 2021 values gracefully"
  - "v2_ring_pops initialized as empty dict when SA1 shapefile missing — downstream ERP cell checks for empty dict before scaling"
  - "G04 fallback returns stub DataFrame with pct_65plus column only — peers marked N/A in fallback mode per D-12"
  - "Used ensure_ascii=False in json.dump (inherited from Plan 02-01 pattern) to preserve Unicode teaching characters"

patterns-established:
  - "Runtime dataflow existence check: check_dataflow_exists(flow_id) queries /rest/dataflow?detail=allstubs and checks ID presence — reusable pattern for any unverified ABS dataflow"
  - "fetch_abs_csv() helper: returns (DataFrame, response) tuple through the CachedSession — single entry point for all ABS CSV-with-labels fetches"
  - "Automatic fallback with printed warning: every API fetch has try/except that falls back to local GCP files with a warning naming the missing data + substituted file (D-15)"
  - "ERP scaling pattern: growth_rate = pop_2024 / pop_2021, applied uniformly to catchment pop and peer table (D-21/D-24)"

requirements-completed:
  - DEMO-01
  - DEMO-02
  - DEMO-03
  - DEMO-04

# Metrics
duration: 10 min
completed: 2026-07-05
---

# Phase 2 Plan 02: Demographics Summary

**ABS G01/G02/G04 census fetch with local GCP fallback, SA1 total persons wired into §2.3 apportionment for v2 catchment population totals, ERP scaling to 2024, peer benchmarking table with Phase 3 placeholders, and 2×2 comparison charts**

## Performance

- **Duration:** 10 min
- **Started:** 2026-07-05T11:20:00Z
- **Completed:** 2026-07-05T11:30:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Extended Johnston_St_v2.ipynb with §3 Demographics (11 new cells: 5 markdown, 6 code) — ABS G01/G02/G04 fetch through CachedSession with local GCP fallback (D-15/D-16/D-17), runtime G04 verification via check_dataflow_exists (D-11), SA1 total persons wired into §2.3 apportionment function to compute actual v2 catchment population totals per ring (D-03), plausibility assertion (D-09b), and compare_v1_v2() called with real v2 totals (D-06 completion — the headline teaching moment)
- ERP scaling via ABS_ANNUAL_ERP_ASGS2021 to 2024 vintage applied to both catchment population and peer benchmarking table (DEMO-04, D-19..D-24), with printed caveat (D-22)
- Peer benchmarking table with census columns (population raw + ERP-scaled, median age, 65+ share, median income) and placeholder GP/pharmacy columns for Phase 3 (D-26); 2×2 peer comparison chart grid with POA 3067 highlighted (D-29)
- Extended validator with Phase 2 demographics checks (DEMO-01..04 + D-03/D-06/D-09b/D-11) — all passing alongside maintained Phase 1 + Phase 2 catchment invariants

## Task Commits

Each task was committed atomically:

1. **Task 1: Create demographics notebook extension script and append §3 cells** - `2e2dac6` (feat)
2. **Task 2: Extend validator with Phase 2 demographics checks** - `5432534` (feat)

## Files Created/Modified
- `scripts/extend_v2_notebook_demographics.py` - Idempotent generator that loads Johnston_St_v2.ipynb, appends §3 Demographics cells (11 new: 5 markdown, 6 code), writes back with json.dump
- `Johnston_St_v2.ipynb` - Extended from 26 to 36 cells (19 code, 17 markdown) with §3 Demographics section
- `scripts/validate_v2_notebook.py` - Extended with Phase 2 DEMO-01..04 + D-03/D-06/D-09b/D-11 checks (additive — Phase 1 + Phase 2 catchment checks preserved)

## Decisions Made
- `fetch_abs_csv()` returns both DataFrame and response object (for `from_cache` inspection) — the plan's pseudocode had a scoping bug where `resp` was referenced outside its try block; returning the tuple from inside the try block fixes this
- ERP growth rate defaults to 1.0 (no scaling) when ERP API unavailable — peer table falls back to unscaled 2021 values gracefully, maintaining the "never hard-fail on a network call" principle (PIPE-04)
- `v2_ring_pops` initialized as empty dict when SA1 shapefile missing — downstream ERP cell checks for empty dict before scaling, avoiding KeyError
- G04 fallback returns stub DataFrame with `pct_65plus` column only — peers marked N/A in fallback mode per D-12, no fabricated peer data
- Used `ensure_ascii=False` in `json.dump` (inherited from Plan 02-01 pattern) to preserve Unicode teaching characters (⚠, ℹ) in notebook source

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] fetch_abs_csv() returns (DataFrame, response) tuple**
- **Found during:** Task 1 (notebook extension script creation)
- **Issue:** Plan's pseudocode for `fetch_g01_poa()` references `resp.from_cache` but `resp` is scoped inside `fetch_abs_csv()` and not accessible from the caller. The plan's `fetch_abs_csv()` only returns the DataFrame.
- **Fix:** Modified `fetch_abs_csv()` to return `(df, resp)` tuple. All callers updated to unpack both values.
- **Files modified:** scripts/extend_v2_notebook_demographics.py, Johnston_St_v2.ipynb
- **Verification:** Notebook source contains `fetch_abs_csv` returning tuple; all callers unpack correctly
- **Committed in:** 2e2dac6 (Task 1 commit)

**2. [Rule 2 - Missing Critical] Added v2_ring_pops initialization for non-SA1 path**
- **Found during:** Task 1 (notebook extension script creation)
- **Issue:** Plan's §3.3 code only defines `v2_ring_pops` inside the `if USE_SA1:` block, but §3.4 ERP cell references `v2_ring_pops` unconditionally. If SA1 shapefile is missing, the ERP cell would raise NameError.
- **Fix:** Added `v2_ring_pops = {}` in the `else` branch of the `if USE_SA1:` check, and the ERP cell checks `if v2_ring_pops:` before scaling.
- **Files modified:** scripts/extend_v2_notebook_demographics.py, Johnston_St_v2.ipynb
- **Verification:** Notebook source contains `v2_ring_pops = {}` in else branch; ERP cell has `if v2_ring_pops:` guard
- **Committed in:** 2e2dac6 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 missing critical)
**Impact on plan:** Both auto-fixes necessary for correct execution. No scope creep — fixes address scoping and initialization bugs in the plan's pseudocode.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required. The SA1 DataPack fallback (`2021Census_G01_AUST_SA1.csv`) is documented in `.env.example` as a manual download step, but the notebook degrades gracefully if the file is missing.

## Next Phase Readiness
- §3 demographics complete: ABS G01/G02/G04 fetch + fallback, SA1 total persons wired into apportionment, ERP scaling, peer benchmarking table, comparison charts
- v1-vs-v2 comparison called with real v2 totals (D-06 completion) — the headline teaching moment is done
- Phase 2 is COMPLETE: §1.2 + §2 + §3 all present; GEO-01..04 + DEMO-01..04 all satisfied and validated
- Peer benchmarking table has placeholder GP/pharmacy columns ready for Phase 3 to fill via Google Places (New) API
- Catchment age profile (G04 5-year bands) ready for Phase 3 demand model (age-band attendance rates)
- ERP-scaled population numbers ready for Phase 3 demand model and Phase 5 reporting
- Phase 3 (Demand & Competitors) can proceed — it depends on the geocoded site, catchment buffers, apportioned population, and age profile from Phase 2

---
*Phase: 02-catchment-demographics*
*Completed: 2026-07-05*
