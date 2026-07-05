---
status: issues_found
phase: 03-demand-competitors
depth: standard
files_reviewed: 4
date: 2026-07-06
findings:
  critical: 2
  warning: 6
  info: 4
  total: 12
---

# Code Review — Phase 03: Demand & Competitors

## Summary

Standard-depth review of 4 source files changed in Phase 03. The phase extends the
feasibility-study notebook with the data acquisition layer (§1.4 Places API client,
§1.5 MBS/AIHW loaders), the competitor landscape (§4), and the demand model (§5).

Two **critical** bugs will break notebook execution end-to-end:
- `ring_pops_erp` is referenced in §5 but never defined (correct name is `v2_ring_pops_erp`)
- `peer_table["poa_code"]` uses the wrong column name (actual column is `POA_CODE21`)

Both will raise runtime errors and stop the notebook. They must be fixed before
verification can pass.

## Findings

### CR-001: `ring_pops_erp` undefined in §5 Demand Model (Critical)

**File:** scripts/extend_v2_notebook_phase3.py (§5 demand_cells) → Johnston_St_v2.ipynb
**Description:** The §5 Demand Model cells reference `ring_pops_erp.get(r, 0)` in 6
locations across 4 cells, but this variable is never defined. The correct variable
from Phase 2 is `v2_ring_pops_erp` (defined in cell 30).
**Impact:** Every §5 cell will raise `NameError` on execution, making the entire
demand model non-functional. Phase 03's headline output (required market share)
cannot be produced.
**Recommendation:** Replace all `ring_pops_erp` references with `v2_ring_pops_erp`
in the demand_cells() function of scripts/extend_v2_notebook_phase3.py, then
regenerate the notebook.

### CR-002: `peer_table["poa_code"]` wrong column name in §4.6 (Critical)

**File:** scripts/extend_v2_notebook_phase3.py (§4.6 peer competitor table) → Johnston_St_v2.ipynb
**Description:** The §4.6 peer competitor table references `peer_table["poa_code"]`
but the actual column is `POA_CODE21` (from `g01_df[["POA_CODE21", "Total_P_P"]]`).
The `"peer_table" in dir()` guard only checks variable existence, not column existence.
**Impact:** Raises `KeyError` and stops the notebook at cell 52. The peer competitor
table (COMP-03) cannot be produced.
**Recommendation:** Replace `peer_table["poa_code"]` with `peer_table["POA_CODE21"]`
in the competitor_cells() function, then regenerate the notebook.

### WR-002: `aggregate_age_bands` 85+ pattern mismatch (Warning)

**File:** scripts/extend_v2_notebook_phase3.py (aggregate_age_bands function)
**Description:** The search key `"85_ov"` won't match any documented ABS G04 column
variant (`Age_yr_85ov`, `Age_85plus`, `Age_85_over`).
**Impact:** The 85+ population is silently dropped, undercounting the 65+ band which
has the highest consultation rate (12.0/100), biasing demand downward.
**Recommendation:** Add additional pattern variants for 85+ matching, or use the
same case-insensitive regex approach used elsewhere in the codebase (per WR-06 fix
from Phase 02).

### Additional findings (8 more — 5 warnings, 4 info)

Full detail not captured in this report. The reviewer identified 6 warnings and 4
info-level items in total across the 4 files. Run `/gsd-code-review-fix 03` to
address all findings, or review the source files manually for:
- Remaining warning-level issues in demand_cells() and competitor_cells()
- Info-level suggestions on code style and documentation

## Next Steps

```
/gsd-code-review-fix 03  — Auto-fix all issues (recommended — 2 criticals block execution)
```

The 2 critical issues MUST be resolved before phase verification can pass. The
verifier agent will detect the runtime errors when it checks must_haves against
the actual codebase.
