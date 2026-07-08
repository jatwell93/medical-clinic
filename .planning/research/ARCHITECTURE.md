# Architecture Research

**Domain:** Reusable multi-site geospatial/financial feasibility tool (Colab notebook, VIC pilot)
**Researched:** 2026-07-07
**Confidence:** HIGH (v1.0 architecture fully audited; integration points traced cell-by-cell; SA1 shapefile attributes verified live)

## Purpose of This Document

This is a **v2.0 integration architecture** — it assumes the v1.0 architecture (documented in the prior cycle and shipped as 88 cells / 36 validator checks) is understood. The focus is exclusively on **how the new multi-site features integrate with the existing v1.0 notebook structure**: what changes, what's new, what's deleted, and in what order to build it.

The v1.0 notebook (`Johnston_St_v2.ipynb`, 88 cells, §0–§8) is the starting point. v2.0 generalises it from a single hardcoded Abbotsford study into a parameterised tool that accepts any Victorian street address. Abbotsford ships as the default config so v2.0 out-of-the-box reproduces v1.0 (minus pharmacy synergy).

---

## Standard Architecture

### System Overview (v2.0 — changes from v1.0 marked)

```
┌──────────────────────────────────────────────────────────────────────┐
│ §0 SETUP & CONFIG                                                    │
│  ┌────────────┐ ┌──────────────┐ ┌────────────────────────────────┐  │
│  │ pip installs│ │ env detect   │ │ §0.3 PARAMS (RESTRUCTURED)     │  │
│  │ + imports   │ │ (Colab/local)│ │  SITE_CONFIG (user inputs)  →  │  │
│  └────────────┘ └──────┬───────┘ │  BASE_ASSUMPTIONS (constants) │  │
│                          │       └───────────────┬────────────────┘  │
│                          │                       │                   │
│                          │       ┌───────────────▼────────────────┐  │
│                          │       │ §0.4 Upload local data (Colab) │  │
│                          │       └───────────────┬────────────────┘  │
├──────────────────────────┴───────────────────────┴──────────────────┤
│ §1 DATA ACQUISITION LAYER (all cached)                               │
│  ┌──────────┐ ┌───────────────┐ ┌──────────────┐ ┌───────────────┐  │
│  │ §1.1     │ │ §1.2 Geocode  │ │ §1.3 DERIVE  │ │ §1.4 ABS Data │  │
│  │ Cache    │ │ site address  │ │ POA + SA3    │ │ API (G01/G02/ │  │
│  │ session  │ │ (Google)      │ │ from point   │ │ G04 for DERIV │  │
│  └──────────┘ └──────┬────────┘ │ (point-in-   │ │ ED POA + peers│  │
│                         │        │  polygon)    │ │ + DERIVED SA3 │  │
│                         │        └──────┬───────┘ └──────┬────────┘  │
│                         │               │                │           │
│                         │       ┌───────▼────────────────▼──────┐   │
│                         │       │  data/cache/*.json             │   │
│                         │       └───────────────────────────────┘   │
│                         │               │                │           │
│                         │       ┌───────▼────────┐ ┌─────▼───────┐  │
│                         │       │ §1.5 Google     │ │ §1.6 MBS    │  │
│                         │       │ Places (nearby) │ │ SA3 (DERIV  │  │
│                         │       │                 │ │ ED SA3)     │  │
│                         │       └─────┬───────────┘ └─────┬──────┘  │
├─────────────────────────┴─────────────┴───────────────────┴─────────┤
│ §2 GEOSPATIAL CATCHMENT (reuses §1.3 geometries)                    │
│  site point → 1/3/5 km buffers (EPSG:7855) → SA1 area apportionment │
├──────────────────────────────────────────────────────────────────────┤
│ §3 DEMOGRAPHICS │ §4 COMPETITORS │ §5 DEMAND MODEL                   │
│ (derived POA    │ (Places →      │ (age-adjusted demand vs           │
│  + peers)       │  dedupe/class) │  capacity → required share)       │
├──────────────────────────────────────────────────────────────────────┤
│ §6 FINANCIAL MODEL │ §7 SCENARIOS (pharmacy synergy DELETED)        │
│ (clinic_pnl(a) —   │ (base/opt/pess + tornado + billing-mix)        │
│  pure function)    │                                              │
├──────────────────────────────────────────────────────────────────────┤
│ §8 EXECUTIVE REPORT                                                  │
│  site-parameterised template → slugified filename → PDF             │
├──────────────────────────────────────────────────────────────────────┤
│ STORES: data/cache/ (JSON)  data/local/ (shapefiles, MBS, AIHW)     │
│         outputs/ (maps, report .html/.pdf — DYNAMIC FILENAME)       │
└──────────────────────────────────────────────────────────────────────┘
```

**Key structural changes from v1.0:**
1. **§0.3 restructured** — split into `SITE_CONFIG` (user inputs) + `BASE_ASSUMPTIONS` (constants), same cell
2. **§1.3 NEW** — POA + SA3 derivation cell (point-in-polygon), inserted between geocode and ABS fetch
3. **§1.4 ABS fetch reparameterised** — uses derived POA/SA3 instead of hardcoded 3067/20604
4. **§1.6 MBS reparameterised** — uses derived SA3 instead of hardcoded 20607
5. **§7.6 pharmacy synergy DELETED** — cells 81–82 removed
6. **§8 report template parameterised** — site name/address from SITE_CONFIG, filename slugified

### Component Responsibilities (v2.0 — new/modified marked)

| Component | Responsibility | v2.0 Status | Implementation |
|-----------|----------------|-------------|----------------|
| §0.1 Installs | pip installs, imports | unchanged | One cell; `%pip install -q` guarded |
| §0.2 Env/paths | Detect Colab/Windows, PROJECT_ROOT, keys | unchanged | `try: from google.colab import userdata` |
| §0.3 PARAMS | All tunable inputs in one cell | **MODIFIED** — restructured into SITE_CONFIG + BASE_ASSUMPTIONS | See Pattern 6 below |
| §0.4 Upload | Colab file upload for local assets | unchanged | No-op on Windows |
| §1.1 Cache | CachedSession construction | unchanged | `requests_cache.CachedSession` |
| §1.2 ABS smoke | Keyless ABS API connectivity test | unchanged | SDMX-ML XML smoke test |
| §1.2 Geocode | Geocode site address → lat/lon | **MODIFIED** — reads SITE_CONFIG["address"] | Google Geocoding API, cached |
| §1.3 Derive POA/SA3 | Point-in-polygon on ASGS boundaries → site POA + SA3 | **NEW** | See Pattern 7 below |
| §1.4 ABS fetch | G01/G02/G04 for derived POA + user peers + derived SA3 | **MODIFIED** — parameterised POA/SA3 | `fetch_abs_csv(flow, key)` with derived codes |
| §1.5 Places | Nearby Search with saturation subdivision | **MODIFIED** — uses derived lat/lon (already did in v1.0) | Unchanged logic, just site-agnostic |
| §1.6 MBS SA3 | SA3-level MBS utilisation | **MODIFIED** — uses derived SA3 instead of hardcoded 20607 | Filter xlsx on `SA3 == site_sa3_code` |
| §2 Catchment | Buffers, area apportionment, maps | **MODIFIED** — reuses §1.3 geometries; plausibility range becomes site-relative | `gpd.overlay` in EPSG:7855 |
| §3 Demographics | Catchment profile, peer table | **MODIFIED** — peer table conditional on user-supplied peers | Skip peer section if `PEER_POSTCODES` empty |
| §4 Competitors | Dedupe, classify, per-ring counts, maps | unchanged (already site-agnostic) | Pure pandas on cached Places JSON |
| §5 Demand model | Age-adjusted consult demand vs capacity | unchanged | Transparent arithmetic |
| §6 Financial model | `clinic_pnl(a)` pure function | **MODIFIED** — FTE from SITE_CONFIG, floor_area parameterised | Pure function of params dict |
| §7 Scenarios | Base/opt/pess overrides, tornado, billing-mix | **MODIFIED** — §7.6 pharmacy synergy DELETED | Override dicts, no pharmacy section |
| §8 Report | Verdict, assumptions register, Jinja2 template, PDF | **MODIFIED** — site-parameterised template, slugified filename | See Pattern 8 below |

