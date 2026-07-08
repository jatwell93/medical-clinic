# Phase 6: Site Config Restructure - Context

**Gathered:** 2026-07-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace v1.0's hardcoded Abbotsford constants with a `#@param` site-input form (`SITE_CONFIG` dict) separated from model constants (`BASE_ASSUMPTIONS`), adopt EPSG:7899 (GDA2020 / Vicgrid) for all metre-based buffer/area math across §2, and add peer postcode validation + geocode quality checks. Abbotsford ships as the default config so out-of-the-box Run All reproduces v1.0 (minus pharmacy synergy).

**In scope (Phase 6):** SITE_CONFIG/BASE_ASSUMPTIONS restructure of §0.3; `#@param` form fields (SITE-01..05); peer postcode validation (SITE-06); geocode reads form-supplied address + quality checks (SITE-07); EPSG:7899 adoption across all §2 geometry cells (GEO-05).

**Out of scope (Phase 7 and later):** POA/SA3 auto-derivation via point-in-polygon (GEO-01/02/06); the authoritative two-layered VIC guard via geocoder state address_component (GEO-04); SA3 override handling (GEO-03); SA3 edge cases (GEO-07). Phase 6 does NOT derive POA/SA3 — it only validates inputs and adopts the new CRS.

</domain>

<decisions>
## Implementation Decisions

### Geocode quality check strictness
- **D-01:** A geocoded point outside the VIC bounding box → **`RuntimeError` hard stop** with a clear VIC-only-scope message. Consistent with Phase 7's GEO-04 non-VIC state check (also RuntimeError). A wrong-state site must not silently proceed (defensible-data Core Value).
- **D-02:** Geocoding returning **zero results** (no match at all, not partial_match) → **`RuntimeError` hard fail** with message: `Geocoding returned no results for: {address}. Check the address and re-run.` Halts before downstream cells receive a `None` point.
- **D-03:** `partial_match=True` and/or non-`ROOFTOP` `location_type` → **warning that prints the returned lat/lon AND formatted_address** alongside the flag, so the user can eyeball whether the point is plausible before the run continues. The run does NOT halt on these — they are warnings only.
- **D-04:** The three checks are ordered: zero-results → bbox-outside (both hard fail) → partial_match/non-ROOFTOP (warn + continue).

### Phase 6 ↔ Phase 7 VIC-check boundary
- **D-05:** VIC enforcement is split into two **distinct, non-overlapping** checks across two phases:
  - **Phase 6 (coarse early-reject):** bounding-box check on the geocoded point's lat/lon against VIC's bbox (~140.96–150.04°E, ~33.98–39.13°S). Mechanism = coordinate bbox test. Failure = RuntimeError (D-01).
  - **Phase 7 (authoritative two-layered guard, GEO-04):** parses the geocoder response's `address_components` for `administrative_area_level_1 == 'Victoria'`. Mechanism = address-component parse. This is the second layer; the form dropdown locked to `["VIC"]` is the first layer.
- **D-06:** The two checks use **different mechanisms** (P6 = coordinate bbox; P7 = address component), so they are not redundant — P6 is a fast geometric gate, P7 is the authoritative administrative check. The planner must not duplicate P6's bbox logic in P7 or vice versa.

### EPSG:7899 migration scope
- **D-07:** Introduce a single **`CRS_METRIC = "EPSG:7899"`** constant in §0.3 (alongside SITE_CONFIG/BASE_ASSUMPTIONS) and replace every literal `"EPSG:7855"` string in §2 with `CRS_METRIC`. One source of truth for the CRS — matches the existing BASE_ASSUMPTIONS single-params-cell pattern and lets the validator check the constant exists.
- **D-08:** **Recompute the expected 3 km buffer area under EPSG:7899** at the Abbotsford site and update `assert_3km_buffer_km2` (and tolerance `assert_3km_buffer_tol`) so the assertion stays a meaningful sanity check. The headline number may shift slightly from 28.27 km² (research notes ~28.27–28.4 under 7855; 7899 should be ~28.27 at catchment scale). Do NOT widen tolerance to hide the change — keep the assertion honest.
- **D-09:** Phase 6 rewrites **ALL §2 geometry cells** that reference 7855 — buffer construction, area apportionment, map rendering, contextily tile fetch. GEO-05 explicitly says "all metre-based buffer/area math uses EPSG:7899"; leaving any cell on 7855 would partially unmet GEO-05 and silently distort western-VIC sites.
- **D-10:** Update the §2.2 header comments and the `assert_3km_buffer_km2` inline comment (currently "sanity check for EPSG:7855 buffering") to reference EPSG:7899.

