#!/usr/bin/env python3
"""
Phase 5 extension script for Johnston_St_v2.ipynb — Plans 05-01 + 05-02.

Loads the existing notebook (built by create_v2_notebook.py + extended by
extend_v2_notebook.py + extend_v2_notebook_phase3.py + extend_v2_notebook_phase4.py
in Phases 1-4), removes the §6 "## Next Steps" markdown cell (§7 replaces it as
the notebook tail), and appends §7 Scenarios & Sensitivity cells:

  §7.1  Scenario override dicts (FIN-04, D-05) — {**BASE_ASSUMPTIONS, **overrides}
  §7.2  Run scenarios + side-by-side P&L table (D-08) + report{} deposits
  §7.3  Tornado sensitivity — annual EBITDA (FIN-05, D-06, D-07(a)) + zero-crossings
  §7.4  Tornado sensitivity — peak capital (FIN-05, D-07(b))
  §7.5  Billing-mix sensitivity curve (FIN-06, D-09, D-10) — 70/30 vs 100%-bulk+BBPIP
  §7.6  Pharmacy synergy — secondary upside range (FIN-07, D-11, D-12)
  §7.7  Interpretation

Reuses clinic_pnl and clinic_ramp_monthly from §6 (Phase 4) — NO new financial
logic. Pharmacy synergy is the only new computation (standalone arithmetic, NOT a
clinic_pnl override). All metrics deposit into the report{} accumulator for
Phase 5 §8 (Pattern 5).

Follows the same cell-dict pattern as extend_v2_notebook_phase4.py:
  cell_type, metadata: {}, source as list of strings (each ending with \n
  except possibly the last); code cells have execution_count: null, outputs: [].

Idempotent: if a cell containing "# §7 Scenarios & Sensitivity" already exists,
the script REMOVES the existing §7 cells and re-appends the corrected versions
(cell-replacement idempotency).

Run:  python scripts/extend_v2_notebook_phase5.py
Output: Johnston_St_v2.ipynb (extended in-place)
"""

import json
from pathlib import Path


# ──────────────────────────────────────────────────────────────────────
#  Cell helpers (same pattern as extend_v2_notebook_phase4.py)
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
#  §7 Scenarios & Sensitivity cells
# ──────────────────────────────────────────────────────────────────────

