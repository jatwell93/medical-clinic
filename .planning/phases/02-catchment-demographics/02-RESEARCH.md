# Phase 2: Catchment & Demographics - Research

**Researched:** 2026-07-05
**Confidence:** HIGH on patterns/libraries; MEDIUM on exact ABS dataflow IDs for SA1/G04/ERP (require runtime verification — by design, per ROADMAP research flag)

## Summary

Phase 2 is technically a well-trodden geopandas + ABS Data API workflow. The headline risk is **ABS dataflow discovery**: `C21_G01_POA` / `C21_G02_POA` are confirmed live (curated in the `abs-mcp` reference project), but `C21_G04_POA` (age by sex), `C21_G01_SA1` (SA1 total persons), and the ERP-by-SA2 dataflow ID need runtime verification via `/rest/dataflow?detail=allstubs`. Each has a documented fallback so the notebook never hard-fails (PIPE-04). The geospatial side (geocode → reproject EPSG:7855 → buffer → `gpd.overlay` intersection → area-weighted apportionment) is fully specified in ARCHITECTURE.md and verified against the geopandas 1.1.x overlay docs. contextily's `add_basemap(ax, crs=..., source=cx.providers.CartoDB.Positron)` is the PDF-basemap primitive; folium is inline-only.

## 1. ABS Data API — dataflow verification (MEDIUM confidence — runtime-verify)

**Confirmed live dataflows** (from `Bigred97/abs-mcp` curated list, cross-referenced with ABS user guide):
- `C21_G01_POA` — 2021 Census G01 Selected person characteristics, by Postal Area ✓
- `C21_G02_POA` — 2021 Census G02 Selected medians and averages, by Postal Area ✓
- `C21_G02_SA2` — G02 at SA2 ✓ (confirms the `C21_{table}_{geography}` generalisation)

**Runtime-verification required (D-11, D-12, D-23):**
- `C21_G04_POA` — 2021 Census G04 Age by Sex by POA. The `C21_{table}_{geography}` pattern + G04 being a standard Census table makes existence *highly likely*, but it is NOT in the abs-mcp curated list. **Verify at runtime** via the dataflow list endpoint, then introspect `/rest/datastructure/ABS/C21_G04_POA?references=codelist` for dimension order.
- `C21_G01_SA1` — G01 at SA1. **MEDIUM-LOW confidence.** The `scgElectionsAU` R package docs note "SA1 and CED level data is available for select datasets (SEIFA, some Census tables)" — implying NOT all Census tables are published at SA1 via the API. **Fallback path (D-12):** download the 2021 GCP SA1 DataPack (Census DataPacks are explicitly available at SA1 level per abs.gov.au/census/find-census-data/datapacks) and parse `2021Census_G01_AUST_SA1.csv` (or the VIC subset) for `Total_P_P` (total persons). Schema parity required (D-17).
- ERP by SA2 dataflow: `ABS_ANNUAL_ERP_ASGS2021` — Estimated Resident Population, annual by state and sub-state geography (confirmed in abs-mcp curated list). This is the ERP source for D-19..D-24. Latest release: 2023-24 FY (released March 2025). **Verify at runtime** that SA2-level rows are returned for the Yarra SA2; introspect the datastructure for the REGION dimension codes.

**API mechanics (HIGH confidence, verified against ABS user guide):**
- Base URL: `https://data.api.abs.gov.au/rest/data/{flowRef}/{dataKey}?format=csvfilewithlabels`
- `flowRef` accepts `ABS,{id},latest` (agency + version optional, default to latest)
- `dataKey` is positional, dot-separated: `{dim1}+{code1}+{code2}.{dim2}.{dim3}`. `+` = OR within a dimension; omitting all codes for a dimension = wildcard. **Wrong dimension order returns empty data, not an error** (PITFALLS.md Pitfall 4) — must introspect the datastructure first.
- `format=csvfilewithlabels` returns CSV with both codes and human-readable labels — pandas reads directly, zero SDMX parsing.
- 30s timeout / 10MB cap per response → filter tightly (D-08: spatial-filter SA1s first; only request the 10 peer POAs, not all).
- All calls go through the Phase 1 `CachedSession` (no `requests.get` from analysis cells — ARCHITECTURE.md Pattern 1).

