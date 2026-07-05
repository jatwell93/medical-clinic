# Phase 3 Research — Demand & Competitors

**Domain:** Healthcare site feasibility analytics (Australian GP demand + Google Places competitor mapping)
**Researched:** 2026-07-06
**Confidence:** HIGH on data URLs/types/benchmarks (verified against official docs); MEDIUM on AIHW Excel sheet structure (JS-rendered data tab, not directly inspectable); HIGH on Places API (New) specifics (verified against current Google docs)

---

## Critical Corrections to Prior Research

Three findings in this research **contradict** claims in STACK.md / 03-CONTEXT.md. These must be reflected in the plan:

### Correction 1: `rating` / `userRatingCount` are ENTERPRISE SKU, not Pro SKU

**STACK.md claims:** "rating/userRatingCount push you into the Pro SKU — acceptable here"
**Reality (verified against Google docs 2026-07):** `places.rating` and `places.userRatingCount` trigger the **Nearby Search Enterprise** SKU, NOT Pro.

| SKU | Price/1k | Free/month | Fields |
|-----|----------|------------|--------|
| Nearby Search Pro | $32.00 | 5,000 | `id`, `displayName`, `location`, `types`, `primaryType`, `businessStatus`, `formattedAddress`, `addressComponents`, etc. |
| Nearby Search Enterprise | $35.00 | **1,000** | `rating`, `userRatingCount`, `currentOpeningHours`, `nationalPhoneNumber`, `priceLevel`, `websiteUri`, etc. |
| Nearby Search Enterprise + Atmosphere | $40.00 | 1,000 | `reviews`, `servesBeer`, `editorialSummary`, etc. |

**Impact on D-05/D-06 budget:** The project's ~180 requests (15 site + ~150 peer) still fit within the 1,000 free Enterprise requests/month. But the margin is tighter (1,000 vs 5,000) and overage costs $35/1k vs $32/1k. **Recommendation: DROP `rating` and `userRatingCount` from the field mask.** They are not needed for competitor counting/classification — `displayName`, `primaryType`, `businessStatus`, and `formattedAddress` are sufficient and keep the call in the Pro SKU tier ($32/1k, 5,000 free/month). If review-count signals are wanted later, they can be fetched via a separate Place Details call for the ~10-20 ambiguous rows only.

### Correction 2: AIHW SA3 age bands are 0-24 / 25-44 / 45-64 / 65+, NOT 0-14 / 15-64 / 65+

**D-02 / 03-CONTEXT.md claims:** "per-capita rates by age band (0-14, 15-64, 65+) at SA3 level"
**Reality (verified from AIHW technical notes):** At SA3 level, the AIHW report disaggregates by these age groups only: **0-24, 25-44, 45-64, 65+**. The finer 0-14 / 15-24 / 25-44 / 45-64 / 65-79 / 80+ split is only available at PHN level, not SA3.

**Impact on D-02/D-03:** The demand model must map Phase 2's ABS 5-year age bands to the AIHW SA3 4-band structure (0-24, 25-44, 45-64, 65+), not the 3-band structure in the current `BASE_ASSUMPTIONS["consults_per_capita_yr"]`. The `consults_per_capita_yr` dict in the params cell needs updating to 4 keys matching AIHW SA3 bands. The AIHW "services per 100 people" measure is the per-capita multiplier.

### Correction 3: AIHW latest edition is 2026 (covering 2024-25 data), not 2022-23

**03-CONTEXT.md / FEATURES.md cite:** AIHW 2022-23 as the vintage
**Reality:** The AIHW report was updated **26 Mar 2026** and now covers 2017-18 to **2024-25**. Citation: AIHW (2026). The 2022-23 edition is the prior release. The data still has a ~1-2 year lag (2024-25 data published March 2026), but it's newer than the research docs assumed.

---

## Standard Stack

Libraries for Phase 3. All are either preinstalled in Colab or already installed in Phase 1.

| Library | Version | Purpose | Why This |
|---------|---------|---------|----------|
| `requests` + `requests-cache` | 2.32.x / ≥1.2 | All Places API (New) POST calls route through the Phase 1 `CachedSession` (already constructed in §1.1) | Already wired with `allowable_methods=('GET','POST')`. No new HTTP boundary. **Confidence: HIGH** |
| `pandas` | 2.2.x | MBS xlsx parsing, AIHW Excel parsing, competitor DataFrame ops, demand arithmetic | Preinstalled. Standard for tabular. **Confidence: HIGH** |
| `openpyxl` | preinstalled | Read `.xlsx` files (MBS SA3 summary, AIHW data tables) | Preinstalled. Required for pandas `.read_excel()`. **Confidence: HIGH** |
| `geopandas` | 1.1.3 | Competitor GeoDataFrame construction, buffer-point spatial joins (which competitors fall in which ring) | Preinstalled. Already used in Phase 2. **Confidence: HIGH** |
| `shapely` | 2.1.2 | Point-in-polygon tests for competitor-to-ring assignment | Preinstalled. Used by geopandas. **Confidence: HIGH** |
| `rapidfuzz` | ≥3.10 (pip) | Fuzzy-dedupe of competitor listings by name+address (Pitfall 9) | MIT-licensed (vs FuzzyWuzzy GPL), C++-fast, drop-in `fuzz.token_sort_ratio` API. ~100-200 rows = instant. **Confidence: HIGH** |
| `folium` | 0.20.0 | Interactive competitor map (D-15) | Preinstalled. Already used in Phase 2. **Confidence: HIGH** |
| `matplotlib` + `contextily` | 3.10.x / ≥1.6 | 3 static competitor map figures for PDF (D-15) | Already used in Phase 2 for catchment maps. Same pattern. **Confidence: HIGH** |

