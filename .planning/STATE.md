---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: milestone_complete
last_updated: "2026-07-06T03:12:36.402Z"
progress:
  total_phases: 5
  completed_phases: 4
  total_plans: 12
  completed_plans: 10
  percent: 83
---

# State — Clinic Feasibility Study

**Project:** JSMC — Johnston St Medical Clinic Feasibility Study
**Roadmap:** [ROADMAP.md](./ROADMAP.md)
**Updated:** 2026-07-05

## Current Phase

**Phase 2 — Catchment & Demographics (COMPLETE)**

Gap-closure plan 02-03 executed — all 6 verification gaps closed (2 critical, 4 warning/info). §3 demographics is runtime-functional; v1-vs-v2 comparison shows real overstatement. Validator OVERALL: PASS (22 checks). Phase 2 complete.

## Current Status

Phase 2 complete. All 5 of 5 plans done.

- `02-01-PLAN.md` — Catchment (geocode + buffers + SA1 apportionment + v1-vs-v2 comparison + maps) — **COMPLETE** (commits 9a0dbbc, 7083642)
- `02-02-PLAN.md` — Demographics (ABS G01/G02/G04 + ERP scaling + peer benchmarking + charts) — **COMPLETE** (commits 2e2dac6, 5432534)
- `02-03-PLAN.md` — Gap closure (CR-01 check_dataflow_exists XML fix, CR-02 v1-vs-v2 comparison fix, WR-01..04 + IR-02 validator strengthening) — **COMPLETE** (commits 782494c, 612d36b, d4d62ed, e870a22)

- `01-01-PLAN.md` — Repo scaffolding — **COMPLETE** (commits 5390043, b0e3e6c)
- `01-02-PLAN.md` — Notebook v2 scaffolding (§0 setup + §1 cache layer + ABS smoke test) — **COMPLETE** (commits 1d47733, 654ab63)

Plan 02-03 closed all 6 gaps from 02-VERIFICATION.md: CR-01 (check_dataflow_exists now parses SDMX-ML XML via ElementTree, no .json() on XML endpoint, try/except safe default True), CR-02 (compare_v1_v2 accepts (v1_ring_pops, v2_ring_pops) and computes real pct_overstate; v1_naive_catchment_pop joins g01_df Total_P_P; v1_pop = v2_pop stub eradicated), WR-01 (try/except safe default), WR-02 (empty-schema GCP fallbacks, no zero-stubs), WR-03 (fetch_g04_poa calls fetch_g04_fallback), WR-04 (explicit age-band prefix matching + matched-columns print). Both generators upgraded to cell-replacement idempotency (re-run regenerates the corrected notebook; 36 cells preserved). Validator strengthened with negative pattern assertions for CR-01 + CR-02 stub (IR-02) — OVERALL: PASS. See [02-03-SUMMARY.md](./phases/02-catchment-demographics/02-03-SUMMARY.md).

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
| Cell-replacement idempotency strips trailing §2 Next Steps when §3 follows | §3 owns the final Next Steps; keeping the §2 version would duplicate it mid-notebook and break the 36-cell count | 2026-07-05 |
| Demographics cell-replacement includes Next Steps in removed range (end_idx = j+1) | demographics_cells() ships its own Next Steps; excluding it from removal would duplicate and break 36-cell count | 2026-07-05 |
| check_dataflow_exists safe-defaults True on any failure | No-hard-fail principle (PIPE-04); downstream fetch_g0X_poa functions have their own try/except fallbacks | 2026-07-05 |
| Added CR-01 to validator report label list + structural-failure filter | report() uses a hardcoded label list; without adding CR-01 the new check was invisible and a failure would double-print | 2026-07-05 |

## Next Actions

1. Phase 2 is complete — all GEO-01..04 + DEMO-01..04 requirements satisfied at the structural/runtime-ready level.
2. Deferred human verification (Colab Restart & Run All): confirm §3 runs end-to-end without JSONDecodeError, v1-vs-v2 chart shows v1 > v2 (pct_overstate > 0%), G04 age bands detected, fallback consistent across G01/G02/G04.
3. Phase 3 — Demand & Competitors: SA3-level MBS data, Google Places competitor mapping, age-adjusted demand model, required market share calculation.
4. Phase 3 depends on: geocoded site (§1.2), catchment buffers (§2), apportioned population (§3), age profile (§3 G04), peer benchmarking table (§3 with placeholder GP/pharmacy columns) — all now runtime-functional after 02-03.
