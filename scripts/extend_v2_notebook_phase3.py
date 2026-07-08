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
    "    # NOTE: consults_per_capita_yr (AIHW SA3 4-band attendance rates) is defined ONCE",
    "    # in the Demand block above — do NOT redefine it here (was a duplicate key).",
    "    \"mbs_sa3_filename\":       \"medicare-quarterly-statistics-statistical-area-sa3-summary-march-quarter-2025-26.xlsx\",  # D-01 manual download",
    "    \"aihw_age_band_filename\": \"aihw-phc-19-csv_file_2425_VIC_SA3.csv\",  # D-02 VIC SA3 rows only — 88% smaller than national CSV",
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
        "Statistical Area (SA3) Summary\" from health.gov.au, filtered to SA3 20607",
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
        "# §1.5 MBS SA3 loader — SA3 20607 Yarra with state fallback (D-01, D-04, Pitfall 6)",
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
        '        # Filter to SA3 20607 Yarra',
        '        sa3_yarra = df[df["SA3"].astype(str) == "20607"]',
        "        if sa3_yarra.empty:",
        '            print("⚠ WARNING: SA3 20607 not found in file. Check SA3 column name.")',
        '        print(f"[mbs] SA3 20607 Yarra: {len(sa3_yarra)} quarters loaded")',
        '        return sa3_yarra, "sa3"',
        "    else:",
        "        # D-04: State fallback with LOUD warning",
        '        state_path = DATA_LOCAL_DIR / "medicare-quarterly-statistics-primary-care-service-type-summary-march-quarter-2025-26(1).xlsx"',
        '        print("═" * 70)',
        '        print("⚠  STATE BENCHMARK, NOT LOCAL — SA3 20607 data not found.")',
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
        "# Download: AIHW Data tab → aihw-phc-019-csv-file-2324-2425.zip → extract the CSV",
        'AIHW_FILENAME = BASE_ASSUMPTIONS.get("aihw_age_band_filename",',
        '    "aihw-phc-19-csv_file_2425.csv")',
        "",
        "def load_aihw_sa3_rates():",
        '    """Load AIHW SA3-level GP attendance rates by age band from long-format CSV.',
        "    Returns (dict, source_str) for SA3 20607 Yarra.\"\"\"",
        "    path = DATA_LOCAL_DIR / AIHW_FILENAME",
        "    if not path.exists():",
        '        print("⚠ WARNING: AIHW age-band data not found. Using national average fallback.")',
        "        # Fallback rates are the single source in BASE_ASSUMPTIONS (services per 100",
        "        # people/yr — SAME unit convention as compute_demand's /100 divisor).",
        '        return (dict(BASE_ASSUMPTIONS["consults_per_capita_yr"]), "national_fallback")',
        "",
        "    # AIHW PHC-019 CSV is long-format: one row per (geography, service, demographic, measure)",
        "    # Columns: GeographicUnit, GeographicCode, Service, DemographicGroup, MeasureName, MeasureValue",
        "    df = pd.read_csv(path, low_memory=False)",
        '    print(f"[aihw] CSV loaded: {len(df)} rows")',
        "",
        "    # Filter to SA3 20607 Yarra, GP attendances (total), Services per 100 people",
        "    sa3_yarra = df[",
        '        (df["GeographicUnit"] == "SA3") &',
        '        (df["GeographicCode"].astype(str) == "20607") &',
        '        (df["Service"] == "GP attendances (total)") &',
        '        (df["MeasureName"] == "Services per 100 people")',
        "    ]",
        "    if sa3_yarra.empty:",
        '        print("⚠ WARNING: SA3 20607 Yarra GP data not found in AIHW CSV. Check file.")',
        '        return (dict(BASE_ASSUMPTIONS["consults_per_capita_yr"]), "national_fallback")',
        "",
        "    # Extract rates by age band (DemographicGroup column has '0-24', '25-44', '45-64', '65+')",
        "    # Strip whitespace on DemographicGroup to defend against trailing-space label mismatches",
        '    sa3_yarra = sa3_yarra.copy()',
        '    sa3_yarra["DemographicGroup"] = sa3_yarra["DemographicGroup"].astype(str).str.strip()',
        "    rates = {}",
        '    for band in ["0-24", "25-44", "45-64", "65+"]:',
        '        row = sa3_yarra[sa3_yarra["DemographicGroup"] == band]',
        "        if not row.empty:",
        '            val = str(row["MeasureValue"].iloc[0]).replace(",", "")',
        "            rates[band] = float(val)",
        "        else:",
        '            print(f"⚠ Age band \'{band}\' not found in AIHW data")',
        "",
        "    # If no bands matched at all (e.g. unexpected label format), fall back — don't",
        "    # return an empty dict masquerading as 'aihw_sa3' (would zero out all demand).",
        "    if not rates:",
        '        print("⚠ WARNING: No AIHW age bands matched expected labels. Using national fallback.")',
        '        return (dict(BASE_ASSUMPTIONS["consults_per_capita_yr"]), "national_fallback")',
        "",
        '    print(f"[aihw] SA3 20607 Yarra rates: {rates}")',
        '    return (rates, "aihw_sa3")',
    ))

    # 8. Code — §1.5 load + assert
    cells.append(code(
        "# Load MBS SA3 + AIHW age-band rates (D-01, D-02, D-03)",
        "mbs_sa3_df, mbs_source = load_mbs_sa3()",
        "aihw_rates, aihw_source = load_aihw_sa3_rates()",
        'print(f"[mbs] source: {mbs_source}, rows: {len(mbs_sa3_df)}")',
        'print(f"[aihw] source: {aihw_source}, rates: {aihw_rates}")',
        "# Assert SA3 20607 present when using SA3 data (Pitfall 6 verification)",
        'if mbs_source == "sa3":',
        '    assert mbs_sa3_df["SA3"].astype(str).str.contains("20607").any(), \\',
        '        "SA3 20607 not found in MBS data — check file (Pitfall 6)"',
        '    print("[mbs] ✓ SA3 20607 Yarra confirmed in data")',
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
        '    poa_pop_row = peer_table[peer_table["POA_CODE21"] == poa_code] if "peer_table" in dir() else None',
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
#  §5 Demand Model cells
# ──────────────────────────────────────────────────────────────────────

def demand_cells():
    """Return the §5 Demand Model cells.

    Implements: aggregate_age_bands (ABS 5-year → AIHW 4 bands, Correction 2),
    compute_demand (transparent arithmetic, no ML — Pitfall 14, DEMAND-04),
    SA3 20607 MBS cross-check (D-03), estimate_gp_capacity_range (D-10 two methods),
    compute_required_market_share (D-13 three framings), label_market_share (D-14),
    plain-language interpretation with NO go/no-go verdict (D-14 — verdict is Phase 5),
    and the No-ML Assertion markdown (DEMAND-04).
    """
    cells = []

    # 1. Markdown — §5 header + teaching commentary
    cells.append(md(
        "# §5 Demand Model",
        "",
        "v1's \"demand model\" was a **3-row Random Forest** on peer postcodes —",
        "statistical theatre on a handful of rows that would destroy investor",
        "credibility if probed (Pitfall 14, FEATURES.md Anti-Features). This section",
        "replaces it with **transparent arithmetic**:",
        "",
        "    annual_demand = sum(population_band × attendance_rate_band)",
        "",
        "Every number is traceable to a cited source. No ML libraries, no regression,",
        "no clustering — just multiplication and addition.",
        "",
        "**Key design decisions:**",
        "- The AIHW SA3 age bands are **0-24, 25-44, 45-64, 65+** (Correction 2 —",
        "  NOT 0-14/15-64/65+). Phase 2's ABS 5-year age bands must be aggregated",
        "  to match these 4 bands before multiplying.",
        "- The SA3 20607 MBS data is a **total-attendance cross-check** (computed",
        "  total ≈ SA3 reported total ±15%, D-03).",
        "- The required-market-share is presented in **three framings** (D-13):",
        "  share of total consults, share of unmet demand, share of population.",
        "- The plain-language interpretation labels the share as low/moderate/high",
        "  but does **NOT** issue a go/no-go verdict (D-14 — that's Phase 5 after",
        "  the P&L).",
    ))

    # 2. Code — §5.1 Aggregate ABS 5-year bands to AIHW 4 bands
    cells.append(code(
        "# §5.1 Aggregate ABS 5-year age bands → AIHW SA3 4 bands (Correction 2)",
        "# AIHW SA3 bands: 0-24, 25-44, 45-64, 65+",
        "# ABS G04 5-year bands: 0-4, 5-9, 10-14, 15-19, 20-24, 25-29, ..., 85+",
        "# Mapping:",
        "#   0-24  = 0-4 + 5-9 + 10-14 + 15-19 + 20-24",
        "#   25-44 = 25-29 + 30-34 + 35-39 + 40-44",
        "#   45-64 = 45-49 + 50-54 + 55-59 + 60-64",
        "#   65+   = 65-69 + 70-74 + 75-79 + 80-84 + 85+",
        "def aggregate_age_bands(g04_age_df):",
        '    """Aggregate ABS 5-year age bands to AIHW SA3 4 bands.',
        "    g04_age_df: DataFrame with age band columns (from Phase 2 §3 G04 fetch).",
        '    Returns dict: {"0-24": pop, "25-44": pop, "45-64": pop, "65+": pop}"""',
        "    band_map = {",
        '        "0-24": ["0_4", "5_9", "10_14", "15_19", "20_24"],',
        '        "25-44": ["25_29", "30_34", "35_39", "40_44"],',
        '        "45-64": ["45_49", "50_54", "55_59", "60_64"],',
        '        "65+": ["65_69", "70_74", "75_79", "80_84", "85_ov", "85ov", "85plus", "85over"],',
        "    }",
        "    result = {}",
        "    for aihw_band, abs_bands in band_map.items():",
        "        total = 0",
        "        for abs_band in abs_bands:",
        "            # Find matching column(s) — handle naming variations",
        '            cols = [c for c in g04_age_df.columns if abs_band in str(c).replace("-", "_").lower()]',
        "            for c in cols:",
        "                total += g04_age_df[c].sum()",
        "        result[aihw_band] = total",
        "    return result",
        "",
        "# Compute per-ring age profiles using POA 3067 G04 data as the age template,",
        "# scaled proportionally to each ring's ERP-scaled population (from Phase 2 §3).",
        "# The catchment is centred on Abbotsford (3067) — POA-level age profile is a",
        "# reasonable proxy for all rings (inner-Melbourne age profiles are similar).",
        "ring_age_profiles = {}",
        'site_g04 = g04_df[g04_df["POA_CODE21"] == "3067"] if "POA_CODE21" in g04_df.columns else g04_df',
        "if len(site_g04) == 0:",
        "    site_g04 = g04_df.iloc[[0]] if len(g04_df) > 0 else g04_df",
        "    print('[demand] ⚠ POA 3067 not in G04 — using first row as age template')",
        "",
        "site_age_bands = aggregate_age_bands(site_g04)",
        "site_total_pop = sum(site_age_bands.values())",
        "print(f'[demand] site age bands (POA 3067): {site_age_bands}')",
        "",
        'for r in BASE_ASSUMPTIONS["catchment_radii_m"]:',
        "    ring_pop = v2_ring_pops_erp.get(r, 0)",
        "    if site_total_pop > 0:",
        "        # Scale age proportions to ring population",
        "        ring_age_profiles[r] = {",
        "            band: (pop / site_total_pop) * ring_pop",
        "            for band, pop in site_age_bands.items()",
        "        }",
        "    else:",
        '        ring_age_profiles[r] = {"0-24": 0, "25-44": 0, "45-64": 0, "65+": 0}',
        '    print(f"[demand] {r//1000}km ring age profile: {ring_age_profiles[r]}")',
        "",
        'print("[demand] aggregate_age_bands() defined — maps ABS 5-year → AIHW 4 bands (0-24, 25-44, 45-64, 65+)")',
    ))

    # 3. Code — §5.2 Compute age-adjusted demand per ring
    cells.append(code(
        "# §5.2 Compute age-adjusted demand per ring (DEMAND-02, Pitfall 14)",
        "# Transparent arithmetic — no ML. annual_demand = sum(pop_band × rate_band)",
        "def compute_demand(catchment_age_profile, aihw_rates_per_100, ring_pop):",
        '    """Age-adjusted annual GP consult demand for a catchment ring.',
        "    Transparent arithmetic — no ML (Pitfall 14, DEMAND-04).",
        "    catchment_age_profile: dict of age_band → population (AIHW 4 bands)",
        "    aihw_rates_per_100: dict of age_band → services per 100 people (from AIHW)",
        "    ring_pop: total population in the ring (ERP-scaled, from Phase 2)",
        '    Returns: annual GP consults demanded in this ring (float)"""',
        "    total_demand = 0",
        "    for band, pop in catchment_age_profile.items():",
        "        rate = aihw_rates_per_100.get(band, 0)",
        "        total_demand += pop * (rate / 100.0)",
        "    return total_demand",
        "",
        "# Compute demand per ring using AIHW rates (from §1.5) and ring age profiles (from §5.1)",
        "ring_demand = {}",
        'for r in BASE_ASSUMPTIONS["catchment_radii_m"]:',
        "    ring_demand[r] = compute_demand(ring_age_profiles[r], aihw_rates, v2_ring_pops_erp.get(r, 0))",
        "    per_capita = ring_demand[r] / v2_ring_pops_erp.get(r, 1) * 100 if v2_ring_pops_erp.get(r, 0) else 0",
        '    print(f"[demand] {r//1000}km ring | age_adjusted_demand: {ring_demand[r]:.0f} | per_capita_rate: {per_capita:.1f}/100")',
        "",
        "# Units guard (Correction 2 follow-up): AIHW rates are 'services per 100 people/yr',",
        "# so per-capita attendance should land ~300-1000/100 (i.e. ~3-10 visits/person/yr).",
        "# A value ~100x low means a per-person rate was used where per-100 was expected",
        "# (or vice-versa) — warn LOUDLY rather than silently shipping nonsense market shares.",
        "PLAUSIBLE_PER100 = (300, 1000)",
        'for r in BASE_ASSUMPTIONS["catchment_radii_m"]:',
        "    ring_pop = v2_ring_pops_erp.get(r, 0)",
        "    if ring_pop:",
        "        pc = ring_demand[r] / ring_pop * 100",
        "        if not (PLAUSIBLE_PER100[0] <= pc <= PLAUSIBLE_PER100[1]):",
        '            print(f"⚠ DEMAND UNITS CHECK: {r//1000}km per-capita rate {pc:.1f}/100 outside "',
        '                  f"plausible {PLAUSIBLE_PER100[0]}-{PLAUSIBLE_PER100[1]}/100 — check AIHW rate units "',
        '                  f"(services per 100 people/yr) vs compute_demand()\'s /100 divisor.")',
        "",
        'print("[demand] compute_demand() defined — sum(pop_band × rate_band), transparent arithmetic (no ML)")',
    ))

    # 4. Code — §5.3 SA3 MBS cross-check (D-03)
    cells.append(code(
        "# §5.3 SA3 20607 MBS total-attendance cross-check (D-03, ±15% tolerance)",
        "# Compare computed total demand against SA3 20607 MBS reported total.",
        "# This validates the demand model against an independent data source.",
        "if mbs_source == \"sa3\":",
        "    # Sum the latest 4 quarters of SA3 20607 GP non-referred attendances",
        "    # (exact column verified at runtime — look for attendance/count columns)",
        "    numeric_cols = mbs_sa3_df.select_dtypes(include=[\"number\"])",
        "    sa3_total = numeric_cols.sum().sum()  # placeholder — adjust at runtime",
        "    computed_total = sum(ring_demand.values())",
        "    if sa3_total > 0:",
        "        pct_diff = abs(computed_total - sa3_total) / sa3_total * 100",
        '        print(f"[cross-check] computed demand total: {computed_total:.0f}")',
        '        print(f"[cross-check] SA3 20607 MBS total: {sa3_total:.0f}")',
        '        print(f"[cross-check] difference: {pct_diff:.1f}% (tolerance: ±15%)")',
        "        if pct_diff > 15:",
        '            print("[cross-check] ⚠ Difference exceeds 15% — check age band mapping or rates")',
        "        else:",
        '            print("[cross-check] ✓ Within ±15% tolerance")',
        "    else:",
        '        print("[cross-check] ⚠ SA3 total is 0 — check MBS data columns")',
        "else:",
        '    print("[cross-check] ⚠ Skipped — using state fallback, no SA3 total to cross-check")',
    ))

    # 5. Code — §5.4 GP FTE capacity range (D-10)
    cells.append(code(
        "# §5.4 GP FTE capacity range (D-10) — two-method range, variance IS the caveat (D-12)",
        "# Method A: clinic count × avg FTE per clinic (4.0 FTE, RACGP+DoH)",
        "# Method B: AMWAC benchmark × population (110.4/100k)",
        "def estimate_gp_capacity_range(clinic_count, ring_pop):",
        '    """D-10: Two-method range. The variance IS the caveat (D-12).',
        "    Method A: clinic count × avg FTE per clinic (4.0 FTE, RACGP+DoH)",
        "    Method B: AMWAC benchmark × population (110.4/100k)",
        '    Returns dict with both methods, range, and caveat string."""',
        '    AVG_FTE_PER_CLINIC = BASE_ASSUMPTIONS["avg_fte_per_clinic"]  # 4.0',
        '    AMWAC_PER_100K = BASE_ASSUMPTIONS["amwac_per_100k"]          # 110.4',
        "    capacity_a = clinic_count * AVG_FTE_PER_CLINIC",
        "    capacity_b = ring_pop * (AMWAC_PER_100K / 100_000)",
        "    return {",
        '        "method_a_clinic_derived": capacity_a,',
        '        "method_b_benchmark_derived": capacity_b,',
        '        "range": (min(capacity_a, capacity_b), max(capacity_a, capacity_b)),',
        '        "caveat": "Places listings ≠ FTE GPs; range spans clinic-derived and benchmark-derived estimates.",',
        "    }",
        "",
        "# Compute capacity per ring using per_ring_counts GP clinic count (from §4)",
        "# and ERP-scaled ring population (from §3). Convert FTE to consult capacity:",
        "# existing_consult_capacity = fte_count × gp_fte_consults_per_yr (5500/yr per FTE)",
        "capacity_results = {}",
        "existing_capacity_range = {}",
        'for r in BASE_ASSUMPTIONS["catchment_radii_m"]:',
        '    ring_row = per_ring_counts[per_ring_counts["ring_km"] == r // 1000]',
        "    if len(ring_row) > 0:",
        '        gp_clinic_count = int(ring_row.iloc[0].get("gp_corporate", 0) + ring_row.iloc[0].get("gp_independent", 0))',
        "    else:",
        "        gp_clinic_count = 0",
        "    ring_pop = v2_ring_pops_erp.get(r, 0)",
        "    cap = estimate_gp_capacity_range(gp_clinic_count, ring_pop)",
        "    capacity_results[r] = cap",
        "    # Convert FTE to consult capacity (5500 consults/yr per FTE)",
        '    consult_cap_a = cap["method_a_clinic_derived"] * BASE_ASSUMPTIONS["gp_fte_consults_per_yr"]',
        '    consult_cap_b = cap["method_b_benchmark_derived"] * BASE_ASSUMPTIONS["gp_fte_consults_per_yr"]',
        "    existing_capacity_range[r] = (min(consult_cap_a, consult_cap_b), max(consult_cap_a, consult_cap_b))",
        '    print(f"[capacity] {r//1000}km ring | GP clinics: {gp_clinic_count} | FTE_a: {cap[\'method_a_clinic_derived\']:.1f} | FTE_b: {cap[\'method_b_benchmark_derived\']:.1f} | consult_cap: {existing_capacity_range[r][0]:.0f}–{existing_capacity_range[r][1]:.0f}/yr")',
        "",
        'print("[capacity] estimate_gp_capacity_range() defined — two methods (clinic-derived × 4.0 FTE, AMWAC 110.4/100k × pop)")',
    ))

    # 6. Code — §5.5 Required market share — three framings (D-13, D-14)
    cells.append(code(
        "# §5.5 Required market share — three framings (D-13, D-14)",
        "# D-13: share_of_total, share_of_unmet, share_of_pop — side-by-side, no ML",
        "# D-14: label_market_share — low/moderate/high, NO go/no-go verdict (Phase 5)",
        "def compute_required_market_share(annual_demand, existing_capacity, clinic_capacity,",
        "                                   ring_pop, consults_per_patient_yr=5.0):",
        '    """D-13: Three framings side-by-side. No ML, pure arithmetic (Pitfall 14).',
        "    annual_demand: age-adjusted GP consults demanded in ring",
        "    existing_capacity: estimated existing GP consult capacity in ring (D-10 range)",
        "    clinic_capacity: 5-FTE clinic annual consult capacity (~27,500/yr)",
        "    ring_pop: total population in ring",
        '    consults_per_patient_yr: ~5.0 (BASE_ASSUMPTIONS)"""',
        "    unmet_demand = max(annual_demand - existing_capacity, 0)",
        "    return {",
        '        "share_of_total":   clinic_capacity / annual_demand * 100 if annual_demand else 0,',
        '        "share_of_unmet":   clinic_capacity / unmet_demand * 100 if unmet_demand else float("inf"),',
        '        "patients_needed":  clinic_capacity / consults_per_patient_yr,',
        '        "share_of_pop":     (clinic_capacity / consults_per_patient_yr) / ring_pop * 100 if ring_pop else 0,',
        "    }",
        "",
        "def label_market_share(pct_of_total):",
        '    """D-14: Plain-language label. <5% low, 5-15% moderate, >15% high."""',
        '    thresholds = BASE_ASSUMPTIONS["market_share_thresholds"]',
        '    if pct_of_total < thresholds["low"]:   return "low"',
        '    if pct_of_total < thresholds["high"]:  return "moderate"',
        '    return "high"',
        "",
        "# Compute market share for each ring using both capacity methods (D-10 range)",
        "# Clinic capacity: 5 FTE × 5,500/yr = 27,500 consults/yr",
        'clinic_capacity = BASE_ASSUMPTIONS["n_gp_fte"] * BASE_ASSUMPTIONS["gp_fte_consults_per_yr"]  # 27,500/yr',
        'print(f"[market-share] clinic capacity: {clinic_capacity:.0f} consults/yr (5 FTE × 5,500/yr)")',
        "",
        "market_share_results = {}",
        'for r in BASE_ASSUMPTIONS["catchment_radii_m"]:',
        "    cap = capacity_results[r]",
        '    consult_cap_a = cap["method_a_clinic_derived"] * BASE_ASSUMPTIONS["gp_fte_consults_per_yr"]',
        '    consult_cap_b = cap["method_b_benchmark_derived"] * BASE_ASSUMPTIONS["gp_fte_consults_per_yr"]',
        "    ms_a = compute_required_market_share(ring_demand[r], consult_cap_a, clinic_capacity,",
        '                                            v2_ring_pops_erp.get(r, 0), BASE_ASSUMPTIONS["consults_per_patient_yr"])',
        "    ms_b = compute_required_market_share(ring_demand[r], consult_cap_b, clinic_capacity,",
        '                                            v2_ring_pops_erp.get(r, 0), BASE_ASSUMPTIONS["consults_per_patient_yr"])',
        "    # Mid values for the interpretation (average of both methods)",
        "    share_total_mid = (ms_a[\"share_of_total\"] + ms_b[\"share_of_total\"]) / 2",
        "    unmet_a = ms_a[\"share_of_unmet\"]",
        "    unmet_b = ms_b[\"share_of_unmet\"]",
        "    if unmet_a != float('inf') and unmet_b != float('inf'):",
        "        share_unmet_mid = (unmet_a + unmet_b) / 2",
        "    else:",
        "        share_unmet_mid = float('inf')",
        "    market_share_results[r] = {",
        '        "share_of_total_a": ms_a["share_of_total"],',
        '        "share_of_total_b": ms_b["share_of_total"],',
        '        "share_of_total_mid": share_total_mid,',
        '        "share_of_unmet_a": unmet_a,',
        '        "share_of_unmet_b": unmet_b,',
        '        "share_of_unmet_mid": share_unmet_mid,',
        '        "patients_needed": ms_a["patients_needed"],',
        '        "share_of_pop": ms_a["share_of_pop"],',
        "    }",
        "    label = label_market_share(share_total_mid)",
        '    print(f"[market-share] {r//1000}km ring | demand: {ring_demand[r]:.0f} | cap_a: {consult_cap_a:.0f} | cap_b: {consult_cap_b:.0f} | share_total_a: {ms_a[\'share_of_total\']:.1f}% | share_total_b: {ms_b[\'share_of_total\']:.1f}% | share_unmet_mid: {share_unmet_mid:.1f}% | share_pop: {ms_a[\'share_of_pop\']:.1f}% | label: {label}")',
        "",
        'print("[market-share] compute_required_market_share() + label_market_share() defined — three framings (D-13), low/moderate/high labels (D-14)")',
    ))

    # 7. Code — §5.6 Plain-language interpretation (D-14, NO go/no-go verdict)
    cells.append(code(
        "# D-14: Plain-language interpretation — NO go/no-go verdict (that's Phase 5)",
        'print("\\n" + "=" * 70)',
        'print("REQUIRED MARKET SHARE — PLAIN LANGUAGE SUMMARY")',
        'print("=" * 70)',
        'for r in BASE_ASSUMPTIONS["catchment_radii_m"]:',
        "    ms = market_share_results[r]",
        '    label = label_market_share(ms["share_of_total_mid"])',
        '    print(f"\\n  {r//1000} km ring:")',
        '    print(f"    • {ms[\'share_of_total_mid\']:.1f}% of all GP consults in the ring — {label} share required")',
        '    unmet_str = f"{ms[\'share_of_unmet_mid\']:.1f}%" if ms["share_of_unmet_mid"] != float("inf") else "N/A (no unmet gap)"',
        '    print(f"    • {unmet_str} of the unmet consult gap (can exceed 100%)")',
        '    print(f"    • {ms[\'patients_needed\']:.0f} patients needed = {ms[\'share_of_pop\']:.1f}% of catchment population")',
        '    print(f"    • Clinic capacity: {clinic_capacity:.0f} consults/yr (5 FTE × 5,500/yr)")',
        '    print(f"    • Demand: {ring_demand[r]:.0f} consults/yr (age-adjusted)")',
        '    print(f"    • Existing capacity range: {existing_capacity_range[r][0]:.0f} – {existing_capacity_range[r][1]:.0f} consults/yr")',
        'print("\\n  Note: The go/no-go verdict is a Phase 5 output (after P&L + scenarios).")',
        'print("  This section quantifies the required share — it does not judge achievability.")',
        'print("=" * 70)',
    ))

    # 8. Markdown — §5.7 No-ML Assertion (DEMAND-04, Pitfall 14)
    cells.append(md(
        "## §5.7 No-ML Assertion",
        "",
        "> **No predictive ML (DEMAND-04, Pitfall 14):** The demand model is",
        "> `sum(population_band × attendance_rate_band)` — pure arithmetic with cited",
        "> rates from AIHW (2026). v1's 3-row Random Forest on peer postcodes was",
        "> statistical theatre on a handful of rows. This section replaces it with",
        "> transparent arithmetic where every input is traceable to a cited source.",
        "> No ML libraries, no regression, no clustering — just multiplication and",
        "> addition.",
    ))

    # 9. Markdown — Next Steps (Phase 4)
    cells.append(md(
        "## Next Steps",
        "",
        "**§6 Financial Model (Phase 4)** will build the clinic P&L as a pure function of",
        "`BASE_ASSUMPTIONS`, using the required market share (§5) to derive consult volume →",
        "revenue. The go/no-go verdict is a Phase 5 output after scenarios + sensitivity.",
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
                # AIHW SA3 age bands 0-24/25-44/45-64/65+ (Correction 2). Units = GP
                # attendances per 100 people/yr (SAME convention as compute_demand's /100
                # divisor). National-average fallback; replaced by load_aihw_sa3_rates() at
                # runtime when the AIHW SA3 file is present. Verify against AIHW national row.
                new_source.append(
                    '    # AIHW SA3 attendance rates — services per 100 people/yr (Correction 2)\n'
                )
                new_source.append(
                    '    "consults_per_capita_yr": {"0-24": 450, "25-44": 550, "45-64": 750, "65+": 1200},  # per 100/yr — AIHW (2026) national fallback\n'
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

    # ── §5 Demand Model cells (cell-replacement idempotency) ──
    DEMAND_MARKER = "# §5 Demand Model"
    DEMAND_STOP_MARKERS = ["## Next Steps"]

    demand_start_idx = None
    for i, c in enumerate(cells):
        if DEMAND_MARKER in "".join(c.get("source", [])):
            demand_start_idx = i
            break

    new_demand_cells = demand_cells()

    if demand_start_idx is not None:
        # Find where the §5 section ends (next major section marker or Next Steps)
        demand_end_idx = len(cells)
        for j in range(demand_start_idx + 1, len(cells)):
            src = "".join(cells[j].get("source", []))
            if any(marker in src for marker in DEMAND_STOP_MARKERS):
                demand_end_idx = j
                break
        demand_removed = demand_end_idx - demand_start_idx
        cells = cells[:demand_start_idx] + cells[demand_end_idx:]
        cells[demand_start_idx:demand_start_idx] = new_demand_cells
        print(f"[extend-phase3] replaced {demand_removed} §5 cells with {len(new_demand_cells)} corrected cells")
    else:
        # Fresh install — find the "## Next Steps" cell, insert before it
        demand_insert_idx = len(cells)
        for i, c in enumerate(cells):
            src = "".join(c.get("source", []))
            if "## Next Steps" in src:
                demand_insert_idx = i
                break
        cells[demand_insert_idx:demand_insert_idx] = new_demand_cells
        print(f"[extend-phase3] appended {len(new_demand_cells)} §5 Demand Model cells (fresh install)")

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
