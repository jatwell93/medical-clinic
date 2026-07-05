# Phase 1: Scaffolding & Data Pipeline - Context

**Gathered:** 2026-07-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish the reproducible foundation for the entire notebook: dual-environment bootstrap (Colab primary, Windows local), a single cached HTTP boundary for all external API calls (ABS Data API, Google Geocoding, Google Places), a single parameters cell holding every numeric assumption with citations, and the teaching-commentary convention. Every subsequent phase fetches external data through this layer and re-runs at $0 offline.

Scope anchor (from ROADMAP.md, fixed): PIPE-01 through PIPE-06. Discussion clarifies HOW to implement within this boundary — not whether to add new capabilities.

</domain>

<decisions>
## Implementation Decisions

### Caching layer
- **D-01:** Use `requests-cache` (≥1.2) with filesystem backend as the single HTTP cache boundary for ALL external calls (ABS Data API, Google Geocoding, Google Places). One `CachedSession` instance constructed in §0/§1.
- **D-02:** Enable `allowable_methods=("GET","POST")` so Places API (New) POST requests are cached (STACK.md requirement — Places (New) uses POST).
- **D-03:** Cache directory lives at `PROJECT_ROOT / "data" / "cache"` so the same path works in Colab (after git clone) and on Windows.
- **D-04:** Single global `FORCE_REFRESH = False` flag in the PARAMS cell, threaded into the session as the refresh control. One switch refreshes everything; no per-source knobs.
- **D-05:** NOT chosen: hand-rolled `cached_fetch()` helper (ARCHITECTURE.md example). The requests-cache approach replaces it. The deduped-competitor GeoJSON persistence (`data/cache/competitors.geojson`) suggested in STACK.md is a Phase 3 concern — Phase 1 only provides the cache session, not analysis-output persistence.

### Colab bootstrap
- **D-06:** §0 setup cell does `!git clone https://github.com/<owner>/medical-clinic.git /content/medical-clinic` (guarded so it skips if the directory already exists). `PROJECT_ROOT = Path("/content/medical-clinic")` in Colab.
- **D-07:** No Drive mount. v1's hardcoded `/content/drive/...` paths are explicitly rejected. Caches and code travel together via git.
- **D-08:** This decision depends on D-09..D-12 (caches must be committed for a fresh clone to run offline). The bootstrap and commit-policy decisions are coupled.

