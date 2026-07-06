#!/usr/bin/env python3
"""
Phase 4 extension script for Johnston_St_v2.ipynb — Plan 04-01.

Loads the existing notebook (built by create_v2_notebook.py + extended by
extend_v2_notebook.py + extend_v2_notebook_phase3.py in Phases 1-3), extends
BASE_ASSUMPTIONS with Phase 4 financial keys (item mix, staffing, overheads,
fit-out capex, allied health), REPLACES the old fitout_capital placeholder with
the derived fitout_total, appends §6 Financial Model cells (clinic_pnl pure
function + base-case P&L display + Pitfall 11 guardrail), and cleans up the
duplicate "## Next Steps" cells (a cell-replacement artifact from Phases 2-3).

Follows the same cell-dict pattern as extend_v2_notebook_phase3.py:
  cell_type, metadata: {}, source as list of strings (each ending with \n
  except possibly the last); code cells have execution_count: null, outputs: [].

Idempotent: if a cell containing "# §6 Financial Model" already exists, the
script REMOVES the existing §6 cells and re-appends the corrected versions
(cell-replacement idempotency). BASE_ASSUMPTIONS extension is idempotent via
checking for "item_mix" already present.

Plan 04-02 extends this same script with §6.2 ramp-up cash flow cells — the
§6 section function is the single insertion point, so ramp cells are added
into phase4_financial_cells() before the Next Steps markdown.

Run:  python scripts/extend_v2_notebook_phase4.py
Output: Johnston_St_v2.ipynb (extended in-place)
"""

import json
from pathlib import Path


# ──────────────────────────────────────────────────────────────────────
#  Cell helpers (same pattern as extend_v2_notebook_phase3.py)
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
#  Phase 4 BASE_ASSUMPTIONS keys to insert
# ──────────────────────────────────────────────────────────────────────

# These keys are inserted before the closing `}` of BASE_ASSUMPTIONS.
# Idempotent: extend_base_assumptions() checks for "item_mix" already present.
PHASE4_ASSUMPTIONS_KEYS = [
    "",
    "    # --- Phase 4: Financial Model (source: MBS Online, Fair Work, industry benchmarks) ---",
    "    # MBS item mix (D-01) — MBS Online, from 1 Jul 2025 (2.4% indexation)",
    "    # Item 965 replaced the old GP Management Plan item (ceased 1 Jul 2025) — Correction 2",
    "    # Item 967 replaced the old Team Care Arrangement review item (ceased 1 Jul 2025)",
    "    \"item_mix\": {",
    "        23:  {\"pct\": 0.70, \"rebate\": 43.90, \"private_fee\": 95.00},   # Level B standard — MBS Online 1 Jul 2025",
    "        36:  {\"pct\": 0.15, \"rebate\": 84.90, \"private_fee\": 165.00},  # Level C long — MBS Online 1 Jul 2025",
    "        44:  {\"pct\": 0.03, \"rebate\": 125.10, \"private_fee\": 250.00}, # Level D prolonged — MBS Online 1 Jul 2025",
    "        965: {\"pct\": 0.05, \"rebate\": 156.55, \"private_fee\": 250.00}, # GPCCMP prepare (replaced old GPMP item) — MBS Online 1 Jul 2025",
    "        967: {\"pct\": 0.03, \"rebate\": 156.55, \"private_fee\": 220.00}, # GPCCMP review (replaced old TCA review item) — MBS Online 1 Jul 2025",
    "        701: {\"pct\": 0.02, \"rebate\": 69.20, \"private_fee\": 120.00},  # Health assessment brief — MBS Online 1 Jul 2025",
    "        \"procedures\": {\"pct\": 0.02, \"rebate\": 80.00, \"private_fee\": 150.00},  # Minor procedures avg — MBS Online",
    "    },",
    "    # Staffing (D-13, D-14) — Fair Work MA000034/MA000002, from 1 Jul 2025",
    "    \"nurse_fte\":              1.0,",
    "    \"nurse_salary_yr\":        75_868,     # RN Level 2 PP2, Fair Work MA000034, from 1 Jul 2025",
    "    \"reception_fte\":          1.5,",
    "    \"reception_salary_yr\":    58_193,     # Clerks Level 2 Y1, Fair Work MA000002, from 1 Jul 2025",
    "    \"manager_fte\":            0.5,",
    "    \"manager_salary_yr\":      64_553,     # Clerks Level 4, Fair Work MA000002, from 1 Jul 2025",
    "    \"oncost_multiplier\":      1.14,       # 12% super (ATO, from 1 Jul 2025) + ~2% WorkCover VIC — NOT 11.5%",
    "    # Overheads (D-15) — industry benchmarks, MEDIUM confidence",
    "    \"insurance_yr\":           12_000,     # practice entity indemnity + public liability — MGRS/TEGO",
    "    \"consumables_yr\":         45_000,     # medical supplies, ~$1.60/consult — GP-Hub benchmark",
    "    \"admin_it_utilities_yr\":  35_000,     # software + hardware + utilities — Bp Premier + industry est",
    "    # Fit-out (D-09, D-10, D-11) — floor plan PDF + industry $/sqm",
    "    \"floor_area_sqm\":         170,        # 292 Johnston ground floor plan PDF, cross-checked RACGP",
    "    \"fitout_per_sqm_low\":     1_200,      # Design Yard 32 (Melbourne base build)",
    "    \"fitout_per_sqm_mid\":     1_700,      # midpoint of Melbourne base + national 2026",
    "    \"fitout_per_sqm_high\":    2_200,      # EasyAsset specialist / SoulMED lower range",
    "    \"fitout_per_sqm\":         1_700,      # base case = mid",
    "    \"equipment_it_lump_sum\":  60_000,     # exam beds + treatment + IT + software setup — Medilogic mid-range",
    "    \"fitout_total\":           349_000,    # $1,700 × 170 + $60,000 (derived — replaces the old 350k placeholder)",
    "    # Allied health (D-02)",
    "    \"allied_consults_per_yr\":     4_000,    # 1 FTE allied health, lower volume than GP",
    "    \"allied_avg_rev_per_consult\": 85.00,    # allied health typical consult fee",
]

