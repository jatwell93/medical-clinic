---
phase: 01-scaffolding-data-pipeline
plan: 02
subsystem: pipeline
tags: [colab, requests-cache, python-dotenv, notebook, dual-environment, caching]

# Dependency graph
requires:
  - phase: 01-scaffolding-data-pipeline/01-01
    provides: "Repo scaffolding (.gitignore, .env.example, data/cache/, data/local/, outputs/, docs/abs-api/)"
provides:
  - "Johnston_St_v2.ipynb — deliverable notebook with §0 setup + §1 cache layer + ABS smoke test"
  - "scripts/create_v2_notebook.py — re-runnable generator script for notebook scaffolding"
  - "scripts/validate_v2_notebook.py — re-runnable validation script for PIPE-01..06 + v1 flaw checks"
  - "BASE_ASSUMPTIONS dict — single parameters cell with citation comments (PIPE-05)"
  - "CachedSession — single cached HTTP boundary for all external API calls (PIPE-04)"
  - "Dual-environment bootstrap pattern (IN_COLAB detection, PROJECT_ROOT resolution)"
affects: [02-catchment-demographics, 03-demand-competitors, 04-clinic-financial-model, 05-scenarios-executive-report]

# Tech tracking
tech-stack:
  added: [requests-cache, python-dotenv]
  patterns: [dual-environment-bootstrap, single-parameters-cell, cached-http-boundary, notebook-generator-script]

key-files:
  created:
    - "Johnston_St_v2.ipynb — deliverable notebook (11 cells: 6 markdown, 5 code)"
    - "scripts/create_v2_notebook.py — generator script (builds notebook via json.dump, no nbformat dep)"
    - "scripts/validate_v2_notebook.py — validation script (PIPE-01..06 + v1 flaw checks)"
  modified: []

key-decisions:
  - "Used json.dump (not nbformat) to avoid extra dependency — RESEARCH.md §4 recommendation"
  - "Teaching commentary reworded to avoid literal /content/drive string — acceptance criteria requires zero occurrences in any cell, including markdown"
  - "Generator script uses Path(__file__).resolve().parent.parent to find repo root — works from any CWD"

patterns-established:
  - "Notebook generator pattern: scripts/ create .ipynb via json.dump, re-runnable, no nbformat dependency"
  - "Validation pattern: scripts/validate_*.py checks structural + content + flaw-eradication, exits 0/1"
  - "Dual-environment bootstrap: IN_COLAB detection + PROJECT_ROOT resolution + graceful key degradation"
  - "Single parameters cell: BASE_ASSUMPTIONS flat dict with inline citation/UNCONFIRMED comments"
  - "Cached HTTP boundary: single CachedSession, all external calls go through session.get/session.post"

requirements-completed:
  - PIPE-01
  - PIPE-02
  - PIPE-03
  - PIPE-04
  - PIPE-05
  - PIPE-06

# Metrics
duration: 8min
completed: 2026-07-05
---

# Phase 1 Plan 02: Notebook v2 Scaffolding Summary

**Johnston_St_v2.ipynb with §0 dual-environment setup, single BASE_ASSUMPTIONS parameters cell, CachedSession HTTP boundary, and keyless ABS smoke test — all v1 flaws eradicated**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-07-05T18:44:00Z
- **Completed:** 2026-07-05T18:49:00Z
- **Tasks:** 2
- **Files modified:** 3 (all new)

## Accomplishments
- Created `Johnston_St_v2.ipynb` (11 cells: 6 markdown teaching commentary, 5 code) with §0 Setup & Configuration and §1 Data Acquisition & Caching sections
- Established the dual-environment bootstrap (IN_COLAB detection, PROJECT_ROOT resolution, Colab Secrets vs python-dotenv key loading)
- Built the single `BASE_ASSUMPTIONS` parameters cell with inline citation comments and `# UNCONFIRMED` flags on every value (PIPE-05)
- Constructed the `CachedSession` HTTP boundary with `allowable_methods=('GET', 'POST')` for Places API (New) POST caching (PIPE-04)
- Included the keyless ABS dataflow list smoke test that proves the cache layer works without a Google API key
- Eradicated all v1 flaws: zero `/content/drive` paths, zero `drive.mount` calls, zero bare `requests.get` calls
- Created re-runnable generator and validation scripts for reproducibility

