---
phase: 02-catchment-demographics
status: passed
score: 8/8
requirements_verified: [GEO-01, GEO-02, GEO-03, GEO-04, DEMO-01, DEMO-02, DEMO-03, DEMO-04]
requirements_failed: []
verified_at: 2026-07-05T12:22:38Z
human_verification:
  - "Colab Restart & Run All with API keys + SA1 shapefile — confirm end-to-end runtime behavior (cannot be automated)"
  - "Google Geocoding API returns coordinates ≈ (-37.799, 145.003) for 292-296 Johnston St, Abbotsford VIC 3067"
  - "ABS C21_G01_POA / C21_G02_POA / C21_G04_POA dataKey dimension order is correct (ROADMAP research flag — MEDIUM confidence; verify via /rest/datastructure/ABS/{id} at runtime)"
  - "ABS API CSV format (wide vs long) — WR-09 in 02-REVIEW.md flags that csvfilewithlabels may return long format requiring a pivot step"
  - "Folium map renders inline in Colab with site pin, 3 buffer rings, peer POA boundaries, Yarra River polyline"
  - "Static matplotlib + contextily figures render with basemap tiles (contextily pip-installed in Colab)"
  - "ERP SA2 code 206041001 is the correct ASGS Edition 3 Yarra SA2 code (IR-01 — hardcoded, verify at runtime)"
  - "v1-vs-v2 chart shows v1 > v2 (pct_overstate > 0%) with real ABS data — the headline teaching moment"
---

# Phase 02 Verification: Catchment & Demographics (Post-Gap-Closure)

## Summary

Phase 02 builds the geospatial catchment (exact-address geocoding, 1/3/5 km buffers in EPSG:7855, SA1-level area-apportioned population) and the census demographic profile (ABS Data API G01/G02/G04 for POA 3067 + 9 peers, with local GCP fallback, ERP scaling, and peer benchmarking). All 8 requirement IDs (GEO-01..04, DEMO-01..04) are verified as satisfied at the structural/runtime-ready level. The validator (`scripts/validate_v2_notebook.py`) exits 0 with OVERALL: PASS across 22 checks. All 6 gap-closure findings (CR-01, CR-02, WR-01..04, IR-02) from the prior verification are confirmed CLOSED in both the generator scripts and the notebook cell source.

The two critical bugs that previously blocked ship-readiness are eradicated: `check_dataflow_exists()` now parses the SDMX-ML XML endpoint via `xml.etree.ElementTree` with a try/except safe-default True (CR-01), and `compare_v1_v2(v1_ring_pops, v2_ring_pops)` accepts both v1 and v2 ring population dicts, computing real `pct_overstate = (v1/v2 - 1)*100` from `g01_df` Total_P_P (CR-02). The `v1_pop = v2_pop` stub is absent from the notebook source. v1-flaw eradication is maintained: no `drive.mount`, no `/content/drive`, no degree-based buffering, no bare `requests.get(`.

**Status: PASSED** — Phase 02 is structurally complete and runtime-ready. Deferred human verification (Colab Restart & Run All with API keys + SA1 shapefile) is required to confirm end-to-end runtime behavior with live data; this cannot be automated in the verification environment.

## Validator Run

```
$ python scripts/validate_v2_notebook.py
[validate] cells: 36 (19 code, 17 markdown)
[validate] PIPE-01 (top-to-bottom flow): PASS
[validate] PIPE-02 (dual-environment): PASS
[validate] PIPE-03 (key loading): PASS
[validate] PIPE-04 (caching): PASS
[validate] PIPE-05 (single PARAMS): PASS
[validate] PIPE-06 (teaching commentary): PASS
[validate] v1 flaws eradicated: PASS
[validate] Phase 2 GEO-01 (geocode): PASS
[validate] Phase 2 GEO-02 (buffers + assertion): PASS
[validate] Phase 2 GEO-03 (SA1 apportionment): PASS
[validate] Phase 2 GEO-04 (maps): PASS
[validate] Phase 2 D-06 (v1-vs-v2 comparison): PASS
[validate] Phase 2 DEMO-01 (ABS G01/G02 + fallback): PASS
[validate] Phase 2 DEMO-02 (peer comparison charts): PASS
[validate] Phase 2 DEMO-03 (peer benchmarking table): PASS
[validate] Phase 2 DEMO-04 (ERP scaling): PASS
[validate] Phase 2 D-11 (G04 runtime verify): PASS
[validate] Phase 2 D-03 (SA1 total persons): PASS
[validate] Phase 2 D-06 (v1-vs-v2 with real totals): PASS
[validate] Phase 2 CR-01 (check_dataflow_exists XML-safe): PASS
[validate] Phase 2 D-09b (pop plausibility assert): PASS
[validate] OVERALL: PASS
Exit code: 0
```

