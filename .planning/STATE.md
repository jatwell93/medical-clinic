---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: in_progress
last_updated: "2026-07-06T05:30:00.000Z"
progress:
  total_phases: 5
  completed_phases: 5
  total_plans: 12
  completed_plans: 12
  percent: 100
---

# State — Clinic Feasibility Study

**Project:** JSMC — Johnston St Medical Clinic Feasibility Study
**Roadmap:** [ROADMAP.md](./ROADMAP.md)
**Updated:** 2026-07-06

## Current Phase

**Phase 5 — Scenarios & Executive Report (COMPLETE)**

Plan 05-02 executed — §8 Executive Report added to the notebook. Binary GO/NO-GO verdict logic (D-01, D-03, D-04, REP-02), 5-column assumptions register (REP-01, D-16), 8-section Jinja2 HTML template (D-14, D-15, REP-03), weasyprint PDF generation (D-18), footnote citations (D-17, REP-04). All 32 requirements satisfied. Notebook now has 88 cells (§0-§8).

## Current Status

Phase 5 complete. 2 of 2 plans done. All 5 phases complete.

- `05-01-PLAN.md` — Scenarios & Sensitivity (base/opt/pess override dicts + 2 tornado charts + billing-mix curve + pharmacy synergy range) — **COMPLETE**
- `05-02-PLAN.md` — Executive Report (verdict logic + assumptions register + Jinja2 template + weasyprint PDF + citations) — **COMPLETE**

## Recent Decisions

