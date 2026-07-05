# Requirements — Johnston St Medical Clinic Feasibility Study

## v1 Requirements

### Pipeline & Environment (PIPE)

- [x] **PIPE-01**: Notebook (`Johnston_St_v2.ipynb`) runs end-to-end via Restart & Run All in Google Colab with no manual intervention
- [x] **PIPE-02**: Notebook also runs locally on Windows — environment auto-detected (`google.colab` in `sys.modules`), paths handled via `pathlib` relative to project root
- [x] **PIPE-03**: `GOOGLE_PLACES_KEY` loaded from Colab `userdata` or local `.env` (python-dotenv); no keys in git; `.env.example` and `.gitignore` provided
- [x] **PIPE-04**: All external API responses (ABS, Google geocode/places) cached to `data/cache/` with deterministic keys; caches committed to git so the notebook re-runs offline/keyless at $0
- [x] **PIPE-05**: Single parameters cell holds every assumption (site, radii, financial constants) with citation comments — no numeric literal appears outside it
- [x] **PIPE-06**: Teaching commentary in markdown throughout — each section explains what it does, why, and what flaw from v1 it fixes

### Geospatial Catchment (GEO)

- [ ] **GEO-01**: Site geocoded from the exact address (292-296 Johnston St) via Google Geocoding API, cached
- [ ] **GEO-02**: 1/3/5 km catchment buffers built from the site point in EPSG:7855 (GDA2020/MGA55); all metre-based operations in projected CRS with a sanity assertion (3 km buffer ≈ 28.3 km²)
- [ ] **GEO-03**: Catchment population computed by area-apportioning POA populations across buffer intersections (not whole-postcode summing)
- [ ] **GEO-04**: Interactive folium map (site, buffers, competitors) plus static matplotlib+contextily twin figures for the PDF

### Demographics (DEMO)

- [ ] **DEMO-01**: 2021 Census G01/G02 variables (population, age bands, median household income) fetched from ABS Data API (`data.api.abs.gov.au`, `C21_G01_POA`/`C21_G02_POA`, csvfilewithlabels) with local GCP files as documented fallback
- [ ] **DEMO-02**: Demographic profile for POA 3067 plus peer postcodes (3066, 3068, 3070, 3078, 3079, 3101, 3121, 3122, 3123) with comparison charts
- [ ] **DEMO-03**: Peer-postcode benchmarking table: demand/supply indicators (population, income, 65+ share, GP and pharmacy counts) across the peer set
- [ ] **DEMO-04**: Census staleness addressed — population scaled to current-year ABS Estimated Resident Population where available, with caveat noted

### Demand Modelling (DEMAND)

- [ ] **DEMAND-01**: SA3-level MBS GP attendance data (SA3 20604 Yarra, "Medicare quarterly statistics — SA3 summary") acquired with documented download instructions; state-level benchmark fallback carries an explicit warning
- [ ] **DEMAND-02**: Age-adjusted GP consultation demand estimated for each catchment ring (attendances per capita by age band, AIHW/MBS-cited)
- [ ] **DEMAND-03**: Demand vs capacity: existing GP capacity in catchment compared to demand; output = required market share for a 5 FTE GP clinic (~25-30k consults/yr) with plain-language interpretation
- [ ] **DEMAND-04**: No predictive ML on small samples — demand model is transparent arithmetic with cited rates

### Competitor Analysis (COMP)

- [ ] **COMP-01**: Competitors (GP clinics, medical centres, pharmacies, allied health) fetched via Places API (New) with field masks, per-type/per-ring query splitting, and place_id dedupe to beat the 20-result cap
- [ ] **COMP-02**: Pharmacy brand classification (Chemist Warehouse, Priceline, Amcal, TerryWhite, independents) and clinic-vs-individual-practitioner filtering so counts aren't inflated
- [ ] **COMP-03**: Competitor inventory table + map layers per catchment ring, with GP-per-1,000 ratio benchmarked against VIC average (~117 FTE GPs/100k)

### Financial Model (FIN)

