# Feature Research

**Domain:** Australian healthcare site feasibility analysis (medical clinic + pharmacy co-location, delivered as Colab notebook + executive PDF)
**Researched:** 2026-07-05
**Confidence:** HIGH (core report structure and Australian benchmarks verified against MBS Online, AIHW, PBS, RACGP, Productivity Commission sources; MEDIUM on private-fee/cost benchmarks which vary by practice)

## Context: What Professional Feasibility Reports Contain

Professional healthcare site feasibility / catchment reports (the kind produced by health planning consultancies, PHNs, and pharmacy brokers, and exemplified locally by the cohealth Collingwood catchment report) follow a consistent skeleton:

1. **Executive summary with a clear recommendation** — go / no-go / go-with-conditions, headline metrics up front.
2. **Site & context description** — exact address, tenancy, floor plan capacity, access/transport, planning context.
3. **Catchment definition & demographic profile** — defined catchment (radius, drive-time, or SA-based), population, age structure, income, growth, health-relevant indicators (SEIFA, chronic disease proxies).
4. **Supply-side / competitor analysis** — existing GPs, clinics, pharmacies mapped and counted; provider-to-population ratios vs benchmarks.
5. **Demand modelling** — expected service utilisation (attendances/scripts per capita, age-adjusted), gap between demand and existing capacity, required market share.
6. **Financial feasibility** — revenue model, cost structure, P&L, breakeven, capital requirements.
7. **Scenario & sensitivity analysis** — base/optimistic/pessimistic; which assumptions move the answer.
8. **Assumptions register & data sources** — every input cited and dated.

Investors reading such a report expect specific Australian metrics (verified current values):

| Metric | Benchmark | Source |
|---|---|---|
| GP attendances per capita | ~6.8/yr national (2022, rising trend; major cities higher — use ~7 with age adjustment) | AIHW, Medicare funding of GP services over time |
| FTE GPs per 100,000 | 113 national (2024); ~110-117 major cities; AMWAC planning benchmark 110.4 (≈1 GP : 905 people) | RACGP Health of the Nation 2025; Productivity Commission RoGS 2026; AMWAC 2000 |
| Population per FTE GP | ~900-1,000 (planning); implies a 5-FTE clinic needs to capture demand equivalent of ~4,500-5,000 people | Derived from above |
| FTE GP consult capacity | ~110-130 consults/week × ~46 weeks ≈ 5,000-6,000/yr per FTE | RACGP mixed-billing guide scenarios |
| MBS item 23 (Level B) rebate | $43.90 (from 1 Jul 2025); Level C item 36 $84.90 | MBS Online |
| Bulk billing incentive | Triple incentive from Nov 2023; +12.5% practice incentive for full-BB practices from Nov 2025 | RACGP / DoH |
| Typical private fee, Level B, inner Melbourne | ~$90-110 (gap ~$46-66) | RACGP billing guide scenario ($95); market observation — flag as assumption |
| PBS scripts per capita | 8.4/yr national (2023-24, subsidised); higher incl. under-co-payment | PBS Expenditure & Prescriptions Report 2023-24 |
| GP earnings split | GP retains ~60-70% of billings; practice keeps 30-40% | Industry standard — cite as assumption range |

## Feature Landscape

### Table Stakes (Users Expect These)

