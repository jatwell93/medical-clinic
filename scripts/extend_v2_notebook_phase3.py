#!/usr/bin/env python3
"""
Phase 3 extension script for Johnston_St_v2.ipynb — Plan 03-01.

Loads the existing notebook (built by create_v2_notebook.py + extended by
extend_v2_notebook.py in Phases 1-2), extends BASE_ASSUMPTIONS with Phase 3
keys (replacing the old 3-band consults_per_capita_yr with the AIHW 4-band
structure), appends §1.4 Places API (New) Client + §1.5 MBS SA3 + AIHW
age-band rate loader cells, and updates .env.example with MBS SA3 + AIHW
download instructions.

Follows the same cell-dict pattern as extend_v2_notebook.py:
  cell_type, metadata: {}, source as list of strings (each ending with \n
  except possibly the last); code cells have execution_count: null, outputs: [].

Idempotent: if a cell containing "# §1.4 Places API" already exists, the
script REMOVES the existing §1.4 + §1.5 cells and re-appends the corrected
versions (cell-replacement idempotency).

Run:  python scripts/extend_v2_notebook_phase3.py
Output: Johnston_St_v2.ipynb (extended in-place), .env.example (extended)
"""

import json
from pathlib import Path


# ──────────────────────────────────────────────────────────────────────
#  Cell helpers (same pattern as extend_v2_notebook.py)
# ──────────────────────────────────────────────────────────────────────

def md(*lns):
    """Create a markdown cell dict."""
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": _join(lns),
    }


def code(*lns):
    """Create a code cell dict."""
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": _join(lns),
    }


def _join(lns):
    """Join strings into a source list, each ending with \\n except the last."""
    result = []
    for i, ln in enumerate(lns):
        if i < len(lns) - 1:
            result.append(ln + "\n")
        else:
            result.append(ln)
    return result


# ──────────────────────────────────────────────────────────────────────
#  Phase 3 BASE_ASSUMPTIONS keys to insert
# ──────────────────────────────────────────────────────────────────────

PHASE3_ASSUMPTIONS_KEYS = [
    "",
    "    # --- Phase 3: Demand & Competitors (source: AIHW 2026, MBS SA3, RACGP, AMWAC) ---",
    "    # AIHW SA3 age bands: 0-24, 25-44, 45-64, 65+ (NOT 0-14/15-64/65+ — Correction 2)",
    "    # Values are \"services per 100 people\" from AIHW (2026), SA3 20604 Yarra",
    "    # These are placeholder defaults — replaced by load_aihw_sa3_rates() at runtime",
    "    \"consults_per_capita_yr\": {\"0-24\": 4.5, \"25-44\": 5.5, \"45-64\": 7.5, \"65+\": 12.0},  # AIHW (2026) fallback",
    "    \"mbs_sa3_filename\":       \"medicare-quarterly-statistics-statistical-area-sa3-summary-march-quarter-2025-26.xlsx\",  # D-01 manual download",
    "    \"aihw_age_band_filename\": \"aihw-medicare-subsidised-gp-allied-health-2024-25-data-tables.xlsx\",  # D-02 manual download",
    "    \"avg_fte_per_clinic\":     4.0,        # RACGP 2019 (5.7 headcount) × DoH 2024 (0.74 FTE/GP) = 4.2, rounded down — D-10",
    "    \"amwac_per_100k\":         110.4,      # AMWAC 2000 planning benchmark (1:905) — D-10; latest actuals: 113 nat, 117 VIC",
    "    \"gp_fte_consults_per_yr\": 5500,       # ~110-130 consults/week × ~46 weeks — midpoint for 5 FTE = 27,500/yr — D-13",
    "    \"consults_per_patient_yr\": 5.0,       # patients-needed framing denominator — D-13c (AIHW nat avg 6.8, regular patients ~5)",
    "    \"mbs_item_23_rebate\":     43.90,      # MBS Online, from 1 Jul 2025 (2.4% indexation) — confirmed",
    "    \"market_share_thresholds\": {\"low\": 5, \"high\": 15},  # <5% low, 5-15% moderate, >15% high — D-14",
    "    \"places_included_types\":  [\"doctor\", \"pharmacy\", \"physiotherapist\", \"dentist\", \"medical_lab\"],  # Places API (New) Table A — D-05",
]

# The old consults_per_capita_yr line that must be REPLACED (3-band → 4-band)
OLD_CONSULTS_LINE = '    "consults_per_capita_yr": {"0-14": 4.4, "15-64": 5.1, "65+": 11.0},  # MBS 2024-25 — UNCONFIRMED vintage'


# ──────────────────────────────────────────────────────────────────────
#  §1.4 Places API (New) Client cells
# ──────────────────────────────────────────────────────────────────────

