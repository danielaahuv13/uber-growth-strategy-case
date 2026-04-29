# Task 2 · Streamlit Dashboard

> **Goal:** an interactive dashboard that turns the weekly delivery extract into operational insight — clear enough for a non-technical stakeholder to use, deep enough for a data-minded reviewer to trust.

## What's in this folder

| File | Purpose |
|---|---|
| `app.py` | The Streamlit application |

> **Note for reviewers:** the live application file (`app.py`) is included here — drop it next to the dataset (`data/BC_A_A_with_ATD.csv`) and run `streamlit run dashboard/app.py`.

---

## How to run

From the repo root:

```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
```

The app opens at `http://localhost:8501` and reads `data/BC_A_A_with_ATD.csv` by default. You can change the CSV path in the sidebar.

---

## What the dashboard shows

The page flows top-to-bottom as a **business narrative**, not a feature dump:

| Section | Question it answers | Visual |
|---|---|---|
| **01 · The numbers** | How long do deliveries actually take? | 6 KPI tiles (orders, couriers, median, mean, p90, % over 45) |
| **Distribution** | Why is the average misleading? | Histogram with median + p90 markers |
| **Speed mix** | What share of orders fall in each speed bucket? | Horizontal bar chart |
| **02 · Where the time hides** | Which segments are slowest? | Three tabs: territory, courier flow, merchant surface |
| **03 · When ops stresses** | When during the day/week is it slow? | Hour pattern (dual-axis) + day-of-week bars |
| **04 · The slow tail** | What does courier-level performance look like? | p10 / p50 / p90 tiles + histogram |
| **05 · The model** | Is the predictive layer trustworthy? | Baseline comparison + feature importance + live what-if predictor |

Sidebar filters (territory, courier flow, hour-of-day) cascade to **every** chart on the page.

---

## Design decisions

### Why one file?

The case rewards modularity, but the case **also** rewards reproducibility, and a single-file Streamlit app removes one entire class of bugs (import path issues, partial writes during `%%writefile`, etc.). For a one-screen dashboard with cleanly-separated sections, single-file is the pragmatic call.

In a multi-week project I'd split into:
- `data.py` — load + clean
- `metrics.py` — KPI math
- `charts.py` — Plotly builders
- `app.py` — layout

The functions inside `app.py` are already organised this way (`load_and_clean()`, `by_dim()`, etc.) so the split would be mechanical.

### Why Plotly (not matplotlib)?

Plotly gives **hover tooltips, zoom, and pan for free**. For a non-technical stakeholder running the dashboard themselves, hovering over a bar to see "Logistics: 30.8 min, n=380k orders" is much more discoverable than reading axis labels.

### Why tabs for segmentation?

Three side-by-side bar charts crowd the screen. Tabs let the user pick which dimension they care about right now, without losing the other two. It also signals "these are equivalent dimensions" — clearer than stacking them.

### Why dark theme?

Uber Eats's actual product uses a dark UI. Matching that visual language signals "we built this for Uber, not just a generic dashboard."

### Why cache the data load?

Reading 1M rows from CSV takes ~5 seconds. Without `@st.cache_data` (used in the production version), every interaction would re-read and re-clean, making the dashboard feel sluggish. Caching means it loads once per session.

---

## What a non-technical user sees vs a technical one

The dashboard is designed for **two audiences in the same view**:

**Non-technical (operations stakeholder):**
- Headline KPIs at the top, plain language
- "Insight callouts" under each chart explaining what it means in plain English
- Speed-coded colours (green = fast, coral = slow) for instant pattern recognition
- The closing "Three plays" section translates analysis into actions

**Technical (data-minded reviewer):**
- Filter combinations let them validate any claim ("does the courier flow finding hold for just the Central territory?")
- The model section shows held-out metrics, baseline comparisons, and feature importance — not just point predictions
- The data-quality expander in the sidebar shows exactly what was cleaned and how much

---

## Code quality

- **Flake8-clean** (config in `.flake8` at repo root, max-line 88)
- **Pure functions** for all data transformations (testable without Streamlit)
- **Defensive defaults** — empty filtered DataFrame raises a friendly warning rather than crashing
- **Documented** — every section has a comment header explaining what it does

---

## What I'd add given more time

- **Persistent URL state.** Today the filters reset on page reload; ideally they'd be reflected in the URL so links can be shared.
- **Anomaly badges.** When this week's median ATD jumps >2 std-dev above the trailing 8-week average, surface a red badge at the top of the dashboard.
- **Drill-through to the courier scorecard.** Today the histogram is informational. Field-ops would want to click a slow-tail bar and see the actual courier UUIDs to follow up.
- **Export to PDF.** A "Generate weekly report" button that snapshots the current filtered view as a one-pager for ops standup.
