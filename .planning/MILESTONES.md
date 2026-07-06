# Milestones — Johnston St Medical Clinic Feasibility Study

## v1.0 — Johnston St Medical Clinic Feasibility Study

**Status:** ✅ SHIPPED 2026-07-06
**PR:** [#1](https://github.com/jatwell93/medical-clinic/pull/1) (merged)
**Phases:** 5 | **Plans:** 12 | **Commits:** 93 | **Files:** 81 | **LOC:** ~29,600
**Timeline:** 2026-07-05 → 2026-07-06 (2 days)
**Archive:** [v1.0-ROADMAP.md](./milestones/v1.0-ROADMAP.md) | [v1.0-REQUIREMENTS.md](./milestones/v1.0-REQUIREMENTS.md)

### Key Accomplishments

1. Built `Johnston_St_v2.ipynb` (88 cells, §0-§8) — a complete investor-grade feasibility study with dual-environment bootstrap (Colab/Windows), cached API boundary ($0 re-runs), and teaching commentary throughout
2. Fixed v1's three critical flaws: degree-based buffer catchment (→ EPSG:7855), whole-postcode summing (→ SA1 area-apportionment), and Random Forest on 3-10 rows (→ transparent arithmetic demand model)
3. Built `clinic_pnl(a)` pure function + 36-month ramp cash flow model — peak capital and breakeven as headline outputs, enabling cheap scenario overrides
4. Produced base/optimistic/pessimistic scenarios + two tornado sensitivity charts (numpy zero-crossings) + billing-mix curve with BBPIP 12.5% incentive
5. Generated executive report: binary GO/NO-GO verdict (gated on EBITDA > 0 AND margin > 15%), 5-column assumptions register, 8-section Jinja2 HTML template, weasyprint PDF (Colab-only)
6. Quantified pharmacy synergy as order-gated secondary upside — never able to rescue an unprofitable clinic (Core Value preserved)

### Known Deferred Items at Close

5 manual-only validation items deferred to Colab runtime (see 05-VALIDATION.md): PNG figure generation, PDF generation, assumptions register runtime population, end-to-end Restart & Run All, HTML visual fidelity.

### Verification

- Automated validator: 36 checks, all PASS
- Phase 5 security audit: 5 threats, 0 open (05-SECURITY.md)
- Phase 5 Nyquist validation: 8/8 gaps filled (05-VALIDATION.md)
- 2 PR review bugs found by sentry[bot] and fixed before merge
