# Stack Research

**Domain:** Australian healthcare location analytics — multi-site (VIC pilot) feasibility tool: site-input form, SA3-from-point spatial join, parameterised ABS/Places fetch, per-site report naming, delivered as a free-Colab notebook + executive PDF
**Researched:** 2026-07-07
**Confidence:** HIGH overall (each item flagged individually)
**Scope:** v2.0 multi-site additions ONLY. The v1.0 stack (Python 3.12, geopandas 1.1.3, shapely 2.1.2, pyproj 3.7.x, folium 0.20.0, pandas 2.2.x, matplotlib 3.10.x, jinja2 3.1.x, weasyprint ≥65, requests-cache ≥1.2, requests 2.32.x, openpyxl, numpy-financial, contextily, python-dotenv) is validated and NOT re-researched here. This doc covers only what is genuinely NEW or CHANGED for v2.0.

## TL;DR — what's genuinely new vs reuse

| v2.0 feature | New library? | Reuses v1.0 stack? |
|--------------|--------------|--------------------|
| Site-input form (street/state/postcode/FTE/peers) | **No** — stdlib `@dataclass` + Colab `#@param` form fields | Colab `#@param` pattern, `BASE_ASSUMPTIONS` dict pattern |
| SA3 auto-derivation from geocoded lat/lon | **No** — geopandas `sjoin(predicate="within")` already in stack | geopandas 1.1.3, shapely 2.1.2, pyproj 3.7.x |
| ASGS 2021 SA3 boundary file (data asset, not a library) | **New data asset** — one-time ~5 MB download, cached | geopandas `read_file()` |
| Parameterised ABS Data API fetch on arbitrary POA/SA3 | **No** — refactor v1.0 helper to accept `{geography, codes}` | requests-cache `CachedSession`, `format=csvfilewithlabels` |
| MGA zone handling for all-VIC | **No new lib** — pyproj already in stack; **decision required** (see §MGA zone) | pyproj 3.7.x |
| Multi-site report naming `feasibility_<postcode>_<street>.pdf` | **Optional new dep** — `python-slugify` (tiny) OR 5-line regex | pathlib |
| Geocoding arbitrary VIC address | **No** — same Google Geocoding API call as v1.0 | requests + CachedSession |
| clinic_pnl(a) + Jinja2/weasyprint report | **No** — unchanged from v1.0 | jinja2, weasyprint, matplotlib |

**Net new runtime dependencies: 0 required, 1 optional (`python-slugify`).** The v2.0 multi-site features are almost entirely a refactor/reuse of the v1.0 stack plus one new data asset (SA3 shapefile). This is the key finding: no heavy geospatial or form-framework additions are needed.

## Recommended Stack — v2.0 additions only

### Core Technologies (additions)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| (none) | — | — | The v1.0 core stack (geopandas/shapely/pyproj/pandas/requests-cache) already covers every v2.0 need: spatial join, CRS reprojection, parameterised HTTP fetch. **No new core library is required.** Confidence: HIGH |

### Supporting Libraries (additions)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-slugify | ≥8.0 (8.0.4 current, MIT, PyPI) | Safe filename slugs from street addresses for `feasibility_<postcode>_<street>.pdf` naming | **Optional.** Street addresses carry apostrophes, hyphens, unicode (e.g. "St Kilda Rd", "O'Connell St"). `slugify("292-296 Johnston St")` → `292-296-johnston-st`. Handles edge cases a naive regex misses (html entities, decimal/hex unicode, mixed scripts). Tiny pure-Python dep (uses `text-unidecode`). **Alternative:** a 5-line `re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')` regex is acceptable if avoiding deps — but misses unicode/punctuation edge cases. Confidence: HIGH on the library; MEDIUM on whether it's worth a dep vs regex. |
| stdlib `dataclasses` | Python 3.12 builtin | `SiteConfig` dataclass for the site-input form values | See §Site-input form pattern. No pip install. |

### Development Tools (additions)

| Tool | Purpose | Notes |
|------|-------|-------|
| Colab `#@param` form fields | Site-input form (street address, state, postcode, FTE count, peer postcodes) | Colab-native; renders a form UI in the cell sidebar; values reflect into Python variables on run. No widget framework needed for a static single-site config. See §Site-input form pattern. |
| ASGS 2021 SA3 shapefile (data asset) | SA3 boundary polygons for point-in-polygon spatial join | One-time download from ABS, cached in `data/cache/`. See §ASGS SA3 boundary file. |

