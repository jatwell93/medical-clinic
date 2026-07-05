---
phase: 02-catchment-demographics
status: gaps_found
verified_at: 2026-07-05T13:00:00Z
score: 21/30
requirements:
  GEO-01: passed
  GEO-02: passed
  GEO-03: partial
  GEO-04: passed
  DEMO-01: partial
  DEMO-02: partial
  DEMO-03: partial
  DEMO-04: passed
human_verification:
  - "Actual Colab execution with API keys + SA1 shapefile to confirm end-to-end runtime behavior"
  - "Google Geocoding API returns correct coordinates for 292-296 Johnston St (expected ≈ -37.799, 145.003)"
  - "ABS C21_G01_POA / C21_G02_POA dataKey dimension order is correct (ROADMAP research flag — MEDIUM confidence)"
  - "Folium map renders inline in Colab with site pin, buffer rings, POA boundaries, Yarra River line"
  - "Static matplotlib + contextily figures render with basemap tiles (contextily pip-installed in Colab)"
  - "ERP SA2 code 206041001 is the correct ASGS Edition 3 Yarra SA2 code"
---

# Phase 02 Verification: Catchment & Demographics

## Summary

Phase 02 adds §1.2 geocoding, §2 geospatial catchment (EPSG:7855 buffers, SA1 apportionment), and §3 demographics (ABS census fetch with fallback, ERP scaling, peer benchmarking) to the Johnston_St_v2 notebook via two idempotent generator scripts. The structural scaffolding is strong: EPSG:7855 discipline is correctly applied (all `.buffer()` calls operate on reprojected geometries), the 3 km area assertion (≈28.27 km²) provides a runtime guard against the v1 degree-buffering flaw, all HTTP is routed through the `CachedSession`, `.env.example` contains no secrets, `.env` is gitignored, and both generator scripts are idempotent with marker-string guards. The validator exits 0 with OVERALL: PASS across all 21 checks.

