# app.py
import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Fuel Price Dashboard", layout="wide")

# =======================
# LOAD DATA
# =======================
df = pd.read_csv("prices.csv", parse_dates=["date"])

# Sort both ways for convenience
df_desc = df.sort_values("date", ascending=False).reset_index(drop=True)
df_trend = df.sort_values("date", ascending=True).reset_index(drop=True)

# Latest row for KPIs
latest = df_desc.iloc[0]
latest_date = latest["date"].strftime("%B %Y")  # e.g., "August 2025"

# =======================
# HEADER
# =======================
st.title("Houston Gasoline Prices vs Texas & U.S. (2020–2025)")
st.caption("Monthly regular gasoline prices ($/gal), with benchmarks and change metrics.")

# =======================
# KPI ROW 1: Latest Prices  (match screenshot)
# =======================
c1, c2, c3 = st.columns(3)

c1.metric("Latest Houston Price ($/gal)", f"${latest['gasoline_price']:.3f}")
c1.caption(f"As of {latest_date}")

c2.metric("Latest Texas Price ($/gal)", f"${latest['texas_avg']:.3f}")
c2.caption(f"As of {latest_date}")

c3.metric("Latest U.S. National Price ($/gal)", f"${latest['national_avg']:.3f}")
c3.caption(f"As of {latest_date}")

st.markdown("---")

# =======================
# KPI ROW 2: Spreads
# =======================
spread_tx = latest["gasoline_price"] - latest["texas_avg"]
spread_us = latest["gasoline_price"] - latest["national_avg"]

s1, s2 = st.columns(2)
s1.metric("Spread: Houston − Texas ($/gal)", f"${spread_tx:+.3f}")
s1.caption(f"As of {latest_date}")

s2.metric("Spread: Houston − U.S. ($/gal)", f"${spread_us:+.3f}")
s2.caption(f"As of {latest_date}")

st.markdown("---")

# =======================
# KPI ROW 3: MoM % and YoY % (latest usable)
# =======================
# Compute MoM and YoY using shift (like SQL LAG)
chg = df_trend.copy()
chg["prev_m"] = chg["gasoline_price"].shift(1)
chg["prev_y"] = chg["gasoline_price"].shift(12)

# Divide-by-zero protection using NA (matches NULLIF behavior)
chg["mom_pct"] = (chg["gasoline_price"] - chg["prev_m"]) / chg["prev_m"].replace(0, pd.NA)
chg["yoy_pct"] = (chg["gasoline_price"] - chg["prev_y"]) / chg["prev_y"].replace(0, pd.NA)

# Take the latest non-null rows for each metric
mom_row = chg.dropna(subset=["mom_pct"]).iloc[-1]
yoy_row = chg.dropna(subset=["yoy_pct"]).iloc[-1]

mom_date = pd.to_datetime(mom_row["date"]).strftime("%B %Y")
yoy_date = pd.to_datetime(yoy_row["date"]).strftime("%B %Y")

k1, k2 = st.columns(2)
k1.metric("MoM % (Houston)", f"{mom_row['mom_pct']*100:+.1f}%")
k1.caption(f"As of {mom_date}")

k2.metric("YoY % (Houston)", f"{yoy_row['yoy_pct']*100:+.1f}%")
k2.caption(f"As of {yoy_date}")

st.markdown("---")

# =======================
# LINE CHART: Monthly Trends (2020–2025)
# =======================
st.subheader("Monthly Gasoline Price Trends (2020–2025)")

# Long form (UNION ALL equivalent)
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
    .mark_line()
    .encode(
        x=alt.X("date:T", title="Monthly Date", axis=alt.Axis(format="%Y-%m", labelAngle=-30)),
        y=alt.Y("price:Q", title="Gasoline Price (USD per Gallon)"),
        color=alt.Color("series:N", title="Series"),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m"),
            alt.Tooltip("series:N", title="Series"),
            alt.Tooltip("price:Q", title="Price ($/gal)", format=".3f"),
        ],
    )
    .properties(height=380)
)
st.altair_chart(trend_chart, use_container_width=True)

st.markdown("---")

# =======================
# LINE CHART: Houston Price Spreads vs Texas & U.S.
# =======================
st.subheader("Houston Price Spreads vs Texas & U.S.")

