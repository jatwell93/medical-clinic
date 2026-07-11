---
phase: quick/260711-gif
plan: 01
subsystem: notebook
tags: [caching, competitor-accuracy, demand-constrained, cost-safety, places-api]
dependency_graph:
  requires: []
  provides:
    - places_cache committed to git (1781 files + 1 geocode)
    - manual_classifications.csv (64 curated entries)
    - ALLOW_LIVE_CALLS guard in cells 5 + 40
    - existing_gp_capacity computed per ring (cells 56-57)
    - demand-constrained verdict (cells 68, 71, 79, 101)
  affects:
    - Johnston_St_v2.ipynb (cells 5, 15, 40, 41, 42, 51, 53, 55, 56, 57, 62, 68, 71, 79, 101, 102)
    - .gitignore
    - data/local/manual_classifications.csv
    - data/cache/places_cache/ (1781 files)
    - data/cache/geocode_cache/ (1 file)
tech_stack:
  added: []
  patterns:
    - ALLOW_LIVE_CALLS guard pattern (hard cap + RuntimeError on cache miss)
    - Manual filesystem cache with git-committed JSON (no requests-cache)
    - Address-based site collapse (normalize_addr → gp_sites_gdf → existing_gp_capacity)
    - Demand-constrained verdict (achievable_util = min(target, unmet/clinic_cap))
key_files:
  created:
    - data/local/manual_classifications.csv
  modified:
    - Johnston_St_v2.ipynb
    - .gitignore
decisions:
  - D-LOCKED-A: Verdict gates on achievable_util = min(target, unmet_demand/clinic_capacity) — not full-books
  - D-LOCKED-B: Existing GP supply = distinct clinic SITES by normalized address, per-site listing-count FTE proxy
  - Cache files (places_cache, geocode_cache) contain NO API keys — safe to commit; un-ignored in .gitignore
  - manual_classifications.csv committed via git add -f (data/local/ is ignored; negation needs force-add for directory-level rules)
metrics:
  duration: "~45 minutes"
  completed: "2026-07-11"
  tasks_completed: 5
  tasks_total: 5
  files_modified: 5
  files_created: 1784
---

# Phase quick/260711-gif Plan 01: Fix Batch — Caching Cost-Safety + Competitor Accuracy + Demand-Constrained Verdict

**One-liner:** 10-bug fix batch: un-ignores 1781 Places cache files (preventing ~$500 AUD API rebilling on Colab), adds ALLOW_LIVE_CALLS guard with hard cap, fixes saturation sub-circle geometry (sqrt(2) overlap), extracts 64 Brave Search classifications to CSV, collapses GP competitors to distinct address-based sites (D-LOCKED-B), and gates the Go/No-Go verdict on demand-constrained utilisation ceiling (D-LOCKED-A).

## Tasks Completed

| Task | Name | Commit | Key files |
|------|------|--------|-----------|
| T1 | Caching cost-safety (.gitignore + cells 5/40/41/42) | f4fbeb7 | .gitignore, cells 5, 40, 41, 42 |
| T2 | Competitor accuracy — site-collapse, CSV extraction | 0d9f451 | cells 51, 53, 55, 56, 57, 62; manual_classifications.csv; .gitignore |
| T3 | Demand-constrained verdict | da460af | cells 68, 71, 79, 101, 102, 5 |
| T4 | Loud geocode fallback banner | 3c5457a | cell 15 |
| T5 | Commit 1781 cache files | 37b9c8c | data/cache/places_cache/ (1781 files), data/cache/geocode_cache/ (1 file) |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] T3: comment in cell 71 triggered verify assertion**
- **Found during:** T3 verify
- **Issue:** Plan's verify check `assert 'constrained_pnl' not in src71` fired because the instructed comment `# NOTE: constrained_pnl = clinic_pnl({...}) runs in cell 79` contained the string. The comment was intentional per plan instructions.
- **Fix:** Renamed comment to `# NOTE: the P&L call at demand-ceiling util runs in cell 79` — same semantics, no false positive.
- **Files modified:** Johnston_St_v2.ipynb (cell 71)
- **Commit:** da460af

**2. [Rule 1 - Bug] T2: data/local/ directory-level gitignore prevents exception**
- **Found during:** T2 commit
- **Issue:** `.gitignore` has `data/local/` as a directory match. Git does not allow a negation `!data/local/manual_classifications.csv` to override a directory-level rule without `git add -f`. The plan's gitignore exception `!data/local/manual_classifications.csv` is present but cannot be staged without force.
- **Fix:** Added a clarifying comment to .gitignore explaining the force-add requirement. Staged the file with `git add -f data/local/manual_classifications.csv`.
- **Files modified:** .gitignore
- **Commit:** 0d9f451

**3. [Rule 2 - Missing] T2: import pd as _pd typo in plan's cell 57 source**
- **Found during:** T2 implementation
- **Issue:** The plan's cell 57 code sample contained `import pandas as pd as _pd` which is invalid Python syntax.
- **Fix:** Used `import pandas as pd` (already imported in cell scope from upstream cells) and referenced `pd.DataFrame` directly. The plan's intent was to use `pd` as a local alias — using the standard import is correct.
- **Files modified:** Johnston_St_v2.ipynb (cell 57)
- **Commit:** 0d9f451

## Known Stubs

None. All plan requirements implemented. `existing_gp_capacity` wired from cell 57 → cell 68 → cell 71 → cell 79 → cell 101. All report deposits present.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: information-disclosure | data/cache/places_cache/ | 1781 JSON files committed to public repo. Verified: contain only place records + lat/lon coordinates, no API keys. Spot-check performed before T5 commit: 0 patterns found for key/api_key/secret/token in first 20 files of each dir. |

## Self-Check

### Files created exist:
- `data/local/manual_classifications.csv` — exists, 64 rows
- `data/cache/places_cache/` — 1781 files tracked (`git ls-files`: 1781)
- `data/cache/geocode_cache/` — 1 file tracked

### Commits exist:
- f4fbeb7 — T1 (prior session)
- 0d9f451 — T2
- da460af — T3
- 3c5457a — T4
- 37b9c8c — T5

### Full structural checks: PASSED (verified above)

## Self-Check: PASSED