**Discovery pattern (run once, record as constants):**
```python
# 1. List all dataflows — cached
flows = session.get("https://data.api.abs.gov.au/rest/dataflow?detail=allstubs").json()
# 2. Filter to C21_*_POA / C21_*_SA1 / ABS_*ERP*ASGS2021
# 3. For each flow of interest, introspect DSD for dimension order
dsd = session.get("https://data.api.abs.gov.au/rest/datastructure/ABS/C21_G04_POA?references=codelist").json()
# 4. Record dimension order as a constant: e.g. C21_G04_POA_DIMS = ["MEASURE", "POA", "SEX", "AGE", "FREQ", "TIME"]
```

## 2. Google Geocoding API (HIGH confidence)

**Request format (legacy Geocoding API — still the standard for address→coord):**
```
GET https://maps.googleapis.com/maps/api/geocode/json?address={url-encoded address}&key={GOOGLE_PLACES_KEY}
```
**Response shape:**
```json
{
  "results": [
    {
      "formatted_address": "...",
      "geometry": {
        "location": {"lat": -37.7990, "lng": 145.0034},
        "location_type": "ROOFTOP"
      },
      "place_id": "ChIJ..."
    }
  ],
  "status": "OK"
}
```
**Pricing:** $5/1,000 requests, 10,000 free/month. One call for this project → $0.
**Cache key:** `geocode_<slugified-address>.json` (ARCHITECTURE.md Pattern 1 — address changes → key changes automatically).
**Verification (D-31, PITFALLS.md Pitfall 3):** print `site_lat, site_lon` + a one-line "visually verify this pin on the map below" instruction, with the folium map immediately after. Known anchor: Johnston St × Hoddle St corner, Abbotsford. Expected coords ≈ (-37.799, 145.003) — use as a sanity range assertion, not a hardcoded override.
**Keyless fallback:** if `GOOGLE_PLACES_KEY` is empty AND a cached geocode response exists, load from cache. If neither, hard-fail with a clear message (geocoding is a hard dependency — no fallback address source).

## 3. Geospatial catchment — buffers, overlay, apportionment (HIGH confidence)

**CRS convention (PITFALLS.md Pitfall 1, D-09):**
- All metric ops (buffer, area, distance, centroid) in **EPSG:7855** (GDA2020 / MGA zone 55 — Melbourne is in MGA zone 55).
- All display/mapping in **EPSG:4326** (WGS84 — folium + contextily input).
- ABS shapefiles ship in GDA2020 geographic (EPSG:7844) — must reproject to 7855 before buffering.

**Buffer construction:**
```python
site_point = gpd.GeoDataFrame(
    [{"name": "site"}], geometry=[Point(site_lon, site_lat)], crs="EPSG:4326"
)
site_metric = site_point.to_crs("EPSG:7855")
buffers = {
    r: site_metric.buffer(r) for r in BASE_ASSUMPTIONS["catchment_radii_m"]  # [1000, 3000, 5000]
}
# Sanity assertion (D-09, GEO-02)
assert abs(buffers[3000].area.iloc[0] / 1e6 - 28.27) < 0.1, \
    f"3km buffer area {buffers[3000].area.iloc[0]/1e6:.2f} km² ≠ 28.27 km² (π×3²)"
```

**SA1 apportionment (D-01 — the headline v1 fix):**
```python
# 1. Load SA1 geometry (data/local/SA1_2021_AUST_GDA2020.zip)
sa1 = gpd.read_file(PROJECT_ROOT / "data/local/SA1_2021_AUST_GDA2020.zip")
sa1 = sa1[sa1["STE_NAME21"] == "Victoria"].to_crs("EPSG:7855")

# 2. Spatial-filter SA1s intersecting the 5km buffer (D-08 — beat 30s timeout)
sa1_in_5k = sa1[sa1.geometry.intersects(buffers[5000].iloc[0])]

# 3. Fetch SA1 total persons (C21_G01_SA1 via API, or SA1 GCP DataPack fallback)
sa1_pop = fetch_sa1_total_persons(sa1_in_5k["SA1_CODE21"].tolist())  # tidy DataFrame

# 4. Per-ring apportionment: area-weighted
for r in BASE_ASSUMPTIONS["catchment_radii_m"]:
    ring = gpd.GeoDataFrame(geometry=[buffers[r].iloc[0]], crs="EPSG:7855")
    inter = sa1_in_5k.overlay(ring, how="intersection")
    inter["frac"] = inter.geometry.area / sa1_in_5k.set_index("SA1_CODE21").loc[inter["SA1_CODE21"]].geometry.area.values
    ring_pop = (inter["frac"] * inter["Total_P_P"]).sum()
```
**Uniform-density caveat (D-05):** printed markdown note + Yarra River line annotated on every catchment map. The assumption likely *overstates* population in the Yarra/industrial slice of Abbotsford.