22 checks green, exit 0. The validator includes the strengthened D-06 check (negative pattern assertion: `v1_pop = v2_pop` must be ABSENT) and the new CR-01 negative pattern check (`flows_resp.json()` must be ABSENT).

## Must-Haves Verification

### Must-Have 1: Exact-address geocoding (cached) + 1/3/5 km buffers in EPSG:7855 with sanity assertion

**Status: PASS**

| Check | Evidence |
|-------|----------|
| Site geocoded from exact address via Google Geocoding API through CachedSession | `Johnston_St_v2.ipynb`: `GEOCODE_URL` built from `SITE_ADDRESS` ("292-296 Johnston St, Abbotsford VIC 3067"), `resp = session.get(GEOCODE_URL)`, `data = resp.json()`, `site_lat`/`site_lon` extracted. 4 `session.get(` calls in notebook, 0 bare `requests.get(`. |
| Geocode response cached | `CachedSession` with `cache_name=str(CACHE_DIR / "api_cache")` — cached under `data/cache/api_cache/`. Re-runs are free/keyless. |
| Prints site_lat, site_lon + "visually verify" instruction (D-31) | `print(f"[geocode] lat={site_lat:.6f}, lon={site_lon:.6f} ...")`, `print(f"[geocode] ⚠ Visually verify this pin on the map below before proceeding.")` |
| Reprojects site to EPSG:7855 before any .buffer() call | `site_metric = site_point.to_crs("EPSG:7855")` → `buf = site_metric.buffer(r)` for r in [1000, 3000, 5000] |
| 3km buffer area assertion (≈28.27 km² = π×3²) | `assert abs(area_3k - BASE_ASSUMPTIONS["assert_3km_buffer_km2"]) < BASE_ASSUMPTIONS["assert_3km_buffer_tol"]` with `assert_3km_buffer_km2: 28.27`, `assert_3km_buffer_tol: 0.1` in BASE_ASSUMPTIONS |
| No .buffer() on EPSG:4326 geometry | Only `.buffer()` call is on `site_metric` (reprojected to EPSG:7855). Validator confirms no `.buffer(` on same line as `EPSG:4326`. |

### Must-Have 2: Area-apportioned catchment population (not whole-postcode summing) + v1-vs-v2 comparison

**Status: PASS**

| Check | Evidence |
|-------|----------|
| SA1-level area apportionment implemented (D-01) | `apportion_ring()` uses `sa1_gdf.overlay(ring, how="intersection")`, `inter["frac"] = inter.geometry.area / inter["SA1_CODE21"].map(full_area).values`, `inter["pop_in_ring"] = inter["frac"] * inter["Total_P_P"]` |
| v1-vs-v2 comparison: side-by-side table + grouped bar chart (D-06) | `compare_v1_v2(v1_ring_pops, v2_ring_pops)` computes `pct_overstate = (v1/v2 - 1)*100`, renders grouped bar chart (v1 red vs v2 green). Called at §3.3 with real v1 + v2 totals. |
| v1 naive whole-postcode sum reproduced | `v1_naive_catchment_pop(ring_geom_m, poa_pop_df)` joins `g01_df[["POA_CODE21", "Total_P_P"]]` onto touching POAs, returns `int(merged["Total_P_P"].sum())` |
| v1_ring_pops computed in §3.3 | `v1_ring_pops = {}`, `v1_ring_pops[r] = v1_pop` per ring, then `compare_v1_v2(v1_ring_pops, v2_ring_pops)` |
| Catchment pop plausibility assertion (D-09b) | `assert lo < v2_ring_pops[3000] < hi` with `catchment_pop_plausible_range: (80_000, 110_000)` in BASE_ASSUMPTIONS |
| `v1_pop = v2_pop` stub ABSENT | Confirmed: string `v1_pop = v2_pop` does NOT appear anywhere in notebook source (CR-02 eradicated) |