def places_cells():
    """Return the §1.4 Places API (New) Client cells."""
    cells = []

    # 1. Markdown — §1.4 header + teaching commentary
    cells.append(md(
        "## §1.4 Places API (New) Client",
        "",
        "v1 used the **legacy Places Nearby Search** (`/maps/api/place/nearbysearch/json`)",
        "with `next_page_token` pagination and uncached `requests.get` (Pitfall 10).",
        "The legacy API is closed to new customers since March 2025. This cell uses",
        "**Places API (New)** `POST places:searchNearby` with a mandatory",
        "`X-Goog-FieldMask` header (STACK.md).",
        "",
        "**Key differences from legacy (Pitfall 8):** Nearby Search (New) has NO",
        "pagination — `maxResultCount` caps at 20. The saturation subdivision (D-05)",
        "beats this by splitting saturated circles into a 2×2 grid of smaller circles",
        "and deduping on `place.id`.",
        "",
        "**Caching:** all calls route through the Phase 1 `CachedSession` with",
        "`allowable_methods=('GET','POST')` so re-runs are $0. The field mask uses",
        "**Pro SKU fields ONLY** — `rating` and `userRatingCount` are Enterprise SKU",
        "(Correction 1) and are dropped to stay in the $32/1k Pro tier with 5,000",
        "free/month.",
    ))

    # 2. Code — §1.4 Places client (places_nearby, offset_meters, places_nearby_saturated)
    cells.append(code(
        "# §1.4 Places API (New) Client — Nearby Search with saturation subdivision (D-05)",
        "# Replaces v1's legacy google_nearby_places (uncached requests.get, next_page_token pagination)",
        "# Places API (New): POST places:searchNearby, mandatory X-Goog-FieldMask, maxResultCount=20, NO pagination",
        "import math",
        "",
        'PLACES_URL = "https://places.googleapis.com/v1/places:searchNearby"',
        "",
        "# Pro SKU field mask ONLY — drops rating/userRatingCount (Enterprise SKU, Correction 1)",
        "# Pro SKU: $32/1k, 5,000 free/month. Enterprise: $35/1k, 1,000 free/month.",
        "PLACES_FIELD_MASK = (",
        '    "places.id,"',
        '    "places.displayName,"',
        '    "places.location,"',
        '    "places.types,"',
        '    "places.primaryType,"',
        '    "places.primaryTypeDisplayName,"',
        '    "places.businessStatus,"',
        '    "places.formattedAddress,"',
        '    "places.shortFormattedAddress,"',
        '    "places.addressComponents"',
        ")",
        "",
        "def places_nearby(lat, lon, radius_m, included_types):",
        '    """Single Nearby Search (New) call. Returns list of place dicts. Max 20."""',
        "    body = {",
        '        "includedTypes": included_types,',
        '        "maxResultCount": 20,',
        '        "locationRestriction": {',
        '            "circle": {',
        '                "center": {"latitude": lat, "longitude": lon},',
        '                "radius": float(radius_m)',
        "            }",
        "        },",
        '        "languageCode": "en-AU"',
        "    }",
        "    headers = {",
        '        "Content-Type": "application/json",',
        '        "X-Goog-Api-Key": GOOGLE_PLACES_KEY,',
        '        "X-Goog-FieldMask": PLACES_FIELD_MASK',
        "    }",
        "    resp = session.post(PLACES_URL, json=body, headers=headers)  # Phase 1 CachedSession",
        "    resp.raise_for_status()",
        '    return resp.json().get("places", [])',
        "",
        "def offset_meters(lat, lon, dx_m, dy_m):",
        '    """Offset lat/lon by dx/dy meters. Good enough for <10km in Melbourne."""',
        "    dlat = dy_m / 111_320",
        "    dlon = dx_m / (111_320 * abs(math.cos(math.radians(lat))))",
        "    return lat + dlat, lon + dlon",
        "",
        "def places_nearby_saturated(lat, lon, radius_m, included_types):",
        '    """Query per-type × per-ring; auto-subdivide 2×2 grid on 20-result cap (D-05)."""',
        "    results = places_nearby(lat, lon, radius_m, included_types)",
        "    if len(results) < 20:",
        "        return results  # Not saturated",
        "",
        "    # Saturated → subdivide into 2×2 grid of smaller circles",
        "    # Sub-circle radius = original_radius / 2 (covers the diameter, overlaps at edges)",
        "    sub_radius = radius_m / 2",
        "    offsets = [",
        "        (sub_radius * 0.5, sub_radius * 0.5),    # NE",
        "        (sub_radius * 0.5, -sub_radius * 0.5),   # SE",
        "        (-sub_radius * 0.5, sub_radius * 0.5),   # NW",
        "        (-sub_radius * 0.5, -sub_radius * 0.5),  # SW",
        "    ]",
        "    sub_results = []",
        "    sub_queries = []",
        "    for dx, dy in offsets:",
        "        sub_lat, sub_lon = offset_meters(lat, lon, dx, dy)",
        "        r = places_nearby(sub_lat, sub_lon, sub_radius, included_types)",
        "        sub_queries.append((sub_lat, sub_lon, r))",
        "        sub_results.extend(r)",
        "",
        "    # If any sub-circle also saturates at 20, sub-subdivide that quarter once (max depth 2)",
        "    for sub_lat, sub_lon, r in sub_queries:",
        "        if len(r) >= 20:",
        "            for sdx, sdy in offsets:",
        "                ss_lat, ss_lon = offset_meters(sub_lat, sub_lon, sdx * 0.5, sdy * 0.5)",
        "                sub_results.extend(places_nearby(ss_lat, ss_lon, sub_radius / 2, included_types))",
        "",
        "    # Dedupe on place.id",
        "    seen = {}",
        "    for p in results + sub_results:",
        '        pid = p.get("id")',
        "        if pid and pid not in seen:",
        "            seen[pid] = p",
        "    return list(seen.values())",
        "",
        'print("[places] places_nearby_saturated() defined — Pro SKU field mask, 2×2 subdivision on 20-cap, dedupe on place.id")',
    ))

    # 3. Code — §1.4 site catchment query
    cells.append(code(
        "# Query site catchment: 5 types × 3 radii = 15 base requests (D-05)",
        "site_places = {}",
        'for ptype in BASE_ASSUMPTIONS["places_included_types"]:',
        '    for r in BASE_ASSUMPTIONS["catchment_radii_m"]:',
        "        results = places_nearby_saturated(site_lat, site_lon, r, [ptype])",
        "        site_places[(ptype, r)] = results",
        '        print(f"[places] {ptype} {r//1000}km: {len(results)} places (after dedupe)")',
        "total_site = sum(len(v) for v in site_places.values())",
        'print(f"[places] site catchment total: {total_site} place records (pre cross-type dedupe)")',
    ))

    # 4. Code — §1.4 peer catchment queries
    cells.append(code(
        "# Peer catchment queries (D-06) — 10 peers × 3 radii × 5 types = ~150 requests (cached)",
        "peer_places = {}",
        "for poa_code in PEER_POSTCODES:",
        '    poa_row = poa[poa["POA_CODE21"] == poa_code]',
        "    if poa_row.empty:",
        '        print(f"[places] ⚠ POA {poa_code} not found in geometry — skipping")',
        "        continue",
        "    # centroid is in EPSG:7855; convert to lat/lon for Places API",
        '    centroid_4326 = poa_row.to_crs("EPSG:4326").geometry.centroid.iloc[0]',
        "    peer_lat, peer_lon = centroid_4326.y, centroid_4326.x",
        '    for ptype in BASE_ASSUMPTIONS["places_included_types"]:',
        '        for r in BASE_ASSUMPTIONS["catchment_radii_m"]:',
        "            results = places_nearby_saturated(peer_lat, peer_lon, r, [ptype])",
        "            peer_places[(poa_code, ptype, r)] = results",
        'print(f"[places] peer queries complete: {len(peer_places)} (type, radius) pairs across {len(PEER_POSTCODES)} peers")',
    ))

    return cells


# ──────────────────────────────────────────────────────────────────────
#  §1.5 MBS SA3 + AIHW Age-Band Rates cells
# ──────────────────────────────────────────────────────────────────────

