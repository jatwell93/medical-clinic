---
status: complete
phase: 02-catchment-demographics
source: [02-01-SUMMARY.md, 02-02-SUMMARY.md, 02-03-SUMMARY.md]
started: 2026-07-05T13:00:00Z
updated: 2026-07-05T13:30:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Validator passes (22 checks)
expected: Running `python scripts/validate_v2_notebook.py` prints 22 PASS lines (PIPE-01..06, v1 flaws eradicated, GEO-01..04, D-06, DEMO-01..04, D-11, D-03, CR-01, D-09b) and ends with `OVERALL: PASS`, exit code 0.
result: pass

### 2. Notebook structure preserved (36 cells)
expected: Johnston_St_v2.ipynb has 36 cells (19 code, 17 markdown) with §1.2 Geocode Site, §2 Geospatial Catchment, and §3 Demographics sections all present in order.
result: pass

### 3. Generator scripts idempotent (re-run safe)
expected: Re-running `python scripts/extend_v2_notebook.py` then `python scripts/extend_v2_notebook_demographics.py` prints "replaced N cells with M corrected cells" messages and the notebook stays at 36 cells (no duplication, no cell loss).
result: pass

### 4. Geocode cell (§1.2) — cached Google Geocoding + folium map
expected: §1.2 cell uses the Phase 1 CachedSession to call Google Geocoding for "292-296 Johnston St, Abbotsford VIC 3067", produces site_lat/site_lon, and renders a folium verification map with a D-31 "visually verify" instruction.
result: pass

### 5. EPSG:7855 buffers with 3km area assertion
expected: §2 cell reprojects to EPSG:7855 before buffering (no .buffer() on EPSG:4326 geometry), constructs 1/3/5 km rings, and asserts the 3km buffer area ≈ 28.27 km² (π×3²) within BASE_ASSUMPTIONS tolerance.
result: pass

### 6. SA1 area apportionment function
expected: `apportion_ring()` function is defined in §2, uses gpd.overlay to compute area-weighted SA1 population shares per ring — the headline v1 fix.
result: pass

### 7. v1-vs-v2 comparison (real, not stub)
expected: `compare_v1_v2(v1_ring_pops, v2_ring_pops)` has a two-parameter signature computing `pct_overstate = (v1/v2 - 1)*100`. The `v1_pop = v2_pop` stub is ABSENT from the notebook source. `v1_naive_catchment_pop` joins g01_df Total_P_P and returns the summed population.
result: pass

### 8. ABS G01/G02/G04 fetch with GCP fallback
expected: `fetch_abs_csv()` returns a (DataFrame, response) tuple through the CachedSession. Each fetch_g0X_poa function has try/except that falls back to local GCP files with a printed warning naming the missing data + substituted file. G04 fallback returns a stub with pct_65plus column only (no fabricated peer data).
result: pass

### 9. check_dataflow_exists XML-safe (no JSONDecodeError)
expected: `check_dataflow_exists()` parses the SDMX-ML XML dataflow endpoint via xml.etree.ElementTree (NOT `.json()`), with try/except safe-defaulting to True. No `flows_resp.json()` call present.
result: pass

### 10. ERP scaling to 2024 vintage
expected: §3 cell fetches ABS_ANNUAL_ERP_ASGS2021, computes growth_rate = pop_2024/pop_2021, applies it to both catchment population and peer benchmarking table, with a printed caveat. Defaults to 1.0 (no scaling) if ERP API unavailable.
result: pass

### 11. Peer benchmarking table with Phase 3 placeholders
expected: §3 produces a peer table with census columns (population raw + ERP-scaled, median age, 65+ share, median income) for POA 3067 + 9 peers, plus placeholder GP/pharmacy columns showing "— Phase 3" for Phase 3 to fill.
result: pass

### 12. 2×2 peer comparison chart grid
expected: §3 generates a matplotlib 2×2 chart grid comparing POA 3067 against peers across key demographics, with POA 3067 highlighted.
result: pass

### 13. Folium interactive map + static matplotlib figures
expected: §2 produces a folium interactive catchment map (1/3/5 km rings) AND one static matplotlib/contextily figure per ring (3 static figures total) for the PDF report.
result: pass

### 14. Colab runtime: §3 executes end-to-end without JSONDecodeError
expected: In Colab (Restart & Run All with API keys + SA1 shapefile), §3 demographics runs to completion with no JSONDecodeError from check_dataflow_exists. ABS G01/G02/G04 fetch succeeds (or falls back to GCP files with printed warnings).
result: pass

### 15. Colab runtime: v1-vs-v2 chart shows v1 > v2 (overstatement > 0%)
expected: In Colab after a full run, the v1-vs-v2 comparison chart shows v1 naive catchment population GREATER than v2 SA1-apportioned population (pct_overstate > 0%) — the headline teaching moment confirming v1's flaw is exposed.
result: pass

## Summary

total: 15
passed: 15
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none — all tests passed]
