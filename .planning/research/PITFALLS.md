# Pitfalls Research

**Domain:** Healthcare site feasibility analytics (geospatial + Australian government data + financial modelling, delivered as a Colab notebook)
**Researched:** 2026-03-02
**Confidence:** HIGH (web-verified for Australian GP economics, MBS changes, fit-out costs, ABS API limits; v1 prototype audited directly)

## Critical Pitfalls

### Pitfall 1: Geographic vs projected CRS confusion (buffers/centroids in degrees)

**What goes wrong:**
Buffers, distances, areas, and centroids computed in a geographic CRS (EPSG:4326 / EPSG:7844) produce garbage: `buffer(3000)` in degrees creates a "buffer" spanning most of the continent; centroids of unprojected polygons are subtly wrong; area calculations are meaningless. v1 partially learned this (it re-projects to EPSG:7855 for the centroid in a "corrected" second cell) but the fix lives alongside the original wrong code — a classic Colab pattern where both versions survive.

**Why it happens:**
GeoPandas doesn't stop you — it warns (`UserWarning: Geometry is in a geographic CRS`) and returns numbers that look plausible at small scale. ABS shapefiles ship in GDA2020 geographic (EPSG:7844), so the default path is wrong.

**How to avoid:**
Adopt a single convention in v2: **all metric operations (buffer, area, distance, centroid) happen in EPSG:7855 (GDA2020 / MGA zone 55); all display/mapping happens in EPSG:4326**. Write one `to_metric()` / `to_display()` helper pair and use it everywhere. Sanity-check: a 3 km buffer around the site must have area ≈ 28.27 km² (`π × 3²`).

**Warning signs:**
Any `GeometryArray` warning in cell output; buffer polygons that cover half of Victoria on a folium map; areas in the 1e-4 range (square degrees); `.buffer(3000)` called on a GeoDataFrame whose `.crs` reports EPSG:4326/7844.

**Phase to address:**
Geospatial foundation phase (site geocoding + catchments). Add an assertion cell that checks buffer area before anything downstream uses it.

---

### Pitfall 2: Whole-postcode population summing instead of area apportionment

**What goes wrong:**
v1's core demand flaw (lines 81–91 of `johnston_st_v1.py`): it intersects the 3 km buffer with POA polygons, then sums the **full population of every postcode that touches the buffer**. Richmond (3121, ~30k people) counts 100% even if only 10% of its area is inside the catchment. Catchment population is inflated 2–4×, which inflates consult demand, which flips the go/no-go answer.

**Why it happens:**
`gpd.overlay(..., how='intersection')` gives you the clipped geometry, but joining population is easier by postcode ID than by computing area ratios — so the lazy join wins.

