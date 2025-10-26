# app.py
import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from io import StringIO

st.set_page_config(page_title="Fuel Price Dashboard", layout="wide")

# =======================
# LOAD CSS
# =======================
def load_css(path="style.css"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

load_css()

# =======================
# THEME PALETTE (consistent everywhere)
# =======================
PALETTE = {
    "Houston": "#9A3412",          # rust
    "Texas Statewide": "#B45309",   # ochre
    "U.S. National": "#065F46",     # moss
    "Houston - Texas": "#A16207",   # golden brown
    "Houston - U.S.": "#7C3E0B",    # chestnut
}
DOMAIN_SERIES = ["Houston", "Texas Statewide", "U.S. National"]
DOMAIN_SPREADS = ["Houston - Texas", "Houston - U.S."]

# Heatmap: peach -> terracotta -> deep maroon
HEATMAP_RANGE = ["#FDEAD7", "#E6A06A", "#9B2C12"]

# =======================
# LOAD DATA
# =======================
df = pd.read_csv("prices.csv", parse_dates=["date"])

MONTH_ORDER = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# =======================
# FILTER BAR (no defaults; empty = all)
# =======================
with st.container():
    f1, f2, f3 = st.columns([2, 3, 3], gap="small")
    years_all = sorted(df["date"].dt.year.unique().tolist())
    months_all = list(range(1, 12+1))
    months_labels = {i: pd.Timestamp(2000, i, 1).strftime("%b") for i in months_all}

    with f1:
        st.markdown("#### Filters")
    with f2:
        sel_years = st.multiselect("Year", options=years_all, default=[])
    with f3:
        sel_months_lbl = st.multiselect("Month", options=[months_labels[m] for m in months_all], default=[])
        sel_months = [k for k, v in months_labels.items() if v in sel_months_lbl]

# “empty = all” behavior
yrs = sel_years if sel_years else years_all
mos = sel_months if sel_months else months_all

df_filt = df[df["date"].dt.year.isin(yrs) & df["date"].dt.month.isin(mos)].copy()
if df_filt.empty:
    st.warning("No data for the selected filters.")
    st.stop()

# Prepare sorts
df_desc = df_filt.sort_values("date", ascending=False).reset_index(drop=True)
df_trend = df_filt.sort_values("date", ascending=True).reset_index(drop=True)

# Latest row for KPIs
latest = df_desc.iloc[0]
latest_date = latest["date"].strftime("%B %Y")

def pct_change(new, old):
    if old is None or pd.isna(old) or old == 0:
        return None
    return (new - old) / old

# =======================
# HEADER
# =======================
st.markdown('<div class="title-wrap"><h1>Houston vs Texas & U.S. • Regular Gas</h1><p class="subtitle">Monthly prices ($/gal), benchmarks & changes.</p></div>', unsafe_allow_html=True)

# =======================
# KPIs (subtle cards)
# =======================
hou_now = float(latest["gasoline_price"])
tx_now  = float(latest["texas_avg"])
us_now  = float(latest["national_avg"])
diff_tx = hou_now - tx_now
diff_us = hou_now - us_now

prev_m = df_desc.iloc[1] if len(df_desc) > 1 else None
prev_y = df_desc.iloc[12] if len(df_desc) > 12 else None
hou_mom = pct_change(hou_now, float(prev_m["gasoline_price"]) if prev_m is not None else None)
hou_yoy = pct_change(hou_now, float(prev_y["gasoline_price"]) if prev_y is not None else None)

k1, k2, k3, k4 = st.columns(4, gap="small")
with k1:
    st.metric("Houston ($/gal)", f"${hou_now:.3f}")
    st.caption(f"As of {latest_date}")
with k2:
    st.metric("Texas ($/gal)", f"${tx_now:.3f}")
    st.caption(f"As of {latest_date}")
with k3:
    st.metric("U.S. ($/gal)", f"${us_now:.3f}")
    st.caption(f"As of {latest_date}")
with k4:
    st.metric("Houston − Texas", f"{diff_tx:+.3f} $/gal")

st.markdown(
    f"""
<div class="note">
<strong>Quick read:</strong> Houston is <strong>{abs(diff_tx):.3f} $/gal {'below' if diff_tx<0 else 'above' if diff_tx>0 else 'at'}</strong> Texas and <strong>{abs(diff_us):.3f} $/gal {'below' if diff_us<0 else 'above' if diff_us>0 else 'at'}</strong> the U.S.  
MoM: <strong>{(hou_mom or 0)*100:+.1f}%</strong> • YoY: <strong>{(hou_yoy or 0)*100:+.1f}%</strong>.
</div>
""",
    unsafe_allow_html=True
)

st.markdown("---")

# =======================
# LINE: Monthly Trends (consistent colors, last-point labels)
# =======================
st.subheader("Monthly Gasoline Price Trends")

df_long = df_trend.melt(
    id_vars=["date"],
    value_vars=["gasoline_price", "texas_avg", "national_avg"],
    var_name="series",
    value_name="price"
).replace({"series": {
    "gasoline_price": "Houston",
    "texas_avg": "Texas Statewide",
    "national_avg": "U.S. National"
}})

trend_chart = (
    alt.Chart(df_long)
    .mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(format="%Y-%m", labelAngle=-30)),
        y=alt.Y("price:Q", title="USD per Gallon"),
        color=alt.Color("series:N", title=None, scale=alt.Scale(domain=DOMAIN_SERIES, range=[PALETTE[s] for s in DOMAIN_SERIES])),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m"),
            alt.Tooltip("series:N", title=""),
            alt.Tooltip("price:Q", title="Price", format=".3f"),
        ],
    )
    .properties(height=360)
)

