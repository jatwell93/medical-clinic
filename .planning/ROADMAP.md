# Roadmap — Clinic Feasibility Study

**Project:** JSMC — Johnston St Medical Clinic Feasibility Study
**Goal:** A professional-grade site feasibility analysis (Colab notebook + executive PDF) evaluating whether 292-296 Johnston St, Abbotsford VIC 3067 can support an independently profitable 5-FTE-GP medical clinic.
**Granularity:** Coarse (5 phases)
**Created:** 2026-07-05

## Phase Overview

| Phase | Name | Requirements | Dependencies |
|-------|------|--------------|--------------|
| 1 | Scaffolding & Data Pipeline | PIPE-01, PIPE-02, PIPE-03, PIPE-04, PIPE-05, PIPE-06 | — |
| 2 | Catchment & Demographics | GEO-01, GEO-02, GEO-03, GEO-04, DEMO-01, DEMO-02, DEMO-03, DEMO-04 | Phase 1 |
| 3 | Demand & Competitors | DEMAND-01, DEMAND-02, DEMAND-03, DEMAND-04, COMP-01, COMP-02, COMP-03 | Phase 2 |
| 4 | Clinic Financial Model | FIN-01, FIN-02, FIN-03 | Phase 3 |
| 5 | Scenarios & Executive Report | FIN-04, FIN-05, FIN-06, FIN-07, REP-01, REP-02, REP-03, REP-04 | Phase 4 |

---

## Phase 1 — Scaffolding & Data Pipeline

**Goal:** Establish the reproducible foundation — dual-environment bootstrap, cached API boundary, single parameters cell, and teaching-commentary convention — so every subsequent phase can fetch external data deterministically and re-run at zero cost.

**Requirements mapped:** PIPE-01, PIPE-02, PIPE-03, PIPE-04, PIPE-05, PIPE-06

**Plan progress:**
- [x] 01-01: Repo scaffolding (.gitignore, .env.example, directory structure, file relocation) — COMPLETE
- [x] 01-02: Notebook v2 scaffolding (§0 setup + §1 cache layer + ABS smoke test) — COMPLETE

**Success criteria:**
1. Notebook executes end-to-end via Restart & Run All in Colab with no manual intervention, and also runs locally on Windows with environment auto-detected.
2. `GOOGLE_PLACES_KEY` loads from Colab `userdata` or local `.env`; no keys appear in git; `.env.example` and `.gitignore` are present.
3. All ABS and Google API responses are cached to `data/cache/` with deterministic keys; a second run completes offline/keyless at $0.
4. A single parameters cell holds every numeric assumption (site, radii, financial constants) with citation comments — no numeric literal appears outside it.

**Dependencies:** None (foundation phase)

**Research flag:** No — well-established patterns, fully specified in ARCHITECTURE.md with code examples.

---

## Phase 2 — Catchment & Demographics

**Goal:** Build the geospatial catchment (exact-address geocoding, 1/3/5 km buffers in EPSG:7855, area-apportioned population) and the census demographic profile (ABS Data API G01/G02 for POA 3067 + 9 peers, with local fallback), fixing v1's whole-postcode summing flaw and degree-based buffer errors.

**Requirements mapped:** GEO-01, GEO-02, GEO-03, GEO-04, DEMO-01, DEMO-02, DEMO-03, DEMO-04

**Plan progress:**
- [x] 02-01: Catchment (geocode + buffers + SA1 apportionment + v1-vs-v2 comparison + maps) — COMPLETE
- [ ] 02-02: Demographics (ABS G01/G02/G04 + ERP scaling + peer benchmarking + charts) — PLANNED (Wave 2, depends on 02-01)

**Cross-cutting constraints:**
- All HTTP through the Phase 1 `CachedSession` (no bare `requests.get`) — appears in both plans
- No numeric literal outside `BASE_ASSUMPTIONS` except unit conversions (PIPE-05) — appears in both plans
- v1-flaw eradication maintained (no `/content/drive`, no `drive.mount`, no degree-based buffering) — appears in both plans

