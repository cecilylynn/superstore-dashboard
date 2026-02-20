"""
flask_app.py — Flask Dashboard Server

This is the main entry point for the Flask version of the dashboard.
Run it with:
    python3 flask_app.py

Architecture:
  - GET /          → serves the single-page HTML app
  - GET /api/data  → returns JSON with all dashboard data for one parameter combo

The frontend (templates/index.html + static/js/dashboard.js) handles all
rendering client-side using Plotly.js.  Changing sidebar filters triggers
a fetch() call to /api/data, which returns everything needed to render
both the overview AND drill-down views in one response.

NO calculations live here — they all live in data_processing.py.
"""

from flask import Flask, render_template, request, jsonify
import data_processing as dp

# ═════════════════════════════════════════════════════════════════════════════
#  APP SETUP
# ═════════════════════════════════════════════════════════════════════════════

app = Flask(__name__)

# Load data once at startup.  This reads the Excel + CSV files and keeps
# them in memory so every API request is fast (no file I/O).
orders, goals = dp.load_data()


# ═════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    """Serve the single-page dashboard HTML."""
    return render_template('index.html')


@app.route('/api/data')
def api_data():
    """
    Return all dashboard data for one set of filter parameters.

    Query params:
        year            — e.g. 2023
        month           — e.g. 12 (1–12)
        time_range      — "YTD" or "Month Only"
        comparison_mode — "vs Goal" or "vs Prior Year"

    Returns JSON matching the same structure used by the static site's
    build.py so the JavaScript rendering code can be shared.
    """
    # ── Parse query parameters with sensible defaults ──────────────
    year = request.args.get('year', 2023, type=int)
    month = request.args.get('month', 12, type=int)
    time_range = request.args.get('time_range', 'YTD')
    comparison_mode = request.args.get('comparison_mode', 'vs Goal')

    # ── Overall (all categories combined) ──────────────────────────
    overall_actuals = dp.get_monthly_actuals(orders, year, category=None).tolist()
    overall_comps = dp.get_monthly_comparison(
        orders, goals, year, comparison_mode, category=None
    )
    overall_total = list(dp.get_period_totals(
        orders, goals, year, month, time_range, comparison_mode, category=None
    ))

    # ── Per-category data (including drill-down subcategories) ─────
    cats = {}
    for cat in dp.CATEGORIES:
        # Monthly actuals and comparisons for the bar chart
        cat_actuals = dp.get_monthly_actuals(orders, year, category=cat).tolist()
        cat_comps = dp.get_monthly_comparison(
            orders, goals, year, comparison_mode, category=cat
        )
        cat_total = list(dp.get_period_totals(
            orders, goals, year, month, time_range, comparison_mode, category=cat
        ))

        # Sub-category drill-down data
        sc_actuals = dp.get_subcategory_actuals(orders, year, month, time_range, cat)
        sc_period = dp.get_subcategory_period_comparison(
            orders, goals, year, month, time_range, comparison_mode, cat
        )
        sc_fy = dp.get_subcategory_full_year_comparison(
            orders, goals, year, comparison_mode, cat
        )

        # Build subcategory arrays in the same sorted order as actuals
        sc_names = sc_actuals.index.tolist()
        sc_actual_vals = sc_actuals.tolist()
        sc_period_vals = [sc_period.get(sc, 0) for sc in sc_names]
        sc_fy_vals = [sc_fy.get(sc, 0) for sc in sc_names]

        cats[cat] = {
            'actuals': cat_actuals,
            'comps': cat_comps,
            'total': cat_total,
            'subcats': {
                'names': sc_names,
                'actuals': sc_actual_vals,
                'period_comps': sc_period_vals,
                'fy_comps': sc_fy_vals,
            }
        }

    # ── Build response ─────────────────────────────────────────────
    # Round floats to 2 decimal places to keep JSON compact
    result = {
        'overall_actuals': [round(v, 2) for v in overall_actuals],
        'overall_comps': [round(v, 2) for v in overall_comps],
        'overall_total': [
            round(overall_total[0], 2),  # actual
            round(overall_total[1], 2),  # comp
            round(overall_total[2], 2),  # pct
            overall_total[3],            # label (string)
        ],
        'cats': {}
    }

    for cat, c in cats.items():
        result['cats'][cat] = {
            'actuals': [round(v, 2) for v in c['actuals']],
            'comps': [round(v, 2) for v in c['comps']],
            'total': [
                round(c['total'][0], 2),
                round(c['total'][1], 2),
                round(c['total'][2], 2),
                c['total'][3],
            ],
            'subcats': {
                'names': c['subcats']['names'],
                'actuals': [round(v, 2) for v in c['subcats']['actuals']],
                'period_comps': [round(v, 2) for v in c['subcats']['period_comps']],
                'fy_comps': [round(v, 2) for v in c['subcats']['fy_comps']],
            }
        }

    return jsonify(result)


# ═════════════════════════════════════════════════════════════════════════════
#  RUN
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("Starting Flask dashboard on http://localhost:5001")
    app.run(debug=True, port=5001)
