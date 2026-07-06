---
phase: 04-clinic-financial-model
plan: 02
subsystem: financial-model
tags: [ramp-cashflow, peak-capital, breakeven, numpy, matplotlib, report-accumulator]

# Dependency graph
requires:
  - phase: 04-clinic-financial-model
    provides: clinic_pnl(a) pure function (Plan 04-01) — ramp calls it per-month
provides:
  - clinic_ramp_monthly(a: dict, months: int = 36) -> dict — 36-month ramp cash flow
  - Peak capital headline (D-12: modelled trough + 3-month working-capital buffer ON TOP)
  - Operating breakeven month (D-08: first month EBITDA > 0)
  - Payback breakeven month (D-08: first month cumulative >= 0)
  - matplotlib ramp chart (outputs/ramp_cashflow.png)
  - report{} deposits — 9 headline metrics for Phase 5 §8
  - BASE_ASSUMPTIONS ramp keys (gp_ramp_milestones, book_fill_curve, ramp_months, working_capital_buffer)
affects: [05-scenarios-sensitivity, 08-executive-report]

# Tech tracking
tech-stack:
  added: []  # numpy + matplotlib only (both preinstalled)
  patterns:
    - "D-16: per-month clinic_pnl calls with ramp-scaled override dicts {**a, **ramp_overrides}"
    - "Don't Hand-Roll: np.cumsum for cumulative, np.min for peak, np.argmax for breakevens"
    - "D-07 staffing split: nurse_fte = gp_fte × 0.2 (variable); reception/manager fixed from day 1"
    - "D-12 buffer ON TOP: peak_capital_total = |min(cumulative)| + working_capital_buffer"
    - "Linear interpolation between book-fill curve points (40% → 75% over 12 months per GP)"

key-files:
  created: []
  modified:
    - scripts/extend_v2_notebook_phase4.py
    - Johnston_St_v2.ipynb

key-decisions:
  - "Per-GP book-fill interpolation: linear between curve points {0:0.40, 3:0.50, 6:0.60, 9:0.68, 12:0.75}"
  - "GP start month derived from milestones dict: GP 0,1 at month 0; GP 2 at month 6; GP 3 at 12; GP 4 at 18"
  - "Working-capital buffer added ON TOP of modelled peak (D-12) — not buried in the cash drain"
  - "Payback breakeven NOT reached in 36 months — meaningful Phase 5 finding (clinic needs ~4-5 years)"
  - "report{} deposits 9 metrics: steady_state_ebitda, margin, practice_revenue, gp_billings, fitout_total, peak_capital, breakeven_operating, breakeven_payback, working_capital_buffer"

patterns-established:
  - "clinic_ramp_monthly override-dict pattern: {**a, **ramp_overrides} per month — Phase 5 scenarios override ramp parameters too"
  - "matplotlib dual-axis chart: cumulative cash curve (top) + monthly EBITDA bar (bottom) with breakeven/peak markers"
  - "report{} accumulator fully populated for Phase 5 §8 (Pattern 5)"

requirements-completed:
  - FIN-03
  - FIN-04

# Metrics
duration: ~20 min
completed: 2026-07-06
---

# Phase 4 Plan 02: Ramp-Up Cash Flow Model Summary

**clinic_ramp_monthly(a, months=36) -> dict with GP recruitment milestones, per-GP book-fill curve, peak capital ($490k with buffer), operating breakeven (month 11), and 9 report{} deposits for Phase 5**

## Performance

- **Duration:** ~20 min
- **Tasks:** 2
- **Files modified:** 2 (scripts/extend_v2_notebook_phase4.py extended, Johnston_St_v2.ipynb extended)