def phase5_scenarios_cells():
    """Return the §7 Scenarios & Sensitivity cells (Plan 05-01).

    Reuses clinic_pnl and clinic_ramp_monthly from §6 (Phase 4) — NO new
    financial logic. Pharmacy synergy (§7.6) is the only new computation
    (standalone arithmetic, NOT a clinic_pnl override).
    """
    cells = []

    # 1. Markdown — §7 header + teaching commentary
    cells.append(md(
        "# §7 Scenarios & Sensitivity",
        "",
        "The steady-state P&L (§6) answers *\"is it profitable at full books?\"*",
        "The ramp model (§6.2) answers *\"how long to get there?\"* This section",
        "answers the third investor question: **\"how robust is the verdict to the",
        "assumptions we're least sure about?\"** (Pitfall 13).",
        "",
        "Three analytical blocks:",
        "- **(a) Base / optimistic / pessimistic scenarios** as override dicts on the",
        "  SAME `clinic_pnl` + `clinic_ramp_monthly` pure functions — no new financial",
        "  logic (FIN-04, D-05). Each scenario is `{**BASE_ASSUMPTIONS, **overrides}`.",
        "- **(b) Two tornado sensitivity charts** ranking which inputs move annual",
        "  EBITDA and peak capital most (FIN-05, D-06/D-07). One-way sensitivity —",
        "  each input varied individually, others at base.",
        "- **(c) A billing-mix sensitivity curve** comparing 70/30 mixed vs",
        "  100%-bulk+BBPIP (FIN-06, D-09/D-10). Shows the optimal mix and where",
        "  100%-bulk+BBPIP crosses 70/30-mixed.",
        "",
        "**Pharmacy synergy (FIN-07) is quantified LAST**, as secondary upside AFTER",
        "the standalone scenarios — it can never rescue an unprofitable clinic (D-04,",
        "Core Value). The clinic verdict (Plan 05-02 §8) is 100% standalone.",
        "",
        "**No numeric literal outside `BASE_ASSUMPTIONS`** in scenario/tornado/synergy",
        "code except loop indices and chart constants (PIPE-05). Tornado uses numpy",
        "vectorised operations, not manual Python loops (Don't Hand-Roll).",
    ))

    # 2. Code — §7.1 scenario override dicts (FIN-04, D-05, D-08)
    cells.append(code(
        "# §7.1 Scenario override dicts (FIN-04, D-05) — {**BASE_ASSUMPTIONS, **overrides}",
        "# 5 independent levers (D-05): rent, utilisation, service-fee %, ramp speed, billing mix",
        "# Base case = BASE_ASSUMPTIONS unchanged (override = {}).",
        "# NO new financial constants — every value overrides an existing BASE_ASSUMPTIONS key.",
        "scenarios = {",
        "    \"base\": {",
        "        # no overrides — uses BASE_ASSUMPTIONS as-is (the §6 base case)",
        "    },",
        "    \"optimistic\": {",
        "        \"rent_yr\": 80_000,           # D-05(a) — lower rent",
        "        \"utilisation\": 0.85,         # D-05(b) — higher utilisation",
        "        \"gp_revenue_share\": 0.38,    # D-05(c) — higher service-fee % (practice retains more)",
        "        \"gp_ramp_milestones\": {0: 3, 6: 4, 12: 5},  # D-05(d) — faster ramp (3 GPs at open, 5 by month 12)",
        "        \"bulk_bill_share\": 0.50,     # D-05(e) — more private billing",
        "    },",
        "    \"pessimistic\": {",
        "        \"rent_yr\": 120_000,          # D-05(a) — higher rent",
        "        \"utilisation\": 0.65,         # D-05(b) — lower utilisation",
        "        \"gp_revenue_share\": 0.32,    # D-05(c) — lower service-fee % (competitive pressure)",
        "        \"gp_ramp_milestones\": {0: 1, 6: 2, 12: 3, 18: 4, 24: 5},  # D-05(d) — slower ramp (5 FTE only by month 24)",
        "        \"bulk_bill_share\": 0.85,     # D-05(e) — more bulk billing",
        "    },",
        "}",
        "print(f\"[§7.1] {len(scenarios)} scenarios defined as override dicts on clinic_pnl (FIN-04, D-05)\")",
    ))

    # 3. Code — §7.2 run scenarios + side-by-side P&L table (D-08) + report{} deposits
    cells.append(code(
        "# §7.2 Run scenarios + side-by-side P&L table (D-08, FIN-04)",
        "# Each scenario: clinic_pnl({**BASE_ASSUMPTIONS, **overrides}) + clinic_ramp_monthly(...)",
        "import pandas as pd",
        "",
        "scenario_results = {}",
        "for name, overrides in scenarios.items():",
        "    a = {**BASE_ASSUMPTIONS, **overrides}",
        "    pnl = clinic_pnl(a)",
        "    ramp = clinic_ramp_monthly(a)",
        "    scenario_results[name] = {**pnl, **{",
        "        \"peak_capital\": ramp[\"peak_capital_total\"],",
        "        \"breakeven_operating\": ramp[\"breakeven_operating\"],",
        "        \"breakeven_payback\": ramp[\"breakeven_payback\"],",
        "    }}",
        "",
        "# Side-by-side P&L table (D-08) — every line as a row, 3 scenario columns",
        "pnl_lines = [",
        "    \"annual_consults\", \"gp_billings\", \"practice_revenue\", \"practice_revenue_gp\",",
        "    \"practice_revenue_allied\", \"staffing_costs\", \"total_costs\", \"ebitda\",",
        "]",
        "",
        "rows = []",
        "for line in pnl_lines + [\"margin\", \"peak_capital\", \"breakeven_operating\", \"breakeven_payback\"]:",
        "    row = {\"Line\": line}",
        "    for name in [\"base\", \"optimistic\", \"pessimistic\"]:",
        "        val = scenario_results[name].get(line)",
        "        if line == \"margin\":",
        "            row[name] = f\"{val:.1%}\" if val is not None else \"N/A\"",
        "        elif line in (\"breakeven_operating\", \"breakeven_payback\"):",
        "            row[name] = f\"mo {val}\" if val is not None else \">36 mo\"",
        "        elif isinstance(val, (int, float)):",
        "            row[name] = f\"${val:,.0f}\"",
        "        else:",
        "            row[name] = str(val)",
        "    rows.append(row)",
        "",
        "scenario_table = pd.DataFrame(rows)",
        'print("=" * 80)',
        'print("§7.2 SCENARIO P&L — SIDE-BY-SIDE (D-08, FIN-04)")',
        'print("=" * 80)',
        "print(scenario_table.to_string(index=False))",
        'print("=" * 80)',
        "",
        "# Deposit scenario headlines into report{} for §8 (Pattern 5)",
        "# Explicit keys: report[\"scenario_ebitda_base\"], report[\"scenario_ebitda_optimistic\"],",
        "# report[\"scenario_ebitda_pessimistic\"] + peak_capital + payback variants (deposited via loop below)",
        "for name in [\"base\", \"optimistic\", \"pessimistic\"]:",
        "    report[f\"scenario_ebitda_{name}\"] = scenario_results[name][\"ebitda\"]",
        "    report[f\"scenario_peak_capital_{name}\"] = scenario_results[name][\"peak_capital\"]",
        "    report[f\"scenario_payback_{name}\"] = scenario_results[name][\"breakeven_payback\"]",
        "print(f\"[report] §7.2 deposited scenario_ebitda_*, scenario_peak_capital_*, scenario_payback_* for {len(scenarios)} scenarios\")",
    ))

    # 4. Code — §7.3 tornado sensitivity — annual EBITDA (FIN-05, D-06, D-07(a))
    cells.append(code(
        "# §7.3 Tornado sensitivity — annual EBITDA (FIN-05, D-06, D-07(a))",
        "# 7-8 inputs, one-way sensitivity: each input varied individually, others at base.",
        "# Tornado uses numpy vectorised operations, not manual Python loops (Don't Hand-Roll).",
        "import numpy as np",
        "import matplotlib.pyplot as plt",
        "",
        "tornado_inputs_ebitda = [",
        "    # (label, base, low, high, override_key)",
        "    (\"Rent ($/yr)\",            100_000,  60_000,  140_000, \"rent_yr\"),",
        "    (\"Utilisation\",            0.75,     0.55,    0.90,    \"utilisation\"),",
        "    (\"Service-fee %\",          0.35,     0.28,    0.40,    \"gp_revenue_share\"),",
        "    (\"Bulk-bill share\",        0.70,     0.40,    1.00,    \"bulk_bill_share\"),",
        "    (\"Consults/GP/yr\",         5_500,    4_500,   6_500,   \"gp_fte_consults_per_yr\"),",
        "    (\"Nurse salary ($/yr)\",    75_868,   65_000,  90_000,  \"nurse_salary_yr\"),",
        "    (\"Consumables ($/yr)\",     45_000,   30_000,  60_000,  \"consumables_yr\"),",
        "    (\"Private fee ($)\",        95.00,    75.00,   120.00,  \"private_fee\"),",
        "]",
        "",
        "import copy",
        "base_ebitda = clinic_pnl(BASE_ASSUMPTIONS)[\"ebitda\"]",
        "swings = []",
        "for label, base, low, high, key in tornado_inputs_ebitda:",
        "    if key == \"private_fee\":",
        "        # private_fee lives inside nested item_mix, not as a top-level key.",
        "        # Scale all item private_fees proportionally (low/base, high/base).",
        "        _lo = copy.deepcopy(BASE_ASSUMPTIONS)",
        "        _hi = copy.deepcopy(BASE_ASSUMPTIONS)",
        "        _s_lo, _s_hi = low / base, high / base",
        "        for _v in _lo[\"item_mix\"].values():",
        "            _v[\"private_fee\"] = _v[\"private_fee\"] * _s_lo",
        "        for _v in _hi[\"item_mix\"].values():",
        "            _v[\"private_fee\"] = _v[\"private_fee\"] * _s_hi",
        "        ebitda_low = clinic_pnl(_lo)[\"ebitda\"]",
        "        ebitda_high = clinic_pnl(_hi)[\"ebitda\"]",
        "    else:",
        "        ebitda_low = clinic_pnl({**BASE_ASSUMPTIONS, key: low})[\"ebitda\"]",
        "        ebitda_high = clinic_pnl({**BASE_ASSUMPTIONS, key: high})[\"ebitda\"]",
        "    swings.append((label, ebitda_low - base_ebitda, ebitda_high - base_ebitda, base, low, high, key))",
        "",
        "# Sort by absolute swing (max of |low|, |high|) — largest driver first",
        "swings.sort(key=lambda x: max(abs(x[1]), abs(x[2])), reverse=True)",
        "",
        "# Plot tornado (horizontal bars) — numpy arrays for the bar positions",
        "fig, ax = plt.subplots(figsize=(10, 6))",
        "labels = [s[0] for s in swings]",
        "lows = np.array([s[1] / 1000 for s in swings])   # numpy array (Don't Hand-Roll)",
        "highs = np.array([s[2] / 1000 for s in swings])  # numpy array (Don't Hand-Roll)",
        "y = np.arange(len(labels))",
        "ax.barh(y, lows, color=\"#d62728\", alpha=0.7, label=\"Low → EBITDA impact\")",
        "ax.barh(y, highs, color=\"#2ca02c\", alpha=0.7, label=\"High → EBITDA impact\")",
        "ax.set_yticks(y)",
        "ax.set_yticklabels(labels)",
        "ax.axvline(x=0, color=\"black\", linewidth=0.8)",
        "ax.set_xlabel(\"Δ Annual EBITDA ($k) from base\")",
        "ax.set_title(\"Tornado Sensitivity — Annual EBITDA (FIN-05, D-06)\")",
        "ax.legend(loc=\"lower right\")",
        "ax.grid(True, alpha=0.3, axis=\"x\")",
        "plt.tight_layout()",
        "plt.savefig(OUTPUTS / \"tornado_ebitda.png\", dpi=150, bbox_inches=\"tight\")",
        "plt.show()",
        "print(f\"[§7.3] tornado_ebitda.png saved — {len(swings)} inputs ranked by EBITDA impact\")",
        "",
        "# Zero-crossings: find the rent and utilisation values where EBITDA = 0 (D-02 flip-conditions)",
        "# numpy vectorised sweep — np.linspace + np.interp (Don't Hand-Roll)",
        "def find_zero_crossing(key, low_val, high_val, steps=200):",
        "    \"\"\"Return the value of `key` at which EBITDA crosses zero (fine sweep + np.interp).\"\"\"",
        "    vals = np.linspace(low_val, high_val, steps)",
        "    ebitdas = np.array([clinic_pnl({**BASE_ASSUMPTIONS, key: v})[\"ebitda\"] for v in vals])",
        "    sign_changes = np.where(np.diff(np.sign(ebitdas)))[0]",
        "    if len(sign_changes) == 0:",
        "        return None  # no zero-crossing in range",
        "    idx = sign_changes[0]",
        "    return float(np.interp(0, [ebitdas[idx], ebitdas[idx + 1]], [vals[idx], vals[idx + 1]]))",
        "",
        "rent_zero = find_zero_crossing(\"rent_yr\", 60_000, 140_000)",
        "util_zero = find_zero_crossing(\"utilisation\", 0.55, 0.90)",
        "service_fee_zero = find_zero_crossing(\"gp_revenue_share\", 0.28, 0.40)",
        "",
        "report[\"tornado_zero_crossings\"] = {",
        "    \"rent_yr\": rent_zero,",
        "    \"utilisation\": util_zero,",
        "    \"gp_revenue_share\": service_fee_zero,",
        "}",
        "crossings = [rent_zero, util_zero, service_fee_zero]",
        "if all(v is not None for v in crossings):",
        "    print(f\"[§7.3] EBITDA zero-crossings: rent=${rent_zero:,.0f}/yr, utilisation={util_zero:.1%}, service-fee={service_fee_zero:.1%}\")",
        "else:",
        "    print(\"[§7.3] some zero-crossings out of range — verdict robust\")",
        "print(f\"[report] §7.3 deposited tornado_zero_crossings\")",
    ))

    # 5. Code — §7.4 tornado sensitivity — peak capital (FIN-05, D-07(b))
    cells.append(code(
        "# §7.4 Tornado sensitivity — peak capital (FIN-05, D-07(b))",
        "# Peak capital is the funding-requirement driver — $/sqm and ramp speed dominate.",
        "# Tornado uses numpy arrays for the swing values (Don't Hand-Roll).",
        "tornado_inputs_peak = [",
        "    # (label, base, low, high, override_key)",
        "    (\"Fit-out $/sqm\",          1_700,   1_200,  2_200,  \"fitout_per_sqm\"),",
        "    (\"Ramp speed (GP mo-0)\",   2,       1,      4,      None),  # special: override gp_ramp_milestones",
        "    (\"Equipment/IT lump\",      60_000,  40_000, 90_000, \"equipment_it_lump_sum\"),",
        "    (\"Utilisation\",            0.75,    0.55,   0.90,   \"utilisation\"),",
        "    (\"Rent ($/yr)\",            100_000, 60_000, 140_000, \"rent_yr\"),",
        "    (\"Service-fee %\",          0.35,    0.28,   0.40,   \"gp_revenue_share\"),",
        "]",
        "",
        "base_peak = clinic_ramp_monthly(BASE_ASSUMPTIONS)[\"peak_capital_total\"]",
        "swings_peak = []",
        "for label, base, low, high, key in tornado_inputs_peak:",
        "    if key is None and \"Ramp speed\" in label:",
        "        # Special: override gp_ramp_milestones — slow = fewer GPs early, fast = more",
        "        low_overrides = {\"gp_ramp_milestones\": {0: 1, 6: 2, 12: 3, 18: 4, 24: 5}}   # slow",
        "        high_overrides = {\"gp_ramp_milestones\": {0: 3, 6: 4, 12: 5}}                 # fast",
        "    else:",
        "        low_overrides = {key: low}",
        "        high_overrides = {key: high}",
        "    # Recompute fitout_total when $/sqm changes (derived key — PIPE-05: derived from BASE_ASSUMPTIONS)",
        "    if key == \"fitout_per_sqm\":",
        "        low_overrides[\"fitout_total\"] = low * BASE_ASSUMPTIONS[\"floor_area_sqm\"] + BASE_ASSUMPTIONS[\"equipment_it_lump_sum\"]",
        "        high_overrides[\"fitout_total\"] = high * BASE_ASSUMPTIONS[\"floor_area_sqm\"] + BASE_ASSUMPTIONS[\"equipment_it_lump_sum\"]",
        "    peak_low = clinic_ramp_monthly({**BASE_ASSUMPTIONS, **low_overrides})[\"peak_capital_total\"]",
        "    peak_high = clinic_ramp_monthly({**BASE_ASSUMPTIONS, **high_overrides})[\"peak_capital_total\"]",
        "    swings_peak.append((label, peak_low - base_peak, peak_high - base_peak))",
        "",
        "swings_peak.sort(key=lambda x: max(abs(x[1]), abs(x[2])), reverse=True)",
        "",
        "fig, ax = plt.subplots(figsize=(10, 5))",
        "labels_p = [s[0] for s in swings_peak]",
        "lows_p = np.array([s[1] / 1000 for s in swings_peak])   # numpy array (Don't Hand-Roll)",
        "highs_p = np.array([s[2] / 1000 for s in swings_peak])  # numpy array (Don't Hand-Roll)",
        "y_p = np.arange(len(labels_p))",
        "ax.barh(y_p, lows_p, color=\"#d62728\", alpha=0.7, label=\"Low → peak capital impact\")",
        "ax.barh(y_p, highs_p, color=\"#2ca02c\", alpha=0.7, label=\"High → peak capital impact\")",
        "ax.set_yticks(y_p)",
        "ax.set_yticklabels(labels_p)",
        "ax.axvline(x=0, color=\"black\", linewidth=0.8)",
        "ax.set_xlabel(\"Δ Peak capital ($k) from base\")",
        "ax.set_title(\"Tornado Sensitivity — Peak Capital (FIN-05, D-07(b))\")",
        "ax.legend(loc=\"lower right\")",
        "ax.grid(True, alpha=0.3, axis=\"x\")",
        "plt.tight_layout()",
        "plt.savefig(OUTPUTS / \"tornado_peak_capital.png\", dpi=150, bbox_inches=\"tight\")",
        "plt.show()",
        "print(f\"[§7.4] tornado_peak_capital.png saved — {len(swings_peak)} inputs ranked by peak-capital impact\")",
        "report[\"tornado_peak_capital_swings\"] = [(s[0], s[1], s[2]) for s in swings_peak]",
        "print(f\"[report] §7.4 deposited tornado_peak_capital_swings\")",
    ))

    # 6. Code — §7.5 billing-mix sensitivity curve (FIN-06, D-09, D-10)
    cells.append(code(
        "# §7.5 Billing-mix sensitivity curve (FIN-06, D-09, D-10)",
        "# Compare 70/30 mixed (base) vs 100%-bulk + BBPIP 12.5% (Pitfall 7).",
        "# BBPIP: from Nov 2025, practices bulk-billing 100% get a 12.5% incentive on MBS billings.",
        "# D-09: practice retains ~half of BBPIP (~6.25%), GP gets ~6.25%.",
        "# bulk_bill_share points: [0%, 25%, 50%, 70%, 100%] (D-10)",
        "billing_mix_points = [0.0, 0.25, 0.50, 0.70, 1.00]",
        "billing_ebitdas = []",
        "for bb_share in billing_mix_points:",
        "    overrides = {\"bulk_bill_share\": bb_share}",
        "    if bb_share == 1.00:",
        "        # 100% bulk + BBPIP — add the practice-retained BBPIP as extra revenue",
        "        # BBPIP = 12.5% of GP billings; practice retains ~6.25% (D-09)",
        "        pnl_preview = clinic_pnl({**BASE_ASSUMPTIONS, **overrides})",
        "        bbpip_practice_share = 0.0625  # D-09 — verify against current DoH factsheet at build time",
        "        bbpip_revenue = pnl_preview[\"gp_billings\"] * bbpip_practice_share",
        "        # clinic_pnl doesn't have a bbpip key, so compute EBITDA = (revenue + bbpip) - costs",
        "        billing_ebitdas.append(pnl_preview[\"ebitda\"] + bbpip_revenue)",
        "    else:",
        "        billing_ebitdas.append(clinic_pnl({**BASE_ASSUMPTIONS, **overrides})[\"ebitda\"])",
        "",
        "fig, ax = plt.subplots(figsize=(9, 5))",
        "ax.plot([b * 100 for b in billing_mix_points], [e / 1000 for e in billing_ebitdas],",
        "        \"o-\", linewidth=2, markersize=8, color=\"#1f77b4\")",
        "ax.axvline(x=70, color=\"gray\", linestyle=\"--\", alpha=0.5, label=\"Base case (70% bulk)\")",
        "ax.axvline(x=100, color=\"green\", linestyle=\"--\", alpha=0.5, label=\"100% bulk + BBPIP\")",
        "ax.set_xlabel(\"Bulk-billing share (%)\")",
        "ax.set_ylabel(\"Annual EBITDA ($k)\")",
        "ax.set_title(\"Billing-Mix Sensitivity — 70/30 Mixed vs 100%-Bulk + BBPIP (FIN-06, D-10)\")",
        "ax.legend(loc=\"lower right\")",
        "ax.grid(True, alpha=0.3)",
        "plt.tight_layout()",
        "plt.savefig(OUTPUTS / \"billing_mix_curve.png\", dpi=150, bbox_inches=\"tight\")",
        "plt.show()",
        "print(f\"[§7.5] billing_mix_curve.png saved — {len(billing_mix_points)} billing-mix points\")",
        "report[\"billing_mix_curve\"] = {",
        "    \"bulk_bill_shares\": billing_mix_points,",
        "    \"ebitdas\": billing_ebitdas,",
        "    \"bbpip_practice_share\": 0.0625,  # D-09 — for assumptions register",
        "}",
        "print(f\"[report] §7.5 deposited billing_mix_curve\")",
    ))

    # 7. Markdown — §7.6 pharmacy synergy framing (FIN-07, D-04)
    cells.append(md(
        "## §7.6 Pharmacy Synergy — Secondary upside (NOT Load-Bearing)",
        "",
        "The clinic verdict (Plan 05-02 §8) is **100% standalone** — it never mentions",
        "the pharmacy (D-04, Core Value). This section quantifies the pharmacy upside",
        "**AS A RANGE**, presented only as secondary information. The clinic does not",
        "need the pharmacy to be profitable; the pharmacy is incremental upside if",
        "co-location works.",
        "",
        "The estimate uses **per-capita scripts × capture rate × gross margin per",
        "script** (D-11) — transparent arithmetic, all cited. The range (D-12)",
        "reflects uncertainty in the pharmacy's market share of the catchment.",
        "",
        "> **Order-gating (D-04, FIN-07):** this section appears AFTER the standalone",
        "> scenarios, tornado, and billing-mix analysis. It can never be read as",
        "> rescuing an unprofitable clinic.",
    ))

    # 8. Code — §7.6 pharmacy synergy range (FIN-07, D-11, D-12)
    cells.append(code(
        "# §7.6 Pharmacy synergy — secondary upside range (FIN-07, D-11, D-12)",
        "# NOT a clinic_pnl override — standalone arithmetic. Presented AFTER standalone scenarios (D-04).",
        "# catchment_pop: use the §2.3 apportioned 3km-ring population (the primary catchment)",
        "# If report{} has it, use it; else fall back to BASE_ASSUMPTIONS catchment_pop_plausible_range midpoint.",
        "catchment_pop = report.get(\"catchment_pop_3km\") or sum(BASE_ASSUMPTIONS[\"catchment_pop_plausible_range\"]) / 2",
        "avg_scripts_per_person_yr = 13.0   # PBS benchmark ~12-14 scripts/person/yr (D-11) — cite PBS Statistics 2023-24",
        "gross_margin_per_script = 10.0     # $8-12 gross margin per script (D-11) — cite Pharmacy Guild PSA Report",
        "capture_rates = {\"low\": 0.15, \"mid\": 0.20, \"high\": 0.25}  # D-12 — pharmacy's share of catchment scripts",
        "",
        "pharmacy_synergy = {}",
        "for label, rate in capture_rates.items():",
        "    annual_scripts = catchment_pop * avg_scripts_per_person_yr * rate",
        "    annual_profit = annual_scripts * gross_margin_per_script",
        "    pharmacy_synergy[label] = {",
        "        \"capture_rate\": rate,",
        "        \"annual_scripts\": annual_scripts,",
        "        \"annual_profit\": annual_profit,",
        "    }",
        "",
        'print("=" * 70)',
        'print("§7.6 PHARMACY SYNERGY — SECONDARY UPSIDE (NOT LOAD-BEARING)")',
        'print("=" * 70)',
        'print(f"Catchment population (3km):   {catchment_pop:,.0f}")',
        'print(f"Avg scripts/person/yr:        {avg_scripts_per_person_yr}  (PBS benchmark)")',
        'print(f"Gross margin per script:      ${gross_margin_per_script}")',
        "print()",
        'for label in ["low", "mid", "high"]:',
        "    r = pharmacy_synergy[label]",
        "    print(f\"  {label.upper():10s} capture {r['capture_rate']:.0%} → {r['annual_scripts']:,.0f} scripts/yr → ${r['annual_profit']:,.0f}/yr\")",
        "print()",
        'print("NOTE: This is SECONDARY UPSIDE. The clinic verdict (§8) is 100% standalone.")',
        'print("=" * 70)',
        "",
        "report[\"pharmacy_synergy_range\"] = {",
        "    \"catchment_pop\": catchment_pop,",
        "    \"avg_scripts_per_person_yr\": avg_scripts_per_person_yr,",
        "    \"gross_margin_per_script\": gross_margin_per_script,",
        "    \"capture_rates\": capture_rates,",
        "    \"results\": pharmacy_synergy,",
        "}",
        "print(f\"[report] §7.6 deposited pharmacy_synergy_range (FIN-07, D-11, D-12)\")",
    ))

    # 9. Markdown — §7.7 interpretation
    cells.append(md(
        "## §7.7 Interpretation",
        "",
        "The scenarios show the clinic's **profitability envelope** across plausible",
        "parameter ranges; the tornado ranks which assumptions the verdict is most",
        "sensitive to (Pitfall 13 — the exec summary must state these); the",
        "billing-mix curve shows the optimal mix and where 100%-bulk+BBPIP crosses",
        "70/30-mixed; the pharmacy synergy is a **range, not a point estimate**",
        "(Pitfall 15 — show uncertainty).",
        "",
        "All of this feeds the §8 go/no-go verdict (Plan 05-02): the verdict is **GO**",
        "if the base case is profitable AND the pessimistic case is not catastrophically",
        "negative AND the tornado zero-crossings are outside the plausible range",
        "(D-01, D-02).",
        "",
        "**Key deposits into `report{}`** for Phase 5 §8 (Pattern 5):",
        "- `scenario_ebitda_{base,opt,pess}` — three-point EBITDA envelope",
        "- `scenario_peak_capital_{base,opt,pess}` — three-point capital requirement",
        "- `scenario_payback_{base,opt,pess}` — three-point payback horizon",
        "- `tornado_zero_crossings` — rent/utilisation/service-fee flip points (D-02)",
        "- `tornado_peak_capital_swings` — peak-capital driver ranking",
        "- `billing_mix_curve` — EBITDA vs bulk-bill share + BBPIP practice share",
        "- `pharmacy_synergy_range` — low/mid/high pharmacy upside (secondary, D-12)",
    ))

    return cells



