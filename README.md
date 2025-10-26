# Fuel-Tracker# Fuel Price Dashboard

A small Streamlit app that shows monthly **Houston** gasoline prices next to the **Texas** and **U.S.** averages. It highlights the latest numbers, how Houston compares (spreads), seasonal patterns, yearly averages, and month-over-month / year-over-year changes.

---

## What the app does

- **Loads one CSV** (`prices.csv`) with monthly data.
- **KPIs (cards)**
  - Latest Houston price
  - Latest Texas average
  - Latest U.S. average
  - Two spreads shown as metrics later (Houston−Texas, Houston−U.S.)
- **Charts**
  - Line: Monthly price trends (Houston vs Texas vs U.S.)
  - Line: Spreads (Houston−Texas, Houston−U.S.)
  - Heatmap: Average Houston price by Month × Year
  - Bar: Yearly average prices (Houston vs Texas vs U.S.)
  - Line: % change for Houston (MoM and YoY)

The code keeps two sorted copies of the data:
- `df_desc` (descending by date) for “latest” metrics
- `df_trend` (ascending by date) for time-based charts and calculations
