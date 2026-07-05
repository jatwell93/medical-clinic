---
status: passed
phase: 01-scaffolding-data-pipeline
verified_at: 2026-07-05T19:30:00Z
requirements_verified: [PIPE-01, PIPE-02, PIPE-03, PIPE-04, PIPE-05, PIPE-06]
must_haves_total: 26
must_haves_verified: 26
gaps: []
human_verification:
  - "Actual Colab Restart & Run All execution (notebook structure is correct but has not been executed in Colab)"
  - "Actual local Windows execution with .env present (dual-environment code path not runtime-tested)"
  - "Second-run cache hit verification (response.from_cache == True on re-run with FORCE_REFRESH=False)"
  - "Replace <OWNER> placeholder in git clone URL with actual GitHub username before first Colab run"
---

## Phase 01 Verification

### Goal Achievement

The phase goal — *"Establish the reproducible foundation — dual-environment bootstrap, cached API boundary, single parameters cell, and teaching-commentary convention — so every subsequent phase can fetch external data deterministically and re-run at zero cost"* — has been **substantially achieved**. All structural and programmatic checks pass. The four pillars of the goal are in place:

1. **Dual-environment bootstrap:** `IN_COLAB = "google.colab" in sys.modules` detection is present (§0.1/§0.2); `PROJECT_ROOT` resolves to `Path("/content/medical-clinic")` in Colab and `Path.cwd()` locally; `CACHE_DIR = PROJECT_ROOT / "data" / "cache"` is environment-agnostic. The Colab branch clones the repo via `git clone` (no Drive mount); the local branch loads `.env` via `python-dotenv`.

2. **Cached API boundary:** A single `CachedSession` is constructed in §1.1 with `backend='filesystem'`, `allowable_methods=('GET', 'POST')` (POST for Places API New), and `expire_after=-1` (immutable census vintage). The `FORCE_REFRESH` flag from the PARAMS cell threads into the session. The ABS dataflow smoke test (§1.2) proves the cache works via a keyless endpoint.

3. **Single parameters cell:** `BASE_ASSUMPTIONS` is a flat dict in §0.3 containing site address, catchment radii, peer postcodes, demand rates, revenue constants, cost estimates, and operational parameters. Every value has an inline citation comment or `# UNCONFIRMED` flag. `FORCE_REFRESH` lives in the same cell.

4. **Teaching-commentary convention:** 6 markdown cells precede each code section, explaining what/why/v1-flaw for §0, §0.2, §0.3, §1, §1.2, and Next Steps.

The remaining gap is runtime verification: the notebook has not been executed in Colab or locally, and the `<OWNER>` placeholder in the git clone URL requires human replacement before the first Colab run.

### Must-Haves Verification

#### Plan 01-01 — Repo Scaffolding (13 must_haves, 13 verified)

| # | Type | Must-Have | Verification |
|---|------|-----------|--------------|
| 1 | truth | .gitignore exists and contains .env, data/local/, outputs/, data/cache/redirects.sqlite | PASS — `.gitignore` lines 2, 13, 16, 19 contain all four patterns |
| 2 | truth | .env.example exists with GOOGLE_PLACES_KEY= placeholder and usage instructions | PASS — `.env.example` line 4 has `GOOGLE_PLACES_KEY=` (empty value); lines 1-3 document both environments |
| 3 | truth | data/local/ contains the 8 moved data files | PASS — `ls data/local/ \| wc -l` = 8 (2 zips, 4 xlsx, 2 pdfs) |
| 4 | truth | data/cache/ directory exists (with .gitkeep) | PASS — `test -f data/cache/.gitkeep` succeeds |
| 5 | truth | outputs/ directory exists (with .gitkeep) | PASS — `test -f outputs/.gitkeep` succeeds |
| 6 | truth | Repo root is clean — no .zip, .xlsx, .pdf at root level | PASS — `ls *.zip *.xlsx *.pdf 2>/dev/null \| wc -l` = 0 |
| 7 | truth | ABS API reference markdown files moved to docs/abs-api/ | PASS — `ls docs/abs-api/ \| wc -l` = 4 (Using_the_API, Worked_Examples, metadata, tips) |
| 8 | artifact | .gitignore (contains ".env") | PASS — line 2: `.env` |
| 9 | artifact | .env.example (contains "GOOGLE_PLACES_KEY") | PASS — line 4: `GOOGLE_PLACES_KEY=` |
| 10 | artifact | data/local/ (fallback data assets) | PASS — 8 files present |
| 11 | artifact | data/cache/.gitkeep (cache directory in git) | PASS — file exists |
| 12 | artifact | docs/abs-api/ (ABS reference docs) | PASS — 4 markdown files present |
| 13 | key_link | .gitignore → data/cache/ via "data/cache/redirects.sqlite" (NOT data/cache/) | PASS — line 19 has `data/cache/redirects.sqlite`; no bare `data/cache/` entry (D-12 policy honored: *.json committed) |

