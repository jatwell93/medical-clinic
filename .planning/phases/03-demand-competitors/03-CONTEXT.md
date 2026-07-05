# Phase 3: Demand & Competitors - Context

**Gathered:** 2026-07-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Quantify both sides of the market: age-adjusted GP consultation demand from SA3 20604 Yarra MBS data (AIHW age-band rates × catchment age structure), and the existing supply landscape via Google Places (New) competitor mapping with per-type/per-ring splitting, place_id dedupe, brand classification, and clinic-vs-practitioner filtering — converging on the required market share a 5-FTE-GP clinic must capture, with GP-per-1,000 benchmarked against the VIC average. Replaces v1's state-level Medicare file (no local signal), uncached Places re-runs, raw `type=doctor` counts (inflated 2-5× by specialists/individual listings), and the 3-row Random Forest "demand model" (Pitfall 14).

Scope anchor (from ROADMAP.md, fixed): DEMAND-01, DEMAND-02, DEMAND-03, DEMAND-04, COMP-01, COMP-02, COMP-03. Discussion clarifies HOW to implement within this boundary — not whether to add new capabilities. The P&L, scenarios, and executive report belong to Phases 4–5.

</domain>

<decisions>
## Implementation Decisions

### MBS data acquisition & fallback
- **D-01:** SA3 20604 MBS data acquired via documented manual download — user downloads the "Medicare quarterly statistics – Statistical Area (SA3) Summary" xlsx from health.gov.au once, drops it in `data/local/`, path + download URL + access date documented in `.env.example`. Treated like the SA1 shapefile in Phase 2 (large, immutable, not committed). Researcher verifies the exact current URL at build time (ROADMAP research flag). The state-level file already in `data/local/` (`medicare-quarterly-statistics-primary-care-service-type-summary-march-quarter-2025-26(1).xlsx`) is the fallback — it has NO SA3 sheet (Pitfall 6).
- **D-02:** Age-band GP attendance rates from AIHW "Medicare-subsidised GP, allied health and specialist health care across local areas" — per-capita rates by age band (0-14, 15-64, 65+) at SA3 level. Aligns with ABS 5-year bands (Phase 2 D-18). ~1-2 year lag — caveat noted. This is the FEATURES.md recommended "Age-adjusted demand model" approach.
- **D-03:** AIHW age-band rates are the per-capita multipliers (cited vintage, ~2023-24); SA3 20604 MBS quarterly data is the total-attendance cross-check / sanity assertion (computed total ≈ SA3 reported total ±15%). Two datasets, complementary roles, both cited with access dates.
- **D-04:** Fallback when SA3 20604 data is missing: use the state-level Medicare file (already in `data/local/`) with a printed warning banner — "STATE BENCHMARK, NOT LOCAL — SA3 20604 data not found. Demand signal is the VIC average, not Yarra." Every output using it is labelled. Honours PIPE-04 no-hard-fail. Matches Pitfall 6 "How to avoid".

### Places query strategy & cost control
- **D-05:** Saturation handling: query per-type × per-ring first (5 types × 3 radii = 15 requests for site). If any query returns exactly 20 (the `maxResultCount` cap, no pagination in Nearby Search New), automatically subdivide that circle into a 2×2 grid of smaller circles (4 more requests) and dedupe on `place.id`. Repeat once if still saturated (max ~16 extra requests per saturated query). Capped, deterministic, cached. Beats the silent-truncation flaw (Pitfall 8).
- **D-06:** Peer scope: run the full Places query for the site catchment (1/3/5km) AND for each of the 10 peer postcodes (centroid-based, 1/3/5km). Fills the DEMO-03 placeholder GP/pharmacy columns from Phase 2 with real data. Cost: ~10 peers × 3 radii × 5 types = ~150 requests (cached, within the 5,000 free/month Pro SKU cap). Most complete; matches FEATURES.md peer-benchmarking feature.
- **D-07:** Pharmacy brand classification via Nearby Search results + keyword rules on `displayName` (e.g. "Priceline" → Priceline, "Chemist Warehouse" → CW, "Amcal" → Amcal, "TerryWhite Chemmart" → TerryWhite, else independent). No extra Text Search API calls. The per-type `pharmacy` query should catch all pharmacies in range anyway (COMP-02).
- **D-08:** Persist the deduped, classified competitor GeoDataFrame to `data/cache/competitors.geojson` (committed to git). Re-runs load the GeoJSON without touching the API. Fulfils the Phase 1 D-05 deferred decision. ~10-50KB for ~100-200 competitors. Raw API responses also cached via the Phase 1 `CachedSession` (audit trail).

