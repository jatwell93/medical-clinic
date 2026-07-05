# Architecture Research

**Domain:** Reproducible geospatial/financial analytics notebook (Colab-first, dual-environment)
**Researched:** 2026-07-05
**Confidence:** HIGH (patterns are well-established for analytics notebooks; specifics verified against v1 prototype and PROJECT.md)

## Standard Architecture

### System Overview

The notebook is a **linear pipeline with a cached I/O boundary**. Every external fetch (ABS API, Google Places, geocoding) goes through a cache layer so re-runs are free and deterministic. Computation flows strictly downward — no section reads state produced by a later section (the v1 `s_lat`/`s_lon` used-before-definition bug is exactly this violation).

```
┌──────────────────────────────────────────────────────────────────┐
│ §0 SETUP & CONFIG (one cell each)                                │
│  ┌────────────┐ ┌──────────────┐ ┌───────────────────────────┐  │
│  │ pip installs│ │ env detect   │ │ PARAMS cell (site, radii, │  │
│  │ + imports   │ │ (Colab/local)│ │ financial assumptions)    │  │
│  └────────────┘ └──────┬───────┘ └─────────────┬─────────────┘  │
├────────────────────────┴───────────────────────┴─────────────────┤
│ §1 DATA ACQUISITION LAYER (all external I/O, all cached)         │
│  ┌──────────┐ ┌───────────┐ ┌────────────┐ ┌─────────────────┐  │
│  │ Geocoding│ │ ABS Data  │ │ Google     │ │ Local file       │  │
│  │ (Google) │ │ API (G01/ │ │ Places     │ │ fallbacks (GCP   │  │
│  │          │ │ G02, POA) │ │ (nearby)   │ │ zip, MBS xlsx)   │  │
│  └────┬─────┘ └─────┬─────┘ └─────┬──────┘ └──────┬──────────┘  │
│       └─────────────┴──── cached_fetch() ─────────┘             │
│                            │                                     │
│                     data/cache/*.json                            │
├──────────────────────────────────────────────────────────────────┤
│ §2 GEOSPATIAL CATCHMENT       §3 DEMOGRAPHICS                    │
│  site point → 1/3/5 km        POA census → area-apportioned      │
│  buffers (EPSG:7855)          catchment population & age bands   │
├──────────────────────────────────────────────────────────────────┤
│ §4 COMPETITORS                §5 DEMAND MODEL                    │
│  Places results → dedupe,     age-adjusted consult demand vs     │
│  classify, per-radius counts  GP capacity → required share       │
├──────────────────────────────────────────────────────────────────┤
│ §6 FINANCIAL MODEL            §7 SCENARIOS                       │
│  P&L function(params) →       base/opt/pess param dicts →        │
│  revenue, costs, breakeven    P&L per scenario, sensitivity      │
├──────────────────────────────────────────────────────────────────┤
│ §8 REPORT GENERATION                                             │
│  collected key metrics + maps → markdown assembly → PDF export   │
├──────────────────────────────────────────────────────────────────┤
│ STORES: data/cache/ (JSON)  data/local/ (ABS zips, MBS xlsx)     │
│         outputs/ (maps .html/.png, report .md/.pdf)              │
└──────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| §0 Setup | pip installs, imports, quiet warnings | One cell; `%pip install -q` guarded so local runs skip it |
| §0 Env/paths | Detect Colab vs Windows, resolve `PROJECT_ROOT`, load API keys | `try: from google.colab import userdata` / `except ImportError:` → `.env` via `python-dotenv`; `pathlib.Path` everywhere |
| §0 PARAMS | Every tunable input in one dict/dataclass with citation comments | `ASSUMPTIONS = {...}` cell — site address, radii `[1000, 3000, 5000]`, billing mix, fee levels, rent, fit-out capital |
| §1 Cache layer | `cached_fetch(key, fetch_fn)` — JSON on disk, deterministic keys | ~20-line helper; every API call goes through it |
| §1 ABS client | Pull G01/G02-equivalent for POA 3067 + peers via api.data.abs.gov.au; fallback to local GCP CSVs with warning | `requests` + SDMX-JSON parse → tidy DataFrame |
| §1 Places client | Nearby search with pagination, per (lat,lon,radius,type) caching | v1's `google_nearby_places` + cache wrapper + 2s page-token sleep |
| §1 MBS loader | SA3 20604 utilisation; fallback to state benchmark with printed warning | Read xlsx/CSV, filter SA3, emit consults-per-capita by age band |
| §2 Catchment | Geocode exact address; buffers in metres (EPSG:7855); area-apportion POA populations into each ring | `gpd.overlay` intersection → `pop × (intersect_area / poa_area)` — fixes v1 whole-postcode summing |
| §3 Demographics | Catchment population, age structure, income; peer-postcode comparison table | DataFrame keyed by radius; merge ABS data with apportionment weights |
| §4 Competitors | Dedupe by place_id across types/radii, classify (corporate GP / independent / pharmacy / allied), per-ring counts, folium map | Pure pandas on cached Places JSON |
| §5 Demand model | Age-band consult rates × catchment age profile → annual consult demand; vs GP FTE capacity → market share required | Transparent arithmetic, no ML (v1's 3-row Random Forest is explicitly replaced) |
| §6 Financial model | `clinic_pnl(params) -> dict` — revenue, cost lines, EBIT, fit-out, months-to-breakeven | Pure function of a params dict; zero globals |
| §7 Scenarios | Base/optimistic/pessimistic param overrides; one-way sensitivity table (rent, bulk-bill %, consults/GP/day) | `{**BASE, **overrides}` per scenario → call `clinic_pnl` |
| §8 Report | Assemble markdown from a `report_metrics` dict collected throughout; render PDF | f-string markdown template → `md → HTML → PDF` (weasyprint or pandoc/wkhtmltopdf; Colab: `!pip install weasyprint`) |

## Recommended Project Structure

The deliverable is a single notebook, so "structure" = repo layout + notebook section layout.

```
medical-clinic/
├── Johnston_St_v2.ipynb      # the deliverable notebook
├── Johnston_St_v1.ipynb      # frozen reference (untouched)
├── johnston_st_v1.py         # frozen reference
├── .env                      # GOOGLE_PLACES_KEY=... (gitignored)
├── .env.example              # documented key names, no values
├── .gitignore                # .env, data/cache/, outputs/, *.pyc
├── data/
│   ├── cache/                # JSON API caches (committed optionally — makes runs reproducible without keys)
│   │   ├── geocode_292-296-johnston-st....json
│   │   ├── abs_G01_POA3067.json
│   │   └── places_doctor_-37.799_145.003_3000.json
│   └── local/                # fallback assets (GCP POA zip, POA shapefile, MBS xlsx, cohealth PDF)
├── outputs/
│   ├── maps/                 # folium .html + static .png exports
│   ├── report.md             # assembled markdown
│   └── Johnston_St_Feasibility.pdf
└── .planning/                # GSD planning docs
```

Notebook section layout (each numbered section = markdown header cell + teaching commentary + code cells):

```
§0  Setup & Configuration
    0.1 Installs & imports        0.2 Environment/paths/keys      0.3 PARAMETERS & ASSUMPTIONS
