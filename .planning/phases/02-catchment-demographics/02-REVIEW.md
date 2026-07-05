---
phase: 02-catchment-demographics
depth: standard
status: issues
files_reviewed: 5
findings:
  critical: 2
  warning: 4
  info: 3
  total: 9
reviewed_at: 2026-07-05T12:15:00Z
---

# Code Review: Phase 02 — Catchment & Demographics

## Summary

Phase 02 adds §1.2 geocoding, §2 geospatial catchment (EPSG:7855 buffers, SA1 apportionment), and §3 demographics (ABS census fetch with fallback, ERP scaling, peer benchmarking) to the Johnston_St_v2 notebook via two idempotent generator scripts. The EPSG:7855 discipline is correctly applied — all `.buffer()` calls operate on reprojected geometries, and the 3 km area assertion (≈28.27 km²) provides a runtime guard against the v1 degree-buffering flaw. API caching is routed through the `CachedSession` consistently, `.env.example` contains no secrets, `.env` is gitignored, and both generator scripts are idempotent with marker-string guards. The validator passes all 21 checks.

However, two critical issues prevent ship-readiness. First, `check_dataflow_exists()` calls `.json()` on the ABS dataflow endpoint that the notebook's own §1.2 smoke test proves returns SDMX-ML XML — this function will crash with `JSONDecodeError` at runtime, and it is called unwrapped in §3.2 and §3.3, violating the no-hard-fail rule. Second, the v1-vs-v2 comparison — described in both summaries as "the headline teaching moment" — is a no-op: `compare_v1_v2()` sets `v1_pop = v2_pop` (a placeholder never replaced), so the chart always shows 0% overstatement, completely defeating D-06's purpose. The validator passes because it only checks for pattern presence, not logical correctness.

## Files Reviewed
- Johnston_St_v2.ipynb
- scripts/extend_v2_notebook.py
- scripts/extend_v2_notebook_demographics.py
- scripts/validate_v2_notebook.py
- .env.example

## Findings

