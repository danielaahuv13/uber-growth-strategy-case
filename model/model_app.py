import json
import pickle

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# Uber Eats
# ============================================================
st.set_page_config(
    page_title="ATD Model | Uber Eats Mexico",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

EATS_GREEN = "#06C167"
EATS_GREEN_LIGHT = "#1FCFA0"
BLACK = "#000000"
DARK_BG = "#0E0E0E"
CARD_BG = "#1A1A1A"
TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#B0B0B0"
TEXT_MUTED = "#6B6B6B"
DIVIDER = "#2A2A2A"
CORAL = "#F46A4E"
ORANGE = "#F4A26A"
GREY = "#888888"

st.markdown(f"""
<style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    .stApp {{ background-color: {DARK_BG}; }}
    section[data-testid="stSidebar"] {{
        background-color: {BLACK};
        border-right: 1px solid {DIVIDER};
    }}
    html, body, [class*="css"] {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                     Roboto, "Helvetica Neue", Arial, sans-serif;
    }}
    h1 {{
        color: {TEXT_PRIMARY} !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        font-size: 2.5rem !important;
    }}
    h2, h3 {{ color: {TEXT_PRIMARY} !important; font-weight: 600 !important; }}
    p, .stMarkdown {{ color: {TEXT_SECONDARY} !important; }}

    [data-testid="stMetric"] {{
        background-color: {CARD_BG};
        border: 1px solid {DIVIDER};
        border-radius: 12px;
        padding: 18px 20px;
    }}
    [data-testid="stMetric"]:hover {{ border-color: {EATS_GREEN}; }}
    [data-testid="stMetricLabel"] {{
        color: {TEXT_MUTED} !important;
        font-size: 0.75rem !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }}
    [data-testid="stMetricValue"] {{
        color: {TEXT_PRIMARY} !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }}

    .section-label {{
        color: {EATS_GREEN};
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }}

    .insight-box {{
        background: linear-gradient(135deg,
                    rgba(6,193,103,0.08), rgba(6,193,103,0.02));
        border-left: 3px solid {EATS_GREEN};
        padding: 16px 20px;
        border-radius: 0 8px 8px 0;
        margin: 16px 0;
    }}
    .insight-box p {{
        color: {TEXT_PRIMARY} !important;
        margin: 0;
        font-size: 0.95rem;
        line-height: 1.5;
    }}

    .stDataFrame {{ background-color: {CARD_BG}; border-radius: 8px; }}
    .stDeployButton {{display: none;}}
</style>
""", unsafe_allow_html=True)

PLOTLY_TEMPLATE = dict(
    layout=dict(
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        font=dict(family="-apple-system, sans-serif",
                  color=TEXT_SECONDARY, size=12),
        xaxis=dict(gridcolor=DIVIDER, linecolor=DIVIDER,
                   zerolinecolor=DIVIDER),
        yaxis=dict(gridcolor=DIVIDER, linecolor=DIVIDER,
                   zerolinecolor=DIVIDER),
        margin=dict(l=20, r=20, t=40, b=40),
    )
)

# ============================================================
# Load model and metrics
# ============================================================
with open("atd_model.pkl", "rb") as f:
    bundle = pickle.load(f)

with open("model_metrics.json", "r") as f:
    metrics = json.load(f)

fi = pd.read_csv("model_feature_importance.csv")

model = bundle["model"]
encoder = bundle["encoder"]
NUM_COLS = bundle["num_cols"]
CAT_COLS = bundle["cat_cols"]
FEATURE_ORDER = bundle["feature_order"]
driver_avg = bundle["driver_avg"]
global_mean = bundle["global_mean"]

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.markdown(f"""
<div style="padding: 8px 0 24px 0;">
    <div style="font-size: 1.5rem; font-weight: 700; color: {EATS_GREEN};">
        🤖 ATD Model
    </div>
    <div style="font-size: 0.875rem; color: {TEXT_MUTED}; margin-top: 4px;">
        Predictive layer · Bonus task
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("**Model summary**")
st.sidebar.markdown(f"""
- **Algorithm:** HistGradientBoosting
- **Train rows:** {metrics['n_train']:,}
- **Test rows:** {metrics['n_test']:,}
- **Train cutoff:** {metrics['train_cutoff'][:10]}
- **Validation:** Time-based 80/20
""")

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style="background-color: {CARD_BG}; padding: 12px 16px;
            border-radius: 8px; border: 1px solid {DIVIDER};">
    <div style="color: {TEXT_MUTED}; font-size: 0.7rem;
                text-transform: uppercase; letter-spacing: 0.1em;">
        Headline metric
    </div>
    <div style="color: {EATS_GREEN}; font-size: 1.5rem;
                font-weight: 700; margin-top: 4px;">
        {metrics['mae']:.2f} min MAE
    </div>
    <div style="color: {TEXT_MUTED}; font-size: 0.75rem; margin-top: 4px;">
        on a held-out fortnight
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.markdown(f"""
<div style="margin-bottom: 8px;">
    <span class="section-label">UBER EATS · MEXICO · BONUS TASK</span>
</div>
""", unsafe_allow_html=True)

st.title("A predictive layer, useful and honest.")

st.markdown(f"""
<div style="color: {TEXT_SECONDARY}; font-size: 1.1rem;
            line-height: 1.6; margin-bottom: 32px; max-width: 800px;">
This page is the model. One job: predict ATD before a delivery starts so
ops can plan capacity and flag slow couriers. The numbers below show how
well it works, what drives it, and what happens when you change the inputs.
</div>
""", unsafe_allow_html=True)

# ============================================================
# Headline metrics
# ============================================================
st.markdown('<span class="section-label">01 · How good is it</span>',
            unsafe_allow_html=True)
st.markdown("### The model performance, on data it never saw during training")

c1, c2, c3, c4 = st.columns(4)
c1.metric("MAE", f"{metrics['mae']:.2f} min",
          help="Mean absolute error. Average minutes off per prediction.")
c2.metric("RMSE", f"{metrics['rmse']:.2f} min",
          help="Penalizes big misses. RMSE > MAE means the errors "
               "aren't symmetric.")
c3.metric("R²", f"{metrics['r2']:.2f}",
          help="Share of ATD variance the model explains.")
c4.metric("Within 10 min", f"{metrics['within_10_pct']:.1f}%",
          help="Share of predictions within 10 minutes of actual ATD.")

# Honest framing block
mae_vs_median = metrics['baseline_median_mae'] - metrics['mae']
mae_vs_lr = metrics['baseline_lr_mae'] - metrics['mae']
pct_vs_lr = mae_vs_lr / metrics['baseline_lr_mae'] * 100

st.markdown(f"""
<div class="insight-box">
<p><strong style="color: {EATS_GREEN};">📊 What this says:</strong>
On a typical delivery, the model is off by about
<strong>{metrics['mae']:.0f} minutes</strong>, and 6 out of 10 predictions
land within 10 minutes of reality. R² of {metrics['r2']:.2f} sounds modest,
but the right comparison is to the alternatives we'd actually use, not to
some abstract perfect model. We beat predict-the-median by
<strong>{mae_vs_median:.1f} min</strong> and beat distance-only linear
regression by <strong>{mae_vs_lr:.1f} min</strong> ({pct_vs_lr:.0f}% better).
The remaining gap is data the model doesn't see: live traffic, kitchen prep
time, courier batching state. Good enough for capacity planning and slow
courier flagging. Not yet good enough to power customer ETAs without help.</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# Baseline comparison
# ============================================================
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<span class="section-label">02 · vs the alternatives</span>',
            unsafe_allow_html=True)
st.markdown("### Better than the obvious baselines, by how much")

baselines = pd.DataFrame({
    "Model": ["Predict the median", "Distance-only linear regression",
              "Gradient boosting (this model)"],
    "MAE": [metrics["baseline_median_mae"],
            metrics["baseline_lr_mae"], metrics["mae"]],
})
colors = [GREY, ORANGE, EATS_GREEN]

fig = go.Figure(go.Bar(
    x=baselines["Model"], y=baselines["MAE"],
    marker=dict(color=colors, line=dict(color=DARK_BG, width=1)),
    text=[f"<b>{v:.2f} min</b>" for v in baselines["MAE"]],
    textposition="outside",
    textfont=dict(color=TEXT_PRIMARY, size=14),
    hovertemplate="<b>%{x}</b><br>MAE %{y:.2f} min<extra></extra>",
))
fig.update_layout(
    template=PLOTLY_TEMPLATE,
    yaxis=dict(title="MAE (min) — lower is better",
               range=[0, max(baselines["MAE"]) * 1.2]),
    height=380,
    showlegend=False,
)
st.plotly_chart(fig, use_container_width=True)

# ============================================================
# Feature importance
# ============================================================
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    '<span class="section-label">03 · What drives the predictions</span>',
    unsafe_allow_html=True)
