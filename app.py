# app.py
import streamlit as st
import pandas as pd
import altair as alt

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Fuel Price Dashboard • Houston vs Texas & U.S.",
    page_icon="⛽",
    layout="wide"
)

# ---------- LOAD DATA ----------
@st.cache_data
def load_data(csv_path: str = "prices.csv") -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    # enforce expected schema
    expected_cols = {"date","city","gasoline_price","texas_avg","national_avg"}
    missing = expected_cols - set(df.columns)
    if missing:
        st.error(f"CSV is missing columns: {sorted(missing)}")
        st.stop()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    # helper features
    df["houston_vs_tx"] = df["gasoline_price"] - df["texas_avg"]
    df["houston_vs_us"] = df["gasoline_price"] - df["national_avg"]
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.strftime("%b")
    df["year_month"] = df["date"].dt.strftime("%Y-%m")
    return df

df = load_data()

# ---------- HEADER ----------
st.title("⛽ Fuel Price Dashboard — Houston vs Texas & U.S. (2020–2025)")
st.caption(
    "Interactive dashboard of monthly regular gasoline prices (USD per gallon). "
    "Compare **Houston** to **Texas statewide** and **U.S. national** benchmarks; explore spreads, seasonality, and yearly averages."
)

# ---------- SIDEBAR FILTERS ----------
with st.sidebar:
    st.header("Filters")
    y_min, y_max = int(df["year"].min()), int(df["year"].max())
    year_range = st.slider("Year range", y_min, y_max, (y_min, y_max), step=1)

    show_raw = st.checkbox("Show raw data (below)", value=False)

    st.markdown("---")
    st.markdown("**Notes**")
    st.caption(
        "• Prices are in **$/gal**\n"
        "• City = Houston\n"
        "• Benchmarks: Texas & U.S. averages"
    )

# apply sidebar year filter for charts that honor it
df_f = df.query("@year_range[0] <= year <= @year_range[1]").copy()

# ---------- KPI ROW ----------
latest_row = df.iloc[-1]  # always latest overall (not filtered)
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Latest Houston", f"${latest_row['gasoline_price']:.3f}/gal")
c2.metric("Latest Texas Avg", f"${latest_row['texas_avg']:.3f}/gal")
c3.metric("Latest U.S. Avg", f"${latest_row['national_avg']:.3f}/gal")
c4.metric("Spread: Houston − Texas", f"{latest_row['houston_vs_tx']:+.3f}")
c5.metric("Spread: Houston − U.S.", f"{latest_row['houston_vs_us']:+.3f}")

st.markdown("---")

# ---------- FULL-PERIOD TREND (unfiltered for full context) ----------
st.subheader("📉 Monthly Price Trends (Full Period)")
long_all = df.melt(
    id_vars=["date"],
    value_vars=["gasoline_price", "texas_avg", "national_avg"],
    var_name="series",
    value_name="price"
)
name_map = {
    "gasoline_price": "Houston Average Price",
    "texas_avg": "Texas Statewide Average",
    "national_avg": "U.S. National Average",
}
long_all["series"] = long_all["series"].map(name_map)

trend_all = (
    alt.Chart(long_all)
    .mark_line()
    .encode(
        x=alt.X("date:T", title="Date (Monthly)"),
        y=alt.Y("price:Q", title="Price ($/gal)"),
        color=alt.Color("series:N", title="Series"),
        tooltip=[
            alt.Tooltip("date:T", title="Date"),
            alt.Tooltip("series:N", title="Series"),
            alt.Tooltip("price:Q", title="Price", format=".3f"),
        ],
    )
    .properties(height=340)
)
st.altair_chart(trend_all, use_container_width=True)

# ---------- FILTERED YEAR TREND (respects sidebar range) ----------
st.subheader("📆 Trend within Selected Year Range")
long_f = df_f.melt(
    id_vars=["date"],
    value_vars=["gasoline_price", "texas_avg", "national_avg"],
    var_name="series",
    value_name="price"
)
long_f["series"] = long_f["series"].map(name_map)