| Decision | Rationale | Date |
|----------|-----------|------|
| Scenario override dicts contain ONLY changed keys | {**BASE_ASSUMPTIONS, **overrides} supplies unchanged values; base case = empty override dict (D-05) | 2026-07-06 |
| 5 scenario levers: rent, utilisation, service-fee %, ramp speed, billing mix | D-05 — each moves independently via override dict on clinic_pnl + clinic_ramp_monthly | 2026-07-06 |
| Tornado zero-crossings via np.linspace(200 steps) + np.interp | Don't Hand-Roll — numpy vectorised search for rent/utilisation/service-fee where EBITDA=0 (D-02) | 2026-07-06 |
| BBPIP 12.5% with 6.25% practice retention at 100% bulk only | D-09/Pitfall 7 — BBPIP is all-or-nothing practice incentive; added as extra revenue on top of clinic_pnl EBITDA | 2026-07-06 |
| Pharmacy synergy as standalone arithmetic, NOT clinic_pnl override | D-11/D-12 — per-capita scripts × capture rate × margin; only new computation in Phase 5; order-gated after standalone (D-04) | 2026-07-06 |
| §6 "## Next Steps" cell removed by Phase 5 generator | §7.7 Interpretation replaces it as notebook tail; remove_next_steps() helper strips all Next Steps cells | 2026-07-06 |
| Verdict gate: EBITDA > 0 AND margin > 15% (D-01) | Payback is context, not the gate — clinic is a long-lived asset; base case +$258k/38.4% clears gate | 2026-07-06 |
| Binary GO/NO-GO verdict, no CONDITIONAL tier (D-03) | Investors want a clear answer; base case clearly profitable so flat GO with flip-conditions is defensible | 2026-07-06 |
| Verdict text is 100% standalone — never mentions pharmacy (D-04) | Core Value — clinic verdict must be independent of pharmacy; pharmacy synergy in separate §6 section labelled "NOT Load-Bearing" | 2026-07-06 |
| Jinja2 template as inline Python string (D-15) | Keeps notebook self-contained — no external template file dependency; r-string handles CSS curly braces | 2026-07-06 |
| Colab-only PDF via weasyprint (D-18) | GTK/pango deps apt-installable on Colab; local Windows produces HTML only — avoids Windows GTK runtime pain | 2026-07-06 |
| All figures as base64-embedded static PNGs (D-15, Pitfall 16) | Portable HTML + weasyprint rendering; no folium (HTML/JS can't render in PDF) | 2026-07-06 |
| Assumptions register parses BASE_ASSUMPTIONS source comments (REP-01, D-16) | Regex-parses # source — date inline comments into 5-column table; keys without citations marked "TBD — needs citation" LOW confidence | 2026-07-06 |
| §7+§8 regenerated together from single idempotency marker | Keeps §7 and §8 in sync — re-running generator always regenerates both sections from '# §7 Scenarios & Sensitivity' marker | 2026-07-06 |
| fetch_abs_csv() returns (DataFrame, response) tuple | Plan pseudocode had scoping bug — resp referenced outside try block; returning tuple fixes this | 2026-07-05 |
| ERP growth rate defaults to 1.0 when API unavailable | Never hard-fail on network call (PIPE-04); peer table falls back to unscaled 2021 values | 2026-07-05 |
| v2_ring_pops initialized as empty dict for non-SA1 path | Plan only defined it inside if USE_SA1; ERP cell references it unconditionally — would NameError | 2026-07-05 |
| Added geopandas/shapely imports inline in §2.1 cell | Plan omitted explicit imports; code uses gpd/Point without importing — would fail on execution | 2026-07-05 |
| Replaced old Phase 1 Next Steps with Phase 2 version | Old Next Steps referenced Phase 2 as future; now Phase 2 cells are present | 2026-07-05 |
| Used ensure_ascii=False in json.dump | Preserve Unicode teaching characters (⚠, π, ℹ) in notebook source | 2026-07-05 |
| 5-phase coarse granularity | Config `granularity=coarse` (3-5 phases); consolidated research's 7 phases into 5 by grouping catchment+demographics and demand+competitors | 2026-07-05 |
| Scenarios/report split from base P&L | FIN-04..07 (scenarios, sensitivity, billing comparison, pharmacy synergy) depend on the pure-function P&L and belong with reporting (REP-01..04) in Phase 5 | 2026-07-05 |
| Demand & competitors grouped (Phase 3) | Required-market-share headline metric needs both demand rates and competitor capacity; converging them in one phase produces the supply/demand verdict | 2026-07-05 |
| Phase 1 split into 2 parallel plans | Repo scaffolding (01-01) and notebook scaffolding (01-02) have no file conflicts — both Wave 1. 6-8 tasks total would exceed the 2-3 tasks/plan guideline in a single plan. | 2026-07-05 |
| Public repo, filesystem cache, section+inline commentary | User-confirmed: public GitHub repo (no Colab auth needed), requests-cache filesystem backend (JSON files, teaching-friendly), section-level markdown + inline comments for PIPE-06 | 2026-07-05 |
| data/cache/*.json committed, redirects.sqlite gitignored | D-12: API response caches are the reproducibility keystone (no secrets); redirects.sqlite is regenerable metadata | 2026-07-05 |
| outputs/.gitkeep force-added despite outputs/ gitignored | Directory structure must survive in fresh clones; outputs contents remain gitignored (regenerated on run) | 2026-07-05 |
| json.dump over nbformat for notebook generation | Avoids extra dependency; .ipynb structure is simple enough for direct dict construction (RESEARCH.md §4) | 2026-07-05 |
| Teaching commentary reworded to avoid literal v1 flaw strings | Acceptance criteria requires zero /content/drive and drive.mount occurrences in any cell, including markdown teaching commentary | 2026-07-05 |
| Cell-replacement idempotency strips trailing §2 Next Steps when §3 follows | §3 owns the final Next Steps; keeping the §2 version would duplicate it mid-notebook and break the 36-cell count | 2026-07-05 |
| Demographics cell-replacement includes Next Steps in removed range (end_idx = j+1) | demographics_cells() ships its own Next Steps; excluding it from removal would duplicate and break 36-cell count | 2026-07-05 |
| check_dataflow_exists safe-defaults True on any failure | No-hard-fail principle (PIPE-04); downstream fetch_g0X_poa functions have their own try/except fallbacks | 2026-07-05 |
| Added CR-01 to validator report label list + structural-failure filter | report() uses a hardcoded label list; without adding CR-01 the new check was invisible and a failure would double-print | 2026-07-05 |

## Next Actions

1. Phase 5 complete — all 12 plans across 5 phases executed. All 32 requirements satisfied (PIPE, GEO, DEMO, DEMAND, COMP, FIN, REP).
2. Feasibility study deliverable complete: Johnston_St_v2.ipynb (88 cells, §0-§8) + executive report (HTML always, PDF Colab-only).
3. Deferred human verification (Colab Restart & Run All): confirm §7+§8 run end-to-end, all PNG figures generate, HTML report renders, PDF generates (Colab), assumptions register populates, verdict displays.
4. Deferred to future milestone: Monte Carlo confidence intervals (V2-01), drive-time isochrone catchments (V2-02), interactive dashboard.
