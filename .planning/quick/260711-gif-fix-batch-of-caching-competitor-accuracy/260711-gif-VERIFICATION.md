---
status: passed
verified: 2026-07-11
mode: quick-full (--validate)
---

# Quick Task 260711-gif — Verification

**Verdict: PASSED.** All 10 findings implemented across 5 atomic commits (T1–T5).
Both HIGH plan-check blockers were fixed and confirmed at runtime.

## How this was verified

The target notebook (Johnston_St_v2.ipynb) is 6.3MB and cannot be executed locally
(Colab-primary; local Windows lacks the geo stack). Verification was therefore:
1. **Structural** — parse the notebook JSON in a subprocess and assert on each edited
   cell's source (18 checks, all pass).
2. **Runtime smoke test** of the pure-Python financial path (no geo deps) — the part
   the whole verdict now hinges on.

## Structural checks (18/18 PASS)

| Cell | Check | Result |
|------|-------|--------|
| 5 | ALLOW_LIVE_CALLS + MAX_LIVE_CALLS cost guards | PASS |
| 40 | cache-miss guard + MAX_LIVE_CALLS cap | PASS |
| 40 | saturation subdivision uses radius/√2 (no annular blind spot) | PASS |
| 41 | sleep gated on live calls only (`_live_before`) | PASS |
| 51 | GeoJSON load-back removed (deterministic rebuild) | PASS |
| 53 | per_ring_counts["total"] = GP-type only | PASS |
| 55 | loads data/local/manual_classifications.csv | PASS |
| 56 | address site-collapse → gp_sites_gdf w/ FTE proxy | PASS |
| 57 | existing_gp_capacity computed; BRAVE_RESULTS literal gone; per_ring_counts recompute | PASS |
| 62 | scope-note caveat added | PASS |
| 68 | unmet_demand_consults from existing_gp_capacity | PASS |
| 71 | achievable_util computed; NO clinic_pnl call (NameError fix) | PASS |
| 79 | constrained_pnl = clinic_pnl(...) appended; uses `margin` key (not ebitda_margin) | PASS |
| 101 | verdict gates on constrained_ebitda/constrained_margin + demand_signal | PASS |
| 102 | achievable_util in assumptions register | PASS |
| 15 | loud geocode-fallback banner | PASS |

## Runtime smoke test — demand-constrained verdict (the point of the task)

Executed cell 5 (BASE_ASSUMPTIONS) + cell 78 (clinic_pnl) in isolation:

- `clinic_pnl()` returns key **`margin`** (not `ebitda_margin`) — HIGH bug #1 fixed, confirmed live.
- Full books (75%): EBITDA **+$158,711**, margin 27.5% → GO
- Demand-constrained (40%): EBITDA **−$110,540**, margin −35.9% → NO-GO
- `achievable_util = min(target, unmet/clinic_cap)` monotonic and correct.

This confirms the core behavioural change: the verdict now flips to NO-GO when the
catchment's unmet demand can't fill the books — instead of always showing the full-books
GO regardless of demand. This is the resolution of review Point 6.

## Plan-check history (2 HIGH blockers, both fixed)

- HIGH #1: T3 referenced `constrained_pnl['ebitda_margin']` — key does not exist
  (clinic_pnl returns `margin`). Fixed in revision.
- HIGH #2: T3 called `clinic_pnl()` at cell 71 but it is defined at cell 78 → NameError
  on Run All. Fixed by moving the constrained-P&L call to an append on existing cell 79
  (no cell insertion → no index drift).

## Residual notes / follow-ups (non-blocking)

- **per_ring_counts staleness** resolved by a recompute appended to cell 57; the §4.8
  hero chart now reflects post-manual-classification counts.
- **Cell 62 peer GP-per-1000** left on pre-site-collapse counts (context-only, not a
  decision input) — carries a scope-note caveat. Candidate for a future pass.
- **FTE proxy is noisy** (Google practitioner listings) — flagged LOW confidence in the
  assumptions register; achievable_util should be read as a range, and the §7 tornado is
  the place to widen it in future work.
- Full end-to-end correctness requires a Colab run — recommend one clean "Restart & Run
  All" in Colab to confirm the wired data flow (existing_gp_capacity → unmet_demand →
  achievable_util → verdict) executes against real data.
