# Phase 5: Scenarios & Executive Report - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-06
**Phase:** 05-scenarios-executive-report
**Areas discussed:** Go/no-go verdict logic, Scenario levers & tornado, Billing comparison & synergy, Report & PDF design

---

## Go/no-go verdict logic

### Q1: What should be the PRIMARY decision rule for the go/no-go recommendation?

| Option | Description | Selected |
|--------|-------------|----------|
| Payback within 5yr | GO if cumulative payback breakeven reached within 5 years (60 months) in base case; NO-GO otherwise. | |
| Composite: 3 signals | GO requires ALL: positive steady-state EBITDA, operating breakeven within 18 months, payback within 5 years. 2/3 → CONDITIONAL. <2 → NO-GO. | |
| Steady-state EBITDA | GO if steady-state annual EBITDA positive AND margin > 15%. Payback as context, not the gate. Clinic as long-lived asset. | ✓ |
| Scenario-weighted | GO if base AND optimistic both reach payback within 5 years; NO-GO if base AND pessimistic both miss. Mixed → CONDITIONAL. | |

**User's choice:** Steady-state EBITDA
**Notes:** Phase 4 base case clears this gate comfortably (+$258k EBITDA, 38.4% margin). Treats the clinic as a long-lived asset — if profitable at steady state, fit-out amortises over the lease regardless of a 3-5yr payback.

### Q2: How should the 'conditions that flip the verdict' be presented in the exec summary?

| Option | Description | Selected |
|--------|-------------|----------|
| Tornado zero-crossings | State the margin safety buffer: 'base-case margin is 38% — stays GO down to ~$X rent / ~Y% utilisation before EBITDA turns negative.' One sentence per lever. | ✓ |
| Named flip-scenarios | List 2-3 named scenarios that would flip it: 'NO-GO if rent exceeds $140k/yr AND utilisation stays below 60%.' | |
| Let tornado speak | Just report the margin and note sensitivity analysis shows which assumptions move this most. | |

**User's choice:** Tornado zero-crossings
**Notes:** Clean alignment between the verdict and the tornado sensitivity output. Investor-readable.

### Q3: Should the verdict be binary GO/NO-GO, or include a CONDITIONAL tier?

| Option | Description | Selected |
|--------|-------------|----------|
| Binary GO/NO-GO | Two tiers only. Decisive — investors want a clear answer. | ✓ |
| Three-tier (incl. CONDITIONAL) | GO / CONDITIONAL / NO-GO. CONDITIONAL = EBITDA positive but margin < 25%, OR payback > 5yr. | |
| GO with caveats | GO with explicit caveats attached: 'GO — contingent on rent ≤ $100k, utilisation ≥ 70%...' | |

**User's choice:** Binary GO/NO-GO
**Notes:** Decisive. Base case is clearly profitable, so a flat GO with flip-conditions noted is defensible.

### Q4: How does the pharmacy synergy relate to the standalone verdict?

| Option | Description | Selected |
|--------|-------------|----------|
| Standalone only | Verdict is 100% standalone. Pharmacy synergy in a SEPARATE section after the verdict, labelled 'Secondary upside — not load-bearing.' | ✓ |
| Standalone + footnote | Verdict standalone, but a one-line footnote acknowledges synergy exists. | |
| Standalone + combined thesis | Verdict standalone, plus a separate 'investment thesis' paragraph frames the combined opportunity. | |

**User's choice:** Standalone only
**Notes:** Cleanest separation — matches the Core Value exactly. Verdict text never mentions the pharmacy.

---

## Scenario levers & tornado

### Q1: Which levers should move in the base/optimistic/pessimistic scenarios?

| Option | Description | Selected |
|--------|-------------|----------|
| 5 levers, independent | rent, utilisation, service-fee %, ramp speed, billing mix. Each moves independently. | ✓ |
| 4 levers + BBPIP separate | rent, utilisation, service-fee %, ramp speed. Billing mix handled separately as FIN-06 comparison. | |
| 6+ levers, comprehensive | rent, utilisation, service-fee %, ramp speed, $/sqm, consults/GP/day, allied health FTE. | |

**User's choice:** 5 levers, independent
**Notes:** Comprehensive but readable. Billing mix is both a scenario lever AND the FIN-06 comparison axis.

### Q2: Which inputs get one-way tornado sensitivity, and what range?

| Option | Description | Selected |
|--------|-------------|----------|
| Same 5, wide range | The 5 scenario levers, each varied one-at-a-time over a wide range. Clean alignment with scenarios. | |
| 7-8 inputs, broader | The 5 scenario levers + $/sqm fit-out + equipment/IT lump sum + consults/GP/day. Full uncertainty picture. | ✓ |
| 6 inputs + fit-out | 5 scenario levers + $/sqm fit-out. Adds capex dimension without overloading. | |

**User's choice:** 7-8 inputs, broader
**Notes:** Full uncertainty picture. Shows fit-out cost sensitivity alongside operational levers.

