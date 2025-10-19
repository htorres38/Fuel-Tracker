import streamlit as st
import pandas as pd

# ---- Page Settings ----
st.set_page_config(page_title="Fuel Price Dashboard", layout="wide")

# ---- Load Data ----
@st.cache_data
def load_data():
    df = pd.read_csv("prices.csv", parse_dates=["date"])
    return df

df = load_data()

# ---- Title & Intro ----
st.title("⛽ Fuel Price Dashboard (Houston vs Texas vs National)")
st.markdown("""
Explore monthly regular gasoline prices from **2020 to 2025**  
- 📍 **City:** Houston  
- 📊 **Comparison:** Texas Average vs National Average  
- 📅 Updated Monthly
""")

# ---- Show Raw Data ----
if st.checkbox("Show Raw Data"):
    st.dataframe(df)
