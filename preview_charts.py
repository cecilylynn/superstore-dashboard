"""
Preview of Dashboard Visualizations
Layout:
  - Left sidebar: Settings panel
  - Right main area:
      Row 1: KPI card (large) + Overall monthly bar chart
      Row 2: Three category panels, each = small KPI text card + monthly bar chart
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly import offline

# ── Load data ────────────────────────────────────────────────────────────────
orders = pd.read_excel(
    '/Users/cecilysantiago/Documents/Claude Code Playground/Datasources/Sample - Superstore.xls',
    sheet_name='Orders')
goals = pd.read_csv(
    '/Users/cecilysantiago/Documents/Claude Code Playground/Datasources/subcategory_monthly_goals.csv')

orders['Order Date'] = pd.to_datetime(orders['Order Date'])
orders['Year']       = orders['Order Date'].dt.year
orders['Month']      = orders['Order Date'].dt.month
orders['Year-Month'] = orders['Order Date'].dt.strftime('%Y-%m')

# ── Parameters (simulated; will be Streamlit widgets in the real dashboard) ──
selected_year       = 2023
selected_month      = 6          # June
selected_month_name = 'June'
time_range          = 'YTD'      # 'YTD' | 'Month Only'
comparison_mode     = 'vs Goal'  # 'vs Goal' | 'vs Prior Year'
selected_category   = None       # None = overview mode, or specific category name for drill-down

CATEGORIES  = ['Furniture', 'Office Supplies', 'Technology']
MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
MONTH_MAP   = {'January':1,'February':2,'March':3,'April':4,'May':5,'June':6,
               'July':7,'August':8,'September':9,'October':10,'November':11,'December':12}
MONTH_NUM_TO_NAME = {v:k for k,v in MONTH_MAP.items()}

# Shared style constants for the settings panel HTML
sel_style  = "width:100%;padding:5px 8px;border:1px solid #ccc;border-radius:4px;font-size:12px;background:white"
radio_row  = "display:block;margin-bottom:5px;cursor:pointer;font-size:12px;color:#444"

selected_months = list(range(1, selected_month + 1)) if time_range == 'YTD' else [selected_month]
bar_colors = ['#6495ED' if m in selected_months else '#B0C4DE' for m in range(1, 13)]
period_label = (f"Jan–{selected_month_name} {selected_year}"
                if time_range == 'YTD' else f"{selected_month_name} {selected_year}")

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt(value):
    a = abs(value)
    if a >= 100_000_000: return f"${value/1_000_000:.0f}M"
    if a >= 10_000_000:  return f"${value/1_000_000:.1f}M"
    if a >= 1_000_000:   return f"${value/1_000_000:.1f}M"
    if a >= 100_000:     return f"${value/1_000:.0f}K"
    if a >= 10_000:      return f"${value/1_000:.1f}K"
    if a >= 1_000:       return f"${value/1_000:.1f}K"
    return f"${value:.0f}"

def get_monthly_actuals(category=None):
    d = orders[orders['Year'] == selected_year].copy()
    if category:
        d = d[d['Category'] == category]
    return d.groupby('Month')['Sales'].sum().reindex(range(1, 13), fill_value=0)

def get_monthly_comparison(category=None):
    if comparison_mode == 'vs Goal':
        subcats = (orders[orders['Category'] == category]['Sub-Category'].unique()
                   if category else None)
        result = []
        for m in range(1, 13):
            ym = f"{selected_year}-{m:02d}"
            g  = goals[goals['Year-Month'] == ym]
            if subcats is not None:
                g = g[g['Sub-Category'].isin(subcats)]
            result.append(g['Sales_Goal'].sum())
        return result
    else:
        prior = orders[orders['Year'] == selected_year - 1].copy()
        if category:
            prior = prior[prior['Category'] == category]
        return prior.groupby('Month')['Sales'].sum().reindex(range(1, 13), fill_value=0).tolist()

def get_period_totals(category=None):
    d = orders[orders['Year'] == selected_year].copy()
    if category:
        d = d[d['Category'] == category]
    d = d[d['Month'] <= selected_month] if time_range == 'YTD' else d[d['Month'] == selected_month]
    actual = d['Sales'].sum()

    if comparison_mode == 'vs Goal':
        ym_list = ([f"{selected_year}-{m:02d}" for m in range(1, selected_month + 1)]
                   if time_range == 'YTD' else [f"{selected_year}-{selected_month:02d}"])
        g = goals[goals['Year-Month'].isin(ym_list)]
        if category:
            subcats = orders[orders['Category'] == category]['Sub-Category'].unique()
            g = g[g['Sub-Category'].isin(subcats)]
        comp  = g['Sales_Goal'].sum()
        label = 'Goal'
    else:
        prior = orders[orders['Year'] == selected_year - 1].copy()
        if category:
            prior = prior[prior['Category'] == category]
        prior = (prior[prior['Month'] <= selected_month] if time_range == 'YTD'
                 else prior[prior['Month'] == selected_month])
        comp  = prior['Sales'].sum()
        label = str(selected_year - 1)

    pct = ((actual - comp) / comp * 100) if comp > 0 else 0
    return actual, comp, pct, label

def make_kpi_text_fig(category=None, large=False):
    """
    Return a Figure that is just text — left-aligned KPI card.
    large=True  → big primary KPI card
    large=False → smaller category header card
    """
    actual, comp, pct, comp_label = get_period_totals(category)
    arrow = '▲' if pct >= 0 else '▼'
    clr   = '#2ecc71' if pct >= 0 else '#e74c3c'

    if large:
        title_str = "TOTAL SALES"
        val_size  = 56
        sub_size  = 15
        height    = 140
    else:
        title_str = category
        val_size  = 28
        sub_size  = 12
        height    = 90

    f = go.Figure()
    # invisible scatter just to carry a hover with exact values
    f.add_trace(go.Scatter(
        x=[0], y=[0.5], mode='markers',
        marker=dict(size=1, opacity=0),
        hovertemplate=(
            f"<b>{title_str}</b><br>"
            f"Actual: ${actual:,.2f}<br>"
            f"{comp_label}: ${comp:,.2f}<br>"
            f"Diff: {arrow} {abs(pct):.1f}%<extra></extra>"
        ),
        showlegend=False
    ))

    # Title line
    f.add_annotation(text=f"<b>{title_str}</b>",
        x=0, y=1, xref='paper', yref='paper',
        xanchor='left', yanchor='top', showarrow=False,
        font=dict(size=13 if large else 12, color='#555'))

    # Big sales number
    f.add_annotation(text=f"<b>{fmt(actual)}</b>",
        x=0, y=0.52, xref='paper', yref='paper',
        xanchor='left', yanchor='middle', showarrow=False,
        font=dict(size=val_size, color='#1a1a2e', family='Arial Black'))

    # Comparison line: "Goal: $259K  ▲ 0.5%"
    f.add_annotation(
        text=f"{comp_label}: {fmt(comp)}   "
             f"<span style='color:{clr}'><b>{arrow} {abs(pct):.1f}%</b></span>",
        x=0, y=0.05, xref='paper', yref='paper',
        xanchor='left', yanchor='bottom', showarrow=False,
        font=dict(size=sub_size, color='#666'))

    f.update_layout(
        height=height,
        margin=dict(t=6, b=6, l=12, r=6),
        template='plotly_white',
        xaxis=dict(visible=False, range=[-0.1, 1]),
        yaxis=dict(visible=False, range=[0, 1]),
        plot_bgcolor='white', paper_bgcolor='#f8f9fb',
    )
    return f

def make_settings_html():
    """Real HTML form controls for the settings panel."""
    years  = [2020, 2021, 2022, 2023]
    months = ['January','February','March','April','May','June',
              'July','August','September','October','November','December']

    yr_opts  = '\n'.join(f'<option value="{y}" {"selected" if y==selected_year else ""}>{y}</option>' for y in years)
    mo_opts  = '\n'.join(f'<option value="{i+1}" {"selected" if i+1==selected_month else ""}>{m}</option>' for i,m in enumerate(months))

    tr_ytd   = 'checked' if time_range == 'YTD'        else ''
    tr_mo    = 'checked' if time_range == 'Month Only'  else ''
    cm_goal  = 'checked' if comparison_mode == 'vs Goal'      else ''
    cm_prior = 'checked' if comparison_mode == 'vs Prior Year' else ''

    return f"""