**Success criteria:**
1. Site is geocoded from the exact address (cached); 1/3/5 km buffers are built in EPSG:7855 with a sanity assertion (3 km buffer ≈ 28.3 km²).
2. Catchment population is computed by area-apportioning POA populations across buffer intersections (not whole-postcode summing); a v1-vs-v2 comparison is shown.
3. ABS Data API returns G01/G02 variables for POA 3067 + 9 peer postcodes (cached), with local GCP fallback emitting the same schema and a printed warning.
4. A peer-postcode benchmarking table and comparison charts (population, income, 65+ share) are produced; census staleness is addressed with ERP scaling and a caveat.

**Dependencies:** Phase 1 (caching layer, parameters cell, dual-environment bootstrap)

**Research flag:** Yes — exact `C21_G01_POA`/`C21_G02_POA` dataKey dimension order was NOT verified live; must introspect `/rest/datastructure/ABS/{id}` at runtime. Confirm `C21_G04_POA` (age by sex) exists via the dataflow list.

---

## Phase 3 — Demand & Competitors

**Goal:** Quantify both sides of the market: age-adjusted GP consultation demand from SA3-level MBS data (SA3 20604 Yarra), and the existing supply landscape via Google Places (New) competitor mapping with dedupe and brand classification — converging on the required market share a 5-FTE-GP clinic must capture.

**Requirements mapped:** DEMAND-01, DEMAND-02, DEMAND-03, DEMAND-04, COMP-01, COMP-02, COMP-03

**Success criteria:**
1. SA3 20604 (Yarra) MBS GP attendance data is loaded (assertion: SA3 code 20604 present); state-level fallback carries an explicit warning.
2. Annual catchment consult demand is computed per ring via age-band attendance rates × catchment age structure (transparent arithmetic, no ML).
3. Competitors (GP clinics, medical centres, pharmacies, allied health) are fetched via Places API (New) with per-type/per-ring splitting and place_id dedupe to beat the 20-result cap; brand classification and clinic-vs-practitioner filtering applied.
4. Required market share for a 5-FTE-GP clinic (~25-30k consults/yr) is computed and stated in plain language, with GP-per-1,000 benchmarked against the VIC average (~117 FTE GPs/100k).

**Dependencies:** Phase 2 (geocoded site, catchment buffers, area-apportioned population, age profile)

**Research flag:** Yes — exact current download URL/format of the "Medicare quarterly statistics – SA3 Summary" product and AIHW supplement needs verification at build time; age-band attendance rates need a specific citable vintage.

---

## Phase 4 — Clinic Financial Model

**Goal:** Build the core standalone clinic P&L as a pure function of the parameters dict — mixed-billing revenue (service-fee model, not gross billings), full cost lines, fit-out capex, monthly ramp-up curve — producing peak capital requirement and months-to-breakeven as headline outputs.

**Requirements mapped:** FIN-01, FIN-02, FIN-03

**Success criteria:**
1. `clinic_pnl(params) -> dict` computes clinic revenue with an explicit service-fee % row (practice retains 30-35% of GP billings, not gross billings), mixed billing 70% bulk / 30% private, MBS item 23 rebate $43.90.
2. Cost model includes rent (~$100k/yr, flagged sensitivity), nursing/reception/manager wages, insurance, consumables, admin, and allied health contribution.
3. Fit-out capex ($1,200-$2,200/sqm) and monthly ramp-up cash flow are modelled; outputs include peak capital requirement and months to breakeven as headline numbers.

**Dependencies:** Phase 3 (required market share → consult volume → revenue; competitor context for supply assumptions)

**Research flag:** Yes — fit-out $/sqm, private-fee levels, and service-fee % are MEDIUM-confidence ranges that vary by practice; every value needs a source + date in the assumptions register; BBPIP mechanics (post-Nov-2025) should be re-verified against current DoH factsheets.

---

## Phase 5 — Scenarios & Executive Report