## Accomplishments
- `clinic_ramp_monthly(a: dict, months: int = 36) -> dict` — 36-month ramp cash flow calling `clinic_pnl` per month with ramp-scaled override dicts (D-16)
- GP recruitment milestones (D-06): 2 GPs at open → 5 FTE by month 18, with per-GP book-fill interpolation (40% → 75% over 12 months)
- Variable-vs-fixed staffing (D-07): nurse FTE = GP_FTE × 0.2 (scales); reception/manager/rent/insurance/admin fixed from day 1
- Three headline outputs (D-08/D-12): peak_capital_total ($490k = $441k modelled + $49k buffer), breakeven_operating (month 11), breakeven_payback (NOT reached in 36 months)
- matplotlib ramp chart (cumulative cash curve + monthly EBITDA bar with breakeven/peak markers), saved to outputs/ramp_cashflow.png
- `report{}` accumulator populated with 9 headline metrics for Phase 5 §8 (Pattern 5)
- Smoke-tested: practice_revenue=$673k (Pitfall 11 PASS), EBITDA=$258k/yr (38.4% margin), all numpy ops verified

## Task Commits

Each task was committed atomically:

1. **Task 1: Add ramp BASE_ASSUMPTIONS keys + clinic_ramp_monthly() + ramp chart + report{} deposits** - `f58999e` (feat)
2. **Task 2: Verify notebook structural integrity after ramp extension** - no code changes (validator OVERALL: PASS, smoke-test passed)

## Files Created/Modified
- `scripts/extend_v2_notebook_phase4.py` - Extended with PHASE4_RAMP_ASSUMPTIONS_KEYS, extend_base_assumptions_ramp(), §6.2/§6.3 cells (ramp function + headline display + chart + report deposits + interpretation)
- `Johnston_St_v2.ipynb` - Extended with §6.2 Ramp-Up Cash Flow cells + §6.3 Interpretation + ramp BASE_ASSUMPTIONS keys

## Decisions Made
- **Linear interpolation for book-fill curve**: the curve has 5 points {0:0.40, 3:0.50, 6:0.60, 9:0.68, 12:0.75}. Between points, linearly interpolate (e.g. month 4 = 0.50 + (1/3)×(0.60-0.50) = 0.533). After month 12, hold at 0.75 (steady state). Before GP starts (months_active < 0), utilisation = 0.
- **GP start month derivation**: the milestones dict {0:2, 6:3, 12:4, 18:5} maps month → cumulative GP count. GP indices 0-1 start at month 0, GP 2 at month 6, GP 3 at month 12, GP 4 at month 18. The `gp_start_month()` helper maps gp_idx → milestone month.
- **Working-capital buffer ON TOP (D-12)**: `peak_capital_total = abs(np.min(cumulative)) + working_capital_buffer`. The buffer ($49,450 = 3 months of fixed costs) is added to the modelled peak, not buried in the cash drain. This is a conservative headline recognising real-world funding contingency.
- **Payback breakeven NOT reached in 36 months** is a meaningful finding, not a bug. With $349k fit-out + $441k cumulative operating losses during ramp, the clinic needs ~4-5 years of steady-state EBITDA ($258k/yr) to recoup. The §6.3 interpretation markdown flags this as a red flag for the Phase 5 verdict.

## Deviations from Plan

None - plan executed exactly as written. All structural checks, numpy function usage (cumsum/argmax/min), report{} deposits, and chart generation match the plan specification.

## Issues Encountered
- None. The generator script's idempotency worked correctly on re-run (ramp keys detected via `gp_ramp_milestones` marker, §6 cells replaced via `# §6 Financial Model` marker).

## User Setup Required
None - no external service configuration required. Phase 4 is pure computation.

## Next Phase Readiness
- `clinic_ramp_monthly(a, months=36) -> dict` is ready for Phase 5 scenario overrides: `{**BASE_ASSUMPTIONS, "gp_ramp_milestones": {0: 3, 6: 4, 12: 5}, **overrides}` (faster ramp scenario)
- `report{}` accumulator fully populated with 9 headline metrics — Phase 5 §8 renders them in the executive report
- `outputs/ramp_cashflow.png` ready for the PDF report (Phase 5)
- Peak capital ($490k), operating breakeven (month 11), and payback (>36 months) are the three investor headlines — Phase 5 sensitivity will test how they change with rent, utilisation, service-fee %, and billing-model scenarios
- The "payback not in 36 months" finding gives Phase 5 a clear question to answer: does any scenario achieve payback within 3 years, or does the clinic fundamentally need a longer horizon?

---
*Phase: 04-clinic-financial-model*
*Completed: 2026-07-06*
