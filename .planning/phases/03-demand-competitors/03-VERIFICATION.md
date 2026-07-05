---
status: passed
phase: 03-demand-competitors
date: 2026-07-06
score: 7/7
requirements_verified: [DEMAND-01, DEMAND-02, DEMAND-03, DEMAND-04, COMP-01, COMP-02, COMP-03]
human_verification:
  - "Colab Restart & Run All with valid GOOGLE_PLACES_KEY + MBS SA3 + AIHW Excel files in data/local/ — confirms §1.4/§1.5/§4/§5 run end-to-end with real data (all 3 SUMMARYs defer this)"
  - "Actual Google Places API calls produce non-empty site_places/peer_places dicts (saturation subdivision + dedupe verified against live 20-result cap)"
  - "MBS SA3 20604 Yarra filter returns expected quarters (sheet name + SA3 column name verified at runtime against real Excel file)"
  - "AIHW age-band rate extraction matches real column names (column-matching logic is runtime-verified)"
  - "competitors.geojson is written/read correctly on first run vs cached re-run (D-08 persistence path)"
---

# Phase 03 Verification — Demand & Competitors

## Summary

Phase 03 achieved its goal. The phase quantifies both sides of the market — age-adjusted GP consultation demand from SA3-level MBS/AIHW data (SA3 20604 Yarra) and the existing supply landscape via Google Places (New) competitor mapping — converging on the required market share a 5-FTE-GP clinic must capture. All 7 requirement IDs (DEMAND-01..04, COMP-01..03) are verified present in the codebase with dedicated validator checks, all 4 success criteria pass against the actual notebook source, and the 2 critical bugs + 1 warning from code review (CR-001, CR-002, WR-002) are confirmed fixed in `scripts/extend_v2_notebook_phase3.py`. The validator (`python scripts/validate_v2_notebook.py`) passes with 29 checks green and exit code 0. The notebook is structurally complete (69 cells: 38 code, 31 markdown). The only remaining verification is a live Colab end-to-end run with a real API key + the manual-download Excel files, which all three SUMMARYs explicitly defer.

## Success Criteria Verification

### SC1: SA3 20604 (Yarra) MBS GP attendance data loaded; state fallback warning — **PASS**

Evidence:
- `load_mbs_sa3()` in `scripts/extend_v2_notebook_phase3.py` (lines 287-321) filters to `df["SA3"].astype(str) == "20604"` and returns `(sa3_yarra, "sa3")`.
- State fallback (lines 311-320) prints the loud warning banner: `"⚠  STATE BENCHMARK, NOT LOCAL — SA3 20604 data not found."` with `"═" * 70` borders.
- §1.5 load+assert cell (lines 376-387) asserts `mbs_sa3_df["SA3"].astype(str).str.contains("20604").any()` when source is "sa3".
- Validator check `Phase 3 DEMAND-01 (SA3 MBS + state fallback warning)`: PASS.

### SC2: Annual catchment consult demand per ring via age-band rates × age structure (transparent arithmetic, no ML) — **PASS**

Evidence:
- `compute_demand()` (notebook §5.2) implements `total_demand += pop * (rate / 100.0)` — pure arithmetic, no ML.
- `aggregate_age_bands()` (notebook §5.1) maps ABS 5-year bands to AIHW 4 bands (0-24, 25-44, 45-64, 65+) via `band_map` dict.
- No `sklearn`, no `RandomForest`, no `random_forest` anywhere in the notebook (DEMAND-04).
- Validator checks `Phase 3 DEMAND-02 (age-adjusted demand + AIHW 4 bands)` and `Phase 3 DEMAND-04 (no ML / no sklearn / no RandomForest)`: both PASS.

### SC3: Competitors fetched via Places API (New) with per-type/per-ring splitting, place_id dedupe, brand classification, clinic-vs-practitioner filtering — **PASS**

Evidence:
- `PLACES_URL = "https://places.googleapis.com/v1/places:searchNearby"` (line 126) — Places API (New) POST endpoint.
- `places_nearby_saturated()` (lines 171-207) implements 2×2 grid subdivision on 20-result cap with dedupe on `p.get("id")` via `seen = {}` dict (max depth 2).
- Pro SKU field mask only (lines 130-141) — no `places.rating` or `places.userRatingCount` (Enterprise SKU avoidance).
- Site catchment query: 5 types × 3 radii = 15 base requests (lines 213-223); peer queries: 10 peers × 3 radii × 5 types = ~150 requests (lines 226-242).
- `classify_place()` with `CORPORATE_GP_BRANDS` (12 keywords), `PHARMACY_BRANDS` (11 keywords), `EXCLUDE_KEYWORDS` (21 terms) — checks pharmacy brands first, then exclude, then corporate GP, then independent GP, then allied health, else ambiguous.
- `fuzzy_dedupe_competitors()` uses `rapidfuzz.fuzz.token_sort_ratio` with `name_threshold=85`, `address_threshold=80` (line 540).
- GeoJSON persistence to `data/cache/competitors.geojson` with load-from-cache path (D-08).
- Validator checks `COMP-01`, `COMP-02`, `COMP-03`: all PASS.

### SC4: Required market share for 5-FTE-GP clinic (~25-30k consults/yr) computed with plain-language interpretation; GP-per-1,000 benchmarked against VIC ~117/100k — **PASS**

