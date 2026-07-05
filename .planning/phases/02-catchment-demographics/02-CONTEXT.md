# Phase 2: Catchment & Demographics - Context

**Gathered:** 2026-07-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the geospatial catchment (exact-address geocoding → 1/3/5 km buffers in EPSG:7855 → **SA1-level** area-apportioned population) and the census demographic profile (ABS Data API G01/G02/G04 for POA 3067 + 9 peers, with local GCP fallback + ERP scaling to 2024), fixing v1's whole-postcode-summing and degree-buffer flaws. Maps (folium interactive + static matplotlib/contextily twin) show site, buffers, POA boundaries, and the Yarra River — competitors are Phase 3.

Scope anchor (from ROADMAP.md, fixed): GEO-01, GEO-02, GEO-03, GEO-04, DEMO-01, DEMO-02, DEMO-03, DEMO-04. Discussion clarifies HOW to implement within this boundary — not whether to add new capabilities. Competitor fetch, demand modelling, and P&L belong to Phases 3–5.

</domain>

<decisions>
## Implementation Decisions

### Apportionment unit & catchment geometry
- **D-01:** SA1-level area apportionment for catchment population (GEO-03), not POA. Sharper at the 1km ring where a POA straddling the buffer would compound the uniform-density assumption (PITFALLS.md Pitfall 2).
- **D-02:** SA1 geometry: download `SA1_2021_AUST_GDA2020` shapefile into `data/local/` (gitignored, documented in `.env.example`). Treated like the existing POA zip — large, immutable, not committed.
- **D-03:** SA1 census counts for apportionment weights: ABS Data API `C21_G01_SA1` (total persons only), fetched via the Phase 1 `CachedSession`. Filter to SA1s intersecting the 5km buffer **before** querying (beat the 30s timeout / 10MB cap — PITFALLS.md Pitfall 4).
- **D-04:** POA-level G01/G02/G04 retained for peer benchmarking (DEMO-02/03) — peers are compared as whole postcodes; SA1 granularity adds nothing there.
- **D-07:** POA boundary geometry: local shapefile (`POA_2021_AUST_GDA2020_SHP.zip`, on hand in `data/local/`) primary; ABS API SDMX-Geo as a documented fallback if the zip is missing. Filter to VIC + peers once, cache the filtered GeoPackage.
- **D-08:** SA1 census fetch strategy: spatial-filter SA1s intersecting the 5km buffer first (using the downloaded SA1 geometry), then query `C21_G01_SA1` for only those SA1 IDs. Minimises API calls and payload.
- **D-09:** Sanity assertions (hard-fail with clear message on violation): (a) 3km buffer area ≈ 28.27 km² (π×3²) — satisfies GEO-02; (b) apportioned 3km-ring population in plausible inner-Melbourne range (~80–110k) — PITFALLS.md Pitfall 2 detection.
- **D-05:** Uniform-density caveat: printed markdown note stating the assumption + its direction (likely overstates population in the Yarra River / industrial slice of Abbotsford) AND a Yarra River line annotated on every catchment map so readers see the geographic issue.

### ABS census tables & fallback
- **D-11:** Age data: verify `C21_G04_POA` (age by sex) exists at runtime via the ABS dataflow list (`/rest/dataflow`). If yes, fetch G04 for POA 3067 + peers → age bands + 65+ share directly.
- **D-12:** G04 fallback if `C21_G04_POA` is NOT available at POA level: Claude's discretion during planning/research (likely `C21_G04_SA2` + apportion into catchment, or local GCP for 3067's 65+ share with peers marked N/A).
- **D-13:** G01 variables extracted: total persons + sex split + dwelling counts (supports DEMO-03 demand/supply indicators).
- **D-14:** G02 variables extracted: `median_age` + `median_total_household_income` + `median_personal_income` (core peer-comparison columns).
- **D-15:** Local fallback trigger: auto on any API failure (timeout, 5xx, empty data) — print a warning cell naming the missing data and the local file substituted. No manual switch. Honours PIPE-04 "never hard-fail on a network call".
- **D-16:** Peer fallback: in fallback mode, populate 3067 from `GCP_POA3067.xlsx` and mark the 9 peer rows N/A with a printed warning that peer comparison is degraded. No fabricated peer data.
- **D-17:** Schema parity: local fallback parses GCP files into the SAME tidy DataFrame schema the API path produces (column names, dtypes, row-per-POA shape). Downstream code is source-agnostic (ARCHITECTURE.md §"data flow" mandate).
- **D-18:** Age band structure: ABS standard 5-year bands (0-4, 5-9, … 80-84, 85+) — aligns with AIHW/MBS age-band attendance rates used in the Phase 3 demand model.