§1  Data Acquisition & Caching
    1.1 cache helper              1.2 geocode site                1.3 ABS census (API + fallback)
    1.4 Google Places fetches     1.5 MBS SA3 data (+ fallback)
§2  Geospatial Catchment (buffers, area apportionment, base map)
§3  Demographics (catchment profile, peer comparison)
§4  Competitor Landscape (classification, density, map)
§5  Demand Model (consult demand vs capacity, required share)
§6  Financial Model (P&L function, base-case run)
§7  Scenarios & Sensitivity
§8  Executive Report (markdown assembly → PDF)
```

### Structure Rationale

- **`data/cache/`:** The reproducibility keystone. With caches committed (they're small JSON), anyone can re-run the full notebook with **zero API calls and zero keys** — critical for a graded/investor artifact and for the Google-spend constraint.
- **`data/local/`:** Fallback-only assets. The notebook must run without them if the ABS API is up; if used, a visible warning prints so provenance is honest.
- **`outputs/`:** Generated artifacts kept out of the notebook file itself (folium maps embedded in .ipynb bloat it badly; save to HTML and display inline plus save PNG for the PDF).
- **Section numbering:** Mirrors data-flow dependencies exactly (see Data Flow) so "run all" always works top-to-bottom — the single most important property v1 lacks.

## Architectural Patterns

### Pattern 1: Cached Fetch Boundary

**What:** Every external request goes through one helper that checks `data/cache/<key>.json` before hitting the network, and writes through on miss.
**When to use:** Always, for all three APIs (geocode, ABS, Places). Never call `requests.get` directly from analysis cells.
**Trade-offs:** + Free/deterministic re-runs, works offline, protects rate limits and Google spend. − Stale data risk (acceptable: census/competitor data changes slowly; invalidation = delete file).

**Example:**
```python
import json, hashlib, re
from pathlib import Path

