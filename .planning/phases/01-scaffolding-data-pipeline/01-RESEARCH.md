# Phase 1: Scaffolding & Data Pipeline - Research

**Researched:** 2026-07-05
**Confidence:** HIGH (well-established libraries; specifics verified against docs and v1 prototype)

## Summary

Phase 1 implementation is technically straightforward with well-documented libraries. The main edge cases are: (1) requests-cache filesystem backend stores individual JSON files plus a `redirects.sqlite`, which matches ARCHITECTURE.md's `data/cache/*.json` expectation with one extra metadata file; (2) python-dotenv is NOT preinstalled in Colab and must be pip-installed; (3) v1 has critical flaws (used-before-definition variables, hardcoded Drive paths, uncached requests) that teaching commentary must explicitly address; (4) the ABS dataflow list endpoint provides a perfect keyless smoke test for cache validation.

## 1. requests-cache Implementation Specifics (HIGH confidence)

**Constructor parameters:**
```python
from requests_cache import CachedSession

session = CachedSession(
    cache_name=str(PROJECT_ROOT / "data" / "cache"),  # Base path for cache files
    backend='filesystem',                              # One JSON file per response
    allowable_methods=('GET', 'POST'),                 # Required for Places API (New) POST
    expire_after=-1,                                   # No expiration (census is immutable vintage)
)
```

**POST caching with Places API:** The cache key DOES include the POST body (normalized JSON). Field-mask headers are included in the key by default unless added to `ignored_parameters`. No special gotcha — requests-cache handles Places (New) POST requests correctly.

**FORCE_REFRESH pattern:** Two options — `session.cache.clear()` for full wipe, or per-request `force_refresh=True` parameter. Cleanest pattern threading the PARAMS flag:
```python
# In PARAMS cell
FORCE_REFRESH = False

# In requests
response = session.post(url, json=payload, force_refresh=FORCE_REFRESH)
```

**Cache file location:** Filesystem backend creates individual JSON files (one per response) in `<cache_name>/<cache_key>.json`, plus a `redirects.sqlite` for redirect tracking. This matches ARCHITECTURE.md's `data/cache/*.json` expectation — the directory structure is correct, just with one additional SQLite metadata file that should be gitignored (regenerable).

**Colab/Windows compatibility:** Works identically on both. `pathlib.Path` ensures cross-platform path handling. No permission issues expected.

## 2. Colab Git Clone Bootstrap (HIGH confidence)

**Shell guard pattern:**
```python
import os
repo_path = "/content/medical-clinic"
if not os.path.exists(repo_path):
    !git clone https://github.com/<owner>/medical-clinic.git {repo_path}
```

**Repo visibility:** OPEN QUESTION — see Open Questions section. If private, auth via PAT in Colab Secrets or embedded in URL.

**Cache directory after clone:** If caches are committed (D-12), they come with the clone. No manual copy needed. This is the reproducibility keystone.

**Working directory:** `%cd /content/medical-clinic` persists across cells in Colab, but it's safer to use `PROJECT_ROOT` everywhere (ARCHITECTURE.md Pattern 4) rather than relying on shell state.

## 3. python-dotenv Dual-Environment Pattern (HIGH confidence)

**Colab installation:** python-dotenv is NOT preinstalled in Colab. Must pip-install in the §0 installs cell:
```python
%pip install -q python-dotenv requests-cache
```

**Import pattern:**
```python
import os, sys
from pathlib import Path

IN_COLAB = "google.colab" in sys.modules

if IN_COLAB:
    from google.colab import userdata
    GOOGLE_PLACES_KEY = userdata.get("GOOGLE_PLACES_KEY")
    PROJECT_ROOT = Path("/content/medical-clinic")
else:
    from dotenv import load_dotenv
    load_dotenv()  # Reads .env from current directory; fails silently if missing
    GOOGLE_PLACES_KEY = os.environ.get("GOOGLE_PLACES_KEY", "")
    PROJECT_ROOT = Path.cwd()  # Notebooks don't have __file__
```