df_spread = df_trend.copy()
df_spread["Houston - Texas"] = df_spread["gasoline_price"] - df_spread["texas_avg"]
df_spread["Houston - U.S."] = df_spread["gasoline_price"] - df_spread["national_avg"]

spread_long = df_spread.melt(
    id_vars=["date"],
    value_vars=["Houston - Texas", "Houston - U.S."],
    var_name="spread",
    value_name="value"
).dropna(subset=["value"])

spread_chart = (
    alt.Chart(spread_long)
    .mark_line()
    .encode(
        x=alt.X("date:T", title="Monthly Date", axis=alt.Axis(format="%Y-%m", labelAngle=-30)),
        y=alt.Y("value:Q", title="Spread ($/gal)"),
        color=alt.Color("spread:N", title=""),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m"),
            alt.Tooltip("spread:N", title="Spread"),
            alt.Tooltip("value:Q", title="Value ($/gal)", format="+.3f"),
        ],
    )
    .properties(height=320)
)
st.altair_chart(spread_chart, use_container_width=True)

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

month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
season["month_lbl"] = pd.Categorical(season["month_lbl"], categories=month_order, ordered=True)
season = season.sort_values(["year", "month_num"])

heatmap = (
    alt.Chart(season)
    .mark_rect()
    .encode(
        x=alt.X("month_lbl:N", title="Month", sort=month_order),
        y=alt.Y("year:O", title="Year"),
        color=alt.Color("avg_price:Q", title="Avg Price ($/gal)"),
        tooltip=[
            alt.Tooltip("year:O", title="Year"),
            alt.Tooltip("month_lbl:N", title="Month"),
            alt.Tooltip("avg_price:Q", title="Avg Price ($/gal)", format=".3f"),
        ],
    )
    .properties(height=340)
)
st.altair_chart(heatmap, use_container_width=True)

st.markdown("---")

# =======================
# BAR CHART: Yearly Average Prices (Houston vs Benchmarks)
# =======================
st.subheader("Yearly Average Prices (Houston vs Benchmarks)")

# Compute yearly averages (SQL yrs CTE equivalent)
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

# Long format for clustered bars
yearly_long = yearly.melt(
    id_vars=["year"],
    var_name="series",
    value_name="avg_price"
)

year_bar = (
    alt.Chart(yearly_long)
    .mark_bar()
    .encode(
        x=alt.X("year:O", title="Year"),
        y=alt.Y("avg_price:Q", title="Average Price ($/gal)"),
        color=alt.Color("series:N", title="Series"),
        tooltip=[
            alt.Tooltip("year:O", title="Year"),
            alt.Tooltip("series:N", title="Series"),
            alt.Tooltip("avg_price:Q", title="Avg Price ($/gal)", format=".3f"),
        ],
    )
    .properties(height=360)
)
st.altair_chart(year_bar, use_container_width=True)

st.markdown("---")

# =======================
# FINAL LINE CHART: Houston Gasoline Price Change — MoM & YoY
# =======================
st.subheader("Houston Gasoline Price Change — MoM & YoY")
st.caption("Percent change; MoM uses prior month, YoY uses the same month last year.")

# Use the already computed 'chg' dataframe (has mom_pct & yoy_pct)
mom_yoy_long = (
    chg[["date", "mom_pct", "yoy_pct"]]
    .melt(id_vars=["date"], var_name="metric", value_name="pct")
    .dropna(subset=["pct"])
    .replace({"metric": {"mom_pct": "MoM %", "yoy_pct": "YoY %"}})
)

mom_yoy_chart = (
    alt.Chart(mom_yoy_long)
    .mark_line()
    .encode(
        x=alt.X("date:T", title="Monthly Date", axis=alt.Axis(format="%Y-%m", labelAngle=-30)),
        y=alt.Y("pct:Q", title="Percent Change", axis=alt.Axis(format="%")),
        color=alt.Color("metric:N", title="Metric"),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m"),
            alt.Tooltip("metric:N", title="Metric"),
            alt.Tooltip("pct:Q", title="Change", format=".1%")
        ],
    )
    .properties(height=360)
)
st.altair_chart(mom_yoy_chart, use_container_width=True)