---

## Recommended Project Structure

The repo layout is unchanged from v1.0. The notebook section layout changes:

```
§0  Setup & Configuration
    0.1 Installs & imports
    0.2 Environment/paths/keys
    0.3 Parameters & Assumptions  ← RESTRUCTURED (SITE_CONFIG + BASE_ASSUMPTIONS)
    0.4 Upload local data files (Colab only)
§1  Data Acquisition & Caching
    1.1 Cache session + ABS smoke test
    1.2 Geocode site address        ← reads SITE_CONFIG["address"]
    1.3 Derive POA + SA3 from point ← NEW CELL
    1.4 ABS census fetch            ← parameterised (derived POA + peers)
    1.5 Google Places fetches       ← already site-agnostic
    1.6 MBS SA3 data                ← parameterised (derived SA3)
§2  Geospatial Catchment (reuses §1.3 geometries)
§3  Demographics (conditional peer table)
§4  Competitor Landscape
§5  Demand Model
§6  Financial Model (FTE from SITE_CONFIG)
§7  Scenarios & Sensitivity (pharmacy synergy DELETED)
§8  Executive Report (site-parameterised, slugified filename)
```

### Structure Rationale

- **§0.3 stays as one cell:** The "single parameters cell" pattern (PIPE-05) is preserved. SITE_CONFIG and BASE_ASSUMPTIONS live in the same cell, with SITE_CONFIG defined first. This keeps the validator's `first_def_cell("BASE_ASSUMPTIONS")` check working and maintains the auditability property.
- **§1.3 is a new cell, not a new section:** It's a derivation step within §1 (Data Acquisition), not a new top-level section. It sits between geocode (§1.2) and ABS fetch (§1.4) because ABS fetch depends on the derived POA/SA3.
- **§7.6 deletion is a cell removal, not a renumbering:** The §7 section keeps its number; cells 81–82 (markdown + code) are simply removed. §7.7 Interpretation (cell 83) becomes §7.6 or just stays as the tail of §7.

---

## Architectural Patterns

### Pattern 1: Cached Fetch Boundary (unchanged from v1.0)

**What:** Every external request goes through `CachedSession`. No analysis cell calls `requests.get` directly.
**When to use:** Always — for geocoding, ABS API, Google Places.
**Trade-offs:** + Free/deterministic re-runs. − Stale data risk (acceptable; invalidation = delete cache file).

**v2.0 note:** Cache keys must now include the derived POA/SA3 codes (not hardcoded 3067/20604). The `cache_key()` helper already produces filesystem-safe keys from arbitrary parts — just pass `site_poa` and `site_sa3` as parts. Different sites produce different cache files automatically.

### Pattern 2: Single Parameters Cell (unchanged from v1.0)

**What:** All tunable inputs live in one cell (§0.3). Downstream cells only read; never redefine.
**When to use:** Always for scenario-driven models.
**v2.0 note:** The cell now contains TWO dicts (SITE_CONFIG + BASE_ASSUMPTIONS) but the principle is identical — one place to audit.

### Pattern 3: Pure-Function Financial Model (unchanged from v1.0)

**What:** `clinic_pnl(a: dict) -> dict` with no globals. Scenarios are override dicts: `{**BASE_ASSUMPTIONS, **overrides}`.
**When to use:** Whenever scenarios/sensitivity are required.
**v2.0 note:** `n_gp_fte` and `n_allied_fte` now come from SITE_CONFIG (user input) but flow through BASE_ASSUMPTIONS the same way. The merge point is `BASE_ASSUMPTIONS["n_gp_fte"] = SITE_CONFIG["n_gp_fte"]` in §0.3 — downstream is unchanged.

### Pattern 4: Dual-Environment Bootstrap (unchanged from v1.0)

**What:** One cell detects runtime, resolves paths/secrets. Everything downstream uses `PROJECT_ROOT`-relative `pathlib`.
**v2.0 note:** No changes needed. The bootstrap is already site-agnostic.

### Pattern 5: Report Metrics Accumulator (unchanged from v1.0)

**What:** Each section deposits headline numbers into `report = {}`. §8 renders from that dict.
**v2.0 note:** `report["site_name"]`, `report["site_address"]`, `report["site_slug"]` are deposited by §1.2/§1.3 and consumed by §8's template + filename logic.

### Pattern 6: Site Config / Assumptions Split (NEW — v2.0)

**What:** The §0.3 cell contains two dicts: `SITE_CONFIG` (user-supplied site inputs) and `BASE_ASSUMPTIONS` (financial/demand constants). SITE_CONFIG is defined first; its values are merged into BASE_ASSUMPTIONS so downstream code sees a single dict.

**When to use:** Whenever a notebook accepts user site inputs but also has a large fixed assumption set. This preserves the "single params cell" auditability while cleanly separating "what the user provides" from "what the tool assumes."

**Trade-offs:** + User inputs are visually distinct from model constants; default config reproduces v1.0; validator can check both dicts. − Slightly more complex than a single flat dict — mitigate with clear section headers and comments.

