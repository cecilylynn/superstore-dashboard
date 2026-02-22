/**
 * dashboard.js — Client-side logic for the Flask Sales Dashboard
 *
 * This file handles:
 *   - Reading sidebar filter values
 *   - Fetching data from the Flask API (/api/data)
 *   - Rendering KPI cards as HTML
 *   - Rendering Plotly bar charts (monthly + subcategory)
 *   - Drill-down navigation (overview ↔ category detail)
 *
 * The chart-rendering functions are adapted from the static site's
 * build.py / index.html, which are proven to work correctly.
 */


// ═════════════════════════════════════════════════════════════════════════════
//  CONSTANTS
// ═════════════════════════════════════════════════════════════════════════════
// These match the Python color constants in chart_builders.py

// Read accent blue from CSS custom property so one change updates both
// the KPI big-number text color (CSS) and the chart bar color (JS).
const BLUE = getComputedStyle(document.documentElement)
                 .getPropertyValue('--accent-blue').trim() || '#6495ED';
const PALE_BLUE  = '#B0C4DE';   // Actual sales bars (unselected months)
const LIGHT_GRAY = '#D3D3D3';   // Comparison bars (goal or prior year)
const DARK_GRAY  = '#555555';   // Full-year reference lines on subcategory chart

const CATEGORIES = ['Furniture', 'Office Supplies', 'Technology'];
const MONTH_NAMES   = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const MONTH_LETTERS = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'];
const MONTH_FULL = ['January', 'February', 'March', 'April', 'May', 'June',
                    'July', 'August', 'September', 'October', 'November', 'December'];


// ═════════════════════════════════════════════════════════════════════════════
//  STATE
// ═════════════════════════════════════════════════════════════════════════════
// null = overview mode, string = drill-down into that category

let selectedCategory = null;

// Cached API response so drill-down doesn't need a new fetch
let currentData = null;


// ═════════════════════════════════════════════════════════════════════════════
//  HELPERS
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Format a dollar amount into an abbreviated string for display.
 * Matches the Python fmt() function in data_processing.py.
 *
 * Examples:
 *   2600000 → "$2.6M"
 *   260000  → "$260K"
 *   26500   → "$26.5K"
 *   260     → "$260"
 */
function fmt(v) {
    const a = Math.abs(v);
    if (a >= 1e8) return '$' + (v / 1e6).toFixed(0) + 'M';
    if (a >= 1e7) return '$' + (v / 1e6).toFixed(1) + 'M';
    if (a >= 1e6) return '$' + (v / 1e6).toFixed(1) + 'M';
    if (a >= 1e5) return '$' + (v / 1e3).toFixed(0) + 'K';
    if (a >= 1e4) return '$' + (v / 1e3).toFixed(1) + 'K';
    if (a >= 1e3) return '$' + (v / 1e3).toFixed(1) + 'K';
    return '$' + v.toFixed(0);
}

/**
 * Read the current sidebar filter values and return them as an object.
 */
function getParams() {
    return {
        year:  +document.getElementById('sel-year').value,
        month: +document.getElementById('sel-month').value,
        tr:    document.querySelector('[name=time_range]:checked').value,
        cm:    document.querySelector('[name=comp_mode]:checked').value,
    };
}

/**
 * Build a human-readable period label like "Jan–June 2023" or "June 2023".
 */
function periodLabel(p) {
    if (p.tr === 'YTD') {
        return 'Jan\u2013' + MONTH_FULL[p.month - 1] + ' ' + p.year;
    }
    return MONTH_FULL[p.month - 1] + ' ' + p.year;
}

/**
 * Build an array of 12 bar colors: blue for selected months, pale blue for others.
 */
function barColors(p) {
    const selected = p.tr === 'YTD'
        ? Array.from({length: p.month}, (_, i) => i + 1)
        : [p.month];
    return Array.from({length: 12}, (_, i) =>
        selected.includes(i + 1) ? BLUE : PALE_BLUE
    );
}


// ═════════════════════════════════════════════════════════════════════════════
//  KPI CARD RENDERING
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Render a KPI card into the given DOM element.
 *
 * Args:
 *   el     — the DOM element to fill with HTML
 *   title  — card heading ("TOTAL SALES" or a category name)
 *   total  — array of [actual, comp, pct, label] from the API
 *   plabel — period label like "Jan–Dec 2023"
 *   large  — true for the big primary KPI (Row 1)
 */