<div style="padding:16px;font-family:-apple-system,sans-serif;font-size:13px;color:#333">
  <div style="font-weight:700;font-size:14px;margin-bottom:16px">⚙ Settings</div>
  <form id="settings" onchange="applySettings()">

    <div style="margin-bottom:14px">
      <label style="font-weight:600;color:#555;display:block;margin-bottom:4px">Year</label>
      <select name="year" style="{sel_style}">
        {yr_opts}
      </select>
    </div>

    <div style="margin-bottom:14px">
      <label style="font-weight:600;color:#555;display:block;margin-bottom:4px">Through Month</label>
      <select name="month" style="{sel_style}">
        {mo_opts}
      </select>
    </div>

    <hr style="border:none;border-top:1px solid #ddd;margin:14px 0">

    <div style="margin-bottom:14px">
      <label style="font-weight:600;color:#555;display:block;margin-bottom:6px">Time Range</label>
      <label style="{radio_row}"><input type="radio" name="time_range" value="YTD" {tr_ytd}> &nbsp;Year-to-Date</label>
      <label style="{radio_row}"><input type="radio" name="time_range" value="Month Only" {tr_mo}> &nbsp;Month Only</label>
    </div>

    <hr style="border:none;border-top:1px solid #ddd;margin:14px 0">

    <div style="margin-bottom:14px">
      <label style="font-weight:600;color:#555;display:block;margin-bottom:6px">Compare To</label>
      <label style="{radio_row}"><input type="radio" name="comparison" value="vs Goal" {cm_goal}> &nbsp;vs Goal</label>
      <label style="{radio_row}"><input type="radio" name="comparison" value="vs Prior Year" {cm_prior}> &nbsp;vs Prior Year</label>
    </div>

  </form>
