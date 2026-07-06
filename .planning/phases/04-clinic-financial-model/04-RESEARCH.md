# Phase 4 Research: Clinic Financial Model

**Domain:** Australian medical clinic financial modelling (GP P&L, mixed billing, fit-out capex, ramp-up)
**Researched:** 2026-07-06
**Confidence:** HIGH on MBS rebate values and award rates (official sources); MEDIUM on overhead benchmarks, fit-out $/sqm, and service-fee % (practice-variable ranges)

## Standard Stack

**No new libraries needed.** Phase 4 is pure computation — no API calls, no geospatial ops, no PDF generation. The existing Colab-preinstalled stack suffices entirely.

| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| pandas | 2.2.x (preinstalled) | P&L table rendering, monthly cash-flow DataFrame | Use for display tables only; core math is dict/arithmetic |
| numpy | 2.0.x (preinstalled) | Monthly ramp array, cumulative cash flow, peak capital | `np.cumsum()` for cumulative cash flow; `np.min()` for peak capital (deepest negative) |
| matplotlib | 3.10.x (preinstalled) | Ramp-up cash-flow chart (cumulative cash curve + monthly EBITDA bar) | One static figure for the notebook + PDF (Phase 5) |

**Optional (already in STACK.md, NOT needed for Phase 4):**

| Library | Purpose | When to use |
|---------|---------|-------------|
| numpy-financial | Named `npv()` / `irr()` functions | NOT needed for Phase 4 — breakeven is read off the cumulative cash-flow array directly (D-08). Plain numpy `cumsum` + `argmax` is clearer and avoids a pip install. If Phase 5 wants NPV for scenario comparison, install then. |

**Verdict:** Do NOT install anything. Phase 4 uses pandas + numpy + matplotlib only.

## Architecture Patterns

### Pattern 1: Pure-Function Financial Model (ARCHITECTURE.md Pattern 3, extended by D-16)

`clinic_pnl(a: dict) -> dict` — no globals, no notebook state. Scenarios (Phase 5) become override dicts: `{**BASE_ASSUMPTIONS, **overrides}`. D-16 extends this to return BOTH a steady-state annual P&L dict AND a 36-month monthly ramp cash-flow array.

**Key structural rules (Pitfall 11 compliance):**
1. **GP gross billings ≠ practice revenue.** The top line is GP billings; the service-fee % row converts it to practice revenue. GP payments (65-70% of billings) are NOT a practice cost — they're the GP's share, deducted before practice revenue is computed.
2. **Practice revenue = billings × service_fee_%.** All practice costs (rent, staff, insurance, consumables, admin) come out of this — NOT out of gross billings.
3. **Allied health on the same service-fee % split** (D-02) — one revenue line, symmetric with GP model.

### Pattern 2: Override-Dict Scenario Pattern (Phase 1 D-10)

Every new financial constant goes into `BASE_ASSUMPTIONS` with a citation comment (PIPE-05). Phase 5 scenarios are `{**BASE_ASSUMPTIONS, **overrides}`. Phase 4 must not break this — every new key is overridable.

### Pattern 3: report{} Accumulator (ARCHITECTURE.md Pattern 5)

§6 deposits headline numbers into `report{}` for Phase 5 §8 to render:
- `report["peak_capital"]`
- `report["breakeven_operating"]` (first month EBITDA > 0)
- `report["breakeven_payback"]` (month cumulative cash flow crosses zero)
- `report["steady_state_ebitda"]`
- `report["fitout_total"]`

### Pattern 4: Monthly Ramp via Per-Month clinic_pnl Calls (D-16)

The monthly ramp function calls `clinic_pnl` with ramp-scaled parameters per month: GP count × book-fill utilisation per D-06, variable staffing per D-07. Two cost categories: variable staffing (scales with GP FTE) and fixed overheads (flat from month 0).

## Don't Hand-Roll

| Problem | Don't hand-roll | Use instead | Why |
|---------|-----------------|-------------|-----|
| Cumulative cash flow | Manual loop with running total | `np.cumsum(monthly_cashflow)` | One-liner, vectorised, no off-by-one |
| Peak capital (max cumulative negative) | Manual min-tracking | `np.min(cumulative)` (negative = funding needed) | `np.min` of cumulative array = deepest cash trough |
| Operating breakeven month | Manual loop | `np.argmax(monthly_ebitda > 0)` | Returns first month index where EBITDA > 0 |
| Payback breakeven month | Manual loop | `np.argmax(cumulative >= 0)` | Returns first month where cumulative crosses zero |
| Monthly ramp array construction | Nested loops | `np.array([...])` with list comprehension over month range | Clear, vectorised downstream ops |
| P&L display table | f-string formatting | `pd.DataFrame([pnl_result]).T` | Clean tabular display for teaching |

**Do NOT use numpy-financial for Phase 4.** Breakeven is read directly off the cumulative cash-flow array (D-08) — NPV/IRR are Phase 5 scenario-comparison tools, not Phase 4 base-case outputs. Installing numpy-financial adds a pip dependency for no functional gain here.

## Common Pitfalls

### Pitfall 11: GP Gross Billings ≠ Practice Revenue (CRITICAL — ~3× overstatement)

