# Project Research Summary

**Project:** Johnston St Medical Clinic Feasibility Study — v2.0 Multi-Site Feasibility Tool
**Domain:** Australian healthcare location analytics — generalising a single-site Colab notebook into a parameterised, address-driven multi-site tool (VIC pilot)
**Researched:** 2026-07-07
**Confidence:** HIGH

## Executive Summary

v2.0 generalises the shipped v1.0 Abbotsford study (88 cells, 36/36 validator checks) into a reusable tool that accepts any Victorian street address via a Colab `#@param` form, auto-derives the correct ABS geographies (POA + SA3) from the geocoded point, parameterises all downstream data fetches, and produces a slugified, site-named executive PDF. The headline finding from stack research: **zero new required runtime dependencies** — every v2.0 capability (form input, spatial join, parameterised ABS fetch, slugified filenames) is a refactor/reuse of the v1.0 stack (geopandas/shapely/pyproj/requests-cache) plus one optional tiny library (`python-slugify`). The only genuinely new asset is a data file (ASGS boundary shapefile), and even that may already be on hand (see conflict below).

The recommended approach is a **5-phase build order (6→7→8→9→10)** that threads the v2.0 changes through the existing v1.0 notebook structure with minimal disruption: restructure §0.3 into `SITE_CONFIG` + `BASE_ASSUMPTIONS` (Phase 6), add a new §1.3 POA/SA3 derivation cell via point-in-polygon (Phase 7), parameterise ABS/MBS fetches (Phase 8), remove pharmacy synergy + parameterise the report (Phase 9), and update the validator + generators for site-agnosticism (Phase 10). A 6th phase (Phase 11) verifies v1.0 reproduction. The architecture preserves all five v1.0 patterns (cached fetch, single params cell, pure-function P&L, dual-env bootstrap, report accumulator) and adds three new ones (site-config/assumptions split, point-in-polygon derivation, slugified filenames). Abbotsford ships as the default config so v2.0 out-of-the-box reproduces v1.0 (minus pharmacy synergy).

The key risks are: (1) **EPSG:7855 does NOT cover all of VIC** — the western strip (141–144°E: Mildura, Swan Hill, far Wimmera) is MGA zone 54, not 55; PROJECT.md's "no zone-awareness needed" claim is factually wrong and must be corrected (STACK and PITFALLS independently confirm this); (2) **hardcoded SA3 20607** appears in 8+ locations across code, assertions, and markdown — missing one produces a report that says "Yarra" for a Frankston site; (3) **pharmacy synergy removal** has hidden dependencies across 4 locations (code cell, markdown, Jinja2 template, citation [6]) — partial removal crashes the report render; (4) **the validator's 36 checks are hardcoded to Abbotsford** — generalising the notebook without generalising the validator creates a false failure wall. Every risk has a concrete mitigation mapped to a specific phase below.

**CONFLICT TO RESOLVE (roadmapper):** ARCHITECTURE.md and STACK.md disagree on SA3 derivation data assets. ARCHITECTURE says the **SA1 shapefile already on hand** (100 MB, loaded by v1.0 cell 16) includes `SA3_CODE21` / `SA3_NAME21` as attribute columns (verified live) — so a single point-in-polygon on SA1s yields the SA3 code with **no new download needed**. STACK.md says a **new SA3 shapefile data asset** (~5 MB, `SA3_2021_AUST_GDA2020.zip`) is required. The ARCHITECTURE finding is more specific (verified the SA1 columns live) and likely correct — it avoids a new download and enables geometry reuse between §1.3 and §2. However, STACK's SA3-only shapefile is far smaller (5 MB vs 100 MB) if a lighter load is preferred. **Both options are viable; the roadmapper should pick one.** Recommendation: use the SA1 shapefile (ARCHITECTURE's approach) since it's already on hand and enables §1.3→§2 geometry reuse, but note the SA3-only shapefile as the lighter alternative.

## Key Findings

### Recommended Stack

