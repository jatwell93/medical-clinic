# Roadmap — Clinic Feasibility Study

**Project:** JSMC — Johnston St Medical Clinic Feasibility Study
**Goal:** A reusable, investor-grade medical-clinic feasibility tool (Colab notebook + executive PDF) that accepts any Victorian street address via a site-input form and produces a standalone-profitability verdict. Abbotsford ships as the default config so v2.0 out-of-the-box reproduces v1.0 (minus pharmacy synergy).
**Granularity:** Coarse (6 phases)
**Created:** 2026-07-05
**Current Milestone:** v2.0 Multi-Site Feasibility Tool

## Milestones

- ✅ **v1.0 Feasibility Study** — Phases 1-5 (shipped 2026-07-06) — [Archive](./milestones/v1.0-ROADMAP.md)
- 🚧 **v2.0 Multi-Site Feasibility Tool** — Phases 6-11 (in progress)

## Phases

<details>
<summary>✅ v1.0 Feasibility Study (Phases 1-5) — SHIPPED 2026-07-06</summary>

- [x] Phase 1: Scaffolding & Data Pipeline (2/2 plans) — completed 2026-07-05
- [x] Phase 2: Catchment & Demographics (3/3 plans) — completed 2026-07-05
- [x] Phase 3: Demand & Competitors (3/3 plans) — completed 2026-07-06
- [x] Phase 4: Clinic Financial Model (2/2 plans) — completed 2026-07-06
- [x] Phase 5: Scenarios & Executive Report (2/2 plans) — completed 2026-07-06

</details>

### v2.0 Multi-Site Feasibility Tool (Phases 6-11)

#### Phase 6: Site Config Restructure

**Goal:** Replace v1.0's hardcoded Abbotsford constants with a `#@param` site-input form (`SITE_CONFIG` dict) separated from model constants (`BASE_ASSUMPTIONS`), adopt EPSG:7899 for state-wide VIC coverage, and add peer postcode validation + geocode quality checks.
**Depends on:** — (first v2.0 phase)
**Requirements:** SITE-01, SITE-02, SITE-03, SITE-04, SITE-05, SITE-06, SITE-07, GEO-05

**Success Criteria:**
1. User can fill in a `#@param` form (street address, postcode, state=VIC dropdown, FTE slider 1–10, peer postcodes, SA3 override) and Run All — the notebook reads form values, not hardcoded constants
2. Running with default form values reproduces v1.0 Abbotsford config (292-296 Johnston St, 3067, 5 FTE, 9 peer postcodes) with zero manual edits
3. Entering an invalid peer postcode (non-4-digit, non-VIC, duplicate, or self-referential) produces a printed warning naming the dropped entry; only valid peers proceed
4. Geocoding a `partial_match` or non-`ROOFTOP` result prints a quality warning; a geocoded point outside the VIC bounding box is rejected with a clear message
5. All metre-based buffer/area math uses EPSG:7899 (GDA2020 / Vicgrid) — the 5 km buffer area is correct for sites across all of VIC (including western VIC where EPSG:7855 would distort)

---

#### Phase 7: Geocode Parameterisation + POA/SA3 Derivation

**Goal:** Auto-derive POA and SA3 codes from the geocoded point via point-in-polygon on ASGS boundaries, implement the two-layered VIC guard, handle SA3 override and edge cases, and derive the ERP SA2 code — replacing all hardcoded geography constants.
**Depends on:** Phase 6
**Requirements:** GEO-01, GEO-02, GEO-03, GEO-04, GEO-06, GEO-07

**Key Decision — SA1 vs SA3 Shapefile (GEO-02):** Use the **existing SA1 shapefile** (already on hand, ~100 MB, loaded by v1.0 cell 16) which carries `SA3_CODE21` / `SA3_NAME21` as attribute columns (verified live). A single point-in-polygon on SA1s yields both the SA1 and SA3 code with no new download. This enables geometry reuse between §1.3 (derivation) and §2 (catchment apportionment) — the SA1 boundaries are loaded once and shared. The alternative (dedicated SA3 shapefile, ~5 MB download) was rejected because it adds a new asset and prevents geometry reuse.

