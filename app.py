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
        pass  # run without custom styles if missing

load_css()

# =======================
# LOAD DATA
# =======================
df = pd.read_csv("prices.csv", parse_dates=["date"])

# Month helpers
MONTH_ORDER = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# =======================
# FILTER BAR
# =======================
with st.container():
    fl_col1, fl_col2, fl_col3 = st.columns([2, 3, 2], gap="small")

    years_all = sorted(df["date"].dt.year.unique().tolist())
    months_all = list(range(1, 13))
    months_labels = {i: pd.Timestamp(2000, i, 1).strftime("%b") for i in months_all}

    with fl_col1:
        st.markdown("##### Filters")
    with fl_col2:
        sel_years = st.multiselect(
            "Year",
            options=years_all,
            default=years_all,
            placeholder="Select years…",
        )
    with fl_col3:
        sel_months_lbl = st.multiselect(
            "Month",
            options=[months_labels[m] for m in months_all],
            default=[months_labels[m] for m in months_all],
            placeholder="Select months…",
        )
        sel_months = [k for k, v in months_labels.items() if v in sel_months_lbl]

# Apply filters
df_filt = df[
    df["date"].dt.year.isin(sel_years) &
    df["date"].dt.month.isin(sel_months)
].copy()

if df_filt.empty:
    st.warning("No data for the selected filters.")
    st.stop()

# Allow CSV download for the filtered slice
csv_buf = StringIO()
df_filt.sort_values("date").to_csv(csv_buf, index=False)
st.download_button(
    "Download filtered CSV",
    data=csv_buf.getvalue(),
    file_name="prices_filtered.csv",
    mime="text/csv",
    use_container_width=True,
)

# Sort both ways for convenience (filtered)
df_desc = df_filt.sort_values("date", ascending=False).reset_index(drop=True)
df_trend = df_filt.sort_values("date", ascending=True).reset_index(drop=True)

# Latest row for KPIs
latest = df_desc.iloc[0]
latest_date = latest["date"].strftime("%B %Y")

# Helper(s)
def pct_change(new, old):
    if old is None or pd.isna(old) or old == 0:
        return None
    return (new - old) / old

# =======================
# HEADER
# =======================
st.title("Houston Gasoline Prices vs Texas & U.S. (2020–2025)")
st.caption("Monthly regular gasoline prices ($/gal), with benchmarks and change metrics.")

# =======================
# KPI ROW 1: Latest Prices (card-styled via CSS)
# =======================
c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Latest Houston Price ($/gal)", f"${latest['gasoline_price']:.3f}")
    st.caption(f"As of {latest_date}")

with c2:
    st.metric("Latest Texas Price ($/gal)", f"${latest['texas_avg']:.3f}")
    st.caption(f"As of {latest_date}")

with c3:
    st.metric("Latest U.S. National Price ($/gal)", f"${latest['national_avg']:.3f}")
    st.caption(f"As of {latest_date}")

# ---- KPI narrative (Comparison) ----
hou_now = float(latest["gasoline_price"])
tx_now  = float(latest["texas_avg"])
us_now  = float(latest["national_avg"])

diff_tx = hou_now - tx_now
diff_us = hou_now - us_now

prev_m = df_desc.iloc[1] if len(df_desc) > 1 else None
prev_y = df_desc.iloc[12] if len(df_desc) > 12 else None

hou_mom = pct_change(hou_now, float(prev_m["gasoline_price"]) if prev_m is not None else None)
hou_yoy = pct_change(hou_now, float(prev_y["gasoline_price"]) if prev_y is not None else None)

st.markdown(
    f"""
**What the latest month says:**  
- Houston is **{abs(diff_tx):.3f} \\$/gal {'below' if diff_tx < 0 else 'above' if diff_tx > 0 else 'at'}** the Texas average and **{abs(diff_us):.3f} \\$/gal {'below' if diff_us < 0 else 'above' if diff_us > 0 else 'at'}** the U.S. average.  
- Month-over-month change for Houston: **{(hou_mom or 0)*100:+.1f}%**; year-over-year: **{(hou_yoy or 0)*100:+.1f}%** (positive = increase).  
*Use these to quickly gauge relative pricing and short/long-term direction.*
"""
)

# =======================
# KPI ROW 2: Spreads (instant view)
# =======================
spread_tx_latest = hou_now - tx_now
spread_us_latest = hou_now - us_now