## Task Commits

Each task was committed atomically:

1. **Task 1: Create notebook generator script and generate Johnston_St_v2.ipynb** - `1d47733` (feat)
2. **Task 2: Validate notebook structure and v1-flaw eradication** - `654ab63` (test)

## Files Created/Modified
- `Johnston_St_v2.ipynb` - The deliverable notebook with §0 (setup, env detect, PARAMS) and §1 (cache + ABS smoke test) cells
- `scripts/create_v2_notebook.py` - Generator script that builds the notebook as a dict and writes with json.dump (no nbformat dependency)
- `scripts/validate_v2_notebook.py` - Validation script checking structural validity, PIPE-01..06 content requirements, and v1 flaw eradication

## Decisions Made
- **json.dump over nbformat:** Used the `json` module to build the notebook dict and write with `json.dump(..., indent=1)` — avoids an extra dependency per RESEARCH.md §4. The .ipynb structure is simple enough that nbformat's abstraction adds no value.
- **Teaching commentary wording:** The plan's markdown cell descriptions referenced `/content/drive` and `drive.mount` as literal strings when describing v1 flaws. The acceptance criteria requires zero occurrences in any cell (including markdown). Reworded the teaching commentary to describe v1's flaws without using the literal strings (e.g., "hardcoded Google Drive mount-point paths" instead of the literal path).
- **Generator script path resolution:** Used `Path(__file__).resolve().parent.parent` to find the repo root from the scripts/ directory, so the generator works regardless of the current working directory.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Unicode arrow character in generator print statement**
- **Found during:** Task 1 (running generator script)
- **Issue:** The generator script's print statement used a Unicode arrow character (`→`) which caused a `UnicodeEncodeError` on Windows cp1252 encoding
- **Fix:** Replaced `→` with ASCII `->` in the print statement
- **Files modified:** scripts/create_v2_notebook.py
- **Verification:** Generator runs without error, produces notebook correctly
- **Committed in:** 1d47733 (Task 1 commit)

**2. [Rule 2 - Missing Critical] Teaching commentary contained literal /content/drive and drive.mount strings**
- **Found during:** Task 1 (running plan verification command)
- **Issue:** The plan's markdown cell descriptions included literal `/content/drive` and `drive.mount` strings when explaining v1 flaws. The acceptance criteria requires zero occurrences in any cell source (including markdown teaching commentary).
- **Fix:** Reworded the teaching commentary to describe v1's flaws without using the literal strings. "Hardcoded Drive paths (`/content/drive/MyDrive/...`)" became "Hardcoded Google Drive paths (v1 used literal Drive mount-point paths)". "Drive mount dependency (`drive.mount(...)`)" became "Drive mount dependency (v1 called the Drive mount API)".
- **Files modified:** scripts/create_v2_notebook.py
- **Verification:** `grep -c "/content/drive" Johnston_St_v2.ipynb` returns 0; `grep -c "drive.mount" Johnston_St_v2.ipynb` returns 0; validation script passes
- **Committed in:** 1d47733 (Task 1 commit)