**Example:**
```python
# ═══════════════════════════════════════════════════════════════
#  SITE CONFIG — user-supplied site inputs (v2.0 multi-site)
#  Default = Abbotsford (reproduces v1.0). Change these for a new site.
# ═══════════════════════════════════════════════════════════════

SITE_CONFIG = {
    "address":        "292-296 Johnston St, Abbotsford VIC 3067",
    "state":          "VIC",              # v2.0 pilot: VIC only
    "postcode":       "3067",             # user-supplied; verified via point-in-polygon
    "n_gp_fte":       5,                  # clinic size — drives financial model
    "n_allied_fte":   1,
    "peer_postcodes": ["3067", "3066", "3068", "3070", "3078", "3079",
                       "3101", "3121", "3122", "3123"],  # optional; empty = skip peers
    "floor_area_sqm": 170,                # site-specific; drives fit-out capex
}

# ═══════════════════════════════════════════════════════════════
#  BASE ASSUMPTIONS — model constants (unchanged from v1.0)
#  Downstream cells READ these; they never redefine them.
#  Scenarios: {**BASE_ASSUMPTIONS, **overrides}
# ═══════════════════════════════════════════════════════════════

CATCHMENT_RADII_M = [1000, 3000, 5000]
FORCE_REFRESH = False

BASE_ASSUMPTIONS = {
    # --- Site & catchment (from SITE_CONFIG) ---
    "site_address":      SITE_CONFIG["address"],
    "catchment_radii_m": CATCHMENT_RADII_M,
    "peer_postcodes":    SITE_CONFIG["peer_postcodes"],
    "n_gp_fte":          SITE_CONFIG["n_gp_fte"],
    "n_allied_fte":      SITE_CONFIG["n_allied_fte"],
    "floor_area_sqm":    SITE_CONFIG["floor_area_sqm"],

    # --- Demand, revenue, costs, ramp (unchanged from v1.0) ---
    "bulk_bill_share":   0.70,
    "std_rebate":        43.90,
    # ... (all v1.0 constants preserved) ...
}
```

**Key detail:** SITE_CONFIG values are injected into BASE_ASSUMPTIONS at definition time. Downstream cells continue to read `BASE_ASSUMPTIONS["n_gp_fte"]` — they don't know or care that it came from SITE_CONFIG. This means **zero changes to §2–§7 consumer code** for the FTE/floor_area parameterisation.

### Pattern 7: Point-in-Polygon POA/SA3 Derivation (NEW — v2.0)

**What:** After geocoding, load ASGS boundary shapefiles (POA + SA1), do a point-in-polygon query with the geocoded point, and extract the containing POA code and SA3 code. This replaces v1.0's hardcoded POA 3067 and SA3 20607.

**When to use:** Whenever the site address is user-supplied and the ABS fetch region must be derived, not hardcoded.