</div>
<script>
function applySettings() {{
  const f = document.getElementById('settings');
  const params = new URLSearchParams(window.location.search);
  params.set('year',       f.year.value);
  params.set('month',      f.month.value);
  params.set('time_range', f.querySelector('[name=time_range]:checked').value);
  params.set('comparison', f.querySelector('[name=comparison]:checked').value);
  window.location.search = params.toString();
}}
</script>
"""


# ── Read URL params passed via query string (for interactive preview) ─────────
import sys, urllib.parse, http.server, threading, webbrowser, os

def parse_params_from_args():
    """Allow overriding params via ?year=2022&month=3&... when served over HTTP."""
    # defaults already set above; this is used by the HTTP handler
    pass

def get_subcategory_actuals(category):
    """Get actual sales by sub-category for selected period."""
    d = orders[orders['Year'] == selected_year].copy()
    d = d[d['Category'] == category]
    d = d[d['Month'] <= selected_month] if time_range == 'YTD' else d[d['Month'] == selected_month]
    return d.groupby('Sub-Category')['Sales'].sum().sort_values(ascending=True)

def get_subcategory_full_year_comparison(category):
    """Get full-year comparison (goal or prior year) by sub-category."""
    subcats = orders[orders['Category'] == category]['Sub-Category'].unique()
    result = {}

    if comparison_mode == 'vs Goal':
        # Sum goals for all 12 months of selected year
        ym_list = [f"{selected_year}-{m:02d}" for m in range(1, 13)]
        g = goals[goals['Year-Month'].isin(ym_list)]
        g = g[g['Sub-Category'].isin(subcats)]
        for sc in subcats:
            result[sc] = g[g['Sub-Category'] == sc]['Sales_Goal'].sum()
    else:
        # Sum actual sales for all 12 months of prior year
        prior = orders[orders['Year'] == selected_year - 1].copy()
        prior = prior[prior['Category'] == category]
        for sc in subcats:
            result[sc] = prior[prior['Sub-Category'] == sc]['Sales'].sum()

    return result

def make_subcategory_chart(category, height=350, width=None):
    """Return a horizontal bar chart showing sub-categories for selected category.

    - Blue bars: actual sales for selected period
    - Gray bars: goal/prior-year for FULL YEAR (behind blue bars)
    - Dark gray line: reference point at gray bar end
    """
    actuals = get_subcategory_actuals(category)
    full_year_comps = get_subcategory_full_year_comparison(category)
    _, _, _, comp_label = get_period_totals(category)

    # Get comparison values in same order as actuals
    comp_vals = [full_year_comps.get(sc, 0) for sc in actuals.index]
    subcat_names = actuals.index.tolist()

    # Build hover text for each sub-category
    hover = []
    for sc, actual, comp in zip(subcat_names, actuals, comp_vals):
        pct = ((actual - comp) / comp * 100) if comp > 0 else 0
        arrow = '▲' if pct >= 0 else '▼'
        hover.append(
            f"<b>{sc}</b><br>"
            f"Actual ({period_label}): ${actual:,.0f}<br>"
            f"{comp_label} (Full Year): ${comp:,.0f}<br>"
            f"Difference: {arrow} {abs(pct):.1f}%"
        )

    f = go.Figure()

    # Gray bars (full-year comparison) in background
    f.add_trace(go.Bar(
        y=subcat_names, x=comp_vals,
        orientation='h',
        name=f'{comp_label} (FY)',
        marker_color='#D3D3D3',
        opacity=0.85,
        showlegend=False,
        hovertemplate='<b>%{y}</b><br>' + comp_label + ' (FY): $%{x:,.0f}<extra></extra>'
    ))

    # Blue bars (actual for selected period) in foreground
    f.add_trace(go.Bar(
        y=subcat_names, x=actuals.tolist(),
        orientation='h',
        name='Actual',
        marker_color='#6495ED',
        width=0.4,
        showlegend=False,
        hovertext=hover,
        hovertemplate='%{hovertext}<extra></extra>'
    ))

    layout_kwargs = dict(
        barmode='overlay',
        height=height,
        margin=dict(t=8, b=20, l=120, r=8),
        template='plotly_white',
        xaxis=dict(tickprefix='$', tickformat=',.0f'),
        yaxis=dict(tickfont=dict(size=11)),
    )
    if width:
        layout_kwargs['width'] = width

    f.update_layout(**layout_kwargs)
    return f

def make_bar_chart(category=None, height=280, width=None):
    """Return a standalone Figure with the overlaid bar chart."""
    actuals = get_monthly_actuals(category)
    comps   = get_monthly_comparison(category)
    _, _, _, comp_label = get_period_totals(category)

    hover = []
    for mn, actual, comp in zip(MONTH_NAMES, actuals, comps):
        pct   = ((actual - comp) / comp * 100) if comp > 0 else 0
        arrow = '▲' if pct >= 0 else '▼'
        hover.append(
            f"<b>{mn} {selected_year}</b><br>"
            f"Actual: ${actual:,.0f}<br>"
            f"{comp_label}: ${comp:,.0f}<br>"
            f"Difference: {arrow} {abs(pct):.1f}%"
        )

    f = go.Figure()
    f.add_trace(go.Bar(x=MONTH_NAMES, y=comps,
                       name=comp_label, marker_color='#D3D3D3', opacity=0.85,
                       showlegend=False,
                       hovertemplate=f'<b>%{{x}}</b><br>{comp_label}: $%{{y:,.0f}}<extra></extra>'))

    # Add customdata to blue bars if category is specified (for drill-down)
    if category:
        f.add_trace(go.Bar(x=MONTH_NAMES, y=actuals.tolist(),
                           name='Actual', marker_color=bar_colors, width=0.4,
                           customdata=[category] * len(MONTH_NAMES),
                           showlegend=False,
                           hovertext=hover, hovertemplate='%{hovertext}<extra></extra>'))
    else:
        f.add_trace(go.Bar(x=MONTH_NAMES, y=actuals.tolist(),
                           name='Actual', marker_color=bar_colors, width=0.4,
                           showlegend=False,
                           hovertext=hover, hovertemplate='%{hovertext}<extra></extra>'))

    layout_kwargs = dict(
        barmode='overlay', height=height,
        margin=dict(t=8, b=36, l=48, r=8),
        template='plotly_white',
        yaxis=dict(tickprefix='$', tickformat=',.0f'),
        xaxis=dict(tickfont=dict(size=10)),
    )
    if width:
        layout_kwargs['width'] = width
    f.update_layout(**layout_kwargs)
    return f


# ── Build HTML ────────────────────────────────────────────────────────────────
def fig_html(fig):
    return offline.plot(fig, output_type='div', include_plotlyjs=False,
                        config={'responsive': True})

plotlyjs = '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>'

html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Dashboard Preview</title>
{plotlyjs}
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, sans-serif; background: #eef0f5; margin: 0; padding: 0; }}
  .page {{ display: flex; min-height: 100vh; }}
  .sidebar {{ width: 200px; flex-shrink: 0; background: #f0f2f6;
              border-right: 1px solid #dde; overflow-y: auto; position: sticky;
              top: 0; height: 100vh; }}
  .main {{ flex: 1; overflow-y: auto; padding: 16px; min-width: 0; }}
  .header {{ font-size: 15px; font-weight: 700; color: #333; margin-bottom: 4px; }}
  .period {{ font-size: 12px; color: #888; margin-bottom: 14px; }}
  .row {{ display: flex; gap: 10px; margin-bottom: 10px; align-items: flex-start; }}
  .kpi-wrap {{ flex: 0 0 240px; }}
  .chart-wrap {{ flex: 1; min-width: 0; }}
  /* Each category block is exactly 1/3 of available width */
  .cat-block {{ flex: 1 1 0; min-width: 0; display: flex; flex-direction: column; gap: 8px; }}
  .card {{ background: white; border-radius: 8px;
           box-shadow: 0 1px 4px rgba(0,0,0,0.08); overflow: hidden; }}
  /* Force Plotly divs inside cat-block to fill their container without overflowing */
  .cat-block .card .js-plotly-plot,
  .cat-block .card .plot-container {{ width: 100% !important; }}
</style>
</head><body>
<div class="page">

  <div class="sidebar">
    {make_settings_html()}
  </div>

  <div class="main">
    <div class="header">Sales Dashboard Preview</div>
    <div class="period">Period: {period_label} &nbsp;|&nbsp; Comparison: {comparison_mode}</div>

    <!-- ROW 1 -->
    <div class="row">
      <div class="kpi-wrap">
        <div class="card">{fig_html(make_kpi_text_fig(large=True))}</div>
      </div>
      <div class="chart-wrap">
        <div class="card">{fig_html(make_bar_chart())}</div>
      </div>
    </div>

    <!-- ROW 2: category blocks -->
    <div class="row">
"""

