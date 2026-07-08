# Pitfalls Research

**Domain:** Adding multi-site capability to an existing single-site healthcare feasibility notebook (v1.0 → v2.0 generalisation)
**Researched:** 2026-07-07
**Confidence:** HIGH (v1.0 codebase audited directly — notebook, validator, generators; MGA zone coverage and ABS POA/SA3 edge cases web-verified)

## Scope Note

This is a **v2.0-focused** pitfalls document. It covers mistakes specific to *generalising the existing v1.0 Abbotsford-hardcoded notebook* into a parameterised multi-site tool. The v1.0 pitfalls (CRS confusion, whole-postcode summing, ML theatre, billings-as-revenue, etc.) are already addressed in the shipped v1.0 system and are not repeated here unless they resurface in a new form during generalisation. See the v1.0 archive for those.

---

## Critical Pitfalls

### Pitfall 1: MGA zone 55 does NOT cover all of Victoria — western VIC spills into zone 54

**What goes wrong:**
PROJECT.md currently asserts "EPSG:7855 (MGA zone 55) stays valid for all VIC sites — no zone-awareness needed in v2.0." This is **false**. EPSG:7855 (GDA2020 / MGA zone 55) is defined for longitudes **144°E to 150°E**. Victoria's western border with South Australia is at **141°E**. The strip of VIC between 141°E and 144°E — encompassing Mildura, Nhill, Ouyen, Swan Hill (western portion), and surrounding rural postcodes (e.g. 3500, 3501, 3502, 2799, 3483, 3401) — falls in **MGA zone 54** (138°E–144°E, EPSG:7854), not zone 55.

A user entering a Mildura address (e.g. "15-17 Langtree Ave, Mildura VIC 3500") will have their geocoded point at ~142.16°E. Reprojecting this to EPSG:7855 doesn't crash — pyproj/PROJ will transform it — but the point lands ~3° outside the zone's defined extent and ~5° from the central meridian (147°E). The Transverse Mercator scale factor at 5° from the CM is approximately 1.0038, meaning a 0.38% distortion. For a 5 km buffer this is ~19 m of error; for area calculations the error compounds. The `assert_3km_buffer_km2 ≈ 28.27` sanity check will still pass approximately (28.27 × 1.0038 ≈ 28.38), so the assertion won't catch it — the error is silent.

**Why it happens:**
The v1.0 site (Abbotsford, ~145.0°E) sits comfortably inside zone 55, so the assumption was never tested. The milestone context even misidentifies the spill zone as "zone 53" — it's actually **zone 54**. The PROJECT.md decision was made looking at a Melbourne-centric map, not the full VIC bounding box.

**How to avoid:**
- **Option A (recommended for v2.0 VIC pilot):** Add a zone-selection guard at the geocoding step. After geocoding, check the site longitude: if `lon < 144.0`, use EPSG:7854 (zone 54); otherwise use EPSG:7855 (zone 55). This is a 3-line `if/else` — not "zone-aware reprojection" in the full sense (which v2.1 would need for national coverage with zones 49–56).
- **Option B (acceptable if documented):** Keep EPSG:7855 for all VIC sites but add a printed warning when `lon < 144.0` noting that buffer/area precision degrades by <0.5% at the western extremity. Given that catchment population apportionment at SA1 level tolerates far larger uncertainty than 0.4%, this is defensible for a pilot — but it must be a conscious, documented decision, not an accidental one.
- Either way, **update PROJECT.md** to replace the false "no zone-awareness needed" claim with the chosen approach and its caveat.

**Warning signs:**
- A VIC site geocodes to a longitude < 144.0 (check the geocoded point's coordinates in the output);
- Buffer area assertion passes but with a value slightly above 28.27 (e.g. 28.35+) — the distortion inflates the area;
- Easting values for the site point that are negative or unexpectedly small (< 100,000) — zone 55's false easting is 500,000; a zone-54 point reprojected to zone 55 can produce eastings well outside the normal 300,000–700,000 range.

**Phase to address:**
Phase 6 (site input + geocoding) — the zone check must live in the geocoding cell, immediately after the coordinates are obtained and before any buffer construction. If Option B is chosen, the warning cell goes here too.

---

### Pitfall 2: Hardcoded SA3 code (20607 Yarra) embedded in 8+ locations — parameterisation misses one

**What goes wrong:**
The v1.0 notebook hardcodes SA3 code **20607** (Yarra) in at least 8 distinct locations: the MBS SA3 loader filter (`df["SA3"].astype(str) == "20607"`), the AIHW age-band rate loader (`df["GeographicCode"].astype(str) == "20607"`), the assertion cell (`assert mbs_sa3_df["SA3"].astype(str).str.contains("20607").any()`), the ERP scaling cell (hardcoded SA2 code `206071139` within Yarra SA3), print statements, warning messages, and markdown commentary. The PROJECT.md and v1.0 PITFALLS.md even reference the *wrong* code (20604 — the ASGS 2016 code; Edition 3 renamed/reassigned it to 20607).

When generalising, the developer parameterises the obvious loader calls (replace `"20607"` with a `SA3_CODE` variable) but misses one of: (a) the assertion cell, (b) the ERP SA2 code (which is SA3-specific and can't be derived from SA3 alone — it's a 9-digit SA2 code), (c) a warning message string, or (d) the markdown commentary that says "SA3 20607 Yarra" literally. Any missed instance either crashes (assertion fails for a new SA3) or produces a report that says "Yarra" for a site in Frankston.

**Why it happens:**
The SA3 code appears in code cells, markdown cells, assertion cells, and string literals — a grep for `20607` returns 15+ matches across both code and prose. It's easy to parameterise the data-loading cells and miss the narrative/assertion cells. The SA2 code for ERP scaling is a separate, longer code that's easy to forget is SA3-specific.

**How to avoid:**
- Introduce a single `SA3_CODE` and `SA3_NAME` variable derived from the geocoded point (via point-in-polygon against the SA3 shapefile). Grep the entire notebook for `20607` and `20604` and replace every instance — code, assertions, markdown, print statements.
- The ERP SA2 code is harder: v1.0 uses a specific SA2 (`206071139`) to derive the growth rate. For a new site, you need the SA2 that contains the geocoded point, not the SA3's "primary" SA2. Derive this from point-in-polygon against SA2 boundaries, or fall back to the SA3-level ERP if SA2 data isn't available.
- Add a validator check that no literal `20607` or `20604` appears in the notebook source (only the variable name `SA3_CODE`).

**Warning signs:**
- A report for a non-Yarra site that mentions "Yarra" in the text;
- An assertion failure on `assert ... "20607" ...` when running against a new site;
- ERP scaling that produces a growth rate identical to Abbotsford's regardless of the site (the SA2 code wasn't parameterised).