### What NOT to install
- **`googlemaps`** PyPI client — wraps legacy Places API only; project uses Places API (New) via raw `requests.post`
- **`fuzzywuzzy`** — GPL-licensed, unmaintained; use `rapidfuzz` instead
- **`scikit-learn`** for demand modelling — Pitfall 14; transparent arithmetic only
- **`scrapy`/`beautifulsoup4`** for competitor data — Google Places is the licensed source; no scraping

---

## Architecture Patterns

### Pattern 1: Places API (New) client with saturation subdivision

The core competitor acquisition function. Replaces v1's legacy `google_nearby_places` (which used `maps/api/place/nearbysearch/json` with `next_page_token` pagination).

```python
PLACES_URL = "https://places.googleapis.com/v1/places:searchNearby"

# Pro SKU only — drops rating/userRatingCount (Enterprise tier, Correction 1)
PLACES_FIELD_MASK = (
    "places.id,"
    "places.displayName,"
    "places.location,"
    "places.types,"
    "places.primaryType,"
    "places.primaryTypeDisplayName,"
    "places.businessStatus,"
    "places.formattedAddress,"
    "places.shortFormattedAddress,"
    "places.addressComponents"
)

def places_nearby(lat, lon, radius_m, included_types):
    """Single Nearby Search (New) call. Returns list of place dicts. Max 20."""
    body = {
        "includedTypes": included_types,
        "maxResultCount": 20,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lon},
                "radius": float(radius_m)
            }
        },
        "languageCode": "en-AU"
    }
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_KEY,
        "X-Goog-FieldMask": PLACES_FIELD_MASK
    }
    resp = session.post(PLACES_URL, json=body, headers=headers)  # Phase 1 CachedSession
    resp.raise_for_status()
    return resp.json().get("places", [])

def places_nearby_saturated(lat, lon, radius_m, included_types):
    """Query per-type × per-ring; auto-subdivide 2×2 grid on 20-result cap (D-05)."""
    results = places_nearby(lat, lon, radius_m, included_types)
    if len(results) < 20:
        return results  # Not saturated

    # Saturated → subdivide into 2×2 grid of smaller circles
    # Sub-circle radius = original_radius / 2 (covers the diameter, overlaps at edges)
    sub_radius = radius_m / 2
    offsets = [
        (sub_radius * 0.5, sub_radius * 0.5),    # NE
        (sub_radius * 0.5, -sub_radius * 0.5),   # SE
        (-sub_radius * 0.5, sub_radius * 0.5),   # NW
        (-sub_radius * 0.5, -sub_radius * 0.5),  # SW
    ]
    sub_results = []
    for dx, dy in offsets:
        sub_lat, sub_lon = offset_meters(lat, lon, dx, dy)
        sub_results.extend(places_nearby(sub_lat, sub_lon, sub_radius, included_types))

    # If any sub-circle also saturates at 20, repeat once (max depth = 2)
    if any(len(places_nearby(*offset_meters(lat, lon, dx, dy), sub_radius, included_types)) >= 20
           for dx, dy in offsets):
        # Second subdivision pass on saturated sub-circles only
        for dx, dy in offsets:
            sub_lat, sub_lon = offset_meters(lat, lon, dx, dy)
            r = places_nearby(sub_lat, sub_lon, sub_radius, included_types)
            if len(r) >= 20:
                # Sub-subdivide this quarter
                for sdx, sdy in offsets:
                    ss_lat, ss_lon = offset_meters(sub_lat, sub_lon, sdx * 0.5, sdy * 0.5)
                    sub_results.extend(places_nearby(ss_lat, ss_lon, sub_radius / 2, included_types))

    # Dedupe on place.id
    seen = {}
    for p in results + sub_results:
        pid = p.get("id")
        if pid and pid not in seen:
            seen[pid] = p
    return list(seen.values())

def offset_meters(lat, lon, dx_m, dy_m):
    """Offset lat/lon by dx/dy meters. Good enough for <10km in Melbourne."""
    dlat = dy_m / 111_320
    dlon = dx_m / (111_320 * abs(math.cos(math.radians(lat))))
    return lat + dlat, lon + dlon
```

**Cache key format** (per ARCHITECTURE.md): `places_<type>_<lat:.4f>_<lon:.4f>_<radius>` — the Phase 1 `CachedSession` handles this automatically by hashing the POST body + URL. No manual cache key needed for Places calls (unlike the manual `cached_fetch()` used for ABS).

### Pattern 2: Competitor classification via keyword rules

