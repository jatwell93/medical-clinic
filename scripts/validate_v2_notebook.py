#!/usr/bin/env python3
"""
Validation script for Johnston_St_v2.ipynb.

Checks structural validity, content requirements (PIPE-01 through PIPE-06),
and v1 flaw eradication. Exits 0 with "OVERALL: PASS" if all checks pass,
exits 1 with failure details if any check fails.

Run:  python scripts/validate_v2_notebook.py
"""

import json
import re
import sys
from pathlib import Path


def main():
    notebook_path = Path(__file__).resolve().parent.parent / "Johnston_St_v2.ipynb"
    failures = []
    passes = []

    # ──────────────────────────────────────────────────────────────
    # 1. Structural validity
    # ──────────────────────────────────────────────────────────────

    # 1a. json.load succeeds
    try:
        nb = json.load(open(notebook_path, encoding="utf-8"))
        passes.append("json.load succeeds")
    except Exception as e:
        print(f"[validate] FAIL: json.load failed: {e}")
        failures.append("json.load failed")
        return report(failures, passes)

    # 1b. nbformat == 4
    if nb.get("nbformat") == 4:
        passes.append("nbformat == 4")
    else:
        failures.append(f"nbformat != 4 (got {nb.get('nbformat')})")

    cells = nb.get("cells", [])

    # 1c. Every code cell has execution_count: null and outputs: []
    code_cells = [c for c in cells if c.get("cell_type") == "code"]
    for i, c in enumerate(code_cells):
        if c.get("execution_count") is not None:
            failures.append(f"code cell {i} has execution_count != null")
        if c.get("outputs") != []:
            failures.append(f"code cell {i} has outputs != []")
    if not any("execution_count" in f for f in failures) and not any("outputs" in f for f in failures):
        passes.append("all code cells have execution_count=null, outputs=[]")

    # 1d. Every cell has source as a list of strings
    for i, c in enumerate(cells):
        src = c.get("source")
        if not isinstance(src, list):
            failures.append(f"cell {i} source is not a list")
        elif not all(isinstance(s, str) for s in src):
            failures.append(f"cell {i} source contains non-string elements")
    if not any("source is not a list" in f for f in failures) and not any("non-string" in f for f in failures):
        passes.append("all cells have source as list of strings")

    # 1e. metadata.kernelspec.name == 'python3'
    kernelspec = nb.get("metadata", {}).get("kernelspec", {})
    if kernelspec.get("name") == "python3":
        passes.append("kernelspec.name == python3")
    else:
        failures.append(f"kernelspec.name != python3 (got {kernelspec.get('name')})")

    # ──────────────────────────────────────────────────────────────
    # 2. Content requirements (PIPE-01 through PIPE-06)
    # ──────────────────────────────────────────────────────────────

    # Build combined source per cell and overall
    cell_sources = ["".join(c.get("source", [])) for c in cells]
    all_source = "\n".join(cell_sources)

    # PIPE-01 (Restart & Run All): cells flow top-to-bottom with no forward references
    # Check: PROJECT_ROOT defined before CACHE_DIR; BASE_ASSUMPTIONS defined before any downstream use
    # Find the cell index where each variable is first defined
    def first_def_cell(varname):
        for i, src in enumerate(cell_sources):
            # Look for assignment pattern (not just mention)
            if re.search(rf'^\s*{re.escape(varname)}\s*=', src, re.MULTILINE):
                return i
        return None

    project_root_cell = first_def_cell("PROJECT_ROOT")
    cache_dir_cell = first_def_cell("CACHE_DIR")
    base_assumptions_cell = first_def_cell("BASE_ASSUMPTIONS")
    session_cell = first_def_cell("session")
    force_refresh_cell = first_def_cell("FORCE_REFRESH")

    pipe01_ok = True
    if project_root_cell is not None and cache_dir_cell is not None:
        if cache_dir_cell < project_root_cell:
            pipe01_ok = False
            failures.append("PIPE-01: CACHE_DIR defined before PROJECT_ROOT")
    else:
        # If either is missing, that's a different failure
        if project_root_cell is None:
            failures.append("PIPE-01: PROJECT_ROOT not defined")
            pipe01_ok = False
        if cache_dir_cell is None:
            failures.append("PIPE-01: CACHE_DIR not defined")
            pipe01_ok = False

    # FORCE_REFRESH should be defined before session (session uses FORCE_REFRESH)
    if force_refresh_cell is not None and session_cell is not None:
        if session_cell < force_refresh_cell:
            pipe01_ok = False
            failures.append("PIPE-01: session defined before FORCE_REFRESH")
    if pipe01_ok:
        passes.append("PIPE-01 (top-to-bottom flow): PASS")
    else:
        print(f"[validate] PIPE-01 (top-to-bottom flow): FAIL")

    # PIPE-02 (dual-environment): IN_COLAB detection; PROJECT_ROOT resolved differently
    pipe02_ok = (
        "IN_COLAB" in all_source
        and "google.colab" in all_source
        and "Path.cwd()" in all_source
    )
    if pipe02_ok:
        passes.append("PIPE-02 (dual-environment): PASS")
    else:
        failures.append("PIPE-02: missing IN_COLAB detection or dual PROJECT_ROOT resolution")
        print(f"[validate] PIPE-02 (dual-environment): FAIL")

    # PIPE-03 (key loading): userdata.get in Colab branch; load_dotenv + os.environ.get in local
    pipe03_ok = (
        'userdata.get("GOOGLE_PLACES_KEY")' in all_source
        and "load_dotenv()" in all_source
        and 'os.environ.get("GOOGLE_PLACES_KEY"' in all_source
    )
    if pipe03_ok:
        passes.append("PIPE-03 (key loading): PASS")
    else:
        failures.append("PIPE-03: missing dual key loading pattern")
        print(f"[validate] PIPE-03 (key loading): FAIL")

    # PIPE-04 (caching): CachedSession with allowable_methods=('GET', 'POST'); ABS smoke test via session.get
    pipe04_ok = (
        "CachedSession" in all_source
        and "allowable_methods=('GET', 'POST')" in all_source
        and "session.get(" in all_source
        and "dataflow?detail=allstubs" in all_source
    )
    if pipe04_ok:
        passes.append("PIPE-04 (caching): PASS")
    else:
        failures.append("PIPE-04: missing CachedSession or ABS smoke test")
        print(f"[validate] PIPE-04 (caching): FAIL")

    # PIPE-05 (single PARAMS cell): BASE_ASSUMPTIONS dict present with citation comments; FORCE_REFRESH flag
    pipe05_ok = (
        "BASE_ASSUMPTIONS" in all_source
        and "FORCE_REFRESH" in all_source
        and "# UNCONFIRMED" in all_source  # citation/flag comments present
    )
    if pipe05_ok:
        passes.append("PIPE-05 (single PARAMS): PASS")
    else:
        failures.append("PIPE-05: missing BASE_ASSUMPTIONS or citation comments or FORCE_REFRESH")
        print(f"[validate] PIPE-05 (single PARAMS): FAIL")

    # PIPE-06 (teaching commentary): >=4 markdown cells with section headers
    md_cells = [c for c in cells if c.get("cell_type") == "markdown"]
    md_source = ["".join(c.get("source", [])) for c in md_cells]
    section_headers = 0
    for src in md_source:
        if any(h in src for h in ["§0", "§1", "§0.2", "§0.3", "§1.2"]):
            section_headers += 1
    pipe06_ok = len(md_cells) >= 4 and section_headers >= 4
    if pipe06_ok:
        passes.append("PIPE-06 (teaching commentary): PASS")
    else:
        failures.append(f"PIPE-06: only {len(md_cells)} markdown cells, {section_headers} section headers")
        print(f"[validate] PIPE-06 (teaching commentary): FAIL")

    # ──────────────────────────────────────────────────────────────
    # 3. v1 flaw eradication (RESEARCH.md §8)
    # ──────────────────────────────────────────────────────────────

    v1_ok = True

    # Zero occurrences of /content/drive in any cell source
    if "/content/drive" in all_source:
        v1_ok = False
        failures.append("v1 flaw: /content/drive found in notebook")

    # Zero occurrences of drive.mount in any cell source
    if "drive.mount" in all_source:
        v1_ok = False
        failures.append("v1 flaw: drive.mount found in notebook")

    # Zero occurrences of bare requests.get (all HTTP through cached session)
    # Check: no 'requests.get(' calls that aren't part of 'session.get('
    # We look for 'requests.get(' specifically — session.get is fine
    bare_requests_get = re.findall(r'(?<!session\.)requests\.get\(', all_source)
    # Also check that 'requests.get(' doesn't appear as a standalone call
    # (the import line 'import ... requests' is fine, only calls matter)
    for match in re.finditer(r'requests\.get\(', all_source):
        # Check if this is preceded by 'session.' on the same logical line
        start = match.start()
        # Look backwards for 'session.' or newline
        line_start = all_source.rfind('\n', 0, start) + 1
        prefix = all_source[line_start:start]
        if 'session.' not in prefix:
            v1_ok = False
            failures.append("v1 flaw: bare requests.get() call found (not through CachedSession)")
            break

    if v1_ok:
        passes.append("v1 flaws eradicated: PASS")
    else:
        print(f"[validate] v1 flaws eradicated: FAIL")

    # ──────────────────────────────────────────────────────────────
    # 4. Summary report
    # ──────────────────────────────────────────────────────────────

    return report(failures, passes, cells, code_cells, md_cells)


