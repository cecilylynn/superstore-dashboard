# Sales Dashboard

Interactive Streamlit dashboard for analyzing Sample Superstore data with drill-down capabilities.

## Quick Start

```bash
# Install dependencies
pip install streamlit pandas plotly openpyxl

# Run the dashboard
streamlit run app.py
```

Dashboard opens at `http://localhost:8501`.

## Features

- **Interactive Drill-Down** — Click any category to see sub-category breakdown
- **Dynamic Filtering** — Year, month, time range (YTD / Month Only), comparison mode (vs Goal / vs Prior Year)
- **KPI Cards** — Abbreviated currency ($260K) with exact values on hover
- **Dual-layer Charts** — Overlaid bars (actual vs comparison) + full-year reference lines in drill-down

## Project Structure

```
app.py               # Streamlit UI — layout, widgets, navigation
chart_builders.py     # Plotly figure construction (3 chart types)
data_processing.py    # All calculations and data loading
preview_charts.py     # Original prototype (standalone HTTP server)
```

**If you want to change a calculation**, edit `data_processing.py`.
**If you want to change how a chart looks**, edit `chart_builders.py`.
**If you want to change the page layout**, edit `app.py`.

## Data Files

Located in `../Datasources/` (not modified by the dashboard):

- `Sample - Superstore.xls` — 10,194 orders across 2020–2023
- `subcategory_monthly_goals.csv` — Generated sales goals (±10% variance from actuals)

## Color Scheme

| Color | Usage |
|-------|-------|
| Cornflower Blue (#6495ED) | Actual sales bars (selected months) |
| Pale Blue (#B0C4DE) | Actual sales bars (unselected months) |
| Light Gray (#D3D3D3) | Comparison bars (goal or prior year) |
| Dark Gray (#555555) | Full-year reference lines (drill-down only) |
| Green / Red | KPI percentage text only |