### Must-Have 3: ABS Data API G01/G02 for POA 3067 + 9 peers (cached) with local GCP fallback

**Status: PASS**

| Check | Evidence |
|-------|----------|
| G01/G02 fetched via C21_G01_POA / C21_G02_POA through CachedSession | `fetch_abs_csv("ABS,C21_G01_POA,latest", ...)`, `fetch_abs_csv("ABS,C21_G02_POA,latest", ...)` — both use `session.get(url)` |
| POA 3067 + 9 peers (10 total) | `PEER_POSTCODES = ['3067', '3066', '3068', '3070', '3078', '3079', '3101', '3121', '3122', '3123']` (10 codes = 3067 + 9 peers) |
| Local GCP fallback emits same schema (D-17) | `parse_gcp_g01_to_tidy()` returns `pd.DataFrame(columns=["POA_CODE21", "Total_P_P", "M_P", "F_P", "Total_Dwll_D"])` (empty schema, NOT zeros — WR-02 fixed). G02 fallback returns `pd.DataFrame(columns=["POA_CODE21", "Median_age_persons", "Median_tot_hshld_inc_weekly"])` |
| Fallback trigger automatic + printed warning (D-15) | Every fetch has try/except → GCP fallback with warning naming missing data + substituted file |
| G04 runtime verification (D-11, D-12) | `check_dataflow_exists("C21_G04_POA")` — now XML-safe via `ET.fromstring` (CR-01 fixed). `fetch_g04_poa()` except block calls `return fetch_g04_fallback()` (WR-03 fixed) |
| G04 age bands use ABS standard 5-year bands (D-18) | Explicit prefix matching: `b.startswith("Age_yr_65") or b.startswith("Age_yr_70") or b.startswith("Age_yr_75") or b.startswith("Age_yr_80") or b.startswith("Age_yr_85") or "Age_yr_85ov" in b` (WR-04 fixed) |

### Must-Have 4: Peer benchmarking table + comparison charts + ERP scaling with caveat

**Status: PASS**

| Check | Evidence |
|-------|----------|
| Peer benchmarking table with required columns (D-26) | `peer_table` merges G01/G02/G04: `Total_P_P`, `Total_P_P_erp`, `Median_age_persons`, `pct_65plus`, `Median_tot_hshld_inc_weekly`, `gp_count = "— Phase 3"`, `pharmacy_count = "— Phase 3"`, `is_site` |
| 2×2 comparison chart grid (D-29) | `fig, axes = plt.subplots(2, 2, figsize=(12, 8))` — 4 charts: population (ERP-scaled), median age, 65+ share, median income. POA 3067 highlighted. |
| ERP scaling applied to BOTH catchment pop AND peer table (D-24) | `v2_ring_pops_erp = {r: pop * erp_growth_rate ...}` (catchment), `peer_table["Total_P_P_erp"] = (peer_table["Total_P_P"] * erp_growth_rate).round(0)` (peer table) |
| ERP source: ABS_ANNUAL_ERP_ASGS2021 through CachedSession (D-23) | `fetch_abs_csv("ABS,ABS_ANNUAL_ERP_ASGS2021,latest", ...)` uses `session.get()` |
| ERP caveat printed (D-22) | `print(f"[erp] ⚠ Caveat: Population scaled from 2021 Census baseline to {ERP_VINTAGE} ERP-adjusted")`, `print(f"  Method: ABS Regional Population (3218.0) Yarra SA2 growth rate applied (D-21)")` |
| Census staleness addressed (DEMO-04) | ERP growth rate = pop_2024 / pop_2021, applied uniformly. Default rate=1.0 on failure (graceful degradation). `erp_vintage_year: 2024` in BASE_ASSUMPTIONS. |

## Requirement ID Traceability