The v2.0 multi-site features are almost entirely a refactor/reuse of the v1.0 stack. **Net new runtime dependencies: 0 required, 1 optional (`python-slugify` ≥8.0, ~20 KB, MIT).** No heavy geospatial or form-framework additions are needed. The v1.0 core (geopandas 1.1.3, shapely 2.1.2, pyproj 3.7.x, requests-cache, pandas, jinja2, weasyprint) covers every v2.0 need: spatial join, CRS reprojection, parameterised HTTP fetch, form input, report generation. Full details in STACK.md.

**Core technologies (v2.0 additions):**
- **(none required)** — the v1.0 stack covers all v2.0 needs; no new core library
- **`python-slugify` ≥8.0 (OPTIONAL)** — safe filename slugs from street addresses for `feasibility_<postcode>_<street>.pdf` naming; handles apostrophes, hyphens, unicode that a 5-line regex misses; acceptable regex fallback exists if zero-deps is a hard rule
- **stdlib `dataclasses`** — `SiteConfig` dataclass for the site-input form values; no pip install
- **Colab `#@param` form fields** — native Colab form UI (text boxes, dropdowns, sliders) for site input; zero imports, survives Restart & Run All; preferred over ipywidgets for static config (confirmed by Colab maintainers)

**CRITICAL stack finding — EPSG:7855 coverage:**
- EPSG:7855 (GDA2020 / MGA zone 55) covers **144°E–150°E only**; VIC's western border is ~141°E
- Far-western VIC (Mildura, Swan Hill, Nhill, Ouyen) is in **MGA zone 54 (EPSG:7854)**, not zone 55
- **Recommended fix: adopt EPSG:7899 (GDA2020 / Vicgrid)** — a single Lambert Conic Conformal CRS purpose-built by the VIC Surveyor-General for state-wide coverage (bbox 140.96–150.04°E); covers ALL of Victoria with no zone edge cases; Vicmap basemaps use it
- Alternative: keep EPSG:7855 but document a 144°E eastern-VIC-only scope (excludes ~5% of VIC population)
- **Either way, PROJECT.md's "EPSG:7855 stays valid for all VIC sites" claim must be corrected** — it is factually wrong

### Expected Features

FEATURES.md benchmarks v2.0 against professional multi-site feasibility tool archetypes (pharmacy-broker templates, health-planning consultancy GIS tools) and defines the feature set scoped to **only the new v2.0 capabilities** — v1.0 features are dependencies, not re-research targets.

**Must have (table stakes):**
- Site-input form (`#@param`: street address, state=VIC locked, postcode, FTE slider, peer postcodes, SA3 override) — replaces v1.0 hardcoded constants; Abbotsford as defaults
- Geocoding of form-supplied address — reuses v1.0 cell 13 logic, reads form variable
- VIC-only guard (two-layered: form dropdown locked to `["VIC"]` + post-geocode state check) — hard error on non-VIC with clear message
- SA3 auto-derivation (spatial join against ASGS boundaries) + editable override field — replaces hardcoded SA3 20607
- Peer postcode entry + validation (format check, VIC check, dedupe, self-referential rejection) — replaces hardcoded peer list
- Graceful peer-skip when no peers provided — None-guards on v1.0 peer cells
- Report filename from site (slugify street + postcode + date) — replaces hardcoded PDF filename
- "How the tool sources data" markdown explainer — auto-vs-manual data split

**Should have (competitive differentiators):**
- SA3 auto-derivation with editable override — most tools hardcode or make user look up manually; auto-derive + visible override is best of both
- Reproduction-path explainer (default = v1.0 minus pharmacy synergy) — builds trust that generalisation didn't break the original
- Slugified, date-stamped report naming with street-name extraction — human-readable, self-identifying, no clobbering
- "How the tool sources data" as a first-class confidence builder (not a task list)

