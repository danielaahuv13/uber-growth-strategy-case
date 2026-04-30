import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# Uber Eats
# ============================================================
st.set_page_config(
    page_title="ATD Optimization | Uber Eats Mexico",
    page_icon="🛵",
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
TEAL = "#5BBFD6"

# ============================================================
# CSS
# ============================================================
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
    h2 {{ color: {TEXT_PRIMARY} !important; font-weight: 600 !important; }}
    h3 {{ color: {TEXT_PRIMARY} !important; font-weight: 600 !important; }}
    p, .stMarkdown {{ color: {TEXT_SECONDARY} !important; }}

    [data-testid="stMetric"] {{
        background-color: {CARD_BG};
        border: 1px solid {DIVIDER};
        border-radius: 12px;
        padding: 18px 20px;
        transition: all 0.2s ease;
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

    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: transparent;
        border-bottom: 1px solid {DIVIDER};
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        color: {TEXT_MUTED};
        font-weight: 500;
        padding: 10px 20px;
        border-bottom: 2px solid transparent;
    }}
    .stTabs [aria-selected="true"] {{
        color: {EATS_GREEN} !important;
        border-bottom: 2px solid {EATS_GREEN} !important;
    }}

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        color: {TEXT_PRIMARY} !important;
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

    .stDataFrame {{
        background-color: {CARD_BG};
        border-radius: 8px;
    }}

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
# Data Cleaning
# ============================================================
df = pd.read_csv("uber.csv")
n_raw = len(df)

COLUMN_ALIASES = {
    "pickupdistance": "pickup_distance",
    "traveldistance": "dropoff_distance",
    "dropoffdistance": "dropoff_distance",
    "atd": "ATD",
    "Atd": "ATD",
}
df = df.rename(columns={k: v for k, v in COLUMN_ALIASES.items()
                        if k in df.columns})

# If distances arrived in metres (raw warehouse units), convert to km.
# Heuristic: median distance > 100 means metres, not kilometres.
for col in ["pickup_distance", "dropoff_distance"]:
    if col in df.columns:
        sample = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(sample) and sample.median() > 100:
            df[col] = pd.to_numeric(df[col], errors="coerce") / 1000.0

cleaning_log = {}

for col in ["pickup_distance", "dropoff_distance"]:
    before = df[col].notna().sum()
    df[col] = pd.to_numeric(df[col], errors="coerce")
    after = df[col].notna().sum()
    cleaning_log[f"{col} non-numeric"] = before - after

for col in ["restaurant_offered_timestamp_utc",
            "order_final_state_timestamp_local",
            "eater_request_timestamp_local"]:
    df[col] = pd.to_datetime(df[col], errors="coerce")

CATEGORICAL_COLS = ["territory", "country_name", "courier_flow",
                    "geo_archetype", "merchant_surface"]
bad_values = {"\\N", "", "nan", "None", "NULL", "null"}

for col in CATEGORICAL_COLS:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        bad_mask = df[col].isin(bad_values) | df[col].isna()
        cleaning_log[f"{col} missing/bad"] = int(bad_mask.sum())
        df.loc[bad_mask, col] = np.nan

before_filter = len(df)
df = df[
    (df["ATD"] >= 5) & (df["ATD"] <= 120)
    & df["pickup_distance"].notna()
    & df["dropoff_distance"].notna()
    & df["eater_request_timestamp_local"].notna()
    & df["courier_flow"].notna()
    & df["territory"].notna()
].reset_index(drop=True)
cleaning_log["rows dropped (cleaning + filter)"] = before_filter - len(df) \
    + (n_raw - before_filter)

df["hour"] = df["eater_request_timestamp_local"].dt.hour
df["dow"] = df["eater_request_timestamp_local"].dt.day_name()
df["date"] = df["eater_request_timestamp_local"].dt.date
df["total_distance"] = df["pickup_distance"] + df["dropoff_distance"]

df["speed_bucket"] = pd.cut(
    df["ATD"],
    bins=[0, 20, 30, 45, 60, 120],
    labels=["≤20 min", "20–30 min", "30–45 min", "45–60 min", "60+ min"],
)

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.markdown(f"""
<div style="padding: 8px 0 24px 0;">
    <div style="font-size: 1.5rem; font-weight: 700; color: {EATS_GREEN};">
        🛵 Uber Eats
    </div>
    <div style="font-size: 0.875rem; color: {TEXT_MUTED}; margin-top: 4px;">
        ATD Optimization · Mexico
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("**Filters**")

territories = st.sidebar.multiselect(
    "Territory",
    sorted(df["territory"].unique()),
    default=sorted(df["territory"].unique()),
)
courier_flows = st.sidebar.multiselect(
    "Courier flow",
    sorted(df["courier_flow"].unique()),
    default=sorted(df["courier_flow"].unique()),
)
hour_range = st.sidebar.slider("Hour of day", 0, 23, (0, 23))

flt = df.copy()
if territories:
    flt = flt[flt["territory"].isin(territories)]
if courier_flows:
    flt = flt[flt["courier_flow"].isin(courier_flows)]
flt = flt[(flt["hour"] >= hour_range[0]) & (flt["hour"] <= hour_range[1])]

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style="background-color: {CARD_BG}; padding: 12px 16px;
            border-radius: 8px; border: 1px solid {DIVIDER};">
    <div style="color: {TEXT_MUTED}; font-size: 0.7rem;
                text-transform: uppercase; letter-spacing: 0.1em;">
        Filtered orders
    </div>
    <div style="color: {EATS_GREEN}; font-size: 1.5rem;
                font-weight: 700; margin-top: 4px;">
        {len(flt):,}
    </div>
</div>
""", unsafe_allow_html=True)

with st.sidebar.expander("📋 Data quality"):
    st.markdown(f"""
    **Raw rows:** {n_raw:,}
    **Clean rows:** {len(df):,} ({len(df)/n_raw*100:.1f}% retained)

    **Cleaning applied:**
    """)
    for step, count in cleaning_log.items():
        if count > 0:
            st.markdown(f"- {step}: **{count:,}** rows")
    st.markdown("""
    **Filter rule:** ATD between 5 and 120 minutes. Below 5 is usually a
    logging artefact (instant cancel or timestamp swap). Above 120 is a stuck
    order that got marked complete much later.
    """)

# ============================================================
# HEADER
# ============================================================
st.markdown(f"""
<div style="margin-bottom: 8px;">
    <span class="section-label">UBER EATS · MEXICO · MARCH–APRIL 2025</span>
</div>
""", unsafe_allow_html=True)

st.title("Where the time goes, and how to get it back.")

st.markdown(f"""
<div style="color: {TEXT_SECONDARY}; font-size: 1.1rem;
            line-height: 1.6; margin-bottom: 32px; max-width: 800px;">
Every minute of delivery time is a tax on customer experience and on
operations cost. This dashboard works through ~1 million Mexico deliveries
to find where the slow time is hiding and what we can actually do about it.
</div>
""", unsafe_allow_html=True)

if flt.empty:
    st.warning("No rows after filtering. Loosen the filters in the sidebar.")
    st.stop()

# ============================================================
# KPIs
# ============================================================
median_atd = float(flt["ATD"].median())
mean_atd = float(flt["ATD"].mean())
p90_atd = float(flt["ATD"].quantile(0.90))
pct_under_30 = float((flt["ATD"] < 30).mean() * 100)
pct_over_45 = float((flt["ATD"] > 45).mean() * 100)
n_couriers = int(flt["driver_uuid"].nunique())
n_merchants = int(flt["workflow_uuid"].nunique())

st.markdown('<span class="section-label">01 · The numbers</span>',
            unsafe_allow_html=True)
st.markdown("### How long do Uber Eats Mexico deliveries take?")

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total orders", f"{len(flt):,}")
c2.metric("Active couriers", f"{n_couriers:,}")
c3.metric("Median ATD", f"{median_atd:.1f} min")
c4.metric("Mean ATD", f"{mean_atd:.1f} min")
c5.metric("p90 ATD", f"{p90_atd:.1f} min")
c6.metric("% over 45 min", f"{pct_over_45:.1f}%")

# ============================================================
# Distribution and speed
# ============================================================
st.markdown("<br>", unsafe_allow_html=True)

col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown("**Distribution of delivery times**")
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=flt["ATD"], nbinsx=80,
        marker=dict(color=EATS_GREEN, line=dict(color=DARK_BG, width=0.5)),
        hovertemplate="%{y:,.0f} orders<br>%{x} min<extra></extra>",
    ))
    fig.add_vline(x=median_atd, line_dash="dash", line_color="white",
                  line_width=2,
                  annotation=dict(text=f"<b>Median {median_atd:.1f}</b>",
                                  font=dict(color="white", size=12),
                                  bgcolor=BLACK, borderpad=4))
    fig.add_vline(x=p90_atd, line_dash="dot", line_color=CORAL, line_width=2,
                  annotation=dict(text=f"<b>p90 {p90_atd:.1f}</b>",
                                  font=dict(color=CORAL, size=12),
                                  bgcolor=BLACK, borderpad=4))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        xaxis_title="ATD (minutes)",
        yaxis_title="Number of orders",
        height=380, bargap=0.02, showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.markdown("**Speed mix: how fast are deliveries arriving?**")
    bucket_counts = (flt["speed_bucket"]
                     .value_counts(normalize=True)
                     .sort_index() * 100).reset_index()
    bucket_counts.columns = ["bucket", "pct"]

    bucket_colors = [EATS_GREEN, EATS_GREEN_LIGHT, ORANGE, CORAL, "#C0392B"]
    fig = go.Figure(go.Bar(
        x=bucket_counts["pct"],
        y=bucket_counts["bucket"].astype(str),
        orientation="h",
        marker=dict(color=bucket_colors[:len(bucket_counts)],
                    line=dict(color=DARK_BG, width=1)),
        text=[f"<b>{v:.1f}%</b>" for v in bucket_counts["pct"]],
        textposition="outside",
        textfont=dict(color=TEXT_PRIMARY, size=12),
        hovertemplate="<b>%{y}</b><br>%{x:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        xaxis_title="% of orders",
        yaxis_title="",
        height=380,
        showlegend=False,
        xaxis=dict(range=[0, max(bucket_counts["pct"]) * 1.2]),
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown(f"""
<div class="insight-box">
<p><strong style="color: {EATS_GREEN};">📊 What this says:</strong>
The shape is right-skewed. The mean sits above the median because a slow
tail is dragging it up. About <strong>{pct_over_45:.0f}% of orders cross
45 minutes</strong> and that's where the customer experience really hurts.
Pulling even a few percentage points of those orders into the 30–45 bucket
moves NPS and reorder rate, which are the metrics ops actually gets paid on.</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# Daily trend
# ============================================================
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown('<span class="section-label">02 · The trend</span>',
            unsafe_allow_html=True)
st.markdown("### Is performance stable, improving, or slipping?")

from calendar import monthrange


def shift_payday_for_weekend(d):
    """Shift a calendar pay date to the Friday before if it falls on
    Sat/Sun. In Mexico, when the 15th or last day of month lands on
    a weekend, employers typically pay on the preceding Friday so
    workers have access to the money before the weekend. We pick
    Friday as the convention; some employers use the following
    Monday instead, but Friday is the more common pattern.
    """
    weekday = d.weekday()
    if weekday == 5:        # Saturday
        return d - pd.Timedelta(days=1)
    if weekday == 6:        # Sunday
        return d - pd.Timedelta(days=2)
    return d


def get_paydays_for_month(year, month):
    """Return the two pay-day dates for a given month, with the
    weekend shift applied. Used by both the daily-trend markers and
    the days-from-payday calculation.
    """
    last_day = monthrange(year, month)[1]
    raw_paydays = [pd.Timestamp(year, month, 15),
                   pd.Timestamp(year, month, last_day)]
    return [shift_payday_for_weekend(d) for d in raw_paydays]


def is_payday(d):
    """True if the date is an effective pay day (with weekend shift)."""
    return d in get_paydays_for_month(d.year, d.month)


daily = (flt.groupby("date")
            .agg(orders=("ATD", "size"),
                 median_atd=("ATD", "median"),
                 p90_atd=("ATD", lambda s: s.quantile(0.90)))
            .reset_index())
daily["date"] = pd.to_datetime(daily["date"])
daily["is_payday"] = daily["date"].apply(is_payday)

fig = go.Figure()
fig.add_trace(go.Bar(
    x=daily["date"], y=daily["orders"],
    name="Orders",
    marker=dict(color=GREY, opacity=0.35),
    hovertemplate="<b>%{x|%a %b %d}</b><br>%{y:,.0f} orders<extra></extra>",
))
fig.add_trace(go.Scatter(
    x=daily["date"], y=daily["median_atd"],
    yaxis="y2", mode="lines+markers", name="Median ATD",
    line=dict(color=EATS_GREEN, width=2.5),
    marker=dict(size=5, color=EATS_GREEN),
    hovertemplate="<b>%{x|%a %b %d}</b><br>Median %{y:.1f} min<extra></extra>",
))
fig.add_trace(go.Scatter(
    x=daily["date"], y=daily["p90_atd"],
    yaxis="y2", mode="lines", name="p90 ATD",
    line=dict(color=CORAL, width=1.5, dash="dot"),
    hovertemplate="<b>%{x|%a %b %d}</b><br>p90 %{y:.1f} min<extra></extra>",
))

# Mark pay days with vertical lines
for pay_date in daily[daily["is_payday"]]["date"]:
    fig.add_vline(
        x=pay_date, line_dash="dot", line_color="#FBBF24",
        line_width=1.5, opacity=0.6,
    )
# Add a single legend entry for pay days
fig.add_trace(go.Scatter(
    x=[None], y=[None], mode="lines",
    line=dict(color="#FBBF24", dash="dot", width=2),
    name="Pay day (15 / last of month)",
))

fig.update_layout(
    template=PLOTLY_TEMPLATE,
    xaxis=dict(title="Date"),
    yaxis=dict(title="Orders"),
    yaxis2=dict(title="ATD (min)", overlaying="y", side="right",
                showgrid=False),
    legend=dict(orientation="h", y=1.12, x=0,
                bgcolor="rgba(0,0,0,0)"),
    height=380,
)
st.plotly_chart(fig, use_container_width=True)

first_week = daily.head(7)["median_atd"].mean()
last_week = daily.tail(7)["median_atd"].mean()
trend_diff = last_week - first_week
if trend_diff < -0.5:
    trend_word = "improved"
elif trend_diff > 0.5:
    trend_word = "slipped"
else:
    trend_word = "stayed flat"

st.markdown(f"""
<div class="insight-box">
<p><strong style="color: {EATS_GREEN};">📊 What this says:</strong>
Over the analysis window, median ATD <strong>{trend_word}</strong>
({first_week:.1f} → {last_week:.1f} min between the first and last 7 days).
The grey bars show demand. Notice that weekend volume spikes don't
automatically cause ATD spikes, which is a sign ops is absorbing the
peaks reasonably well. The dotted coral line is the p90 tail. That's
the line we want to drop, because that's the line customers feel.</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# Pay day
# ============================================================
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown('<span class="section-label">03 · The pay-day cycle</span>',
            unsafe_allow_html=True)
st.markdown("### Does la quincena change how Uber Eats Mexico runs?")

st.markdown(f"""
<div style="color: {TEXT_SECONDARY}; margin-bottom: 16px; max-width: 800px;">
Mexican workers get paid twice a month, on the 15th and the last day.
When those land on a Saturday or Sunday, employers usually pay on the
preceding Friday so the money is in hand before the weekend, so we
apply that shift here. The chart collapses every day in the dataset
onto its position relative to the nearest effective pay day.
Day 0 is pay day. Negative is before, positive is after.
</div>
""", unsafe_allow_html=True)


def days_from_payday(d):
    """Distance in days to the nearest effective pay day.

    Pay days are the 15th and last day of each month, shifted to
    the preceding Friday when they fall on Sat or Sun (the Mexican
    payroll convention). Negative = before, positive = after,
    0 = pay day itself.
    """
    paydays = list(get_paydays_for_month(d.year, d.month))
    # Include previous month's last-day pay date so dates near the.
    if d.month == 1:
        paydays.extend(get_paydays_for_month(d.year - 1, 12))
    else:
        paydays.extend(get_paydays_for_month(d.year, d.month - 1))
    diffs = [(d - p).days for p in paydays]
    return min(diffs, key=abs)


# Add the offset to each row
flt_pay = flt.copy()
flt_pay["date_dt"] = pd.to_datetime(flt_pay["date"])
flt_pay["days_from_payday"] = flt_pay["date_dt"].apply(days_from_payday)

# Aggregate to a 5 day window
window = flt_pay[flt_pay["days_from_payday"].between(-5, 5)]
pay_agg = (window.groupby("days_from_payday")
                  .agg(orders=("ATD", "size"),
                       median_atd=("ATD", "median"),
                       p90_atd=("ATD", lambda s: s.quantile(0.90)),
                       n_days=("date", "nunique"))
                  .reset_index())
pay_agg["orders_per_day"] = (pay_agg["orders"]
                              / pay_agg["n_days"]).round(0)

c1, c2 = st.columns([3, 2])

with c1:
    fig = go.Figure()
    # Volume on left axis
    fig.add_trace(go.Bar(
        x=pay_agg["days_from_payday"], y=pay_agg["orders_per_day"],
        name="Avg orders per day",
        marker=dict(color=GREY, opacity=0.4),
        hovertemplate="<b>Day %{x:+d} from pay day</b><br>"
                      "%{y:,.0f} orders/day<extra></extra>",
    ))
    # Median ATD on right
    fig.add_trace(go.Scatter(
        x=pay_agg["days_from_payday"], y=pay_agg["median_atd"],
        yaxis="y2", mode="lines+markers", name="Median ATD",
        line=dict(color=EATS_GREEN, width=3),
        marker=dict(size=10, color=EATS_GREEN,
                    line=dict(color=DARK_BG, width=2)),
        hovertemplate="<b>Day %{x:+d} from pay day</b><br>"
                      "Median %{y:.1f} min<extra></extra>",
    ))
    # Pay day vertical band
    fig.add_vline(x=0, line_color="#FBBF24", line_width=2,
                  line_dash="dash",
                  annotation=dict(
                      text="<b>PAY DAY</b>",
                      font=dict(color="#FBBF24", size=11),
                      bgcolor=BLACK, borderpad=4,
                      yref="paper", y=1.05,
                  ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title=dict(text="Orders and ATD around pay day",
                   font=dict(color=TEXT_PRIMARY, size=14),
                   x=0, xanchor="left"),
        xaxis=dict(title="Days from nearest pay day",
                   tickmode="linear", dtick=1, range=[-5.5, 5.5]),
        yaxis=dict(title="Avg orders per day"),
        yaxis2=dict(title="Median ATD (min)", overlaying="y",
                    side="right", showgrid=False),
        legend=dict(orientation="h", y=1.15, x=0,
                    bgcolor="rgba(0,0,0,0)"),
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)

with c2:
    # KPIs that compare pay day adjacent to other days
    payday_window = pay_agg[pay_agg["days_from_payday"].isin([-1, 0, 1])]
    other_window = pay_agg[~pay_agg["days_from_payday"].isin([-1, 0, 1])]

    payday_atd = payday_window["median_atd"].mean()
    other_atd = other_window["median_atd"].mean()
    atd_gap = payday_atd - other_atd

    payday_volume = payday_window["orders_per_day"].mean()
    other_volume = other_window["orders_per_day"].mean()
    volume_gap_pct = (payday_volume - other_volume) / other_volume * 100

    n_paydays = flt_pay[flt_pay["days_from_payday"] == 0]["date"].nunique()

    st.markdown(f"""
    <div style="background-color: {CARD_BG}; padding: 20px;
                border-radius: 12px; border: 1px solid {DIVIDER};
                border-top: 3px solid #FBBF24; margin-bottom: 12px;">
        <div style="color: #FBBF24; font-size: 0.7rem;
                    text-transform: uppercase; letter-spacing: 0.1em;
                    font-weight: 700; margin-bottom: 8px;">
            SAMPLE SIZE NOTE
        </div>
        <div style="color: {TEXT_PRIMARY}; font-size: 0.9rem; line-height: 1.5;">
            Only <strong>{n_paydays} actual pay days</strong> in this window
            (Mar–Apr 2025). Treat patterns as directional, not conclusive.
        </div>
    </div>
    """, unsafe_allow_html=True)

    c2a, c2b = st.columns(2)
    with c2a:
        st.metric(
            "ATD on pay-day window",
            f"{payday_atd:.1f} min",
            f"{atd_gap:+.1f} min vs other days",
            delta_color="inverse",
        )
    with c2b:
        st.metric(
            "Volume on pay-day window",
            f"{payday_volume:,.0f}/day",
            f"{volume_gap_pct:+.1f}% vs other days",
        )

# Build the analytical takeaway
slowest_offset = pay_agg.loc[pay_agg["median_atd"].idxmax(),
                              "days_from_payday"]
slowest_atd = pay_agg["median_atd"].max()

if abs(atd_gap) < 0.5:
    atd_call = ("Pay day itself doesn't move ATD in any meaningful way "
                "in this 2-month window")
elif atd_gap > 0:
    atd_call = (f"Pay-day-adjacent days run about {atd_gap:.1f} min "
                "slower than other days")
else:
    atd_call = (f"Pay-day-adjacent days run about {abs(atd_gap):.1f} min "
                "faster than other days, which is counter-intuitive")

if abs(volume_gap_pct) < 5:
    vol_call = "and order volume is roughly flat"
elif volume_gap_pct > 0:
    vol_call = f"with volume {volume_gap_pct:+.0f}% higher"
else:
    vol_call = f"with volume {volume_gap_pct:+.0f}% lower"

st.markdown(f"""
<div class="insight-box">
<p><strong style="color: {EATS_GREEN};">📊 What this says:</strong>
{atd_call} {vol_call}. The slowest day in the window is offset
<strong>{slowest_offset:+d}</strong> from pay day at
<strong>{slowest_atd:.1f} min</strong> median ATD. With only {n_paydays}
pay days observed, we can't yet call this a real pattern, but the chart
shape gives ops a hypothesis to validate against a longer sample. The
operational question worth tracking: <em>do eaters order differently in
the days right before pay day (smaller orders, less premium delivery,
worse merchant mix), and is that what's pulling ATD?</em></p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# Segmentation
# ============================================================
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown('<span class="section-label">04 · Where the time hides</span>',
            unsafe_allow_html=True)
st.markdown("### Four segments tell the whole story")

st.markdown(f"""
<div style="color: {TEXT_SECONDARY}; margin-bottom: 16px; max-width: 700px;">
The biggest lever isn't geography. Territory variance is small. The real
spread lives in <strong>courier flow</strong> and
<strong>merchant surface</strong>, and the tables now show the volume
share so you can size each opportunity.
</div>
""", unsafe_allow_html=True)


def color_by_speed(v):
    if v < 33:
        return EATS_GREEN
    if v < 42:
        return ORANGE
    return CORAL


def segment_chart(seg, dim, title):
    seg = seg.sort_values("median_atd")
    colors = [color_by_speed(v) for v in seg["median_atd"]]
    # Build hover text that includes share of total
    hover_text = [
        f"<b>{row[dim]}</b><br>"
        f"Median ATD: {row['median_atd']:.1f} min<br>"
        f"Orders: {row['orders']:,} ({row['pct_of_total']:.1f}% of total)"
        for _, row in seg.iterrows()
    ]
    fig = go.Figure(go.Bar(
        x=seg["median_atd"], y=seg[dim], orientation="h",
        marker=dict(color=colors, line=dict(color=DARK_BG, width=1)),
        text=[f"<b>{v:.1f}</b>" for v in seg["median_atd"]],
        textposition="outside",
        textfont=dict(color=TEXT_PRIMARY, size=12),
        hovertext=hover_text,
        hoverinfo="text",
    ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title=dict(text=title, font=dict(color=TEXT_PRIMARY, size=14),
                   x=0, xanchor="left"),
        xaxis_title="Median ATD (min)",
        yaxis_title="",
        height=max(280, 50 * len(seg) + 100),
        margin=dict(l=20, r=80),
        showlegend=False,
    )
    return fig


tab1, tab2, tab3, tab4 = st.tabs([
    "📍 Territory",
    "🛵 Courier flow",
    "🏪 Merchant surface",
    "🌐 Geo archetype",
])

total_orders = len(flt)

for tab, dim, label in [
    (tab1, "territory", "Median ATD by territory"),
    (tab2, "courier_flow", "Median ATD by courier flow"),
    (tab3, "merchant_surface", "Median ATD by merchant surface"),
    (tab4, "geo_archetype", "Median ATD by geo archetype"),
]:
    with tab:
        seg = (flt.groupby(dim)
                  .agg(orders=("ATD", "size"),
                       median_atd=("ATD", "median"),
                       mean_atd=("ATD", "mean"),
                       p90_atd=("ATD", lambda s: s.quantile(0.90)))
                  .round(2))
        seg = seg[seg["orders"] >= 200].sort_values("median_atd").reset_index()
        # Add share of total
        seg["pct_of_total"] = (seg["orders"] / total_orders * 100).round(1)

        st.plotly_chart(segment_chart(seg, dim, label),
                        use_container_width=True)

        spread = seg["median_atd"].max() - seg["median_atd"].min()

        # Insight
        if dim == "territory":
            insight = (f"Spread of just <strong>{spread:.1f} min</strong> "
                       "between the fastest and slowest territory. Whatever "
                       "the levers are, geography barely moves the needle. "
                       "Don't burn cycles re-routing. Focus on flow and surface.")
        elif dim == "courier_flow":
            fastest = seg.iloc[0]
            slowest = seg.iloc[-1]
            insight = (f"<strong>{spread:.1f} minute spread</strong> between "
                       f"{fastest[dim]} ({fastest['median_atd']:.1f} min, "
                       f"{fastest['pct_of_total']:.1f}% of orders) and "
                       f"{slowest[dim]} ({slowest['median_atd']:.1f} min, "
                       f"{slowest['pct_of_total']:.1f}% of orders). "
                       "These are different operating models with different "
                       "supply economics, so they should not share dispatch "
                       "expectations. The volume share tells you how much "
                       "weight each lever has.")
        elif dim == "merchant_surface":
            pos_row = seg[seg[dim] == "POS"]
            pos_share = pos_row["pct_of_total"].iloc[0] if len(pos_row) else 0
            insight = (f"<strong>{spread:.1f} min</strong> spread across "
                       f"surfaces. POS handles {pos_share:.1f}% of orders "
                       "and runs faster. The non-POS cohort is finite and "
                       "addressable. Migrating high-volume slow merchants "
                       "is closer to a Merchant Success project than a tech build.")
        else:
            insight = (f"<strong>{spread:.1f} min</strong> spread between "
                       "geo archetypes. Useful for tailoring marketing "
                       "spend by zone, but the operational lever is "
                       "smaller than courier flow or merchant surface.")

        st.markdown(f"""
        <div class="insight-box">
        <p><strong style="color: {EATS_GREEN};">📊 What this says:</strong>
        {insight}</p>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("View detailed table"):
            display_seg = seg[[dim, "orders", "pct_of_total",
                               "median_atd", "mean_atd", "p90_atd"]].copy()
            display_seg.columns = [
                dim.replace("_", " ").title(),
                "Orders", "% of total", "Median ATD", "Mean ATD", "p90 ATD"
            ]
            st.dataframe(display_seg, use_container_width=True,
                         hide_index=True)

# ============================================================
# Time patterns
# ============================================================
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown('<span class="section-label">05 · When ops stresses</span>',
            unsafe_allow_html=True)
st.markdown("### Demand peaks aren't always ATD peaks")
st.markdown(f"""
<div style="color: {TEXT_SECONDARY}; margin-bottom: 16px; max-width: 700px;">
Late nights are slow because <strong>supply collapses</strong>, not because
demand spikes. And not every day looks the same. Use the day filter below
to compare how Friday's curve differs from Monday's.
</div>
""", unsafe_allow_html=True)

# Day of week filter for the hourly view
day_options = ["All days"] + ["Monday", "Tuesday", "Wednesday", "Thursday",
                              "Friday", "Saturday", "Sunday"]
selected_days = st.multiselect(
    "Compare days of the week",
    day_options,
    default=["All days"],
    help="Pick one or more days to overlay on the hourly chart. "
         "Useful for spotting whether weekend curves look different "
         "from weekday curves."
)

c1, c2 = st.columns([3, 2])

with c1:
    fig = go.Figure()

    # Always show the volume
    by_h_all = (flt.groupby("hour")
                  .agg(orders=("ATD", "size"))
                  .reset_index())
    fig.add_trace(go.Bar(
        x=by_h_all["hour"], y=by_h_all["orders"], name="Orders (all)",
        marker=dict(color=GREY, opacity=0.3),
        hovertemplate="<b>%{x}:00</b><br>%{y:,.0f} orders<extra></extra>",
    ))

    # ATD curves by day
    day_palette = {
        "All days": EATS_GREEN,
        "Monday": "#5BBFD6",
        "Tuesday": "#A78BFA",
        "Wednesday": "#F4A26A",
        "Friday": "#06C167",
        "Thursday": "#FBBF24",
        "Saturday": "#F46A4E",
        "Sunday": "#EC4899",
    }

    if not selected_days or "All days" in selected_days:
        by_h = (flt.groupby("hour")
                  .agg(median_atd=("ATD", "median"))
                  .reset_index())
        fig.add_trace(go.Scatter(
            x=by_h["hour"], y=by_h["median_atd"],
            yaxis="y2", mode="lines+markers", name="All days",
            line=dict(color=EATS_GREEN, width=3),
            marker=dict(size=8, color=EATS_GREEN,
                        line=dict(color=DARK_BG, width=2)),
            hovertemplate="<b>%{x}:00</b><br>"
                          "Median %{y:.1f} min<extra></extra>",
        ))

    for day in selected_days:
        if day == "All days":
            continue
        day_df = flt[flt["dow"] == day]
        if len(day_df) < 100:
            continue
        by_h = (day_df.groupby("hour")
                  .agg(median_atd=("ATD", "median"))
                  .reset_index())
        fig.add_trace(go.Scatter(
            x=by_h["hour"], y=by_h["median_atd"],
            yaxis="y2", mode="lines+markers", name=day,
            line=dict(color=day_palette.get(day, EATS_GREEN), width=2.5),
            marker=dict(size=6),
            hovertemplate=f"<b>{day} %{{x}}:00</b><br>"
                          "Median %{y:.1f} min<extra></extra>",
        ))

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        xaxis=dict(title="Hour", tickmode="linear", dtick=2),
        yaxis=dict(title="Orders (all days)"),
        yaxis2=dict(title="Median ATD (min)", overlaying="y",
                    side="right", showgrid=False),
        legend=dict(orientation="h", y=1.08, x=0,
                    bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=20, r=20, t=70, b=40),
        height=440,
    )
    st.plotly_chart(fig, use_container_width=True)

with c2:
    short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    full = ["Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"]
    by_d = (flt.groupby("dow")
              .agg(orders=("ATD", "size"), median_atd=("ATD", "median"))
              .reindex(full).reset_index())
    by_d["dow_short"] = short
    colors = [CORAL if d == "Sunday" else EATS_GREEN for d in by_d["dow"]]

    fig = go.Figure(go.Bar(
        x=by_d["dow_short"], y=by_d["median_atd"],
        marker=dict(color=colors, line=dict(color=DARK_BG, width=1)),
        text=[f"<b>{v:.1f}</b>" for v in by_d["median_atd"]],
        textposition="outside",
        textfont=dict(color=TEXT_PRIMARY, size=11),
        hovertemplate="<b>%{x}</b><br>Median %{y:.1f} min<extra></extra>",
    ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title=dict(text="Day of week",
                   font=dict(color=TEXT_PRIMARY, size=14),
                   x=0, xanchor="left"),
        yaxis=dict(title="Median ATD (min)"),
        margin=dict(l=20, r=20, t=70, b=40),
        height=440, showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

# Build a smarter, day-aware insight
fri_df = flt[flt["dow"] == "Friday"]
mon_df = flt[flt["dow"] == "Monday"]
fri_dinner = fri_df[fri_df["hour"].isin([19, 20, 21])]["ATD"].median() \
    if len(fri_df) > 100 else None
mon_dinner = mon_df[mon_df["hour"].isin([19, 20, 21])]["ATD"].median() \
    if len(mon_df) > 100 else None

if fri_dinner is not None and mon_dinner is not None:
    fri_vs_mon = fri_dinner - mon_dinner
    fri_text = (f"Friday dinner runs {fri_dinner:.1f} min vs Monday dinner "
                f"{mon_dinner:.1f} min, a "
                f"<strong>{abs(fri_vs_mon):.1f} min "
                f"{'gap' if abs(fri_vs_mon) >= 1 else 'difference'}</strong>.")
else:
    fri_text = ""

st.markdown(f"""
<div class="insight-box">
<p><strong style="color: {EATS_GREEN};">📊 What this says:</strong>
Lunch and dinner peaks are absorbed reasonably well, which is a sign that
the dispatch system is doing its job during peak hours. The damage is at
night when very few couriers are online and ATD jumps because of supply,
not demand. {fri_text} The fix here isn't a smarter algorithm. It's a
courier incentive schedule that gets riders online before the curve climbs.
Pair that with weekend volume forecasts and ops can stay ahead of the peak
instead of chasing it.</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# Courier Performance
# ============================================================
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown('<span class="section-label">06 · The slow tail</span>',
            unsafe_allow_html=True)
st.markdown("### Courier performance: is the slow tail really about distance?")

st.markdown(f"""
<div style="color: {TEXT_SECONDARY}; margin-bottom: 16px; max-width: 800px;">
Slow couriers might just be doing longer trips. The filter below lets you
control for that. Pick a distance band and see whether the p90 vs p50 gap
holds inside trips of similar length. If it does, the slow tail isn't a
distance problem, it's a courier behaviour problem, which is coachable.
</div>
""", unsafe_allow_html=True)

# Total distance filter
max_dist = float(np.ceil(flt["total_distance"].quantile(0.99)))
distance_range = st.slider(
    "Total distance band (km)",
    min_value=0.0,
    max_value=max_dist,
    value=(0.0, max_dist),
    step=0.5,
    help="Filter couriers' trips to a similar distance band. If the slow "
         "tail still shows up inside a tight band, distance isn't the excuse."
)

courier_flt = flt[
    (flt["total_distance"] >= distance_range[0])
    & (flt["total_distance"] <= distance_range[1])
]

cp = (courier_flt.groupby("driver_uuid")
        .agg(trips=("ATD", "size"),
             median_atd=("ATD", "median"),
             avg_distance=("total_distance", "mean")))
cp = cp[cp["trips"] >= 30].sort_values("median_atd")

if cp.empty:
    st.info("Not enough courier data inside this distance band. "
            "Widen the slider.")
else:
    p10, p50, p90 = cp["median_atd"].quantile([0.10, 0.50, 0.90])
    avg_dist_p10 = cp.head(int(len(cp)*0.10))["avg_distance"].mean()
    avg_dist_p90 = cp.tail(int(len(cp)*0.10))["avg_distance"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Top decile (p10)", f"{p10:.1f} min", "Fastest 10%")
    c2.metric("Typical (p50)", f"{p50:.1f} min", "Median courier")
    c3.metric("Slow decile (p90)", f"{p90:.1f} min",
              f"+{p90 - p50:.1f} min vs typical", delta_color="inverse")
    c4.metric("Avg trip length, p10 vs p90",
              f"{avg_dist_p10:.1f} vs {avg_dist_p90:.1f} km",
              help="If these are similar, the slow tail isn't doing "
                   "longer trips. It's just slower at the same trips.")

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=cp["median_atd"], nbinsx=50,
        marker=dict(color=EATS_GREEN, line=dict(color=DARK_BG, width=0.5)),
        hovertemplate="%{y} couriers<br>%{x:.1f} min<extra></extra>",
    ))
    fig.add_vline(x=p10, line_dash="dash", line_color="white", line_width=2,
                  annotation=dict(text=f"<b>p10 {p10:.1f}</b>",
                                  font=dict(color="white"),
                                  bgcolor=BLACK, borderpad=4))
    fig.add_vline(x=p50, line_color=GREY, line_width=2,
                  annotation=dict(text=f"<b>p50 {p50:.1f}</b>",
                                  font=dict(color=GREY),
                                  bgcolor=BLACK, borderpad=4))
    fig.add_vline(x=p90, line_dash="dot", line_color=CORAL, line_width=2,
                  annotation=dict(text=f"<b>p90 {p90:.1f}</b>",
                                  font=dict(color=CORAL),
                                  bgcolor=BLACK, borderpad=4))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        xaxis_title="Per-courier median ATD (minutes)",
        yaxis_title="Number of couriers",
        height=400, showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Insight
    dist_gap = avg_dist_p90 - avg_dist_p10
    if abs(dist_gap) < 0.5:
        dist_takeaway = (
            f"The fast decile and slow decile run trips of about the same "
            f"length ({avg_dist_p10:.1f} km vs {avg_dist_p90:.1f} km, "
            f"a {abs(dist_gap):.1f} km gap). That means the slow tail isn't "
            "a distance problem. Same trips, different times. Coachable."
        )
    elif dist_gap > 0:
        dist_takeaway = (
            f"The slow decile runs slightly longer trips on average "
            f"({avg_dist_p90:.1f} km vs {avg_dist_p10:.1f} km, "
            f"+{dist_gap:.1f} km). That explains some of the gap, but "
            "not all of it. Tighten the distance slider to control for "
            "that and see how much remains."
        )
    else:
        dist_takeaway = (
            f"The slow decile actually runs <strong>shorter</strong> trips "
            f"on average ({avg_dist_p90:.1f} km vs {avg_dist_p10:.1f} km). "
            "So distance isn't protecting them. They're slow at the same or "
            "shorter trips, which makes the case for coaching even cleaner."
        )

    st.markdown(f"""
    <div class="insight-box">
    <p><strong style="color: {EATS_GREEN};">📊 What this says:</strong>
    Restricted to <strong>{len(cp):,} couriers</strong> with ≥30 trips
    in this distance band. The p90 to p50 gap of
    <strong>{p90 - p50:.1f} minutes</strong> is the slow-tail opportunity.
    {dist_takeaway} Field Operations can act on this individually with
    route coaching, hot zone hints.</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# Distance Breakdown
# ============================================================
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown('<span class="section-label">07 · What predicts ATD</span>',
            unsafe_allow_html=True)
st.markdown("### Pickup distance vs dropoff distance: which leg matters more?")

st.markdown(f"""
<div style="color: {TEXT_SECONDARY}; margin-bottom: 16px; max-width: 800px;">
Pickup is courier to restaurant. Dropoff is restaurant to eater. The
reference markers at 5 and 10 km make it easy to read off the typical
ATD impact of an extra kilometre on each leg.
</div>
""", unsafe_allow_html=True)

c1, c2 = st.columns(2)

# Bucket distances into 1-km bins.

samp = flt.sample(min(8000, len(flt)), random_state=0)


def binned_trend(d, x_col, max_x=15):
    """Return a smooth median-line by binning the distance axis."""
    d = d[(d[x_col] > 0) & (d[x_col] <= max_x)].copy()
    d["bin"] = pd.cut(d[x_col], bins=np.arange(0, max_x + 0.5, 0.5))
    line = (d.groupby("bin", observed=True)
              .agg(x_mid=(x_col, "mean"),
                   y_med=("ATD", "median"),
                   n=("ATD", "size"))
              .reset_index())
    line = line[line["n"] >= 50]
    return line


with c1:
    st.markdown("**Pickup distance vs ATD**")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=samp["pickup_distance"], y=samp["ATD"],
        mode="markers",
        marker=dict(color=EATS_GREEN, size=4, opacity=0.35),
        name="Trips",
        hovertemplate="%{x:.1f} km<br>%{y:.1f} min<extra></extra>",
    ))
    pk_line = binned_trend(flt, "pickup_distance", max_x=15)
    fig.add_trace(go.Scatter(
        x=pk_line["x_mid"], y=pk_line["y_med"],
        mode="lines+markers",
        line=dict(color=CORAL, width=3),
        marker=dict(color=CORAL, size=8),
        name="Median ATD by distance",
        hovertemplate="<b>%{x:.1f} km</b><br>"
                      "Median %{y:.1f} min<extra></extra>",
    ))
    # Reference markers at 5 and 10 km
    for ref in [5, 10]:
        match = pk_line[(pk_line["x_mid"] >= ref - 0.5)
                        & (pk_line["x_mid"] <= ref + 0.5)]
        if len(match):
            y_at_ref = match["y_med"].iloc[0]
            fig.add_vline(
                x=ref, line_dash="dash", line_color="white",
                line_width=1, opacity=0.4,
                annotation=dict(
                    text=f"<b>{ref}km<br>{y_at_ref:.0f}min</b>",
                    font=dict(color="white", size=10),
                    bgcolor=BLACK, borderpad=3,
                    yref="paper", y=0.95,
                ),
            )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        xaxis=dict(title="Pickup distance (km)", range=[0, 15]),
        yaxis=dict(title="ATD (min)", range=[0, 90]),
        height=420,
        legend=dict(orientation="h", y=1.1, x=0,
                    bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.markdown("**Dropoff distance vs ATD**")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=samp["dropoff_distance"], y=samp["ATD"],
        mode="markers",
        marker=dict(color=TEAL, size=4, opacity=0.35),
        name="Trips",
        hovertemplate="%{x:.1f} km<br>%{y:.1f} min<extra></extra>",
    ))
    dp_line = binned_trend(flt, "dropoff_distance", max_x=15)
    fig.add_trace(go.Scatter(
        x=dp_line["x_mid"], y=dp_line["y_med"],
        mode="lines+markers",
        line=dict(color=CORAL, width=3),
        marker=dict(color=CORAL, size=8),
        name="Median ATD by distance",
        hovertemplate="<b>%{x:.1f} km</b><br>"
                      "Median %{y:.1f} min<extra></extra>",
    ))
    for ref in [5, 10]:
        match = dp_line[(dp_line["x_mid"] >= ref - 0.5)
                        & (dp_line["x_mid"] <= ref + 0.5)]
        if len(match):
            y_at_ref = match["y_med"].iloc[0]
            fig.add_vline(
                x=ref, line_dash="dash", line_color="white",
                line_width=1, opacity=0.4,
                annotation=dict(
                    text=f"<b>{ref}km<br>{y_at_ref:.0f}min</b>",
                    font=dict(color="white", size=10),
                    bgcolor=BLACK, borderpad=3,
                    yref="paper", y=0.95,
                ),
            )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        xaxis=dict(title="Dropoff distance (km)", range=[0, 15]),
        yaxis=dict(title="ATD (min)", range=[0, 90]),
        height=420,
        legend=dict(orientation="h", y=1.1, x=0,
                    bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig, use_container_width=True)

# Insight
def y_at(line, ref):
    m = line[(line["x_mid"] >= ref - 0.5) & (line["x_mid"] <= ref + 0.5)]
    return float(m["y_med"].iloc[0]) if len(m) else None


pk_5, pk_10 = y_at(pk_line, 5), y_at(pk_line, 10)
dp_5, dp_10 = y_at(dp_line, 5), y_at(dp_line, 10)

corr_pickup = flt["ATD"].corr(flt["pickup_distance"])
corr_dropoff = flt["ATD"].corr(flt["dropoff_distance"])
stronger = "dropoff" if abs(corr_dropoff) > abs(corr_pickup) else "pickup"

if pk_5 and pk_10 and dp_5 and dp_10:
    pk_slope = pk_10 - pk_5
    dp_slope = dp_10 - dp_5
    ref_text = (
        f"Reading the markers: at 5 km a typical pickup adds about "
        f"{pk_5:.0f} min and a typical dropoff adds about {dp_5:.0f} min. "
        f"At 10 km the pickup leg climbs to {pk_10:.0f} min "
        f"(+{pk_slope:.0f} min for the extra 5 km) while the dropoff "
        f"climbs to {dp_10:.0f} min (+{dp_slope:.0f} min). "
    )
else:
    ref_text = ""

st.markdown(f"""
<div class="insight-box">
<p><strong style="color: {EATS_GREEN};">📊 What this says:</strong>
Pickup distance correlation with ATD is <strong>{corr_pickup:.2f}</strong>.
Dropoff distance correlation is <strong>{corr_dropoff:.2f}</strong>. The
<strong>{stronger}</strong> leg pulls harder. {ref_text}
Neither correlation crosses 0.5, which means more than half of the variation
in ATD has nothing to do with distance. That gap is preparation time,
dispatch latency, traffic, and how the courier handles the trip. Distance
is the floor. Operating model is the ceiling.</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(f"""
<div style="background: linear-gradient(135deg, {BLACK}, {CARD_BG});
            padding: 32px; border-radius: 16px;
            border: 1px solid {DIVIDER}; margin-top: 24px;">
    <div class="section-label">THE TAKEAWAY</div>
    <h2 style="color: {TEXT_PRIMARY} !important; margin: 8px 0 4px 0;
               font-size: 1.75rem !important;">
        We don't need a smarter map.
    </h2>
    <h2 style="color: {EATS_GREEN} !important; margin: 0 0 24px 0;
               font-size: 1.75rem !important;">
        We need a smarter operating model.
    </h2>
    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr;
                gap: 20px; margin-top: 24px;">
        <div>
            <div style="color: {EATS_GREEN}; font-weight: 700;
                        font-size: 0.875rem; margin-bottom: 4px;">
                01 · DISPATCH
            </div>
            <div style="color: {TEXT_PRIMARY};">
                Tier dispatch by courier flow.
            </div>
        </div>
        <div>
            <div style="color: {EATS_GREEN}; font-weight: 700;
                        font-size: 0.875rem; margin-bottom: 4px;">
                02 · MERCHANT
            </div>
            <div style="color: {TEXT_PRIMARY};">
                Migrate slow merchants to POS.
            </div>
        </div>
        <div>
            <div style="color: {EATS_GREEN}; font-weight: 700;
                        font-size: 0.875rem; margin-bottom: 4px;">
                03 · COURIER
            </div>
            <div style="color: {TEXT_PRIMARY};">
                Coach the slow tail of the fleet.
            </div>
        </div>
    </div>
</div>
<br>
<div style="text-align: center; color: {TEXT_MUTED};
            font-size: 0.8rem; padding: 16px 0;">
ATD Optimization Dashboard · Automation & Analytics · Uber Eats business case
</div>
""", unsafe_allow_html=True)