CACHE_DIR = PROJECT_ROOT / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def cache_key(*parts) -> str:
    """Human-readable, filesystem-safe, deterministic key."""
    raw = "_".join(str(p) for p in parts)
    return re.sub(r"[^A-Za-z0-9._-]+", "-", raw)[:120]

def cached_fetch(key: str, fetch_fn, force: bool = False):
    path = CACHE_DIR / f"{key}.json"
    if path.exists() and not force:
        print(f"[cache hit] {path.name}")
        return json.loads(path.read_text(encoding="utf-8"))
    data = fetch_fn()                      # only place the network is touched
    path.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"[cache write] {path.name}")
    return data

# usage
places = cached_fetch(
    cache_key("places", "doctor", f"{lat:.4f}", f"{lon:.4f}", radius_m),
    lambda: google_nearby_all_pages(lat, lon, radius_m, "doctor"),
)
```

**Cache keys and invalidation:**

| Source | Key composition | Invalidate when |
|--------|-----------------|-----------------|
| Geocode | `geocode_<slugified address>` | Address changes (key changes automatically) |
| ABS API | `abs_<dataflow>_<region>_<census-year>` e.g. `abs_C21_G02_POA3067` | Never for 2021 census (immutable vintage) |
| Places | `places_<type>_<lat:.4f>_<lon:.4f>_<radius>` | Want fresh competitors → delete file or `force=True` (rounded coords keep keys stable across float noise) |
| MBS | local file, no cache needed; if API'd, `mbs_sa3_20604_<quarter>` | New quarter released |

A single `FORCE_REFRESH = False` flag in the PARAMS cell threads through as `force=` for a one-switch full refresh.

### Pattern 2: Single Parameters Cell (Assumptions ≠ Computation)

**What:** All tunable inputs live in one clearly-labelled cell near the top: site address, radii, and every financial assumption — each with an inline citation or "UNCONFIRMED" flag. Downstream cells only *read* these; they never redefine them.
**When to use:** Always for scenario-driven models. This is what makes §7 scenarios trivial (`{**BASE_ASSUMPTIONS, **overrides}`).
**Trade-offs:** + One place to audit, investor-defensible, sensitivity analysis falls out for free. − Slight verbosity; discipline required not to hardcode constants downstream (rule: any numeric literal in §2-§8 that isn't a unit conversion is a bug).

**Example:**
```python
SITE_ADDRESS = "292-296 Johnston St, Abbotsford VIC 3067"
CATCHMENT_RADII_M = [1000, 3000, 5000]
PEER_POSTCODES = ["3067","3066","3121","3068","3070","3078","3079","3101","3122","3123"]

