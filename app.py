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
# We inject custom CSS to match the Tableau dashboard design:
#   - Light gray page background
#   - White card containers with rounded corners and subtle shadows
#   - Structured KPI cards with consistent typography
#   - Tight spacing between elements
#   - Full-width header bar
st.markdown("""
<style>
    /* ── Page background ── */
    /* Light gray background so white cards stand out visually */
    .stApp {
        background-color: #f0f2f6;
    }

    /* Reduce Streamlit's default top padding on the main content area */
    .block-container {
        padding-top: 0.5rem;
        padding-bottom: 0rem;
        max-width: 100%;
    }

    /* ── Dashboard header bar ── */
    /* White strip spanning full width at the top of the page */
    .dashboard-header {
        background: white;
        padding: 14px 24px;
        border-bottom: 2px solid #e0e0e0;
        margin: -0.5rem -1rem 16px -1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-radius: 0 0 4px 4px;
    }
    .dashboard-title {
        font-size: 20px;
        font-weight: 700;
        color: #1a1a2e;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    .dashboard-subtitle {
        font-size: 13px;
        color: #888;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    /* ── KPI card ── */
    /* White box with structured text: header, period, big number, comparison */
    .kpi-card {
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        padding: 16px 20px;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .kpi-card-large {
        min-height: 140px;
    }
    .kpi-header {
        font-size: 11px;
        font-weight: 600;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
    }
    .kpi-period {
        font-size: 11px;
        color: #aaa;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 32px;
        font-weight: 900;
        color: #1a1a2e;
        font-family: 'Arial Black', Arial, sans-serif;
        line-height: 1.1;
        margin-bottom: 4px;
    }
    .kpi-value-large {
        font-size: 44px;
    }
    .kpi-comp {
        font-size: 13px;
        color: #666;
        margin-top: 4px;
    }
    .kpi-up { color: #2ecc71; font-weight: 700; }
    .kpi-down { color: #e74c3c; font-weight: 700; }
    .kpi-exact {
        font-size: 10px;
        color: #bbb;
        margin-top: 6px;
    }

    /* ── Chart card ── */
    /* White box wrapping each Plotly chart */
    .chart-card {
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        padding: 12px 8px 4px 8px;
        overflow: hidden;
    }
    .chart-label {
        font-size: 11px;
        color: #aaa;
        padding: 0 8px 4px 8px;
    }

    /* ── Tighten Streamlit element spacing ── */
    .element-container {
        margin-bottom: 0px !important;
    }
    .stPlotlyChart {
        margin-bottom: -10px;
    }

    /* ── Drill-down button styling ── */
    /* Full-width button below each category panel */
    .stButton > button {
        width: 100%;
        border: 1px solid #ddd;
        background: white;
        color: #555;
        font-size: 12px;
        border-radius: 6px;
        padding: 6px 12px;
        margin-top: 6px;
    }
    .stButton > button:hover {
        background: #f8f9fb;
        border-color: #bbb;
    }

    /* ── Back button in drill-down mode ── */
    .back-bar {
        margin-bottom: 12px;
    }
    .back-btn {
        display: inline-block;
        padding: 6px 14px;
        background: white;
        border: 1px solid #ddd;
        border-radius: 6px;
        cursor: pointer;
        font-size: 12px;
        color: #555;
        text-decoration: none;
    }
    .back-btn:hover {
        background: #f0f2f6;
    }

    /* ── Section title for drill-down monthly trend ── */
    .section-title {
        font-size: 14px;
        font-weight: 600;
        color: #555;
        margin: 8px 0 8px 0;
    }

    /* ── Hide Streamlit's default header and footer chrome ── */
    header[data-testid="stHeader"] {
        background: transparent;
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
    # index=3 makes 2023 the default selection (0-indexed).
    selected_year = st.selectbox(
        "Year",
        options=[2020, 2021, 2022, 2023],
        index=3,   # Default to 2023
    )

    # ── Month selector ───────────────────────────────────────────
    # Shows full month names (January, February, ...) but we need the
    # month NUMBER (1–12) for our calculations.
    month_options = list(dp.MONTH_MAP.keys())   # ['January', 'February', ..., 'December']
    selected_month_name = st.selectbox(
        "Through Month",
        options=month_options,
        index=11,   # Default to December
    )
    # Convert the full month name to a number (e.g. "June" → 6)
    selected_month = dp.MONTH_MAP[selected_month_name]

    st.divider()   # Visual horizontal line to separate groups

    # ── Time Range toggle ────────────────────────────────────────
    time_range = st.radio(
        "Time Range",
        options=["YTD", "Month Only"],
        index=0,   # Default to YTD
    )

    st.divider()

    # ── Comparison Mode toggle ───────────────────────────────────
    comparison_mode = st.radio(
        "Compare To",
        options=["vs Goal", "vs Prior Year"],
        index=0,   # Default to vs Goal
    )


# ═════════════════════════════════════════════════════════════════════════════
#  SESSION STATE: DRILL-DOWN NAVIGATION
# ═════════════════════════════════════════════════════════════════════════════
# Streamlit's "session state" persists across reruns within the same browser
# session.  We use it to remember which category the user has drilled into.

if 'selected_category' not in st.session_state:
    st.session_state.selected_category = None   # Start in overview mode


# ═════════════════════════════════════════════════════════════════════════════
#  DERIVED VALUES
# ═════════════════════════════════════════════════════════════════════════════
# These values are computed from the sidebar selections and used by multiple
# parts of the page.

# Which months are "selected" (used for bar coloring)?
if time_range == 'YTD':
    selected_months = list(range(1, selected_month + 1))
else:
    selected_months = [selected_month]

# Bar colors: blue for active months, pale blue for others.
bar_colors = [
    cb.BLUE if m in selected_months else cb.PALE_BLUE
    for m in range(1, 13)
]

# Human-readable period label for tooltips and headers.
if time_range == 'YTD':
    period_label = f"Jan–{selected_month_name} {selected_year}"
else:
    period_label = f"{selected_month_name} {selected_year}"


# ═════════════════════════════════════════════════════════════════════════════
#  HELPER: KPI CARD RENDERER
# ═════════════════════════════════════════════════════════════════════════════
# We render KPI cards as raw HTML instead of Plotly figures for precise
# control over typography, spacing, and alignment.  This matches the
# Tableau dashboard's clean card design.

def render_kpi_html(
    title: str,
    actual: float,
    comp: float,
    pct: float,
    comp_label: str,
    period_text: str,
    large: bool = False
) -> str:
    """
    Build a KPI card as an HTML string.

    Args:
        title:       Card heading — "TOTAL SALES" or a category name.
        actual:      Actual sales dollar amount.
        comp:        Comparison value (goal or prior year).
        pct:         Percent difference (positive = above, negative = below).
        comp_label:  Label for comparison ("Goal" or "2022").
        period_text: Text like "Jan–Dec 2023" shown under the title.
        large:       True = big primary KPI card (Row 1).

    Returns:
        An HTML string. Render with st.markdown(html, unsafe_allow_html=True).
    """
    # Pick arrow direction and color class
    arrow = '▲' if pct >= 0 else '▼'
    color_cls = 'kpi-up' if pct >= 0 else 'kpi-down'

    # CSS classes for sizing
    card_cls = 'kpi-card kpi-card-large' if large else 'kpi-card'
    val_cls  = 'kpi-value kpi-value-large' if large else 'kpi-value'

    return f"""
    <div class="{card_cls}">
        <div class="kpi-header">{title}</div>
        <div class="kpi-period">{period_text}</div>
        <div class="{val_cls}">{dp.fmt(actual)}</div>
        <div class="kpi-comp">
            {comp_label}: {dp.fmt(comp)}
            &nbsp;<span class="{color_cls}">({arrow} {abs(pct):.1f}%)</span>
        </div>
        <div class="kpi-exact">
            Actual: ${actual:,.2f} &nbsp;|&nbsp; {comp_label}: ${comp:,.2f}
        </div>
    </div>
    """


# ═════════════════════════════════════════════════════════════════════════════
#  DASHBOARD HEADER BAR
# ═════════════════════════════════════════════════════════════════════════════
# Full-width white strip at the top with title on the left and period info
# on the right, matching the Tableau dashboard header.

st.markdown(f"""
<div class="dashboard-header">
    <div class="dashboard-title">Sales Dashboard</div>
    <div class="dashboard-subtitle">
        FY {selected_year} &nbsp;&nbsp;|&nbsp;&nbsp; {period_label} &nbsp;&nbsp;|&nbsp;&nbsp; {comparison_mode}
    </div>
</div>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
#  DRILL-DOWN NAVIGATION BAR
# ═════════════════════════════════════════════════════════════════════════════
# If we're in drill-down mode, show a "Back" button and category label.
if st.session_state.selected_category:
    col_back, col_label = st.columns([1, 5])
    with col_back:
        if st.button("← Back to Overview"):
            st.session_state.selected_category = None
            st.rerun()
    with col_label:
        st.markdown(f"Viewing: **{st.session_state.selected_category}**")


# ═════════════════════════════════════════════════════════════════════════════
#  LAYOUT: OVERVIEW MODE
# ═════════════════════════════════════════════════════════════════════════════
# Overview shows:
#   Row 1: [KPI card (narrow)] [Overall monthly bar chart (wide)]
#   Row 2: [Furniture] [Office Supplies] [Technology]
#           Each has a KPI card + bar chart + drill-down button

if st.session_state.selected_category is None:

    # ── ROW 1: Overall KPI + Overall monthly chart ───────────────
    kpi_col, chart_col = st.columns([1, 3])

    with kpi_col:
        # Calculate overall totals (no category filter)
        actual, comp, pct, comp_label = dp.get_period_totals(
            orders, goals, selected_year, selected_month,
            time_range, comparison_mode, category=None
        )
        # Render KPI card as HTML
        st.markdown(
            render_kpi_html("Total Sales", actual, comp, pct,
                            comp_label, period_label, large=True),
            unsafe_allow_html=True
        )

    with chart_col:
        # Calculate monthly actuals and comparisons
        actuals = dp.get_monthly_actuals(orders, selected_year, category=None)
        comps   = dp.get_monthly_comparison(
            orders, goals, selected_year, comparison_mode, category=None
        )
        _, _, _, comp_label = dp.get_period_totals(
            orders, goals, selected_year, selected_month,
            time_range, comparison_mode, category=None
        )
        # Build bar chart
        fig = cb.make_bar_chart(
            actuals.tolist(), comps, comp_label,
            bar_colors, dp.MONTH_NAMES, selected_year, height=280
        )
        # Wrap in a white card container
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown(
            f'<div class="chart-label">Blue = Actual &nbsp;|&nbsp; Gray = {comp_label}</div>',
            unsafe_allow_html=True
        )
        st.plotly_chart(fig, use_container_width=True, key="chart_overall")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── ROW 2: Three category panels ─────────────────────────────
    cat_cols = st.columns(3)

    for i, cat in enumerate(dp.CATEGORIES):
        with cat_cols[i]:
            # Small KPI card for this category
            actual, comp, pct, comp_label = dp.get_period_totals(
                orders, goals, selected_year, selected_month,
                time_range, comparison_mode, category=cat
            )
            st.markdown(
                render_kpi_html(cat, actual, comp, pct,
                                comp_label, period_label, large=False),
                unsafe_allow_html=True
            )

            # Small spacer between KPI card and chart
            st.markdown('<div style="height: 8px;"></div>', unsafe_allow_html=True)

            # Monthly bar chart for this category
            actuals = dp.get_monthly_actuals(orders, selected_year, category=cat)
            comps   = dp.get_monthly_comparison(
                orders, goals, selected_year, comparison_mode, category=cat
            )
            fig = cb.make_bar_chart(
                actuals.tolist(), comps, comp_label,
                bar_colors, dp.MONTH_NAMES, selected_year, height=220
            )
            # Wrap in a white card container
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, key=f"chart_{cat}")
            st.markdown('</div>', unsafe_allow_html=True)

            # Drill-down button
            if st.button(f"🔍 Drill into {cat}", key=f"drill_{cat}"):
                st.session_state.selected_category = cat
                st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