def report(failures, passes, cells=None, code_cells=None, md_cells=None):
    """Print the summary report and return exit code."""
    if cells is not None:
        n_cells = len(cells)
        n_code = len(code_cells) if code_cells else 0
        n_md = len(md_cells) if md_cells else 0
        print(f"[validate] cells: {n_cells} ({n_code} code, {n_md} markdown)")

    # Print PIPE results in order
    pipe_labels = {
        "PIPE-01": "PIPE-01 (top-to-bottom flow)",
        "PIPE-02": "PIPE-02 (dual-environment)",
        "PIPE-03": "PIPE-03 (key loading)",
        "PIPE-04": "PIPE-04 (caching)",
        "PIPE-05": "PIPE-05 (single PARAMS)",
        "PIPE-06": "PIPE-06 (teaching commentary)",
    }

    for key, label in pipe_labels.items():
        found_pass = any(label in p for p in passes)
        found_fail = any(key in f for f in failures)
        if found_pass:
            print(f"[validate] {label}: PASS")
        elif found_fail:
            print(f"[validate] {label}: FAIL")
        else:
            print(f"[validate] {label}: FAIL")

    # v1 flaws
    v1_pass = any("v1 flaws eradicated" in p for p in passes)
    print(f"[validate] v1 flaws eradicated: {'PASS' if v1_pass else 'FAIL'}")

    # Structural passes (not printed individually unless failed)
    for f in failures:
        if not any(k in f for k in ["PIPE-01", "PIPE-02", "PIPE-03", "PIPE-04", "PIPE-05", "PIPE-06", "v1 flaw"]):
            print(f"[validate] FAIL: {f}")

    overall = len(failures) == 0
    print(f"[validate] OVERALL: {'PASS' if overall else 'FAIL'}")

    if not overall:
        print(f"\n[validate] {len(failures)} failure(s):")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
