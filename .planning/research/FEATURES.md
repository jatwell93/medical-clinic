# Feature Research

**Domain:** Multi-site medical-clinic feasibility tool (VIC pilot) — generalising a single-site Colab notebook into a parameterised, address-driven tool
**Researched:** 2026-07-07
**Confidence:** HIGH (Colab form-field patterns verified against official Colab docs + colabtools issues; notebook cell references verified by reading `Johnston_St_v2.ipynb` directly; MEDIUM on SA3 boundary-join availability — depends on ABS ASGS structure pack being loadable in Colab)

## Context: How Multi-Site Feasibility Tools Typically Work

Professional site-feasibility tools that generalise beyond a single hardcoded site share a common interaction pattern:

1. **Site input** — user enters an address (or picks from a list), the tool geocodes it, derives the administrative geography (SA3, LGA, PHN), and fetches all downstream data for that geography automatically.
2. **Scope guard** — the tool validates the input is within its supported scope (state, country, data-availability zone) and fails fast with a clear message if not.
3. **Peer/comparator entry** — user optionally supplies peer sites (postcodes, suburbs, or addresses) for benchmarking; the tool validates these against a reference codelist.
4. **Auto-derivation with override** — administrative geographies (SA3, SA2, LGA) are derived from the geocoded point via spatial join; the user sees what was derived and can override if the derivation picked the wrong boundary (edge cases near SA3 borders).
5. **Named output** — the report file is named after the site (street + postcode + date), so multiple runs don't clobber each other and the file is self-identifying.
6. **Reproduction default** — the tool ships with a default config that reproduces a known reference case, so a reviewer can run it out-of-the-box and get a baseline result before trying their own site.