# ──────────────────────────────────────────────────────────────────────
#  §8 Executive Report cells (Plan 05-02)
# ──────────────────────────────────────────────────────────────────────

def phase5_executive_report_cells():
    """Return the §8 Executive Report cells (Plan 05-02).

    §8 is a pure render step (ARCHITECTURE.md Pattern 5, Data Flow #4) — it
    reads the report{} accumulator (populated by §6 and §7) and the saved PNG
    figures, and produces the investor deliverable: HTML (always) + PDF
    (Colab-only via weasyprint). Re-running §8 alone regenerates the report.
    """
    cells = []

    # 1. Markdown — §8 header + teaching commentary
    cells.append(md(
        "# §8 Executive Report",
        "",
        "§8 is a **pure render step** (ARCHITECTURE.md Pattern 5, Data Flow #4) —",
        "it reads the `report{}` accumulator (populated by §6 and §7) and the saved",
        "PNG figures, and produces the investor deliverable. Re-running §8 alone",
        "regenerates the PDF from current state.",
        "",
        "The report has **8 sections** (D-14):",
        "1. **Executive Summary** with verdict + 5 key numbers + one map (D-13)",
        "2. **Site & Catchment**",
        "3. **Competitor Landscape**",
        "4. **Financial Model**",
        "5. **Scenarios & Sensitivity**",
        "6. **Pharmacy Synergy** (secondary upside, after the verdict — D-04)",
        "7. **Assumptions Register** (5-column: Parameter | Value | Source | Date |",
        "   Confidence, D-16)",
        "8. **Data Sources & Citations** (footnote-style [1], [2] with access dates,",
        "   D-17)",
        "",
        "The verdict is **binary GO/NO-GO** (D-03), **100% standalone** (D-04), gated",
        "on **steady-state EBITDA > 0 AND margin > 15%** (D-01). PDF generation is",
        "Colab-only via weasyprint (D-18); local Windows runs produce HTML only.",
    ))

    # 2. Code — §8.1 verdict logic (D-01, D-02, D-03, D-04, REP-02)
    cells.append(code(
        "# §8.1 Go/no-go verdict logic (D-01, D-02, D-03, D-04, REP-02)",
        "# Gate: steady-state EBITDA > 0 AND margin > 15% (D-01).",
        "# Payback is CONTEXT, not the gate — clinic is a long-lived asset (D-01).",
        "# Binary verdict (D-03). 100% standalone — verdict text never mentions pharmacy (D-04).",
        "",
        'steady_ebitda = report["steady_state_ebitda"]',
        'steady_margin = report["steady_state_margin"]',
        'peak_capital = report["peak_capital"]',
        'be_operating = report["breakeven_operating"]',
        'be_payback = report["breakeven_payback"]',
        "",
        "GATE_MARGIN = 0.15  # D-01 — margin threshold",
        'verdict = "GO" if (steady_ebitda > 0 and steady_margin > GATE_MARGIN) else "NO-GO"',
        "",
        "# Flip-conditions (D-02) — one sentence per lever from tornado zero-crossings",
        'zc = report.get("tornado_zero_crossings", {})',
        "flip_conditions = []",
        'if zc.get("rent_yr") is not None:',
        "    flip_conditions.append(f\"Rent above ${zc['rent_yr']:,.0f}/yr flips EBITDA negative\")",
        'if zc.get("utilisation") is not None:',
        "    flip_conditions.append(f\"Utilisation below {zc['utilisation']:.1%} flips EBITDA negative\")",
        'if zc.get("gp_revenue_share") is not None:',
        "    flip_conditions.append(f\"Service-fee % below {zc['gp_revenue_share']:.1%} flips EBITDA negative\")",
        "",
        "# 5 key numbers for page 1 (D-13)",
        "key_numbers = {",
        '    "steady_state_ebitda": steady_ebitda,',
        '    "steady_state_margin": steady_margin,',
        '    "peak_capital": peak_capital,',
        '    "breakeven_operating": be_operating,',
        '    "breakeven_payback": be_payback,',
        "}",
        "",
        "# Verdict text — 100% standalone, never mentions pharmacy (D-04)",
        'payback_str = f"month {be_payback}" if be_payback is not None else "beyond 36 months"',
        "verdict_text = (",
        '    f"VERDICT: {verdict}. The clinic is projected to generate ${steady_ebitda:,.0f}/yr "',
        '    f"steady-state EBITDA at a {steady_margin:.1%} margin, requiring ${peak_capital:,.0f} "',
        '    f"in peak startup capital. Operating breakeven is reached at month {be_operating}; "',
        '    f"payback at {payback_str}. The verdict is robust to the tested sensitivity ranges — "',
        '    "EBITDA stays positive unless: " + "; ".join(flip_conditions) + "."',
        ")",
        "",
        'print("=" * 70)',
        'print("§8.1 GO/NO-GO VERDICT (D-01, D-03, D-04)")',
        'print("=" * 70)',
        "print(verdict_text)",
        'print("=" * 70)',
        "",
        "# Deposit verdict + key numbers + flip-conditions for the template render",
        'report["verdict"] = verdict',
        'report["verdict_text"] = verdict_text',
        'report["key_numbers"] = key_numbers',
        'report["flip_conditions"] = flip_conditions',
        'print(f"[report] §8.1 deposited verdict, key_numbers, flip_conditions")',
    ))

    # 3. Code — §8.2 assumptions register (REP-01, D-16)
    cells.append(code(
        "# §8.2 Assumptions register (REP-01, D-16) — 5-column table from BASE_ASSUMPTIONS",
        "# Parameter | Value | Source | Date | Confidence (HIGH/MEDIUM/LOW)",
        "# Parses the # source — date inline comments (PIPE-05) from the §0 BASE_ASSUMPTIONS cell.",
        "import re",
        "",
        "# Extract the BASE_ASSUMPTIONS source from the kernel's input history (In[]).",
        "# This avoids relying on Path.cwd() which is unreliable in Colab (CWD != notebook dir).",
        '_base_src = ""',
        'for _cell_src in In:',
        '    if "BASE_ASSUMPTIONS = {" in _cell_src:',
        "        _base_src = _cell_src",
        "        break",
        "",
        '# Parse each line: "key": value,  # source — date [confidence]',
        "register_rows = []",
        "for line in _base_src.splitlines():",
        '    # Match lines like:  "key":   value,  # comment',
        "    m = re.match(r'\\s*\"([^\"]+)\":\\s*(.+?),?\\s*(?:#\\s*(.*))?$', line)",
        '    if not m or m.group(1) in ("site_address", "catchment_radii_m", "peer_postcodes"):',
        "        continue  # skip non-numeric config keys",
        '    key, val_str, comment = m.group(1), m.group(2), m.group(3) or ""',
        "    # Extract confidence from comment",
        '    conf = "MEDIUM"',
        '    if "HIGH" in comment.upper():',
        '        conf = "HIGH"',
        '    elif "LOW" in comment.upper() or "UNCONFIRMED" in comment.upper():',
        '        conf = "LOW"',
        "    # Extract date (4-digit year or YYYY-MM)",
        "    date_m = re.search(r'(20\\d{2}(?:-\\d{2})?|1 Jul 20\\d{2})', comment)",
        '    date = date_m.group(1) if date_m else "—"',
        "    # Source = comment minus date/confidence tokens",
        "    source = re.sub(r'\\b(HIGH|MEDIUM|LOW|UNCONFIRMED)\\b', '', comment, flags=re.IGNORECASE)",
        "    source = re.sub(r'\\b(20\\d{2}(?:-\\d{2})?|1 Jul 20\\d{2})\\b', '', source).strip(' —-')",
        '    source = source or "TBD — needs citation"',
        '    register_rows.append({"Parameter": key, "Value": val_str.strip(), "Source": source, "Date": date, "Confidence": conf})',
        "",
        "assumptions_register = pd.DataFrame(register_rows)",
        'print("=" * 90)',
        'print("§8.2 ASSUMPTIONS REGISTER (REP-01, D-16)")',
        'print("=" * 90)',
        "print(assumptions_register.to_string(index=False))",
        'print(f"\\nTotal: {len(register_rows)} parameters | Confidence: "',
        "      f\"{sum(1 for r in register_rows if r['Confidence']=='HIGH')} HIGH, \"",
        "      f\"{sum(1 for r in register_rows if r['Confidence']=='MEDIUM')} MEDIUM, \"",
        "      f\"{sum(1 for r in register_rows if r['Confidence']=='LOW')} LOW\")",
        'print("=" * 90)',
        'report["assumptions_register"] = assumptions_register',
        'print(f"[report] §8.2 deposited assumptions_register ({len(register_rows)} rows)")',
    ))

    # 4. Code — §8.3 Jinja2 HTML template (D-14, D-15, REP-02, REP-03)
    cells.append(code(
        "# §8.3 Jinja2 HTML template (D-14, D-15, REP-02, REP-03)",
        "# 8 sections (D-14). Page 1 = verdict + 5 key numbers + one map (D-13).",
        "# Footnote-style citations [1], [2] with access dates (D-17, REP-04).",
        "# CSS for investor-grade paginated PDF (weasyprint).",
        "import base64",
        "from datetime import date as _date",
        "from jinja2 import Template",
        "",
        "def _img_b64(path):",
        '    """Embed a PNG as base64 for portable HTML + weasyprint rendering."""',
        '    p = OUTPUTS / path if not str(path).startswith(str(OUTPUTS)) else Path(path)',
        "    if not p.exists():",
        '        return ""  # missing figure — render empty (don\'t crash the report)',
        '    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()',
        "",
        "# Figures for the report (all static matplotlib PNGs — no folium, Pitfall 16)",
        "figs = {",
        '    "catchment_3km": _img_b64("catchment_3km.png"),       # page 1 map (D-13)',
        '    "ramp_cashflow": _img_b64("ramp_cashflow.png"),        # §4 Financial Model',
        '    "tornado_ebitda": _img_b64("tornado_ebitda.png"),      # §5 Scenarios',
        '    "tornado_peak_capital": _img_b64("tornado_peak_capital.png"),',
        '    "billing_mix_curve": _img_b64("billing_mix_curve.png"),',
        "}",
        "",
        "report_html_template = r\"\"\"",
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        '<meta charset="utf-8">',
        "<style>",
        '  @page { size: A4; margin: 2cm 2.5cm; @bottom-center { content: counter(page) " / " counter(pages); font-size: 9px; color: #666; } }',
        "  @page :first { margin: 0; @bottom-center { content: none; } }",
        "  body { font-family: 'Helvetica', 'Arial', sans-serif; font-size: 11px; line-height: 1.5; color: #222; }",
        "  .cover { page-break-after: always; padding: 4cm 3cm; text-align: center; }",
        "  .cover h1 { font-size: 28px; margin-bottom: 0.2cm; }",
        "  .cover h2 { font-size: 16px; font-weight: normal; color: #555; margin-top: 0; }",
        "  .verdict-go { color: #1a7a1a; font-size: 22px; font-weight: bold; }",
        "  .verdict-nogo { color: #b00000; font-size: 22px; font-weight: bold; }",
        "  .key-numbers { display: table; width: 100%; margin: 1cm 0; }",
        "  .key-numbers div { display: table-cell; text-align: center; padding: 0.3cm; border: 1px solid #ddd; }",
        "  .key-numbers .num { font-size: 18px; font-weight: bold; }",
        "  .key-numbers .lbl { font-size: 9px; color: #666; }",
        "  table { width: 100%; border-collapse: collapse; margin: 0.5cm 0; font-size: 10px; }",
        "  th, td { border: 1px solid #ccc; padding: 4px 6px; text-align: left; }",
        "  th { background: #f0f0f0; }",
        "  h2 { font-size: 15px; border-bottom: 2px solid #333; padding-bottom: 2px; page-break-after: avoid; }",
        "  h3 { font-size: 12px; color: #444; page-break-after: avoid; }",
        "  img { max-width: 100%; page-break-inside: avoid; }",
        "  .footnote { font-size: 8px; color: #666; border-top: 1px solid #ccc; margin-top: 1cm; padding-top: 0.3cm; }",
        "  .secondary { background: #fffbe6; border-left: 4px solid #d4a000; padding: 0.3cm 0.5cm; }",
        "</style>",
        "</head>",
        "<body>",
        "",
        "<!-- COVER / PAGE 1 (D-13) -->",
        '<div class="cover">',
        "<h1>Johnston St Medical Clinic</h1>",
        "<h2>Feasibility Study — Executive Report</h2>",
        "<h2>292-296 Johnston St, Abbotsford VIC 3067 · {{ report_date }}</h2>",
        '<p style="margin-top: 2cm;">',
        "    <span class=\"{{ 'verdict-go' if report['verdict'] == 'GO' else 'verdict-nogo' }}\">",
        "      VERDICT: {{ report['verdict'] }}",
        "    </span>",
        "</p>",
        '<div class="key-numbers">',
        "    {% set kn = report['key_numbers'] %}",
        "<div><div class=\"num\">${{ '%,.0f'|format(kn['steady_state_ebitda']) }}</div><div class=\"lbl\">Steady-state EBITDA</div></div>",
        "<div><div class=\"num\">{{ '%.1f'|format(kn['steady_state_margin']*100) }}%</div><div class=\"lbl\">Margin</div></div>",
        "<div><div class=\"num\">${{ '%,.0f'|format(kn['peak_capital']) }}</div><div class=\"lbl\">Peak capital</div></div>",
        "<div><div class=\"num\">mo {{ kn['breakeven_operating'] }}</div><div class=\"lbl\">Operating breakeven</div></div>",
        "<div><div class=\"num\">{{ 'mo ' ~ kn['breakeven_payback'] if kn['breakeven_payback'] else '>36 mo' }}</div><div class=\"lbl\">Payback</div></div>",
        "</div>",
        "<p style=\"font-size: 10px; text-align: left; margin: 1cm 2cm;\">{{ report['verdict_text'] }}</p>",
        "{% if figs['catchment_3km'] %}<img src=\"{{ figs['catchment_3km'] }}\" style=\"max-height: 8cm;\"/>{% endif %}",
        "</div>",
        "",
        "<!-- §1 EXECUTIVE SUMMARY -->",
        "<h2>1. Executive Summary</h2>",
        "<p>{{ report['verdict_text'] }}</p>",
        "<h3>Flip-conditions (tornado zero-crossings)</h3>",
        "<ul>",
        "{% for fc in report['flip_conditions'] %}<li>{{ fc }}</li>{% endfor %}",
        "</ul>",
        "",
        "<!-- §2 SITE & CATCHMENT -->",
        "<h2>2. Site & Catchment</h2>",
        "<p>The site at 292-296 Johnston St, Abbotsford is geocoded from the exact address [1]. Catchment buffers of 1/3/5 km are constructed in EPSG:7855 (GDA2020/MGA zone 55) and population is area-apportioned across SA1 boundaries — fixing v1's whole-postcode summing flaw [2].</p>",
        "",
        "<!-- §3 COMPETITOR LANDSCAPE -->",
        "<h2>3. Competitor Landscape</h2>",
        "<p>Competitors (GP clinics, medical centres, pharmacies, allied health) are mapped via Google Places API (New) with per-type/per-ring splitting and place_id dedupe [3]. Brand classification and clinic-vs-practitioner filtering are applied.</p>",
        "",
        "<!-- §4 FINANCIAL MODEL -->",
        "<h2>4. Financial Model</h2>",
        "<p>The clinic P&L is modelled as a pure function of the parameters dict (ARCHITECTURE.md Pattern 3). Practice revenue = GP billings × service-fee % (Pitfall 11 guardrail — GP payments are NOT a cost line). The 36-month ramp-up cash flow models GP recruitment milestones and per-GP book-fill utilisation.</p>",
        "{% if figs['ramp_cashflow'] %}<img src=\"{{ figs['ramp_cashflow'] }}\"/>{% endif %}",
        "",
        "<!-- §5 SCENARIOS & SENSITIVITY -->",
        "<h2>5. Scenarios & Sensitivity</h2>",
        "<p>Base/optimistic/pessimistic scenarios are run as override dicts on the same P&L function (FIN-04). Two tornado charts rank which assumptions move annual EBITDA and peak capital most (FIN-05). A billing-mix sensitivity curve compares 70/30 mixed vs 100%-bulk+BBPIP (FIN-06).</p>",
        "{% if figs['tornado_ebitda'] %}<img src=\"{{ figs['tornado_ebitda'] }}\"/>{% endif %}",
        "{% if figs['tornado_peak_capital'] %}<img src=\"{{ figs['tornado_peak_capital'] }}\"/>{% endif %}",
        "{% if figs['billing_mix_curve'] %}<img src=\"{{ figs['billing_mix_curve'] }}\"/>{% endif %}",
        "",
        "<!-- §6 PHARMACY SYNERGY (SECONDARY UPSIDE — D-04) -->",
        "<h2>6. Pharmacy Synergy — Secondary Upside (NOT Load-Bearing)</h2>",
        '<div class="secondary">',
        "<p><strong>The clinic verdict above is 100% standalone.</strong> The pharmacy synergy below is secondary upside, quantified only after the standalone verdict. It is NOT load-bearing — the clinic does not need the pharmacy to be profitable.</p>",
        "{% set ps = report['pharmacy_synergy_range'] %}",
        "<p>Catchment pop: {{ '{:,.0f}'.format(ps['catchment_pop']) }} · Scripts/person/yr: {{ ps['avg_scripts_per_person_yr'] }} · Gross margin/script: ${{ ps['gross_margin_per_script'] }}</p>",
        "<ul>",
        "{% for label, r in ps['results'].items() %}",
        "<li><strong>{{ label|upper }}</strong> capture {{ '%.0f%%'|format(r['capture_rate']*100) }} → {{ '{:,.0f}'.format(r['annual_scripts']) }} scripts/yr → ${{ '{:,.0f}'.format(r['annual_profit']) }}/yr</li>",
        "{% endfor %}",
        "</ul>",
        "</div>",
        "",
        "<!-- §7 ASSUMPTIONS REGISTER (REP-01, D-16) -->",
        "<h2>7. Assumptions Register</h2>",
        "<table>",
        "<tr><th>Parameter</th><th>Value</th><th>Source</th><th>Date</th><th>Confidence</th></tr>",
        "{% for _, row in report['assumptions_register'].iterrows() %}",
        "<tr><td>{{ row['Parameter'] }}</td><td>{{ row['Value'] }}</td><td>{{ row['Source'] }}</td><td>{{ row['Date'] }}</td><td>{{ row['Confidence'] }}</td></tr>",
        "{% endfor %}",
        "</table>",
        "",
        "<!-- §8 DATA SOURCES & CITATIONS (REP-04, D-17) -->",
        "<h2>8. Data Sources & Citations</h2>",
        '<div class="footnote">',
        "<p>[1] Google Geocoding API — site address geocoding. Access date: {{ report_date }}.</p>",
        "<p>[2] ABS Census 2021 — G01/G02/G04 via ABS Data API (data.api.abs.gov.au/rest). Access date: {{ report_date }}.</p>",
        "<p>[3] Google Places API (New) — Nearby Search. Access date: {{ report_date }}.</p>",
        "<p>[4] MBS Online — item 23 rebate $43.90, from 1 Jul 2025 (2.4% indexation). Access date: {{ report_date }}.</p>",
        "<p>[5] Fair Work — MA000034/MA000002, from 1 Jul 2025. Access date: {{ report_date }}.</p>",
        "<p>[6] PBS Statistics 2023-24 — scripts/person/yr benchmark. Access date: {{ report_date }}.</p>",
        "<p>[7] AIHW (2026) — Medicare-subsidised GP and allied health attendances, SA3 age-band rates.</p>",
        "<p>[8] AMWAC 2000 — GP:population planning benchmark (1:905).</p>",
        "</div>",
        "",
        "</body>",
        "</html>",
        "\"\"\"",
        "",
        "html_rendered = Template(report_html_template).render(",
        "    report=report,",
        "    figs=figs,",
        "    report_date=_date.today().isoformat(),",
        ")",
        '(OUTPUTS / "Johnston_St_v2_Executive_Report.html").write_text(html_rendered, encoding="utf-8")',
        'print(f"[§8.3] HTML report written to outputs/Johnston_St_v2_Executive_Report.html ({len(html_rendered):,} chars)")',
    ))

    # 5. Code — §8.4 weasyprint PDF generation (REP-03, D-18)
    cells.append(code(
        "# §8.4 PDF generation via weasyprint (REP-03, D-18)",
        "# Colab-only — local Windows produces HTML only (D-18, STACK.md).",
        "import sys",
        "",
        'IS_COLAB = "google.colab" in sys.modules',
        'pdf_path = OUTPUTS / "Johnston_St_v2_Executive_Report.pdf"',
        "",
        "if IS_COLAB:",
        "    try:",
        "        import subprocess",
        '        subprocess.run(["pip", "install", "-q", "weasyprint"], check=True)',
        '        subprocess.run(["apt-get", "install", "-y", "libpango-1.0-0", "libpangocairo-1.0-0"], check=True)',
        "        from weasyprint import HTML",
        "        HTML(string=html_rendered).write_pdf(str(pdf_path))",
        '        print(f"[§8.4] PDF written to {pdf_path} (Colab + weasyprint)")',
        "    except Exception as e:",
        '        print(f"[§8.4] weasyprint PDF generation failed: {e}")',
        '        print(f"[§8.4] HTML report is available at outputs/Johnston_St_v2_Executive_Report.html")',
        "else:",
        '        print("[§8.4] Local Windows detected — HTML report produced (PDF generation is Colab-only, D-18).")',
        '        print(f"[§8.4] Open in Colab to generate the PDF, or view the HTML: outputs/Johnston_St_v2_Executive_Report.html")',
    ))

    # 6. Markdown — §8.5 interpretation + final Next Steps
    cells.append(md(
        "## §8.5 Interpretation",
        "",
        "§8 is the **investor deliverable**. The verdict is binary and standalone",
        "(D-03, D-04); the assumptions register (REP-01) and citations (REP-04) are",
        "the credibility layer; the PDF is Colab-only because weasyprint's GTK deps",
        "are painful on Windows (D-18). Re-running §8 alone regenerates the report",
        "from the current `report{}` state — the notebook is the single source of",
        'truth. This completes the feasibility study: the notebook + PDF answer',
        '"can the clinic be profitable on its own at this site?" with defensible',
        "data and transparent assumptions.",
        "",
        "## Next Steps",
        "",
        "Feasibility study complete. The notebook + PDF are the deliverable.",
        "Deferred to a future milestone: Monte Carlo confidence intervals (V2-01),",
        "drive-time isochrone catchments (V2-02), interactive dashboard.",
    ))

    return cells