s1, s2 = st.columns(2)
with s1:
    st.metric("Spread: Houston − Texas ($/gal)", f"${spread_tx_latest:+.3f}")
    st.caption(f"As of {latest_date}")
with s2:
    st.metric("Spread: Houston − U.S. ($/gal)", f"${spread_us_latest:+.3f}")
    st.caption(f"As of {latest_date}")

st.markdown("---")

# =======================
# KPI ROW 3: MoM % and YoY % (latest usable)
# =======================
chg = df_trend.copy()
chg["prev_m"] = chg["gasoline_price"].shift(1)
chg["prev_y"] = chg["gasoline_price"].shift(12)
chg["mom_pct"] = (chg["gasoline_price"] - chg["prev_m"]) / chg["prev_m"].replace(0, pd.NA)
chg["yoy_pct"] = (chg["gasoline_price"] - chg["prev_y"]) / chg["prev_y"].replace(0, pd.NA)

if not chg.dropna(subset=["mom_pct"]).empty:
    mom_row = chg.dropna(subset=["mom_pct"]).iloc[-1]
    mom_date = pd.to_datetime(mom_row["date"]).strftime("%B %Y")
else:
    mom_row, mom_date = {"mom_pct": 0}, latest_date

if not chg.dropna(subset=["yoy_pct"]).empty:
    yoy_row = chg.dropna(subset=["yoy_pct"]).iloc[-1]
    yoy_date = pd.to_datetime(yoy_row["date"]).strftime("%B %Y")
else:
    yoy_row, yoy_date = {"yoy_pct": 0}, latest_date

k1, k2 = st.columns(2)
with k1:
    st.metric("MoM % (Houston)", f"{mom_row['mom_pct']*100:+.1f}%")
    st.caption(f"As of {mom_date}")
with k2:
    st.metric("YoY % (Houston)", f"{yoy_row['yoy_pct']*100:+.1f}%")
    st.caption(f"As of {yoy_date}")

st.markdown("---")

# =======================
# LINE CHART: Monthly Trends (filtered)
# =======================
st.subheader("Monthly Gasoline Price Trends")

df_long = df_trend.melt(
    id_vars=["date"],
    value_vars=["gasoline_price", "texas_avg", "national_avg"],
    var_name="series",
    value_name="price"
)
name_map = {
    "gasoline_price": "Houston",
    "texas_avg": "Texas Statewide",
    "national_avg": "U.S. National",
}
df_long["series"] = df_long["series"].map(name_map)

trend_chart = (
    alt.Chart(df_long)
    .mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="Monthly Date", axis=alt.Axis(format="%Y-%m", labelAngle=-30)),
        y=alt.Y("price:Q", title="Gasoline Price ($/gal)"),
        color=alt.Color("series:N", title=None),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m"),
            alt.Tooltip("series:N", title=""),
            alt.Tooltip("price:Q", title="Price ($/gal)", format=".3f"),
        ],
    )
    .properties(height=380)
)

# ADD LAST-POINT LABELS ONLY (keeps labels tidy)
lastpoints = (
    df_long.sort_values("date")
           .groupby("series", as_index=False)
           .last()
)
trend_labels = (
    alt.Chart(lastpoints)
    .mark_text(align="left", dx=6)
    .encode(
        x="date:T",
        y="price:Q",
        text=alt.Text("price:Q", format=".2f"),
        color=alt.Color("series:N", legend=None),
    )
)
st.altair_chart(trend_chart + trend_labels, use_container_width=True)

# ---- Trend narrative ----
peak_row = df_trend.loc[df_trend["gasoline_price"].idxmax()]
peak_val = float(peak_row["gasoline_price"])
peak_date = pd.to_datetime(peak_row["date"]).strftime("%B %Y")
min_row = df_trend.loc[df_trend["gasoline_price"].idxmin()]
min_val = float(min_row["gasoline_price"])
min_date = pd.to_datetime(min_row["date"]).strftime("%B %Y")

st.markdown(
    f"""
**How prices evolved:**  
- Local peak occurred in **{peak_date}** at **${peak_val:.3f}/gal**, with the sharpest run-up centered in **2022**.  
- Local trough since selection start was **{min_date}** at **${min_val:.3f}/gal**.  
- Houston generally tracks state and national moves, but the gap to U.S. widens during high-price periods (see spreads below).
"""
)

st.markdown("---")