### Q3: Should there be one tornado (EBITDA) or two (add peak capital or payback)?

| Option | Description | Selected |
|--------|-------------|----------|
| EBITDA only | One tornado on annual EBITDA. Standard investor expectation. | |
| Two: EBITDA + peak capital | (a) annual EBITDA (profitability), (b) peak capital (funding requirement). Different levers dominate each. | ✓ |
| Two: EBITDA + payback | (a) annual EBITDA, (b) payback months. Shows which levers shorten payback most. | |

**User's choice:** Two: EBITDA + peak capital
**Notes:** Different levers dominate each view — rent/utilisation drive EBITDA; $/sqm/ramp speed drive peak capital. Both add value.

### Q4: How should the base/optimistic/pessimistic results be presented?

| Option | Description | Selected |
|--------|-------------|----------|
| Full P&L side-by-side | Every revenue/cost line for base/opt/pess in 3 columns + EBITDA/margin/peak-capital/payback rows. | ✓ |
| Summary metrics only | 3 columns × ~6 rows. Compact — line-by-line detail is in the base-case P&L already. | |
| Summary + delta chart | Summary metrics table + a scenario delta chart decomposing the EBITDA spread into lever contributions. | |

**User's choice:** Full P&L side-by-side
**Notes:** Matches FEATURES.md 'side-by-side P&L table.' Most detailed — investor sees exactly where scenarios diverge.

---

## Billing comparison & synergy

### Q1: How should the BBPIP 12.5% incentive be modelled in the 100%-bulk scenario?

| Option | Description | Selected |
|--------|-------------|----------|
| Simple: +12.5% revenue line | BBPIP added as a revenue line on top of the bulk-billing rebate, practice receives the full 12.5%. | |
| Split: practice/GP share | Practice retains ~6.25%, GP gets ~6.25% (per Pitfall 7: 'practice gets half'). Researcher verifies exact split. | ✓ |
| Both BBI + BBPIP | Model both the triple BBI (Nov 2023) AND the BBPIP 12.5% (Nov 2025). Two incentive layers. | |

**User's choice:** Split: practice/GP share
**Notes:** More accurate to the DoH factsheet. Researcher confirms the exact split at build time.

### Q2: How should the 70/30 vs 100%-bulk+BBPIP comparison be presented?

| Option | Description | Selected |
|--------|-------------|----------|
| 2-col table + verdict | 2-column comparison table + one-paragraph interpretation. Compact, decisive. | |
| 2-col table + chart | Same table + a bar chart/waterfall showing the EBITDA/margin difference visually. | |
| Full mix sensitivity curve | Run clinic_pnl across bulk_bill_share = [0%, 25%, 50%, 70%, 100%] and plot EBITDA vs billing mix. Shows optimal mix and crossover. | ✓ |

**User's choice:** Full mix sensitivity curve
**Notes:** Most analytical — answers 'what billing mix maximises profit?' Shows the crossover where 100%-bulk+BBPIP crosses 70/30-mixed.

### Q3: How should the pharmacy synergy be quantified?

| Option | Description | Selected |
|--------|-------------|----------|
| Per-capita scripts × share | catchment pop × avg scripts/person/yr × Priceline's market share × gross margin per script. Transparent, all cited. | ✓ |
| Clinic-driven footfall only | clinic patients × % who fill scripts on-site × scripts/visit × margin. Only the clinic-attributable portion. | |
| Both footfall + total | (a) clinic-driven footfall AND (b) total pharmacy profit estimate. Two cuts. | |

**User's choice:** Per-capita scripts × share
**Notes:** Transparent arithmetic, all cited. Annual pharmacy profit estimate as 'secondary upside.'

### Q4: Should the pharmacy synergy be a range or a single point estimate?

| Option | Description | Selected |
|--------|-------------|----------|
| Range (low/mid/high) | low/mid/high capture rate (e.g. 15%/20%/25%) → low/mid/high annual pharmacy profit. | ✓ |
| Single point | Single point estimate with capture rate stated as an assumption. Simpler. | |

**User's choice:** Range (low/mid/high)
**Notes:** Matches the uncertainty in pharmacy market share. Consistent with the scenario approach.

---

## Report & PDF design

### Q1: What goes on page 1 of the executive PDF?

| Option | Description | Selected |
|--------|-------------|----------|
| Verdict + 5 numbers only | GO/NO-GO in large text + 3-5 key numbers + flip-conditions + site address + date. Nothing else. | |
| Verdict + 5 numbers + map | Executive summary + a single 'site at a glance' map (3km catchment with competitors). | ✓ |
| Cover page + page 2 summary | Cover page (title, address, date, author) THEN page 2 = executive summary. | |

**User's choice:** Verdict + 5 numbers + map
**Notes:** Gives context without overwhelming. Map is the most investor-friendly visual anchor.

### Q2: What overall structure should the executive report follow?