### Classification, dedupe & GP capacity estimation
- **D-09:** Classification: keyword rules on `displayName` + `primaryType` to bucket into corporate GP (Myhealth, Healthscope, IPN, etc.), independent GP clinic ("medical centre", "general practice", "GP clinic"), pharmacy (by brand per D-07), allied health ("physio", "psychology", "dental"), and an exclude bucket (specialists, cosmetic, skin, vet). Individual-practitioner listings fuzzy-deduped by name+address (Pitfall 9 — they share the practice address). Ambiguous rows flagged for a manual-review checkpoint before the demand/supply gap is computed (Pitfall 9 "manual review of the final ≤100-row list").
- **D-10:** Existing GP FTE capacity estimated as a RANGE with two methods: (a) cleaned Places clinic count × assumed avg FTE GPs per clinic (e.g. 4-5 FTE, cited from RACGP/Alecto surveys); (b) AMWAC planning benchmark 110.4 FTE GPs per 100k × catchment population. Both presented side-by-side; the variance IS the caveat (Pitfall 9 "headcount ≠ capacity"). Assumptions stated explicitly. Used as the supply side of the demand-vs-capacity gap (DEMAND-03).
- **D-11:** Manual-review checkpoint mechanism (D-09): notebook prints the ambiguous-rows table (name, address, type, reason-for-flag) inline with a markdown instruction to review and edit `data/cache/competitors.geojson` manually if any are misclassified, then re-run from §5. User does the review outside the notebook. Honours PIPE-01 "no manual intervention" (no `input()` prompt blocking execution); the review is a documented post-run step, not an in-session gate.
- **D-12:** Capacity caveat presentation: the two-method range (D-10) IS the caveat — no separate caveat cell needed. The side-by-side range shows the uncertainty explicitly. A one-line note: "Places listings ≠ FTE GPs; range spans clinic-derived and benchmark-derived estimates." State the limitation prominently per Pitfall 9.

### Market share headline & maps
- **D-13:** Required-market-share headline metric (DEMAND-03) presented as ALL THREE framings side-by-side: (a) clinic consult capacity ÷ total catchment consult demand (age-adjusted) = "X% of all GP consults in the ring"; (b) clinic capacity ÷ unmet demand (total − existing capacity) = "X% of the unmet consult gap" (can exceed 100% — a signal in itself); (c) patients-needed = clinic capacity ÷ avg consults-per-patient-per-year (~4-5) = "X% of catchment population". Three cuts of the same transparent arithmetic (Pitfall 14 — no ML). Per-ring (1/3/5km).
- **D-14:** Plain-language interpretation: print the numbers with a one-line neutral framing ("X% of consults needed — [low/moderate/high] share required") but NO verdict on whether it's achievable. The go/no-go verdict is a Phase 5 output (after P&L + scenarios), not Phase 3. Avoids pre-empting the standalone-clinic verdict before the financial model exists (DEMAND-03 "plain-language interpretation" satisfied without overreaching).
- **D-15:** Competitor map design (COMP-03, GEO-04): one interactive folium map with all rings (1/3/5km) as toggleable layers + competitors coloured by type (GP clinic, pharmacy, allied health) + brand markers for pharmacies. Plus 3 static matplotlib+contextily figures (one per ring, zoomed) for the PDF — same pattern as Phase 2 D-27. Comprehensive; matches GEO-04 "interactive folium map + static matplotlib twin". Folium is inline-only (not in PDF); static figures handle the PDF (Phase 2 D-30 constraint).
- **D-16:** Peer-table integration: keep the Phase 2 peer benchmarking table as census-only; add a SEPARATE Phase 3 peer competitor table (GP count, pharmacy count by brand, allied health count, GP-per-1,000 ratio per peer). Two tables, cleaner separation of concerns. The Phase 2 DEMO-03 placeholder columns ("— Phase 3") are removed in the Phase 3 table, not back-edited into the Phase 2 table. GP-per-1,000 ratio benchmarked against VIC average (~117 FTE GPs/100k, COMP-03).

