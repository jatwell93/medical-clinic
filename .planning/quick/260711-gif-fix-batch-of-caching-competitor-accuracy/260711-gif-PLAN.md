---
phase: quick/260711-gif
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - .gitignore
  - Johnston_St_v2.ipynb
  - data/local/manual_classifications.csv
autonomous: true
requirements:
  - caching-cost-safety
  - competitor-accuracy
  - demand-constrained-verdict
must_haves:
  truths:
    - "Colab clone includes places_cache + geocode_cache so no live API calls bill on re-run"
    - "places_nearby() raises RuntimeError on cache miss when ALLOW_LIVE_CALLS=False (default)"
    - "places_nearby_saturated() 2x2 sub-circles cover the full parent circle with no uncovered annulus"
    - "Cells 41/42 sleep only on live calls, not cache hits; cost summary counts billable calls only"
    - "Competitor pipeline rebuilds deterministically from raw places_cache + manual_classifications.csv each run"
    - "competitors_gdf reflects distinct clinic SITES with per-site FTE proxy, not inflated listing counts"
    - "per_ring_counts[total] is GP-type only (gp_corporate + gp_independent)"
    - "per_ring_counts reflects post-classification GP counts (recomputed after cell 57 site-collapse)"
    - "Verdict (cell 101) gates on CONSTRAINED EBITDA at achievable_util = min(target, unmet_demand/clinic_capacity)"
    - "constrained_pnl is called in cell 79 (after clinic_pnl defined at 78 and achievable_util set at 71)"
    - "Geocode fallback (cell 15) emits a loud multi-line banner — not a quiet one-liner"
    - "BRAVE_RESULTS literal is gone from cell 57; manual_classifications.csv is committed"
  artifacts:
    - path: "data/cache/places_cache/"
      provides: "1781 cached Places API JSON responses — committed, travels to Colab"
    - path: "data/cache/geocode_cache/"
      provides: "1 cached geocode response — committed, travels to Colab"
    - path: "data/local/manual_classifications.csv"
      provides: "~64 curated Brave Search classifications (displayName, category, evidence)"
    - path: "Johnston_St_v2.ipynb"
      provides: "Updated notebook — cells 5, 15, 40, 41, 42, 51, 53, 57, 62, 68, 71, 79, 101, 102"
    - path: ".gitignore"
      provides: "Un-ignores places_cache/ and geocode_cache/; adds .gitignore exception for manual_classifications.csv"
  key_links:
    - from: "cell 5 (ALLOW_LIVE_CALLS)"
      to: "cell 40 places_nearby()"
      via: "global flag checked before live HTTP call"
      pattern: "ALLOW_LIVE_CALLS"
    - from: "data/cache/places_cache/"
      to: "cell 40 places_nearby()"
      via: "manual file cache read"
      pattern: "PLACES_CACHE_DIR"
    - from: "data/local/manual_classifications.csv"
      to: "cell 57 (replacement)"
      via: "pd.read_csv join on displayName"
      pattern: "manual_classifications"
    - from: "cell 51 site-collapse (existing_gp_capacity)"
      to: "cell 71 compute_required_market_share"
      via: "existing_capacity argument (site-derived FTE proxy)"
      pattern: "existing_gp_capacity"
    - from: "cell 71 (achievable_util)"
      to: "cell 79 (constrained_pnl call)"
      via: "achievable_util local variable in scope"
      pattern: "achievable_util"
    - from: "cell 79 (constrained_pnl deposits)"
      to: "cell 101 verdict"
      via: "report dict deposit"
      pattern: "constrained_ebitda"
---

<objective>
Fix 10 bugs across caching cost-safety, competitor accuracy, and the demand-constrained verdict
in Johnston_St_v2.ipynb. The root cause of a ~$500 Places API bill is that `data/cache/places_cache/`
is gitignored, so Colab clones an empty cache and re-bills every call. Secondary issues inflate competitor
counts, sleep on cache hits, and let the Go/No-Go verdict run at full-books utilisation ignoring actual
market capacity.

Purpose: Make the notebook safe to run in Colab (cache-first, cannot bill without explicit opt-in),
produce accurate competitor site-collapse counts, and gate the verdict on a demand-constrained
utilisation ceiling — the two locked design decisions.

Output:
- .gitignore with places_cache/ and geocode_cache/ un-ignored
- Updated notebook cells: 5, 15, 40, 41, 42, 51, 53, 57, 62, 68, 71, 79, 101, 102
- data/local/manual_classifications.csv (the ~64 Brave Search classifications extracted from cell 57)
- Two clean git commits: one for the cache files, one for notebook + gitignore + CSV
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md

Key invariants (from CLAUDE.md + background):
- EPSG:7855 for all metric distance/area operations — never buffer in EPSG:4326
- Places API (New) POST places:searchNearby — never the legacy client
- Cache-first, never hard-fail on a network call (ALLOW_LIVE_CALLS guard degrades gracefully)
- No ML on small n — arithmetic demand model only
- Investor-grade reproducibility: every assumption transparent, every caveat flagged

LOCKED DESIGN DECISIONS (do not revisit):
- D-LOCKED-A (finding 9): Verdict must be DEMAND-CONSTRAINED.
  achievable_util = min(target_utilisation, unmet_demand / clinic_full_capacity)
  Gate verdict on P&L at achievable_util, surface "demand can't support this site" when low.
- D-LOCKED-B (finding 5): Existing GP supply = distinct clinic SITES by normalized address,
  per-site practitioner-listing count as FTE proxy, fallback avg_fte_per_clinic=4 where count=0.

Task ordering constraint: T2 (site-collapse → existing_gp_capacity) must execute before T3
(demand-constrained verdict consumes existing_gp_capacity). T1, T4, T5 are independent of T2/T3.
</context>

<tasks>

<!-- ═══════════════════════════════════════════════════════════
     T1 — Caching / cost safety
     Findings 1, 2, 3, 4
     Files: .gitignore, cell 5, cell 40, cell 41, cell 42
     ═══════════════════════════════════════════════════════════ -->

<task type="auto">
  <name>T1: Fix caching cost-safety (.gitignore + cells 5/40/41/42)</name>
  <files>
    .gitignore
    Johnston_St_v2.ipynb (cells 5, 40, 41, 42)
  </files>
  <action>
**Finding 1 — un-ignore the manual caches (.gitignore lines 25-26):**

Replace the current block:
```
# Google API caches — may contain API keys, never commit (D-15)
data/cache/geocode_cache/
data/cache/places_cache/
```
With:
```
# Google API manual-cache JSON files — contain NO secrets (only place records /
# lat-lon coordinates). Un-ignoring so they travel to Colab via git clone.
# These are the $0-rerun guarantee for the ~1781 Places + geocode responses.
# VERIFIED: no API key present in any .json file in these dirs — D-15 unchanged.
# !data/cache/geocode_cache/   # now tracked (see above)
# !data/cache/places_cache/    # now tracked (see above)
```
Note: because `data/cache/` itself is NOT listed in .gitignore, removing the two
subdirectory lines is sufficient to un-ignore them. Confirm `data/cache/**/redirects.sqlite`
line stays intact (it is on a separate line — do not disturb it).

**Finding 2 — add ALLOW_LIVE_CALLS + MAX_LIVE_CALLS to cell 5 (PARAMS cell):**

