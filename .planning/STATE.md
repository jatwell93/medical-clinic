---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
last_updated: "2026-07-05T11:24:11.595Z"
progress:
  total_phases: 2
  completed_phases: 2
  total_plans: 4
  completed_plans: 4
  percent: 100
---

# State — Clinic Feasibility Study

**Project:** JSMC — Johnston St Medical Clinic Feasibility Study
**Roadmap:** [ROADMAP.md](./ROADMAP.md)
**Updated:** 2026-07-05

## Current Phase

**Phase 2 — Catchment & Demographics (COMPLETE)**

Ready for Phase 3 — Demand & Competitors.

## Current Status

Phase 2 complete. All 4 plans across 2 phases delivered.

- `02-01-PLAN.md` — Catchment (geocode + buffers + SA1 apportionment + v1-vs-v2 comparison + maps) — **COMPLETE** (commits 9a0dbbc, 7083642)
- `02-02-PLAN.md` — Demographics (ABS G01/G02/G04 + ERP scaling + peer benchmarking + charts) — **COMPLETE** (commits 2e2dac6, 5432534)

- `01-01-PLAN.md` — Repo scaffolding — **COMPLETE** (commits 5390043, b0e3e6c)
- `01-02-PLAN.md` — Notebook v2 scaffolding (§0 setup + §1 cache layer + ABS smoke test) — **COMPLETE** (commits 1d47733, 654ab63)

Plan 02-02 delivered: Johnston_St_v2.ipynb extended from 26→36 cells with §3 Demographics (ABS G01/G02/G04 fetch + local GCP fallback, SA1 total persons wired into §2.3 apportionment for v2 catchment population totals, ERP scaling to 2024, peer benchmarking table with Phase 3 placeholders, 2×2 comparison charts). compare_v1_v2() called with real v2 totals — D-06 headline teaching moment complete. scripts/extend_v2_notebook_demographics.py (idempotent generator), scripts/validate_v2_notebook.py (extended with DEMO-01..04 + D-03/D-06/D-09b/D-11 — OVERALL: PASS). See [02-02-SUMMARY.md](./phases/02-catchment-demographics/02-02-SUMMARY.md).

## Recent Decisions

| Decision | Rationale | Date |
|----------|-----------|------|
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

## Next Actions

1. Phase 2 is complete — all GEO-01..04 + DEMO-01..04 requirements satisfied and validated.
2. Ready for Phase 3 — Demand & Competitors: SA3-level MBS data, Google Places competitor mapping, age-adjusted demand model, required market share calculation.
3. Phase 3 depends on: geocoded site (§1.2), catchment buffers (§2), apportioned population (§3), age profile (§3 G04), peer benchmarking table (§3 with placeholder GP/pharmacy columns).
