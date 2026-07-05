# Project Research Summary

**Project:** Johnston St Medical Clinic Feasibility Study
**Domain:** Australian healthcare location analytics (geospatial catchment + census + MBS demand + financial modelling), delivered as a free-Colab notebook (`Johnston_St_v2.ipynb`) + executive PDF
**Researched:** 2026-07-05
**Confidence:** HIGH

## Executive Summary

This is a professional-grade site feasibility study answering one question: can a 5-FTE-GP clinic at 292-296 Johnston St, Abbotsford VIC 3067 be profitable on its own (not as a script-driver for the co-located Priceline pharmacy)? Experts build these as a consistent skeleton — executive summary with explicit go/no-go, catchment definition and demographics, competitor/supply analysis, demand modelling, parameterised P&L with breakeven, and scenarios/sensitivity — all with a cited, dated assumptions register. The deliverable is judged against health-planning consultancy reports (e.g. the cohealth Collingwood catchment study), and our unique edge is a cached, reproducible, fully-cited pipeline.

The recommended approach is a **linear notebook pipeline with a cached I/O boundary**: everything preinstalled in Colab (geopandas 1.1.x, shapely 2.1, pyproj, folium, pandas, matplotlib) plus a small pip layer (requests-cache, contextily, weasyprint, python-dotenv). All external fetches (ABS Data API, Google Places API (New), geocoding) go through a disk cache so re-runs are free, deterministic, and demonstrable offline — this is both a cost control (Places is US$32/1k requests) and the reproducibility keystone. All metre-based geometry happens in EPSG:7855 (GDA2020 / MGA zone 55); catchment population is **area-apportioned** from POA/SA1 geometry, fixing v1's headline flaw of summing whole postcodes.

The key risks are (1) repeating v1's analytical flaws (degree-based buffers, whole-postcode population sums, centroid-based catchments, ML on 3–10 rows); (2) silently wrong external data (ABS positional dataKeys returning empty-200s, Places' 20-per-query cap silently truncating competitor counts, state Medicare files carrying zero local signal); and (3) financial-model errors that flip the verdict (confusing GP gross billings with practice revenue — a ~3× overstatement — ignoring ramp-up, underestimating fit-out capex at $1,200–$2,200+/sqm, and using pre-Nov-2025 MBS billing economics). Every one of these has a concrete mitigation mapped to a specific phase below.

**One correction to PROJECT.md:** the ABS API base URL listed there (`https://api.data.abs.gov.au`) was **retired 29 Nov 2024**. The correct base is **`https://data.api.abs.gov.au`** (e.g. `https://data.api.abs.gov.au/rest/data/{dataflowId}/{dataKey}?format=csvfilewithlabels`). The old URL currently redirects but is not guaranteed to. PROJECT.md should be updated at the next transition.

## Key Findings

### Recommended Stack

Python 3.12 on the current Colab runtime, using Colab's preinstalled geospatial set unchanged (geopandas 1.1.3 / shapely 2.1.2 / pyproj 3.7 / folium 0.20 / pandas 2.2 / matplotlib 3.10) — **zero pip installs for the core**. One small install cell adds `requests-cache`, `contextily`, `weasyprint`, `python-dotenv` (and optionally `numpy-financial`). Dual-environment config detects Colab vs local Windows, loads `GOOGLE_PLACES_KEY` from Colab Secrets or `.env`, and resolves all paths via `pathlib` — no hardcoded `/content/drive/...` outside one config cell (a v1 flaw). Full details in STACK.md.

**Core technologies:**
- **geopandas 1.1.x + shapely 2.x + pyproj (EPSG:7855)**: buffers, overlay intersection, area apportionment — the standard, preinstalled, and metre-correct once reprojected
- **ABS Data API via raw `requests` + `format=csvfilewithlabels`**: census G01/G02 for POA 3067 + 9 peers; no SDMX parsing needed; dataflows `C21_G01_POA` / `C21_G02_POA` confirmed live; **avoid `pandasdmx` (unmaintained)**; local GCP DataPack as first-class fallback
- **Google Places API (New)** — `POST places:searchNearby` with a minimal field mask: the legacy Places API and the `googlemaps` PyPI client are closed/discouraged; Nearby Search (New) has **no pagination, max 20 results** — design around it (per-type, per-radius queries, subdivide on saturation, dedupe on `place.id`)
- **requests-cache (filesystem backend, GET+POST)**: transparent on-disk caching of all API calls; committed ABS caches make the notebook re-runnable with zero keys
- **jinja2 + weasyprint**: executive PDF built as a separate templated HTML→PDF artifact (not a notebook export); folium is interactive-only — all PDF figures are matplotlib + contextily static maps

