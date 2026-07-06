# Phase 5: Scenarios & Executive Report - Context

**Gathered:** 2026-07-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Run base/optimistic/pessimistic scenarios + tornado sensitivity over the Phase 4 `clinic_pnl` pure function, billing-model comparison (70/30 mixed vs 100%-bulk+BBPIP), pharmacy synergy as secondary upside AFTER the standalone verdict, assemble the cited assumptions register, and export the executive PDF report with an explicit go/no-go recommendation. This is the final phase — it consumes every upstream output (catchment maps, demographics, competitor inventory, demand model, P&L, ramp cash flow) via the `report{}` accumulator and renders the investor deliverable.

Scope anchor (from ROADMAP.md, fixed): FIN-04, FIN-05, FIN-06, FIN-07, REP-01, REP-02, REP-03, REP-04. Discussion clarifies HOW to implement within this boundary. The `clinic_pnl` and `clinic_ramp_monthly` pure functions (Phase 4) are the architectural dependency — Phase 5 mutates them only via override dicts. No new financial modelling; no new data acquisition.

</domain>

<decisions>
## Implementation Decisions

### Go/no-go verdict logic
- **D-01:** Primary gate = **steady-state annual EBITDA positive AND margin > 15%**. Payback period reported as context, not the gate. Clinic treated as a long-lived asset — if profitable at steady state, the fit-out amortises over the lease regardless of a 3-5yr payback. The Phase 4 base case (+$258k EBITDA, 38.4% margin) clears this gate comfortably.
- **D-02:** Flip-conditions presented as **tornado zero-crossings** — "base-case margin is 38%; the clinic stays GO down to ~$X rent / ~Y% utilisation before EBITDA turns negative." One sentence per lever, pulled directly from the tornado sensitivity output. Investor-readable, ties verdict to sensitivity.
- **D-03:** **Binary GO/NO-GO** verdict (no CONDITIONAL tier). Decisive — investors want a clear answer. The base case is clearly profitable, so a flat GO with flip-conditions noted is defensible.
- **D-04:** Verdict is **100% standalone**. Pharmacy synergy appears in a SEPARATE section after the verdict, labelled "Secondary upside — not load-bearing." The verdict text never mentions the pharmacy. Matches the Core Value exactly.

### Scenario levers & tornado
- **D-05:** **5 independent scenario levers** moving in base/optimistic/pessimistic: (a) rent ($80k/$100k/$120k), (b) utilisation (65%/75%/85%), (c) service-fee % (32%/35%/38%), (d) ramp speed (slow/base/fast GP-recruitment milestones), (e) billing mix (100% bulk / 70-30 / 100% private). Each moves independently — override dicts on `clinic_pnl` and `clinic_ramp_monthly`.
- **D-06:** Tornado sensitivity on **7-8 inputs**: the 5 scenario levers + $/sqm fit-out + equipment/IT lump sum + consults/GP/day. Wide range per input (e.g. rent $60k-$140k, utilisation 55%-90%, service-fee 28%-40%). One-way sensitivity — each input varied individually while others held at base.
- **D-07:** **Two tornado charts**: (a) annual EBITDA (profitability driver — rent/utilisation/service-fee dominate), (b) peak capital (funding requirement driver — $/sqm/ramp speed dominate). Different levers dominate each view; both add value.
- **D-08:** **Full side-by-side P&L table** — every revenue and cost line for base/optimistic/pessimistic in 3 columns, plus EBITDA/margin/peak-capital/payback rows at the bottom. Matches FEATURES.md "side-by-side P&L table." Most detailed — investor sees exactly where scenarios diverge line-by-line.