The v2.0 milestone applies this pattern to the existing v1.0 Abbotsford notebook. The features below are scoped to **only the new v2.0 capabilities** — the v1.0 features (geocoding, catchment, demographics, demand model, P&L, scenarios, report) are already built and are dependencies, not re-research targets.

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist in a "multi-site" tool. Missing these and the tool is still a single-site notebook with a cosmetic input cell.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Site-input form (street address + state + postcode + FTE count) | The entire premise of v2.0 is "enter any VIC address"; without a form, it's still hardcoded | LOW | Use Colab `#@param` form fields — native to Colab, renders visual controls, values flow into Python variables. Street address as `{type:"string"}`, state as dropdown `["VIC"]` (locked — VIC-only pilot), postcode as `{type:"integer"}`, FTE count as `{type:"slider", min:1, max:10, step:1}` with default 5. Abbotsford values as defaults. See UX Patterns section for full rationale. |
| Abbotsford as default config | Reviewers/investors must be able to run out-of-the-box and get a baseline; PROJECT.md states "v2.0 out-of-the-box reproduces v1.0" | LOW | Just set the `#@param` default values to 292-296 Johnston St, Abbotsford VIC 3067, 5 FTE. No separate config file needed — the form IS the config. |
| Geocoding of arbitrary VIC street addresses | v1.0 geocodes a hardcoded address; v2.0 must geocode whatever the user enters | LOW | v1.0 already has the geocoding cell (cell 13) using Google Geocoding API through CachedSession. Change: replace the hardcoded `SITE_ADDRESS` constant with the form-field variable. The geocode logic, caching, and assertion are reused as-is. **Depends on v1.0 cell 13 (geocoding) + cell 9 (CachedSession).** |
| SA3 auto-derivation from geocoded point | v1.0 hardcodes SA3 20607 Yarra in the MBS loader (cell 42); v2.0 must derive the correct SA3 for whatever site is geocoded | MEDIUM | Spatial join: geocoded point (EPSG:4326) → reproject to EPSG:7855 → point-in-polygon against SA3 boundary file. Requires an SA3 boundary shapefile/GeoJSON in `data/local/` (ABS ASGS ESRI shapefile or GeoPackage). Output: SA3 code + SA3 name. **Depends on v1.0 cell 16 (boundary geometry loader) — extend it to also load SA3 boundaries, or add a new loader cell.** |
| VIC-only guard | v2.0 is a VIC pilot; non-VIC sites would need MGA zone-aware reprojection (zones 49-56) which is deferred to v2.1 | LOW | Two-layer guard: (1) state dropdown locked to `["VIC"]` in the form — prevents non-VIC state entry at the UI level; (2) post-geocode check — verify the geocoded result's `address_components` includes `administrative_area_level_1: Victoria`. If mismatch (user typed a NSW street address but left state as VIC), raise `RuntimeError` with a clear message: "Geocoded address is in [state], not Victoria. v2.0 supports VIC-only sites. v2.1 will add multi-state support." Hard error, not silent skip — silent skip would produce a report for the wrong state without warning. |
| Peer postcode entry (optional) | v1.0 has 9 hardcoded peer postcodes; v2.0 lets the user supply their own peer set | LOW-MEDIUM | Free-text `#@param {type:"string"}` field, comma-separated (e.g., `"3066, 3068, 3070, 3121"`). Parsed into a list in a validation cell. If empty/blank, peer benchmarking is skipped entirely (the §3.5 peer table and §4.6 peer competitor table emit "No peers provided — skipping" and continue). **Depends on v1.0 cells 28-34 (peer census fetch) + cell 40 (peer Places queries) + cell 54 (peer competitor table) — all parameterised by `PEER_POSTCODES`, which becomes the parsed form input instead of a hardcoded list.** |
| Peer postcode validation | Users will enter invalid postcodes (typos, non-VIC, wrong format) | LOW | Validation cell after the form: (1) parse comma-separated string → strip whitespace → list of strings; (2) format check: each must be exactly 4 digits — invalid format → hard `ValueError` with message listing the bad entries; (3) VIC check: validate each against a VIC POA codelist (loaded from ABS ASGS or a hardcoded VIC postcode range 3000-3999 as a quick filter) — non-VIC postcodes → printed warning + dropped from the list (don't hard-fail; user might not know which are VIC); (4) dedupe. The cleaned list replaces the form input. |
| Report filename derived from site | Multiple runs for different sites must not clobber each other; filename should be self-identifying | LOW | `slugify(f"{street_keyword}-{postcode}-{date}")`. E.g., `johnston-st-3067-2026-07-07.pdf`. Slugify rules: lowercase, extract street name from the address (first significant token(s) before the first comma or "St/Rd/Ave/Dr"), replace spaces and punctuation with hyphens, collapse repeated hyphens, strip trailing hyphens. Date in ISO format (YYYY-MM-DD) for sortability. Implementation: a `slugify_site(address, postcode)` helper called in the PDF generation cell (cell 88). **Depends on v1.0 cell 88 (PDF generation) — change the hardcoded output filename to the slugified name.** |
| "How the tool sources data" explainer | v1.0's "guide on which ABS files to download" becomes obsolete when the tool auto-fetches; users need to understand what the tool fetches automatically vs what they still need to upload | LOW | Markdown cell in §0 (after the form, before §1). Explains: (1) ABS Data API — auto-fetched, free, cached, no key needed; (2) Google Places + Geocoding — auto-fetched, cached, needs `GOOGLE_PLACES_KEY`; (3) MBS SA3 Excel + AIHW age-band Excel — manual download required (these aren't available via API), links provided; (4) SA1/POA/SA3 boundary files — manual download required, links provided. This replaces v1.0's download checklist with a "what's automatic vs what you still upload" split. A separate guide doc (`docs/COLAB_SETUP.md`) already exists for the upload steps — the markdown cell links to it. Both (markdown cell + guide doc) is the right split: the cell is the in-notebook summary, the doc is the detailed download links. |

### Differentiators (Competitive Advantage)

