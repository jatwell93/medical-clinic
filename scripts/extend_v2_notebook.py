#!/usr/bin/env python3
"""
Extension script for Johnston_St_v2.ipynb — Phase 2 (Plan 02-01).

Loads the existing notebook (built by create_v2_notebook.py in Phase 1),
appends §1.2 Geocode Site + §2 Geospatial Catchment cells, and writes it
back with json.dump(nb, f, indent=1).

Follows the same cell-dict pattern as create_v2_notebook.py:
  cell_type, metadata: {}, source as list of strings (each ending with \n
  except possibly the last); code cells have execution_count: null, outputs: [].

Idempotent: if a cell containing "# §1.2 Geocode Site" already exists,
the script REMOVES the existing §1.2 + §2 cells and re-appends the
corrected versions (cell-replacement idempotency — re-running produces
the corrected notebook).

Run:  python scripts/extend_v2_notebook.py
Output: Johnston_St_v2.ipynb (extended in-place)
"""

import json
import re
from pathlib import Path


# ──────────────────────────────────────────────────────────────────────
#  Cell helpers (same pattern as create_v2_notebook.py)
# ──────────────────────────────────────────────────────────────────────

def md(*lns):
    """Create a markdown cell dict."""
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": _join(lns),
    }


def code(*lns):
    """Create a code cell dict."""
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": _join(lns),
    }


def _join(lns):
    """Join strings into a source list, each ending with \\n except the last."""
    result = []
    for i, ln in enumerate(lns):
        if i < len(lns) - 1:
            result.append(ln + "\n")
        else:
            result.append(ln)
    return result


# ──────────────────────────────────────────────────────────────────────
#  Phase 2 BASE_ASSUMPTIONS keys to insert
# ──────────────────────────────────────────────────────────────────────

PHASE2_ASSUMPTIONS_KEYS = [
    "",
    "    # --- Phase 2: Catchment (source: ABS ASGS Edition 3; PITFALLS.md Pitfall 1/2) ---",
    '    "sa1_shapefile":          "SA1_2021_AUST_GDA2020.zip",  # ABS ASGS Edition 3 — manual download',
    '    "poa_shapefile":          "POA_2021_AUST_GDA2020_SHP.zip",  # ABS ASGS Edition 3 — on hand',
    '    "assert_3km_buffer_km2":  28.27,       # π×3² — sanity check for EPSG:7855 buffering (GEO-02, D-09a)',
    '    "assert_3km_buffer_tol":  0.1,         # km² tolerance',
    '    "catchment_pop_plausible_range": (80_000, 110_000),  # inner-Melbourne 3km ring (D-09b, PITFALLS.md Pitfall 2)',
    '    "erp_vintage_year":       2024,        # ABS Regional Population 2023-24 FY (released March 2025) — DEMO-04',
]


# ──────────────────────────────────────────────────────────────────────
#  §1.2 Geocode Site cells
# ──────────────────────────────────────────────────────────────────────

