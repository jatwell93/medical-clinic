#!/usr/bin/env python3
"""
Generator script for Johnston_St_v2.ipynb.

Builds the notebook as a dict and writes it with json.dump(..., indent=1).
Does NOT use nbformat — avoids an extra dependency (RESEARCH.md §4).

The notebook contains:
  §0 Setup & Configuration
    §0.1 Installs & imports
    §0.2 Environment Detection & Paths
    §0.3 Parameters & Assumptions (BASE_ASSUMPTIONS — the single params cell)
  §1 Data Acquisition & Caching
    §1.1 Cache session construction (CachedSession)
    §1.2 ABS Data API Smoke Test (keyless, proves cache works)
  Next Steps (markdown)

Run:  python scripts/create_v2_notebook.py
Output: Johnston_St_v2.ipynb (in repo root)
"""

import json
from pathlib import Path


def md(source_lines):
    """Create a markdown cell dict."""
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source_lines,
    }


def code(source_lines):
    """Create a code cell dict."""
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source_lines,
    }


def lines(*lns):
    """Join strings into a source list, each ending with \\n except the last."""
    result = []
    for i, ln in enumerate(lns):
        if i < len(lns) - 1:
            result.append(ln + "\n")
        else:
            result.append(ln)
    return result


# ──────────────────────────────────────────────────────────────────────
#  Cell definitions
# ──────────────────────────────────────────────────────────────────────

cells = []

# === §0 SETUP & CONFIGURATION ===

# 1. Markdown — §0 header
cells.append(md(lines(
    "# §0 Setup & Configuration",
    "",
    "This section establishes the **reproducible foundation** for the entire notebook.",
    "Every subsequent phase (§2 catchment, §3 demographics, §4 competitors, §5 demand,",
    "§6 financial model, §7 scenarios, §8 report) depends on the paths, keys, and",
    "parameters defined here.",
    "",
    "**v1 flaws addressed in this section:**",
    "- *Hardcoded Google Drive paths* (v1 used literal Drive mount-point paths",
    "  that only worked on the original author's Colab) — replaced with",
    "  `PROJECT_ROOT`-relative `pathlib.Path`s that work on any machine.",
    "- *Drive mount dependency* (v1 called the Drive mount API) — replaced with",
    "  `git clone`, so caches travel with the repo and no manual Drive setup",
    "  is needed.",
    "- *Scattered constants* — consolidated into a single `BASE_ASSUMPTIONS` dict.",
    "",
    "The **dual-environment pattern** detects Colab vs Windows at runtime and resolves",
    "all paths accordingly. This is what makes \"Restart & Run All\" work in both",
    "environments without manual intervention (PIPE-01, PIPE-02).",
)))

# 2. Code — §0.1 Installs & imports
cells.append(code(lines(
    "# §0.1 — Installs & imports",
    "# Only pip-install packages NOT preinstalled in Colab (RESEARCH.md §3).",
    "# geopandas/shapely/pyproj/folium/pandas/matplotlib/jinja2 are preinstalled.",
    "import os, sys, json, requests",
    "from pathlib import Path",
    "",
    "IN_COLAB = \"google.colab\" in sys.modules",
    "",
    "if IN_COLAB:",
    "    # requests-cache and python-dotenv are NOT preinstalled in Colab",
    "    %pip install -q requests-cache python-dotenv",
    "",
    "from requests_cache import CachedSession",
    "",
    "print(\"[setup] imports loaded\")",
)))

# 3. Markdown — §0.2 Environment Detection & Paths
cells.append(md(lines(
    "## §0.2 Environment Detection & Paths",
    "",
    "v1 used hardcoded Google Drive mount-point paths that only worked on the",
    "original author's Colab with a manually mounted Drive. This cell detects the",
    "runtime environment and resolves `PROJECT_ROOT` via `pathlib` so the same code",
    "works on Colab (after `git clone`) and on Windows.",
    "",
    "**Key design decisions (from CONTEXT.md):**",
    "- **D-06:** Colab clones the repo into `/content/medical-clinic`; caches come",
    "  with the clone (committed to git per D-12).",
    "- **D-07:** No Drive mount — explicitly rejected. Caches and code travel",
    "  together via git.",
    "- **D-12:** API response caches are committed to git, so a fresh clone can",
    "  re-run the notebook offline/keyless at $0 (PIPE-04).",
    "",
    "The API key loads from Colab Secrets (`userdata`) or local `.env`",
    "(`python-dotenv`). A missing key degrades gracefully — cache hits satisfy",
    "all fetches (PIPE-03).",
)))

