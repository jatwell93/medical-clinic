# Phase 2: Catchment & Demographics - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-05
**Phase:** 02-catchment-demographics
**Areas discussed:** Apportionment unit, ABS census tables, ERP scaling method, Map & table scope at boundary

---

## Apportionment unit

### Q1: Which geographic unit should the area-apportionment use?

| Option | Description | Selected |
|--------|-------------|----------|
| POA (MVP) | Postcode polygons (~10 POAs). Simpler, local shapefile on hand. Coarser — uniform-density assumption is loud at 1km ring. Matches FEATURES.md MVP. | |
| SA1 (sharper) | Statistical Area 1 (~hundreds of small units). PITFALLS.md Pitfall 2 recommends — much less apportionment error at 1km ring. Cost: fetch SA1 geometry + SA1 census. | ✓ |
| Mesh-block (best) | Smallest ABS unit. Minimum error. Cost: heaviest — overkill for MVP. | |
| You decide | Claude picks based on build cost vs accuracy. | |

**User's choice:** SA1 (sharper)
**Notes:** User opted for the more accurate SA1 apportionment over the MVP POA approach, accepting the added build cost (SA1 geometry + census fetch).

### Q2: How to handle the uniform-density assumption caveat (Pitfall 2)?

| Option | Description | Selected |
|--------|-------------|----------|
| Printed note + map annotation | Markdown caveat + Yarra River line on map. Teaching-friendly. | ✓ |
| Clip non-residential mesh blocks | Exclude river/industrial from denominator. More accurate but scope-creep. | |
| Note only, no map annotation | Markdown caveat only; clean maps. | |
| You decide | Claude chooses. | |

**User's choice:** Printed note + map annotation

### Q3: v1-vs-v2 comparison (success criterion #2) — what should it show?

| Option | Description | Selected |
|--------|-------------|----------|
| Side-by-side table per ring | ring | v1 naive | v2 apportioned | diff | % overstatement. Teaching moment. | |
| Bar chart + table | Grouped bar chart + table. More visual punch for investor report. | ✓ |
| Table only, no chart | Minimal comparison table. | |
| You decide | Claude picks. | |

**User's choice:** Bar chart + table

### Q4: Where does the POA boundary geometry come from?

| Option | Description | Selected |
|--------|-------------|----------|
| Local shapefile (on hand) | POA_2021_AUST_GDA2020_SHP.zip in data/local/. Fast, deterministic, immutable. | |
| ABS API (SDMX-Geo) | Fetch from API. Avoids 56MB zip but adds SDMX-Geo complexity + Beta timeout risk. | |
| Both, local primary | Local shapefile primary; ABS API documented fallback. Most robust. | ✓ |
| You decide | Claude picks. | |

**User's choice:** Both, local primary

### Q5 (follow-up): SA1 boundary geometry — where from?

| Option | Description | Selected |
|--------|-------------|----------|
| Download SA1 shapefile | ABS SA1_2021_AUST_GDA2020 into data/local/. Reliable, no timeout risk. | ✓ |
| ABS API SDMX-Geo | Fetch via API. No download but SDMX-Geo parsing complex + Beta risk. | |
| GCP SA1 pack (local) | SA1 GCP pack bundles geometry + census. Need to confirm availability. | |
| You decide | Claude picks. | |

**User's choice:** Download SA1 shapefile

### Q6 (follow-up): SA1-level census counts for apportionment — which source?

| Option | Description | Selected |
|--------|-------------|----------|
| ABS API C21_G01_SA1 | Fetch G01 total persons at SA1 level via API. Cached. Lightweight if filtered. | ✓ |
| Local GCP SA1 pack | Census counts bundled with geometry if SA1 GCP pack downloaded. | |
| POA pop × SA1 area share | Skip SA1 census; apportion POA pop across SA1s by area. Cheaper, compounds assumption. | |
| You decide | Claude picks. | |

**User's choice:** ABS API C21_G01_SA1

### Q7 (follow-up): POA-level demographics for peer benchmarking still from POA G01/G02?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, POA for peers | SA1 only for catchment apportionment. Peer comparison uses POA G01/G02. Matches REQUIREMENTS. | ✓ |
| SA1 for peers too | Aggregate SA1 up to POA for peers. More work, no benefit. | |
| You decide | Claude confirms. | |

**User's choice:** Yes, POA for peers

### Q8 (follow-up): How to scope the SA1 census fetch (30s timeout / 10MB cap)?