for cat in CATEGORIES:
    html += f"""
      <div class="cat-block">
        <div class="card">{fig_html(make_kpi_text_fig(cat))}</div>
        <div class="card">{fig_html(make_bar_chart(cat, height=240))}</div>
      </div>
"""

html += """
    </div>
  </div>
</div>

<script>
// Read URL query params and restore form state on page load
(function() {
  const params = new URLSearchParams(window.location.search);
  const f = document.getElementById('settings');
  if (!f) return;
  if (params.get('year'))       f.year.value = params.get('year');
  if (params.get('month'))      f.month.value = params.get('month');
  if (params.get('time_range')) {
    const r = f.querySelector('[name=time_range][value="' + params.get('time_range') + '"]');
    if (r) r.checked = true;
  }
  if (params.get('comparison')) {
    const r = f.querySelector('[name=comparison][value="' + params.get('comparison') + '"]');
    if (r) r.checked = true;
  }
})();

// Relay form changes → Python server → regenerate page
function applySettings() {
  const f = document.getElementById('settings');
  const tr = f.querySelector('[name=time_range]:checked');
  const cm = f.querySelector('[name=comparison]:checked');
  const params = new URLSearchParams();
  params.set('year',       f.year.value);
  params.set('month',      f.month.value);
  params.set('time_range', tr ? tr.value : 'YTD');
  params.set('comparison', cm ? cm.value : 'vs Goal');
  window.location.search = params.toString();
}
</script>
</body></html>
"""