st.markdown("### The signals that actually matter")

# Pretty labels
label_map = {
    "total_distance": "Total distance",
    "driver_hist_atd": "Driver historical ATD",
    "dropoff_distance": "Dropoff distance",
    "pickup_distance": "Pickup distance",
    "territory": "Territory",
    "hour": "Hour of day",
    "courier_flow": "Courier flow",
    "merchant_surface": "Merchant surface",
    "dow": "Day of week",
    "geo_archetype": "Geo archetype",
    "is_peak_dinner": "Dinner peak flag",
    "is_peak_lunch": "Lunch peak flag",
    "log_pickup": "Log pickup distance",
    "log_dropoff": "Log dropoff distance",
    "is_weekend": "Weekend flag",
    "is_late_night": "Late night flag",
}
fi_top = fi.head(10).copy()
fi_top["pretty"] = fi_top["feature"].map(label_map).fillna(fi_top["feature"])
fi_top = fi_top.iloc[::-1]

fig = go.Figure(go.Bar(
    x=fi_top["importance"], y=fi_top["pretty"],
    orientation="h",
    marker=dict(color=EATS_GREEN, line=dict(color=DARK_BG, width=1)),
    hovertemplate="<b>%{y}</b><br>Importance %{x:.4f}<extra></extra>",
))
fig.update_layout(
    template=PLOTLY_TEMPLATE,
    xaxis=dict(title="Permutation importance"),
    yaxis_title="",
    height=400,
    showlegend=False,
)
st.plotly_chart(fig, use_container_width=True)

