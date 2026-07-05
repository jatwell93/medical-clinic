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
    new_cells = places_cells() + mbs_aihw_cells()

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
        cells[start_idx:start_idx] = new_cells
        print(f"[extend-phase3] replaced {removed} §1.4+§1.5 cells with {len(new_cells)} corrected cells")
    else:
        # Fresh install — find the "## Next Steps" cell, insert before it
        insert_idx = len(cells)
        for i, c in enumerate(cells):
            src = "".join(c.get("source", []))
            if "## Next Steps" in src:
                insert_idx = i
                break
        cells[insert_idx:insert_idx] = new_cells
        print(f"[extend-phase3] appended {len(new_cells)} §1.4+§1.5 cells (fresh install)")

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
