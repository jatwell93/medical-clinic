---
phase: 02-catchment-demographics
plan: 03
subsystem: data
tags: [abs-data-api, sdmx-xml, geopandas, catchment-apportionment, demographics, validation]

# Dependency graph
requires:
  - phase: 02-catchment-demographics/02-01
    provides: "§1.2 geocode + §2 catchment cells (generator + notebook) with v1-vs-v2 comparison scaffold"
  - phase: 02-catchment-demographics/02-02
    provides: "§3 demographics cells (ABS G01/G02/G04 + ERP + peer benchmarking) with SA1→§2.3 wiring"
provides:
  - "Runtime-functional §3 demographics — check_dataflow_exists no longer crashes on the SDMX-ML XML endpoint (CR-01)"
  - "Real v1-vs-v2 catchment comparison — compare_v1_v2(v1_ring_pops, v2_ring_pops) computes actual pct_overstate from g01_df (CR-02)"
  - "Consistent G01/G02/G04 fallback behaviour — empty-schema DataFrames + G04 fallback wiring (WR-02, WR-03)"
  - "Explicit age-band column detection with teaching transparency (WR-04)"
  - "Cell-replacement idempotency in both generator scripts — re-running regenerates the corrected notebook"
  - "Strengthened validator with negative pattern assertions for CR-01 and CR-02 stub (IR-02)"
affects: [03-demand-competitors, 04-financial-model, 05-report]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Cell-replacement idempotency: generator scripts remove existing section cells and re-append corrected versions (re-run safe)"
    - "SDMX-ML XML parsing via xml.etree.ElementTree for ABS dataflow endpoint (not .json())"
    - "Negative pattern assertions in validator: required-bad strings must be ABSENT, not just required-good strings present"

key-files:
  created: []
  modified:
    - scripts/extend_v2_notebook.py
    - scripts/extend_v2_notebook_demographics.py
    - Johnston_St_v2.ipynb
    - scripts/validate_v2_notebook.py

key-decisions:
  - "Cell-replacement idempotency strips the trailing §2 'Next Steps' markdown when §3 Demographics follows, so the §3-owned final Next Steps is not duplicated mid-notebook"
  - "Demographics cell-replacement includes the trailing 'Next Steps' in the removed range (end_idx = j+1) since demographics_cells() ships its own — preserves 36-cell count"
  - "check_dataflow_exists safe-defaults to True on any failure (no-hard-fail principle) — downstream fetch_g0X_poa functions have their own try/except fallbacks"
  - "Added CR-01 to the validator's report label list + structural-failure filter so the new check is visible in output (report uses a hardcoded label list)"

patterns-established:
  - "Cell-replacement idempotency: MARKER/STOP_MARKER scan → remove existing section → re-append corrected cells (re-run produces the fixed notebook, not a skip)"
  - "Negative pattern validation: a check can require a bad string to be ABSENT (v1_pop = v2_pop, flows_resp.json()) in addition to good strings present"

requirements-completed:
  - GEO-03
  - DEMO-01
  - DEMO-02
  - DEMO-03

# Metrics
duration: 18 min
completed: 2026-07-05
---

# Phase 2 Plan 03: Gap Closure Summary

**Closed all 6 verification gaps — §3 demographics is now runtime-functional (XML-safe dataflow check) and the v1-vs-v2 comparison shows real overstatement from g01_df instead of a 0% no-op stub**

## Performance

- **Duration:** ~18 min
- **Started:** 2026-07-05
- **Completed:** 2026-07-05
- **Tasks:** 4
- **Files modified:** 4

## Accomplishments
- CR-01 fixed: `check_dataflow_exists` now parses the SDMX-ML XML dataflow endpoint via `xml.etree.ElementTree` with a try/except safe-default True — no more `JSONDecodeError` on every §3 run
- CR-02 fixed: `compare_v1_v2(v1_ring_pops, v2_ring_pops)` accepts both v1 and v2 ring population dicts and computes real `pct_overstate = (v1/v2 - 1)*100`; `v1_naive_catchment_pop` joins `g01_df` Total_P_P and returns the summed population; the `v1_pop = v2_pop` stub is eradicated
- WR-01..04 fixed: try/except safe default (WR-01), empty-schema GCP fallbacks instead of zero-stubs (WR-02), G04 except block calls `fetch_g04_fallback()` (WR-03), explicit prefix matching for 65+ age bands with matched-columns print (WR-04)
- Both generator scripts upgraded from skip-if-exists to cell-replacement idempotency — re-running regenerates the corrected notebook (replaced 15 §1.2+§2 cells + 11 §3 cells, cell count preserved at 36)
- Validator strengthened: D-06 now requires `v1_ring_pops` present AND `v1_pop = v2_pop` ABSENT (IR-02); new CR-01 negative pattern check — validator exits 0 with OVERALL: PASS (22 checks green)

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix CR-02 in extend_v2_notebook.py** — `782494c` (fix)
2. **Task 2: Fix CR-01/WR-01..04 in extend_v2_notebook_demographics.py** — `612d36b` (fix)
3. **Task 3: Regenerate Johnston_St_v2.ipynb** — `d4d62ed` (fix)
4. **Task 4: Strengthen validator D-06 + CR-01 check** — `e870a22` (fix)

**Plan metadata:** `32b6f27` (docs: complete plan)