```python
# Corporate GP brands (from gpzoo.com.au 2025 — verified site counts)
CORPORATE_GP_BRANDS = {
    "ipn": "IPN (Sonic Healthcare)",
    "myhealth": "Amplar Health (Myhealth/Medibank)",
    "family doctor": "Family Doctor",
    "forhealth": "ForHealth",
    "healius": "ForHealth (formerly Healius)",
    "bupa": "Bupa (Partnered Health)",
    "better medical": "Amplar Health (Better Medical)",
    "jupiter health": "Jupiter Health",
    "ochre": "Ochre Health",
    "sonic": "Sonic Healthcare",
    "qualitas": "Qualitas",
    "health&co": "ForHealth (Health&Co)",
}

# Pharmacy brands (D-07)
PHARMACY_BRANDS = {
    "chemist warehouse": "Chemist Warehouse",
    "priceline": "Priceline",
    "amcal": "Amcal",
    "terrywhite": "TerryWhite Chemmart",
    "terry white": "TerryWhite Chemmart",
    "chemmart": "TerryWhite Chemmart",
    "sigma": "Sigma (API)",
    "pharmacy 4 less": "Pharmacy 4 Less",
    "national pharmacy": "National Pharmacy",
    "soul pattinson": "Soul Pattinson",
    "discount drug stores": "Discount Drug Stores",
}

# Exclude keywords — these are NOT GP clinics
EXCLUDE_KEYWORDS = [
    "skin", "cosmetic", "dermatology", "laser", "beauty",
    "vet", "veterinary", "animal",
    "optometry", "optometrist", "eyecare",
    "podiatry", "podiatrist",
    "audiology", "hearing",
    "radiology", "imaging", "x-ray", "xray",
    "pathology", "laboratory", "collection centre",
    "specialist", "paediatric", "obstetric", "gynaecology",
    "psychiatry", "psychiatric",
]

def classify_place(name, primary_type, types_list):
    """Classify a place into: gp_corporate, gp_independent, pharmacy, allied_health, exclude, ambiguous."""
    name_lower = name.lower()

    # Check pharmacy first (most specific)
    for brand, label in PHARMACY_BRANDS.items():
        if brand in name_lower:
            return "pharmacy", label

    if primary_type == "pharmacy" or "pharmacy" in (types_list or []):
        return "pharmacy", "Independent"

    # Check exclude bucket
    for kw in EXCLUDE_KEYWORDS:
        if kw in name_lower:
            return "exclude", kw

    # Check corporate GP
    for brand, label in CORPORATE_GP_BRANDS.items():
        if brand in name_lower:
            return "gp_corporate", label

    # Check independent GP clinic indicators
    gp_clinic_indicators = ["medical centre", "medical center", "general practice",
                            "gp clinic", "gp practice", "medical clinic", "family practice",
                            "health centre", "health center", "community health"]
    if any(kw in name_lower for kw in gp_clinic_indicators):
        return "gp_independent", "Independent"

    if primary_type in ("doctor", "medical_center", "medical_clinic"):
        # Could be GP or specialist — flag for manual review
        return "ambiguous", "doctor-type but no clinic indicator in name"

    # Allied health
    allied_indicators = ["physio", "physiotherapy", "psychology", "psychologist",
                         "dental", "dentist", "chiropractic", "chiropractor",
                         "occupational therapy", "dietitian", "dietician",
                         "speech", "acupuncture", "osteopath"]
    if any(kw in name_lower for kw in allied_indicators):
        return "allied_health", "Allied Health"
    if primary_type in ("physiotherapist", "dentist", "dental_clinic", "chiropractor"):
        return "allied_health", "Allied Health"

    return "ambiguous", f"Unclassified (primaryType={primary_type})"
```

### Pattern 3: Fuzzy-dedupe with rapidfuzz

```python
from rapidfuzz import fuzz

def fuzzy_dedupe_competitors(places_gdf, name_threshold=85, address_threshold=80):
    """Dedupe individual-practitioner listings that share a practice address.
    Uses rapidfuzz.token_sort_ratio on normalised name + formattedAddress.
    Keeps the first occurrence (by place.id), merges duplicates into a 'duplicates' list."""
    keep = []
    seen = []
    duplicates = []

    for idx, row in places_gdf.iterrows():
        name_norm = str(row.get("displayName", "")).lower().strip()
        addr_norm = str(row.get("formattedAddress", "")).lower().strip()
        is_dup = False

        for kept in seen:
            name_sim = fuzz.token_sort_ratio(name_norm, kept["name"])
            addr_sim = fuzz.token_sort_ratio(addr_norm, kept["addr"])
            # Match if name is very similar AND address is very similar
            if name_sim >= name_threshold and addr_sim >= address_threshold:
                is_dup = True
                duplicates.append({
                    "kept_id": kept["id"],
                    "dup_id": row.get("id"),
                    "name": row.get("displayName"),
                    "name_sim": name_sim,
                    "addr_sim": addr_sim,
                })
                break

        if not is_dup:
            keep.append(idx)
            seen.append({"id": row.get("id"), "name": name_norm, "addr": addr_norm})

    deduped = places_gdf.loc[keep].copy()
    return deduped, duplicates
```

**Threshold rationale:** `token_sort_ratio` ≥ 85 on names catches "Dr John Smith" vs "John Smith Medical" (word-order independent). Address ≥ 80 catches "123 Johnston St" vs "123 Johnston Street, Abbotsford VIC 3067" (partial address variations). These thresholds are conservative — better to over-flag and let the manual-review checkpoint (D-11) catch false positives than to miss real duplicates.

### Pattern 4: Demand model — transparent arithmetic (no ML)

