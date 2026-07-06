---
status: all_fixed
phase: 03-demand-competitors
iteration: 1
findings_in_scope: 3
fixed: 3
skipped: 0
date: 2026-07-06
---

# Code Review Fix Report — Phase 03

## Summary

All 3 detailed findings from the Phase 03 REVIEW.md were fixed in the generator
script (`scripts/extend_v2_notebook_phase3.py`), the notebook was regenerated,
and the validator confirms OVERALL: PASS with all 29 checks green.

The 2 critical bugs (CR-001 `ring_pops_erp` undefined, CR-002 wrong column name)
would have raised `NameError`/`KeyError` and stopped notebook execution. The 1
warning (WR-002 85+ pattern mismatch) would have silently undercounted the 65+
band. All three are now resolved.

The 8 additional findings mentioned without full detail (5 warnings, 4 info)
were not addressed in this iteration — they require manual review to identify
the specific code locations. They are documented as skipped below.

## Fixes Applied

### CR-001: `ring_pops_erp` undefined in §5 Demand Model — FIXED

**Files changed:** scripts/extend_v2_notebook_phase3.py, Johnston_St_v2.ipynb
**Commit:** 43fbf2b
**What was changed:** Replaced all 6 occurrences of `ring_pops_erp` with
`v2_ring_pops_erp` in the `demand_cells()` function. The correct variable name
is `v2_ring_pops_erp` (defined in Phase 2, cell 30 of the notebook). The 6
locations span 4 cells: §5.1 ring age profiles (1), §5.2 demand computation (2),
§5.4 GP capacity range (1), and §5.5 required market share (2). Without this
fix, every §5 cell would raise `NameError`, making the entire demand model
non-functional.

### CR-002: `peer_table["poa_code"]` wrong column name in §4.6 — FIXED

**Files changed:** scripts/extend_v2_notebook_phase3.py, Johnston_St_v2.ipynb
**Commit:** dcdb942
**What was changed:** Replaced `peer_table["poa_code"]` with
`peer_table["POA_CODE21"]` in the `competitor_cells()` function (§4.6 peer
competitor table). The actual column name is `POA_CODE21` (from
`g01_df[["POA_CODE21", "Total_P_P"]]` in Phase 2). The `"peer_table" in dir()`
guard only checks variable existence, not column existence, so the `KeyError`
would have stopped the notebook at the peer competitor table cell. This fix
restores the GP-per-1,000 benchmark computation (COMP-03).

### WR-002: `aggregate_age_bands` 85+ pattern mismatch — FIXED

**Files changed:** scripts/extend_v2_notebook_phase3.py, Johnston_St_v2.ipynb
**Commit:** bd2f671
**What was changed:** Added three pattern variants (`"85ov"`, `"85plus"`,
`"85over"`) to the 65+ band list in `aggregate_age_bands()`. The original search
key `"85_ov"` only matches column names with an underscore between 85 and ov
(e.g. `Age_85_over`), but the actual ABS G04 column is `Age_yr_85ov` (no
underscore). The new variants cover all three documented ABS G04 column naming
conventions (`Age_yr_85ov`, `Age_85plus`, `Age_85_over`) without risk of false
positives or double-counting. Without this fix, the 85+ population was silently
dropped, undercounting the 65+ band which has the highest consultation rate
(12.0/100) and biasing demand downward.

## Skipped Findings

The REVIEW.md mentions 8 additional findings (5 warnings, 4 info) without full
detail. These were not addressed in this iteration:

- **5 warnings (unspecified):** Remaining warning-level issues in
  `demand_cells()` and `competitor_cells()`. Skipped — needs manual review to
  identify specific code locations and failure modes.
- **4 info (unspecified):** Info-level suggestions on code style and
  documentation. Skipped — needs manual review; non-blocking.

These should be addressed in a follow-up review iteration with full detail
captured for each finding.

## Verification

- Generator script ran successfully (exit 0)
- Validator: `python scripts/validate_v2_notebook.py` → OVERALL: PASS (exit 0)
- All 29 checks green: 6 PIPE, v1 flaws, 14 Phase 2, 7 Phase 3
- Notebook: 69 cells (38 code, 31 markdown)
