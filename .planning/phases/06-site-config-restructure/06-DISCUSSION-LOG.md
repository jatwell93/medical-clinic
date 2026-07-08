# Phase 6: Site Config Restructure - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-08
**Phase:** 06-site-config-restructure
**Areas discussed:** Geocode strictness, P6↔P7 VIC boundary, 7899 migration scope, Peer validation UX

---

## Geocode strictness

| Option | Description | Selected |
|--------|-------------|----------|
| RuntimeError hard stop | bbox-outside → RuntimeError, consistent with P7 GEO-04; hard stop, Run All halts | ✓ |
| Print + skip | Print rejection, leave site_point None; downstream fails later with less clear errors | |

**Question:** When the geocoded point falls outside the VIC bounding box, what does "rejected" mean?
**User's choice:** RuntimeError hard stop

| Option | Description | Selected |
|--------|-------------|----------|
| Hard fail with message | RuntimeError: "Geocoding returned no results for: {address}..." | ✓ |
| Warn + None | Print warning, leave site_point None; downstream crashes later | |

**Question:** What if geocoding returns ZERO results?
**User's choice:** Hard fail with message

| Option | Description | Selected |
|--------|-------------|----------|
| Show coords + address | Print returned lat/lon + formatted_address alongside warning | ✓ |
| Flag only | Print just the flag name, no coordinates | |

**Question:** Should partial_match/non-ROOFTOP warnings include the returned coordinates?
**User's choice:** Show coords + address

**Notes:** Success criteria already locked partial_match=warn, non-ROOFTOP=warn, bbox-outside=reject. Discussion resolved the *behavior* of "rejected" (RuntimeError) and the zero-results edge case (not covered by criteria). Run continues on warnings; halts on bbox/zero-results.

---

## P6↔P7 VIC boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Distinct: bbox (P6) then state (P7) | P6 = coarse bbox reject; P7 = authoritative state-component check. Non-overlapping. | ✓ |
| All VIC checks in P7 | P6 does no VIC reject; defer all to P7's two-layered guard | |
| Full guard in P6 | P6 implements full two-layered guard now; P7 reuses. Pulls GEO-04 forward. | |

**Question:** How should VIC-enforcement be split between Phase 6 and Phase 7?
**User's choice:** Distinct: bbox (P6) then state (P7)

| Option | Description | Selected |
|--------|-------------|----------|
| bbox=coords, state=address component | P6 = lat/lon bbox test; P7 = parse administrative_area_level_1 == 'Victoria' | ✓ |
| Both coordinate-based | P6 = bbox; P7 = point-in-polygon on VIC state boundary | |

**Question:** If distinct: what mechanism does each phase use?
**User's choice:** bbox=coords, state=address component

**Notes:** Confirms the two checks use different mechanisms (coordinate bbox vs address component) so they are not redundant. P6 is the fast geometric gate; P7 is the authoritative administrative guard. Planner must not duplicate either.

---

## 7899 migration scope

| Option | Description | Selected |
|--------|-------------|----------|
| Single CRS_METRIC constant | Define CRS_METRIC='EPSG:7899' in §0.3; replace every literal in §2 | ✓ |
| Literal string replace | Replace every 'EPSG:7855' with 'EPSG:7899' in §2 cells | |

**Question:** How should Phase 6 swap the CRS across §2 geometry cells?
**User's choice:** Single CRS_METRIC constant

| Option | Description | Selected |
|--------|-------------|----------|
| Recompute expected value | Recompute 3km buffer area under 7899; update assertion value + tolerance | ✓ |
| Widen tolerance | Keep 28.27 km², widen tolerance so it passes under 7899 | |
| Print only, no assert | Drop the assertion; print area as info | |

**Question:** What should happen to the 28.27 km² buffer assertion under 7899?
**User's choice:** Recompute expected value

| Option | Description | Selected |
|--------|-------------|----------|
| All §2 geometry cells | Rewrite all §2 cells referencing 7855 (buffers, apportionment, maps, tiles) | ✓ |
| Buffer cell only | Only buffer-construction + assertion; leave apportionment/maps on 7855 | |

**Question:** Does Phase 6 rewrite ALL §2 geometry cells or just the buffer cell?
**User's choice:** All §2 geometry cells

**Notes:** GEO-05 says "all metre-based buffer/area math uses EPSG:7899" — confirmed all §2 cells migrate. The assertion stays honest (recomputed, not tolerance-widened). CRS_METRIC constant matches the BASE_ASSUMPTIONS single-source-of-truth pattern.

---

## Peer validation UX

| Option | Description | Selected |
|--------|-------------|----------|
| One line per drop + reason | e.g. "[peer] dropped 312X — not 4 digits"; most auditable | ✓ |
| Single summary line | e.g. "[peer] dropped 3 invalid: 312X, 2000, 3067(dup)"; compact | |

**Question:** What warning format for dropped peer postcodes?
**User's choice:** One line per drop + reason

| Option | Description | Selected |
|--------|-------------|----------|
| Inline in §0.3 | Validate immediately after dicts; preserves single-params-cell invariant | ✓ |
| Dedicated §0.4 cell | Separate validation cell; cleaner but breaks single-params-cell convention | |

**Question:** Where does peer validation run?
**User's choice:** Inline in §0.3

| Option | Description | Selected |
|--------|-------------|----------|
| Prefix '3' (3000–3999) | VIC postcodes start with '3'; simple, deterministic, no shapefile | ✓ |
| POA centroid in VIC | Point-in-polygon on POA shapefile; authoritative but heavy for §0.3 | |

**Question:** How is the VIC-only peer filter implemented?
**User's choice:** Prefix '3' (3000–3999)

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — list valid peers | Print "[peer] {N} valid peers: ..." confirmation | ✓ |
| Silent on success | Print nothing if all peers valid | |

**Question:** Should validation print a confirmation when peers pass?
**User's choice:** Yes — list valid peers

**Notes:** SITE-06 locked the rules (4-digit, VIC, dedupe, self-referential); discussion resolved presentation (per-line + reason), placement (inline §0.3), VIC mechanism (prefix '3', matching v1.0's existing POA filter), and positive confirmation.

---

## Claude's Discretion

- Exact VIC bounding box coordinates (research lookup from EPSG:7899 registry / Land Victoria).
- Exact recomputed 3 km buffer area value under EPSG:7899 (determined at build time).
- Whether `location_type` accepts `RANGE_INTERPOLATED` or warns on anything non-ROOFTOP (researcher confirms Google taxonomy; default warn).
- SITE_CONFIG dict field naming/key conventions (planner may refine the architecture sketch).
- Whether `floor_area_sqm` is a `#@param` form field or stays in BASE_ASSUMPTIONS (architecture places it in SITE_CONFIG; planner confirms).

## Deferred Ideas

- Exact VIC bounding box coordinates — research lookup, not a user decision.
- `location_type` acceptable values — researcher confirms Google taxonomy.
- `catchment_pop_plausible_range` (80k–110k) generalisation to site-relative — later phase (P7/P8), NOT Phase 6.
- contextily basemap CRS under 7899 — researcher verifies during planning (display already converts to 3857).