### CR-01: `check_dataflow_exists()` calls `.json()` on an XML endpoint — will crash at runtime (critical)
**File:** Johnston_St_v2.ipynb (§3.1 code cell, lines 764-770); scripts/extend_v2_notebook_demographics.py (lines 104-110)
**Lines:** 764-770
**Issue:** The §1.2 ABS smoke test (lines 299-313) explicitly documents and asserts that `https://data.api.abs.gov.au/rest/dataflow?detail=allstubs` returns SDMX-ML XML (`Content-Type: application/vnd.sdmx.structure+xml`). Yet `check_dataflow_exists()` calls `flows_resp.json()` on that same URL with no format parameter. `json.JSONDecodeError` will be raised because the response body is XML, not JSON. The function is called unwrapped in §3.2 (`G04_POA_EXISTS = check_dataflow_exists("C21_G04_POA")`, line 848) and §3.3 (`SA1_G01_EXISTS = check_dataflow_exists("C21_G01_SA1")`, line 903). Neither call site has a try/except guard. Even with a populated cache, the cached response is still XML, so `.json()` fails regardless of network state.
**Impact:** The notebook will hard-crash at §3.2 on every run (online or offline, cached or not). This violates the no-hard-fail rule (concern #3) and makes §3 demographics entirely non-functional. The validator passes because it only checks that the string `check_dataflow_exists` appears in source, not that the function works.
**Recommendation:** Either (a) add `?format=json` to the dataflow URL and verify the ABS API returns JSON-SDMX with a `dataflows` key at the top level (the current `flows.get("dataflows", [])` path may also be wrong for SDMX-JSON), or (b) parse the XML response with `xml.etree.ElementTree` to extract dataflow IDs, or (c) simpler: wrap the entire function in try/except and default to `True` on failure (the fetch itself has fallbacks). Option (c) is the most defensible given the no-hard-fail principle — if you can't verify the dataflow exists, attempt the fetch anyway and rely on the existing try/except in `fetch_g01_poa`/`fetch_g04_poa`.

### CR-02: v1-vs-v2 comparison is a no-op — `v1_pop = v2_pop` placeholder never replaced (critical)
**File:** Johnston_St_v2.ipynb (§2.4 code cell, lines 588-614); scripts/extend_v2_notebook.py (lines 312-350)
**Lines:** 600
**Issue:** The `compare_v1_v2()` function contains `v1_pop = v2_pop  # placeholder, overwritten in §3`. But §3.3 (line 957) calls `compare_v1_v2(v2_ring_pops)` without modifying the function or passing v1 population data. The `v1_naive_catchment_pop()` function (lines 581-586) returns a GeoDataFrame of touching POAs (`return touching`) but never joins or sums their populations — it doesn't even have access to POA total persons. Result: the comparison table and grouped bar chart always show `v1_naive == v2_apportioned` with `diff=0` and `pct_overstate=0%`. The "headline teaching moment" (D-06) that both plan summaries describe as complete is entirely non-functional.
**Impact:** The core pedagogical deliverable of Phase 02 — showing v1's whole-postcode summing inflated catchment population 2–4× — is broken. An investor or grader running the notebook sees a chart proving v1 == v2, which is the opposite of the intended lesson. The validator's D-06 check passes because it only greps for `compare_v1_v2(` and `v2_ring_pops` in source (see IR-02).
**Recommendation:** In §3.3 after the SA1 census fetch, also fetch POA total persons (G01 POA data is already in `g01_df`), then compute v1 naive population by summing `Total_P_P` for all POAs touching each ring. Pass both v1 and v2 totals to a revised `compare_v1_v2(v1_ring_pops, v2_ring_pops)`. Alternatively, move the entire comparison into §3.3 where both v1 (POA-level) and v2 (SA1-level) populations are available. The `v1_naive_catchment_pop` function should join `g01_df[["POA_CODE21", "Total_P_P"]]` and return the sum, not the raw GeoDataFrame.

### WR-01: `check_dataflow_exists()` has no try/except — violates no-hard-fail rule (warning)
**File:** Johnston_St_v2.ipynb (§3.1 code cell, lines 764-770)
**Lines:** 764-770
**Issue:** Even if the JSON parsing bug (CR-01) is fixed, `check_dataflow_exists()` has no error handling. If the ABS endpoint is unreachable and not cached, `session.get()` raises `ConnectionError`. The callers in §3.2 and §3.3 do not wrap the call in try/except. This violates the "never hard-fail on a network call" principle documented in CLAUDE.md and PROJECT.md.
**Impact:** Offline execution without a cached dataflow response will crash the notebook at §3.2.
**Recommendation:** Wrap the function body in try/except, returning `True` on failure (safe default — attempt the fetch and rely on downstream fallbacks). This is consistent with the pattern used by `fetch_g01_poa`, `fetch_g02_poa`, and `fetch_erp_sa2`.

### WR-02: `parse_gcp_g01_to_tidy()` is a stub returning all zeros (warning)
**File:** Johnston_St_v2.ipynb (§3.1 code cell, lines 772-786); scripts/extend_v2_notebook_demographics.py (lines 112-126)
**Lines:** 772-786
**Issue:** The GCP fallback parser creates a DataFrame with `Total_P_P: 0, M_P: 0, F_P: 0, Total_Dwll_D: 0` and has a `# TODO: populate from actual xlsx cells` comment. The D-17 schema parity requirement (same columns/dtypes) is structurally met but the values are all zero. If the ABS API fails and the GCP xlsx exists, the peer table will show 0 population for POA 3067 — worse than showing "N/A".
**Impact:** In fallback mode, the peer benchmarking table and comparison charts display misleading zero values for the site postcode. An investor viewing the fallback output sees 0 population for Abbotsford.
**Recommendation:** Either implement the xlsx parsing (the GCP G01 sheet has a known structure — `pd.read_excel` with the right sheet name and cell references), or if deferring to Phase 3, return an empty DataFrame with the correct schema and print a warning that fallback values are not yet populated. Zero is not a valid population.

### WR-03: G04 fallback is inconsistent — no GCP fallback on API failure (warning)
**File:** Johnston_St_v2.ipynb (§3.2 code cell, lines 851-859)
**Lines:** 851-859
**Issue:** `fetch_g04_poa()` catches exceptions and returns `(pd.DataFrame(), "none")` — no GCP fallback. This is inconsistent with `fetch_g01_poa()` and `fetch_g02_poa()` which fall back to `GCP_POA3067.xlsx`. The `fetch_g04_fallback()` function exists (lines 861-871) but is only called when `G04_POA_EXISTS` is False (dataflow not found), not when the API call raises an exception. If the dataflow exists but the network call fails, G04 returns empty with no fallback attempt.
**Impact:** In a network-failure scenario where G01/G02 degrade to GCP fallback but G04 returns empty, the peer table will have `pct_65plus = NaN` for all POAs. The 2×2 comparison chart for "65+ share" will be blank.
**Recommendation:** In the `except` block of `fetch_g04_poa()`, call `fetch_g04_fallback()` instead of returning empty. Or restructure: have `fetch_g04_poa` call `fetch_g04_fallback` on any failure (dataflow missing OR API error).

### WR-04: G04 age-band column detection is fragile (warning)
**File:** Johnston_St_v2.ipynb (§3.2 code cell, line 877)
**Lines:** 877
**Issue:** `age_bands_65plus = [b for b in g04_df.columns if "65" in b or "70" in b or "75" in b or "80" in b or "85" in b]` uses substring matching that could match non-age columns. ABS CSV-with-labels format produces columns with both codes and labels — column names may contain those numbers in label text (e.g., a column like `"Age_85_plus"` would match, but so could `"Total_85"` or a metadata column). Additionally, the G04 ABS table uses specific column codes (`Age_65_69`, `Age_70_74`, etc.) that this pattern may or may not match depending on the CSV-with-labels naming convention.
**Impact:** If the substring match picks up wrong columns, `pct_65plus` will be computed incorrectly, feeding bad data into the peer benchmarking table and Phase 3 demand model.
**Recommendation:** Use explicit column name patterns based on the ABS G04 data dictionary (e.g., `[b for b in g04_df.columns if b.startswith("Age_6") or b.startswith("Age_7") or b.startswith("Age_8")]`), or inspect the datastructure endpoint at runtime to get exact column names. Add a print of matched columns for teaching transparency.

### IR-01: ERP SA2 code `206041001` hardcoded without runtime verification (info)
**File:** Johnston_St_v2.ipynb (§3.4 code cell, line 1001)
**Lines:** 1000-1001
**Issue:** The Yarra SA2 code `206041001` is hardcoded with a comment `# ASGS Edition 3 Yarra SA2 code: 206041001 (verify at runtime)`, but no runtime verification is implemented. If the code is wrong, the ERP fetch returns no data, `erp_growth_rate` defaults to 1.0, and scaling is silently skipped.
**Impact:** Low — failure is graceful (no scaling applied, caveat printed). But the "verify at runtime" comment is misleading since no verification occurs.
**Recommendation:** Either implement the verification (query the datastructure endpoint for valid SA2 codes) or remove the "verify at runtime" comment and flag the code as `# UNCONFIRMED` consistent with the BASE_ASSUMPTIONS citation pattern.

### IR-02: Validator D-06 check is a pattern-presence no-op (info)
**File:** scripts/validate_v2_notebook.py (lines 347-351)
**Lines:** 347-351
**Issue:** The D-06 completion check verifies `"compare_v1_v2(" in all_source and "v2_ring_pops" in all_source`. Both strings are present in the stub form (§2.4 defines the function with the placeholder, §3.3 calls it). The check passes despite the comparison being logically broken (CR-02). This is the same class of issue as concern #7 — the validator claims to verify D-06 completion but only verifies pattern presence.
**Impact:** The validator gives false confidence that D-06 is satisfied. A broken headline deliverable passes validation.
**Recommendation:** Add a check that `v1_naive` is not assigned from `v2_pop` (e.g., assert `"v1_pop = v2_pop"` does NOT appear in source, or assert that `v1_naive_catchment_pop` returns a numeric sum, not a GeoDataFrame). Note: pattern-based validators can't fully verify logic, but they can catch known stub patterns.

### IR-03: `v1_naive_catchment_pop()` returns GeoDataFrame, not population (info)
**File:** Johnston_St_v2.ipynb (§2.4 code cell, lines 581-586)
**Lines:** 581-586
**Issue:** The function is named `..._pop` suggesting it returns a population number, but it returns `touching` (a GeoDataFrame of POA polygons). The docstring says "sum FULL POA population" but the implementation returns the raw geometry. This is part of the CR-02 stub, but even as a stub the naming is misleading.
**Impact:** Confusing for a teaching notebook — a student reading the function name expects a number.
**Recommendation:** Rename to `v1_naive_touching_poas()` while it's a stub, or implement it to return the summed population as the name suggests.

## Verdict

**Fix before Phase 3.** Two critical issues block ship-readiness. CR-01 (`check_dataflow_exists` calling `.json()` on an XML endpoint) will crash the notebook on every run of §3 — this must be fixed before any execution. CR-02 (the v1-vs-v2 comparison being a no-op placeholder) undermines the headline pedagogical deliverable of the entire phase — the "teaching moment" chart currently proves v1 == v2, which is worse than having no chart at all. Both issues are fixable within §3 without restructuring: CR-01 needs a try/except wrapper with safe default (or XML parsing), and CR-02 needs the POA total persons (already fetched in `g01_df`) joined into the v1 naive sum. The warning findings (GCP stub returning zeros, G04 fallback inconsistency, fragile column matching) should be addressed but are not blockers — they degrade gracefully. The EPSG:7855 discipline, caching routing, secrets hygiene, idempotency, and notebook JSON integrity are all correct and verified.