### Billing comparison & synergy
- **D-09:** BBPIP 12.5% modelled with **practice/GP split** (per Pitfall 7: practice retains ~half = ~6.25%, GP gets ~6.25%). Researcher verifies the exact split against the current DoH factsheet at build time. Added as a revenue line in the 100%-bulk override dict.
- **D-10:** **Full billing-mix sensitivity curve**: run `clinic_pnl` across `bulk_bill_share = [0%, 25%, 50%, 70%, 100%]` and plot EBITDA vs billing mix. Shows the optimal mix and the crossover where 100%-bulk+BBPIP crosses 70/30-mixed. Most analytical — answers "what billing mix maximises profit?" Replaces a simple 2-column comparison.
- **D-11:** Pharmacy synergy quantified via **per-capita scripts × capture rate**: catchment population × avg scripts/person/yr (PBS benchmark ~12-14) × Priceline's assumed market share of the catchment × gross margin per script (~$8-12). Transparent arithmetic, all cited. Outputs an annual pharmacy profit estimate as "secondary upside."
- **D-12:** Pharmacy synergy presented as a **range**: low/mid/high capture rate (e.g. 15%/20%/25%) → low/mid/high annual pharmacy profit. Matches the uncertainty in pharmacy market share; consistent with the scenario approach.