**Phase to address:**
Phase 7 (SA3 auto-derivation) for the point-in-polygon + variable introduction; Phase 6 (site input) for the `SA3_CODE`/`SA3_NAME` variable scaffolding. A regression-check validator pass should be added in the final phase.

---

### Pitfall 3: SA3 derivation via point-in-polygon — boundary, water, and off-shore edge cases

**What goes wrong:**
v2.0 must derive the SA3 code from the geocoded point via a spatial join (`gpd.sjoin` or point-in-polygon) against the ASGS SA3 shapefile. Several edge cases produce silent failures or crashes:

1. **Point on an SA3 boundary:** Shapely's `intersects` vs `within` behave differently on boundaries. A point exactly on a shared SA3 boundary (e.g. a site on a major road that forms an SA3 border) may be assigned to the wrong SA3 or to both (with `intersects`) or neither (with `within`). The geocoded point's precision (6 decimal places ≈ 0.11 m) makes exact boundary hits rare but not impossible — Google's rooftop geocoding can snap to a property boundary.

2. **Point in water / no SA3:** The ASGS SA3 shapefile covers onshore Australia only. A geocoded point that lands in Port Phillip Bay, the Yarra River, or the ocean has no containing SA3. `gpd.sjoin` returns an empty result — the SA3 code is `None`, and every downstream cell that filters MBS/AIHW data by SA3 code silently returns empty dataframes.

3. **Geocoded point slightly off-shore:** Google Geocoding API can return a point a few metres into the bay for coastal addresses (e.g. a site on Beach Rd, Brighton). The point misses all SA3 polygons. This is more common than case 2 because geocoding precision near coastlines is degraded.

4. **SA3 boundaries that changed between ASGS editions:** The MBS SA3 Summary file uses ASGS Edition 3 (2021) SA3 codes. If the SA3 shapefile loaded for point-in-polygon is from a different ASGS edition (e.g. 2016), the codes won't match. ASGS Edition 3 changed some SA3 labels and SA2 codes (e.g. 206041122 "Melbourne" → 206041503 "Melbourne CBD - East"; 206071144 "Richmond (Vic.)" → 206071517 "Richmond (South) - Cremorne"). SA3 boundaries themselves had only "minor alignment changes" but the codes/labels shifted. The MBS file and the shapefile must be from the same ASGS edition.

**Why it happens:**
Point-in-polygon looks like a one-liner (`gpd.sjoin(gdf_points, sa3_gdf, how="left", predicate="within")`). The edge cases are all silent — no error, just empty or wrong results. The ASGS edition mismatch is invisible because both datasets use 5-digit numeric codes that *look* compatible.

**How to avoid:**
- Use `predicate="within"` (not `intersects`) for the spatial join — a point on a boundary gets assigned to exactly one SA3 (the one it falls within, with ties broken by shapefile order). Document this.
- After the join, **assert the SA3 code is not None**. If it is, fall back to a nearest-neighbor lookup (`sjoin_nearest`) with a printed warning that the site is in water/off-shore and the nearest SA3 is being used. Cap the nearest distance at ~2 km — if the nearest SA3 is further, the geocoded point is genuinely wrong (outside VIC, in the bay, etc.) and the run should fail with a clear error.
- Pin the SA3 shapefile to ASGS Edition 3 (2021) to match the MBS file's codes. Store the ASGS edition as a constant and print it in the output.
- For coastal sites, consider buffering the geocoded point by 50 m before the spatial join — this catches off-shore snaps without misassigning inland points.

**Warning signs:**
- `SA3_CODE` is `None` or `NaN` after the spatial join;
- MBS/AIHW dataframes empty after SA3 filtering (no rows match);
- A site in Brighton assigned to an SA3 on the other side of the bay;
- SA3 codes in the shapefile that don't exist in the MBS file (edition mismatch).

**Phase to address:**
Phase 7 (SA3 auto-derivation). The assertion + fallback logic must be in the same cell as the spatial join — not deferred to a "validation" phase.

---

### Pitfall 4: ABS Data API parameterised fetch — POA codes that don't exist, non-digit codes, and rate limiting

**What goes wrong:**
v1.0 fetches `C21_G01_POA` / `C21_G02_POA` / `C21_G04_POA` for a hardcoded list of 10 POA codes (3067 + 9 peers). v2.0 must fetch for arbitrary user-supplied POA codes. Several edge cases break:

1. **POA code doesn't exist in the 2021 Census:** ABS Postal Areas exclude non-street-delivery postcodes (PO boxes, large volume receivers, mail-back competitions). A user entering a PO-box-only postcode (e.g. some CBD postcodes) gets an empty response — HTTP 200 with zero data rows. The ABS API returns an empty CSV, not an error. Downstream code that expects at least one row crashes on `KeyError` or produces `NaN` demographics.

2. **Postcode abolished/created between ASGS editions:** ASGS Edition 3 (2021) POA codes "may not match those used in past editions" because postcodes are abolished, boundaries adjusted, or new postcodes created. A user entering a postcode that was created after the 2021 Census (e.g. a new suburban development) won't find it in the 2021 data. Conversely, a postcode that existed in 2016 but was abolished by 2021 won't appear.

3. **4-digit vs 3-digit POA codes:** All ABS POA codes are 4-digit strings matching Australia Post postcodes. But some VIC postcodes have leading zeros in their ABS representation (none in VIC currently, but the API returns POA_CODE21 as a string — if the user enters an integer `3067` instead of string `"3067"`, the join fails silently). The v1.0 notebook stores `PEER_POSTCODES` as strings — but a form input might return integers.

4. **Rate limiting on multi-POA fetches:** v1.0 fetches all 10 peer POAs in a single API call using the SDMX `+` OR operator (`"3067+3066+3068+..."`). The ABS API enforces a **30-second timeout and 10 MB response cap**. For G01/G02 (small tables), 10 POAs is fine. But if a user enters many peer postcodes (20+), or if G04 (age by sex — larger) is fetched for many POAs, the response can exceed 10 MB or timeout. The API returns a 504, which `requests-cache` may cache as the error response — poisoning the cache for subsequent runs.

5. **Special-purpose POA codes:** ABS includes 3 non-spatial special purpose codes (including "Outside Australia"). If a user somehow enters one of these, the demographics are meaningless.

**Why it happens:**
The v1.0 fetch works because 3067 and its 9 peers are all valid, existing, 4-digit VIC POA codes. The developer assumes all user inputs will be equally well-behaved. The SDMX `+` operator makes multi-POA fetches look identical to single-POA fetches, hiding the scaling risk.