**v1-vs-v2 comparison (D-06, success criterion #2):** reproduce v1's naive whole-postcode sum (sum full POA population for any POA touching the buffer) inline, then show grouped bar chart + side-by-side table per ring: `ring | v1 naive | v2 apportioned | diff | % overstatement`. Expected: v1 inflates 2–4× (PITFALLS.md Pitfall 2).

## 4. POA peer benchmarking & demographics (HIGH confidence)

**POA geometry (D-07):** `data/local/POA_2021_AUST_GDA2020_SHP.zip` (on hand). Filter to VIC + 10 peer POAs once, cache filtered GeoPackage to `data/cache/poa_vic_peers.gpkg`. ABS API SDMX-Geo as documented fallback if zip missing.

**G01 variables (D-13):** total persons (`Total_P_P`), sex split (`M_P`, `F_P`), dwelling counts (`Total_Dwll_D`). Supports DEMO-03 demand/supply indicators.
**G02 variables (D-14):** `Median_age_persons`, `Median_tot_prsnl_inc_weekly`, `Median_tot_hshld_inc_weekly`. Core peer-comparison columns.
**G04 variables (D-11, D-18):** age by sex in ABS standard 5-year bands (0-4, 5-9, … 80-84, 85+). Aligns with AIHW/MBS age-band attendance rates for Phase 3 demand model. 65+ share derived: sum bands ≥ 65.

**Local fallback (D-15, D-16, D-17):**
- Trigger: auto on any API failure (timeout, 5xx, empty data). Print warning cell naming the missing data + local file substituted.
- 3067 populated from `data/local/GCP_POA3067.xlsx`; 9 peer rows marked N/A with printed warning that peer comparison is degraded.
- Schema parity: local fallback parses GCP files into the SAME tidy DataFrame schema the API path produces (column names, dtypes, row-per-POA shape). Downstream code is source-agnostic.

## 5. ERP scaling — census staleness (MEDIUM-HIGH confidence)

**Source (D-19):** ABS Regional Population by SA2 (catalog 3218.0) via `ABS_ANNUAL_ERP_ASGS2021` dataflow.
**Vintage (D-20):** latest available = 2023-24 FY (released March 2025). Scale 2021 census → 2024 estimate (~3-year adjustment).
**Method (D-21 — Claude's discretion):** uniform Yarra SA2 growth rate is the MVP choice. The catchment is largely within Yarra SA2, so a single rate applied to all 10 peer POAs is defensible. POA-SA2 correspondence file is the rigorous alternative (deferred per CONTEXT.md).
**Application (D-24):** apply ERP scaling to BOTH the catchment population (GEO-03 output) AND the peer-postcode benchmarking table (DEMO-02/03) — each peer scaled by its own SA2 growth rate.
**Caveat display (D-22):** printed markdown note + table column showing both raw 2021 and ERP-scaled values side by side. Round aggressively (PITFALLS.md Pitfall 15 — false precision).

## 6. Maps & charts (HIGH confidence)

**Folium interactive (D-25, D-30):** inline only, NOT in PDF. Layers: site pin + 1/3/5 km buffer rings + POA boundaries (shaded by apportionment share) + Yarra River line + peer postcode markers. No competitors (Phase 3).

**Static matplotlib + contextily (D-27, D-29):** one figure per ring (1km, 3km, 5km), each zoomed to its ring. 3 figures total. Basemap: `cx.providers.CartoDB.Positron` (clean investor-report aesthetic — D-28 discretion applied).
```python
import contextily as cx
fig, ax = plt.subplots(figsize=(8, 8))
buffers_4326[r].boundary.plot(ax=ax, color="red")
site_4326.plot(ax=ax, color="black", markersize=50)
cx.add_basemap(ax, crs="EPSG:4326", source=cx.providers.CartoDB.Positron)
ax.set_title(f"Catchment — {r//1000} km ring")
```
**Tile caching:** contextily caches tiles in-memory per session; for disk persistence use `cx.bounds2raster(...)` for the report figures. Tiles are not committed (regenerable).

**Peer comparison charts (D-29):** 2×2 bar chart grid — population (ERP-scaled), median age, 65+ share, median income. POA 3067 highlighted in each chart.

**Geocode verification (D-31):** print coords + "visually verify this pin on the map below" instruction, with folium map immediately after.

## 7. SA1 shapefile acquisition (HIGH confidence)

**File:** `SA1_2021_AUST_GDA2020.zip` from ABS digital boundary files (abs.gov.au/statistics/standards/australian-statistical-geography-standard/asgs/edition-3-july-2021-june-2026/access-and-downloads/digital-boundary-files).
**Naming convention (verified):** `SA1_2021_AUST_GDA2020` — `{geography}_{year}_AUST_{datum}`.
**Storage:** `data/local/` (gitignored, documented in `.env.example` — same pattern as POA zip).
**Download mechanism (Claude's discretion):** direct URL vs ABS download page. The ABS download page requires accepting a terms-of-use click before the direct link is exposed; the direct URL pattern is `https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard/asgs/edition-3-july-2021-june-2026/access-and-downloads/digital-boundary-files/...` but the exact path is unstable. **Recommendation:** document the manual download step in `.env.example` (like the POA zip), and have the notebook print a clear "download SA1 shapefile from <URL> and place at data/local/SA1_2021_AUST_GDA2020.zip" message if the file is missing. Do NOT hard-fail — fall back to POA-level apportionment with a printed warning (degraded but functional).

## 8. Integration with Phase 1 (HIGH confidence)

**Reuse, do not redefine:**
- `CachedSession` (§1) — all ABS + geocode calls route through it. `allowable_methods=("GET","POST")` already enabled.
- `BASE_ASSUMPTIONS` (§0) — already holds `site_address`, `catchment_radii_m`, `peer_postcodes`. Phase 2 may ADD keys (`erp_vintage_year`, `sa1_shapefile_name`, `assert_3km_buffer_km2`, `catchment_pop_plausible_range`) with citation comments per PIPE-05. Must not break the `{**BASE_ASSUMPTIONS, **overrides}` scenario pattern (Phase 1 D-10).
- `PROJECT_ROOT` + `CACHE_DIR` (§0) — path resolution for `data/local/` and `data/cache/`.
- `FORCE_REFRESH` flag (§0) — threads through the `CachedSession`; Phase 2 inherits it.

**New notebook sections (per ARCHITECTURE.md §-flow):**
- §1.2 geocode (new) → produces `site_lat, site_lon` consumed by §2 buffer construction and (Phase 3) Places search centres.
- §2 catchment (new) → produces buffer GeoDataFrames + SA1 apportionment weights, consumed by §3 demographics (catchment age profile) and Phase 3 §5 demand model.
- §3 demographics (new) → produces catchment pop/age/income by ring + peer benchmarking table, consumed by Phase 3 §5 demand model and Phase 5 reporting.

**Notebook generation pattern (Phase 1 RESEARCH.md §4):** extend `scripts/create_v2_notebook.py` OR append cells directly via a new generator script. Phase 1 used `json.dump` (not nbformat) — Phase 2 must follow the same pattern (consistency, no extra dependency). **Recommendation:** create `scripts/extend_v2_notebook.py` that loads `Johnston_St_v2.ipynb`, appends §1.2/§2/§3 cells, and writes back. Re-runnable.

## Validation Architecture

**Dimension 8 (Nyquist validation) for Phase 2:**

The phase's validation is geospatial correctness + data-source-agnosticism + cache reproducibility. Concrete assertions:

1. **Buffer area assertion (GEO-02, D-09a):** 3km buffer area in EPSG:7855 ≈ 28.27 km² (π×3²), tolerance ±0.1 km². Hard-fail on violation.
2. **Catchment population plausibility (D-09b, PITFALLS.md Pitfall 2):** apportioned 3km-ring population in plausible inner-Melbourne range (~80–110k). Hard-fail outside range with a clear message pointing to the apportionment logic.
3. **v1-vs-v2 comparison present (D-06, success criterion #2):** grep notebook source for a v1 naive sum reproduction + a comparison table/chart. The teaching moment showing v1 inflated 2–4×.
4. **Cache hit assertion (PIPE-04):** after second run with `FORCE_REFRESH=False`, ABS G01/G02 responses have `from_cache == True`.
5. **Source-agnostic schema (D-17, ARCHITECTURE.md):** API path and GCP fallback path emit DataFrames with identical columns/dtypes. Verify with a schema-comparison assertion when both paths are exercised (or a structural check that the fallback parser produces the same column names).
6. **Geocode verification (D-31, PITFALLS.md Pitfall 3):** notebook prints `site_lat, site_lon` + a "visually verify" instruction, with a folium map in the immediately-following cell. Grep notebook source for both.
7. **No-degree-buffer assertion (PITFALLS.md Pitfall 1):** grep notebook source — no `.buffer(` call on a GeoDataFrame whose `.crs` is EPSG:4326/7844 at the moment of the call. All buffer ops happen after `.to_crs("EPSG:7855")`.
8. **ERP scaling present (DEMO-04):** grep notebook source for ERP fetch + scaling logic + a printed caveat. Peer table has both raw 2021 and ERP-scaled columns.
9. **G04 verification (D-11):** notebook contains a runtime check that queries the dataflow list for `C21_G04_POA` and branches to the documented fallback if absent.
10. **Keyless-run assertion:** with `GOOGLE_PLACES_KEY=""` and populated cache, the notebook runs to completion of §3 demographics without raising (ABS + geocode-from-cache). Places (Phase 3) not yet reached.

## Resolved Questions

1. **ERP dataflow ID:** `ABS_ANNUAL_ERP_ASGS2021` (confirmed in abs-mcp curated list). Verify at runtime that SA2-level rows are returned for Yarra SA2.
2. **Basemap provider:** `cx.providers.CartoDB.Positron` — clean investor-report aesthetic (D-28 discretion applied).
3. **SA1 census source:** primary = `C21_G01_SA1` via API (existence unverified — MEDIUM-LOW confidence); fallback = 2021 GCP SA1 DataPack CSV (`2021Census_G01_AUST_SA1.csv`). Both produce the same tidy schema.
4. **v1 comparison source:** reproduce v1's naive whole-postcode sum inline (3 lines) rather than hardcoding a documented constant — the teaching moment is stronger when readers see the flawed logic next to the fixed logic.
5. **Notebook extension pattern:** create `scripts/extend_v2_notebook.py` (load → append §1.2/§2/§3 cells → write back) rather than modifying `create_v2_notebook.py`. Keeps Phase 1 generator frozen, Phase 2 generator re-runnable independently.

## Open Questions (none blocking — all have documented fallbacks)

1. **C21_G04_POA existence** — runtime-verify via dataflow list. Fallback: `C21_G04_SA2` + apportion into catchment, or local GCP for 3067's 65+ share with peers marked N/A (D-12).
2. **C21_G01_SA1 existence** — runtime-verify. Fallback: 2021 GCP SA1 DataPack CSV (D-03).
3. **`ABS_ANNUAL_ERP_ASGS2021` dimension order** — runtime-verify via datastructure introspection. The REGION dimension codes for SA2s need to be filtered to Yarra SA2 (code 206041001 per ASGS Edition 3 — verify at runtime).
4. **SA1 shapefile download mechanism** — direct URL unstable; document manual download in `.env.example`. Fallback: POA-level apportionment with printed warning (degraded).

## RESEARCH COMPLETE

Phase 2 is ready for planning. All implementation patterns are documented with code examples. All open questions have documented fallbacks (no hard-fails). The runtime-verification items (C21_G04_POA, C21_G01_SA1, ERP dimensions) are by design — the ROADMAP research flag explicitly notes the dataKey dimension order was not verified live.