### Claude's Discretion
- Exact AIHW dataset URL and download mechanism (researcher verifies at build time)
- Exact SA3 MBS product URL on health.gov.au (researcher verifies — quarterly release URLs reshuffle)
- The 5 `includedTypes` values sent to Nearby Search (New) — `doctor`, `medical_lab`, `pharmacy`, `physiotherapist`, `dentist` per STACK.md, but researcher confirms the current Places API (New) type taxonomy
- Field mask exact composition (STACK.md lists the recommended minimal mask; researcher confirms `rating`/`userRatingCount` are worth the Pro SKU cost)
- Subdivision grid geometry (2×2 vs adaptive) and sub-circle radius calculation
- Keyword rules for classification (exact corporate-GP brand list, exact exclude-keyword list)
- Fuzzy-dedupe similarity threshold (name+address match cutoff)
- Avg FTE GPs per clinic assumption (4-5 range — researcher picks a cited point estimate)
- AMWAC benchmark vintage (110.4/100k is the FEATURES.md figure; researcher confirms latest)
- Consults-per-patient-per-year denominator for patients-needed framing (~4-5 — researcher cites)
- Market-share threshold labels (what counts as "low/moderate/high" share)
- Folium map styling (marker icons, type colours, layer control format)
- Static figure composition (axis labels, scale bars, north arrows — inherited from Phase 2)
- Contextily basemap provider (inherited from Phase 2 D-28 — CartoDB Positron vs OSM)
- Whether to cache contextily tiles for the 3 static competitor figures (Phase 2 cached them)

</decisions>

<specifics>
## Specific Ideas