However, **two critical bugs identified in 02-REVIEW.md are confirmed real** by reading the actual notebook cell source. CR-01 (`check_dataflow_exists()` calls `.json()` on the ABS dataflow endpoint that the notebook's own §1.2 smoke test proves returns SDMX-ML XML) will crash the notebook with `JSONDecodeError` at §3.2 on every run — online or offline, cached or not — because the cached response is still XML. This breaks all of §3 demographics (G04 fetch, SA1 fetch, v2 catchment totals, plausibility assertion, v1-vs-v2 comparison, ERP scaling, peer table, peer charts). CR-02 (the v1-vs-v2 comparison sets `v1_pop = v2_pop`, a placeholder never replaced) means the "headline teaching moment" chart always shows 0% overstatement — the opposite of the intended lesson. The validator passes both because it checks pattern presence, not logical correctness (IR-02 confirmed). These two bugs prevent ship-readiness and must be fixed before Phase 3.

## Must-Haves Verification

### Plan 02-01 (Geocode + Catchment) — 13/14 truths verified

| # | Must-Have Truth | Status | Evidence |
|---|----------------|--------|----------|
| 1 | §1.2 geocode cell calls Google Geocoding API through CachedSession | PASS | `Johnston_St_v2.ipynb` lines 354-381: `resp = session.get(GEOCODE_URL)`, `data = resp.json()` |
| 2 | Geocode response cached under data/cache/ | PASS | `session.get()` uses `CachedSession` with `cache_name=str(CACHE_DIR / "api_cache")` (line 243-244). Cached under `api_cache/`, not `geocode_*.json` — functionally equivalent |
| 3 | Prints site_lat, site_lon + "visually verify" instruction (D-31) | PASS | Lines 373-376: `print(f"[geocode] lat=...")`, `print(f"[geocode] ⚠ Visually verify this pin on the map below before proceeding.")` |
| 4 | §2 reprojects site to EPSG:7855 before any .buffer() call | PASS | Line 481: `site_metric = site_point.to_crs("EPSG:7855")` → line 485: `buf = site_metric.buffer(r)` |
| 5 | 3km buffer area assertion: abs(area_km2 - 28.27) < 0.1 (GEO-02, D-09a) | PASS | Lines 491-493: `assert abs(area_3k - BASE_ASSUMPTIONS["assert_3km_buffer_km2"]) < BASE_ASSUMPTIONS["assert_3km_buffer_tol"]` |
| 6 | Catchment pop plausibility assertion: 80e3 < ring_pop_3k < 110e3 (D-09b) | PASS (structurally) | Lines 951-953: `assert lo < v2_ring_pops[3000] < hi`. **Caveat:** gated behind CR-01 — unreachable at runtime because `check_dataflow_exists()` crashes before `v2_ring_pops` is populated |
| 7 | SA1-level area apportionment implemented (D-01) — NOT whole-postcode summing | PASS | Lines 534-544: `apportion_ring()` uses `sa1_gdf.overlay(ring, how="intersection")`, `inter["frac"] = inter.geometry.area / inter["SA1_CODE21"].map(full_area).values`, `inter["pop_in_ring"] = inter["frac"] * inter["Total_P_P"]` |
| 8 | v1-vs-v2 comparison: side-by-side table + grouped bar chart per ring (D-06) | **FAIL** | Lines 588-614: `compare_v1_v2()` defined and called at line 957, BUT line 600: `v1_pop = v2_pop  # placeholder, overwritten in §3` — placeholder NEVER overwritten. `v1_naive_catchment_pop()` (line 581-586) returns GeoDataFrame, not population sum. Chart always shows 0% overstatement (CR-02) |
| 9 | Folium map: site pin + 1/3/5 km rings + POA boundaries + Yarra River (D-25, D-30) | PASS | Lines 638-667: `folium.Map(...)`, `folium.Marker(...)`, `folium.GeoJson(buf_4326...)`, `folium.GeoJson(poa_peers_4326...)`, `folium.PolyLine(yarra_pts...)` |
| 10 | Static matplotlib + contextily figures, one per ring (D-27) | PASS | Lines 676-701: `for r in BASE_ASSUMPTIONS["catchment_radii_m"]: fig, ax = plt.subplots(...)`, `cx.add_basemap(ax, crs="EPSG:4326", source=cx.providers.CartoDB.Positron)` |
| 11 | Uniform-density caveat markdown note present (D-05) | PASS | Lines 708-718: §2.6 markdown cell with "Caveat (uniform-density assumption)" |
| 12 | No .buffer() on EPSG:4326 GeoDataFrame (PITFALLS.md Pitfall 1) | PASS | Only `.buffer()` call is line 485 on `site_metric` (reprojected to EPSG:7855 at line 481). Validator confirms no `.buffer(` on same line as `EPSG:4326` |
| 13 | No bare requests.get — all HTTP through CachedSession | PASS | All HTTP calls use `session.get()`. Validator regex check passes |
| 14 | No numeric literal outside BASE_ASSUMPTIONS except unit conversions (PIPE-05) | PASS | `/ 1e6` (m²→km²), `* 100` (fraction→percent) are unit conversions. SA2 code `206041001` (line 1001) and Yarra coords are data, not assumptions. Minor: SA2 code should be in BASE_ASSUMPTIONS |

### Plan 02-02 (Demographics) — 8/16 truths verified

| # | Must-Have Truth | Status | Evidence |
|---|----------------|--------|----------|
| 1 | §3 fetches ABS G01/G02 via C21_G01_POA / C21_G02_POA through CachedSession | PASS | Lines 788-836: `fetch_abs_csv("ABS,C21_G01_POA,latest", ...)`, `fetch_abs_csv("ABS,C21_G02_POA,latest", ...)`, both use `session.get(url)` |
| 2 | Runtime-verifies C21_G04_POA existence + branches to fallback (D-11, D-12) | **FAIL** | Line 848: `G04_POA_EXISTS = check_dataflow_exists("C21_G04_POA")` — `check_dataflow_exists()` (lines 764-770) calls `flows_resp.json()` on XML endpoint → `JSONDecodeError` on every run (CR-01). No try/except around the call |
| 3 | Local GCP fallback parses into SAME tidy schema (D-17) | PARTIAL | Lines 772-786: `parse_gcp_g01_to_tidy()` exists with correct schema columns, BUT returns all zeros (`"Total_P_P": 0`) with `# TODO: populate from actual xlsx cells` (WR-02). Schema parity met structurally; values are stub |
| 4 | Fallback trigger automatic on API failure + printed warning (D-15) | PARTIAL | G01/G02 fallback: PASS (lines 796-807, try/except → GCP file + warning). G04 fallback: FAIL — `fetch_g04_poa()` except block (line 857-859) returns empty DataFrame, does NOT call `fetch_g04_fallback()` (WR-03) |
| 5 | Peer benchmarking table with all required columns (D-26) | PASS | Lines 1057-1080: `peer_table` merges G01/G02/G04, has `Total_P_P`, `Total_P_P_erp`, `Median_age_persons`, `pct_65plus`, `Median_tot_hshld_inc_weekly`, `gp_count = "— Phase 3"`, `pharmacy_count = "— Phase 3"`, `is_site` |
| 6 | ERP scaling applied to BOTH catchment pop AND peer table (D-24) | PASS | Lines 1018-1024: `v2_ring_pops_erp = {r: pop * erp_growth_rate ...}`. Lines 1067-1071: `peer_table["Total_P_P_erp"] = (peer_table["Total_P_P"] * erp_growth_rate).round(0)` |
| 7 | ERP source is ABS_ANNUAL_ERP_ASGS2021 through CachedSession (D-23) | PASS | Line 1001: `fetch_abs_csv("ABS,ABS_ANNUAL_ERP_ASGS2021,latest", ...)` uses `session.get()` |
| 8 | ERP caveat printed: 2021 → 2024 ERP-adjusted, SA2 rate (D-22) | PASS | Lines 1027-1029: `print(f"[erp] ⚠ Caveat: Population scaled from 2021 Census baseline to {ERP_VINTAGE} ERP-adjusted")` |
| 9 | Peer comparison 2×2 bar chart grid, POA 3067 highlighted (D-29) | PASS | Lines 1100-1117: `fig, axes = plt.subplots(2, 2, figsize=(12, 8))`, 4 charts (pop ERP, median age, 65+ share, median income), `colors = ["#d62728" if s else "#2ca02c" for s in peer_table["is_site"]]` |
| 10 | SA1 total persons fetched + wired into §2.3 apportionment (D-03) | **FAIL** | Lines 895-963: code structure correct (`sa1_codes = sa1_in_5k["SA1_CODE21"].tolist()`, `fetch_abs_csv("ABS,C21_G01_SA1,latest", ...)`), BUT line 903: `SA1_G01_EXISTS = check_dataflow_exists("C21_G01_SA1")` crashes with CR-01 before SA1 fetch can execute. Unreachable at runtime |
| 11 | §2.3 apportionment called with real SA1 pop → v2 totals per ring | **FAIL** | Line 946: `pop, inter = apportion_ring(sa1_in_5k, sa1_pop_df, buffers[r].iloc[0])` — call exists but is unreachable due to CR-01 crash at line 903 |
| 12 | §2.4 compare_v1_v2() called with real v2 totals → chart with actual numbers | **FAIL** | Line 957: `comparison_df = compare_v1_v2(v2_ring_pops)` — call exists but (a) unreachable due to CR-01, and (b) even if reached, CR-02 makes it a no-op (`v1_pop = v2_pop`) |
| 13 | Catchment pop plausibility assertion fires: 80e3 < ring_pop_3k < 110e3 (D-09b) | **FAIL** | Lines 951-953: assertion exists but unreachable due to CR-01 crash at line 903 |
| 14 | Age band structure uses ABS standard 5-year bands (D-18) | PARTIAL | Line 847: comment documents "0-4, 5-9, ..., 80-84, 85+". Line 877: `age_bands_65plus = [b for b in g04_df.columns if "65" in b or "70" in b or "75" in b or "80" in b or "85" in b]` — fragile substring matching (WR-04), could match non-age columns |
| 15 | No bare requests.get — all HTTP through CachedSession | PASS | All HTTP calls use `session.get()`. Validator confirms |
| 16 | No numeric literal outside BASE_ASSUMPTIONS except unit conversions (PIPE-05) | PASS | Same assessment as Plan 02-01 #14 |

## Requirement Traceability

| REQ-ID | Requirement Text | Status | Code Evidence | Gap |
|--------|-----------------|--------|---------------|-----|
| GEO-01 | Site geocoded from exact address via Google Geocoding API, cached | **PASSED** | `Johnston_St_v2.ipynb` lines 354-381: `session.get(GEOCODE_URL)` with `GEOCODE_URL` built from `SITE_ADDRESS` = "292-296 Johnston St, Abbotsford VIC 3067". Response parsed for `site_lat`, `site_lon`. Folium verification map at lines 390-400. | None — requires human verification of actual API response |
| GEO-02 | 1/3/5 km buffers in EPSG:7855 with sanity assertion (3 km ≈ 28.3 km²) | **PASSED** | Lines 478-494: `site_point.to_crs("EPSG:7855")` → `site_metric.buffer(r)` for r in [1000, 3000, 5000]. Assertion: `abs(area_3k - 28.27) < 0.1`. No `.buffer()` on EPSG:4326 geometry. | None |
| GEO-03 | Catchment population by area-apportioning POA populations (not whole-postcode summing) | **PARTIAL** | `apportion_ring()` (lines 534-544) implements SA1-level overlay+intersection+area-fraction weighting — structurally correct and finer than POA. Called at line 946. BUT: (1) unreachable at runtime due to CR-01 crash at `check_dataflow_exists()`, (2) v1-vs-v2 comparison that demonstrates the fix is a no-op (CR-02: `v1_pop = v2_pop`) | CR-01 blocks runtime execution; CR-02 undermines the teaching moment that proves the fix works |
| GEO-04 | Interactive folium map + static matplotlib+contextily twin for PDF | **PASSED** | Lines 638-667: folium map with site pin, buffer rings, POA boundaries, Yarra River polyline. Lines 676-701: static matplotlib + `cx.add_basemap()` one per ring. | None — requires human verification of map rendering |
| DEMO-01 | G01/G02 from ABS Data API with local GCP fallback | **PARTIAL** | Lines 788-836: `fetch_g01_poa()` and `fetch_g02_poa()` use `fetch_abs_csv("ABS,C21_G01_POA,latest", ...)` through `session.get()`. Both have try/except → GCP fallback. BUT: (1) `parse_gcp_g01_to_tidy()` returns all zeros (WR-02), (2) G04 path broken by CR-01 | GCP fallback parser is a zero-stub (WR-02); G04 dataflow check crashes (CR-01) |
| DEMO-02 | Demographic profile for POA 3067 + 9 peers with comparison charts | **PARTIAL** | Lines 1057-1080: peer table merges G01/G02/G04 for 10 POAs. Lines 1100-1117: 2×2 chart grid. BUT: data depends on G01/G02/G04 fetches — G04 path crashes at `check_dataflow_exists()` (CR-01), so `g04_df` is never populated. Peer table merge at line 1063 would fail or produce NaN for `pct_65plus` | CR-01 prevents G04 fetch; peer table incomplete at runtime |
| DEMO-03 | Peer benchmarking table: demand/supply indicators across peer set | **PARTIAL** | Lines 1057-1080: table has `Total_P_P`, `Median_age_persons`, `pct_65plus`, `Median_tot_hshld_inc_weekly`, `gp_count = "— Phase 3"`, `pharmacy_count = "— Phase 3"`. Structure is correct. BUT: `pct_65plus` depends on G04 which is broken by CR-01; fallback returns 0 (WR-02/WR-03) | CR-01 blocks G04; fallback values are zeros, not real data |
| DEMO-04 | Census staleness addressed with ERP scaling + caveat | **PASSED** | Lines 991-1032: `fetch_erp_sa2()` uses `fetch_abs_csv("ABS,ABS_ANNUAL_ERP_ASGS2021,latest", ...)` with try/except (NOT `check_dataflow_exists` — so not affected by CR-01). `erp_growth_rate = pop_2024 / pop_2021`. Applied to catchment (line 1020) and peer table (line 1069). Caveat printed (lines 1027-1029). Default rate=1.0 on failure. | None structurally — SA2 code `206041001` is hardcoded (IR-01) but failure is graceful |

## Code Review Findings Impact

| Finding | Severity | Confirmed Real? | Must-Have Impact | Requirement Impact |
|---------|----------|----------------|------------------|-------------------|
| **CR-01**: `check_dataflow_exists()` calls `.json()` on SDMX-ML XML endpoint → `JSONDecodeError` | Critical | **YES** — line 767: `flows = flows_resp.json()`. §1.2 smoke test (lines 268-269, 295-296, 305-308) explicitly documents and asserts the endpoint returns XML. No `?format=json` parameter. No try/except around calls at lines 848 and 903. | Breaks Plan 02-02 truths #2, #10, #11, #12, #13 (5 truths). Also cascades to #3, #4, #5, #6, #8, #9, #14, #16 (data-dependent truths). | GEO-03 (runtime-blocked), DEMO-01 (G04 path broken), DEMO-02 (G04 data missing), DEMO-03 (pct_65plus missing) |
| **CR-02**: `v1_pop = v2_pop` placeholder never replaced → comparison is no-op | Critical | **YES** — line 600: `v1_pop = v2_pop  # placeholder, overwritten in §3`. §3.3 (line 957) calls `compare_v1_v2(v2_ring_pops)` without modifying the function or passing v1 data. `v1_naive_catchment_pop()` (line 586) returns GeoDataFrame, not population sum. | Breaks Plan 02-01 truth #8, Plan 02-02 truth #12. | GEO-03 (teaching moment broken — chart shows 0% overstate, opposite of intended lesson) |
| **WR-01**: `check_dataflow_exists()` has no try/except — violates no-hard-fail | Warning | **YES** — lines 764-770: function body has no error handling. Callers at lines 848, 903 do not wrap in try/except. | Compounds CR-01 — even if JSON parsing were fixed, network errors would crash the notebook | DEMO-01 (no-hard-fail violation) |
| **WR-02**: `parse_gcp_g01_to_tidy()` returns all zeros | Warning | **YES** — lines 778-786: `pd.DataFrame([{"POA_CODE21": "3067", "Total_P_P": 0, ...}])` with `# TODO: populate from actual xlsx cells` | Degrades Plan 02-02 truth #3. In fallback mode, peer table shows 0 population for 3067. | DEMO-01 (fallback produces misleading zeros, not N/A) |
| **WR-03**: G04 fallback inconsistent — no GCP fallback on API exception | Warning | **YES** — lines 857-859: `fetch_g04_poa()` except block returns `pd.DataFrame(), "none"`. `fetch_g04_fallback()` (lines 861-871) only called when `G04_POA_EXISTS` is False, not on API exception. | Degrades Plan 02-02 truth #4. G04 returns empty on network failure while G01/G02 fall back to GCP. | DEMO-01 (inconsistent fallback behavior) |
| **WR-04**: G04 age-band column detection uses fragile substring matching | Warning | **YES** — line 877: `[b for b in g04_df.columns if "65" in b or "70" in b or "75" in b or "80" in b or "85" in b]` | Degrades Plan 02-02 truth #14. Could match non-age columns, producing incorrect `pct_65plus`. | DEMO-02/DEMO-03 (incorrect 65+ share if columns don't match expected pattern) |
| **IR-01**: ERP SA2 code `206041001` hardcoded without runtime verification | Info | **YES** — line 1001: `f"all.206041001.A.2021+2024"` with comment `# verify at runtime` but no verification code. | No must_have impact — failure is graceful (rate defaults to 1.0). | DEMO-04 (low impact — graceful degradation) |
| **IR-02**: Validator D-06 check is pattern-presence no-op | Info | **YES** — validator lines 347-351: `d06_call = "compare_v1_v2(" in all_source` and `d06_totals = "v2_ring_pops" in all_source`. Both strings present in stub form. Check passes despite CR-02. | False confidence that D-06 is satisfied. | GEO-03 (validator gives false PASS on broken comparison) |
| **IR-03**: `v1_naive_catchment_pop()` returns GeoDataFrame, not population | Info | **YES** — line 586: `return touching` (GeoDataFrame). Function name suggests it returns a population number. | Part of CR-02 stub. Confusing for teaching notebook. | GEO-03 (naming misleading) |

## Validator Assessment

The validator (`scripts/validate_v2_notebook.py`) exits 0 with OVERALL: PASS across all 21 checks. However, verification of the validator's assertion quality reveals:

- **Real assertions:** PIPE-01 (top-to-bottom flow via `first_def_cell` ordering), PIPE-02/03/04/05 (multi-condition substring checks), v1 flaw eradication (regex-based `requests.get` detection with prefix checking), GEO-02 (no `.buffer(` on same line as `EPSG:4326` — line-by-line check). These verify structural properties meaningfully.
- **Pattern-presence no-ops:** GEO-01 (checks `"geocode/json" in all_source`), GEO-03 (checks `"overlay(" in all_source`), GEO-04 (checks `"folium.Map" in all_source`), DEMO-01..04 (substring checks for API names, column names), D-06 (checks `"compare_v1_v2(" in all_source` — passes despite CR-02 no-op), D-11 (checks `"check_dataflow_exists" in all_source` — passes despite CR-01 crash). These verify code presence but NOT logical correctness.

The validator cannot catch CR-01 (it doesn't verify that `.json()` is called on a JSON endpoint) or CR-02 (it doesn't verify that `v1_pop` is not assigned from `v2_pop`). This is a known limitation of pattern-based validators, but IR-02 notes the D-06 check could be strengthened to assert `"v1_pop = v2_pop"` does NOT appear in source.

## Human Verification Items

1. **Actual Colab execution** — The notebook cannot be executed in this verification environment (no Colab runtime, no API keys, no SA1 shapefile). All structural verification is based on reading cell source. A full Restart & Run All in Colab with keys + shapefiles is needed to confirm runtime behavior — **but CR-01 WILL crash the notebook at §3.2 before any of this can be tested**.
2. **Google Geocoding API response** — Confirm the geocode returns coordinates ≈ (-37.799, 145.003) for "292-296 Johnston St, Abbotsford VIC 3067" and that the pin lands on the Johnston St × Hoddle St corner.
3. **ABS C21_G01_POA / C21_G02_POA dataKey dimension order** — ROADMAP research flag (MEDIUM confidence). The dataKey `f"all.{PEER_POA_CODES}.A.2021"` assumes dimension order [MEASURE, POA, FREQ, TIME]. Must be verified via `/rest/datastructure/ABS/{id}` at runtime.
4. **Folium map rendering** — Confirm the interactive map renders inline in Colab with all layers (site pin, 3 buffer rings, peer POA boundaries, Yarra River polyline).
5. **Static matplotlib + contextily figures** — Confirm contextily is pip-installed in Colab and basemap tiles render. Three figures (1/3/5 km) should each show the ring, POA boundaries, site pin, and Yarra River annotation.
6. **ERP SA2 code 206041001** — Confirm this is the correct ASGS Edition 3 Yarra SA2 code. If wrong, ERP fetch returns no data and scaling silently defaults to 1.0 (graceful but silent).

## Gaps

### GAP-01: CR-01 — `check_dataflow_exists()` crashes on XML endpoint (CRITICAL)
- **Requirement IDs affected:** DEMO-01, DEMO-02, DEMO-03, GEO-03
- **What's missing:** `check_dataflow_exists()` (line 764-770) calls `flows_resp.json()` on `https://data.api.abs.gov.au/rest/dataflow?detail=allstubs` which returns SDMX-ML XML (as documented by the notebook's own §1.2 smoke test at lines 268-269, 295-296). This raises `JSONDecodeError` on every run. The function is called unwrapped at lines 848 and 903.
- **Impact:** The entire §3 demographics section is non-functional. G04 age bands, SA1 total persons, v2 catchment totals, plausibility assertion, v1-vs-v2 comparison, and downstream peer table/charts are all unreachable. The notebook cannot complete a Restart & Run All.
- **Recommended fix:** Wrap `check_dataflow_exists()` body in try/except, returning `True` on any failure (safe default — attempt the fetch and rely on existing try/except in `fetch_g01_poa`/`fetch_g04_poa`/etc.). Alternatively, add `?format=json` to the URL and verify the response structure, or parse the XML with `xml.etree.ElementTree`. Option (c) from 02-REVIEW.md is most defensible given the no-hard-fail principle.

