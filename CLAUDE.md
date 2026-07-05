<!-- GSD:project-start source:PROJECT.md -->
## Project

**Johnston St Medical Clinic Feasibility Study**

A professional-grade site feasibility analysis, delivered as a Colab notebook (`Johnston_St_v2.ipynb`) plus an executive PDF report, evaluating whether 292-296 Johnston St, Abbotsford VIC 3067 can support an independently profitable medical clinic (5 FTE GPs + 1 FTE allied health) alongside a Priceline Pharmacy (beauty/cosmetics focus). Built by and for a business analytics student learning healthcare location analytics, to an investor-presentation standard.

**Core Value:** Answer, with defensible data and transparent assumptions, one question: **can the clinic be profitable on its own at this site** — not as a script-driving vehicle for the pharmacy?

### Constraints

- **Environment**: Free Colab primary, local Windows compatible — no paid compute, no huge rasters
- **Budget**: Limited startup capital — fit-out cost and time-to-breakeven must be first-class model outputs
- **Data**: Public/licensed sources only, all cited — investor credibility and legality
- **API cost**: Google Places calls cost money — cache aggressively, make re-runs free
- **Rent assumption**: ~$100k AUD/year — flagged as a key sensitivity, not a confirmed figure
- **Census vintage**: 2021 Census is ~4-5 years old — note as caveat; Abbotsford has grown since
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Core Technologies
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12 (Colab 2025.10+ / 2026.01 runtime) | Runtime | Current Colab runtimes ship Python 3.12.12–3.12.13 on Ubuntu 22.04. Pin nothing below 3.10. **Confidence: HIGH** (verified at github.com/googlecolab/backend-info) |
| geopandas | 1.1.x (1.1.3 preinstalled in Colab) | Vector geospatial dataframes: POA polygons, buffer intersections, area apportionment | The standard. 1.1.x requires pandas ≥2.0, numpy ≥1.24, pyproj ≥3.5 — all satisfied in Colab. **Zero pip install needed in Colab.** Confidence: HIGH |
| shapely | 2.1.x (2.1.2 preinstalled) | Geometry ops: buffers, intersection, area | Shapely 2.x vectorised API; used by geopandas internally. Confidence: HIGH |
| pyproj | 3.7.x (preinstalled) | CRS transforms — critical: reproject GDA2020/WGS84 → **EPSG:7855 (GDA2020 / MGA zone 55)** before any metre-based buffer/area math | Buffering in degrees was the class of bug behind v1's catchment flaw. Confidence: HIGH |
| folium | 0.20.x (0.20.0 preinstalled) | Interactive Leaflet maps in the notebook (catchment rings, competitor pins) | Renders inline in Colab; geopandas `.explore()` uses it. Interactive only — NOT for the PDF (see PDF section). Confidence: HIGH |
| pandas | 2.2.x (preinstalled) | Everything tabular: census extracts, MBS tables, P&L model | Confidence: HIGH |
| requests + requests-cache | requests 2.32.x (preinstalled); requests-cache ≥1.2 (pip) | ABS Data API and Google Places calls with transparent on-disk caching | `requests_cache.CachedSession(backend="filesystem", cache_dir=...)` gives free re-runs of both APIs with ~3 lines. Cache dir lives in the project folder so it works in Colab (Drive) and Windows alike. Confidence: HIGH |
### Supporting Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| matplotlib | 3.10.x (preinstalled) | Static charts + static maps for the PDF report | All report figures. Folium can't go in a PDF; matplotlib can. |
| contextily | ≥1.6 (pip) | Static basemap tiles under matplotlib maps (OSM/CartoDB) | Only for report-quality static maps. Lightweight tile fetcher, not a heavy raster lib. Cache tiles. |
| mapclassify | preinstalled | Choropleth classification for `.explore()` | Optional, already in Colab. |
| jinja2 | 3.1.x (preinstalled) | HTML template for the executive report | Render metrics/tables/figures into a styled HTML doc. |
| weasyprint | ≥65 (pip) | HTML+CSS → executive PDF | Installs cleanly on Colab's Ubuntu 22.04 (pango present via apt: `apt install -y libpango-1.0-0 libpangocairo-1.0-0` if needed). Produces investor-grade paginated PDF with CSS control. |
| python-dotenv | ≥1.1 | Local Windows `.env` loading for `GOOGLE_PLACES_KEY` | Local runs only; no-op in Colab (see config pattern below). |
| numpy-financial | ≥1.0 (pip, tiny) | NPV / breakeven / payback math for the P&L | Optional — plain numpy also fine; use if you want `npv`/`irr` named functions for teaching clarity. |
| openpyxl | preinstalled | Read local GCP_POA3067.xlsx fallback files | Fallback census path only. |
### Development Tools
| Tool | Purpose | Notes |
|------|---------|-------|
| Colab `google.colab.userdata` | Secret storage in Colab | Key name `GOOGLE_PLACES_KEY`; user adds it once via the 🔑 sidebar. |
| `pathlib` + a single `CONFIG` cell | Environment-agnostic paths | Detect Colab via `"google.colab" in sys.modules`; set `DATA_DIR`/`CACHE_DIR` accordingly. No hardcoded `/content/drive/...` outside this cell (v1 flaw). |
| requests-cache filesystem backend | API response cache committed alongside notebook data | Makes ABS + Places re-runs free and offline-reproducible. |
## ABS Data API — verified specifics (Confidence: HIGH on URLs/IDs, MEDIUM on exact datakey order)
- All dataflows: `https://data.api.abs.gov.au/rest/dataflow?detail=allstubs`
- Data structure (to learn dimension order + codelists): `https://data.api.abs.gov.au/rest/datastructure/ABS/{id}?references=codelist`
- Data: `https://data.api.abs.gov.au/rest/data/{flowRef}/{dataKey}?format=csvfilewithlabels`
- `C21_G01_POA` — 2021 Census G01 Selected person characteristics, by Postal Area
- `C21_G02_POA` — 2021 Census G02 Selected medians and averages, by Postal Area
- Pattern generalises: `C21_{table}_{geography}` (e.g. `C21_G02_SA2`). Other useful tables for age structure / demand: `C21_G04_POA` (age by sex) — verify existence via the dataflow list at runtime.
- CSV-with-labels returns both dimension codes and human-readable names — ideal for a teaching notebook, zero SDMX parsing.
- `sdmx1` (PyPI `sdmx1`, ≥2.25) is the maintained SDMX client and has built-in `ABS` (SDMX-ML) source support — a fine alternative, but it adds an SDMX information-model learning curve the project doesn't need.
- `pandasdmx` is effectively unmaintained (superseded by its fork `sdmx1`) — do not use.
## Google Places API — use Places API (New) (Confidence: HIGH)
- **Legacy Places API is in "Legacy" status** (closed to new customers since March 2025; existing use discouraged). Use **Nearby Search (New)**: `POST https://places.googleapis.com/v1/places:searchNearby` with an `X-Goog-FieldMask` header.
- **Field masking is mandatory** and determines billing tier. Keep the mask minimal: `places.id,places.displayName,places.location,places.types,places.primaryType,places.rating,places.userRatingCount,places.businessStatus,places.formattedAddress`. Note: `rating`/`userRatingCount` push you into the **Pro SKU** — acceptable here; avoid Enterprise-tier fields (phone, website, opening hours) unless needed.
- **Pricing (verified, post-March-2025 model):** Nearby Search Pro = **US$32 per 1,000 requests with 5,000 free requests/month** (the old $200 credit is gone; each SKU now has its own free monthly cap). This project needs on the order of tens of requests — comfortably $0 **if cached**. Geocoding API (for the exact street address) = $5/1,000 with 10,000 free/month.
- **No pagination in Nearby Search (New)** — `maxResultCount` caps at 20 and there is no `pagetoken` (a change from legacy). Design around it: query per-type (`includedTypes` accepts multiple values: `doctor`, `medical_lab`, `pharmacy`, `physiotherapist`, `dentist`) and per-radius (1/3/5 km via `locationRestriction.circle`), then dedupe on `place.id`. If a single query saturates at 20 results, subdivide the circle. If free-text brand searches are needed (e.g. "Priceline"), use **Text Search (New)** (`places:searchText`, also $32/1k Pro, supports `pageToken` up to 60 results).
- **Caching strategy:** route all calls through the same `requests_cache` filesystem session (POST caching: enable `allowable_methods=("GET","POST")`), and additionally persist the deduped competitor GeoDataFrame to `data/cache/competitors.geojson` so analysis re-runs never touch the API. The v1 notebook's raw JSON responses can seed the cache for cross-checking.
- Do **not** use the `googlemaps` PyPI client — it wraps the legacy endpoints only.
## PDF report generation (Confidence: MEDIUM-HIGH)
- The deliverable is an *executive* report (maps, key metrics, go/no-go) — investors shouldn't see code cells. A templated report gives full layout control (cover page, headers, page numbers) and works identically in Colab and on Windows (`pip install weasyprint`; on Windows it needs the GTK runtime — if that's painful locally, generation can be Colab-only since Colab is primary).
- Folium maps are HTML/JS and won't render in any PDF path — the report must use static matplotlib maps (contextily basemap + geopandas plot).
## Config / secrets — dual-environment pattern (Confidence: HIGH)
- `.env` and `data/cache/` with API responses containing keys go in `.gitignore`. ABS cache responses contain no secrets and CAN be committed for reproducibility.
- `python-dotenv` ≥1.1 works fine on Windows; no OS-specific handling needed beyond `pathlib`.
## Installation
# In Colab — geopandas/shapely/pyproj/folium/pandas/matplotlib/jinja2 are PREINSTALLED.
# Single install cell:
# Optional (technical-appendix notebook PDF only):
# %pip install -q "nbconvert[webpdf]" && playwright install chromium
# Local Windows (venv) — mirror Colab versions:
## Alternatives Considered
| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Raw requests + `format=csvfilewithlabels` for ABS | `sdmx1` (≥2.25) client with built-in `ABS` source | If the project later needs many dataflows, codelist introspection as objects, or SDMX-ML validation. Overkill for ~3 Census tables. |
| requests-cache | Hand-rolled JSON file cache keyed by request hash | If you want the cache files human-readable for teaching; slightly more code, equally valid. |
| weasyprint templated report | `nbconvert --to webpdf` of a curated "report" notebook | If layout polish matters less than speed; acceptable but shows notebook chrome. |
| contextily static basemaps | Pure geopandas plots, no basemap | If tile fetching is flaky in Colab; report maps just look barer. |
| Nearby Search (New) per-type queries | Text Search (New) with text queries | For brand-name searches ("Priceline", "IPN medical centre") and when >20 results per query needed (pageToken to 60). |
## What NOT to Use
| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `pandasdmx` | Unmaintained; broken against modern pandas; superseded by its fork | `sdmx1`, or raw requests (recommended) |
| `https://api.data.abs.gov.au/data/...` URL pattern | Retired 29 Nov 2024; redirects today but not guaranteed | `https://data.api.abs.gov.au/rest/data/...` |
| Places API (Legacy) Nearby Search / `googlemaps` PyPI client | Legacy status since March 2025, closed to new customers; client wraps legacy only | Places API (New) `places:searchNearby` via requests POST + field mask |
| `nbconvert --to pdf` (LaTeX path) | Requires Pandoc + full TeX Live (~GBs, ~10+ min install in Colab every session) | weasyprint report; `--to webpdf` for appendix |
| rasterio / xarray / rioxarray / GDAL raster stack | Heavy, slow to install, zero raster data in this project | Vector-only geopandas; contextily for basemap tiles |
| osmnx / OSRM / Distance Matrix isochrones | Explicitly out of scope (cost, reproducibility) | 1/3/5 km radial buffers in EPSG:7855 |
| Buffering/area math in EPSG:4326 (degrees) | Root cause class of v1's catchment population error | Reproject to EPSG:7855 (GDA2020 / MGA55) first; areas in m² |
| scikit-learn demand models on <30 rows | v1's Random Forest on 3–10 rows is statistically meaningless | Transparent arithmetic demand model: age-band consult rates × apportioned population |
| ABS Data Explorer scraping / undocumented endpoints | Fragile; the documented REST API covers the need | `data.api.abs.gov.au/rest` |
## Stack Patterns by Variant
- Fall through to local 2021 GCP POA DataPack files (already on hand) with a printed warning cell.
- Because the notebook must be demonstrable on demand (investor setting), never hard-fail on a network call.
- Generate the PDF in Colab only; keep local runs producing the HTML report.
- Because Colab is the primary environment and the HTML is byte-identical input.
- Split the circle into smaller sub-circles or split `includedTypes` into separate queries and dedupe on `place.id`.
- Because Nearby Search (New) has no pagination — silent undercounting of competitors would bias the whole demand model.
## Version Compatibility
| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| geopandas 1.1.3 | pandas 2.2.x, numpy 2.0.x, shapely 2.1.2, pyproj 3.7.x, folium 0.20.0 | Exactly Colab's current (2026.01) preinstalled set — verified via googlecolab/backend-info pip-freeze. Don't pip-upgrade these in Colab; you'll trigger dependency resolution churn. |
| geopandas 1.1.x | Python ≥3.10 | Colab is 3.12; fine. |
| requests-cache ≥1.2 | requests 2.32.x | Enable `allowable_methods=("GET","POST")` to cache Places POST calls. |
| weasyprint ≥65 | Ubuntu 22.04 (Colab) | Pango/cairo present or apt-installable; Windows needs GTK runtime (fallback: Colab-only PDF). |
| Colab runtime pinning | 2026.01 / 2025.10 | Colab supports pinning past runtime versions — pin the notebook's runtime for reproducible demos. |
## Sources
- https://github.com/googlecolab/backend-info (pip-freeze) — Colab preinstalled versions: Python 3.12, geopandas 1.1.3, shapely 2.1.2, folium 0.20.0 — HIGH confidence
- https://geopandas.org/en/stable/docs/changelog.html — geopandas 1.1.x release line + min deps — HIGH
- https://www.abs.gov.au/statistics/application-programming-interfaces-apis/data-api-user-guide (+ worked examples, tutorials pages) — base URL migration (29 Nov 2024), `/rest/data/{flow}/{key}?format=csvfilewithlabels` syntax, dataflow/datastructure endpoints — HIGH
- https://github.com/Bigred97/abs-mcp — confirms `C21_G01_POA` / `C21_G02_POA` as live dataflow IDs — MEDIUM-HIGH (third-party but consistent with ABS naming)
- https://sdmx1.readthedocs.io — sdmx1 maintained with built-in ABS source; pandasdmx superseded — HIGH
- https://developers.google.com/maps/billing-and-pricing/pricing + /march-2025 — Nearby Search Pro $32/1k, 5,000 free/month Pro SKU, 10,000 free Essentials; legacy status — HIGH
- https://developers.google.com/maps/documentation/places/web-service/legacy/migrate-nearby — Nearby Search (New): POST, mandatory FieldMask, no pagetoken, maxResultCount 20 — HIGH
- https://nbconvert.readthedocs.io/en/latest/usage.html — webpdf vs LaTeX PDF paths — HIGH
- Exact C21_* datakey dimension order NOT verified live (no network exec available) — flagged MEDIUM; notebook must introspect the datastructure at runtime.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