```python
def compute_demand(catchment_age_profile, aihw_rates_per_100, ring_pop):
    """Age-adjusted annual consult demand for a catchment ring.

    catchment_age_profile: dict of age_band → population (from Phase 2 §3, mapped to AIHW bands)
    aihw_rates_per_100: dict of age_band → services per 100 people (from AIHW SA3 data)
    ring_pop: total population in the ring (ERP-scaled, from Phase 2)
    """
    total_demand = 0
    for band, pop in catchment_age_profile.items():
        rate = aihw_rates_per_100.get(band, 0)
        total_demand += pop * (rate / 100.0)
    return total_demand  # annual GP consults demanded in this ring
```

### Pattern 5: Competitor GeoDataFrame persistence (D-08)

```python
# After dedupe + classification, persist to GeoJSON
competitors_gdf = gpd.GeoDataFrame(
    competitor_records,
    geometry=[Point(lon, lat) for lon, lat in zip(lons, lats)],
    crs="EPSG:4326"
)
competitors_gdf.to_file(CACHE_DIR / "competitors.geojson", driver="GeoJSON")
# Re-runs: load from file, skip API entirely
geojson_path = CACHE_DIR / "competitors.geojson"
if geojson_path.exists() and not FORCE_REFRESH:
    competitors_gdf = gpd.read_file(geojson_path)
    print(f"[cache] loaded {len(competitors_gdf)} competitors from {geojson_path.name}")
```

---

## Don't Hand-Roll

| Problem | Do NOT hand-roll | Use instead |
|---------|-------------------|-------------|
| Fuzzy string matching for dedupe | Custom Levenshtein / `difflib.SequenceMatcher` loops | `rapidfuzz.fuzz.token_sort_ratio()` — C++-fast, MIT-licensed, handles word-order differences |
| Excel file parsing | CSV conversion / manual XML parsing | `pandas.read_excel(engine="openpyxl")` — handles multi-sheet xlsx natively |
| Point-in-polygon for ring assignment | Manual coordinate math | `geopandas.sjoin(gdf_points, gdf_buffers, predicate="within")` — vectorised spatial join |
| HTTP caching for Places POST | Manual JSON file write/read per call | Phase 1 `CachedSession` with `allowable_methods=('GET','POST')` — already constructed in §1.1 |
| GeoJSON persistence | Manual dict → JSON serialisation | `geopandas.GeoDataFrame.to_file(driver="GeoJSON")` — handles geometry + attributes |
| Distance offset for grid subdivision | Custom geodesic formulas | Simple `lat += dy/111320` approximation — accurate enough for <10km at Melbourne's latitude |
| Folium map with layer control | Manual Leaflet JS | `folium.Map()` + `FeatureGroup` per ring — same pattern as Phase 2 catchment map |
| Static map with basemap | Manual tile fetching | `contextily.add_basemap()` — same pattern as Phase 2 static figures |

---

## Common Pitfalls

### Pitfall 8 (verified): Nearby Search (New) 20-result cap, NO pagination

**Verified against Google docs (2026-07):** `maxResultCount` "Must be between 1 and 20 (default) inclusive." There is **no `pageToken` field** in Nearby Search (New) — this is a fundamental change from the legacy API. The 60-result/3-page legacy cap is gone; the new cap is 20 per request with no pagination mechanism.

**Verification step:** Assert no single `places_nearby()` call returns exactly 20 results without triggering subdivision. If `len(results) == 20`, treat as saturated and subdivide.

### Pitfall 9 (verified): Duplicate/miscategorised places

**`type=doctor` returns specialists, individual practitioners, and multi-listing per clinic.** The classification rules (Pattern 2 above) handle this, but the manual-review checkpoint (D-11) is the safety net.

**Verification steps:**
- Assert no duplicate `place.id` values in the final GeoDataFrame
- Assert no `formattedAddress` appears 3+ times (individual practitioner red flag)
- Print the ambiguous-rows table inline (D-11) — user reviews outside the notebook
- GP-per-1,000 density should be in the range 0.8-2.0 FTE/1,000 (sanity check vs ~1.17 VIC average)

### Pitfall 6 (verified): State-level Medicare file has NO SA3 sheet

**Confirmed:** `data/local/medicare-quarterly-statistics-primary-care-service-type-summary-march-quarter-2025-26(1).xlsx` has sheets `['Contents', 'State', 'Modified Monash', 'Primary Care Service Types']` — no SA3 data. This is the D-04 fallback only, used with a loud warning.

**Verification step:** Assert the loaded SA3 MBS dataframe contains a row where SA3 code == 20604. If the SA3 file is missing and the state fallback is used, print the warning banner per D-04.

### Pitfall 10 (verified): Places cost from uncached re-runs

**Verification step:** After the first complete run, set `FORCE_REFRESH=False` and re-run §4. Assert zero API calls are made (all cache hits). Check `session.cache.size()` before and after.

### Pitfall 14 (verified): ML theatre

**Verification step:** Assert no `sklearn` import in Phase 3 cells. The demand model is `sum(pop_band × rate_band)` — pure arithmetic, traceable to cited inputs.

### NEW PITFALL: AIHW SA3 age bands don't match the params cell

The current `BASE_ASSUMPTIONS["consults_per_capita_yr"]` has keys `{"0-14": 4.4, "15-64": 5.1, "65+": 11.0}`. The AIHW SA3 data uses bands `0-24, 25-44, 45-64, 65+`. **The params cell must be updated** to 4 keys matching AIHW SA3 bands, with values sourced from the AIHW data (not guessed). The Phase 2 ABS 5-year age bands must be aggregated to match these 4 bands before multiplying.