def mbs_aihw_cells():
    """Return the §1.5 MBS SA3 + AIHW age-band rates cells."""
    cells = []

    # 5. Markdown — §1.5 header + teaching commentary
    cells.append(md(
        "## §1.5 MBS SA3 Data + AIHW Age-Band Rates",
        "",
        "v1 loaded the **state-level** Medicare file",
        "(`medicare-quarterly-statistics-primary-care-service-type-summary...xlsx`)",
        "whose sheets are `['Contents', 'State', 'Modified Monash', 'Primary Care",
        "Service Types']` — **NO SA3 data** (Pitfall 6). Any \"local utilisation\"",
        "from it is just the VIC average in disguise.",
        "",
        "This cell loads the **correct product**: \"Medicare quarterly statistics –",
        "Statistical Area (SA3) Summary\" from health.gov.au, filtered to SA3 20604",
        "Yarra (D-01). The AIHW age-band rates provide per-capita GP attendance by",
        "age band — the SA3 age bands are **0-24, 25-44, 45-64, 65+** (NOT",
        "0-14/15-64/65+ — Correction 2). The AIHW latest edition is **2026** covering",
        "2024-25 data (Correction 3).",
        "",
        "The state file remains as a **fallback** with a LOUD warning (D-04). Both",
        "datasets are manual downloads to `data/local/` (like the SA1 shapefile in",
        "Phase 2).",
    ))

    # 6. Code — §1.5 MBS SA3 loader
    cells.append(code(
        "# §1.5 MBS SA3 loader — SA3 20604 Yarra with state fallback (D-01, D-04, Pitfall 6)",
        "# MBS SA3 Summary (March quarter 2025-26), published 25 May 2026. health.gov.au",
        "import pandas as pd",
        "",
        'DATA_LOCAL_DIR = PROJECT_ROOT / "data" / "local"',
        'MBS_SA3_FILENAME = BASE_ASSUMPTIONS.get("mbs_sa3_filename",',
        '    "medicare-quarterly-statistics-statistical-area-sa3-summary-march-quarter-2025-26.xlsx")',
        "",
        "def load_mbs_sa3():",
        '    """Load SA3-level MBS GP Non-Referred Attendance data. Fallback to state with warning (D-04)."""',
        "    sa3_path = DATA_LOCAL_DIR / MBS_SA3_FILENAME",
        "",
        "    if sa3_path.exists():",
        "        xl = pd.ExcelFile(sa3_path)",
        '        print(f"[mbs] SA3 file sheets: {xl.sheet_names}")',
        '        # Find the SA3 sheet — try "SA3" first, fall back to first sheet containing "SA3"',
        "        sa3_sheet = None",
        "        for name in xl.sheet_names:",
        '            if "SA3" in str(name).upper():',
        "                sa3_sheet = name",
        "                break",
        "        if sa3_sheet is None:",
        "            sa3_sheet = xl.sheet_names[0]",
        '            print(f"[mbs] ⚠ No \'SA3\' sheet found, using first sheet: {sa3_sheet}")',
        "        df = pd.read_excel(sa3_path, sheet_name=sa3_sheet)",
        '        # Filter to SA3 20604 Yarra',
        '        sa3_yarra = df[df["SA3"].astype(str) == "20604"]',
        "        if sa3_yarra.empty:",
        '            print("⚠ WARNING: SA3 20604 not found in file. Check SA3 column name.")',
        '        print(f"[mbs] SA3 20604 Yarra: {len(sa3_yarra)} quarters loaded")',
        '        return sa3_yarra, "sa3"',
        "    else:",
        "        # D-04: State fallback with LOUD warning",
        '        state_path = DATA_LOCAL_DIR / "medicare-quarterly-statistics-primary-care-service-type-summary-march-quarter-2025-26(1).xlsx"',
        '        print("═" * 70)',
        '        print("⚠  STATE BENCHMARK, NOT LOCAL — SA3 20604 data not found.")',
        '        print("⚠  Download the SA3 Summary file from health.gov.au")',
        '        print("⚠  and place in data/local/. Demand signal = VIC average, not Yarra.")',
        '        print("═" * 70)',
        '        df = pd.read_excel(state_path, sheet_name="State")',
        '        vic = df[df["State"] == "VIC"]',
        '        return vic, "state_fallback"',
    ))

    # 7. Code — §1.5 AIHW age-band rates loader
    cells.append(code(
        "# §1.5 AIHW age-band rates loader (D-02, Correction 2, Correction 3)",
        '# AIHW (2026) — "Medicare-subsidised GP, allied health and specialist health care across local areas"',
        "# Updated 26 Mar 2026, covers 2017-18 to 2024-25. SA3 age bands: 0-24, 25-44, 45-64, 65+",
        'AIHW_FILENAME = BASE_ASSUMPTIONS.get("aihw_age_band_filename",',
        '    "aihw-medicare-subsidised-gp-allied-health-2024-25-data-tables.xlsx")',
        "",
        "def load_aihw_sa3_rates():",
        '    """Load AIHW SA3-level GP attendance rates by age band.',
        "    Returns (dict, source_str) for SA3 20604 Yarra.\"\"\"",
        "    path = DATA_LOCAL_DIR / AIHW_FILENAME",
        "    if not path.exists():",
        '        print("⚠ WARNING: AIHW age-band data not found. Using national average fallback.")',
        '        return ({"0-24": 4.5, "25-44": 5.5, "45-64": 7.5, "65+": 12.0}, "national_fallback")',
        "",
        "    xl = pd.ExcelFile(path)",
        '    print(f"[aihw] sheets: {xl.sheet_names}")',
        "",
        "    # Find the SA3 GP attendances sheet — verify at runtime",
        "    sa3_sheet = None",
        "    for name in xl.sheet_names:",
        '        if "SA3" in str(name).upper() and "GP" in str(name).upper():',
        "            sa3_sheet = name",
        "            break",
        "    if sa3_sheet is None:",
        "        # Fall back to first sheet containing \"SA3\"",
        "        for name in xl.sheet_names:",
        '            if "SA3" in str(name).upper():',
        "                sa3_sheet = name",
        "                break",
        "    if sa3_sheet is None:",
        "        sa3_sheet = xl.sheet_names[0]",
        '        print(f"[aihw] ⚠ No SA3 sheet found, using first sheet: {sa3_sheet}")',
        "",
        "    df = pd.read_excel(path, sheet_name=sa3_sheet)",
        "    # Filter to SA3 20604",
        '    sa3_yarra = df[df["SA3"].astype(str) == "20604"]',
        "",
        "    # Extract rates by age band (column structure verified at runtime)",
        "    rates = {}",
        '    for band in ["0-24", "25-44", "45-64", "65+"]:',
        '        # Column name pattern verified at runtime — may be "0-24" or "0_24" etc.',
        '        col = [c for c in df.columns if band.replace("-", "") in str(c).replace("-", "")]',
        "        if col:",
        "            rates[band] = float(sa3_yarra[col[0]].iloc[0])",
        "        else:",
        '            print(f"⚠ Age band \'{band}\' column not found in AIHW data")',
        "",
        '    return (rates, "aihw_sa3")',
    ))

    # 8. Code — §1.5 load + assert
    cells.append(code(
        "# Load MBS SA3 + AIHW age-band rates (D-01, D-02, D-03)",
        "mbs_sa3_df, mbs_source = load_mbs_sa3()",
        "aihw_rates, aihw_source = load_aihw_sa3_rates()",
        'print(f"[mbs] source: {mbs_source}, rows: {len(mbs_sa3_df)}")',
        'print(f"[aihw] source: {aihw_source}, rates: {aihw_rates}")',
        "# Assert SA3 20604 present when using SA3 data (Pitfall 6 verification)",
        'if mbs_source == "sa3":',
        '    assert mbs_sa3_df["SA3"].astype(str).str.contains("20604").any(), \\',
        '        "SA3 20604 not found in MBS data — check file (Pitfall 6)"',
        '    print("[mbs] ✓ SA3 20604 Yarra confirmed in data")',
    ))

    return cells