### Expected Features

FEATURES.md benchmarks against professional feasibility reports and verifies current Australian metrics (item 23 rebate $43.90 from 1 Jul 2025; ~6.8–7 GP attendances/capita; 113 FTE GPs/100k national; 8.4 PBS scripts/capita; practice keeps ~30–35% of billings).

**Must have (table stakes):**
- Executive summary + explicit go/no-go recommendation with headline numbers
- Demographic catchment profile (ABS G01/G02, 2021 vintage caveat) + catchment maps (1/3/5 km rings, competitors)
- Competitor inventory with counts/classification + provider-to-population ratios vs benchmarks
- Demand model (attendances per capita × catchment population vs existing capacity → required market share)
- Full parameterised clinic P&L + breakeven + fit-out capital + ramp-up curve
- Base/optimistic/pessimistic scenarios + tornado sensitivity
- Cited, dated assumptions register; executive PDF export

**Should have (competitive differentiators):**
- Area-apportioned catchment population (fixes v1; most cheap reports get this wrong)
- Age-adjusted demand model (Abbotsford skews young-adult → more conservative, more credible)
- SA3 20604 (Yarra) MBS utilisation instead of state files
- Cached reproducible pipeline; explicit market-share framing; teaching commentary throughout
- Pharmacy synergy quantified only as **secondary** upside, after the standalone verdict (order-gated by design)

**Defer (v1.x / v2+):**
- Monte Carlo confidence intervals on breakeven — after scenario machinery is stable
- Peer-postcode benchmarking table — after Places caching is proven
- SA1-level apportionment upgrade — if ABS API pulls prove reliable
- Drive-time isochrones, interactive dashboard, pharmacy retail P&L — explicitly out of scope / anti-features

