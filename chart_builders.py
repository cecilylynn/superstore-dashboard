"""
chart_builders.py — All Plotly Chart Construction

This file builds every chart displayed on the dashboard.
Each function takes PRE-COMPUTED data (numbers, lists, strings) and
returns a Plotly Figure object.  No data loading or calculation happens
here — that all lives in data_processing.py.

Think of it this way:
  data_processing.py  →  crunches the numbers
  chart_builders.py   →  draws the pictures  (this file)
  app.py              →  wires the UI together

If you need to change how a chart LOOKS (colors, fonts, margins, tooltips),
edit this file.  If you need to change how a NUMBER IS COMPUTED, look in
data_processing.py instead.
"""

import plotly.graph_objects as go


# ── COLOR CONSTANTS ──────────────────────────────────────────────────────────
# Defining colors in one place makes it easy to tweak the whole dashboard's
# look without hunting through multiple functions.

BLUE        = '#6495ED'   # Cornflower blue — actual sales bars (selected months)
PALE_BLUE   = '#B0C4DE'   # Light steel blue — actual sales bars (unselected months)
LIGHT_GRAY  = '#D3D3D3'   # Comparison bars (goal or prior year)
DARK_GRAY   = '#555555'   # Full-year reference lines on sub-category chart
GREEN       = '#2ecc71'   # KPI percentage text when ABOVE goal/comparison
RED         = '#e74c3c'   # KPI percentage text when BELOW goal/comparison
GRID_COLOR  = '#f0f0f0'   # Subtle gridlines on charts


# ── HOVERLABEL STYLE ─────────────────────────────────────────────────────────
# Shared tooltip (hoverlabel) styling so all charts have a consistent look.
# This controls the little popup box that appears when you hover over a bar.
HOVERLABEL_STYLE = dict(
    bgcolor='white',         # White background in the tooltip box
    font_size=12,            # Readable but not huge text
    font_family='Arial',     # Clean sans-serif font
    bordercolor='#ddd',      # Subtle border around the tooltip
)


# ═════════════════════════════════════════════════════════════════════════════
#  MONTHLY BAR CHART (vertical bars, Jan–Dec)
# ═════════════════════════════════════════════════════════════════════════════
#
#  This draws the vertical bar chart showing sales for each month.
#
#  Two layers of bars are overlaid:
#    1. GRAY bars in the back  = comparison (goal or prior year)
#    2. COLORED bars in front  = actual sales
#
#  The colored bars use BLUE for selected months and PALE BLUE for
#  unselected months.  For example, if viewing "YTD through June",
#  Jan–Jun bars are blue and Jul–Dec bars are pale blue.