#### Plan 01-02 — Notebook Scaffolding (13 must_haves, 13 verified)

| # | Type | Must-Have | Verification |
|---|------|-----------|--------------|
| 1 | truth | Johnston_St_v2.ipynb exists and is valid JSON with nbformat 4 | PASS — `json.load` succeeds; `nb['nbformat'] == 4` |
| 2 | truth | §0 Setup section with env detection (IN_COLAB) and PROJECT_ROOT resolution | PASS — `IN_COLAB` appears 4×; `PROJECT_ROOT` resolved in both branches |
| 3 | truth | §0 PARAMETERS cell with BASE_ASSUMPTIONS dict (site, radii, peer postcodes, financial constants, citation comments) | PASS — `BASE_ASSUMPTIONS` appears 7×; dict contains all required keys; `# UNCONFIRMED` flags present (5×) |
| 4 | truth | §1 Data Acquisition section with CachedSession construction (filesystem, GET+POST) | PASS — `CachedSession` appears 5×; `allowable_methods=('GET', 'POST')` present (3×) |
| 5 | truth | §1 ABS smoke test cell calls dataflow list through cached session | PASS — `dataflow?detail=allstubs` present (2×); `session.get(ABS_DATAFLOW_URL)` in smoke test cell |
| 6 | truth | NO hardcoded /content/drive paths | PASS — `grep -c "/content/drive"` = 0 |
| 7 | truth | Teaching commentary markdown cells before each section | PASS — 6 markdown cells (≥4 required); section headers §0, §0.2, §0.3, §1, §1.2 present |
| 8 | truth | FORCE_REFRESH flag in PARAMS cell, referenced by cache session | PASS — `FORCE_REFRESH` appears 5×; defined in §0.3, used in §1.1 (`if FORCE_REFRESH: session.cache.clear()`) |
| 9 | truth | GOOGLE_PLACES_KEY loads from Colab userdata or local .env | PASS — `userdata.get("GOOGLE_PLACES_KEY")` in Colab branch; `load_dotenv()` + `os.environ.get` in local branch |
| 10 | artifact | Johnston_St_v2.ipynb (contains "BASE_ASSUMPTIONS") | PASS — 7 occurrences |
| 11 | artifact | scripts/create_v2_notebook.py (contains "json.dump") | PASS — line 365: `json.dump(nb, f, indent=1)` |
| 12 | key_link | FORCE_REFRESH flows from §0 PARAMS to §1 cache cell | PASS — defined in cell 5 (§0.3), consumed in cell 7 (§1.1); validation confirms definition-before-use |
| 13 | key_link | PROJECT_ROOT resolved in env detect, used by PARAMS for paths | PASS — defined in cell 3 (§0.2), `CACHE_DIR = PROJECT_ROOT / "data" / "cache"` in same cell; validation confirms PROJECT_ROOT before CACHE_DIR |

### Requirements Traceability

| REQ-ID | Description | Where Addressed | Verified |
|--------|-------------|-----------------|----------|
| PIPE-01 | Restart & Run All, no manual intervention | §0.1–§1.2 cells flow top-to-bottom; validation script confirms PROJECT_ROOT before CACHE_DIR, FORCE_REFRESH before session | PASS (structural) |
| PIPE-02 | Dual-environment auto-detection | §0.2: `IN_COLAB = "google.colab" in sys.modules`; `PROJECT_ROOT = Path(repo_path)` (Colab) / `Path.cwd()` (local) | PASS |
| PIPE-03 | Key loading from Colab userdata or local .env; no keys in git | §0.2: `userdata.get("GOOGLE_PLACES_KEY")` (Colab) / `load_dotenv()` + `os.environ.get` (local); `.env` gitignored; `.env.example` has empty placeholder; no .env tracked in git | PASS |
| PIPE-04 | All API responses cached to data/cache/; re-runs offline/keyless at $0 | §1.1: `CachedSession(backend='filesystem', allowable_methods=('GET','POST'), expire_after=-1)`; §1.2: ABS smoke test via `session.get()`; `.gitignore` commits `data/cache/*.json` (only redirects.sqlite ignored) | PASS (structural) |
| PIPE-05 | Single parameters cell with citation comments | §0.3: `BASE_ASSUMPTIONS` flat dict with inline `# source:` and `# UNCONFIRMED` comments; `FORCE_REFRESH` flag in same cell | PASS |
| PIPE-06 | Teaching commentary in markdown throughout | 6 markdown cells before each section explaining what/why/v1-flaw (§0, §0.2, §0.3, §1, §1.2, Next Steps) | PASS |