# ──────────────────────────────────────────────────────────────────────
#  §4 Competitor Landscape cells
# ──────────────────────────────────────────────────────────────────────

def competitor_cells():
    """Return the §4 Competitor Landscape cells.

    Implements: classify_place (D-09), fuzzy_dedupe_competitors (rapidfuzz),
    GeoJSON persistence (D-08), ring assignment via sjoin, manual-review
    checkpoint (D-11 — no input()), folium competitor map + 3 static figures
    (D-15), peer competitor table with GP-per-1,000 benchmark (D-16, COMP-03),
    and the D-12 capacity caveat.
    """
    cells = []

    # 1. Markdown — §4 header + teaching commentary
    cells.append(md(
        "# §4 Competitor Landscape",
        "",
        "v1's raw `type=doctor` Google Places counts were **inflated 2–5×** by",
        "three problems (Pitfall 9):",
        "1. **Specialists** — skin clinics, cosmetic clinics, and vets mis-tagged",
        "   as \"doctor\" in Google Places",
        "2. **Individual practitioner listings** — each GP gets their own Places",
        "   entry *plus* the practice entry (double-counting)",
        "3. **Miscategorised places** — radiology, pathology, optometry flagged as",
        "   \"medical\" but not GP clinics",
        "",
        "v1 concluded \"6.6 doctors per 1,000\" when the sane metro benchmark is",
        "~1.2 FTE GPs per 1,000. This section fixes it with:",
        "- **Keyword-based classification** (D-09) — pharmacy brands first, then",
        "  exclude keywords, corporate GP brands, independent GP indicators,",
        "  allied health indicators",
        "- **rapidfuzz fuzzy-dedupe** (D-09) of individual-practitioner listings",
        "  (MIT-licensed, NOT the deprecated GPL alternative)",
        "- **Manual-review checkpoint** (D-11) for ambiguous rows — printed inline,",
        "  no blocking prompts",
        "- **GeoJSON persistence** (D-08) — deduped GeoDataFrame saved to",
        "  `data/cache/competitors.geojson` so re-runs never touch the API (Pitfall 10)",
        "",
        "The per-ring competitor counts feed the GP FTE capacity estimate in §5.",
        "The peer competitor table (D-16) fills the DEMO-03 placeholder with real data.",
    ))

    # 2. Code — §4.1 Classification rules
    cells.append(code(
        "# §4.1 Classification rules (D-09) — keyword-based competitor bucketing",
        "# pip install rapidfuzz  # MIT-licensed fuzzy string matching",
        "# Checks pharmacy brands FIRST (D-07), then exclude keywords, corporate GP",
        "# brands, independent GP indicators, allied health indicators, else ambiguous.",
        "",
        "# Corporate GP brands (from gpzoo.com.au 2025 — verified site counts)",
        "CORPORATE_GP_BRANDS = {",
        '    "ipn": "IPN (Sonic Healthcare)",',
        '    "myhealth": "Amplar Health (Myhealth/Medibank)",',
        '    "family doctor": "Family Doctor",',
        '    "forhealth": "ForHealth",',
        '    "healius": "ForHealth (formerly Healius)",',
        '    "bupa": "Bupa (Partnered Health)",',
        '    "better medical": "Amplar Health (Better Medical)",',
        '    "jupiter health": "Jupiter Health",',
        '    "ochre": "Ochre Health",',
        '    "sonic": "Sonic Healthcare",',
        '    "qualitas": "Qualitas",',
        '    "health&co": "ForHealth (Health&Co)",',
        "}",
        "",
        "# Pharmacy brands (D-07) — keyword rules on displayName",
        "PHARMACY_BRANDS = {",
        '    "chemist warehouse": "Chemist Warehouse",',
        '    "priceline": "Priceline",',
        '    "amcal": "Amcal",',
        '    "terrywhite": "TerryWhite Chemmart",',
        '    "terry white": "TerryWhite Chemmart",',
        '    "chemmart": "TerryWhite Chemmart",',
        '    "sigma": "Sigma (API)",',
        '    "pharmacy 4 less": "Pharmacy 4 Less",',
        '    "national pharmacy": "National Pharmacy",',
        '    "soul pattinson": "Soul Pattinson",',
        '    "discount drug stores": "Discount Drug Stores",',
        "}",
        "",
        "# Exclude keywords — these are NOT GP clinics (21 terms)",
        "EXCLUDE_KEYWORDS = [",
        '    "skin", "cosmetic", "dermatology", "laser", "beauty",',
        '    "vet", "veterinary", "animal",',
        '    "optometry", "optometrist", "podiatry", "audiology",',
        '    "radiology", "imaging", "pathology", "laboratory",',
        '    "specialist", "paediatric", "obstetric", "gynaecology", "psychiatry",',
        "]",
        "",
        "def classify_place(name, primary_type, types_list):",
        '    """Classify a place into: gp_corporate, gp_independent, pharmacy, allied_health, exclude, ambiguous."""',
        "    name_lower = str(name).lower()",
        "",
        "    # 1. Check pharmacy brands first (most specific — D-07)",
        "    for brand, label in PHARMACY_BRANDS.items():",
        "        if brand in name_lower:",
        '            return ("pharmacy", label)',
        "",
        '    if primary_type == "pharmacy" or "pharmacy" in (types_list or []):',
        '        return ("pharmacy", "Independent")',
        "",
        "    # 2. Check exclude bucket (specialists, cosmetic, vet, etc.)",
        "    for kw in EXCLUDE_KEYWORDS:",
        "        if kw in name_lower:",
        '            return ("exclude", kw)',
        "",
        "    # 3. Check corporate GP brands",
        "    for brand, label in CORPORATE_GP_BRANDS.items():",
        "        if brand in name_lower:",
        '            return ("gp_corporate", label)',
        "",
        "    # 4. Check independent GP clinic indicators",
        '    gp_clinic_indicators = ["medical centre", "medical center", "general practice",',
        '                            "gp clinic", "gp practice", "medical clinic", "family practice",',
        '                            "health centre", "health center", "community health"]',
        "    if any(kw in name_lower for kw in gp_clinic_indicators):",
        '        return ("gp_independent", "Independent")',
        "",
        "    # 5. doctor-type without clinic indicator → ambiguous (manual review)",
        '    if primary_type in ("doctor", "medical_center", "medical_clinic"):',
        '        return ("ambiguous", "doctor-type but no clinic indicator in name")',
        "",
        "    # 6. Allied health indicators",
        '    allied_indicators = ["physio", "physiotherapy", "psychology", "psychologist",',
        '                         "dental", "dentist", "chiropractic", "chiropractor",',
        '                         "occupational therapy", "dietitian", "dietician",',
        '                         "speech", "acupuncture", "osteopath"]',
        "    if any(kw in name_lower for kw in allied_indicators):",
        '        return ("allied_health", "Allied Health")',
        '    if primary_type in ("physiotherapist", "dentist", "dental_clinic", "chiropractor"):',
        '        return ("allied_health", "Allied Health")',
        "",
        "    # 7. Unclassified → ambiguous",
        '    return ("ambiguous", f"Unclassified (primaryType={primary_type})")',
        "",
        'print("[classify] classify_place() defined — 12 corporate GP brands, 11 pharmacy brands, 21 exclude keywords")',
    ))

    # 3. Code — §4.2 Fuzzy-dedupe + GeoDataFrame construction + GeoJSON persistence
    cells.append(code(
        "# §4.2 Fuzzy-dedupe + GeoDataFrame construction + GeoJSON persistence (D-08, D-09)",
        "# rapidfuzz: MIT-licensed, C++-fast, drop-in fuzz.token_sort_ratio API",
        "from rapidfuzz import fuzz",
        "import geopandas as gpd",
        "from shapely.geometry import Point",
        "",
        "def fuzzy_dedupe_competitors(places_gdf, name_threshold=85, address_threshold=80):",
        '    """Dedupe individual-practitioner listings that share a practice address.',
        "    Uses rapidfuzz.token_sort_ratio on normalised name + formattedAddress.",
        '    Keeps the first occurrence (by place.id), merges duplicates into a list."""',
        "    keep = []",
        "    seen = []",
        "    duplicates = []",
        "",
        "    for idx, row in places_gdf.iterrows():",
        '        name_norm = str(row.get("displayName", "")).lower().strip()',
        '        addr_norm = str(row.get("formattedAddress", "")).lower().strip()',
        "        is_dup = False",
        "",
        "        for kept in seen:",
        '            name_sim = fuzz.token_sort_ratio(name_norm, kept["name"])',
        '            addr_sim = fuzz.token_sort_ratio(addr_norm, kept["addr"])',
        "            # Match if name is very similar AND address is very similar",
        "            if name_sim >= name_threshold and addr_sim >= address_threshold:",
        "                is_dup = True",
        "                duplicates.append({",
        '                    "kept_id": kept["id"],',
        '                    "dup_id": row.get("id"),',
        '                    "name": row.get("displayName"),',
        '                    "name_sim": name_sim,',
        '                    "addr_sim": addr_sim,',
        "                })",
        "                break",
        "",
        "        if not is_dup:",
        "            keep.append(idx)",
        '            seen.append({"id": row.get("id"), "name": name_norm, "addr": addr_norm})',
        "",
        "    deduped = places_gdf.loc[keep].copy()",
        "    return deduped, duplicates",
        "",
        "# Build GeoDataFrame from site_places raw results",
        "# Flatten all (type, radius) results into a list of place dicts",
        "all_places = []",
        "for (ptype, radius), places in site_places.items():",
        "    for p in places:",
        '        pid = p.get("id", "")',
        '        dn = p.get("displayName", {})',
        '        name = dn.get("text", "") if isinstance(dn, dict) else str(dn)',
        '        loc = p.get("location", {})',
        '        lat = loc.get("latitude", None) if isinstance(loc, dict) else None',
        '        lon = loc.get("longitude", None) if isinstance(loc, dict) else None',
        '        ptdn = p.get("primaryTypeDisplayName", {})',
        '        ptdn_text = ptdn.get("text", "") if isinstance(ptdn, dict) else str(ptdn)',
        "        record = {",
        '            "id": pid,',
        '            "displayName": name,',
        '            "lat": lat,',
        '            "lon": lon,',
        '            "types": p.get("types", []),',
        '            "primaryType": p.get("primaryType", ""),',
        '            "primaryTypeDisplayName": ptdn_text,',
        '            "businessStatus": p.get("businessStatus", ""),',
        '            "formattedAddress": p.get("formattedAddress", ""),',
        '            "query_type": ptype,',
        '            "query_radius": radius,',
        "        }",
        "        all_places.append(record)",
        "",
        "# Dedupe on place.id first (cross-type duplicates from saturation subdivision)",
        "seen_ids = {}",
        "unique_places = []",
        "for rec in all_places:",
        '    if rec["id"] and rec["id"] not in seen_ids:',
        '        seen_ids[rec["id"]] = True',
        "        unique_places.append(rec)",
        "    elif not rec[\"id\"]:",
        "        unique_places.append(rec)  # keep records without id",
        "",
        "# Classify each place",
        "for rec in unique_places:",
        '    category, label = classify_place(rec["displayName"], rec["primaryType"], rec["types"])',
        '    rec["category"] = category',
        '    rec["label"] = label',
        "",
        "# Build GeoDataFrame",
        "geometry = [Point(r[\"lon\"], r[\"lat\"]) for r in unique_places if r[\"lon\"] is not None and r[\"lat\"] is not None]",
        "valid_records = [r for r in unique_places if r[\"lon\"] is not None and r[\"lat\"] is not None]",
        "competitors_gdf = gpd.GeoDataFrame(valid_records, geometry=geometry, crs=\"EPSG:4326\")",
        "",
        "# Fuzzy-dedupe individual-practitioner listings (D-09)",
        "competitors_gdf, dup_list = fuzzy_dedupe_competitors(competitors_gdf)",
        'print(f"[dedupe] kept {len(competitors_gdf)}, removed {len(dup_list)} duplicates")',
        "",
        "# D-08: GeoJSON persistence — re-runs load from cache, never touch the API",
        'geojson_path = CACHE_DIR / "competitors.geojson"',
        "if geojson_path.exists() and not FORCE_REFRESH:",
        "    competitors_gdf = gpd.read_file(geojson_path)",
        '    print(f"[cache] loaded {len(competitors_gdf)} competitors from {geojson_path.name}")',
        "else:",
        '    competitors_gdf.to_file(geojson_path, driver="GeoJSON")',
        '    print(f"[cache] wrote {len(competitors_gdf)} competitors to {geojson_path.name}")',
        'print(f"[competitors] {len(competitors_gdf)} unique competitors after dedupe + classification")',
    ))

    # 4. Code — §4.3 Ring assignment via spatial join
    cells.append(code(
        "# §4.3 Ring assignment via spatial join — which ring is each competitor in?",
        "# Reproject competitors to EPSG:7855 (metric), spatial join with buffer GeoDataFrames",
        "import pandas as pd",
        "",
        'competitors_gdf_metric = competitors_gdf.to_crs("EPSG:7855")',
        "",
        "# Build per-ring counts table",
        "per_ring_rows = []",
        'for radius in BASE_ASSUMPTIONS["catchment_radii_m"]:',
        "    # Get the buffer for this radius",
        '    ring_gdf = buffers[radius].to_crs("EPSG:7855") if hasattr(buffers[radius], "to_crs") else buffers[radius]',
        "    # Spatial join: which competitors are WITHIN this ring?",
        '    comp_in_ring = gpd.sjoin(competitors_gdf_metric, ring_gdf, predicate="within")',
        "",
        "    # Count by category",
        '    counts = comp_in_ring["category"].value_counts().to_dict() if len(comp_in_ring) > 0 else {}',
        "    row = {",
        '        "ring_km": radius // 1000,',
        '        "gp_corporate": counts.get("gp_corporate", 0),',
        '        "gp_independent": counts.get("gp_independent", 0),',
        '        "pharmacy": counts.get("pharmacy", 0),',
        '        "allied_health": counts.get("allied_health", 0),',
        '        "ambiguous": counts.get("ambiguous", 0),',
        '        "exclude": counts.get("exclude", 0),',
        "    }",
        '    row["total"] = sum(v for k, v in row.items() if k != "ring_km")',
        "    per_ring_rows.append(row)",
        "",
        "per_ring_counts = pd.DataFrame(per_ring_rows)",
        'print("[ring-assignment] per-ring competitor counts:")',
        "print(per_ring_counts.to_string(index=False))",
    ))

    # 5. Code — §4.4 Manual-review checkpoint (D-11, no blocking prompts)
    cells.append(code(
        "# D-11: Manual-review checkpoint — print ambiguous rows inline (no blocking)",
        '# The review is a documented post-run step, not an in-session gate (PIPE-01).',
        'ambiguous = competitors_gdf[competitors_gdf["category"] == "ambiguous"]',
        "if len(ambiguous) > 0:",
        '    print(f"\\n⚠ MANUAL REVIEW: {len(ambiguous)} ambiguous competitors flagged.")',
        '    print("Review the table below. If any are misclassified, edit data/cache/competitors.geojson")',
        '    print("manually and re-run from §5.\\n")',
        '    review_cols = ["displayName", "formattedAddress", "primaryType", "label"]',
        "    print(ambiguous[review_cols].to_string(index=False))",
        "else:",
        '    print("[review] No ambiguous competitors — all classified successfully.")',
    ))

    # 6. Markdown — §4.5 Competitor Maps
    cells.append(md(
        "## §4.5 Competitor Maps",
        "",
        "**Folium** interactive map (inline only, NOT in PDF — D-15): toggleable",
        "ring layers (1/3/5km) + competitor markers coloured by type.",
        "",
        "**3 static matplotlib + contextily figures** (one per ring, for PDF — D-15):",
        "competitors coloured by category (GP corporate=red, GP independent=orange,",
        "pharmacy=blue, allied health=green, ambiguous=gray). Same pattern as Phase 2",
        "§2.5 catchment maps.",
    ))

    # 7. Code — §4.5 folium competitor map
    cells.append(code(
        "# §4.5 Folium interactive competitor map (D-15) — inline only, NOT in PDF",
        "import folium",
        "",
        "def make_competitor_map(competitors, site_lat, site_lon, buffers_dict):",
        '    """Interactive competitor map with toggleable ring layers + type colours."""',
        '    m = folium.Map(location=[site_lat, site_lon], zoom_start=13, tiles="CartoDB Positron")',
        "",
        "    # Site marker",
        '    folium.Marker(',
        "        [site_lat, site_lon],",
        '        popup="Site: 292-296 Johnston St, Abbotsford",',
        '        icon=folium.Icon(color="red", icon="star", prefix="fa")',
        "    ).add_to(m)",
        "",
        "    # Ring layers as FeatureGroups (toggleable)",
        '    ring_colours = {1000: "blue", 3000: "green", 5000: "purple"}',
        "    for radius, colour in ring_colours.items():",
        '        fg = folium.FeatureGroup(name=f"{radius//1000} km ring")',
        "        buf = buffers_dict.get(radius)",
        "        if buf is not None:",
        '            buf_4326 = buf.to_crs("EPSG:4326") if hasattr(buf, "to_crs") else buf',
        "            for _, row in buf_4326.iterrows():",
        "                geom = row.geometry",
        '                if geom.geom_type == "Polygon":',
        "                    folium.Polygon(",
        "                        locations=[(lat, lon) for lon, lat in geom.exterior.coords],",
        '                        color=colour, weight=2, fill=False, dashArray="5"',
        "                    ).add_to(fg)",
        '                elif geom.geom_type == "LineString":',
        "                    folium.PolyLine(",
        "                        locations=[(lat, lon) for lon, lat in geom.coords],",
        '                        color=colour, weight=2, dashArray="5"',
        "                    ).add_to(fg)",
        "        fg.add_to(m)",
        "",
        "    # Competitor markers coloured by type",
        '    type_colours = {"gp_corporate": "red", "gp_independent": "orange", "pharmacy": "blue", "allied_health": "green", "ambiguous": "gray"}',
        '    for _, row in competitors.iterrows():',
        '        cat = row.get("category", "ambiguous")',
        '        colour = type_colours.get(cat, "gray")',
        "        folium.CircleMarker(",
        "            location=[row.geometry.y, row.geometry.x],",
        "            radius=5, color=colour, fill=True, fillOpacity=0.7,",
        '            popup=f"{row.get(\'displayName\', \'\')} ({cat})"',
        "        ).add_to(m)",
        "",
        '    folium.LayerControl(collapsed=False).add_to(m)',
        "    return m",
        "",
        "comp_map = make_competitor_map(competitors_gdf, site_lat, site_lon, buffers)",
        "comp_map",
    ))

    # 8. Code — §4.5 static matplotlib figures (3, one per ring)
    cells.append(code(
        "# §4.5 Static matplotlib + contextily figures for PDF (D-15) — one per ring",
        "import matplotlib.pyplot as plt",
        "import contextily as cx",
        "",
        'type_colours = {"gp_corporate": "red", "gp_independent": "orange", "pharmacy": "blue", "allied_health": "green", "ambiguous": "gray"}',
        "",
        'for radius in BASE_ASSUMPTIONS["catchment_radii_m"]:',
        "    fig, ax = plt.subplots(1, 1, figsize=(8, 8))",
        "",
        "    # Plot buffer boundary",
        '    buf = buffers[radius].to_crs("EPSG:7855") if hasattr(buffers[radius], "to_crs") else buffers[radius]',
        '    buf.boundary.plot(ax=ax, color="black", linewidth=1.5, linestyle="--")',
        "",
        "    # Plot competitors coloured by category",
        "    for cat, colour in type_colours.items():",
        '        subset = competitors_gdf_metric[competitors_gdf_metric["category"] == cat]',
        "        if len(subset) > 0:",
        "            subset.plot(ax=ax, color=colour, markersize=30, label=cat, alpha=0.7)",
        "",
        "    # Add contextily basemap",
        '    cx.add_basemap(ax, crs="EPSG:7855", source=cx.providers.CartoDB.Positron)',
        '    ax.set_title(f"Competitors — {radius//1000} km ring")',
        '    ax.legend(loc="upper right", fontsize=8)',
        "    ax.set_axis_off()",
        "    plt.tight_layout()",
        "    plt.show()",
    ))

    # 9. Markdown — §4.6 Peer Competitor Table
    cells.append(md(
        "## §4.6 Peer Competitor Table",
        "",
        "D-16 — separate from the Phase 2 census-only peer table. This table adds",
        "**GP count, pharmacy count by brand, allied health count, and GP-per-1,000",
        "ratio** per peer. Benchmarked against the VIC average ~117 FTE GPs/100k",
        "(COMP-03). Fills the DEMO-03 placeholder GP/pharmacy columns with real",
        "Places data.",
    ))

    # 10. Code — §4.6 peer competitor table
    cells.append(code(
        "# §4.6 Peer competitor table (D-16, COMP-03) — GP count, pharmacy by brand, GP-per-1,000",
        "# Separate from the Phase 2 census-only peer table — this adds real Places data.",
        "",
        "peer_comp_rows = []",
        "for poa_code in PEER_POSTCODES:",
        "    # Gather all places for this peer across all (type, radius) pairs",
        "    peer_all = []",
        "    for (p_poa, ptype, radius), places in peer_places.items():",
        "        if p_poa == poa_code:",
        "            for p in places:",
        '                dn = p.get("displayName", {})',
        '                name = dn.get("text", "") if isinstance(dn, dict) else str(dn)',
        '                loc = p.get("location", {})',
        '                lat = loc.get("latitude") if isinstance(loc, dict) else None',
        '                lon = loc.get("longitude") if isinstance(loc, dict) else None',
        "                if lat and lon:",
        "                    cat, lbl = classify_place(name, p.get(\"primaryType\", \"\"), p.get(\"types\", []))",
        "                    peer_all.append({\"name\": name, \"category\": cat, \"label\": lbl})",
        "",
        "    # Dedupe on name (peers use centroid, no place.id dedupe across radii)",
        "    seen_names = set()",
        "    unique_peer = []",
        "    for rec in peer_all:",
        '        key = rec["name"].lower().strip()',
        "        if key not in seen_names:",
        "            seen_names.add(key)",
        "            unique_peer.append(rec)",
        "",
        "    # Count by category",
        '    gp_corp = sum(1 for r in unique_peer if r["category"] == "gp_corporate")',
        '    gp_indep = sum(1 for r in unique_peer if r["category"] == "gp_independent")',
        '    gp_clinic_count = gp_corp + gp_indep',
        '    pharmacy_count = sum(1 for r in unique_peer if r["category"] == "pharmacy")',
        '    allied_count = sum(1 for r in unique_peer if r["category"] == "allied_health")',
        "",
        "    # Pharmacy by brand",
        '    pharmacy_brands = {}',
        '    for r in unique_peer:',
        '        if r["category"] == "pharmacy":',
        '            brand = r["label"]',
        '            pharmacy_brands[brand] = pharmacy_brands.get(brand, 0) + 1',
        "",
        "    # GP-per-1,000 using ERP-scaled population from Phase 2",
        '    poa_pop_row = peer_table[peer_table["poa_code"] == poa_code] if "peer_table" in dir() else None',
        "    peer_pop = 0",
        '    if poa_pop_row is not None and not poa_pop_row.empty:',
        '        peer_pop = poa_pop_row.iloc[0].get("Total_P_P_erp", poa_pop_row.iloc[0].get("Total_P_P", 0))',
        "",
        "    if peer_pop > 0:",
        '        gp_per_1000 = (gp_clinic_count * BASE_ASSUMPTIONS["avg_fte_per_clinic"]) / (peer_pop / 1000)',
        "    else:",
        "        gp_per_1000 = 0",
        "",
        "    peer_comp_rows.append({",
        '        "poa_code": poa_code,',
        '        "gp_clinics": gp_clinic_count,',
        '        "pharmacies": pharmacy_count,',
        '        "allied_health": allied_count,',
        '        "gp_per_1000": round(gp_per_1000, 2),',
        '        "top_pharmacy_brand": max(pharmacy_brands, key=pharmacy_brands.get) if pharmacy_brands else "—",',
        "    })",
        "",
        "peer_comp_table = pd.DataFrame(peer_comp_rows)",
        'print("[peer-competitors] peer competitor table:")',
        "print(peer_comp_table.to_string(index=False))",
        'print(f"\\n[benchmark] VIC average: {BASE_ASSUMPTIONS[\'amwac_per_100k\']} FTE GPs/100k (AMWAC planning), 117 (VIC actual RACGP 2025)")',
        'print(f"[benchmark] GP-per-1,000 = (gp_clinics × {BASE_ASSUMPTIONS[\'avg_fte_per_clinic\']} FTE/clinic) / (population / 1000)")',
    ))

    # 11. Markdown — §4.7 Capacity Caveat (D-12)
    cells.append(md(
        "## §4.7 Capacity Caveat",
        "",
        "> **Caveat (D-12):** Places listings ≠ FTE GPs. The GP capacity estimate",
        "> (computed in §5) spans a **clinic-derived method** (clinic count × 4.0",
        "> FTE/clinic) and a **benchmark-derived method** (AMWAC 110.4/100k ×",
        "> population). The variance IS the caveat — there is no single point",
        "> estimate. The range spans clinic-derived and benchmark-derived estimates.",
    ))

    return cells


