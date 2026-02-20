"""
app.py — Streamlit Dashboard UI

This is the main entry point for the dashboard.  Run it with:
    streamlit run app.py

This file handles ONLY the user interface:
  - Sidebar controls (Year, Month, Time Range, Comparison Mode)
  - Page layout (columns, rows, spacing)
  - Rendering charts built by chart_builders.py
  - Navigation between Overview and Drill-Down views

NO calculations live here.  If you need to change how a number is computed,
look in data_processing.py.  If you need to change how a chart looks,
look in chart_builders.py.

Architecture:
  data_processing.py  →  crunches the numbers
  chart_builders.py   →  draws the pictures
  app.py              →  wires the UI together  (this file)
"""

import streamlit as st

# Our two helper modules:
#   data_processing  — loads data and computes every number
#   chart_builders   — takes numbers and draws Plotly charts
import data_processing as dp
import chart_builders as cb


# ═════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ═════════════════════════════════════════════════════════════════════════════
# This MUST be the very first Streamlit command in the script.
# layout="wide" tells Streamlit to use the full browser width instead of
# a narrow centered column.  This gives us room for side-by-side charts.
st.set_page_config(
    page_title="Sales Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",   # Sidebar starts open
)


# ═════════════════════════════════════════════════════════════════════════════
#  CUSTOM CSS
# ═════════════════════════════════════════════════════════════════════════════
# Streamlit lets us inject raw CSS with st.markdown(unsafe_allow_html=True).
# We use this to:
#   1. Add card-like styling (white background, rounded corners, shadow)
#   2. Control spacing between elements
#   3. Make the layout tighter than Streamlit's generous defaults
#
# The .card class wraps each chart/KPI in a white box with a subtle shadow.
# The .stPlotlyChart CSS removes extra padding Streamlit adds around charts.
st.markdown("""
<style>
    /* Reduce Streamlit's default top padding on the main content area */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    /* Card wrapper: white box with rounded corners and a subtle shadow */
    .card {
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        padding: 0px;
        overflow: hidden;
    }
    /* Remove extra bottom margin Streamlit adds to each element */
    .element-container {
        margin-bottom: 0px !important;
    }
    /* Tighten up Plotly chart containers */
    .stPlotlyChart {
        margin-bottom: -10px;
    }
</style>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
#  DATA LOADING (cached)
# ═════════════════════════════════════════════════════════════════════════════
# @st.cache_data tells Streamlit: "Run this function once, store the result,
# and reuse it every time the page reruns."  This is crucial because Streamlit
# reruns the ENTIRE script from top to bottom every time you interact with
# any widget (change a dropdown, click a button, etc.).
#
# Without caching, we'd reload the Excel file on every single interaction,
# which would be slow.  With caching, it loads once and stays in memory.
@st.cache_data
def load_data():
    """Load and cache the two data sources (orders + goals)."""
    return dp.load_data()

# Actually call the function.  On the first run this reads the files;
# on subsequent reruns it returns the cached result instantly.
orders, goals = load_data()


# ═════════════════════════════════════════════════════════════════════════════
#  SIDEBAR CONTROLS
# ═════════════════════════════════════════════════════════════════════════════
# The sidebar is the narrow panel on the left side of the page.
# All our filter controls live here.
#
# IMPORTANT: Every time a user changes any widget, Streamlit reruns the
# entire script from top to bottom.  That's how Streamlit works — there's
# no explicit "onChange" handler.  The widgets just return their current
# value, and the rest of the script uses that value.

with st.sidebar:
    st.markdown("### ⚙ Settings")

    # ── Year selector ────────────────────────────────────────────
    # The Superstore dataset spans 2020–2023.
    # index=3 makes 2023 the default selection (0-indexed: 2020=0, 2021=1, 2022=2, 2023=3).
    selected_year = st.selectbox(
        "Year",
        options=[2020, 2021, 2022, 2023],
        index=3,   # Default to 2023
    )

    # ── Month selector ───────────────────────────────────────────
    # Shows full month names (January, February, ...) but we need the
    # month NUMBER (1–12) for our calculations.  So we use the index
    # of the selected option + 1.
    month_options = list(dp.MONTH_MAP.keys())   # ['January', 'February', ..., 'December']
    selected_month_name = st.selectbox(
        "Through Month",
        options=month_options,
        index=11,   # Default to December (0-indexed, so 11 = December)
    )
    # Convert the full month name to a number (e.g. "June" → 6)
    selected_month = dp.MONTH_MAP[selected_month_name]

    st.divider()   # Visual horizontal line to separate groups

    # ── Time Range toggle ────────────────────────────────────────
    # "Year-to-Date" = show cumulative data from January through the selected month.
    # "Month Only" = show data for just the one selected month.
    #
    # st.radio returns the exact string the user selected.
    time_range = st.radio(
        "Time Range",
        options=["YTD", "Month Only"],
        index=0,   # Default to YTD
    )

    st.divider()

    # ── Comparison Mode toggle ───────────────────────────────────
    # "vs Goal" = compare actual sales to the sales goal we generated.
    # "vs Prior Year" = compare to the same period last year.
    comparison_mode = st.radio(
        "Compare To",
        options=["vs Goal", "vs Prior Year"],
        index=0,   # Default to vs Goal
    )


# ═════════════════════════════════════════════════════════════════════════════
#  SESSION STATE: DRILL-DOWN NAVIGATION
# ═════════════════════════════════════════════════════════════════════════════
# Streamlit's "session state" is like a dictionary that persists across
# reruns within the same browser session.  We use it to remember which
# category the user has drilled into (or None if they're on the overview).
#
# When the user clicks a "Drill Down" button, we set the category name
# in session state and call st.rerun() to reload the page in drill-down mode.
# When they click "Back to Overview", we clear it and rerun.

if 'selected_category' not in st.session_state:
    st.session_state.selected_category = None   # Start in overview mode


# ═════════════════════════════════════════════════════════════════════════════
#  DERIVED VALUES
# ═════════════════════════════════════════════════════════════════════════════
# These values are computed from the sidebar selections and used by multiple
# parts of the page.  We compute them once here to avoid repeating the logic.

# Which months are "selected" (used for bar coloring)?
# In YTD mode: months 1 through the selected month are "active" (blue).
# In Month Only mode: just the one selected month is "active" (blue).
if time_range == 'YTD':
    selected_months = list(range(1, selected_month + 1))   # e.g. [1, 2, 3, 4, 5, 6] for June YTD
else:
    selected_months = [selected_month]                      # e.g. [6] for June only

# Bar colors for the monthly chart: blue for active months, pale blue for others.
# This creates a list of 12 color strings, one per month.
bar_colors = [
    cb.BLUE if m in selected_months else cb.PALE_BLUE
    for m in range(1, 13)
]

# Human-readable period label for tooltips and headers.
# e.g. "Jan–June 2023" for YTD, or "June 2023" for Month Only.
if time_range == 'YTD':
    period_label = f"Jan–{selected_month_name} {selected_year}"
else:
    period_label = f"{selected_month_name} {selected_year}"


# ═════════════════════════════════════════════════════════════════════════════
#  PAGE HEADER
# ═════════════════════════════════════════════════════════════════════════════
st.markdown(f"**Sales Dashboard** &nbsp;&nbsp; "
            f"<span style='font-size:13px; color:#888'>Period: {period_label} &nbsp;|&nbsp; "
            f"Comparison: {comparison_mode}</span>",
            unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
#  DRILL-DOWN NAVIGATION BAR
# ═════════════════════════════════════════════════════════════════════════════
# If we're in drill-down mode (a category is selected), show a "Back" button
# and tell the user which category they're viewing.
if st.session_state.selected_category:
    col_back, col_label = st.columns([1, 5])
    with col_back:
        # When clicked, this button clears the category and reruns the page
        if st.button("← Back to Overview"):
            st.session_state.selected_category = None
            st.rerun()   # Immediately reload the page in overview mode
    with col_label:
        st.markdown(f"Viewing: **{st.session_state.selected_category}**")


# ═════════════════════════════════════════════════════════════════════════════
#  LAYOUT: OVERVIEW MODE
# ═════════════════════════════════════════════════════════════════════════════
# Overview shows all three categories side by side.
#
# Row 1: [KPI card (narrow)] [Overall monthly bar chart (wide)]
# Row 2: [Furniture] [Office Supplies] [Technology]
#         Each has a small KPI card + monthly bar chart

if st.session_state.selected_category is None:
    # ── ROW 1: Overall KPI + Overall monthly chart ───────────────
    # st.columns([1, 3]) creates two columns where the right one is 3x wider.
    kpi_col, chart_col = st.columns([1, 3])

    with kpi_col:
        # Calculate the overall totals (no category filter)
        actual, comp, pct, comp_label = dp.get_period_totals(
            orders, goals, selected_year, selected_month,
            time_range, comparison_mode, category=None
        )
        # Build and display the big KPI card
        fig = cb.make_kpi_text_fig(actual, comp, pct, comp_label,
                                   title="TOTAL SALES", large=True)
        st.plotly_chart(fig, use_container_width=True, key="kpi_overall")

    with chart_col:
        # Calculate monthly actuals and comparisons (no category filter)
        actuals = dp.get_monthly_actuals(orders, selected_year, category=None)
        comps   = dp.get_monthly_comparison(
            orders, goals, selected_year, comparison_mode, category=None
        )
        _, _, _, comp_label = dp.get_period_totals(
            orders, goals, selected_year, selected_month,
            time_range, comparison_mode, category=None
        )
        # Build and display the overall monthly bar chart
        fig = cb.make_bar_chart(
            actuals.tolist(), comps, comp_label,
            bar_colors, dp.MONTH_NAMES, selected_year, height=280
        )
        st.plotly_chart(fig, use_container_width=True, key="chart_overall")

    # ── ROW 2: Three category panels ─────────────────────────────
    # st.columns(3) creates three equal-width columns.
    cat_cols = st.columns(3)

    for i, cat in enumerate(dp.CATEGORIES):
        with cat_cols[i]:
            # Small KPI card for this category
            actual, comp, pct, comp_label = dp.get_period_totals(
                orders, goals, selected_year, selected_month,
                time_range, comparison_mode, category=cat
            )
            fig = cb.make_kpi_text_fig(actual, comp, pct, comp_label,
                                       title=cat, large=False)
            st.plotly_chart(fig, use_container_width=True, key=f"kpi_{cat}")

            # Monthly bar chart for this category
            actuals = dp.get_monthly_actuals(orders, selected_year, category=cat)
            comps   = dp.get_monthly_comparison(
                orders, goals, selected_year, comparison_mode, category=cat
            )
            fig = cb.make_bar_chart(
                actuals.tolist(), comps, comp_label,
                bar_colors, dp.MONTH_NAMES, selected_year, height=240
            )
            st.plotly_chart(fig, use_container_width=True, key=f"chart_{cat}")

            # Drill-down button below each category's charts
            # When clicked, we store the category name and rerun.
            if st.button(f"🔍 Drill into {cat}", key=f"drill_{cat}"):
                st.session_state.selected_category = cat
                st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
#  LAYOUT: DRILL-DOWN MODE
# ═════════════════════════════════════════════════════════════════════════════
# Drill-down shows one category in detail with a sub-category breakdown.
#
# Row 1: [KPI card (narrow)] [Sub-category horizontal bar chart (wide)]
# Row 2: [Full-width monthly bar chart for the selected category]
#
# The sub-category chart shows:
#   - Blue bars: actual sales for the selected period
#   - Gray bars: comparison for the selected period (e.g. Jan–June goal)
#   - Dark gray lines: full-year comparison (e.g. full 2023 goal)

else:
    cat = st.session_state.selected_category

    # ── ROW 1: Category KPI + Sub-category chart ────────────────
    kpi_col, subcat_col = st.columns([1, 3])

    with kpi_col:
        # KPI card — but this time filtered to the selected category.
        # We use large=True so it matches the overall KPI card size.
        actual, comp, pct, comp_label = dp.get_period_totals(
            orders, goals, selected_year, selected_month,
            time_range, comparison_mode, category=cat
        )
        fig = cb.make_kpi_text_fig(actual, comp, pct, comp_label,
                                   title=cat, large=True)
        st.plotly_chart(fig, use_container_width=True, key="kpi_drilldown")

    with subcat_col:
        # Sub-category horizontal bar chart.
        # We need three datasets:
        #   1. Actual sales by sub-category for the selected period
        #   2. Comparison values for the selected period (gray bars)
        #   3. Comparison values for the full year (dark reference lines)
        sc_actuals = dp.get_subcategory_actuals(
            orders, selected_year, selected_month, time_range, cat
        )
        sc_period_comps = dp.get_subcategory_period_comparison(
            orders, goals, selected_year, selected_month,
            time_range, comparison_mode, cat
        )
        sc_fy_comps = dp.get_subcategory_full_year_comparison(
            orders, goals, selected_year, comparison_mode, cat
        )
        fig = cb.make_subcategory_chart(
            sc_actuals, sc_period_comps, sc_fy_comps,
            comp_label, period_label, selected_year, height=350
        )
        st.plotly_chart(fig, use_container_width=True, key="chart_subcategory")

    # ── ROW 2: Full-width monthly bar chart for this category ────
    st.markdown(f"#### {cat} — Monthly Trend")

    actuals = dp.get_monthly_actuals(orders, selected_year, category=cat)
    comps   = dp.get_monthly_comparison(
        orders, goals, selected_year, comparison_mode, category=cat
    )
    fig = cb.make_bar_chart(
        actuals.tolist(), comps, comp_label,
        bar_colors, dp.MONTH_NAMES, selected_year, height=280
    )
    st.plotly_chart(fig, use_container_width=True, key="chart_drilldown_monthly")