**Missing .env handling:** `load_dotenv()` returns `False` but does NOT raise if `.env` doesn't exist. Acceptable — the cache fallback (D-12) means a missing key degrades gracefully to cache hits.

**PROJECT_ROOT resolution:** `Path.cwd()` is correct for notebooks since `__file__` is not available. ARCHITECTURE.md's example using `Path(__file__).parent` is wrong for notebooks — use `Path.cwd()`.

## 4. Notebook Creation Approach (HIGH confidence)

**Recommendation:** Create the `.ipynb` JSON directly via a Python script using `json.dump`, NOT via nbformat (avoids an extra dependency, the structure is simple). A small `create_notebook.py` helper script can generate the initial `Johnston_St_v2.ipynb` with all §0 and §1 cells pre-populated.

**Minimal valid .ipynb structure:**
```json
{
  "nbformat": 4,
  "nbformat_minor": 0,
  "metadata": {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.12.0"}
  },
  "cells": []
}
```

**Teaching commentary convention:** Markdown cells with section headers in `## §0.1` format (matching ARCHITECTURE.md). Place a markdown cell before each code section explaining: what it does, why, and what v1 flaw it fixes (PIPE-06).

## 5. ABS Data API Smoke Test (HIGH confidence)

**Minimal keyless endpoint:**
```python
response = session.get("https://data.api.abs.gov.au/rest/dataflow?detail=allstubs")
```

**Response format:** Returns SDMX-ML/JSON structure. The `format=csvfilewithlabels` parameter (used in Phase 2 for actual data) produces CSV with both codes and human-readable labels.

**Phase 1 smoke test suitability:** YES — this endpoint requires no API key, validates that the cache works (PIPE-04), and doesn't overlap with Phase 2's actual census data fetching. Perfect for proving the caching layer works before adding Google Places (which requires a key).

**Validation assertions:**
```python
assert (PROJECT_ROOT / "data" / "cache").exists(), "Cache directory not created"
assert len(list((PROJECT_ROOT / "data" / "cache").glob("*.json"))) > 0, "No cache files created"
# After second run with FORCE_REFRESH=False:
assert response.from_cache == True, "ABS smoke test not cached on re-run"
```

## 6. .gitignore Patterns (HIGH confidence)

**Recommended .gitignore:**
```
# Secrets
.env

# Python
__pycache__/
*.pyc
*.pyo

# Jupyter
.ipynb_checkpoints/

# Local fallback data (large files — D-13)
data/local/

# Generated outputs
outputs/

# Cache metadata (regenerable; keep the .json response files per D-12)
data/cache/redirects.sqlite

# OS
.DS_Store
Thumbs.db
```

**Cache commit policy (per D-12):** Commit `data/cache/*.json` files (ABS and Places responses contain no secrets). Gitignore `data/cache/redirects.sqlite` (metadata only, regenerable).

**v1 notebook tracking:** YES — `Johnston_St_v1.ipynb` and `johnston_st_v1.py` should be tracked as frozen reference per PROJECT.md.

## 7. Local Data File Organization (HIGH confidence)

**Files to move to `data/local/` (per D-14):**
- `2021_GCP_POA_for_VIC_short-header.zip`
- `POA_2021_AUST_GDA2020_SHP.zip`
- `GCP_POA3067.xlsx`
- `SA3_2021_AUST.xlsx`
- `medicare-annual-statistics-state-and-territory-2009-10-to-2024-25.xlsx`
- `medicare-quarterly-statistics-primary-care-service-type-summary-march-quarter-2025-26(1).xlsx`
- `Catchment-Report-Cohealth-collingwood-Centre-2026-6-11-113449 (1).pdf`
- `292 Johnston Ground Floor Plan (1).pdf`