After the existing `FORCE_REFRESH = False` line add (keep comment style matching the cell):
```python
# API cost safety — default OFF so notebook cannot bill without explicit opt-in (D-15)
# Flip to True for a session where you intend to make live Places/Geocode calls.
# MAX_LIVE_CALLS is a hard cap per session — raise if you need a larger batch.
ALLOW_LIVE_CALLS = False   # COST GUARD: False = cache-only; raises on any cache miss
MAX_LIVE_CALLS   = 200     # Hard cap on billable calls per notebook session
```
Also add to BASE_ASSUMPTIONS (it's a global parameter used by places_nearby):
```python
    # --- API cost safety (D-15) ---
    "allow_live_calls":   False,   # mirrors ALLOW_LIVE_CALLS; use the global directly in places_nearby()
    "max_live_calls":     200,     # hard cap on billable Places/Geocode calls per session
```
Do NOT add allow_live_calls to BASE_ASSUMPTIONS if it creates a duplicate — the global
ALLOW_LIVE_CALLS is the authoritative value; BASE_ASSUMPTIONS comment is documentation only.
Actually: keep the cost-guard as module-level globals only (ALLOW_LIVE_CALLS, MAX_LIVE_CALLS)
and reference them directly in places_nearby(). Do not add to BASE_ASSUMPTIONS dict to avoid
confusion with scenario overrides.

**Finding 2 — guard in places_nearby() (cell 40):**

At the top of the cache-miss branch (after `# Cache miss — make live API call (costs money)`
and BEFORE the `body = {...}` dict), insert:
```python
    # Cost guard — raise immediately if live calls are disabled or capped (D-15)
    if not ALLOW_LIVE_CALLS:
        raise RuntimeError(
            f"[places] Cache MISS for {included_types} r={radius_m}m — "
            "live call blocked (ALLOW_LIVE_CALLS=False).\n"
            "  To allow spending: set ALLOW_LIVE_CALLS=True in cell §0.3 for this session.\n"
            "  Cached files should be present after `git clone` — if missing, check .gitignore fix."
        )
    if _places_live_calls >= MAX_LIVE_CALLS:
        raise RuntimeError(
            f"[places] Hard cap reached: {_places_live_calls} live calls >= MAX_LIVE_CALLS={MAX_LIVE_CALLS}.\n"
            "  Raise MAX_LIVE_CALLS in cell §0.3 if you need more."
        )
```

**Finding 3 — fix saturation subdivision geometry in places_nearby_saturated() (cell 40):**

The current offsets are `±sub_radius * 0.5 = ±r/4` with `sub_radius = r/2`. This leaves
the annulus between 0.75r and r uncovered. Replace the subdivision block.

Correct geometry: four sub-circles of radius `sub_r = r * 0.7071` (= r/√2) centered at
`(±r/2, ±r/2)` in dx/dy metres. Each sub-circle of radius r/√2 centred at distance
r/√2 from origin covers from 0 to r (the diagonal from center to corner of the bounding
square is r/√2 + r/√2 = r√2, but the key property is that every point within the parent
circle of radius r is within r/√2 of at least one sub-center).

Replace the `sub_radius` and `offsets` block with:
```python
    # Fixed coverage: sub-circles of radius r/√2 centred at (±r/2, ±r/2).
    # Every point in the parent circle of radius r is ≤ r/√2 from its nearest
    # sub-center — no annular blind spot. (Prior code: sub_radius=r/2, centres at
    # ±r/4 — left annulus between 0.75r and r uncovered, undercounting competitors.)
    sub_radius = radius_m / math.sqrt(2)   # ≈ 0.7071 * r
    offsets = [
        ( radius_m / 2,  radius_m / 2),   # NE quadrant centre
        ( radius_m / 2, -radius_m / 2),   # SE quadrant centre
        (-radius_m / 2,  radius_m / 2),   # NW quadrant centre
        (-radius_m / 2, -radius_m / 2),   # SW quadrant centre
    ]
```
Keep the depth-2 recursion block unchanged. In the recursive depth-2 sub_queries loop,
apply the same fix: replace `sdx * 0.5, sdy * 0.5` and `sub_radius / 2` with the
correctly-scaled recursive values. At depth 2 the sub-sub-radius is `sub_radius / sqrt(2)`
and offsets are `sub_radius/2` in each axis:
```python
    for sub_lat, sub_lon, r_sub in sub_queries:
        if len(r_sub) >= 20:
            ss_sub_radius = sub_radius / math.sqrt(2)
            ss_offsets = [
                ( sub_radius / 2,  sub_radius / 2),
                ( sub_radius / 2, -sub_radius / 2),
                (-sub_radius / 2,  sub_radius / 2),
                (-sub_radius / 2, -sub_radius / 2),
            ]
            for sdx, sdy in ss_offsets:
                ss_lat, ss_lon = offset_meters(sub_lat, sub_lon, sdx, sdy)
                sub_results.extend(places_nearby(ss_lat, ss_lon, ss_sub_radius, included_types))
```

**Finding 4 — sleep only on live calls (cells 41 and 42):**

In cell 41, the `time.sleep(_places_call_delay)` call is outside the function and runs
unconditionally. Wrap it in a check:
```python
        # Sleep only on live calls — cached reruns should not waste 165+ seconds
        if _places_live_calls > _live_before:
            time.sleep(_places_call_delay)
```
This requires capturing `_live_before = _places_live_calls` before the
`places_nearby_saturated()` call. Apply the same pattern to cell 42.

In cell 42's cost summary, `_places_live_calls` is currently inflated by 429 retry attempts
(each retry loop iteration increments it). Fix in places_nearby() (cell 40): move
`_places_live_calls += 1` OUTSIDE the retry loop — increment once per logical query,
not per attempt. Add a separate counter `_places_retry_attempts` for the retry loop so
the cost summary can distinguish billable calls from retries:
```python
    # Count one LOGICAL call (billable unit) — NOT per retry attempt
    _places_live_calls += 1          # one billable request
    _places_retry_attempts = 0       # track retries separately
    for attempt in range(4):
        resp = session.post(PLACES_URL, json=body, headers=headers)
        _places_call_count += 1
        if resp.status_code == 429:
            _places_retry_attempts += 1
            ...
```
Update the cost summary in cell 42 to print both:
```python
print(f"Live API calls:   {_places_live_calls} (billable)")
if _places_retry_attempts > 0:
    print(f"429 retries:      {_places_retry_attempts} (not separately billed)")
```
  </action>
  <verify>
    <automated>
python -c "
# 1. gitignore no longer blocks the two cache dirs
import subprocess, re
result = subprocess.run(['git', 'check-ignore', '-v',
  'data/cache/places_cache/00c29f55344e0606.json',
  'data/cache/geocode_cache/'], capture_output=True, text=True, cwd='C:/Users/josha/medical-clinic')
assert result.stdout.strip() == '', f'Still gitignored: {result.stdout}'

# 2. Cell 5 has ALLOW_LIVE_CALLS and MAX_LIVE_CALLS
import json
with open('C:/Users/josha/medical-clinic/Johnston_St_v2.ipynb', encoding='utf-8') as f:
    cells = json.load(f)['cells']
src5 = ''.join(cells[5]['source'])
assert 'ALLOW_LIVE_CALLS' in src5, 'Missing ALLOW_LIVE_CALLS in cell 5'
assert 'MAX_LIVE_CALLS' in src5, 'Missing MAX_LIVE_CALLS in cell 5'

# 3. Cell 40 places_nearby() has both guards
src40 = ''.join(cells[40]['source'])
assert 'not ALLOW_LIVE_CALLS' in src40, 'Missing ALLOW_LIVE_CALLS guard in cell 40'
assert '_places_live_calls >= MAX_LIVE_CALLS' in src40, 'Missing MAX_LIVE_CALLS guard in cell 40'

# 4. Sub-radius uses sqrt(2)
assert 'math.sqrt(2)' in src40, 'Missing sqrt(2) in saturation geometry fix'
assert 'radius_m / 2,  radius_m / 2' in src40 or 'radius_m/2' in src40, 'Missing correct offsets'

# 5. sleep gated on live calls in cell 41
src41 = ''.join(cells[41]['source'])
assert '_live_before' in src41, 'Missing _live_before live-call gate in cell 41'

print('T1 verification PASSED')
"
    </automated>
  </verify>
  <done>
- .gitignore: places_cache/ and geocode_cache/ are tracked (git check-ignore returns empty)
- Cell 5: ALLOW_LIVE_CALLS=False and MAX_LIVE_CALLS=200 present
- Cell 40: RuntimeError raised on cache miss when ALLOW_LIVE_CALLS=False; raised when cap hit
- Cell 40: sub-circles use radius/√2 with centres at ±radius/2 — no uncovered annulus
- Cell 40: _places_live_calls incremented once per logical query (not per retry)
- Cells 41/42: sleep wrapped in `if _places_live_calls > _live_before:` guard
  </done>
</task>


<!-- ═══════════════════════════════════════════════════════════
     T2 — Competitor accuracy: site-collapse + CSV extraction
     Findings 5, 6, 7, 8
     Files: cell 51 (full rewrite of load-back bug + build deterministic),
            cell 53 (total = GP-type only),
            cell 55/56/57 (replace with site-collapse + CSV load),
            cell 57 (ALSO: append per_ring_counts recompute after site-collapse),
            cell 62 (prepend scope caveat comment),
            data/local/manual_classifications.csv (new file),
            .gitignore (exception for manual_classifications.csv)
     MUST run before T3.
     ═══════════════════════════════════════════════════════════ -->

<task type="auto">
  <name>T2: Competitor accuracy — site-collapse, CSV extraction, deterministic rebuild (findings 5-8)</name>
  <files>
    Johnston_St_v2.ipynb (cells 51, 53, 55, 56, 57, 62)
    data/local/manual_classifications.csv
    .gitignore
  </files>
  <action>
**Background on current state:**
- Cell 51 builds competitors_gdf from site_places raw data, THEN overwrites it with
  `gpd.read_file(geojson_path)` if the GeoJSON cache exists. This makes classification
  non-deterministic (GeoJSON round-trips `types` list as a string) and hides bugs.
- Cells 55/56/57 run incremental pass-by-pass classification edits on competitors_gdf.
- Cell 57 has a ~64-entry BRAVE_RESULTS Python literal hardcoded in source.
- Cell 53 `total` counts ALL categories including exclude + ambiguous.
- The Healthdirect addition in cell 52 adds new GP records that may already exist in
  Google Places under a different name — double-counting suppressed only by name similarity,
  not address matching during the final collapse.

**Finding 7 — fix cell 51: remove GeoJSON cache as INPUT; rebuild deterministically:**

Replace the final block in cell 51 (from `# D-08: GeoJSON persistence` onwards) with:
```python
# D-08 revised: competitors.geojson is an OUTPUT, never an INPUT.
# Rebuild competitors_gdf deterministically from raw places_cache each run.
# (Prior code loaded from GeoJSON if it existed — GeoJSON mangles `types` list
# to string, making classification non-reproducible. Fixed: always build from raw.)
geojson_path = CACHE_DIR / "competitors.geojson"
# Save output for downstream (maps, peer table) — not used as input on next run.
competitors_gdf.to_file(geojson_path, driver="GeoJSON")
print(f"[competitors] built {len(competitors_gdf)} unique competitors from raw places_cache")
print(f"[competitors] GeoJSON written to {geojson_path.name} (output only — not read back on re-run)")
print(f"[competitors] category breakdown:\n{competitors_gdf['category'].value_counts()}")
```
The full competitors_gdf construction (fuzzy_dedupe_competitors, classify_place loop,
GeoDataFrame build) remains unchanged — only the load-back block is removed.

**Finding 6 — extract BRAVE_RESULTS to data/local/manual_classifications.csv:**

Create `data/local/manual_classifications.csv` with columns:
```
displayName,category,evidence
```
Extract all ~64 tuples from the current cell 57 BRAVE_RESULTS list into this CSV.
Each row corresponds to one `(displayName, category, evidence)` tuple.
Example first rows:
```
displayName,category,evidence
cohealth Innerspace,exclude,cohealth community health — drug safety services not a GP competitor
Flying Needles TCM,exclude,Traditional Chinese Medicine — not a GP clinic
...
```
Include ALL entries from BRAVE_RESULTS (both exclude and gp_independent entries).
Escape commas in the evidence field with standard CSV quoting.

Add a .gitignore exception so this one file is committed despite `data/local/` being ignored:
After the `data/local/` ignore line add:
```
# Exception: curated human-labelled classifications — reproducibility artifact, not bulk data
!data/local/manual_classifications.csv
```

**Finding 5 + 6 — replace cells 55/56/57 with a SINGLE end-of-pipeline site-collapse cell:**

Replace the SOURCE of cells 55, 56, and 57 with three new focused cells:

**Cell 55 replacement — load manual_classifications.csv and apply:**
```python
# §4.4c Apply curated manual classifications from data/local/manual_classifications.csv
# Replaces the old per-pass heuristic cells (§4.4c/d/e).
# CSV columns: displayName, category, evidence
# Source of truth for Brave Search + manual review results — human-auditable artifact.
import pandas as pd

manual_csv_path = PROJECT_ROOT / "data" / "local" / "manual_classifications.csv"
if not manual_csv_path.exists():
    print(f"[manual-classify] ⚠ {manual_csv_path.name} not found — skipping manual classifications")
    manual_applied = 0
else:
    manual_df = pd.read_csv(manual_csv_path)
    manual_applied = 0
    not_found = []
    for _, row in manual_df.iterrows():
        name = str(row["displayName"])
        new_cat = str(row["category"])
        evidence = str(row["evidence"])
        mask = competitors_gdf["displayName"] == name
        if not mask.any():
            mask = competitors_gdf["displayName"].str.contains(name, case=False, na=False)
        if mask.any():
            for idx in competitors_gdf[mask].index:
                if competitors_gdf.loc[idx, "category"] == "ambiguous":
                    competitors_gdf.loc[idx, "category"] = new_cat
                    competitors_gdf.loc[idx, "label"] = f"Manual/Brave: {evidence}"
                    manual_applied += 1
        else:
            not_found.append(name)
    print(f"[manual-classify] Applied {manual_applied} classifications from {manual_csv_path.name}")
    if not_found:
        print(f"[manual-classify] {len(not_found)} names not found (already classified): {not_found[:5]}...")
    print(f"[manual-classify] Remaining ambiguous: {(competitors_gdf['category'] == 'ambiguous').sum()}")
```

**Cell 56 replacement — end-of-pipeline address-based site collapse (D-LOCKED-B):**
```python
# §4.4d End-of-pipeline site collapse — distinct clinic SITES by normalized address
# Locked design (D-LOCKED-B): collapse GP-type records to distinct physical sites;
# use per-site practitioner-listing count as FTE proxy (fallback avg_fte_per_clinic=4).
# This also resolves Healthdirect double-counting: HD additions that share an address
# with a Google Places record collapse to the same site.
import pandas as pd, re

def normalize_addr(addr):
    """Strip suite/level/unit prefixes so co-located practitioners share a site key.
    Reuses the logic from the old §4.4c deduplication step."""
    a = str(addr).lower()
    a = re.sub(r'^(suite?|level?|lvl|unit|floor|flr|ste)[\s\d/]+', '', a)
    a = re.sub(r'[\s,]+', ' ', a).strip()
    return a

GP_CATEGORIES = {"gp_corporate", "gp_independent"}

# Filter to GP-type records only for the site collapse
gp_mask = competitors_gdf["category"].isin(GP_CATEGORIES)
gp_records = competitors_gdf[gp_mask].copy()
gp_records["norm_addr"] = gp_records["formattedAddress"].apply(normalize_addr)

# Group by normalized address → distinct clinic sites
site_groups = gp_records.groupby("norm_addr")
site_rows = []
AVG_FTE = BASE_ASSUMPTIONS["avg_fte_per_clinic"]  # 4.0 fallback
for norm_addr, group in site_groups:
    listing_count = len(group)
    # FTE proxy: practitioner listing count (≥1), fallback to avg_fte_per_clinic
    # if site appears as a single unlisted clinic rather than individual practitioners.
    # Heuristic: if listing_count == 1 and the name looks like a clinic (not a person),
    # treat as avg_fte_per_clinic. Otherwise listing_count IS the FTE proxy.
    looks_like_clinic = not bool(re.search(r'\bdr\.?\b|\bdoctor\b', group.iloc[0]["displayName"], re.I))
    if listing_count == 1 and looks_like_clinic:
        fte_proxy = AVG_FTE
    else:
        fte_proxy = float(listing_count)
    site_rows.append({
        "norm_addr":      norm_addr,
        "site_name":      group.iloc[0]["displayName"],  # representative name
        "listing_count":  listing_count,
        "fte_proxy":      fte_proxy,
        "category":       group.iloc[0]["category"],
        "lat":            group.iloc[0]["lat"],
        "lon":            group.iloc[0]["lon"],
        "ring_km":        group.iloc[0].get("ring_km", None),  # set by cell 53
    })

gp_sites_gdf = gpd.GeoDataFrame(
    site_rows,
    geometry=[Point(r["lon"], r["lat"]) for r in site_rows],
    crs="EPSG:4326"
)

existing_gp_capacity = {}   # ring_m → total FTE (sum of site fte_proxy for sites in ring)
print(f"[site-collapse] {len(gp_records)} GP listings → {len(gp_sites_gdf)} distinct clinic sites")
print(f"[site-collapse] FTE proxies: listing-count where multiple practitioners listed, "
      f"{AVG_FTE} fallback for single-listing clinic entries")
print(f"[site-collapse] ASSUMPTION FLAGGED: practitioner listing count as FTE proxy — "
      f"Google listings are noisy. Treat as range, not point estimate. (D-LOCKED-B)")
```

**Cell 57 replacement — assign ring membership to sites, compute existing_gp_capacity, then recompute per_ring_counts:**
```python
# §4.4e Assign ring membership to GP sites + compute existing_gp_capacity per ring
# existing_gp_capacity[ring_m] = total FTE proxy for distinct GP sites in that ring.
# Consumed by §5.2 (demand model) and §8.1 (demand-constrained verdict). (D-LOCKED-A)
import geopandas as gpd

gp_sites_metric = gp_sites_gdf.to_crs("EPSG:7855")

for radius in BASE_ASSUMPTIONS["catchment_radii_m"]:
    ring_geom = buffers[radius]
    if hasattr(ring_geom, "to_crs"):
        ring_geom = ring_geom.to_crs("EPSG:7855")
    ring_gdf = gpd.GeoDataFrame(geometry=ring_geom, crs="EPSG:7855")
    sites_in_ring = gpd.sjoin(gp_sites_metric, ring_gdf, predicate="within")
    total_fte = sites_in_ring["fte_proxy"].sum()
    site_count = len(sites_in_ring)
    existing_gp_capacity[radius] = total_fte
    print(f"[gp-supply] {radius//1000}km ring: {site_count} distinct GP sites, "
          f"total FTE proxy: {total_fte:.1f} (fallback={BASE_ASSUMPTIONS['avg_fte_per_clinic']} where single-listing clinic)")

# Sanity cap: if FTE proxy exceeds AMWAC benchmark × ring_pop by >2×, warn loudly
for radius in BASE_ASSUMPTIONS["catchment_radii_m"]:
    ring_pop = v2_ring_pops_erp.get(radius, 0)
    if ring_pop > 0:
        benchmark_fte = ring_pop * BASE_ASSUMPTIONS["amwac_per_100k"] / 100_000
        if existing_gp_capacity[radius] > benchmark_fte * 2:
            print(f"⚠ [gp-supply] {radius//1000}km FTE proxy {existing_gp_capacity[radius]:.1f} "
                  f"exceeds 2× AMWAC benchmark ({benchmark_fte:.1f}) — "
                  f"listing-count proxy may overstate supply; review GP sites manually.")

print(f"\n[gp-supply] existing_gp_capacity computed → available for §5 demand model")
print(f"[gp-supply] deposit: existing_gp_capacity = {existing_gp_capacity}")
report["existing_gp_capacity"] = existing_gp_capacity

# §4.4f Recompute per_ring_counts to reflect post-classification GP counts (FIX 4)
# Cell 53 ran BEFORE manual classification (cell 55) and site-collapse (cell 56/57),
# so its GP counts were pre-classification. Recompute here so the §4.8 hero chart
# (cell 64, which runs after this cell) shows accurate post-classification counts.
# Re-runs cell 53's ring-assignment + counting logic on the now-fully-classified
# competitors_gdf so gp_corporate/gp_independent reflect manual CSV reclassifications.
_RING_CATS = ["gp_corporate", "gp_independent", "pharmacy", "allied_health", "ambiguous", "exclude"]
_comp_metric = competitors_gdf.to_crs("EPSG:7855")
_per_ring_rows = []
for radius in BASE_ASSUMPTIONS["catchment_radii_m"]:
    ring_geom = buffers[radius]
    if hasattr(ring_geom, "to_crs"):
        ring_geom = ring_geom.to_crs("EPSG:7855")
    ring_gdf = gpd.GeoDataFrame(geometry=ring_geom, crs="EPSG:7855")
    comps_in = gpd.sjoin(_comp_metric, ring_gdf, predicate="within")
    row = {"ring_km": radius // 1000}
    for cat in _RING_CATS:
        row[cat] = int((comps_in["category"] == cat).sum())
    # total = GP-type only (gp_corporate + gp_independent) — consistent with cell 53 fix
    row["total"] = row["gp_corporate"] + row["gp_independent"]
    _per_ring_rows.append(row)
import pandas as pd as _pd
per_ring_counts = _pd.DataFrame(_per_ring_rows)
print(f"[per-ring-counts] recomputed after manual classification — GP counts reflect CSV reclassifications")
print(per_ring_counts[["ring_km", "gp_corporate", "gp_independent", "total"]].to_string(index=False))
```

**Finding 8 — fix per_ring_counts["total"] in cell 53:**

Replace:
```python
    row["total"] = sum(v for k, v in row.items() if k != "ring_km")
```
With:
```python
    # total = GP-type only (gp_corporate + gp_independent)
    # Excludes exclude, ambiguous, pharmacy, allied_health so the §4.8 hero chart
    # and downstream counts reflect real competitors, not inflated totals.
    row["total"] = row["gp_corporate"] + row["gp_independent"]
```
Also add a comment header to clarify the intent above the per_ring_rows loop:
```python
# NOTE: per_ring_counts["total"] = GP-type only (gp_corporate + gp_independent).
# This drives the §4.8 hero chart competitor counts. Pharmacy/allied/ambiguous/exclude
# are retained as separate columns for audit but not summed into total.
# NOTE: per_ring_counts is RECOMPUTED at end of cell 57 after manual classification
# and site-collapse to ensure §4.8 hero chart shows post-classification GP counts.
```

**FIX 5 — add scope caveat comment to cell 62 (peer GP-per-1,000 table):**

Prepend a one-line comment at the very top of cell 62's source block:
```python
# SCOPE NOTE: GP-per-1,000 here uses pre-site-collapse listing counts (peer context only — not a decision input).
```
This is a comment only — do not alter cell 62's logic. It documents that the peer table's
GP counts come from the raw listing pass (not the site-collapsed gp_sites_gdf) so a future
reader understands the difference without needing to cross-reference cells.
  </action>
  <verify>
    <automated>
python -c "
import json, os

# 1. manual_classifications.csv exists and has expected columns
import csv
csv_path = 'C:/Users/josha/medical-clinic/data/local/manual_classifications.csv'
assert os.path.exists(csv_path), f'CSV not found: {csv_path}'
with open(csv_path, encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
assert 'displayName' in rows[0], 'Missing displayName column'
assert 'category' in rows[0], 'Missing category column'
assert 'evidence' in rows[0], 'Missing evidence column'
assert len(rows) >= 50, f'Too few rows: {len(rows)} (expected ~64)'
print(f'manual_classifications.csv: {len(rows)} rows OK')

# 2. .gitignore has exception for manual_classifications.csv
with open('C:/Users/josha/medical-clinic/.gitignore') as f:
    gi = f.read()
assert '!data/local/manual_classifications.csv' in gi, 'Missing gitignore exception for CSV'

# 3. Cell 51 no longer has the load-back block
with open('C:/Users/josha/medical-clinic/Johnston_St_v2.ipynb', encoding='utf-8') as f:
    cells = json.load(f)['cells']
src51 = ''.join(cells[51]['source'])
assert 'geojson_path.exists() and not FORCE_REFRESH' not in src51, 'Old load-back block still present in cell 51'

# 4. Cell 53 total = GP-type only
src53 = ''.join(cells[53]['source'])
assert 'gp_corporate\"] + row[\"gp_independent' in src53 or \"gp_independent']\" in src53, 'total still sums all categories'

# 5. Cell 56 has normalize_addr and gp_sites_gdf
src56 = ''.join(cells[56]['source'])
assert 'normalize_addr' in src56, 'Missing normalize_addr in cell 56'
assert 'gp_sites_gdf' in src56, 'Missing gp_sites_gdf in cell 56'
assert 'existing_gp_capacity' in src56, 'Missing existing_gp_capacity in cell 56'

# 6. Cell 57 computes existing_gp_capacity, deposits to report, AND recomputes per_ring_counts
src57 = ''.join(cells[57]['source'])
assert 'existing_gp_capacity' in src57, 'Missing existing_gp_capacity computation in cell 57'
assert 'report[\"existing_gp_capacity\"]' in src57, 'Missing report deposit in cell 57'
assert 'BRAVE_RESULTS' not in src57, 'Old BRAVE_RESULTS literal still in cell 57'
assert 'per_ring_counts' in src57, 'Missing per_ring_counts recompute in cell 57'
assert 'post-classification' in src57 or 'recomputed' in src57, 'Missing recompute annotation in cell 57'

# 7. Cell 62 has scope caveat comment
src62 = ''.join(cells[62]['source'])
assert 'pre-site-collapse' in src62 or 'SCOPE NOTE' in src62, 'Missing scope caveat comment in cell 62'

print('T2 verification PASSED')
"
    </automated>
  </verify>
  <done>
- data/local/manual_classifications.csv exists with ~64 rows, columns: displayName, category, evidence
- .gitignore has `!data/local/manual_classifications.csv` exception
- Cell 51: no GeoJSON load-back block; builds competitors_gdf deterministically from raw places_cache
- Cell 53: per_ring_counts["total"] = gp_corporate + gp_independent only; comment notes cell 57 recompute
- Cell 55: loads and applies manual_classifications.csv
- Cell 56: site-collapse → gp_sites_gdf with fte_proxy per site
- Cell 57: ring-assigns gp_sites_gdf → existing_gp_capacity dict, deposits to report dict; BRAVE_RESULTS literal removed
- Cell 57 (appended): recomputes per_ring_counts from fully-classified competitors_gdf so §4.8 hero chart shows post-classification GP counts
- Cell 62: one-line scope caveat comment prepended noting GP-per-1,000 uses pre-site-collapse listing counts (context only)
  </done>
</task>


<!-- ═══════════════════════════════════════════════════════════
     T3 — Demand-constrained verdict
     Findings 9 (locked design D-LOCKED-A)
     Files: cells 68, 71, 79, 101, 102, 5
     DEPENDS ON T2 (existing_gp_capacity must exist before cell 68 wires it)

     ORDERING NOTE: clinic_pnl() is defined at cell 78. achievable_util is set
     at cell 71. Cell 79 runs AFTER both (71 < 78 < 79) so the constrained_pnl
     call and its report deposits are APPENDED TO THE END of cell 79 — NOT
     placed in cell 71. This avoids a NameError on Run All.
     ═══════════════════════════════════════════════════════════ -->

<task type="auto">
  <name>T3: Demand-constrained verdict — wire existing_gp_capacity into P&amp;L + verdict (finding 9)</name>
  <files>
    Johnston_St_v2.ipynb (cells 68, 71, 79, 101, 102, 5)
  </files>
  <action>
**Locked design D-LOCKED-A recap:**
- `existing_gp_capacity` (FTE) comes from T2 (cell 57 deposits to report dict and as a local variable)
- `unmet_demand_consults[r] = max(ring_demand[r] - existing_gp_capacity[r] * gp_fte_consults_per_yr, 0)`
- `achievable_util = min(target_utilisation, unmet_demand_consults[3000] / clinic_full_capacity)`
- Run `clinic_pnl({**BASE_ASSUMPTIONS, "utilisation": achievable_util})` for the constrained P&L
- Gate verdict on constrained EBITDA & margin
- When `achievable_util` is well below target, surface a clear relocation/demand signal

**CRITICAL ORDERING CONSTRAINT — why constrained_pnl call goes in cell 79, not cell 71:**

`clinic_pnl()` is defined at cell 78. Cell 71 runs BEFORE cell 78 in the notebook execution
order (71 < 78 < 79). Calling `clinic_pnl(...)` inside cell 71 causes a `NameError` on
Run All. Cell 79 (the base-case P&L cell) runs after both cell 71 (achievable_util is set)
and cell 78 (clinic_pnl is defined), so `achievable_util` is in scope when cell 79 runs.

Do NOT insert a new cell between 71 and 78 — that would shift every subsequent 0-based
cell index by +1, breaking references to cells 101 and 102 elsewhere in this plan.
Instead, append code to the END of existing cell 79.

**Cell 68 — add unmet_demand computation after ring_demand loop:**

After the existing `ring_demand` loop and plausibility check, add:
```python
# §5.2b Unmet demand — ring_demand minus existing GP consult capacity (D-LOCKED-A)
# existing_gp_capacity[r] is FTE proxy from §4.4e site-collapse.
# Convert FTE to annual consult capacity using gp_fte_consults_per_yr (5500/yr per FTE).
unmet_demand_consults = {}
for r in BASE_ASSUMPTIONS["catchment_radii_m"]:
    gp_fte_in_ring = existing_gp_capacity.get(r, 0)
    supply_consults = gp_fte_in_ring * BASE_ASSUMPTIONS["gp_fte_consults_per_yr"]
    unmet = max(ring_demand[r] - supply_consults, 0)
    unmet_demand_consults[r] = unmet
    saturation_pct = supply_consults / ring_demand[r] * 100 if ring_demand[r] > 0 else 0
    print(f"[unmet-demand] {r//1000}km ring | demand: {ring_demand[r]:.0f} | "
          f"supply: {supply_consults:.0f} ({gp_fte_in_ring:.1f} FTE × 5500) | "
          f"unmet: {unmet:.0f} | saturation: {saturation_pct:.0f}%")

# ASSUMPTION FLAGGED: FTE proxy from listing-count is noisy — unmet_demand is a range, not a point.
# Sensitivity is explored in §7 tornado; surfaced in §8.2 assumptions register.
print("[unmet-demand] NOTE: FTE proxy from practitioner listing count is noisy — "
      "treat unmet_demand as indicative range. See §7 tornado sensitivity.")
report["unmet_demand_consults"] = unmet_demand_consults
```

**Cell 71 — add achievable_util computation ONLY (no clinic_pnl call here):**

After the existing `market_share_results` loop and printed table, add ONLY the
achievable_util computation and its report deposits. Do NOT call `clinic_pnl()` here
(it is not yet defined — see ordering constraint above).
```python
# §5.5b Demand-constrained utilisation ceiling (D-LOCKED-A)
# The primary catchment ring is 3km (BASE_ASSUMPTIONS["catchment_radii_m"][1]).
# achievable_util = min(target, unmet_demand_3km / clinic_full_capacity)
# clinic_full_capacity = 5 FTE × 5500/yr consults = 27,500/yr (at 100% utilisation)
# NOTE: constrained_pnl = clinic_pnl({...achievable_util}) runs in cell 79 (after
# clinic_pnl is defined at cell 78). achievable_util is available there as a local.
_PRIMARY_R = 3000   # 3km primary catchment
_target_util   = BASE_ASSUMPTIONS["utilisation"]          # 0.75
_clinic_cap    = BASE_ASSUMPTIONS["n_gp_fte"] * BASE_ASSUMPTIONS["gp_fte_consults_per_yr"]  # 27500
_unmet_3km     = unmet_demand_consults.get(_PRIMARY_R, 0)

if _clinic_cap > 0 and _unmet_3km > 0:
    _demand_ceil_util = _unmet_3km / _clinic_cap
else:
    _demand_ceil_util = _target_util   # no unmet data — fall back to target (conservative)

achievable_util = min(_target_util, _demand_ceil_util)

print("\n" + "=" * 70)
print("DEMAND-CONSTRAINED UTILISATION")
print("=" * 70)
print(f"Target utilisation (BASE_ASSUMPTIONS):    {_target_util:.1%}")
print(f"Unmet demand 3km ring:                    {_unmet_3km:.0f} consults/yr")
print(f"Clinic full capacity (5 FTE × 5500):      {_clinic_cap:.0f} consults/yr")
print(f"Demand-implied utilisation ceiling:       {_demand_ceil_util:.1%}")
print(f"Achievable utilisation (constrained):     {achievable_util:.1%}")
if achievable_util < _target_util * 0.8:
    print(f"⚠ DEMAND SIGNAL: achievable utilisation ({achievable_util:.1%}) is well below target ({_target_util:.1%}).")
    print(f"  The 3km catchment may not support full books — consider site relocation or smaller FTE headcount.")
print("=" * 70)

# Deposit utilisation values for cell 79 constrained P&L and cell 101 verdict
report["achievable_util"]  = achievable_util
report["demand_ceil_util"] = _demand_ceil_util
```

**Cell 79 — APPEND constrained P&L call and deposits to the END of the existing cell:**

Cell 79 currently ends after the Pitfall 11 range check. Append the following block
to the END of cell 79's source (do not replace any existing content):
```python
# §6.1c Constrained P&L at demand-ceiling utilisation (D-LOCKED-A)
# achievable_util is set in cell 71; clinic_pnl() is defined in cell 78.
# Both are in scope here (cell 79 runs after both). This is intentional —
# calling clinic_pnl() at cell 71 would cause a NameError (defined at 78).
constrained_pnl = clinic_pnl({**BASE_ASSUMPTIONS, "utilisation": achievable_util})
print(f"\n[constrained-pnl] EBITDA at achievable util ({achievable_util:.1%}): "
      f"${constrained_pnl['ebitda']:,.0f} | margin: {constrained_pnl['margin']:.1%}")

# Deposit for verdict (cell 101) and assumptions register (cell 102)
report["constrained_ebitda"]       = constrained_pnl["ebitda"]
report["constrained_margin"]       = constrained_pnl["margin"]
report["constrained_peak_capital"] = constrained_pnl.get("peak_capital", report.get("peak_capital"))
```

Note: `clinic_pnl()` returns the key `"margin"` (NOT `"ebitda_margin"` — verified in cell 78
source). Use `constrained_pnl["margin"]` in both the print line and the report deposit.

**Cell 101 — update verdict logic to gate on CONSTRAINED values:**

The current cell gates on `steady_ebitda` and `steady_margin` from `report["steady_state_ebitda"]`.
Update to:
1. Read constrained values from report dict
2. Gate verdict on constrained EBITDA & margin (not full-books)
3. Surface demand signal when achievable_util is well below target
4. Keep all existing flip_conditions, key_numbers, and verdict text structure

Replace the verdict assignment and key_numbers block:
```python
# Constrained P&L values (D-LOCKED-A) — gate on demand-constrained utilisation
achievable_util  = report.get("achievable_util", BASE_ASSUMPTIONS["utilisation"])
demand_ceil_util = report.get("demand_ceil_util", achievable_util)
constrained_ebitda  = report.get("constrained_ebitda", steady_ebitda)
constrained_margin  = report.get("constrained_margin", steady_margin)
demand_constrained  = achievable_util < BASE_ASSUMPTIONS["utilisation"]

# Verdict gates on CONSTRAINED values (not full-books steady state)
verdict = "GO" if (constrained_ebitda > 0 and constrained_margin > GATE_MARGIN) else "NO-GO"

# Demand signal — surface prominently when achievable_util well below target
demand_signal = ""
if demand_constrained:
    gap = BASE_ASSUMPTIONS["utilisation"] - achievable_util
    if gap > 0.10:   # more than 10 pp below target
        demand_signal = (
            f" ⚠ DEMAND CONSTRAINT: The 3km catchment unmet demand supports only "
            f"{achievable_util:.0%} utilisation (target {BASE_ASSUMPTIONS['utilisation']:.0%}). "
            f"The P&L and verdict reflect this constrained ceiling. "
            f"Consider a smaller initial FTE count or site relocation."
        )
    else:
        demand_signal = (
            f" Demand ceiling: {achievable_util:.0%} (target {BASE_ASSUMPTIONS['utilisation']:.0%}) "
            f"— modest gap, achievable with aggressive patient acquisition."
        )

key_numbers = {
    "constrained_ebitda":   constrained_ebitda,
    "constrained_margin":   constrained_margin,
    "steady_state_ebitda":  steady_ebitda,    # retained as context
    "steady_state_margin":  steady_margin,    # retained as context
    "achievable_util":      achievable_util,
    "peak_capital":         peak_capital,
    "breakeven_operating":  be_operating,
    "breakeven_payback":    be_payback,
}
```

Update the verdict_text to include `demand_signal` and reference constrained values:
In the existing verdict_text f-string, replace references to `steady_ebitda`/`steady_margin`
with `constrained_ebitda`/`constrained_margin`, and append `{demand_signal}` to the text.
Preserve the existing payback_str, operating_str, _flip variables unchanged.

**Cell 102 — add achievable_util and constrained_ebitda to assumptions register:**

After the existing `report["assumptions_register"] = assumptions_register` line, add:
```python
# Append demand-constraint sensitivity note to register
_demand_rows = [
    {
        "Parameter": "achievable_util",
        "Value":     f"{report.get('achievable_util', 'N/A'):.1%}",
        "Source":    "Derived: min(target_util, unmet_demand/clinic_capacity) — D-LOCKED-A",
        "Date":      "2026",
        "Confidence": "LOW"   # Google practitioner listings are noisy
    },
    {
        "Parameter": "existing_gp_capacity_3km_fte",
        "Value":     f"{report.get('existing_gp_capacity', {}).get(3000, 0):.1f} FTE",
        "Source":    "Places API listing-count proxy by clinic site — RACGP/DoH fallback 4.0 FTE",
        "Date":      "2026",
        "Confidence": "LOW"   # noisy proxy
    },
]
for r in _demand_rows:
    assumptions_register = pd.concat([assumptions_register, pd.DataFrame([r])], ignore_index=True)
report["assumptions_register"] = assumptions_register
print(f"[report] §8.2 appended demand-constraint assumptions (achievable_util, existing_gp_capacity_3km)")
print(f"[report] NOTE: achievable_util confidence = LOW (practitioner listing count is noisy — see §4.7 caveat)")
```

**Cell 5 — add achievable_util sensitivity note to BASE_ASSUMPTIONS comments:**

In the `# --- Demand (source: ...)` block, after the `gp_fte_consults_per_yr` line add:
```python
    # NOTE: achievable_util is DERIVED in §5.5b — min(utilisation, unmet_demand/clinic_capacity).
    # It is NOT a BASE_ASSUMPTIONS key; it is computed each run from the demand model.
    # The verdict (§8.1) gates on achievable_util, not utilisation directly.
    # Sensitivity: see §7 tornado and §8.2 assumptions register (confidence LOW).
```
  </action>
  <verify>
    <automated>
python -c "
import json

with open('C:/Users/josha/medical-clinic/Johnston_St_v2.ipynb', encoding='utf-8') as f:
    cells = json.load(f)['cells']

# Cell 68: unmet_demand_consults computed
src68 = ''.join(cells[68]['source'])
assert 'unmet_demand_consults' in src68, 'Missing unmet_demand_consults in cell 68'
assert 'existing_gp_capacity' in src68, 'Missing existing_gp_capacity reference in cell 68'
assert 'report[\"unmet_demand_consults\"]' in src68, 'Missing report deposit in cell 68'

# Cell 71: achievable_util set and deposited; constrained_pnl call ABSENT (it moved to cell 79)
src71 = ''.join(cells[71]['source'])
assert 'achievable_util' in src71, 'Missing achievable_util in cell 71'
assert 'report[\"achievable_util\"]' in src71, 'Missing report[achievable_util] deposit in cell 71'
assert 'report[\"demand_ceil_util\"]' in src71, 'Missing report[demand_ceil_util] deposit in cell 71'
assert 'constrained_pnl' not in src71, 'constrained_pnl call must NOT be in cell 71 (NameError risk — clinic_pnl not yet defined)'
assert 'ebitda_margin' not in src71, 'Wrong key ebitda_margin found in cell 71 — must use margin'

# Cell 79: constrained_pnl call present and uses correct key 'margin'
src79 = ''.join(cells[79]['source'])
assert 'constrained_pnl' in src79, 'Missing constrained_pnl call in cell 79'
assert 'clinic_pnl(' in src79, 'Missing clinic_pnl( call in cell 79'
assert 'ebitda_margin' not in src79, 'Wrong key ebitda_margin in cell 79 — clinic_pnl returns margin not ebitda_margin'
assert 'report[\"constrained_ebitda\"]' in src79, 'Missing constrained_ebitda deposit in cell 79'
assert 'constrained_pnl[\"margin\"]' in src79 or \"constrained_pnl['margin']\" in src79, 'Must use margin key (not ebitda_margin) in cell 79'

# Cell 101: gates on constrained values
src101 = ''.join(cells[101]['source'])
assert 'constrained_ebitda' in src101, 'Cell 101 still gates on steady_ebitda only'
assert 'constrained_margin' in src101, 'Cell 101 missing constrained_margin gate'
assert 'demand_signal' in src101, 'Cell 101 missing demand_signal'
assert 'achievable_util' in src101, 'Cell 101 missing achievable_util'

# Cell 102: demand rows added to register
src102 = ''.join(cells[102]['source'])
assert 'achievable_util' in src102, 'Cell 102 missing achievable_util in register'

print('T3 verification PASSED')
"
    </automated>
  </verify>
  <done>
- Cell 68: unmet_demand_consults[r] computed for each ring, deposited to report dict
- Cell 71: achievable_util = min(target, unmet_demand_3km/clinic_capacity); demand_ceil_util both deposited to report; prints clear demand signal when achievable_util well below target; NO constrained_pnl call (avoids NameError)
- Cell 79: constrained_pnl = clinic_pnl({**BASE_ASSUMPTIONS, "utilisation": achievable_util}) appended to end of existing cell; uses correct key "margin" (not "ebitda_margin") in both print line and report["constrained_margin"] deposit
- Cell 101: verdict gates on constrained_ebitda and constrained_margin; demand_signal included in verdict text
- Cell 102: achievable_util and existing_gp_capacity_3km_fte rows added to assumptions register with LOW confidence
  </done>
</task>


<!-- ═══════════════════════════════════════════════════════════
     T4 — Small: geocode fallback warning (finding 10)
     Files: cell 15
     Independent of T1/T2/T3.
     ═══════════════════════════════════════════════════════════ -->

<task type="auto">
  <name>T4: Loud geocode fallback banner (finding 10, cell 15)</name>
  <files>
    Johnston_St_v2.ipynb (cell 15)
  </files>
  <action>
The current fallback branch (the `else:` when no cache and no API key) prints three quiet
lines. A wrong pin silently corrupts every downstream buffer, catchment population count,
competitor ring assignment, and ultimately the verdict.

Replace the three quiet print statements in the `else:` branch with a loud banner:
```python
else:
    # No cache, no key — use hardcoded fallback coordinates
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # CRITICAL WARNING: USING HARDCODED FALLBACK COORDINATES
    # A wrong pin corrupts: buffers, catchment population, competitor
    # ring assignments, demand model, and the Go/No-Go verdict.
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    site_lat = _SITE_FALLBACK_LAT
    site_lon = _SITE_FALLBACK_LON
    site_place_id = ""
    banner = "\n" + "!" * 70
    banner += "\n  GEOCODE FALLBACK ACTIVE — HARDCODED COORDINATES IN USE"
    banner += f"\n  lat={site_lat}, lon={site_lon}"
    banner += "\n"
    banner += "\n  WHY: No geocode cache found AND no GOOGLE_PLACES_KEY set."
    banner += "\n"
    banner += "\n  RISK: If these coordinates are wrong, every downstream calculation"
    banner += "\n  is silently corrupt: 1/3/5 km buffers, catchment population,"
    banner += "\n  competitor ring assignment, demand model, and the verdict."
    banner += "\n"
    banner += "\n  TO FIX (pick one):"
    banner += "\n    (a) Commit the geocode_cache/ directory (git pull in Colab)"
    banner += "\n    (b) Set GOOGLE_PLACES_KEY in Colab secrets and re-run this cell"
    banner += "\n        with FORCE_REFRESH=True to generate the cache."
    banner += "\n    (c) Verify the fallback coordinates match 292-296 Johnston St"
    banner += "\n        on the map below before proceeding."
    banner += "\n" + "!" * 70 + "\n"
    print(banner)
    print(f"[geocode] {SITE_ADDRESS}")
    print(f"[geocode] lat={site_lat:.6f}, lon={site_lon:.6f} (FALLBACK — hardcoded)")
    print(f"[geocode] ⚠ Verify on the map below before proceeding further.")
```
  </action>
  <verify>
    <automated>
python -c "
import json
with open('C:/Users/josha/medical-clinic/Johnston_St_v2.ipynb', encoding='utf-8') as f:
    cells = json.load(f)['cells']
src15 = ''.join(cells[15]['source'])
assert 'GEOCODE FALLBACK ACTIVE' in src15, 'Missing loud banner in cell 15 fallback'
assert 'silently corrupt' in src15.lower() or 'corrupt' in src15, 'Missing corruption risk language'
assert '!' * 20 in src15, 'Banner not visually prominent (missing !!!...)'
assert 'TO FIX' in src15, 'Missing TO FIX instructions in fallback'
print('T4 verification PASSED')
"
    </automated>
  </verify>
  <done>
Cell 15 else-branch emits a multi-line banner with !!! borders, explains the corruption risk,
and gives three concrete fix options. The prior three quiet print lines are replaced.
  </done>
</task>


<!-- ═══════════════════════════════════════════════════════════
     T5 — Commit the 1781 cache files
     Independent of T2/T3/T4 but logically first commit.
     ═══════════════════════════════════════════════════════════ -->

<task type="auto">
  <name>T5: Commit the 1781 places_cache + geocode_cache files as a standalone commit</name>
  <files>
    data/cache/places_cache/ (1781 JSON files)
    data/cache/geocode_cache/ (1 JSON file)
  </files>
  <action>
After T1 un-ignores the cache directories, stage and commit ONLY the cache files in a
dedicated commit. This keeps the cache addition atomic and reviewable separately from the
notebook edits.

Run in sequence:
```bash
# Verify no API keys in cache files before staging (spot-check)
python -c "
import os, json, glob
cache_dirs = ['data/cache/places_cache', 'data/cache/geocode_cache']
key_patterns = ['key', 'api_key', 'secret', 'token']
issues = []
for d in cache_dirs:
    for f in glob.glob(os.path.join(d, '*.json'))[:20]:  # spot-check first 20
        try:
            raw = open(f, encoding='utf-8').read().lower()
            for kw in key_patterns:
                if kw + '\"' in raw or kw + ':' in raw:
                    issues.append(f'{f}: suspicious keyword {kw!r}')
        except: pass
if issues:
    print('STOP: possible secret in cache:', issues)
else:
    print(f'Spot-check OK — no API key patterns in first 20 files of each dir')
"

# Stage ONLY the cache files
rtk git add data/cache/places_cache/ data/cache/geocode_cache/

# Verify staged count is ~1782 (1781 + 1)
rtk git status

# Commit
rtk git commit -m "feat(cache): commit 1781 Places + geocode JSON cache files

Un-ignored from .gitignore (finding 1): these files contain NO API keys,
only place records and lat/lon coordinates. Committing so Colab clones
receive the full cache and cannot incur live API billing on re-run.

This is the primary fix for the ~500 AUD Google Places API bill caused by
cache-less Colab sessions. Cache files are deterministic output of the
Places API (New) manual-cache system in cell 40."
```

Note: if git add times out due to 1781 files, use:
```bash
rtk git add data/cache/
```
(only the JSON files match — redirects.sqlite is still gitignored by the existing rule).
  </action>
  <verify>
    <automated>
python -c "
import subprocess, os
result = subprocess.run(
    ['git', 'log', '--oneline', '-3'],
    capture_output=True, text=True,
    cwd='C:/Users/josha/medical-clinic'
)
print('Recent commits:', result.stdout)

# Verify cache files are now tracked
result2 = subprocess.run(
    ['git', 'ls-files', 'data/cache/places_cache/'],
    capture_output=True, text=True,
    cwd='C:/Users/josha/medical-clinic'
)
count = len([l for l in result2.stdout.splitlines() if l.strip()])
print(f'Tracked places_cache files: {count}')
assert count >= 1700, f'Too few tracked files: {count} (expected ~1781)'

result3 = subprocess.run(
    ['git', 'ls-files', 'data/cache/geocode_cache/'],
    capture_output=True, text=True,
    cwd='C:/Users/josha/medical-clinic'
)
gc_count = len([l for l in result3.stdout.splitlines() if l.strip()])
print(f'Tracked geocode_cache files: {gc_count}')
assert gc_count >= 1, 'geocode_cache not tracked'
print('T5 verification PASSED')
"
    </automated>
  </verify>
  <done>
~1782 cache files committed in a single atomic commit. `git ls-files data/cache/places_cache/`
returns ~1781 entries. The commit message explains why these files are safe to commit (no secrets).
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| ALLOW_LIVE_CALLS guard | Prevents accidental live API billing; user must explicitly set True |
| .gitignore | Controls what secrets/API responses travel to Colab via public repo |
| manual_classifications.csv | Human-curated data — could be tampered if repo access is compromised |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-gif-01 | Information Disclosure | data/cache/places_cache/ committed to git | mitigate | Spot-check in T5 action: grep first 20 files for key/secret/token patterns before staging. Verified: only place records + lat/lon in responses |
| T-gif-02 | Elevation of Privilege | ALLOW_LIVE_CALLS=False bypass | accept | Guard is purely financial (cost control), not a security boundary. User controls their own API key budget |
| T-gif-03 | Tampering | manual_classifications.csv edited to misclassify competitors | accept | Low-value target; file is committed and auditable in git history. Intentional manipulation would require repo access |
| T-gif-04 | Information Disclosure | geocode fallback uses hardcoded lat/lon from public address | accept | 292-296 Johnston St is a publicly listed commercial address; no PII exposure |
</threat_model>

<verification>
End-to-end structural checks after all tasks complete:

```bash
# 1. Cache files are tracked
python -c "
import subprocess
r = subprocess.run(['git', 'ls-files', 'data/cache/places_cache/'], capture_output=True, text=True, cwd='C:/Users/josha/medical-clinic')
count = len(r.stdout.splitlines())
print(f'Tracked places_cache files: {count}')
assert count >= 1700
"

# 2. Key notebook cells contain required identifiers
python -c "
import json
with open('C:/Users/josha/medical-clinic/Johnston_St_v2.ipynb', encoding='utf-8') as f:
    cells = json.load(f)['cells']
checks = {
    5:   ['ALLOW_LIVE_CALLS', 'MAX_LIVE_CALLS'],
    15:  ['GEOCODE FALLBACK ACTIVE', 'silently corrupt'],
    40:  ['not ALLOW_LIVE_CALLS', 'math.sqrt(2)', '_places_live_calls >= MAX_LIVE_CALLS'],
    41:  ['_live_before'],
    51:  [],  # no load-back
    53:  ['gp_corporate\"] + row[\"gp_independent'],
    55:  ['manual_classifications.csv'],
    56:  ['gp_sites_gdf', 'normalize_addr', 'existing_gp_capacity'],
    57:  ['existing_gp_capacity', 'report[\"existing_gp_capacity\"]', 'per_ring_counts'],
    62:  ['SCOPE NOTE'],
    68:  ['unmet_demand_consults', 'existing_gp_capacity'],
    71:  ['achievable_util', 'report[\"achievable_util\"]'],
    79:  ['constrained_pnl', 'clinic_pnl(', 'report[\"constrained_ebitda\"]'],
    101: ['constrained_ebitda', 'constrained_margin', 'demand_signal'],
    102: ['achievable_util'],
}
for idx, patterns in checks.items():
    src = ''.join(cells[idx]['source'])
    for p in patterns:
        assert p in src, f'Cell {idx}: missing pattern {p!r}'
    if idx == 51:
        assert 'geojson_path.exists() and not FORCE_REFRESH' not in src, 'Cell 51: old load-back still present'
    if idx == 57:
        assert 'BRAVE_RESULTS' not in src, 'Cell 57: BRAVE_RESULTS literal still present'
    if idx == 71:
        assert 'constrained_pnl' not in src, 'Cell 71: constrained_pnl must NOT be here (NameError risk)'
    if idx == 79:
        assert 'ebitda_margin' not in src, 'Cell 79: wrong key ebitda_margin (must use margin)'
print('All structural checks PASSED')
"

# 3. manual_classifications.csv present and has >=50 rows
python -c "
import csv, os
path = 'C:/Users/josha/medical-clinic/data/local/manual_classifications.csv'
assert os.path.exists(path)
rows = list(csv.DictReader(open(path, encoding='utf-8')))
print(f'manual_classifications.csv: {len(rows)} rows, cols: {list(rows[0].keys())}')
assert len(rows) >= 50
"
```
</verification>

<success_criteria>
- .gitignore: places_cache/ and geocode_cache/ are tracked (git check-ignore returns empty for a file in each dir)
- ~1782 cache files committed in one atomic commit (T5), travelling to Colab via git clone
- Cell 5: ALLOW_LIVE_CALLS=False and MAX_LIVE_CALLS=200 present as module-level globals
- Cell 40: places_nearby() raises RuntimeError on cache miss when ALLOW_LIVE_CALLS=False; raises when cap hit; sub-circles use radius/√2 geometry; _places_live_calls incremented once per logical call
- Cells 41/42: sleep gated on `_places_live_calls > _live_before`
- Cell 15: loud !!! banner in fallback branch with corruption risk and fix instructions
- Cell 51: no GeoJSON load-back block; always rebuilds from raw places_cache
- Cell 53: per_ring_counts["total"] = gp_corporate + gp_independent only
- Cell 55: loads manual_classifications.csv and applies to competitors_gdf
- Cell 56: gp_sites_gdf with fte_proxy per distinct normalized-address site; existing_gp_capacity dict initialised
- Cell 57: ring-assigns sites, computes existing_gp_capacity per ring, deposits to report; BRAVE_RESULTS literal absent; per_ring_counts recomputed from fully-classified competitors_gdf after site-collapse
- Cell 62: one-line scope caveat comment noting GP-per-1,000 uses pre-site-collapse listing counts
- data/local/manual_classifications.csv: ~64 rows, columns displayName/category/evidence; committed via .gitignore exception
- Cell 68: unmet_demand_consults computed per ring; deposited to report
- Cell 71: achievable_util = min(target, unmet_demand_3km/clinic_capacity) and demand_ceil_util deposited to report; loud demand signal when gap > 10pp; NO constrained_pnl call (clinic_pnl not yet defined at this cell index)
- Cell 79: constrained_pnl = clinic_pnl({**BASE_ASSUMPTIONS, "utilisation": achievable_util}) appended to end of existing cell; uses "margin" key (not "ebitda_margin") in print and report["constrained_margin"] deposit
- Cell 101: verdict gates on constrained_ebitda + constrained_margin; demand_signal in verdict text
- Cell 102: achievable_util and existing_gp_capacity_3km_fte rows in assumptions register (confidence LOW)
</success_criteria>

<output>
After completion, create `.planning/quick/260711-gif-fix-batch-of-caching-competitor-accuracy/260711-gif-SUMMARY.md`
</output>