Features that elevate v2.0 from "parameterised v1.0" to a genuinely reusable tool.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| SA3 auto-derivation with editable override | Most feasibility tools either hardcode the SA3 or make the user look it up manually; auto-derivation with a visible "derived SA3: 20607 Yarra — override?" prompt is both user-friendly and transparent | MEDIUM | After spatial join, print: `"[sa3] Derived SA3: 20607 Yarra (from geocoded point)"`. Provide an `#@param` override field: `sa3_override = "" #@param {type:"string"}` — if non-empty, use that SA3 code instead of the derived one (with a printed note that the override was used). This handles edge cases where the geocoded point falls near an SA3 border and the user knows the correct SA3. The override is a string (not a dropdown) because SA3 codes can't be hardcoded as a closed list without being huge. |
| Reproduction-path explainer (default = v1.0) | Makes it explicit that running with defaults reproduces the v1.0 study, building trust that the generalisation didn't break the original result | LOW | Markdown cell in §0: "Running this notebook with the default form values (292-296 Johnston St, Abbotsford VIC 3067, 5 FTE) reproduces the v1.0 feasibility study, with one difference: the pharmacy synergy section (v1.0 §7.6) has been removed in v2.0. The clinic standalone verdict, demand model, and financials are identical." This is a single markdown cell — no code, no complexity. |
| Graceful peer-skip when no peers provided | v1.0 always runs 10 peers (150 Places queries); v2.0 with no peers should skip cleanly without the user seeing empty-table errors | LOW | Guard clauses in the peer-fetch cells: `if not PEER_POSTCODES: print("[peers] No peer postcodes provided — skipping peer benchmarking"); peer_table = None`. Downstream cells that reference `peer_table` check for `None` before rendering. **Depends on v1.0 cells 28-36 (peer census) + 40 (peer Places) + 54 (peer competitor table) — add `if not PEER_POSTCODES` guards.** |
| Slugified, date-stamped report naming | v1.0 produces a single hardcoded filename; v2.0's per-site naming makes it obvious which report belongs to which site, and multiple runs accumulate rather than clobber | LOW | See table stakes row above. The differentiator is not the slugify itself (that's table stakes) but the thoughtfulness of the slug: extracting the street name (not the full address with numbers) makes the filename human-readable (`johnston-st-3067` not `292-296-johnston-st-abbotsford-vic-3067`). |
| "How the tool sources data" as a first-class explainer | v1.0's download guide is a chore; v2.0's explainer teaches the user what's automated vs manual, building confidence in the tool's reproducibility | LOW | See table stakes row. The differentiator is framing it as "here's what the tool does for you" rather than "here's what you need to do" — a tool-confidence builder, not a task list. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| ipywidgets for the site-input form | More flexible than `#@param`; supports dynamic dropdowns; works in local Jupyter too | The notebook is Colab-primary; ipywidgets add a `display(widget)` + `.value` indirection that breaks the "just edit the cell and Run All" flow; ipywidgets don't survive PDF export or static notebook viewing; `#@param` is native, simpler, and renders inline. Use ipywidgets only if a field needs runtime-dynamic options (e.g., SA3 dropdown populated after geocoding) — but the SA3 override is better as a free-text string field. | Colab `#@param` form fields for all static inputs; free-text string for SA3 override. Reserve ipywidgets for v2.1 if interactive site-selection maps are needed. |
| Batch/multi-site comparison mode | "Run 5 sites at once and compare" | Explicitly deferred to v2.1 per PROJECT.md; adds a loop wrapper, comparison tables, and multi-report generation that doubles the notebook complexity; v2.0's goal is to prove the single-site generalisation works | Single-run per site in v2.0; batch mode in v2.1. The slugified report naming (table stakes) makes manual batch runs feasible — run 5 times, get 5 named PDFs. |
| Non-VIC site support in v2.0 | "Why limit to Victoria?" | EPSG:7855 (MGA zone 55) is only valid for VIC; other states need zone-aware reprojection (NSW = zone 55/56, QLD = zone 55/56, etc.); the ABS Data API and MBS SA3 loader generalise, but the CRS handling doesn't; scope creep risk is high | VIC-only pilot in v2.0 with a hard guard and clear error message; v2.1 adds zone-aware reprojection (zones 49-56) for national coverage. |
| Dynamic SA3 dropdown (populated after geocoding) | "Show me a dropdown of valid SA3s for my site" | Can't be done with `#@param` (options must be hardcoded in comments); would require ipywidgets (anti-feature above); the auto-derivation + free-text override pattern is simpler and handles the 99% case | Auto-derive SA3 from geocoded point, display it, allow free-text override. The user doesn't need to pick from a list — the tool picks for them. |
| Silent skip for non-VIC addresses | "Just skip it and run the rest" | Produces a report with no data or wrong data without warning; violates the "defensible data" Core Value; the user might not realise the site was skipped | Hard error with a clear message explaining VIC-only scope and pointing to v2.1. |
| Pharmacy synergy as opt-in toggle | "Keep it but make it optional" | PROJECT.md explicitly drops pharmacy synergy for v2.0; an opt-in toggle keeps dead code in the notebook, complicates the report template (conditional sections), and muddies the "clinic standalone verdict" Core Value; the toggle is a maintenance burden for a feature that's been deliberately scoped out | Clean removal (see Feature Dependencies). Candidate for v2.1+ reintroduction as an explicit opt-in module, not a toggle in v2.0. |
| Auto-download of MBS SA3 + AIHW Excel files | "If ABS is auto-fetched, why not these too?" | These files are published as Excel downloads on health.gov.au / AIHW with no stable API endpoint; scraping the download page is fragile and breaks reproducibility; the files are large and change quarterly | Keep as manual upload (clearly explained in the "how the tool sources data" markdown cell); the upload is a one-time step per Colab session. |
| Free-text address without state/postcode fields | "Just type the full address in one field" | Geocoding ambiguity (there are multiple "Johnston St" in VIC alone); the state + postcode fields disambiguate and enable the VIC guard before geocoding (saves an API call); structured fields also enable the slugify to extract postcode reliably | Structured form: street address + state (dropdown) + postcode (integer). The geocode query concatenates them. |