## ASGS SA3 boundary file — verified source (Confidence: HIGH on source/page, MEDIUM on exact zip URL)

**Source page:** ABS Digital boundary files — ASGS Edition 3 (July 2021 – June 2026):
`https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-3-july-2021-june-2026/access-and-downloads/digital-boundary-files`

**File names (listed on that page):**
- `SA3_2021_AUST_GDA2020` (GDA2020 — use this one; matches the project's GDA2020 datum)
- `SA3_2021_AUST_GDA94` (legacy GDA94 — do not use)

**Expected direct-download URL** (ABS's consistent URL pattern for boundary files on that page):
```
https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-3-july-2021-june-2026/access-and-downloads/digital-boundary-files/SA3_2021_AUST_GDA2020.zip
```
> **Verify this exact URL at runtime** with a HEAD request before committing it to the notebook — ABS occasionally restructures download paths. The page itself is the canonical source; if the direct link 404s, download manually from the page and place in `data/cache/SA3_2021_AUST_GDA2020.zip`. Confidence: MEDIUM on the literal URL string (not live-verified); HIGH that the file exists on that page under that name.

**Format:** ESRI Shapefile (`.shp` + siblings in the zip) OR GeoPackage (`.gpkg`). Both are read by `geopandas.read_file()`. The shapefile is the documented download; a GeoPackage variant is also available via the ABS GeoPackages page (`https://www.abs.gov.au/census/guide-census-data/about-census-tools/geopackages`) if a single-file asset is preferred.

**Key columns (ASGS 2021 SA3):** `SA3_CODE_2021`, `SA3_NAME_2021`. The v1.0 notebook's hardcoded SA3 `20604` (Yarra) matches `SA3_CODE_2021`. Use `SA3_CODE_2021` (string, 5-digit) as the join key for ABS Data API dataKeys.

**Size:** SA3 is the coarsest useful ASGS layer for this project (~108 polygons nationally, ~50 in VIC) — the shapefile is a few MB. Trivial for free Colab. Do NOT pull SA1 or SA2 nationally for this step (SA1 is ~60k polygons, ~57 MB; SA2 is ~2.3k polygons, ~20 MB) — SA3 is the right granularity for the MBS/Medicare utilisation lookup that v1.0 hardcoded to SA3 20604.

**Alternative source (ArcGIS REST):** ABS also publishes SA3 as an ArcGIS MapServer: `https://geo.abs.gov.au/arcgis/rest/services/ASGS2021/SA3/MapServer` (spatial reference 3857 / Web Mercator). Usable via `geopandas.read_file(url, layer=...)` with the Esri FeatureServer driver, but the shapefile download is simpler, offline-cacheable, and matches the v1.0 "cache everything locally" pattern. Recommend the shapefile.

## SA3 auto-derivation from a geocoded point (Confidence: HIGH — pure reuse of v1.0 stack)

The v1.0 notebook already does exact-address geocoding (Google Geocoding API) and EPSG:7855 reprojection. The v2.0 addition is a single spatial join to derive the SA3 code from the geocoded lat/lon. **No new library** — geopandas `sjoin` + shapely predicates are already in the stack.

**Pattern:**
```python
import geopandas as gpd
from shapely import Point

# 1. Load SA3 boundaries (one-time, cached). GDA2020 = EPSG:7844.
sa3 = gpd.read_file(CACHE_DIR / "SA3_2021_AUST_GDA2020.zip")
#    -> sa3.crs == EPSG:7844 (GDA2020 geographic)

# 2. Build a point GeoDataFrame from the geocoded lat/lon (WGS84/EPSG:4326 from Google).
site_point = gpd.GeoDataFrame(
    {"site": [site_name]},
    geometry=[Point(lon, lat)],
    crs="EPSG:4326",
)

# 3. Reproject point to match SA3 CRS (both must share a CRS for sjoin).
site_point = site_point.to_crs(sa3.crs)   # EPSG:4326 -> EPSG:7844 (no datum shift; both GDA2020-based)

# 4. Point-in-polygon spatial join.
joined = site_point.sjoin(sa3, how="left", predicate="within")
sa3_code = str(joined["SA3_CODE_2021"].iloc[0])   # e.g. "20604" for Abbotsford
sa3_name = joined["SA3_NAME_2021"].iloc[0]        # e.g. "Yarra"
```

**Notes:**
- `predicate="within"` is correct for a point falling inside a polygon. `sjoin_nearest` is the fallback if a point lands exactly on a boundary (rare; geocoded addresses are interior).
- CRS matching is mandatory before `sjoin`. Reprojecting the single point is cheaper than reprojecting all SA3 polygons.
- The geocoded point comes back in WGS84 (EPSG:4326) from Google; SA3 GDA2020 shapefile is EPSG:7844. These differ only by the ~1.8 m GDA94→GDA2020 shift is NOT relevant here (4326 vs 7844 is a datum difference of ~1.8 m, but for SA3 assignment at catchment scale this is well inside any polygon — no boundary ambiguity). If strictness is wanted, reproject via `to_crs("EPSG:7844")` which pyproj handles natively.
- Cache the loaded `sa3` GeoDataFrame in memory across cells (module-level variable); the shapefile read is the only non-trivial cost and only happens once per run.

## Parameterised ABS Data API fetch (Confidence: HIGH — refactor of v1.0 pattern)

The v1.0 notebook hardcodes POA `3067` + 9 peers and SA3 `20604` (Yarra). v2.0 derives these from the geocoded point and passes them through. **No new library** — the `C21_{table}_{geography}` dataflow-ID pattern already documented in v1.0's STACK.md generalises directly to SA3.

**Dataflow IDs (pattern: `C21_{table}_{geography}`):**
- `C21_G01_SA3` — 2021 Census G01 Selected person characteristics, by SA3
- `C21_G02_SA3` — 2021 Census G02 Selected medians and averages, by SA3
- `C21_G04_SA3` — 2021 Census G04 Age by sex, by SA3 (for the demand model's age bands)
- Verify existence at runtime via `https://data.api.abs.gov.au/rest/dataflow?detail=allstubs` (the v1.0 notebook already does this introspection for POA flows).

**Datakey construction (parameterised):**
```python
# v1.0 hardcoded:  dataKey = "3067+3066+3121+...+3123"  (POA dimension)
# v2.0 parameterised:
def abs_datakey(codes: list[str]) -> str:
    return "+".join(codes)            # "+" = OR within a dimension

# POA: site postcode + user-supplied peer postcodes (optional)
poa_codes = [site_postcode] + (peer_postcodes or [])
poa_key   = abs_datakey(poa_codes)    # e.g. "3067+3066+3121"

# SA3: the single derived SA3 code (MBS/Medicare utilisation is one SA3)
sa3_key   = site_sa3_code             # e.g. "20604"

# Fetch through the existing CachedSession:
url = f"https://data.api.abs.gov.au/rest/data/C21_G01_POA/{poa_key}?format=csvfilewithlabels"
df  = pd.read_csv(io.StringIO(session.get(url).text))
```

**Refactor guidance:**
- Extract v1.0's inline ABS-fetch code into a `fetch_abs(flow_id, codes, session)` helper that takes `geography` ("POA" | "SA3") and a list of codes. The v1.0 notebook already introspects the datastructure for dimension order — keep that; do not hardcode dimension order.
- The `requests_cache.CachedSession` from v1.0 is reused unchanged. SA3 fetches cache identically to POA fetches (URL-keyed).
- Fallback: v1.0's GCP DataPack fallback is Abbotsford-specific (POA 3067). For v2.0 arbitrary sites, the GCP fallback does not generalise — the ABS Data API is the primary path, and a network failure should emit a visible warning and skip that section rather than fall back to a wrong-site DataPack. This matches PROJECT.md's "manual download fallback is out of scope for v2.0".

## MGA zone handling — CRITICAL FINDING (Confidence: HIGH)

**PROJECT.md states: "EPSG:7855 (MGA zone 55) stays valid for all VIC sites — no zone-awareness needed in v2.0." This is INCORRECT for far-western Victoria.**

**Verified facts (EPSG registry, epsg.org/crs_7855):**
- EPSG:7855 (GDA2020 / MGA zone 55) area of use: **Australia onshore/offshore between 144°E and 150°E.**
- MGA zone 55 central meridian: 147°E. Zone width: 6° (144–150°E).
- Victoria's longitude extent: **~140°57′E (VIC/SA border, due to the 1836–1914 surveying error — the intended 141°E meridian was placed ~3.6 km west) to ~150°E (Cape Howe area).**
- Therefore the **far-western strip of Victoria (≈141°E to 144°E) is in MGA zone 54 (EPSG:7854), NOT zone 55.** This strip includes Mildura, Swan Hill, Robinvale, Wentworth (VIC side), and the western Mallee/Wimmera (Horsham is ~141.6°E — borderline; Nhill ~141.6°E; Ouyen ~142°E).

**Practical impact:** Reprojecting a far-western VIC point to EPSG:7855 does not crash (pyproj will transform it), but the resulting coordinates are outside the zone's intended area of use and distortion grows with distance from the central meridian (147°E). For a site at 142°E, that's 5° from the central meridian — the scale factor error at the zone edge is ~1.0006 (0.06%), which for a 5 km buffer is ~3 m. **Not catastrophic for catchment population math, but technically out-of-spec and will confuse anyone checking the CRS against the site's longitude.**

**Two clean options for v2.0:**

| Option | What | Pros | Cons | Recommendation |
|--------|------|------|------|----------------|
| **A. Zone-55-only VIC pilot** | Keep EPSG:7855; document that v2.0 supports VIC sites east of 144°E only; reject/warn on far-western postcodes. | Matches PROJECT.md's "no zone-awareness" intent; zero code change to v1.0 reprojection; covers Melbourne + Geelong + Gippsland + north-east VIC (~95% of VIC population). | Excludes Mildura, Swan Hill, far Wimmera. A user entering a Mildura address gets a silent out-of-spec reprojection or a hard reject. | Acceptable if scope is honestly "Melbourne + eastern VIC pilot". **Must update PROJECT.md to reflect the 144°E boundary** — the current "all VIC" claim is wrong. |
| **B. Adopt EPSG:7899 (GDA2020 / Vicgrid)** | Switch the project's working CRS from EPSG:7855 to EPSG:7899 — a single Lambert Conic Conformal CRS purpose-built by the VIC Surveyor-General for state-wide spatial data. | **Covers ALL of Victoria** (bbox 140.96°E–150.04°E, per EPSG registry) — no zone edge cases, no zone-awareness logic, no far-west exclusion. One CRS for every VIC site. Vicgrid is the official VIC government projection (Vicmap basemaps use EPSG:7899). Standard parallels at -36° and -38° span Melbourne and most VIC population centres with minimal distortion. | Slightly higher local distortion than the local MGA zone for any single site (Lambert LCC vs Transverse Mercator) — but for 1–5 km catchment buffers the difference is sub-meter and irrelevant to population apportionment. Requires changing the v1.0 EPSG:7855 constant to EPSG:7899 and re-running the 28.27 km² sanity assertion (buffer areas will differ by a negligible fraction). | **Recommended for a genuine VIC-wide pilot.** Cleanest, no edge cases, no user-facing postcode rejection. The distortion trade-off is immaterial at catchment scale. |
| C. Zone-aware reprojection | Auto-select EPSG:7854 (zone 54) vs EPSG:7855 (zone 55) based on the geocoded point's longitude (`lon < 144 → 7854, else 7855`). | Most locally accurate; covers all VIC. | Adds branching logic; peer postcodes could span zones (a zone-54 site with zone-55 peers would need per-site CRS handling); more complexity for v2.0's single-site-per-run scope. | Overkill for v2.0. Note as the v2.1 approach if multi-state (zones 49–56) is added. |

**Recommendation: Option B (EPSG:7899 Vicgrid) for v2.0**, with Option A as the fallback if the team prefers to keep v1.0's EPSG:7855 unchanged. Either way, **PROJECT.md's "EPSG:7855 stays valid for all VIC sites" claim must be corrected** — it is factually wrong for ~141–144°E. No new library is needed for either option (pyproj 3.7.x already in stack handles both EPSG:7855 and EPSG:7899).

**If Option B is chosen, the v1.0 sanity assertion changes:**
- v1.0 asserts a 3 km buffer = 28.27 km² in EPSG:7855. In EPSG:7899 the same 3 km buffer will be ~28.27 km² ± a negligible Lambert distortion (sub-0.1%). Update the assertion tolerance, not the target value.

## Site-input form pattern (Confidence: HIGH)

**Recommendation: Colab `#@param` form fields populating a stdlib `@dataclass` — NOT ipywidgets, NOT pydantic.**

**Why `#@param` over ipywidgets:**
- The v2.0 form is a **static, single-site config** (street address, state, postcode, FTE count, optional peer postcodes). The options are not dynamic (no runtime-dependent dropdowns).
- Colab `#@param` renders a native form UI in the cell sidebar (text boxes, number inputs, dropdowns, checkboxes) with zero imports and zero widget-state management. Values reflect into Python variables on Run.
- ipywidgets (`widgets.Text`, `widgets.Dropdown`, etc.) are recommended by Colab **only for dynamic options** (dropdowns whose values depend on prior runtime state) — confirmed by Colab maintainers in github.com/googlecolab/colabtools issue #2407. For static config, `#@param` is simpler and the documented first choice.
- ipywidgets add a state-readiness hazard: the widget value is only available after the cell renders and the user interacts, which complicates "Restart & Run All". `#@param` values are set at cell-edit time and available immediately on run.

**Why `@dataclass` over pydantic:**
- The site config has ~5–6 scalar fields with trivial validation (postcode is 4 digits, FTE > 0, state == "VIC"). A stdlib `@dataclass` + a couple of `assert` statements or `__post_init__` checks covers this with **zero new dependencies**.
- pydantic v2 (≥2.x) would add a ~5 MB dependency (and its `pydantic-core` Rust extension) for validation that 3 lines of asserts handle. It is the right tool for a web API with nested/external input; it is overkill for a notebook config cell the author controls.
- The v1.0 notebook already uses a plain `BASE_ASSUMPTIONS` dict — a `@dataclass` is a small, clean upgrade that adds type hints and a constructor without changing the pattern.

**Pattern:**
```python
# @title Site configuration  { display-mode: "form" }
from dataclasses import dataclass, field

@dataclass
class SiteConfig:
    street_address: str          # "292-296 Johnston St"
    state: str = "VIC"           # v2.0 pilot: VIC only
    postcode: str = "3067"       # 4-digit string (leading zeros matter for some POAs)
    gp_fte: float = 5.0
    allied_health_fte: float = 1.0
    peer_postcodes: list[str] = field(default_factory=list)  # optional; empty = skip peer benchmarking

    def __post_init__(self):
        assert self.state == "VIC", f"v2.0 pilot is VIC-only; got {self.state!r}"
        assert len(self.postcode) == 4 and self.postcode.isdigit(), f"postcode must be 4 digits: {self.postcode!r}"
        assert self.gp_fte > 0, "gp_fte must be positive"

# Default = the v1.0 Abbotsford site (so v2.0 out-of-the-box reproduces v1.0)
SITE = SiteConfig(
    street_address="292-296 Johnston St",
    state="VIC",
    postcode="3067",
    gp_fte=5.0,
    allied_health_fte=1.0,
    peer_postcodes=["3066", "3121", "3068", "3070", "3078", "3079", "3101", "3122", "3123"],
)
```

**Colab `#@param` equivalent** (renders the form UI; the dataclass above is the typed wrapper):
```python
# @title Site configuration
street_address = "292-296 Johnston St"  #@param {type:"string"}
state = "VIC"  #@param ["VIC"]  # v2.0 pilot
postcode = "3067"  #@param {type:"string"}
gp_fte = 5.0  #@param {type:"number"}
peer_postcodes_str = "3066,3121,3068,3070,3078,3079,3101,3122,3123"  #@param {type:"string"}
peer_postcodes = [p.strip() for p in peer_postcodes_str.split(",") if p.strip()]
```
The `#@param` form is the user-facing input; the `SiteConfig` dataclass is the typed object the rest of the notebook consumes. This keeps v1.0's "single config cell" pattern (a v1.0 fix for v1's scattered hardcoded values) while adding a form UI.

## Multi-site report naming (Confidence: HIGH)

**Convention:** `feasibility_<postcode>_<street_slug>.pdf` (and `.html`).

**Examples:**
- `feasibility_3067_292-296-johnston-st.pdf` (Abbotsford default)
- `feasibility_3000_123-bourke-st.pdf` (Melbourne CBD)
- `feasibility_3121_100-church-st.pdf` (Richmond)

**Slug generation:**
```python
# Option 1: python-slugify (recommended for robustness)
from slugify import slugify
street_slug = slugify(SITE.street_address, lowercase=True, separator="-")
# "292-296 Johnston St" -> "292-296-johnston-st"

# Option 2: regex (zero-dependency fallback)
import re
street_slug = re.sub(r'[^a-z0-9]+', '-', SITE.street_address.lower()).strip('-')

report_name = f"feasibility_{SITE.postcode}_{street_slug}"
pdf_path  = REPORT_DIR / f"{report_name}.pdf"
html_path = REPORT_DIR / f"{report_name}.html"
```

**Why `python-slugify` over regex:**
- Street addresses contain apostrophes (`O'Connell St`), hyphens (`292-296`), unicode (`Café` St, rare but possible), and HTML entities (if any leak through). `slugify` normalises all of these; the regex handles ASCII alphanumerics only.
- `python-slugify` 8.0.4 is MIT-licensed, pure Python, ~20 KB + `text-unidecode` (also tiny). Negligible install cost in Colab.
- The regex is an acceptable fallback if the project wants zero new deps — the addresses a user enters will almost always be ASCII. The risk is a silent mangled filename on an edge-case address, not a crash.

**Recommendation:** add `python-slugify` to the pip install cell (it's one line, tiny, and removes a class of filename bugs). If the team prefers zero new deps, the regex fallback is documented and acceptable.

**Path safety:** always write reports to `REPORT_DIR` (a `pathlib.Path` under the project folder); never to CWD (v1.0 had a `Path.cwd()` Colab failure — fixed via `In[]` history lookup; v2.0 should use the explicit `REPORT_DIR` from the CONFIG cell).

## Installation (v2.0 delta)

```python
# In Colab — v1.0 install cell plus ONE optional line:
%pip install -q requests-cache contextily weasyprint python-dotenv numpy-financial
%pip install -q python-slugify          # NEW (optional) — report filename slugs
# Everything else (geopandas/shapely/pyproj/folium/pandas/matplotlib/jinja2) is preinstalled.
```

```bash
# Local Windows (venv) — mirror Colab; add python-slugify:
pip install "geopandas>=1.1,<2" "shapely>=2.1" "pyproj>=3.7" "folium>=0.20" ^
    "pandas>=2.2" matplotlib jinja2 requests requests-cache contextily ^
    weasyprint python-dotenv numpy-financial openpyxl python-slugify
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| stdlib `@dataclass` + `#@param` for site config | pydantic v2 `BaseModel` | If the config grows to nested/external-sourced input with complex cross-field validation, or if serialising to/from JSON for a future web UI. Overkill for a 6-field notebook form. |
| stdlib `@dataclass` + `#@param` for site config | ipywidgets (`widgets.Text`, `widgets.Dropdown`) | Only if dropdown options must be dynamic (runtime-dependent). Colab maintainers explicitly recommend `#@param` for static config. |
| `python-slugify` for report filenames | 5-line `re.sub` regex | If zero new deps is a hard rule. Acceptable; misses unicode/punctuation edge cases. |
| ABS SA3 shapefile (download + `read_file`) | ABS ArcGIS MapServer `geo.abs.gov.au/arcgis/rest/services/ASGS2021/SA3/MapServer` via `geopandas.read_file(url)` | If you want to skip the download step and stream the layer. Needs network on every run (or a separate cache); the shapefile matches the v1.0 "cache locally" pattern better. |
| EPSG:7899 (Vicgrid) for all-VIC | EPSG:7855 zone-55-only + reject far-west | If scope is honestly Melbourne + eastern VIC only. Must correct PROJECT.md's "all VIC" claim. |
| EPSG:7899 (Vicgrid) for all-VIC | Zone-aware 7854/7855 selection by longitude | The v2.1 approach for multi-state (zones 49–56). Overkill for v2.0 single-site VIC. |
| Parameterised `fetch_abs(flow, codes, session)` helper | Keep v1.0's inline per-flow fetch code | If you want minimal diff from v1.0. The helper is a pure refactor (no new dep) and makes POA-vs-SA3 and arbitrary codes clean. |

## What NOT to Use (v2.0-specific additions to the v1.0 list)

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| pydantic for the `SiteConfig` | Adds ~5 MB + Rust extension for 6 scalar fields with trivial validation; notebook-config overkill | stdlib `@dataclass` + `__post_init__` asserts |
| ipywidgets for the static site form | State-readiness hazard on Restart & Run All; overkill for non-dynamic options | Colab `#@param` form fields |
| SA1 or SA2 national shapefiles for SA3 derivation | SA1 ~57 MB / ~60k polygons, SA2 ~20 MB / ~2.3k polygons — unnecessary when SA3 (~5 MB / ~108 polygons) is the granularity the MBS data uses | ASGS 2021 SA3 shapefile only |
| ASGS GDA94 shapefiles (`SA3_2021_AUST_GDA94`) | Legacy datum; project standardised on GDA2020 in v1.0 | `SA3_2021_AUST_GDA2020` |
| Hardcoding EPSG:7855 and claiming all-VIC coverage | Zone 55 covers 144–150°E only; far-west VIC (141–144°E) is zone 54. PROJECT.md's current claim is wrong. | EPSG:7899 (Vicgrid) for all-VIC, OR document a 144°E eastern-VIC-only scope |
| `googlemaps` PyPI client for geocoding | (Carried from v1.0) wraps legacy endpoints only | Google Geocoding API via `requests` + CachedSession (v1.0 pattern) |

## Stack Patterns by Variant

**If the user enters a far-western VIC postcode (e.g. 3500 Mildura, ~142°E) under Option A (zone-55-only):**
- Emit a visible warning that the site is outside MGA zone 55 and results may be out-of-spec; OR hard-reject with a message pointing to v2.1.
- Because EPSG:7855 is only valid 144–150°E; silently reprojecting a 142°E point to zone 55 is technically out-of-spec.

**If the user enters a far-western VIC postcode under Option B (Vicgrid EPSG:7899):**
- Proceed normally — Vicgrid covers all of VIC (140.96–150.04°E).
- Because EPSG:7899 is the VIC Surveyor-General's state-wide projection, purpose-built for this.

**If the ABS SA3 shapefile download URL 404s:**
- Fall back to manual download from the ABS digital boundary files page; place `SA3_2021_AUST_GDA2020.zip` in `data/cache/` and load from there.
- Because ABS occasionally restructures download paths; the page is canonical, the direct link is a convenience.

**If the spatial join returns no SA3 match (point outside all SA3 polygons):**
- Warn that the geocoded point is outside VIC SA3 coverage (e.g. a border address geocoded to the SA side) and fall back to the postcode-derived SA3 via the ABS POA→SA3 correspondence, or skip the SA3-specific section with a warning.
- Because geocoding near state borders can return coordinates just outside VIC; the tool should degrade gracefully, not crash.

**If the user supplies no peer postcodes:**
- Skip the peer benchmarking section (PROJECT.md: "Peer benchmarking via user-supplied peer postcodes (optional; skipped if not provided)").
- Because peer benchmarking is optional in v2.0; the standalone verdict does not depend on it.

## Version Compatibility (v2.0 additions)

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| python-slugify 8.0.4 | Python ≥3.7 | Pure Python; uses `text-unidecode` (GPL/Artistic) by default or `Unidecode` via `python-slugify[unidecode]`. License note: text-unidecode is GPL — if that's a concern for the project, use the regex fallback. MIT-slugify itself is MIT. |
| ASGS 2021 SA3 shapefile (GDA2020) | geopandas 1.1.3, pyproj 3.7.x | Read via `gpd.read_file()`; CRS = EPSG:7844 (GDA2020 geographic). |
| EPSG:7899 (GDA2020 / Vicgrid) | pyproj 3.7.x | Lambert Conic Conformal (2SP); supported by pyproj since 2016. No version concern. |
| EPSG:7854 (GDA2020 / MGA zone 54) | pyproj 3.7.x | Only needed if Option C (zone-aware) is chosen; same pyproj as zone 55. |
| stdlib `dataclasses` | Python 3.12 builtin | No compat concern. |

## Sources

- https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-3-july-2021-june-2026/access-and-downloads/digital-boundary-files — ASGS 2021 SA3 shapefile source page; file names `SA3_2021_AUST_GDA2020` / `SA3_2021_AUST_GDA94` listed — HIGH (page verified via search; exact direct-download URL string is MEDIUM — verify at runtime)
- https://www.abs.gov.au/census/guide-census-data/about-census-tools/geopackages — ABS GeoPackage alternative for SA3 boundaries — HIGH
- https://geo.abs.gov.au/arcgis/rest/services/ASGS2021/SA3/MapServer — ABS ArcGIS REST SA3 layer (spatial ref 3857) — HIGH
- https://epsg.org/crs_7855/GDA2020-MGA-zone-55.html — EPSG:7855 area of use = 144°E–150°E — HIGH
- https://epsg.org/crs_7899/GDA2020-Vicgrid.html — EPSG:7899 GDA2020/Vicgrid, area = Australia-Victoria, bbox 140.96–150.04°E, Lambert Conic Conformal (2SP), scope "State-wide spatial data management" — HIGH
- https://spatialreference.org/ref/epsg/7899/ — EPSG:7899 WGS84 bounds 140.96, -39.2, 150.04, -33.98 — HIGH
- https://www.land.vic.gov.au/maps-and-spatial/data-services/vicmap-basemaps/technical-information — "VicGrid2020 projection EPSG:7899 has been chosen as the projection of choice as it is the most accurate projection with minimal distortions for the state of Victoria" — HIGH (VIC government source)
- https://www.land.vic.gov.au/maps-and-spatial/maps/how-to-access-a-map/map-grids-and-magnetic-information — MGA zone boundaries: zone 54 = 138–144°E, zone 55 = 144–150°E — HIGH
- https://www.ga.gov.au/scientific-topics/national-location-information/dimensions/border-lengths — VIC/SA border at 141°E (with 3.6 km surveying error history) — HIGH
- https://www.land.vic.gov.au/maps-and-spatial/first-time-here/geographic-facts — VIC western boundary coordinate 140°57'45"E — HIGH
- https://pypi.org/project/python-slugify/ — python-slugify v8.0.4, MIT, Python ≥3.7, unicode-aware slugify — HIGH
- https://github.com/un33k/python-slugify/ — slugify API + `text-unidecode` vs `Unidecode` backend note — HIGH
- https://github.com/googlecolab/colabtools/issues/2407 — Colab maintainers recommend `#@param` for static config, ipywidgets for dynamic options — HIGH
- https://prof-rossetti.github.io/intro-software-dev-python-book/notes/dev-tools/google-colab/form-inputs.html — Colab `#@param` field types (string, number, slider, date, dropdown, boolean) + ipywidgets comparison — HIGH
- https://colab.research.google.com/notebooks/forms.ipynb — Official Colab Forms notebook (canonical `#@param` reference) — HIGH
- https://docs.geopandas.org/en/stable/docs/reference/api/geopandas.GeoDataFrame.sjoin.html — `GeoDataFrame.sjoin(predicate="within")` for point-in-polygon — HIGH
- https://geopandas.org/en/stable/gallery/spatial_joins.html — geopandas spatial join examples (point→polygon attribute transfer) — HIGH
- https://www.abs.gov.au/statistics/application-programming-interfaces-apis/data-api-user-guide/worked-examples — ABS Data API datakey syntax (`+` = OR within dimension, `.` separates dimensions), `format=csvfilewithlabels` — HIGH (carried from v1.0)
- https://docs.sarahcgall.co.uk/scgElectionsAU/reference/get_abs_data.html — confirms `C21_G01_CED` / `C21_G02_CED` dataflow pattern; `C21_{table}_{geography}` generalises to SA3 — MEDIUM-HIGH (third-party but consistent with ABS naming)
- https://docs.pydantic.dev/latest/concepts/dataclasses/ — pydantic dataclass API (considered, rejected as overkill) — HIGH

---
*Stack research for: v2.0 multi-site feasibility tool (VIC pilot) — site-input form, SA3-from-point spatial join, parameterised ABS fetch, multi-site report naming*
*Researched: 2026-07-07*
