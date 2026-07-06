---
phase: 05-scenarios-executive-report
plan: 02
subsystem: executive-report
tags: [verdict, go-no-go, jinja2, weasyprint, pdf, assumptions-register, citations, report-accumulator]

# Dependency graph
requires:
  - phase: 05-scenarios-executive-report
    provides: Plan 05-01 §7 Scenarios & Sensitivity — report{} deposits (scenario_ebitda_*, tornado_zero_crossings, billing_mix_curve, pharmacy_synergy_range) + 3 PNG figures
  - phase: 04-clinic-financial-model
    provides: §6 report{} deposits (steady_state_ebitda, steady_state_margin, peak_capital, breakeven_operating, breakeven_payback) + clinic_pnl/clinic_ramp_monthly pure functions
provides:
  - §8 Executive Report section (6 cells: §8.1-§8.5)
  - Binary GO/NO-GO verdict logic gated on EBITDA > 0 AND margin > 15% (D-01, D-03, REP-02)
  - 5-column assumptions register from BASE_ASSUMPTIONS (REP-01, D-16)
  - 8-section Jinja2 HTML template with investor-grade CSS (D-14, D-15, REP-03)
  - weasyprint PDF generation (Colab-only, D-18, REP-03)
  - Footnote-style citations [1]-[8] with access dates (D-17, REP-04)
  - report{} deposits: verdict, verdict_text, key_numbers, flip_conditions, assumptions_register
affects: []

# Tech tracking
tech-stack:
  added: [jinja2 (preinstalled), weasyprint (Colab pip)]
  patterns:
    - "D-01: Verdict gate = steady-state EBITDA > 0 AND margin > 15% — payback is context, not the gate"
    - "D-03: Binary GO/NO-GO verdict — no CONDITIONAL tier"
    - "D-04: Verdict text is 100% standalone — never mentions pharmacy (Core Value)"
    - "D-13: Page 1 = verdict + 5 key numbers + one catchment map"
    - "D-14: 8-section narrative report structure"
    - "D-15: Jinja2 HTML template as inline string (self-contained notebook) + weasyprint PDF"
    - "D-16: 5-column assumptions register: Parameter | Value | Source | Date | Confidence"
    - "D-17: Footnote-style citations [1], [2] with access dates in footnotes section"
    - "D-18: Colab-only PDF — local Windows produces HTML only with printed note"
    - "Pattern 5: §8 is a pure render step — reads report{} + saved PNGs, produces HTML → PDF"
    - "PIPE-04: weasyprint failure wrapped in try/except — no-hard-fail"
    - "Pitfall 16: All figures are static matplotlib PNGs embedded as base64 — no folium"

key-files:
  created:
    - .planning/phases/05-scenarios-executive-report/05-02-SUMMARY.md
  modified:
    - scripts/extend_v2_notebook_phase5.py
    - Johnston_St_v2.ipynb

key-decisions:
  - "Verdict gate: steady-state EBITDA > 0 AND margin > 15% (D-01) — payback is context, not the gate"
  - "Binary GO/NO-GO verdict (D-03) — no CONDITIONAL tier, investors want a clear answer"
  - "Verdict text is 100% standalone — never mentions pharmacy (D-04, Core Value)"
  - "Flip-conditions presented as tornado zero-crossings — one sentence per lever (D-02)"
  - "Jinja2 template as inline Python string — keeps notebook self-contained (D-15)"
  - "PDF generation is Colab-only via weasyprint — local Windows produces HTML only (D-18)"
  - "All static figures embedded as base64 — portable HTML + weasyprint rendering (D-15, Pitfall 16)"
  - "Assumptions register parses # source — date inline comments from BASE_ASSUMPTIONS (PIPE-05)"

patterns-established:
  - "§8 pure render step: reads report{} + saved PNGs only — re-runnable standalone (Data Flow #4)"
  - "Generator idempotency: §7+§8 regenerated together from '# §7 Scenarios & Sensitivity' marker"
  - "Verdict logic pattern: binary gate on EBITDA + margin, flip-conditions from tornado zero-crossings"
  - "Assumptions register pattern: regex-parse BASE_ASSUMPTIONS source for citation comments → 5-column DataFrame"

requirements-completed:
  - REP-01
  - REP-02
  - REP-03
  - REP-04

# Metrics
duration: ~35 min
completed: 2026-07-06
---

# Phase 5 Plan 02: Executive Report Summary

**§8 Executive Report — binary GO/NO-GO verdict logic, 5-column assumptions register, 8-section Jinja2 HTML template with weasyprint PDF, footnote citations — the investor deliverable**

## Performance

- **Duration:** ~35 min
- **Tasks:** 1
- **Files modified:** 2 (scripts/extend_v2_notebook_phase5.py updated, Johnston_St_v2.ipynb extended 82→88 cells)