### NEW PITFALL: Enterprise SKU cost creep

If `rating` or `userRatingCount` are included in the field mask, every Nearby Search call bills at the Enterprise rate ($35/1k, 1,000 free/month) instead of Pro ($32/1k, 5,000 free/month). With ~180 calls this is still within the free tier, but subdivision can push the count up (15 site + 60 subdivision + 150 peer = ~225 calls). **Drop rating/userRatingCount from the mask** to stay in Pro tier.

---

## Code Examples

### Example 1: MBS SA3 data loader with state fallback (D-01, D-04)

```python
import pandas as pd
from pathlib import Path

# D-01: SA3 20604 MBS via manual download
# Latest: "Medicare quarterly statistics – Statistical Area (SA3) Summary (March quarter 2025–26)"
# URL: https://www.health.gov.au/resources/publications/medicare-quarterly-statistics-statistical-area-sa3-summary-march-quarter-2025-26
# Download: /sites/default/files/2026-05/medicare-quarterly-statistics-statistical-area-sa3-summary-march-quarter-2025-26.xlsx
# Published: 25 May 2026. Contains GP Non-Referred Attendances by SA3, Sept-qtr 2019-20 → Mar-qtr 2025-26.
# Manual download → data/local/ (gitignored, like SA1 shapefile in Phase 2)

MBS_SA3_FILENAME = BASE_ASSUMPTIONS.get("mbs_sa3_filename",
    "medicare-quarterly-statistics-statistical-area-sa3-summary-march-quarter-2025-26.xlsx")

def load_mbs_sa3():
    """Load SA3-level MBS GP Non-Referred Attendance data. Fallback to state with warning (D-04)."""
    sa3_path = DATA_LOCAL_DIR / MBS_SA3_FILENAME

    if sa3_path.exists():
        # Read the SA3 sheet — verify sheet names first (Pitfall 6)
        xl = pd.ExcelFile(sa3_path)
        print(f"[mbs] SA3 file sheets: {xl.sheet_names}")
        # Expected sheets include 'SA3' or similar — verify at runtime

        # Filter to SA3 20604 Yarra
        df = pd.read_excel(sa3_path, sheet_name="SA3")  # sheet name verified at runtime
        sa3_yarra = df[df["SA3"].astype(str) == "20604"]
        if sa3_yarra.empty:
            print("⚠ WARNING: SA3 20604 not found in file. Check SA3 column name.")
        print(f"[mbs] SA3 20604 Yarra: {len(sa3_yarra)} quarters loaded")
        return sa3_yarra, "sa3"
    else:
        # D-04: State fallback with LOUD warning
        state_path = DATA_LOCAL_DIR / "medicare-quarterly-statistics-primary-care-service-type-summary-march-quarter-2025-26(1).xlsx"
        print("═" * 70)
        print("⚠  STATE BENCHMARK, NOT LOCAL — SA3 20604 data not found.")
        print("⚠  Download the SA3 Summary file from health.gov.au")
        print("⚠  and place in data/local/. Demand signal = VIC average, not Yarra.")
        print("═" * 70)
        df = pd.read_excel(state_path, sheet_name="State")
        vic = df[df["State"] == "VIC"]
        return vic, "state_fallback"
```

### Example 2: AIHW age-band rates loader (D-02)

```python
# D-02: Age-band GP attendance rates from AIHW
# Dataset: "Medicare-subsidised GP, allied health and specialist health care across local areas"
# Latest edition: updated 26 Mar 2026, covers 2017-18 to 2024-25
# URL: https://www.aihw.gov.au/reports/primary-health-care/medicare-subsidised-gp-allied-health-specialist
# Data tab: https://www.aihw.gov.au/reports/primary-health-care/medicare-subsidised-gp-allied-health-specialist/data
# Also on Regional Data Hub: catalogue.data.infrastructure.gov.au/dataset/rdh-medicare-subsidised-gp-allied-health-and-specialist-health-care-across-local-areas
# Format: downloadable Excel data tables (JS-rendered Data tab — download manually)
# SA3 age groups: 0-24, 25-44, 45-64, 65+ (NOT 0-14/15-64/65+ — see Correction 2)
# Measure: "services per 100 people" by age band at SA3 level
# Citation: AIHW (2026) — accessed [date]

# Manual download → data/local/ (same pattern as MBS SA3 file)
AIHW_FILENAME = BASE_ASSUMPTIONS.get("aihw_age_band_filename",
    "aihw-medicare-subsidised-gp-allied-health-2024-25-data-tables.xlsx")

def load_aihw_sa3_rates():
    """Load AIHW SA3-level GP attendance rates by age band.
    Returns dict: {age_band: services_per_100_people} for SA3 20604 Yarra."""
    path = DATA_LOCAL_DIR / AIHW_FILENAME
    if not path.exists():
        print("⚠ WARNING: AIHW age-band data not found. Using national average fallback.")
        # Fallback: national average ~6.8 attendances/person/year (AIHW 2022)
        # Split approximately across age bands (MJA/ABS data)
        return {"0-24": 4.5, "25-44": 5.5, "45-64": 7.5, "65+": 12.0}, "national_fallback"

    xl = pd.ExcelFile(path)
    print(f"[aihw] sheets: {xl.sheet_names}")

    # Find the SA3 GP attendances sheet — verify at runtime
    # Expected: a sheet with SA3 codes, age bands, and "services per 100 people"
    df = pd.read_excel(path, sheet_name=0)  # adjust sheet name at runtime

    # Filter to SA3 20604
    sa3_yarra = df[df["SA3"].astype(str) == "20604"]

    # Extract rates by age band (column structure verified at runtime)
    rates = {}
    for band in ["0-24", "25-44", "45-64", "65+"]:
        # Column name pattern verified at runtime — may be "0-24" or "0_24" etc.
        col = [c for c in df.columns if band.replace("-", "") in str(c).replace("-", "")]
        if col:
            rates[band] = float(sa3_yarra[col[0]].iloc[0])
        else:
            print(f"⚠ Age band '{band}' column not found in AIHW data")

    return rates, "aihw_sa3"
```