# ──────────────────────────────────────────────────────────────────────
#  BASE_ASSUMPTIONS extension
# ──────────────────────────────────────────────────────────────────────

def extend_base_assumptions(cells):
    """Insert Phase 3 keys into the BASE_ASSUMPTIONS dict cell.

    Also replaces the old 3-band consults_per_capita_yr line with the
    new 4-band AIHW structure (Correction 2).

    Idempotent: if 'mbs_sa3_filename' is already present, the cell is
    left unchanged.
    """
    for cell in cells:
        src = cell.get("source", [])
        joined = "".join(src)
        if "BASE_ASSUMPTIONS = {" not in joined:
            continue
        if "mbs_sa3_filename" in joined:
            return False  # already extended

        new_source = []
        for line in src:
            # Replace old 3-band consults_per_capita_yr with 4-band version
            if OLD_CONSULTS_LINE in line:
                new_source.append(
                    '    "consults_per_capita_yr": {"0-24": 4.5, "25-44": 5.5, "45-64": 7.5, "65+": 12.0},  # AIHW (2026) fallback\n'
                )
            elif line.strip() == "}":
                # Insert Phase 3 keys before the closing brace
                for key_line in PHASE3_ASSUMPTIONS_KEYS:
                    new_source.append(key_line + "\n")
                new_source.append(line)
            else:
                new_source.append(line)
        cell["source"] = new_source
        return True
    return False