| Option | Description | Selected |
|--------|-------------|----------|
| 8-section narrative | Exec Summary → Site & Catchment → Competitor Landscape → Financial Model → Scenarios & Sensitivity → Pharmacy Synergy → Assumptions Register → Data Sources. Follows ARCHITECTURE.md §2-§8. | ✓ |
| Financials-first (5 sections) | Exec Summary → Financial Model & Scenarios → Market Context → Pharmacy Synergy → Assumptions & Sources. Financials first. | |
| Verdict-emphasised (6 sections) | Exec Summary → Go/No-Go Detail → Market Analysis → Financial Projections → Pharmacy Synergy → Assumptions & Sources. | |

**User's choice:** 8-section narrative
**Notes:** Follows the ARCHITECTURE.md §2-§8 flow. Investor reads top-to-bottom.

### Q3: Which rendering pipeline for the PDF?

| Option | Description | Selected |
|--------|-------------|----------|
| Jinja2 + weasyprint | Single .html template with CSS (cover, page breaks, headers, page numbers) rendered with weasyprint. Full layout control. | ✓ |
| f-string markdown → weasyprint | f-string markdown template → markdown library → HTML → weasyprint. Simpler, less layout control. | |
| Jinja2 + pandas to_html | Jinja2 HTML template for prose, pandas .to_html() for tables injected into template. | |

**User's choice:** Jinja2 + weasyprint
**Notes:** Full layout control — investor-grade paginated PDF. Matches STACK.md recommendation.

### Q4: How should the assumptions register (REP-01) be structured?

| Option | Description | Selected |
|--------|-------------|----------|
| 5-col table, all params | Parameter | Value | Source | Date | Confidence. Every BASE_ASSUMPTIONS key gets a row. | ✓ |
| 5-col table, key params only | Same columns but only financial/demand assumptions (the ones that move the verdict). | |
| Two tables: assumptions + sources | (a) Financial assumptions with confidence + sensitivity range, (b) Data sources with vintage + access date. | |

**User's choice:** 5-col table, all params
**Notes:** Matches Pitfall 13 'value, source, confidence' + adds date. The single investor-credible artifact.

### Q5: How should inline citations (REP-04) be handled in the report?

| Option | Description | Selected |
|--------|-------------|----------|
| Inline + sources section | Inline parenthetical citations in prose + consolidated Data Sources section. | |
| Footnote-style [1] | Numbered footnote-style citations [1], [2] in prose with footnotes section. More formal/rigorous. | ✓ |
| Register-only (no inline) | All citations in the assumptions register + standalone data sources table. Cleaner prose. | |

**User's choice:** Footnote-style [1]
**Notes:** More formal/rigorous. All data sources cited with access dates (REP-04).

### Q6: Where should the PDF be generated — Colab only, or both environments?

| Option | Description | Selected |
|--------|-------------|----------|
| Colab-only PDF | Colab generates PDF via weasyprint (GTK/pango present or apt-installable). Windows produces HTML only. | ✓ |
| Both, with Windows fallback | Attempt weasyprint on both; fall back to pandoc/pypandoc on Windows if GTK missing. | |
| Colab PDF + Windows HTML-to-print | Colab generates PDF; Windows generates HTML for browser Ctrl+P. | |

**User's choice:** Colab-only PDF
**Notes:** Matches STACK.md 'generate the PDF in Colab only; keep local runs producing the HTML report.' Avoids Windows GTK pain.

---

## Claude's Discretion

- Exact optimistic/pessimistic values for the 5 scenario levers (D-05 lists ranges; researcher/planner finalises specific low/high points with citations)
- Exact tornado input ranges (D-06 gives examples; researcher picks defensible wide ranges)
- Ramp-speed milestone variants for slow/base/fast (planner defines override dicts for `gp_ramp_milestones`)
- BBPIP exact practice/GP split percentage (D-09 — researcher verifies against current DoH factsheet)
- Exact PBS scripts-per-person benchmark vintage and gross-margin-per-script figure (D-11 — researcher cites)
- 3 capture-rate values for pharmacy synergy range (D-12 — researcher picks defensible low/mid/high)
- Jinja2 template file location (inline string vs separate file — planner's call)
- CSS styling specifics (planner/designer's call, investor-professional default)
- Which catchment map goes on page 1 (3km ring with competitors is the obvious choice; planner confirms)
- Whether the 6 duplicate "Next Steps" markdown cells at notebook end are cleaned up in Phase 5
- Whether the billing-mix curve scales BBPIP proportionally or all-or-nothing (planner's call)

## Deferred Ideas

- Monte Carlo confidence intervals (V2-01) — future milestone
- Drive-time isochrone catchments (V2-02) — future milestone
- Interactive dashboard / Streamlit / Voila — out of scope (PROJECT.md)
- Pharmacy retail P&L modelling — out of scope (PROJECT.md)
- Itemised equipment schedule (10+ line items) — deferred in Phase 4 (D-10 uses a lump sum)
- Per-pharmacy PBS dispensing data — out of scope (PROJECT.md, not publicly available)