# 4. Code — §0.2 Environment detection
cells.append(code(lines(
    "# §0.2 — Environment detection & path resolution (PIPE-02)",
    "# TODO: replace <OWNER> with your GitHub username",
    "if IN_COLAB:",
    "    # Clone repo if not already present (caches come with it — D-06)",
    "    import subprocess",
    "    repo_path = \"/content/medical-clinic\"",
    "    if not os.path.exists(repo_path):",
    "        subprocess.run([\"git\", \"clone\", \"https://github.com/jatwell93/medical-clinic.git\", repo_path],",
    "                       check=True)",
    "    PROJECT_ROOT = Path(repo_path)",
    "    # Load API key from Colab Secrets",
    "    try:",
    "        from google.colab import userdata",
    "        GOOGLE_PLACES_KEY = userdata.get(\"GOOGLE_PLACES_KEY\")",
    "    except Exception:",
    "        GOOGLE_PLACES_KEY = \"\"",
    "else:",
    "    # Local Windows — load from .env via python-dotenv",
    "    from dotenv import load_dotenv",
    "    load_dotenv()  # Fails silently if .env missing — acceptable (cache fallback)",
    "    GOOGLE_PLACES_KEY = os.environ.get(\"GOOGLE_PLACES_KEY\", \"\")",
    "    PROJECT_ROOT = Path.cwd()  # Notebooks don't have __file__",
    "",
    "# Graceful degradation: key is optional if cache is populated (D-12)",
    "CACHE_DIR = PROJECT_ROOT / \"data\" / \"cache\"",
    "assert CACHE_DIR.exists() or GOOGLE_PLACES_KEY, \\",
    "    \"Need GOOGLE_PLACES_KEY or a populated data/cache/ to run.\"",
    "",
    "print(f\"[env] IN_COLAB={IN_COLAB}, PROJECT_ROOT={PROJECT_ROOT}\")",
    "print(f\"[env] Google Places key: {'loaded' if GOOGLE_PLACES_KEY else 'empty (cache-only mode)'}\")",
)))

# 5. Markdown — §0.3 Parameters & Assumptions
cells.append(md(lines(
    "## §0.3 Parameters & Assumptions",
    "",
    "This is the **single source of truth** for every numeric assumption in the",
    "notebook (PIPE-05). v1 had constants scattered across cells — making it",
    "impossible to audit or run scenarios without hunting through the notebook.",
    "",
    "**Why a flat dict?** The flat-dict shape makes Phase 5 scenarios trivial:",
    "`{**BASE_ASSUMPTIONS, **overrides}`. A `@dataclass` would break this pattern;",
    "an external YAML/JSON file would break the \"single parameters cell\" wording.",
    "",
    "**Rule (from ARCHITECTURE.md):** any numeric literal in §2–§8 that isn't a",
    "unit conversion is a bug. Downstream cells *read* these values; they never",
    "redefine them.",
    "",
    "Every value has an inline comment with a **source citation** or an",
    "`# UNCONFIRMED` flag so the assumptions register (Phase 5, REP-01) can be",
    "assembled automatically from this cell.",
)))