- [ ] **FIN-01**: Clinic P&L built as a pure function of the parameters dict — mixed billing (70% bulk / 30% private), MBS item 23 rebate $43.90, private fee ~$95, practice retains 30-35% of GP billings (billings ≠ revenue)
- [ ] **FIN-02**: Cost model: rent (~$100k/yr, flagged sensitivity), nursing/reception/practice manager wages, insurance, consumables, admin, allied health contribution
- [ ] **FIN-03**: Fit-out capex ($1,200-$2,200/sqm benchmark) and monthly ramp-up cash flow modelled; outputs include peak capital requirement and months to breakeven
- [ ] **FIN-04**: Base / optimistic / pessimistic scenarios expressed as parameter override dicts on the same P&L function
- [ ] **FIN-05**: Tornado sensitivity chart ranking which assumptions move annual EBITDA most
- [ ] **FIN-06**: Billing-model comparison: 70/30 mixed vs fully bulk-billed with Nov 2025 triple BBI + BBPIP 12.5% incentive, side-by-side
- [ ] **FIN-07**: Pharmacy synergy quantified only after the standalone clinic verdict, presented as secondary upside (script flow estimate), never as a rescue for an unprofitable clinic

### Reporting (REP)

- [ ] **REP-01**: Assumptions register: every constant in one table with value, source citation, and confidence level
- [ ] **REP-02**: Executive summary with key metrics, maps, scenario table, and an explicit go/no-go recommendation
- [ ] **REP-03**: Executive report exported to PDF (jinja2 + weasyprint from accumulated metrics; static map figures) runnable in Colab
- [ ] **REP-04**: All data sources cited inline (ABS Census 2021, ABS Data API, MBS statistics, AIHW, Google Places) with access dates

## v2 Requirements

Deferred to a future milestone:

- **V2-01**: Monte Carlo simulation for confidence intervals on profitability (deferred — parameterised P&L makes this cheap to add later)
- **V2-02**: Drive-time isochrone catchments (Distance Matrix/OSRM) as robustness check on radial buffers
- **V2-03**: SA1/mesh-block level population apportionment for finer catchment accuracy

## Out of Scope

- Pharmacy retail P&L — the pharmacy is a separate business; this study only proves the clinic doesn't need to subsidise it
- Per-pharmacy PBS dispensing data — not publicly available at that granularity
- Scraping competitor websites/booking systems — licensed/public data only
- Interactive dashboards / live recompute — a notebook + PDF is the deliverable
- ML demand prediction — sample sizes make it statistical theatre; transparent arithmetic instead

## Traceability

Every v1 requirement is mapped to exactly one phase in [ROADMAP.md](./ROADMAP.md).

| REQ-ID | Phase | Phase Name |
|--------|-------|------------|
| PIPE-01 | 1 | Scaffolding & Data Pipeline |
| PIPE-02 | 1 | Scaffolding & Data Pipeline |
| PIPE-03 | 1 | Scaffolding & Data Pipeline |
| PIPE-04 | 1 | Scaffolding & Data Pipeline |
| PIPE-05 | 1 | Scaffolding & Data Pipeline |
| PIPE-06 | 1 | Scaffolding & Data Pipeline |
| GEO-01 | 2 | Catchment & Demographics |
| GEO-02 | 2 | Catchment & Demographics |
| GEO-03 | 2 | Catchment & Demographics |
| GEO-04 | 2 | Catchment & Demographics |
| DEMO-01 | 2 | Catchment & Demographics |
| DEMO-02 | 2 | Catchment & Demographics |
| DEMO-03 | 2 | Catchment & Demographics |
| DEMO-04 | 2 | Catchment & Demographics |
| DEMAND-01 | 3 | Demand & Competitors |
| DEMAND-02 | 3 | Demand & Competitors |
| DEMAND-03 | 3 | Demand & Competitors |
| DEMAND-04 | 3 | Demand & Competitors |
| COMP-01 | 3 | Demand & Competitors |
| COMP-02 | 3 | Demand & Competitors |
| COMP-03 | 3 | Demand & Competitors |
| FIN-01 | 4 | Clinic Financial Model |
| FIN-02 | 4 | Clinic Financial Model |
| FIN-03 | 4 | Clinic Financial Model |
| FIN-04 | 5 | Scenarios & Executive Report |
| FIN-05 | 5 | Scenarios & Executive Report |
| FIN-06 | 5 | Scenarios & Executive Report |
| FIN-07 | 5 | Scenarios & Executive Report |
| REP-01 | 5 | Scenarios & Executive Report |
| REP-02 | 5 | Scenarios & Executive Report |
| REP-03 | 5 | Scenarios & Executive Report |
| REP-04 | 5 | Scenarios & Executive Report |

**Coverage:** 32/32 v1 requirements mapped (100%).