Missing any of these and the report does not read as professional / investor-grade.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Executive summary + explicit go/no-go recommendation | The single thing an investor reads; every professional feasibility report leads with it | LOW | Write last; must state the recommendation, the 3-5 numbers that drive it, and the conditions under which it flips |
| Site description & floor-plan capacity check | Confirms 5 GP rooms + allied health + pharmacy physically fit; anchors the FTE assumption | LOW | Ground floor plan PDF already on hand; a paragraph + consult-room count, not CAD analysis |
| Demographic catchment profile (population, age bands, income, growth) | Core of any catchment report; demand model is meaningless without it | MEDIUM | ABS Data API G01/G02 for POA 3067 + peers; 2021 vintage caveat stated prominently |
| Catchment maps (site, 1/3/5 km rings, competitors) | Visual table stakes — a feasibility report without a map looks amateur | MEDIUM | folium/geopandas; static PNG export needed for the PDF (folium is HTML-only — render matplotlib/contextily versions for print) |
| Competitor inventory (GPs, clinics, pharmacies, allied health) with counts and locations | Investors always ask "who else is there?"; supply side of the gap analysis | MEDIUM | Google Places with pagination + caching; classify by type and brand; note Places FTE counts are unknown — headcount ≠ capacity, state this limitation |
| Provider-to-population ratios vs national/state benchmarks | The standard supply metric (FTE GPs per 100k = 113 national, ~110-117 major cities) | LOW | Depends on catchment population + competitor counts; use AMWAC 110.4/100k as planning benchmark with caveat that no official benchmark exists |
| Demand model: attendances per capita × catchment population vs existing capacity | The core analytical claim — is there unmet demand for 5 more FTE GPs? | MEDIUM | Baseline ~6.8-7 attendances/capita (AIHW); output = market share the clinic must capture; sanity threshold: 5 FTE GPs ≈ 25,000-30,000 consults/yr ≈ ~4,000-4,500 regular patients |
| Full clinic P&L (revenue vs costs, monthly/annual) | Financial feasibility is the point of the study | HIGH | Mixed billing 70/30; item mix (not just item 23 — include Level C, care plans, procedures); costs: GP % split, nurse/admin, rent $100k, insurance, consumables, IT |
| Breakeven analysis + time-to-breakeven | Limited startup capital makes this the investor's first question | MEDIUM | Depends on P&L + patient ramp-up curve (clinics take 12-24 months to fill books); model ramp explicitly |
| Fit-out capital estimate | Capital-constrained project; capex drives time-to-breakeven | LOW-MEDIUM | Benchmark $-per-sqm ranges for medical fit-out, cited; flag as high-uncertainty input |
| Base / optimistic / pessimistic scenarios | Standard in every professional feasibility report | MEDIUM | Vary: billing mix, consults/GP/day, ramp speed, rent; present as side-by-side P&L table |
| Sensitivity analysis (tornado-style: which assumption moves breakeven most) | Investors expect to see which levers matter | MEDIUM | One-way sensitivity on 5-8 key inputs; tornado chart is the expected visual |
| Cited data sources + dated assumptions register | Investor credibility; PROJECT.md constraint | LOW | Single assumptions table: value, source, date, confidence; cite ABS, MBS Online, AIHW, PBS, RACGP |
| Executive PDF export | Deliverable format is notebook + PDF | MEDIUM | nbconvert or a dedicated report-building cell; must work in free Colab; all figures must render as static images |

### Differentiators (Competitive Advantage)

