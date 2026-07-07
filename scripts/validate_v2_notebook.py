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

    # DEMAND-04 (no ML — strengthened negative assertion)
    demand04_no_sklearn = "sklearn" not in all_source and "scikit-learn" not in all_source
    demand04_no_rf = "RandomForest" not in all_source and "random_forest" not in all_source
    demand04 = demand04_no_sklearn and demand04_no_rf
    check_phase3("Phase 3 DEMAND-04 (no ML / no sklearn / no RandomForest)", demand04,
                 f"DEMAND-04: sklearn or scikit-learn found ({not demand04_no_sklearn}), "
                 f"RandomForest or random_forest found ({not demand04_no_rf})")

    # DEMAND-01 (SA3 MBS data acquired + state fallback warning)
    demand01_sa3 = "load_mbs_sa3" in all_source and "20607" in all_source
    demand01_fallback = "STATE BENCHMARK, NOT LOCAL" in all_source
    demand01 = demand01_sa3 and demand01_fallback
    check_phase3("Phase 3 DEMAND-01 (SA3 MBS + state fallback warning)", demand01,
                 f"DEMAND-01: missing load_mbs_sa3+20607 ({demand01_sa3}) or state fallback warning ({demand01_fallback})")

    # DEMAND-02 (age-adjusted demand per ring with AIHW 4 bands)
    demand02_compute = "compute_demand" in all_source
    demand02_aggregate = "aggregate_age_bands" in all_source
    demand02_bands = "0-24" in all_source and "25-44" in all_source and "45-64" in all_source and "65+" in all_source
    demand02 = demand02_compute and demand02_aggregate and demand02_bands
    check_phase3("Phase 3 DEMAND-02 (age-adjusted demand + AIHW 4 bands)", demand02,
                 f"DEMAND-02: missing compute_demand ({demand02_compute}), aggregate_age_bands ({demand02_aggregate}), "
                 f"or AIHW 4 bands ({demand02_bands})")

    # DEMAND-03 (demand vs capacity + required market share + plain language)
    demand03_capacity = "estimate_gp_capacity_range" in all_source
    demand03_marketshare = "compute_required_market_share" in all_source
    demand03_three = "share_of_total" in all_source and "share_of_unmet" in all_source and "share_of_pop" in all_source
    demand03_interpretation = "label_market_share" in all_source and ("PLAIN LANGUAGE" in all_source or "plain language" in all_source)
    demand03_no_verdict = "Phase 5" in all_source  # verdict deferred to Phase 5
    demand03 = demand03_capacity and demand03_marketshare and demand03_three and demand03_interpretation and demand03_no_verdict
    check_phase3("Phase 3 DEMAND-03 (capacity range + market share + interpretation)", demand03,
                 f"DEMAND-03: missing capacity range ({demand03_capacity}), market share ({demand03_marketshare}), "
                 f"three framings ({demand03_three}), interpretation ({demand03_interpretation}), or Phase 5 deferral ({demand03_no_verdict})")

    passes.extend(phase3_passes)
    failures.extend(phase3_failures)

    # ──────────────────────────────────────────────────────────────
    # 6. Phase 5 checks (FIN-04..07, REP-01..04)
    # ──────────────────────────────────────────────────────────────

    phase5_failures = []
    phase5_passes = []

    def check_phase5(label, condition, fail_msg):
        if condition:
            phase5_passes.append(label)
        else:
            phase5_failures.append(fail_msg)
            print(f"[validate] {label}: FAIL")

    # Helper: find cell index containing a marker string
    def cell_index_containing(marker):
        for i, src in enumerate(cell_sources):
            if marker in src:
                return i
        return None

    # FIN-04 (§7.1 scenario override dicts — 3 scenarios, 5 levers, {**BASE, **overrides})
    fin04_cell_idx = cell_index_containing("§7.1")
    fin04_cell_present = fin04_cell_idx is not None
    fin04_scenarios = (
        fin04_cell_present
        and '"base"' in cell_sources[fin04_cell_idx]
        and '"optimistic"' in cell_sources[fin04_cell_idx]
        and '"pessimistic"' in cell_sources[fin04_cell_idx]
    )
    fin04_levers = (
        fin04_cell_present
        and "rent_yr" in cell_sources[fin04_cell_idx]
        and "utilisation" in cell_sources[fin04_cell_idx]
        and "gp_revenue_share" in cell_sources[fin04_cell_idx]
        and "gp_ramp_milestones" in cell_sources[fin04_cell_idx]
        and "bulk_bill_share" in cell_sources[fin04_cell_idx]
    )
    fin04_override_pattern = "{**BASE_ASSUMPTIONS, **overrides}" in all_source
    fin04 = fin04_cell_present and fin04_scenarios and fin04_levers and fin04_override_pattern
    check_phase5("Phase 5 FIN-04 (scenario override dicts)", fin04,
                 f"FIN-04: missing §7.1 cell ({fin04_cell_present}), 3 scenarios ({fin04_scenarios}), "
                 f"5 levers ({fin04_levers}), or {{**BASE_ASSUMPTIONS, **overrides}} pattern ({fin04_override_pattern})")

    # FIN-05 (§7.3 + §7.4 tornado cells — 8 EBITDA inputs, 6 peak inputs, find_zero_crossing, np.linspace/np.interp, PNG saves)
    fin05_ebitda_cell = cell_index_containing("§7.3") is not None
    fin05_peak_cell = cell_index_containing("§7.4") is not None
    fin05_ebitda_count = all_source.count("tornado_inputs_ebitda") > 0 and len(re.findall(r'\(".*?",\s*[\d_]+', all_source)) >= 8
    # Count tuples in tornado_inputs_ebitda list by finding the list block
    fin05_ebitda_8 = False
    fin05_peak_6 = False
    for i, src in enumerate(cell_sources):
        if "tornado_inputs_ebitda = [" in src:
            # Count tuple entries (lines with parenthesised 5-tuples)
            tuple_count = len(re.findall(r'\("[^"]+",\s*[\d_.]+,\s*[\d_.]+,\s*[\d_.]+,\s*"[^"]+"\)', src))
            fin05_ebitda_8 = tuple_count >= 8
        if "tornado_inputs_peak = [" in src:
            tuple_count_peak = len(re.findall(r'\("[^"]+",\s*[\d_.]+,\s*[\d_.]+,\s*[\d_.]+,\s*(?:"[^"]+"|None)\)', src))
            fin05_peak_6 = tuple_count_peak >= 6
    fin05_zero_crossing = "find_zero_crossing" in all_source
    fin05_linspace = "np.linspace" in all_source
    fin05_interp = "np.interp" in all_source
    fin05_png_ebitda = "tornado_ebitda.png" in all_source
    fin05_png_peak = "tornado_peak_capital.png" in all_source
    fin05 = (
        fin05_ebitda_cell and fin05_peak_cell and fin05_ebitda_8 and fin05_peak_6
        and fin05_zero_crossing and fin05_linspace and fin05_interp
        and fin05_png_ebitda and fin05_png_peak
    )
    check_phase5("Phase 5 FIN-05 (tornado sensitivity + zero-crossings)", fin05,
                 f"FIN-05: missing §7.3 cell ({fin05_ebitda_cell}), §7.4 cell ({fin05_peak_cell}), "
                 f"8 EBITDA inputs ({fin05_ebitda_8}), 6 peak inputs ({fin05_peak_6}), "
                 f"find_zero_crossing ({fin05_zero_crossing}), np.linspace ({fin05_linspace}), "
                 f"np.interp ({fin05_interp}), tornado_ebitda.png ({fin05_png_ebitda}), "
                 f"tornado_peak_capital.png ({fin05_png_peak})")

    # FIN-06 (§7.5 billing-mix curve — 5 points, BBPIP 12.5%/6.25%, PNG save)
    fin06_cell_idx = cell_index_containing("§7.5")
    fin06_cell_present = fin06_cell_idx is not None
    fin06_5_points = (
        fin06_cell_present
        and "billing_mix_points" in cell_sources[fin06_cell_idx]
        and "0.0" in cell_sources[fin06_cell_idx]
        and "0.25" in cell_sources[fin06_cell_idx]
        and "0.50" in cell_sources[fin06_cell_idx]
        and "0.70" in cell_sources[fin06_cell_idx]
        and "1.00" in cell_sources[fin06_cell_idx]
    )
    fin06_bbpip = (
        fin06_cell_present
        and ("0.0625" in cell_sources[fin06_cell_idx] or "6.25%" in cell_sources[fin06_cell_idx])
        and ("12.5%" in cell_sources[fin06_cell_idx] or "0.125" in cell_sources[fin06_cell_idx] or "BBPIP" in cell_sources[fin06_cell_idx])
    )
    fin06_png = "billing_mix_curve.png" in all_source
    fin06 = fin06_cell_present and fin06_5_points and fin06_bbpip and fin06_png
    check_phase5("Phase 5 FIN-06 (billing-mix curve + BBPIP)", fin06,
                 f"FIN-06: missing §7.5 cell ({fin06_cell_present}), 5 points ({fin06_5_points}), "
                 f"BBPIP 12.5%/6.25% ({fin06_bbpip}), billing_mix_curve.png ({fin06_png})")

    # FIN-07 (§7.6 pharmacy synergy — order-gated after scenarios, NOT Load-Bearing, no clinic_pnl call)
    fin07_cell_idx = cell_index_containing("§7.6")
    fin07_cell_present = fin07_cell_idx is not None
    fin07_order_gated = (
        fin04_cell_idx is not None and fin07_cell_idx is not None
        and fin07_cell_idx > fin04_cell_idx
    )
    fin07_not_loadbearing = (
        fin07_cell_present
        and ("NOT Load-Bearing" in cell_sources[fin07_cell_idx] or "NOT load-bearing" in cell_sources[fin07_cell_idx])
    )
    # The §7.6 pharmacy synergy CODE cell should NOT call clinic_pnl() — standalone arithmetic only
    # Find the code cell containing "§7.6 Pharmacy synergy" (the code cell, not the markdown framing cell)
    fin07_code_cell_idx = None
    for i, src in enumerate(cell_sources):
        if "§7.6 Pharmacy synergy" in src and "capture_rates" in src:
            fin07_code_cell_idx = i
            break
    fin07_no_clinic_pnl = (
        fin07_code_cell_idx is not None
        and "clinic_pnl(" not in cell_sources[fin07_code_cell_idx]
    )
    fin07 = fin07_cell_present and fin07_order_gated and fin07_not_loadbearing and fin07_no_clinic_pnl
    check_phase5("Phase 5 FIN-07 (pharmacy synergy order-gated + standalone)", fin07,
                 f"FIN-07: missing §7.6 cell ({fin07_cell_present}), order-gated ({fin07_order_gated}), "
                 f"NOT Load-Bearing label ({fin07_not_loadbearing}), no clinic_pnl in synergy cell ({fin07_no_clinic_pnl})")

    # REP-01 (§8.2 assumptions register — 5-column, deposited into report{})
    rep01_cell_idx = cell_index_containing("§8.2")
    rep01_cell_present = rep01_cell_idx is not None
    rep01_5col = (
        rep01_cell_present
        and "Parameter" in cell_sources[rep01_cell_idx]
        and "Value" in cell_sources[rep01_cell_idx]
        and "Source" in cell_sources[rep01_cell_idx]
        and "Date" in cell_sources[rep01_cell_idx]
        and "Confidence" in cell_sources[rep01_cell_idx]
    )
    rep01_deposited = (
        rep01_cell_present
        and "assumptions_register" in cell_sources[rep01_cell_idx]
        and "report[" in cell_sources[rep01_cell_idx]
    )
    rep01 = rep01_cell_present and rep01_5col and rep01_deposited
    check_phase5("Phase 5 REP-01 (assumptions register 5-column)", rep01,
                 f"REP-01: missing §8.2 cell ({rep01_cell_present}), 5 columns ({rep01_5col}), "
                 f"deposited into report{{}} ({rep01_deposited})")

    # REP-02 (§8.1 verdict logic — binary GO/NO-GO, GATE_MARGIN=0.15, standalone, 5 key numbers)
    rep02_cell_idx = cell_index_containing("§8.1")
    rep02_cell_present = rep02_cell_idx is not None
    rep02_binary = (
        rep02_cell_present
        and 'verdict = "GO" if' in cell_sources[rep02_cell_idx]
        and '"NO-GO"' in cell_sources[rep02_cell_idx]
    )
    rep02_gate = (
        rep02_cell_present
        and "GATE_MARGIN = 0.15" in cell_sources[rep02_cell_idx]
    )
    # D-04 standalone: verdict_text construction block must NOT mention pharmacy/priceline
    # Extract just the verdict_text assignment block (not comments) to check for pharmacy mentions
    rep02_standalone = False
    if rep02_cell_present:
        src = cell_sources[rep02_cell_idx]
        # Find the verdict_text construction block (from "verdict_text = (" to the closing ")")
        vt_start = src.find("verdict_text = (")
        if vt_start >= 0:
            vt_end = src.find(")", vt_start)
            # Find the LAST closing paren of the multi-line f-string concatenation
            # The block ends with a ")" on its own line after the last f-string
            vt_block = src[vt_start:vt_end + 1] if vt_end > vt_start else ""
            # Also include the full multi-line block by finding the next "\n)" after vt_start
            lines = src[vt_start:].split("\n")
            vt_lines = []
            for line in lines[1:]:
                vt_lines.append(line)
                if line.strip() == ")":
                    break
            vt_block = "\n".join(vt_lines)
            rep02_standalone = (
                "pharmac" not in vt_block.lower()
                and "priceline" not in vt_block.lower()
            )
        else:
            # Fallback: if verdict_text block not found, check the whole cell minus comments
            no_comments = "\n".join(l for l in src.split("\n") if not l.strip().startswith("#"))
            rep02_standalone = (
                "pharmac" not in no_comments.lower()
                and "priceline" not in no_comments.lower()
            )
    rep02_5keys = (
        rep02_cell_present
        and "steady_state_ebitda" in cell_sources[rep02_cell_idx]
        and "steady_state_margin" in cell_sources[rep02_cell_idx]
        and "peak_capital" in cell_sources[rep02_cell_idx]
        and "breakeven_operating" in cell_sources[rep02_cell_idx]
        and "breakeven_payback" in cell_sources[rep02_cell_idx]
        and "key_numbers" in cell_sources[rep02_cell_idx]
        and "report[" in cell_sources[rep02_cell_idx]
    )
    rep02 = rep02_cell_present and rep02_binary and rep02_gate and rep02_standalone and rep02_5keys
    check_phase5("Phase 5 REP-02 (verdict logic binary + standalone)", rep02,
                 f"REP-02: missing §8.1 cell ({rep02_cell_present}), binary GO/NO-GO ({rep02_binary}), "
                 f"GATE_MARGIN=0.15 ({rep02_gate}), standalone no pharmacy ({rep02_standalone}), "
                 f"5 key numbers deposited ({rep02_5keys})")

    # REP-03 (§8.3 Jinja2 template 8 sections + §8.4 weasyprint + IS_COLAB + try/except)
    rep03_template_cell_idx = cell_index_containing("§8.3")
    rep03_template_present = rep03_template_cell_idx is not None
    rep03_sections = (
        rep03_template_present
        and "Executive Summary" in cell_sources[rep03_template_cell_idx]
        and "Site & Catchment" in cell_sources[rep03_template_cell_idx]
        and "Competitor Landscape" in cell_sources[rep03_template_cell_idx]
        and "Financial Model" in cell_sources[rep03_template_cell_idx]
        and "Scenarios & Sensitivity" in cell_sources[rep03_template_cell_idx]
        and "Pharmacy Synergy" in cell_sources[rep03_template_cell_idx]
        and "Assumptions Register" in cell_sources[rep03_template_cell_idx]
        and "Data Sources & Citations" in cell_sources[rep03_template_cell_idx]
    )
    rep03_jinja2 = (
        rep03_template_present
        and "jinja2" in cell_sources[rep03_template_cell_idx].lower()
        and "Template" in cell_sources[rep03_template_cell_idx]
    )
    rep03_weasyprint_cell = cell_index_containing("§8.4") is not None
    rep03_is_colab = "IS_COLAB" in all_source
    rep03_try_except = (
        "try:" in all_source
        and "except" in all_source
        and "weasyprint" in all_source
    )
    rep03 = rep03_template_present and rep03_sections and rep03_jinja2 and rep03_weasyprint_cell and rep03_is_colab and rep03_try_except
    check_phase5("Phase 5 REP-03 (Jinja2 template 8 sections + weasyprint)", rep03,
                 f"REP-03: missing §8.3 cell ({rep03_template_present}), 8 sections ({rep03_sections}), "
                 f"Jinja2 ({rep03_jinja2}), §8.4 cell ({rep03_weasyprint_cell}), IS_COLAB ({rep03_is_colab}), "
                 f"try/except weasyprint ({rep03_try_except})")

    # REP-04 (footnote-style citations [1]-[8] + access date markers)
    rep04_cell = rep03_template_cell_idx  # citations are in the §8.3 template cell
    rep04_citations = (
        rep04_cell is not None
        and all(f"[{n}]" in cell_sources[rep04_cell] for n in range(1, 9))
    )
    rep04_access_date = (
        rep04_cell is not None
        and ("Access date" in cell_sources[rep04_cell] or "access date" in cell_sources[rep04_cell])
    )
    rep04 = rep04_citations and rep04_access_date
    check_phase5("Phase 5 REP-04 (footnote citations [1]-[8] + access dates)", rep04,
                 f"REP-04: citations [1]-[8] all present ({rep04_citations}), access date markers ({rep04_access_date})")

    passes.extend(phase5_passes)
    failures.extend(phase5_failures)

    # ──────────────────────────────────────────────────────────────
    # 6b. Regression checks (post-review fixes — REV-01..06)
    # ──────────────────────────────────────────────────────────────

    def check_rev(label, condition, fail_msg):
        if condition:
            passes.append(label)
            print(f"[validate] {label}: PASS")
        else:
            failures.append(fail_msg)
            print(f"[validate] {label}: FAIL")

    # REV-01: every code cell compiles (would have caught the linestyle="--, SyntaxError).
    # Strip IPython magics/shell escapes (%pip, !cmd) which aren't valid pure-Python syntax.
    rev01_errors = []
    for i, c in enumerate(code_cells):
        raw_lines = c.get("source", [])
        # Replace IPython magics/shell escapes with a same-indented `pass` so block
        # structure (e.g. `if IN_COLAB:` followed by `%pip install`) stays valid.
        py_lines = []
        for ln in raw_lines:
            stripped = ln.lstrip()
            if stripped.startswith(("%", "!")):
                indent = ln[:len(ln) - len(stripped)]
                py_lines.append(indent + "pass\n")
            else:
                py_lines.append(ln)
        src = "".join(py_lines)
        try:
            compile(src, f"<code cell {i}>", "exec")
        except SyntaxError as e:
            rev01_errors.append(f"cell {i}: {e.msg} (line {e.lineno})")
    check_rev("REV-01 (all code cells compile)", not rev01_errors,
              f"REV-01: {len(rev01_errors)} code cell(s) fail to compile: {rev01_errors}")

    # REV-02: demand rates use the per-100 convention (values >= 100, not per-person ~4-12)
    # AND the demand units plausibility guard is present.
    rev02_per100 = bool(re.search(r'"consults_per_capita_yr":\s*\{[^}]*"65\+":\s*\d{3,}', all_source))
    rev02_guard = "DEMAND UNITS CHECK" in all_source and "PLAUSIBLE_PER100" in all_source
    check_rev("REV-02 (demand rates per-100 + units guard)", rev02_per100 and rev02_guard,
              f"REV-02: per-100 rate values ({rev02_per100}), units guard present ({rev02_guard})")

    # REV-03: no duplicate consults_per_capita_yr key in the BASE_ASSUMPTIONS cell.
    ba_idx = first_def_cell("BASE_ASSUMPTIONS")
    rev03_single = ba_idx is not None and cell_sources[ba_idx].count('"consults_per_capita_yr":') == 1
    check_rev("REV-03 (no duplicate consults_per_capita_yr key)", rev03_single,
              "REV-03: consults_per_capita_yr defined != once in BASE_ASSUMPTIONS cell")

    # REV-04: working-capital buffer is derived, not a stale hardcoded literal.
    rev04_no_literal = "49_450" not in all_source and "49450" not in all_source
    rev04_derived = "monthly_fixed_costs" in all_source and "working_capital_buffer_months" in all_source
    check_rev("REV-04 (working-capital buffer derived)", rev04_no_literal and rev04_derived,
              f"REV-04: stale 49,450 literal absent ({rev04_no_literal}), derived buffer ({rev04_derived})")

    # REV-05: §6 narrative arithmetic corrected (effective 20,625, not the false "=27,500").
    rev05 = "20,625" in all_source and "75% utilisation = 27,500" not in all_source
    check_rev("REV-05 (§6 narrative 20,625 not false 27,500)", rev05,
              "REV-05: §6 narrative still states '75% utilisation = 27,500' or missing 20,625")

    # REV-06: dead/contradictory params removed (check KEY definitions, not mentions in comments).
    rev06 = '"consults_per_gp_day":' not in all_source and '"days_per_yr":' not in all_source
    check_rev("REV-06 (dead params removed)", rev06,
              "REV-06: consults_per_gp_day or days_per_yr key still defined")

    # ──────────────────────────────────────────────────────────────
    # 7. Summary report
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
        "Phase 3 DEMAND-04 (no ML / no sklearn / no RandomForest)",
        "Phase 3 DEMAND-01 (SA3 MBS + state fallback warning)",
        "Phase 3 DEMAND-02 (age-adjusted demand + AIHW 4 bands)",
        "Phase 3 DEMAND-03 (capacity range + market share + interpretation)",
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

    # Phase 5 checks
    phase5_labels = [
        "Phase 5 FIN-04 (scenario override dicts)",
        "Phase 5 FIN-05 (tornado sensitivity + zero-crossings)",
        "Phase 5 FIN-06 (billing-mix curve + BBPIP)",
        "Phase 5 FIN-07 (pharmacy synergy order-gated + standalone)",
        "Phase 5 REP-01 (assumptions register 5-column)",
        "Phase 5 REP-02 (verdict logic binary + standalone)",
        "Phase 5 REP-03 (Jinja2 template 8 sections + weasyprint)",
        "Phase 5 REP-04 (footnote citations [1]-[8] + access dates)",
    ]
    for label in phase5_labels:
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
        if not any(k in f for k in ["PIPE-01", "PIPE-02", "PIPE-03", "PIPE-04", "PIPE-05", "PIPE-06", "v1 flaw", "GEO-01", "GEO-02", "GEO-03", "GEO-04", "D-06", "CR-01", "DEMO-01", "DEMO-02", "DEMO-03", "DEMO-04", "D-11", "D-03", "D-09b", "COMP-01", "COMP-02", "COMP-03", "DEMAND-01", "DEMAND-02", "DEMAND-03", "DEMAND-04", "FIN-04", "FIN-05", "FIN-06", "FIN-07", "REP-01", "REP-02", "REP-03", "REP-04"]):
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