**Success Criteria:**
1. After geocoding, the tool prints the auto-derived POA code and SA3 code (e.g., "POA: 3067, SA3: 20607 Yarra" for default Abbotsford)
2. Entering a non-VIC address (e.g., a Sydney street address) raises a `RuntimeError` with a clear VIC-only scope message (two-layered guard: form dropdown locked to VIC + post-geocode state check)
3. User can override the auto-derived SA3 via the form field; the override value and a "using override" log message appear in cell output
4. ERP SA2 code is derived from the geocoded point via point-in-polygon (not hardcoded 206071139) and printed in cell output
5. Edge cases are handled: boundary-hit points resolve to the containing polygon; water/off-shore points fall back to nearest-neighbor within a 2 km cap; ASGS edition mismatches emit a warning

---

#### Phase 8: ABS + MBS Parameterisation

**Goal:** Parameterise all ABS Data API and MBS fetches to use derived POA/SA3 codes and the validated peer list, remove the Abbotsford-specific GCP fallback, add peer-skip graceful handling, and harden the cache against error-response poisoning.
**Depends on:** Phase 7
**Requirements:** DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06

**Success Criteria:**
1. ABS Data API fetches use the derived POA/SA3 codes via a `fetch_abs(flow, codes, session)` helper — changing the site address changes which census tables are fetched
2. MBS SA3 loader filters on the derived SA3 code (not hardcoded 20607) with the state fallback warning preserved
3. Running with no peer postcodes skips peer table, peer charts, and peer competitor table gracefully (None-guards + printed skip message) without errors
4. A 504/5xx ABS API response is NOT cached (`allowable_codes=(200,)`) — retrying the same fetch hits the live API again, not a cached error
5. Abbotsford-specific GCP DataPack fallback is absent from the codebase — a network failure produces a warning-and-skip, not wrong-site data

---

#### Phase 9: Pharmacy Synergy Removal + Report Parameterisation

**Goal:** Fully remove the pharmacy synergy section (cells, template, citation, report deposit), parameterise the report template with site address/name, slugify the output filename, and add the data-sourcing and reproduction-path explainer cells.
**Depends on:** Phase 6 (SITE_CONFIG exists for site_address/site_name)
**Parallelisable with:** Phase 8 (touches §7/§8 only — independent of §1.4/§1.6/§3)
**Requirements:** REPORT-01, REPORT-02, REPORT-03, REPORT-04, REPORT-05, REPORT-06

**Success Criteria:**
1. Running the notebook produces no pharmacy synergy output — no §7.6 cells, no Jinja2 template §6 block, no citation [6], no `report["pharmacy_synergy_range"]` deposit, and no dangling references
2. The generated PDF/HTML filename is auto-derived from the site (slugified street name + postcode + ISO date, e.g., `johnston-st-3067-2026-07-08.pdf`), not hardcoded
3. The report template renders `{{ report["site_address"] }}` and `{{ report["site_name"] }}` — changing the site form changes the report header text
4. A "How the tool sources data" markdown explainer cell documents auto-fetched vs manual-upload data sources in a 4-column table
5. A reproduction-path markdown explainer states that default config reproduces v1.0 (minus pharmacy synergy) and what remains identical; report sections are renumbered (8→7) with no broken cross-references

---

#### Phase 10: Validator Update + Generator Hardening

**Goal:** Parameterise the validator with a site fixture and `--site` mode, add 6–8 new v2.0 checks, replace site-specific literal checks with variable-existence checks, and verify generator scripts remain byte-stable.
**Depends on:** Phases 6–9 (all v2.0 features must be in place before validator can check them)
**Requirements:** QUAL-01, QUAL-02, QUAL-03, QUAL-04