function renderKPI(el, title, total, plabel, large) {
    const [actual, comp, pct, label] = total;
    const arrow = pct >= 0 ? '\u25B2' : '\u25BC';
    const cls   = pct >= 0 ? 'kpi-up' : 'kpi-down';

    // Three lines: combined header | big dollar value | comparison
    el.innerHTML =
        '<div class="kpi-header">' + title + ' \u2013 ' + plabel + ' Revenue</div>' +
        '<div class="kpi-value' + (large ? ' large' : '') + '">' + fmt(actual) + '</div>' +
        '<div class="kpi-comp">' + label + ': ' + fmt(comp) +
        '  <span class="' + cls + '">' + arrow + ' ' + Math.abs(pct).toFixed(1) + '%</span>' +
        '</div>';
}


// ═════════════════════════════════════════════════════════════════════════════
//  CHART RENDERING — Monthly vertical bar chart
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Render a vertical bar chart (Jan–Dec) into the given div.
 *
 * Two layers overlaid:
 *   1. Gray bars (back)  = comparison (goal or prior year)
 *   2. Colored bars (front) = actual sales
 *
 * Args:
 *   divId     — ID of the chart container div
 *   actuals   — array of 12 actual sales values
 *   comps     — array of 12 comparison values
 *   compLabel — "Goal" or "2022"
 *   colors    — array of 12 color strings (blue or pale blue)
 *   height    — chart height in pixels (null = fill container)
 *   xLabels   — optional array of 12 tick labels (e.g. MONTH_LETTERS for category charts)
 */
function plotBarChart(divId, actuals, comps, compLabel, colors, height, xLabels) {
    const p = getParams();

    // Build hover text for each month showing actual, comparison, and % difference
    const hoverTexts = MONTH_NAMES.map((mn, i) => {
        const pct = comps[i] > 0 ? ((actuals[i] - comps[i]) / comps[i] * 100) : 0;
        const arrow = pct >= 0 ? '\u25B2' : '\u25BC';
        return '<b>' + mn + ' ' + p.year + '</b><br>' +
               'Actual: $' + actuals[i].toLocaleString('en-US', {maximumFractionDigits: 0}) + '<br>' +
               compLabel + ': $' + comps[i].toLocaleString('en-US', {maximumFractionDigits: 0}) + '<br>' +
               'Difference: ' + arrow + ' ' + Math.abs(pct).toFixed(1) + '%';
    });

    const traces = [
        // Layer 1: Gray comparison bars (wider, behind)
        {
            x: MONTH_NAMES, y: comps, type: 'bar', name: compLabel,
            marker: {color: LIGHT_GRAY}, opacity: 0.85, showlegend: false,
            hovertemplate: MONTH_NAMES.map((mn, i) =>
                '<b>' + mn + '</b><br>' + compLabel + ': $' +
                comps[i].toLocaleString('en-US', {maximumFractionDigits: 0}) +
                '<extra></extra>'
            ),
        },
        // Layer 2: Colored actual bars (narrower, in front)
        {
            x: MONTH_NAMES, y: actuals, type: 'bar', name: 'Actual',
            marker: {color: colors}, width: 0.4, showlegend: false,
            hovertext: hoverTexts,
            hovertemplate: '%{hovertext}<extra></extra>',
        },
    ];

    // Compute chart dimensions from container element.
    // Reading clientWidth/clientHeight forces a synchronous layout reflow,
    // ensuring the flex-computed sizes are available.
    var el = document.getElementById(divId);
    var chartWidth  = el.clientWidth  || el.parentElement.clientWidth  || 600;
    var chartHeight = height || el.clientHeight || el.parentElement.clientHeight || 300;

    const layout = {
        barmode: 'overlay',
        width: chartWidth,
        height: chartHeight,
        // Margins zeroed — spacing is controlled by CSS containers.
        // automargin on each axis lets Plotly expand only as needed for tick labels.
        margin: {t: 0, b: 0, l: 0, r: 0},
        template: 'plotly_white',
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {family: 'Open Sans, sans-serif'},
        yaxis: {
            tickformat: '$~s',
            tickfont: {size: 12, color: '#888'},
            showgrid: false,
            automargin: true,
        },
        xaxis: Object.assign(
            {tickfont: {size: 11, color: '#888'}, automargin: true},
            xLabels ? {tickvals: MONTH_NAMES, ticktext: xLabels} : {}
        ),
        hoverlabel: {bgcolor: 'white', font: {size: 12}, bordercolor: '#ddd'},
    };

    Plotly.react(divId, traces, layout, {responsive: true, displayModeBar: false});
}