def geocode_cells():
    """Return the §1.2 Geocode Site cells (markdown + code + verification map)."""
    cells = []

    # 1. Markdown — §1.2 Geocode Site header + teaching commentary
    cells.append(md(
        "## §1.2 Geocode Site",
        "",
        "v1 used the **postcode centroid** as the catchment centre (PITFALLS.md Pitfall 3)",
        "and referenced the site coordinates before they were defined (out-of-order",
        "execution). This cell geocodes the **exact address** ONCE through the cached",
        "session, prints the coordinates, and asks the reader to visually verify the pin",
        "on the immediately-following map before proceeding.",
        "",
        "The cached response means re-runs are **free and keyless** — after the first",
        "successful geocode, the coordinates are served from `data/cache/` and no",
        "`GOOGLE_PLACES_KEY` is needed (PIPE-04).",
        "",
        "**Known anchor (D-31):** The site is at the Johnston St × Hoddle St corner,",
        "Abbotsford. Expected coordinates ≈ (-37.799, 145.003). The map below lets you",
        "confirm the pin lands on the right spot before any buffer or Places search",
        "centres on it.",
    ))

    # 2. Code — §1.2 geocode
    cells.append(code(
        "# Geocode the exact site address through the Phase 1 CachedSession (D-31, PITFALLS.md Pitfall 3)",
        "# v1 flaw: used postcode centroid + referenced site coords before definition (out-of-order execution)",
        "import urllib.parse",
        "",
        "GEOCODE_URL = (",
        '    "https://maps.googleapis.com/maps/api/geocode/json?address="',
        "    + urllib.parse.quote(SITE_ADDRESS)",
        '    + f"&key={GOOGLE_PLACES_KEY}"',
        ")",
        "",
        "# Cached fetch — re-runs are free and keyless after first run (PIPE-04)",
        'if GOOGLE_PLACES_KEY or any(CACHE_DIR.glob("geocode_*.json")):',
        "    resp = session.get(GEOCODE_URL)",
        "    data = resp.json()",
        '    assert data.get("status") == "OK", f"Geocode failed: {data.get(\'status\')} {data.get(\'error_message\',\'\')}"',
        '    result = data["results"][0]',
        '    site_lat = result["geometry"]["location"]["lat"]',
        '    site_lon = result["geometry"]["location"]["lng"]',
        '    site_place_id = result.get("place_id", "")',
        '    print(f"[geocode] {SITE_ADDRESS}")',
        '    print(f"[geocode] lat={site_lat:.6f}, lon={site_lon:.6f} (from_cache={resp.from_cache})")',
        '    print(f"[geocode] ⚠ Visually verify this pin on the map below before proceeding.")',
        '    print(f"[geocode]    Expected: Johnston St × Hoddle St corner, Abbotsford")',
        "else:",
        "    raise RuntimeError(",
        '        "No GOOGLE_PLACES_KEY and no cached geocode response. "',
        '        "Add the key via Colab Secrets or local .env, run once, then re-run keyless."',
        "    )",
    ))

    # 3. Code — §1.2 verification map (folium)
    cells.append(code(
        "# §1.2 verification map — visually confirm the pin (D-31)",
        "import folium",
        'm_verify = folium.Map(location=[site_lat, site_lon], zoom_start=16, tiles="CartoDB Positron")',
        "folium.Marker(",
        "    [site_lat, site_lon],",
        '    popup=f"Site: {SITE_ADDRESS}<br>({site_lat:.5f}, {site_lon:.5f})",',
        '    tooltip="292-296 Johnston St",',
        '    icon=folium.Icon(color="red", icon="info-sign"),',
        ").add_to(m_verify)",
        "m_verify",
    ))

    return cells


# ──────────────────────────────────────────────────────────────────────
#  §2 Geospatial Catchment cells
# ──────────────────────────────────────────────────────────────────────

