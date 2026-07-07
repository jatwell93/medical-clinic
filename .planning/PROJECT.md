# Johnston St Medical Clinic Feasibility Study

## What This Is

A reusable, investor-grade medical-clinic feasibility **tool**, delivered as a Colab notebook that accepts any Victorian street address via a site-input form and produces a standalone-profitability verdict plus an executive PDF report. Built by and for a business analytics student learning healthcare location analytics. v1.0 shipped a single-site study (Abbotsford, PR #1, merged 2026-07-06); v2.0 generalises it into a parameterised, multi-site tool with Abbotsford as the default config.

## Core Value

Answer, with defensible data and transparent assumptions, one question: **can a clinic be profitable on its own at a user-specified site** — for any Victorian address the user enters, not just the original Abbotsford site.

## Current State

**Shipped:** v1.0 (2026-07-06) — all 32 requirements satisfied, 36/36 validator checks pass.

- `Johnston_St_v2.ipynb` — 88 cells (§0-§8), dual-environment (Colab/Windows), cached API boundary ($0 re-runs)
- Executive report generator — Jinja2 HTML template (8 sections) + weasyprint PDF (Colab-only)
- `scripts/validate_v2_notebook.py` — 36 structural checks, all PASS
- 5 idempotent generator scripts (one per phase) — re-runnable, byte-stable output

**Deferred to Colab runtime:** PNG figure generation, PDF generation, assumptions register population, end-to-end Restart & Run All, HTML visual fidelity (requires Colab + API keys + matplotlib/weasyprint/GTK deps).

## Current Milestone: v2.0 Multi-Site Feasibility Tool

**Goal:** Generalise the v1.0 Abbotsford study into a reusable, VIC-pilot feasibility tool that any user can point at a new street address and get the same investor-grade standalone clinic profitability verdict.

**Target features:**
- Site input form (street address + state + postcode + clinic FTE count + optional peer postcodes) replacing v1.0's hardcoded Abbotsford config
- ABS Data API auto-fetches the right POA/SA2/SA3 census tables for whatever VIC site is entered (no manual downloads; guide becomes a "how it works" explainer)
- Geocoding of arbitrary VIC street addresses (Google Geocoding API, cached)
- SA3 auto-derivation from the geocoded point (so MBS/Medicare utilisation data is fetched for the correct SA3, not hardcoded 20604 Yarra)
- EPSG:7899 (GDA2020 / Vicgrid) adopted for state-wide VIC coverage — replaces v1.0's EPSG:7855 (MGA zone 55) which only covers 144°E–150°E and silently distorts western VIC (Mildura, Nhill, Ouyen — zone 54). Vicgrid is the VIC government's own state-wide Lambert Conformal CRS; sub-meter distortion vs MGA at catchment scale.
- Clinic standalone profitability model reused from v1.0 (`clinic_pnl(a)` pure function), driven by the site form's FTE count
- Pharmacy synergy section **dropped** for v2.0 — clinic verdict is purely standalone
- Peer benchmarking via user-supplied peer postcodes (optional; skipped if not provided)
- Single report per run, named after the site; batch/comparison mode deferred to v2.1
- Abbotsford (292-296 Johnston St) ships as the default site config, so v2.0 out-of-the-box reproduces the v1.0 study (minus pharmacy synergy)

**Key context:**
- Major version bump (v1.0 → v2.0) — product's core use case changes from single-site study to reusable tool
- Phase numbering continues from v1.0 (new phases start at 6)
- VIC-only pilot scope — other states/territories deferred to v2.1 (would require MGA zone-aware reprojection)
- ABS Data API is free + already wired in v1.0; the "guide on which files to download" reframes as a "how the tool sources data" explainer, not a manual download checklist
- Pharmacy synergy removal is a deliberate scope reduction — the tool's Core Value (clinic standalone verdict) becomes cleaner
- v1.0 notebook preserved as reference (same pattern as v1.0 preserving v1 notebook)

## Requirements

### Validated

- ✓ v1 notebook exists as a working prototype (reference preserved) — existing
- ✓ Local data assets on hand (GCP POA census pack, shapefiles, SA3 correspondence, Medicare stats, cohealth report, floor plan) — existing
- ✓ `Johnston_St_v2.ipynb` built from scratch (v1 preserved as reference) — v1.0
- ✓ Runs in Colab as primary environment, paths/config also work on Windows — v1.0
- ✓ `.env` / Colab userdata handling for `GOOGLE_PLACES_KEY` (no keys committed) — v1.0
- ✓ Exact-address geocoding and 1/3/5 km radial catchments with area-apportioned population — v1.0 (fixes v1 whole-postcode summing flaw)
- ✓ ABS Data API as primary census source (G01/G02/G04), local GCP fallback, responses cached — v1.0
- ✓ SA3-level MBS/Medicare utilisation data (SA3 20604 Yarra) with state fallback warning — v1.0
- ✓ Competitor mapping via Google Places (New) with saturation subdivision, fuzzy dedupe, brand classification — v1.0
- ✓ Age-adjusted GP demand model: catchment consult demand vs existing GP capacity → required market share — v1.0 (transparent arithmetic, no ML)
- ✓ Full clinic P&L: mixed billing (70% bulk / 30% private), service-fee revenue model, full cost lines — v1.0
- ✓ Fit-out capital and time-to-breakeven modelled prominently (36-month ramp, peak capital headline) — v1.0
- ✓ Base / optimistic / pessimistic scenario analysis with tornado sensitivity — v1.0
- ✓ Pharmacy synergy quantified only as secondary upside after standalone verdict — v1.0 (order-gated, never rescues unprofitable clinic)
- ✓ Executive summary: maps, key metrics, go/no-go recommendation; exported as PDF — v1.0
- ✓ Every dataset cited (ABS, MBS, Google) with teaching-style commentary throughout — v1.0

### Active

(Defined for v2.0 via `/gsd-new-milestone` — see REQUIREMENTS.md.)

### Out of Scope

- Pharmacy retail P&L modelling — pharmacy is a separate business; this study only validates it doesn't need to subsidise the clinic
- Pharmacy synergy quantification — dropped for v2.0; clinic verdict is purely standalone. Candidate for v2.1+ reintroduction as opt-in.
- Drive-time isochrones (Distance Matrix/OSRM) — radial buffers chosen for reproducibility and zero API cost; candidate for v2.1
- Real-time PBS dispensing data by pharmacy — not publicly available at that granularity; per-capita script benchmarks used instead
- Web scraping of competitor websites/booking systems — licensed/public data only
- Heavy raster/geospatial computation — must stay feasible in free Colab
- ML demand prediction — sample sizes make it statistical theatre; transparent arithmetic instead
- Non-VIC sites (v2.0) — VIC-only pilot; other states/territories deferred to v2.1 (would require zone-aware reprojection or a national CRS like EPSG:9473 GDA2020 / Australian National Grid)
- Batch/multi-site comparison mode — deferred to v2.1; v2.0 is single-run per site
- Manual ABS file download path — ABS Data API auto-fetch is primary; manual download fallback is out of scope for v2.0 (v1.0's GCP fallback pattern is VIC-Abbotsford-specific)

## Context

- v1 notebook (`Johnston_St_v1.ipynb` / `johnston_st_v1.py`) preserved as reference/audit trail. v1's three critical flaws fixed in v2: degree-based buffers (→ EPSG:7855), whole-postcode summing (→ SA1 area-apportionment), Random Forest on 3-10 rows (→ transparent arithmetic).
- User is studying business analytics; the notebook teaches as it goes (plain-language explanations of each fix and method).
- Peer postcodes for comparison: 3067, 3066, 3121, 3068, 3070, 3078, 3079, 3101, 3122, 3123.
- Google API key available; ABS Data API is free (no key required) but rate-limited — all responses cached.
- Codebase: ~29,600 LOC across 81 files. Tech stack: Python 3.12, geopandas, shapely, pyproj, folium, pandas, matplotlib, jinja2, weasyprint, requests-cache.
- 2 PR review bugs found by sentry[bot] and fixed before merge: private_fee tornado no-op (scaled item_mix proportionally) and Path.cwd() Colab failure (In[] history lookup).

## Constraints

- **Environment**: Free Colab primary, local Windows compatible — no paid compute, no huge rasters
- **Budget**: Limited startup capital — fit-out cost and time-to-breakeven must be first-class model outputs
- **Data**: Public/licensed sources only, all cited — investor credibility and legality
- **API cost**: Google Places calls cost money — cache aggressively, make re-runs free
- **Rent assumption**: ~$100k AUD/year — flagged as a key sensitivity, not a confirmed figure
- **Census vintage**: 2021 Census is ~4-5 years old — ERP scaling applied as mitigation; caveat noted

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Clinic modelled as independent profit centre | Core brief: clinic must stand alone; synergy validated only after | ✓ Good — verdict text never mentions pharmacy |
| Mixed billing 70% bulk / 30% private | Typical inner-Melbourne GP model | ✓ Good — MBS item 23 rebate $43.90, private fee ~$95 |
| Radial buffers (1/3/5 km) over isochrones | Reproducible, free, adequate for inner-urban grid | ✓ Good — EPSG:7855 reprojection fixed v1 flaw |
| ABS Data API primary, local files fallback | User preference; reproducible without large local zips | ✓ Good — G01/G02/G04 fetched, GCP fallback emits warning |
| SA3-level MBS data over state-level files | State files carry no local demand signal | ✓ Good — SA3 20604 Yarra with state fallback warning |
| Fresh v2 notebook, v1 untouched | Clean structure; v1 kept as reference/audit trail | ✓ Good — v1 preserved, v2 is 88 cells |
| Notebook + executive PDF deliverable | Investor presentation standard | ✓ Good — Jinja2 HTML + weasyprint PDF (Colab-only) |
| Verdict gate: EBITDA > 0 AND margin > 15% | Payback is context, not the gate — clinic is a long-lived asset | ✓ Good — base case clears gate |
| Binary GO/NO-GO, no CONDITIONAL tier | Investors want a clear answer | ✓ Good — flat GO with flip-conditions |
| Verdict 100% standalone, never mentions pharmacy | Core Value — clinic verdict independent of pharmacy | ✓ Good — pharmacy synergy in separate section, "NOT Load-Bearing" |
| Pharmacy synergy order-gated after standalone | Can never rescue an unprofitable clinic | ✓ Good — FIN-07 satisfied |
| Transparent arithmetic demand model, no ML | v1's Random Forest on 3-10 rows was statistically meaningless | ✓ Good — DEMAND-04 satisfied |
| Places API (New) with field masking + filesystem caching | $0 API cost on re-runs | ✓ Good — GeoJSON persistence, saturation subdivision |
| Colab-only PDF via weasyprint | GTK/pango deps apt-installable on Colab; Windows produces HTML only | ✓ Good — avoids Windows GTK runtime pain |
| clinic_pnl(a) as pure function of parameters dict | Enables cheap scenario overrides (ARCHITECTURE.md Pattern 3) | ✓ Good — all scenarios use {**BASE_ASSUMPTIONS, **overrides} |
| Service-fee % revenue model (Pitfall 11) | Practice retains 30-35% of GP billings, not gross billings | ✓ Good — guardrail in §6 |
| Jinja2 template as inline Python string | Keeps notebook self-contained — no external template file | ✓ Good — r-string handles CSS |
| All figures as base64-embedded static PNGs | Portable HTML + weasyprint rendering; no folium in PDF | ✓ Good — D-15, Pitfall 16 |
| EPSG:7899 (GDA2020/Vicgrid) over EPSG:7855 (MGA zone 55) for v2.0 | EPSG:7855 only covers 144°E–150°E; western VIC (Mildura, Nhill) is zone 54 — 7855 silently distorts there. Vicgrid covers all of VIC with sub-meter distortion vs MGA at catchment scale. | ◌ Pending — v2.0 adoption (research-verified, user-approved 2026-07-07) |
| Pharmacy synergy dropped for v2.0 | Multi-site tool's Core Value is standalone clinic verdict; pharmacy synergy was Abbotsford-specific (Priceline). Cleaner scope; candidate for v2.1 reintroduction as opt-in. | ◌ Pending — v2.0 removal |
| VIC-only pilot scope for v2.0 | Fastest path to multi-site; single CRS (Vicgrid), known SA3/MBS structure. Other states deferred to v2.1 (national CRS or zone-aware logic). | ◌ Pending — v2.0 scope |
| ABS Data API auto-fetch (no manual download guide) | API is free, already wired in v1.0, cache makes re-runs $0. Manual download fallback is Abbotsford-specific and doesn't generalise. Guide reframes as "how it works" explainer. | ◌ Pending — v2.0 data path |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---

## Phase Completion Log

- **Phase 1: Scaffolding & Data Pipeline** — complete (2026-07-05). Reproducible foundation established: dual-environment bootstrap (Colab/Windows), single `BASE_ASSUMPTIONS` parameters cell, `CachedSession` HTTP boundary with keyless ABS smoke test (SDMX-ML XML response format). All 6 PIPE requirements (PIPE-01..06) verified. 2 plans, 8 commits, 0 critical code-review findings. Note for Phase 2: ABS REST API returns SDMX-ML XML by default — use `?format=csvfilewithlabels` for actual census data fetches.
- **Phase 2: Catchment & Demographics** — complete (2026-07-05). Exact-address geocoding (cached), 1/3/5 km buffers in EPSG:7855 with 28.27 km² sanity assertion, SA1-level area-apportioned catchment population (v1 whole-postcode flaw fixed), v1-vs-v2 comparison with real `pct_overstate`. ABS Data API G01/G02/G04 for POA 3067 + 9 peers through CachedSession, GCP fallback emits empty schema + warning, ERP scaling to 2024, peer benchmarking table + 2×2 comparison charts. All 8 requirements (GEO-01..04, DEMO-01..04) verified. 3 plans (incl. 1 gap-closure), 0 critical code-review findings post-fix. 6 prior verification gaps (CR-01 XML endpoint crash, CR-02 v1-vs-v2 no-op, WR-01..04, IR-02) all closed. Deferred: Colab Restart & Run All with API keys + SA1 shapefile to confirm §3 runs end-to-end and v1-vs-v2 chart shows real overstatement.
- **Phase 3: Demand & Competitors** — complete (2026-07-06). Phase 3 data acquisition layer (Places API New client with 2×2 saturation subdivision + place_id dedupe, MBS SA3 20604 Yarra loader with state fallback warning, AIHW 4-band age-rate loader), §4 Competitor Landscape (12 corporate GP + 11 pharmacy brand classification, 21 exclude keywords, rapidfuzz fuzzy-dedupe, GeoJSON persistence, spatial-join ring assignment, folium + 3 static contextily figures, peer table benchmarked vs VIC 117 FTE GPs/100k), §5 Demand Model (ABS 5-year → AIHW 4-band aggregation, transparent arithmetic `sum(pop×rate)` replacing v1's 3-row RandomForest, two-method GP FTE capacity range, three market-share framings, plain-language interpretation with NO go/no-go verdict deferred to Phase 5). All 7 requirements (DEMAND-01..04, COMP-01..03) verified. 3 plans, 3 waves (sequential dependency chain), 2 critical + 1 warning code-review findings all fixed (CR-001 undefined `ring_pops_erp` → `v2_ring_pops_erp`, CR-002 wrong `peer_table["poa_code"]` column → `POA_CODE21`, WR-002 85+ age-band pattern mismatch). Notebook extended 36→69 cells. Validator: 29 checks pass, 0 failures, no Phase 1/2 regressions. Deferred: Colab Restart & Run All with real API key + MBS SA3 + AIHW Excel files; live Google Places saturation/dedupe against real 20-result cap; runtime sheet/column-name matching.
- **Phase 4: Clinic Financial Model** — complete (2026-07-06). `clinic_pnl(a)` pure function (ARCHITECTURE.md Pattern 3) with mixed-billing revenue (service-fee % model, Pitfall 11 guardrail), full cost lines (rent, staffing, insurance, consumables, admin, allied health), fit-out capex. `clinic_ramp_monthly(a, months=36)` with GP recruitment milestones, peak capital headline (D-12: trough + 3-month working-capital buffer), operating + payback breakeven months. matplotlib ramp chart. `report{}` accumulator initialised with 9 headline metrics for Phase 5 §8. All 3 requirements (FIN-01..03) verified. 2 plans, 0 critical code-review findings. Notebook extended 69→76 cells. Deferred: Colab Restart & Run All to confirm ramp chart generates.
- **Phase 5: Scenarios & Executive Report** — complete (2026-07-06). Base/optimistic/pessimistic scenario override dicts (5 independent levers), side-by-side P&L table (D-08), two tornado sensitivity charts (EBITDA + peak capital) with numpy zero-crossings, billing-mix sensitivity curve with BBPIP 12.5%/6.25% practice retention, pharmacy synergy as standalone arithmetic (order-gated after verdict, FIN-07), 5-column assumptions register parsed from BASE_ASSUMPTIONS citations, 8-section Jinja2 HTML template with weasyprint PDF generation, footnote-style citations [1]-[8] with access dates. Binary GO/NO-GO verdict gated on EBITDA > 0 AND margin > 15% (D-01, D-03, D-04). All 8 requirements (FIN-04..07, REP-01..04) verified. 2 plans, 0 critical code-review findings. Security audit: 5 threats, 0 open (05-SECURITY.md). Nyquist validation: 8/8 gaps filled (05-VALIDATION.md). Notebook extended 76→88 cells. Validator: 36 checks pass. 2 PR review bugs found by sentry[bot] and fixed (private_fee tornado no-op, Path.cwd() Colab failure). Deferred: Colab Restart & Run All for PNG/PDF generation, assumptions register runtime population, HTML visual fidelity.

---
*Last updated: 2026-07-07 — v2.0 milestone started (Multi-Site Feasibility Tool, VIC pilot)*
