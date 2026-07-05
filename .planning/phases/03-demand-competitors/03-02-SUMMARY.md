---
phase: 03-demand-competitors
plan: 02
subsystem: data
tags: [google-places-api, competitor-mapping, rapidfuzz, fuzzy-dedupe, geopandas, folium, contextily, geojson-persistence, classification]

# Dependency graph
requires:
  - phase: 03-demand-competitors
    provides: "Places API (New) client with saturation subdivision, site_places and peer_places dicts with raw Places results per (type, radius)"
  - phase: 02-catchment-demographics
    provides: "Geocoded site (site_lat/site_lon), catchment buffers, ERP-scaled peer population, peer benchmarking table"
  - phase: 01-scaffolding-data-pipeline
    provides: "CachedSession with allowable_methods=('GET','POST'), BASE_ASSUMPTIONS dict, PROJECT_ROOT/CACHE_DIR paths, FORCE_REFRESH flag"
provides:
  - "classify_place() function with 12 corporate GP brands, 11 pharmacy brands, 21 exclude keywords (D-09)"
  - "fuzzy_dedupe_competitors() using rapidfuzz.fuzz.token_sort_ratio with name_threshold=85, address_threshold=80 (D-09)"
  - "Deduped competitor GeoDataFrame persisted to data/cache/competitors.geojson with load-from-cache path (D-08)"
  - "Per-ring competitor counts table via geopandas.sjoin spatial join"
  - "Manual-review checkpoint printing ambiguous rows inline (D-11 — no blocking prompts)"
  - "Folium interactive competitor map with toggleable ring layers + type colours (D-15)"
  - "3 static matplotlib + contextily figures (one per ring) for PDF (D-15)"
  - "Peer competitor table with GP count, pharmacy by brand, allied health, GP-per-1,000 benchmarked against VIC 117/100k (D-16, COMP-03)"
  - "D-12 capacity caveat markdown cell (Places listings ≠ FTE GPs, two-method range)"
affects: [03-03-demand-model]

# Tech tracking
tech-stack:
  added: ["rapidfuzz (MIT-licensed fuzzy string matching, pip install)"]
  patterns:
    - "Keyword-based competitor classification: pharmacy brands first → exclude keywords → corporate GP brands → independent GP indicators → allied health → ambiguous"
    - "rapidfuzz.fuzz.token_sort_ratio fuzzy-dedupe of individual-practitioner listings (name≥85, address≥80)"
    - "GeoJSON persistence with load-from-cache (D-08): if competitors.geojson exists and not FORCE_REFRESH, load it; else write it"
    - "geopandas.sjoin for competitor-to-ring spatial assignment (predicate='within')"
    - "Manual-review checkpoint: print ambiguous rows inline, no blocking prompts (D-11, PIPE-01)"
    - "Folium FeatureGroup per ring + CircleMarker per competitor type (D-15)"

key-files:
  modified:
    - "scripts/extend_v2_notebook_phase3.py — extended with competitor_cells() function (11 §4 cells)"
    - "Johnston_St_v2.ipynb — extended from 44 to 55 cells with §4 Competitor Landscape"
    - "scripts/validate_v2_notebook.py — extended with Phase 3 COMP-01..03 + DEMAND-04 checks"

key-decisions:
  - "Removed all mentions of 'fuzzywuzzy' from notebook (acceptance criteria: zero occurrences) — replaced with 'deprecated GPL alternative' in teaching commentary"
  - "Removed all 'input(' text from notebook (acceptance criteria: zero occurrences) — replaced with 'no blocking prompts' in comments and markdown"
  - "Used regular strings (not f-strings) in generator for all notebook code lines containing curly braces — f-strings in the generator would try to evaluate notebook variables in the generator scope"

patterns-established:
  - "Pattern: Competitor classification — keyword rules on displayName + primaryType, pharmacy brands checked first (D-07)"
  - "Pattern: Fuzzy-dedupe with rapidfuzz — token_sort_ratio on normalised name + address, conservative thresholds"
  - "Pattern: GeoJSON persistence — to_file(driver='GeoJSON') + gpd.read_file load-from-cache (D-08)"
  - "Pattern: Spatial join ring assignment — gpd.sjoin(points, buffers, predicate='within') for per-ring counts"
  - "Pattern: Manual-review checkpoint — print ambiguous rows inline, no blocking prompts (D-11)"

requirements-completed:
  - COMP-02
  - COMP-03

# Metrics
duration: 12min
completed: 2026-07-06
---

# Phase 3 Plan 02: Competitor Landscape Summary