**How to avoid:**
- Validate user-supplied postcodes against the loaded POA shapefile *before* any API call. If a postcode isn't in the shapefile, print a warning and skip it (don't crash). The shapefile is already loaded for catchment apportionment — reuse it.
- Always store/compare POA codes as **zero-padded 4-digit strings**. Convert form inputs: `str(int(postcode)).zfill(4)` or just `str(postcode).strip().zfill(4)`.
- Cap peer postcode count at a reasonable limit (e.g. 15) and split API calls into batches if exceeded. For G04 (larger table), consider fetching per-POA in a loop with caching rather than one giant `+` query.
- After each API fetch, **assert the response dataframe has at least one row**. If empty, print a warning naming the POA code and fall back to the GCP local file (if it covers that POA) or mark demographics as "unavailable" in the peer table.
- Configure `requests-cache` to **not cache error responses** (set `cache_control=False` and use `allowable_codes=(200,)` so 504s/500s aren't cached).

**Warning signs:**
- Empty dataframes after ABS API fetch (HTTP 200 but zero rows);
- `KeyError` on column names when building the peer table (one POA returned no data, its row is missing);
- 504 responses in the cache directory (check `data/cache/` for response files with 504 status);
- Peer table with `NaN`/`None` values for some postcodes.

**Phase to address:**
Phase 8 (ABS API parameterised fetch) for the validation + batching logic; Phase 6 (site input) for the postcode type-normalisation (string, zero-padded).

---

### Pitfall 5: Geocoding arbitrary VIC addresses — ambiguous, centroid, rural, and out-of-state results

**What goes wrong:**
v1.0 geocodes one known address ("292-296 Johnston St, Abbotsford VIC 3067") and verifies it visually. v2.0 must geocode arbitrary user-supplied VIC addresses. Google Geocoding API edge cases:

1. **Ambiguous addresses:** "123 Main St, VIC 3000" may match multiple locations. Google returns the best match but `partial_match: true` in the response. v1.0 doesn't check `partial_match` — it trusts the first result. For a user who typos their address, the geocoded point could be kilometres away, producing a completely wrong catchment/SA3/competitor set.

2. **Centroid instead of rooftop:** Google returns `location_type: "ROOFTOP"`, `"RANGE_INTERPOLATED"`, `"GEOMETRIC_CENTER"`, or `"APPROXIMATE"`. A rural address with no street number (e.g. "Smiths Rd, Yea VIC 3717") geocodes to `APPROXIMATE` or `GEOMETRIC_CENTER` — the centroid of the road, not the property. For a 1 km catchment this shifts the entire catchment by hundreds of metres.

3. **Rural VIC addresses with no street number:** Common in rural VIC — addresses like "Springvale Rd, Traralgon VIC 3844" with no number. Google returns a road centroid. The catchment may not contain the actual site. This is less of a problem for 3/5 km catchments but material for the 1 km ring.

4. **Addresses that geocode outside VIC:** A user enters "1 Smith St, Richmond" (forgetting VIC). Google may return Richmond, NSW or Richmond, QLD. The site point is outside VIC, the POA shapefile (filtered to VIC postcode prefix `3`, i.e. 3000-3999) has no containing polygon, and the entire pipeline produces empty results. Or worse: the point is just across the border in NSW but near a VIC postcode, and the pipeline runs with subtly wrong data. Note: the POA shapefile carries no `STE_NAME21` column (only SA1 does), so VIC filtering uses postcode prefix, not a state-name attribute.

5. **Address format variations:** Users enter addresses in many formats: "292 Johnston St" vs "292-296 Johnston St" vs "292-296 Johnston Street". Google handles most of these, but the geocoded point can differ by 10-50 m between formulations, which matters for the 1 km catchment.

**Why it happens:**
v1.0 has exactly one address, verified once, cached forever. The geocoding cell has a visual verification step but no programmatic checks on result quality. Generalising to arbitrary inputs means trusting the geocoder for addresses the developer has never seen.

**How to avoid:**
- After geocoding, check `response["results"][0].get("partial_match")` — if `true`, print a warning and ask the user to verify the address (in a notebook context, this means a prominent warning cell with the geocoded coordinates and a map).
- Check `location_type` — if it's `"APPROXIMATE"` or `"GEOMETRIC_CENTER"`, print a warning that the catchment may be centred on a road centroid, not the exact property.
- **Assert the geocoded point is within VIC** by doing a point-in-polygon against the VIC boundary (or simply check `lat` is in [-39.2, -33.9] and `lon` is in [141.0, 150.0]). If outside, fail with a clear error: "Geocoded point appears to be outside Victoria. Please check the address."
- Always display the geocoded point on a map immediately after geocoding, with the address as a popup, so the user can visually verify before the pipeline proceeds.
- Cache the geocoded result keyed by the normalised address string (lowercase, stripped, postcode appended) so re-runs are free.

**Warning signs:**
- `partial_match: true` in the geocode response (not checked in v1.0);
- `location_type` other than `"ROOFTOP"`;
- Geocoded coordinates outside the VIC bounding box;
- Catchment population that looks wrong for the expected area (too high = geocoded to a city centre; too low = geocoded to a rural area).

**Phase to address:**
Phase 6 (site input + geocoding). All checks must be in the geocoding cell — before any downstream cell uses the coordinates.

---

### Pitfall 6: Peer postcode validation — non-VIC, non-existent, and self-referential peers

**What goes wrong:**
v1.0 hardcodes 10 peer postcodes, all valid inner-Melbourne VIC POAs. v2.0 lets the user enter peer postcodes (optional). Three failure modes:

1. **Non-VIC postcode:** User enters a NSW postcode (e.g. 2000). The ABS API returns data (Census covers all of Australia), but the peer comparison is meaningless — comparing a VIC clinic site to Sydney demographics. The POA shapefile is filtered to VIC, so the peer postcode's polygon won't be found, but the API fetch still succeeds, creating an inconsistent state (demographics exist, geometry doesn't).

2. **Postcode doesn't exist in 2021 Census:** User enters a postcode that's a PO-box-only code or was created after 2021. ABS API returns empty. Peer table shows `NaN` for that peer. Not a crash, but the report has gaps.

3. **User enters the site's own postcode as a peer:** The site POA is already in the peer table (v1.0 includes 3067 in `PEER_POSTCODES` and marks it with `is_site=True`). If the user enters the site postcode as a peer too, it appears twice — once as the site, once as a peer. The `is_site` flag only marks the first occurrence (or the last, depending on merge order), and the peer comparison chart has a duplicate data point.

**Why it happens:**
v1.0's peer list was curated by the developer and known-good. User-supplied peers have no such guarantee. The notebook has no validation step for peer postcodes — it passes them straight to the API and the shapefile filter.

**How to avoid:**
- Validate each peer postcode: (a) exists in the POA shapefile (which is already filtered to VIC); (b) is not the site's own postcode. Print a warning for each rejected peer and skip it.
- Deduplicate the peer list (including removing the site postcode if the user included it).
- If no valid peers remain after validation, skip the peer comparison section entirely with a printed notice (don't crash on empty peer table).
- Consider auto-suggesting peers: for a new site, find the N nearest POAs by centroid distance. This is a v2.1 feature but worth noting — it eliminates all three failure modes.

**Warning signs:**
- Peer table with `NaN` rows;
- Peer postcodes that don't appear on the catchment map (geometry missing);
- Duplicate site postcode in the peer table;
- Peer comparison charts with fewer data points than the user entered.

**Phase to address:**
Phase 6 (site input) for the validation logic; Phase 8 (peer benchmarking) for the graceful-skip-on-empty behaviour.

---

### Pitfall 7: Report filename slugification — special characters, long addresses, and duplicate filenames

**What goes wrong:**
v1.0 writes the report to a hardcoded filename: `outputs/Johnston_St_v2_Executive_Report.html` (and `.pdf`). v2.0 must name the report after the site. Slugifying arbitrary VIC addresses produces several issues:

1. **Special characters in street names:** "St" (Street), "Rd" (Road), "Ct" (Court), "Pl" (Place), "Cres" (Crescent) are fine, but addresses contain hyphens ("292-296 Johnston St"), slashes ("1/3 Smith St"), and apostrophes (rare in VIC but possible in some road names). A naive `address.replace(" ", "_")` produces `292-296_Johnston_St` which is fine, but `1/3_Smith_St` has a slash — invalid in Windows filenames.

2. **Very long addresses:** "123-127 Victoria Parade, East Melbourne VIC 3002" slugifies to a long filename. Windows has a 260-character path limit; Colab/Linux has 255-byte filename limit. With the `outputs/` prefix and `_Executive_Report.html` suffix, a long address can exceed this.

3. **Duplicate filenames across runs:** Two different sites on "Johnston St" in different suburbs (e.g. "100 Johnston St, Fitzroy VIC 3065" and "100 Johnston St, Bentleigh VIC 3204") both slugify to `100_Johnston_St` — the second run overwrites the first's report. v1.0 doesn't have this problem because there's only one site.

4. **Addresses with no street name:** Rural addresses ("Smiths Rd, Yea VIC 3717") slugify fine, but a property-name-only address ("The Grange, Ballarat VIC 3350") produces `The_Grange` — not very identifying.

**Why it happens:**
v1.0 never slugifies — the filename is a constant. Slugification is a new v2.0 concern that's easy to get wrong because edge cases in address formatting are numerous.

**How to avoid:**
- Use a slugify function that: (a) lowercases, (b) replaces non-alphanumeric with underscores, (c) collapses consecutive underscores, (d) truncates to 60 characters, (e) appends the postcode for uniqueness (e.g. `292_296_johnston_st_3067`). The postcode suffix eliminates most collision risk.
- For full uniqueness, append a date stamp or short hash: `292_296_johnston_st_3067_20260707.html`. This guarantees no overwrites across runs.
- Test the slugify function against a battery of VIC addresses including hyphens, slashes, rural addresses, and very long street names.

**Warning signs:**
- `OSError` or `FileNotFoundError` when writing the report (invalid characters in filename);
- Report files being silently overwritten (same filename for different sites);
- Filenames that are too long to display in the Colab file browser.

**Phase to address:**
Phase 9 (report generation) — the slugify function and filename construction live in the §8.3/§8.4 report cells.

---

### Pitfall 8: Pharmacy synergy removal breaks the verdict cell, assumptions register, and citations

**What goes wrong:**
v2.0 drops the pharmacy synergy section (§7.6). But the v1.0 notebook weaves pharmacy references through multiple cells that are NOT in §7.6:

1. **Jinja2 template (§8.3):** The HTML template has a dedicated "6. Pharmacy Synergy" section (`<h2>6. Pharmacy Synergy — Secondary Upside (NOT Load-Bearing)</h2>`) that references `report['pharmacy_synergy_range']`. If §7.6 is removed but the template still references `pharmacy_synergy_range`, the Jinja2 render crashes with `UndefinedError`.

2. **Assumptions register (§8.2):** The register parser skips `site_address`, `catchment_radii_m`, and `peer_postcodes` (line 3489: `if not m or m.group(1) in ("site_address", "catchment_radii_m", "peer_postcodes")`). If pharmacy-related parameters were added to `BASE_ASSUMPTIONS` (they weren't in v1.0 — the synergy calculation uses local variables, not `BASE_ASSUMPTIONS`), they'd appear in the register as orphaned rows.

3. **Citations (§8.3):** Citation `[6]` is "PBS Statistics 2023-24 — scripts/person/yr benchmark" — used only by the pharmacy synergy calculation. Removing §7.6 leaves a dangling citation `[6]` in the template's Data Sources section. The validator (REP-04) checks that citations `[1]`-`[8]` all exist — removing `[6]` breaks the validator.

4. **`report{}` accumulator:** §7.6 deposits `report["pharmacy_synergy_range"]`. The template references it. If the deposit is removed but the template reference remains (or vice versa), the render fails.

5. **Verdict cell (§8.1):** The verdict text is already 100% standalone (D-04) — it never mentions pharmacy. This is safe. But the validator's REP-02 check verifies that the verdict_text block doesn't contain "pharmac" or "priceline" — this check remains valid and should be kept.

**Why it happens:**
Pharmacy synergy was designed as "NOT load-bearing" and "order-gated after the verdict" — it's architecturally separate. This creates a false sense that it can be cleanly removed. But the report template, citations, and `report{}` accumulator create hidden dependencies. The developer removes the §7.6 code cell and thinks they're done.

**How to avoid:**
- Remove pharmacy synergy as a **coordinated change across 4 locations**: (a) §7.6 code cell, (b) §7.6 markdown cell, (c) Jinja2 template section 6, (d) citation `[6]` in the Data Sources section. Also renumber citations `[7]`-`[8]` to `[6]`-`[7]` (or keep the numbering and just remove `[6]` — but the validator checks `[1]`-`[8]` all exist, so the validator must be updated too).
- Update the validator: REP-03 checks for "Pharmacy Synergy" in the template's 8 sections — this must be removed from the section list. REP-04 checks `[1]`-`[8]` — update to `[1]`-`[7]`. FIN-07 (pharmacy synergy order-gated) should be removed entirely.
- Grep the entire notebook for `synergy`, `pharmacy_synergy`, `capture_rates`, `pharmac`, and `PBS` after removal — every hit must be either deleted or explicitly justified.
- The v1.0 reproduction requirement (default Abbotsford config produces the same report minus pharmacy synergy) means the verdict, financial model, and demand model outputs must be **byte-identical or semantically-identical** to v1.0. Only the pharmacy synergy section should be absent.

**Warning signs:**
- `jinja2.exceptions.UndefinedError: 'pharmacy_synergy_range'` when rendering the report;
- Validator REP-03 failure ("missing Pharmacy Synergy section");
- Validator REP-04 failure ("missing citation [6]");
- Dangling `report["pharmacy_synergy_range"]` deposit with no template consumer (or vice versa).

**Phase to address:**
Phase 9 (report generation) for the template/citation removal; the validator update should be in the same phase. The §7.6 code/markdown removal can happen earlier (Phase 9 or a dedicated cleanup step).

---

### Pitfall 9: Validator's 36 hardcoded checks assume Abbotsford — running against a different site fails

**What goes wrong:**
The v1.0 validator (`scripts/validate_v2_notebook.py`) has 36 checks, many of which assert the presence of Abbotsford-specific literal strings in the notebook source. When the notebook is generalised, these literals are replaced with variables, and the validator fails. Specific hardcoded assertions:

| Check | Hardcoded literal | What breaks |
|-------|-------------------|-------------|
| GEO-04 | `"Yarra"` in all_source | Maps markdown mentions "Yarra" — a non-Yarra site won't have this |
| DEMO-01 | `"GCP_POA3067"` in all_source | Fallback filename is Abbotsford-specific |
| DEMO-01 | `"parse_gcp_g01_to_tidy"` | Fallback parser is Abbotsford-specific |
| DEMO-03 | `"Total_P_P"`, `"Median_age_persons"`, `"pct_65plus"` | Column names — these are generic, safe |
| DEMO-04 | `"ABS_ANNUAL_ERP_ASGS2021"` | Flow ID — generic, safe |
| DEMAND-01 | `"20607"` in all_source | SA3 code — must be parameterised |
| DEMAND-01 | `"STATE BENCHMARK, NOT LOCAL"` | Warning text — generic, safe |
| COMP-03 | `"117"` in all_source | GP-per-100k benchmark — generic, safe |
| REP-03 | `"Pharmacy Synergy"` in template sections | Must be removed (see Pitfall 8) |
| REP-04 | `[1]`-`[8]` all present | Citation count changes if pharmacy removed |
| FIN-07 | `"§7.6 Pharmacy synergy"` cell exists | Must be removed |

The validator also checks for `"292-296 Johnston St"` indirectly (the assumptions register parser skips `"site_address"`, and the geocode cell references `SITE_ADDRESS`). The `assert_3km_buffer_km2` value (28.27) is generic but the buffer area assertion will fail for zone 54 sites (see Pitfall 1).

**Why it happens:**
The validator was written to verify the v1.0 notebook's specific content, not to be site-agnostic. Each check was added to verify a specific requirement was met *for Abbotsford*. Generalising the notebook without generalising the validator creates a false failure wall.

**How to avoid:**
- **Parameterise or skip site-specific assertions:** For each check that asserts a site-specific literal, either (a) replace it with a check for the *variable* that now holds the value (e.g. check `"SA3_CODE"` exists instead of `"20607"`), or (b) skip it when the site is not Abbotsford (add a `SITE_CONFIG == "abbotsford"` mode), or (c) remove it if the requirement it verified is now met by a more general check.
- **Add a v2.0 validator mode:** The validator should accept a `--site` argument (default: `abbotsford`) and run site-specific checks only when `--site abbotsford`. For other sites, it runs the generalised checks (structure, dual-environment, caching, no-ML, service-fee model, etc.).
- **Keep the v1.0 reproduction check:** When `--site abbotsford`, the validator should verify the notebook still reproduces v1.0 (all 36 original checks pass, minus pharmacy synergy). This is the v1.0 reproduction requirement.
- **Update the byte-stable generator check:** The generators produce the notebook from Python scripts. If the generators start embedding site-specific values (e.g. the SA3 code from a config file), the byte-stable output assumption breaks — running the generator twice with different configs produces different notebooks. The generator must either (a) always produce the default Abbotsford config (and the user overrides at runtime via the form), or (b) accept a config argument and the byte-stability is per-config.

**Warning signs:**
- Validator fails with "GEO-04: missing Yarra" for a non-Yarra site;
- Validator fails with "DEMAND-01: missing 20607" after parameterising SA3;
- Validator fails with "REP-03: missing Pharmacy Synergy" after removing the section;
- Generator produces different notebook output on re-run (byte-stability broken).

**Phase to address:**
Phase 10 (validator + generator update) — a dedicated phase for updating the validation and generation tooling to be site-agnostic. This must happen *after* the notebook is generalised (Phases 6-9) but *before* the milestone ships.

---

### Pitfall 10: Generator scripts' byte-stable output assumption breaks with site-specific values

**What goes wrong:**
The 5 generator scripts (`create_v2_notebook.py`, `extend_v2_notebook_*.py`) produce the notebook by appending cell dicts with hardcoded source strings. They are idempotent — re-running produces a byte-identical notebook. v2.0 generalisation risks breaking this:

1. **Embedding site-specific values in generators:** If a generator is modified to embed the site address, SA3 code, or peer postcodes directly into the cell source (instead of using variables that are set at runtime), the generator's output depends on the site config. Re-running with a different config produces a different notebook — byte-stability is per-config, not absolute.

2. **Generator assumptions about cell structure:** The generators assume specific marker strings (e.g. `"# §7 Scenarios & Sensitivity"`) to find and replace sections. If the site input form changes the §0 cell structure, the Phase 1 generator's idempotency check (which looks for `"BASE_ASSUMPTIONS = {"`) may fail to find the cell.

3. **Generator order dependencies:** The generators must run in order (create → extend_phase2 → extend_phase3 → extend_phase4 → extend_phase5). If v2.0 adds a new generator (e.g. `extend_v2_notebook_phase6.py` for the site input form), it must be inserted at the right position, and all downstream generators must still find their markers.

**Why it happens:**
The generators were designed for a single-site notebook where the content is fixed. Byte-stability means "re-running the generator produces the same notebook" — which is true when the content doesn't change. v2.0 makes the content site-dependent, breaking the assumption.

**How to avoid:**
- **Keep site-specific values out of the generators.** The generators should always produce the default Abbotsford config. Site-specific values (address, SA3, peers) should be runtime form inputs that override the defaults — not embedded in the notebook source by the generator.
- The `BASE_ASSUMPTIONS` cell should contain `SITE_ADDRESS = "292-296 Johnston St, Abbotsford VIC 3067"` as the *default*, with a form cell above it that overrides `SITE_ADDRESS` when the user enters a different address. The generator always produces the Abbotsford default; the form provides the override.
- If a new generator is needed for v2.0, add it as `extend_v2_notebook_phase6.py` (or similar) and ensure it runs before the existing generators' markers are affected.
- Verify byte-stability by running the full generator chain twice and `diff`-ing the output — they must be identical.

**Warning signs:**
- `diff` between two generator runs shows differences;
- Generator fails to find its marker string after a new generator modifies the cell structure;
- Notebook contains a non-Abbotsford address after a fresh generator run (site-specific value leaked into the generator).

**Phase to address:**
Phase 10 (validator + generator update). The "site-specific values stay out of generators" principle should be established as a convention before any generator is modified.

---

### Pitfall 11: v1.0 reproduction — default Abbotsford config must produce a semantically-identical report

**What goes wrong:**
v2.0 must reproduce the v1.0 Abbotsford study when the default config is used (minus pharmacy synergy). Several subtle differences can creep in:

1. **SA3 code change:** v1.0 uses SA3 20607 (Yarra). If v2.0's SA3 auto-derivation assigns a different SA3 code to the same Abbotsford point (e.g. due to a shapefile edition mismatch — see Pitfall 3), the MBS/AIHW data changes, the demand model changes, and the verdict may flip.

2. **ERP scaling SA2 code:** v1.0 uses SA2 `206071139` for the ERP growth rate. If v2.0 derives the SA2 from point-in-polygon and gets a different SA2 (e.g. because the point falls in an adjacent SA2 due to boundary alignment changes), the growth rate changes, the catchment population changes, and downstream numbers shift.

3. **Geocoded point drift:** v1.0 caches the geocoded coordinates for the Abbotsford address. If v2.0 re-geocodes the same address and Google returns slightly different coordinates (Google updates its geocoding database), the catchment shifts slightly, the SA1 apportionment changes, and the population numbers differ by a few percent.

4. **Peer postcode list:** v1.0 hardcodes 10 peers. If v2.0's default config has a different peer list (or the user form overrides it with an empty list), the peer comparison changes.

5. **Pharmacy synergy removal:** The report should be identical to v1.0 *minus* the pharmacy synergy section. But if the removal also changes the citation numbering (see Pitfall 8), the Data Sources section differs, and the assumptions register may lose rows that were previously derived from pharmacy-related parameters.

6. **Report filename:** v1.0 writes `Johnston_St_v2_Executive_Report.html`. v2.0 with slugification writes `292_296_johnston_st_3067_20260707.html` (or similar). The filename is different — this is expected, but any v1.0 reproduction check that compares filenames will fail.

**Why it happens:**
Generalisation changes the code path even for the default config. The SA3 derivation, geocoding, and ERP scaling all go through new logic that *should* produce the same result for Abbotsford but might not due to edge cases in the new code.

**How to avoid:**
- **Add a v1.0 reproduction test:** Run v2.0 with the default Abbotsford config and compare key outputs to v1.0: catchment population (within 1% — allow for geocoding drift), SA3 code (must be 20607), MBS utilisation rate, demand model output, clinic P&L base case, verdict (must be GO), and the 5 key numbers. Document acceptable tolerances.
- Pin the geocoded coordinates for Abbotsford as a cached/verified constant (v1.0 already does this). Don't re-geocode on every run — use the cache.
- Pin the SA3 shapefile to ASGS Edition 3 (2021) so the SA3 derivation is deterministic.
- The report content (verdict text, financial tables, demand model) should be semantically identical. The filename and the absence of the pharmacy synergy section are the only expected differences.
- Run the v1.0 validator (36 checks) against the v2.0 notebook with default config — all checks that aren't pharmacy-related should still pass.

**Warning signs:**
- v2.0 default config produces a different SA3 code than 20607;
- Catchment population differs by >1% from v1.0;
- Verdict flips from GO to NO-GO (or vice versa) for the same site;
- Clinic P&L base-case EBITDA differs by >5% from v1.0;
- Assumptions register has fewer rows than v1.0 (parameters lost in generalisation).

**Phase to address:**
Phase 11 (v1.0 reproduction verification) — the final phase before milestone close. This is a dedicated verification pass, not a development phase.

---

### Pitfall 12: Census vintage — ERP scaling factor for new sites may differ materially from Abbotsford's

**What goes wrong:**
v1.0 applies an ERP scaling factor derived from the Yarra SA2 growth rate (2021 → 2024). Abbotsford/Yarra is a high-growth inner-Melbourne area with significant apartment development. For a new site in a different part of VIC, the growth rate can be dramatically different:

- **High-growth fringe suburbs** (e.g. Craigieburn, Clyde): growth rates of 5-8% per year — the 2021 Census population understates 2024 reality by 15-25%.
- **Stable/declining regional areas** (e.g. some rural VIC towns): growth rates near 0% or negative — the 2021 Census is close to current reality.
- **Different SA2 → different growth rate:** v1.0 uses one SA2's growth rate. For a new site, the SA2 is different, and the ERP data may not be available at SA2 level for all areas (ABS releases ERP by SA2 annually, but some SA2s have suppressed data due to small populations).

If v2.0 applies Abbotsford's growth rate to a different site (because the SA2 code wasn't parameterised — see Pitfall 2), the catchment population is wrong by 10-25%. If it derives the correct SA2's growth rate but the data is suppressed, it falls back to... what? v1.0 has no fallback for ERP suppression.

**Why it happens:**
The ERP scaling was built for one SA2. Generalising it requires handling the full range of VIC growth rates and data availability. The ABS ERP release (3218.0) doesn't cover every SA2 with equal reliability.

**How to avoid:**
- Derive the SA2 code from the geocoded point (point-in-polygon against SA2 boundaries) — don't reuse Abbotsford's SA2 code.
- Fetch the ERP growth rate for the site's SA2. If the data is suppressed or unavailable, fall back to the SA3-level or SA4-level growth rate with a printed warning. If no ERP data is available at any level, fall back to the state-wide VIC growth rate (~1.5-2% per year) with a prominent warning.
- Print the growth rate used and its source (SA2/SA3/SA4/state) in the output so the user can sanity-check it.
- For the v1.0 reproduction check, the Abbotsford SA2 growth rate must match v1.0's value.

**Warning signs:**
- ERP growth rate identical across different sites (SA2 code not parameterised);
- Catchment population for a high-growth fringe suburb that's close to 2021 Census values (growth not applied);
- `KeyError` or empty dataframe when fetching ERP for a regional SA2 (data suppressed);
- No warning printed when falling back to a coarser geography.

**Phase to address:**
Phase 7 (SA3 auto-derivation) for the SA2 point-in-polygon; Phase 8 (ABS API parameterised fetch) for the ERP data fetch with fallback logic.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Keep EPSG:7855 for all VIC sites (no zone check) | No zone-selection logic; simpler code | <0.5% area distortion for western VIC; silent precision degradation | Acceptable for v2.0 pilot IF documented with a printed warning for `lon < 144.0`; must fix in v2.1 |
| Hardcode Abbotsford SA3/SA2 codes as defaults, override at runtime | Generator byte-stability preserved; v1.0 reproduction trivial | Two code paths (default vs. override) can diverge; easy to forget to test the override path | Acceptable — this is the intended v2.0 design (default config + form override) |
| Skip peer comparison when no valid peers provided | No crash on empty peer table | Report is thinner; user may not realise their peers were all invalid | Acceptable for v2.0 — print a warning; auto-suggest peers in v2.1 |
| Use nearest-neighbor SA3 fallback for water/off-shore points | No crash on edge-case geocoding | Wrong SA3 for coastal sites; demand model uses wrong MBS data | Acceptable as a fallback with a printed warning; cap distance at 2 km |
| Re-geocode the default Abbotsford address on each run | No cached coordinates to manage | Geocoded point may drift between Google API updates; v1.0 reproduction may fail | Never for the default config — use the cached/verified coordinates. Acceptable for new user-entered addresses. |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Google Geocoding API | Trusting the first result without checking `partial_match` or `location_type` | Check both; warn on `partial_match=true` and non-`ROOFTOP` results; assert point is within VIC bounding box |
| Google Geocoding API | Not handling ambiguous addresses (multiple matches) | Use the first result but display it on a map for visual verification; warn if `partial_match` |
| ABS Data API (POA fetch) | Passing user-entered postcodes as integers instead of zero-padded strings | Normalise: `str(code).strip().zfill(4)`; validate against POA shapefile before API call |
| ABS Data API (POA fetch) | Caching 504/500 error responses | Set `allowable_codes=(200,)` in `CachedSession` so errors aren't cached |
| ABS Data API (multi-POA) | One giant `+` query for 20+ POAs that times out | Batch in groups of 10; use per-POA loop for G04 (larger table) |
| ABS ERP (3218.0) | Assuming SA2-level data exists for all VIC SA2s | Handle suppression: fall back to SA3/SA4/state with warning |
| ASGS SA3 shapefile | Using a different ASGS edition than the MBS file | Pin both to ASGS Edition 3 (2021); store edition as a constant |
| MBS SA3 Summary | Assuming SA3 codes are stable across editions | They're not — 20604 (2016) ≠ 20607 (Edition 3). Verify the code via the shapefile, not PROJECT.md |
| Jinja2 template | Removing §7.6 code but leaving `report['pharmacy_synergy_range']` in template | Remove template section + citation + `report{}` deposit in one coordinated change |
| Validator | Running v1.0 checks against a generalised notebook without updating assertions | Parameterise or skip site-specific checks; add `--site` mode |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| ABS API multi-POA query for 20+ peers | 504 timeout; 10 MB cap hit | Batch in groups of 10; per-POA loop for G04 | >15 peer postcodes, especially with G04 |
| Point-in-polygon against full national SA3 shapefile | Slow cell (30+ seconds); Colab RAM pressure | Filter SA3 shapefile to VIC before the spatial join | Every fresh runtime with national shapefile |
| Re-geocoding on every run instead of using cache | API cost; slow re-runs; coordinate drift | Cache geocoded result keyed by normalised address; use cache for default Abbotsford config | 3rd+ re-run of the notebook |
| Loading full national POA shapefile for peer validation | 1-2 min cell, RAM pressure | Filter to VIC once, save filtered version in cache | Every fresh runtime |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| User-entered address appearing in report filename without sanitisation | Path traversal (`../../etc/`) in filename on Windows | Slugify: lowercase, non-alphanumeric → underscore, truncate, append postcode |
| Geocoded coordinates of a private address committed to git | Privacy leak if the notebook is shared with outputs | Strip outputs before commit; cache geocoded results in `.gitignore`'d `data/cache/` |
| User-supplied peer postcodes logged in plaintext in the report | Minor PII (postcode-level) — acceptable for investor report but don't commit to git | Keep peer postcodes in `BASE_ASSUMPTIONS` (config), not in committed outputs |

## UX Pitfalls

(Here "users" = the analyst running the notebook with a new site address.)

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No validation feedback when user enters an invalid postcode | Pipeline runs with empty data; user sees `NaN` everywhere and doesn't know why | Validate postcodes against POA shapefile immediately after form submission; print named warnings for each rejected postcode |
| Geocoded point not shown on a map before the pipeline proceeds | User can't tell if the geocoder found the right location | Display the geocoded point on a folium map immediately after geocoding, with the address as popup |
| SA3 name not printed after auto-derivation | User doesn't know which SA3's MBS data is being used | Print "SA3: {code} {name} (derived from geocoded point)" prominently |
| Report filename doesn't include the postcode | User can't distinguish reports for same-named streets in different suburbs | Slugify with postcode suffix: `292_296_johnston_st_3067` |
| No warning when site is in western VIC (zone 54) | User doesn't know buffer precision is slightly degraded | Print warning if `lon < 144.0` (if keeping EPSG:7855 for all VIC) |
| Pharmacy synergy section removed without explanation | v1.0 users expect it and wonder where it went | Add a note in the report or notebook: "Pharmacy synergy analysis removed in v2.0 — clinic verdict is 100% standalone" |

## "Looks Done But Isn't" Checklist

- [ ] **SA3 derivation:** Often missing boundary/water edge-case handling — verify `SA3_CODE` is not `None` after spatial join; verify nearest-neighbor fallback exists with distance cap
- [ ] **MGA zone coverage:** Often assumed zone 55 covers all VIC — verify a `lon < 144.0` check exists (or the limitation is documented); test with a Mildura address
- [ ] **POA validation:** Often missing pre-API validation — verify user postcodes are checked against the POA shapefile before any API call
- [ ] **Geocode quality:** Often missing `partial_match`/`location_type` checks — verify both are checked and warnings printed
- [ ] **Pharmacy synergy removal:** Often partially done — verify ALL of: §7.6 code cell, §7.6 markdown, Jinja2 template section 6, citation [6], `report["pharmacy_synergy_range"]` deposit, and validator checks FIN-07/REP-03/REP-04 are updated
- [ ] **Validator generalisation:** Often only notebook is generalised — verify validator doesn't assert `20607`, `Yarra`, `GCP_POA3067`, or `Pharmacy Synergy` as hardcoded literals
- [ ] **Generator byte-stability:** Often broken by embedding site values — verify generator output is byte-identical across two runs with default config
- [ ] **v1.0 reproduction:** Often not tested — verify default Abbotsford config produces SA3 20607, same catchment pop (±1%), same verdict, same P&L base case (±5%)
- [ ] **ERP scaling:** Often uses Abbotsford's SA2 growth rate for all sites — verify SA2 code is derived from the geocoded point, not hardcoded
- [ ] **Report filename:** Often still hardcoded to `Johnston_St_v2_Executive_Report` — verify filename is slugified from the site address
- [ ] **Citation numbering:** Often has dangling [6] after pharmacy removal — verify citations are renumbered or the validator's `[1]-[8]` check is updated to `[1]-[7]`

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| MGA zone 55 used for western VIC site | LOW | Add `lon < 144.0` check → use EPSG:7854; re-run the affected site. Buffer/area numbers change by <0.5% |
| SA3 code not parameterised (missed instance) | LOW | Grep for `20607`/`20604`, replace with `SA3_CODE` variable; re-run |
| SA3 derivation returns None for water point | LOW | Add nearest-neighbor fallback with distance cap; re-run |
| POA code doesn't exist in Census (empty API response) | LOW | Add pre-API validation against shapefile; skip invalid POA with warning; re-run |
| Pharmacy synergy partially removed (template crash) | MEDIUM | Remove template section + citation + report{} deposit in one pass; update validator; re-run report generation |
| Validator fails on generalised notebook | MEDIUM | Parameterise or skip site-specific checks; add `--site` mode; re-run validator |
| Generator byte-stability broken | MEDIUM | Remove site-specific values from generator; keep them as runtime form overrides; re-run generator chain twice and diff |
| v1.0 reproduction fails (different SA3/population/verdict) | MEDIUM-HIGH | Debug SA3 derivation (shapefile edition?), ERP SA2 code, geocoded point drift; fix and re-verify against v1.0 outputs |
| ERP scaling uses wrong SA2 growth rate | LOW | Derive SA2 from point-in-polygon; fetch correct ERP data; re-run demand model |
| Report filename collision overwrites previous run | LOW | Add postcode + date stamp to slugify; re-run |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| MGA zone 55 coverage (Pitfall 1) | Phase 6 (site input + geocoding) | Zone check exists; test with Mildura address (lon < 144.0) |
| Hardcoded SA3 code (Pitfall 2) | Phase 7 (SA3 derivation) + Phase 10 (validator) | `grep 20607` returns 0 hits in notebook source; `SA3_CODE` variable used everywhere |
| SA3 point-in-polygon edge cases (Pitfall 3) | Phase 7 (SA3 derivation) | `SA3_CODE` not None after join; nearest-neighbor fallback with 2 km cap; ASGS edition printed |
| ABS API parameterised fetch (Pitfall 4) | Phase 8 (ABS API fetch) + Phase 6 (input validation) | Pre-API POA validation; `allowable_codes=(200,)` in cache; empty-response warning; batch >10 POAs |
| Geocoding edge cases (Pitfall 5) | Phase 6 (site input + geocoding) | `partial_match` checked; `location_type` checked; VIC bounding-box assertion; map displayed |
| Peer postcode validation (Pitfall 6) | Phase 6 (site input) + Phase 8 (peer benchmarking) | Non-VIC/non-existent/self-referential peers rejected with named warnings; empty-peer graceful skip |
| Report filename slugification (Pitfall 7) | Phase 9 (report generation) | Slugify function tested with hyphens/slashes/long addresses; postcode + date suffix; no overwrites |
| Pharmacy synergy removal (Pitfall 8) | Phase 9 (report generation) + Phase 10 (validator) | `grep synergy/pharmacy_synergy/capture_rates` clean; template renders without UndefinedError; citations renumbered |
| Validator hardcoded checks (Pitfall 9) | Phase 10 (validator update) | Validator passes for non-Abbotsford site; `--site abbotsford` mode reproduces v1.0 checks |
| Generator byte-stability (Pitfall 10) | Phase 10 (generator update) | Two generator runs produce byte-identical notebook; no site-specific values in generator source |
| v1.0 reproduction (Pitfall 11) | Phase 11 (reproduction verification) | Default config: SA3=20607, catchment pop ±1%, verdict=GO, P&L base ±5%; v1.0 validator passes (minus pharmacy) |
| Census vintage / ERP scaling (Pitfall 12) | Phase 7 (SA2 derivation) + Phase 8 (ERP fetch) | SA2 derived from point-in-polygon; ERP growth rate printed with source level; fallback for suppressed SA2 |

## Sources

- v1.0 codebase audit: `Johnston_St_v2.ipynb` (88 cells — hardcoded SA3 20607 in 8+ locations, hardcoded peer postcodes, hardcoded report filename, hardcoded SA2 code 206071139 for ERP, assumptions register skip-list at line 3489)
- v1.0 validator audit: `scripts/validate_v2_notebook.py` (901 lines, 36 checks — site-specific literals: `20607`, `Yarra`, `GCP_POA3067`, `Pharmacy Synergy`, `[1]`-`[8]`)
- v1.0 generator audit: `scripts/extend_v2_notebook_phase5.py` (920 lines — cell-replacement idempotency via marker strings, byte-stable `json.dumps(indent=1, ensure_ascii=False)`)
- EPSG:7855 coverage: epssg.org CRS 7855 — "Australia - onshore and offshore between 144°E and 150°E"; Land Vic map grids — "Zone 54 is longitude 138° to 144°, Zone 55 is longitude 144° to 150°" — verified 2026-07
- ABS Postal Areas (ASGS Edition 3): abs.gov.au — "2,644 Postal Areas ... 3 non-spatial special purpose codes"; "Postal Areas exclude postcodes that are not street delivery areas"; "codes may not match those used in past editions" — verified 2026-07
- ASGS Edition 3 SA3 changes: abs.gov.au — "no major changes to SA3s ... only minor alignment changes"; SA2 label/code changes listed (206041122→206041503, 206071144→206071517) — verified 2026-07
- ABS Data API limits: abs.gov.au user guide — 30-second timeout, 10 MB response cap, 5,000-char dataKey limit, Beta status — verified 2026-03 (v1.0 PITFALLS.md)
- Google Geocoding API: `partial_match`, `location_type` (ROOFTOP/RANGE_INTERPOLATED/GEOMETRIC_CENTER/APPROXIMATE) — developers.google.com/maps/documentation/geocoding

---
*Pitfalls research for: adding multi-site capability to existing v1.0 single-site feasibility notebook (v2.0 generalisation)*
*Researched: 2026-07-07*