| Option | Description | Selected |
|--------|-------------|----------|
| Spatial filter first | Filter SA1s intersecting 5km buffer before fetching. Minimises calls. | ✓ |
| Fetch by SA2, filter locally | Fetch all SA1s in relevant SA2s, filter locally. Simpler query, more data. | |
| All VIC SA1s | Largest payload, highest timeout risk. Not recommended. | |
| You decide | Claude picks. | |

**User's choice:** Spatial filter first

### Q9 (follow-up): What sanity assertions guard the catchment math?

| Option | Description | Selected |
|--------|-------------|----------|
| Area + pop range assert | 3km buffer ≈ 28.27 km² (hard fail) AND apportioned pop in 80-110k range (hard fail). | ✓ |
| Area assert only | Buffer area only; pop plausibility as printed warning. | |
| You decide | Claude picks. | |

**User's choice:** Area + pop range assert

### Q10 (follow-up): How to obtain v1's naive catchment population number?

| Option | Description | Selected |
|--------|-------------|----------|
| Reproduce v1 logic inline | Re-run v1's naive sum logic in v2. Self-documenting. | |
| Hardcoded v1 constant | Documented constant with v1 cell reference. Simpler. | |
| You decide | Claude picks during planning. | ✓ |

**User's choice:** You decide

---

## ABS census tables

### Q1: How to get age bands / 65+ share (G01 = totals, G02 = medians — neither has age structure)?

| Option | Description | Selected |
|--------|-------------|----------|
| Verify G04_POA at runtime | Query dataflow list to confirm C21_G04_POA exists. If yes, fetch for age bands + 65+ share. Researcher must confirm. | ✓ |
| Derive from local + G02 median | Skip G04; derive 65+ from local GCP for 3067, G02 median_age for peers. Weaker peer comparison. | |
| G04 at SA2 + apportion | Fetch C21_G04_SA2 (more likely to exist), apportion into catchment. Peers still need POA age source. | |
| You decide | Claude/researcher picks after verifying dataflows. | |

**User's choice:** Verify G04_POA at runtime

### Q2: Which G01 variables to extract?

| Option | Description | Selected |
|--------|-------------|----------|
| Total persons only | Minimal column set, fastest. Other G01 columns unused. | |
| Persons + sex + dwellings | Supports DEMO-03 demand/supply indicators. Slightly larger payload. | ✓ |
| You decide | Claude picks based on DEMO-03 needs. | |

**User's choice:** Persons + sex + dwellings

### Q3: Which G02 variables (medians/averages) to extract?

| Option | Description | Selected |
|--------|-------------|----------|
| Age + income medians | median_age + median_total_household_income + median_personal_income. Core peer columns. | ✓ |
| All G02 medians | Age, income, mortgage, rent, household size, family. Richer but more than needed. | |
| You decide | Claude picks. | |

**User's choice:** Age + income medians

### Q4: When does the local GCP fallback trigger?

| Option | Description | Selected |
|--------|-------------|----------|
| Auto on API failure | Any failure (timeout, 5xx, empty) → fallback + warning cell. No manual switch. Honours PIPE-04. | ✓ |
| Manual flag + auto | BASE_ASSUMPTIONS switch + auto on failure. Useful for offline dev. | |
| You decide | Claude picks. | |

**User's choice:** Auto on API failure

### Q5 (follow-up): In local-fallback mode, how to handle the 9 peer postcodes (GCP_POA3067.xlsx only has 3067)?

| Option | Description | Selected |
|--------|-------------|----------|
| 3067 only, peers N/A | Populate 3067 from xlsx; mark 9 peers N/A with warning. No fabricated data. | ✓ |
| Pre-extracted peer CSV snapshot | Bundle pre-extracted peer census CSV as fallback. Most robust but adds file. | |
| Skip peer table in fallback | Skip peer comparison entirely; 3067 standalone profile only. | |
| You decide | Claude picks. | |

**User's choice:** 3067 only, peers N/A

### Q6 (follow-up): Confirm the source-agnostic schema parity pattern?

| Option | Description | Selected |
|--------|-------------|----------|
| Same schema, source-agnostic | Fallback parses GCP into SAME tidy DataFrame schema. Downstream code is source-agnostic. ARCHITECTURE.md mandate. | ✓ |
| Native schema + branch | Fallback emits native schema with source flag; downstream branches. Less work, violates principle. | |
| You decide | Claude picks. | |

**User's choice:** Same schema, source-agnostic

### Q7 (follow-up): If C21_G04_POA is NOT available at POA level, what's the fallback?