BASE_ASSUMPTIONS = {
    # --- Demand (source: MBS SA3 20604; RACGP GP:pop benchmarks) ---
    "consults_per_capita_yr": {"0-14": 4.4, "15-64": 5.1, "65+": 11.0},  # MBS 2024-25
    "consults_per_gp_day":   28,          # RACGP typical full-book GP
    # --- Revenue (source: MBS item 23 rebate; local gap-fee scan) ---
    "bulk_bill_share":       0.70,        # DECISION: mixed-billing model
    "std_rebate":            42.85,       # MBS item 23, 2025-26 — cite exact figure at build time
    "private_fee":           90.00,       # inner-Melb typical standard consult
    # --- Costs ---
    "gp_revenue_share":      0.35,        # % of billings retained by clinic (GPs keep 65%)
    "rent_yr":               100_000,     # UNCONFIRMED — key sensitivity, flagged in report
    "fitout_capital":        350_000,     # estimate — flagged, sensitivity-tested
    "n_gp_fte":              5,
    "n_allied_fte":          1,
}
```

### Pattern 3: Pure-Function Financial Model

**What:** The P&L is a function `clinic_pnl(a: dict) -> dict` with no globals, no notebook state, returning every line item plus derived metrics (EBIT, margin, months-to-breakeven).
**When to use:** Whenever scenarios/sensitivity are required. Scenarios become data (dicts of overrides), not copy-pasted cells.
**Trade-offs:** + Scenario table and tornado/sensitivity chart are ~10 lines each; testable with an asserted sanity check. − Slightly less "notebook-y" than inline arithmetic — mitigate with a teaching cell that walks through the base case line by line.

**Example:**
```python
def clinic_pnl(a: dict) -> dict:
    annual_consults = a["n_gp_fte"] * a["consults_per_gp_day"] * a["days_per_yr"] * a["utilisation"]
    rev_gp = annual_consults * (
        a["bulk_bill_share"] * a["std_rebate"]
        + (1 - a["bulk_bill_share"]) * a["private_fee"]
    )
    revenue = rev_gp + a["allied_revenue_yr"] + a["procedures_revenue_yr"]
    costs = (rev_gp * (1 - a["gp_revenue_share"])   # GP share paid out
             + a["rent_yr"] + a["staff_costs_yr"] + a["insurance_yr"]
             + a["admin_it_yr"] + a["equipment_leases_yr"])
    ebit = revenue - costs
    return {"revenue": revenue, "costs": costs, "ebit": ebit,
            "margin": ebit / revenue if revenue else 0,
            "breakeven_months": (a["fitout_capital"] / (ebit / 12)) if ebit > 0 else float("inf")}

SCENARIOS = {
    "base":        {},
    "optimistic":  {"utilisation": 0.85, "bulk_bill_share": 0.60},
    "pessimistic": {"utilisation": 0.60, "rent_yr": 120_000, "bulk_bill_share": 0.80},
}
results = {name: clinic_pnl({**BASE_ASSUMPTIONS, **ov}) for name, ov in SCENARIOS.items()}
```

### Pattern 4: Dual-Environment Bootstrap (Colab + local Windows)

**What:** One early cell detects the runtime and resolves paths and secrets accordingly; everything downstream uses `PROJECT_ROOT`-relative `pathlib.Path`s only.
**When to use:** Required by PROJECT.md ("Runs in Colab as primary… also work locally on Windows").
**Trade-offs:** + No hardcoded `/content/drive/...` paths (v1's flaw); `git clone` in Colab replaces Drive mounting. − Colab loses `data/cache/` between sessions unless the repo (with caches) is cloned or Drive is optionally mounted — committing caches solves this cleanly.

**Example:**
```python
import os, sys
from pathlib import Path

IN_COLAB = "google.colab" in sys.modules

if IN_COLAB:
    from google.colab import userdata
    GOOGLE_PLACES_KEY = userdata.get("GOOGLE_PLACES_KEY")   # Colab Secrets UI
    # repo cloned into /content (git clone in setup cell), caches come with it
    PROJECT_ROOT = Path("/content/medical-clinic")
else:
    from dotenv import load_dotenv
    load_dotenv()                                            # reads .env next to notebook
    GOOGLE_PLACES_KEY = os.environ.get("GOOGLE_PLACES_KEY", "")
    PROJECT_ROOT = Path(__file__).parent if "__file__" in dir() else Path.cwd()

assert GOOGLE_PLACES_KEY or (PROJECT_ROOT / "data/cache").exists(), \
    "Need GOOGLE_PLACES_KEY or a populated cache to run."