# Label last point only
lastpoints = df_long.sort_values("date").groupby("series", as_index=False).last()
trend_labels = (
    alt.Chart(lastpoints)
    .mark_text(align="left", dx=6)
    .encode(
        x="date:T",
        y="price:Q",
        text=alt.Text("price:Q", format=".2f"),
        color=alt.Color("series:N", legend=None, scale=alt.Scale(domain=DOMAIN_SERIES, range=[PALETTE[s] for s in DOMAIN_SERIES])),
    )
)

st.altair_chart(trend_chart + trend_labels, use_container_width=True)

# Narrative
peak_row = df_trend.loc[df_trend["gasoline_price"].idxmax()]
min_row  = df_trend.loc[df_trend["gasoline_price"].idxmin()]
st.markdown(
    f"""
**Range (selection):** Peak **{pd.to_datetime(peak_row['date']).strftime('%b %Y')}** at **${float(peak_row['gasoline_price']):.3f}/gal**; 
trough **{pd.to_datetime(min_row['date']).strftime('%b %Y')}** at **${float(min_row['gasoline_price']):.3f}/gal**.
"""
)

st.markdown("---")

# =======================
# LINE: Spreads (consistent colors, last-point labels)
# =======================
st.subheader("Houston Price Spreads vs Texas & U.S.")

df_spread = df_trend.copy()
df_spread["Houston - Texas"] = df_spread["gasoline_price"] - df_spread["texas_avg"]
df_spread["Houston - U.S."]  = df_trend["gasoline_price"] - df_trend["national_avg"]

spread_long = df_spread.melt(
    id_vars=["date"],
    value_vars=DOMAIN_SPREADS,
    var_name="spread",
    value_name="value"
).dropna(subset=["value"])

spread_chart = (
    alt.Chart(spread_long)
    .mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(format="%Y-%m", labelAngle=-30)),
        y=alt.Y("value:Q", title="Spread ($/gal)"),
        color=alt.Color("spread:N", title=None, scale=alt.Scale(domain=DOMAIN_SPREADS, range=[PALETTE[s] for s in DOMAIN_SPREADS])),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m"),
            alt.Tooltip("spread:N", title=""),
            alt.Tooltip("value:Q", title="Value", format="+.3f"),
        ],
    )
    .properties(height=280)
)

spread_last = spread_long.sort_values("date").groupby("spread", as_index=False).last()
spread_labels = (
    alt.Chart(spread_last)
    .mark_text(align="left", dx=6)
    .encode(
        x="date:T",
        y="value:Q",
        text=alt.Text("value:Q", format="+.2f"),
        color=alt.Color("spread:N", legend=None, scale=alt.Scale(domain=DOMAIN_SPREADS, range=[PALETTE[s] for s in DOMAIN_SPREADS])),
    )
)
st.altair_chart(spread_chart + spread_labels, use_container_width=True)

st.markdown("---")

# =======================
# HEATMAP: Seasonality
# =======================
st.subheader("Seasonality — Avg Houston Price by Month & Year")

season = (
    df_trend.assign(
        year=df_trend["date"].dt.year,
        month_num=df_trend["date"].dt.month,
        month_lbl=df_trend["date"].dt.strftime("%b")
    )
    .groupby(["year", "month_num", "month_lbl"], as_index=False)["gasoline_price"]
    .mean()
    .rename(columns={"gasoline_price": "avg_price"})
)
season["month_lbl"] = pd.Categorical(season["month_lbl"], categories=MONTH_ORDER, ordered=True)
season = season.sort_values(["year", "month_num"])

heatmap = alt.Chart(season).mark_rect().encode(
    x=alt.X("month_lbl:N", title="Month", sort=MONTH_ORDER),
    y=alt.Y("year:O", title="Year"),
    color=alt.Color("avg_price:Q", title="Avg Price ($/gal)", scale=alt.Scale(range=HEATMAP_RANGE)),
    tooltip=[
        alt.Tooltip("year:O", title="Year"),
        alt.Tooltip("month_lbl:N", title="Month"),
        alt.Tooltip("avg_price:Q", title="Avg Price ($/gal)", format=".3f"),
    ],
).properties(height=320)