### GAP-02: CR-02 — v1-vs-v2 comparison is a no-op (CRITICAL)
- **Requirement IDs affected:** GEO-03
- **What's missing:** `compare_v1_v2()` (line 600) sets `v1_pop = v2_pop  # placeholder, overwritten in §3` but §3.3 (line 957) calls `compare_v1_v2(v2_ring_pops)` without modifying the function or passing v1 population data. `v1_naive_catchment_pop()` (line 586) returns a GeoDataFrame, not a population sum. The comparison chart always shows v1 == v2 with 0% overstatement.
- **Impact:** The headline pedagogical deliverable — showing v1's whole-postcode summing inflated catchment population 2–4× — is broken. An investor running the notebook sees a chart proving v1 == v2, which is the opposite of the intended lesson.
- **Recommended fix:** In §3.3 after the SA1 census fetch, compute v1 naive population by summing `Total_P_P` from `g01_df` for all POAs touching each ring. Pass both v1 and v2 totals to a revised `compare_v1_v2(v1_ring_pops, v2_ring_pops)`. The `v1_naive_catchment_pop` function should join `g01_df[["POA_CODE21", "Total_P_P"]]` and return the sum, not the raw GeoDataFrame.

### GAP-03: WR-02 — GCP fallback parser returns all zeros (WARNING)
- **Requirement IDs affected:** DEMO-01
- **What's missing:** `parse_gcp_g01_to_tidy()` (lines 778-786) returns `pd.DataFrame([{"POA_CODE21": "3067", "Total_P_P": 0, ...}])` with a `# TODO: populate from actual xlsx cells` comment. Zero is not a valid population.
- **Impact:** In fallback mode (ABS API unavailable), the peer table shows 0 population for POA 3067 — worse than showing "N/A".
- **Recommended fix:** Either implement the xlsx parsing (GCP G01 sheet has known structure), or return an empty DataFrame with correct schema and print a warning that fallback values are not yet populated.