# ──────────────────────────────────────────────────────────────────────
#  .env.example extension
# ──────────────────────────────────────────────────────────────────────

ENV_PHASE3_SECTION = """
# Phase 3 — MBS SA3 Summary (for demand model, D-01)
# Manual download from Department of Health:
#   https://www.health.gov.au/resources/publications/medicare-quarterly-statistics-statistical-area-sa3-summary-march-quarter-2025-26
# File name: medicare-quarterly-statistics-statistical-area-sa3-summary-march-quarter-2025-26.xlsx
# Published: 25 May 2026. Contains GP Non-Referred Attendances by SA3.
# Place at: data/local/medicare-quarterly-statistics-statistical-area-sa3-summary-march-quarter-2025-26.xlsx
# (gitignored — large, immutable, not committed; same pattern as SA1 shapefile)

# Phase 3 — AIHW age-band GP attendance rates (for demand model, D-02)
# Manual download from AIHW:
#   https://www.aihw.gov.au/reports/primary-health-care/medicare-subsidised-gp-allied-health-specialist
# Click the "Data" tab, download the Excel data tables.
# Updated 26 Mar 2026, covers 2017-18 to 2024-25.
# SA3 age bands: 0-24, 25-44, 45-64, 65+
# Place at: data/local/aihw-medicare-subsidised-gp-allied-health-2024-25-data-tables.xlsx
# (gitignored — manual download, same pattern as MBS SA3 file)
"""