Evidence:
- `estimate_gp_capacity_range()` implements two methods: (a) `clinic_count * 4.0` FTE/clinic, (b) `ring_pop * (110.4 / 100_000)` AMWAC benchmark — returns `method_a_clinic_derived`, `method_b_benchmark_derived`, `range`, `caveat`.
- `compute_required_market_share()` produces three framings: `share_of_total`, `share_of_unmet`, `share_of_pop`, plus `patients_needed`.
- `label_market_share()` returns low/moderate/high based on `market_share_thresholds` (low=5, high=15).
- `gp_fte_consults_per_yr = 5500` → 5 FTE × 5500 = 27,500 consults/yr (within the ~25-30k target).
- Plain-language interpretation prints per-ring summary with NO go/no-go verdict — explicitly defers to Phase 5 (`"Note: The go/no-go verdict is a Phase 5 output"`).
- GP-per-1,000 benchmarked against VIC 117/100k and AMWAC 110.4/100k (both values present in peer competitor table cell).
- Validator check `Phase 3 DEMAND-03 (capacity range + market share + interpretation)`: PASS.

## Requirements Traceability

| REQ-ID | Status | Evidence |
|--------|--------|----------|
| **DEMAND-01** | ✅ verified | `load_mbs_sa3()` filters to SA3 20604 Yarra; state fallback with loud warning banner; `.env.example` documents health.gov.au download URL; validator check DEMAND-01 PASS |
| **DEMAND-02** | ✅ verified | `compute_demand()` = `sum(pop_band × rate_band)`; `aggregate_age_bands()` maps ABS 5-year → AIHW 4 bands (0-24/25-44/45-64/65+); per-ring computation; validator check DEMAND-02 PASS |
| **DEMAND-03** | ✅ verified | `estimate_gp_capacity_range()` (two-method range), `compute_required_market_share()` (three framings), `label_market_share()` (low/moderate/high), plain-language interpretation with Phase 5 deferral; validator check DEMAND-03 PASS |
| **DEMAND-04** | ✅ verified | No `sklearn`, no `RandomForest`, no `random_forest` in notebook; demand model is transparent arithmetic; No-ML Assertion markdown cell present; validator check DEMAND-04 PASS |
| **COMP-01** | ✅ verified | Places API (New) POST `places:searchNearby`; Pro SKU field mask (no rating/userRatingCount); `places_nearby_saturated()` with 2×2 subdivision + place_id dedupe; 5 types × 3 radii; validator check COMP-01 PASS |
| **COMP-02** | ✅ verified | `classify_place()` with 12 corporate GP brands, 11 pharmacy brands, 21 exclude keywords; `fuzzy_dedupe_competitors()` with rapidfuzz (MIT, not fuzzywuzzy); validator check COMP-02 PASS |
| **COMP-03** | ✅ verified | GeoJSON persistence (`competitors.geojson`); folium map with toggleable ring layers; 3 static matplotlib+contextily figures; peer competitor table with GP-per-1,000 benchmarked against VIC 117/100k; validator check COMP-03 PASS |

## Code Review Fixes Verification

### CR-001: `ring_pops_erp` undefined in §5 — **FIXED** ✅

All 6 occurrences in `scripts/extend_v2_notebook_phase3.py` now use `v2_ring_pops_erp` (the correct Phase 2 variable name). Verified via grep: lines 972, 1006, 1007, 1071, 1122, 1124 — zero bare `ring_pops_erp` references remain. Commit: `43fbf2b`.

### CR-002: `peer_table["poa_code"]` wrong column name in §4.6 — **FIXED** ✅

The single occurrence (line 843) now reads `peer_table["POA_CODE21"]` — the correct column name from `g01_df[["POA_CODE21", "Total_P_P"]]` in Phase 2. Commit: `dcdb942`.

### WR-002: `aggregate_age_bands` 85+ pattern mismatch — **FIXED** ✅

The 65+ band list (line 944) now includes 4 pattern variants: `"85_ov", "85ov", "85plus", "85over"` — covering all documented ABS G04 column naming conventions (`Age_yr_85ov`, `Age_85plus`, `Age_85_over`). Commit: `bd2f671`.

## Human Verification Items

The following require a live Colab runtime with real data and cannot be verified by static source inspection:

1. **Colab Restart & Run All end-to-end** — with valid `GOOGLE_PLACES_KEY` + MBS SA3 Excel + AIHW Excel files in `data/local/`. All three SUMMARYs explicitly defer this. Confirms §1.4/§1.5/§4/§5 execute without runtime errors and produce the expected outputs (site_places, peer_places, competitors_gdf, ring_demand, market_share_results).
2. **Actual Google Places API calls** — verify saturation subdivision + dedupe work against the live 20-result cap, and that site_places/peer_places dicts are non-empty.
3. **MBS SA3 20604 Yarra filter** — verify the runtime sheet-name detection (`"SA3"` in sheet name) and SA3 column name match the real Excel file structure.
4. **AIHW age-band rate extraction** — verify the column-matching logic (`band.replace("-", "")` matching) works against the real AIHW data tables column names.
5. **competitors.geojson persistence** — verify D-08 write-on-first-run / load-from-cache-on-rerun path works with a real API key (first run writes, second run loads without API calls).

## Gaps

None. All 7 requirements verified, all 4 success criteria pass, all 3 code review fixes confirmed present, validator passes with 29 checks green. The only open items are runtime/human-verification tasks that require a live Colab environment with real API keys and manual-download data files — these are inherent to the phase design (manual downloads to `data/local/`, same pattern as Phase 2 SA1 shapefile) and are explicitly deferred by all three plan SUMMARYs.