| Option | Description | Selected |
|--------|-------------|----------|
| G04_SA2 + apportion | Fall back to C21_G04_SA2, apportion into catchment. Documented approximation. | |
| Median age only, drop 65+ | Use G02 median_age; drop 65+ share column. Honest but weaker. | |
| Local GCP for 3067 65+ | Extract 65+ from local GCP for 3067; peers N/A. Partial fallback. | |
| You decide | Claude/researcher picks after confirming what exists. | ✓ |

**User's choice:** You decide

### Q8 (follow-up): Which age band structure?

| Option | Description | Selected |
|--------|-------------|----------|
| ABS 5-year bands | 0-4, 5-9, ... 80-84, 85+. Matches AIHW/MBS attendance rates for Phase 3. | ✓ |
| Demand-model bands | 0-14, 15-24, 25-44, 45-64, 65+. Fewer columns, directly maps to rate tiers. | |
| Both (internal vs display) | 5-year internally, coarse for display. More work. | |
| You decide | Claude picks. | |

**User's choice:** ABS 5-year bands

---

## ERP scaling method

### Q1: Which ERP source for scaling 2021 census forward (DEMO-04)?

| Option | Description | Selected |
|--------|-------------|----------|
| ABS ERP by SA2 (3218.0) | Official annual ERP release. Fetch Yarra SA2 row(s). Most defensible. | ✓ |
| State ERP scaled | Less local signal. PITFALLS.md Pitfall 6 warns against. | |
| Caveat only, no scaling | Just print staleness caveat. DEMO-04 requires scaling — not sufficient. | |
| You decide | Claude/researcher picks. | |

**User's choice:** ABS ERP by SA2 (3218.0)

### Q2: Which ERP vintage / what year to scale TO?

| Option | Description | Selected |
|--------|-------------|----------|
| Latest (2023-24) | Released March 2025. Scale 2021 → 2024. Most current; ~3-year adjustment. | ✓ |
| 2022-23 vintage | Released 2024. Scale 2021 → 2023. Slightly older, more stable. | |
| Extrapolate to 2026 | Extrapolate SA2 growth rate forward 2 more years. Aggressive; extrapolation risk. | |
| You decide | Claude picks based on what's published. | |

**User's choice:** Latest (2023-24)

### Q3: How to map SA2-level ERP growth onto the POA/SA1 catchment?

| Option | Description | Selected |
|--------|-------------|----------|
| Uniform Yarra SA2 rate | Apply Yarra SA2 growth rate to all catchment POAs/SA1s. Simple, defensible. | |
| Weighted by SA2 membership | Multiple SA2s weighted by each SA1's SA2 membership. More accurate if 5km ring spills beyond Yarra. | |
| POA-SA2 correspondence | ABS correspondence file + population weights. Most rigorous, adds complexity. | |
| You decide | Claude picks during planning. | ✓ |

**User's choice:** You decide

### Q4: How to present the census-staleness caveat + scaling?

| Option | Description | Selected |
|--------|-------------|----------|
| Note + table column | Markdown note + table column showing raw 2021 and ERP-scaled values side by side. | ✓ |
| Note only, scaled value | Markdown note only; table shows only scaled value with footnote. Cleaner table. | |
| You decide | Claude picks. | |

**User's choice:** Note + table column

### Q5 (follow-up): How to fetch the ABS ERP by SA2 data?

| Option | Description | Selected |
|--------|-------------|----------|
| ABS Data API dataflow | Check if ERP by SA2 is a dataflow (e.g. ABS_ERP_SA2). Fetch via CachedSession. Consistent with cache boundary. | ✓ |
| Manual download to data/local | Download 3218.0 Excel/CSV manually. No API dependency; deterministic. | |
| API first, file fallback | Try API; fall back to manual download. Most robust, two code paths. | |
| You decide | Claude/researcher picks after checking dataflow availability. | |

**User's choice:** ABS Data API dataflow

### Q6 (follow-up): Does ERP scaling apply to catchment only, or also to peer table?

| Option | Description | Selected |
|--------|-------------|----------|
| Catchment only | Scale catchment pop only. Peer table shows raw 2021 with footnote. | |
| Catchment + peers | Scale both; each peer by its own SA2 rate. Consistent treatment. | ✓ |
| You decide | Claude picks. | |

**User's choice:** Catchment + peers

---

## Map & table scope at boundary

### Q1: Which layers on the Phase 2 catchment map (competitors are Phase 3)?