**Defer (v2.1+):**
- Batch/multi-site comparison mode — v2.0 proves single-site generalisation first
- Non-VIC site support (MGA zone-aware reprojection, zones 49–56) — once VIC pilot validates
- Pharmacy synergy as opt-in module — once standalone verdict is stable
- Dynamic SA3 dropdown via ipywidgets — only if free-text override proves insufficient
- Auto-suggest peers by nearest POA centroid — eliminates peer validation failure modes

**Anti-features to refuse:** ipywidgets for static form (state-readiness hazard), silent skip for non-VIC addresses (violates defensible-data core value), pharmacy synergy as opt-in toggle (keeps dead code), auto-download of MBS/AIHW Excel files (no stable API, fragile scraping).

### Architecture Approach

A v2.0 **integration architecture** that threads multi-site changes through the existing v1.0 notebook structure (88 cells, §0–§8) with minimal disruption. The §0.3 parameters cell is restructured into two dicts (`SITE_CONFIG` for user inputs + `BASE_ASSUMPTIONS` for constants) in the same cell — preserving the single-params-cell auditability invariant. A new §1.3 cell (point-in-polygon POA/SA3 derivation) is inserted between geocode (§1.2) and ABS fetch (§1.4), loading ASGS boundaries once and reusing them in §2 catchment. SITE_CONFIG values are injected into BASE_ASSUMPTIONS at definition time, so downstream cells (§2–§7) continue reading `BASE_ASSUMPTIONS["n_gp_fte"]` with **zero changes**. Full details in ARCHITECTURE.md.

**Major components (v2.0 new/modified):**
1. **§0.3 SITE_CONFIG + BASE_ASSUMPTIONS split** (MODIFIED) — user inputs visually distinct from model constants; default = Abbotsford (reproduces v1.0)
2. **§1.3 POA/SA3 Derivation** (NEW) — point-in-polygon on ASGS boundaries → `site_poa_code` + `site_sa3_code`; VIC guard (RuntimeError on point outside VIC); geometry reuse with §2
3. **§1.4 ABS fetch** (MODIFIED) — parameterised POA/SA3 codes via `fetch_abs(flow, codes, session)` helper; derived codes replace hardcoded 3067/20604
4. **§1.6 MBS SA3** (MODIFIED) — filters on `site_sa3_code` instead of hardcoded 20607
5. **§7 pharmacy synergy** (DELETED) — cells 81–82 removed; Jinja2 template §6 block removed; citation [6] removed
6. **§8 Report** (MODIFIED) — site-parameterised template (`{{ report["site_address"] }}`); slugified filename (`slugify(SITE_CONFIG["address"])`)
7. **Validator** (MODIFIED) — parameterised with site fixture; 6–8 new v2.0 checks; `--site` mode for v1.0 reproduction

### Critical Pitfalls

Top 5 of 12 documented in PITFALLS.md (each mapped to a phase):

1. **MGA zone 55 does NOT cover all of VIC** (Pitfall 1, Phase 6) — western VIC (141–144°E) is zone 54; reprojection doesn't crash but produces out-of-spec coordinates with ~0.4% distortion; the 28.27 km² buffer assertion passes silently (28.38) so the error is invisible. **Fix:** adopt EPSG:7899 (Vicgrid) for all-VIC coverage, OR add a `lon < 144.0` zone check + warning. Either way, correct PROJECT.md.

2. **Hardcoded SA3 20607 in 8+ locations** (Pitfall 2, Phase 7 + 10) — the SA3 code appears in MBS loader, AIHW loader, assertion cell, ERP SA2 code (206071139), print statements, warning messages, and markdown. Parameterising the obvious loaders but missing one produces a report that says "Yarra" for a Frankston site, or crashes the assertion. **Fix:** grep the entire notebook for `20607` and `20604`; replace every instance with `SA3_CODE`/`SA3_NAME` variables; add validator check that no literal SA3 code appears in source.

3. **Pharmacy synergy removal has hidden dependencies** (Pitfall 8, Phase 9 + 10) — removing §7.6 code cells but leaving the Jinja2 template's `{{ report['pharmacy_synergy_range'] }}` reference crashes the render with `UndefinedError`; citation [6] becomes dangling; validator REP-03/REP-04/FIN-07 fail. **Fix:** coordinated removal across 4 locations (code cell, markdown, template section 6, citation [6]) + validator updates in one pass.