top4_share = (fi_top["importance"].iloc[-4:].sum()
              / fi["importance"].sum() * 100)

st.markdown(f"""
<div class="insight-box">
<p><strong style="color: {EATS_GREEN};">📊 What this says:</strong>
The top 4 features (total distance, driver historical ATD, dropoff distance,
pickup distance) account for about <strong>{top4_share:.0f}% of the model's
predictive power</strong>. The story it tells is simple: <strong>ATD is a
function of distance and driver</strong>. Time of day matters at the margins.
Categorical segments matter even less. The peak flags do almost nothing,
which means the model already learns "dinner is busier" from the hour
feature alone. The biggest win for a future version would be data the
model doesn't have today: live traffic, kitchen prep, batching state.</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# Live what if predictor
# ============================================================
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<span class="section-label">04 · The what-if predictor</span>',
            unsafe_allow_html=True)
st.markdown("### Try a delivery and see what the model thinks")

st.markdown(f"""
<div style="color: {TEXT_SECONDARY}; margin-bottom: 16px; max-width: 700px;">
Set the inputs below and the model will return a predicted ATD. Useful for
counterfactuals: <em>what if we routed this Fleet trip through Logistics?
What if the courier is a top-decile performer instead of slow-tail?</em>
</div>
""", unsafe_allow_html=True)

# Get encoder vocab so we know what categories are valid
cat_categories = {col: list(cats) for col, cats
                   in zip(CAT_COLS, encoder.categories_)}

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("**Trip basics**")
    pickup_distance = st.slider(
        "Pickup distance (km)", 0.1, 15.0, 2.5, 0.1,
        help="Courier to restaurant"
    )
    dropoff_distance = st.slider(
        "Dropoff distance (km)", 0.1, 15.0, 3.5, 0.1,
        help="Restaurant to eater"
    )
    hour = st.slider("Hour of day", 0, 23, 13)
    dow_label = st.selectbox(
        "Day of week",
        ["Monday", "Tuesday", "Wednesday", "Thursday",
         "Friday", "Saturday", "Sunday"],
        index=4
    )

with c2:
    st.markdown("**Segments**")
    territory = st.selectbox("Territory",
                             [c for c in cat_categories["territory"]
                              if c not in ("nan", "Unknown")])
    courier_flow = st.selectbox(
        "Courier flow",
        [c for c in cat_categories["courier_flow"]
         if c not in ("nan", "Unknown")],
        index=0
    )
    merchant_surface = st.selectbox(
        "Merchant surface",
        [c for c in cat_categories["merchant_surface"]
         if c not in ("nan", "Unknown")],
        index=0
    )
    geo_archetype = st.selectbox(
        "Geo archetype",
        [c for c in cat_categories["geo_archetype"]
         if c not in ("nan", "Unknown")],
        index=0
    )

with c3:
    st.markdown("**Courier profile**")
    courier_profile = st.selectbox(
        "Courier type",
        ["Top decile (fast, ~25 min hist)",
         "Typical courier (~31 min hist)",
         "Slow decile (~39 min hist)",
         "New courier (use global mean)"],
        index=1,
    )
    if "Top decile" in courier_profile:
        driver_hist_atd = 25.0
    elif "Typical" in courier_profile:
        driver_hist_atd = 31.0
    elif "Slow decile" in courier_profile:
        driver_hist_atd = 39.0
    else:
        driver_hist_atd = global_mean

    st.markdown(f"""
    <div style="background-color: {CARD_BG}; padding: 12px 16px;
                border-radius: 8px; border: 1px solid {DIVIDER};
                margin-top: 8px;">
        <div style="color: {TEXT_MUTED}; font-size: 0.7rem;
                    text-transform: uppercase; letter-spacing: 0.05em;">
            Using driver history
        </div>
        <div style="color: {EATS_GREEN}; font-size: 1.25rem;
                    font-weight: 700; margin-top: 4px;">
            {driver_hist_atd:.1f} min
        </div>
    </div>
    """, unsafe_allow_html=True)

# Build the feature row
dow_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2,
           "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
dow_num = dow_map[dow_label]

total_distance = pickup_distance + dropoff_distance
log_pickup = np.log1p(pickup_distance)
log_dropoff = np.log1p(dropoff_distance)
is_weekend = 1 if dow_num >= 5 else 0
is_peak_lunch = 1 if 12 <= hour <= 14 else 0
is_peak_dinner = 1 if 19 <= hour <= 21 else 0
is_late_night = 1 if 0 <= hour <= 5 else 0

# Construct in the exact training feature order
num_values = {
    "pickup_distance": pickup_distance,
    "dropoff_distance": dropoff_distance,
    "total_distance": total_distance,
    "log_pickup": log_pickup,
    "log_dropoff": log_dropoff,
    "hour": hour,
    "dow": dow_num,
    "is_weekend": is_weekend,
    "is_peak_lunch": is_peak_lunch,
    "is_peak_dinner": is_peak_dinner,
    "is_late_night": is_late_night,
    "driver_hist_atd": driver_hist_atd,
}
cat_row = pd.DataFrame([{
    "territory": territory,
    "courier_flow": courier_flow,
    "geo_archetype": geo_archetype,
    "merchant_surface": merchant_surface,
}])
cat_encoded = encoder.transform(cat_row[CAT_COLS].astype(str))[0]
num_row = [num_values[c] for c in NUM_COLS]
X_row = np.array(num_row + list(cat_encoded)).reshape(1, -1)

# Predict
prediction = float(model.predict(X_row)[0])

# Build a vs-typical narrative
diff_from_median = prediction - 33.8
if abs(diff_from_median) < 2:
    speed_word = "in line with the typical Mexico delivery"
    speed_color = TEXT_PRIMARY
elif diff_from_median > 0:
    speed_word = (f"{diff_from_median:.1f} min slower than the typical "
                  "delivery")
    speed_color = CORAL
else:
    speed_word = (f"{abs(diff_from_median):.1f} min faster than the "
                  "typical delivery")
    speed_color = EATS_GREEN

# big prediction display
st.markdown("<br>", unsafe_allow_html=True)
c_left, c_right = st.columns([1, 1])

with c_left:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {BLACK}, {CARD_BG});
                padding: 32px; border-radius: 16px;
                border: 1px solid {EATS_GREEN}; text-align: center;">
        <div style="color: {TEXT_MUTED}; font-size: 0.8rem;
                    text-transform: uppercase; letter-spacing: 0.1em;
                    margin-bottom: 12px;">
            Predicted ATD
        </div>
        <div style="color: {EATS_GREEN}; font-size: 4rem;
                    font-weight: 800; line-height: 1; margin: 8px 0;">
            {prediction:.1f}
        </div>
        <div style="color: {TEXT_PRIMARY}; font-size: 1rem;">
            minutes
        </div>
        <div style="color: {speed_color}; font-size: 0.95rem;
                    margin-top: 16px; font-weight: 500;">
            {speed_word}
        </div>
    </div>
    """, unsafe_allow_html=True)

