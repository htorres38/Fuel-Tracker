import streamlit as st
import pandas as pd

# --- Load CSV & get latest row ---
df = pd.read_csv("prices.csv", parse_dates=["date"]).sort_values("date", ascending=False)
latest = df.iloc[0]
latest_date = latest["date"].strftime("%B %Y")  # e.g., "September 2025")

# --- KPI row: Houston, Texas, U.S. ---
col1, col2, col3 = st.columns(3)

col1.metric(
    "📍 Latest Houston Price ($/gal)",
    f"${latest['gasoline_price']:.3f}",
    help=f"As of {latest_date}"
)

col2.metric(
    "📊 Latest Texas Avg ($/gal)",
    f"${latest['texas_avg']:.3f}",
    help=f"As of {latest_date}"
)

col3.metric(
    "🇺🇸 Latest U.S. Avg ($/gal)",
    f"${latest['national_avg']:.3f}",
    help=f"As of {latest_date}"
)
