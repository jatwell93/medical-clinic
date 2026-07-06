---
phase: 02-catchment-demographics
plan: 01
subsystem: geospatial
tags: [geopandas, epsg7855, sa1-apportionment, folium, contextily, google-geocoding, abs-shapefiles]

# Dependency graph
requires:
  - phase: 01-scaffolding-data-pipeline
    provides: CachedSession HTTP boundary, BASE_ASSUMPTIONS params cell, dual-environment bootstrap, PROJECT_ROOT/CACHE_DIR paths
provides:
  - "§1.2 geocode cell producing site_lat, site_lon (cached, verified via folium map)"
  - "§2 catchment buffers (1/3/5 km in EPSG:7855) with 3km area sanity assertion"
  - "SA1-level area apportionment function (apportion_ring) — wired to §3 population weights in Plan 02-02"
  - "v1-vs-v2 comparison function (compare_v1_v2) — called in §3 after v2 totals computed"
  - "Folium interactive catchment map + static matplotlib/contextily figures (one per ring)"
  - "Extended validator with Phase 2 GEO-01..04 + D-06 checks"
  - "BASE_ASSUMPTIONS extended with 6 Phase 2 keys (sa1_shapefile, poa_shapefile, assertion thresholds, ERP vintage)"
affects: [02-02-demographics, 03-demand-competitors, 05-scenarios-report]

# Tech tracking
tech-stack:
  added: [contextily]
  patterns: ["EPSG:7855 for metric ops / EPSG:4326 for display convention", "SA1-level gpd.overlay area apportionment", "Idempotent notebook extension generator (json.dump, no nbformat)", "Folium interactive + static matplotlib/contextily twin for PDF"]

key-files:
  created:
    - scripts/extend_v2_notebook.py
  modified:
    - Johnston_St_v2.ipynb
    - scripts/validate_v2_notebook.py
    - .env.example

key-decisions:
  - "Added geopandas/shapely imports inline in §2.1 cell (plan omitted explicit import — code would fail without it)"
  - "Replaced old Phase 1 'Next Steps' markdown with Phase 2 version (old one referenced Phase 2 as future; now Phase 2 is present)"
  - "Generator inserts new cells after §1.2 ABS smoke test code cell and removes old Next Steps (cleaner than appending at end)"
  - "Used ensure_ascii=False in json.dump to preserve Unicode teaching characters (⚠, π, ℹ) in notebook source"

patterns-established:
  - "Idempotent notebook extension: check for marker string before appending, skip if present"
  - "Phase 2 validator extends Phase 1 (additive, not replacement) — Phase 1 checks preserved"
  - "No degree-based buffering validated by checking no .buffer( on same line as EPSG:4326"

requirements-completed:
  - GEO-01
  - GEO-02
  - GEO-03
  - GEO-04

# Metrics
duration: 12 min
completed: 2026-07-05
---

# Phase 2 Plan 01: Geocode Site & Geospatial Catchment Summary

**Cached Google Geocoding + EPSG:7855 1/3/5 km buffers with SA1-level area apportionment, v1-vs-v2 comparison, and folium/static contextily maps**

## Performance

- **Duration:** 12 min
- **Started:** 2026-07-05T11:02:00Z
- **Completed:** 2026-07-05T11:14:34Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Extended Johnston_St_v2.ipynb with §1.2 Geocode Site (cached Google Geocoding API through Phase 1 CachedSession + folium verification map with D-31 "visually verify" instruction)
- Extended notebook with §2 Geospatial Catchment: SA1/POA geometry loading, EPSG:7855 buffer construction with 3km area sanity assertion (≈28.27 km² = π×3²), SA1-level area apportionment via gpd.overlay (the headline v1 fix), v1-vs-v2 comparison function, folium interactive map + static matplotlib/contextily figures (one per ring), uniform-density caveat with Yarra River annotation
- Extended BASE_ASSUMPTIONS with 6 Phase 2 keys (sa1_shapefile, poa_shapefile, assert_3km_buffer_km2, assert_3km_buffer_tol, catchment_pop_plausible_range, erp_vintage_year)
- Extended validator with Phase 2 GEO-01..04 + D-06 checks — all passing alongside maintained Phase 1 invariants