**Anti-features to refuse:** ML demand models on <30 rows (v1's Random Forest), exploratory clustering as "analysis", uncited rules of thumb, web-scraped booking data, live-recompute-everything.

### Architecture Approach

A single notebook structured as a strictly-downward linear pipeline (no section reads state produced later — v1's `s_lat`/`s_lon` used-before-definition bug is exactly this violation), with a repo layout of `data/cache/` (committed JSON API caches), `data/local/` (fallback assets), and `outputs/` (maps, report.md, PDF). Five patterns carry the design: (1) **cached fetch boundary** — every API call goes through one `cached_fetch()` helper; (2) **single PARAMS cell** — every tunable assumption in one dict with inline citations, no numeric literals downstream; (3) **pure-function P&L** — `clinic_pnl(params) -> dict`, making scenarios/sensitivity ~10 lines each; (4) **dual-environment bootstrap** — Colab Secrets vs `.env`, graceful degradation to cache-only if no key; (5) **report-metrics accumulator** — sections deposit headline numbers into a `report{}` dict rendered to markdown → HTML → PDF, so the report can never drift from the analysis.

**Major components (notebook sections):**
1. **§0 Setup/Config/PARAMS** — installs, env detection, all assumptions in one cell
2. **§1 Data acquisition layer** — geocode, ABS client (+ local fallback), Places client, MBS SA3 loader; all cached
3. **§2 Geospatial catchment** — site point → 1/3/5 km buffers in EPSG:7855, area-apportionment weights
4. **§3 Demographics** — catchment population/age/income by ring; peer comparison
5. **§4 Competitors** — dedupe, classify, per-ring counts, maps
6. **§5 Demand model** — age-band consult rates × catchment profile vs GP capacity → required market share
7. **§6 Financial model** — pure-function P&L, base case
8. **§7 Scenarios & sensitivity** — param-override dicts, tornado chart
9. **§8 Report** — markdown assembly → weasyprint PDF

### Critical Pitfalls

Top 5 of 12+ documented in PITFALLS.md (each mapped to a phase):

1. **CRS confusion (buffers in degrees)** — all metric ops in EPSG:7855, all display in EPSG:4326; one `to_metric()`/`to_display()` helper pair; assert 3 km buffer area ≈ 28.27 km² before anything downstream
2. **Whole-postcode population summing (v1's core flaw)** — area-weighted apportionment `pop × (∩area / POA area)` in EPSG:7855; show v2 vs v1 numbers side-by-side as the teaching moment; sanity range: 3 km inner-Melbourne catchment ≈ 80–110k
3. **Places truncation + inflated competitor counts** — Nearby Search (New) caps at 20 with no pagination: treat saturation as truncation and subdivide; then dedupe by `place_id` + name/address, classify with keyword rules + manual review (raw "doctor" counts overstate GP competition 2–5×)
4. **GP gross billings ≠ practice revenue** — practice revenue is the service fee (~30–35% of billings), not the $2.75M gross; getting this wrong overstates revenue ~3× and makes any site look profitable; structure the P&L with an explicit service-fee % row
5. **Stale MBS economics + no ramp/capex realism** — Nov 2023 and Nov 2025 bulk-billing changes (tripled BBI, BBPIP 12.5%) structurally changed GP revenue: date-stamp every item value, model both 70/30 mixed and 100%-BB+BBPIP strategies; model monthly ramp (books fill over 12–24 months) and cited fit-out $/sqm ranges ($350k–$700k+ plausible) with peak cash requirement as a headline output

Also critical: ABS API positional dataKeys return **empty data with HTTP 200** when dimension order is wrong — introspect the datastructure at runtime, never hardcode; and use the **SA3 Summary** Medicare product (SA3 20604 must appear in the loaded dataframe), never the state/MMM file v1 used.

## Implications for Roadmap

The four documents agree on dependency order. Note on reconciliation: ARCHITECTURE.md's section numbering (§0–§8) places competitors (§4) before the demand model (§5), while the phase list below places MBS/demand data work before competitor mapping. These are compatible: the MBS phase acquires and validates the *demand-rate inputs* (SA3 utilisation, age-band rates), but the final market-share calculation is completed only after competitor capacity is known. The required market-share headline metric therefore lands at the end of the competitors phase / start of the financial phase, exactly as FEATURES.md's dependency graph specifies (`market share ──requires──> demand model + competitor capacity`).

### Phase 1: Scaffolding — Config, Caching, Environment
**Rationale:** Every subsequent feature touches an external API; the cache layer must exist before the first bulk fetch (Pitfall 10 — Places cost blowout), and the dual-env bootstrap prevents v1's hardcoded-path flaws.
**Delivers:** Repo layout (`data/cache/`, `data/local/`, `outputs/`), §0 setup + PARAMS cell, `cached_fetch()` helper, Colab/Windows key handling, `.gitignore`/`.env.example`.
**Addresses:** Caching + config + key handling (P1, HIGH value / LOW cost per FEATURES.md).
**Avoids:** API cost blowout; hardcoded Drive paths; out-of-order execution.

### Phase 2: Geospatial Catchment
**Rationale:** The site point and buffers are the root of the dependency graph ("start here" in FEATURES.md); v1's three geometry flaws all live here.
**Delivers:** Geocoded exact address (cached, visually verified), 1/3/5 km buffers in EPSG:7855, POA geometry intersection + area-apportionment weights, base map.
**Uses:** geopandas/shapely/pyproj (preinstalled), `to_metric()`/`to_display()` convention.
**Avoids:** Pitfalls 1–3 (CRS confusion, whole-postcode summing, centroid-based catchment). Include the buffer-area assertion cell and the v1-vs-v2 population comparison.

### Phase 3: Census Demographics (ABS Data API)
**Rationale:** Demand modelling is meaningless without the apportioned age/income profile; the ABS API has real discovery friction to absorb early.
**Delivers:** G01/G02 pulls for POA 3067 + 9 peers via **`https://data.api.abs.gov.au/rest/...`** (corrected base URL — the old `api.data.abs.gov.au` in PROJECT.md was retired Nov 2024), `format=csvfilewithlabels`, cached; local GCP DataPack fallback emitting the *same tidy schema* with a printed warning; catchment demographic profile by ring.
**Uses:** raw requests + requests-cache; runtime datastructure introspection for dataKey dimension order.
**Avoids:** Pitfall 4 (silent empty-200s, 30 s/10 MB gateway limits, Beta-service flakiness — verify the notebook runs cache-only/offline).

### Phase 4: MBS Demand Data & Age-Adjusted Demand Model
**Rationale:** Demand rates are independent of competitors and depend on Phase 3's age profile; getting the geography strategy right (POA census vs SA3 rates) needs deciding before any merges.
**Delivers:** SA3 20604 (Yarra) utilisation from the Medicare **SA3 Summary** product (fallback to state benchmark with loud warning), age-band consult rates × catchment age structure → annual catchment consult demand.
**Addresses:** Age-adjusted demand model + SA3-level data (differentiators).
**Avoids:** Pitfalls 5–6 (POA/SA3 geography mismatch — use SA3 data only as rates, never counts; state files masquerading as local signal — assert SA3 code 20604 present).

### Phase 5: Competitor Landscape
**Rationale:** Needs the geocoded site (Phase 2) and completes the supply side, enabling the required-market-share headline metric.
**Delivers:** Places (New) Nearby Search per-type/per-radius with subdivision on 20-result saturation, dedupe + classification (corporate GP / independent / pharmacy / allied / exclude), per-ring counts, provider-to-population ratios vs the ~110–113/100k benchmark, competitor maps, persisted `competitors.geojson`, **required market share** computed.
**Uses:** Places API (New) POST + field mask via cached requests-cache session (POST caching enabled).
**Avoids:** Pitfalls 8–10 (truncation, duplicates/miscategorisation with a manual-review checkpoint, uncached spend).

### Phase 6: Financial Model
**Rationale:** The point of the study; consumes the market-share/volume outputs and the PARAMS cell built in Phase 1.
**Delivers:** Pure-function `clinic_pnl(params)` — billings top line, explicit service-fee % row, cost lines, EBIT; monthly ramp curve (GP recruitment + book fill), cited fit-out $/sqm × floor area, time-to-breakeven and peak cash requirement as headline outputs.
**Implements:** Pattern 3 (pure-function P&L) — the single most important architectural dependency (scenarios are cheap only if this is a function of a config dict).
**Avoids:** Pitfalls 7, 11, 12 (stale MBS values — date-stamp everything and model both billing strategies incl. BBPIP; billings ≠ revenue; steady-state fantasy).

### Phase 7: Scenarios, Sensitivity & Executive Report
**Rationale:** Scenarios are override-dicts over the Phase 6 function; the report needs every upstream number and figure.
**Delivers:** Base/optimistic/pessimistic table (incl. 70/30-mixed vs 100%-BB+BBPIP comparison), one-way tornado sensitivity, assumptions register, pharmacy-synergy upside module (computed **after** the standalone verdict, clearly non-load-bearing), `report{}` accumulator → jinja2/markdown → weasyprint PDF with static matplotlib+contextily maps, executive summary + go/no-go.
**Addresses:** Scenarios, sensitivity, assumptions register, PDF export, pharmacy synergy (order-gated).

### Phase Ordering Rationale

- Order follows the dependency graph in FEATURES.md and the §-flow in ARCHITECTURE.md exactly: cache/config → geocode/buffers → census → demand rates → competitors → P&L → scenarios/report. "Run all" must always work top-to-bottom — the single property v1 lacked.
- Caching first makes every later phase free to re-run and is itself a differentiator (reproducibility for graders/investors).
- The demand model spans Phases 4–5 deliberately: rates before supply, market share once both exist.
- Pharmacy synergy and Monte Carlo CIs are explicitly sequenced after their gates (standalone verdict; stable scenario machinery) — pulling them earlier violates the Core Value or wastes effort.
- Teaching commentary is written as-you-go in every phase, not retrofitted.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (Census/ABS):** exact `C21_*` dataKey dimension order was NOT verified live — must introspect `/rest/datastructure/ABS/{id}?references=codelist` at runtime; confirm `C21_G04_POA` (age by sex) exists via the dataflow list.
- **Phase 4 (MBS):** exact current download URL/format of the "Medicare quarterly statistics – SA3 Summary" product and AIHW supplement needs verification at build time; age-band attendance rates need a specific citable vintage.
- **Phase 6 (Financial):** fit-out $/sqm, private-fee levels, and service-fee % are MEDIUM-confidence ranges that vary by practice — every value needs a source + date in the assumptions register, and BBPIP mechanics (post-Nov-2025) should be re-verified against current DoH factsheets.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Scaffolding):** well-established patterns, fully specified in ARCHITECTURE.md with code examples.
- **Phase 2 (Geospatial):** textbook geopandas overlay/apportionment; conventions and assertions already defined.
- **Phase 5 (Competitors):** Places (New) request/response shape, pricing, and caps verified HIGH-confidence in STACK.md.
- **Phase 7 (Report):** jinja2 + weasyprint is a known path; only risk is Windows GTK (fallback: Colab-only PDF, already decided).

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Colab preinstalled versions verified against googlecolab/backend-info; ABS URL migration and Places (New) pricing/caps verified against official docs. MEDIUM only on exact ABS dataKey dimension order (runtime introspection required). |
| Features | HIGH | Report skeleton and Australian benchmarks verified against MBS Online, AIHW, RACGP, PBS, Productivity Commission. MEDIUM on private-fee/fit-out cost ranges (market-variable). |
| Architecture | HIGH | Patterns are standard for reproducible analytics notebooks; specifics validated directly against the v1 prototype's failure modes. |
| Pitfalls | HIGH | Web-verified (MBS changes, fit-out costs, API limits) plus direct audit of v1 code (line-level flaws identified). |

**Overall confidence:** HIGH

### Gaps to Address

- **ABS dataKey dimension order (`C21_G01_POA` etc.):** not verified live — Phase 3 must GET the datastructure first and print dimension order; never hardcode from research docs.
- **MBS SA3 Summary product URL/format:** verify current release at Phase 4 build time; the loaded dataframe must contain SA3 code 20604 as an assertion.
- **Corrected ABS base URL vs PROJECT.md:** PROJECT.md still lists retired `https://api.data.abs.gov.au` — update to `https://data.api.abs.gov.au` at the next PROJECT.md revision.
- **weasyprint on local Windows (GTK):** if install is painful, PDF generation is Colab-only with local HTML output — acceptable fallback, decide in Phase 7.
- **Financial benchmark vintages (service-fee %, private fee, fit-out $/sqm, BBPIP details):** carry as cited ranges with sensitivity tests, never point estimates; re-verify BBPIP factsheets during Phase 6.
- **Document-date inconsistency:** PITFALLS.md is dated 2026-03-02 vs 2026-07-05 for the others — immaterial to content, but MBS/BBPIP facts in PITFALLS.md should be re-checked for anything newer at Phase 6.

## Sources

### Primary (HIGH confidence)
- https://github.com/googlecolab/backend-info — Colab runtime pip-freeze (Python 3.12, geopandas 1.1.3, shapely 2.1.2, folium 0.20.0)
- https://www.abs.gov.au/statistics/application-programming-interfaces-apis/data-api-user-guide — base URL migration (29 Nov 2024), `/rest/data/{flow}/{key}?format=csvfilewithlabels`, dataflow/datastructure endpoints
- https://developers.google.com/maps/billing-and-pricing/pricing (+ march-2025 pages) — Places (New) Pro $32/1k, 5,000 free/month, legacy closure; migrate-nearby doc — POST, mandatory FieldMask, no pagetoken, max 20
- MBS Online (www9.health.gov.au/mbs) — item 23 $43.90 from 1 Jul 2025; Level C item 36 $84.90
- AIHW *Medicare funding of GP services over time* — ~6.8 attendances/capita (2022); Productivity Commission RoGS 2026; RACGP Health of the Nation 2025 — 113 FTE GPs/100k
- PBS Expenditure & Prescriptions Report 2023-24 — 8.4 subsidised scripts/capita
- Direct audit of `johnston_st_v1.py` / `Johnston_St_v1.ipynb` — line-level identification of v1 flaws

### Secondary (MEDIUM confidence)
- https://github.com/Bigred97/abs-mcp — confirms `C21_G01_POA`/`C21_G02_POA` dataflow IDs (third-party, consistent with ABS naming)
- RACGP mixed-billing guide + Alecto 2025 survey — GP service-fee splits (65–70% retained by GPs), $95 private-fee scenario
- Melbourne medical fit-out cost guides — $1,200–$2,200+/sqm ranges (market-variable)

### Tertiary (LOW confidence)
- Inner-Melbourne private-fee observation (~$90–110 Level B) — flag as assumption, sensitivity-test
- Exact `C21_*` dataKey dimension order — inferred, must be introspected at runtime

---
*Research completed: 2026-07-05*
*Ready for roadmap: yes*