### GAP-04: WR-03 — G04 fallback inconsistent (WARNING)
- **Requirement IDs affected:** DEMO-01
- **What's missing:** `fetch_g04_poa()` except block (lines 857-859) returns empty DataFrame without calling `fetch_g04_fallback()`. The fallback is only triggered when `G04_POA_EXISTS` is False, not on API exception.
- **Impact:** If G04 dataflow exists but the network call fails, G04 returns empty with no GCP fallback attempt, while G01/G02 degrade to GCP. Inconsistent fallback behavior.
- **Recommended fix:** In the `except` block of `fetch_g04_poa()`, call `fetch_g04_fallback()` instead of returning empty.

### GAP-05: WR-04 — G04 age-band column detection fragile (WARNING)
- **Requirement IDs affected:** DEMO-02, DEMO-03
- **What's missing:** Line 877 uses substring matching (`"65" in b or "70" in b or ...`) that could match non-age columns.
- **Impact:** If the ABS CSV-with-labels format produces column names where these substrings appear in non-age contexts, `pct_65plus` will be computed incorrectly.
- **Recommended fix:** Use explicit column name patterns based on the ABS G04 data dictionary (e.g., `b.startswith("Age_6") or b.startswith("Age_7") or b.startswith("Age_8")`), or inspect the datastructure endpoint at runtime. Add a print of matched columns for teaching transparency.

