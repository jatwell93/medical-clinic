# Requirements: Johnston St Medical Clinic Feasibility Study — v2.0 Multi-Site Tool

**Defined:** 2026-07-08
**Core Value:** Answer, with defensible data and transparent assumptions, whether a clinic can be profitable on its own at a user-specified site — for any Victorian address the user enters, not just the original Abbotsford site.

## v2.0 Requirements

Requirements for the v2.0 Multi-Site Feasibility Tool milestone. Each maps to roadmap phases 6–11 (continuing from v1.0's phases 1–5).

### Site Input & Configuration

- [ ] **SITE-01**: User can enter a VIC street address via `#@param` form field (replaces v1.0 hardcoded Abbotsford address)
- [ ] **SITE-02**: User can enter postcode, state (dropdown locked to VIC), and GP FTE count (slider 1–10) via `#@param` form fields
- [ ] **SITE-03**: User can enter optional peer postcodes (comma-separated string) via `#@param` form field
- [ ] **SITE-04**: User can enter optional SA3 override code (free-text string) via `#@param` form field
- [ ] **SITE-05**: Form defaults reproduce v1.0 Abbotsford config (292-296 Johnston St, 3067, 5 FTE, 9 peer postcodes) so out-of-the-box Run All reproduces v1.0
- [ ] **SITE-06**: Peer postcodes are validated (4-digit format check, VIC-only filter, dedupe, self-referential rejection) with clear printed warnings for dropped entries
- [ ] **SITE-07**: Geocoding reads the form-supplied address (not a hardcoded constant) with quality checks (partial_match flag warning, location_type assertion, VIC bounding box verification)

### Geographic Derivation

- [ ] **GEO-01**: Tool auto-derives POA code from geocoded point via point-in-polygon on ASGS POA boundaries
- [ ] **GEO-02**: Tool auto-derives SA3 code from geocoded point via point-in-polygon on ASGS boundaries (SA1 shapefile with SA3_CODE21 attribute or dedicated SA3 shapefile — roadmapper to decide)
- [ ] **GEO-03**: User can override auto-derived SA3 code via the SA3 override form field; override usage is logged in cell output
- [ ] **GEO-04**: Tool rejects non-VIC geocoded points with a clear `RuntimeError` explaining VIC-only scope (two-layered guard: form dropdown locked to VIC + post-geocode state check)
- [ ] **GEO-05**: Tool adopts EPSG:7899 (GDA2020 / Vicgrid) for all metre-based buffer/area math, replacing v1.0's EPSG:7855 (which only covers 144°E–150°E and silently distorts western VIC)
- [ ] **GEO-06**: Tool derives ERP SA2 code from geocoded point via point-in-polygon (not hardcoded 206071139)
- [ ] **GEO-07**: Tool handles SA3 point-in-polygon edge cases (boundary hits, water/off-shore points via nearest-neighbor fallback within 2 km cap, ASGS edition mismatch warning)

### Data Pipeline Parameterisation

- [ ] **DATA-01**: ABS Data API fetches use derived POA/SA3 codes (not hardcoded 3067/20607) via a parameterised `fetch_abs(flow, codes, session)` helper
- [ ] **DATA-02**: MBS SA3 loader filters on derived SA3 code (not hardcoded 20607) with state fallback warning preserved
- [ ] **DATA-03**: Peer census, Places, and competitor fetches use the validated user-supplied peer list (not hardcoded 9 peers)
- [ ] **DATA-04**: Peer table, peer charts, and peer competitor table are skipped gracefully (None-guards + printed skip message) when no peer postcodes are provided
- [ ] **DATA-05**: Abbotsford-specific GCP DataPack fallback is removed (does not generalise to other sites); network failure produces a warning-and-skip, not wrong-site data
- [ ] **DATA-06**: ABS API cache uses `allowable_codes=(200,)` to prevent error-response cache poisoning from 504s/5xxs

### Report & Pharmacy Removal

- [ ] **REPORT-01**: Pharmacy synergy section is fully removed (cells 81/82 deleted, Jinja2 template §6 block removed, citation [6] removed, `report["pharmacy_synergy_range"]` deposit removed) with no dangling references
- [ ] **REPORT-02**: Report filename is auto-derived from site (slugified street name + postcode + ISO date, e.g. `johnston-st-3067-2026-07-08.pdf`), not hardcoded
- [ ] **REPORT-03**: Report template is parameterised with site address and site name (`{{ report["site_address"] }}`, `{{ report["site_name"] }}`)
- [ ] **REPORT-04**: "How the tool sources data" markdown explainer cell documents auto-fetched vs manual-upload data sources with a 4-column table
- [ ] **REPORT-05**: Reproduction-path markdown explainer states that default config reproduces v1.0 (minus pharmacy synergy) and what remains identical
- [ ] **REPORT-06**: Report sections renumbered after pharmacy synergy removal (8→7 sections) with no broken cross-references

### Validator & Generator Hardening

- [ ] **QUAL-01**: Validator is parameterised with a site fixture (`--site` mode, default=abbotsford reproduces v1.0 checks)
- [ ] **QUAL-02**: Validator adds 6–8 new v2.0 checks (SITE_CONFIG present, no hardcoded 3067/20607 in §1.4+, pharmacy section absent, slug filename, template uses `site_address`, VIC guard present, §1.3 derive cell present)
- [ ] **QUAL-03**: Validator replaces site-specific literal checks (`"Yarra"`, `"GCP_POA3067"`, `"20607"`) with variable-existence checks
- [ ] **QUAL-04**: Generator scripts remain byte-stable (two runs produce identical output; no site-specific values embedded in generator source)

### v1.0 Reproduction Verification

- [ ] **REPRO-01**: Default Abbotsford config produces SA3 20607 (not a different code from ASGS edition mismatch)
- [ ] **REPRO-02**: Default Abbotsford config produces catchment population within ±1% of v1.0's value
- [ ] **REPRO-03**: Default Abbotsford config produces verdict = GO (matching v1.0)
- [ ] **REPRO-04**: Default Abbotsford config produces P&L base case within ±5% of v1.0's values
- [ ] **REPRO-05**: v1.0 validator passes against v2.0 notebook with default config (minus pharmacy-specific checks FIN-07/REP-03/REP-04)

## v2.1+ Requirements (Deferred)

Acknowledged but not in v2.0 roadmap. Tracked for future milestones.

### Multi-State Expansion

- **MSTATE-01**: Tool supports non-VIC Australian addresses with zone-aware CRS reprojection (MGA zones 49–56 or national CRS EPSG:9473)
- **MSTATE-02**: Tool auto-selects the correct MGA zone based on longitude, or adopts a single national CRS

### Batch & Comparison

- **BATCH-01**: User can run multiple site configs from a CSV/JSON list in a single notebook run
- **BATCH-02**: Tool produces one report per site plus a cross-site comparison summary table

### Pharmacy Synergy Reintroduction

- **PHARM-01**: Pharmacy synergy quantified as opt-in module (not toggle) with user-supplied pharmacy brand and script volume assumptions

### Advanced Catchments

- **ISO-01**: Drive-time isochrone catchments via OSRM or Distance Matrix (replaces radial buffers)
- **PEER-01**: Auto-suggest peer postcodes by nearest POA centroid + similar population density heuristic

## Out of Scope

Explicitly excluded from v2.0. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| ipywidgets for site-input form | Colab `#@param` is native, simpler, survives Run All + PDF export; ipywidgets break the edit-and-run flow. Reserve for v2.1+ only if dynamic dropdowns are needed. |
| Silent skip for non-VIC addresses | Violates "defensible data" Core Value — user might not realise the site was skipped. Hard error with clear message instead. |
| Pharmacy synergy as opt-in toggle | Keeps dead code in notebook, complicates report template with conditional sections, muddies standalone verdict Core Value. Clean removal in v2.0; opt-in module candidate for v2.1+. |
| Auto-download of MBS SA3 + AIHW Excel files | No stable API endpoint; scraping health.gov.au/AIHW download pages is fragile and breaks reproducibility. Manual upload with clear explainer instead. |
| Dynamic SA3 dropdown (populated after geocoding) | Can't be done with `#@param` (options must be hardcoded); would require ipywidgets (anti-feature). Free-text override handles the 1% edge case. |
| Manual ABS file download path | ABS Data API auto-fetch is primary, free, cached. v1.0's GCP fallback is Abbotsford-specific and doesn't generalise. Network failure = warn-and-skip, not wrong-site fallback. |
| Non-VIC site support (v2.0) | VIC-only pilot; other states need zone-aware reprojection or national CRS. Deferred to v2.1. |
| Batch/multi-site comparison mode | v2.0 proves single-site generalisation first. Deferred to v2.1. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Phase Name | Status |
|-------------|-------|------------|--------|
| SITE-01 | 6 | Site Config Restructure | Mapped |
| SITE-02 | 6 | Site Config Restructure | Mapped |
| SITE-03 | 6 | Site Config Restructure | Mapped |
| SITE-04 | 6 | Site Config Restructure | Mapped |
| SITE-05 | 6 | Site Config Restructure | Mapped |
| SITE-06 | 6 | Site Config Restructure | Mapped |
| SITE-07 | 6 | Site Config Restructure | Mapped |
| GEO-01 | 7 | Geocode Parameterisation + POA/SA3 Derivation | Mapped |
| GEO-02 | 7 | Geocode Parameterisation + POA/SA3 Derivation | Mapped |
| GEO-03 | 7 | Geocode Parameterisation + POA/SA3 Derivation | Mapped |
| GEO-04 | 7 | Geocode Parameterisation + POA/SA3 Derivation | Mapped |
| GEO-05 | 6 | Site Config Restructure | Mapped |
| GEO-06 | 7 | Geocode Parameterisation + POA/SA3 Derivation | Mapped |
| GEO-07 | 7 | Geocode Parameterisation + POA/SA3 Derivation | Mapped |
| DATA-01 | 8 | ABS + MBS Parameterisation | Mapped |
| DATA-02 | 8 | ABS + MBS Parameterisation | Mapped |
| DATA-03 | 8 | ABS + MBS Parameterisation | Mapped |
| DATA-04 | 8 | ABS + MBS Parameterisation | Mapped |
| DATA-05 | 8 | ABS + MBS Parameterisation | Mapped |
| DATA-06 | 8 | ABS + MBS Parameterisation | Mapped |
| REPORT-01 | 9 | Pharmacy Synergy Removal + Report Parameterisation | Mapped |
| REPORT-02 | 9 | Pharmacy Synergy Removal + Report Parameterisation | Mapped |
| REPORT-03 | 9 | Pharmacy Synergy Removal + Report Parameterisation | Mapped |
| REPORT-04 | 9 | Pharmacy Synergy Removal + Report Parameterisation | Mapped |
| REPORT-05 | 9 | Pharmacy Synergy Removal + Report Parameterisation | Mapped |
| REPORT-06 | 9 | Pharmacy Synergy Removal + Report Parameterisation | Mapped |
| QUAL-01 | 10 | Validator Update + Generator Hardening | Mapped |
| QUAL-02 | 10 | Validator Update + Generator Hardening | Mapped |
| QUAL-03 | 10 | Validator Update + Generator Hardening | Mapped |
| QUAL-04 | 10 | Validator Update + Generator Hardening | Mapped |
| REPRO-01 | 11 | v1.0 Reproduction Verification | Mapped |
| REPRO-02 | 11 | v1.0 Reproduction Verification | Mapped |
| REPRO-03 | 11 | v1.0 Reproduction Verification | Mapped |
| REPRO-04 | 11 | v1.0 Reproduction Verification | Mapped |
| REPRO-05 | 11 | v1.0 Reproduction Verification | Mapped |

**Coverage:**
- v2.0 requirements: 35 total
- Mapped to phases: 35 (100%)
- Unmapped: 0 ✅

**Phase Summary:**
- Phase 6 (Site Config Restructure): 8 requirements — SITE-01..07, GEO-05
- Phase 7 (Geocode Parameterisation + POA/SA3 Derivation): 6 requirements — GEO-01..04, GEO-06..07
- Phase 8 (ABS + MBS Parameterisation): 6 requirements — DATA-01..06
- Phase 9 (Pharmacy Synergy Removal + Report Parameterisation): 6 requirements — REPORT-01..06
- Phase 10 (Validator Update + Generator Hardening): 4 requirements — QUAL-01..04
- Phase 11 (v1.0 Reproduction Verification): 5 requirements — REPRO-01..05

**Key Decision — GEO-02 (SA1 vs SA3 Shapefile):** Use the existing SA1 shapefile (already on hand, ~100 MB, carries `SA3_CODE21`/`SA3_NAME21` attributes — verified live). A single point-in-polygon on SA1s yields both SA1 and SA3 codes with no new download, and enables geometry reuse between §1.3 (derivation) and §2 (catchment apportionment). The dedicated SA3 shapefile alternative (~5 MB download) was rejected.

---
*Requirements defined: 2026-07-08*
*Last updated: 2026-07-08 — roadmap created, 35/35 requirements mapped to Phases 6–11*