## Feature Dependencies

```
Site-input form (@param fields)
    └──requires──> nothing (start here — replaces v1.0 cell 5 hardcoded constants)

Geocoding of arbitrary VIC address
    └──requires──> site-input form (street + state + postcode)
    └──requires──> v1.0 cell 9 (CachedSession) + cell 13 (geocode logic, reused)

VIC-only guard
    └──requires──> geocoding result (post-geocode state check)
    └──requires──> state dropdown locked to ["VIC"] (pre-geocode UI guard)

SA3 auto-derivation
    └──requires──> geocoded point (lat/lon)
    └──requires──> SA3 boundary file in data/local/ (ABS ASGS)
    └──requires──> v1.0 cell 16 pattern (boundary geometry loader) — extended for SA3
    └──enhances──> v1.0 cell 42 (MBS SA3 loader) — replace hardcoded "20607" with derived SA3 code

SA3 editable override
    └──requires──> SA3 auto-derivation (override is relative to the derived value)

Peer postcode entry + validation
    └──requires──> site-input form (peer postcodes field)
    └──requires──> VIC POA codelist (for validation — ABS ASGS or range filter)
    └──enhances──> v1.0 cells 28-36, 40, 54 (peer census/Places/table — parameterised by validated list)

Graceful peer-skip
    └──requires──> peer postcode entry (skip when empty)
    └──requires──> v1.0 peer cells (add None-guards)

Report filename from site
    └──requires──> site-input form (street + postcode)
    └──requires──> v1.0 cell 88 (PDF generation — change output filename)

"How the tool sources data" explainer
    └──requires──> nothing (markdown cell, standalone)
    └──enhances──> v1.0 §0.4 upload cell (contextualises what's manual vs auto)

Reproduction-path explainer
    └──requires──> Abbotsford default config (form defaults)
    └──requires──> pharmacy synergy removal (explainer states the difference)

Pharmacy synergy removal
    └──requires──> v1.0 cells 81, 82 (DELETE — markdown header + calculation code)
    └──requires──> v1.0 cell 87 (Jinja2 template — remove §6 Pharmacy Synergy HTML block, renumber subsequent sections)
    └──conflicts──> pharmacy synergy itself (by design — deliberate scope reduction)
```

### Dependency Notes

- **Site-input form is the root dependency for everything.** Every v2.0 feature reads from the form fields. The form replaces v1.0's hardcoded `SITE_ADDRESS` and `PEER_POSTCODES` constants in cell 5. Build it first.

- **SA3 auto-derivation requires an SA3 boundary file that v1.0 doesn't load.** v1.0 cell 16 loads SA1 + POA boundaries; v2.0 must extend this (or add a new cell) to also load SA3 boundaries. The ABS ASGS structure pack includes SA3 boundaries — confirm the file is in `data/local/` or add it to the upload list in §0.4.

- **Pharmacy synergy removal touches 3 cells, not the whole notebook.** The pharmacy synergy is cleanly isolated in v1.0: cell 81 (markdown header), cell 82 (calculation code + `report["pharmacy_synergy_range"]` deposit), and cell 87 (Jinja2 template §6 block). The verdict logic (cell 85) already never mentions pharmacy. `BASE_ASSUMPTIONS` (cell 5) has no pharmacy-specific keys — the synergy calculation used local variables in cell 82, not config dict keys. The `places_included_types` list in cell 5 includes `"pharmacy"` — KEEP this (pharmacies are still mapped as competitors in §4; only the synergy P&L is removed). After removal, the report's 8 sections become 7 (renumber §7 Assumptions Register → §6, §8 Verdict → §7, or renumber all).