def make_bar_chart(
    actuals: list[float],
    comps: list[float],
    comp_label: str,
    bar_colors: list[str],
    month_names: list[str],
    year: int,
    height: int = 280
) -> go.Figure:
    """
    Build a vertical monthly bar chart (Jan–Dec).

    Args:
        actuals:     List of 12 actual sales values, one per month.
        comps:       List of 12 comparison values (goal or prior year).
        comp_label:  Label for the comparison, like "Goal" or "2022".
        bar_colors:  List of 12 color strings — blue for selected months,
                     pale blue for unselected months.
        month_names: List of 12 short month names: ['Jan', 'Feb', ..., 'Dec'].
        year:        The selected year (used in tooltip text, e.g. "Jun 2023").
        height:      Chart height in pixels. Default 280 for overview row 1,
                     use 240 for the smaller category charts in row 2.

    Returns:
        A Plotly Figure. Render it with st.plotly_chart(use_container_width=True).
    """
    # ── Build hover text for each month ──────────────────────────
    # When you hover over a blue bar, you see:
    #   "Jun 2023"
    #   "Actual: $45,230"
    #   "Goal: $42,100"
    #   "Difference: ▲ 7.4%"
    hover_texts = []
    for month_name, actual, comp in zip(month_names, actuals, comps):
        # Calculate percent difference for this specific month
        pct   = ((actual - comp) / comp * 100) if comp > 0 else 0
        arrow = '▲' if pct >= 0 else '▼'
        hover_texts.append(
            f"<b>{month_name} {year}</b><br>"
            f"Actual: ${actual:,.0f}<br>"
            f"{comp_label}: ${comp:,.0f}<br>"
            f"Difference: {arrow} {abs(pct):.1f}%"
        )

    # ── Start building the figure ────────────────────────────────
    fig = go.Figure()

    # Layer 1 (back): GRAY comparison bars
    # These are full-width bars that sit behind the narrower blue bars.
    # They show the goal or prior-year sales for each month.
    fig.add_trace(go.Bar(
        x=month_names,
        y=comps,
        name=comp_label,
        marker_color=LIGHT_GRAY,
        opacity=0.85,                 # Slightly transparent so they feel "behind"
        showlegend=False,
        hovertemplate=(               # Simple tooltip for gray bars
            f'<b>%{{x}}</b><br>'
            f'{comp_label}: $%{{y:,.0f}}'
            f'<extra></extra>'
        ),
    ))

    # Layer 2 (front): COLORED actual sales bars
    # These are narrower (width=0.4) and sit on top of the gray bars.
    # Colors come from bar_colors — blue for selected months, pale for others.
    fig.add_trace(go.Bar(
        x=month_names,
        y=actuals,
        name='Actual',
        marker_color=bar_colors,
        width=0.4,                    # Narrower than the gray bars behind
        showlegend=False,
        hovertext=hover_texts,
        hovertemplate='%{hovertext}<extra></extra>',
    ))

    # ── Layout styling ───────────────────────────────────────────
    # Backgrounds are transparent so the white card container shows through.
    fig.update_layout(
        barmode='overlay',            # Bars on top of each other (not side by side)
        height=height,
        margin=dict(t=8, b=36, l=48, r=8),   # Tight margins
        template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent — white card shows through
        plot_bgcolor='rgba(0,0,0,0)',   # Transparent — white card shows through
        yaxis=dict(
            tickprefix='$',           # Show dollar sign on y-axis labels
            tickformat=',.0f',        # Comma-separated, no decimals (e.g. "$45,000")
            tickfont=dict(size=11, color='#888'),   # Subtle gray tick labels
            gridcolor=GRID_COLOR,     # Very faint gridlines for readability
        ),
        xaxis=dict(
            tickfont=dict(size=10, color='#888'),   # Month labels
        ),
        hoverlabel=HOVERLABEL_STYLE,  # Consistent tooltip styling
    )

    return fig


# ═════════════════════════════════════════════════════════════════════════════
#  SUB-CATEGORY HORIZONTAL BAR CHART (drill-down view)
# ═════════════════════════════════════════════════════════════════════════════
#
#  This chart appears when you click on a category to "drill down."
#  It shows a HORIZONTAL bar chart with one row per sub-category.
#
#  Three layers of data:
#    1. GRAY bars     = comparison for the SELECTED PERIOD
#                       (e.g. goal through June if viewing YTD June)
#    2. BLUE bars     = actual sales for the SELECTED PERIOD
#    3. DARK LINES    = full-year comparison (e.g. the FULL 2023 goal)
#
#  The dark lines let you see "how close am I to the full-year target?"
#  while the gray bars show "how am I doing vs the period target?"
#
#  Sub-categories are sorted smallest-to-largest because Plotly draws
#  horizontal bars from bottom to top. This puts the biggest sub-categories
#  at the top of the chart where your eye goes first.