```
Key detail: because everything is cached, **a missing key degrades gracefully** — cache hits satisfy all fetches, so graders/reviewers can run without any secrets.

### Pattern 5: Report Metrics Accumulator → Markdown → PDF

**What:** Each analysis section deposits its headline numbers into a shared `report = {}` dict (e.g. `report["pop_3km"] = ...`, `report["gp_within_1km"] = ...`). §8 renders one f-string markdown template from that dict plus saved map PNGs, then converts to PDF.
**When to use:** Whenever a PDF deliverable must stay in sync with notebook numbers — no manual copy-paste of figures.
**Trade-offs:** + Zero drift between analysis and report; report template is readable prose. − Folium maps are HTML — export static images (`selenium`+headless chrome in Colab, or `folium` screenshot via `map._to_png()`, or simply matplotlib/contextily static maps for the PDF). Recommend: **folium for interactive notebook display, matplotlib+contextily for PDF figures** — avoids the headless-browser dependency entirely.

```python
md = REPORT_TEMPLATE.format(**report)          # f-string / .format template
(OUTPUTS / "report.md").write_text(md, encoding="utf-8")
# PDF: markdown → HTML → PDF
import markdown, weasyprint
html = f"<style>{REPORT_CSS}</style>" + markdown.markdown(md, extensions=["tables"])
weasyprint.HTML(string=html, base_url=str(OUTPUTS)).write_pdf(OUTPUTS / "Johnston_St_Feasibility.pdf")
```
(Fallback if weasyprint's native deps misbehave on Windows: `pandoc` via `pypandoc`, or Colab-only `!jupyter nbconvert --to pdf` for a notebook-styled export. Weasyprint in Colab needs `!apt-get install -y libpango-1.0-0 libpangocairo-1.0-0` — one line.)

## Data Flow

### Pipeline Flow (which sections depend on which)

```
§0 PARAMS ──────────────┬───────────────┬──────────────┬──────────────┐
                        ▼               ▼              ▼              ▼
§1.2 geocode ──► §2 catchment buffers   §1.4 Places    §1.5 MBS SA3   §6 P&L fn
                        │               (needs site    (independent)      ▲
        §1.3 ABS ──►────┤                lat/lon §1.2)     │              │
                        ▼                   ▼              │              │
                 §3 demographics      §4 competitors       │              │
                 (area-apportioned    (dedupe/classify     │              │
                  pop by ring)         per ring)           │              │
                        │                   │              │              │
                        └───────┬───────────┴──────────────┘              │
                                ▼                                         │
                        §5 demand model                                   │
                        (demand vs capacity → required share) ──► feeds ──┤
                                                                          ▼
                                                    §6 base-case P&L ──► §7 scenarios
                                                                          │
   §2 map + §4 map + §3 tables + §5/§6/§7 metrics ──► report{} dict ──►  §8 report → PDF