### ERP scaling (census staleness — DEMO-04)
- **D-19:** ERP source: ABS Regional Population by SA2 (catalog 3218.0) — the official annual ERP release. Fetch the Yarra SA2 row(s) covering Abbotsford + neighbours.
- **D-20:** ERP vintage: latest available ABS ERP release (2023-24 FY, released March 2025). Scale 2021 census → 2024 estimate (~3-year adjustment).
- **D-21:** SA2→POA/SA1 mapping method: Claude's discretion during planning (uniform Yarra SA2 rate vs weighted by SA2 membership vs POA-SA2 correspondence file). The catchment is largely within Yarra SA2, so a uniform rate is defensible.
- **D-22:** Caveat display: printed markdown note stating the scaling (2021 baseline → 2024 ERP-adjusted, SA2 rate applied) AND a table column showing both raw 2021 and ERP-scaled values side by side.
- **D-23:** ERP fetch: ABS Data API dataflow (check if ERP by SA2 is available as a dataflow, e.g. `ABS_ERP_SA2`). Fetch via the same Phase 1 `CachedSession`. Consistent with the cache boundary; no extra manual download. If no dataflow exists, researcher identifies the alternative fetch path.
- **D-24:** ERP scope: apply ERP scaling to BOTH the catchment population (GEO-03 output) AND the peer-postcode benchmarking table (DEMO-02/03) — each peer scaled by its own SA2 growth rate. Consistent treatment.