// ═════════════════════════════════════════════════════════════════════════════
//  CHART RENDERING — Subcategory horizontal bar chart (drill-down)
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Render a horizontal bar chart showing subcategories within one category.
 *
 * Three layers:
 *   1. Gray bars     = comparison for the SELECTED PERIOD
 *   2. Blue bars     = actual sales for the SELECTED PERIOD
 *   3. Dark lines    = full-year comparison (reference markers)
 *
 * Args:
 *   divId     — ID of the chart container div
 *   sc        — subcategory data object {names, actuals, period_comps, fy_comps}
 *   compLabel — "Goal" or "2022"
 *   plabel    — period label like "Jan–Jun 2023"
 *   year      — selected year number
 */
function plotSubcatChart(divId, sc, compLabel, plabel, year) {
    const names      = sc.names;
    const actuals    = sc.actuals;
    const periodComps = sc.period_comps;
    const fyComps    = sc.fy_comps;

    // Build hover text for each subcategory
    const hoverTexts = names.map((name, i) => {
        const pct = periodComps[i] > 0
            ? ((actuals[i] - periodComps[i]) / periodComps[i] * 100)
            : 0;
        const arrow = pct >= 0 ? '\u25B2' : '\u25BC';
        return '<b>' + name + '</b><br>' +
               'Actual (' + plabel + '): $' + actuals[i].toLocaleString('en-US', {maximumFractionDigits: 0}) + '<br>' +
               compLabel + ' (' + plabel + '): $' + periodComps[i].toLocaleString('en-US', {maximumFractionDigits: 0}) + '<br>' +
               'Difference: ' + arrow + ' ' + Math.abs(pct).toFixed(1) + '%<br>' +
               compLabel + ' (Full Year ' + year + '): $' + fyComps[i].toLocaleString('en-US', {maximumFractionDigits: 0});
    });

    const traces = [
        // Layer 1: Gray period comparison bars (wider, behind)
        {
            y: names, x: periodComps, type: 'bar', orientation: 'h',
            name: compLabel, marker: {color: LIGHT_GRAY}, opacity: 0.85,
            showlegend: false,
            hovertemplate: names.map((n, i) =>
                '<b>' + n + '</b><br>' + compLabel + ' (' + plabel + '): $' +
                periodComps[i].toLocaleString('en-US', {maximumFractionDigits: 0}) +
                '<extra></extra>'
            ),
        },
        // Layer 2: Blue actual bars (narrower, in front)
        {
            y: names, x: actuals, type: 'bar', orientation: 'h',
            name: 'Actual', marker: {color: BLUE}, width: 0.4,
            showlegend: false,
            hovertext: hoverTexts,
            hovertemplate: '%{hovertext}<extra></extra>',
        },
    ];

    // Layer 3: Dark gray reference lines for full-year comparison
    const shapes = fyComps.map((fy, i) => fy > 0 ? {
        type: 'line', x0: fy, x1: fy, y0: i - 0.4, y1: i + 0.4,
        line: {color: DARK_GRAY, width: 2}, layer: 'above',
    } : null).filter(Boolean);

    // Compute chart dimensions from container element
    var el = document.getElementById(divId);
    var chartWidth  = el.clientWidth  || el.parentElement.clientWidth  || 600;
    var chartHeight = el.clientHeight || el.parentElement.clientHeight || 400;

    const layout = {
        barmode: 'overlay',
        width: chartWidth,
        height: chartHeight,
        // t/b/r zeroed. l must be non-zero so annotation labels have physical
        // space to render — sized to fit the longest subcategory name at 12px.
        margin: {t: 0, b: 0, l: 110, r: 0},
        template: 'plotly_white',
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {family: 'Open Sans, sans-serif'},
        xaxis: {
            tickformat: '$~s',
            tickfont: {size: 12, color: '#888'},
            showgrid: false,
            automargin: true,
        },
        yaxis: {
            showticklabels: false,
        },
        shapes: shapes,
        // Left-aligned subcategory labels via annotations (native tick labels
        // would be right-aligned; annotations let us left-align at a fixed column).
        annotations: names.map(function(name) {
            return {
                xref: 'paper', yref: 'y',
                x: 0, y: name,
                text: name,
                showarrow: false,
                xanchor: 'left',
                xshift: -105,   // margin.l is 110, leaves 5px left padding
                font: {size: 12, color: '#555', family: 'Open Sans, sans-serif'},
            };
        }),
        hoverlabel: {bgcolor: 'white', font: {size: 12}, bordercolor: '#ddd'},
    };

    Plotly.react(divId, traces, layout, {responsive: true, displayModeBar: false});
}