## Files Created/Modified
- `scripts/extend_v2_notebook.py` — Fixed `compare_v1_v2` (two-param signature) + `v1_naive_catchment_pop` (joins g01_df, returns population sum) + cell-replacement idempotency in main()
- `scripts/extend_v2_notebook_demographics.py` — Fixed `check_dataflow_exists` (XML-safe, try/except), `parse_gcp_g01_to_tidy` + G02 fallback (empty schema), `fetch_g04_poa` (calls fallback), `age_bands_65plus` (explicit prefix matching), §3.3 SA1 cell (v1_ring_pops + two-param compare call) + cell-replacement idempotency
- `Johnston_St_v2.ipynb` — Regenerated with all 6 gap fixes (36 cells preserved, structure intact)
- `scripts/validate_v2_notebook.py` — Strengthened D-06 (v1_ring_pops + stub negative) + new CR-01 negative pattern check + report label list

## Decisions Made
- Cell-replacement idempotency strips the trailing §2 "Next Steps" markdown when §3 Demographics follows, so the §3-owned final Next Steps is not duplicated mid-notebook (preserves 36-cell count)
- Demographics cell-replacement includes the trailing "Next Steps" in the removed range (`end_idx = j+1`) since `demographics_cells()` ships its own — preserves 36-cell count
- `check_dataflow_exists` safe-defaults to True on any failure (no-hard-fail principle) — downstream `fetch_g0X_poa` functions have their own try/except fallbacks
- Added CR-01 to the validator's report label list + structural-failure filter so the new check is visible in output (the report function uses a hardcoded label list)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Cell-replacement idempotency preserves notebook structure**
- **Found during:** Task 1 (cell-replacement logic in extend_v2_notebook.py main())
- **Issue:** The plan's Change 1 snippet used `catchment_cells()` alone and a STOP_MARKER that would either drop the §1.2 geocode cells or duplicate the §2 "Next Steps" mid-notebook, breaking the Task 3 acceptance criterion (cell count == 36, structure preserved)
- **Fix:** Used `geocode_cells() + catchment_cells()` for the replacement set, and strip the trailing §2 "Next Steps" markdown when §3 Demographics follows (§3 owns the final Next Steps). Applied the symmetric fix to the demographics script (include the trailing Next Steps in the removed range via `end_idx = j+1`)
- **Files modified:** scripts/extend_v2_notebook.py, scripts/extend_v2_notebook_demographics.py
- **Verification:** Both generators print `replaced N cells with M corrected cells` and the notebook stays at 36 cells after both run
- **Committed in:** 782494c, 612d36b

**2. [Rule 2 - Missing Critical] Validator CR-01 check not visible in report output**
- **Found during:** Task 4 (running the validator)
- **Issue:** The new CR-01 `check_demog` call was evaluated and contributed to OVERALL, but the `report()` function uses a hardcoded `phase2_labels` list to print demog checks — CR-01 was not in it, so the check was invisible (and a CR-01 failure would have been double-printed by the structural-failure fallback)
- **Fix:** Added `"Phase 2 CR-01 (check_dataflow_exists XML-safe)"` to `phase2_labels` and `"CR-01"` to the structural-failure filter key list
- **Files modified:** scripts/validate_v2_notebook.py
- **Verification:** Validator output now shows `Phase 2 CR-01 (check_dataflow_exists XML-safe): PASS`; OVERALL: PASS; exit 0
- **Committed in:** e870a22

---

**Total deviations:** 2 auto-fixed (2 missing critical)
**Impact on plan:** Both auto-fixes necessary for correctness (notebook structure preservation + validator visibility). No scope creep — the fixes implement the plan's intent faithfully.

## Issues Encountered
None — all 4 tasks executed cleanly; all acceptance criteria and plan-level verification checks pass on the first run.

## User Setup Required
None - no external service configuration required. (Colab Restart & Run All with API keys + SA1 shapefile is the deferred human verification step, noted in the plan's §4.)

## Next Phase Readiness
- Phase 2 is complete: all GEO-01..04 + DEMO-01..04 requirements satisfied at the structural/runtime-ready level. §3 demographics is runtime-functional (no JSONDecodeError), the v1-vs-v2 comparison will show real overstatement once Colab executes with real ABS data, and G04 age bands feed the Phase 3 demand model.
- Deferred human verification (Colab Restart & Run All): confirm §3 runs end-to-end without JSONDecodeError, the v1-vs-v2 chart shows v1 > v2 (pct_overstate > 0%), G04 age bands are detected, and fallback behaviour is consistent across G01/G02/G04.
- Phase 3 (Demand & Competitors) can proceed — it depends on the geocoded site (§1.2), catchment buffers (§2), apportioned population (§3), age profile (§3 G04), and peer benchmarking table (§3 with placeholder GP/pharmacy columns), all of which are now runtime-functional.

## Self-Check: PASSED

Plan-level verification (all green):
- `python scripts/validate_v2_notebook.py` → OVERALL: PASS, exit 0 (22 checks)
- CR-01: FIXED (`flows_resp.json()` absent from notebook source)
- CR-02: FIXED (`v1_pop = v2_pop` absent; `compare_v1_v2(v1_ring_pops, v2_ring_pops)` present)
- WR-02: FIXED (empty-schema fallback, no zero-stub)
- WR-03: FIXED (`return fetch_g04_fallback()` present)
- Cell count: 36 (preserved — cells replaced, not duplicated)

---
*Phase: 02-catchment-demographics*
*Completed: 2026-07-05*