### Maps, charts & phase-boundary scope
- **D-25:** Phase 2 catchment map layers (folium interactive + static twin): site pin + 1/3/5 km buffer rings + POA boundaries (shaded by apportionment share) + Yarra River line + peer postcode markers. **No competitors** — competitor layer is added in Phase 3.
- **D-26:** DEMO-03 peer table: census columns now (population, ERP-scaled pop, median age, 65+ share, median income) with 'GP count' + 'pharmacy count' columns as placeholders ("— Phase 3") for Phase 3 to fill. DEMO-03 is fully satisfied in Phase 3 when Places data lands. No Places API calls in Phase 2.
- **D-27:** Static matplotlib+contextily figure(s) for the PDF: **one figure per ring** (1km, 3km, 5km), each zoomed to its ring. 3 figures total. Contextily basemap tiles cached.
- **D-28:** Basemap provider for contextily static maps: Claude's discretion during planning (CartoDB Positron for clean investor-report aesthetic vs OSM for orientation detail).
- **D-29:** Peer comparison charts (DEMO-02): 2×2 bar chart grid — population (ERP-scaled), median age, 65+ share, median income. POA 3067 highlighted in each chart.
- **D-30:** Folium interactive map: inline only, NOT embedded in the PDF (folium is HTML/JS — won't render in weasyprint; STACK.md constraint). The static matplotlib twin handles the PDF.
- **D-31:** Geocode verification (PITFALLS.md Pitfall 3): print geocoded coordinates + a one-line "visually verify this pin on the map below before proceeding" instruction, with the folium map immediately after. Pin must be checked against the known Johnston St × Hoddle St corner.
- **D-06:** v1-vs-v2 catchment population comparison (success criterion #2): grouped bar chart + side-by-side table per ring (ring | v1 naive | v2 apportioned | diff | % overstatement). The teaching moment showing v1 inflated 2–4×.

### Claude's Discretion
- v1 comparison number source (reproduce v1 logic inline vs hardcoded documented constant) — D-10
- G04 fallback strategy if `C21_G04_POA` unavailable at POA level — D-12
- SA2→POA/SA1 ERP mapping method (uniform rate vs weighted vs correspondence) — D-21
- Basemap provider for contextily static maps — D-28
- Exact `requests-cache` session construction details (inherited from Phase 1)
- SA1 shapefile download mechanism (direct URL vs ABS download page) and exact file naming in `data/local/`
- ERP dataflow ID discovery (researcher confirms the exact ABS Data API dataflow for ERP by SA2)
- Folium map styling (marker icons, ring colours, legend format)
- Static figure composition (axis labels, scale bars, north arrows)
- Whether to cache the filtered SA1/POA GeoPackage as an intermediate artifact in `data/cache/`

</decisions>

<specifics>
## Specific Ideas

- PITFALLS.md Pitfalls 1–5 + 15 are the structural templates for this phase: CRS confusion (P1), whole-postcode summing (P2 — the headline v1 flaw being fixed), centroid-vs-address (P3), ABS API dataflow discovery (P4), POA-vs-SA2/SA3 geography mismatch (P5), census staleness / point-estimate false precision (P15). Each has a "Do this instead" that maps directly to a decision above.
- ARCHITECTURE.md §2 (Geospatial Catchment) and §3 (Demographics) define the notebook section layout and the `gpd.overlay` intersection → `pop × (intersect_area / poa_area)` pattern (now upgraded to SA1 per D-01).
- The cohealth Collingwood catchment report PDF (`data/local/Catchment-Report-Cohealth-collingwood-Centre-2026-6-11-113449 (1).pdf`) is the structural benchmark for what a professional catchment report contains — FEATURES.md §"What good looks like" references it.
- v1 files (`Johnston_St_v1.ipynb`, `johnston_st_v1.py`) stay frozen in repo root as the reference for the v1-vs-v2 comparison (D-06) and as the cautionary example for every flaw this phase fixes.
- The 10 peer postcodes are already in `BASE_ASSUMPTIONS["peer_postcodes"]` from Phase 1; site address + radii are likewise already in `BASE_ASSUMPTIONS`. Phase 2 reads these, does not redefine them.
- Phase 1's `CachedSession` (in §1) and `PROJECT_ROOT` (in §0) are the integration points — Phase 2 reuses both, adds no new HTTP boundary.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture & patterns
- `.planning/research/ARCHITECTURE.md` §"Standard Architecture" + "Recommended Project Structure" — the §2 (Geospatial Catchment) + §3 (Demographics) notebook section layout, `data/cache/` + `data/local/` directory structure, and the linear-pipeline-with-cached-IO-boundary model
- `.planning/research/ARCHITECTURE.md` §"Pattern 1: Cached Fetch Boundary" — all ABS/Google calls in Phase 2 go through the Phase 1 `CachedSession` (no `requests.get` from analysis cells)
- `.planning/research/ARCHITECTURE.md` §"data flow" / §"Data acquisition spikes" — the source-agnostic tidy-DataFrame schema mandate (D-17) and the recommended build order (geocode → ABS spike → buffers → demographics)

### Pitfalls to avoid (each maps to a decision)
- `.planning/research/PITFALLS.md` §"Pitfall 1" (CRS confusion) — drives D-09 area assertion + the EPSG:7855-for-metric / EPSG:4326-for-display convention
- `.planning/research/PITFALLS.md` §"Pitfall 2" (whole-postcode summing) — the headline v1 flaw; drives D-01 (SA1 apportionment), D-05 (caveat + river), D-09 (pop range assert), D-06 (v1-vs-v2 comparison)
- `.planning/research/PITFALLS.md` §"Pitfall 3" (centroid vs address) — drives D-31 (geocode verification)
- `.planning/research/PITFALLS.md` §"Pitfall 4" (ABS API dataflows/timeout) — drives D-08 (spatial filter first), D-11 (verify G04 at runtime), D-15 (auto fallback)
- `.planning/research/PITFALLS.md` §"Pitfall 5" (POA vs SA2/SA3 mismatch) — drives D-04 (POA for peers, SA1 for catchment)
- `.planning/research/PITFALLS.md` §"Pitfall 15" (census staleness / false precision) — drives D-19..D-24 (ERP scaling) and the "report ranges, round aggressively" guidance for Phase 5

### Stack & library specifics
- `.planning/research/STACK.md` §"Core Technologies" (geopandas, shapely, pyproj, folium, matplotlib, contextily rows) — the exact preinstalled versions and the EPSG:7855 reprojection requirement
- `.planning/research/STACK.md` §"ABS Data API — verified specifics" — `C21_G01_POA`/`C21_G02_POA` dataflow IDs, `csvfilewithlabels` format, the `/rest/data/{flow}/{key}` URL pattern, and the `C21_{table}_{geography}` generalisation (drives D-11 `C21_G04_POA`, D-03 `C21_G01_SA1`)
- `CLAUDE.md` (STACK.md source) §"PDF report generation" — confirms folium cannot go in the PDF; static matplotlib+contextily twin is mandatory (D-30)

### Features & quality bar
- `.planning/research/FEATURES.md` §"Core feature table" (catchment, demographic profile, maps, provider ratios rows) — the feature priority and approach notes
- `.planning/research/FEATURES.md` §"What good looks like" + §"Comparison to template reports" — the professional catchment-report standard the deliverable must meet (cohealth benchmark)
- `.planning/research/FEATURES.md` §"Dependency graph" — the build order (geocoded site → buffers → apportioned pop → demographic profile → demand model)

### Requirements & roadmap
- `.planning/REQUIREMENTS.md` §"Geospatial Catchment (GEO)" — GEO-01..04 are the verifiable success criteria for the catchment half
- `.planning/REQUIREMENTS.md` §"Demographics (DEMO)" — DEMO-01..04 are the verifiable success criteria for the demographics half
- `.planning/ROADMAP.md` §"Phase 2 — Catchment & Demographics" — phase goal, success criteria, dependencies (Phase 1), research flag (Yes — `C21_G01_POA`/`C21_G02_POA` dataKey dimension order unverified; `C21_G04_POA` existence unverified)

### Phase 1 context (integration points)
- `.planning/phases/01-scaffolding-data-pipeline/01-CONTEXT.md` — D-01..D-16 establish the `CachedSession`, `BASE_ASSUMPTIONS` shape, `PROJECT_ROOT`, cache commit policy, and dual-environment bootstrap that Phase 2 builds on. **Phase 2 must not redefine these.**

### Local data assets (fallback + geometry)
- `data/local/POA_2021_AUST_GDA2020_SHP.zip` — POA boundary geometry primary source (D-07)
- `data/local/GCP_POA3067.xlsx` — local census fallback for POA 3067 (D-16); peers N/A in fallback mode
- `data/local/Catchment-Report-Cohealth-collingwood-Centre-2026-6-11-113449 (1).pdf` — professional catchment report structural benchmark
- `Johnston_St_v1.ipynb` / `johnston_st_v1.py` — frozen v1 reference for the v1-vs-v2 comparison (D-06) and the flaw catalogue

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Phase 1 `CachedSession`** (§1 of `Johnston_St_v2.ipynb`) — every ABS Data API call in Phase 2 (G01/G02/G04 POA, G01 SA1, ERP by SA2) routes through this session. No new HTTP boundary. `allowable_methods=("GET","POST")` already enabled.
- **`BASE_ASSUMPTIONS` dict** (§0) — already holds `site_address`, `catchment_radii_m` (`[1000, 3000, 5000]`), `peer_postcodes` (10 POAs), `rent_yr`, `n_allied_fte`. Phase 2 reads these; any new Phase-2 constants (e.g. ERP vintage year, SA1 shapefile URL) get added here with citation comments per PIPE-05.
- **`PROJECT_ROOT` + `CACHE_DIR`** (§0) — path resolution for `data/local/` (SA1 zip, POA zip, GCP xlsx) and `data/cache/` (ABS responses, geocode response, filtered GeoPackages).
- **`FORCE_REFRESH` flag** (§0) — single switch threads through the `CachedSession`; Phase 2 inherits it.
- **v1 notebook** — mine for the `google_nearby_places` function structure (not needed in Phase 2 but useful in Phase 3) and the v1 catchment-population logic (for the D-06 comparison).

### Established Patterns
- **Single parameters cell** (PIPE-05) — no numeric literal outside `BASE_ASSUMPTIONS`. Phase 2's buffer radii, SA1 fetch scope, ERP vintage, and assertion thresholds must live in the dict or be derived from it.
- **Source-agnostic tidy DataFrames** (ARCHITECTURE.md) — analysis cells never see raw JSON or know whether API or fallback supplied the data. Phase 2's ABS fetch + GCP fallback must emit the same schema.
- **Cache-everything, run-offline** (PIPE-04) — ABS responses (POA + SA1 + ERP) are cached and committed; a fresh clone re-runs keyless at $0.

### Integration Points
- **§1.2 geocode** (new in Phase 2) → produces `site_lat, site_lon` consumed by §2 buffer construction and (Phase 3) Places search centres. Cached as `geocode_<slug>.json`.
- **§2 catchment** (new) → produces buffer GeoDataFrames + SA1 apportionment weights, consumed by §3 demographics (catchment age profile) and Phase 3 §5 demand model.
- **§3 demographics** (new) → produces catchment pop/age/income by ring + peer benchmarking table, consumed by Phase 3 §5 demand model and Phase 5 reporting.
- **`BASE_ASSUMPTIONS`** → Phase 2 may add keys (ERP vintage, SA1 source URL, assertion thresholds) but must not break the `{**BASE_ASSUMPTIONS, **overrides}` scenario pattern (Phase 1 D-10).

</code_context>

<deferred>
## Deferred Ideas

- **Mesh-block apportionment** (finer than SA1) — noted in PITFALLS.md Pitfall 2 as the "best" option; deferred as overkill for an MVP investor report. Revisit only if SA1 apportionment at the 1km ring is challenged by a reviewer.
- **SA1-level demographics for peers** — aggregating SA1 census up to POA for peers. No benefit (peers are whole-postcode units); dropped.
- **Clipping non-residential mesh blocks** from the apportionment denominator (river, industrial) — would sharpen the catchment pop but needs a land-use layer; scope-creep for Phase 2. The Yarra River map annotation + caveat (D-05) is the MVP treatment.
- **Drive-time isochrones** — already an Out of Scope / v2 decision (V2-02); radial buffers with a stated limitation note remain the choice.
- **Standalone folium HTML export** to `outputs/` — considered for live investor demos; deferred (inline-only per D-30). Can be added trivially in Phase 5 if a live demo is needed.
- **POA-SA2 correspondence file for ERP mapping** — the most rigorous SA2→POA mapping method; deferred as a planning-time Claude discretion (D-21) — uniform Yarra SA2 rate is the likely MVP choice.

</deferred>

---

*Phase: 02-catchment-demographics*
*Context gathered: 2026-07-05*