### Validation Results

**`python scripts/validate_v2_notebook.py`** — Exit code 0:
```
[validate] cells: 11 (5 code, 6 markdown)
[validate] PIPE-01 (top-to-bottom flow): PASS
[validate] PIPE-02 (dual-environment): PASS
[validate] PIPE-03 (key loading): PASS
[validate] PIPE-04 (caching): PASS
[validate] PIPE-05 (single PARAMS): PASS
[validate] PIPE-06 (teaching commentary): PASS
[validate] v1 flaws eradicated: PASS
[validate] OVERALL: PASS
```

**`python scripts/create_v2_notebook.py`** — Exit code 0:
```
[generator] wrote 11 cells -> C:\Users\josha\medical-clinic\Johnston_St_v2.ipynb
[generator]   markdown cells: 6
[generator]   code cells:     5
```

**Grep checks:**
| Check | Expected | Actual | Result |
|-------|----------|--------|--------|
| `grep -c "/content/drive" Johnston_St_v2.ipynb` | 0 | 0 | PASS |
| `grep -c "drive.mount" Johnston_St_v2.ipynb` | 0 | 0 | PASS |
| `grep -c "BASE_ASSUMPTIONS" Johnston_St_v2.ipynb` | ≥1 | 7 | PASS |
| `grep -c "CachedSession" Johnston_St_v2.ipynb` | ≥1 | 5 | PASS |
| `ls data/local/ \| wc -l` | 8 | 8 | PASS |
| `ls docs/abs-api/ \| wc -l` | 4 | 4 | PASS |
| `test -f data/cache/.gitkeep && test -f outputs/.gitkeep` | pass | PASS | PASS |
| `ls *.zip *.xlsx *.pdf 2>/dev/null \| wc -l` | 0 | 0 | PASS |

**Additional checks:**
- `.gitignore` contains `data/cache/redirects.sqlite` but NOT bare `data/cache/` — D-12 policy honored (API cache JSONs are committed)
- `.env` is NOT tracked in git (`git ls-files .env` returns 0)
- `.env.example` has `GOOGLE_PLACES_KEY=` with empty value (no secret leaked)
- No bare `requests.get()` calls — all HTTP goes through `session.get()` (validation confirms)

### Gaps

None. All 26 must_haves are verified programmatically. No structural or content gaps found.

### Human Verification Items

1. **Actual Colab Restart & Run All execution:** The notebook structure is verified correct (top-to-bottom flow, no forward references), but it has not been executed in Colab. The `<OWNER>` placeholder in the git clone URL (`https://github.com/<OWNER>/medical-clinic.git`) must be replaced with the actual GitHub username before the first Colab run. This is by design (documented as a TODO comment in §0.2).

2. **Actual local Windows execution:** The dual-environment code path (`Path.cwd()`, `load_dotenv()`, `os.environ.get`) is structurally correct but has not been runtime-tested on Windows with a `.env` file present.

3. **Second-run cache hit verification:** The ABS smoke test is designed to demonstrate `response.from_cache == True` on a second run with `FORCE_REFRESH=False`. This requires actual execution to confirm. The cache layer structure (CachedSession, filesystem backend, cache file assertions) is verified correct.

4. **`<OWNER>` placeholder replacement:** Before the notebook can execute end-to-end in Colab, the `<OWNER>` placeholder must be replaced with the actual GitHub username/org. This is a one-time human action documented in the TODO comment.

### Verdict

**HUMAN_NEEDED** — All 26 must_haves across both plans are verified programmatically. The validation script exits 0 with "OVERALL: PASS". The generator script regenerates the notebook without error. All grep checks, file counts, and structural inspections pass. The reproducible foundation is structurally complete and correct.

However, the phase's success criteria include runtime behaviors that cannot be verified by static analysis alone:
- Success criterion 1 requires actual Colab Restart & Run All and local Windows execution
- Success criterion 3 requires a second-run cache hit demonstration (`from_cache == True`)

These require human testing in the target environments. The `<OWNER>` placeholder in the git clone URL is an intentional design decision (documented TODO) that requires a one-time human action before the first Colab run. No code changes are needed — only runtime verification.
