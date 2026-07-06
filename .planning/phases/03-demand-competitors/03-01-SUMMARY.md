---
phase: 03-demand-competitors
plan: 01
subsystem: data
tags: [google-places-api, places-api-new, mbs-sa3, aihw, demand-model, competitor-mapping, requests-cache]

# Dependency graph
requires:
  - phase: 02-catchment-demographics
    provides: "Geocoded site (site_lat/site_lon), catchment buffers, SA1-apportioned population, peer benchmarking table, poa GeoDataFrame"
  - phase: 01-scaffolding-data-pipeline
    provides: "CachedSession with allowable_methods=('GET','POST'), BASE_ASSUMPTIONS dict, PROJECT_ROOT/CACHE_DIR paths"
provides:
  - "Places API (New) client with saturation subdivision (places_nearby, places_nearby_saturated, offset_meters)"
  - "MBS SA3 20604 Yarra loader with state fallback (load_mbs_sa3)"
  - "AIHW age-band rates loader with 4-band structure (load_aihw_sa3_rates)"
  - "Phase 3 BASE_ASSUMPTIONS keys: consults_per_capita_yr (4-band), avg_fte_per_clinic, amwac_per_100k, gp_fte_consults_per_yr, consults_per_patient_yr, mbs_item_23_rebate, market_share_thresholds, places_included_types"
  - "site_places and peer_places dicts with raw Places results per (type, radius)"
affects: [03-02-competitor-landscape, 03-03-demand-model]

# Tech tracking
tech-stack:
  added: []  # No new libraries — all via existing CachedSession + pandas + openpyxl
  patterns:
    - "Places API (New) POST with X-Goog-FieldMask header through CachedSession"
    - "2×2 grid saturation subdivision on 20-result cap with place.id dedupe"
    - "Pro SKU field mask only (drops rating/userRatingCount — Enterprise SKU avoidance)"
    - "MBS SA3 loader with state fallback + loud warning banner (D-04)"
    - "AIHW 4-band age structure (0-24/25-44/45-64/65+) replacing old 3-band (0-14/15-64/65+)"

key-files:
  created:
    - "scripts/extend_v2_notebook_phase3.py — re-runnable Phase 3 generator (idempotent cell-replacement)"
  modified:
    - "Johnston_St_v2.ipynb — extended from 36 to 44 cells with §1.4 + §1.5 acquisition cells"
    - ".env.example — extended with MBS SA3 + AIHW manual download instructions"

key-decisions:
  - "Dropped rating/userRatingCount from Places field mask — Enterprise SKU ($35/1k, 1k free/mo) vs Pro SKU ($32/1k, 5k free/mo). Correction 1 from research."
  - "Replaced 3-band consults_per_capita_yr (0-14/15-64/65+) with 4-band AIHW SA3 structure (0-24/25-44/45-64/65+). Correction 2 from research."
  - "AIHW citation updated to 2026 (covers 2024-25 data, updated 26 Mar 2026). Correction 3 from research."
  - "Optimized saturation subdivision to store sub-query results and check for saturation without re-querying (same behavior as RESEARCH Pattern 1, fewer API calls on first run)."
  - "All Places POST calls route through Phase 1 CachedSession (session.post), not bare requests.post."

patterns-established:
  - "Pattern: Places API (New) client — POST places:searchNearby with X-Goog-FieldMask, maxResultCount=20, session.post for caching"
  - "Pattern: Saturation subdivision — 2×2 grid on 20-result cap, max depth 2, dedupe on place.id"
  - "Pattern: Data loader with fallback — SA3 file → state file with loud warning banner (D-04)"
  - "Pattern: AIHW age-band matching — column name normalization (0-24 or 0_24) for runtime sheet structure variance"

requirements-completed:
  - DEMAND-01
  - COMP-01

# Metrics
duration: 15min
completed: 2026-07-06
---

# Phase 3 Plan 01: Data Acquisition Layer Summary