// ═════════════════════════════════════════════════════════════════════════════
//  DATA FETCHING
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Fetch dashboard data from the Flask API for the current filter params.
 * Returns a Promise that resolves with the JSON response.
 */
function fetchData(p) {
    const url = '/api/data?' +
        'year=' + p.year +
        '&month=' + p.month +
        '&time_range=' + encodeURIComponent(p.tr) +
        '&comparison_mode=' + encodeURIComponent(p.cm);

    return fetch(url).then(function(response) {
        return response.json();
    });
}


// ═════════════════════════════════════════════════════════════════════════════
//  MAIN UPDATE — orchestrates fetching + rendering
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Main update function.  Called whenever:
 *   - A sidebar filter changes (via onchange="update()")
 *   - User clicks into a category (selectCategory)
 *   - User clicks "Back to Overview" (goBack)
 *
 * If the filter params changed, fetches new data from the API.
 * If only the view mode changed (overview ↔ drill-down), reuses cached data.
 */
function update(forceRefetch) {
    const p = getParams();
    const plabel = periodLabel(p);
    const colors = barColors(p);

    // Update the year display in the title bar
    document.getElementById('title-year').textContent = 'FY ' + p.year;

    // Decide whether we need fresh data or can use the cache
    if (forceRefetch !== false || currentData === null) {
        fetchData(p).then(function(data) {
            currentData = data;
            render(p, plabel, colors);
        });
    } else {
        render(p, plabel, colors);
    }
}

/**
 * Render the dashboard using currentData.  Called after data is loaded.
 *
 * Uses requestAnimationFrame to defer Plotly rendering until the browser
 * has computed flex layout — ensures chart containers have real dimensions.
 */