### Example 3: Required market share — three framings (D-13)

```python
def compute_required_market_share(annual_demand, existing_capacity, clinic_capacity,
                                   ring_pop, consults_per_patient_yr=5.0):
    """D-13: Three framings side-by-side. No ML, pure arithmetic (Pitfall 14).

    annual_demand: age-adjusted GP consults demanded in ring (from demand model)
    existing_capacity: estimated existing GP consult capacity in ring (D-10 range)
    clinic_capacity: 5-FTE clinic annual consult capacity (~25-30k)
    ring_pop: total population in ring
    consults_per_patient_yr: ~5 (AIHW national average ~6.8, but regular patients ~5)
    """
    unmet_demand = max(annual_demand - existing_capacity, 0)

    return {
        "share_of_total":   clinic_capacity / annual_demand * 100 if annual_demand else 0,
        "share_of_unmet":   clinic_capacity / unmet_demand * 100 if unmet_demand else float('inf'),
        "patients_needed":  clinic_capacity / consults_per_patient_yr,
        "share_of_pop":     (clinic_capacity / consults_per_patient_yr) / ring_pop * 100 if ring_pop else 0,
    }

# Market-share threshold labels (D-14 — Claude's discretion)
def label_market_share(pct_of_total):
    """Plain-language label for the share-of-total framing."""
    if pct_of_total < 5:   return "low"
    if pct_of_total < 15:  return "moderate"
    return "high"
```

### Example 4: GP FTE capacity range (D-10)

```python
def estimate_gp_capacity_range(clinic_count, ring_pop):
    """D-10: Two-method range. The variance IS the caveat (D-12).

    Method A: clinic count × avg FTE per clinic
    Method B: AMWAC benchmark × population
    """
    # Method A: cleaned Places clinic count × assumed avg FTE GPs per clinic
    # RACGP 2019: avg clinic size 5.7 GPs (37,000 GPs / 6,500 clinics)
    # But this is headcount, not FTE. Avg FTE per GP = 0.74 (DoH 2024)
    # So avg FTE per clinic ≈ 5.7 × 0.74 ≈ 4.2 FTE
    # Use 4.0 FTE/clinic as conservative point estimate (inner-Melbourne clinics may be smaller)
    AVG_FTE_PER_CLINIC = 4.0  # cited: RACGP HotN 2019 + DoH GP workforce 2024
    capacity_a = clinic_count * AVG_FTE_PER_CLINIC

    # Method B: AMWAC benchmark × population
    # AMWAC 2000: 110.4 FTE GPs per 100k (1:905) — still the planning benchmark
    # RACGP HotN 2025: 113 national (2024), VIC 117, major cities 117.3
    # Use AMWAC 110.4 as the conservative planning benchmark
    AMWAC_PER_100K = 110.4  # cited: AMWAC 2000, still referenced in RACGP/DoH 2024-25
    capacity_b = ring_pop * (AMWAC_PER_100K / 100_000)

    return {
        "method_a_clinic_derived": capacity_a,
        "method_b_benchmark_derived": capacity_b,
        "range": (min(capacity_a, capacity_b), max(capacity_a, capacity_b)),
        "caveat": "Places listings ≠ FTE GPs; range spans clinic-derived and benchmark-derived estimates.",
    }
```

### Example 5: Folium competitor map (D-15)

```python
import folium

def make_competitor_map(site_lat, site_lon, competitors_gdf, radii_m):
    """D-15: Interactive folium map with toggleable ring layers + competitor type colours."""
    m = folium.Map(location=[site_lat, site_lon], zoom_start=13, tiles="CartoDB Positron")

    # Site marker
    folium.Marker(
        [site_lat, site_lon],
        popup="292-296 Johnston St (proposed site)",
        icon=folium.Icon(color="red", icon="star", prefix="fa")
    ).add_to(m)

    # Ring layers (toggleable)
    colours = {1000: "blue", 3000: "green", 5000: "purple"}
    for r in radii_m:
        ring_group = folium.FeatureGroup(name=f"{r//1000}km ring", show=(r <= 3000))
        folium.Circle([site_lat, site_lon], radius=r, color=colours[r],
                      fill=False, weight=2, dashArray="5").add_to(ring_group)
        ring_group.add_to(m)

    # Competitor markers coloured by type
    type_colours = {
        "gp_corporate": "red",
        "gp_independent": "orange",
        "pharmacy": "blue",
        "allied_health": "green",
        "ambiguous": "gray",
    }
    comp_group = folium.FeatureGroup(name="Competitors", show=True)
    for _, row in competitors_gdf.iterrows():
        lat, lon = row.geometry.y, row.geometry.x
        colour = type_colours.get(row.get("category", "ambiguous"), "gray")
        popup = f"{row.get('displayName', '?')}<br>{row.get('category', '?')}<br>{row.get('label', '')}"
        folium.CircleMarker(
            [lat, lon], radius=5, color=colour, fill=True, fillColor=colour,
            fillOpacity=0.7, popup=popup
        ).add_to(comp_group)
    comp_group.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m
```