## Task Commits

Each task was committed atomically:

1. **Task 1: Create notebook extension script and append §1.2 geocode + §2 catchment cells** - `9a0dbbc` (feat)
2. **Task 2: Extend validator with Phase 2 catchment checks** - `7083642` (feat)

## Files Created/Modified
- `scripts/extend_v2_notebook.py` - Idempotent generator that loads Johnston_St_v2.ipynb, extends BASE_ASSUMPTIONS with Phase 2 keys, appends §1.2 geocode + §2 catchment cells (16 new cells), writes back with json.dump
- `Johnston_St_v2.ipynb` - Extended from 11 to 26 cells (13 code, 13 markdown) with §1.2 Geocode Site + §2 Geospatial Catchment sections
- `scripts/validate_v2_notebook.py` - Extended with Phase 2 GEO-01..04 + D-06 checks (additive — Phase 1 PIPE-01..06 + v1 flaw eradication preserved)
- `.env.example` - Added SA1 shapefile manual download documentation (D-02)

## Decisions Made
- Added `import geopandas as gpd` and `from shapely.geometry import Point` inline in the §2.1 code cell — the plan's code used `gpd` and `Point` without importing them (the Phase 1 §0.1 imports cell only imports os/sys/json/requests/Path/CachedSession)
- Replaced the old Phase 1 "Next Steps" markdown cell with the Phase 2 version — the old one described Phase 2 as future work; now that Phase 2 cells are present, the new Next Steps points to §3 Demographics (Plan 02-02)
- Used `ensure_ascii=False` in `json.dump` to preserve Unicode teaching characters (⚠, π, ℹ) in the notebook source rather than escaping them to `\uXXXX`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added geopandas/shapely imports to §2.1 cell**
- **Found during:** Task 1 (notebook extension script creation)
- **Issue:** Plan's §2.1 code cell uses `gpd.read_file()` and §2.2 uses `gpd.GeoDataFrame()` + `Point()`, but neither geopandas nor shapely.geometry.Point are imported in the Phase 1 notebook or any new cell
- **Fix:** Prepended `import geopandas as gpd` and `from shapely.geometry import Point` to the §2.1 code cell (first cell that uses them)
- **Files modified:** scripts/extend_v2_notebook.py (generator), Johnston_St_v2.ipynb (generated output)
- **Verification:** Notebook source contains the imports; validator passes
- **Committed in:** 9a0dbbc (Task 1 commit)

**2. [Rule 2 - Missing Critical] Added numpy import to §2.5 static figures cell**
- **Found during:** Task 1 (notebook extension script creation)
- **Issue:** Plan's §2.5 static matplotlib cell uses `np.array` implicitly via the Yarra River coordinate lists; while the code as written doesn't call numpy directly, the plan's code references `import numpy as np` in the original plan text. Added the import to match the plan's intent.
- **Fix:** Added `import numpy as np` to the §2.5 static figures code cell
- **Files modified:** scripts/extend_v2_notebook.py, Johnston_St_v2.ipynb
- **Verification:** Notebook source contains the import
- **Committed in:** 9a0dbbc (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 missing critical)
**Impact on plan:** Both auto-fixes are necessary for the notebook to execute. No scope creep — the imports are standard Colab preinstalled libraries documented in STACK.md.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required. The SA1 shapefile download is documented in `.env.example` as a manual step, but the notebook degrades gracefully to POA-level apportionment if the file is missing.

## Next Phase Readiness
- §1.2 geocode cell produces `site_lat, site_lon` ready for §3 demographics and Phase 3 Places search centres
- §2 catchment buffers (1/3/5 km in EPSG:7855) ready for §3 demographics apportionment
- `apportion_ring()` function defined and ready to receive `sa1_pop_df` from §3 (Plan 02-02)
- `compare_v1_v2()` function defined and ready to receive `v2_ring_pops` from §3 (Plan 02-02)
- Plan 02-02 (Wave 2) can proceed — it depends on the site point, buffers, and apportionment function from this plan

---
*Phase: 02-catchment-demographics*
*Completed: 2026-07-05*