### Parameters cell shape
- **D-09:** Flat dict `BASE_ASSUMPTIONS = {...}` with inline `# source: ...` / `# UNCONFIRMED` comments per key, exactly as ARCHITECTURE.md's Pattern 2 example. Lives in a single labelled cell in §0.
- **D-10:** Scenarios (Phase 4/5) are `{**BASE_ASSUMPTIONS, **overrides}` dicts — the flat-dict shape makes this trivial. Do NOT use a `@dataclass` (breaks the `**overrides` pattern) or an external YAML/JSON file (breaks PIPE-05's "single parameters cell" wording).
- **D-11:** Site address, radii, peer postcodes, and every financial/demand constant live in this dict. Rule (from ARCHITECTURE.md): any numeric literal in §2–§8 that isn't a unit conversion is a bug.

### Cache & data commit policy
- **D-12:** Commit API caches to git — ABS responses, geocode response, Places responses. They contain no secrets and are the reproducibility keystone (PIPE-04: "re-runs offline/keyless at $0"). This is what makes the git-clone bootstrap (D-06) work for graders/reviewers with no API key.
- **D-13:** Gitignore `data/local/` and the large local fallback files. Do NOT commit the ~74MB of local data (GCP zip 13MB, POA shapefile zip 56MB, MBS xlsx ~4.5MB, cohealth PDF, floor plan PDF).
- **D-14:** Move the existing root-level data files into `data/local/` per ARCHITECTURE.md's layout. Reference them downstream via `PROJECT_ROOT / "data" / "local" / ...`. Repo root stays clean.
- **D-15:** `.env` and any cache files containing API keys go in `.gitignore`. ABS cache responses contain no secrets and ARE committed. Places responses contain no secrets and ARE committed.
- **D-16:** NOT chosen: Git LFS for large files (overkill for a solo student project); ignoring all of `data/cache/` (contradicts PIPE-04 and breaks the git-clone bootstrap).

### Claude's Discretion
- Exact `requests-cache` session construction details (backend format, expiry policy, cache filename)
- §0 pip-install cell design (which optional libs to `%pip install -q`, guard for local runs)
- `.env.example` exact contents and comment style
- Teaching commentary style (markdown cells per section vs inline comments vs both) — PIPE-06 requires teaching commentary throughout but the format is flexible
- Notebook section header format / numbering display
- Whether to print cache hit/miss messages and in what format
- Private-repo authentication handling in Colab (only relevant if the repo is private — user can clarify at plan time)

</decisions>

<specifics>
## Specific Ideas

- ARCHITECTURE.md's Pattern 1 (`cached_fetch`) and Pattern 4 (dual-environment bootstrap) are the structural templates — Phase 1 implements them with `requests-cache` replacing the hand-rolled helper.
- STACK.md's "Config / secrets — dual-environment pattern" is the authoritative source for the Colab-vs-Windows detection logic (`"google.colab" in sys.modules`).
- The existing local data files to move into `data/local/`: `2021_GCP_POA_for_VIC_short-header.zip`, `POA_2021_AUST_GDA2020_SHP.zip`, `GCP_POA3067.xlsx`, `SA3_2021_AUST.xlsx`, `medicare-annual-statistics-state-and-territory-2009-10-to-2024-25.xlsx`, `medicare-quarterly-statistics-primary-care-service-type-summary-march-quarter-2025-26(1).xlsx`, `Catchment-Report-Cohealth-collingwood-Centre-2026-6-11-113449 (1).pdf`, `292 Johnston Ground Floor Plan (1).pdf`. The ABS API reference markdown files (`Using_the_API_*.md`, `Worked_Examples_*.md`, `metadata.md`, `tips.md`) can stay in root or move to `docs/` — Claude's discretion.
- v1 files (`Johnston_St_v1.ipynb`, `johnston_st_v1.py`) stay in repo root, frozen as reference (PROJECT.md decision).

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture & patterns
- `.planning/research/ARCHITECTURE.md` §"Standard Architecture" + "Recommended Project Structure" — the §0–§8 notebook section layout, `data/cache/` + `data/local/` + `outputs/` directory structure, and the linear-pipeline-with-cached-IO-boundary model
- `.planning/research/ARCHITECTURE.md` §"Pattern 1: Cached Fetch Boundary" — the caching pattern (implement with `requests-cache` per D-01, not the hand-rolled helper shown)
- `.planning/research/ARCHITECTURE.md` §"Pattern 2: Single Parameters Cell" — the `BASE_ASSUMPTIONS = {...}` shape with citation comments (D-09, D-10, D-11)
- `.planning/research/ARCHITECTURE.md` §"Pattern 4: Dual-Environment Bootstrap" — the `IN_COLAB` detection + `PROJECT_ROOT` resolution logic (D-06, D-07)

### Stack & library specifics
- `.planning/research/STACK.md` §"Core Technologies" (requests-cache row) — `requests-cache ≥1.2`, `allowable_methods=("GET","POST")` for Places POST caching (D-01, D-02)
- `.planning/research/STACK.md` §"Google Places API — use Places API (New)" — confirms POST + field-mask requirement that drives the `allowable_methods` decision
- `.planning/research/STACK.md` §"Config / secrets — dual-environment pattern" — `.env` + `data/cache/` gitignore split, `python-dotenv` for Windows (D-15)

### Requirements & roadmap
- `.planning/REQUIREMENTS.md` §"Pipeline & Environment (PIPE)" — PIPE-01 through PIPE-06 are the verifiable success criteria for this phase
- `.planning/ROADMAP.md` §"Phase 1 — Scaffolding & Data Pipeline" — phase goal, success criteria, dependencies (none), research flag (No — well-established patterns)

### Pitfalls to avoid
- `.planning/research/PITFALLS.md` §"Pitfall 4" (ABS Data API) and §"Pitfall 10" (Places cost blowout) — both justify the cache-everything, run-offline design
- `.planning/research/PITFALLS.md` §"Pitfall 3" (centroid vs address, out-of-order execution) — informs the §0/§1 ordering discipline that Phase 1 establishes

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Johnston_St_v1.ipynb` / `johnston_st_v1.py` — v1 prototype. Reference only (frozen). Useful to mine for: the `google_nearby_places` function structure (Places query logic), the ABS API call shape, and the list of peer postcodes. Do NOT copy v1's hardcoded Drive paths, `s_lat`/`s_lon` used-before-definition pattern, or its uncached `requests.get` calls.
- Local data files (listed in Specific Ideas) — these become the `data/local/` fallback assets. Already on hand, no download needed for first run.

### Established Patterns
- None yet — Phase 1 IS the pattern-establishment phase. Every decision here becomes the convention downstream phases follow.

### Integration Points
- §0 PARAMS cell → read by every downstream section (§2 catchment reads radii; §6 P&L reads financial constants; §7 scenarios read BASE_ASSUMPTIONS for override merging)
- `CachedSession` (§1) → used by §1.2 geocode, §1.3 ABS, §1.4 Places, and indirectly by §1.5 MBS if it ever moves to an API
- `PROJECT_ROOT` (§0) → used by every path in the notebook
- `data/cache/` directory → committed to git; the git-clone bootstrap (D-06) depends on it being populated after a first complete run

</code_context>

<deferred>
## Deferred Ideas

- Deduped competitor GeoDataFrame persistence to `data/cache/competitors.geojson` (STACK.md suggestion) — Phase 3 (Demand & Competitors), when competitor dedupe is actually built.
- External YAML/JSON config file for non-Python-savvy investors to edit — rejected for now (breaks PIPE-05's "single cell" wording); could revisit in a v2 milestone if collaborator editing becomes a real need.
- Git LFS for large local data files — rejected as overkill; revisit if the local data set grows beyond what a manual copy can handle.
- Auto-download of local fallback files from ABS/DoH websites if `data/local/` is missing — noted as a possible enhancement but not required for Phase 1 (the files are already on hand).

</deferred>

---

*Phase: 01-scaffolding-data-pipeline*
*Context gathered: 2026-07-05*