**Keyword-based competitor classification (12 corporate GP brands, 11 pharmacy brands, 21 exclude keywords) + rapidfuzz fuzzy-dedupe + GeoJSON persistence + folium/static maps + peer competitor table with GP-per-1,000 benchmark**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-07-06
- **Completed:** 2026-07-06
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Extended `scripts/extend_v2_notebook_phase3.py` with `competitor_cells()` function generating 11 §4 cells: classification rules, fuzzy-dedupe + GeoJSON persistence, ring assignment via sjoin, manual-review checkpoint, folium + static maps, peer competitor table, capacity caveat
- Extended `Johnston_St_v2.ipynb` from 44 to 55 cells with §4 Competitor Landscape: `classify_place()` checks pharmacy brands first (D-07), then exclude keywords, corporate GP brands, independent GP indicators, allied health, else ambiguous; `fuzzy_dedupe_competitors()` uses rapidfuzz `token_sort_ratio` with name_threshold=85, address_threshold=80; GeoJSON persistence with load-from-cache (D-08); `gpd.sjoin` for ring assignment; folium map with FeatureGroup layers + 3 static contextily figures (D-15); peer competitor table with GP-per-1,000 benchmarked against VIC 117/100k (COMP-03); D-12 capacity caveat
- Extended `scripts/validate_v2_notebook.py` with Phase 3 COMP-01..03 + DEMAND-04 checks — all pass
- Validator OVERALL: PASS — 26 checks, 0 failures, no Phase 1/2 regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend generator with §4 Competitor Landscape cells** - `acb22ad` (feat)
2. **Task 2: Extend validator with Phase 3 COMP-01..03 + DEMAND-04 checks** - `e7e3930` (test)

## Files Created/Modified
- `scripts/extend_v2_notebook_phase3.py` - Extended with `competitor_cells()` function (11 §4 cells) and cell-replacement idempotency for §4
- `Johnston_St_v2.ipynb` - Extended from 44 to 55 cells with §4 Competitor Landscape (classification, dedupe, GeoJSON, maps, peer table, caveat)
- `scripts/validate_v2_notebook.py` - Extended with COMP-01..03 + DEMAND-04 checks, Phase 3 labels in report(), structural-failure filter updated

## Decisions Made
- **Removed "fuzzywuzzy" text from notebook:** The acceptance criteria requires zero occurrences of "fuzzywuzzy" in the notebook. Replaced teaching commentary mentions with "deprecated GPL alternative" to maintain the teaching point without triggering the negative assertion.
- **Removed "input(" text from notebook:** The acceptance criteria requires zero occurrences of "input(" (D-11 violation check is a blunt string search). Replaced "no `input()` blocking" with "no blocking prompts" in markdown and code comments.
- **Used regular strings in generator:** All notebook code lines containing curly braces (f-strings in the notebook) use regular Python strings in the generator, not f-strings — f-strings in the generator would try to evaluate notebook variables in the generator's scope, causing NameError.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Removed "fuzzywuzzy" and "input(" from notebook text**
- **Found during:** Task 1 (§4 cell generation)
- **Issue:** The plan's acceptance criteria requires zero occurrences of "fuzzywuzzy" and "input(" in the notebook, but the plan's own cell descriptions mention "NOT GPL fuzzywuzzy" and "no `input()` blocking" in teaching commentary
- **Fix:** Replaced "fuzzywuzzy" with "deprecated GPL alternative" and "input()" with "blocking prompts" in all markdown and code comments
- **Files modified:** scripts/extend_v2_notebook_phase3.py
- **Verification:** `'fuzzywuzzy' not in s` and `'input(' not in s` both pass
- **Committed in:** acb22ad (Task 1 commit)

**2. [Rule 1 - Bug] Fixed f-string variable scope errors in generator**
- **Found during:** Task 1 (§4 cell generation)
- **Issue:** Several lines in `competitor_cells()` used Python f-strings that referenced notebook variables (e.g., `len(competitors_gdf)`, `radius`, `colour`) — these would cause NameError in the generator scope
- **Fix:** Converted all f-strings to regular strings; the notebook's own f-strings are preserved as literal text in the generated source
- **Files modified:** scripts/extend_v2_notebook_phase3.py
- **Verification:** `python scripts/extend_v2_notebook_phase3.py` runs without error
- **Committed in:** acb22ad (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 missing critical, 1 bug)
**Impact on plan:** Both auto-fixes necessary for acceptance criteria compliance and generator functionality. No scope creep.

## Issues Encountered
- Windows stdout encoding with Unicode characters (⚠, ×) required `PYTHONIOENCODING=utf-8` environment variable for script output. Does not affect script functionality — the notebook is written correctly with `ensure_ascii=False`.

## User Setup Required

None - no external service configuration required. The `competitors.geojson` file is created at runtime when the notebook is executed with a valid Google Places API key. The rapidfuzz package is installed via `%pip install` in the notebook (comment in §4.1 cell).

## Next Phase Readiness
- §4 Competitor Landscape is ready for Plan 03-03 (demand model): `competitors_gdf` (deduped, classified GeoDataFrame) and `per_ring_counts` (GP clinics, pharmacies, allied health by ring) feed the GP FTE capacity estimate in §5
- `peer_comp_table` with GP-per-1,000 ratios fills the DEMO-03 placeholder with real Places data
- The D-12 capacity caveat (two-method range) is ready for §5 to compute: clinic-derived (clinic count × 4.0 FTE/clinic) vs benchmark-derived (AMWAC 110.4/100k × population)
- Deferred: Colab Restart & Run All with API key to confirm §4 runs end-to-end (requires Google Places API key + MBS SA3 + AIHW files)

---
*Phase: 03-demand-competitors*
*Completed: 2026-07-06*
