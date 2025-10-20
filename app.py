import streamlit as st
import pandas as pd

# --- Load CSV ---
df = pd.read_csv("prices.csv", parse_dates=["date"])

# --- Sort by most recent date ---
df = df.sort_values("date", ascending=False)

# --- Grab the latest row ---
latest_record = df.iloc[0]
latest_date = latest_record["date"].strftime("%B %Y")  # Example: "August 2025"

# --- Display KPI Cards ---
col1, col2, col3 = st.columns(3)

col1.metric(
    "📍 Latest Houston Price ($/gal)",
    f"${latest_record['gasoline_price']:.3f}"
)
col1.caption(f"As of {latest_date}")

col2.metric(
    "📊 Latest Texas Avg ($/gal)",
    f"${latest_record['texas_avg']:.3f}"
)
col2.caption(f"As of {latest_date}")

col3.metric(
    "🇺🇸 Latest U.S. Avg ($/gal)",
    f"${latest_record['national_avg']:.3f}"
)
col3.caption(f"As of {latest_date}")