# =======================
# LINE CHART: Houston Price Spreads vs Texas & U.S.
# =======================
st.subheader("Houston Price Spreads vs Texas & U.S.")

df_spread = df_trend.copy()
df_spread["Houston - Texas"] = df_spread["gasoline_price"] - df_spread["texas_avg"]
df_spread["Houston - U.S."] = df_trend["gasoline_price"] - df_trend["national_avg"]

spread_long = df_spread.melt(
    id_vars=["date"],
    value_vars=["Houston - Texas", "Houston - U.S."],
    var_name="spread",
    value_name="value"
).dropna(subset=["value"])

spread_chart = (
    alt.Chart(spread_long)
    .mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="Monthly Date", axis=alt.Axis(format="%Y-%m", labelAngle=-30)),
        y=alt.Y("value:Q", title="Spread ($/gal)"),
        color=alt.Color("spread:N", title=None),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m"),
            alt.Tooltip("spread:N", title=""),
            alt.Tooltip("value:Q", title="Value ($/gal)", format="+.3f"),
        ],
    )
    .properties(height=320)
)

# Label last point only for each spread
spread_last = spread_long.sort_values("date").groupby("spread", as_index=False).last()
spread_labels = (
    alt.Chart(spread_last)
    .mark_text(align="left", dx=6)
    .encode(
        x="date:T",
        y="value:Q",
        text=alt.Text("value:Q", format="+.2f"),
        color=alt.Color("spread:N", legend=None),
    )
)
st.altair_chart(spread_chart + spread_labels, use_container_width=True)

# ---- Spread narrative ----
def slope_last_n(series, n=3):
    s = series.dropna().tail(n)
    if len(s) < 2:
        return np.nan
    x = np.arange(len(s))
    coef = np.polyfit(x, s.values, 1)[0]
    return coef

slope_tx = slope_last_n(df_spread["Houston - Texas"], 3)
slope_us = slope_last_n(df_spread["Houston - U.S."], 3)

st.markdown(
    f"""
**How to read spreads:**  
- Positive spread = **Houston priced above** the benchmark; negative = **below**.  
- Latest spreads: **Houston–Texas: {spread_tx_latest:+.3f} \\$/gal**, **Houston–U.S.: {spread_us_latest:+.3f} \\$/gal**.  
- Recent trend (last ~3 months): spreads vs Texas **{'widening' if slope_tx > 0 else 'narrowing' if slope_tx < 0 else 'flat'}**, vs U.S. **{'widening' if slope_us > 0 else 'narrowing' if slope_us < 0 else 'flat'}**.
"""
)

st.markdown("---")

# =======================
# HEATMAP: Seasonality — Average Houston Price by Month & Year
# =======================
st.subheader("Seasonality — Average Houston Price by Month and Year")

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
    color=alt.Color("avg_price:Q", title="Avg Price ($/gal)"),
    tooltip=[
        alt.Tooltip("year:O", title="Year"),
        alt.Tooltip("month_lbl:N", title="Month"),
        alt.Tooltip("avg_price:Q", title="Avg Price ($/gal)", format=".3f"),
    ],
).properties(height=340)

# Data labels (3 decimals)
heatmap_labels = alt.Chart(season).mark_text(baseline='middle', align='center').encode(
    x=alt.X("month_lbl:N", sort=MONTH_ORDER),
    y=alt.Y("year:O"),
    text=alt.Text("avg_price:Q", format=".3f")
)

st.altair_chart(heatmap + heatmap_labels, use_container_width=True)

# ---- Seasonality narrative ----
monthly_avg = (
    df_trend.assign(month=df_trend["date"].dt.strftime("%b"))
    .groupby("month", as_index=False)["gasoline_price"].mean()
)
monthly_avg["order"] = monthly_avg["month"].apply(lambda m: MONTH_ORDER.index(m))
monthly_avg = monthly_avg.sort_values("order")
hi = monthly_avg.loc[monthly_avg["gasoline_price"].idxmax()]
lo = monthly_avg.loc[monthly_avg["gasoline_price"].idxmin()]

st.markdown(
    f"""
**Recurring patterns:**  
- On average since selection start, the **highest months** for Houston are around **{hi['month']}** (~${hi['gasoline_price']:.2f}/gal).  
- The **lowest months** tend to be around **{lo['month']}** (~${lo['gasoline_price']:.2f}/gal).  
- Seasonality helps set expectations and compare current prices against typical monthly levels.
"""
)