with c_right:
    # Show the prediction interval implied by MAE
    low = prediction - metrics['mae']
    high = prediction + metrics['mae']
    st.markdown(f"""
    <div style="background-color: {CARD_BG}; padding: 24px;
                border-radius: 16px; border: 1px solid {DIVIDER};
                height: 100%;">
        <div class="section-label">HOW TO READ THIS</div>
        <p style="color: {TEXT_PRIMARY}; font-size: 0.95rem;
                  line-height: 1.5; margin-top: 12px;">
            Best estimate: <strong>{prediction:.1f} min</strong>.
            With held-out MAE of {metrics['mae']:.1f} min, a useful
            range to expect is roughly
            <strong>{low:.0f} to {high:.0f} min</strong>.
        </p>
        <p style="color: {TEXT_SECONDARY}; font-size: 0.875rem;
                  line-height: 1.5; margin-top: 12px;">
            This is the model's best guess given what it knows.
            It doesn't see live traffic, kitchen state, or whether
            the courier is currently mid-batch on another order.
            Treat it as a planning number, not a customer-facing promise.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# Honest limitations block
# ============================================================
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown('<span class="section-label">05 · The honest limits</span>',
            unsafe_allow_html=True)
st.markdown("### What this model is not for")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f"""
    <div style="background-color: {CARD_BG}; padding: 20px;
                border-radius: 12px; border: 1px solid {DIVIDER};
                border-top: 3px solid {EATS_GREEN}; height: 100%;">
        <div style="color: {EATS_GREEN}; font-weight: 700;
                    font-size: 1rem; margin-bottom: 8px;">
            ✅ Good for
        </div>
        <p style="color: {TEXT_PRIMARY}; font-size: 0.9rem;
                  line-height: 1.4; margin: 0;">
            Capacity planning, slow-courier flagging, weekly performance
            reporting, counterfactual analysis. Anything where being off
            by 10 minutes on average is acceptable.
        </p>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div style="background-color: {CARD_BG}; padding: 20px;
                border-radius: 12px; border: 1px solid {DIVIDER};
                border-top: 3px solid {ORANGE}; height: 100%;">
        <div style="color: {ORANGE}; font-weight: 700;
                    font-size: 1rem; margin-bottom: 8px;">
            ⚠️ Use with caution
        </div>
        <p style="color: {TEXT_PRIMARY}; font-size: 0.9rem;
                  line-height: 1.4; margin: 0;">
            Single-trip operational decisions like dispatching a specific
            order. The 10-minute MAE is the average. Individual
            predictions can be off by much more.
        </p>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div style="background-color: {CARD_BG}; padding: 20px;
                border-radius: 12px; border: 1px solid {DIVIDER};
                border-top: 3px solid {CORAL}; height: 100%;">
        <div style="color: {CORAL}; font-weight: 700;
                    font-size: 1rem; margin-bottom: 8px;">
            ❌ Not yet ready for
        </div>
        <p style="color: {TEXT_PRIMARY}; font-size: 0.9rem;
                  line-height: 1.4; margin: 0;">
            Customer-facing ETA promises. We need live traffic,
            kitchen prep time, and batching state before we put a
            number in front of an eater.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# Footer
# ============================================================
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(f"""
<div style="text-align: center; color: {TEXT_MUTED};
            font-size: 0.8rem; padding: 16px 0;
            border-top: 1px solid {DIVIDER}; margin-top: 24px;">
ATD Model Dashboard · Bonus task · Uber Eats business case
</div>
""", unsafe_allow_html=True)