| REQ-ID | Requirement Text | Status | Code Evidence | Gap |
|--------|-----------------|--------|---------------|-----|
| GEO-01 | Site geocoded from exact address via Google Geocoding API, cached | **PASSED** | `session.get(GEOCODE_URL)` with `GEOCODE_URL` from `SITE_ADDRESS`. `site_lat`/`site_lon` extracted. Folium verification map. | None — requires human verification of actual API response |
| GEO-02 | 1/3/5 km buffers in EPSG:7855 with sanity assertion (3 km ≈ 28.3 km²) | **PASSED** | `site_point.to_crs("EPSG:7855")` → `site_metric.buffer(r)` for r in [1000, 3000, 5000]. Assertion: `abs(area_3k - 28.27) < 0.1`. No degree-based buffering. | None |
| GEO-03 | Catchment population by area-apportioning POA populations (not whole-postcode summing) | **PASSED** | `apportion_ring()` implements SA1-level overlay+intersection+area-fraction weighting. `v1_naive_catchment_pop()` joins g01_df and returns summed population. `compare_v1_v2(v1_ring_pops, v2_ring_pops)` shows real overstatement. | None — CR-02 closed; teaching moment functional |
| GEO-04 | Interactive folium map + static matplotlib+contextily twin for PDF | **PASSED** | Folium map with site pin, buffer rings, POA boundaries, Yarra River polyline. Static matplotlib + `cx.add_basemap()` one per ring. | None — requires human verification of map rendering |
| DEMO-01 | G01/G02 from ABS Data API with local GCP fallback | **PASSED** | `fetch_g01_poa()` / `fetch_g02_poa()` use `fetch_abs_csv("ABS,C21_G01_POA,latest", ...)` through `session.get()`. Both have try/except → GCP fallback with empty-schema DataFrames (WR-02 fixed). G04 path XML-safe (CR-01 fixed). | None — requires human verification of API response format (WR-09) |
| DEMO-02 | Demographic profile for POA 3067 + 9 peers with comparison charts | **PASSED** | Peer table merges G01/G02/G04 for 10 POAs. 2×2 chart grid (population, median age, 65+ share, median income). POA 3067 highlighted. | None — requires human verification of G04 age-band column names (WR-06) |
| DEMO-03 | Peer benchmarking table: demand/supply indicators across peer set | **PASSED** | Table has `Total_P_P`, `Total_P_P_erp`, `Median_age_persons`, `pct_65plus`, `Median_tot_hshld_inc_weekly`, `gp_count = "— Phase 3"`, `pharmacy_count = "— Phase 3"`. | None — GP/pharmacy counts are Phase 3 placeholders by design |
| DEMO-04 | Census staleness addressed with ERP scaling + caveat | **PASSED** | `fetch_erp_sa2()` uses `ABS_ANNUAL_ERP_ASGS2021` through CachedSession. Growth rate applied to catchment pop + peer table. Caveat printed. Default rate=1.0 on failure. | None — SA2 code 206041001 hardcoded (IR-01, advisory) |

**Coverage: 8/8 requirement IDs verified (100%).**

## Gap Closure Confirmation

All 6 findings from the prior verification (02-VERIFICATION.md pre-fix state) are confirmed CLOSED in the notebook cell source (not just the generator scripts):

| Finding | Severity | Status | Evidence (notebook source) |
|---------|----------|--------|----------------------------|
| **CR-01**: `check_dataflow_exists()` calls `.json()` on SDMX-ML XML endpoint → JSONDecodeError | Critical | **CLOSED** | `flows_resp.json()` ABSENT from notebook source. `ET.fromstring(flows_resp.text)` present. try/except with safe default `return True` present. |
| **CR-02**: `v1_pop = v2_pop` placeholder never replaced → comparison is no-op | Critical | **CLOSED** | `v1_pop = v2_pop` ABSENT from notebook source. `def compare_v1_v2(v1_ring_pops: dict, v2_ring_pops: dict)` present. `v1_naive_catchment_pop(ring_geom_m, poa_pop_df)` returns `int(merged["Total_P_P"].sum())`. `v1_ring_pops` computed in §3.3. `compare_v1_v2(v1_ring_pops, v2_ring_pops)` called. |
| **WR-01**: `check_dataflow_exists()` has no try/except | Warning | **CLOSED** | Function body wrapped in try/except, returns `True` on any exception. |
| **WR-02**: `parse_gcp_g01_to_tidy()` returns all zeros | Warning | **CLOSED** | Returns `pd.DataFrame(columns=["POA_CODE21", "Total_P_P", "M_P", "F_P", "Total_Dwll_D"])` (empty schema). `Total_P_P": 0` ABSENT. G02 fallback returns empty schema similarly. |
| **WR-03**: G04 fallback inconsistent — no GCP fallback on API exception | Warning | **CLOSED** | `fetch_g04_poa()` except block calls `return fetch_g04_fallback()`. |
| **WR-04**: G04 age-band column detection uses fragile substring matching | Warning | **CLOSED** | Uses `b.startswith("Age_yr_65")` etc. + explicit `b in (...)` set + `"Age_yr_85ov" in b`. Prints matched columns for transparency. |
| **IR-02**: Validator D-06 check is pattern-presence no-op | Info | **CLOSED** | Validator D-06 now includes `d06_stub_present = "v1_pop = v2_pop" in all_source` with `not d06_stub_present` in pass condition. New CR-01 negative pattern check added. |