**Goal:** Run base/optimistic/pessimistic scenarios and sensitivity analysis over the pure-function P&L, quantify pharmacy synergy only as secondary upside after the standalone verdict, assemble the cited assumptions register, and export the executive PDF report with go/no-go recommendation.

**Requirements mapped:** FIN-04, FIN-05, FIN-06, FIN-07, REP-01, REP-02, REP-03, REP-04

**Success criteria:**
1. Base/optimistic/pessimistic scenario table is produced as parameter-override dicts over the same P&L function, including a 70/30-mixed vs 100%-BB+BBPIP billing-model comparison side-by-side.
2. A tornado sensitivity chart ranks which assumptions move annual EBITDA most; pharmacy synergy is quantified only after the standalone verdict, presented as non-load-bearing secondary upside.
3. An assumptions register lists every constant with value, source citation, and confidence level; all data sources are cited inline with access dates.
4. Executive report is exported to PDF (jinja2 + weasyprint) with key metrics, maps, scenario table, and an explicit go/no-go recommendation; runnable in Colab.

**Dependencies:** Phase 4 (base-case P&L pure function); upstream figures from Phases 2-3 (maps, demographics, competitor inventory)

**Research flag:** No — jinja2 + weasyprint is a known path; only risk is Windows GTK (fallback: Colab-only PDF, already decided).

---

## Coverage Matrix

| REQ-ID | Phase | REQ-ID | Phase | REQ-ID | Phase | REQ-ID | Phase |
|--------|-------|--------|-------|--------|-------|--------|-------|
| PIPE-01 | 1 | GEO-01 | 2 | DEMO-01 | 2 | DEMAND-01 | 3 |
| PIPE-02 | 1 | GEO-02 | 2 | DEMO-02 | 2 | DEMAND-02 | 3 |
| PIPE-03 | 1 | GEO-03 | 2 | DEMO-03 | 2 | DEMAND-03 | 3 |
| PIPE-04 | 1 | GEO-04 | 2 | DEMO-04 | 2 | DEMAND-04 | 3 |
| PIPE-05 | 1 | COMP-01 | 3 | FIN-01 | 4 | REP-01 | 5 |
| PIPE-06 | 1 | COMP-02 | 3 | FIN-02 | 4 | REP-02 | 5 |
| | | COMP-03 | 3 | FIN-03 | 4 | REP-03 | 5 |
| | | | | FIN-04 | 5 | REP-04 | 5 |
| | | | | FIN-05 | 5 | | |
| | | | | FIN-06 | 5 | | |
| | | | | FIN-07 | 5 | | |

**Coverage check:** 32/32 v1 requirements mapped. Every REQ-ID appears exactly once.

| Phase | Count |
|-------|-------|
| 1 | 6 |
| 2 | 8 |
| 3 | 7 |
| 4 | 3 |
| 5 | 8 |
| **Total** | **32** |

---

## Ordering Rationale

The phase order follows the dependency graph in the research synthesis and ARCHITECTURE.md's §-flow exactly: cache/config → geocode/buffers + census → demand rates + competitors → P&L → scenarios/report.

- **Caching first (Phase 1)** makes every later phase free to re-run and is itself a reproducibility differentiator.
- **Catchment & demographics together (Phase 2)** groups the two geospatial-data phases that share the POA geometry and feed both demand and competitor work.
- **Demand & competitors together (Phase 3)** converges on the required-market-share headline metric, which needs both demand rates (from Phase 2 age profile) and supply capacity (from Places queries using the Phase 2 site point).
- **Financial model alone (Phase 4)** is the pure-function P&L — the single most important architectural dependency; scenarios are cheap only if this is a function of a config dict.
- **Scenarios & report (Phase 5)** consumes the P&L function and every upstream figure; pharmacy synergy is order-gated after the standalone verdict by design.

Teaching commentary is written as-you-go in every phase, not retrofitted.

---
*Last updated: 2026-07-05 — plan 02-01 complete, Phase 2 Wave 1 delivered*