function render(p, plabel, colors) {
    const d = currentData;
    if (!d) return;

    const compLabel = d.overall_total[3];

    if (selectedCategory === null) {
        // ── OVERVIEW MODE ─────────────────────────────────────────

        // Hide the sidebar back button
        document.getElementById('sidebar-back').style.display = 'none';
        document.getElementById('sidebar-back-hr').style.display = 'none';

        // Row 1: Overall KPI + overall bar chart
        renderKPI(document.getElementById('kpi-main'), 'TOTAL SALES',
                  d.overall_total, plabel, true);

        // Chart title — styled with bar colors
        document.getElementById('chart-main-label').innerHTML =
            'Total Revenue ' + plabel + ' \u2013 ' +
            '<span style="color:' + BLUE + '; font-weight:700;">Actuals</span>' +
            ' vs ' +
            '<span style="color:' + LIGHT_GRAY + '; font-weight:700;">' + compLabel + '</span>';

        // Row 2: Three category panels (clicking any card drills down)
        // Each category is ONE unified card (.cat-column):
        //   - KPI div acts as the card header (no card styling of its own)
        //   - chart div fills the remaining card height
        //   - onclick on the whole column — no separate clickable inner elements
        var row2Html = '<div class="row" style="height: 100%; gap: 12px;">';
        CATEGORIES.forEach(function(cat, i) {
            row2Html +=
                '<div class="cat-column" onclick="selectCategory(\'' + cat + '\')">' +
                    '<div class="kpi" id="kpi-cat-' + i + '"></div>' +
                    '<div class="cat-chart">' +
                        '<div class="chart-card-inner">' +
                            '<div id="chart-cat-' + i + '" class="chart-container"></div>' +
                        '</div>' +
                    '</div>' +
                '</div>';
        });
        row2Html += '</div>';
        document.getElementById('row2').innerHTML = row2Html;

        // Defer Plotly calls so the browser computes flex layout first.
        // Double-rAF ensures style + layout are fully resolved before we
        // read container dimensions inside the chart functions.
        requestAnimationFrame(function() {
        requestAnimationFrame(function() {
            // Overall bar chart in Row 1
            plotBarChart('chart-main', d.overall_actuals, d.overall_comps,
                         compLabel, colors, null);

            // Each category's KPI card and chart in Row 2
            CATEGORIES.forEach(function(cat, i) {
                var c = d.cats[cat];
                renderKPI(document.getElementById('kpi-cat-' + i), cat,
                          c.total, plabel, false);
                plotBarChart('chart-cat-' + i, c.actuals, c.comps,
                             compLabel, colors, null, MONTH_LETTERS);
            });
        });
        });

    } else {
        // ── DRILL-DOWN MODE ───────────────────────────────────────

        // Show the sidebar back button
        document.getElementById('sidebar-back').style.display = 'block';
        document.getElementById('sidebar-back-hr').style.display = 'block';
        document.getElementById('nav-label').innerHTML =
            'Viewing: <b>' + selectedCategory + '</b>';

        var c = d.cats[selectedCategory];

        // Row 1: Total Sales KPI (persistent) + subcategory chart
        renderKPI(document.getElementById('kpi-main'), 'TOTAL SALES',
                  d.overall_total, plabel, true);

        // Chart title — two lines: main title + full-year reference note
        document.getElementById('chart-main-label').innerHTML =
            selectedCategory + ' Revenue ' + plabel + ' \u2013 ' +
            '<span style="color:' + BLUE + '; font-weight:700;">Actuals</span>' +
            ' vs ' +
            '<span style="color:' + LIGHT_GRAY + '; font-weight:700;">' + compLabel + '</span>' +
            '<br><span style="font-size:12px; color:#555;">Total ' + compLabel + ' (full year) indicated by ' +
            '<span style="color:' + DARK_GRAY + '; font-weight:700;">|</span></span>';

        // Row 2: Single unified card — Category KPI header + monthly trend chart.
        // Mirrors the .cat-column pattern from overview: one card wraps both,
        // no internal borders or shadows, overflow:hidden clips to rounded corners.
        document.getElementById('row2').innerHTML =
            '<div class="cat-column" style="height: 100%;" onclick="goBack()">' +
                '<div class="kpi" id="kpi-drilldown-cat"></div>' +
                '<div class="cat-chart">' +
                    '<div class="chart-card-inner">' +
                        '<div id="chart-drilldown" class="chart-container"></div>' +
                    '</div>' +
                '</div>' +
            '</div>';

        // Render the category KPI
        renderKPI(document.getElementById('kpi-drilldown-cat'), selectedCategory,
                  c.total, plabel, false);

        // Defer Plotly calls — double-rAF for layout computation
        requestAnimationFrame(function() {
        requestAnimationFrame(function() {
            plotSubcatChart('chart-main', c.subcats, compLabel, plabel, p.year);
            plotBarChart('chart-drilldown', c.actuals, c.comps,
                         compLabel, colors, null);
        });
        });
    }
}


// ═════════════════════════════════════════════════════════════════════════════
//  NAVIGATION — drill-down into a category / back to overview
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Enter drill-down mode for the given category.
 * Reuses cached data (no new API call needed).
 */
function selectCategory(cat) {
    selectedCategory = cat;
    update(false);  // false = don't refetch, reuse cached data
}

/**
 * Return to overview mode.
 * Reuses cached data (no new API call needed).
 */
function goBack() {
    selectedCategory = null;
    update(false);  // false = don't refetch, reuse cached data
}


// ═════════════════════════════════════════════════════════════════════════════
//  INITIAL RENDER — load data and draw the dashboard
// ═════════════════════════════════════════════════════════════════════════════

// Default the month selector to the current calendar month
document.getElementById('sel-month').value = new Date().getMonth() + 1;

update();

// Re-render on window resize so charts match their new container sizes.
// Debounced to 150 ms so we don't re-render on every pixel of a drag-resize.
var _resizeTimer;
window.addEventListener('resize', function() {
    clearTimeout(_resizeTimer);
    _resizeTimer = setTimeout(function() {
        if (currentData) {
            var p = getParams();
            render(p, periodLabel(p), barColors(p));
        }
    }, 150);
});