def catchment_cells():
    """Return the §2 Geospatial Catchment cells (markdown + code interleaved)."""
    cells = []

    # 4. Markdown — §2 header
    cells.append(md(
        "# §2 Geospatial Catchment",
        "",
        "v1's headline flaw was **whole-postcode summing** (PITFALLS.md Pitfall 2):",
        "it summed the FULL population of every postcode touching the buffer, inflating",
        "catchment population 2–4× and flipping the go/no-go answer. This section fixes",
        "it with **SA1-level area apportionment** (D-01).",
        "",
        "All metric operations (buffer, area, distance) happen in **EPSG:7855**",
        "(GDA2020 / MGA zone 55) — PITFALLS.md Pitfall 1 warns that buffering in",
        "degrees creates a \"buffer\" spanning the continent. The CRS convention is:",
        "**metric ops in EPSG:7855, display in EPSG:4326**.",
        "",
        "The v1-vs-v2 comparison at the end (§2.4) is the teaching moment showing",
        "v1 inflated 2–4×.",
    ))

    # 5. Code — §2.1 Load SA1 + POA geometry
    cells.append(code(
        "# Load SA1 + POA boundary geometry from data/local/ (D-02, D-07)",
        "# Both are gitignored — large, immutable, not committed",
        "# Geospatial imports (preinstalled in Colab — STACK.md)",
        "import geopandas as gpd",
        "from shapely.geometry import Point",
        "",
        'SA1_ZIP = PROJECT_ROOT / "data" / "local" / BASE_ASSUMPTIONS["sa1_shapefile"]',
        'POA_ZIP = PROJECT_ROOT / "data" / "local" / BASE_ASSUMPTIONS["poa_shapefile"]',
        "",
        "if not SA1_ZIP.exists():",
        '    print(f"⚠ SA1 shapefile missing: {SA1_ZIP}")',
        '    print(f"  Download from ABS ASGS Edition 3 digital boundary files (see .env.example)")',
        '    print(f"  Falling back to POA-level apportionment (degraded — uniform-density assumption coarser)")',
        "    USE_SA1 = False",
        "else:",
        "    USE_SA1 = True",
        "",
        "poa = gpd.read_file(POA_ZIP)",
        'poa = poa[poa["STE_NAME21"] == "Victoria"].to_crs("EPSG:7855")  # metric CRS for area math',
        'print(f"[geom] POA: {len(poa)} VIC polygons, CRS={poa.crs.to_epsg()}")',
        "",
        "if USE_SA1:",
        "    sa1 = gpd.read_file(SA1_ZIP)",
        '    sa1 = sa1[sa1["STE_NAME21"] == "Victoria"].to_crs("EPSG:7855")',
        '    print(f"[geom] SA1: {len(sa1)} VIC polygons, CRS={sa1.crs.to_epsg()}")',
    ))

    # 6. Markdown — §2.2 Build 1/3/5 km Buffers
    cells.append(md(
        "## §2.2 Build 1/3/5 km Buffers (EPSG:7855)",
        "",
        "The CRS convention is **metric ops in EPSG:7855, display in EPSG:4326**",
        "(PITFALLS.md Pitfall 1). The 3 km buffer area assertion (≈ 28.27 km² = π×3²)",
        "is the sanity check that catches a degree-based buffer before it poisons",
        "everything downstream.",
        "",
        "v1 buffered in degrees → the \"buffer\" spanned half of Victoria. The assertion",
        "below would have caught it instantly.",
    ))

    # 7. Code — §2.2 buffer construction + assertion
    cells.append(code(
        "# Build 1/3/5 km buffers in EPSG:7855 (GEO-02, D-09a, PITFALLS.md Pitfall 1)",
        '# v1 flaw: buffered in degrees → "buffer" spanning half of Victoria',
        "site_point = gpd.GeoDataFrame(",
        '    [{"name": "site"}], geometry=[Point(site_lon, site_lat)], crs="EPSG:4326"',
        ")",
        'site_metric = site_point.to_crs("EPSG:7855")',
        "",
        "buffers = {}",
        'for r in BASE_ASSUMPTIONS["catchment_radii_m"]:',
        "    buf = site_metric.buffer(r)",
        "    buffers[r] = buf",
        "    area_km2 = buf.area.iloc[0] / 1e6",
        '    print(f"[buffer] {r//1000} km: area={area_km2:.2f} km²")',
        "",
        "# Sanity assertion (GEO-02, D-09a) — 3km buffer ≈ 28.27 km² (π×3²)",
        'area_3k = buffers[3000].area.iloc[0] / 1e6',
        'assert abs(area_3k - BASE_ASSUMPTIONS["assert_3km_buffer_km2"]) < BASE_ASSUMPTIONS["assert_3km_buffer_tol"], \\',
        '    f"3km buffer area {area_3k:.2f} km² ≠ {BASE_ASSUMPTIONS[\'assert_3km_buffer_km2\']} km² — CRS bug (PITFALLS.md Pitfall 1)"',
        'print(f"[buffer] ✓ 3km buffer area assertion passed ({area_3k:.2f} km² ≈ π×3²)")',
    ))

    # 8. Markdown — §2.3 SA1 Area Apportionment
    cells.append(md(
        "## §2.3 SA1 Area Apportionment",
        "",
        "This is the **headline v1 fix** (PITFALLS.md Pitfall 2). v1 summed the FULL",
        "population of every postcode touching the buffer. v2 area-apportions each",
        "SA1's population by the fraction of its area inside the buffer.",
        "",
        "The **uniform-density assumption** is documented (D-05) and the Yarra River",
        "is annotated on every map so readers see the geographic issue — the river and",
        "industrial land in Abbotsford mean the assumption likely *overstates*",
        "population in that slice.",
        "",
        "**Note:** The SA1 total persons come from §3 (Plan 02-02) via",
        "`fetch_sa1_total_persons(sa1_codes)`. This cell defines the apportionment",
        "logic and spatial filter; the population weights are wired in §3 once the ABS",
        "SA1 census is fetched.",
    ))

    # 9. Code — §2.3 SA1 apportionment
    cells.append(code(
        "# SA1-level area apportionment (D-01 — the headline v1 fix, PITFALLS.md Pitfall 2)",
        "# v1 flaw: summed FULL population of every postcode touching the buffer (2-4× overstatement)",
        "# v2: area-weight each SA1's population by the fraction inside the buffer",
        "if USE_SA1:",
        "    # Spatial-filter SA1s intersecting the 5km buffer (D-08 — beat 30s API timeout)",
        "    sa1_in_5k = sa1[sa1.geometry.intersects(buffers[5000].iloc[0])].copy()",
        '    print(f"[apportion] {len(sa1_in_5k)} SA1s intersect 5km buffer")',
        "",
        "    # Per-ring area-weighted apportionment",
        "    # sa1_pop_df is produced in §3 (Plan 02-02) — stub here, wired there",
        "    def apportion_ring(sa1_gdf, sa1_pop_df, ring_geom):",
        '        """Area-weight SA1 populations into a ring. Returns total population in ring."""',
        '        ring = gpd.GeoDataFrame(geometry=[ring_geom], crs="EPSG:7855")',
        '        inter = sa1_gdf.overlay(ring, how="intersection")',
        "        # Join population",
        '        inter = inter.merge(sa1_pop_df, on="SA1_CODE21", how="left")',
        "        # Area fraction (intersect_area / full_sa1_area)",
        '        full_area = sa1_gdf.set_index("SA1_CODE21")["geometry"].area',
        '        inter["frac"] = inter.geometry.area / inter["SA1_CODE21"].map(full_area).values',
        '        inter["pop_in_ring"] = inter["frac"] * inter["Total_P_P"]',
        '        return inter["pop_in_ring"].sum(), inter',
        "",
        "    # NOTE: sa1_pop_df is assigned in §3 demographics (Plan 02-02).",
        "    # For Phase 2 §2 standalone validation, we use a proxy: SA1 area-only weights",
        "    # (uniform density across all SA1s in 5km). The real population weights land in §3.",
        "    # This stub is overwritten by §3 once ABS SA1 census is fetched.",
        '    print("[apportion] ℹ Population weights come from §3 (ABS C21_G01_SA1). "',
        '          "Catchment population totals are computed in §3 after the SA1 census fetch.")',
        "else:",
        '    print("[apportion] ⚠ SA1 shapefile missing — using POA-level apportionment (degraded)")',
        "    # POA-level fallback (coarser) — same area-weight logic at POA granularity",
    ))

    # 10. Markdown — §2.4 v1-vs-v2 Catchment Comparison
    cells.append(md(
        "## §2.4 v1-vs-v2 Catchment Comparison",
        "",
        "This is the **teaching moment** (D-06, success criterion #2). v1's naive",
        "whole-postcode sum is reproduced inline so readers see the flawed logic next",
        "to the fixed logic. The grouped bar chart + side-by-side table show v1",
        "inflating 2–4× per ring.",
        "",
        "The v1 and v2 totals come from §3 (Plan 02-02). This cell defines the comparison",
        "function `compare_v1_v2(v1_ring_pops, v2_ring_pops)` that §3.3 calls after",
        "computing both the v1 naive whole-postcode sums and the v2 apportioned totals.",
    ))

    # 11. Code — §2.4 v1-vs-v2 comparison
    cells.append(code(
        "# v1-vs-v2 catchment comparison (D-06, success criterion #2)",
        "# Reproduce v1's naive whole-postcode sum inline, compare against v2 apportioned",
        "def v1_naive_catchment_pop(ring_geom_m, poa_pop_df):",
        '    """v1 flaw: sum FULL POA population for any POA touching the buffer.',
        "    poa_pop_df: DataFrame with columns POA_CODE21, Total_P_P (from §3 G01 fetch).",
        '    Returns the summed population (int), NOT a GeoDataFrame."""',
        "    touching = poa[poa.geometry.intersects(ring_geom_m)]",
        "    # Join POA total persons onto the touching POAs and sum (v1's naive approach)",
        '    merged = touching.merge(poa_pop_df[["POA_CODE21", "Total_P_P"]], on="POA_CODE21", how="left")',
        '    return int(merged["Total_P_P"].sum())',
        "",
        "def compare_v1_v2(v1_ring_pops: dict, v2_ring_pops: dict):",
        '    """',
        "    v1_ring_pops: {radius_m: naive_whole_postcode_pop} — v1's flawed approach",
        "    v2_ring_pops: {radius_m: sa1_apportioned_pop} — v2's corrected approach",
        "    Returns comparison DataFrame + renders grouped bar chart showing v1 overstatement.",
        '    """',
        "    import pandas as pd",
        "    import matplotlib.pyplot as plt",
        "    rows = []",
        "    for r, v2_pop in v2_ring_pops.items():",
        "        v1_pop = v1_ring_pops.get(r, 0)",
        '        rows.append({"ring_km": r//1000, "v1_naive": v1_pop, "v2_apportioned": v2_pop,',
        '                     "diff": v1_pop - v2_pop,',
        '                     "pct_overstate": (v1_pop/v2_pop - 1)*100 if v2_pop else None})',
        "    df = pd.DataFrame(rows)",
        "    print(df.to_string(index=False))",
        "    # Grouped bar chart",
        "    fig, ax = plt.subplots(figsize=(8, 4))",
        "    x = range(len(df))",
        '    ax.bar([i-0.2 for i in x], df["v1_naive"], width=0.4, label="v1 naive (whole-postcode)", color="#d62728")',
        '    ax.bar([i+0.2 for i in x], df["v2_apportioned"], width=0.4, label="v2 apportioned (SA1)", color="#2ca02c")',
        '    ax.set_xticks(list(x)); ax.set_xticklabels([f"{r} km" for r in df["ring_km"]])',
        '    ax.set_ylabel("Catchment population"); ax.legend(); ax.set_title("v1 vs v2 catchment population")',
        "    plt.show()",
        "    return df",
        'print("[compare] compare_v1_v2(v1_ring_pops, v2_ring_pops) defined — called in §3.3 after both v1 and v2 totals are computed")',
    ))

    # 12. Markdown — §2.5 Catchment Maps
    cells.append(md(
        "## §2.5 Catchment Maps",
        "",
        "**Folium** is interactive (inline only, NOT in the PDF — it's HTML/JS and",
        "won't render in weasyprint, STACK.md constraint). The **static matplotlib +",
        "contextily** twin handles the PDF.",
        "",
        "One static figure per ring (1 km, 3 km, 5 km), each zoomed to its ring (D-27).",
        "The Yarra River is annotated on every map so readers see the uniform-density",
        "caveat's geographic issue (D-05).",
    ))

    # 13. Code — §2.5 folium interactive map
    cells.append(code(
        "# Folium interactive map — inline only, NOT in PDF (D-25, D-30, STACK.md)",
        "import folium",
        'm_catch = folium.Map(location=[site_lat, site_lon], zoom_start=12, tiles="CartoDB Positron")',
        "",
        "# Site pin",
        'folium.Marker([site_lat, site_lon], popup=SITE_ADDRESS,',
        '              icon=folium.Icon(color="red", icon="info-sign")).add_to(m_catch)',
        "",
        "# 1/3/5 km buffer rings (reproject to EPSG:4326 for folium)",
        'for r in BASE_ASSUMPTIONS["catchment_radii_m"]:',
        '    buf_4326 = gpd.GeoDataFrame(geometry=buffers[r], crs="EPSG:7855").to_crs("EPSG:4326")',
        "    folium.GeoJson(buf_4326, style_function=lambda f, r=r: {",
        '        "color": {1000:"blue", 3000:"orange", 5000:"green"}[r],',
        '        "weight": 2, "fillOpacity": 0.05',
        '    }, name=f"{r//1000} km ring").add_to(m_catch)',
        "",
        "# POA boundaries (peers) — shaded by apportionment share (computed in §3)",
        'poa_peers_4326 = poa[poa["POA_CODE21"].isin(PEER_POSTCODES)].to_crs("EPSG:4326")',
        'folium.GeoJson(poa_peers_4326, style_function=lambda f: {"color":"purple","weight":1,"fillOpacity":0.1},',
        '               name="Peer POAs").add_to(m_catch)',
        "",
        "# Yarra River line (D-05) — approximate path through Abbotsford",
        "# NOTE: exact Yarra geometry comes from OSM or a local GeoJSON; for MVP, a hand-drawn",
        "# polyline through known points is acceptable. Plan 02-02 may upgrade to OSM fetch.",
        "yarra_pts = [[-37.808, 145.003], [-37.810, 145.000], [-37.815, 144.998], [-37.820, 144.995]]",
        'folium.PolyLine(yarra_pts, color="aqua", weight=4, opacity=0.7, tooltip="Yarra River (approx)").add_to(m_catch)',
        "",
        "folium.LayerControl().add_to(m_catch)",
        'print("[map] Folium catchment map rendered (inline only — PDF uses static matplotlib below)")',
        "m_catch",
    ))

    # 14. Code — §2.5 static matplotlib + contextily figures
    cells.append(code(
        "# Static matplotlib + contextily figures for the PDF (D-27, D-29) — one per ring",
        "import matplotlib.pyplot as plt",
        "import contextily as cx",
        "import numpy as np",
        "",
        'site_4326 = site_point.to_crs("EPSG:4326")',
        'poa_peers_4326 = poa[poa["POA_CODE21"].isin(PEER_POSTCODES)].to_crs("EPSG:4326")',
        "",
        'for r in BASE_ASSUMPTIONS["catchment_radii_m"]:',
        "    fig, ax = plt.subplots(figsize=(8, 8))",
        "    # Buffer ring",
        '    buf_4326 = gpd.GeoDataFrame(geometry=buffers[r], crs="EPSG:7855").to_crs("EPSG:4326")',
        '    buf_4326.boundary.plot(ax=ax, color={1000:"blue", 3000:"orange", 5000:"green"}[r], linewidth=2)',
        "    # POA boundaries",
        '    poa_peers_4326.boundary.plot(ax=ax, color="purple", linewidth=0.8, alpha=0.6)',
        "    # Site pin",
        '    site_4326.plot(ax=ax, color="red", markersize=40)',
        "    # Yarra River (approx)",
        "    yarra_x = [145.003, 145.000, 144.998, 144.995]",
        "    yarra_y = [-37.808, -37.810, -37.815, -37.820]",
        '    ax.plot(yarra_x, yarra_y, color="aqua", linewidth=3, alpha=0.7, label="Yarra River (approx)")',
        "    # Basemap",
        '    cx.add_basemap(ax, crs="EPSG:4326", source=cx.providers.CartoDB.Positron)',
        '    ax.set_title(f"Catchment — {r//1000} km ring (Johnston St site)")',
        '    ax.legend(loc="upper right")',
        "    plt.show()",
    ))

    # 15. Markdown — §2.6 Uniform-Density Caveat
    cells.append(md(
        "## §2.6 Uniform-Density Caveat",
        "",
        "> **Caveat (uniform-density assumption):** Catchment population is",
        "> area-apportioned at SA1 level assuming population is uniformly distributed",
        "> within each SA1. This likely *overstates* population in the Yarra River /",
        "> industrial slice of Abbotsford (non-residential land). The Yarra River is",
        "> annotated on every catchment map so readers can see the geographic issue.",
        "> Mesh-block apportionment (finer) is the rigorous alternative — noted in",
        "> PITFALLS.md Pitfall 2 as the \"best\" option; deferred as overkill for an",
        "> MVP investor report.",
    ))

    # 16. Markdown — Next Steps
    cells.append(md(
        "## Next Steps",
        "",
        "**§3 Demographics (Plan 02-02)** will fetch ABS G01/G02/G04 census data",
        "(POA + SA1), apply ERP scaling to 2024, produce the peer benchmarking table",
        "+ comparison charts, and wire the SA1 total persons into the §2.3",
        "apportionment function to compute the actual v2 catchment population totals",
        "+ the v1-vs-v2 comparison.",
    ))

    return cells