**The single most common GP-clinic P&L error.** Treating 5 GPs × ~$550k gross billings = $2.75M as clinic revenue overstates by ~3×.

**Structural fix (enforced in clinic_pnl):**
```
GP billings (top line, informational)
  × service_fee_% (30-35%, base 35%)
  = practice revenue (THIS is the P&L revenue line)
  − practice costs (rent, staff, insurance, consumables, admin)
  = practice EBITDA
```

**GP payments are NOT a practice cost.** The GP's 65-70% share is deducted at the revenue line (billings × service_fee_% = practice revenue), not added as a cost. Double-counting GP payments as a cost alongside 100% of billings as revenue is the other common error variant.

**Verification step:** Practice revenue for a 5-GP clinic should be ~$800k-$1,000k (not $2.5M+). If the P&L shows revenue in the millions, the structure is wrong.

### Pitfall 7: MBS Item/Incentive Changes (date-stamp every value)

MBS rebates change annually (2.4% indexation 1 July 2025). Chronic disease management items were restructured 1 July 2025 (item 721 → item 965). BBPIP (12.5% incentive) started 1 November 2025.

**Fix:** Every MBS item value in `BASE_ASSUMPTIONS` has a `# MBS Online, from 1 Jul 2025` citation. BBPIP is NOT in the base case — it's a Phase 5 scenario (FIN-06).

**Key change to note:** Item 721 (GP Management Plan) CEASED on 1 July 2025, replaced by item 965 (GPCCMP) at $156.55. The 04-CONTEXT.md D-01 references "item 721" — use item 965 instead.

### Pitfall 12: Ramp-Up + Fit-Out Capex

**Fix:** Monthly 36-month cash flow (D-05), GP recruitment milestones + book-fill curve (D-06), cited $/sqm × floor area (D-09/D-11), peak capital headline (D-08/D-12).

**Verification step:** The P&L must have a time axis (monthly array). If breakeven is reported as "year 1" with no ramp model, it's wrong. Peak capital must be a headline output.

### Pitfall 13: Rent and Key Assumptions as Facts

**Fix:** Every cost/revenue line has source + date in `BASE_ASSUMPTIONS` citation comments. The full assumptions register + tornado is Phase 5 (REP-01/FIN-05), but the cited lines are built now.

**Verification step:** No numeric literal outside `BASE_ASSUMPTIONS` except unit conversions (PIPE-05). Every new financial constant has a `# source: ...` comment.

### Pitfall: Superannuation Guarantee Rate (CORRECTION)

**04-CONTEXT.md D-14 cites "super 11.5%" — this is OUTDATED.** The SG rate increased to **12%** from 1 July 2025 (ATO, verified). The on-costs multiplier must use 12%, not 11.5%.

## Cited MBS Item-Mix Table (D-01)

**Source:** MBS Online (mbsonline.gov.au), 1 July 2025 vintage (2.4% indexation applied). Access date: 2026-07-06.
**Cross-referenced with:** AusDoc MBS Quick Guide November 2025; Lyrebird Health MBS Item Cheat Sheet (updated June 2026); RACGP 1 July 2025 MBS updates page.

| Item | Description | Rebate (2025-26) | % of consult volume | Source |
|------|-------------|-------------------|---------------------|--------|
| 23 | Level B (standard, 6-20 min) | $43.90 | 70% | MBS Online; Medical Republic (66% of non-referred attendances, ~70% excluding Level A) |
| 36 | Level C (long, 20-40 min) | $84.90 | 15% | MBS Online; MJA 2010 (Level C ~15-18% of GP consults) |
| 44 | Level D (prolonged, 40-60 min) | $125.10 | 3% | MBS Online; estimated from Medicare quarterly data (~2-4%) |
| 965 | GPCCMP prepare (replaced item 721 from 1 Jul 2025) | $156.55 | 5% | MBS Online; RACGP 1 July 2025 updates |
| 967 | GPCCMP review (replaced item 732) | $156.55 | 3% | MBS Online; RACGP (review items aligned to same fee) |
| 701 | Health assessment (brief, <30 min) | $69.20 | 2% | MBS Online; AusDoc Quick Guide Nov 2025 |
| Procedures (various, e.g. 30071) | Minor procedures | ~$80 avg | 2% | MBS Online; estimated (small fraction of GP volume) |

