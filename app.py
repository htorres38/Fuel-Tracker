import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Fuel Price Dashboard", layout="wide")

# --- Load CSV ---
df = pd.read_csv("prices.csv", parse_dates=["date"])

# --- Sort newest first & grab latest row for KPIs ---
df = df.sort_values("date", ascending=False).reset_index(drop=True)
latest = df.iloc[0]
latest_date = latest["date"].strftime("%B %Y")  # e.g., "August 2025"

# =======================
# KPI ROW 1: Latest Prices
# =======================
c1, c2, c3 = st.columns(3)

c1.metric("📍 Latest Houston Price ($/gal)", f"${latest['gasoline_price']:.3f}")
c1.caption(f"As of {latest_date}")

c2.metric("📊 Latest Texas Avg ($/gal)", f"${latest['texas_avg']:.3f}")
c2.caption(f"As of {latest_date}")

c3.metric("🇺🇸 Latest U.S. Avg ($/gal)", f"${latest['national_avg']:.3f}")
c3.caption(f"As of {latest_date}")

st.markdown("---")

# =======================
# KPI ROW 2: Spreads
# =======================
spread_tx = latest["gasoline_price"] - latest["texas_avg"]
spread_us = latest["gasoline_price"] - latest["national_avg"]

s1, s2 = st.columns(2)

s1.metric("➖ Spread: Houston − Texas ($/gal)", f"${spread_tx:+.3f}")
s1.caption(f"As of {latest_date}")

s2.metric("➖ Spread: Houston − U.S. ($/gal)", f"${spread_us:+.3f}")
s2.caption(f"As of {latest_date}")

st.markdown("---")

# =======================
# LINE CHART: Monthly Trends (2020–2025)
# =======================
st.subheader("Monthly Gasoline Price Trends (2020 - 2025)")

# Prepare long (UNION ALL equivalent)
df_long = (
    df.sort_values("date", ascending=True)
      .melt(
          id_vars=["date"],
          value_vars=["gasoline_price", "texas_avg", "national_avg"],
          var_name="series",
          value_name="price"
      )
)

# Map series names to match your SQL labels
name_map = {
    "gasoline_price": "Houston",
    "texas_avg": "Texas Statewide",
    "national_avg": "U.S. National",
}
df_long["series"] = df_long["series"].map(name_map)

# Build the Altair line chart
trend_chart = (
    alt.Chart(df_long)
    .mark_line()
    .encode(
        x=alt.X("date:T",
                title="Monthly Date",
                axis=alt.Axis(format="%Y-%m", labelAngle=-30)),  # shows 2020-01 style
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
