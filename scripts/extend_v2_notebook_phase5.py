#!/usr/bin/env python3
"""
Phase 5 extension script for Johnston_St_v2.ipynb — Plan 05-01.

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
        "base_ebitda = clinic_pnl(BASE_ASSUMPTIONS)[\"ebitda\"]",
        "swings = []",
        "for label, base, low, high, key in tornado_inputs_ebitda:",
        "    ebitda_low = clinic_pnl({**BASE_ASSUMPTIONS, key: low})[\"ebitda\"]",
        "    ebitda_high = clinic_pnl({**BASE_ASSUMPTIONS, key: high})[\"ebitda\"]",
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

    new_phase5_cells = phase5_scenarios_cells()

    if start_idx is not None:
        # Replace from §7 marker to end of notebook (§7 section is the tail)
        removed = len(cells) - start_idx
        cells = cells[:start_idx]
        cells.extend(new_phase5_cells)
        print(f"[extend-phase5] replaced {removed} §7 cells with {len(new_phase5_cells)} corrected cells")
    else:
        # Fresh install — append §7 section at end
        cells.extend(new_phase5_cells)
        print(f"[extend-phase5] appended {len(new_phase5_cells)} §7 Scenarios & Sensitivity cells (fresh install)")

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