st.markdown("---")

# =======================
# BAR CHART: Yearly Average Prices (Houston vs Benchmarks)
# =======================
st.subheader("Yearly Average Prices (Houston vs Benchmarks)")

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

year_bars = alt.Chart(yearly_long).mark_bar().encode(
    x=alt.X("year:O", title="Year"),
    y=alt.Y("avg_price:Q", title="Average Price ($/gal)"),
    color=alt.Color("series:N", title=None),
    tooltip=[
        alt.Tooltip("year:O", title="Year"),
        alt.Tooltip("series:N", title=""),
        alt.Tooltip("avg_price:Q", title="Avg Price ($/gal)", format=".3f"),
    ],
).properties(height=360)

# Labels on bars (3 decimals)
year_labels = alt.Chart(yearly_long).mark_text(dy=-6).encode(
    x=alt.X("year:O"),
    y=alt.Y("avg_price:Q"),
    detail="series:N",
    color=alt.value("black"),
    text=alt.Text("avg_price:Q", format=".3f")
)

st.altair_chart(year_bars + year_labels, use_container_width=True)

# ---- Yearly narrative ----
hou_year_max = yearly.loc[yearly["Houston"].idxmax()]
st.markdown(
    f"""
**Macro view by year:**  
- The highest annual average for Houston in this period was **{int(hou_year_max['year'])}** at **${hou_year_max['Houston']:.2f}/gal**.  
- Houston generally sits **below** the U.S. annual average and close to the Texas average.  
- Yearly aggregates smooth short-term spikes and are useful for budgeting and long-range planning.
"""
)

st.markdown("---")

# =======================
# FINAL LINE CHART: Houston Gasoline Price Change — MoM & YoY
# =======================
st.subheader("Houston Gasoline Price Change — MoM & YoY")
st.caption("Percent change; MoM uses prior month, YoY uses the same month last year.")

mom_yoy_long = (
    chg[["date", "mom_pct", "yoy_pct"]]
    .melt(id_vars=["date"], var_name="metric", value_name="pct")
    .dropna(subset=["pct"])
    .replace({"metric": {"mom_pct": "MoM %", "yoy_pct": "YoY %"}})
)

mom_yoy_chart = (
    alt.Chart(mom_yoy_long)
    .mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="Monthly Date", axis=alt.Axis(format="%Y-%m", labelAngle=-30)),
        y=alt.Y("pct:Q", title="Percent Change", axis=alt.Axis(format="%")),
        color=alt.Color("metric:N", title=None),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m"),
            alt.Tooltip("metric:N", title=""),
            alt.Tooltip("pct:Q", title="Change", format=".1%"),
        ],
    )
    .properties(height=360)
)
st.altair_chart(mom_yoy_chart, use_container_width=True)

# ---- Volatility & change narrative ----
mom_abs = chg.dropna(subset=["mom_pct"]).copy()
yoy_abs = chg.dropna(subset=["yoy_pct"]).copy()
if not mom_abs.empty and not yoy_abs.empty:
    mom_up = mom_abs.loc[mom_abs["mom_pct"].idxmax()]
    mom_dn = mom_abs.loc[mom_abs["mom_pct"].idxmin()]
    yoy_up = yoy_abs.loc[yoy_abs["yoy_pct"].idxmax()]
    yoy_dn = yoy_abs.loc[yoy_abs["yoy_pct"].idxmin()]

    st.markdown(
        f"""
**Where change was most significant:**  
- Largest monthly jump: **{pd.to_datetime(mom_up['date']).strftime('%b %Y')}** (**{mom_up['mom_pct']*100:+.1f}%**).  
- Largest monthly drop: **{pd.to_datetime(mom_dn['date']).strftime('%b %Y')}** (**{mom_dn['mom_pct']*100:+.1f}%**).  
- Biggest YoY increase: **{pd.to_datetime(yoy_up['date']).strftime('%b %Y')}** (**{yoy_up['yoy_pct']*100:+.1f}%**); biggest YoY decrease: **{pd.to_datetime(yoy_dn['date']).strftime('%b %Y')}** (**{yoy_dn['yoy_pct']*100:+.1f}%**).  
*These help identify periods of unusual volatility that may warrant deeper investigation (supply shocks, policy, refinery outages, etc.).*
"""
    )
