# Phase 4: Clinic Financial Model - Context

**Gathered:** 2026-07-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the core standalone clinic P&L as a pure function of the parameters dict — mixed-billing revenue (service-fee model, not gross billings), full cost lines, fit-out capex, monthly ramp-up curve — producing **peak capital requirement** and **months-to-breakeven** as headline outputs. The `clinic_pnl(params)` function built here is the single most important architectural dependency: Phase 5 scenarios, sensitivity, BBPIP billing comparison, pharmacy synergy, and the go/no-go verdict all run over it via override dicts.

Scope anchor (from ROADMAP.md, fixed): FIN-01, FIN-02, FIN-03. Discussion clarifies HOW to implement within this boundary — not whether to add new capabilities. Scenarios/sensitivity/tornado (FIN-04/05), BBPIP billing-model comparison (FIN-06), pharmacy synergy (FIN-07), assumptions register (REP-01), and the go/no-go verdict (REP-02) are all **Phase 5** — out of scope here. Phase 4 builds the function; Phase 5 runs scenarios over it.

</domain>

<decisions>
## Implementation Decisions

### Revenue model granularity
- **D-01:** Weighted item mix, not item-23-only. The GP revenue top line models Level B (item 23) as the base plus Level C (item 36), care plans (item 721), health assessments (item 701), and minor procedures — each with a cited % of consult volume and a cited MBS rebate. More realistic than a single-item model (~15-25% higher revenue), each line sourced. Researcher cites the item-mix percentages and rebate values at build time (MBS Online, 2025-26 vintage). Aligns with FEATURES.md "item mix, not just item 23".
- **D-02:** Allied health (1 FTE) on the same service-fee % split as GPs — practice retains ~30-35% of allied health billings, practitioner keeps the rest. One revenue line (allied billings × service fee %), symmetric with the GP model. No separate room-rental income line. (If Phase 5 wants to test a room-rental alternative, it's an override dict — but the base-case structure is % split.)
- **D-03:** Steady-state consult volume = clinic capacity from §5 (5 FTE × 5,500/yr = 27,500 consults/yr). The P&L is a function of capacity, not captured demand. The §5 market-share results are displayed as context ("this volume = X% of ring demand") alongside the P&L but do NOT drive the volume. Demand is the feasibility question; capacity is the P&L input. Cleanest separation: the P&L answers "if the clinic fills its books, is it profitable?"; Phase 5 scenarios explore what happens if it doesn't.
- **D-04:** $95 private fee = TOTAL fee (rebate + gap), NOT a gap on top of the rebate. Practice collects $95 per private consult (of which $43.90 is the MBS rebate claimed back by the patient, $51.10 is the out-of-pocket gap). Aligns with FEATURES.md inner-Melb gap ~$46-66 and the standard RACGP "private fee" definition. Pitfall 11 compliant — no gross-billings confusion.

### Ramp-up & time axis
- **D-05:** Monthly cash flow for 36 months (years 1-3). Most granular — shows the real cash drain during ramp-up; peak capital and breakeven month read directly off the cumulative cash-flow curve. Pitfall 12's recommended treatment. The pure function returns a monthly array plus derived headline numbers.
- **D-06:** Discrete GP-recruitment milestones + per-GP book-fill curve. Ramp: 2 GPs at open, +1 at month 6, +1 at month 12, +1 at month 18 → 5 FTE by month 18. Each GP's utilisation ramps from ~40% to 75% (the steady-state target) over their first 12 months. Milestones and book-fill parameters live in `BASE_ASSUMPTIONS` (cited). Matches Pitfall 12 "2 GPs at open → 5 by month 18, books fill over 12-24 months".
- **D-07:** Support staff (nurse/reception) scale with GP count during ramp; rent, insurance, and admin/IT/utilities are fixed at 100% from day 1. You don't need 2 receptionists for 2 GPs, but rent is owed from day 1. Two cost categories in the ramp model: variable staffing (scales with GP FTE) and fixed overheads (flat from month 0).
- **D-08:** Both breakeven definitions reported as headlines: (a) **operating breakeven** = first month where monthly EBITDA > 0; (b) **cumulative/payback breakeven** = month where cumulative cash flow crosses zero (fit-out + accumulated losses fully recovered). **Peak capital** = max cumulative negative cash flow. Three headline numbers. Most informative for investors — operating breakeven says when the clinic stops bleeding monthly; payback breakeven says when the investor is whole.

### Fit-out capex derivation
- **D-09:** Floor area = **170 sqm**, taken from the floor plan PDF (`data/local/292 Johnston Ground Floor Plan (1).pdf` — the 292 Johnston ground-floor tenancy). Cross-checked via room count × sqm/room (RACGP 5th-edition standards: consult room ~14-18 sqm, treatment room 15-20 sqm). 170 sqm is site-specific and below the generic 250-350 sqm range in PITFALLS.md — this is a smaller fit-out, so capex is on the lower end. The 170 sqm figure and its derivation (stated on plan vs measured) are documented in the assumptions register.
- **D-10:** Two capex lines: (a) base fit-out ($/sqm × 170 sqm, construction only — walls, hand basins, electrical, plumbing, flooring) and (b) a separate cited equipment & IT lump sum (exam beds, treatment trolley, steriliser, clinical software, hardware). PITFALLS.md Pitfall 12 implies equipment/IT/compliance are add-ons to the $/sqm base. Two lines, not a 10-line equipment schedule and not a single all-in rate.
- **D-11:** $/sqm as a low/mid/high triplet: **$1,200 / $1,700 / $2,200 per sqm** → base fit-out range **$204k / $289k / $374k** (× 170 sqm), shown upfront in §6. The triplet is carried as three BASE_ASSUMPTIONS values; the mid ($1,700) is the base-case point estimate, low/high feed Phase 5 sensitivity. Equipment & IT lump sum cited separately (researcher picks a defensible cited figure in the ~$40-80k range for a 5-GP clinic).
- **D-12:** Peak capital = fit-out capex + max cumulative operating loss during ramp + **3-month working-capital buffer** (3 months of fixed costs: rent + insurance + admin/IT/utilities, as a cited BASE_ASSUMPTIONS parameter). Conservative headline — recognises real-world funding needs a contingency beyond the modelled cumulative loss. The buffer is added on top of the modelled peak, not buried in it.

### Cost lines & sourcing
- **D-13:** Lean support staffing: **1 FTE practice nurse, 1.5 FTE reception/admin, 0.5 FTE practice manager**. Flagged as lean vs the RACGP "standard 5-GP" structure (1N + 2R + 0.5M) — more realistic for a capital-constrained startup that cross-trains reception to do some admin. Practice nurse scales with GP count during ramp (D-07); reception/admin and manager are fixed from day 1 (reception coverage needed from open).
- **D-14:** Modern Award rates + on-costs (super 11.5%, WorkCover). Public, dated, defensible — award rates are citable to the dollar. Researcher cites the current Nursing Award and Clerks-Private Sector Award pay points + the on-cost multiplier. Lower than market rates but the most auditable basis for an investor report.
- **D-15:** Three grouped overhead lines, each cited: (a) **insurance** (professional indemnity + public liability — cited lump sum), (b) **consumables & medical supplies** (gloves, swabs, syringes — cited $/consult or % of revenue), (c) **admin/IT/utilities** (clinical software subscriptions, hardware leases, cleaning, electricity — cited lump sum). Three lines, not 6-8 itemised and not a single % of revenue. Matches the REP-01 assumptions-register requirement (Phase 5, but the cited lines built now make the register trivial).
- **D-16:** `clinic_pnl()` returns BOTH: (a) a **steady-state annual P&L** (5 FTE, 75% utilisation, full books — the "destination") AND (b) the **36-month monthly ramp cash-flow array** (the "path"). The steady-state P&L is the ARCHITECTURE.md Pattern 3 function; the monthly ramp is a separate function that calls `clinic_pnl` per month with ramp-scaled parameters (GP count × book-fill utilisation per D-06, variable staffing per D-07). Two views, one function family. Most teaching value: "here's where it lands, here's how it gets there."

### Claude's Discretion
- Exact item-mix percentages and MBS rebate values for Level C / care plans / health assessments / procedures (researcher cites MBS Online 2025-26 vintage)
- Exact equipment & IT lump-sum figure (researcher picks a cited defensible figure in the ~$40-80k range)
- Exact Modern Award pay points and the on-cost multiplier (researcher cites current award values + super/WorkCover rates)
- Exact cited figures for the 3 grouped overhead lines (insurance, consumables, admin/IT/utilities — researcher sources and dates each)
- The 3-month working-capital buffer parameter (which fixed costs are included — researcher defines the basket)
- Whether the monthly ramp function reuses `clinic_pnl` per month via parameter overrides or is a separate derivation (D-16 implies per-month calls; planner decides exact structure)
- How the §5 market-share context is displayed alongside the capacity-driven P&L (printed note vs small table — teaching-clarity call)
- Steady-state utilisation target (75% is already in `BASE_ASSUMPTIONS["utilisation"]` — locked, not re-decided)
- Whether the 6 duplicate "Next Steps" markdown cells at the end of the notebook (a cell-replacement artifact from Phases 2-3) are cleaned up as part of Phase 4 cell insertion (notebook hygiene; planner's call)

</decisions>

<specifics>
## Specific Ideas

- PITFALLS.md Pitfalls 7, 11, 12, 13 are the structural templates for this phase: MBS item/incentive changes making revenue assumptions stale (P7 — date-stamp every item value, model BBPIP as a Phase 5 scenario not a Phase 4 base case), confusing GP gross billings with practice revenue (P11 — the ~3× overstatement; service-fee % row is the structural fix, locked), ignoring ramp-up and underestimating fit-out capex (P12 — monthly ramp + cited $/sqm × floor area + peak capital headline), rent and key assumptions presented as facts (P13 — assumptions register + sensitivity, the register lines are built here and the tornado is Phase 5).
- ARCHITECTURE.md Pattern 3 (Pure-Function Financial Model) is the exact structural template: `clinic_pnl(a: dict) -> dict`, no globals, scenarios become override dicts. D-16 extends it to return both a steady-state annual dict and a monthly ramp array.
- ARCHITECTURE.md data flow #3 (Assumption flow): `BASE_ASSUMPTIONS` (§0) is the only source of financial constants; §5 outputs (demand, required share) merge with it into the `clinic_pnl` input; §7 (Phase 5) mutates only via override dicts. Phase 4 honours this — every new financial constant goes into `BASE_ASSUMPTIONS` with a citation comment (PIPE-05).
- FEATURES.md financial feature rows: "Full clinic P&L" (HIGH priority, P1) — mixed billing 70/30, item mix, costs: GP % split, nurse/admin, rent $100k, insurance, consumables, IT; "Breakeven + time-to-breakeven" (MEDIUM) — ramp explicitly modelled; "Fit-out capital estimate" (LOW-MEDIUM) — benchmark $/sqm, cited, high-uncertainty input.
- FEATURES.md key numbers: GP retains ~60-70% of billings, practice keeps 30-40% (base 35% per BASE_ASSUMPTIONS); private fee Level B inner-Melb ~$90-110 (base $95); BBI triple incentive from Nov 2023, BBPIP 12.5% from Nov 2025 (Phase 5 scenario, not Phase 4 base).
- The floor plan PDF (`data/local/292 Johnston Ground Floor Plan (1).pdf`) is the site-specific anchor for the 170 sqm figure — researcher reads it and documents the derivation. This is what makes the fit-out capex site-specific rather than a generic range.
- Phase 3 §5 outputs are the integration points: `market_share_results` (per-ring share_of_total/unmet/pop), `ring_demand` (age-adjusted consult demand per ring), `clinic_capacity` (27,500 consults/yr). Phase 4 reads these for the context display (D-03) but the P&L volume is capacity-driven, not demand-driven.
- `BASE_ASSUMPTIONS` already holds the locked financial constants from Phase 1: `bulk_bill_share=0.70`, `std_rebate=43.90`, `private_fee=95.00`, `gp_revenue_share=0.35`, `rent_yr=100_000`, `fitout_capital=350_000` (placeholder — to be replaced by the D-09/D-10/D-11 derivation), `n_gp_fte=5`, `n_allied_fte=1`, `days_per_yr=220`, `utilisation=0.75`. Phase 4 adds the new constants (item-mix %, item rebates, staffing FTE/award rates, overhead figures, ramp milestones, book-fill curve, $/sqm triplet, equipment lump sum, working-capital buffer months) with citation comments.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture & patterns
- `.planning/research/ARCHITECTURE.md` §"Pattern 3: Pure-Function Financial Model" — the exact `clinic_pnl(a: dict) -> dict` structural template, the scenario-override-dict pattern, and the breakeven-months derivation. D-16 extends it to return both steady-state annual + monthly ramp.
- `.planning/research/ARCHITECTURE.md` §"Standard Architecture" + "Recommended Project Structure" — the §6 (Financial Model) notebook section layout and the `report{}` metrics accumulator that §6 deposits into (Pattern 5, consumed by Phase 5 §8).
- `.planning/research/ARCHITECTURE.md` §"Data Flow" #3 (Assumption flow) — `BASE_ASSUMPTIONS` is the only source of financial constants; §5 outputs merge into the `clinic_pnl` input; Phase 5 mutates only via override dicts. Phase 4 must not introduce globals or redefine existing constants.
- `.planning/research/ARCHITECTURE.md` §"Pattern 2: Single Parameters Cell" — every new financial constant (item mix, staffing, overheads, ramp, capex) goes into `BASE_ASSUMPTIONS` with a citation comment (PIPE-05).

### Pitfalls to avoid (each maps to a decision)
- `.planning/research/PITFALLS.md` §"Pitfall 7" (MBS item/incentive changes) — drives the date-stamping of every MBS item value (D-01); BBPIP 12.5% is a Phase 5 scenario, NOT a Phase 4 base case (scope boundary)
- `.planning/research/PITFALLS.md` §"Pitfall 11" (GP gross billings vs practice revenue) — the ~3× overstatement; drives D-04 ($95 = total fee), the service-fee % structure (locked from PROJECT.md), and the "GP payments are NOT a practice cost" guardrail
- `.planning/research/PITFALLS.md` §"Pitfall 12" (ramp-up + fit-out capex) — drives D-05 (monthly 36-month cash flow), D-06 (milestones + book-fill), D-08 (peak capital + both breakevens), D-09/D-10/D-11 (fit-out from floor plan × $/sqm triplet)
- `.planning/research/PITFALLS.md` §"Pitfall 13" (rent and key assumptions as facts) — drives the per-line citation discipline (D-14/D-15); the full assumptions register + tornado is Phase 5 (REP-01/FIN-05) but the cited lines are built now

### Features & quality bar
- `.planning/research/FEATURES.md` §"Core feature table" (Full clinic P&L, Breakeven + time-to-breakeven, Fit-out capital estimate rows) — the feature priority and approach notes (item mix, ramp explicit, $/sqm cited)
- `.planning/research/FEATURES.md` §"Key numbers" — GP earnings split (60-70% GP / 30-40% practice), private fee Level B inner-Melb ~$90-110, BBI/BBPIP incentives (Phase 5 scenario), FTE GP consult capacity ~5,000-6,000/yr
- `.planning/research/FEATURES.md` §"Dependency graph" — "Clinic P&L requires market-share/consult-volume + billing benchmarks"; "Breakeven requires P&L + fit-out + ramp curve"; "Scenarios require parameterised P&L" (Phase 5, but the parameterisation is built here)

### Requirements & roadmap
- `.planning/REQUIREMENTS.md` §"Financial Model (FIN)" — FIN-01 (pure-function P&L, service-fee %, mixed billing 70/30, item 23 $43.90), FIN-02 (cost model: rent, wages, insurance, consumables, admin, allied health), FIN-03 (fit-out capex $1,200-$2,200/sqm + monthly ramp + peak capital + months to breakeven) are the verifiable success criteria
- `.planning/ROADMAP.md` §"Phase 4 — Clinic Financial Model" — phase goal, success criteria, dependencies (Phase 3), research flag (Yes — fit-out $/sqm, private-fee levels, service-fee % are MEDIUM-confidence ranges; BBPIP mechanics re-verified in Phase 5)

### Prior phase context (integration points)
- `.planning/phases/03-demand-competitors/03-CONTEXT.md` — §5 outputs (`market_share_results`, `ring_demand`, `clinic_capacity = 27,500`) are the Phase 4 integration points (D-03 context display). D-13/D-14 there locked the GP-capacity and market-share framings; Phase 4 reads, does not redefine.
- `.planning/phases/01-scaffolding-data-pipeline/01-CONTEXT.md` — D-08/D-10 establish the `BASE_ASSUMPTIONS` flat-dict + `{**BASE_ASSUMPTIONS, **overrides}` scenario pattern that Phase 4's `clinic_pnl` must honour. The `fitout_capital=350_000` placeholder is replaced by the D-09/D-10/D-11 derivation.
- `.planning/phases/02-catchment-demographics/02-CONTEXT.md` — establishes the `BASE_ASSUMPTIONS` extension pattern (new keys with citation comments) and the source-agnostic tidy-output convention.

### Local data assets
- `data/local/292 Johnston Ground Floor Plan (1).pdf` — the ground-floor tenancy floor plan; source of the 170 sqm figure (D-09). Researcher reads it and documents the derivation.
- `Johnston_St_v2.ipynb` §0 (`BASE_ASSUMPTIONS`) — the locked financial constants already present; §5 (`market_share_results`, `ring_demand`, `clinic_capacity`) — the demand-side integration points.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`BASE_ASSUMPTIONS` dict** (§0 of `Johnston_St_v2.ipynb`) — already holds every locked financial constant: `bulk_bill_share=0.70`, `std_rebate=43.90`, `private_fee=95.00`, `gp_revenue_share=0.35`, `rent_yr=100_000`, `fitout_capital=350_000` (placeholder, replaced by D-09/D-10/D-11), `n_gp_fte=5`, `n_allied_fte=1`, `days_per_yr=220`, `utilisation=0.75`, `gp_fte_consults_per_yr=5500`. Phase 4 adds new keys (item-mix %, item rebates, staffing FTE/award rates, overheads, ramp milestones, book-fill curve, $/sqm triplet, equipment lump sum, working-capital buffer months) with citation comments per PIPE-05. Must not break the `{**BASE_ASSUMPTIONS, **overrides}` scenario pattern.
- **Phase 3 §5 outputs** — `market_share_results` (per-ring dict: share_of_total_a/b/mid, share_of_unmet, patients_needed, share_of_pop), `ring_demand` (per-ring age-adjusted consult demand), `clinic_capacity` (27,500 consults/yr = 5 FTE × 5,500). Phase 4 reads these for the D-03 context display.
- **`PROJECT_ROOT` + `CACHE_DIR` + `data/local/`** (§0) — path resolution for the floor plan PDF (D-09). No new HTTP boundary (Phase 4 makes no API calls — pure computation).

### Established Patterns
- **Single parameters cell** (PIPE-05) — no numeric literal outside `BASE_ASSUMPTIONS`. Every new financial constant (item mix, staffing, overheads, ramp, capex) lives in the dict or is derived from it.
- **Pure-function financial model** (ARCHITECTURE.md Pattern 3) — `clinic_pnl(a: dict) -> dict`, no globals, no notebook state. D-16 extends to return steady-state annual + monthly ramp array.
- **`{**BASE_ASSUMPTIONS, **overrides}` scenario pattern** (Phase 1 D-10) — Phase 5 scenarios are override dicts; Phase 4 must not break this. Every new key is overridable.
- **`report{}` metrics accumulator** (ARCHITECTURE.md Pattern 5) — §6 deposits headline numbers (`report["peak_capital"]`, `report["breakeven_operating"]`, `report["breakeven_payback"]`, `report["steady_state_ebitda"]`) for Phase 5 §8 to render.

### Integration Points
- **§6 Financial Model** (new in Phase 4) → produces `clinic_pnl()` + base-case steady-state P&L + 36-month ramp cash flow + headline metrics, consumed by Phase 5 §7 (scenarios/sensitivity) and §8 (report).
- **§5 demand outputs** (Phase 3) → read by §6 for the market-share context display (D-03); the P&L volume is capacity-driven, not demand-driven.
- **`BASE_ASSUMPTIONS`** → Phase 4 adds ~15-20 new financial keys (item mix, staffing, overheads, ramp, capex, buffer) but must not redefine existing locked constants.
- **Notebook cell insertion** → §6 cells are appended after the §5 demand-model cells. Note: there are 6 duplicate "Next Steps" markdown cells at the notebook end (a cell-replacement artifact from Phases 2-3) — planner decides whether to clean these up during Phase 4 cell insertion.

</code_context>

<deferred>
## Deferred Ideas

- **BBPIP 12.5% billing-model comparison** (FIN-06) — Phase 5 scenario. Phase 4's `clinic_pnl` must be structured so a 100%-bulk-billing + BBPIP override dict works (the function parameterises billing mix), but the base case is 70/30 mixed (locked).
- **Base/optimistic/pessimistic scenarios + tornado sensitivity** (FIN-04, FIN-05) — Phase 5. The $/sqm low/mid/high triplet (D-11) feeds this; the override-dict machinery is built here.
- **Pharmacy synergy quantification** (FIN-07) — Phase 5, order-gated AFTER the standalone verdict. Not modelled in Phase 4.
- **Go/no-go verdict** (REP-02) — Phase 5. Phase 4 produces the P&L and headlines; it does not judge viability.
- **Assumptions register as a standalone table** (REP-01) — Phase 5, but every cost/revenue line built in Phase 4 is cited with source + date, making the register a render step.
- **Monte Carlo confidence intervals** (V2-01) — future milestone. The parameterised P&L makes this cheap to add later.
- **Itemised equipment schedule** (10+ line items) — D-10 uses a single equipment & IT lump sum instead; itemisation deferred as over-granular for an investor report.

</deferred>

---

*Phase: 04-clinic-financial-model*
*Context gathered: 2026-07-06*