# 6. Code — §0.3 PARAMETERS cell
cells.append(code(lines(
    "# ═══════════════════════════════════════════════════════════════",
    "#  SINGLE PARAMETERS CELL — every assumption lives here (PIPE-05)",
    "#  Downstream cells READ these; they never redefine them.",
    "#  Scenarios (Phase 5): {**BASE_ASSUMPTIONS, **overrides}",
    "# ═══════════════════════════════════════════════════════════════",
    "",
    "SITE_ADDRESS = \"292-296 Johnston St, Abbotsford VIC 3067\"",
    "CATCHMENT_RADII_M = [1000, 3000, 5000]  # 1/3/5 km rings",
    "PEER_POSTCODES = [\"3067\", \"3066\", \"3068\", \"3070\", \"3078\", \"3079\",",
    "                  \"3101\", \"3121\", \"3122\", \"3123\"]",
    "",
    "# Cache control — single global refresh flag (D-04)",
    "FORCE_REFRESH = False",
    "",
    "BASE_ASSUMPTIONS = {",
    "    # --- Site & catchment ---",
    "    \"site_address\":           SITE_ADDRESS,",
    "    \"catchment_radii_m\":      CATCHMENT_RADII_M,",
    "    \"peer_postcodes\":         PEER_POSTCODES,",
    "",
    "    # --- Demand (source: MBS SA3 20604 Yarra; RACGP GP:pop benchmarks) ---",
    "    \"consults_per_capita_yr\": {\"0-14\": 4.4, \"15-64\": 5.1, \"65+\": 11.0},  # MBS 2024-25 — UNCONFIRMED vintage",
    "    \"consults_per_gp_day\":    28,          # RACGP typical full-book GP",
    "",
    "    # --- Revenue (source: MBS item 23 rebate; local gap-fee scan) ---",
    "    \"bulk_bill_share\":        0.70,        # DECISION: mixed-billing model (70% bulk / 30% private)",
    "    \"std_rebate\":             43.90,       # MBS item 23, 2025-26 — verify at build time",
    "    \"private_fee\":            95.00,       # inner-Melb typical standard consult — UNCONFIRMED",
    "    \"gp_revenue_share\":       0.35,        # % of billings retained by clinic (GPs keep 65%) — UNCONFIRMED range 30-35%",
    "",
    "    # --- Costs ---",
    "    \"rent_yr\":                100_000,     # UNCONFIRMED — key sensitivity, flagged in report",
    "    \"fitout_capital\":         350_000,     # estimate — flagged, sensitivity-tested",
    "    \"n_gp_fte\":               5,",
    "    \"n_allied_fte\":           1,",
    "",
    "    # --- Operational ---",
    "    \"days_per_yr\":            220,         # GP working days after leave",
    "    \"utilisation\":            0.75,        # ramp-up target utilisation",
    "}",
    "",
    "print(f\"[params] {len(BASE_ASSUMPTIONS)} assumptions loaded\")",
    "print(f\"[params] FORCE_REFRESH={FORCE_REFRESH}\")",
)))

# === §1 DATA ACQUISITION & CACHING ===

# 7. Markdown — §1 header
cells.append(md(lines(
    "# §1 Data Acquisition & Caching",
    "",
    "v1 had **no caching** — every re-run hit the ABS and Google APIs, costing",
    "money and making the notebook non-reproducible offline. This section",
    "establishes a single `CachedSession` that **all** external calls go through",
    "(ABS Data API, Google Geocoding, Google Places).",
    "",
    "**What this gives us (PIPE-04):**",
    "- Re-runs are **free** — cached responses are served from disk.",
    "- Re-runs are **offline-capable** — no network needed if cache is populated.",
    "- Re-runs are **keyless** — ABS needs no key; Places/Geocode cache hits",
    "  need no key. A grader or investor can clone the repo and run the entire",
    "  notebook without any API keys.",
    "",
    "The ABS smoke test below proves the cache works using a **keyless** endpoint",
    "(the dataflow list requires no API key). On first run it fetches from the",
    "network; on second run it serves from cache (`response.from_cache == True`).",
)))

# 8. Code — §1.1 Cache session construction
cells.append(code(lines(
    "# §1.1 — Cache session construction (D-01, D-02, D-03)",
    "# Single cached HTTP boundary for ALL external calls (D-01, D-02, D-03)",
    "# requests-cache filesystem backend: one JSON file per response in data/cache/",
    "# allowable_methods includes POST for Google Places API (New) — STACK.md requirement",
    "CACHE_DIR.mkdir(parents=True, exist_ok=True)",
    "",
    "session = CachedSession(",
    "    cache_name=str(CACHE_DIR / \"api_cache\"),",
    "    backend='filesystem',",
    "    allowable_methods=('GET', 'POST'),  # POST needed for Places API (New)",
    "    expire_after=-1,                     # No expiry — census is immutable vintage",
    ")",
    "",
    "# Apply FORCE_REFRESH flag from PARAMS cell (D-04)",
    "if FORCE_REFRESH:",
    "    session.cache.clear()",
    "    print(\"[cache] cleared (FORCE_REFRESH=True)\")",
    "",
    "print(f\"[cache] session ready → {CACHE_DIR}\")",
)))

