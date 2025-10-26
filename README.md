# Fuel-Tracker Dashboard

A Streamlit application that visualizes monthly **Houston gasoline prices** compared to the **Texas** and **U.S.** averages.  
The dashboard highlights the most recent values, price differences (spreads), seasonal patterns, yearly averages, and both month-over-month (MoM) and year-over-year (YoY) changes.

View the live app here: **[https://houston-fuel-tracker-dashboard.streamlit.app](https://houston-fuel-tracker-dashboard.streamlit.app)**

---

## Overview

Fuel-Tracker is designed to give a clear, data-driven view of gasoline price trends over time.  
It’s built with a focus on readability, lightweight computation, and easily interpretable visuals.

---

## What the App Does

### Data Loading
- Loads a single CSV file named `prices.csv` containing monthly data.
- Expects the following columns:
  - `date`
  - `gasoline_price`
  - `texas_avg`
  - `national_avg`

---

### Key Performance Indicators (KPIs)
The dashboard begins with a concise set of metrics summarizing the most current data:
- Latest **Houston** gasoline price.
- Latest **Texas** statewide average.
- Latest **U.S.** national average.
- Two additional **spread metrics**:
  - Houston − Texas
  - Houston − U.S.

---

### Visualizations
The following charts provide deeper insight into trends and relationships:

| Chart Type | Description |
|-------------|--------------|
| **Line – Monthly Trends** | Tracks monthly gasoline prices for Houston, Texas, and the U.S. side-by-side. |
| **Line – Spreads** | Visualizes price differences between Houston and both benchmarks. |
| **Heatmap – Seasonality** | Displays average Houston prices by month and year to reveal recurring seasonal patterns. |
| **Bar – Yearly Averages** | Shows annual mean prices for Houston, Texas, and U.S. |
| **Line – MoM & YoY %** | Plots Houston’s monthly and yearly percentage changes. |

Each chart includes tooltips and labeled axes for clarity.

---

### Data Handling
To streamline analysis:
- `df_desc` sorts data in **descending order** by date for the “latest” metrics.
- `df_trend` sorts data in **ascending order** for charts and rate calculations.

Core calculations include:
- **MoM % Change:** `(current_month − previous_month) / previous_month`
- **YoY % Change:** `(current_month − same_month_last_year) / same_month_last_year`
- **Spreads:** Difference between Houston and each benchmark.

---

## Technical Details

**Frameworks & Libraries**
- Streamlit — user interface and layout.
- Pandas — data processing and cleaning.
- Altair — interactive data visualization.
- NumPy — numerical operations and linear fits for recent spread trends.