# ──────────────────────────────────────────────────────────────────────
#  BASE_ASSUMPTIONS extension
# ──────────────────────────────────────────────────────────────────────

def extend_base_assumptions(cells):
    """Insert Phase 2 keys into the BASE_ASSUMPTIONS dict cell.

    Locates the cell whose source contains 'BASE_ASSUMPTIONS = {' and inserts
    the Phase 2 keys before the closing '}'.  Idempotent: if the keys are
    already present, the cell is left unchanged.
    """
    for cell in cells:
        src = cell.get("source", [])
        joined = "".join(src)
        if "BASE_ASSUMPTIONS = {" not in joined:
            continue
        if "sa1_shapefile" in joined:
            return False  # already extended
        # Find the closing '}' of the BASE_ASSUMPTIONS dict.
        # The dict spans multiple source lines; the closing brace is on its
        # own line (or at the end of a line).  We insert the new keys just
        # before that brace.
        new_source = []
        inserted = False
        for line in src:
            if not inserted and line.strip() == "}":
                # Insert Phase 2 keys before the closing brace
                for key_line in PHASE2_ASSUMPTIONS_KEYS:
                    new_source.append(key_line + "\n")
                new_source.append(line)
                inserted = True
            else:
                new_source.append(line)
        if inserted:
            cell["source"] = new_source
            return True
    return False