# ── Serve with a tiny HTTP server so query-string changes regenerate the page ─
PORT = 8765

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args): pass  # silence request logs

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        # Pull overrides from query string
        global selected_year, selected_month, selected_month_name, time_range, comparison_mode, selected_category
        global selected_months, bar_colors, period_label

        if 'year' in params:
            selected_year = int(params['year'][0])
        if 'month' in params:
            selected_month      = int(params['month'][0])
            selected_month_name = MONTH_NUM_TO_NAME[selected_month]
        if 'time_range' in params:
            time_range = params['time_range'][0]
        if 'comparison' in params:
            comparison_mode = params['comparison'][0]
        if 'category' in params:
            selected_category = params['category'][0] if params['category'][0] else None

        selected_months = list(range(1, selected_month + 1)) if time_range == 'YTD' else [selected_month]
        bar_colors = ['#6495ED' if m in selected_months else '#B0C4DE' for m in range(1, 13)]
        period_label = (f"Jan–{selected_month_name} {selected_year}"
                        if time_range == 'YTD' else f"{selected_month_name} {selected_year}")

        # Regenerate HTML
        page = build_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(page.encode())


def build_html():
    """Build the full dashboard HTML with current parameter values.

    Two modes:
    - Overview: Three category charts in Row 2
    - Drill-down: Expanded category with sub-category chart in Row 1, full-width category chart in Row 2
    """
    _plotlyjs = '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>'

    # ── Layout math (pixel widths) ─────────────────────────────
    # Assume 1440px viewport. Sidebar=200, main padding=32, gap=10
    VIEWPORT   = 1440
    SIDEBAR_W  = 200
    MAIN_PAD   = 32
    GAP        = 10
    main_w     = VIEWPORT - SIDEBAR_W - MAIN_PAD

    # Row 1: KPI (240px) + gap + bar chart
    kpi_w        = 240
    row1_chart_w = main_w - kpi_w - GAP

    # Row 2: 3 equal columns with 2 gaps (overview mode) OR full-width (drill-down)
    cat_w = (main_w - 2 * GAP) // 3

    body = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Dashboard Preview</title>
{_plotlyjs}
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, sans-serif; background: #eef0f5; margin: 0; padding: 0; }}
  .page {{ display: flex; min-height: 100vh; }}
  .sidebar {{ width: {SIDEBAR_W}px; flex-shrink: 0; background: #f0f2f6;
              border-right: 1px solid #dde; overflow-y: auto;
              position: sticky; top: 0; height: 100vh; }}
  .main {{ flex: 1; overflow-y: auto; padding: 16px; min-width: 0; }}
  .header {{ font-size: 15px; font-weight: 700; color: #333; margin-bottom: 4px; }}
  .header-nav {{ font-size: 13px; color: #888; margin-bottom: 14px; }}
  .back-btn {{ display: inline-block; padding: 6px 12px; background: #f0f2f6; border: 1px solid #ddd;
               border-radius: 4px; cursor: pointer; font-size: 12px; color: #555;
               text-decoration: none; margin-right: 8px; }}
  .back-btn:hover {{ background: #e0e2e6; }}
  .period {{ font-size: 12px; color: #888; margin-bottom: 14px; }}
  .row {{ display: flex; gap: {GAP}px; margin-bottom: 10px; }}
  .card {{ background: white; border-radius: 8px;
           box-shadow: 0 1px 4px rgba(0,0,0,0.08); overflow: hidden; }}
  .clickable-chart {{ cursor: pointer; }}
  .clickable-chart:hover {{ box-shadow: 0 2px 8px rgba(0,0,0,0.12); }}
</style>
</head><body>
<div class="page">
  <div class="sidebar">{make_settings_html()}</div>
  <div class="main">
    <div class="header">Sales Dashboard Preview</div>
"""

    # Navigation header for drill-down mode
    if selected_category:
        body += f"""
    <div class="header-nav">
      <a href="?" class="back-btn">← Back to Overview</a>
      <span>Viewing: <b>{selected_category}</b></span>
    </div>
"""

    body += f"""
    <div class="period">Period: {period_label} &nbsp;|&nbsp; Comparison: {comparison_mode}</div>

    <!-- ROW 1 -->
    <div class="row">
      <div style="width:{kpi_w}px; flex-shrink:0">
        <div class="card">{fig_html(make_kpi_text_fig(large=True))}</div>
      </div>
      <div style="width:{row1_chart_w}px; flex-shrink:0">
        <div class="card">"""

    # Row 1 chart: monthly bar chart (overview) or sub-category chart (drill-down)
    if selected_category:
        body += f"""{fig_html(make_subcategory_chart(selected_category, width=row1_chart_w))}"""
    else:
        body += f"""{fig_html(make_bar_chart(width=row1_chart_w))}"""

    body += """
        </div>
      </div>
    </div>

    <!-- ROW 2 -->
    <div class="row">
"""

    if selected_category:
        # Drill-down mode: full-width category chart
        body += f"""
      <div style="width:{main_w}px; flex-shrink:0">
        <div class="card" style="margin-bottom:8px">{fig_html(make_kpi_text_fig(selected_category))}</div>
        <div class="card">{fig_html(make_bar_chart(selected_category, height=240, width=main_w))}</div>
      </div>
"""
    else:
        # Overview mode: three category charts
        for cat in CATEGORIES:
            body += f"""
      <div style="width:{cat_w}px; flex-shrink:0">
        <div class="card clickable-chart" style="margin-bottom:8px; cursor:pointer"
             onclick="selectCategory('{cat}')">{fig_html(make_kpi_text_fig(cat))}</div>
        <div class="card clickable-chart" style="cursor:pointer"
             onclick="selectCategory('{cat}')">{fig_html(make_bar_chart(cat, height=240, width=cat_w))}</div>
      </div>
"""

    body += """
    </div>
  </div>
</div>

<script>
function selectCategory(category) {
  const params = new URLSearchParams(window.location.search);
  params.set('category', category);
  window.location.search = params.toString();
}
</script>
</body></html>"""
    return body


server = http.server.HTTPServer(('localhost', PORT), Handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()

url = f'http://localhost:{PORT}'
webbrowser.open(url)
print(f"✅ Interactive preview running at {url}")
print(f"   Change settings in the sidebar — the page will reload with new data.")
print(f"   Press Ctrl+C to stop.\n")
print(f"   Period: {period_label}  |  Comparison: {comparison_mode}")
for cat in [None] + CATEGORIES:
    a, c, p, lbl = get_period_totals(cat)
    arrow = '▲' if p >= 0 else '▼'
    print(f"   {cat or 'All':20s}  actual={fmt(a):>8}  {lbl}={fmt(c):>8}  {arrow} {abs(p):.1f}%")

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nStopped.")