# Text labels but slightly translucent to avoid clutter
heatmap_labels = alt.Chart(season).mark_text(baseline='middle', align='center', opacity=0.8).encode(
    x=alt.X("month_lbl:N", sort=MONTH_ORDER),
    y=alt.Y("year:O"),
    text=alt.Text("avg_price:Q", format=".3f")
)

st.altair_chart(heatmap + heatmap_labels, use_container_width=True)

st.markdown("---")

# =======================
# GROUPED BAR: Yearly Average Prices (clustered by year)
# =======================
st.subheader("Yearly Average Prices (Grouped by Year)")

yearly = (
    df_trend.assign(year=df_trend["date"].dt.year)
    .groupby("year", as_index=False)[["gasoline_price", "texas_avg", "national_avg"]]
    .mean()
    .rename(columns={
        "gasoline_price": "Houston",
        "texas_avg": "Texas Statewide",
        "national_avg": "U.S. National"
    })
)

yearly_long = yearly.melt(id_vars=["year"], var_name="series", value_name="avg_price")

# Proper clustered bars via xOffset
bars = (
    alt.Chart(yearly_long)
    .mark_bar()
    .encode(
        x=alt.X("year:O", title="Year"),
        xOffset=alt.X("series:N", title=None, sort=DOMAIN_SERIES),
        y=alt.Y("avg_price:Q", title="Average Price ($/gal)"),
        color=alt.Color("series:N", title=None, scale=alt.Scale(domain=DOMAIN_SERIES, range=[PALETTE[s] for s in DOMAIN_SERIES])),
        tooltip=[
            alt.Tooltip("year:O", title="Year"),
            alt.Tooltip("series:N", title=""),
            alt.Tooltip("avg_price:Q", title="Avg Price", format=".3f"),
        ],
    )
    .properties(height=340)
)

labels = (
    alt.Chart(yearly_long)
    .mark_text(dy=-6, size=11)
    .encode(
        x=alt.X("year:O"),
        xOffset=alt.X("series:N", sort=DOMAIN_SERIES),
        y=alt.Y("avg_price:Q"),
        text=alt.Text("avg_price:Q", format=".3f"),
        color=alt.value("#1f2937")  # slate-800
    )
)

st.altair_chart(bars + labels, use_container_width=True)

# Yearly highlight
hou_year_max = yearly.loc[yearly["Houston"].idxmax()]
st.markdown(
    f"""**Highest Houston yearly avg (selection):** **{int(hou_year_max['year'])}** at **${hou_year_max['Houston']:.2f}/gal**."""
)

st.markdown("---")

# =======================
# LINE: MoM & YoY % (consistent colors)
# =======================
st.subheader("Houston % Change — MoM & YoY")

chg = df_trend.copy()
chg["prev_m"] = chg["gasoline_price"].shift(1)
chg["prev_y"] = chg["gasoline_price"].shift(12)
chg["mom_pct"] = (chg["gasoline_price"] - chg["prev_m"]) / chg["prev_m"].replace(0, pd.NA)
chg["yoy_pct"] = (chg["gasoline_price"] - chg["prev_y"]) / chg["prev_y"].replace(0, pd.NA)

mom_yoy_long = (
    chg[["date", "mom_pct", "yoy_pct"]]
    .melt(id_vars=["date"], var_name="metric", value_name="pct")
    .dropna(subset=["pct"])
    .replace({"metric": {"mom_pct": "MoM %", "yoy_pct": "YoY %"}})
)

pct_colors = {"MoM %": "#8C3A1C", "YoY %": "#3F7B57"}  # warm rust + moss

pct_chart = (
    alt.Chart(mom_yoy_long)
    .mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(format="%Y-%m", labelAngle=-30)),
        y=alt.Y("pct:Q", title="Percent Change", axis=alt.Axis(format="%")),
        color=alt.Color("metric:N", title=None, scale=alt.Scale(domain=["MoM %","YoY %"], range=[pct_colors["MoM %"], pct_colors["YoY %"]])),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m"),
            alt.Tooltip("metric:N", title=""),
            alt.Tooltip("pct:Q", title="Change", format=".1%"),
        ],
    )
    .properties(height=320)
)
st.altair_chart(pct_chart, use_container_width=True)

# =======================
# SUBTLE DOWNLOAD (at the very end)
# =======================
csv_buf = StringIO()
df_filt.sort_values("date").to_csv(csv_buf, index=False)
st.markdown('<div class="dl-wrap">', unsafe_allow_html=True)
st.download_button(
    "Download filtered CSV",
    data=csv_buf.getvalue(),
    file_name="prices_filtered.csv",
    mime="text/csv",
    use_container_width=False,
)
st.markdown('</div>', unsafe_allow_html=True)