**ABS reference markdown files** (recommend moving to `docs/abs-api/` for cleaner repo root):
- `Using_the_API_Australian_Bureau_of_Statistics.md`
- `Worked_Examples_Australian_Bureau_of_Statistics.md`
- `metadata.md`
- `tips.md`

**Files staying in repo root:**
- `Johnston_St_v1.ipynb` (frozen reference)
- `johnston_st_v1.py` (frozen reference)
- `Johnston_St_v2.ipynb` (the deliverable — created in this phase)
- `CLAUDE.md`, `.planning/`, `.gitignore`, `.env.example`

## 8. Teaching Commentary — v1 Flaws to Address (HIGH confidence)

**Critical v1 flaws that Phase 1 teaching commentary must reference (PIPE-06):**

1. **Used-before-definition pattern (v1 line 69 vs 495):** `s_lat`/`s_lon` used in catchment cell before geocoding cell defines them. Teaching point for §0/§1: "Variables flow strictly downward — unlike v1 where site coordinates were used before definition, breaking 'Restart & Run All'."

2. **Hardcoded Drive paths (v1 lines 37, 140, 525):** `/content/drive/MyDrive/Colab_Notebooks/...` literals. Teaching point for §0 env-detect cell: "We use PROJECT_ROOT-relative paths — unlike v1's hardcoded Drive paths that fail on Windows and other users' systems."

3. **Uncached requests.get calls (v1 throughout):** No caching layer; every re-run hits the API. Teaching point for §1 cache cell: "All API calls go through the CachedSession — unlike v1's uncached requests that cost money on every re-run."

4. **Drive mount dependency (v1 line 33):** `drive.mount('/content/drive')`. Teaching point for §0 bootstrap: "We use git clone instead of Drive mount — unlike v1 which required manual Drive setup and lost caches between sessions."

5. **ML on tiny data (v1 lines 204-224):** KMeans clustering on 3 postcodes. Teaching point (referenced in PARAMS cell commentary, addressed in Phase 3): "We use transparent arithmetic instead of ML — v1's clustering on 3 data points was statistically meaningless."

## Validation Architecture

**Dimension 8 (Nyquist validation) for Phase 1:**

The phase's "validation" is reproducibility itself — the notebook must run offline/keyless after caches are committed. Concrete assertions:

1. **Cache creation assertion:** After first run, `data/cache/` exists and contains ≥1 JSON file.
2. **Cache hit assertion:** After second run with `FORCE_REFRESH=False`, ABS smoke test response has `from_cache == True`.
3. **No-hardcoded-paths assertion:** Grep the notebook source for `/content/drive` — must return zero matches (v1 flaw eradication).
4. **Single-PARAMS-cell assertion:** Grep for numeric literals in §2–§8 cells — only unit conversions allowed (PIPE-05). Phase 1 only has §0/§1, so this is a forward-looking convention established here.
5. **Dual-environment assertion:** `IN_COLAB` detection runs without error in both environments; `PROJECT_ROOT` resolves to an existing directory in both.
6. **Keyless-run assertion:** With `GOOGLE_PLACES_KEY=""` and populated cache, the notebook runs to completion of §1 ABS smoke test without raising.

## Resolved Questions (user-confirmed 2026-07-05)

1. **Repo visibility:** **PUBLIC** — git clone in Colab needs no auth. The bootstrap cell uses a plain `!git clone https://github.com/<owner>/medical-clinic.git /content/medical-clinic` with a TODO placeholder for the owner username.

2. **Cache file format:** **Filesystem backend** — individual JSON files in `data/cache/` plus a gitignored `redirects.sqlite`. Matches ARCHITECTURE.md's `data/cache/*.json` expectation and is teaching-friendly.

3. **Teaching commentary granularity:** **Section markdown + inline** — markdown cells before each section (§0.1, §0.2, etc.) explaining what/why/v1-flaw; inline comments for implementation details within code cells.

## RESEARCH COMPLETE

Phase 1 is ready for planning. All implementation patterns are documented with code examples. All open questions resolved.