# 9. Markdown — §1.2 ABS Data API Smoke Test
cells.append(md(lines(
    "## §1.2 ABS Data API Smoke Test",
    "",
    "This proves the cache layer works using a **keyless** ABS endpoint. The",
    "dataflow list (`/rest/dataflow?detail=allstubs`) requires no API key, so",
    "this test runs even in cache-only mode (no `GOOGLE_PLACES_KEY`).",
    "",
    "**What it validates (PIPE-04):**",
    "- The `CachedSession` is correctly constructed and can make HTTP requests.",
    "- On first run: fetches from the network and writes a cache file.",
    "- On second run: serves from cache (`response.from_cache == True`).",
    "- Cache files appear in `data/cache/` as JSON.",
    "",
    "This is the foundation that makes every subsequent API call (ABS census,",
    "Google geocode, Google Places) free and offline-reproducible.",
)))

# 10. Code — §1.2 ABS smoke test
cells.append(code(lines(
    "# §1.2 — ABS Data API smoke test (PIPE-04 validation)",
    "# Keyless smoke test — proves the cache layer works (PIPE-04)",
    "# ABS dataflow list endpoint requires no API key",
    "ABS_DATAFLOW_URL = \"https://data.api.abs.gov.au/rest/dataflow?detail=allstubs\"",
    "",
    "response = session.get(ABS_DATAFLOW_URL)",
    "print(f\"[abs] HTTP {response.status_code}, from_cache={response.from_cache}\")",
    "",
    "# Validate response structure",
    "data = response.json()",
    "assert \"dataflows\" in data or \"structure\" in str(data)[:500], \\",
    "    f\"ABS response structure unexpected: {str(data)[:200]}\"",
    "",
    "# Cache validation assertions (RESEARCH.md Validation Architecture)",
    "assert CACHE_DIR.exists(), \"Cache directory not created\"",
    "cache_files = list(CACHE_DIR.glob(\"*.json\"))",
    "assert len(cache_files) > 0, \"No cache files created — cache layer not working\"",
    "",
    "print(f\"[abs] {len(cache_files)} cache file(s) in {CACHE_DIR}\")",
    "print(f\"[abs] Smoke test PASSED — cache layer operational\")",
)))

# 11. Markdown — Next Steps
cells.append(md(lines(
    "## Next Steps",
    "",
    "The foundation is now in place:",
    "- §0 established the dual-environment bootstrap, paths, API key loading,",
    "  and the single `BASE_ASSUMPTIONS` parameters cell.",
    "- §1 established the cached HTTP boundary (`CachedSession`) and proved it",
    "  works with the ABS smoke test.",
    "",
    "**Phase 2 (§2 Catchment & Demographics)** will use this cache session for:",
    "- Google Geocoding API — geocode the exact site address (cached).",
    "- ABS Data API — fetch `C21_G01_POA` / `C21_G02_POA` census tables (cached).",
    "",
    "**Phase 3 (§4 Competitors)** will use it for:",
    "- Google Places API (New) — `POST places:searchNearby` queries (cached,",
    "  `allowable_methods=('GET', 'POST')` enables POST caching).",
    "",
    "Every downstream section reads from `BASE_ASSUMPTIONS` and routes HTTP",
    "through `session`. No exceptions.",
)))

# ──────────────────────────────────────────────────────────────────────
#  Assemble notebook
# ──────────────────────────────────────────────────────────────────────

nb = {
    "nbformat": 4,
    "nbformat_minor": 0,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.12.0",
        },
    },
    "cells": cells,
}

# Write to repo root (parent of scripts/)
output_path = Path(__file__).resolve().parent.parent / "Johnston_St_v2.ipynb"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print(f"[generator] wrote {len(cells)} cells -> {output_path}")
print(f"[generator]   markdown cells: {sum(1 for c in cells if c['cell_type'] == 'markdown')}")
print(f"[generator]   code cells:     {sum(1 for c in cells if c['cell_type'] == 'code')}")