**Places API (New) client with 2×2 saturation subdivision + MBS SA3/AIHW age-band loaders with 4-band structure, replacing v1's legacy uncached Places + state-level Medicare**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-07-06
- **Completed:** 2026-07-06
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created `scripts/extend_v2_notebook_phase3.py` — a re-runnable, idempotent generator that extends the notebook with §1.4 Places API (New) client + §1.5 MBS SA3/AIHW loader cells and Phase 3 BASE_ASSUMPTIONS keys
- Extended `Johnston_St_v2.ipynb` from 36 to 44 cells: §1.4 implements `places_nearby()` with Pro SKU field mask (no rating/userRatingCount), `places_nearby_saturated()` with 2×2 grid subdivision on 20-result cap, and `offset_meters()` for grid offsets; §1.5 implements `load_mbs_sa3()` with SA3 20604 Yarra filter + state fallback warning, and `load_aihw_sa3_rates()` with 4-band age structure
- Updated `.env.example` with MBS SA3 Summary (health.gov.au, published 25 May 2026) + AIHW data tables (aihw.gov.au, updated 26 Mar 2026) manual download instructions
- Replaced old 3-band `consults_per_capita_yr` (0-14/15-64/65+) with 4-band AIHW SA3 structure (0-24/25-44/45-64/65+) — Correction 2
- All 3 critical corrections from research applied: (1) Pro SKU field mask only, (2) 4-band AIHW age structure, (3) AIHW (2026) citation
- Validator OVERALL: PASS — 22 checks, 0 failures, no Phase 1/2 regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Phase 3 generator script + extend notebook + update .env.example** - `a0b3a26` (feat)
2. **Task 2: Verify notebook structural integrity** - `dc191ed` (test)

## Files Created/Modified
- `scripts/extend_v2_notebook_phase3.py` - Re-runnable Phase 3 generator script (idempotent cell-replacement, BASE_ASSUMPTIONS extension, .env.example update)
- `Johnston_St_v2.ipynb` - Extended from 36 to 44 cells with §1.4 Places client + §1.5 MBS/AIHW loaders + Phase 3 BASE_ASSUMPTIONS keys
- `.env.example` - Extended with MBS SA3 Summary + AIHW data tables manual download instructions

## Decisions Made
- **Optimized saturation subdivision:** Stored sub-query results from the first pass and checked them for saturation, rather than re-querying all sub-circles in an `any(...)` check (as in RESEARCH Pattern 1). Same behavior, fewer API calls on first run. Cached, so re-runs are $0 either way.
- **All 3 research corrections applied:** (1) Dropped rating/userRatingCount from field mask (Enterprise SKU avoidance), (2) 4-band AIHW age structure (0-24/25-44/45-64/65+), (3) AIHW (2026) citation for 2024-25 data vintage.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Windows stdout flushing with Unicode characters (⚠, ×) caused an OSError when printing script output directly to terminal. Resolved by piping through `cat`. Does not affect script functionality — the notebook and .env.example are written correctly.

## User Setup Required

None - no external service configuration required. The MBS SA3 and AIHW Excel files are manual downloads documented in `.env.example` (same pattern as the SA1 shapefile in Phase 2). The notebook degrades gracefully with fallbacks + warnings when files are absent.

## Next Phase Readiness
- §1.4 Places client is ready for Plan 03-02 (competitor landscape): `site_places` and `peer_places` dicts contain raw place lists per (type, radius) that §4 will classify, dedupe, and map
- §1.5 MBS/AIHW loaders are ready for Plan 03-03 (demand model): `mbs_sa3_df` and `aihw_rates` provide SA3 20604 Yarra attendance data and age-band per-capita rates that §5 will multiply by the catchment age profile
- Phase 3 BASE_ASSUMPTIONS keys (avg_fte_per_clinic, amwac_per_100k, gp_fte_consults_per_yr, consults_per_patient_yr, mbs_item_23_rebate, market_share_thresholds) are ready for the demand model and market share calculations
- Deferred: Colab Restart & Run All with API key + MBS SA3 + AIHW files to confirm §1.4 + §1.5 run end-to-end

---
*Phase: 03-demand-competitors*
*Completed: 2026-07-06*