**3. [Rule 2 - Missing Critical] ABS smoke test assumed JSON but ABS returns SDMX-ML XML**
- **Found during:** Colab runtime testing (user-reported during human UAT)
- **Issue:** The §1.2 smoke test called `response.json()` and asserted on JSON keys, but the ABS dataflow endpoint returns SDMX-ML XML by default (Content-Type: `application/vnd.sdmx.structure+xml`). Requesting JSON via `Accept: application/json` causes the server to hang/return 500. The plan's research notes (STACK.md) confirmed the endpoint URL but did not verify the response format.
- **Fix:** Rewrote the smoke test to validate HTTP 200 + SDMX content-type + `sdmx` namespace in the response body, instead of parsing JSON. Updated the markdown teaching commentary to explain that ABS returns SDMX-ML XML and that Phase 2 will use `?format=csvfilewithlabels` for actual census data. Also fixed `CACHE_DIR.glob("*.json")` → `CACHE_DIR.rglob("*.json")` because requests-cache filesystem backend stores responses in a `data/cache/api_cache/` subdirectory named after `cache_name`.
- **Files modified:** scripts/create_v2_notebook.py, Johnston_St_v2.ipynb, .gitignore
- **Verification:** End-to-end smoke test run: Run 1 HTTP 200 from_cache=False (1 cache file written), Run 2 from_cache=True (cache hit confirmed — PIPE-04 validated). Validation script still passes OVERALL: PASS.
- **Committed in:** db14f6f (post-execution fix during human UAT)

**4. [Rule 2 - Missing Critical] .gitignore redirects.sqlite path did not match actual cache layout**
- **Found during:** fix #3 above (cache files are in `data/cache/api_cache/` subdirectory, not directly in `data/cache/`)
- **Issue:** The plan specified `.gitignore` pattern `data/cache/redirects.sqlite`, but requests-cache creates the file at `data/cache/api_cache/redirects.sqlite`. The original pattern did not match, so the regenerable cache metadata would have been committed.
- **Fix:** Changed `.gitignore` pattern to `data/cache/**/redirects.sqlite` to match recursively regardless of cache_name.
- **Files modified:** .gitignore
- **Verification:** `git check-ignore -v data/cache/api_cache/redirects.sqlite` matches; `git check-ignore -v data/cache/api_cache/*.json` returns exit 1 (not ignored — correct per D-12).
- **Committed in:** db14f6f (same commit as fix #3)

---

**Total deviations:** 4 auto-fixed (4 missing critical)
**Impact on plan:** Fixes 3 and 4 were discovered during human UAT (Colab runtime testing). Both are format/path assumptions in the plan that could only be caught by actually running the smoke test against the live ABS API. No scope creep — the smoke test still validates the same property (cache layer works) and the .gitignore policy (D-12) is still honored.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required. The notebook degrades gracefully without a Google API key (cache-only mode).

## Next Phase Readiness
- §0 setup, env detection, and single parameters cell are complete — Phase 2 can read `BASE_ASSUMPTIONS` for site address, radii, and peer postcodes
- §1 CachedSession is constructed and proven via ABS smoke test — Phase 2 can use `session.get()` for ABS census data and Google geocoding
- `PROJECT_ROOT` and `CACHE_DIR` are resolved and available to all downstream cells
- The validation script can be re-run at any time to confirm structural integrity
- Phase 2 (Catchment & Demographics) can proceed: geocode the site address, build 1/3/5 km buffers in EPSG:7855, and fetch ABS census data through the cached session

## Self-Check: PASSED

All plan-level verification commands executed successfully:
- `python scripts/create_v2_notebook.py` — runs without error, produces 11-cell notebook
- `python -c "import json; json.load(open('Johnston_St_v2.ipynb'))"` — valid JSON
- `python scripts/validate_v2_notebook.py` — exits 0 with "OVERALL: PASS"
- `grep -c "BASE_ASSUMPTIONS" Johnston_St_v2.ipynb` — returns 7 (>=1)
- `grep -c "CachedSession" Johnston_St_v2.ipynb` — returns 5 (>=1)
- `grep -c "/content/drive" Johnston_St_v2.ipynb` — returns 0
- `grep -c "drive.mount" Johnston_St_v2.ipynb` — returns 0

---
*Phase: 01-scaffolding-data-pipeline*
*Completed: 2026-07-05*
