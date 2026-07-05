# Phase 1: Scaffolding & Data Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-05
**Phase:** 01-scaffolding-data-pipeline
**Areas discussed:** Caching library, Colab bootstrap, Parameters cell shape, Cache/data commit policy

---

## Caching library

| Option | Description | Selected |
|--------|-------------|----------|
| requests-cache | `requests-cache` (≥1.2) filesystem backend, `allowable_methods=("GET","POST")`, ~3 lines. SQLite + blobs, not human-readable. Matches STACK.md. | ✓ |
| Hand-rolled helper | `cached_fetch(key, fn)` per ARCHITECTURE.md. Human-readable JSON, full control, but you write POST caching + key logic. | |
| Hybrid | requests-cache for HTTP + persist deduped competitor GeoDataFrame to `competitors.geojson`. | |

**User's choice:** requests-cache
**Notes:** The deduped-competitor GeoJSON persistence is a Phase 3 concern; Phase 1 only provides the cache session.

### Refresh control (follow-up)

| Option | Description | Selected |
|--------|-------------|----------|
| Single global flag | One `FORCE_REFRESH = False` in PARAMS, threaded into session. | ✓ |
| Per-source flags | `REFRESH_ABS`, `REFRESH_PLACES`, `REFRESH_GEOCODE`. | |
| Delete-file only | No flag; delete cache file/directory to refresh. | |

**User's choice:** Single global flag

---

## Colab bootstrap

| Option | Description | Selected |
|--------|-------------|----------|
| git clone | `!git clone` into `/content/medical-clinic`; caches + data committed. Cleanest reproducibility. | ✓ |
| Drive mount | v1 pattern; keeps big files out of git but reintroduces Drive-path coupling. | |
| Hybrid | git clone for code + optional Drive mount for large data if `data/local/` missing. | |

**User's choice:** git clone
**Notes:** Depends on caches being committed (see Cache/data commit policy). No Drive mount — v1's hardcoded Drive paths explicitly rejected.

---

## Parameters cell shape

| Option | Description | Selected |
|--------|-------------|----------|
| Flat dict | `BASE_ASSUMPTIONS = {...}` with inline `# source:` comments. Scenarios via `{**BASE, **overrides}`. Matches ARCHITECTURE.md. | ✓ |
| @dataclass | Typed fields, `dataclasses.replace()` for scenarios. Type-checked but breaks `**overrides`. | |
| External YAML/JSON | Config file loaded in §0. Separates config from code but breaks "single parameters CELL" rule (PIPE-05). | |

**User's choice:** Flat dict
**Notes:** ARCHITECTURE.md Pattern 2 is the structural template. Rule: any numeric literal in §2–§8 that isn't a unit conversion is a bug.

---

## Cache & data commit policy

| Option | Description | Selected |
|--------|-------------|----------|
| Commit caches, ignore big data | Commit ABS/geocode/Places caches (no secrets); gitignore `data/local/` + large files. Makes git-clone bootstrap work offline. | ✓ |
| Ignore everything in data/ | Tiny repo, but fresh clone can't run offline. Contradicts PIPE-04. | |
| Caches + Git LFS | Full offline reproducibility including local fallback. Overkill for solo student project. | |

**User's choice:** Commit caches, ignore big data

### Data file location (follow-up)

| Option | Description | Selected |
|--------|-------------|----------|
| Move to data/local/ | Move existing root-level data files into `data/local/` per ARCHITECTURE.md. Clean repo root. | ✓ |
| Leave in repo root | Less churn, but contradicts ARCHITECTURE.md layout. | |
| Move + auto-download | Move + setup-cell download if missing. Full bootstrap-from-scratch. More code. | |

**User's choice:** Move to data/local/

---

## Claude's Discretion

- Exact `requests-cache` session construction (backend format, expiry, filename)
- §0 pip-install cell design (which optional libs, local-run guard)
- `.env.example` exact contents and comment style
- Teaching commentary style (PIPE-06 requires it; format flexible)
- Notebook section header format / numbering display
- Cache hit/miss message format
- Private-repo auth handling in Colab (only if repo is private)
- Whether ABS API reference markdown files stay in root or move to `docs/`

## Deferred Ideas

- Deduped competitor GeoDataFrame persistence (`data/cache/competitors.geojson`) — Phase 3
- External YAML/JSON config file for non-Python investors — possible v2 milestone
- Git LFS for large local data — revisit if data set grows
- Auto-download of local fallback files from ABS/DoH websites if `data/local/` missing — possible enhancement
