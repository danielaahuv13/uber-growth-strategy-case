# Task 2: ATD Optimization Dashboard

A Streamlit dashboard for exploring ~1 million Uber Eats Mexico deliveries from March-April 2025. The page tells a story from top to bottom: the numbers, the trend, la quincena, where the time hides by segment, when ops stresses by hour and day, the slow tail of couriers, and what predicts ATD.

## What's in this file

- `app.py` — the dashboard, a single Streamlit file
- `uber.csv` — the dataset (renamed from `BC_A&A_with_ATD.csv` for ease of typing)

## How to run it (Google Colab)

The dashboard is set up to run from a Colab notebook. Open the notebook and run the cells in order. The flow is:

1. **Install dependencies.** This installs Streamlit, Plotly, and localtunnel so we can expose the dashboard from Colab.
2. **Upload `uber.csv`** to the Colab session, or mount Drive and copy it into the working directory.
3. **Write `app.py`** to disk. The notebook has a `%%writefile app.py` cell with the full dashboard code.
4. **Launch Streamlit** on port 8501 in the background, with the log piped to a file you can `cat` to confirm it started.
5. **Get the tunnel password** from `https://loca.lt/mytunnelpassword`. This is the IP address Colab is running from.
6. **Open the tunnel** with `npx localtunnel --port 8501`. Click the URL it prints, paste the password, and the dashboard opens.

## If something doesn't load

Streamlit is a bit slow on its first render in Colab because it has to read ~1 million rows from CSV and build all the Plotly charts. **First load can take 20-40 seconds.** If the page looks stuck or shows a half rendered chart, just hit refresh in the browser. That usually fixes it.

If a filter change doesn't update a chart, refresh the page. The cached data stays cached so the second load should be quicker.

If the tunnel says "503 Tunnel Unavailable":
- Confirm Streamlit is actually running: `cat streamlit.log` in a notebook cell.
- Confirm the port matches: the launch cell uses `--server.port 8501` and the tunnel cell uses `--port 8501`. Both must match.
- Restart in this order: `!pkill -f streamlit && !pkill -f localtunnel`, then re-run the launch cell, then re-run the tunnel cell.

## Sections, in order

| # | Section | What it shows |
|---|---|---|
| 01 | The numbers | Six KPI tiles (orders, couriers, median, mean, p90, % over 45 min) |
| — | Distribution | The right-skewed histogram with median + p90 markers, plus a speed-mix breakdown |
| 02 | The trend | Daily volume + median ATD + p90, with payday markers |
| 03 | The payday cycle | "Days from nearest pay day" curve|
| 04 | Where the time hides | Tabbed segmentation: territory, courier flow, merchant surface, geo archetype. Tables show share of total orders. |
| 05 | When ops stresses | Hour of day curve with day of week comparison filter, plus day of week bars |
| 06 | The slow tail | p10/p50/p90 tiles, distance band slider, courier histogram |
| 07 | What predicts ATD | Pickup vs dropoff scatter with binned median lines and 5km/10km reference markers |

## Filters in the sidebar

- **Territory** — multi-select
- **Courier flow** — multi-select
- **Hour of day** — slider

These cascade to every chart on the page. Filtered row count and a data-quality expander sit at the bottom of the sidebar.

## Payday logic

Mexican workers get paid twice a month, on the 15th and the last day. When those land on a Saturday or Sunday, employers usually pay on the preceding Friday so the money is in hand before the weekend. The dashboard applies that shift, so the "PAY DAY" markers on the trend chart and the day zero point on the payday cycle chart use the effective pay date, not the calendar date.

In our data window, March 15 was a Saturday, so the real pay day was Friday March 14. That's what the chart will show.

## A note on the data

The raw CSV uses `\N` for missing values. The dashboard handles that on load: numeric columns get coerced (errors become NaN), categorical columns get stripped and bad strings get nulled out. ATD is filtered to the operational range of 5 to 120 minutes to drop logging artefacts and stuck orders. Roughly 97.7% of raw rows survive cleaning. The data quality expander in the sidebar shows the breakdown.

## Branding choices

The dashboard uses Uber Eats's actual product palette: green `#06C167` on a dark `#0E0E0E` background. This was with the purpose of matching Uber's visual.
