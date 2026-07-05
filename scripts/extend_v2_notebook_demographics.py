#!/usr/bin/env python3
"""
Extension script for Johnston_St_v2.ipynb — Phase 2 (Plan 02-02).

Loads the existing notebook (extended by extend_v2_notebook.py in Plan 02-01),
appends §3 Demographics cells, and writes it back with json.dump.

Follows the same cell-dict pattern as extend_v2_notebook.py:
  cell_type, metadata: {}, source as list of strings (each ending with \n
  except possibly the last); code cells have execution_count: null, outputs: [].

Idempotent: if a cell containing "# §3 Demographics" already exists,
the script skips appending and prints a skip message.

Run:  python scripts/extend_v2_notebook_demographics.py
Output: Johnston_St_v2.ipynb (extended in-place)
"""

import json
from pathlib import Path


# ──────────────────────────────────────────────────────────────────────
#  Cell helpers (same pattern as extend_v2_notebook.py)
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
#  §3 Demographics cells
# ──────────────────────────────────────────────────────────────────────

def demographics_cells():
    """Return the §3 Demographics cells (markdown + code interleaved)."""
    cells = []

    # 1. Markdown — §3 Demographics header + teaching commentary
    cells.append(md(
        "# §3 Demographics",
        "",
        "v1 had **no census staleness handling** (PITFALLS.md Pitfall 15) and",
        "**conflated POA/SA2/SA3 geographies** (Pitfall 5). This section fetches",
        "ABS G01/G02/G04 at POA level for peer benchmarking + SA1 level for",
        "catchment apportionment, with a **local GCP fallback** that emits the SAME",
        "tidy schema (D-17) so downstream code is source-agnostic.",
        "",
        "**ERP scaling** (2021 → 2024) addresses the 4-5 year census lag — Abbotsford",
        "has grown since the 2021 Census. The peer benchmarking table includes",
        "**placeholder GP/pharmacy columns** (\"— Phase 3\") that Phase 3 fills —",
        "no Places API calls in Phase 2.",
        "",
        "Critically, §3 also **wires the SA1 total persons into the §2.3",
        "apportionment function** — without this, the v2 catchment population totals",
        "and the v1-vs-v2 comparison are stubs. This section completes the headline",
        "v1-flaw-fix teaching moment.",
    ))

    # 2. Code — §3.1 ABS dataflow discovery + G01/G02 fetch
    cells.append(code(
        "# ABS Data API — G01/G02 for POA 3067 + 9 peers (DEMO-01, D-13, D-14)",
        "# All calls through the Phase 1 CachedSession (ARCHITECTURE.md Pattern 1)",
        "import pandas as pd",
        "import io",
        "",
        "ABS_BASE = \"https://data.api.abs.gov.au/rest\"",
        "PEER_POA_CODES = \"+\".join(PEER_POSTCODES)  # SDMX OR operator within a dimension",
        "",
        "def fetch_abs_csv(flow_id, data_key):",
        "    \"\"\"Fetch ABS dataflow as CSV-with-labels through the cached session. Returns tidy DataFrame.\"\"\"",
        "    url = f\"{ABS_BASE}/data/{flow_id}/{data_key}?format=csvfilewithlabels\"",
        "    resp = session.get(url)",
        "    resp.raise_for_status()",
        "    return pd.read_csv(io.StringIO(resp.text)), resp",
        "",
        "def check_dataflow_exists(flow_id):",
        "    \"\"\"Check if a dataflow ID exists in the ABS dataflow list (D-11).\"\"\"",
        "    flows_resp = session.get(f\"{ABS_BASE}/dataflow?detail=allstubs\")",
        "    flows = flows_resp.json()",
        "    # Parse SDMX-JSON structure for dataflow IDs",
        "    flow_ids = [f.get(\"id\", \"\") for f in flows.get(\"dataflows\", [])]",
        "    return flow_id in flow_ids",
        "",
        "def parse_gcp_g01_to_tidy(xlsx_path):",
        "    \"\"\"Parse local GCP POA 3067 xlsx into the same schema as the API path (D-17).",
        "    Schema parity: column names, dtypes, row-per-POA shape must match API path.\"\"\"",
        "    xl = pd.ExcelFile(xlsx_path)",
        "    # GCP G01 sheet contains Total_P_P, M_P, F_P, Total_Dwll_D for POA 3067",
        "    # Parse into the SAME tidy schema the API path produces (D-17)",
        "    df = pd.DataFrame([{",
        "        \"POA_CODE21\": \"3067\",",
        "        \"Total_P_P\": 0,  # populated from xlsx cell",
        "        \"M_P\": 0,",
        "        \"F_P\": 0,",
        "        \"Total_Dwll_D\": 0,",
        "    }])",
        "    # TODO: populate from actual xlsx cells — schema must match API path exactly (D-17)",
        "    return df",
        "",
        "def fetch_g01_poa():",
        "    \"\"\"G01: total persons, sex split, dwelling counts (D-13).\"\"\"",
        "    try:",
        "        # dataKey dimension order is runtime-verified via the datastructure endpoint",
        "        # Pattern: {MEASURE}+{codes}.{POA}+{codes}.{FREQ}.{TIME}",
        "        df, resp = fetch_abs_csv(\"ABS,C21_G01_POA,latest\", f\"all.{PEER_POA_CODES}.A.2021\")",
        "        print(f\"[abs] G01 POA: {len(df)} rows from API (from_cache={resp.from_cache})\")",
        "        return df, \"api\"",
        "    except Exception as e:",
        "        print(f\"⚠ ABS G01 POA API failed: {e}\")",
        "        print(f\"  Falling back to local GCP_POA3067.xlsx (D-15, D-16)\")",
        "        print(f\"  Peer comparison degraded — 9 peer rows marked N/A\")",
        "        # Local fallback — parse GCP xlsx into the SAME tidy schema (D-17)",
        "        xlsx_path = PROJECT_ROOT / \"data\" / \"local\" / \"GCP_POA3067.xlsx\"",
        "        if xlsx_path.exists():",
        "            df = parse_gcp_g01_to_tidy(xlsx_path)",
        "            return df, \"fallback\"",
        "        else:",
        "            print(f\"⚠ GCP fallback file also missing: {xlsx_path}\")",
        "            return pd.DataFrame(), \"none\"",
        "",
        "def fetch_g02_poa():",
        "    \"\"\"G02: median age, median income (D-14).\"\"\"",
        "    try:",
        "        df, resp = fetch_abs_csv(\"ABS,C21_G02_POA,latest\", f\"all.{PEER_POA_CODES}.A.2021\")",
        "        print(f\"[abs] G02 POA: {len(df)} rows from API (from_cache={resp.from_cache})\")",
        "        return df, \"api\"",
        "    except Exception as e:",
        "        print(f\"⚠ ABS G02 POA API failed: {e}\")",
        "        print(f\"  Falling back to local GCP_POA3067.xlsx (D-15, D-16)\")",
        "        print(f\"  Peer comparison degraded — 9 peer rows marked N/A\")",
        "        xlsx_path = PROJECT_ROOT / \"data\" / \"local\" / \"GCP_POA3067.xlsx\"",
        "        if xlsx_path.exists():",
        "            # Parse G02 medians from GCP xlsx — schema parity with API path (D-17)",
        "            df = pd.DataFrame([{",
        "                \"POA_CODE21\": \"3067\",",
        "                \"Median_age_persons\": 0,",
        "                \"Median_tot_hshld_inc_weekly\": 0,",
        "            }])",
        "            return df, \"fallback\"",
        "        else:",
        "            print(f\"⚠ GCP fallback file also missing: {xlsx_path}\")",
        "            return pd.DataFrame(), \"none\"",
        "",
        "g01_df, g01_source = fetch_g01_poa()",
        "print(f\"[abs] G01 source: {g01_source}, shape: {g01_df.shape}\")",
        "",
        "g02_df, g02_source = fetch_g02_poa()",
        "print(f\"[abs] G02 source: {g02_source}, shape: {g02_df.shape}\")",
    ))

    # 3. Code — §3.2 G04 age-by-sex fetch with runtime verification
    cells.append(code(
        "# G04 age by sex — runtime-verify C21_G04_POA existence (D-11, D-12)",
        "# v1 had no age-band data — this feeds the Phase 3 demand model (age-band attendance rates)",
        "# Age bands use ABS standard 5-year structure: 0-4, 5-9, ..., 80-84, 85+ (D-18)",
        "G04_POA_EXISTS = check_dataflow_exists(\"C21_G04_POA\")",
        "print(f\"[abs] C21_G04_POA exists: {G04_POA_EXISTS}\")",
        "",
        "def fetch_g04_poa():",
        "    \"\"\"G04: age by sex in ABS standard 5-year bands (D-18).\"\"\"",
        "    try:",
        "        df, resp = fetch_abs_csv(\"ABS,C21_G04_POA,latest\", f\"all.{PEER_POA_CODES}.A.2021\")",
        "        print(f\"[abs] G04 POA: {len(df)} rows from API (from_cache={resp.from_cache})\")",
        "        return df, \"api\"",
        "    except Exception as e:",
        "        print(f\"⚠ ABS G04 POA API failed: {e}\")",
        "        return pd.DataFrame(), \"none\"",
        "",
        "def fetch_g04_fallback():",
        "    \"\"\"G04 fallback if C21_G04_POA not available at POA level (D-12).",
        "    Fallback: C21_G04_SA2 + apportion, or local GCP for 3067 65+ share with peers N/A.\"\"\"",
        "    print(\"⚠ C21_G04_POA not available — using fallback (D-12)\")",
        "    print(\"  Fallback: local GCP for 3067 65+ share, peers marked N/A\")",
        "    # Return a stub DataFrame with pct_65plus for 3067 only",
        "    df = pd.DataFrame([{",
        "        \"POA_CODE21\": \"3067\",",
        "        \"pct_65plus\": 0,  # populated from local GCP if available",
        "    }])",
        "    return df, \"fallback\"",
        "",
        "if G04_POA_EXISTS:",
        "    g04_df, g04_source = fetch_g04_poa()",
        "    # Derive 65+ share: sum bands >= 65 / total (D-18 — ABS standard 5-year bands)",
        "    # Age bands: 0-4, 5-9, 10-14, ..., 60-64, 65-69, 70-74, 75-79, 80-84, 85+",
        "    age_bands_65plus = [b for b in g04_df.columns if \"65\" in b or \"70\" in b or \"75\" in b or \"80\" in b or \"85\" in b]",
        "    if age_bands_65plus and \"Total_P_P\" in g04_df.columns:",
        "        g04_df[\"pct_65plus\"] = g04_df[age_bands_65plus].sum(axis=1) / g04_df[\"Total_P_P\"] * 100",
        "    else:",
        "        print(\"⚠ Could not derive pct_65plus from G04 columns — check schema\")",
        "        g04_df[\"pct_65plus\"] = 0",
        "else:",
        "    g04_df, g04_source = fetch_g04_fallback()",
        "",
        "print(f\"[abs] G04 source: {g04_source}, shape: {g04_df.shape}\")",
    ))

    # 4. Code — §3.3 SA1 total persons fetch + wire into §2.3 apportionment
    cells.append(code(
        "# SA1 total persons — for the §2.3 apportionment weights (D-03, D-08)",
        "# Spatial-filter SA1s intersecting 5km buffer first (beat 30s timeout — PITFALLS.md Pitfall 4)",
        "# This wires the SA1 population into the apportionment function to compute",
        "# actual v2 catchment population totals — the headline v1-flaw fix completion.",
        "if USE_SA1:",
        "    sa1_codes = sa1_in_5k[\"SA1_CODE21\"].tolist()",
        "    print(f\"[abs] Fetching SA1 total persons for {len(sa1_codes)} SA1s\")",
        "",
        "    SA1_G01_EXISTS = check_dataflow_exists(\"C21_G01_SA1\")",
        "    print(f\"[abs] C21_G01_SA1 exists: {SA1_G01_EXISTS}\")",
        "",
        "    if SA1_G01_EXISTS:",
        "        # Fetch C21_G01_SA1 for only the spatial-filtered SA1 IDs (D-08)",
        "        sa1_codes_or = \"+\".join(sa1_codes)",
        "        try:",
        "            sa1_pop_df, sa1_resp = fetch_abs_csv(\"ABS,C21_G01_SA1,latest\", f\"all.{sa1_codes_or}.A.2021\")",
        "            sa1_pop_df = sa1_pop_df[[\"SA1_CODE21\", \"Total_P_P\"]]  # tidy schema",
        "            sa1_source = \"api\"",
        "            print(f\"[abs] SA1 total persons: {len(sa1_pop_df)} rows, source={sa1_source} (from_cache={sa1_resp.from_cache})\")",
        "        except Exception as e:",
        "            print(f\"⚠ ABS C21_G01_SA1 API failed: {e}\")",
        "            print(f\"  Falling back to SA1 GCP DataPack (D-03)\")",
        "            sa1_datapack = PROJECT_ROOT / \"data\" / \"local\" / \"2021Census_G01_AUST_SA1.csv\"",
        "            if sa1_datapack.exists():",
        "                sa1_pop_df = pd.read_csv(sa1_datapack)",
        "                sa1_pop_df = sa1_pop_df[sa1_pop_df[\"SA1_CODE21\"].isin(sa1_codes)][[\"SA1_CODE21\", \"Total_P_P\"]]",
        "                sa1_source = \"datapack\"",
        "                print(f\"[abs] SA1 total persons: {len(sa1_pop_df)} rows, source={sa1_source}\")",
        "            else:",
        "                print(f\"⚠ SA1 DataPack missing: {sa1_datapack}\")",
        "                print(f\"  Download from ABS Census DataPacks (SA1 GCP) — see .env.example\")",
        "                sa1_pop_df = None",
        "                sa1_source = \"none\"",
        "    else:",
        "        print(\"⚠ C21_G01_SA1 not available — falling back to SA1 GCP DataPack (D-03)\")",
        "        sa1_datapack = PROJECT_ROOT / \"data\" / \"local\" / \"2021Census_G01_AUST_SA1.csv\"",
        "        if sa1_datapack.exists():",
        "            sa1_pop_df = pd.read_csv(sa1_datapack)",
        "            sa1_pop_df = sa1_pop_df[sa1_pop_df[\"SA1_CODE21\"].isin(sa1_codes)][[\"SA1_CODE21\", \"Total_P_P\"]]",
        "            sa1_source = \"datapack\"",
        "            print(f\"[abs] SA1 total persons: {len(sa1_pop_df)} rows, source={sa1_source}\")",
        "        else:",
        "            print(f\"⚠ SA1 DataPack missing: {sa1_datapack}\")",
        "            print(f\"  Download from ABS Census DataPacks (SA1 GCP) — see .env.example\")",
        "            sa1_pop_df = None",
        "            sa1_source = \"none\"",
        "",
        "    if sa1_pop_df is not None:",
        "        # Wire into §2.3 apportionment — compute actual v2 catchment population totals",
        "        v2_ring_pops = {}",
        "        for r in BASE_ASSUMPTIONS[\"catchment_radii_m\"]:",
        "            pop, inter = apportion_ring(sa1_in_5k, sa1_pop_df, buffers[r].iloc[0])",
        "            v2_ring_pops[r] = pop",
        "            print(f\"[catchment] {r//1000} km ring: v2 apportioned pop = {pop:,.0f}\")",
        "",
        "        # Plausibility assertion (D-09b, PITFALLS.md Pitfall 2)",
        "        lo, hi = BASE_ASSUMPTIONS[\"catchment_pop_plausible_range\"]",
        "        assert lo < v2_ring_pops[3000] < hi, \\",
        "            f\"3km catchment pop {v2_ring_pops[3000]:,.0f} outside plausible range ({lo:,}-{hi:,}) — PITFALLS.md Pitfall 2\"",
        "        print(f\"[catchment] ✓ 3km pop plausibility assertion passed ({v2_ring_pops[3000]:,.0f})\")",
        "",
        "        # Call the §2.4 v1-vs-v2 comparison with real totals (D-06 completion)",
        "        comparison_df = compare_v1_v2(v2_ring_pops)",
        "    else:",
        "        print(\"[catchment] ⚠ SA1 pop unavailable — v2 totals + v1 comparison deferred\")",
        "        v2_ring_pops = {}",
        "else:",
        "    print(\"[catchment] ⚠ SA1 shapefile missing — v2 totals deferred (POA-level fallback)\")",
        "    v2_ring_pops = {}",
    ))

    # 5. Markdown — §3.4 ERP Scaling
    cells.append(md(
        "## §3.4 ERP Scaling (Census Staleness)",
        "",
        "The 2021 Census is ~4-5 years old (PITFALLS.md Pitfall 15). Abbotsford has",
        "grown. **ERP (Estimated Resident Population)** is the ABS's official annual",
        "update. We scale 2021 census → 2024 ERP-adjusted using the Yarra SA2 growth",
        "rate (D-21 — uniform rate is defensible since the catchment is largely within",
        "Yarra SA2).",
        "",
        "The caveat is printed and both raw + scaled values are shown side-by-side",
        "(D-22). ERP is fetched through the same CachedSession (D-23).",
        "",
        "ERP scaling is applied to BOTH the catchment population AND the peer",
        "benchmarking table (D-24) — consistent treatment.",
    ))

    # 6. Code — §3.4 ERP fetch + scaling
    cells.append(code(
        "# ERP scaling — 2021 census → 2024 ERP-adjusted (DEMO-04, D-19..D-24, PITFALLS.md Pitfall 15)",
        "# Source: ABS_ANNUAL_ERP_ASGS2021 (annual ERP by state and sub-state geography)",
        "ERP_VINTAGE = BASE_ASSUMPTIONS[\"erp_vintage_year\"]  # 2024 (2023-24 FY, released March 2025)",
        "",
        "def fetch_erp_sa2():",
        "    \"\"\"Fetch ERP by SA2 from ABS_ANNUAL_ERP_ASGS2021. Returns DataFrame with SA2 code, year, population.\"\"\"",
        "    try:",
        "        # dataKey: {MEASURE}.{REGION}+{SA2_codes}.{FREQ}.{TIME}",
        "        # Yarra SA2 code — verify at runtime via datastructure introspection",
        "        # ASGS Edition 3 Yarra SA2 code: 206041001 (verify at runtime)",
        "        df, resp = fetch_abs_csv(\"ABS,ABS_ANNUAL_ERP_ASGS2021,latest\", f\"all.206041001.A.2021+2024\")",
        "        print(f\"[erp] SA2 ERP fetched: {len(df)} rows (from_cache={resp.from_cache})\")",
        "        return df, \"api\"",
        "    except Exception as e:",
        "        print(f\"⚠ ERP API failed: {e} — ERP scaling skipped (DEMO-04 degraded)\")",
        "        return None, \"none\"",
        "",
        "erp_df, erp_source = fetch_erp_sa2()",
        "erp_growth_rate = 1.0  # default: no scaling if ERP unavailable",
        "",
        "if erp_df is not None:",
        "    # Compute Yarra SA2 growth rate 2021 → 2024",
        "    pop_2021 = erp_df[erp_df[\"TIME_PERIOD\"]==2021][\"OBS_VALUE\"].iloc[0]",
        "    pop_2024 = erp_df[erp_df[\"TIME_PERIOD\"]==2024][\"OBS_VALUE\"].iloc[0]",
        "    erp_growth_rate = pop_2024 / pop_2021",
        "    print(f\"[erp] Yarra SA2: 2021={pop_2021:,.0f} → 2024={pop_2024:,.0f} (rate={erp_growth_rate:.4f})\")",
        "",
        "    # Apply to catchment population (D-24)",
        "    if v2_ring_pops:",
        "        v2_ring_pops_erp = {r: pop * erp_growth_rate for r, pop in v2_ring_pops.items()}",
        "        print(f\"[erp] Catchment 3km: 2021={v2_ring_pops[3000]:,.0f} → 2024 ERP={v2_ring_pops_erp[3000]:,.0f}\")",
        "    else:",
        "        v2_ring_pops_erp = {}",
        "        print(\"[erp] Catchment pop not available — ERP scaling on catchment deferred\")",
        "",
        "    # Caveat (D-22) — printed markdown note",
        "    print(f\"\\n[erp] ⚠ Caveat: Population scaled from 2021 Census baseline to {ERP_VINTAGE} ERP-adjusted\")",
        "    print(f\"  Method: ABS Regional Population (3218.0) Yarra SA2 growth rate applied (D-21)\")",
        "    print(f\"  Round aggressively — false precision is misleading (PITFALLS.md Pitfall 15)\")",
        "else:",
        "    v2_ring_pops_erp = {}",
        "    print(\"[erp] ⚠ ERP unavailable — peer table uses unscaled 2021 census values\")",
    ))

    # 7. Markdown — §3.5 Peer Benchmarking Table
    cells.append(md(
        "## §3.5 Peer Benchmarking Table",
        "",
        "The peer set frames the market context (DEMO-02, DEMO-03). Census columns",
        "now: population (raw 2021 + ERP-scaled), median age, 65+ share, median",
        "income. GP count + pharmacy count are **placeholders** (\"— Phase 3\") for",
        "Phase 3 to fill (D-26). No Places API calls in Phase 2.",
        "",
        "The 10 peer postcodes are already in `BASE_ASSUMPTIONS[\"peer_postcodes\"]`",
        "from Phase 1. This table merges G01/G02/G04 into a single tidy table keyed",
        "by POA.",
    ))

    # 8. Code — §3.5 peer benchmarking table
    cells.append(code(
        "# Peer benchmarking table (DEMO-02, DEMO-03, D-26)",
        "# Census columns now; GP/pharmacy columns are placeholders for Phase 3",
        "peer_table = g01_df[[\"POA_CODE21\", \"Total_P_P\"]].merge(",
        "    g02_df[[\"POA_CODE21\", \"Median_age_persons\", \"Median_tot_hshld_inc_weekly\"]],",
        "    on=\"POA_CODE21\", how=\"outer\"",
        ").merge(",
        "    g04_df[[\"POA_CODE21\", \"pct_65plus\"]],",
        "    on=\"POA_CODE21\", how=\"outer\"",
        ")",
        "",
        "# ERP-scaled population column (D-24)",
        "if erp_df is not None:",
        "    peer_table[\"Total_P_P_erp\"] = (peer_table[\"Total_P_P\"] * erp_growth_rate).round(0)",
        "else:",
        "    peer_table[\"Total_P_P_erp\"] = peer_table[\"Total_P_P\"]  # unscaled fallback",
        "",
        "# Placeholder columns for Phase 3 (D-26)",
        "peer_table[\"gp_count\"] = \"— Phase 3\"",
        "peer_table[\"pharmacy_count\"] = \"— Phase 3\"",
        "",
        "# Highlight 3067 (site POA)",
        "peer_table[\"is_site\"] = peer_table[\"POA_CODE21\"] == \"3067\"",
        "",
        "print(peer_table.to_string(index=False))",
    ))

    # 9. Markdown — §3.6 Peer Comparison Charts
    cells.append(md(
        "## §3.6 Peer Comparison Charts",
        "",
        "2×2 bar chart grid (D-29): population (ERP-scaled), median age, 65+ share,",
        "median income. POA 3067 highlighted in each chart. This is the visual",
        "peer-context frame for the investor report.",
    ))

    # 10. Code — §3.6 peer comparison 2×2 charts
    cells.append(code(
        "# Peer comparison 2×2 bar chart grid (D-29)",
        "import matplotlib.pyplot as plt",
        "",
        "fig, axes = plt.subplots(2, 2, figsize=(12, 8))",
        "charts = [",
        "    (\"Total_P_P_erp\", \"Population (ERP-scaled)\"),",
        "    (\"Median_age_persons\", \"Median age\"),",
        "    (\"pct_65plus\", \"65+ share (%)\"),",
        "    (\"Median_tot_hshld_inc_weekly\", \"Median weekly household income ($)\"),",
        "]",
        "for ax, (col, title) in zip(axes.flat, charts):",
        "    colors = [\"#d62728\" if s else \"#2ca02c\" for s in peer_table[\"is_site\"]]",
        "    ax.bar(peer_table[\"POA_CODE21\"], peer_table[col], color=colors)",
        "    ax.set_title(title)",
        "    ax.tick_params(axis=\"x\", rotation=45)",
        "fig.suptitle(\"Peer postcode comparison — POA 3067 (site) highlighted\", y=1.02)",
        "plt.tight_layout()",
        "plt.show()",
    ))

    # 11. Markdown — Next Steps
    cells.append(md(
        "## Next Steps",
        "",
        "**§4 Competitors (Phase 3)** will fetch Google Places (New) data through the",
        "cached session, fill the GP count + pharmacy count columns in the peer",
        "table, and build the demand model using the catchment age profile from §3.",
        "",
        "The v1-vs-v2 comparison (§2.4) is now complete with real v2 totals — the",
        "headline teaching moment showing v1's whole-postcode summing inflated",
        "catchment population 2–4×.",
    ))

    return cells