### Peer validation UX
- **D-11:** Peer validation runs **inline in §0.3**, immediately after the SITE_CONFIG/BASE_ASSUMPTIONS dicts, producing a cleaned `PEER_POSTCODES` list that downstream cells read. Preserves the PIPE-05 single-params-cell invariant (all input handling in one auditable cell).
- **D-12:** Warning format = **one printed line per dropped peer, naming the entry AND the reason**, e.g. `[peer] dropped 312X — not 4 digits`, `[peer] dropped 2000 — not VIC (3000–3999)`, `[peer] dropped 3067 — duplicate`, `[peer] dropped 3067 — self-referential`. Matches success criteria #3 ("printed warning naming the dropped entry") literally and is the most auditable form for a teaching notebook.
- **D-13:** VIC-only peer filter = **postcode prefix `'3'`** (VIC postcodes are 3000–3999, all start with `'3'`). Simple, deterministic, no shapefile load required in §0.3. Matches v1.0's existing `poa["POA_CODE21"].str.startswith("3")` filter pattern in §2.
- **D-14:** Validation also **prints a confirmation listing the valid peers** when peers pass: `[peer] {N} valid peers: 3066, 3068, ...`. Gives positive feedback that validation ran — not just warnings on the bad entries.
- **D-15:** Validation order: format (4-digit) → VIC-prefix → dedupe → self-referential (reject the site's own postcode if it appears in peers). Each rejected entry is dropped before the next check sees it.

### Claude's Discretion
- Exact VIC bounding box coordinates to hardcode (use the canonical VIC bbox from the EPSG:7899 registry entry / Land Victoria — ~140.96–150.04°E, ~33.98–39.13°S; researcher/planner to confirm the precise values).
- Exact recomputed 3 km buffer area value under EPSG:7899 (determined at build time by running the buffer in 7899 and reading the area).
- Whether `location_type` accepts `ROOFTOP` only or also `RANGE_INTERPOLATED` as "acceptable" (researcher to confirm Google's taxonomy; default: warn on anything non-ROOFTOP per D-03).
- SITE_CONFIG dict field naming/key conventions (the architecture sketch uses `address`, `peer_postcodes`, `n_gp_fte`, `n_allied_fte`, `floor_area_sqm`, `sa3_override` — planner may refine).
- Whether `floor_area_sqm` is a `#@param` form field (site-specific) or stays a BASE_ASSUMPTIONS constant — architecture places it in SITE_CONFIG, planner to confirm it warrants a form field.

</decisions>

<specifics>
## Specific Ideas

- Geocode warnings should feel like the v1.0 teaching style — plain-language, print the actual returned values so a student can see what the geocoder sent back.
- The peer validation lines should prefix `[peer]` to match v1.0's existing `[params]`, `[§1.3]` log-line conventions.
- The CRS constant should live in §0.3 next to the dicts, not in §2 — so a future CRS change is a one-line edit, consistent with how BASE_ASSUMPTIONS already centralises tunables.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 6 architecture & integration
- `.planning/research/ARCHITECTURE.md` — §0.3 restructure (Pattern 6: SITE_CONFIG + BASE_ASSUMPTIONS split, injection at definition time), §1.2 geocode modification, geometry-reuse pattern. The authoritative integration architecture for v2.0.
- `.planning/research/SUMMARY.md` — Phase 6 deliverables list, EPSG:7855 coverage-gap finding (Pitfall 1), EPSG:7899 recommendation, `#@param` form decision, VIC-only guard design.
- `.planning/research/STACK.md` — EPSG:7899 (GDA2020/Vicgrid) CRS details, `#@param` form field patterns, what NOT to use (EPSG:4326 buffering, EPSG:7855 for western VIC).

### Requirements & roadmap
- `.planning/REQUIREMENTS.md` — SITE-01..07 (Phase 6), GEO-05 (Phase 6); Out of Scope table (ipywidgets, silent non-VIC skip, dynamic SA3 dropdown). Traceability matrix.
- `.planning/ROADMAP.md` — Phase 6 goal, success criteria (5 items), dependency graph (6→7→8→10→11; 6→9).
- `.planning/PROJECT.md` — Key Decisions table (EPSG:7899 adoption pending v2.0; VIC-only pilot scope; `#@param` form; pharmacy synergy dropped). Core Value (standalone clinic verdict, defensible data).

### Existing code to modify
- `Johnston_St_v2.ipynb` §0.3 (lines ~155–263) — current single BASE_ASSUMPTIONS cell to restructure into SITE_CONFIG + BASE_ASSUMPTIONS + CRS_METRIC + peer validation.
- `Johnston_St_v2.ipynb` §1.2 (geocode cell) — currently reads hardcoded `SITE_ADDRESS`; modify to read `SITE_CONFIG["address"]` + add quality checks (D-01..D-04).
- `Johnston_St_v2.ipynb` §2 (lines ~522–812) — all `to_crs("EPSG:7855")` calls + the 28.27 km² assertion (lines ~599–616) to migrate to CRS_METRIC (D-07..D-10).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `BASE_ASSUMPTIONS` dict (§0.3) — already the single source of truth for tunables; SITE_CONFIG merges into it via `BASE_ASSUMPTIONS["n_gp_fte"] = SITE_CONFIG["n_gp_fte"]` etc. Downstream §2–§7 consumer code needs ZERO changes for FTE/floor_area/peer parameterisation (ARCHITECTURE.md Pattern 6).
- `poa["POA_CODE21"].str.startswith("3")` filter (§2, line ~564) — the exact VIC-postcode-prefix pattern to reuse for peer validation (D-13).
- `CachedSession` HTTP boundary (§0.x) — geocode calls already routed through it; quality checks add no new network cost.
- `clinic_pnl(a)` pure function (§6) — already parameterised via the dict; FTE flowing from SITE_CONFIG through BASE_ASSUMPTIONS requires no §6 change.

### Established Patterns
- **Single parameters cell (PIPE-05):** all tunables in §0.3; downstream cells only read, never redefine. SITE_CONFIG + BASE_ASSUMPTIONS + CRS_METRIC + peer validation all live in this one cell (D-07, D-11).
- **`{**BASE_ASSUMPTIONS, **overrides}` scenario pattern (Phase 5):** preserved — SITE_CONFIG injection happens at definition time, before any scenario override.
- **Log-line prefix convention:** `[params]`, `[§1.3]` — peer validation uses `[peer]` (D-12), geocode warnings follow suit.
- **Hard-fail-on-wrong-data over silent-skip:** v1.0's GCP fallback emits a warning; v2.0 extends the "defensible data" stance — non-VIC and zero-result geocodes hard-fail (D-01, D-02), only partial_match/non-ROOFTOP warn.

### Integration Points
- §0.3 → §1.2: `SITE_CONFIG["address"]` replaces hardcoded `SITE_ADDRESS`; geocode quality checks run in §1.2 and deposit `site_lat`/`site_lon` + warnings into the run output.
- §0.3 → §2: `CRS_METRIC` constant replaces every `"EPSG:7855"` literal; `PEER_POSTCODES` (cleaned) flows into BASE_ASSUMPTIONS for §2/§3 peer fetches.
- §0.3 → §6: `n_gp_fte`/`n_allied_fte`/`floor_area_sqm` flow from SITE_CONFIG through BASE_ASSUMPTIONS (no §6 change).
- Phase 7 hand-off: §1.2 deposits the geocoded point + raw geocoder response (for P7's state address_component check); P6's bbox check is the coarse gate, P7's state check is the authoritative gate (D-05, D-06).

</code_context>

<deferred>
## Deferred Ideas

- **Exact VIC bounding box coordinates** — researcher/planner to confirm the canonical values from the EPSG:7899 registry entry or Land Victoria (~140.96–150.04°E, ~33.98–39.13°S). Not a Phase 6 user decision; a research lookup.
- **`location_type` acceptable values** — whether `RANGE_INTERPOLATED` is acceptable or also warns; researcher to confirm Google's taxonomy. Default: warn on anything non-ROOFTOP (D-03).
- **`catchment_pop_plausible_range` (80k–110k) generalisation** — currently calibrated for inner-Melbourne 3 km ring; for non-Abbotsford sites this range is wrong. Becomes site-relative in a later phase (likely Phase 7/8 when POA/SA3 derivation enables a site-relative plausibility band). Noted for roadmap; NOT Phase 6.
- **contextily basemap CRS under 7899** — contextily expects Web Mercator (EPSG:3857) tiles; the `to_crs` for display already converts to 3857, so 7899 adoption should not affect basemap fetching. Researcher to verify during planning.

</deferred>

---

*Phase: 06-site-config-restructure*
*Context gathered: 2026-07-08*