#  LAYOUT: DRILL-DOWN MODE
# ═════════════════════════════════════════════════════════════════════════════
# Drill-down shows one category in detail:
#   Row 1: [KPI card (narrow)] [Sub-category horizontal bar chart (wide)]
#   Row 2: [Full-width monthly bar chart for the selected category]

else:
    cat = st.session_state.selected_category

    # ── ROW 1: Category KPI + Sub-category chart ────────────────
    kpi_col, subcat_col = st.columns([1, 3])

    with kpi_col:
        actual, comp, pct, comp_label = dp.get_period_totals(
            orders, goals, selected_year, selected_month,
            time_range, comparison_mode, category=cat
        )
        st.markdown(
            render_kpi_html(cat, actual, comp, pct,
                            comp_label, period_label, large=True),
            unsafe_allow_html=True
        )

    with subcat_col:
        # Sub-category horizontal bar chart
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
        # Wrap in a white card container
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown(
            f'<div class="chart-label">'
            f'Blue = Actual &nbsp;|&nbsp; Gray = {comp_label} (period) '
            f'&nbsp;|&nbsp; Dark line = {comp_label} (full year)'
            f'</div>',
            unsafe_allow_html=True
        )
        st.plotly_chart(fig, use_container_width=True, key="chart_subcategory")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── ROW 2: Full-width monthly bar chart for this category ────
    st.markdown(f'<div class="section-title">{cat} — Monthly Trend</div>',
                unsafe_allow_html=True)

    actuals = dp.get_monthly_actuals(orders, selected_year, category=cat)
    comps   = dp.get_monthly_comparison(
        orders, goals, selected_year, comparison_mode, category=cat
    )
    fig = cb.make_bar_chart(
        actuals.tolist(), comps, comp_label,
        bar_colors, dp.MONTH_NAMES, selected_year, height=280
    )
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="chart-label">Blue = Actual &nbsp;|&nbsp; Gray = {comp_label}</div>',
        unsafe_allow_html=True
    )
    st.plotly_chart(fig, use_container_width=True, key="chart_drilldown_monthly")
    st.markdown('</div>', unsafe_allow_html=True)