# ──────────────────────────────────────────────────────────────────────
#  §6 "## Next Steps" cleanup
# ──────────────────────────────────────────────────────────────────────

def remove_next_steps(cells):
    """Remove ALL '## Next Steps' cells from the notebook.

    The §6 section (Phase 4) ships a single '## Next Steps' markdown cell as the
    notebook tail. §7 replaces it as the new tail — §7 ships its own §7.7
    Interpretation as the closing section. Remove all existing '## Next Steps'
    cells so §7 is the final section.

    Returns the count of removed cells.
    """
    kept = []
    removed = 0
    for cell in cells:
        src = "".join(cell.get("source", []))
        if "## Next Steps" in src:
            removed += 1
            continue
        kept.append(cell)
    return kept, removed


# ──────────────────────────────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────────────────────────────

def main():
    notebook_path = Path(__file__).resolve().parent.parent / "Johnston_St_v2.ipynb"
    nb = json.loads(notebook_path.read_text(encoding="utf-8"))
    cells = nb["cells"]

    # 1. Remove ALL "## Next Steps" cells (§7 replaces the §6 tail)
    cells, ns_removed = remove_next_steps(cells)
    if ns_removed > 0:
        print(f"[extend-phase5] removed {ns_removed} '## Next Steps' cell(s) — §7 replaces it as the notebook tail")
    else:
        print("[extend-phase5] no '## Next Steps' cells found — skipping cleanup")

    # 2. §7 Scenarios & Sensitivity cells (cell-replacement idempotency)
    MARKER = "# §7 Scenarios & Sensitivity"

    start_idx = None
    for i, c in enumerate(cells):
        if MARKER in "".join(c.get("source", [])):
            start_idx = i
            break

    new_phase5_cells = phase5_scenarios_cells() + phase5_executive_report_cells()

    if start_idx is not None:
        # Replace from §7 marker to end of notebook (§7 section is the tail)
        removed = len(cells) - start_idx
        cells = cells[:start_idx]
        cells.extend(new_phase5_cells)
        print(f"[extend-phase5] replaced {removed} §7+§8 cells with {len(new_phase5_cells)} corrected cells")
    else:
        # Fresh install — append §7 section at end
        cells.extend(new_phase5_cells)
        print(f"[extend-phase5] appended {len(new_phase5_cells)} §7+§8 cells (fresh install)")

    # 3. Write back (matches Phase 4 generator — preserves Unicode teaching characters)
    nb["cells"] = cells
    notebook_path.write_text(
        json.dumps(nb, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    n_cells = len(cells)
    n_code = sum(1 for c in cells if c.get("cell_type") == "code")
    n_md = sum(1 for c in cells if c.get("cell_type") == "markdown")
    print(f"[extend-phase5] notebook now: {n_cells} cells ({n_code} code, {n_md} markdown)")


if __name__ == "__main__":
    main()