| Option | Description | Selected |
|--------|-------------|----------|
| Site + buffers + POA + river | Site pin + 1/3/5 km rings + POA boundaries (shaded by apportionment share) + Yarra River + peer markers. No competitors. | ✓ |
| Above + competitor placeholder | All above + empty competitor layer placeholder. Signals what's coming. | |
| You decide | Claude picks. | |

**User's choice:** Site + buffers + POA + river

### Q2: DEMO-03 peer table — how to handle the phase boundary (GP/pharmacy counts are Phase 3)?

| Option | Description | Selected |
|--------|-------------|----------|
| Census now, GP/pharmacy placeholder | Census columns now; GP/pharmacy columns as "— Phase 3" placeholders. DEMO-03 fully satisfied in Phase 3. | ✓ |
| Full table incl. competitor counts | Lightweight Places count fetch now. Pulls Phase 3 forward; scope creep + API cost risk. | |
| Census-only, rebuild in Phase 3 | Census-only table now; Phase 3 rebuilds with all columns. Avoids placeholders. | |
| You decide | Claude picks. | |

**User's choice:** Census now, GP/pharmacy placeholder

### Q3: Static matplotlib+contextily figure(s) for the PDF — one combined or per-ring?

| Option | Description | Selected |
|--------|-------------|----------|
| One combined figure | All 3 buffer rings together. Single PDF-ready figure. | |
| One figure per ring | Separate zoomed figure per ring (1km, 3km, 5km). 3 figures. Better ring detail. | ✓ |
| Overview + 1km detail | Combined overview + 1km detail. 2 figures. | |
| You decide | Claude picks. | |

**User's choice:** One figure per ring

### Q4: Which basemap provider for contextily static maps?

| Option | Description | Selected |
|--------|-------------|----------|
| CartoDB Positron | Light, minimal. Clean investor-report aesthetic. Free, no key. | |
| OpenStreetMap | More detail (streets, labels). Busier. Free, no key. | |
| Positron PDF, OSM folium | Different basemaps per output format. | |
| You decide | Claude picks. | ✓ |

**User's choice:** You decide

### Q5 (follow-up): DEMO-02 peer comparison charts — which?

| Option | Description | Selected |
|--------|-------------|----------|
| 2×2 bar chart grid | Population (ERP-scaled), median age, 65+ share, median income. 3067 highlighted. | ✓ |
| Table + 1 pop chart | Ranked comparison table + 1 population bar chart. Minimal charts. | |
| You decide | Claude picks. | |

**User's choice:** 2×2 bar chart grid

### Q6 (follow-up): Folium interactive map — inline only, or also saved as standalone HTML?

| Option | Description | Selected |
|--------|-------------|----------|
| Inline only, no PDF embed | Render inline; do NOT embed in PDF (folium is HTML/JS). Static twin handles PDF. STACK.md constraint. | ✓ |
| Inline + save HTML | Also save HTML to outputs/ for standalone viewer. Extra output for live demos. | |
| You decide | Claude picks. | |

**User's choice:** Inline only, no PDF embed

### Q7 (follow-up): Geocode verification (Pitfall 3)?

| Option | Description | Selected |
|--------|-------------|----------|
| Coords + verify prompt + map | Print coordinates + "visually verify this pin" prompt + folium map immediately after. | ✓ |
| Map only, no prompt | Just render map; reader verifies by looking. Less hand-holding. | |
| You decide | Claude picks. | |

**User's choice:** Coords + verify prompt + map

---

## Claude's Discretion

- v1 comparison number source (reproduce v1 logic inline vs hardcoded documented constant) — D-10
- G04 fallback strategy if C21_G04_POA unavailable at POA level — D-12
- SA2→POA/SA1 ERP mapping method (uniform rate vs weighted vs correspondence) — D-21
- Basemap provider for contextily static maps — D-28

## Deferred Ideas

- Mesh-block apportionment (finer than SA1) — overkill for MVP; revisit if SA1 at 1km ring is challenged
- SA1-level demographics for peers — no benefit; dropped
- Clipping non-residential mesh blocks from apportionment denominator — scope-creep; Yarra River annotation + caveat is MVP treatment
- Drive-time isochrones — already Out of Scope / v2 (V2-02)
- Standalone folium HTML export to outputs/ — deferred (inline-only); can add in Phase 5 if live demo needed
- POA-SA2 correspondence file for ERP mapping — deferred as planning-time discretion; uniform Yarra SA2 rate is likely MVP choice