---

## Resolved Discretion Items

| Discretion item | Resolution | Confidence | Source |
|----------------|------------|------------|--------|
| **AIHW dataset URL** | `https://www.aihw.gov.au/reports/primary-health-care/medicare-subsidised-gp-allied-health-specialist` (Data tab: `/data`). Also on Regional Data Hub: `catalogue.data.infrastructure.gov.au/dataset/rdh-medicare-subsidised-gp-allied-health-and-specialist-health-care-across-local-areas`. Download = Excel data tables (JS-rendered, manual download like MBS SA3 file). | HIGH on URL, MEDIUM on exact sheet structure | AIHW website, accessed 2026-07-06 |
| **AIHW vintage** | Latest edition updated 26 Mar 2026, covers 2017-18 to 2024-25. Citation: AIHW (2026). | HIGH | AIHW website |
| **AIHW SA3 age bands** | 0-24, 25-44, 45-64, 65+ (NOT 0-14/15-64/65+). PHN-level has finer bands but SA3 does not. | HIGH | AIHW "Scope and measures" technical notes |
| **SA3 MBS product URL** | `https://www.health.gov.au/resources/publications/medicare-quarterly-statistics-statistical-area-sa3-summary-march-quarter-2025-26` (latest = March quarter 2025-26, published 25 May 2026). Download path: `/sites/default/files/2026-05/medicare-quarterly-statistics-statistical-area-sa3-summary-march-quarter-2025-26.xlsx`. Contains GP Non-Referred Attendances by SA3, Sept-qtr 2019-20 → Mar-qtr 2025-26. | HIGH | health.gov.au, accessed 2026-07-06 |
| **5 includedTypes values** | ALL confirmed valid in Places API (New) Table A: `doctor`, `medical_lab`, `pharmacy`, `physiotherapist`, `dentist`. Also available: `medical_center`, `medical_clinic`, `dental_clinic`, `chiropractor`, `skin_care_clinic`. | HIGH | Google Place Types (New) docs, accessed 2026-07-06 |
| **Field mask composition** | Use Pro SKU fields ONLY: `places.id,places.displayName,places.location,places.types,places.primaryType,places.primaryTypeDisplayName,places.businessStatus,places.formattedAddress,places.shortFormattedAddress,places.addressComponents`. DROP `rating` and `userRatingCount` (they trigger Enterprise SKU $35/1k with only 1,000 free/month, vs Pro $32/1k with 5,000 free/month). | HIGH | Google Place Data Fields docs + SKU pricing page |
| **Subdivision grid geometry** | 2×2 grid (4 sub-circles). Sub-circle radius = original_radius / 2. Offset centres by ±radius/4 in lat/lon (converted to meters). Max depth = 2 (sub-subdivide only saturated quarters). Dedupe on `place.id` after. | HIGH (design decision, math verified) | D-05 decision + geometric reasoning |
| **Corporate GP brand list** | IPN (Sonic Healthcare, 143 sites), Amplar Health/Myhealth (Medibank, 116 sites), Family Doctor (105 sites), ForHealth (92 sites), Bupa/Partnered Health (58 sites), Better Medical (59 sites), Jupiter Health (36 sites), Ochre Health (67 sites), Qualitas, Health&Co (ForHealth). Keywords: `ipn`, `myhealth`, `family doctor`, `forhealth`, `healius`, `bupa`, `better medical`, `jupiter health`, `ochre`, `sonic`, `qualitas`, `health&co`. | HIGH | gpzoo.com.au 2025 dataset + company websites |
| **Exclude-keyword list** | `skin`, `cosmetic`, `dermatology`, `laser`, `beauty`, `vet`, `veterinary`, `optometry`, `optometrist`, `podiatry`, `audiology`, `radiology`, `imaging`, `x-ray`, `pathology`, `laboratory`, `specialist`, `paediatric`, `obstetric`, `gynaecology`, `psychiatry`. | HIGH | Standard medical taxonomy + Pitfall 9 |
| **Fuzzy-dedupe threshold** | `rapidfuzz.fuzz.token_sort_ratio` ≥ 85 on name, ≥ 80 on address. Conservative — over-flags for manual review rather than misses duplicates. | MEDIUM (empirical, not formally validated) | rapidfuzz docs + dedup best practice |
| **Avg FTE GPs per clinic** | **4.0 FTE** (point estimate). Derived: RACGP 2019 avg clinic size 5.7 GPs (headcount) × DoH 2024 avg FTE/GP 0.74 = 4.2 FTE. Rounded down to 4.0 for conservative inner-Melbourne estimate. | MEDIUM-HIGH | RACGP Health of the Nation 2019 + DoH GP Workforce 2024 |
| **AMWAC benchmark** | **110.4 FTE GPs per 100k** (AMWAC 2000, 1:905). Still the planning benchmark cited by RACGP/DoH 2024-25. Latest actuals: 113 national (2024), VIC 117, major cities 117.3 (RACGP HotN 2025, AMA). Use 110.4 as conservative planning benchmark; cite 113/117 as current actuals. | HIGH | RACGP Health of the Nation 2025 + AMA GP Facts + AMWAC 2000 |
| **Consults-per-patient-per-year** | **5.0** for the patients-needed framing (D-13c). AIHW national average = 6.8 attendances/person/year (2022), but this counts ALL people including non-attenders. Regular patients average ~5 visits/year (ABS Coordination of Health Care study: 8.7 for 45+ cohort, ~6.3 for 45-54). Use 5.0 as conservative denominator for "patients needed" framing. | MEDIUM | AIHW "Medicare funding of GP services over time" + ABS 4343.0.55.001 |
| **MBS item 23 rebate** | **$43.90** (confirmed current from 1 Jul 2025, MBS indexation 2.4%). Level C item 36 = $84.90, Level D item 44 = $125.10. | HIGH | MBS Online (www9.health.gov.au/mbs) + AHCWA quick reference guide Jul 2025 |
| **Market-share threshold labels** | <5% = "low", 5-15% = "moderate", >15% = "high" (share of total consults). These are heuristic — no official benchmark exists for "what market share is achievable." The labels frame the number without prejudging feasibility (D-14). | LOW (heuristic, no official source) | Design decision per D-14 |
| **GP FTE consult capacity** | ~5,000-6,000/year per FTE (110-130 consults/week × ~46 weeks). For 5 FTE: ~25,000-30,000/year. Use 27,500 as midpoint (5 FTE × 5,500/yr). | MEDIUM-HIGH | FEATURES.md key numbers + RACGP mixed-billing guide |

