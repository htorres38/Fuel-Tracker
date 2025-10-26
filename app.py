# app.py
import streamlit as st
import pandas as pd
import altair as alt
import numpy as np

st.set_page_config(page_title="Fuel Price Dashboard", layout="wide")

# =======================
# LOAD DATA
# =======================
@st.cache_data
def load_data():
    df = pd.read_csv("prices.csv", parse_dates=["date"])
    df.columns = [c.strip() for c in df.columns]
    return df

df = load_data()

# =======================
# BASIC FILTERS (Year & Month)
# =======================
st.sidebar.header("Filters")

years = sorted(df["date"].dt.year.unique().tolist())
min_y, max_y = min(years), max(years)
yr_min, yr_max = st.sidebar.select_slider(
    "Year range",
    options=years,
    value=(min_y, max_y),
)

month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
month_map = {i+1: m for i, m in enumerate(month_order)}
months_selected = st.sidebar.multiselect(
    "Months",
    options=list(range(1,13)),
    default=list(range(1,13)),
    format_func=lambda m: month_map[m]
)

# Apply filters
mask = (
    (df["date"].dt.year >= yr_min) & (df["date"].dt.year <= yr_max) &
    (df["date"].dt.month.isin(months_selected))
)
df_f = df.loc[mask].copy().sort_values("date")
if df_f.empty:
    st.warning("No data in the selected filters.")
    st.stop()

# Convenience views
df_desc = df_f.sort_values("date", ascending=False).reset_index(drop=True)
df_trend = df_f.sort_values("date", ascending=True).reset_index(drop=True)

# =======================
# HELPERS
# =======================
def pct_change(new, old):
    if old is None or pd.isna(old) or old == 0:
        return None
    return (new - old) / old

def fmt_pct(x):
    return f"{x*100:+.1f}%" if x is not None and not pd.isna(x) else "n/a"

def slope_last_n(series, n=3):
    s = series.dropna().tail(n)
    if len(s) < 2:
        return np.nan
    x = np.arange(len(s))
    return np.polyfit(x, s.values, 1)[0]

def trend_word(s):
    if pd.isna(s):
        return "n/a"
    return "widening" if s > 0 else "narrowing" if s < 0 else "flat"

# =======================
# HEADER
# =======================
st.title("Houston Gasoline Prices vs Texas & U.S. (2020–2025)")
st.caption("Monthly regular gasoline prices ($/gal). Use the sidebar to filter by year and month.")

# =======================
# KPI ROW 1: Latest Prices
# =======================
latest = df_desc.iloc[0]
latest_date = latest["date"].strftime("%B %Y")

c1, c2, c3 = st.columns(3)
c1.metric("Latest Houston Price ($/gal)", f"${latest['gasoline_price']:.3f}")
c1.caption(f"As of {latest_date}")

c2.metric("Latest Texas Price ($/gal)", f"${latest['texas_avg']:.3f}")
c2.caption(f"As of {latest_date}")

c3.metric("Latest U.S. National Price ($/gal)", f"${latest['national_avg']:.3f}")
c3.caption(f"As of {latest_date}")

# KPI narrative
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
- Month-over-month change for Houston: **{fmt_pct(hou_mom)}**; year-over-year: **{fmt_pct(hou_yoy)}** (positive = increase).
"""
)

st.markdown("---")

# =======================
# LINE: Monthly Price Trends
# =======================
st.subheader("Monthly Gasoline Price Trends")

name_map = {
    "gasoline_price": "Houston",
    "texas_avg": "Texas Statewide",
    "national_avg": "U.S. National",
}
df_long = df_trend.melt(
    id_vars=["date"],
    value_vars=["gasoline_price", "texas_avg", "national_avg"],
    var_name="series",
    value_name="price"
)
df_long["series"] = df_long["series"].map(name_map)

trend_chart = (
    alt.Chart(df_long)
    .mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(format="%Y-%m", labelAngle=-30)),
        y=alt.Y("price:Q", title="Price (\\$/gal)"),
        color=alt.Color("series:N", title=None),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m"),
            alt.Tooltip("series:N", title=""),
            alt.Tooltip("price:Q", title="Price (\\$/gal)", format=".3f"),
        ],
    )
    .properties(height=360)
)
st.altair_chart(trend_chart, use_container_width=True)

# Trend narrative (peak/trough)
peak_row = df_trend.loc[df_trend["gasoline_price"].idxmax()]
min_row  = df_trend.loc[df_trend["gasoline_price"].idxmin()]
st.markdown(
    f"""
