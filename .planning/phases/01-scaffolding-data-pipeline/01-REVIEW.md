---
status: issues
phase: 01-scaffolding-data-pipeline
depth: standard
files_reviewed: 5
findings:
  critical: 0
  warning: 3
  info: 4
  total: 7
reviewed_at: 2026-07-05T08:55:20Z
---

# Phase 01 Review — Scaffolding & Data Pipeline

## scripts/create_v2_notebook.py

**WR-001** — `json.dump(nb, f, indent=1)` uses the default `ensure_ascii=True`, producing `\u00a7` Unicode escapes for the § character in the output notebook JSON (visible in `Johnston_St_v2.ipynb` lines 20, 47, 68, etc.). This is valid JSON and renders correctly in Jupyter, but makes the raw `.ipynb` file harder to read/diff. Consider adding `ensure_ascii=False` for human-readable UTF-8 output. The notebook is committed to git, so readable diffs matter.

**IN-001** — No error handling around the file write (lines 364–365). If the output path is not writable, the script raises an unhandled exception. Acceptable for a generator script, but a try/except with a clear error message would improve UX.

**IN-002** — The `cells` list is built at module level (line 61). If this module were ever imported (not just run as `__main__`), the list would accumulate on re-import. Not a problem for script execution, but wrapping cell construction in a `build_notebook()` function would be cleaner and testable.

**Idempotency:** The script overwrites the output file on each run with the same content. Idempotent. ✓

**JSON generation correctness:** Cell dicts match the nbformat 4 schema (`cell_type`, `metadata`, `source` for markdown; adds `execution_count`, `outputs` for code). The `lines()` helper correctly appends `\n` to all but the last element. ✓

---

## scripts/validate_v2_notebook.py

**WR-002** — Line 29: `json.load(open(notebook_path, encoding="utf-8"))` opens a file without a `with` statement or explicit `.close()`. The file handle is never closed (relies on GC). Use `with open(...) as f:` to guarantee cleanup.

**WR-003** — Line 201: `bare_requests_get = re.findall(...)` is computed but **never used**. The actual bare-`requests.get` check is the `re.finditer` loop on lines 204–213. This is dead code that may confuse future maintainers into thinking the findall result is used for validation. Remove line 201.

**IN-003** — PIPE-01 ordering check operates at cell granularity only. If `CACHE_DIR` were defined before `PROJECT_ROOT` *within the same cell*, the validator would not catch it (both would return the same cell index, and the `<` check would be False). This is an inherent limitation of cell-level analysis and acceptable for this phase, but documenting it would prevent false confidence.

**Exit code handling:** `sys.exit(1)` on failure, `sys.exit(0)` on success. The early-return path (line 34, JSON parse failure) correctly delegates to `report()` which calls `sys.exit(1)`. ✓

**False-positive/negative risk:** The `first_def_cell` regex `^\s*{varname}\s*=` correctly avoids matching comments (the `#` prefix is not whitespace, so `^\s*session` won't match `# session =`). The bare-`requests.get` check (lines 204–213) checks for `session.` in the line prefix, which is reasonable. A theoretical false positive exists if `requests.get(` appeared in a string literal or comment, but no such case exists in this notebook. ✓

---

## Johnston_St_v2.ipynb

**WR-004** — Cell §0.2 (notebook line 101): the git clone URL contains a literal `<OWNER>` placeholder: `https://github.com/<OWNER>/medical-clinic.git`. This is marked `# TODO: replace <OWNER>` but if the notebook is run in Colab as-is, `subprocess.run(..., check=True)` will fail with a git error (repository not found), breaking the entire Colab execution path. This must be replaced with the actual GitHub username before the notebook is runnable in Colab. Until then, the "Restart & Run All in Colab" claim (PIPE-01/PIPE-02) does not hold.

**IN-004** — Cell §0.1 (notebook line 50): `import os, sys, json, requests` — the `json` and `requests` modules are imported but not used in any phase-01 cell. `response.json()` is a method call, not the `json` module. These imports are likely pre-emptive for later phases, but unused imports in a teaching notebook may confuse students.

**Security (API key handling):** The key is loaded from Colab Secrets (`userdata.get`) or local `.env` (`os.environ.get`) and is never printed in full — only `'loaded'` or `'empty (cache-only mode)'` is shown. No key appears in any cell source or output. ✓

**v1 flaw eradication:** No `/content/drive` paths, no `drive.mount` calls, no bare `requests.get()` calls. All HTTP goes through `session.get()`. `PROJECT_ROOT`-relative `pathlib.Path`s replace hardcoded Drive paths. ✓

**Hardcoded paths:** `/content/medical-clinic` (Colab clone target) is the only hardcoded path and is intentional per D-06. `Path.cwd()` is used for local `PROJECT_ROOT` — assumes the notebook is run from the repo root, which is documented in the comment `# Notebooks don't have __file__`. Acceptable. ✓

**Code cell correctness:** The `assert CACHE_DIR.exists() or GOOGLE_PLACES_KEY` guard (line 119) correctly enforces that a fresh clone needs either committed cache files or a key. The `CachedSession` construction with `allowable_methods=('GET', 'POST')` and `expire_after=-1` matches the STACK.md requirements. The smoke test validates both response structure and cache file creation. ✓

---

## .gitignore

No issues found. Policy is correct:

- `.env` ignored (D-15 secrets). ✓
- `data/cache/redirects.sqlite` ignored (regenerable metadata). ✓
- `data/cache/*.json` **NOT** ignored — cache response files are committed per D-12. ✓
- `data/local/` ignored (D-13 large fallback files). ✓
- `outputs/` ignored (regenerated on run). ✓
- `.ipynb_checkpoints/`, `__pycache__/`, `*.pyc`, OS files ignored. ✓

---

## .env.example

No issues found.

- Key name `GOOGLE_PLACES_KEY` matches the notebook's `os.environ.get("GOOGLE_PLACES_KEY", "")` and Colab Secrets `userdata.get("GOOGLE_PLACES_KEY")`. ✓
- Value is empty (`GOOGLE_PLACES_KEY=`) — no real secrets present. ✓
- Helpful comments point to Colab Secrets and the Google Cloud console. ✓

---

## Summary

| Severity | Count | IDs |
|----------|-------|-----|
| Critical | 0 | — |
| Warning | 3 | WR-001, WR-002, WR-003 |
| Info | 4 | IN-001, IN-002, IN-003, IN-004 |

**Overall assessment:** No critical bugs or security issues. The phase-01 scaffolding is structurally sound and the validation script provides meaningful coverage. The most actionable item is **WR-004** — the `<OWNER>` placeholder must be replaced before the notebook can actually run in Colab. The remaining warnings are code-quality issues (resource leak, dead code, Unicode escapes) that should be addressed but do not block progress.