---

## Data Source Summary

| Source | URL | Format | Vintage | Access | Confidence |
|--------|-----|--------|---------|--------|------------|
| MBS SA3 Summary (Mar-qtr 2025-26) | `health.gov.au/resources/publications/medicare-quarterly-statistics-statistical-area-sa3-summary-march-quarter-2025-26` | xlsx, 2MB | Sept-qtr 2019-20 → Mar-qtr 2025-26 (published 25 May 2026) | Manual download → `data/local/` | HIGH |
| AIHW Medicare-subsidised GP care | `aihw.gov.au/reports/primary-health-care/medicare-subsidised-gp-allied-health-specialist` | Excel data tables (Data tab) | 2017-18 to 2024-25 (updated 26 Mar 2026) | Manual download → `data/local/` | HIGH on URL, MEDIUM on sheet structure |
| State MBS fallback (already on hand) | `data/local/medicare-quarterly-statistics-primary-care-service-type-summary-march-quarter-2025-26(1).xlsx` | xlsx | Mar-qtr 2025-26 | Already present | HIGH (verified sheets: no SA3) |
| Google Places API (New) | `places.googleapis.com/v1/places:searchNearby` | JSON POST | Real-time | API key via CachedSession | HIGH |
| RACGP Health of the Nation 2025 | `racgp.org.au/health-of-the-nation-2025` | Web report | 2024 data | Web | HIGH |
| AMWAC 2000 benchmark | Referenced in RACGP/DoH publications | Report | 2000 (still cited) | Web | HIGH |
| MBS Online item 23 | `www9.health.gov.au/mbs/fullDisplay.cfm?criteria=23` | Web | 1 Jul 2025 (2.4% indexation) | Web | HIGH |
| GP corporate brands | `gpzoo.com.au` | Web dataset | 2025 | Web | HIGH |

---

## RESEARCH COMPLETE

- **3 critical corrections to prior research:** (1) `rating`/`userRatingCount` are Enterprise SKU not Pro — drop them from the field mask; (2) AIHW SA3 age bands are 0-24/25-44/45-64/65+ not 0-14/15-64/65+ — update `consults_per_capita_yr` to 4 keys; (3) AIHW latest edition is 2026 (2024-25 data) not 2022-23.
- **All 6 ROADMAP research questions answered with verified URLs:** SA3 MBS product (March qtr 2025-26, published 25 May 2026), AIHW dataset (updated 26 Mar 2026), Places API types (all 5 confirmed in Table A), AMWAC benchmark (110.4/100k confirmed, latest actuals 113 national/117 VIC), consult rates (~6.8/capita national, 5.0 for patients-needed framing), MBS item 23 ($43.90 confirmed from 1 Jul 2025).
- **All discretion items resolved:** Field mask (Pro-only, no rating), subdivision (2×2 grid, radius/2, max depth 2), fuzzy-dedupe (rapidfuzz token_sort_ratio ≥85/≥80), corporate brands (12 keywords from gpzoo.com.au), avg FTE/clinic (4.0 from RACGP+DoH), market-share labels (<5% low, 5-15% moderate, >15% high).
- **Standard stack confirmed:** rapidfuzz (pip) is the only new install; everything else is preinstalled or already wired from Phase 1. No `googlemaps` client, no `fuzzywuzzy`, no `sklearn`.
- **Architecture patterns provided as copy-ready code:** Places client with saturation subdivision, keyword classification rules, rapidfuzz dedupe, demand arithmetic, GeoJSON persistence, folium competitor map — all aligned with the 16 locked decisions.