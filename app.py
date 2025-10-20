import streamlit as st
import pandas as pd

st.set_page_config(page_title="Fuel Price Dashboard", layout="wide")

# --- Load CSV ---
df = pd.read_csv("prices.csv", parse_dates=["date"])

# --- Sort newest first & grab latest row ---
df = df.sort_values("date", ascending=False).reset_index(drop=True)
latest = df.iloc[0]
latest_date = latest["date"].strftime("%B %Y")  # e.g., "August 2025"

# --- First row: Latest price KPIs ---
c1, c2, c3 = st.columns(3)

c1.metric("📍 Latest Houston Price ($/gal)", f"${latest['gasoline_price']:.3f}")
c1.caption(f"As of {latest_date}")

c2.metric("📊 Latest Texas Avg ($/gal)", f"${latest['texas_avg']:.3f}")
c2.caption(f"As of {latest_date}")

c3.metric("🇺🇸 Latest U.S. Avg ($/gal)", f"${latest['national_avg']:.3f}")
c3.caption(f"As of {latest_date}")

st.markdown("---")

# --- Second row: Spread KPIs ---
spread_tx = latest["gasoline_price"] - latest["texas_avg"]
spread_us = latest["gasoline_price"] - latest["national_avg"]

s1, s2 = st.columns(2)

s1.metric("➖ Spread: Houston − Texas ($/gal)", f"${spread_tx:+.3f}")
s1.caption(f"As of {latest_date}")

s2.metric("➖ Spread: Houston − U.S. ($/gal)", f"${spread_us:+.3f}")
s2.caption(f"As of {latest_date}")