- **VIC-only guard is two-layered by design.** The form-level guard (state dropdown locked to VIC) prevents most non-VIC input without any code. The post-geocode guard catches the edge case where the user enters a non-VIC street address but leaves the state field as VIC (the geocoder resolves the real location). Both are needed; neither is sufficient alone.

- **Peer-skip and peer-validation are complementary, not conflicting.** Validation handles "user entered bad postcodes"; skip handles "user entered none". Both guard the same downstream cells (28-36, 40, 54) but at different stages: validation runs after the form, skip runs at the peer-fetch entry point.

## MVP Definition

### Launch With (v2.0)

- [ ] Site-input form (`#@param` fields: street address, state=VIC, postcode, FTE count, peer postcodes, SA3 override) — replaces v1.0 hardcoded constants; Abbotsford as defaults
- [ ] Geocoding of form-supplied address — reuses v1.0 cell 13 logic, reads form variable instead of constant
- [ ] VIC-only guard (form-level + post-geocode) — hard error on non-VIC with clear message
- [ ] SA3 auto-derivation (spatial join against SA3 boundaries) + editable override field — replaces hardcoded SA3 20607
- [ ] Peer postcode entry + validation (format check, VIC check, dedupe) — replaces hardcoded peer list
- [ ] Graceful peer-skip when no peers provided — None-guards on v1.0 peer cells
- [ ] Report filename from site (slugify street + postcode + date) — replaces hardcoded PDF filename
- [ ] "How the tool sources data" markdown explainer — replaces v1.0 download checklist
- [ ] Reproduction-path markdown explainer — "defaults reproduce v1.0 minus pharmacy synergy"
- [ ] Pharmacy synergy removal — delete cells 81/82, remove template §6 block, renumber report sections

### Add After Validation (v2.1)

- [ ] Batch/multi-site comparison mode — once single-site generalisation is proven across multiple VIC addresses
- [ ] Non-VIC site support (MGA zone-aware reprojection, zones 49-56) — once VIC pilot validates the demand model generalises
- [ ] Pharmacy synergy as opt-in module — once v2.0 standalone verdict is stable and users request it
- [ ] Drive-time isochrones — once a reviewer challenges radial buffers and free OSRM/Distance Matrix is viable in Colab
- [ ] Dynamic SA3 dropdown via ipywidgets — only if the free-text override proves insufficient

### Future Consideration (v2.2+)

- [ ] Interactive site-selection map (click to pick a site) — only if ipywidgets/Colab interactivity matures
- [ ] 2026 Census refresh — when data releases (~2027), swap in via the same auto-fetch pipeline
- [ ] National expansion (all states/territories) — requires zone-aware reprojection + national MBS SA3 coverage

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Site-input form (@param fields) | HIGH | LOW | P1 |
| Abbotsford as default config | HIGH | LOW | P1 |
| Geocoding of form-supplied address | HIGH | LOW | P1 |
| VIC-only guard (two-layered) | HIGH | LOW | P1 |
| SA3 auto-derivation + override | HIGH | MEDIUM | P1 |
| Peer postcode entry + validation | MEDIUM | LOW-MEDIUM | P1 |
| Graceful peer-skip | MEDIUM | LOW | P1 |
| Report filename from site | MEDIUM | LOW | P1 |
| "How the tool sources data" explainer | MEDIUM | LOW | P1 |
| Reproduction-path explainer | MEDIUM | LOW | P1 |
| Pharmacy synergy removal | MEDIUM | LOW | P1 |
| SA3 editable override field | LOW-MEDIUM | LOW | P2 (ships with SA3 auto-derivation) |
| Batch/multi-site comparison | HIGH | HIGH | P3 (v2.1) |
| Non-VIC site support | HIGH | HIGH | P3 (v2.1) |
| Pharmacy synergy as opt-in | LOW | LOW-MEDIUM | P3 (v2.1+) |
| ipywidgets for site form | LOW | MEDIUM | P3 (likely never — @param is sufficient) |

## UX Patterns for Colab Notebook Forms

### The `#@param` vs ipywidgets vs code-cell-dict decision

Three options exist for surfacing the site-input form in a Colab notebook. The recommendation is **`#@param` form fields** as the primary pattern, with a validation code cell downstream.

