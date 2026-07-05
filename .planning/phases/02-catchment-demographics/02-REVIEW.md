---
phase: 02-catchment-demographics
depth: standard
status: issues
files_reviewed: 4
findings:
  critical: 0
  warning: 5
  info: 4
  total: 9
reviewed_at: 2026-07-05T12:17:00Z
---

# Code Review: Phase 02 Plan 03 — Gap-Closure Post-Fix Review

## Summary

This review verifies that the 6 gaps identified in the prior 02-REVIEW.md (CR-01 XML endpoint crash, CR-02 v1-vs-v2 no-op, WR-01..04, IR-02) are properly closed by Plan 03's changes, and checks for newly introduced bugs. All 6 original gaps are confirmed closed: `check_dataflow_exists()` now parses SDMX-ML XML via ElementTree with a try/except safe default (CR-01/WR-01), `compare_v1_v2()` accepts both v1 and v2 ring population dicts with real v1 naive sums (CR-02), GCP fallbacks return empty-schema DataFrames instead of zeros (WR-02), `fetch_g04_poa()` except block calls `fetch_g04_fallback()` (WR-03), age-band matching uses explicit prefixes (WR-04), and the validator includes a negative pattern check for `v1_pop = v2_pop` (IR-02). The validator passes all 21 checks, the notebook preserves 36 cells (19 code, 17 markdown), and both generator scripts are idempotent (re-running produces identical output).

No new critical issues were introduced. Five warnings remain — none are blockers for Phase 3, but two (WR-05, WR-08) represent edge cases where the no-hard-fail principle could be violated at runtime under specific failure conditions. The age-band matching (WR-06) has verified gaps against known ABS column name variants but degrades gracefully with a debug print. The ABS API CSV format assumption (WR-09) is pre-existing and affects the entire §3 section, not just this plan's changes.

## Files Reviewed
- scripts/extend_v2_notebook.py (579 lines)
- scripts/extend_v2_notebook_demographics.py (554 lines)
- Johnston_St_v2.ipynb (36 cells: 19 code, 17 markdown)
- scripts/validate_v2_notebook.py (456 lines)

## Gap Closure Verification

| Prior Finding | Status | Evidence |
|---|---|---|
| CR-01: `.json()` on XML endpoint | **CLOSED** | `check_dataflow_exists` uses `ET.fromstring(flows_resp.text)` with SDMX-ML namespace search + fallback. No `flows_resp.json()` in notebook source (verified). Validator CR-01 check passes. |
| CR-02: v1-vs-v2 no-op | **CLOSED** | `compare_v1_v2(v1_ring_pops, v2_ring_pops)` takes two params. `v1_naive_catchment_pop()` joins `g01_df[["POA_CODE21", "Total_P_P"]]` and returns `int(merged["Total_P_P"].sum())`. §3.3 computes `v1_ring_pops` and calls `compare_v1_v2(v1_ring_pops, v2_ring_pops)`. `v1_pop = v2_pop` absent from source (verified). |
| WR-01: no try/except | **CLOSED** | `check_dataflow_exists` body wrapped in try/except, returns `True` on any exception. |
| WR-02: GCP zeros | **CLOSED** | `parse_gcp_g01_to_tidy` returns `pd.DataFrame(columns=["POA_CODE21", "Total_P_P", "M_P", "F_P", "Total_Dwll_D"])` (empty, correct schema). G02 fallback returns empty schema similarly. |
| WR-03: G04 fallback inconsistent | **CLOSED** | `fetch_g04_poa()` except block calls `return fetch_g04_fallback()` instead of returning empty. |
| WR-04: fragile age-band matching | **CLOSED** | Uses `b.startswith("Age_yr_65")` etc. + explicit `b in (...)` set. Prints matched columns for transparency. (See WR-06 for remaining coverage gaps.) |
| IR-02: validator D-06 no-op | **CLOSED** | D-06 check now includes `d06_stub_present = "v1_pop = v2_pop" in all_source` with `not d06_stub_present` in the pass condition. New CR-01 check added. |

## Findings

### WR-05: `check_dataflow_exists` returns False (not safe default True) for valid-XML non-SDMX responses (warning)

**File:** scripts/extend_v2_notebook_demographics.py (lines 106-125); Johnston_St_v2.ipynb (cell 26)
**Lines:** 118-122

**Issue:** The function's docstring states "Safe default: returns True on any failure." However, the safe default (`return True`) only applies in the `except` block. If the ABS endpoint returns a valid XML response that is not SDMX-ML (e.g., an XHTML error page like `<html><body>503 Service Unavailable</body></html>`), `ET.fromstring()` succeeds, both `findall` and `iter` searches return empty `flow_ids`, and the function returns `flow_id in []` = `False` — not the documented safe default `True`.

