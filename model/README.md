# Task 3 (Bonus): Predictive ATD Model

A gradient-boosted model that predicts Actual Time of Delivery (ATD) before a delivery starts. Built as the bonus task. Useful for capacity planning, slow courier flagging, and as the first version layer that gets richer over time.

## What's in this file

- `model_app.py`: a Streamlit dashboard that surfaces the model
- `atd_model.pkl`: the trained model bundle (encoder + GBM + driver history lookup)
- `model_metrics.json`: held out performance and baseline comparisons
- `model_feature_importance.csv`: permutation importance ranking

The training script lives in the same Colab notebook as the dashboard.

## How to run it (Google Colab)

The model and its dashboard live in the **same Colab notebook** as the main dashboard. You do not need a separate notebook. The model section is at the bottom of the notebook, after the main dashboard cells.

The flow:

1. **Run the main dashboard cells first** (the ones that install dependencies, write `app.py`, launch Streamlit on port 8501, and open the tunnel). The main dashboard should be working before you move on.
2. **Run the model training cell.** This reads `uber.csv`, trains the gradient-boosted regressor, evaluates it, and saves `atd_model.pkl`, `model_metrics.json`, and `model_feature_importance.csv` to the Colab working directory.
3. **Run the cell that writes `model_app.py`** to disk.
4. **Launch the model dashboard on port 8502** (so it doesn't clash with the main dashboard on 8501).
5. **Open a separate localtunnel on port 8502** and click through to the model dashboard.
6. **If that doesn´t work just follow the cell orders and there shouldn't be any problem**

You can have both dashboards running at the same time. Two tunnels, two URLs, two browser tabs.

## If something doesn't load

Same fix as the main dashboard. **First load takes time** because Streamlit has to load the model bundle and build the live what if predictor. If the page looks stuck or a chart looks half rendered, hit refresh.

If a filter or input doesn't seem to update the prediction, refresh once. The cached state should sort itself out.

If the tunnel says "503 Tunnel Unavailable":
- `cat streamlit_model.log` to see what Streamlit said on startup
- Confirm Streamlit is on port 8502 and the tunnel is also on `--port 8502`
- If you have a stale process: `!pkill -f streamlit && !pkill -f localtunnel`, then re-run the launch and tunnel cells

## What the dashboard shows

| Section | Content |
|---|---|
| 01 · How good is it | MAE, RMSE, R², % within 10 minutes |
| 02 · vs the alternatives | Bar chart comparing predict the median, distance only LR, and the gradient-boosted model |
| 03 · What drives the predictions | Top 10 features by permutation importance |
| 04 · The what if predictor | Live inputs (distances, hour, day, segments, courier profile) that return a prediction with an MAE-based range |
| 05 · The honest limits | Three cards: good for / use with caution / not yet ready for |

## Headline numbers

- **MAE: 10.4 minutes** 
- **R²: 0.29** modest in isolation, but the right comparison is to the alternatives ops would actually use
- **60% of predictions land within 10 minutes** of actual ATD
- **Beats predict the median by 2.0 minutes** of MAE
- **Beats distance only linear regression by 0.9 minutes** of MAE (about 8% better)

## What this model is for

- Capacity planning, slow courier flagging, weekly performance reporting, counterfactual analysis
- Anything where being off by 10 minutes on average is acceptable

## What it's not for

- Customer facing ETA promises, without adding live traffic and kitchen prep telemetry first
- Single trip operational decisions like dispatching a specific order, where individual predictions can be off by much more than the average

## A note on the data

The model reads `uber.csv` (renamed from `BC_A&A_with_ATD.csv` for ease of typing). The training script applies the same cleaning the dashboard uses, then trains on a chronological 80/20 split so the model is evaluated on a future fortnight it never saw.

The `driver_hist_atd` feature is computed from train data only, with a global mean fallback for unseen drivers. No leakage.