| Pattern | Pros | Cons | Verdict for v2.0 |
|---------|------|------|-------------------|
| **Colab `#@param` form fields** | Native to Colab; renders visual controls (text boxes, dropdowns, sliders) next to the code cell; values flow directly into Python variables; survives `Restart & Run All`; no extra imports; form can be collapsed to show only the fields (hide code); defaults are visible in the cell source | Dropdown options must be hardcoded in comments (can't be dynamic); Colab-only (no-op in local Jupyter, but the variables still resolve to their default values); no validation built into the form itself | **USE THIS** for all static inputs: street address, state, postcode, FTE count, peer postcodes, SA3 override |
| **ipywidgets** | Works in Colab AND local Jupyter; supports dynamic dropdowns (options populated at runtime); richer widget types (DatePicker, BoundedIntText, etc.) | Requires `display(widget)` + reading `.value` (breaks "just edit and Run All" flow); widgets don't survive PDF export or static notebook viewing; adds import overhead; state management is fiddly (widget value vs Python variable) | **DON'T USE** for v2.0. Reserve for v2.1 only if a dynamic SA3 dropdown or interactive site map is needed. |
| **Code-cell dict** (e.g., `SITE = {"address": "...", "postcode": 3067}`) | Full Python flexibility; validation can be inline; works everywhere | No visual form — user must edit Python code; non-technical users find dict syntax intimidating; no input controls (sliders, dropdowns); feels like "just editing code" not "using a tool" | **DON'T USE** as the primary form. Use as the internal representation: the `#@param` fields are parsed into a `SITE_CONFIG` dict in a validation cell, which downstream cells read. This gives the form UX of `#@param` with the programmatic flexibility of a dict. |

### Recommended form cell structure

```python
# @title Site Configuration
# @markdown Enter the site address and clinic parameters. Defaults reproduce the v1.0 Abbotsford study.
# @markdown ---
# @markdown **Site address** (street number + name + suburb, e.g., "292-296 Johnston St, Abbotsford")
site_address = "292-296 Johnston St, Abbotsford"  # @param {type:"string"}
# @markdown **State** (v2.0 supports VIC only — v2.1 will add other states)
site_state = "VIC"  # @param ["VIC"]
# @markdown **Postcode** (4-digit VIC postcode)
site_postcode = 3067  # @param {type:"integer"}
# @markdown **GP FTE count** (full-time-equivalent GPs)
gp_fte_count = 5  # @param {type:"slider", min:1, max:10, step:1}
# @markdown **Peer postcodes** (comma-separated VIC postcodes for benchmarking, or blank to skip)
peer_postcodes = "3066, 3068, 3070, 3078, 3079, 3101, 3121, 3122, 3123"  # @param {type:"string"}
# @markdown **SA3 override** (blank = auto-derive from geocoded point; enter a 5-digit SA3 code to override)
sa3_override = ""  # @param {type:"string"}
```

Followed by a validation cell that:
1. Concatenates `site_address + ", " + site_state + " " + str(site_postcode)` → `SITE_ADDRESS` (used by the geocoder)
2. Parses `peer_postcodes` → list, validates format (4-digit), filters to VIC, dedupes → `PEER_POSTCODES`
3. Builds `SITE_CONFIG = {"address": ..., "postcode": ..., "gp_fte": ..., "sa3_override": ...}` for downstream cells
4. Prints a summary: `"[config] Site: 292-296 Johnston St, Abbotsford VIC 3067 | 5 FTE | 9 peers | SA3: auto-derive"`

### Why `#@param` over a code-cell dict for this project

- **Colab is the primary environment** (PROJECT.md constraint). `#@param` is native and renders the form automatically.
- **The user is a business analytics student**, not a developer. Visual form fields (slider for FTE, dropdown for state) are more approachable than editing a Python dict.
- **Defaults reproduce v1.0.** The `#@param` defaults ARE the Abbotsford config — a reviewer opening the notebook sees the v1.0 values pre-filled and can Run All immediately.
- **The validation cell handles what `#@param` can't.** Format validation, VIC postcode filtering, and dict construction happen in code, not in the form. This is the right separation: form for input, code for validation.

### SA3 override UX

The SA3 override is a free-text string field, not a dropdown, because:
- SA3 codes can't be hardcoded as a `#@param` dropdown list (there are ~100 VIC SA3s — too many for a closed list, and the list would need updating if ABS revises boundaries).
- The 99% case is "auto-derive is correct, leave override blank." The 1% case (border edge case) is a power user who knows the SA3 code they want.
- The user sees the derived SA3 printed in the output of the derivation cell: `"[sa3] Derived SA3: 20607 Yarra (from geocoded point)"`. If wrong, they type the correct code in the override field and re-run.

### Report naming UX

The user doesn't see or control the filename — it's derived automatically. This is intentional:
- Prevents human error (typos, inconsistent naming).
- Makes the file self-identifying (`johnston-st-3067-2026-07-07.pdf` tells you the site and date at a glance).
- Multiple runs accumulate (date-stamped), don't clobber.
- The slugify extracts the street name (not the full address with numbers) for readability: `johnston-st-3067` not `292-296-johnston-st-abbotsford-vic-3067-2026-07-07`.

### "How the tool sources data" explainer UX

A markdown cell in §0, after the form and before §1. Structure:

```markdown
## How This Tool Sources Data

| Data | Source | How it's fetched | What you do |
|------|--------|-----------------|-------------|
| Census (G01/G02/G04) | ABS Data API | Auto-fetched, cached | Nothing — free, no key |
| Geocoding | Google Geocoding API | Auto-fetched, cached | Add `GOOGLE_PLACES_KEY` to Colab Secrets |
| Competitors | Google Places API (New) | Auto-fetched, cached | Same key as above |
| MBS SA3 utilisation | health.gov.au Excel | Manual download | Upload via §0.4 (see docs/COLAB_SETUP.md) |
| AIHW age-band rates | AIHW Excel | Manual download | Upload via §0.4 |
| SA1/POA/SA3 boundaries | ABS ASGS | Manual download | Upload via §0.4 |
```

This replaces v1.0's "guide on which files to download" with a clear auto-vs-manual split. The in-notebook markdown cell is the summary; `docs/COLAB_SETUP.md` has the detailed download links. Both is the right answer — the cell is what the user sees in the notebook, the doc is what they reference when actually downloading.

## Competitor Feature Analysis

"Competitors" here = multi-site feasibility tool archetypes that v2.0 will be judged against.

| Feature | Pharmacy-broker template tool | Health-planning consultancy tool | Our Approach (v2.0) |
|---------|-------------------------------|----------------------------------|---------------------|
| Site input | Fixed address in a Word doc | GIS desktop app (ArcGIS/QGIS) | Colab `#@param` form — web-accessible, no install |
| Geography derivation | Manual (user looks up SA3) | Automatic (GIS spatial join) | Automatic with editable override — best of both |
| Scope guard | None (any address) | Configured per project | VIC-only hard guard with clear v2.1 roadmap |
| Peer selection | Hardcoded in template | Manual GIS selection | User-supplied postcodes with validation + graceful skip |
| Report naming | Manual filename | Project-based naming | Auto-slugified from site + date |
| Reproduction | None (static PDF) | Project files (ArcGIS) | Default config reproduces v1.0 — unique traceability |
| Data sourcing transparency | None | Implicit (GIS layers) | Explicit "auto vs manual" table — teaching tool |

## Sources

- Google Colab Forms documentation — `colab.research.google.com/notebooks/forms.ipynb` — `#@param` syntax, field types, `{allow-input: true}` for dropdown+free-text, `#@title` for cell titles, `cellView: form` for hiding code — HIGH confidence
- GoogleColab/colabtools Issue #2407 — Colab team recommends ipywidgets for dynamic/runtime-determined dropdown options; `#@param` dropdown options must be hardcoded — HIGH confidence
- GoogleColab/colabtools Issue #116 — Confirms `#@param` can't reference variables for dropdown options; ipywidgets is the workaround — HIGH confidence
- Cosmoscalibur blog (2026) — Best practices for Colab with non-technical teams: use `#@param` with closed dropdown lists to prevent typos, hide internal cells with `cellView: form`, use programmatic filenames — HIGH confidence
- `Johnston_St_v2.ipynb` cell-by-cell inspection — verified cell 5 (BASE_ASSUMPTIONS), cell 13 (geocoding), cell 16 (boundary loader), cell 42 (MBS SA3 loader with hardcoded 20607), cells 81-82 (pharmacy synergy), cell 85 (verdict logic), cell 87 (Jinja2 template §6 pharmacy block), cell 88 (PDF generation) — HIGH confidence
- PROJECT.md v2.0 milestone context — VIC-only pilot, pharmacy synergy dropped, Abbotsford as default, batch mode deferred to v2.1 — HIGH confidence

---
*Feature research for: v2.0 multi-site feasibility tool (VIC pilot)*
*Researched: 2026-07-07*