**Trade-offs:** + Authoritative (the polygon says what region the point is in, regardless of what postcode the user typed). + SA1 shapefile already includes `SA3_CODE21` / `SA3_NAME21` as attributes — no separate SA3 shapefile needed. − Requires loading shapefiles before ABS fetch (currently they're loaded in §2). Mitigation: load boundaries in §1.3, reuse in §2.

**Why point-in-polygon over reverse-geocoding postcode from address string:**
- The user-supplied postcode in SITE_CONFIG is a hint, not ground truth. A user might enter "3000" (Melbourne CBD) for an address that's actually in postcode 3000's fringe.
- The POA shapefile is the authoritative ABS boundary. Point-in-polygon gives the correct POA code for census fetch.
- SA3 cannot be reverse-geocoded from an address string at all — SA3 is an ABS statistical geography, not a postal geography. Point-in-polygon is the only option.

**Example:**
```python
# §1.3 — Derive POA + SA3 from geocoded point (v2.0 multi-site)
# Loads ASGS boundaries (reused by §2 catchment), does point-in-polygon.
import geopandas as gpd
from shapely.geometry import Point

# Load POA + SA1 boundaries (VIC only, EPSG:7855 for metric area math later)
# Prefer VIC-only GeoPackages (pre-filtered — 68-74% smaller upload for Colab).
# Fall back to full national ZIPs + filter if GPKG not found (backward compat).
POA_PATH = PROJECT_ROOT / "data" / "local" / BASE_ASSUMPTIONS["poa_shapefile"]
SA1_PATH = PROJECT_ROOT / "data" / "local" / BASE_ASSUMPTIONS["sa1_shapefile"]

if POA_PATH.exists():
    poa = gpd.read_file(POA_PATH).to_crs("EPSG:7855")  # already VIC-only GPKG
else:
    poa = gpd.read_file("data/local/POA_2021_AUST_GDA2020_SHP.zip")
    poa = poa[poa["POA_CODE21"].str.startswith("3")].to_crs("EPSG:7855")  # VIC postcodes 3000-3999

if SA1_PATH.exists():
    sa1 = gpd.read_file(SA1_PATH).to_crs("EPSG:7855")  # already VIC-only GPKG
else:
    sa1 = gpd.read_file("data/local/SA1_2021_AUST_GDA2020.zip")
    sa1 = sa1[sa1["STE_NAME21"] == "Victoria"].to_crs("EPSG:7855")

# Point-in-polygon: which POA contains the geocoded site?
site_point = gpd.GeoDataFrame(
    [{"geometry": Point(site_lon, site_lat)}],
    crs="EPSG:4326",
).to_crs("EPSG:7855")

poa_hit = gpd.sjoin(site_point, poa, how="left", predicate="within")
site_poa_code = str(poa_hit.iloc[0].get("POA_CODE21", "")).zfill(4)
site_poa_name = poa_hit.iloc[0].get("POA_NAME21", "")

# Point-in-polygon: which SA1 → SA3 contains the geocoded site?
sa1_hit = gpd.sjoin(site_point, sa1, how="left", predicate="within")
site_sa3_code = str(sa1_hit.iloc[0].get("SA3_CODE21", ""))
site_sa3_name = sa1_hit.iloc[0].get("SA3_NAME21", "")

# ── GUARD: point outside VIC ──
if not site_poa_code or not site_sa3_code:
    raise RuntimeError(
        f"Geocoded point ({site_lat}, {site_lon}) falls outside VIC ASGS boundaries. "
        f"v2.0 is a VIC-only pilot. Check the address or use v2.1 for other states."
    )

# Deposit into report accumulator for §8
report["site_poa_code"] = site_poa_code
report["site_poa_name"] = site_poa_name
report["site_sa3_code"] = site_sa3_code
report["site_sa3_name"] = site_sa3_name

print(f"[§1.3] Site POA: {site_poa_code} ({site_poa_name})")
print(f"[§1.3] Site SA3: {site_sa3_code} ({site_sa3_name})")
```

**Guard: point outside VIC.** If `gpd.sjoin` returns no match (empty result), the geocoded point is outside Victoria. v2.0 is a VIC-only pilot — raise a clear `RuntimeError` with a message pointing to v2.1 for other states. This is a hard fail, not a warning, because all downstream ABS/MBS fetches would be wrong for a non-VIC site.

**Geometry reuse:** The `poa` and `sa1` GeoDataFrames loaded here are reused by §2 (catchment area apportionment). §2's cell 16 (which currently loads these) should be refactored to check if they're already loaded (`if "poa" not in globals(): ...`) or simply removed, with §1.3 becoming the single load point. The cleaner approach: §1.3 loads and §2 references the globals — but this creates an implicit dependency. The safest approach: §1.3 loads into globals, §2 asserts they exist (`assert "poa" in globals() and "sa1" in globals()`).

### Pattern 8: Slugified Report Filename (NEW — v2.0)

**What:** The report PDF/HTML filename is derived from the site address via slugification, with special-character handling and length limits.

**When to use:** Whenever the report output must be named after an arbitrary user-supplied address.

**Trade-offs:** + Each site gets a distinct, human-readable filename. − Must handle edge cases (special chars, very long addresses, non-ASCII).

**Example:**
```python
# §8 — Derive safe filename from site address (v2.0 multi-site)
import re

def slugify(address: str, max_len: int = 60) -> str:
    """Convert an address to a filesystem-safe slug."""
    # Take the street part before the first comma (usually "292-296 Johnston St")
    street_part = address.split(",")[0].strip()
    # Lowercase, replace non-alphanumeric with hyphens, collapse repeats
    slug = re.sub(r"[^a-z0-9]+", "-", street_part.lower()).strip("-")
    # Truncate to max_len (don't cut mid-word)
    if len(slug) > max_len:
        slug = slug[:max_len].rsplit("-", 1)[0]
    return slug or "site"

site_slug = slugify(SITE_CONFIG["address"])
# "292-296 Johnston St, Abbotsford VIC 3067" → "292-296-johnston-st"

pdf_path = OUTPUTS / f"{site_slug}_Feasibility_Report.pdf"
html_path = OUTPUTS / f"{site_slug}_Feasibility_Report.html"
```

**Edge cases handled:**
- Special characters (`/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`) → replaced with hyphens
- Very long addresses → truncated at `max_len` without cutting mid-word
- Empty/whitespace-only → falls back to `"site"`
- Non-ASCII (unlikely for VIC addresses, but possible) → `re.sub` strips to `[a-z0-9-]`

---

## Data Flow

### v2.0 Pipeline Flow (changes from v1.0 in **bold**)

```
§0.3 SITE_CONFIG ──┬──────────────────────────────────────────────────┐
                   │                                                   │
                   ▼                                                   │
§1.2 geocode ──► site_lat, site_lon                                    │
                   │                                                   │
                   ▼                                                   │
§1.3 **DERIVE POA + SA3** ──► site_poa_code, site_sa3_code             │
     (point-in-polygon on ASGS boundaries)                             │
                   │                                                   │
                   ├──► §1.4 **ABS fetch (parameterised)**             │
                   │     G01/G02/G04 for site_poa + peers + site_sa3   │
                   │                                                   │
                   ├──► §1.6 **MBS SA3 (parameterised)**               │
                   │     filter on site_sa3_code (not hardcoded 20607) │
                   │                                                   │
                   ▼                                                   │
§2 catchment (reuses §1.3 geometries) ──► buffers, apportionment       │
                   │                                                   │
                   ▼                                                   │
§3 demographics (conditional peers) ──► catchment profile, peer table  │
                   │                                                   │
§1.5 Places ──► §4 competitors                                         │
                   │                                                   │
                   └───────┬───────────┘                               │
                           ▼                                           │
                   §5 demand model                                     │
                           │                                           │
                           ▼                                           │
§0.3 BASE_ASSUMPTIONS ──────────────────► §6 clinic_pnl(a) ◄──────────┘
                           │
                           ▼
                   §7 scenarios (pharmacy synergy DELETED)
                           │
                           ▼
                   §8 report (site-parameterised template, slugified filename)
```

### Dependency Summary (v2.0 — new/modified marked)

| Section | Depends on | Produces | v2.0 Change |
|---------|-----------|----------|-------------|
| §0.3 | — | `SITE_CONFIG`, `BASE_ASSUMPTIONS`, paths | **MODIFIED** — SITE_CONFIG split |
| §1.2 geocode | §0.3 SITE_CONFIG | `site_lat, site_lon` | **MODIFIED** — reads SITE_CONFIG["address"] |
| §1.3 derive | §1.2, ASGS shapefiles | `site_poa_code, site_sa3_code`, loaded `poa`/`sa1` GeoDataFrames | **NEW** |
| §1.4 ABS | §1.3 (derived POA), §0.3 (peers) | census DataFrames per POA + SA3 | **MODIFIED** — parameterised codes |
| §1.5 Places | §1.2 (lat/lon) | raw place lists per (type, radius) | unchanged (already site-agnostic) |
| §1.6 MBS | §1.3 (derived SA3), §0.3 | SA3 consult rates by age band | **MODIFIED** — parameterised SA3 |
| §2 catchment | §1.2, §1.3 (geometries) | buffer GeoDataFrames, apportionment weights | **MODIFIED** — reuses §1.3 geometries |
| §3 demographics | §2, §1.4 | catchment pop/age by ring; peer table (conditional) | **MODIFIED** — conditional peers |
| §4 competitors | §1.5, §2 | classified competitor df, counts per ring | unchanged |
| §5 demand | §3, §4, §1.6 | annual consult demand, GP capacity, required share | unchanged |
| §6 financial | §0.3 (FTE from SITE_CONFIG), §5 | `clinic_pnl()`, base-case P&L | **MODIFIED** — FTE/floor_area from SITE_CONFIG |
| §7 scenarios | §6 | scenario table, sensitivity charts | **MODIFIED** — pharmacy synergy deleted |
| §8 report | §2–§7, §0.3 (site name/address) | report.html, report.pdf (slugified) | **MODIFIED** — parameterised template + filename |

### Key Data Flows

1. **Site config flow (NEW):** `SITE_CONFIG["address"]` → §1.2 geocode → `site_lat/lon` → §1.3 point-in-polygon → `site_poa_code` + `site_sa3_code` → §1.4 ABS fetch + §1.6 MBS fetch. The derived codes are the parameterisation keys for all census/MBS data.
2. **Census flow (MODIFIED):** ABS API (G01/G02/G04) fetched for `site_poa_code` + user-supplied `peer_postcodes` (validated against ABS POA codelist) → cache → tidy DataFrames → §2 area weights → §3 catchment profile → §5 demand. If `peer_postcodes` is empty, peer table section is skipped entirely.
3. **MBS flow (MODIFIED):** MBS SA3 xlsx filtered on `site_sa3_code` (derived, not hardcoded 20607) → SA3 consult rates by age band → §5 demand model. State fallback warning fires if the derived SA3 is not found in the file.
4. **Competitor flow (unchanged):** site coords → Places nearby (per type × radius) → cache → dedupe → classify → per-ring counts → §5 capacity + §4 map.
5. **Assumption flow (unchanged):** `BASE_ASSUMPTIONS` (§0.3) is the only source of financial constants. SITE_CONFIG values are injected at definition time. §7 mutates only via override dicts.
6. **Report flow (MODIFIED):** every section appends to `report{}`; §8 renders from `report{}` + `SITE_CONFIG` (for site name/address in template) + `slugify(SITE_CONFIG["address"])` (for filename).

---

## Component-by-Component Integration Analysis

### 1. Site-Config Form: Where Does It Sit?

**v1.0:** Cell 5 (§0.3) contains `SITE_ADDRESS`, `CATCHMENT_RADII_M`, `PEER_POSTCODES` as module-level variables at the top, followed by `BASE_ASSUMPTIONS` dict.

**v2.0:** Same cell (§0.3), restructured. `SITE_CONFIG` dict replaces the three module-level variables. `BASE_ASSUMPTIONS` follows, with SITE_CONFIG values injected. This preserves:
- The single-params-cell pattern (PIPE-05) — validator's `first_def_cell("BASE_ASSUMPTIONS")` still works
- The `{**BASE_ASSUMPTIONS, **overrides}` scenario pattern — unchanged
- Top-to-bottom flow — SITE_CONFIG defined before BASE_ASSUMPTIONS

**Why not a new §0.5 cell?** A separate cell would break the "single params cell" invariant and require validator changes. Keeping it in §0.3 with clear visual separation (comment headers) is cleaner and lower-risk.

### 2. Site Config Flow Through the Notebook

**Strategy: single SITE_CONFIG dict, values injected into BASE_ASSUMPTIONS at definition time.**

This mirrors the BASE_ASSUMPTIONS pattern exactly. Downstream cells read `BASE_ASSUMPTIONS["n_gp_fte"]` — they don't know it came from SITE_CONFIG. The only cells that read SITE_CONFIG directly are:
- §1.2 geocode: `SITE_CONFIG["address"]`
- §8 report template: `SITE_CONFIG["address"]` for the report header, `slugify(SITE_CONFIG["address"])` for the filename

Everything else flows through BASE_ASSUMPTIONS as before. This minimises downstream changes.

**Alternative considered (per-cell parameter extraction):** Each cell reads SITE_CONFIG directly. Rejected — it would require touching every consumer cell and break the "downstream reads BASE_ASSUMPTIONS only" invariant.

### 3. SA3 Derivation: Pipeline Position + Guard

**Position:** New §1.3 cell, after geocode (§1.2, cell 13) and before ABS fetch (§1.4, cell 28). The derivation needs:
- Input: `site_lat`, `site_lon` (from §1.2)
- Assets: POA shapefile + SA1 shapefile (from `data/local/`)
- Output: `site_poa_code`, `site_sa3_code`, plus loaded `poa`/`sa1` GeoDataFrames for §2 reuse

**Why SA1 shapefile for SA3 (not a separate SA3 shapefile):** The SA1 shapefile (already on hand, 100MB) includes `SA3_CODE21` and `SA3_NAME21` as attribute columns (verified live: `sa1.columns` includes both). A single point-in-polygon on SA1s gives the SA3 code. No additional download needed. The SA3 correspondence xlsx (`SA3_2021_AUST.xlsx`) is a lookup table, not boundaries — insufficient for point-in-polygon.

**Guard: point outside VIC.** If `gpd.sjoin(site_point, poa, how="left", predicate="within")` returns an empty match (NaN in joined columns), the geocoded point is outside Victoria. v2.0 is VIC-only — raise `RuntimeError` with a clear message. This is a hard fail because:
- EPSG:7855 (MGA zone 55) is only valid for VIC (zone 55 covers VIC + parts of NSW/QLD, but the pilot scope is VIC)
- ABS fetch would return wrong/empty data for a non-VIC POA
- MBS SA3 filter would fail silently

**Geometry reuse with §2:** §1.3 loads `poa` and `sa1` into globals. §2 (cell 16) currently loads these independently. Refactor §2 to assert they exist rather than reload:
```python
# §2 — assert geometries loaded by §1.3 (v2.0 reuse)
assert "poa" in globals() and "sa1" in globals(), "§1.3 must run first (loads ASGS boundaries)"
```
This avoids double-loading 100MB+ shapefiles and enforces the §1.3 → §2 dependency.

### 4. Parameterised ABS Fetch: The Cleanest Refactor

**v1.0 (cell 28):** `PEER_POA_CODES = "+".join(PEER_POSTCODES)` — hardcodes 3067 + 9 peers. The site POA (3067) is included in PEER_POSTCODES. Fetches G01/G02 for all of them in one SDMX query.

**v2.0 refactor:** Replace `PEER_POSTCODES` (module-level, hardcoded) with a derived list:
```python
# §1.4 — Build POA list from derived site POA + user-supplied peers (v2.0)
all_poa_codes = [site_poa_code] + SITE_CONFIG["peer_postcodes"]
# Dedupe (site POA might also be in peer list)
all_poa_codes = list(dict.fromkeys(all_poa_codes))  # preserve order, dedupe
# Validate against ABS POA codelist (optional — the API will 404 invalid codes anyway)
PEER_POA_CODES = "+".join(all_poa_codes)
```

The fetch functions (`fetch_g01_poa`, `fetch_g02_poa`, `fetch_g04_poa`) are **unchanged** — they already take `PEER_POA_CODES` as a module-level variable and build the SDMX data key from it. The only change is how `PEER_POA_CODES` is constructed.

**G04 (age by sex):** Cell 29 fetches G04. Same parameterisation — it uses the same `PEER_POA_CODES` variable. No additional changes.

**SA3 fetch (if needed):** v1.0 doesn't fetch census data at SA3 level (MBS SA3 data comes from a local xlsx, not the ABS API). If v2.0 needs SA3-level census (e.g., for cross-checking), the data key would use `site_sa3_code` instead of POA codes. But this is not required for the core pipeline — SA3 is only used for MBS utilisation (§1.6).

**GCP fallback removal:** v1.0's GCP fallback (`parse_gcp_g01_to_tidy`, `GCP_POA3067.xlsx`) is Abbotsford-specific. PROJECT.md explicitly scopes this out: "Manual ABS file download path — out of scope for v2.0." The fallback functions should be kept but modified to emit a generic warning (not Abbotsford-specific) or removed entirely. Recommendation: **keep the fallback function signature but remove the Abbotsford-specific xlsx reference** — the fallback becomes "empty schema + warning" for any site where the API fails.

### 5. Peer Postcode Handling

**v1.0:** `PEER_POSTCODES` is a hardcoded list of 10 postcodes. The peer table (§3.5, cell 34) and peer comparison charts (§3.6, cell 36) always render.

**v2.0:**
1. User supplies `peer_postcodes` in SITE_CONFIG (can be empty list).
2. §1.4 builds `all_poa_codes = [site_poa_code] + peer_postcodes`, deduped.
3. ABS fetch validates each peer postcode against the POA shapefile's `POA_CODE21` codelist. Invalid postcodes are dropped with a warning.
4. §3.5 peer table: if `peer_postcodes` is empty, skip the peer table cell entirely (guard with `if SITE_CONFIG["peer_postcodes"]:`).
5. §3.6 peer charts: same guard.
6. §4.6 peer competitor table (cell 54): same guard — skip if no peers.

**Validation approach:** Rather than calling the ABS dataflow endpoint to validate each postcode (slow, rate-limited), validate against the already-loaded POA GeoDataFrame:
```python
valid_poa_codes = set(poa["POA_CODE21"].astype(str).str.zfill(4))
validated_peers = [p for p in SITE_CONFIG["peer_postcodes"]
                   if p.zfill(4) in valid_poa_codes]
invalid_peers = set(SITE_CONFIG["peer_postcodes"]) - set(validated_peers)
if invalid_peers:
    print(f"⚠ Dropped invalid peer postcodes (not in VIC ASGS): {invalid_peers}")
```

### 6. Pharmacy Synergy Removal: What to Delete, What to Keep

**Delete:**
- Cell 81 (§7.6 markdown header + explanation)
- Cell 82 (§7.6 pharmacy synergy code — `pharmacy_synergy` dict, capture rates, print block)
- §8 report template section "6. Pharmacy Synergy — Secondary Upside" (in cell 87's Jinja2 template string)
- `report["pharmacy_synergy_range"]` deposit (in cell 82)

**Keep (no changes needed):**
- Cell 85 (§8.1 verdict logic) — already 100% standalone, never mentions pharmacy (D-04). The verdict gate (EBITDA > 0 AND margin > 15%) is unchanged.
- Cell 83 (§7.7 Interpretation) — becomes the tail of §7 (may renumber to §7.6 or just stay as-is)
- All §7.1–§7.5 cells (scenarios, tornado, billing-mix) — unchanged

**Verdict cell impact:** None. The verdict was already standalone-first in v1.0. The pharmacy synergy was explicitly "NOT Load-Bearing" (FIN-07) and order-gated after the verdict. Removing it makes the verdict cleaner — no more "secondary upside" section to confuse the narrative.

**Report template impact:** Cell 87's Jinja2 template has a `<h2>6. Pharmacy Synergy</h2>` section. Delete that section from the template string. The section numbering of subsequent sections (7. Assumptions Register, 8. Citations) may shift down by one, or the pharmacy section number is simply removed and subsequent sections keep their numbers (cleaner — avoids renumbering).

### 7. Report Naming + Output Path

**v1.0 (cell 88):** `pdf_path = OUTPUTS / "Johnston_St_v2_Executive_Report.pdf"` — hardcoded.
**v1.0 (cell 87):** `html_path = OUTPUTS / "Johnston_St_v2_Executive_Report.html"` — hardcoded.
**v1.0 (cell 87 template):** `<h1>Johnston St Medical Clinic</h1>`, `<h2>292-296 Johnston St, Abbotsford VIC 3067</h2>` — hardcoded.

**v2.0:**
- Filename: `slugify(SITE_CONFIG["address"])` → e.g., `"292-296-johnston-st_Feasibility_Report.pdf"` (see Pattern 8)
- Template header: `{{ report["site_address"] }}` instead of hardcoded address
- Template title: derive a short site name from the address (street name only) or use a SITE_CONFIG["site_name"] field (optional)

**Template parameterisation:** The Jinja2 template (cell 87) needs these hardcoded strings replaced with template variables:
- `"Johnston St Medical Clinic"` → `{{ report["site_name"] }}` (derived from address street part, or a SITE_CONFIG field)
- `"292-296 Johnston St, Abbotsford VIC 3067"` → `{{ report["site_address"] }}`
- `"The site at 292-296 Johnston St, Abbotsford is geocoded..."` → `"The site at {{ report['site_address'] }} is geocoded..."`

These values are deposited into `report{}` by §1.2/§1.3:
```python
# §1.2 — deposit site info for §8 report
report["site_address"] = SITE_CONFIG["address"]
report["site_name"] = SITE_CONFIG["address"].split(",")[0]  # "292-296 Johnston St"
report["site_slug"] = slugify(SITE_CONFIG["address"])
```

### 8. Validator Updates: Multi-Site Adaptation

**v1.0 validator (`scripts/validate_v2_notebook.py`):** 36 checks, some hardcoded to Abbotsford:
- `GEO-04`: checks for "Yarra" in source (cell 42 references SA3 20607 Yarra)
- `DEMO-01`: checks for "GCP_POA3067" in source (fallback file reference)
- Various checks look for `PEER_POSTCODES`, `BASE_ASSUMPTIONS`, `{**BASE_ASSUMPTIONS, **overrides}`

**v2.0 strategy: parameterise the validator with a site fixture.**

The validator should accept a `--site-config` argument (or read a fixture file) that specifies the expected site values. Default fixture = Abbotsford (reproduces v1.0 behaviour). The validator then checks:
- Structural checks (json.load, nbformat, execution_count, source format) — **site-agnostic, unchanged**
- Flow checks (PIPE-01 top-to-bottom, PIPE-02 dual-env, PIPE-05 single params cell) — **site-agnostic, unchanged**
- Content checks that look for specific strings ("Yarra", "GCP_POA3067") — **parameterised**: check for the fixture's expected SA3 name and POA code instead
- New v2.0 checks: SITE_CONFIG dict present, slugify function present, §1.3 derive cell present, pharmacy synergy section absent, report filename uses slug

**Implementation approach:**
```python
# scripts/validate_v2_notebook.py — v2.0 parameterisation
SITE_FIXTURE = {
    "address": "292-296 Johnston St, Abbotsford VIC 3067",
    "poa_code": "3067",
    "sa3_code": "20607",
    "sa3_name": "Yarra",
    "slug": "292-296-johnston-st",
}
# Checks use SITE_FIXTURE["sa3_name"] instead of hardcoded "Yarra"
```

**Alternative: separate v2.0 validator.** Rejected — it would duplicate 30+ structural/flow checks that are site-agnostic. Better to parameterise the existing validator and add v2.0-specific checks as new sections.

**New v2.0 validator checks (estimated 6–8 new checks):**
1. `SITE_CONFIG` dict defined in §0.3 (before BASE_ASSUMPTIONS)
2. `slugify` function defined (in §8 or a utility cell)
3. §1.3 derive cell present (point-in-polygon, `site_poa_code`, `site_sa3_code`)
4. No hardcoded "3067" or "20607" in §1.4/§1.6 (replaced by derived variables)
5. Pharmacy synergy section absent (no "§7.6 Pharmacy" marker, no `pharmacy_synergy` variable)
6. Report filename uses `slugify` or `site_slug` (not hardcoded "Johnston_St")
7. Report template uses `{{ report['site_address'] }}` (not hardcoded address)
8. VIC guard present in §1.3 (RuntimeError on point outside VIC)

### 9. Generator Scripts: Coexistence Strategy

**v1.0 generators (5 scripts):**
1. `create_v2_notebook.py` — builds §0–§1.1 (skeleton)
2. `extend_v2_notebook.py` — appends §1.2 geocode + §2 catchment
3. `extend_v2_notebook_demographics.py` — appends §3 demographics
4. `extend_v2_notebook_phase3.py` — appends §1.4 Places + §1.5 MBS + §4 competitors + §5 demand
5. `extend_v2_notebook_phase4.py` — appends §6 financial model
6. `extend_v2_notebook_phase5.py` — appends §7 scenarios + §8 report

(That's actually 6 scripts — create + 5 extend.)

**Idempotency pattern:** Each extend script finds its section marker (e.g., `"# §1.2 Geocode Site"`), removes existing cells from that marker to the next section marker, and re-appends corrected cells. Re-running produces byte-identical output.

**v2.0 strategy: new generators for modified phases, following the same pattern.**

The v2.0 changes touch §0.3, §1.2, §1.3 (new), §1.4, §1.6, §2, §3, §6, §7, §8. Rather than one mega-generator, follow the v1.0 pattern of one generator per phase:

| v2.0 Generator | Phase | What it modifies | Idempotency marker |
|----------------|-------|------------------|--------------------|
| `extend_v2_notebook_phase6.py` | Phase 6 | §0.3 restructure (SITE_CONFIG split) | `"SITE_CONFIG"` or `"# §0.3"` |
| `extend_v2_notebook_phase7.py` | Phase 7 | §1.2 geocode + §1.3 derive (NEW cell) | `"# §1.2 Geocode"` / `"# §1.3 Derive"` |
| `extend_v2_notebook_phase8.py` | Phase 8 | §1.4 ABS fetch + §1.6 MBS parameterisation | `"# §3 Demographics"` (replaces §3 block) |
| `extend_v2_notebook_phase9.py` | Phase 9 | §7.6 deletion + §8 report parameterisation | `"# §7 Scenarios"` / `"# §8 Executive"` |

**Coexistence with v1.0 generators:** The v1.0 generators remain as-is (they produce the v1.0 notebook). The v2.0 generators load the current notebook state and apply their modifications. Running v1.0 generators first, then v2.0 generators, produces the v2.0 notebook. This preserves the "byte-stable output" property — the full generator chain is deterministic.

**Critical ordering:** v2.0 generators must run AFTER v1.0 generators (they modify v1.0 output). The build chain is:
```
create_v2_notebook.py → extend_phase2..5.py → extend_phase6..9.py
```

**§0.3 restructure challenge:** The §0.3 cell (cell 5) is built by `create_v2_notebook.py`. The v2.0 phase 6 generator needs to replace its contents. This is a cell-content replacement (not a section append), which is a different idempotency pattern. The generator should:
1. Find the cell containing `BASE_ASSUMPTIONS = {`
2. Replace its entire source with the new SITE_CONFIG + BASE_ASSUMPTIONS content
3. This is the same pattern used by `extend_v2_notebook_phase4.py`'s `extend_base_assumptions()` function (which modifies the BASE_ASSUMPTIONS cell in-place)

---

## Suggested Build Order

The build order respects the dependency chain: site-config → geocode → derive POA/SA3 → ABS fetch → catchment → demand → competitors → financial model → scenarios → report.

### Phase 6: Site Config Restructure (§0.3)

**What:** Split §0.3 into SITE_CONFIG + BASE_ASSUMPTIONS. Inject SITE_CONFIG values into BASE_ASSUMPTIONS.
**Dependencies:** None (modifies only §0.3).
**Verification:** Validator check for SITE_CONFIG dict; `Restart & Run All` still passes (downstream cells read BASE_ASSUMPTIONS, which is unchanged in shape).
**Generator:** `extend_v2_notebook_phase6.py`
**Risk:** LOW — additive change to one cell; downstream consumers unaffected because BASE_ASSUMPTIONS shape is preserved.

### Phase 7: Geocode Parameterisation + POA/SA3 Derivation (§1.2, §1.3 NEW)

**What:** Modify §1.2 to read `SITE_CONFIG["address"]`. Add §1.3 cell: load ASGS boundaries, point-in-polygon, derive `site_poa_code` + `site_sa3_code`, VIC guard. Refactor §2 to reuse §1.3 geometries.
**Dependencies:** Phase 6 (SITE_CONFIG must exist).
**Verification:** Derive POA 3067 + SA3 20607 for default Abbotsford config (matches v1.0). VIC guard fires for a non-VIC test point.
**Generator:** `extend_v2_notebook_phase7.py`
**Risk:** MEDIUM — new cell insertion shifts cell indices; §2 geometry reuse requires refactoring cell 16. SA1 shapefile is 100MB — loading in §1.3 instead of §2 doesn't change memory but changes execution order.

### Phase 8: ABS + MBS Parameterisation (§1.4, §1.6, §3)

**What:** Replace hardcoded `PEER_POSTCODES` with derived `all_poa_codes`. Parameterise MBS SA3 filter to use `site_sa3_code`. Add peer postcode validation. Add conditional peer table/charts (skip if empty). Remove Abbotsford-specific GCP fallback references.
**Dependencies:** Phase 7 (derived POA/SA3 codes must exist).
**Verification:** Default config fetches same data as v1.0 (POA 3067 + 9 peers, SA3 20607). Empty peer list skips peer table. Invalid peer postcodes dropped with warning.
**Generator:** `extend_v2_notebook_phase8.py`
**Risk:** MEDIUM — ABS fetch functions are unchanged (they already take PEER_POA_CODES); the change is in how PEER_POA_CODES is constructed. MBS filter change is a one-line replacement (`"20607"` → `site_sa3_code`).

### Phase 9: Pharmacy Synergy Removal + Report Parameterisation (§7, §8)

**What:** Delete §7.6 cells (81–82). Remove pharmacy section from §8 Jinja2 template. Parameterise report template (site name/address from `report{}`). Add `slugify()` function. Parameterise PDF/HTML filenames.
**Dependencies:** Phases 6–8 (SITE_CONFIG, derived codes, report accumulator values must exist).
**Verification:** No "pharmacy" references in notebook source. Report filename uses slug. Template renders site address dynamically. Default config produces `292-296-johnston-st_Feasibility_Report.pdf`.
**Generator:** `extend_v2_notebook_phase9.py`
**Risk:** LOW — deletions are safe (pharmacy was non-load-bearing). Template parameterisation is string replacement in the Jinja2 template.

### Phase 10: Validator Update + Hardening

**What:** Parameterise validator with site fixture. Add 6–8 new v2.0 checks. Run full generator chain (v1.0 + v2.0) to verify byte-stable output. Keyless run from cache. Fresh-clone Colab run.
**Dependencies:** Phases 6–9 (all v2.0 features must be in place).
**Verification:** All v2.0 validator checks pass. Generator chain produces byte-identical notebook on re-run.
**Risk:** LOW — validator-only changes; no notebook cell changes.

### Parallelisable Pairs

- Phase 6 (§0.3 restructure) ∥ Phase 9 slugify function draft (no dependencies on each other)
- Phase 8 ABS parameterisation ∥ Phase 9 pharmacy deletion (independent sections)

### Critical Path

```
Phase 6 (SITE_CONFIG) → Phase 7 (derive POA/SA3) → Phase 8 (parameterise ABS/MBS) → Phase 10 (validator)
                                                                                    ↑
                                              Phase 9 (pharmacy delete + report param) ─┘
```

---

## Scaling Considerations

Scaling here means analysis scope, not users.

| Scale | Architecture Adjustments |
|-------|--------------------------|
| v2.0 (1 site per run, VIC only, user-supplied peers) | Single notebook, SITE_CONFIG + derived POA/SA3. All patterns above. |
| v2.1 (batch/multi-site comparison) | Loop over SITE_CONFIG list; `report{}` becomes `reports[site_slug]`; per-site cache files (already keyed by derived codes). Generator scripts parameterised with `--site-list`. |
| v2.1 (non-VIC sites) | MGA zone-aware reprojection (zones 49–56); VIC guard becomes state guard; SA3 derivation works for any state (SA1 shapefile is national). |
| Ongoing/refreshable product | Move to scripts + papermill parameterised runs; SQLite cache instead of JSON; SA1-level ABS geometry for finer apportionment. |

### Scaling Priorities

1. **First bottleneck (v2.0):** ASGS shapefile load time (100MB SA1 + 56MB POA) — loaded once in §1.3, reused in §2. Acceptable for single-run; for batch mode (v2.1), load once and loop.
2. **Second bottleneck (v2.1):** Cache file proliferation — each site produces ~15 cache files (geocode + ABS + Places). Mitigated by slug/keyed naming; for batch mode, consider SQLite cache.

---

## Anti-Patterns

### Anti-Pattern 1: Hardcoded Site Constants in Downstream Cells

**What people do:** Leave `"3067"` or `"20607"` literals in §1.4/§1.6 cells "just for now."
**Why it's wrong:** The whole point of v2.0 is multi-site. Any hardcoded site constant is a bug that silently produces wrong data for non-Abbotsford sites.
**Do this instead:** All site-specific values flow through `site_poa_code` / `site_sa3_code` (derived in §1.3) or `SITE_CONFIG` (user-supplied in §0.3). Validator check: no hardcoded `"3067"` or `"20607"` in §1.4+ cells.

### Anti-Pattern 2: Trusting User-Supplied Postcode Over Point-in-Polygon

**What people do:** Use `SITE_CONFIG["postcode"]` directly for ABS fetch instead of deriving POA from the geocoded point.
**Why it's wrong:** Users make typos. A user might enter "3000" for an address in postcode 3067. The ABS fetch would return wrong census data.
**Do this instead:** Always derive `site_poa_code` via point-in-polygon on the POA shapefile (§1.3). Use `SITE_CONFIG["postcode"]` only as a sanity-check hint (warn if it doesn't match the derived POA).

### Anti-Pattern 3: Reloading Shapefiles in §2 After §1.3 Already Loaded Them

**What people do:** §1.3 loads POA/SA1 for derivation; §2 loads them again independently.
**Why it's wrong:** Doubles memory usage and load time for 150MB+ of shapefiles.
**Do this instead:** §1.3 loads into globals; §2 asserts they exist (`assert "poa" in globals()`). Single load point.

### Anti-Pattern 4: Leaving Pharmacy Synergy References in the Report Template

**What people do:** Delete the §7.6 code cells but forget the Jinja2 template section in cell 87.
**Why it's wrong:** The report renders an empty "Pharmacy Synergy" section with missing data, breaking the investor narrative.
**Do this instead:** Validator check: no "pharmacy" or "Pharmacy Synergy" string in the §8 template cell. Delete the template section in the same phase as the code deletion.

### Anti-Pattern 5: Non-Slugified Filenames with Special Characters

**What people do:** Use `SITE_CONFIG["address"]` directly in the filename: `outputs/292-296 Johnston St, Abbotsford VIC 3067_Feasibility_Report.pdf`.
**Why it's wrong:** Commas, spaces, and slashes break filesystem paths and shell commands.
**Do this instead:** `slugify()` with special-character stripping and length limits (Pattern 8).

---

## Integration Points

### External Services

| Service | Integration Pattern | v2.0 Notes |
|---------|---------------------|------------|
| ABS Data API | REST/SDMX CSV, via CachedSession | **Parameterised** — data key uses derived POA/SA3 codes, not hardcoded. Cache files keyed by derived codes (automatic). |
| Google Geocoding API | Single GET per address, cached | **Parameterised** — reads SITE_CONFIG["address"]. Cache key = slugified address (already site-specific in v1.0). |
| Google Places Nearby Search | POST per (type, lat, lon, radius), cached | Unchanged — already uses geocoded lat/lon (site-agnostic since v1.0). |
| MBS SA3 xlsx (local file) | pandas read_excel, filter on SA3 code | **Parameterised** — filters on `site_sa3_code` instead of hardcoded "20607". |
| weasyprint | §8 only, Colab-only PDF | **Parameterised** — output filename uses slugify(site_address). |

### Internal Boundaries

| Boundary | Communication | v2.0 Notes |
|----------|---------------|------------|
| §0.3 SITE_CONFIG ↔ §1.2 geocode | `SITE_CONFIG["address"]` string | New boundary — user input enters the pipeline here |
| §1.2 geocode ↔ §1.3 derive | `site_lat`, `site_lon` globals | New boundary — geocoded point feeds point-in-polygon |
| §1.3 derive ↔ §1.4 ABS fetch | `site_poa_code`, `site_sa3_code` globals | New boundary — derived codes parameterise ABS/MBS fetch |
| §1.3 derive ↔ §2 catchment | `poa`, `sa1` GeoDataFrame globals | **Modified** — §2 reuses §1.3 loaded geometries (was independent load in v1.0) |
| §0.3 BASE_ASSUMPTIONS ↔ §6-§7 model | Single dict → pure `clinic_pnl()` | Unchanged — SITE_CONFIG values injected at definition time |
| §2-§7 ↔ §8 report | `report{}` accumulator + saved figures | **Modified** — `report["site_address"]`, `report["site_slug"]` added by §1.2/§1.3 |
| Colab ↔ Windows | `PROJECT_ROOT` + `pathlib` | Unchanged |

---

## Sources

- v1.0 notebook audit: `Johnston_St_v2.ipynb` (88 cells, cell-by-cell inspection of cells 5, 13, 16, 28, 42, 81–82, 85, 87–88)
- v1.0 architecture: prior `.planning/research/ARCHITECTURE.md` (Patterns 1–5, data flow, build order)
- v1.0 validator: `scripts/validate_v2_notebook.py` (36 checks, hardcoded Abbotsford references at lines 275, 278, 303, 307)
- v1.0 generators: `scripts/create_v2_notebook.py` + 5 `extend_v2_notebook_*.py` (idempotent cell-replacement pattern)
- SA1 shapefile attributes: verified live — `SA1_2021_AUST_SHP_GDA2020.zip` includes `SA3_CODE21`, `SA3_NAME21`, `SA2_CODE21`, `SA2_NAME21` columns (15,482 VIC SA1s)
- Project context: `.planning/PROJECT.md` (v2.0 target features, key decisions, out-of-scope items)
- Milestone history: `.planning/MILESTONES.md` (v1.0 accomplishments, 36/36 validator checks)

---
*Architecture research for: v2.0 multi-site feasibility tool (VIC pilot) — integration with v1.0 notebook architecture*
*Researched: 2026-07-07*