**Success Criteria:**
1. `python scripts/validate_v2_notebook.py --site abbotsford` passes all checks (default mode reproduces v1.0 validation)
2. Validator includes 6–8 new v2.0 checks (SITE_CONFIG present, no hardcoded 3067/20607 in §1.4+, pharmacy section absent, slug filename, template uses `site_address`, VIC guard present, §1.3 derive cell present) — all pass against the v2.0 notebook
3. No site-specific literals (`"Yarra"`, `"GCP_POA3067"`, `"20607"`) appear in validator check definitions — replaced with variable-existence checks that work for any site
4. Running all generator scripts twice produces byte-identical output — no site-specific values are embedded in generator source

---

#### Phase 11: v1.0 Reproduction Verification

**Goal:** Verify that the default Abbotsford config reproduces v1.0 results within documented tolerances — the final confidence check that generalisation didn't break the original study.
**Depends on:** Phase 10 (needs the updated validator to run v1.0 checks against the v2.0 notebook)
**Requirements:** REPRO-01, REPRO-02, REPRO-03, REPRO-04, REPRO-05

**Success Criteria:**
1. Default Abbotsford config produces SA3 20607 (not a different code from ASGS edition mismatch)
2. Default Abbotsford config produces catchment population within ±1% of v1.0's value
3. Default Abbotsford config produces verdict = GO (matching v1.0)
4. Default Abbotsford config produces P&L base case within ±5% of v1.0's values
5. v1.0 validator passes against v2.0 notebook with default config (minus pharmacy-specific checks FIN-07/REP-03/REP-04)

---

## Progress

| Phase | Name | Milestone | Plans | Status | Completed |
|-------|------|-----------|-------|--------|-----------|
| 1 | Scaffolding & Data Pipeline | v1.0 | 2/2 | Complete | 2026-07-05 |
| 2 | Catchment & Demographics | v1.0 | 3/3 | Complete | 2026-07-05 |
| 3 | Demand & Competitors | v1.0 | 3/3 | Complete | 2026-07-06 |
| 4 | Clinic Financial Model | v1.0 | 2/2 | Complete | 2026-07-06 |
| 5 | Scenarios & Executive Report | v1.0 | 2/2 | Complete | 2026-07-06 |
| 6 | Site Config Restructure | v2.0 | 0/? | Not started | — |
| 7 | Geocode Parameterisation + POA/SA3 Derivation | v2.0 | 0/? | Not started | — |
| 8 | ABS + MBS Parameterisation | v2.0 | 0/? | Not started | — |
| 9 | Pharmacy Synergy Removal + Report Parameterisation | v2.0 | 0/? | Not started | — |
| 10 | Validator Update + Generator Hardening | v2.0 | 0/? | Not started | — |
| 11 | v1.0 Reproduction Verification | v2.0 | 0/? | Not started | — |

## Dependency Graph

```
Phase 6 (Site Config)
  ├──→ Phase 7 (POA/SA3 Derivation)
  │      └──→ Phase 8 (ABS + MBS Parameterisation) ──┐
  └──→ Phase 9 (Pharmacy Removal + Report) ───────────┤
                                                       ↓
                                              Phase 10 (Validator + Generators)
                                                       ↓
                                              Phase 11 (Reproduction Verification)
```

- **6 → 7:** SITE_CONFIG must exist before geocode can read `SITE_CONFIG["address"]`
- **7 → 8:** Derived POA/SA3 codes must exist before ABS/MBS fetches can be parameterised
- **6 → 9:** SITE_CONFIG must exist for `site_address`/`site_name` in the report template
- **8 ∥ 9:** ABS/MBS parameterisation (§1.4/§1.6/§3) and pharmacy removal + report (§7/§8) touch different sections — parallelisable
- **6–9 → 10:** Validator can only check v2.0 features once they exist; generator byte-stability verified after all generator modifications
- **10 → 11:** Reproduction verification needs the updated validator to run v1.0 checks against the v2.0 notebook
- **Critical path:** 6 → 7 → 8 → 10 → 11 (Phase 9 joins at Phase 10)

---
*Last updated: 2026-07-08 — v2.0 roadmap created (6 phases, 35 requirements mapped)*