# The old fitout_capital line that must be REPLACED (placeholder → derived).
# Removed entirely; the new fitout_total key (in PHASE4_ASSUMPTIONS_KEYS) replaces it.
OLD_FITOUT_CAPITAL_LINE = '    "fitout_capital":         350_000,     # estimate — flagged, sensitivity-tested'


# ──────────────────────────────────────────────────────────────────────
#  §6 Financial Model cells
# ──────────────────────────────────────────────────────────────────────

def phase4_financial_cells():
    """Return the §6 Financial Model cells (Plan 04-01: clinic_pnl + base-case P&L).

    Plan 04-02 extends this function to add §6.2 ramp-up cash flow cells
    before the Next Steps markdown. The §6 section is the single insertion
    point — the cell-replacement idempotency in main() handles re-runs.
    """
    cells = []

    # 1. Markdown — §6 header + teaching commentary
    cells.append(md(
        "# §6 Financial Model",
        "",
        "This section builds the clinic P&L as a **pure function** of `BASE_ASSUMPTIONS`",
        "(ARCHITECTURE.md Pattern 3) — no globals, no notebook state. Phase 5 scenarios",
        "become override dicts: `{**BASE_ASSUMPTIONS, **overrides}`.",
        "",
        "**The single most common GP-clinic P&L error (Pitfall 11):** confusing GP gross",
        "billings with practice revenue. 5 GPs × ~$550k gross billings = ~$2.75M, but the",
        "practice retains only 30-35% (the service fee). Practice revenue = ~$825k-$960k,",
        "NOT $2.75M. Treating gross billings as revenue overstates by ~3×.",
        "",
        "**Structural fix — explicit service-fee % row:**",
        "- `gp_billings` is the INFORMATIONAL top line (investors see the gross figure)",
        "- `practice_revenue = gp_billings × service_fee_%` (THIS is the P&L revenue line)",
        "- GP payments (65-70% of billings) are NOT a practice cost — they're the GP's share,",
        "  already deducted at the revenue line. Double-counting them as a cost alongside",
        "  100% of billings as revenue is the other common Pitfall 11 error variant.",
        "",
        "**Capacity-driven, not demand-driven (D-03):** consult volume = 5 FTE × 5,500/yr ×",
        "75% utilisation = 27,500/yr (from §5 `clinic_capacity`). The §5 market-share results",
        "are displayed as context but do NOT drive the volume — the P&L answers \"if the",
        "clinic fills its books, is it profitable?\" Phase 5 scenarios explore what happens",
        "if it doesn't.",
        "",
        "**MBS item values are date-stamped to 1 Jul 2025** (Pitfall 7 — 2.4% indexation).",
        "Items 965/967 replaced the ceased chronic-disease-management items from 1 Jul 2025",
        "(Correction 2). The Nov 2025 bulk-billing incentive is a Phase 5 scenario, NOT in",
        "this base case — the base case is 70/30 mixed billing.",
        "",
        "**Every cost/revenue line has a source + date** in `BASE_ASSUMPTIONS` (Pitfall 13).",
        "No numeric literal outside `BASE_ASSUMPTIONS` except unit conversions (PIPE-05).",
    ))

    # 2. Code — §6 context display (D-03 capacity-driven) + report{} accumulator init
    cells.append(code(
        "# §6 context: P&L is capacity-driven, not demand-driven (D-03)",
        "# Display §5 market-share results as context alongside the capacity-driven P&L.",
        "# report{} accumulator (ARCHITECTURE.md Pattern 5) — Phase 4 deposits headline",
        "# metrics here; Phase 5 §8 renders them in the executive report.",
        "report = {}  # Pattern 5 accumulator — Phase 5 §8 reads this",
        "",
        'print("=" * 70)',
        'print("§6 FINANCIAL MODEL — CONTEXT")',
        'print("=" * 70)',
        'print(f"Clinic capacity: {clinic_capacity:.0f} consults/yr (5 FTE × 5,500/yr)")',
        "print(f\"Utilisation target: {BASE_ASSUMPTIONS['utilisation']:.0%} (steady-state)\")",
        "print(f\"Effective annual consults: {clinic_capacity * BASE_ASSUMPTIONS['utilisation']:.0f}\")",
        "print()",
        'for r in BASE_ASSUMPTIONS["catchment_radii_m"]:',
        "    ms = market_share_results[r]",
        '    print(f"  {r//1000}km ring: {ms[\'share_of_total_mid\']:.1f}% of consults (context only — P&L is capacity-driven)")',
        "print()",
        'print("Note: The P&L answers \'if the clinic fills its books, is it profitable?\'")',
        'print("Phase 5 scenarios explore what happens if it doesn\'t.")',
        'print("=" * 70)',
    ))

    # 3. Code — §6 clinic_pnl pure function (Pitfall 11 compliant)
    cells.append(code(
        "# §6 clinic_pnl — pure-function steady-state annual P&L (ARCHITECTURE.md Pattern 3)",
        "# Pitfall 11 compliance: GP gross billings ≠ practice revenue.",
        "#   gp_billings (INFORMATIONAL top line) × service_fee_% = practice_revenue (THE revenue line)",
        "#   GP payments are NOT a cost — deducted at the revenue line, not double-counted.",
        "# D-16: steady-state annual view (Plan 04-02 adds the 36-month monthly ramp wrapper).",
        "# No billing incentive in base case (Phase 5 scenario, Pitfall 7).",
        "def clinic_pnl(a: dict) -> dict:",
        '    """',
        "    Pure-function steady-state annual P&L for a 5-FTE GP + 1-FTE allied health clinic.",
        "    ",
        "    ARCHITECTURE.md Pattern 3 — no globals, no notebook state.",
        "    Scenarios (Phase 5): {**BASE_ASSUMPTIONS, **overrides}",
        "    ",
        "    Pitfall 11 compliance: GP gross billings ≠ practice revenue.",
        "    Practice revenue = billings × service_fee_%. GP payments are NOT a cost.",
        "    D-16: steady-state annual view.",
        "    \"\"\"",
        "    # --- Consult volume (capacity-driven, D-03) ---",
        '    annual_consults = a["n_gp_fte"] * a["gp_fte_consults_per_yr"] * a["utilisation"]',
        "    ",
        "    # --- GP billings (top line, INFORMATIONAL — not practice revenue) ---",
        "    # Weighted by item mix (D-01): each item has a % of volume and a rebate/fee",
        "    # Bulk-billed consults: patient pays $0, practice claims MBS rebate",
        "    # Private consults: patient pays private_fee, claims MBS rebate back",
        "    # Revenue per consult = bulk_bill_share × rebate + private_share × private_fee",
        '    item_mix = a["item_mix"]  # dict: {item_number: {"pct": float, "rebate": float, "private_fee": float}}',
        '    weighted_rebate = sum(v["pct"] * v["rebate"] for v in item_mix.values())',
        '    weighted_private_fee = sum(v["pct"] * v["private_fee"] for v in item_mix.values())',
        "    avg_rev_per_consult = (",
        '        a["bulk_bill_share"] * weighted_rebate',
        '        + (1 - a["bulk_bill_share"]) * weighted_private_fee',
        "    )",
        "    gp_billings = annual_consults * avg_rev_per_consult  # GROSS billings (informational)",
        "    ",
        "    # --- Practice revenue = billings × service_fee_% (Pitfall 11 fix) ---",
        '    practice_revenue_gp = gp_billings * a["gp_revenue_share"]',
        "    ",
        "    # --- Allied health revenue (D-02: same service-fee % split) ---",
        '    allied_consults = a["n_allied_fte"] * a["allied_consults_per_yr"] * a["utilisation"]',
        '    allied_billings = allied_consults * a["allied_avg_rev_per_consult"]',
        '    practice_revenue_allied = allied_billings * a["gp_revenue_share"]  # same split',
        "    ",
        "    practice_revenue = practice_revenue_gp + practice_revenue_allied",
        "    ",
        "    # --- Costs (all from practice revenue, NOT from gross billings) ---",
        "    # NOTE: GP payments (65-70% of billings) are NOT here — they're already deducted",
        "    # at the revenue line (billings × service_fee_% = practice revenue).",
        '    staffing_costs = (',
        '        a["nurse_fte"] * a["nurse_salary_yr"] * a["oncost_multiplier"]',
        '        + a["reception_fte"] * a["reception_salary_yr"] * a["oncost_multiplier"]',
        '        + a["manager_fte"] * a["manager_salary_yr"] * a["oncost_multiplier"]',
        "    )",
        "    costs = (",
        '        a["rent_yr"]',
        "        + staffing_costs",
        '        + a["insurance_yr"]           # D-15 line (a)',
        '        + a["consumables_yr"]         # D-15 line (b)',
        '        + a["admin_it_utilities_yr"]  # D-15 line (c)',
        "    )",
        "    ",
        "    ebitda = practice_revenue - costs",
        "    margin = ebitda / practice_revenue if practice_revenue else 0",
        "    ",
        "    return {",
        '        "annual_consults": annual_consults,',
        '        "gp_billings": gp_billings,              # informational (Pitfall 11 guardrail)',
        '        "practice_revenue": practice_revenue,     # THE revenue line',
        '        "practice_revenue_gp": practice_revenue_gp,',
        '        "practice_revenue_allied": practice_revenue_allied,',
        '        "staffing_costs": staffing_costs,',
        '        "total_costs": costs,',
        '        "ebitda": ebitda,',
        '        "margin": margin,',
        '        "service_fee_pct": a["gp_revenue_share"],  # explicit service-fee % row (FIN-01)',
        "    }",
        "",
        'print("[pnl] clinic_pnl() defined — pure function, Pitfall 11 compliant (billings × service_fee_% = revenue)")',
    ))

    # 4. Code — §6 base-case P&L run + display
    cells.append(code(
        "# §6 base-case steady-state P&L (5 FTE, 75% utilisation, full books)",
        "pnl_result = clinic_pnl(BASE_ASSUMPTIONS)",
        "",
        "# Display as a clean table for teaching",
        "import pandas as pd",
        "pnl_display = pd.DataFrame([",
        '    ("GP consults/yr", pnl_result["annual_consults"]),',
        '    ("GP gross billings (INFORMATIONAL)", pnl_result["gp_billings"]),',
        '    ("Service fee % (practice retains)", pnl_result["service_fee_pct"]),',
        '    ("Practice revenue — GP", pnl_result["practice_revenue_gp"]),',
        '    ("Practice revenue — Allied health", pnl_result["practice_revenue_allied"]),',
        '    ("Practice revenue — TOTAL", pnl_result["practice_revenue"]),',
        '    ("Staffing costs (nurse+reception+manager)", pnl_result["staffing_costs"]),',
        '    ("Rent", BASE_ASSUMPTIONS["rent_yr"]),',
        '    ("Insurance", BASE_ASSUMPTIONS["insurance_yr"]),',
        '    ("Consumables & medical supplies", BASE_ASSUMPTIONS["consumables_yr"]),',
        '    ("Admin/IT/utilities", BASE_ASSUMPTIONS["admin_it_utilities_yr"]),',
        '    ("Total costs", pnl_result["total_costs"]),',
        '    ("EBITDA", pnl_result["ebitda"]),',
        '    ("Margin", f"{pnl_result[\'margin\']:.1%}"),',
        '], columns=["Line item", "Value ($)"])',
        "print(pnl_display.to_string(index=False))",
        "",
        "# Pitfall 11 verification: practice revenue should be ~$800k-$1,000k, NOT $2.5M+",
        "print(f\"\\n[pnl] Pitfall 11 check: practice revenue = ${pnl_result['practice_revenue']:,.0f}\")",
        "print(f\"[pnl] GP gross billings (informational) = ${pnl_result['gp_billings']:,.0f}\")",
        'if pnl_result["practice_revenue"] > 2_000_000:',
        '    print("⚠ WARNING: Practice revenue > $2M — likely gross billings confusion (Pitfall 11)")',
        "else:",
        '    print("[pnl] ✓ Practice revenue in expected range (~$800k-$1M for 5-GP clinic)")',
    ))

    # 5. Markdown — §6.1 Pitfall 11 Guardrail
    cells.append(md(
        "## §6.1 Pitfall 11 Guardrail",
        "",
        "The **service-fee model** is the structural fix for the most common GP-clinic",
        "P&L error. GP gross billings for 5 GPs at ~$550k each = ~$2.75M, but the practice",
        "retains only 30-35% (the service fee). Practice revenue = ~$825k-$960k.",
        "",
        "All practice costs (rent, staff, insurance, consumables, admin) come out of THIS",
        "figure, not out of gross billings. GP payments (65-70% of billings) are NOT a",
        "practice cost — they're the GP's share, already deducted at the revenue line.",
        "Double-counting GP payments as a cost alongside 100% of billings as revenue is",
        "the other common error variant.",
        "",
        "The `gp_billings` key in the return dict is **INFORMATIONAL only** — it exists so",
        "investors can see the gross figure, but it is NOT the revenue line. The",
        "`service_fee_pct` key makes the service-fee % explicit (FIN-01) so Phase 5",
        "sensitivity can override it: `{**BASE_ASSUMPTIONS, \"gp_revenue_share\": 0.30}`.",
    ))

    # 6. Markdown — Next Steps (single cell; replaces the 7 duplicate artifacts)
    cells.append(md(
        "## Next Steps",
        "",
        "**Phase 5** runs over `clinic_pnl` via override dicts `{**BASE_ASSUMPTIONS, **overrides}`:",
        "- **Scenarios** — base / optimistic / pessimistic (rent, utilisation, service-fee %, billing mix)",
        "- **Sensitivity tornado** — one-variable-at-a-time ±30% ranges on the key drivers",
        "- **Bulk-billing incentive comparison** — 100% bulk billing + 12.5% incentive vs 70/30 mixed (FIN-06)",
        "- **Pharmacy synergy** — does the clinic need the pharmacy, or vice versa?",
        "- **Assumptions register** — every BASE_ASSUMPTIONS key with source + confidence (REP-01)",
        "- **Go/no-go verdict** — the headline answer, with the sensitivity range as the uncertainty band",
        "",
        "**Plan 04-02** adds the monthly ramp-up cash flow, peak capital requirement, and",
        "months-to-breakeven headlines — the two questions an investor with limited startup",
        "capital cares about most (Pitfall 12): how long to get there, and how much capital",
        "to survive the journey.",
    ))

    return cells


