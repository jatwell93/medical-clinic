---
phase: 05
slug: scenarios-executive-report
status: verified
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-06
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python `assert` + `scripts/validate_v2_notebook.py` (extended from Phase 1-3) |
| **Config file** | `scripts/validate_v2_notebook.py` (single re-runnable structural + content check script) |
| **Quick run command** | `python scripts/validate_v2_notebook.py` |
| **Full suite command** | `python scripts/validate_v2_notebook.py` |
| **Estimated runtime** | ~3 seconds |

> This is a notebook project, not a unit-tested application. Validation is structural (notebook JSON integrity, cell presence, source content pattern matching) + execution-time (in-notebook `assert` statements that fail loudly on Restart & Run All). The validator was extended with 8 Phase 5 checks (section `# 6. Phase 5 checks`), following the established Phase 1-3 pattern. No separate pytest suite is introduced.

---

## Sampling Rate

- **After every task commit:** Run `python scripts/validate_v2_notebook.py`
- **After every plan wave:** Run full suite command + manual cell-count check
- **Before `/gsd-verify-work`:** Full suite green + in-notebook asserts pass on a fresh Restart & Run All (Colab primary, Windows local secondary)
- **Max feedback latency:** 5 seconds (structural) / one notebook run (execution-time)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | FIN-04 | — | N/A (no PII; financial model only) | structural | `python scripts/validate_v2_notebook.py` (FIN-04 check) | ✅ | ✅ green |
| 05-01-01 | 01 | 1 | FIN-05 | — | N/A | structural | `python scripts/validate_v2_notebook.py` (FIN-05 check) | ✅ | ✅ green |
| 05-01-01 | 01 | 1 | FIN-06 | — | N/A | structural | `python scripts/validate_v2_notebook.py` (FIN-06 check) | ✅ | ✅ green |
| 05-01-01 | 01 | 1 | FIN-07 | — | N/A | structural | `python scripts/validate_v2_notebook.py` (FIN-07 check) | ✅ | ✅ green |
| 05-02-01 | 02 | 2 | REP-01 | — | N/A | structural | `python scripts/validate_v2_notebook.py` (REP-01 check) | ✅ | ✅ green |
| 05-02-01 | 02 | 2 | REP-02 | T-05-01 | Verdict text never mentions pharmacy (D-04 standalone) — checked by REP-02 validator | structural | `python scripts/validate_v2_notebook.py` (REP-02 check) | ✅ | ✅ green |
| 05-02-01 | 02 | 2 | REP-03 | T-05-04 | PDF generation wrapped in try/except (PIPE-04 no-hard-fail) — checked by REP-03 validator | structural | `python scripts/validate_v2_notebook.py` (REP-03 check) | ✅ | ✅ green |
| 05-02-01 | 02 | 2 | REP-04 | — | N/A | structural | `python scripts/validate_v2_notebook.py` (REP-04 check) | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

### Check Details

| Check | Requirement | What It Verifies |
|-------|-------------|------------------|
| FIN-04 | Scenario override dicts | §7.1 cell present, `scenarios = {}` with 3 keys (base/optimistic/pessimistic), 5 independent levers (rent_yr, utilisation, gp_revenue_share, gp_ramp_milestones, bulk_bill_share), `{**BASE_ASSUMPTIONS, **overrides}` pattern |
| FIN-05 | Tornado sensitivity | §7.3 (EBITDA tornado, 8 inputs) + §7.4 (peak capital tornado, 6 inputs) cells present, `find_zero_crossing` function, `np.linspace` + `np.interp`, PNG save calls |
| FIN-06 | Billing-mix curve | §7.5 cell present, 5 bulk_bill_share points [0%, 25%, 50%, 70%, 100%], BBPIP 12.5%/6.25% practice retention, `billing_mix_curve.png` save |
| FIN-07 | Pharmacy synergy order-gated | §7.6 cell index > §7.1 cell index, "NOT Load-Bearing" label, NO `clinic_pnl()` call in synergy cell (standalone arithmetic) |
| REP-01 | Assumptions register | §8.2 cell present, 5-column headers (Parameter, Value, Source, Date, Confidence), `assumptions_register` deposited into `report{}` |
| REP-02 | Verdict logic | §8.1 cell present, binary `verdict = "GO" if ... else "NO-GO"`, `GATE_MARGIN = 0.15`, verdict_text f-string block excludes "pharmac"/"priceline" (D-04), 5 key numbers deposited |
| REP-03 | Executive report PDF | §8.3 Jinja2 template with 8 sections, `Template` usage, §8.4 weasyprint cell, `IS_COLAB` check, try/except wrapper |
| REP-04 | Footnote citations | Citations [1] through [8] all present in §8.3 template cell, "Access date" markers |