**How prices evolved:**  
- Local peak: **{pd.to_datetime(peak_row['date']).strftime('%B %Y')}** at **\\${peak_row['gasoline_price']:.3f}/gal**.  
- Local trough: **{pd.to_datetime(min_row['date']).strftime('%B %Y')}** at **\\${min_row['gasoline_price']:.3f}/gal**.
"""
)

st.markdown("---")

# =======================
# LINE: Spreads vs Benchmarks
# =======================
st.subheader("Houston Price Spreads vs Texas & U.S.")

df_spread = df_trend.copy()
df_spread["Houston - Texas"] = df_spread["gasoline_price"] - df_spread["texas_avg"]
df_spread["Houston - U.S."]  = df_spread["gasoline_price"] - df_trend["national_avg"]

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
        x=alt.X("date:T", title="Date", axis=alt.Axis(format="%Y-%m", labelAngle=-30)),
        y=alt.Y("value:Q", title="Spread (\\$/gal)"),
        color=alt.Color("spread:N", title=None),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m"),
            alt.Tooltip("spread:N", title=""),
            alt.Tooltip("value:Q", title="Value (\\$/gal)", format="+.3f"),
        ],
    )
    .properties(height=300)
)
st.altair_chart(spread_chart, use_container_width=True)

# Spread narrative
slope_tx = slope_last_n(df_spread["Houston - Texas"], 3)
slope_us = slope_last_n(df_spread["Houston - U.S."], 3)
spread_tx_latest = float(df_spread["Houston - Texas"].iloc[-1])
spread_us_latest = float(df_spread["Houston - U.S."].iloc[-1])
st.markdown(
    f"""
**How to read spreads:**  
- Positive spread = **Houston above** the benchmark; negative = **below**.  
- Latest spreads: **Houston–Texas {spread_tx_latest:+.3f} \\$/gal**, **Houston–U.S. {spread_us_latest:+.3f} \\$/gal**.  
- Recent trend (last ~3 months): vs Texas **{trend_word(slope_tx)}**, vs U.S. **{trend_word(slope_us)}**.
"""
)

st.markdown("---")

# =======================
# YEARLY AVERAGES — GROUPED BARS
# =======================
st.subheader("Yearly Average Prices (Grouped)")

yearly = (
    df_trend.assign(year=df_trend["date"].dt.year)
    .groupby("year", as_index=False)
    .agg(
        Houston=("gasoline_price", "mean"),
        **{"Texas Statewide": ("texas_avg", "mean")},
        **{"U.S. National": ("national_avg", "mean")},
        n_months=("gasoline_price", "size")
    )
)

# Melt for plotting
yearly_long = yearly.melt(
    id_vars=["year", "n_months"],
    value_vars=["Houston", "Texas Statewide", "U.S. National"],
    var_name="series",
    value_name="avg_price"
)

# Grouped bars via xOffset (Altair/Vega-Lite 5+)
bars = (
    alt.Chart(yearly_long)
    .mark_bar()
    .encode(
        x=alt.X("year:O", title="Year"),
        xOffset=alt.X("series:N", title=None),
        y=alt.Y("avg_price:Q", title="Avg Price (\\$/gal)"),
        color=alt.Color("series:N", title=None),
        tooltip=[
            alt.Tooltip("year:O", title="Year"),
            alt.Tooltip("series:N", title=""),
            alt.Tooltip("avg_price:Q", title="Avg (\\$/gal)", format=".3f"),
            alt.Tooltip("n_months:Q", title="Months"),
        ],
    )
    .properties(height=320)
)

# Clean labels above each bar
labels = (
    alt.Chart(yearly_long)
    .mark_text(dy=-6, color="black")
    .encode(
        x=alt.X("year:O"),
        xOffset=alt.X("series:N"),
        y=alt.Y("avg_price:Q"),
        detail="series:N",
        text=alt.Text("avg_price:Q", format=".2f")
    )
)

st.altair_chart(bars + labels, use_container_width=True)

# Narrative (complete years only)
yearly_complete = yearly[yearly["n_months"] == 12]
if not yearly_complete.empty:
    hou_year_max = yearly_complete.loc[yearly_complete["Houston"].idxmax()]
    st.markdown(
        f"""
**Macro view by year:**  
- Highest full-year Houston average: **{int(hou_year_max['year'])}** at **\\${hou_year_max['Houston']:.2f}/gal**.
"""
    )

st.markdown("---")

# =======================
# LINE: MoM & YoY %
# =======================
st.subheader("Houston Gasoline Price Change — MoM & YoY")
st.caption("MoM uses prior month; YoY uses the same month last year.")

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

mom_yoy_chart = (
    alt.Chart(mom_yoy_long)
    .mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(format="%Y-%m", labelAngle=-30)),
        y=alt.Y("pct:Q", title="Percent Change", axis=alt.Axis(format="%")),
        color=alt.Color("metric:N", title=None),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m"),
            alt.Tooltip("metric:N", title=""),
            alt.Tooltip("pct:Q", title="Change", format=".1%"),
        ],
    )
    .properties(height=320)
)
st.altair_chart(mom_yoy_chart, use_container_width=True)