### GAP-06: IR-02 — Validator D-06 check is a no-op (INFO)
- **Requirement IDs affected:** GEO-03 (false confidence)
- **What's missing:** Validator D-06 check (lines 347-351) only verifies pattern presence (`"compare_v1_v2(" in all_source`), not logical correctness. It passes despite CR-02.
- **Impact:** The validator gives false confidence that D-06 is satisfied. A broken headline deliverable passes validation.
- **Recommended fix:** Add a check that `"v1_pop = v2_pop"` does NOT appear in source (known stub pattern detection).

## Verdict

Phase 02's structural scaffolding is strong — EPSG:7855 discipline, CachedSession routing, secrets hygiene, idempotent generators, and teaching commentary are all correctly implemented and verified. The geocode (GEO-01), buffer construction with assertion (GEO-02), maps (GEO-04), and ERP scaling (DEMO-04) requirements are fully met in code. However, **two critical bugs prevent ship-readiness**: CR-01 (`check_dataflow_exists()` calling `.json()` on an XML endpoint) will crash the notebook at §3.2 on every run, making all of §3 demographics non-functional and blocking GEO-03, DEMO-01, DEMO-02, and DEMO-03 at runtime; and CR-02 (the v1-vs-v2 comparison being a no-op with `v1_pop = v2_pop`) undermines the headline pedagogical deliverable of the entire phase. The validator passes both because it checks pattern presence, not logical correctness. These bugs must be fixed before Phase 3 can proceed — CR-01 needs a try/except wrapper with safe default (or XML parsing), and CR-02 needs the POA total persons (already fetched in `g01_df`) joined into the v1 naive sum. The warning findings (GCP stub returning zeros, G04 fallback inconsistency, fragile column matching) should also be addressed but degrade gracefully. **Phase goal not yet achieved — gaps need closure before proceeding.**