---

## Wave 0 Requirements

- [x] `scripts/validate_v2_notebook.py` extended with Phase 5 checks (section `# 6. Phase 5 checks (FIN-04..07, REP-01..04)`)

*Existing infrastructure covers all phase requirements. No new test framework needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| PNG figure generation (tornado_ebitda.png, tornado_peak_capital.png, billing_mix_curve.png) | FIN-05, FIN-06 | matplotlib not installed locally; cells execute in Colab only | Run notebook in Colab (Restart & Run All); confirm 3 PNG files appear in `outputs/` |
| weasyprint PDF generation | REP-03 | Requires Colab GTK/pango deps (apt-installable); local Windows produces HTML only by design (D-18) | Run notebook in Colab; confirm `outputs/Johnston_St_v2_Executive_Report.pdf` is generated |
| Assumptions register runtime population | REP-01 | Requires BASE_ASSUMPTIONS cell to execute first; regex parsing verified structurally | Run notebook in Colab; confirm §8.2 prints a populated 5-column table with Source/Date/Confidence filled |
| Verdict display + report{} accumulator end-to-end | REP-02 | Requires full notebook execution (§0-§8) to populate all report{} deposits | Run notebook in Colab; confirm §8.1 prints "VERDICT: GO" with 5 key numbers and flip-conditions |
| HTML report visual fidelity | REP-03 | Visual layout verification (cover page, page breaks, CSS styling) | Open `outputs/Johnston_St_v2_Executive_Report.html` in a browser; confirm 8 sections render with investor-grade styling |

---

## Validation Audit Trail

| Audit Date | Gaps Found | Resolved | Escalated | Run By |
|------------|------------|----------|-----------|--------|
| 2026-07-06 | 8 | 8 | 0 | gsd-nyquist-auditor agent |

### Audit Notes

- **Input state:** State B — no prior VALIDATION.md; reconstructed from PLAN/SUMMARY artifacts + implementation code review.
- **Gap source:** The existing `scripts/validate_v2_notebook.py` covered Phases 1-3 (28 checks, all pass) but had ZERO Phase 5 coverage. All 8 requirements (FIN-04..07, REP-01..04) were classified MISSING.
- **Resolution:** Extended the validator script with 8 new structural checks (section `# 6. Phase 5 checks`), following the established Phase 1-3 pattern of inspecting notebook cell sources as strings.
- **Debug iterations:** 1 iteration needed — REP-02 check initially failed because the §8.1 cell contains the comment `# verdict text never mentions pharmacy (D-04)` which includes "pharmacy". Fixed by refining the check to extract only the `verdict_text = (...)` f-string construction block, excluding comments. The verdict_text block itself correctly contains no pharmacy/priceline mentions.
- **Final validator output:** 36 checks pass (28 existing + 8 new), exit code 0, "OVERALL: PASS".
- **Security cross-reference:** REP-02 check verifies the D-04 standalone verdict constraint (threat T-05-01 from 05-SECURITY.md). REP-03 check verifies the PIPE-04 no-hard-fail try/except wrapper (threat T-05-04).

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s (structural) / one notebook run (execution-time)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-07-06