These lift the study above a broker-grade template and directly serve the Core Value (defensible, transparent, standalone-clinic answer) and the teaching goal.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Area-apportioned catchment population | Fixes v1's whole-postcode-summing flaw; most cheap reports get this wrong. Intersect buffer with POA/SA1 geometry, apportion population by area share | MEDIUM | geopandas overlay; document assumption of uniform density within zones; using SA1s instead of POAs sharpens it further if ABS API cooperates |
| Age-adjusted demand model | Attendance rates vary steeply by age; Abbotsford skews young-adult (below-average per-capita use). Applying age-band attendance rates instead of a flat 7/capita is more honest and likely more conservative — which investors respect | MEDIUM | AIHW/Medicare age-band attendance rates × catchment age structure; depends on demographic profile + apportioned population |
| SA3-level (Yarra 20604) MBS utilisation instead of state files | Local signal replaces noise; distinguishes this from v1 and from lazy reports | MEDIUM | SA3 MBS data via data.gov.au / AIHW downloads; documented fallback to state benchmark with warning banner |
| Uncertainty ranges / confidence intervals on key outputs | Most site reports present point estimates; showing breakeven as a range (via scenario envelope or simple Monte Carlo on 4-6 inputs) signals analytical maturity | MEDIUM-HIGH | Keep simple: triangular distributions on key inputs, 1-5k draws, percentile bands on breakeven month and year-2 profit. Do NOT over-engineer |
| Cached, reproducible pipeline (re-run free, deterministic) | Google API cost control + auditability; an investor (or marker) can re-run it | MEDIUM | JSON/parquet cache keyed by query; cache-first fetch functions; env-based key handling; works in Colab and local Windows |
| Teaching-style commentary throughout | The user is learning; the notebook doubles as a portfolio piece showing *why* each method was chosen and what v1 got wrong | LOW (effort, not complexity) | Markdown cells: "what we're doing / why / what the naive approach gets wrong"; explicitly narrate the v1→v2 fixes |
| Explicit market-share framing ("clinic needs X% of catchment consults") | Converts abstract demand-gap into one intuitive investor number; few template reports do this | LOW | Falls out of the demand model; present as the headline feasibility metric |
| Pharmacy synergy as quantified *secondary* upside | Answers the co-location question without contaminating the standalone-clinic verdict; disciplined sequencing is itself a differentiator | LOW-MEDIUM | Foot-traffic/script-capture uplift estimate using 8.4 scripts/capita benchmark; presented only *after* standalone verdict, clearly labelled non-load-bearing |
| Peer-postcode benchmarking (3067 vs 9 peers) | Contextualises whether Abbotsford is under- or over-served relative to comparable inner suburbs | MEDIUM | Reuses census + Places machinery across 10 postcodes; good teaching content; watch Places API cost — cache aggressively |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| ML demand model (Random Forest etc.) on the peer-postcode sample | "Data science" credibility; v1 did it | 3-10 rows cannot support any ML model; it's noise dressed as rigour and would destroy investor credibility if probed | Transparent arithmetic demand model (population × age-adjusted rates) with cited benchmarks; use regression only if ever working with hundreds of SA1s, and even then as illustration |
| Exploratory clustering of suburbs presented as analysis | Looks sophisticated; v1 had it | Unstable at n=10, answers no feasibility question | Simple ranked comparison table of peer postcodes on 4-5 metrics |
| Script-dependency assumption (clinic viability propped up by pharmacy scripts, or clinic sized to feed pharmacy) | The pharmacy co-location is the commercial motivation | Directly contradicts the Core Value; also raises ethical/regulatory red flags (inducement optics) | Model clinic standalone first; pharmacy synergy quantified separately as upside only |
| Uncited "industry rule of thumb" assumptions | Fast; everyone quotes them | One uncited number an investor recognises as wrong poisons the whole report | Every assumption in the register with source + date + confidence; where genuinely unknown (private fee, fit-out $), state a cited *range* and sensitivity-test it |
| Drive-time isochrones | More realistic than circles | Paid APIs / OSRM setup; poor reproducibility in free Colab; marginal gain in a dense inner-urban grid | 1/3/5 km radial buffers with a stated limitation note (already an Out of Scope decision) |
| Pharmacy retail P&L | "While we're at it" | Different business, different data (retail margins, FOS mix), no public data at site level; scope creep | Out of scope per PROJECT.md; only validate clinic doesn't need subsidy |
| Real-time / per-pharmacy PBS dispensing volumes | Would sharpen pharmacy analysis | Not publicly available at that granularity | Per-capita script benchmark (8.4/yr subsidised, PBS 2023-24) × catchment population |
| Web-scraped competitor booking data (HotDoc availability, etc.) | Great demand signal in theory | ToS violations, fragile, unreproducible | Google Places counts + ratings/review counts as licensed proxy; state the limitation |
| Interactive dashboard (Streamlit/Voila) | Impressive demo | Doesn't survive into the PDF deliverable; adds a second runtime to maintain | Well-organised notebook with a parameters cell at top; scenario toggle via config dict |
| Live-recomputed everything on each run | "Always fresh" | Google Places costs money per run; ABS API rate-limits; breaks Colab reproducibility | Cache-first with explicit `force_refresh` flag |