- PITFALLS.md Pitfalls 6–10 + 14 are the structural templates for this phase: state-level Medicare as fake local signal (P6), MBS item/incentive changes (P7 — relevant to Phase 4 but the SA3 data vintage must be date-stamped here), Places 20-result cap silent truncation (P8), duplicate/miscategorised places inflating counts (P9), Places cost blowout from uncached re-runs (P10), ML theatre on handfuls of rows (P14 — the v1 Random Forest explicitly replaced by transparent arithmetic). Each has a "Do this instead" that maps to a decision above.
- ARCHITECTURE.md §4 (Competitor Landscape) and §5 (Demand Model) define the notebook section layout and the data flow: §1.4 Places → §4 dedupe/classify → §5 demand vs capacity → required share. §1.5 MBS SA3 loader feeds §5.
- ARCHITECTURE.md "data flow" #2 (Competitor flow): site coords → Places nearby (per type × radius) → cache → dedupe on `place_id` → brand classification (name-pattern rules) → per-ring counts feeding §5 capacity estimate and §4 map.
- ARCHITECTURE.md "data flow" #1 (Census flow) feeds §5: ABS API → cache → tidy per-POA DataFrame → §2 area weights → §3 catchment age profile → §5 demand. The catchment age profile (Phase 2 G04, ABS 5-year bands, D-18) is the demand-model input.
- FEATURES.md "Age-adjusted demand model" (MEDIUM confidence, P1): "AIHW/Medicare age-band attendance rates × catchment age structure; depends on demographic profile + apportioned population" — exactly D-02/D-03.
- FEATURES.md "Explicit market-share framing" (LOW confidence, falls out of demand model): "present as the headline feasibility metric" — D-13.
- FEATURES.md "Competitor inventory" (MEDIUM confidence): "Google Places with pagination + caching; classify by type and brand; note Places FTE counts are unknown — headcount ≠ capacity, state this limitation" — D-09/D-10/D-12.
- The 5,000 free Places requests/month (Pro SKU) is the budget ceiling; D-06's ~150 peer requests + D-05's ~15-31 site requests = ~180 total, comfortably within cap. Cached, so re-runs are $0.
- v1 files (`Johnston_St_v1.ipynb`, `johnston_st_v1.py`) stay frozen in repo root — mine for the `google_nearby_places` function structure (the Places query loop pattern, minus v1's uncached `requests.get` and degree-based buffering) and the v1 competitor-count inflation (for the teaching comparison).
- Phase 2's `BASE_ASSUMPTIONS["peer_postcodes"]` (10 POAs), `site_lat`/`site_lon` (§1.2 geocode), catchment buffers (§2), and catchment age profile (§3 G04) are the integration points — Phase 3 reads these, does not redefine them.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture & patterns
- `.planning/research/ARCHITECTURE.md` §"Standard Architecture" + "Recommended Project Structure" — the §4 (Competitor Landscape) + §5 (Demand Model) notebook section layout, and the §1.4 (Places client) + §1.5 (MBS SA3 loader) acquisition cells
- `.planning/research/ARCHITECTURE.md` §"Pattern 1: Cached Fetch Boundary" — all Places calls in Phase 3 go through the Phase 1 `CachedSession` (no `requests.get` from analysis cells); the competitor GeoJSON persistence (D-08) is an additional layer on top
- `.planning/research/ARCHITECTURE.md` §"data flow" — flow #1 (census → §3 age profile → §5 demand) and flow #2 (site coords → Places → dedupe → classify → §4 map + §5 capacity) define the integration sequence
- `.planning/research/ARCHITECTURE.md` §"Data acquisition spikes" — recommended build order: §1.4 Places client with cache → §1.5 MBS SA3 loader with state fallback → §4 competitors → §5 demand model (first integration point, validates all upstream data)
- `.planning/research/ARCHITECTURE.md` §"Cache key conventions" — Places cache key format `places_<type>_<lat:.4f>_<lon:.4f>_<radius>` and MBS key `mbs_sa3_20604_<quarter>`

### Pitfalls to avoid (each maps to a decision)
- `.planning/research/PITFALLS.md` §"Pitfall 6" (state-level Medicare as fake local signal) — drives D-01 (correct SA3 product), D-04 (state fallback with loud warning)
- `.planning/research/PITFALLS.md` §"Pitfall 7" (MBS item/incentive changes) — drives the date-stamping of MBS values (D-03); full billing-model impact is Phase 4 but the SA3 data vintage must be cited here
- `.planning/research/PITFALLS.md` §"Pitfall 8" (Places 20-result cap / silent truncation) — drives D-05 (auto-subdivide on 20)
- `.planning/research/PITFALLS.md` §"Pitfall 9" (duplicate/miscategorised places inflating counts) — drives D-09 (rules + manual review), D-10 (capacity range), D-11 (review mechanism), D-12 (caveat presentation)
- `.planning/research/PITFALLS.md` §"Pitfall 10" (Places cost blowout from uncached re-runs) — drives D-08 (GeoJSON persistence) + the Phase 1 `CachedSession` inheritance
- `.planning/research/PITFALLS.md` §"Pitfall 14" (ML theatre on handfuls of rows) — drives D-13 (transparent arithmetic, three cuts of the same calculation, no ML)

### Stack & library specifics
- `.planning/research/STACK.md` §"Google Places API — use Places API (New)" — POST + mandatory `X-Goog-FieldMask` header, `maxResultCount=20`, no pagination, `includedTypes` accepts multiple values (`doctor`, `medical_lab`, `pharmacy`, `physiotherapist`, `dentist`), `locationRestriction.circle` for radius, dedupe on `place.id`, subdivide on saturation. Pricing: Nearby Search Pro = US$32/1k with 5,000 free/month. Drives D-05, D-06, D-07.
- `.planning/research/STACK.md` §"Caching strategy" — route all Places calls through `requests_cache` filesystem session with `allowable_methods=("GET","POST")` (already enabled in Phase 1), AND persist deduped competitor GeoDataFrame to `data/cache/competitors.geojson` (D-08)
- `CLAUDE.md` (STACK.md source) §"Google Places API" — confirms the field mask, pricing, and no-pagination constraint

### Features & quality bar
- `.planning/research/FEATURES.md` §"Core feature table" (competitor inventory, provider-to-population ratios, demand model rows) — the feature priority and approach notes
- `.planning/research/FEATURES.md` §"Differentiators" (age-adjusted demand model, SA3-level MBS, explicit market-share framing) — the features that distinguish this from v1 and from lazy template reports
- `.planning/research/FEATURES.md` §"Dependency graph" — the build order (catchment age profile + apportioned population → age-adjusted demand model → competitor inventory → provider-to-population ratios → required market share)
- `.planning/research/FEATURES.md` §"Key numbers" — FTE GPs per 100k (113 national, ~110-117 major cities, AMWAC 110.4), FTE GP consult capacity (~110-130/week × ~46 weeks ≈ 5,000-6,000/yr per FTE), MBS item 23 rebate $43.90 (from 1 Jul 2025)

### Requirements & roadmap
- `.planning/REQUIREMENTS.md` §"Demand Modelling (DEMAND)" — DEMAND-01..04 are the verifiable success criteria for the demand half
- `.planning/REQUIREMENTS.md` §"Competitor Analysis (COMP)" — COMP-01..03 are the verifiable success criteria for the competitor half
- `.planning/ROADMAP.md` §"Phase 3 — Demand & Competitors" — phase goal, success criteria, dependencies (Phase 2), research flag (Yes — SA3 MBS download URL/format + AIHW supplement needs runtime verification; age-band attendance rates need a citable vintage)

### Prior phase context (integration points)
- `.planning/phases/01-scaffolding-data-pipeline/01-CONTEXT.md` — D-01..D-16 establish the `CachedSession` (with `allowable_methods=("GET","POST")` for Places POST caching), `BASE_ASSUMPTIONS` flat dict, `PROJECT_ROOT`, `data/cache/` commit policy, and `FORCE_REFRESH` flag. Phase 3 inherits all of these. D-05 explicitly deferred the deduped competitor GeoDataFrame to Phase 3 (fulfilled by D-08 here).
- `.planning/phases/02-catchment-demographics/02-CONTEXT.md` — D-01..D-31 establish the site geocode (§1.2), 1/3/5km buffers in EPSG:7855 (§2), SA1-apportioned population by ring (§2), catchment age profile from G04 in ABS 5-year bands (§3, D-18), ERP-scaled population (§3, D-19..D-24), and the peer benchmarking table with "— Phase 3" placeholder GP/pharmacy columns (D-26). Phase 3 reads all of these; D-16 here decides how the peer competitor counts integrate.

### Local data assets (fallback + reference)
- `data/local/medicare-quarterly-statistics-primary-care-service-type-summary-march-quarter-2025-26(1).xlsx` — state-level Medicare file (NO SA3 sheet, Pitfall 6); the D-04 fallback, used only with a loud warning
- `data/local/medicare-annual-statistics-state-and-territory-2009-10-to-2024-25.xlsx` — annual state file; secondary fallback
- `data/local/SA3_2021_AUST.xlsx` — SA3 correspondence (may be useful for SA3 20604 Yarra boundary verification)
- `Johnston_St_v1.ipynb` / `johnston_st_v1.py` — frozen v1 reference for the `google_nearby_places` function structure (Places query loop) and the v1 competitor-count inflation (teaching comparison); do NOT copy v1's uncached `requests.get` or degree-based buffering

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Phase 1 `CachedSession`** (§1 of `Johnston_St_v2.ipynb`) — every Places API (New) POST call in Phase 3 routes through this session. `allowable_methods=("GET","POST")` already enabled. No new HTTP boundary. Cache key format `places_<type>_<lat:.4f>_<lon:.4f>_<radius>` per ARCHITECTURE.md.
- **`BASE_ASSUMPTIONS` dict** (§0) — already holds `site_address`, `catchment_radii_m` (`[1000, 3000, 5000]`), `peer_postcodes` (10 POAs), `rent_yr`, `n_allied_fte`, and Phase 2 additions (ERP vintage, SA1 source URL, assertion thresholds). Phase 3 reads these; new Phase-3 constants (MBS SA3 file path, AIHW age-band rates, avg FTE per clinic, AMWAC benchmark, consults-per-patient-per-year, market-share thresholds) get added here with citation comments per PIPE-05.
- **`PROJECT_ROOT` + `CACHE_DIR` + `data/local/`** (§0) — path resolution for the SA3 MBS xlsx (D-01), state fallback xlsx (D-04), and `data/cache/competitors.geojson` (D-08).
- **`FORCE_REFRESH` flag** (§0) — single switch threads through the `CachedSession`; Phase 3 inherits it. Setting `FORCE_REFRESH=True` re-fetches Places; otherwise loads `competitors.geojson` (D-08).
- **Phase 2 site geocode** (§1.2) → `site_lat, site_lon` consumed by §1.4 Places search centres.
- **Phase 2 catchment buffers** (§2) → buffer GeoDataFrames consumed by §4 competitor per-ring assignment (which ring is each competitor in?).
- **Phase 2 catchment age profile** (§3 G04) → age-band populations by ring consumed by §5 demand model (D-02/D-03).
- **Phase 2 ERP-scaled population** (§3) → catchment pop by ring consumed by §5 demand model and the patients-needed framing (D-13c).
- **Phase 2 peer benchmarking table** (§3) → census-only table; Phase 3 adds a separate competitor table (D-16).
- **v1 notebook** — mine for the `google_nearby_places` function structure (Places query loop pattern, minus v1's uncached `requests.get` and degree-based buffering) and the v1 competitor-count inflation (for the teaching comparison).

### Established Patterns
- **Single parameters cell** (PIPE-05) — no numeric literal outside `BASE_ASSUMPTIONS`. Phase 3's AIHW age-band rates, avg FTE per clinic, AMWAC benchmark, consults-per-patient-per-year, and market-share thresholds must live in the dict or be derived from it.
- **Source-agnostic tidy DataFrames** (ARCHITECTURE.md) — analysis cells never see raw JSON or know whether API or fallback supplied the data. Phase 3's MBS fetch + state fallback must emit the same schema.
- **Cache-everything, run-offline** (PIPE-04) — Places responses cached AND deduped GeoJSON persisted (D-08); a fresh clone re-runs keyless at $0 (competitors loaded from committed GeoJSON, MBS from `data/local/`).
- **No-hard-fail on network call** (PIPE-04) — Places API unavailable → load `competitors.geojson` from cache; MBS SA3 file missing → state fallback with warning (D-04).
- **Cell-replacement idempotency** (Phase 2 pattern) — Phase 3 cell generators should be re-runnable; regenerating the notebook replaces §4/§5 cells cleanly without duplicating.

### Integration Points
- **§1.4 Places client** (new in Phase 3) → produces raw place lists per (type, radius), consumed by §4 competitor classification and (Phase 5) report maps. Cached as `places_<type>_<lat>_<lon>_<radius>` JSON + persisted as `data/cache/competitors.geojson` (D-08).
- **§1.5 MBS SA3 loader** (new) → produces SA3 20604 consult rates / total attendances, consumed by §5 demand model. Local xlsx from `data/local/` (D-01); state fallback with warning (D-04).
- **§4 Competitor Landscape** (new) → produces classified competitor df + per-ring counts + competitor map, consumed by §5 capacity estimate and Phase 5 reporting.
- **§5 Demand Model** (new) → produces annual consult demand by ring (age-adjusted), existing GP capacity range (D-10), required market share (D-13, three framings), plain-language interpretation (D-14). Consumed by Phase 4 §6 P&L (consult volume → revenue) and Phase 5 reporting (headline metric).
- **`BASE_ASSUMPTIONS`** → Phase 3 may add keys (AIHW age-band rates, avg FTE per clinic, AMWAC benchmark, consults-per-patient-per-year, market-share thresholds, MBS file path) but must not break the `{**BASE_ASSUMPTIONS, **overrides}` scenario pattern (Phase 1 D-10).

</code_context>

<deferred>
## Deferred Ideas

- **Text Search (New) for brand-name searches** ("Priceline", "IPN medical centre") — STACK.md suggests it for >20-result queries; D-05's auto-subdivide handles saturation instead. Text Search with `pageToken` (up to 60 results) could be a future enhancement if subdivide proves insufficient for a specific query type. Revisit only if a query type consistently saturates even after subdivide.
- **Healthdirect National Health Services Directory cross-check** — Pitfall 9 suggests cross-checking the GP clinic list against Healthdirect. Deferred because Healthdirect has no official API and scraping-like behaviour is out of scope (PROJECT.md "licensed/public data only"). The manual-review checkpoint (D-09/D-11) is the MVP treatment.
- **SA1-level demand apportionment** — demand is currently ring-level (age-band rates × ring population). SA1-level would be finer but adds complexity for marginal accuracy gain at this scale. Revisit only if a reviewer challenges the ring-level estimate.
- **Drive-time isochrone competitor search** — already Out of Scope / v2 (V2-02); radial buffers with stated limitation remain the choice.
- **Live competitor re-fetch on each run** — rejected (Pitfall 10); cached GeoJSON (D-08) + `FORCE_REFRESH` flag is the pattern.
- **GP capacity from AHPRA/Health Workforce data** — would give actual FTE GP counts by SA3, but the data is restricted and not publicly available at clinic granularity. The two-method range (D-10) is the public-data treatment.
- **Competitor rating/review analysis** (sentiment, volume as a demand proxy) — the field mask includes `rating`/`userRatingCount` (STACK.md), so the data is collected; analysis of it is deferred to Phase 5 reporting if it adds investor signal.
- **Per-peer demand model** (age-adjusted demand for each of the 10 peers, not just the site) — would enable a peer-level required-market-share comparison. Deferred as scope creep; the peer competitor table (D-16) gives the supply-side comparison, which is sufficient for benchmarking.

</deferred>

---

*Phase: 03-demand-competitors*
*Context gathered: 2026-07-05*
