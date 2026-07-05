---
phase: 01-scaffolding-data-pipeline
plan: 01
subsystem: infra
tags: [gitignore, env, repo-structure, data-pipeline, reproducibility]

# Dependency graph
requires: []
provides:
  - ".gitignore with secrets/local-data/outputs exclusion policy (D-12, D-13, D-15)"
  - ".env.example documenting GOOGLE_PLACES_KEY for Colab and Windows"
  - "data/local/ directory with 8 fallback data assets (D-14)"
  - "data/cache/ directory (git-tracked via .gitkeep) for committed API response caches (D-12)"
  - "outputs/ directory (git-tracked via .gitkeep) for generated maps and report"
  - "docs/abs-api/ with 4 ABS Data API reference markdown files"
  - "Clean repo root — no data files cluttering the top level"
affects: [01-scaffolding-data-pipeline, 02-catchment-demographics, 03-demand-competitors]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Cache commit policy: data/cache/*.json committed (no secrets), redirects.sqlite gitignored"
    - "Local fallback data gitignored (data/local/) — large files not in git"
    - "Dual-environment secrets: .env.example documents key name for both Colab and Windows"

key-files:
  created:
    - ".gitignore"
    - ".env.example"
    - "data/cache/.gitkeep"
    - "outputs/.gitkeep"
    - "docs/abs-api/Using_the_API_Australian_Bureau_of_Statistics.md"
    - "docs/abs-api/Worked_Examples_Australian_Bureau_of_Statistics.md"
    - "docs/abs-api/metadata.md"
    - "docs/abs-api/tips.md"
  modified: []

key-decisions:
  - "data/cache/*.json files are NOT gitignored — only redirects.sqlite is (D-12: committed for reproducibility)"
  - "outputs/.gitkeep force-added to git despite outputs/ being gitignored, so the directory survives in fresh clones"
  - "data/local/ files moved but not committed (gitignored per D-13 — large fallback assets)"

patterns-established:
  - "Repo hygiene: secrets in .env (gitignored), local data in data/local/ (gitignored), caches in data/cache/ (committed)"
  - "Directory layout matches ARCHITECTURE.md Recommended Project Structure"

requirements-completed: [PIPE-03, PIPE-04]

# Metrics
duration: 4 min
completed: 2026-07-05
---

# Phase 1 Plan 01: Repo Scaffolding Summary

**.gitignore, .env.example, and clean directory layout with 8 data files relocated to data/local/ and 4 ABS docs to docs/abs-api/**

## Performance

- **Duration:** 4 min
- **Started:** 2026-07-05T08:37:00Z
- **Completed:** 2026-07-05T08:41:10Z
- **Tasks:** 2
- **Files modified:** 8 (2 created in Task 1, 6 new tracked files in Task 2)

## Accomplishments
- Established repo hygiene rules: .env (secrets), data/local/ (large files), outputs/ (generated), redirects.sqlite (metadata) all gitignored; data/cache/*.json committed for reproducibility
- Created .env.example documenting GOOGLE_PLACES_KEY for both Colab (Secrets sidebar) and Windows (.env + python-dotenv) environments
- Relocated 8 local data assets (GCP census zip, POA shapefile zip, MBS xlsx files, cohealth catchment PDF, floor plan PDF) from repo root to data/local/
- Relocated 4 ABS Data API reference markdown files from repo root to docs/abs-api/
- Created data/cache/ and outputs/ directories with .gitkeep files so they survive in git
- Repo root is now clean — zero .zip/.xlsx/.pdf files at root level

## Task Commits

Each task was committed atomically:

1. **Task 1: Create .gitignore and .env.example** - `5390043` (chore)
2. **Task 2: Create directory structure and relocate data files** - `b0e3e6c` (chore)

## Files Created/Modified
- `.gitignore` - Repo hygiene rules: excludes .env, data/local/, outputs/, data/cache/redirects.sqlite; does NOT exclude data/cache/*.json
- `.env.example` - Documents GOOGLE_PLACES_KEY= placeholder with usage instructions for Colab and Windows
- `data/cache/.gitkeep` - Empty marker so cache directory survives in git (for committed API response caches)
- `outputs/.gitkeep` - Empty marker so outputs directory survives in git (force-added; outputs/ is gitignored)
- `docs/abs-api/Using_the_API_Australian_Bureau_of_Statistics.md` - ABS Data API user guide (moved from root)
- `docs/abs-api/Worked_Examples_Australian_Bureau_of_Statistics.md` - ABS API worked examples (moved from root)
- `docs/abs-api/metadata.md` - ABS API metadata reference (moved from root)
- `docs/abs-api/tips.md` - ABS API tips (moved from root)
- `data/local/` - 8 relocated data files (gitignored, not tracked: 2 zips, 4 xlsx, 2 pdfs)

## Decisions Made
- data/cache/*.json files are NOT gitignored (only redirects.sqlite is) — per D-12, API response caches are the reproducibility keystone and contain no secrets
- outputs/.gitkeep force-added to git with `git add -f` despite outputs/ being in .gitignore, so the directory structure survives in fresh clones
- data/local/ files moved but not committed to git (gitignored per D-13 — ~74MB of large fallback assets)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required. The .env.example documents the GOOGLE_PLACES_KEY name; users copy it to .env locally or add it via Colab Secrets. No setup file generated.

## Next Phase Readiness
- Repo structure is now in place for Plan 01-02 (notebook v2 scaffolding): data/cache/ exists for the CachedSession, data/local/ holds fallback assets, outputs/ ready for generated artifacts
- The .gitignore policy ensures API caches committed in later plans will be tracked correctly
- Ready for 01-02-PLAN.md execution

---
*Phase: 01-scaffolding-data-pipeline*
*Completed: 2026-07-05*