```

Dependency summary (build/run order is forced by this):

| Section | Depends on | Produces |
|---------|-----------|----------|
| §0 | — | `ASSUMPTIONS`, paths, keys, cache helper config |
| §1.2 geocode | §0 | `site_lat, site_lon` |
| §1.3 ABS | §0 | census DataFrames per POA |
| §1.4 Places | §1.2 | raw place lists per (type, radius) |
| §1.5 MBS | §0 | SA3 consult rates by age band |
| §2 catchment | §1.2, POA geometries | buffer GeoDataFrames, apportionment weights, base map |
| §3 demographics | §2, §1.3 | catchment pop/age/income by ring; peer table |
| §4 competitors | §1.4, §2 | classified competitor df, counts per ring, competitor map |
| §5 demand | §3, §4, §1.5 | annual consult demand, GP capacity, required market share |
| §6 financial | §0, §5 | `clinic_pnl()`, base-case P&L |
| §7 scenarios | §6 | scenario table, sensitivity table/chart |
| §8 report | §2–§7 (`report{}`) | report.md, PDF |

### Key Data Flows

1. **Census flow:** ABS API (SDMX-JSON, POA-level) → cache → tidy per-POA DataFrame → §2 area weights apportion into rings → §3 catchment age profile → §5 demand. Fallback branch: local GCP CSVs parsed into the *same tidy schema* so downstream code is source-agnostic.
2. **Competitor flow:** site coords → Places nearby (paginated, per type × radius) → cache → dedupe on `place_id` → brand classification (name-pattern rules for corporates/pharmacy chains) → per-ring counts feeding §5 capacity estimate and §4 map.
3. **Assumption flow:** `BASE_ASSUMPTIONS` (§0) is the *only* source of financial constants; §5 outputs (demand, required share) merge with it into the `clinic_pnl` input; §7 mutates only via override dicts.
4. **Report flow:** every section appends to `report{}`; §8 is a pure render step — re-running §8 alone regenerates the PDF from current state.

## Scaling Considerations

Scaling here means analysis scope, not users.

| Scale | Architecture Adjustments |
|-------|--------------------------|
| This project (1 site, 10 postcodes, 3 radii) | Single notebook, everything above. No modules needed. |
| Several candidate sites | Extract §1-§5 helpers into a `feasibility.py` module imported by the notebook; loop over site addresses; caches already keyed by coords so nothing else changes. |
| Ongoing/refreshable product | Move to scripts + Makefile/papermill parameterised runs; SQLite instead of JSON cache; SA1-level ABS geometry for finer apportionment. |

### Scaling Priorities

1. **First bottleneck:** Google Places spend and rate limits — solved day one by the cache boundary; never regress by adding uncached calls.
2. **Second bottleneck:** Notebook file size from embedded folium maps — save maps to `outputs/maps/*.html`, display via small inline render, use static matplotlib maps in the PDF.

## Anti-Patterns

(Each observed in v1 — these are the concrete fixes.)

### Anti-Pattern 1: Whole-Postcode Population Summing

**What people do:** Sum full populations of every POA whose polygon *touches* the buffer (v1 lines 84-91).
**Why it's wrong:** Massively overstates catchment population — a 3 km buffer clipping 5% of Richmond's polygon claims 100% of Richmond's residents. Demand model inherits the inflation.
**Do this instead:** Area-apportion: `pop_in_ring = poa_pop × (area(poa ∩ buffer) / area(poa))`, computed in a projected CRS (EPSG:7855). State the uniform-density assumption as a documented caveat.

### Anti-Pattern 2: Forward References / Non-Linear Execution Order

**What people do:** Use variables defined in later cells (v1 uses `s_lat`/`s_lon` at line 69, defined at line 495), relying on out-of-order interactive execution.
**Why it's wrong:** "Restart & Run All" fails; reproducibility is the whole point of the deliverable.
**Do this instead:** Strict top-to-bottom data flow (dependency table above). Acceptance test for every phase: **Restart & Run All must pass.**

### Anti-Pattern 3: ML Theatre on Tiny Data

**What people do:** Fit RandomForest/KMeans on 3-10 rows and present it as a demand model (v1 §clustering, RF import).
**Why it's wrong:** Statistically meaningless; destroys investor credibility; obscures the actual arithmetic.
**Do this instead:** Transparent age-adjusted arithmetic: `demand = Σ(age_band_pop × consults_per_capita[band])` from MBS SA3 rates. Peer-postcode comparison as a plain sorted table, not clusters. Every number traceable to a cited input.

### Anti-Pattern 4: Uncached, Un-keyed API Calls Scattered Through Analysis Cells

**What people do:** Call `requests.get` inline wherever data is needed (v1 refetches Places for every radius/postcode combination on each run).
**Why it's wrong:** Costs money each run, rate-limits ABS, makes runs nondeterministic (competitor counts drift), and requires the key just to re-render.
**Do this instead:** All I/O in §1 behind `cached_fetch`; analysis sections consume DataFrames only.

### Anti-Pattern 5: Hardcoded Environment Paths & Constants Buried in Cells

**What people do:** `/content/drive/MyDrive/Colab_Notebooks/...` literals (v1 lines 37, 140, 525); financial constants typed inline mid-analysis.
**Why it's wrong:** Breaks local runs; assumptions become unauditable; changing rent requires hunting through cells.
**Do this instead:** Pattern 4 bootstrap + Pattern 2 single params cell. Rule: no path literal and no un-cited numeric assumption outside §0.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| ABS Data API (api.data.abs.gov.au) | REST/SDMX-JSON GET, no key, via `cached_fetch` | Rate-limited; census 2021 data immutable → cache forever. Dataflow discovery (finding the right C21 dataflow/dimension codes for G01/G02-equivalents at POA level) is the main build risk — spike this early; local GCP CSVs are the safety net |
| Google Geocoding API | Single GET per address, cached by slugified address | One call ever, then free |
| Google Places Nearby Search | Paginated (max 60 results/query, 2s token delay), cached per (type, lat, lon, radius) | 60-result cap can truncate dense 5 km "doctor" queries — mitigate with grid of sub-queries or note as floor-count caveat; classify with name rules after fetch |
| Local files (GCP zip, POA shapefile, MBS xlsx, cohealth PDF) | `data/local/`, read with pandas/geopandas | Fallback only; print provenance warning when used. POA shapefile may be needed regardless (ABS API serves data, not geometry) unless using ABS geometry web service / a hosted GeoJSON |
| weasyprint / pandoc | §8 only | Colab needs one apt-get line for pango; test on Windows early or fall back to pandoc |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| §1 acquisition ↔ §2-§5 analysis | Tidy DataFrames with fixed schemas | Analysis never sees raw JSON or knows which source (API vs fallback) supplied data |
| §0 assumptions ↔ §6-§7 model | Single `BASE_ASSUMPTIONS` dict → pure `clinic_pnl()` | Scenarios are override dicts; no constant defined outside §0 |
| §2-§7 ↔ §8 report | `report{}` accumulator dict + saved figure files | §8 re-runnable standalone after any upstream change |
| Colab ↔ Windows | `PROJECT_ROOT` + `pathlib`; secrets via userdata/.env | Committed caches make either environment runnable keyless |

## Suggested Build Order

Order follows the dependency graph; each step ends with a "Restart & Run All" check.

1. **Skeleton + environment bootstrap (§0):** repo layout, `.env`/userdata handling, `PROJECT_ROOT`, params cell stub, cache helper. *Everything depends on this.*
2. **Data acquisition spikes (§1):** geocode (trivial) → **ABS API spike first** (highest uncertainty: finding correct dataflow/codes; wire fallback) → Places client with pagination+cache → MBS SA3 loader with state fallback. *Populates `data/cache/`.*
3. **Geospatial catchment (§2):** buffers, area apportionment, base folium map. *Needs geocode + POA geometry only — can proceed in parallel with ABS spike.*
4. **Demographics (§3):** merge §2 weights with §1.3 census; peer table. *Needs §1.3 + §2.*
5. **Competitors (§4):** dedupe, classify, per-ring counts, map. *Needs §1.4 + §2; parallel with §3.*
6. **Demand model (§5):** consult demand vs capacity → required share. *Needs §3 + §4 + §1.5 — first integration point; validates all upstream data.*
7. **Financial model (§6):** `clinic_pnl()`, base case, breakeven. *Needs only §0 assumptions + §5 required-share; the function itself can be drafted anytime after §0.*
8. **Scenarios & sensitivity (§7):** override dicts, sensitivity table (rent, bulk-bill %, utilisation, fit-out). *Trivial once §6 is a pure function.*
9. **Report & PDF (§8):** `report{}` template, static map exports, weasyprint/pandoc pipeline, test PDF render in **both** environments. *Last, but stub the `report{}` accumulator from step 3 onward so metrics accrue as sections land.*
10. **Hardening pass:** keyless run from cache only; fresh-clone Colab run; assumption citation audit; teaching-commentary pass.

Parallelisable pairs: (§2 ∥ ABS spike), (§3 ∥ §4), (§6 draft ∥ §5). Critical path: §0 → §1.3-ABS → §3 → §5 → §6 → §7 → §8.

## Sources

- v1 prototype audit: `C:\Users\josha\medical-clinic\johnston_st_v1.py` (flaws at lines 69, 84-91, 140, 201-224, 525)
- Project brief: `C:\Users\josha\medical-clinic\.planning\PROJECT.md`
- ABS Data API: https://api.data.abs.gov.au (free, no key, SDMX-JSON, rate-limited)
- Google Places Nearby Search docs (pagination, 60-result cap, next_page_token delay)
- Standard analytics-notebook practice: "Restart & Run All" reproducibility, parameters-first cells (papermill convention), cache-through I/O boundaries, cookiecutter-data-science `data/` layout conventions

---
*Architecture research for: reproducible geospatial/financial analytics notebook (Colab + local Windows)*
*Researched: 2026-07-05*