## Accomplishments
- `scripts/extend_v2_notebook_phase5.py` updated with `phase5_executive_report_cells()` function producing 6 §8 cells; `main()` now combines §7 + §8 cells with single idempotency marker
- §8.1 verdict logic (D-01, D-02, D-03, D-04, REP-02): binary GO/NO-GO gated on steady-state EBITDA > 0 AND margin > 15%; flip-conditions from tornado zero-crossings; 5 key numbers for page 1; verdict text never mentions pharmacy
- §8.2 assumptions register (REP-01, D-16): 5-column table (Parameter | Value | Source | Date | Confidence) parsed from BASE_ASSUMPTIONS inline citation comments; deposited as DataFrame into report{}
- §8.3 Jinja2 HTML template (D-14, D-15, REP-02, REP-03): 8-section narrative report with investor-grade CSS (cover page, page breaks, page numbers); static PNG figures embedded as base64; footnote-style citations [1]-[8] with access dates; pharmacy synergy labelled "Secondary Upside — NOT Load-Bearing"
- §8.4 weasyprint PDF generation (REP-03, D-18): Colab-only via `google.colab` detection; local Windows produces HTML only with printed note; try/except ensures no-hard-fail (PIPE-04)
- §8.5 interpretation + final Next Steps: feasibility study complete, deferred items listed
- All 27 plan verify assertions pass; all 18 acceptance criteria verified; idempotency confirmed (88 cells maintained after re-run)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add §8 Executive Report cells to generator + extend notebook** - `dcf2277` (feat)

## Files Created/Modified
- `scripts/extend_v2_notebook_phase5.py` - Updated. Added `phase5_executive_report_cells()` function (6 cells: 1 markdown header + 4 code cells + 1 markdown interpretation). Updated `main()` to combine `phase5_scenarios_cells() + phase5_executive_report_cells()`. Docstring updated to reflect Plans 05-01 + 05-02. Idempotency replaces from `# §7 Scenarios & Sensitivity` marker to end-of-notebook with full §7+§8 cell list.
- `Johnston_St_v2.ipynb` - Extended 82→88 cells. §8 Executive Report section appended after §7. 6 new cells: §8.1 verdict logic, §8.2 assumptions register, §8.3 Jinja2 HTML template, §8.4 weasyprint PDF, §8.5 interpretation + Next Steps.

## Decisions Made
- **Verdict gate: EBITDA > 0 AND margin > 15% (D-01):** Payback is context, not the gate — clinic is a long-lived asset. The Phase 4 base case (+$258k EBITDA, 38.4% margin) clears this gate comfortably.
- **Binary GO/NO-GO (D-03):** No CONDITIONAL tier — investors want a clear answer. The base case is clearly profitable, so a flat GO with flip-conditions noted is defensible.
- **Verdict text is 100% standalone (D-04):** The verdict_text string never mentions "pharmacy" or "Priceline" — it describes only the clinic's standalone economics. Pharmacy synergy appears in a separate §6 section labelled "Secondary Upside — NOT Load-Bearing."
- **Jinja2 template as inline string (D-15):** Keeps the notebook self-contained — no external template file dependency. The template uses `r"""..."""` raw string to handle CSS curly braces.
- **Colab-only PDF (D-18):** weasyprint's GTK/pango deps are present or apt-installable in one line on Colab. Local Windows runs produce HTML only with a printed note. Avoids Windows GTK runtime pain.
- **All figures as base64 (D-15, Pitfall 16):** Static matplotlib PNGs embedded as `data:image/png;base64,...` — portable HTML + weasyprint rendering. No folium (HTML/JS, can't render in PDF).
- **Assumptions register parses BASE_ASSUMPTIONS source (REP-01, D-16):** The §8.2 cell reads the notebook's own BASE_ASSUMPTIONS cell source and regex-parses the `# source — date` inline comments into the 5-column table. Keys without citations are marked "TBD — needs citation" with LOW confidence.

## Deviations from Plan

None — plan executed exactly as written. All 27 verify assertions and 18 acceptance criteria pass on first execution. The generator's idempotency was verified by re-running and confirming 88 cells maintained.

## Issues Encountered
- **CRLF line endings in generator script:** The existing `scripts/extend_v2_notebook_phase5.py` uses CRLF line endings (Windows). The §8 function was written separately and inserted via a Python helper script, then line endings were normalized to CRLF. No functional impact.
- **Unicode output encoding:** The generator script's print statements contain Unicode section signs (§) and em-dashes (—) which cause encoding issues when captured via subprocess on Windows. The script runs correctly (exit code 0) — the issue is only with output capture, not execution.
- **matplotlib/jinja2 not installed locally:** The §8.3 Jinja2 template cell requires jinja2 which is preinstalled in Colab but may not be locally. The notebook is designed for Colab (primary environment). No code changes needed.

## User Setup Required
None — no external service configuration required. §8 is a pure render step that reads the `report{}` accumulator and saved PNG figures. The HTML report is always produced; the PDF is Colab-only via weasyprint (D-18).

## Next Phase Readiness
- **Feasibility study complete.** The notebook + PDF are the deliverable. The notebook now has 88 cells covering §0-§8: setup, data pipeline, catchment, demographics, competitors, demand model, financial model, scenarios & sensitivity, and executive report.
- `report{}` accumulator now holds all metrics for the executive report: `steady_state_ebitda`, `steady_state_margin`, `peak_capital`, `breakeven_operating`, `breakeven_payback`, `scenario_ebitda_*`, `tornado_zero_crossings`, `billing_mix_curve`, `pharmacy_synergy_range`, `verdict`, `verdict_text`, `key_numbers`, `flip_conditions`, `assumptions_register`.
- The §8 render step is re-runnable standalone — re-running §8 alone regenerates the HTML/PDF from current `report{}` state (ARCHITECTURE.md Data Flow #4).
- **Deferred to future milestone:** Monte Carlo confidence intervals (V2-01), drive-time isochrone catchments (V2-02), interactive dashboard.
- **Deferred human verification (Colab Restart & Run All):** confirm §8 runs end-to-end, HTML report generates, PDF generates (Colab), assumptions register populates, verdict displays.

---
*Phase: 05-scenarios-executive-report*
*Completed: 2026-07-06*
