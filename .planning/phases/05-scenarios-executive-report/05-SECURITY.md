---
phase: 05
slug: scenarios-executive-report
status: verified
threats_open: 0
asvs_level: 1
created: 2026-07-06
---

# Phase 05 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| TB-05-1 | Notebook computation → HTML/PDF report output (Jinja2 template render) | Computed financial metrics, scenario results, citation text — all developer-authored or derived from internal computation. No external/user input. |
| TB-05-2 | BASE_ASSUMPTIONS source code → assumptions register (regex parsing) | Developer-authored inline code comments (`# source — date [confidence]`) parsed via regex into 5-column DataFrame. No external data. |
| TB-05-3 | Colab environment → system packages (subprocess pip/apt-get) | Hardcoded package names (`weasyprint`, `libpango-1.0-0`, `libpangocairo-1.0-0`). No user input. Colab-gated. |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-05-01 | Tampering / Information Spoofing | §8.3 Jinja2 HTML template rendering (`Template(...).render()`, line 772) | accept | `autoescape=False` on bare `Template` class; `{{ row['Source'] }}` renders assumptions register values unescaped. Accepted: data source is developer-authored code comments in BASE_ASSUMPTIONS — no external/user input path. Report is a static document, not a web application. | closed |
| T-05-02 | Elevation of Privilege | §8.4 subprocess calls (lines 793-794) | mitigate | List-form `subprocess.run([...], check=True)` with hardcoded string literals — no `shell=True`, no user input in arguments. Colab-gated via `IS_COLAB` check. | closed |
| T-05-03 | Information Disclosure | §8 `report{}` accumulator → HTML/PDF output | mitigate | Grep verified zero references to `GOOGLE_PLACES_KEY`, `userdata`, `api_key`, `.env`, `load_dotenv` in Phase 5 generator. `report{}` contains only computed financial metrics + developer-authored citation text. API key loaded in §0 setup, never deposited into `report{}`. | closed |
| T-05-04 | Denial of Service | §8.4 weasyprint PDF generation (lines 791-800) | mitigate | Wrapped in `try/except Exception` with graceful fallback to HTML-only output (PIPE-04 no-hard-fail pattern). Local Windows produces HTML only with printed note (D-18). | closed |
| T-05-05 | Denial of Service | §8.3 `_img_b64()` missing figure handling (line 640) | mitigate | Defensive check: `if not p.exists(): return ""` — missing PNG figures render as empty, do not crash the report. | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-05-01 | T-05-01 | Jinja2 template uses `autoescape=False`. The `{{ row['Source'] }}` expression renders assumptions register values without HTML escaping. Accepted because: (1) the data source is developer-authored inline code comments in BASE_ASSUMPTIONS — no external or user-controlled input reaches the template; (2) the report is a static HTML/PDF document, not a web application served to browsers with session context; (3) all other template variables are computed numeric metrics (EBITDA, margin, peak capital) or hardcoded string literals (verdict text, citations). If the notebook is later extended to render external/API-sourced text into the report, autoescape must be enabled (`jinja2.Environment(autoescape=True)`). | gsd-secure-phase agent | 2026-07-06 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-07-06 | 5 | 5 | 0 | gsd-secure-phase agent |

### Audit Notes

- **Phase type:** Financial modeling notebook + executive report generator. No external attack surface (no auth, no network endpoints, no user input handling, no PII).
- **Input state:** State B — no prior SECURITY.md; threat register derived from PLAN.md + SUMMARY.md artifacts and implementation code review.
- **Code reviewed:** `scripts/extend_v2_notebook_phase5.py` (906 lines) — generator script producing §7 Scenarios & Sensitivity + §8 Executive Report notebook cells.
- **No threat_model block** was present in either 05-01-PLAN.md or 05-02-PLAN.md. Threats were derived from the implemented code patterns (Jinja2 template, subprocess calls, report accumulator, file I/O).
- **ASVS Level 1** (default) — appropriate for a non-networked analytical notebook.
- **Future milestone consideration:** If the notebook is ever converted to a served web application (e.g., interactive dashboard — deferred per 05-02-SUMMARY.md), T-05-01 must be re-evaluated and autoescape enabled.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-07-06