# ──────────────────────────────────────────────────────────────────────
#  BASE_ASSUMPTIONS extension
# ──────────────────────────────────────────────────────────────────────

def extend_base_assumptions(cells):
    """Insert Phase 4 keys into the BASE_ASSUMPTIONS dict cell.

    Also REMOVES the old fitout_capital placeholder line (replaced by the
    derived fitout_total key in PHASE4_ASSUMPTIONS_KEYS).

    Idempotent: if 'item_mix' is already present in the BASE_ASSUMPTIONS cell,
    the cell is left unchanged.
    """
    for cell in cells:
        src = cell.get("source", [])
        joined = "".join(src)
        if "BASE_ASSUMPTIONS = {" not in joined:
            continue
        if "item_mix" in joined:
            return False  # already extended

        new_source = []
        for line in src:
            # Remove the old fitout_capital placeholder line — fitout_total replaces it
            if OLD_FITOUT_CAPITAL_LINE in line:
                continue
            elif line.strip() == "}":
                # Insert Phase 4 keys before the closing brace
                for key_line in PHASE4_ASSUMPTIONS_KEYS:
                    new_source.append(key_line + "\n")
                new_source.append(line)
            else:
                new_source.append(line)
        cell["source"] = new_source
        return True
    return False


# ──────────────────────────────────────────────────────────────────────
#  Duplicate "## Next Steps" cleanup
# ──────────────────────────────────────────────────────────────────────