## Feature Dependencies

```
Geocoded site + radial buffers (1/3/5 km)
    └──requires──> nothing (start here)

Area-apportioned catchment population
    └──requires──> radial buffers
    └──requires──> POA/SA1 geometry + ABS census pull (cached)

Demographic catchment profile ──requires──> area-apportioned population

Age-adjusted demand model
    └──requires──> demographic profile (age bands)
    └──requires──> attendance-rate benchmarks (AIHW/SA3 MBS, cached)

Competitor inventory (Places, cached)
    └──requires──> geocoded site
Provider-to-population ratios ──requires──> competitor inventory + apportioned population

Market-share requirement (headline metric)
    └──requires──> age-adjusted demand model + competitor capacity estimate

Clinic P&L ──requires──> market-share/consult-volume assumptions + billing benchmarks (MBS rebates)
Breakeven & time-to-breakeven ──requires──> P&L + fit-out capital + ramp-up curve
Scenarios ──requires──> P&L (parameterised)
Sensitivity / tornado ──requires──> scenarios (same parameter machinery)
Confidence intervals (Monte Carlo) ──requires──> parameterised P&L (enhances scenarios)

Pharmacy synergy upside ──requires──> standalone clinic verdict (must come AFTER, by design)

Executive summary + PDF export ──requires──> everything above (static figures)

Caching layer ──enhances──> every API-touching feature (build it FIRST)
Teaching commentary ──enhances──> everything (write as you go, not at the end)

ML demand model ──conflicts──> cited transparent assumptions (anti-feature)
Live recompute ──conflicts──> caching / API-cost constraint
```

### Dependency Notes

- **Caching layer first:** every subsequent feature touches ABS or Google APIs; building fetch-with-cache utilities in the first phase makes all later work free to re-run and is itself a differentiator.
- **P&L must be parameterised from day one:** scenarios, sensitivity, and Monte Carlo are all cheap *if* the P&L is a function of a config dict; expensive retrofits otherwise. This is the single most important architectural dependency.
- **Pharmacy synergy is order-dependent by design:** it must be computed and presented after the standalone verdict to preserve the Core Value framing.
- **PDF export constrains visualisation choices upstream:** any folium interactive map needs a static twin; decide the figure pipeline early.

## MVP Definition

### Launch With (v1 of the v2 notebook)

- [ ] Config + caching + env-key utilities — everything depends on them; makes re-runs free
- [ ] Geocoded site, 1/3/5 km buffers, area-apportioned catchment population — fixes the headline v1 flaw
- [ ] Demographic profile (ABS API, local fallback) with maps — table stakes
- [ ] Competitor inventory + provider-to-population ratios — table stakes
- [ ] Age-adjusted demand model → required market share — the core analytical claim
- [ ] Parameterised clinic P&L + breakeven + fit-out capital + ramp curve — the point of the study
- [ ] Base/optimistic/pessimistic scenarios + tornado sensitivity — investor expectation
- [ ] Assumptions register with citations — credibility requirement
- [ ] Executive summary + go/no-go + PDF export — the deliverable

### Add After Validation (v1.x)

- [ ] Monte Carlo confidence intervals on breakeven — once scenario machinery works and point estimates are stable
- [ ] Peer-postcode benchmarking table — once Places caching is proven (API cost control)
- [ ] Pharmacy synergy upside module — only after the standalone verdict is computed and written up
- [ ] SA1-level apportionment upgrade (from POA) — if ABS API pulls prove reliable

### Future Consideration (v2+)