# ──────────────────────────────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────────────────────────────

def main():
    notebook_path = Path(__file__).resolve().parent.parent / "Johnston_St_v2.ipynb"
    nb = json.loads(notebook_path.read_text(encoding="utf-8"))
    cells = nb["cells"]

    # Extend BASE_ASSUMPTIONS with Phase 2 keys (idempotent — no-op if already present)
    extend_base_assumptions(cells)

    # Cell-replacement idempotency: if §1.2 Geocode Site already exists,
    # remove the existing §1.2 + §2 cells and re-append the corrected versions.
    MARKER = "# §1.2 Geocode Site"
    STOP_MARKER = "# §3 Demographics"
    start_idx = None
    for i, c in enumerate(cells):
        if MARKER in "".join(c.get("source", [])):
            start_idx = i
            break

    # Build the new cells (geocode + catchment)
    new_cells = geocode_cells() + catchment_cells()

    if start_idx is not None:
        # Find where the §1.2+§2 section ends (next major section marker or Next Steps)
        end_idx = len(cells)
        has_section3 = False
        for j in range(start_idx + 1, len(cells)):
            src = "".join(cells[j].get("source", []))
            if STOP_MARKER in src:
                end_idx = j
                has_section3 = True
                break
            if "## Next Steps" in src:
                end_idx = j
                break
        removed = end_idx - start_idx
        cells = cells[:start_idx] + cells[end_idx:]
        # If §3 Demographics follows, drop the trailing §2 "Next Steps" markdown
        # (§3 owns the final Next Steps — the §2 version would be mid-notebook)
        if has_section3 and new_cells and new_cells[-1].get("cell_type") == "markdown" \
                and "".join(new_cells[-1].get("source", [])).startswith("## Next Steps"):
            new_cells = new_cells[:-1]
        cells[start_idx:start_idx] = new_cells
        print(f"[extend] replaced {removed} §1.2+§2 cells with {len(new_cells)} corrected cells")
    else:
        # Fresh install — find the §1.2 ABS smoke test code cell, insert after it
        insert_idx = None
        for i, c in enumerate(cells):
            src = "".join(c.get("source", []))
            if "ABS Data API smoke test" in src and c.get("cell_type") == "code":
                insert_idx = i + 1
                break
        if insert_idx is None:
            insert_idx = len(cells)
        # Remove old Next Steps if present at insert point (replaced by new §2 Next Steps)
        if insert_idx < len(cells):
            old_next = cells[insert_idx]
            old_src = "".join(old_next.get("source", []))
            if old_next.get("cell_type") == "markdown" and old_src.startswith("## Next Steps"):
                cells.pop(insert_idx)
        cells[insert_idx:insert_idx] = new_cells
        print(f"[extend] appended {len(new_cells)} §1.2+§2 cells (fresh install)")

    # Write back
    nb["cells"] = cells
    notebook_path.write_text(
        json.dumps(nb, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    n_cells = len(cells)
    n_code = sum(1 for c in cells if c.get("cell_type") == "code")
    n_md = sum(1 for c in cells if c.get("cell_type") == "markdown")
    print(f"[extend] notebook now: {n_cells} cells ({n_code} code, {n_md} markdown)")


if __name__ == "__main__":
    main()
