#!/usr/bin/env python3
"""
Validation script for Johnston_St_v2.ipynb.

Checks structural validity, content requirements (PIPE-01 through PIPE-06),
v1 flaw eradication, and Phase 2 catchment checks (GEO-01 through GEO-04 + D-06).
Exits 0 with "OVERALL: PASS" if all checks pass, exits 1 with failure details
if any check fails.

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
    # 4. Phase 2 — Catchment (GEO-01 through GEO-04 + D-06)
    # ──────────────────────────────────────────────────────────────

    phase2_failures = []
    phase2_passes = []

    def check_phase2(label, condition, fail_msg):
        if condition:
            phase2_passes.append(label)
        else:
            phase2_failures.append(fail_msg)
            print(f"[validate] {label}: FAIL")

    # GEO-01 (geocode)
    geo01 = (
        "geocode/json" in all_source
        and "session.get" in all_source
        and "geocode" in all_source
        and "visually verify" in all_source
    )
    check_phase2("Phase 2 GEO-01 (geocode)", geo01,
                 "GEO-01: missing geocode/json, session.get+geocode, or visually verify")

    # GEO-02 (buffers + assertion)
    geo02_to_crs = '.to_crs("EPSG:7855")' in all_source or ".to_crs('EPSG:7855')" in all_source
    geo02_assert = "assert_3km_buffer_km2" in all_source
    geo02_buffer = ".buffer(" in all_source
    geo02_epsg = "EPSG:7855" in all_source
    # No degree-based buffering: no .buffer( on the same line as EPSG:4326
    geo02_no_degree = True
    for src in cell_sources:
        for line in src.split("\n"):
            if ".buffer(" in line and "EPSG:4326" in line:
                geo02_no_degree = False
                phase2_failures.append("GEO-02: .buffer() on same line as EPSG:4326 (degree-based buffering)")
                break
    geo02 = geo02_to_crs and geo02_assert and geo02_buffer and geo02_epsg and geo02_no_degree
    check_phase2("Phase 2 GEO-02 (buffers + assertion)", geo02,
                 f"GEO-02: missing to_crs EPSG:7855 ({geo02_to_crs}), assert_3km_buffer_km2 ({geo02_assert}), .buffer( ({geo02_buffer}), EPSG:7855 ({geo02_epsg}), or degree-buffer check ({geo02_no_degree})")

    # GEO-03 (SA1 apportionment)
    geo03_overlay = 'overlay(' in all_source and 'how="intersection"' in all_source
    geo03_sa1 = "SA1_CODE21" in all_source
    geo03_frac = '"frac"' in all_source or "'frac'" in all_source or "frac" in all_source
    geo03_plausible = "catchment_pop_plausible_range" in all_source
    geo03 = geo03_overlay and geo03_sa1 and geo03_frac and geo03_plausible
    check_phase2("Phase 2 GEO-03 (SA1 apportionment)", geo03,
                 f"GEO-03: missing overlay+intersection ({geo03_overlay}), SA1_CODE21 ({geo03_sa1}), frac ({geo03_frac}), or catchment_pop_plausible_range ({geo03_plausible})")

    # GEO-04 (maps)
    geo04_folium = "folium.Map" in all_source
    geo04_contextily = "cx.add_basemap" in all_source
    geo04_carto = "CartoDB Positron" in all_source
    geo04_yarra = "Yarra" in all_source
    geo04 = geo04_folium and geo04_contextily and geo04_carto and geo04_yarra
    check_phase2("Phase 2 GEO-04 (maps)", geo04,
                 f"GEO-04: missing folium.Map ({geo04_folium}), cx.add_basemap ({geo04_contextily}), CartoDB Positron ({geo04_carto}), or Yarra ({geo04_yarra})")

    # D-06 (v1-vs-v2 comparison)
    d06 = "compare_v1_v2" in all_source
    check_phase2("Phase 2 D-06 (v1-vs-v2 comparison)", d06,
                 "D-06: missing compare_v1_v2 function")

    # Add Phase 2 passes/failures to the main lists
    passes.extend(phase2_passes)
    failures.extend(phase2_failures)

    # Phase 2 Demographics checks (DEMO-01..04 + D-03/D-06/D-09b/D-11)
    phase2_demog_failures = []
    phase2_demog_passes = []

    def check_demog(label, condition, fail_msg):
        if condition:
            phase2_demog_passes.append(label)
        else:
            phase2_demog_failures.append(fail_msg)
            print(f"[validate] {label}: FAIL")

    # DEMO-01 (ABS G01/G02 fetch + fallback)
    demo01_g01 = "C21_G01_POA" in all_source
    demo01_g02 = "C21_G02_POA" in all_source or "C21_G02" in all_source
    demo01_fallback = "GCP_POA3067" in all_source
    demo01_parser = "parse_gcp_g01_to_tidy" in all_source
    demo01 = demo01_g01 and demo01_g02 and demo01_fallback and demo01_parser
    check_demog("Phase 2 DEMO-01 (ABS G01/G02 + fallback)", demo01,
                f"DEMO-01: missing C21_G01_POA ({demo01_g01}), C21_G02 ({demo01_g02}), GCP_POA3067 ({demo01_fallback}), or parse_gcp_g01_to_tidy ({demo01_parser})")

    # DEMO-02 (peer comparison charts)
    demo02_subplots = "subplots(2, 2" in all_source
    demo02_site = "is_site" in all_source
    demo02 = demo02_subplots and demo02_site
    check_demog("Phase 2 DEMO-02 (peer comparison charts)", demo02,
                f"DEMO-02: missing subplots(2, 2 ({demo02_subplots}) or is_site ({demo02_site})")

    # DEMO-03 (peer benchmarking table)
    demo03_gp = "gp_count" in all_source and "pharmacy_count" in all_source
    demo03_pop = "Total_P_P" in all_source
    demo03_age = "Median_age_persons" in all_source
    demo03_65 = "pct_65plus" in all_source
    demo03 = demo03_gp and demo03_pop and demo03_age and demo03_65
    check_demog("Phase 2 DEMO-03 (peer benchmarking table)", demo03,
                f"DEMO-03: missing gp_count+pharmacy_count ({demo03_gp}), Total_P_P ({demo03_pop}), Median_age_persons ({demo03_age}), or pct_65plus ({demo03_65})")

    # DEMO-04 (ERP scaling)
    demo04_erp = "ABS_ANNUAL_ERP_ASGS2021" in all_source
    demo04_rate = "erp_growth_rate" in all_source
    demo04_col = "Total_P_P_erp" in all_source
    demo04_caveat = "Caveat" in all_source and "ERP" in all_source
    demo04 = demo04_erp and demo04_rate and demo04_col and demo04_caveat
    check_demog("Phase 2 DEMO-04 (ERP scaling)", demo04,
                f"DEMO-04: missing ABS_ANNUAL_ERP_ASGS2021 ({demo04_erp}), erp_growth_rate ({demo04_rate}), Total_P_P_erp ({demo04_col}), or Caveat+ERP ({demo04_caveat})")

    # D-11 (G04 runtime verification)
    d11 = "C21_G04_POA" in all_source and "check_dataflow_exists" in all_source
    check_demog("Phase 2 D-11 (G04 runtime verify)", d11,
                f"D-11: missing C21_G04_POA ({'C21_G04_POA' in all_source}) or check_dataflow_exists ({'check_dataflow_exists' in all_source})")

    # D-03 (SA1 total persons)
    d03_flow = "C21_G01_SA1" in all_source
    d03_df = "sa1_pop_df" in all_source
    d03 = d03_flow and d03_df
    check_demog("Phase 2 D-03 (SA1 total persons)", d03,
                f"D-03: missing C21_G01_SA1 ({d03_flow}) or sa1_pop_df ({d03_df})")

    # D-06 completion (v1-vs-v2 with real totals) — strengthened (IR-02 fix)
    d06_call = "compare_v1_v2(" in all_source
    d06_totals = "v2_ring_pops" in all_source
    d06_v1_totals = "v1_ring_pops" in all_source
    d06_stub_present = "v1_pop = v2_pop" in all_source  # CR-02 stub — must be ABSENT
    d06_done = d06_call and d06_totals and d06_v1_totals and not d06_stub_present
    check_demog("Phase 2 D-06 (v1-vs-v2 with real totals)", d06_done,
                f"D-06: missing compare_v1_v2( call ({d06_call}), v2_ring_pops ({d06_totals}), "
                f"v1_ring_pops ({d06_v1_totals}), or CR-02 stub present ({d06_stub_present})")

    # CR-01 fix (check_dataflow_exists must not call .json() on XML endpoint)
    cr01_json_on_xml = "flows_resp.json()" in all_source
    cr01_xml_parse = "xml.etree.ElementTree" in all_source or "ET.fromstring" in all_source
    cr01_safe_default = "return True" in all_source
    cr01_fixed = not cr01_json_on_xml and (cr01_xml_parse or cr01_safe_default)
    check_demog("Phase 2 CR-01 (check_dataflow_exists XML-safe)", cr01_fixed,
                f"CR-01: flows_resp.json() present ({cr01_json_on_xml}), XML parse ({cr01_xml_parse}), safe default ({cr01_safe_default})")

    # D-09b (catchment pop plausibility assertion)
    d09b = "catchment_pop_plausible_range" in all_source and "assert" in all_source
    check_demog("Phase 2 D-09b (pop plausibility assert)", d09b,
                f"D-09b: missing catchment_pop_plausible_range ({'catchment_pop_plausible_range' in all_source}) or assert")

    passes.extend(phase2_demog_passes)
    failures.extend(phase2_demog_failures)

    # ──────────────────────────────────────────────────────────────
    # 6. Phase 3 — Competitors (COMP-01..03 + DEMAND-04)
    # ──────────────────────────────────────────────────────────────

    phase3_failures = []
    phase3_passes = []

    def check_phase3(label, condition, fail_msg):
        if condition:
            phase3_passes.append(label)
        else:
            phase3_failures.append(fail_msg)
            print(f"[validate] {label}: FAIL")

    # COMP-01 (Places API New with saturation + dedupe)
    comp01_url = "places.googleapis.com/v1/places:searchNearby" in all_source
    comp01_fieldmask = "X-Goog-FieldMask" in all_source
    comp01_saturated = "places_nearby_saturated" in all_source
    comp01_dedupe = "place.id" in all_source or "place_id" in all_source
    comp01_no_rating = "places.rating" not in all_source and "places.userRatingCount" not in all_source
    comp01 = comp01_url and comp01_fieldmask and comp01_saturated and comp01_dedupe and comp01_no_rating
    check_phase3("Phase 3 COMP-01 (Places API New + saturation + dedupe)", comp01,
                 f"COMP-01: missing Places URL ({comp01_url}), field mask ({comp01_fieldmask}), "
                 f"saturation ({comp01_saturated}), dedupe ({comp01_dedupe}), or no-rating ({comp01_no_rating})")

    # COMP-02 (pharmacy brand classification + clinic-vs-practitioner filtering)
    comp02_pharmacy = "PHARMACY_BRANDS" in all_source and "chemist warehouse" in all_source.lower()
    comp02_classify = "classify_place" in all_source
    comp02_fuzzy = "fuzzy_dedupe_competitors" in all_source and "rapidfuzz" in all_source
    comp02_no_fuzzywuzzy = "fuzzywuzzy" not in all_source
    comp02 = comp02_pharmacy and comp02_classify and comp02_fuzzy and comp02_no_fuzzywuzzy
    check_phase3("Phase 3 COMP-02 (classification + fuzzy dedupe)", comp02,
                 f"COMP-02: missing PHARMACY_BRANDS+chemist warehouse ({comp02_pharmacy}), "
                 f"classify_place ({comp02_classify}), rapidfuzz dedupe ({comp02_fuzzy}), "
                 f"or no-fuzzywuzzy ({comp02_no_fuzzywuzzy})")

    # COMP-03 (competitor inventory table + map layers + GP-per-1,000 benchmark)
    comp03_geojson = "competitors.geojson" in all_source
    comp03_folium = "folium.FeatureGroup" in all_source and "folium.LayerControl" in all_source
    comp03_static = "cx.add_basemap" in all_source
    comp03_ratio = "gp_per_1000" in all_source or "GP-per-1,000" in all_source or "gp_per_1k" in all_source
    comp03_benchmark = "117" in all_source
    comp03 = comp03_geojson and comp03_folium and comp03_static and comp03_ratio and comp03_benchmark
    check_phase3("Phase 3 COMP-03 (GeoJSON + maps + GP-per-1000 benchmark)", comp03,
                 f"COMP-03: missing GeoJSON ({comp03_geojson}), folium layers ({comp03_folium}), "
                 f"contextily ({comp03_static}), GP-per-1000 ({comp03_ratio}), or 117 benchmark ({comp03_benchmark})")

    # DEMAND-04 (no ML — negative assertion)
    demand04_no_sklearn = "sklearn" not in all_source and "scikit-learn" not in all_source
    demand04 = demand04_no_sklearn
    check_phase3("Phase 3 DEMAND-04 (no ML / no sklearn)", demand04,
                 f"DEMAND-04: sklearn or scikit-learn found in notebook ({not demand04_no_sklearn})")

    passes.extend(phase3_passes)
    failures.extend(phase3_failures)

    # ──────────────────────────────────────────────────────────────
    # 5. Summary report
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

    # Phase 2 checks
    phase2_labels = [
        "Phase 2 GEO-01 (geocode)",
        "Phase 2 GEO-02 (buffers + assertion)",
        "Phase 2 GEO-03 (SA1 apportionment)",
        "Phase 2 GEO-04 (maps)",
        "Phase 2 D-06 (v1-vs-v2 comparison)",
        "Phase 2 DEMO-01 (ABS G01/G02 + fallback)",
        "Phase 2 DEMO-02 (peer comparison charts)",
        "Phase 2 DEMO-03 (peer benchmarking table)",
        "Phase 2 DEMO-04 (ERP scaling)",
        "Phase 2 D-11 (G04 runtime verify)",
        "Phase 2 D-03 (SA1 total persons)",
        "Phase 2 D-06 (v1-vs-v2 with real totals)",
        "Phase 2 CR-01 (check_dataflow_exists XML-safe)",
        "Phase 2 D-09b (pop plausibility assert)",
    ]
    for label in phase2_labels:
        found_pass = any(label in p for p in passes)
        found_fail = any(label in f for f in failures)
        if found_pass:
            print(f"[validate] {label}: PASS")
        elif found_fail:
            print(f"[validate] {label}: FAIL")
        else:
            print(f"[validate] {label}: FAIL")

    # Phase 3 checks
    phase3_labels = [
        "Phase 3 COMP-01 (Places API New + saturation + dedupe)",
        "Phase 3 COMP-02 (classification + fuzzy dedupe)",
        "Phase 3 COMP-03 (GeoJSON + maps + GP-per-1000 benchmark)",
        "Phase 3 DEMAND-04 (no ML / no sklearn)",
    ]
    for label in phase3_labels:
        found_pass = any(label in p for p in passes)
        found_fail = any(label in f for f in failures)
        if found_pass:
            print(f"[validate] {label}: PASS")
        elif found_fail:
            print(f"[validate] {label}: FAIL")
        else:
            print(f"[validate] {label}: FAIL")

    # Structural passes (not printed individually unless failed)
    for f in failures:
        if not any(k in f for k in ["PIPE-01", "PIPE-02", "PIPE-03", "PIPE-04", "PIPE-05", "PIPE-06", "v1 flaw", "GEO-01", "GEO-02", "GEO-03", "GEO-04", "D-06", "CR-01", "DEMO-01", "DEMO-02", "DEMO-03", "DEMO-04", "D-11", "D-03", "D-09b", "COMP-01", "COMP-02", "COMP-03", "DEMAND-04"]):
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
