---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: ready_to_execute
last_updated: "2026-07-05T20:30:00Z"
progress:
  total_phases: 5
  completed_phases: 1
  total_plans: 4
  completed_plans: 2
  percent: 50
---

# State — Clinic Feasibility Study

**Project:** JSMC — Johnston St Medical Clinic Feasibility Study
**Roadmap:** [ROADMAP.md](./ROADMAP.md)
**Updated:** 2026-07-05

## Current Phase

**Phase 2 — Catchment & Demographics**

## Current Status

Phase 2 planning complete. Ready to execute.

- `02-01-PLAN.md` — Catchment (geocode + buffers + SA1 apportionment + v1-vs-v2 comparison + maps) — **PLANNED** (Wave 1)
- `02-02-PLAN.md` — Demographics (ABS G01/G02/G04 + ERP scaling + peer benchmarking + charts) — **PLANNED** (Wave 2, depends on 02-01)

- `01-01-PLAN.md` — Repo scaffolding — **COMPLETE** (commits 5390043, b0e3e6c)
- `01-02-PLAN.md` — Notebook v2 scaffolding (§0 setup + §1 cache layer + ABS smoke test) — **COMPLETE** (commits 1d47733, 654ab63)

Plan 01-01 delivered: .gitignore, .env.example, directory structure (data/local/, data/cache/, outputs/, docs/abs-api/), 8 data files relocated, 4 ABS docs relocated, clean repo root. See [01-01-SUMMARY.md](./phases/01-scaffolding-data-pipeline/01-01-SUMMARY.md).

Plan 01-02 delivered: Johnston_St_v2.ipynb (11 cells: §0 setup/env-detect/PARAMS + §1 CachedSession/ABS-smoke-test), scripts/create_v2_notebook.py (generator), scripts/validate_v2_notebook.py (validation — OVERALL: PASS). All v1 flaws eradicated. See [01-02-SUMMARY.md](./phases/01-scaffolding-data-pipeline/01-02-SUMMARY.md).

## Recent Decisions

| Decision | Rationale | Date |
|----------|-----------|------|
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

1. Execute Phase 2 Plan 02-01 (Wave 1) — Catchment: geocode, buffers, SA1 apportionment, maps.
2. Execute Phase 2 Plan 02-02 (Wave 2) — Demographics: ABS G01/G02/G04, ERP scaling, peer benchmarking.
3. Phase 2 uses the CachedSession and BASE_ASSUMPTIONS established in 01-02; extends BASE_ASSUMPTIONS with 6 new Phase 2 keys.