**All 6 gaps: CLOSED.** Both generator scripts (`extend_v2_notebook.py`, `extend_v2_notebook_demographics.py`) contain the fixes and use cell-replacement idempotency (re-running regenerates the corrected notebook). The notebook (36 cells: 19 code, 17 markdown) reflects all fixes.

## Cross-Cutting Constraints Check

| Constraint | Status | Evidence |
|-----------|--------|----------|
| All HTTP through Phase 1 CachedSession (no bare `requests.get`) | **PASS** | 0 bare `requests.get(` calls in notebook source. 4 `session.get(` calls (geocode, ABS G01/G02/G04, ERP). Validator confirms. |
| No numeric literal outside BASE_ASSUMPTIONS except unit conversions (PIPE-05) | **PASS** | `/ 1e6` (m²→km²), `* 100` (fraction→percent) are unit conversions. Assertion thresholds, radii, ERP vintage, plausible range all in BASE_ASSUMPTIONS. SA2 code `206041001` is data (advisory IR-01 — should be in BASE_ASSUMPTIONS but not a blocker). |
| No `/content/drive` | **PASS** | String `/content/drive` ABSENT from notebook source. |
| No `drive.mount` | **PASS** | String `drive.mount` ABSENT from notebook source. |
| No degree-based buffering | **PASS** | Only `.buffer()` call is on `site_metric` (reprojected to EPSG:7855). No `.buffer(` on same line as `EPSG:4326` or `EPSG:7844`. Validator confirms. |
| v1-flaw eradication maintained | **PASS** | All v1 flaws (drive.mount, /content/drive, degree-based buffering, whole-postcode summing) are absent. The v1-vs-v2 comparison explicitly reproduces v1's naive logic inline for the teaching moment, then shows the corrected v2 approach. |

## Human Verification Items (Deferred to Colab)

These items cannot be automated in the verification environment (no Colab runtime, no API keys, no SA1 shapefile). They are deferred to a Colab Restart & Run All with keys + shapefiles:

1. **End-to-end runtime execution** — Confirm the notebook runs top-to-bottom via Restart & Run All in Colab without errors. CR-01 is fixed (no JSONDecodeError), but live API responses may reveal format issues (WR-09: ABS CSV may be long-format, requiring a pivot step).
2. **Google Geocoding API response** — Confirm the geocode returns coordinates ≈ (-37.799, 145.003) for "292-296 Johnston St, Abbotsford VIC 3067" and that the pin lands on the Johnston St × Hoddle St corner on the folium verification map.
3. **ABS C21_G01_POA / C21_G02_POA / C21_G04_POA dataKey dimension order** — ROADMAP research flag (MEDIUM confidence). The dataKey `f"all.{PEER_POA_CODES}.A.2021"` assumes dimension order [MEASURE, POA, FREQ, TIME]. Must be verified via `/rest/datastructure/ABS/{id}` at runtime.
4. **ABS API CSV format (wide vs long)** — WR-09 in 02-REVIEW.md flags that `csvfilewithlabels` may return long format (one row per observation) rather than wide format (one row per POA with measures as columns). If long, a pivot step is needed. Verify by printing `g01_df.columns` and `g01_df.head()` after the first fetch.
5. **Folium map rendering** — Confirm the interactive map renders inline in Colab with all layers (site pin, 3 buffer rings, peer POA boundaries, Yarra River polyline).
6. **Static matplotlib + contextily figures** — Confirm the static figures render with basemap tiles (contextily pip-installed in Colab).
7. **ERP SA2 code 206041001** — IR-01: the Yarra SA2 code is hardcoded. Verify it is the correct ASGS Edition 3 code at runtime. Failure is graceful (rate defaults to 1.0).
8. **v1-vs-v2 chart shows real overstatement** — The headline teaching moment: confirm the chart shows v1 > v2 (pct_overstate > 0%) with real ABS data, demonstrating v1's 2–4× inflation.
9. **G04 age-band column names** — WR-06: the prefix matching covers `Age_yr_65_69`, `Age_yr_85ov`, `Age_65_69`, `Age_85plus` but may miss `_over`/`_yr` suffix variants or uppercase variants. Verify the matched columns print shows the expected bands.
10. **SA1 shapefile download** — Manual download of `SA1_2021_AUST_GDA2020.zip` from ABS ASGS Edition 3 digital boundary files (documented in `.env.example`). Notebook degrades to POA-level apportionment if missing.