- [ ] Drive-time isochrones — deferred by explicit decision; revisit only if a reviewer challenges radial buffers
- [ ] 2026 Census refresh — when data releases (~2027), swap in via the same cached pipeline
- [ ] Multi-site comparison tooling — only if the study generalises beyond Johnston St

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Caching + config + key handling | HIGH | LOW | P1 |
| Area-apportioned catchment population | HIGH | MEDIUM | P1 |
| Demographic profile + maps | HIGH | MEDIUM | P1 |
| Competitor inventory + ratios | HIGH | MEDIUM | P1 |
| Age-adjusted demand → market share | HIGH | MEDIUM | P1 |
| Parameterised P&L + breakeven + ramp | HIGH | HIGH | P1 |
| Scenarios + sensitivity tornado | HIGH | MEDIUM | P1 |
| Assumptions register + citations | HIGH | LOW | P1 |
| Executive summary + PDF export | HIGH | MEDIUM | P1 |
| Teaching commentary | MEDIUM | LOW | P1 (write as you go) |
| SA3 MBS utilisation data | MEDIUM | MEDIUM | P2 |
| Monte Carlo confidence intervals | MEDIUM | MEDIUM | P2 |
| Peer-postcode benchmarking | MEDIUM | MEDIUM | P2 |
| Pharmacy synergy upside | MEDIUM | LOW-MEDIUM | P2 (order-gated) |
| Drive-time isochrones | LOW | HIGH | P3 |
| Interactive dashboard | LOW | HIGH | P3 (likely never) |

## Competitor Feature Analysis

"Competitors" here = report archetypes the deliverable will be judged against.

| Feature | Pharmacy-broker template report | Health-planning consultancy report (e.g. cohealth-style catchment study) | Our Approach |
|---------|--------------------------------|--------------------------------------------------------------------------|--------------|
| Catchment population | Whole-suburb/postcode totals, often overstated | SA-based, sometimes apportioned | Area-apportioned 1/3/5 km, method shown |
| Demand model | Flat scripts/consults per capita | Age/SEIFA-adjusted utilisation | Age-adjusted attendances, SA3 MBS calibration, market-share framing |
| Competitor analysis | List of nearby pharmacies | Mapped provider ratios vs benchmarks | Places-derived map + ratios vs 113/100k national, capacity caveats stated |
| Financials | Rules-of-thumb revenue multiple | Often absent (public-health focus) | Full parameterised P&L, breakeven, ramp, capex — our strongest section |
| Uncertainty | None | Qualitative caveats | Scenarios + tornado + optional CI bands |
| Reproducibility | None (static PDF) | None | Cached, re-runnable notebook — unique among the archetypes |
| Sources | Sparse, undated | Well-cited | Fully cited assumptions register |

## Sources

- MBS Online, Item 23 (rebate $43.90 from 1 Jul 2025) and Level A-E item table — www9.health.gov.au/mbs
- RACGP newsGP, July MBS indexation changes; RACGP *A guide to introducing mixed billing* (worked scenario: $95 private fee, item 23) — racgp.org.au
- AIHW, *Medicare funding of General Practitioner services over time* — 6.8 GP attendances per person (2022), major-cities vs remote gradient
- Productivity Commission, Report on Government Services 2026, Primary & community health — 110.2 FTE GPs per 100,000 (2024)
- RACGP Health of the Nation 2025 — 113 FTE GPs/100k national 2024; VIC 117
- AMWAC 2000 planning benchmark — 110.4 GPs/100k (1:905), with the caveat no official benchmark exists
- PBS Expenditure and Prescriptions Report 2023-24 — 8.4 subsidised scripts per capita national
- cohealth Collingwood catchment report (local PDF) — structural benchmark for professional catchment reports
- PROJECT.md — scope decisions, v1 flaw inventory, constraints

---
*Feature research for: Australian healthcare site feasibility analysis*
*Researched: 2026-07-05*