Verified with simulation:
```
Input: '<html><body>503 Service Unavailable</body></html>'
Namespace search flow_ids: []
Fallback search flow_ids: []
Returns: False (safe default would be: True)
```

**Impact:** If the ABS dataflow endpoint returns a non-SDMX XML response (e.g., a CDN error page, a maintenance page), `check_dataflow_exists` returns `False`, causing the downstream code to skip the fetch and use the fallback path. This contradicts the no-hard-fail principle and the function's own docstring. The fallback path is used instead of attempting the fetch (which has its own try/except).

**Recommendation:** Add a guard after the `flow_ids` searches: if `flow_ids` is empty after both searches, return `True` (can't determine dataflow existence — attempt fetch and rely on downstream fallbacks). Alternatively, check `flows_resp.ok` (status code) before parsing, or check the `Content-Type` header for SDMX-ML before attempting XML parsing.

### WR-06: Age-band prefix matching misses 5+ known ABS G04 column name variants (warning)

**File:** scripts/extend_v2_notebook_demographics.py (lines 221-225); Johnston_St_v2.ipynb (cell 27)
**Lines:** 221-225

**Issue:** The age-band prefix matching was improved from fragile substring matching (`"65" in b`) to explicit prefix matching, but verification against known ABS column naming conventions reveals 5+ unmatched variants:

| Column name | Source | Matched? |
|---|---|---|
| `Age_yr_65_69` | API CSV-with-labels | Yes |
| `Age_yr_85ov` | API CSV-with-labels | Yes |
| `Age_65_69` | DataPack (exact) | Yes |
| `Age_85plus` | DataPack (exact) | Yes |
| `Age_85_over` | DataPack (`_over` variant) | **No** |
| `Age_65_69_yr` | DataPack (`_yr` suffix) | **No** |
| `Age_70_74_yr` | DataPack (`_yr` suffix) | **No** |
| `AGE_YR_65_69` | Uppercase API variant | **No** |
| `AGE_65_69` | Uppercase DataPack | **No** |
| `AGE_85_OVER` | Uppercase DataPack | **No** |

The matching is case-sensitive (`startswith("Age_yr_65")` does not match `AGE_YR_65_69`) and the exact-match set `("Age_65_69", ..., "Age_85plus")` does not include `_over` or `_yr` suffix variants.

**Impact:** If the ABS API or DataPack uses any of the unmatched column name conventions, `age_bands_65plus` will be empty, `pct_65plus` will be set to `0` for all POAs, and the peer benchmarking table will show 0% 65+ share. The code prints a debug warning (`No 65+ age bands matched — G04 columns: [...]`), so the issue is visible but the degraded output is misleading.

**Recommendation:** Make the matching case-insensitive (`b.lower().startswith("age_yr_65")` or `b.lower().startswith("age_65")` etc.) and broaden the exact-match set to include `_over` and `_yr` suffix variants. Alternatively, use a regex pattern like `re.match(r"age[__yr]*_?(65|70|75|80|85)", b, re.IGNORECASE)` to cover all variants.

### WR-07: `fetch_g04_fallback` returns `pct_65plus: 0` — misleading (should be NaN) (warning)

**File:** scripts/extend_v2_notebook_demographics.py (lines 204-214); Johnston_St_v2.ipynb (cell 27)
**Lines:** 210-213

**Issue:** The G04 fallback function returns a DataFrame with `"pct_65plus": 0` for POA 3067. The comment says "populated from local GCP if available" but the value is never populated. Zero percent 65+ is not a valid demographic value for any postcode — it implies no elderly residents, which is false. This is the same class of issue as WR-02 (zero is not a valid population), applied to a percentage column.

**Impact:** In the fallback scenario (G04 API unavailable), the peer benchmarking table shows 0% 65+ share for POA 3067 and NaN for peers (from the outer merge). The 2×2 comparison chart shows a 0% bar for 3067, which is misleading. An investor viewing the fallback output sees an impossible demographic profile.

**Recommendation:** Return `float("nan")` or `None` instead of `0` for `pct_65plus` in the fallback DataFrame. This ensures the peer table and chart show "N/A" rather than a misleading 0%.

### WR-08: §3.5 peer_table crashes with KeyError on `pd.DataFrame()` "none" fallback (warning)

**File:** scripts/extend_v2_notebook_demographics.py (lines 409-418); Johnston_St_v2.ipynb (cell 32)
**Lines:** 412-418

**Issue:** The §3.5 peer benchmarking table cell accesses `g01_df[["POA_CODE21", "Total_P_P"]]` directly without a try/except guard or column-existence check. When `fetch_g01_poa()` returns `pd.DataFrame(), "none"` (API failure + GCP file missing), the DataFrame has no columns, and this line raises `KeyError: "['POA_CODE21', 'Total_P_P'] not in index"`. The same applies to `g02_df[["POA_CODE21", ...]]` and `g04_df[["POA_CODE21", "pct_65plus"]]`.

The WR-02 fix improved the "fallback" case (GCP file exists but parser is a stub) to return empty-schema DataFrames with correct columns, which are safe for the merge. But the "none" case (GCP file also missing) still returns `pd.DataFrame()` with no columns, which crashes.

**Impact:** In a double-failure scenario (ABS API down + local GCP file missing), the notebook hard-crashes at §3.5 with a KeyError. This violates the no-hard-fail principle. The §3.3 cell handles this gracefully (checks `"POA_CODE21" in g01_df.columns` before use), but §3.5 does not.

**Recommendation:** Either (a) return empty-schema DataFrames in the "none" case as well (consistent with the "fallback" case), or (b) wrap the §3.5 peer_table construction in a try/except that prints a warning and skips the table on failure. Option (a) is simpler and consistent with the WR-02 fix pattern.

### WR-09: ABS API CSV format assumption (wide vs long) unverified — may cause silent failures (warning)

**File:** scripts/extend_v2_notebook_demographics.py (lines 99-104, 137-183, 409-418); Johnston_St_v2.ipynb (cells 26, 32)
**Lines:** 99-104, 412-418

**Issue:** The code assumes the ABS Data API `format=csvfilewithlabels` response is in "wide" format — one row per POA with measures as columns (`Total_P_P`, `Median_age_persons`, `pct_65plus`, etc.). However, the ABS Data API CSV format typically returns "flat" (long) data: one row per observation (POA × MEASURE × TIME_PERIOD), with a `MEASURE` dimension column and an `OBS_VALUE` measure column. In long format, `Total_P_P` would be a value in the `MEASURE` column, not a column name.

If the API returns long format:
- `g01_df[["POA_CODE21", "Total_P_P"]]` → KeyError (columns don't exist)
- `g04_df.columns` age-band search → empty (age bands are values, not columns)
- `sa1_pop_df[["SA1_CODE21", "Total_P_P"]]` → KeyError (caught by try/except, falls back to DataPack)

The §3.3 SA1 cell handles this gracefully (try/except with DataPack fallback). But §3.5 (peer_table) and the G04 age-band derivation do not.

**Impact:** If the ABS API returns long-format CSV, the peer benchmarking table crashes (WR-08), the 65+ share is set to 0 (WR-06), and the v1 naive population is set to 0 (column-existence check fails). The notebook degrades but does not produce correct results. This is pre-existing (not introduced by Plan 03) but affects the reviewed code.

**Recommendation:** Verify the ABS API CSV format at runtime by printing `g01_df.columns` and `g01_df.head()` after the first fetch. If the data is in long format, add a pivot step: `g01_wide = g01_df.pivot_table(index="POA", columns="MEASURE", values="OBS_VALUE").reset_index()`. Consider adding this as a `tidy_abs_csv()` helper function that all fetch functions use.

## Info Findings

### IR-03: `compare_v1_v2` with all-zero v1 shows -100% overstate (misleading but warned) (info)

**File:** scripts/extend_v2_notebook_demographics.py (lines 302-308); Johnston_St_v2.ipynb (cell 28)
**Lines:** 302-308

**Issue:** When `g01_df` is empty or missing the `POA_CODE21` column, §3.3 sets `v1_ring_pops[r] = 0` for all rings. The `if v1_ring_pops:` check passes (non-empty dict), so `compare_v1_v2` is called with all-zero v1 values. The comparison table shows `pct_overstate = (0/v2 - 1)*100 = -100%` for each ring, and the bar chart shows v1 bars at 0. This is misleading — it suggests v1 understated by 100% rather than "v1 data unavailable." A print warning (`g01_df empty — v1 naive pop unavailable`) is emitted but the chart still renders.

**Impact:** Low — the warning print mitigates the confusion, and this only occurs in the degraded fallback scenario. But the chart is visually misleading.

**Recommendation:** Skip the `compare_v1_v2` call if all v1 values are 0, or pass a flag to render a "data unavailable" message instead of the chart.

### IR-04: `"Age_yr_85ov" in b` check partially redundant with `startswith("Age_yr_85")` (info)

**File:** scripts/extend_v2_notebook_demographics.py (line 224); Johnston_St_v2.ipynb (cell 27)
**Lines:** 224

**Issue:** The condition `or "Age_yr_85ov" in b` is evaluated after `b.startswith("Age_yr_85")`. Any column starting with `"Age_yr_85"` (including `"Age_yr_85ov"`) is already matched by the `startswith` check. The `in` check only adds value for non-prefix matches like `"Total_Age_yr_85ov"` (unlikely in ABS column naming). This is not a bug but is dead code in practice.

**Impact:** None — the redundancy doesn't affect correctness. Minor code clarity issue.

**Recommendation:** Remove the `"Age_yr_85ov" in b` clause, or replace with a comment explaining the edge case it covers.

### IR-05: `v1_naive_catchment_pop` relies on global `poa` variable from §2.1 (info)

**File:** scripts/extend_v2_notebook.py (lines 318-325); Johnston_St_v2.ipynb (cell 20)
**Lines:** 322

**Issue:** The `v1_naive_catchment_pop(ring_geom_m, poa_pop_df)` function uses the global `poa` GeoDataFrame (defined in §2.1) without receiving it as a parameter. This works correctly in notebook execution order (§2.1 runs before §2.4 where the function is defined, and §3.3 where it's called), but the function is not self-contained — it would fail if extracted to a separate module.

**Impact:** None for notebook execution. Minor code quality issue for a teaching notebook — a student reading the function signature sees two parameters but the function depends on a third implicit global.

**Recommendation:** Acceptable as-is for a notebook. If refactoring to a module later, add `poa_gdf` as a parameter.

### IR-06: Potential dtype mismatch between POA_CODE21/SA1_CODE21 in shapefiles vs API CSV/DataPacks (info)

**File:** scripts/extend_v2_notebook.py (line 324); scripts/extend_v2_notebook_demographics.py (lines 269, 282); Johnston_St_v2.ipynb (cells 20, 28)
**Lines:** extend_v2_notebook.py:324; extend_v2_notebook_demographics.py:269,282

**Issue:** The `v1_naive_catchment_pop` function merges `touching` (from `poa` shapefile, `POA_CODE21` likely string) with `poa_pop_df` (from API CSV, `POA_CODE21` dtype unknown). Similarly, the SA1 DataPack fallback uses `sa1_pop_df["SA1_CODE21"].isin(sa1_codes)` where `sa1_codes` comes from the shapefile (string) but the DataPack might infer `SA1_CODE21` as int64. If dtypes differ, the merge/isin silently produces no matches, resulting in 0 population.

The code has defensive column-existence checks (`"POA_CODE21" in g01_df.columns`) that prevent crashes, but doesn't check dtype compatibility.

**Impact:** If dtypes mismatch, v1 naive population and SA1 apportionment silently produce 0. The plausibility assertion (`80_000 < v2_ring_pops[3000] < 110_000`) would catch the v2 case (assertion fails). The v1 case would show 0 in the comparison, which is caught by IR-03's warning.

**Recommendation:** Add explicit dtype conversion before merges: `poa_pop_df["POA_CODE21"] = poa_pop_df["POA_CODE21"].astype(str)` and `sa1_pop_df["SA1_CODE21"] = sa1_pop_df["SA1_CODE21"].astype(str)`.

## Verdict

**Ship-ready for Phase 3 with caveats.** All 6 prior gaps (CR-01, CR-02, WR-01..04, IR-02) are confirmed closed. No new critical issues were introduced. The notebook is structurally valid (36 cells, nbformat 4, all code cells have `execution_count: null` and `outputs: []`), both generator scripts are idempotent (verified by re-running — produces identical 36-cell output), and the validator passes all 21 checks.

The 5 remaining warnings are all edge-case or runtime-format issues that only manifest under specific failure conditions (WR-05: non-SDMX XML error page; WR-08: double-failure API + GCP missing) or depend on unverified API response formats (WR-06, WR-09). None are blockers for Phase 3, but WR-05 and WR-08 should be addressed before investor demonstration to ensure the no-hard-fail principle holds under all failure modes. WR-09 (API CSV format) is the highest-risk item — if the ABS API returns long-format data, the entire §3 section produces incorrect results. This should be verified by executing the notebook against the live API at the earliest opportunity.

The cell-replacement idempotency logic is correct for all tested scenarios: fresh install, re-run with existing sections, and re-run after manual edits. The `extend_base_assumptions` function correctly inserts Phase 2 keys before the closing `}` and is idempotent (checks for `sa1_shapefile` presence). The `compare_v1_v2` pct_overstate math is correct (`(v1/v2 - 1)*100`) and handles `v2_pop=0` by returning `None`. The XML namespace handling in `check_dataflow_exists` uses a two-pass approach (namespaced search + namespace-agnostic fallback) that is robust for SDMX 2.1 and potential namespace variants.