### Report & PDF design
- **D-13:** Page 1 = **executive summary with verdict + 5 key numbers + one catchment map**. The 5 numbers: steady-state EBITDA, margin, peak capital, operating breakeven month, payback period. Plus one-line flip-conditions from the tornado. Site address + date. Maximum investor impact in 10 seconds.
- **D-14:** **8-section narrative report structure** following the ARCHITECTURE.md §2-§8 flow: (1) Executive Summary, (2) Site & Catchment, (3) Competitor Landscape, (4) Financial Model, (5) Scenarios & Sensitivity, (6) Pharmacy Synergy, (7) Assumptions Register, (8) Data Sources & Citations. Investor reads top-to-bottom.
- **D-15:** **Jinja2 HTML template + weasyprint** rendering pipeline. Full layout control — cover page, page breaks, headers, page numbers, CSS styling. Investor-grade paginated PDF. Template lives in the notebook (string) or a separate template file (planner's call).
- **D-16:** Assumptions register as a **5-column table with all params**: Parameter | Value | Source | Date | Confidence (HIGH/MEDIUM/LOW). Every `BASE_ASSUMPTIONS` key gets a row. Sorted by section (site, demand, financial). Matches Pitfall 13 "value, source, confidence" + adds date.
- **D-17:** **Footnote-style citations [1], [2]** in the report prose with a footnotes section. More formal/rigorous than inline parentheticals. All data sources cited with access dates (REP-04).
- **D-18:** **Colab-only PDF generation**. weasyprint's GTK/pango deps are present or apt-installable in one line on Colab. Local Windows runs produce the HTML report only, with a printed note: "Open in Colab to generate the PDF." Matches STACK.md. Avoids the Windows GTK runtime pain.

### Claude's Discretion
- Exact optimistic/pessimistic values for the 5 scenario levers (D-05 lists the base-case-anchored ranges; researcher/planner finalises the specific low/high points with citations)
- Exact tornado input ranges (D-06 gives examples; researcher picks defensible wide ranges per input)
- The ramp-speed milestone variants for slow/base/fast (planner defines the override dicts for `gp_ramp_milestones`)
- BBPIP exact practice/GP split percentage (D-09 — researcher verifies against current DoH factsheet)
- Exact PBS scripts-per-person benchmark vintage and gross-margin-per-script figure (D-11 — researcher cites)
- The 3 capture-rate values for the pharmacy synergy range (D-12 — researcher picks defensible low/mid/high)
- Jinja2 template file location (inline string in notebook vs separate `report_template.html` file — planner's call)
- CSS styling specifics (fonts, colours, page margins — planner/designer's call, investor-professional default)
- Which catchment map goes on page 1 (the 3km ring with competitors is the obvious choice; planner confirms)
- Whether the 6 duplicate "Next Steps" markdown cells at the notebook end (Phase 2-3 artifact, noted in Phase 4 context) are cleaned up as part of Phase 5 cell insertion
- Whether the billing-mix sensitivity curve (D-10) includes BBPIP only at 100% bulk or scales it proportionally (planner's call — structurally BBPIP is an all-or-nothing practice incentive)

</decisions>

<specifics>
## Specific Ideas

- The Phase 4 finding that **payback breakeven is NOT reached in 36 months** is the elephant in the room. D-01's verdict logic (steady-state EBITDA as the gate, payback as context) is the structural response — the clinic is profitable but slow to pay back, and the verdict treats it as a long-lived asset. The exec summary must present payback honestly ("~4-5 years to recoup fit-out + ramp losses") without letting it override the profitability verdict.
- ARCHITECTURE.md Pattern 5 (`report{}` accumulator → markdown/HTML → PDF) is the structural template. Phase 4 already deposited 9 metrics into `report{}`; Phase 5 adds scenario/sensitivity/synergy metrics and renders the full report. §8 is a pure render step — re-running it alone regenerates the PDF.
- The `{**BASE_ASSUMPTIONS, **overrides}` scenario pattern (Phase 1 D-10, Phase 4 D-16) is the engine for ALL Phase 5 scenarios, tornado, and billing comparison. Every scenario is an override dict; no new financial logic.
- PITFALLS.md Pitfall 7 (MBS item/incentive changes) drives D-09 (BBPIP split modelling) and D-10 (billing-mix sensitivity). The 70/30 mixed base case (Phase 4) vs 100%-bulk+BBPIP comparison is the explicit Pitfall 7 "model two billing strategies" response.
- PITFALLS.md Pitfall 13 (rent and key assumptions as facts) drives D-16 (assumptions register) and D-06 (tornado). The register + tornado together satisfy "assumptions register table + one-way sensitivity + exec summary states which assumptions the go/no-go is most sensitive to."
- PITFALLS.md Pitfall 16 (notebook hygiene / PDF export) drives D-18 (Colab-only PDF) and D-13 (page 1 = verdict + numbers). "Burying the go/no-go — investors read page 1 only" is the explicit constraint.
- FEATURES.md "Executive summary + explicit go/no-go recommendation" (LOW effort, but the single most important feature): "must state the recommendation, the 3-5 numbers that drive it, and the conditions under which it flips." D-01/D-02/D-13 implement this exactly.
- FEATURES.md "Base / optimistic / pessimistic scenarios" (MEDIUM): "Vary: billing mix, consults/GP/day, ramp speed, rent; present as side-by-side P&L table." D-05/D-08 implement this.
- FEATURES.md "Sensitivity analysis (tornado-style)" (MEDIUM): "One-way sensitivity on 5-8 key inputs; tornado chart is the expected visual." D-06/D-07 implement this.
- FEATURES.md "Cited data sources + dated assumptions register" (LOW): "Single assumptions table: value, source, date, confidence." D-16 implements this.
- FEATURES.md "Executive PDF export" (MEDIUM): "must work in free Colab; all figures must render as static images." D-15/D-18 implement this.
- The `report{}` dict already holds: `steady_state_ebitda`, `steady_state_margin`, `practice_revenue`, `gp_billings`, `fitout_total`, `peak_capital`, `breakeven_operating`, `breakeven_payback`, `working_capital_buffer`. Phase 5 adds: scenario metrics (base/opt/pess EBITDA + payback), tornado zero-crossings, billing-mix curve data, pharmacy synergy range, assumptions register rows, and the verdict itself.
- Phase 4's `outputs/ramp_cashflow.png` is ready for the PDF. Phase 5 adds: 2 tornado charts, 1 billing-mix curve, 1 scenario comparison (if visual), and reuses the Phase 2/3 static catchment + competitor maps.
- The pharmacy synergy (D-11/D-12) is the ONLY new computation in Phase 5 that isn't a `clinic_pnl` override. It's a standalone arithmetic block — per-capita scripts × capture rate × margin — presented as a range, clearly labelled "secondary upside."

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture & patterns
- `.planning/research/ARCHITECTURE.md` §"Pattern 3: Pure-Function Financial Model" — the `clinic_pnl(a: dict) -> dict` + `{**BASE_ASSUMPTIONS, **overrides}` scenario pattern that ALL Phase 5 scenarios/tornado/billing-comparison use. No new financial logic; Phase 5 is override dicts + rendering.
- `.planning/research/ARCHITECTURE.md` §"Pattern 5: Report Metrics Accumulator → Markdown → PDF" — the `report{}` dict → template → weasyprint PDF pipeline. D-15 extends it to a Jinja2 HTML template (full layout control) rather than the f-string markdown example. §8 is a pure render step.
- `.planning/research/ARCHITECTURE.md` §"Standard Architecture" + "Recommended Project Structure" — the §7 (Scenarios & Sensitivity) + §8 (Executive Report) notebook section layout. §7 produces scenario tables + tornado charts; §8 renders the PDF from `report{}`.
- `.planning/research/ARCHITECTURE.md` §"Data Flow" #4 (Report flow) — "every section appends to `report{}`; §8 is a pure render step — re-running §8 alone regenerates the PDF from current state." Phase 5 §8 must be re-runnable standalone.
- `.planning/research/ARCHITECTURE.md` §"Data Flow" #3 (Assumption flow) — `BASE_ASSUMPTIONS` is the only source of financial constants; §7 mutates only via override dicts. Phase 5 must not introduce new financial constants outside `BASE_ASSUMPTIONS`.

### Pitfalls to avoid (each maps to a decision)
- `.planning/research/PITFALLS.md` §"Pitfall 7" (MBS item/incentive changes) — drives D-09 (BBPIP practice/GP split) and D-10 (billing-mix sensitivity curve). "Model two billing strategies in scenarios: (a) 70/30 mixed billing without BBPIP; (b) 100% bulk billing with BBPIP 12.5%." The exact split and BBPIP mechanics must be re-verified against current DoH factsheets.
- `.planning/research/PITFALLS.md` §"Pitfall 13" (rent and key assumptions presented as facts) — drives D-16 (5-column assumptions register: value/source/date/confidence) and D-06 (tornado on 7-8 inputs). "Run one-way sensitivity (tornado chart) on rent ±40%, service fee %, consults/day, and bulk-billing mix. The exec summary must state which assumptions the go/no-go is most sensitive to."
- `.planning/research/PITFALLS.md` §"Pitfall 16" (notebook hygiene / PDF export) — drives D-18 (Colab-only PDF) and D-13 (page 1 = verdict + 5 numbers + map). "Burying the go/no-go — investors read page 1 only — Recommendation + 3 key sensitivities on the first page of the PDF." Also: "Folium maps are HTML/JS — export static maps (contextily/matplotlib) for the PDF."
- `.planning/research/PITFALLS.md` §"Pitfall 15" (point estimates without uncertainty) — drives D-12 (pharmacy synergy as a range, not a point). The scenario envelope + tornado + synergy range together address the "show uncertainty" expectation.

### Features & quality bar
- `.planning/research/FEATURES.md` §"Core feature table" — Executive summary + go/no-go (LOW effort, but THE deliverable), Base/optimistic/pessimistic scenarios (MEDIUM), Sensitivity analysis tornado (MEDIUM), Cited data sources + dated assumptions register (LOW), Executive PDF export (MEDIUM). Each maps directly to a decision above.
- `.planning/research/FEATURES.md` §"Key numbers" — BBPIP 12.5% practice incentive from Nov 2025; GP earnings split 60-70% GP / 30-40% practice; private fee Level B inner-Melb ~$90-110. Phase 5 uses these in the billing-mix comparison and assumptions register.
- `.planning/research/FEATURES.md` §"Differentiators" — "Scenarios + tornado + optional CI bands" and "Fully cited assumptions register" distinguish this from v1 and from lazy template reports.
- `.planning/research/FEATURES.md` §"Competitor archetypes" table — "Our Approach" column: Scenarios + tornado + optional CI bands; Fully cited assumptions register; Cached, re-runnable notebook. Phase 5 delivers the first two; the re-runnability is inherited.

### Stack & library specifics
- `.planning/research/STACK.md` §"PDF report generation" — jinja2 3.1.x (preinstalled) + weasyprint ≥65 (pip). "Weasyprint in Colab needs `!apt-get install -y libpango-1.0-0 libpangocairo-1.0-0` — one line." "Generate the PDF in Colab only; keep local runs producing the HTML report." Drives D-15/D-18.
- `.planning/research/STACK.md` §"Supporting Libraries" — matplotlib 3.10.x for the 2 tornado charts + billing-mix curve (all static figures for the PDF); folium 0.20.x is inline-only (NOT in PDF — static matplotlib+contextily maps from Phase 2/3 are reused).
- `CLAUDE.md` (STACK.md source) §"PDF report generation" — confirms the Colab-only PDF decision and the weasyprint + jinja2 pipeline.

### Requirements & roadmap
- `.planning/REQUIREMENTS.md` §"Financial Model (FIN)" — FIN-04 (base/opt/pess as override dicts), FIN-05 (tornado sensitivity ranking), FIN-06 (70/30 mixed vs 100%-bulk+BBPIP side-by-side), FIN-07 (pharmacy synergy as secondary upside after standalone verdict) are the verifiable financial success criteria.
- `.planning/REQUIREMENTS.md` §"Reporting (REP)" — REP-01 (assumptions register: value/source/confidence), REP-02 (exec summary + go/no-go), REP-03 (PDF via jinja2+weasyprint, Colab-runnable), REP-04 (inline citations with access dates) are the verifiable reporting success criteria.
- `.planning/ROADMAP.md` §"Phase 5 — Scenarios & Executive Report" — phase goal, success criteria (4 items), dependencies (Phase 4 + upstream figures from Phases 2-3), research flag (No — jinja2 + weasyprint is a known path; only risk is Windows GTK, resolved by D-18).

### Prior phase context (integration points)
- `.planning/phases/04-clinic-financial-model/04-CONTEXT.md` — D-01..D-16 establish `clinic_pnl(a)` + `clinic_ramp_monthly(a, months=36)` as pure functions, the `{**BASE_ASSUMPTIONS, **overrides}` pattern, the $/sqm triplet ($1,200/$1,700/$2,200), the ramp milestones + book-fill curve, the 9 `report{}` deposits, and the headline findings (EBITDA +$258k/38.4% margin, peak capital $490k, operating breakeven month 11, payback >36 months). Phase 5 reads ALL of these; the deferred items (BBPIP, scenarios, tornado, synergy, verdict, register) are exactly what Phase 5 delivers.
- `.planning/phases/04-clinic-financial-model/04-02-SUMMARY.md` — confirms the 9 `report{}` deposits, the ramp chart at `outputs/ramp_cashflow.png`, and the "payback not in 36 months" finding that drives D-01's verdict logic.
- `.planning/phases/03-demand-competitors/03-CONTEXT.md` — D-13/D-14 establish the three market-share framings and the explicit deferral of the go/no-go verdict to Phase 5. Phase 5 §1 (Executive Summary) consumes the §5 demand outputs as context for the verdict.
- `.planning/phases/02-catchment-demographics/02-CONTEXT.md` — D-27/D-29/D-30 establish the static matplotlib+contextily map figures (one per ring) that Phase 5 reuses in the PDF. Folium maps are inline-only (D-30).
- `.planning/phases/01-scaffolding-data-pipeline/01-CONTEXT.md` — D-08/D-10 establish the `BASE_ASSUMPTIONS` flat-dict + `{**BASE_ASSUMPTIONS, **overrides}` scenario pattern that Phase 5's scenario/tornado/billing-comparison override dicts must honour.

### Local data assets & outputs
- `Johnston_St_v2.ipynb` §0 (`BASE_ASSUMPTIONS`) — the locked financial constants; §5 (`market_share_results`, `ring_demand`, `clinic_capacity`) — demand-side context for the verdict; §6 (`clinic_pnl`, `clinic_ramp_monthly`, `report{}` with 9 deposits) — the Phase 5 architectural dependency.
- `outputs/ramp_cashflow.png` (Phase 4) — ready for the PDF Financial Model section.
- `outputs/catchment_*.png` + `outputs/competitors_*.png` (Phase 2/3 static maps) — ready for the PDF Site & Catchment + Competitor Landscape sections.
- `data/cache/competitors.geojson` (Phase 3) — the competitor inventory backing the Competitor Landscape section.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`clinic_pnl(a: dict) -> dict`** (§6 of `Johnston_St_v2.ipynb`) — the pure-function steady-state P&L. Phase 5 calls it with override dicts for every scenario, tornado input, and billing-mix point. No modification to the function itself.
- **`clinic_ramp_monthly(a: dict, months: int = 36) -> dict`** (§6.2) — the 36-month ramp cash flow. Phase 5 calls it with scenario override dicts to produce scenario-specific peak capital and breakeven metrics.
- **`report = {}` accumulator** (§6, Pattern 5) — already holds 9 metrics from Phase 4. Phase 5 §7 adds scenario/sensitivity/synergy metrics; §8 renders the full dict into the PDF.
- **`BASE_ASSUMPTIONS` dict** (§0) — holds every locked financial constant. Phase 5 adds NO new financial constants (all scenario variation is via override dicts, not new keys). The assumptions register (D-16) reads every key + its citation comment.
- **Phase 2/3 static map figures** (`outputs/catchment_*.png`, `outputs/competitors_*.png`) — already saved as PNGs, ready for the PDF. No re-generation needed.
- **`outputs/ramp_cashflow.png`** (Phase 4) — the ramp chart, ready for the PDF Financial Model section.

### Established Patterns
- **`{**BASE_ASSUMPTIONS, **overrides}` scenario pattern** (Phase 1 D-10, Phase 4 D-16) — every Phase 5 scenario is an override dict. No new financial logic; no constants defined outside §0.
- **`report{}` accumulator** (ARCHITECTURE.md Pattern 5) — every Phase 5 section deposits its headline numbers; §8 is a pure render step.
- **Pure-function financial model** (ARCHITECTURE.md Pattern 3) — Phase 5 does NOT modify `clinic_pnl` or `clinic_ramp_monthly`. It calls them with different inputs.
- **Static matplotlib figures for PDF** (Phase 2 D-27/D-30) — all PDF figures are matplotlib PNGs, never folium (HTML/JS). Phase 5's 2 tornado charts + billing-mix curve follow this pattern.
- **Citation comments in `BASE_ASSUMPTIONS`** (PIPE-05) — every financial constant has a `# source — date` comment. The assumptions register (D-16) renders these into the 5-column table.

### Integration Points
- **§7 Scenarios & Sensitivity** (new in Phase 5) → produces scenario table, 2 tornado charts, billing-mix curve, pharmacy synergy range; deposits metrics into `report{}`. Consumes `clinic_pnl` + `clinic_ramp_monthly` via override dicts.
- **§8 Executive Report** (new in Phase 5) → renders `report{}` + saved PNGs into the Jinja2 HTML template → weasyprint PDF. Pure render step; re-runnable standalone.
- **§6 outputs** (Phase 4) → `clinic_pnl`, `clinic_ramp_monthly`, 9 `report{}` deposits, `outputs/ramp_cashflow.png`. Phase 5 §7 reads the functions; §8 reads the deposits + PNG.
- **§2/§3/§4/§5 outputs** (Phases 2-3) → catchment maps, demographics tables, competitor inventory, demand model results. Phase 5 §8 renders these in the report via `report{}` deposits (to be added in §7 or at §8 render time) + the saved PNG figures.

</code_context>

<deferred>
## Deferred Ideas

- **Monte Carlo confidence intervals** (V2-01) — future milestone. The parameterised P&L + scenario machinery make this cheap to add later (triangular distributions on 4-6 inputs, 1-5k draws, percentile bands on breakeven). Not in Phase 5 scope.
- **Drive-time isochrone catchments** (V2-02) — future milestone. Radial buffers are the Phase 2-5 approach; isochrones are a robustness check for a later version.
- **Interactive dashboard / Streamlit / Voila** — out of scope (PROJECT.md). The notebook + PDF is the deliverable.
- **Pharmacy retail P&L modelling** — out of scope (PROJECT.md). The pharmacy synergy (D-11/D-12) is a single secondary-upside estimate, not a full pharmacy business model.
- **Itemised equipment schedule** (10+ line items) — deferred in Phase 4 (D-10 uses a single equipment & IT lump sum). Phase 5's assumptions register carries the lump sum, not the itemisation.
- **Per-pharmacy PBS dispensing data** — out of scope (PROJECT.md, not publicly available at that granularity). The per-capita scripts benchmark (D-11) is the cited proxy.

</deferred>

---

*Phase: 05-scenarios-executive-report*
*Context gathered: 2026-07-06*
