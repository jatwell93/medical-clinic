# Colab Setup Guide — Johnston St Medical Clinic Feasibility Notebook

This guide walks you through everything needed to run `Johnston_St_v2.ipynb`
end-to-end in Google Colab via **Runtime → Restart & Run All**.

The notebook is designed to degrade gracefully — most missing files trigger a
printed warning and a fallback rather than a hard crash. The two **hard
requirements** are:

1. **Google Places API key** (for geocoding + competitor search — no fallback)
2. **POA shapefile** (for catchment geometry — no fallback)

Everything else has a fallback path, but for investor-grade output you should
upload all the files listed below.

---

## Step 1 — Open the notebook in Colab

1. Go to [colab.research.google.com](https://colab.research.google.com)
2. **File → Open notebook → GitHub** tab
3. Enter your repo: `jatwell93/medical-clinic`
4. Select `Johnston_St_v2.ipynb`

> The notebook's §0.2 cell auto-clones the repo to `/content/medical-clinic`
> on first run, which brings the committed `data/cache/` ABS responses with
> it (free re-runs of ABS calls).

---

## Step 2 — Add your Google Places API key (REQUIRED)

The notebook reads this from Colab Secrets — it never appears in the notebook
source or git history.

1. In Colab, click the **🔑 key icon** in the left sidebar
2. Click **+ New secret**
3. **Name:** `GOOGLE_PLACES_KEY`
4. **Value:** paste your Google Places API key
5. Toggle **Notebook access** ON

### Getting a key (if you don't have one)

1. Go to [Google Cloud Console](https://console.cloud.google.com/google/maps-apis/credentials)
2. Create a project (or use an existing one)
3. **Enable APIs:** Places API (New), Geocoding API
4. **Create credentials → API key**
5. Copy the key into Colab Secrets (step above)

**Cost:** Nearby Search (New) Pro = US$32/1k requests, 5,000 free/month.
This notebook makes ~15–200 requests total (cached after first run). Expect
**~$0–$2 USD** for a single end-to-end run. Re-runs are free (cached).

> **No ABS API key is needed.** The ABS Data API is free and unauthenticated.
> The notebook caches ABS responses to `data/cache/` (committed to git), so
> ABS calls are also free on re-runs.

---

## Step 3 — Upload data files to Colab (REQUIRED + recommended)

The notebook's §0.2 cell clones the repo, which includes `data/cache/` (ABS
API responses — makes ABS re-runs free) but **not** `data/local/` (gitignored
— large manual-download files). You need to upload the local data files.

### How to upload

The notebook includes a dedicated **§0.4 "Upload Local Data Files"** cell
(Colab only — it's a no-op on Windows). After the §0.2 cell clones the repo,
run the §0.4 cell to open a file picker and select the four files below. Then
do **Runtime → Restart & Run All**.

> The §0.4 cell moves uploaded files into `/content/medical-clinic/data/local/`
> automatically. On a fresh Colab runtime you must re-upload (Colab storage is
> ephemeral).

> **Alternative:** Use the left sidebar **Files** tab → drag and drop into
> `/content/medical-clinic/data/local/` (create the folder first). This skips
> the §0.4 cell entirely.

### Files to upload

| # | File | Required? | Source | What happens if missing |
|---|------|-----------|--------|------------------------|
| 1 | `POA_2021_AUST_GDA2020_SHP.zip` | **YES** (hard crash) | [ABS digital boundaries](https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard/asgs/edition-3-july-2021-june-2026/access-and-downloads/digital-boundary-files) — "Postal Areas" | Notebook cannot build catchment rings |
| 2 | `SA1_2021_AUST_GDA2020.zip` | Recommended (degraded fallback) | Same ABS page — "Statistical Area Level 1" | Falls back to POA-level apportionment (coarser) |
| 3 | `medicare-quarterly-statistics-statistical-area-sa3-summary-march-quarter-2025-26.xlsx` | Recommended (state fallback exists) | [health.gov.au](https://www.health.gov.au/resources/publications/medicare-quarterly-statistics-statistical-area-sa3-summary-march-quarter-2025-26) — published 25 May 2026 | Falls back to VIC state average (less local) |
| 4 | `aihw-phc-19-csv_file_2425.csv` (extract from zip) | Recommended (national fallback exists) | [AIHW](https://www.aihw.gov.au/reports/primary-health-care/medicare-subsidised-gp-allied-health-specialist) — click "Data" tab, download `aihw-phc-019-csv-file-2324-2425.zip`, then **extract the CSV** from the zip | Falls back to national average age-band rates |

> **Check your `data/local/` folder before uploading.** You need all four
> files for best results. Common issues:
> - **File 2 (SA1):** Make sure you have `SA1_2021_AUST_GDA2020.zip` (the
>   shapefile), not `SA3_2021_AUST.xlsx` (a reference table — wrong file).
> - **File 3 (MBS):** Make sure you have the **SA3 Summary** file
>   (`...statistical-area-sa3-summary...`), not the **Primary Care Service
>   Type Summary** file (`...primary-care-service-type-summary...`). The
>   latter is state-level only — no SA3 data (Pitfall 6).
> - **File 4 (AIHW):** The download is a **zip** containing CSV files (not
>   xlsx). Extract `aihw-phc-19-csv_file_2425.csv` from the zip and upload
>   that CSV.

### Download links (direct)

- **ABS boundaries:** <https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard/asgs/edition-3-july-2021-june-2026/access-and-downloads/digital-boundary-files>
  - Download: `SA1_2021_AUST_GDA2020.zip` (~150 MB)
  - Download: `POA_2021_AUST_GDA2020_SHP.zip` (~50 MB)
- **MBS SA3 Summary:** <https://www.health.gov.au/resources/publications/medicare-quarterly-statistics-statistical-area-sa3-summary-march-quarter-2025-26>
  - Download: the `.xlsx` file (~5 MB)
- **AIHW age-band rates:** <https://www.aihw.gov.au/reports/primary-health-care/medicare-subsidised-gp-allied-health-specialist>
  - Click the **Data** tab → download `aihw-phc-019-csv-file-2324-2425.zip` (~210 MB)
  - **Extract the zip** and upload `aihw-phc-19-csv_file_2425.csv` (the 2024-25 data file, ~109 MB)
  - The zip also contains `aihw-phc-19-csv_file_2324.csv` (2023-24) and a metadata xlsx — you only need the 2425 CSV

---

## Step 4 — Restart & Run All

1. **Runtime → Restart and Run All** (or `Ctrl+F8`)
2. Watch the output — the notebook prints `[env]`, `[abs]`, `[geom]`,
   `[demand]`, `[pnl]`, `[ramp]` status lines as it progresses
3. Expected runtime: **~3–5 minutes** (first run with API calls) or
   **~1 minute** (cached re-run)

### What you should see

| Section | Key output |
|---------|------------|
| §0.2 | `IN_COLAB=True`, `Google Places key: loaded` |
| §1.2 | `[geocode] lat=-37.80..., lon=144.99...` (Abbotsford) |
| §2 | `[geom] POA: N VIC polygons`, `3km buffer area ≈ 28.27 km² ✓` |
| §3 | `[abs] G01/G02 from API (from_cache=...)` |
| §5 | `[demand] 3km ring per_capita_rate: ~600-700/100` |
| §6 | `EBITDA: $264,507`, `Margin: 39.3%` |
| §6.2 | `Operating breakeven: month 10`, `Peak capital: $504,644` |
| §8 | `VERDICT: GO` |

---

## Step 5 — Download the PDF report (optional)

After a successful run, the executive PDF is generated at:
`/content/medical-clinic/outputs/Johnston_St_Feasibility_Report.pdf`

Download it via the left sidebar **Files** tab, or run:

```python
from google.colab import files
files.download("/content/medical-clinic/outputs/Johnston_St_Feasibility_Report.pdf")
```

> PDF generation requires `weasyprint` — the install cell (§0.1) handles
> this automatically in Colab.

---

## Troubleshooting

### "No GOOGLE_PLACES_KEY and no cached geocode response"
→ You didn't add the key to Colab Secrets, or Notebook access is OFF.
Go back to Step 2.

### "SA1 shapefile missing — falling back to POA-level apportionment"
→ You didn't upload `SA1_2021_AUST_GDA2020.zip`. The notebook still runs,
but catchment apportionment is coarser. Upload it for best results.

### "⚠ STATE BENCHMARK, NOT LOCAL — SA3 20607 data not found"
→ You didn't upload the MBS SA3 xlsx, or you uploaded the wrong file
(the state-level "Primary Care Service Type Summary" instead of the
"Statistical Area SA3 Summary"). The notebook falls back to VIC state
average. Download the correct SA3-level file from the health.gov.au link
in Step 3 and upload it for SA3-level (Yarra) demand signal.

### "⚠ AIHW age-band data not found. Using national average fallback."
→ You didn't upload the AIHW CSV. The notebook uses national average
age-band rates (the same values in `BASE_ASSUMPTIONS`). Download the
AIHW zip, extract `aihw-phc-19-csv_file_2425.csv`, and upload it
for SA3-level rates.

### ABS API calls fail (network/timeout)
→ The notebook caches ABS responses in `data/cache/` (committed to git).
If the repo clone succeeds, ABS calls should hit cache. If you see
`from_cache=True`, the cache is working. If ABS is down, the notebook
falls back to local GCP files (if uploaded) or prints a warning.

### Google Places API quota exceeded
→ The free tier gives 5,000 Nearby Search requests/month. This notebook
uses ~15–200. If you've exhausted the free tier elsewhere, wait for the
monthly reset or enable billing on your Google Cloud project.

---

## Quick checklist

- [ ] Open notebook in Colab (GitHub tab)
- [ ] Add `GOOGLE_PLACES_KEY` to Colab Secrets (notebook access ON)
- [ ] Upload `POA_2021_AUST_GDA2020_SHP.zip` to `/content/medical-clinic/data/local/`
- [ ] Upload `SA1_2021_AUST_GDA2020.zip` (recommended — not the SA3 xlsx reference table)
- [ ] Upload MBS SA3 xlsx (recommended — must be the SA3 Summary, not the state-level file)
- [ ] Upload AIHW CSV (recommended — extract `aihw-phc-19-csv_file_2425.csv` from the downloaded zip)
- [ ] **Runtime → Restart and Run All**
- [ ] Verify `VERDICT: GO` appears at the end
- [ ] Download PDF from `outputs/`