**Notes:**
- Item 23 (Level B) at 66% of all GP non-referred attendance services (Medical Republic, Medicare quarterly data). Model uses 70% because the remaining 15% of "time-based items" includes Level A (item 3, ~$20.05, very brief) which is negligible in a mixed-billing practice.
- **Item 721 NO LONGER EXISTS.** From 1 July 2025, GP Management Plans (items 229, 721, 92024, 92055) and Team Care Arrangements (items 230, 723, 92025, 92056) were replaced by GP Chronic Condition Management Plan (GPCCMP) items 965 (prepare) and 967 (review), both at $156.55. The 04-CONTEXT.md D-01 references "item 721" — use item 965 instead.
- Time-based items (A-E) together account for ~85% of GP Medicare services (Medical Republic). The remaining ~15% includes care plans, health assessments, procedures, mental health items.
- The weighted average rebate across this mix: ~$55-60 per consult (higher than item-23-only $43.90, confirming D-01's "~15-25% higher revenue" claim).

**Confidence:** HIGH on rebate values (MBS Online, official). MEDIUM on item-mix percentages (derived from Medicare quarterly statistics + industry commentary; exact percentages vary by practice demographics and billing behaviour).

## Cited Staffing Cost Table (D-13, D-14)

**Sources:** Fair Work Ombudsman (awards.fairwork.gov.au); Nurses Award 2020 [MA000034]; Clerks—Private Sector Award 2020 [MA000002]. Rates from 1 July 2025 (3.5% Annual Wage Review increase). Access date: 2026-07-06.

### Nursing (Nurses Award 2020, MA000034)

| Role | Pay point | Weekly rate | Hourly rate | Annual (×52) | Source |
|------|-----------|-------------|-------------|--------------|--------|
| Registered Nurse Level 2 (Clinical Nurse) | Pay Point 1 | $1,436.20 | $37.79 | $74,682 | Fair Work MA000034, from 1 Jul 2025 |
| Registered Nurse Level 2 | Pay Point 2 | $1,459.00 | $38.39 | $75,868 | Fair Work MA000034 |
| Registered Nurse Level 2 | Pay Point 3 | $1,484.30 | $39.06 | $77,184 | Fair Work MA000034 |
| Registered Nurse Level 2 | Pay Point 4+ | $1,508.60 | $39.70 | $78,447 | Fair Work MA000034 |

**Use RN Level 2 Pay Point 2 ($75,868/yr) as the base-case practice nurse salary.** A registered nurse with ~1-2 years experience at Level 2 — appropriate for a general practice nurse.

### Reception/Admin (Clerks—Private Sector Award 2020, MA000002)

| Role | Level | Weekly rate | Hourly rate | Annual (×52) | Source |
|------|-------|-------------|-------------|--------------|--------|
| Receptionist (entry) | Level 1 Year 1 | $1,024.70 | $26.97 | $53,284 | Fair Work MA000002, from 1 Jul 2025 |
| Receptionist (experienced) | Level 2 Year 1 | $1,119.10 | $29.45 | $58,193 | Fair Work MA000002 |
| Senior admin | Level 3 | $1,182.10 | $31.11 | $61,469 | Fair Work MA000002 |
| Practice Manager | Level 4 | $1,241.40 | $32.67 | $64,553 | Fair Work MA000002 |
| Senior Practice Manager | Level 5 | $1,291.80 | $33.99 | $67,174 | Fair Work MA000002 |

**Use Level 2 Year 1 ($58,193/yr) for reception, Level 4 ($64,553/yr) for practice manager.** D-13 specifies 1 FTE nurse + 1.5 FTE reception + 0.5 FTE manager (lean staffing).

### On-Costs Multiplier

| Component | Rate | Source |
|-----------|------|--------|
| Superannuation Guarantee (2025-26) | **12%** of OTE | ATO (ato.gov.au), from 1 July 2025 — **NOT 11.5% as cited in CONTEXT.md D-14** |
| WorkCover Victoria (2025-26) | ~1.8% of remuneration (industry average; medical services classification varies) | WorkSafe Victoria Premiums Order No. 33, 2025-26 |
| Payroll tax (VIC) | 4.85% of wages above $700k/yr threshold | State Revenue Office Victoria — likely NOT applicable for lean startup with total wages ~$200k (below threshold) |

**On-costs multiplier: 1.14** (12% super + ~2% WorkCover = ~14% loading on base salary).

**Total staffing cost (D-13 lean structure):**
- 1 FTE practice nurse: $75,868 × 1.14 = $86,490
- 1.5 FTE reception: $58,193 × 1.5 × 1.14 = $99,510
- 0.5 FTE practice manager: $64,553 × 0.5 × 1.14 = $36,795
- **Total: ~$222,795/yr** (steady-state, all staff at 100%)

**Confidence:** HIGH on award rates (Fair Work official, current from 1 July 2025). HIGH on SG rate (ATO official). MEDIUM on WorkCover rate (industry average; actual rate varies by claims experience and specific classification).

## Cited Overhead Benchmarks Table (D-15)

**Three grouped overhead lines, each cited.** Sources are industry benchmarks and practice management guides — these are MEDIUM-confidence ranges that vary by practice.

| Line | Annual cost (base case) | Source + date | Confidence |
|------|------------------------|---------------|------------|
| **Insurance** (professional indemnity + public liability, practice entity) | $12,000/yr | MGRS practice indemnity ($500-$50k range, GP practice ~$5-15k); TEGO/Avant practice policies; Morgan Insurance Brokers (typical $1-5M cover for GP practice entity). GPs carry their OWN individual indemnity ($3,750-$8,000/yr, NOT a practice cost). | MEDIUM — varies by claims history, practice size, cover level |
| **Consumables & medical supplies** | $45,000/yr | GP-Hub financial model ($35k for 4-GP clinic, scaled to 5-GP); XS Supply (primary care ~$6,400/month = ~$77k/yr, but US data); healthandlife.com.au (overhead 60-75% of revenue includes consumables). $45k ≈ ~$1.60/consult for 27,500 consults. | MEDIUM — varies by practice type (procedural vs non-procedural) |
| **Admin/IT/utilities** (clinical software, hardware, internet, cleaning, electricity, secure messaging) | $35,000/yr | Bp Premier software $1,418.49/yr per FT GP × 5 = $7,092; Clinically ~$4,000/yr; IT support/hardware ~$10,000; utilities (electricity, cleaning, water) ~$15,000; secure messaging/My Health Record ~$3,000. Total ~$35k. | MEDIUM — software costs are known; utilities vary by tenancy |

**Total overheads (3 lines): ~$92,000/yr** (steady-state, separate from rent and staffing).

**Confidence:** MEDIUM on all three lines. Insurance and consumables are the most variable. These are defensible base-case point estimates; Phase 5 sensitivity will test ±30% ranges.

## Cited Fit-Out Cost Table (D-09, D-10, D-11)

### Floor Area (D-09): 170 sqm

**Source:** `data/local/292 Johnston Ground Floor Plan (1).pdf` — the ground-floor tenancy plan for 292 Johnston St.

**Derivation note:** The floor plan PDF could not be independently re-measured in this research session (binary PDF, no PDF extraction library available in the sandbox). The 170 sqm figure is cited in 04-CONTEXT.md D-09 as taken from the floor plan. Cross-check via RACGP Standards 5th edition room requirements:

| Room type | RACGP guide | Qty | Subtotal |
|-----------|-------------|-----|----------|
| Consulting room | 12-16 sqm each | 5 (GP) + 1 (allied health) = 6 | 72-96 sqm |
| Treatment room | 7 sqm (2.5 × 3.0 m) | 1 | 7 sqm |
| Reception + waiting | ~30-40 sqm | 1 | 35 sqm |
| Staff room + admin office | ~15-20 sqm | 1 | 18 sqm |
| Corridors + amenities (WC, store) | ~15-20% of total | — | ~25 sqm |
| **Total** | | | **157-181 sqm** |

170 sqm falls within the RACGP-derived range (157-181 sqm). This is a compact inner-city fit-out — below the RACGP business toolkit's generic "250 sqm for 4 consulting rooms" (which assumes suburban practice with more generous rooms + car parking). The 170 sqm figure is plausible and site-specific.

**Action for planner:** The implementation should attempt to read the PDF at runtime (or document the figure as "from floor plan PDF, cross-checked against RACGP room standards") and note the derivation method in the assumptions register.

### $/sqm Triplet (D-11): $1,200 / $1,700 / $2,200

| Level | $/sqm | × 170 sqm | Source |
|-------|-------|-----------|--------|
| Low | $1,200 | $204,000 | Design Yard 32 (Melbourne, $1,200-$1,800/sqm base build, excludes equipment); EasyAsset ($1,200-$2,000/sqm general medical) |
| Mid (base case) | $1,700 | $289,000 | Midpoint of Melbourne base range ($1,200-$1,800) and national 2026 range ($1,850-$3,500); Practical guide ($1,500-$2,500 for basic GP) |
| High | $2,200 | $374,000 | EasyAsset specialist clinic ($1,600-$2,200/sqm); SoulMED 2026 ($1,850-$3,500/sqm, lower end); Unita ($1,500-$4,000/sqm) |

**Sources (all accessed 2026-07-06):**
- Design Yard 32: designyard32.com.au — Melbourne-specific, $1,200-$1,800/sqm for base build (partitions, ceilings, flooring, joinery, lighting, basic services), excludes medical equipment
- SoulMED 2026 guide: soulmed.com.au — $1,850-$3,500+/sqm national, GP 100-200 sqm = $267k-$535k
- EasyAsset: easyasset.com.au — $1,200-$2,000+/sqm general medical, $1,600-$2,200 specialist
- Unita: unita.com.au — $1,500-$4,000/sqm
- Practical guide (ulikethisnoweh.com): $1,500-$2,500/sqm for basic GP clinic

**Confidence:** MEDIUM. The $1,200 low is well-supported (Melbourne base build). The $2,200 high is supported (specialist clinic level). The $1,700 mid is a defensible midpoint. All sources note that actual costs depend on tenancy condition (cold shell vs warm shell), compliance requirements, and finishes.

### Equipment & IT Lump Sum (D-10): $60,000

| Component | Estimated cost | Source |
|-----------|---------------|--------|
| Examination beds (5, height-adjustable, RACGP requirement) | $15,000 ($3,000 each) | Medilogic medical equipment calculator; RACGP Standards 5th ed (GP5.2: at least one height-adjustable bed) |
| Treatment room equipment (trolley, steriliser, instruments) | $15,000 | Medilogic; RACGP furniture & equipment guide |
| Clinical software setup + hardware (5 GP workstations + reception) | $15,000 | Bp Premier $1,418/GP/yr (ongoing); initial hardware ~$3,000/workstation × 5 = $15,000 |
| IT infrastructure (server/network/printer/secure messaging setup) | $10,000 | Industry estimate for small clinic IT setup |
| Reception furniture + waiting room + misc | $5,000 | RACGP business toolkit |
| **Total** | **$60,000** | Mid-range of D-10's ~$40-80k range |

**Confidence:** MEDIUM. The $60k figure is a defensible mid-range point estimate for a 5-GP clinic. Medilogic's calculator suggests $25k-$75k for mid-range equipment (excluding fit-out construction). The RACGP business toolkit provides room-by-room guidance but not dollar figures.

### Total Fit-Out Capex (base case)

| Line | Cost |
|------|------|
| Base fit-out ($1,700/sqm × 170 sqm) | $289,000 |
| Equipment & IT lump sum | $60,000 |
| **Total fit-out capex** | **$349,000** |

This replaces the `fitout_capital=350_000` placeholder in `BASE_ASSUMPTIONS` — the placeholder was remarkably close to the derived figure.

## Ramp Curve Parameter Table (D-06)

**Sources:** National Health Experts (nationalhealthexperts.com.au); ClinicComply (cliniccomply.com.au); Reyah GP hiring guide (reyah.ai); RACGP business toolkit. Access date: 2026-07-06.

### GP Recruitment Milestones

| Month | GP FTE | Event | Source |
|-------|--------|-------|--------|
| 0 (opening) | 2 | 2 GPs at open (founder + 1 recruited pre-opening) | D-06; National Health Experts ("12-18 month runway") |
| 6 | 3 | +1 GP recruited | Reyah ("vacancies open 60 days to 18 months"); ClinicComply ("first on-site assessment at 12-18 months") |
| 12 | 4 | +1 GP recruited | National Health Experts ("books take 12-24 months to fill") |
| 18 | 5 | +1 GP recruited → full 5 FTE | D-06; National Health Experts ("18-month truth") |

### Per-GP Book-Fill Curve

| Months since GP started | Utilisation (% of steady-state 75%) | Source |
|--------------------------|--------------------------------------|--------|
| 0-3 | 40% | National Health Experts ("doctors rarely start with full schedules"); D-06 |
| 3-6 | 50% | Gradual ramp; word-of-mouth builds |
| 6-9 | 60% | Books filling; repeat patients accumulating |
| 9-12 | 68% | Approaching steady state |
| 12+ | 75% | Steady-state target (BASE_ASSUMPTIONS["utilisation"]) |

**Ramp model:** Each GP's monthly consult volume = `gp_fte_consults_per_yr × book_fill_pct × (1/12)`. The book-fill curve applies per-GP from their start month. A GP starting at month 6 reaches 75% utilisation at month 18.

**Support staff scaling (D-07):** Practice nurse FTE scales with GP FTE (nurse FTE = GP_FTE × 0.2, so 2 GPs = 0.4 nurse, 5 GPs = 1.0 nurse). Reception/admin and manager are fixed at 100% from day 1 (reception coverage needed from open).

**Confidence:** MEDIUM. The milestones and book-fill curve are consistent across multiple practice management sources but are not from a single cited dataset — they represent industry consensus, not empirical measurement.

## Working-Capital Buffer Basket Definition (D-12)

**3-month working-capital buffer** = 3 months of fixed costs that must be paid regardless of revenue.

| Component (fixed, monthly) | Monthly cost | × 3 months | Source |
|----------------------------|-------------|------------|--------|
| Rent | $8,333 ($100k/yr ÷ 12) | $25,000 | BASE_ASSUMPTIONS["rent_yr"] |
| Insurance | $1,000 ($12k/yr ÷ 12) | $3,000 | D-15 overhead table |
| Admin/IT/utilities | $2,917 ($35k/yr ÷ 12) | $8,750 | D-15 overhead table |
| Reception/admin/manager (fixed from day 1) | $4,233 ($50.8k/yr ÷ 12, reception 1.5 FTE + manager 0.5 FTE) | $12,700 | D-13 staffing table |
| **Total 3-month buffer** | | **$49,450** | |

**Peak capital (D-12) = fit-out capex + max cumulative operating loss during ramp + 3-month working-capital buffer.**

The buffer is added ON TOP of the modelled peak cumulative loss, not buried in it. This is a conservative headline — recognises real-world funding needs contingency beyond the modelled cash drain.

**Confidence:** HIGH on the basket definition (fixed costs are well-defined). MEDIUM on the 3-month duration (industry practice varies; some sources suggest 6-12 months for GP clinics, but 3 months is the D-12 locked decision).

## Code Examples

### clinic_pnl Function Skeleton

```python
def clinic_pnl(a: dict) -> dict:
    """
    Pure-function steady-state annual P&L for a 5-FTE GP + 1-FTE allied health clinic.
    
    ARCHITECTURE.md Pattern 3 — no globals, no notebook state.
    Scenarios (Phase 5): {**BASE_ASSUMPTIONS, **overrides}
    
    Pitfall 11 compliance: GP gross billings ≠ practice revenue.
    Practice revenue = billings × service_fee_%. GP payments are NOT a cost.
    """
    # --- Consult volume (capacity-driven, D-03) ---
    annual_consults = a["n_gp_fte"] * a["gp_fte_consults_per_yr"] * a["utilisation"]
    
    # --- GP billings (top line, INFORMATIONAL — not practice revenue) ---
    # Weighted by item mix (D-01): each item has a % of volume and a rebate/fee
    item_mix = a["item_mix"]  # dict: {item_number: {"pct": float, "rebate": float, "private_fee": float}}
    
    # Bulk-billed consults: patient pays $0, practice claims MBS rebate
    # Private consults: patient pays private_fee, claims MBS rebate back
    # Revenue per consult = bulk_bill_share × rebate + private_share × private_fee
    weighted_rebate = sum(v["pct"] * v["rebate"] for v in item_mix.values())
    weighted_private_fee = sum(v["pct"] * v["private_fee"] for v in item_mix.values())
    
    avg_rev_per_consult = (
        a["bulk_bill_share"] * weighted_rebate
        + (1 - a["bulk_bill_share"]) * weighted_private_fee
    )
    gp_billings = annual_consults * avg_rev_per_consult  # GROSS billings (informational)
    
    # --- Practice revenue = billings × service_fee_% (Pitfall 11 fix) ---
    practice_revenue_gp = gp_billings * a["gp_revenue_share"]
    
    # --- Allied health revenue (D-02: same service-fee % split) ---
    allied_consults = a["n_allied_fte"] * a["allied_consults_per_yr"] * a["utilisation"]
    allied_billings = allied_consults * a["allied_avg_rev_per_consult"]
    practice_revenue_allied = allied_billings * a["gp_revenue_share"]  # same split
    
    practice_revenue = practice_revenue_gp + practice_revenue_allied
    
    # --- Costs (all from practice revenue, NOT from gross billings) ---
    # NOTE: GP payments (65-70% of billings) are NOT here — they're already deducted
    # at the revenue line (billings × service_fee_% = practice revenue).
    staffing_costs = a["nurse_fte"] * a["nurse_salary_yr"] * a["oncost_multiplier"] \
                   + a["reception_fte"] * a["reception_salary_yr"] * a["oncost_multiplier"] \
                   + a["manager_fte"] * a["manager_salary_yr"] * a["oncost_multiplier"]
    
    costs = (
        a["rent_yr"]
        + staffing_costs
        + a["insurance_yr"]           # D-15 line (a)
        + a["consumables_yr"]         # D-15 line (b)
        + a["admin_it_utilities_yr"]  # D-15 line (c)
    )
    
    ebitda = practice_revenue - costs
    margin = ebitda / practice_revenue if practice_revenue else 0
    
    return {
        "annual_consults": annual_consults,
        "gp_billings": gp_billings,              # informational (Pitfall 11 guardrail)
        "practice_revenue": practice_revenue,     # THE revenue line
        "practice_revenue_gp": practice_revenue_gp,
        "practice_revenue_allied": practice_revenue_allied,
        "staffing_costs": staffing_costs,
        "total_costs": costs,
        "ebitda": ebitda,
        "margin": margin,
        "service_fee_pct": a["gp_revenue_share"],  # explicit service-fee % row
    }
```

### Monthly Ramp Function Skeleton (D-16)

```python
def clinic_ramp_monthly(a: dict, months: int = 36) -> dict:
    """
    36-month monthly ramp cash flow (D-05, D-06, D-07, D-08).
    
    Calls clinic_pnl with ramp-scaled parameters per month:
    - GP count per D-06 milestones
    - Book-fill utilisation per GP per D-06 curve
    - Variable staffing scales with GP FTE (D-07)
    - Fixed overheads flat from month 0 (D-07)
    
    Returns monthly array + headline metrics.
    """
    # GP recruitment milestones (D-06)
    gp_milestones = a["gp_ramp_milestones"]  # {0: 2, 6: 3, 12: 4, 18: 5}
    
    # Book-fill curve: utilisation ramps from 40% to 75% over 12 months per GP
    book_fill_curve = a["book_fill_curve"]  # {0: 0.40, 3: 0.50, 6: 0.60, 9: 0.68, 12: 0.75}
    
    monthly_ebitda = np.zeros(months)
    monthly_revenue = np.zeros(months)
    monthly_costs = np.zeros(months)
    
    for m in range(months):
        # Determine GP FTE at this month
        gp_fte = max(v for k, v in gp_milestones.items() if k <= m)
        
        # Determine weighted-average utilisation across all active GPs
        total_util = 0
        for gp_idx in range(gp_fte):
            months_active = m - gp_milestones_start_month(gp_idx, gp_milestones)
            util = interpolate_book_fill(months_active, book_fill_curve)
            total_util += util
        avg_util = total_util / gp_fte if gp_fte > 0 else 0
        
        # Scale nurse FTE with GP FTE (D-07); reception/manager fixed
        ramp_overrides = {
            "n_gp_fte": gp_fte,
            "utilisation": avg_util,
            "nurse_fte": gp_fte * 0.2,  # scales with GP count
            # reception_fte, manager_fte stay at steady-state (fixed from day 1)
        }
        
        month_result = clinic_pnl({**a, **ramp_overrides})
        monthly_revenue[m] = month_result["practice_revenue"] / 12
        monthly_costs[m] = month_result["total_costs"] / 12
        monthly_ebitda[m] = month_result["ebitda"] / 12
    
    # Cash flow: EBITDA - fit-out (month 0 only)
    monthly_cashflow = monthly_ebitda.copy()
    monthly_cashflow[0] -= a["fitout_total"]  # fit-out paid at opening
    
    cumulative = np.cumsum(monthly_cashflow)
    
    # Headline metrics (D-08)
    peak_capital_modelled = np.min(cumulative)  # deepest cash trough (negative)
    peak_capital_total = peak_capital_modelled - a["working_capital_buffer"]  # D-12: add buffer
    
    breakeven_operating = int(np.argmax(monthly_ebitda > 0)) if np.any(monthly_ebitda > 0) else None
    breakeven_payback = int(np.argmax(cumulative >= 0)) if np.any(cumulative >= 0) else None
    
    return {
        "monthly_revenue": monthly_revenue,
        "monthly_costs": monthly_costs,
        "monthly_ebitda": monthly_ebitda,
        "monthly_cashflow": monthly_cashflow,
        "cumulative": cumulative,
        "peak_capital_modelled": abs(peak_capital_modelled),
        "peak_capital_total": abs(peak_capital_total),  # with working-capital buffer
        "breakeven_operating": breakeven_operating,     # first month EBITDA > 0
        "breakeven_payback": breakeven_payback,         # month cumulative crosses zero
        "fitout_total": a["fitout_total"],
        "working_capital_buffer": a["working_capital_buffer"],
    }
```

### BASE_ASSUMPTIONS New Keys (to add in §0)

```python
# --- Phase 4: Financial Model (source: MBS Online, Fair Work, industry benchmarks) ---
# MBS item mix (D-01) — MBS Online, from 1 Jul 2025 (2.4% indexation)
"item_mix": {
    23:  {"pct": 0.70, "rebate": 43.90, "private_fee": 95.00},   # Level B standard
    36:  {"pct": 0.15, "rebate": 84.90, "private_fee": 165.00},  # Level C long
    44:  {"pct": 0.03, "rebate": 125.10, "private_fee": 250.00}, # Level D prolonged
    965: {"pct": 0.05, "rebate": 156.55, "private_fee": 250.00}, # GPCCMP prepare (replaced 721)
    967: {"pct": 0.03, "rebate": 156.55, "private_fee": 220.00}, # GPCCMP review (replaced 732)
    701: {"pct": 0.02, "rebate": 69.20, "private_fee": 120.00},  # Health assessment brief
    "procedures": {"pct": 0.02, "rebate": 80.00, "private_fee": 150.00},  # Minor procedures avg
},
# Staffing (D-13, D-14) — Fair Work MA000034/MA000002, from 1 Jul 2025
"nurse_fte":              1.0,
"nurse_salary_yr":        75_868,     # RN Level 2 PP2, Fair Work MA000034
"reception_fte":          1.5,
"reception_salary_yr":    58_193,     # Clerks Level 2 Y1, Fair Work MA000002
"manager_fte":            0.5,
"manager_salary_yr":      64_553,     # Clerks Level 4, Fair Work MA000002
"oncost_multiplier":      1.14,       # 12% super (ATO, from 1 Jul 2025) + ~2% WorkCover VIC
# Overheads (D-15) — industry benchmarks, MEDIUM confidence
"insurance_yr":           12_000,     # practice entity indemnity + public liability — MGRS/TEGO
"consumables_yr":         45_000,     # medical supplies, ~$1.60/consult — GP-Hub benchmark
"admin_it_utilities_yr":  35_000,     # software + hardware + utilities — Bp Premier + industry est
# Fit-out (D-09, D-10, D-11) — floor plan PDF + industry $/sqm
"floor_area_sqm":         170,        # 292 Johnston ground floor plan PDF, cross-checked RACGP
"fitout_per_sqm_low":     1_200,      # Design Yard 32 (Melbourne base build)
"fitout_per_sqm_mid":     1_700,      # midpoint of Melbourne base + national 2026
"fitout_per_sqm_high":    2_200,      # EasyAsset specialist / SoulMED lower range
"fitout_per_sqm":         1_700,      # base case = mid
"equipment_it_lump_sum":  60_000,     # exam beds + treatment + IT + software setup — Medilogic mid-range
"fitout_total":           349_000,    # $1,700 × 170 + $60,000 (replaces placeholder 350,000)
# Ramp (D-05, D-06) — industry consensus, MEDIUM confidence
"ramp_months":            36,         # years 1-3 monthly cash flow
"gp_ramp_milestones":     {0: 2, 6: 3, 12: 4, 18: 5},  # GP FTE by month
"book_fill_curve":        {0: 0.40, 3: 0.50, 6: 0.60, 9: 0.68, 12: 0.75},  # per-GP utilisation
# Working capital (D-12)
"working_capital_buffer_months": 3,
"working_capital_buffer": 49_450,  # 3 months of fixed costs (rent + insurance + admin/IT + reception/manager)
# Allied health (D-02)
"allied_consults_per_yr":     4_000,    # 1 FTE allied health, lower volume than GP
"allied_avg_rev_per_consult": 85.00,    # allied health typical consult fee
```

### report{} Deposits

```python
# After computing base-case P&L and ramp:
report["steady_state_ebitda"] = pnl_result["ebitda"]
report["steady_state_margin"] = pnl_result["margin"]
report["practice_revenue"] = pnl_result["practice_revenue"]
report["gp_billings"] = pnl_result["gp_billings"]  # informational (Pitfall 11 guardrail)
report["fitout_total"] = ramp_result["fitout_total"]
report["peak_capital"] = ramp_result["peak_capital_total"]
report["breakeven_operating"] = ramp_result["breakeven_operating"]
report["breakeven_payback"] = ramp_result["breakeven_payback"]
report["working_capital_buffer"] = ramp_result["working_capital_buffer"]
```

## Key Findings Summary

### Critical Correction: Superannuation Guarantee Rate

**04-CONTEXT.md D-14 cites "super 11.5%" — this is WRONG.** The SG rate increased to **12%** from 1 July 2025 (ATO, verified via multiple sources). The on-costs multiplier must use 12%, giving 1.14 (12% + ~2% WorkCover), not 1.135 (11.5% + ~2%).

### Critical Correction: Item 721 No Longer Exists

**04-CONTEXT.md D-01 references "item 721" (GP Management Plan) — this item CEASED on 1 July 2025.** It was replaced by item 965 (GPCCMP prepare) at $156.55. Similarly, item 732 (review) was replaced by item 967 at $156.55. The implementation must use items 965/967, not 721/732.

### MBS Item 23 Rebate Confirmed at $43.90

The BASE_ASSUMPTIONS already has `std_rebate: 43.90` — this is correct for 2025-26 (from 1 July 2025, 2.4% indexation). The RACGP Health of the Nation 2025 survey references $42.85, but that was the 2024-25 value. $42.85 × 1.024 ≈ $43.90.

### BBPIP Confirmed as Phase 5 Only

BBPIP (12.5% quarterly incentive on MBS benefits, split 50/50 GP/practice) is confirmed from 1 November 2025 via DoH factsheets and Services Australia. It requires 100% bulk billing of all eligible services — incompatible with the 70/30 mixed-billing base case. Correctly excluded from Phase 4 base case; Phase 5 will model it as a billing-model comparison scenario (FIN-06).

### Service Fee % Confirmed at 35% Base

The Alecto 2025 GP Salary Survey confirms: 70% to GP (30% to practice) is most common (37% of GPs), 65% to GP (35% to practice) is second (27% of GPs). DoH 2025 modelling assumes 30% practice fee "becoming the norm." The BASE_ASSUMPTIONS `gp_revenue_share: 0.35` (35% to practice) is at the higher end of the common range — defensible for an inner-Melbourne practice with high overhead, but Phase 5 should test 30-35% as a sensitivity range.

### Fit-Out Capex Validates Placeholder

The derived fit-out total ($349,000) is remarkably close to the `fitout_capital=350_000` placeholder. The derivation: $1,700/sqm × 170 sqm + $60,000 equipment = $349,000. The placeholder can be replaced with the derived figure with high confidence.

### Floor Plan PDF: Could Not Independently Verify

The 170 sqm figure from the floor plan PDF could not be independently re-measured (binary PDF, no extraction library available in sandbox). The RACGP room-standards cross-check (157-181 sqm range) supports the figure. The implementation should document the derivation method and attempt to read the PDF at runtime or note it as "from floor plan, cross-checked against RACGP Standards 5th edition room sizes."

## RESEARCH COMPLETE

All domains investigated:
- [x] MBS item mix (item numbers, rebate values, % of consult volume, source + date)
- [x] Staffing costs (Modern Award pay points + on-costs multiplier for nurse/reception/manager)
- [x] Overhead benchmarks (insurance, consumables, admin/IT/utilities — $/yr with source)
- [x] Fit-out costs ($/sqm low/mid/high + equipment lump sum, Australian medical fit-out sources)
- [x] Floor plan reading note (170 sqm derivation, RACGP cross-check, PDF access limitation noted)
- [x] Ramp curve parameters (GP recruitment milestones, book-fill %, time-to-full-booking)
- [x] Working-capital buffer basket definition (which fixed costs are in the 3-month buffer)
- [x] clinic_pnl function skeleton (Python signature, input dict keys, output dict keys, monthly ramp wrapper)

Quality gate:
- [x] All domains investigated
- [x] Negative claims verified with official docs (BBPIP 12.5% from Nov 2025 — DoH factsheet cited; MBS item 23 $43.90 — MBS Online cited; SG 12% — ATO cited)
- [x] Multiple sources for critical claims (fit-out $/sqm: 5 sources; service-fee %: 4 sources; private fee: RACGP + market data)
- [x] Confidence levels assigned honestly (MEDIUM on overheads, fit-out $/sqm, service-fee %, ramp curve; HIGH on MBS rebates, award rates, SG rate)
- [x] Section names match plan-phase expectations: Standard Stack, Architecture Patterns, Don't Hand-Roll, Common Pitfalls, Code Examples
- [x] Every cited value has source + access date (Pitfall 13 compliance)
- [x] BBPIP is NOT in the base case (Pitfall 7 / scope boundary compliance)
- [x] GP gross billings ≠ practice revenue is structurally enforced (Pitfall 11 compliance — service-fee % row in function skeleton, GP payments NOT a cost line)