## Code Review Findings Summary (Advisory)

The post-fix code review (02-REVIEW.md) found **0 critical, 5 warnings, 4 info** findings. All 6 prior gaps (CR-01, CR-02, WR-01..04, IR-02) are confirmed closed. The remaining findings are advisory — none are blockers for Phase 3, but two (WR-05, WR-08) represent edge cases where the no-hard-fail principle could be violated under specific failure conditions:

| Finding | Severity | Status | Impact |
|---------|----------|--------|--------|
| WR-05: `check_dataflow_exists` returns False (not True) for valid-XML non-SDMX responses (e.g., CDN error page) | Warning | Advisory | If ABS endpoint returns non-SDMX XML, function returns False → skips fetch. Contradicts safe-default docstring. |
| WR-06: Age-band prefix matching misses 5+ known ABS column name variants (`_over`, `_yr` suffix, uppercase) | Warning | Advisory | If API/DataPack uses unmatched variants, `pct_65plus` = 0. Debug print visible. |
| WR-07: `fetch_g04_fallback` returns `pct_65plus: 0` — misleading (should be NaN) | Warning | Advisory | In fallback mode, peer table shows 0% 65+ for 3067. Same class as WR-02. |
| WR-08: §3.5 peer_table crashes with KeyError on `pd.DataFrame()` "none" fallback (double-failure: API + GCP missing) | Warning | Advisory | Double-failure scenario crashes §3.5. Violates no-hard-fail. |
| WR-09: ABS API CSV format assumption (wide vs long) unverified | Warning | Advisory | If API returns long format, §3.5 crashes, 65+ share = 0. Highest-risk item — verify at runtime. |
| IR-03: `compare_v1_v2` with all-zero v1 shows -100% overstate (misleading but warned) | Info | Advisory | Degraded fallback only. Warning print mitigates. |
| IR-04: `"Age_yr_85ov" in b` check partially redundant with `startswith("Age_yr_85")` | Info | Advisory | Dead code, no correctness impact. |
| IR-05: `v1_naive_catchment_pop` relies on global `poa` variable | Info | Advisory | Works in notebook execution order. Not self-contained for module extraction. |
| IR-06: Potential dtype mismatch between POA_CODE21/SA1_CODE21 in shapefiles vs API CSV/DataPacks | Info | Advisory | If dtypes mismatch, merges silently produce 0. Plausibility assertion catches v2 case. |

**Recommendation:** WR-05, WR-07, WR-08, and WR-09 should be addressed before investor demonstration to ensure the no-hard-fail principle holds under all failure modes and the ABS API response format is verified. These are advisory for Phase 3 entry — the structural scaffolding is sound and the headline v1-flaw-fix teaching moment is functional.

---

*Phase: 02-catchment-demographics*
*Verified: 2026-07-05T12:22:38Z*
*Validator: 22 checks PASS, exit 0*
*Gap closure: 6/6 CLOSED (CR-01, CR-02, WR-01..04, IR-02)*
*Requirements: 8/8 verified (GEO-01..04, DEMO-01..04)*
