---
phase: 2
slug: catchment-demographics
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-05
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python `assert` + `scripts/validate_v2_notebook.py` (extended from Phase 1) |
| **Config file** | `scripts/validate_v2_notebook.py` (re-runnable structural + content checks) |
| **Quick run command** | `python scripts/validate_v2_notebook.py` |
| **Full suite command** | `python scripts/validate_v2_notebook.py && python -c "import json; json.load(open('Johnston_St_v2.ipynb'))"` |
| **Estimated runtime** | ~3 seconds |

> This is a notebook project, not a unit-tested application. Validation is structural (notebook JSON integrity, cell presence, v1-flaw eradication) + execution-time (in-notebook `assert` statements that fail loudly on Restart & Run All). The Phase 1 validator is extended with Phase 2 checks; no separate pytest suite is introduced.

---

## Sampling Rate

- **After every task commit:** Run `python scripts/validate_v2_notebook.py`
- **After every plan wave:** Run full suite command + manual cell-count check
- **Before `/gsd-verify-work`:** Full suite green + in-notebook asserts pass on a fresh Restart & Run All (Colab primary, Windows local secondary)
- **Max feedback latency:** 5 seconds (structural) / one notebook run (execution-time)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | GEO-01 | — | N/A (no PII; address is public) | structural + execution | `python scripts/validate_v2_notebook.py` (geocode cell present) | ✅ | ⬜ pending |
| 02-01-02 | 01 | 1 | GEO-02 | — | N/A | execution (in-notebook assert) | `assert abs(buffers[3000].area.iloc[0]/1e6 - 28.27) < 0.1` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | GEO-03 | — | N/A | execution (in-notebook assert) | `assert 80e3 < ring_pop_3k < 110e3` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 1 | GEO-04 | — | N/A | structural | `validate_v2_notebook.py` (folium + contextily cells present) | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 2 | DEMO-01 | — | N/A | structural + execution | `validate_v2_notebook.py` (ABS G01/G02 fetch cells present); in-notebook fallback warning | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 2 | DEMO-02 | — | N/A | structural | `validate_v2_notebook.py` (peer comparison chart cell present) | ❌ W0 | ⬜ pending |
| 02-02-03 | 02 | 2 | DEMO-03 | — | N/A | structural | `validate_v2_notebook.py` (peer benchmarking table cell present) | ❌ W0 | ⬜ pending |
| 02-02-04 | 02 | 2 | DEMO-04 | — | N/A | structural + execution | `validate_v2_notebook.py` (ERP scaling cell present); in-notebook caveat print | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `scripts/validate_v2_notebook.py` extended with Phase 2 checks (geocode, buffer, apportionment, ABS G01/G02/G04, ERP, maps, v1-vs-v2 comparison)
- [ ] `data/local/SA1_2021_AUST_GDA2020.zip` documented in `.env.example` (manual download step)

*If neither is feasible: existing Phase 1 validator + in-notebook asserts cover the critical path; the validator extension is a nice-to-have, not a blocker.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Geocode pin visually matches Johnston St × Hoddle St corner | GEO-01 / D-31 | Visual map verification | Run §1.2 geocode cell; confirm the folium pin in the immediately-following map cell sits on the Johnston St × Hoddle St end of the block, not the postcode centroid |
| Catchment map shows Yarra River annotation | D-05 | Visual | Run §2 map cell; confirm the Yarra River line is annotated on the folium map and the static matplotlib figures |
| Peer comparison chart highlights POA 3067 | DEMO-02 / D-29 | Visual | Run §3 chart cell; confirm 3067 is highlighted in each of the 4 sub-charts |
| v1-vs-v2 comparison shows v1 inflating 2–4× | D-06 / success criterion #2 | Visual + arithmetic | Run §2 comparison cell; confirm the side-by-side table + grouped bar chart show v1 naive > v2 apportioned by ~2–4× per ring |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s (structural) / one notebook run (execution-time)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