def make_subcategory_chart(
    actuals: 'pd.Series',
    period_comps: dict[str, float],
    fy_comps: dict[str, float],
    comp_label: str,
    period_label: str,
    year: int,
    height: int = 350
) -> go.Figure:
    """
    Build a horizontal bar chart showing sub-categories within one category.

    Args:
        actuals:       A pandas Series indexed by sub-category name,
                       values are total sales, sorted ascending (smallest first).
                       Example: {"Labels": 5000, "Bookcases": 12000, "Chairs": 45000}
        period_comps:  Dict mapping sub-category name → comparison value
                       for the SELECTED PERIOD (e.g. Jan–June goal).
        fy_comps:      Dict mapping sub-category name → comparison value
                       for the FULL YEAR (e.g. all of 2023 goal).
        comp_label:    Label for the comparison, like "Goal" or "2022".
        period_label:  Text describing the selected period, like "Jan–Jun 2023"
                       or "June 2023".
        year:          The selected year (used in tooltip text).
        height:        Chart height in pixels (default 350).

    Returns:
        A Plotly Figure. Render it with st.plotly_chart(use_container_width=True).
    """
    # ── Extract values in the same order as actuals (sorted ascending) ───
    subcat_names = actuals.index.tolist()          # e.g. ["Labels", "Bookcases", "Chairs"]
    period_vals  = [period_comps.get(sc, 0) for sc in subcat_names]   # Period comparison amounts
    fy_vals      = [fy_comps.get(sc, 0) for sc in subcat_names]       # Full-year comparison amounts

    # ── Build hover text for each sub-category ───────────────────
    # When you hover over a blue bar, you see:
    #   "Chairs"
    #   "Actual (Jan–Jun 2023): $45,230"
    #   "Goal (Jan–Jun 2023): $42,100"
    #   "Difference: ▲ 7.4%"
    #   "Goal (Full Year 2023): $85,000"
    hover_texts = []
    for sc, actual, pcomp, fycomp in zip(subcat_names, actuals, period_vals, fy_vals):
        # Calculate percent difference vs. the period comparison
        pct   = ((actual - pcomp) / pcomp * 100) if pcomp > 0 else 0
        arrow = '▲' if pct >= 0 else '▼'
        hover_texts.append(
            f"<b>{sc}</b><br>"
            f"Actual ({period_label}): ${actual:,.0f}<br>"
            f"{comp_label} ({period_label}): ${pcomp:,.0f}<br>"
            f"Difference: {arrow} {abs(pct):.1f}%<br>"
            f"{comp_label} (Full Year {year}): ${fycomp:,.0f}"
        )

    # ── Start building the figure ────────────────────────────────
    fig = go.Figure()

    # Layer 1 (back): GRAY bars = comparison for the SELECTED PERIOD
    # These show how much the goal (or prior year) was for the same period
    # you're viewing — e.g. the Jan–June goal, not the full-year goal.
    fig.add_trace(go.Bar(
        y=subcat_names,
        x=period_vals,
        orientation='h',               # Horizontal bars
        name=comp_label,
        marker_color=LIGHT_GRAY,
        opacity=0.85,
        showlegend=False,
        hovertemplate=(
            '<b>%{y}</b><br>'
            + comp_label + ' (' + period_label + '): $%{x:,.0f}'
            + '<extra></extra>'
        ),
    ))

    # Layer 2 (front): BLUE bars = actual sales for the SELECTED PERIOD
    # Narrower than the gray bars (width=0.4) so you can see both.
    fig.add_trace(go.Bar(
        y=subcat_names,
        x=actuals.tolist(),
        orientation='h',
        name='Actual',
        marker_color=BLUE,
        width=0.4,                     # Narrower than the gray bars behind
        showlegend=False,
        hovertext=hover_texts,
        hovertemplate='%{hovertext}<extra></extra>',
    ))

    # Layer 3: DARK GRAY REFERENCE LINES = full-year comparison
    # These are thin vertical lines that show "where does this sub-category
    # need to end up by December?"  Comparing the blue bar to this line tells
    # you if you're on pace for the full year.
    #
    # We draw these as Plotly "shapes" (lines), not as bars.
    # Each line spans from y-0.4 to y+0.4 to cover the height of one bar row.
    shapes = []
    for i, fycomp in enumerate(fy_vals):
        if fycomp > 0:   # Don't draw a line if the full-year target is $0
            shapes.append(dict(
                type='line',
                x0=fycomp, x1=fycomp,          # Vertical line at the full-year value
                y0=i - 0.4, y1=i + 0.4,        # Span the height of one bar row
                line=dict(color=DARK_GRAY, width=2),
                layer='above',                  # Draw on top of the bars
            ))

    # ── Layout styling ───────────────────────────────────────────
    # Backgrounds are transparent so the white card container shows through.
    fig.update_layout(
        barmode='overlay',             # Bars on top of each other
        height=height,
        margin=dict(t=8, b=20, l=120, r=8),   # Extra left margin for sub-category names
        template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent — white card shows through
        plot_bgcolor='rgba(0,0,0,0)',   # Transparent — white card shows through
        xaxis=dict(
            tickprefix='$',
            tickformat=',.0f',
            tickfont=dict(size=11, color='#888'),
            gridcolor=GRID_COLOR,      # Subtle vertical gridlines
        ),
        yaxis=dict(
            tickfont=dict(size=11, color='#444'),   # Sub-category name labels
        ),
        shapes=shapes,                 # The dark gray reference lines
        hoverlabel=HOVERLABEL_STYLE,   # Consistent tooltip styling
    )

    return fig