**How to avoid:**
Area-weighted apportionment: for each POA, compute `pop × (area of POA ∩ buffer) / (area of full POA)`, with both areas computed in EPSG:7855. Better still, do apportionment at **SA1 or mesh-block level** (smaller units → less apportionment error) — the ABS Mesh Block counts file is small and free. Document the assumption that population is uniformly distributed within each unit (it isn't — note the Yarra River and industrial land in Abbotsford make this locally material; consider clipping non-residential mesh blocks).

**Warning signs:**
Catchment population that exceeds the sum of the obviously-inside suburbs; 3 km catchment population > ~120k in inner Melbourne (plausible range is roughly 80–110k); population that jumps discontinuously when the radius changes slightly (a whole postcode entering/leaving).

**Phase to address:**
Catchment/demand phase. Success criterion: v2 catchment population must be shown side-by-side with v1's naive sum, with the difference explained (this is also the teaching moment).

---

### Pitfall 3: Centroid-based instead of address-based catchments

**What goes wrong:**
v1 initially buffers from the **postcode centroid**, not the site. POA 3067's centroid is several hundred metres from 292-296 Johnston St; at a 1 km radius that shifts a large fraction of the catchment and changes which competitors fall inside. v1 also references `s_lat`/`s_lon` (line 69) **before** they're defined (line 495) — an out-of-order-execution artifact that means the notebook doesn't run top-to-bottom.

**Why it happens:**
The centroid is available before geocoding is set up; the address-based version was bolted on later in v1 and never reconciled.

**How to avoid:**
Geocode `292-296 Johnston St, Abbotsford VIC 3067` **once**, cache the coordinates, hardcode them as a verified constant with the geocode date, and use them for every buffer and every Places search. Visually verify the pin on a map against the known corner (Johnston St × Hoddle St end of the block) before proceeding.

**Warning signs:**
Two different lat/lon pairs floating around the notebook (`lat_corr/lon_corr` vs `s_lat/s_lon`); `NameError` on fresh run; competitor counts that change depending on which cell ran last.

**Phase to address:**
Geospatial foundation phase — first cells of the notebook, before any catchment work.

---

### Pitfall 4: ABS Data API — undocumented dataflows, SDMX complexity, silent timeouts

**What goes wrong:**
Teams burn days discovering that: (a) Census dataflow IDs (e.g. `C21_G01_POA`-style flows) are not listed in friendly documentation — you must query `https://data.api.abs.gov.au/rest/dataflow` (hundreds of flows) and inspect each DSD to learn dimension order; (b) the dataKey is positional (`{dim1}.{dim2}...` separated by dots) and a wrong dimension order returns empty data, not an error; (c) the API gateway enforces a **30-second response timeout and 10 MB max response** — broad queries 504; (d) the service is officially **Beta** with no availability guarantee, so an uncached notebook fails randomly in demos.

**Why it happens:**
SDMX is a genuinely complex standard; the ABS API is metadata-driven and expects you to do discovery calls first. People copy a working CPI example and assume Census flows behave the same.

**How to avoid:**
- Do dataflow/DSD discovery **once**, record the exact flow ID, version, and dimension order as constants with comments.
- Request CSV (`Accept: application/vnd.sdmx.data+csv;labels=both`) instead of parsing SDMX-JSON/XML by hand — pandas reads it directly.
- Always send `Accept-Encoding: gzip, deflate, br`.
- Filter tightly: request only POA 3067 + the 9 peer postcodes, only the variables needed (G01/G02 equivalents) — never `all`.
- **Cache every response to disk** (Drive/local `data/cache/`) keyed by URL hash; the notebook must run fully offline from cache.
- Keep the local GCP POA VIC pack as documented fallback with an explicit warning cell if the API is unreachable.

**Warning signs:**
Empty datasets with HTTP 200 (wrong dataKey order); 504 "Endpoint request timed out"; notebook re-runs hitting the API dozens of times; different results between runs.

**Phase to address:**
Census data phase. Verification: kill network access (or set a `USE_CACHE_ONLY` flag) and confirm the notebook still runs end-to-end.

---

### Pitfall 5: POA vs SA2/SA3 geography mismatch

**What goes wrong:**
ABS Postal Areas (POA) are approximations of postcodes built from mesh blocks — they are **not** Australia Post postcodes, and they don't nest inside SA2s/SA3s. Mixing POA-level census data with SA3-level MBS data (SA3 20604 Yarra covers Abbotsford, Collingwood, Richmond, Fitzroy…) without an explicit correspondence step produces mismatched denominators — e.g. dividing SA3 GP attendances by POA population. Some census variables also aren't published at POA level, forcing silent substitutions.

**Why it happens:**
Both look like "areas around the site," and the SA3 correspondence file on hand makes it tempting to fudge conversions without weighting.

**How to avoid:**
Pick the native geography for each dataset and convert explicitly: census demographics at POA/SA1 for the catchment, MBS utilisation at SA3 used only as a **rate** (services per capita per year) applied to the catchment population — never as raw counts. Use the ABS correspondence file with population weights when a crosswalk is genuinely needed, and state the conversion in the notebook commentary.

**Warning signs:**
Per-capita figures wildly off national benchmarks (~7 GP attendances/person/year nationally); any cell dividing a number from one geography by a population from another; SA3 codes and POA codes appearing in the same merge.

**Phase to address:**
Demand model phase — define the geography strategy in a markdown cell before writing any merges.

---

### Pitfall 6: State-level Medicare files treated as local signal

**What goes wrong:**
v1 loads `medicare-quarterly-statistics-primary-care-service-type-summary...xlsx` whose sheets are `['Contents', 'State', 'Modified Monash', 'Primary Care Service Types']` — **no SA3 data at all**. Any "local utilisation" derived from it is just the Victorian average wearing a costume. The analysis looks data-rich but the local demand signal is zero.

**Why it happens:**
The Department of Health publishes several Medicare quarterly statistics files with near-identical names; the state/MMM summary is the first search hit. Nobody checks sheet contents before building on it.

**How to avoid:**
Use the correct product: **"Medicare quarterly statistics – Statistical Area (SA3) Summary"** (health.gov.au), which contains GP Non-Referred Attendances by SA3 from Sept-quarter 2019-20 onward, updated quarterly (Dec quarter 2025-26 released Feb 2026). Filter to SA3 20604 (Yarra). Supplement with AIHW "Medicare-subsidised GP, allied health and specialist health care across local areas" for richer per-capita and bulk-billing breakdowns (note: latest full-year AIHW release lags ~1–2 years). If only state data is available for a metric, print a loud warning and label it "state benchmark, not local" in every output that uses it.

**Warning signs:**
An Excel file whose sheet list contains "State" but no "SA3"; utilisation rates identical across candidate areas; no SA3 code appearing anywhere in the Medicare-loading cells.

**Phase to address:**
MBS data phase. Verification: the loaded dataframe must contain a row where SA3 code == 20604.

---

### Pitfall 7: MBS item/incentive changes making time series and revenue assumptions wrong

**What goes wrong:**
GP billing economics changed structurally three times in the data window: (1) **1 Nov 2023** — tripled bulk billing incentive + 13 new BBI items (75870-76, 75880-85) for under-16s and concession card holders; (2) **23 Feb 2025** — $7.9 B expansion announced; (3) **1 Nov 2025** — BBI eligibility extended to **all Medicare-eligible patients**, plus the new Bulk Billing Practice Incentive Program (BBPIP) paying participating fully-bulk-billing practices a quarterly **12.5% of MBS revenue** (split evenly between GP and practice). Consequences: pre-2023 bulk-billing rates and per-consult revenue don't extrapolate; the 70/30 mixed-billing assumption may be dominated by the alternative of full bulk billing + BBPIP; a P&L built on 2022-era item values understates bulk-billed revenue materially.

**Why it happens:**
MBS fee schedules are versioned and the analysis pulls whatever vintage a benchmark report used. The 2025 changes are recent enough that most published GP-economics content predates them.

**How to avoid:**
Date-stamp every MBS item value and incentive used (e.g. item 23 rebate + item 75870 tripled incentive, as at Nov 2025). Model **two billing strategies** in scenarios: (a) 70/30 mixed billing without BBPIP; (b) 100% bulk billing with BBPIP 12.5% — and let the scenario table show which wins for this demographic. Note any historical bulk-billing-rate trend (e.g. SA3 bulk-billing data from 2022) has a structural break at Nov 2023 and Nov 2025.

**Warning signs:**
A single "average consult revenue" number with no date; bulk-billing rates trended across 2023 without a break annotation; BBPIP absent from the revenue model.

**Phase to address:**
Financial modelling phase. Verification: revenue assumptions cell cites MBS Online factsheets with dates.

---

### Pitfall 8: Google Places 60-result cap and pagination silently truncating competitor counts

**What goes wrong:**
Nearby Search returns max 20 results per page, max 3 pages = **60 results per search**. A 3 km radius over inner Melbourne for `type=doctor` easily exceeds 60 real places, so counts hit an invisible ceiling — v1's "60 Medical Facilities in 3 km" is almost certainly the cap, not the count. Additionally, `next_page_token` needs ~2 s before it becomes valid (v1 handles this) and requesting it too early returns `INVALID_REQUEST` which naive code treats as "no more results."

**Why it happens:**
The API doesn't say "results truncated"; 60 looks like a plausible number. The token delay is only mentioned deep in the docs.

**How to avoid:**
- Treat any search returning exactly 60 as truncated: **subdivide** (grid of smaller-radius searches covering the buffer, then dedupe by `place_id`), or use multiple keyword/type searches and union results.
- Retry `INVALID_REQUEST` on page tokens with backoff rather than breaking.
- Prefer the newer Places API (Text Search with field masks) where practical, but the 60/20-per-page structure persists — subdivision is still the fix.

**Warning signs:**
Counts of exactly 60 (or exactly 20 with pagination broken); competitor density that plateaus as radius grows; `INVALID_REQUEST` in logs.

**Phase to address:**
Competitor mapping phase. Verification: assert no single search's result count == 60 without a subdivision pass; spot-check total against a manual Google Maps count for a small area.

---

### Pitfall 9: Duplicate and miscategorised places inflating competitor counts

**What goes wrong:**
`type=doctor` in Google Places returns specialists, dentists, cosmetic clinics, psychologists, skin clinics, vets mis-tagged, and multiple entries per clinic (each GP with their own listing plus the practice itself). A "6.6 doctors per 1,000 residents" density (v1's conclusion) built on raw counts can overstate actual **GP clinic** competition by 2–5×, poisoning the market-share requirement.

**Why it happens:**
Google's type taxonomy reflects business self-categorisation, not AHPRA reality. Individual-practitioner listings are a known Places quirk for medical.

**How to avoid:**
- Dedupe by `place_id`, then fuzzy-dedupe by name+address (individual GP listings usually share the practice address).
- Classify results: keyword rules on names (e.g. "medical centre", "general practice", "GP" → clinic; "dental", "physio", "skin", "cosmetic" → exclude/other bucket) plus manual review of the final ≤100-row list — this catchment is small enough to eyeball.
- Cross-check the clinic list against the Healthdirect National Health Services Directory or a manual map pass; count **clinics and estimated FTE GPs**, not listings.

**Warning signs:**
Same street address appearing 3+ times; obvious non-GP names in the "doctor" list; GP-per-1,000 density far above metro benchmarks (~1.2 FTE GPs per 1,000 is a sane order of magnitude — 6.6 "doctors"/1,000 is a red flag that listings ≠ GPs).

**Phase to address:**
Competitor mapping phase, with a manual-review checkpoint before the demand/supply gap is computed.

---

### Pitfall 10: Google Places API cost blowout from uncached re-runs

**What goes wrong:**
Nearby Search costs ~US$32/1,000 requests (SKU-dependent). A notebook doing multi-type × multi-radius × multi-postcode searches (v1 does exactly this: 2 types × 3 radii × 10 peer postcodes × up to 3 pages ≈ 180 requests per full run) that gets re-run 30 times during development quietly burns real money — and Colab restarts guarantee re-runs.

**Why it happens:**
Each individual run costs cents, so nobody notices until the bill. Colab's ephemeral state means "just re-run all cells" is the default workflow.

**How to avoid:**
Disk-cache every Places response as JSON keyed by (endpoint, params hash) in Drive/local `data/cache/`, with the request date stored. Load-from-cache first, fetch only on cache miss, and expose a `REFRESH_PLACES = False` flag. After the first complete run, all re-runs must be $0.

**Warning signs:**
`requests.get` to googleapis.com inside loops with no cache check; no `data/cache/` directory; API dashboard showing hundreds of requests/day during development.

**Phase to address:**
Competitor mapping phase — build the cache layer **before** the first bulk search, not after.

---

### Pitfall 11: Confusing GP gross billings with practice revenue

**What goes wrong:**
The single most common GP-clinic P&L error: treating 5 GPs × ~$550k gross billings = $2.75M as clinic revenue. GPs are contractors who **retain 65–70% of their billings** (RACGP: current standard 63–75%; Alecto 2025 survey: most practices 65–70%). The **practice's** revenue is the service fee — typically **30–35% of billings** (Dept of Health 2025 modelling assumes 30%; ATO benchmark caps reasonable service fees at 40–45%). So actual practice revenue on $2.75M of billings is ~$825k–$960k, and all practice costs (rent, admin staff, nurses, insurance, equipment) come out of that. Getting this wrong overstates revenue ~3× and makes any site look profitable.

**Why it happens:**
Published "GP revenue" figures usually mean gross billings; the service-entity structure (practice invoices the GP a service fee + GST) is unintuitive to non-industry modellers.

**How to avoid:**
Structure the P&L with billings as the top line, an explicit **service fee % row** (base 32%, pessimistic 30%, optimistic 35% — note the market has drifted toward GPs keeping more), and practice revenue = billings × service fee %. GP payments are **not** a practice cost under this structure — don't double count. Allied health typically on a similar % or room-rental model. Add BBPIP's 12.5% (practice gets half) as a scenario line if fully bulk billing.

**Warning signs:**
Practice "revenue" in the millions for a 5-GP clinic; GP salaries appearing as a cost line alongside 100% of billings as revenue; profit margins over ~25% of billings.

**Phase to address:**
Financial modelling phase — the P&L template structure is the prevention; get it reviewed before scenarios are run.

---

### Pitfall 12: Ignoring ramp-up, and underestimating fit-out capex

**What goes wrong:**
Feasibility models often assume day-one steady state (5 GPs, full books). Reality: recruiting 5 FTE GPs into inner Melbourne takes 6–18 months amid a GP shortage, patient books take 12–24 months to fill, and revenue in year 1 may be 30–50% of steady state while rent and admin costs are 100%. On capex: medical fit-outs in Melbourne run roughly **$1,200–$2,200/sqm** (Melbourne-specific guides: $1,200–$1,800/sqm base; national 2026 guides: $1,850–$3,500/sqm), so a ~250–350 sqm 6-room clinic is plausibly **$350k–$700k+ including equipment, IT, and compliance (RACGP 5th-edition standards: hand basins in consult rooms, accessible facilities, treatment room 15–20 sqm)** — often the single largest startup cost and fatal if the budget assumed $100k. With "limited startup capital" a constraint, this is the difference between feasible and not.

**Why it happens:**
Steady-state models are easier; fit-out quotes aren't obtainable from a notebook, so a placeholder number survives into the conclusion.

**How to avoid:**
Model monthly (or quarterly) cash flow for years 1–3 with a GP-recruitment ramp (e.g. 2 GPs at open → 5 by month 18) and per-GP book fill curves. Make fit-out a first-class scenario input with a cited $/sqm range × floor area from the ground-floor plan PDF. Report **time-to-breakeven and peak cash requirement** as headline outputs alongside steady-state profit.

**Warning signs:**
A P&L with no time axis; breakeven reported in "year 1"; fit-out as a single uncited round number; peak funding requirement never computed.

**Phase to address:**
Financial modelling phase; roadmap should make "time-to-breakeven + peak capital" explicit success criteria (they're already in PROJECT.md — enforce them).

---

### Pitfall 13: Rent and key assumptions presented as facts

**What goes wrong:**
The ~$100k/yr rent is a guess. Johnston St retail/medical strip rents vary widely; if actual rent is $140k, clinic profit could swing by more than the modelled margin. Same for gap fee levels, consults per GP per day, and bulk-billing share. A single-point model launders guesses into an authoritative-looking recommendation.

**Why it happens:**
Getting real rent comparables requires agent contact, not code; assumptions get typed once and never revisited.

**How to avoid:**
An **assumptions register** table at the top of the financial section: value, source ("estimate — unvalidated"), confidence, and sensitivity. Run one-way sensitivity (tornado chart) on rent ±40%, service fee %, consults/day, and bulk-billing mix. The exec summary must state which assumptions the go/no-go is most sensitive to.

**Warning signs:**
Assumptions embedded as magic numbers mid-cell; no sensitivity section; the recommendation not caveated by the rent assumption.

**Phase to address:**
Financial modelling + reporting phases (register built early, sensitivity in scenarios, caveats in exec summary).

---

### Pitfall 14: ML theatre — models trained on a handful of rows

**What goes wrong:**
v1 fits KMeans on **3 postcodes** ("Using 2 clusters given we only have 3 data points" — an actual comment in the code) and the PROJECT.md notes a Random Forest trained on 3–10 rows presented as a demand model. These outputs are noise with a scikit-learn veneer, and an investor with any quant literacy will discount the entire report on seeing them.

**Why it happens:**
Business-analytics coursework rewards "using ML"; clustering 3 rows runs without error, so it feels legitimate.

**How to avoid:**
Delete predictive ML from v2. The demand model should be **transparent arithmetic**: catchment population × age-band GP attendance rates (from AIHW/MBS SA3 data) = consult demand; existing GP capacity from the cleaned competitor list; gap = required market share. If peer-postcode comparison is wanted, use a simple ranked table or z-scores across the 10 peers — descriptive, not model-based. This is also more defensible and more teachable.

**Warning signs:**
`fit_predict` on a dataframe with `len(df) < 30`; feature matrices with more columns than rows; "the model predicts…" language anywhere in the report.

**Phase to address:**
Demand model phase — the roadmap should explicitly specify the arithmetic demand model and exclude ML.

---

### Pitfall 15: Point estimates without uncertainty; stale 2021 Census in a growing suburb

**What goes wrong:**
"Catchment demand: 187,432 consults/year" communicates false precision. Every input (apportioned population, attendance rates, competitor FTE counts) carries 10–30% uncertainty, and the 2021 Census is 4–5 years stale in a suburb with substantial apartment development since — catchment population is likely **understated**, and the age/income mix has shifted toward young renters.

**Why it happens:**
Pipelines produce single numbers; propagating ranges takes deliberate effort; Census is the only free granular source so its vintage gets ignored.

**How to avoid:**
Carry base/optimistic/pessimistic through the **demand** side, not just the P&L. Adjust 2021 population forward using ABS Regional Population (ERP by SA2, released annually — Yarra SA2s have current estimates) and disclose the growth uplift applied. Report ranges ("roughly 95k–115k residents within 3 km") and round aggressively in the exec summary.

**Warning signs:**
Six-significant-figure populations; a single demand number feeding the market-share calc; no mention of post-2021 growth in commentary.

**Phase to address:**
Demand model phase (ERP adjustment); reporting phase (ranges + rounding in exec summary).

---

### Pitfall 16: Notebook hygiene — hidden state, hardcoded paths, keys in git

**What goes wrong:**
v1 exhibits all three: `s_lat` used before definition (works only if cells ran in a historical order), hardcoded `/content/drive/MyDrive/Colab_Notebooks/...` paths (fails locally on Windows and on anyone else's Drive), and a Places key retrieved but whose usage pattern invites accidental hardcoding. A notebook that only runs in one person's historical session state is not a deliverable; a committed API key is a security incident with billing exposure.

**Why it happens:**
Colab encourages incremental cell execution; Drive paths are what `drive.mount` gives you; keys get pasted "temporarily" during debugging.

**How to avoid:**
- **Restart-and-run-all before every commit** — make it a ritual; the notebook must execute top-to-bottom clean.
- A single config cell at the top: detect environment (`google.colab` importable?) and set `DATA_DIR`/`CACHE_DIR` accordingly (Drive path vs relative Windows path via `pathlib`).
- Key handling: Colab `userdata.get('GOOGLE_PLACES_KEY')` with fallback to `os.environ` / `.env` via python-dotenv locally; `.env` in `.gitignore`; never print the key; strip notebook outputs before commit (`nbstripout` or manual clear) since outputs can leak keys and cost money to regenerate anyway.
- Restrict the Google key in Cloud Console (API restrictions: Places + Geocoding only; set a budget alert).

**Warning signs:**
`NameError` on fresh runtime; any literal `/content/drive/` outside the config cell; `AIza...` appearing in `git grep` or cell outputs; notebook diffs full of output blobs.

**Phase to address:**
Notebook scaffolding phase (first phase) — config cell, `.gitignore`, key handling, and the run-all discipline set up before any analysis code exists.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Summing whole-postcode populations for catchments | One join instead of area math | 2–4× demand overstatement; invalidates the core answer | Never |
| Radial buffers instead of drive-time isochrones | Free, reproducible, no API | Slightly wrong catchment shape (Yarra River severs the south) | Acceptable (already a logged decision) — but annotate the river caveat on maps |
| POA-level census instead of SA1/mesh block | Fewer files, simpler joins | Coarser apportionment error at 1 km radius | MVP only; upgrade to SA1 if 1 km catchment drives the decision |
| Raw Places counts as competitor supply | No cleaning work | Inflated competition → understated opportunity (or vice versa) | Never for the final answer; fine for a first-pass map |
| Hardcoded verified site coordinates | No geocoding dependency | None if commented with source + date | Acceptable — actually preferred after one-time verification |
| Single steady-state P&L year | Simpler model | Hides ramp-up losses and peak capital need | Never, given "limited startup capital" constraint |
| Skipping response caching "for now" | Faster to first result | API costs + rate limits + non-reproducible runs | Never — cache from day one |
| State-level Medicare benchmarks | Data on hand | Zero local signal dressed as local analysis | Only as clearly-labelled fallback with warning cell |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| ABS Data API | Parsing SDMX-JSON by hand; requesting `all` | Request SDMX-CSV with `labels=both`, tight dataKey filters, gzip headers, disk cache |
| ABS Data API | Assuming documented dataflow IDs exist | Discover via `/rest/dataflow`, pin flow ID + version + dimension order as constants |
| ABS geographies | Treating POA = postcode, or POA nests in SA3 | Use each dataset at native geography; population-weighted correspondence when converting |
| MBS quarterly stats | Downloading the state/MMM summary file | Use the **SA3 Summary** product; filter SA3 20604; check sheet names before building |
| MBS item values | Using pre-Nov-2023 or pre-Nov-2025 rebates/incentives | Date-stamp all items; model tripled BBI (all patients from 1 Nov 2025) and BBPIP 12.5% option |
| Google Places | Trusting counts at the 60-result cap | Grid subdivision + `place_id` dedupe; treat exactly-60 as truncation |
| Google Places | Immediate `next_page_token` use | Sleep ~2 s and retry `INVALID_REQUEST` before concluding no more pages |
| Google Geocoding | Re-geocoding the site every run | Geocode once, verify visually, cache/hardcode with provenance |
| Colab ↔ Windows | Drive-only paths | Environment-detecting config cell with `pathlib`; relative `data/` dir |
| PDF export | Assuming folium maps render in PDF | Folium is HTML/JS — export static maps (contextily/matplotlib or folium screenshot) for the PDF |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Loading full national POA shapefile every run | 1–2 min cell, Colab RAM pressure | Filter to VIC/peer POAs once, save as GeoPackage/parquet in cache | Every fresh runtime |
| ABS API broad queries | 504 timeouts, 10 MB cap | Tight dataKey filters; split by region; CSV + gzip | Any query near "all POAs × all variables" |
| Uncached Places loops over 10 postcodes × types × radii | Slow re-runs, $ cost, quota errors | Cache-first fetch pattern; `REFRESH` flag | ~3rd full re-run of the notebook |
| `gpd.overlay` on full national layers | Minutes-long cells | Clip to a bounding box around the study area first | National-scale inputs |
| Notebook outputs (folium maps) bloating the .ipynb | 50 MB+ file, git pain, Colab save failures | Strip outputs before commit; regenerate from cache | After a few map-heavy runs |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Places key committed to git or left in cell output | Key scraping → billing abuse (Places is $$$) | `.env` + `.gitignore`, Colab userdata, nbstripout, key restrictions + budget alerts in Cloud Console |
| Unrestricted API key | Any Google API billable on your key if leaked | Restrict key to Places + Geocoding APIs only |
| Caching raw API responses containing the key in URL params | Key leaks via cache files committed to repo | Hash cache keys; never store the key param in cached filenames/contents; gitignore `data/cache/` if unsure |
| Sharing the Colab notebook with outputs intact | Outputs may contain key fragments, Drive paths, personal info | Clear outputs before sharing; share the PDF, not the live notebook, with investors |

## UX Pitfalls

(Here "users" = the analyst re-running the notebook, and investors reading the report.)

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Analysis code interleaved with dead/superseded cells (v1 pattern) | Reader can't tell which result is authoritative | Fresh v2, one authoritative path per computation, teaching commentary in markdown not comments |
| False precision in exec summary | Investors over-trust, then discredit on first challenged number | Ranges + rounding; assumptions register up front |
| ML jargon in an investor doc | Signals naivety to quant-literate readers | Plain arithmetic demand model, clearly explained |
| Maps without the site pin / competitor overlay / river annotated | Reader can't sanity-check the catchment | Every map: site marker, buffer rings, competitor pins, river visible |
| Burying the go/no-go | Investors read page 1 only | Recommendation + 3 key sensitivities on the first page of the PDF |
| No "how to re-run" instructions | Notebook rots immediately | Top cell: environment setup, key setup, cache behaviour, expected runtime |

## "Looks Done But Isn't" Checklist

- [ ] **Catchment population:** Often missing area apportionment — verify a partially-intersecting postcode contributes < its full population, and 3 km buffer area ≈ 28.3 km².
- [ ] **Competitor counts:** Often missing dedupe/classification — verify no count equals exactly 60, no duplicate addresses, and the final list was eyeballed.
- [ ] **MBS data:** Often actually state-level — verify a dataframe row exists with SA3 == 20604 and the vintage/quarter is printed.
- [ ] **Revenue model:** Often uses gross billings — verify a service-fee % line exists and practice revenue ≈ 30–35% of billings.
- [ ] **Bulk-billing assumptions:** Often pre-Nov-2025 — verify BBI expansion and BBPIP 12.5% are at least addressed in scenarios.
- [ ] **Breakeven:** Often steady-state only — verify monthly ramp-up cash flow and peak capital requirement are outputs.
- [ ] **Reproducibility:** Often session-state-dependent — verify Restart & Run All succeeds, and succeeds again with network-off (cache-only) mode.
- [ ] **Keys:** Often in outputs — verify `git grep AIza` is clean and outputs are stripped.
- [ ] **Census staleness:** Often unadjusted — verify an ERP-based growth adjustment (or explicit caveat with quantified direction) exists.
- [ ] **PDF export:** Often has blank map placeholders — verify static map images render in the exported PDF.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| CRS error found late | LOW | Fix helper functions, re-run; results change but code structure survives |
| Whole-postcode summing shipped | MEDIUM | Rebuild apportionment; every downstream demand/market-share number changes — re-verify conclusions |
| Wrong Medicare file used | LOW-MEDIUM | Download SA3 Summary, swap loader, re-run demand rates |
| Places cost blowout | LOW | Add caching, restrict key, set budget alert; sunk cost only |
| Places counts capped at 60 | MEDIUM | Implement grid subdivision, re-fetch (one-time cost), re-dedupe |
| Billings-as-revenue P&L discovered after review | MEDIUM-HIGH | Restructure P&L; profitability conclusion likely flips — re-write exec summary |
| Key committed to git | MEDIUM | Revoke + reissue key immediately, purge from history (filter-repo), add restrictions |
| Notebook only runs in stale session | LOW-MEDIUM | Restart & Run All, fix NameErrors top-down, add config cell |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Notebook hygiene (state/paths/keys) | Phase 1: Scaffolding & config | Restart-and-run-all passes; `git grep AIza` clean; runs on Windows + Colab |
| CRS errors | Phase 2: Geospatial foundation | Buffer-area assertion cell (≈28.3 km² for 3 km) |
| Centroid vs address catchment | Phase 2: Geospatial foundation | Site pin visually verified; single coordinate constant used everywhere |
| ABS API dataflows/SDMX/limits | Phase 3: Census data | Cache-only re-run succeeds; POA 3067 values match local GCP file |
| POA/SA2/SA3 mismatch | Phase 3–4 boundary | Geography strategy markdown cell; per-capita rates within national benchmark range |
| Area apportionment | Phase 4: Catchment demand | v1-vs-v2 population comparison cell; partial postcodes contribute partial pop |
| State-level Medicare files | Phase 4: MBS/demand | SA3 20604 row exists; vintage printed |
| ML on tiny data | Phase 4: Demand model | No `sklearn` predictive fit in v2; arithmetic model documented |
| Census staleness / point estimates | Phase 4 + Phase 7 | ERP adjustment applied; demand reported as range |
| Places cap/dedupe/miscategorisation | Phase 5: Competitor mapping | No raw count == 60; dedupe + classification + manual review checkpoint |
| Places cost | Phase 5: Competitor mapping | Second full run makes zero API calls |
| Billings vs practice revenue | Phase 6: Financial model | Service-fee line present; practice revenue ≈ 30–35% of billings |
| MBS changes 2023–2025 | Phase 6: Financial model | Item values date-stamped; BBPIP scenario present |
| Ramp-up & fit-out capex | Phase 6: Financial model | Monthly cash flow; fit-out from $/sqm × floor plan area; peak capital output |
| Rent/assumption laundering | Phase 6–7 | Assumptions register + tornado sensitivity; exec summary caveats |
| PDF/map rendering | Phase 7: Reporting | Exported PDF reviewed page-by-page with all maps rendering |

## Sources

- v1 prototype audit: `C:\Users\josha\medical-clinic\johnston_st_v1.py` (whole-postcode summing lines 81–91; `s_lat` used line 69, defined line 495; KMeans on 3 rows lines 204–224; state-level Medicare sheets line 525+)
- ABS Data API user guide & troubleshooting (abs.gov.au): 30 s timeout, 10 MB response cap, 5,000-char dataKey limit, SDMX-CSV recommendation, Beta status — verified 2026-03
- MBS Online factsheets: "Bulk Billing in General Practice from 1 November 2023" (tripled BBI, new items 75870–85); "Bulk Billing Incentives – Changes to Eligibility" (1 Nov 2025 expansion to all Medicare-eligible patients); Dept of Health "Bulk Billing Practice Incentive Program registration now open" (1 Nov 2025, 12.5% quarterly incentive) — verified 2026-03
- Dept of Health "Medicare quarterly statistics – Statistical Area (SA3) Summary" (GP Non-Referred Attendances by SA3, Sept-qtr 2019-20 → Dec-qtr 2025-26, released Feb 2026)
- AIHW "Medicare-subsidised GP, allied health and specialist health care across local areas" (SA3-level, ~1–2 yr lag)
- GP practice economics: Medius Global GP-valuation benchmarks (RACGP standard 63–75% GP retention; service fees 30–35% now mid-market); Medical Republic (service fees typically 30–40%); Dept of Health 2025 bulk-billing impact modelling (30% practice fee "becoming the norm"); Pilot Partners / ATO benchmarks (40–45% upper bound for GP service fees) — verified 2026-03
- Fit-out costs: Design Yard 32 (Melbourne, $1,200–$1,800/sqm base); SoulMED 2026 guide ($1,850–$3,500/sqm; GP clinic 100–200 sqm ≈ $267k–$535k); EasyAsset ($1,200–$2,000+/sqm); RACGP Standards 5th ed. room requirements — verified 2026-03
- MJA 2024 (doi:10.5694/mja2.52562): SA3-level bulk-billing rates 46–99% across Australia in 2022 — context for local billing-mix assumptions
- Google Places API documented behaviour: 20 results/page, 3 pages max (60 cap), next_page_token propagation delay

---
*Pitfalls research for: healthcare site feasibility analytics (Johnston St medical clinic study)*
*Researched: 2026-03-02*