def extend_env_example():
    """Append Phase 3 MBS SA3 + AIHW download instructions to .env.example.

    Idempotent: if 'medicare-quarterly-statistics-statistical-area-sa3-summary'
    is already present, the file is left unchanged.
    """
    env_path = Path(__file__).resolve().parent.parent / ".env.example"
    content = env_path.read_text(encoding="utf-8")

    if "medicare-quarterly-statistics-statistical-area-sa3-summary" in content:
        print("[extend-phase3] .env.example already has Phase 3 sections — skipping")
        return False

    # Ensure file ends with newline before appending
    if not content.endswith("\n"):
        content += "\n"

    content += ENV_PHASE3_SECTION
    env_path.write_text(content, encoding="utf-8")
    print("[extend-phase3] .env.example extended with MBS SA3 + AIHW download instructions")
    return True


# ──────────────────────────────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────────────────────────────

def main():
    notebook_path = Path(__file__).resolve().parent.parent / "Johnston_St_v2.ipynb"
    nb = json.loads(notebook_path.read_text(encoding="utf-8"))
    cells = nb["cells"]

    # Extend BASE_ASSUMPTIONS with Phase 3 keys (idempotent — no-op if already present)
    extended = extend_base_assumptions(cells)
    if extended:
        print("[extend-phase3] BASE_ASSUMPTIONS extended with Phase 3 keys (4-band AIHW structure)")
    else:
        print("[extend-phase3] BASE_ASSUMPTIONS already has Phase 3 keys — skipping")

    # Extend .env.example with MBS SA3 + AIHW download instructions
    extend_env_example()

    # Cell-replacement idempotency: if §1.4 Places API already exists,
    # remove the existing §1.4 + §1.5 cells and re-append the corrected versions.
    MARKER = "# §1.4 Places API"
    STOP_MARKERS = ["# §4 Competitor", "## Next Steps"]

    start_idx = None
    for i, c in enumerate(cells):
        if MARKER in "".join(c.get("source", [])):
            start_idx = i
            break

    # Build the new cells (§1.4 Places + §1.5 MBS/AIHW)
    new_acquisition_cells = places_cells() + mbs_aihw_cells()

    if start_idx is not None:
        # Find where the §1.4+§1.5 section ends (next major section marker or Next Steps)
        end_idx = len(cells)
        for j in range(start_idx + 1, len(cells)):
            src = "".join(cells[j].get("source", []))
            if any(marker in src for marker in STOP_MARKERS):
                end_idx = j
                break
        removed = end_idx - start_idx
        cells = cells[:start_idx] + cells[end_idx:]
        cells[start_idx:start_idx] = new_acquisition_cells
        print(f"[extend-phase3] replaced {removed} §1.4+§1.5 cells with {len(new_acquisition_cells)} corrected cells")
    else:
        # Fresh install — find the "## Next Steps" cell, insert before it
        insert_idx = len(cells)
        for i, c in enumerate(cells):
            src = "".join(c.get("source", []))
            if "## Next Steps" in src:
                insert_idx = i
                break
        cells[insert_idx:insert_idx] = new_acquisition_cells
        print(f"[extend-phase3] appended {len(new_acquisition_cells)} §1.4+§1.5 cells (fresh install)")

    # ── §4 Competitor Landscape cells (cell-replacement idempotency) ──
    COMP_MARKER = "# §4 Competitor Landscape"
    COMP_STOP_MARKERS = ["# §5 Demand Model", "## Next Steps"]

    comp_start_idx = None
    for i, c in enumerate(cells):
        if COMP_MARKER in "".join(c.get("source", [])):
            comp_start_idx = i
            break

    new_comp_cells = competitor_cells()

    if comp_start_idx is not None:
        # Find where the §4 section ends (next major section marker or Next Steps)
        comp_end_idx = len(cells)
        for j in range(comp_start_idx + 1, len(cells)):
            src = "".join(cells[j].get("source", []))
            if any(marker in src for marker in COMP_STOP_MARKERS):
                comp_end_idx = j
                break
        comp_removed = comp_end_idx - comp_start_idx
        cells = cells[:comp_start_idx] + cells[comp_end_idx:]
        cells[comp_start_idx:comp_start_idx] = new_comp_cells
        print(f"[extend-phase3] replaced {comp_removed} §4 cells with {len(new_comp_cells)} corrected cells")
    else:
        # Fresh install — find the "## Next Steps" cell, insert before it
        comp_insert_idx = len(cells)
        for i, c in enumerate(cells):
            src = "".join(c.get("source", []))
            if "## Next Steps" in src:
                comp_insert_idx = i
                break
        cells[comp_insert_idx:comp_insert_idx] = new_comp_cells
        print(f"[extend-phase3] appended {len(new_comp_cells)} §4 Competitor Landscape cells (fresh install)")

    # Write back
    nb["cells"] = cells
    notebook_path.write_text(
        json.dumps(nb, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    n_cells = len(cells)
    n_code = sum(1 for c in cells if c.get("cell_type") == "code")
    n_md = sum(1 for c in cells if c.get("cell_type") == "markdown")
    print(f"[extend-phase3] notebook now: {n_cells} cells ({n_code} code, {n_md} markdown)")


if __name__ == "__main__":
    main()