def remove_duplicate_next_steps(cells):
    """Remove ALL '## Next Steps' cells from the notebook.

    A cell-replacement artifact from Phases 2-3 left 7 duplicate '## Next Steps'
    cells (cells 62-68 in the pre-Phase-4 notebook). The §6 section ships its
    own single Next Steps cell, so we remove all existing ones first.

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

    # 1. Extend BASE_ASSUMPTIONS with Phase 4 keys (idempotent — no-op if already present)
    extended = extend_base_assumptions(cells)
    if extended:
        print("[extend-phase4] BASE_ASSUMPTIONS extended with Phase 4 keys (item_mix, staffing, overheads, fitout, allied)")
        print("[extend-phase4] old fitout_capital placeholder removed — replaced by fitout_total=349,000")
    else:
        print("[extend-phase4] BASE_ASSUMPTIONS already has Phase 4 keys — skipping")

    # 2. Remove ALL duplicate "## Next Steps" cells (Phase 2-3 artifact cleanup)
    cells, ns_removed = remove_duplicate_next_steps(cells)
    if ns_removed > 0:
        print(f"[extend-phase4] removed {ns_removed} duplicate '## Next Steps' cell(s)")
    else:
        print("[extend-phase4] no duplicate '## Next Steps' cells found — skipping cleanup")

    # 3. §6 Financial Model cells (cell-replacement idempotency)
    MARKER = "# §6 Financial Model"
    # After duplicate Next Steps cleanup, §6 section is the tail of the notebook.
    # Stop markers: none needed — §6 section runs to end (it ships its own Next Steps).

    start_idx = None
    for i, c in enumerate(cells):
        if MARKER in "".join(c.get("source", [])):
            start_idx = i
            break

    new_phase4_cells = phase4_financial_cells()

    if start_idx is not None:
        # Replace from §6 marker to end of notebook (§6 section is the tail after Next Steps cleanup)
        removed = len(cells) - start_idx
        cells = cells[:start_idx]
        cells.extend(new_phase4_cells)
        print(f"[extend-phase4] replaced {removed} §6 cells with {len(new_phase4_cells)} corrected cells")
    else:
        # Fresh install — append §6 section at end
        cells.extend(new_phase4_cells)
        print(f"[extend-phase4] appended {len(new_phase4_cells)} §6 Financial Model cells (fresh install)")

    # 4. Write back
    nb["cells"] = cells
    notebook_path.write_text(
        json.dumps(nb, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    n_cells = len(cells)
    n_code = sum(1 for c in cells if c.get("cell_type") == "code")
    n_md = sum(1 for c in cells if c.get("cell_type") == "markdown")
    print(f"[extend-phase4] notebook now: {n_cells} cells ({n_code} code, {n_md} markdown)")


if __name__ == "__main__":
    main()
