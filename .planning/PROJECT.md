# Johnston St Medical Clinic Feasibility Study

## What This Is

A professional-grade site feasibility analysis, delivered as a Colab notebook (`Johnston_St_v2.ipynb`) plus an executive PDF report, evaluating whether 292-296 Johnston St, Abbotsford VIC 3067 can support an independently profitable medical clinic (5 FTE GPs + 1 FTE allied health) alongside a Priceline Pharmacy (beauty/cosmetics focus). Built by and for a business analytics student learning healthcare location analytics, to an investor-presentation standard.

## Core Value

Answer, with defensible data and transparent assumptions, one question: **can the clinic be profitable on its own at this site** — not as a script-driving vehicle for the pharmacy?

## Requirements

### Validated

- ✓ v1 notebook exists as a working prototype (postcode geometry, Google Places competitor counts, basic census extraction, exploratory clustering) — existing
- ✓ Local data assets on hand: 2021 GCP POA VIC census pack, POA shapefile, GCP_POA3067.xlsx, SA3 correspondence, state-level Medicare statistics, cohealth Collingwood catchment report, ground floor plan PDF — existing

### Active

- [ ] New `Johnston_St_v2.ipynb` built from scratch (v1 preserved as reference)
- [ ] Runs in Colab as primary environment, but paths/config also work locally on Windows
- [ ] `.env` / Colab userdata handling for `GOOGLE_PLACES_KEY` (no keys committed)
- [x] Exact-address geocoding and 1/3/5 km radial catchments with **area-apportioned** population (fixes v1 whole-postcode summing flaw) — Validated in Phase 2: Catchment & Demographics
- [x] ABS Data API as primary census source (G01/G02-equivalent variables for POA 3067 + peer postcodes), local GCP files as fallback, responses cached — Validated in Phase 2: Catchment & Demographics (G01/G02/G04 fetched, GCP fallback emits empty schema + warning)
- [x] SA3-level MBS/Medicare utilisation data (SA3 20604 Yarra) replacing state-level files; documented fallback to state benchmarks with warning — Validated in Phase 3: Demand & Competitors (load_mbs_sa3 with SA3 20604 filter + state fallback warning banner)
- [x] Competitor mapping via Google Places (doctors, medical centres, pharmacies, allied health) with pagination, caching, and brand classification — Validated in Phase 3: Demand & Competitors (Places API New with saturation subdivision, rapidfuzz fuzzy-dedupe, 12 corporate GP + 11 pharmacy brand classification, GeoJSON persistence)
- [x] Age-adjusted GP demand model: catchment consult demand vs existing GP capacity → market share the clinic must capture — Validated in Phase 3: Demand & Competitors (transparent arithmetic sum(pop×rate), AIHW 4-band age structure, two-method capacity range, three market-share framings, VIC 117/100k benchmark)
- [ ] Full clinic P&L: mixed billing (70% bulk / 30% private), revenue (consults, gap fees, procedures, allied health) vs costs (GP %, staff, rent ~$100k/yr, insurance, equipment, admin)
- [ ] Fit-out capital and time-to-breakeven modelled prominently (limited startup capital)
- [ ] Base / optimistic / pessimistic scenario analysis with sensitivity to key assumptions
- [ ] Pharmacy synergy quantified only as secondary upside after standalone clinic profitability is established
- [ ] Executive summary: maps, key metrics, go/no-go recommendation; exported as PDF
- [ ] Every dataset cited (ABS, MBS, PBS, Google) with clear teaching-style commentary throughout

### Out of Scope

- Pharmacy retail P&L modelling — pharmacy is a separate business; this study only validates it doesn't need to subsidise the clinic
- Drive-time isochrones (Distance Matrix/OSRM) — radial buffers chosen for reproducibility and zero API cost; can revisit later
- Real-time PBS dispensing data by pharmacy — not publicly available at that granularity; per-capita script benchmarks used instead
- Web scraping of competitor websites/booking systems — licensed/public data only
- Heavy raster/geospatial computation — must stay feasible in free Colab

## Context

- v1 notebook (`Johnston_St_v1.ipynb` / `johnston_st_v1.py`) is a Colab-generated prototype with known flaws: hardcoded Drive paths, `s_lat`/`s_lon` used before definition, catchment population summed over whole postcodes intersecting the buffer, a Random Forest trained on 3-10 rows presented as a demand model, and state-level Medicare files that carry no local signal.
- User is studying business analytics; the process should teach as it goes (plain-language explanations of each fix and method).
- The cohealth Collingwood catchment report PDF is a useful benchmark for what a professional catchment report contains.
- Peer postcodes for comparison: 3067, 3066, 3121, 3068, 3070, 3078, 3079, 3101, 3122, 3123.
- Google API key available; ABS Data API (https://data.api.abs.gov.au — note: old api.data.abs.gov.au retired Nov 2024) is free, no key required, but rate-limited — cache everything.

## Constraints

- **Environment**: Free Colab primary, local Windows compatible — no paid compute, no huge rasters
- **Budget**: Limited startup capital — fit-out cost and time-to-breakeven must be first-class model outputs
- **Data**: Public/licensed sources only, all cited — investor credibility and legality
- **API cost**: Google Places calls cost money — cache aggressively, make re-runs free
- **Rent assumption**: ~$100k AUD/year — flagged as a key sensitivity, not a confirmed figure
- **Census vintage**: 2021 Census is ~4-5 years old — note as caveat; Abbotsford has grown since

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Clinic modelled as independent profit centre | Core brief: clinic must stand alone; synergy validated only after | — Pending |
| Mixed billing 70% bulk / 30% private | Typical inner-Melbourne GP model | — Pending |
| Radial buffers (1/3/5 km) over isochrones | Reproducible, free, adequate for inner-urban grid | — Pending |
| ABS Data API primary, local files fallback | User preference; reproducible without large local zips | — Pending |
| SA3-level MBS data over state-level files | State files carry no local demand signal | — Pending |
| Fresh v2 notebook, v1 untouched | Clean structure; v1 kept as reference/audit trail | — Pending |
| Notebook + executive PDF deliverable | Investor presentation standard | — Pending |

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

---
*Last updated: 2026-07-06 after Phase 3 completion*