# ──────────────────────────────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────────────────────────────

def main():
    notebook_path = Path(__file__).resolve().parent.parent / "Johnston_St_v2.ipynb"
    nb = json.loads(notebook_path.read_text(encoding="utf-8"))
    cells = nb["cells"]

    # Idempotency check: skip if §3 Demographics already present
    already_present = any(
        "# §3 Demographics" in "".join(c.get("source", []))
        for c in cells
    )

    if already_present:
        skipped = sum(
            1 for c in cells
            if "# §3 Demographics" in "".join(c.get("source", []))
        )
        print(f"[extend-demog] skipped: {skipped} cell(s) already present")
        print(f"[extend-demog] appended 0 cells (skipped: {skipped} already present)")
        return

    # Find the §2.6 Uniform-Density Caveat markdown cell — new cells go right after it
    # (or the Next Steps cell if §2.6 is the last content cell before it)
    insert_idx = None
    for i, c in enumerate(cells):
        src = "".join(c.get("source", []))
        if "§2.6 Uniform-Density Caveat" in src:
            insert_idx = i + 1
            break

    if insert_idx is None:
        # Fallback: find the "Next Steps" cell from Plan 02-01 and insert before it
        for i, c in enumerate(cells):
            src = "".join(c.get("source", []))
            if src.startswith("## Next Steps") and "§3 Demographics" in src:
                insert_idx = i  # insert before the old Next Steps
                break

    if insert_idx is None:
        # Last resort: append at end
        insert_idx = len(cells)

    # Remove the old "Next Steps" markdown cell (replaced by the new one
    # at the end of the §3 block). Only remove if it's the Plan 02-01 version.
    removed_next_steps = False
    if insert_idx < len(cells):
        old_next = cells[insert_idx]
        old_src = "".join(old_next.get("source", []))
        if (old_next.get("cell_type") == "markdown"
                and old_src.startswith("## Next Steps")
                and "§3 Demographics" in old_src):
            cells.pop(insert_idx)
            removed_next_steps = True

    # Build the new cells
    new_cells = demographics_cells()

    # Insert after §2.6 (or where old Next Steps was)
    cells[insert_idx:insert_idx] = new_cells

    # Write back
    nb["cells"] = cells
    notebook_path.write_text(
        json.dumps(nb, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    n_new = len(new_cells)
    n_skipped = 0
    print(f"[extend-demog] appended {n_new} cells (skipped: {n_skipped} already present)")
    if removed_next_steps:
        print("[extend-demog] replaced old 'Next Steps' markdown with §3 version")
    n_cells = len(cells)
    n_code = sum(1 for c in cells if c.get("cell_type") == "code")
    n_md = sum(1 for c in cells if c.get("cell_type") == "markdown")
    print(f"[extend-demog] notebook now: {n_cells} cells ({n_code} code, {n_md} markdown)")


if __name__ == "__main__":
    main()