4. **Validator hardcoded to Abbotsford** (Pitfall 9, Phase 10) — 36 checks assert Abbotsford-specific literals (`"Yarra"`, `"GCP_POA3067"`, `"20607"`, `"Pharmacy Synergy"`, `[1]`-`[8]`). Generalising the notebook without generalising the validator creates a false failure wall. **Fix:** parameterise validator with site fixture; add `--site` mode (default: abbotsford reproduces v1.0); replace literal checks with variable-existence checks.

5. **v1.0 reproduction must be verified** (Pitfall 11, Phase 11) — default Abbotsford config must produce SA3 20607, same catchment population (±1%), same verdict (GO), same P&L base case (±5%). Subtle differences creep in via SA3 shapefile edition mismatch, ERP SA2 code drift, geocoded point drift, and peer list changes. **Fix:** dedicated reproduction verification phase; pin ASGS edition, pin cached geocoded coordinates, document acceptable tolerances.

Also critical: SA3 point-in-polygon edge cases (Pitfall 3 — boundary hits, water/off-shore points, ASGS edition mismatch), ABS API parameterised fetch edge cases (Pitfall 4 — non-existent POAs, rate limiting, cache poisoning from 504s), geocoding edge cases (Pitfall 5 — `partial_match`, `location_type`, out-of-state results), and ERP scaling for new sites (Pitfall 12 — high-growth fringe suburbs vs declining regional areas need site-specific SA2 growth rates, not Abbotsford's).

## Implications for Roadmap

The four documents agree on a 5-phase build order (6→7→8→9→10) plus a verification phase (11), threading v2.0 changes through the v1.0 notebook structure. The dependency chain is: site-config → geocode → derive POA/SA3 → parameterise ABS/MBS → remove pharmacy + parameterise report → update validator/generators → verify v1.0 reproduction.

### Phase 6: Site Config Restructure (§0.3)
**Rationale:** Every v2.0 feature reads from the form fields; the form replaces v1.0's hardcoded constants. Must exist before geocode parameterisation.
**Delivers:** `SITE_CONFIG` dict (user inputs via `#@param` form) + `BASE_ASSUMPTIONS` dict (constants) in the same §0.3 cell; SITE_CONFIG values injected into BASE_ASSUMPTIONS; Abbotsford as defaults. Peer postcode validation cell (format, VIC, dedupe). Geocode quality checks (`partial_match`, `location_type`, VIC bounding box). MGA zone check/warning (or EPSG:7899 adoption).
**Addresses:** Site-input form, Abbotsford default, VIC-only guard, peer postcode validation, geocoding edge cases (FEATURES table stakes).
**Avoids:** Pitfalls 1 (MGA zone), 5 (geocoding edge cases), 6 (peer validation).
**Generator:** `extend_v2_notebook_phase6.py`

### Phase 7: Geocode Parameterisation + POA/SA3 Derivation (§1.2, §1.3 NEW)
**Rationale:** SA3 derivation is the keystone of multi-site — all downstream ABS/MBS fetches depend on derived codes. Must follow SITE_CONFIG (Phase 6) and precede ABS parameterisation (Phase 8).
**Delivers:** §1.2 modified to read `SITE_CONFIG["address"]`; new §1.3 cell loads ASGS boundaries, point-in-polygon → `site_poa_code` + `site_sa3_code`, VIC guard (RuntimeError on point outside VIC), SA3 override handling, nearest-neighbor fallback for water/off-shore points (2 km cap). §2 refactored to reuse §1.3 geometries (assert globals exist, no reload). ERP SA2 code derived from point-in-polygon (not hardcoded 206071139).
**Uses:** geopandas `sjoin(predicate="within")`, shapely `Point`, pyproj CRS transforms — all from v1.0 stack.
**Implements:** Pattern 7 (point-in-polygon POA/SA3 derivation).
**Avoids:** Pitfalls 2 (hardcoded SA3), 3 (PIP edge cases), 12 (ERP scaling).
**Generator:** `extend_v2_notebook_phase7.py`
**CONFLICT NOTE:** This phase must decide SA1-vs-SA3 shapefile (see conflict above). If SA1 is chosen, §1.3 loads the existing 100 MB SA1 shapefile and extracts SA3_CODE21. If SA3 is chosen, a new ~5 MB download is required.

### Phase 8: ABS + MBS Parameterisation (§1.4, §1.6, §3)
**Rationale:** With derived POA/SA3 codes available (Phase 7), the ABS and MBS fetches can be parameterised. Peer conditional logic depends on validated peer list (Phase 6).
**Delivers:** `fetch_abs(flow, codes, session)` helper replacing inline fetch code; `PEER_POA_CODES` built from derived site POA + user peers (deduped, validated against POA shapefile); MBS SA3 filter on `site_sa3_code` (not hardcoded 20607); conditional peer table/charts (skip if empty); `allowable_codes=(200,)` to prevent cache poisoning; batch logic for >10 peers; empty-response warnings. Abbotsford-specific GCP fallback removed/genericised.
**Addresses:** Peer postcode entry, graceful peer-skip, parameterised ABS/MBS fetch (FEATURES).
**Avoids:** Pitfalls 4 (ABS API edge cases), 6 (peer validation downstream).
**Generator:** `extend_v2_notebook_phase8.py`

### Phase 9: Pharmacy Synergy Removal + Report Parameterisation (§7, §8)
**Rationale:** Pharmacy removal and report parameterisation are independent of Phases 7–8 (different sections) and can be parallelised. Both touch §7/§8 only.
**Delivers:** §7.6 cells (81–82) deleted; Jinja2 template §6 pharmacy block removed; citation [6] removed + citations renumbered (or validator updated to [1]–[7]); `report["pharmacy_synergy_range"]` deposit removed; `slugify()` function; report template parameterised (`{{ report["site_address"] }}`, `{{ report["site_name"] }}`); PDF/HTML filenames slugified; "How the tool sources data" markdown explainer; reproduction-path explainer.
**Addresses:** Pharmacy synergy removal, report filename from site, data sourcing explainer, reproduction explainer (FEATURES).
**Avoids:** Pitfalls 7 (filename slugification), 8 (pharmacy removal hidden deps).
**Generator:** `extend_v2_notebook_phase9.py`
**Parallelisable with:** Phase 8 (independent sections).

### Phase 10: Validator Update + Generator Hardening
**Rationale:** All v2.0 features must be in place before the validator can be updated to check them. Generator byte-stability must be verified after all generator modifications.
**Delivers:** Validator parameterised with site fixture (`--site` mode, default: abbotsford); 6–8 new v2.0 checks (SITE_CONFIG present, slugify present, §1.3 derive cell present, no hardcoded 3067/20607 in §1.4+, pharmacy synergy absent, filename uses slug, template uses `{{ report['site_address'] }}`, VIC guard present); site-specific checks (GEO-04 "Yarra", DEMO-01 "GCP_POA3067", DEMAND-01 "20607") replaced with variable-existence checks; REP-03/REP-04/FIN-07 updated for pharmacy removal. Generator chain verified byte-stable (two runs produce identical output; no site-specific values embedded in generators).
**Addresses:** Validator generalisation, generator byte-stability (PITFALLS).
**Avoids:** Pitfalls 9 (validator hardcoded), 10 (generator byte-stability).

### Phase 11: v1.0 Reproduction Verification
**Rationale:** The final verification before milestone close — confirms the generalisation didn't break the original result.
**Delivers:** Default Abbotsford config run: SA3 = 20607 (not a different code from edition mismatch), catchment population ±1% of v1.0, verdict = GO, P&L base case ±5%, v1.0 validator passes (minus pharmacy checks). Documented tolerances. Fresh-clone Colab run + keyless cache-only run.
**Addresses:** v1.0 reproduction requirement (PITFALLS Pitfall 11).
**Avoids:** Pitfall 11 (reproduction failure from subtle code-path differences).

### Phase Ordering Rationale

- **6 before 7:** SITE_CONFIG must exist before geocode can read `SITE_CONFIG["address"]`.
- **7 before 8:** Derived POA/SA3 codes must exist before ABS/MBS fetches can be parameterised.
- **8 ∥ 9:** ABS/MBS parameterisation (§1.4/§1.6/§3) and pharmacy removal + report parameterisation (§7/§8) touch different sections — parallelisable.
- **10 after 6–9:** Validator can only check v2.0 features once they exist; generator byte-stability verified after all generator modifications.
- **11 after 10:** Reproduction verification needs the updated validator to run v1.0 checks against the v2.0 notebook.
- **Critical path:** Phase 6 → 7 → 8 → 10 → 11 (Phase 9 joins at Phase 10).

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 6 (MGA zone decision):** The EPSG:7855 vs EPSG:7899 decision has architectural consequences (changes the v1.0 CRS constant, buffer area assertion tolerance, all §2 geometry). STACK recommends EPSG:7899; PITFALLS offers a zone-check alternative. This is a PROJECT.md-level decision that must be made before Phase 6 planning.
- **Phase 7 (SA1 vs SA3 shapefile):** The CONFLICT between ARCHITECTURE (use existing SA1 shapefile with SA3_CODE21 attribute) and STACK (new SA3 shapefile download) must be resolved. ARCHITECTURE's finding is more specific (verified live) and enables geometry reuse; STACK's is lighter. Roadmapper decides.
- **Phase 7 (SA3 PIP edge cases):** Boundary hits, water/off-shore points, ASGS edition mismatch all need handling logic — the exact fallback strategy (nearest-neighbor cap distance, coastal point buffering) needs specification.
- **Phase 8 (ABS SA3 dataflows):** `C21_G01_SA3` / `C21_G02_SA3` / `C21_G04_SA3` dataflow IDs are inferred from the `C21_{table}_{geography}` pattern but not live-verified — must confirm via `dataflow?detail=allstubs` at runtime.

Phases with standard patterns (skip research-phase):
- **Phase 6 (site-input form):** Colab `#@param` is well-documented; `@dataclass` + `__post_init__` validation is textbook Python.
- **Phase 9 (pharmacy removal + report param):** Deletions are safe (pharmacy was non-load-bearing); Jinja2 template parameterisation is string replacement; slugify is a solved problem.
- **Phase 10 (validator update):** Parameterisation strategy is straightforward (site fixture dict); generator byte-stability is verified by diff.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Zero new deps verified against Colab preinstalled set; EPSG:7855 coverage gap verified against EPSG registry + Land Vic; EPSG:7899 verified as VIC government standard. MEDIUM on exact ABS SA3 shapefile download URL (verify at runtime). |
| Features | HIGH | Colab `#@param` patterns verified against official docs + colabtools issues; notebook cell references verified by reading `Johnston_St_v2.ipynb` directly. MEDIUM on SA3 boundary-join availability in Colab (depends on shapefile load). |
| Architecture | HIGH | v1.0 architecture fully audited cell-by-cell; SA1 shapefile SA3_CODE21 attribute verified live; integration points traced. The SA1-vs-SA3 conflict is a genuine open question, not a confidence gap. |
| Pitfalls | HIGH | v1.0 codebase audited directly (notebook, validator, generators); MGA zone coverage and ABS POA/SA3 edge cases web-verified against EPSG registry + ABS docs. All 12 pitfalls mapped to specific phases. |

**Overall confidence:** HIGH

### Gaps to Address

- **SA1 vs SA3 shapefile (CONFLICT):** ARCHITECTURE says SA1 shapefile (already on hand, 100 MB) has `SA3_CODE21` attribute — no new download needed. STACK says a new SA3 shapefile (~5 MB) is required. Roadmapper must resolve. Recommendation: SA1 (already on hand, enables §1.3→§2 reuse), but flag both options.
- **EPSG:7855 vs EPSG:7899 decision:** PROJECT.md's "no zone-awareness needed" claim is wrong. Must decide: adopt EPSG:7899 (STACK recommendation, covers all VIC) or keep EPSG:7855 with documented 144°E scope limitation. This is a PROJECT.md correction + architectural decision before Phase 6.
- **ABS SA3 dataflow IDs:** `C21_G01_SA3` etc. inferred from pattern, not live-verified — confirm at runtime via dataflow list. (Note: v2.0 may not need SA3-level census at all — SA3 is only used for MBS utilisation which comes from a local xlsx, not the ABS API.)
- **ERP SA2 derivation:** v1.0 uses a specific SA2 code (206071139) for ERP growth rate. v2.0 must derive the SA2 from point-in-polygon — but SA2-level ERP data may be suppressed for some areas. Fallback strategy (SA3 → SA4 → state) needs specification in Phase 7/8.
- **ASGS edition pinning:** MBS SA3 Summary uses ASGS Edition 3 (2021) codes. The shapefile used for point-in-polygon must be the same edition. Store edition as a constant and print it.
- **Citation renumbering:** Removing citation [6] (PBS Statistics, pharmacy-only) requires either renumbering [7]–[8] → [6]–[7] or updating the validator's `[1]`-`[8]` check to `[1]`-`[7]`. Decide in Phase 9.

## Sources

### Primary (HIGH confidence)
- EPSG registry (epsg.org) — EPSG:7855 area of use (144°E–150°E), EPSG:7899 GDA2020/Vicgrid bbox (140.96–150.04°E) — HIGH
- Land Victoria (land.vic.gov.au) — VicGrid2020 EPSG:7899 is "the most accurate projection for Victoria"; MGA zone boundaries (zone 54 = 138–144°E, zone 55 = 144–150°E) — HIGH
- ABS digital boundary files page (abs.gov.au) — ASGS 2021 SA3 shapefile source; file names `SA3_2021_AUST_GDA2020` / `SA3_2021_AUST_GDA94` — HIGH (page verified; exact direct-download URL MEDIUM)
- Colab Forms notebook (colab.research.google.com/notebooks/forms.ipynb) — `#@param` syntax, field types — HIGH
- GoogleColab/colabtools Issue #2407 — Colab maintainers recommend `#@param` for static config, ipywidgets for dynamic — HIGH
- v1.0 notebook audit (`Johnston_St_v2.ipynb`, 88 cells) — cell-by-cell inspection of hardcoded SA3 20607, pharmacy synergy cells, report template — HIGH
- v1.0 validator audit (`scripts/validate_v2_notebook.py`, 36 checks) — site-specific literals identified — HIGH
- SA1 shapefile attributes verified live — `SA1_2021_AUST_SHP_GDA2020.zip` includes `SA3_CODE21`, `SA3_NAME21`, `SA2_CODE21`, `SA2_NAME21` — HIGH

### Secondary (MEDIUM confidence)
- python-slugify PyPI (v8.0.4, MIT, Python ≥3.7) — unicode-aware slugify; `text-unidecode` backend GPL note — HIGH on library, MEDIUM on dep-vs-regex decision
- ABS Data API dataflow pattern `C21_{table}_{geography}` generalises to SA3 — inferred from POA pattern + third-party confirmation (docs.sarahcgall.co.uk) — MEDIUM-HIGH
- ABS Postal Areas (ASGS Edition 3) — exclude non-street-delivery postcodes; codes may not match past editions — HIGH

### Tertiary (LOW confidence)
- Exact ABS SA3 shapefile direct-download URL string — not live-verified; ABS occasionally restructures paths — verify with HEAD request at runtime
- ABS ArcGIS REST SA3 MapServer (geo.abs.gov.au) — alternative source, usable but shapefile download preferred for offline cache pattern

---
*Research completed: 2026-07-07*
*Ready for roadmap: yes*