trend_filtered = (
    alt.Chart(long_f)
    .mark_line()
    .encode(
        x=alt.X("date:T", title="Date (Monthly)"),
        y=alt.Y("price:Q", title="Price ($/gal)"),
        color=alt.Color("series:N", title="Series"),
        tooltip=[
            alt.Tooltip("date:T", title="Date"),
            alt.Tooltip("series:N", title="Series"),
            alt.Tooltip("price:Q", title="Price", format=".3f"),
        ],
    )
    .properties(height=300)
)
st.altair_chart(trend_filtered, use_container_width=True)

# ---------- SPREADS ----------
st.subheader("➖ Price Spreads — Houston minus Benchmarks (Selected Range)")
spread_long = df_f.melt(
    id_vars=["date"],
    value_vars=["houston_vs_tx", "houston_vs_us"],
    var_name="spread",
    value_name="value"
)
spread_long["spread"] = spread_long["spread"].map({
    "houston_vs_tx": "Houston − Texas",
    "houston_vs_us": "Houston − U.S."
})

spreads_chart = (
    alt.Chart(spread_long)
    .mark_line()
    .encode(
        x=alt.X("date:T", title="Date (Monthly)"),
        y=alt.Y("value:Q", title="Spread ($/gal)"),
        color=alt.Color("spread:N", title="Spread"),
        tooltip=[
            alt.Tooltip("date:T", title="Date"),
            alt.Tooltip("spread:N", title="Spread"),
            alt.Tooltip("value:Q", title="Value", format="+.3f"),
        ],
    )
    .properties(height=260)
)
st.altair_chart(spreads_chart, use_container_width=True)

# ---------- YEARLY AVERAGES ----------
st.subheader("📊 Yearly Average Prices (Selected Range)")
yearly_avg = (
    df_f.groupby("year")[["gasoline_price", "texas_avg", "national_avg"]]
    .mean()
    .reset_index()
    .melt(id_vars=["year"], var_name="series", value_name="avg_price")
)
yearly_avg["series"] = yearly_avg["series"].map(name_map)

year_bar = (
    alt.Chart(yearly_avg)
    .mark_bar()
    .encode(
        x=alt.X("year:O", title="Year"),
        y=alt.Y("avg_price:Q", title="Average Price ($/gal)"),
        color=alt.Color("series:N", title="Series"),
        tooltip=[
            alt.Tooltip("year:O", title="Year"),
            alt.Tooltip("series:N", title="Series"),
            alt.Tooltip("avg_price:Q", title="Avg Price", format=".3f"),
        ],
    )
    .properties(height=300)
)
st.altair_chart(year_bar, use_container_width=True)

# ---------- SEASONALITY ----------
st.subheader("📅 Seasonality — Average by Calendar Month (Houston, Selected Range)")
month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
season = (
    df_f.groupby("month", as_index=False)["gasoline_price"].mean()
    .assign(month_cat=lambda d: pd.Categorical(d["month"], categories=month_order, ordered=True))
    .sort_values("month_cat")
)

season_chart = (
    alt.Chart(season)
    .mark_bar()
    .encode(
        x=alt.X("month_cat:N", title="Month"),
        y=alt.Y("gasoline_price:Q", title="Avg Price ($/gal)"),
        tooltip=[
            alt.Tooltip("month_cat:N", title="Month"),
            alt.Tooltip("gasoline_price:Q", title="Avg", format=".3f"),
        ],
    )
    .properties(height=240)
)
st.altair_chart(season_chart, use_container_width=True)

# ---------- DOWNLOADS & RAW ----------
st.markdown("---")
c_dl1, c_dl2 = st.columns([1,1])

with c_dl1:
    st.subheader("⬇️ Download (Selected Range)")
    csv_filtered = df_f.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered data (CSV)",
        data=csv_filtered,
        file_name="fuel_prices_filtered.csv",
        mime="text/csv"
    )

with c_dl2:
    st.subheader("⬇️ Download (Full Dataset)")
    csv_full = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download full data (CSV)",
        data=csv_full,
        file_name="fuel_prices_full.csv",
        mime="text/csv"
    )

if show_raw:
    st.markdown("---")
    st.subheader("🔎 Raw Data Preview")
    st.dataframe(
        df[[
            "date","city","gasoline_price","texas_avg","national_avg",
            "houston_vs_tx","houston_vs_us","year","month","year_month"
        ]],
        use_container_width=True
    )
