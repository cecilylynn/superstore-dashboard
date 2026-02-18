# Dashboard Architecture - Interactive Drill-Down Feature

## System Overview

```
                    ┌─────────────────┐
                    │  User's Browser │
                    │  (localhost:    │
                    │   8765)         │
                    └────────┬────────┘
                             │ HTTP GET with URL params
                             │ ?year=2023&month=6
                             │ &time_range=YTD
                             │ &comparison=vs Goal
                             │ &category=Furniture
                             ▼
                    ┌─────────────────────────┐
                    │ Python HTTP Server      │
                    │ (Handler.do_GET)        │
                    │                         │
                    │ 1. Parse URL params     │
                    │ 2. Update globals       │
                    │ 3. Regenerate HTML      │
                    │ 4. Send response        │
                    └────────┬────────────────┘
                             │
                             ▼
        ┌────────────────────────────────────┐
        │ Dashboard Generation Pipeline      │
        │                                    │
        │ build_html() {                     │
        │   ├─ Check: overview or           │
        │   │          drill-down mode?     │
        │   │                               │
        │   ├─ ROW 1:                       │
        │   │   ├─ make_kpi_text_fig()      │
        │   │   └─ make_bar_chart() OR      │
        │   │      make_subcategory_        │
        │   │      chart()                  │
        │   │                               │
        │   └─ ROW 2:                       │
        │       ├─ (overview) 3x            │
        │       │  make_bar_chart()         │
        │       │  with onclick handlers    │
        │       │                           │
        │       └─ (drill-down) 1x          │
        │          make_bar_chart()         │
        │          full-width               │
        │                                   │
        └────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────────┐
                    │ HTML Response       │
                    │ + JavaScript        │
                    │ + Plotly Charts     │
                    └────────┬────────────┘
                             │
                             ▼
                    ┌─────────────────────────┐
                    │ Browser Renders HTML    │
                    │                         │
                    │ JavaScript loads:       │
                    │ - selectCategory()      │
                    │ - applySettings()       │
                    │ - Plotly library        │
                    │                         │
                    └────────┬────────────────┘
                             │ User clicks category card
                             │ OR adjusts settings
                             │
                             └─► Back to start (HTTP GET)
```

## Data Flow Architecture

```
Global State Variables (parameters)
├─ selected_year = 2023
├─ selected_month = 6
├─ selected_month_name = 'June'
├─ time_range = 'YTD'
├─ comparison_mode = 'vs Goal'
└─ selected_category = 'Furniture' (NEW)
         │
         ▼ These globals are used by all data functions
    ┌──────────────────────────────┐
    │ Data Aggregation Functions   │
    │                              │
    │ For Monthly Charts:          │
    │ ├─ get_monthly_actuals()     │
    │ ├─ get_monthly_comparison()  │
    │ └─ get_period_totals()       │
    │                              │
    │ For Sub-Category Charts:     │
    │ ├─ get_subcategory_          │ (NEW)
    │ │  actuals()                 │
    │ ├─ get_subcategory_          │ (NEW)
    │ │  full_year_comparison()    │
    │ └─ (reuses get_period_       │
    │    totals())                 │
    └────────────┬─────────────────┘
                 │
         ┌───────┴────────┐
         ▼                ▼
    ┌────────────┐   ┌──────────────┐
    │ Plotly     │   │ Plotly       │
    │ Bar Chart  │   │ Horizontal   │
    │ Figures    │   │ Bar Chart    │
    │            │   │ Figures      │
    │ (Vertical  │   │              │
    │ bars)      │   │ (NEW)        │
    └────────────┘   └──────────────┘
         │                │
         └────────┬───────┘
                  ▼
         ┌────────────────┐
         │ Convert to     │
         │ HTML with      │
         │ offline.plot() │
         └────────────────┘
                  │
                  ▼
         ┌────────────────────┐
         │ Embed in HTML page │
         │ with event         │
         │ handlers           │
         └────────────────────┘
```

## View Mode State Machine

```
                        START
                         │
                         ▼
            ┌────────────────────────┐
            │ URL: no category       │
            │ selected_category=None │
            └────────────┬───────────┘
                         │
                    OVERVIEW MODE
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
    ┌────────┐      ┌────────┐      ┌────────┐
    │Furni   │      │Office  │      │Tech    │
    │ture   │      │ Sup.   │      │nology  │
    │ (click)│      │(click) │      │(click) │
    └───┬────┘      └───┬────┘      └───┬────┘
        │               │               │
        └───────────────┼───────────────┘
                        │ selectCategory(cat)
                        │ URL: ?...&category=Furniture
                        ▼
            ┌────────────────────────┐
            │ URL: category set      │
            │ selected_category=     │
            │ 'Furniture'            │
            └────────────┬───────────┘
                         │
                   DRILL-DOWN MODE
                   (Single Category)
                         │
                         │ "Back to Overview"
                         │ OR ?...&category=
                         │ (clears category)
                         │
                         ▼
                    Returns to
                    OVERVIEW MODE
```

## Sub-Category Chart Data Pipeline

```
Input Parameters:
  - selected_year (2023)
  - selected_month (6)
  - time_range ('YTD')
  - comparison_mode ('vs Goal')
  - selected_category ('Furniture')

        │
        ▼
┌───────────────────────────────┐
│ get_subcategory_actuals()     │
│                               │
│ Filter: Year=2023,            │
│         Category=Furniture,    │
│         Month <= 6 (if YTD)    │
│                               │
│ Result: Series([              │
│   'Bookcase': 12000,           │
│   'Cabinets': 28500,           │
│   'Chairs': 45200,             │
│   'Desks': 62100,              │
│   'Tables': 18200              │
│ ])                             │
└────────────┬──────────────────┘
             │
        ┌────┴─────┐
        │           │
        ▼           ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ get_subcategory_full_year_   │  │ make_subcategory_chart()     │
│ comparison()                 │  │                              │
│                              │  │ Input: actuals (blue bars)   │
│ If comparison='vs Goal':     │  │        comp_vals (gray bars) │
│ ├─ Sum all goals for         │  │                              │
│ │  months 1-12 of 2023       │  │ Output: Plotly Figure        │
│ │  by sub-category           │  │ - Horizontal bars layout     │
│ │                            │  │ - Overlaid gray + blue       │
│ If comparison='vs Prior Year'│  │ - Hover tooltips             │
│ └─ Sum all actual sales      │  │ - Currency formatting        │
│   for months 1-12 of 2022    │  │                              │
│   by sub-category           │  │                              │
│                              │  │                              │
│ Result: Dict({               │  └──────────────────────────────┘
│   'Bookcase': 85000,         │
│   'Cabinets': 125000,        │
│   'Chairs': 210000,          │
│   'Desks': 285000,           │
│   'Tables': 95000            │
│ })                           │
└────────────────────────────────┘
```

## HTML Generation by Mode

### Overview Mode (selected_category = None)

```
Header: "Sales Dashboard Preview"
         Period: Jan-Jun 2023 | Comparison: vs Goal

ROW 1:
┌────────────┬───────────────────────────────┐
│ KPI Card   │ Monthly Bar Chart              │
│ (Total     │ (Vertical bars, all categories)│
│  Sales)    │                               │
└────────────┴───────────────────────────────┘

ROW 2:
┌──────────┬──────────────┬─────────────┐
│Furniture │ Office Sup.  │ Technology  │
├──────────┼──────────────┼─────────────┤
│KPI Card  │ KPI Card     │ KPI Card    │
├──────────┼──────────────┼─────────────┤
│Monthly   │ Monthly      │ Monthly     │
│Bar Chart │ Bar Chart    │ Bar Chart   │
│(Blue/    │ (Blue/       │ (Blue/      │
│Gray, 6mo)│ Gray, 6mo)   │ Gray, 6mo)  │
│          │              │             │
│[onclick: │ [onclick:    │ [onclick:   │
│ select   │  select      │  select     │
│ Furn.]   │  Office]     │  Tech]      │
└──────────┴──────────────┴─────────────┘
```

All category cards have `onclick="selectCategory('{category}')"` handler.

### Drill-Down Mode (selected_category = 'Furniture')

```
Header: [← Back to Overview] Viewing: Furniture
         Period: Jan-Jun 2023 | Comparison: vs Goal

ROW 1:
┌────────────┬──────────────────────────┐
│ KPI Card   │ Sub-Category Chart        │
│ (Furniture │ (Horizontal bars:         │
│  Sales)    │  Bookcase, Cabinets,      │
│            │  Chairs, Desks, Tables)   │
│            │ (Blue=actual, Gray=FY)    │
└────────────┴──────────────────────────┘

ROW 2:
┌─────────────────────────────────────┐
│ Furniture KPI Card                  │
├─────────────────────────────────────┤
│ Monthly Bar Chart (full width)       │
│ All 12 months, blue/gray overlay    │
│ Jan-Jun highlighted blue,           │
│ Jul-Dec paler blue                  │
└─────────────────────────────────────┘
```

No click handlers on charts (can't drill down further).

## CSS Layout System

```
Fixed Pixel Widths (1440px viewport assumption):

VIEWPORT = 1440px
│
├─ SIDEBAR = 200px (fixed)
│
└─ MAIN = 1168px
   ├─ PADDING = 32px (total: 16px left + 16px right)
   │
   └─ MAIN_CONTENT_WIDTH = 1136px
      │
      ├─ ROW 1:
      │  ├─ KPI_WIDTH = 240px (fixed)
      │  ├─ GAP = 10px
      │  └─ CHART_WIDTH = 886px (responsive)
      │
      └─ ROW 2:
         ├─ Overview: 3 equal columns
         │  ├─ CAT_WIDTH = 368px each
         │  └─ GAP = 10px between columns
         │
         └─ Drill-down: full width
            └─ CHART_WIDTH = 1136px
```

Explicit pixel widths prevent overflow issues with Plotly charts.

## Key Design Decisions

### 1. **Global State Variables**
- Simplifies parameter passing through deep function calls
- Updated by HTTP handler based on URL query string
- All visualization functions read from these globals

### 2. **Two Data Sets for Comparison**
- **Selected period actuals:** Filtered by year, month, time_range
- **Full-year comparison:** Always includes all 12 months
- Allows "pace" analysis (are we on track for full year?)

### 3. **View Mode State in URL**
- `selected_category=None` → Overview (default)
- `selected_category=Furniture` → Drill-down
- Bookmarkable URLs
- Back button in browser works naturally

### 4. **Plotly Figure Reuse**
- Single `fig_html()` function converts all figures
- Consistent look and feel
- Easy to add new chart types

### 5. **Server Regeneration on Parameter Change**
- Browser sets URL parameter via JavaScript
- Page reloads (HTTP GET with new params)
- Server recalculates all data and regenerates HTML
- Ensures data consistency (no stale state)

## Performance Characteristics

### Data Loading
- Excel file loaded once at startup (10,194 rows, ~50MB)
- Goals CSV loaded once (816 rows, ~50KB)
- Both held in memory throughout execution

### Per Request (HTTP GET)
- Parse URL parameters: ~1ms
- Aggregate data by sub-category/month: ~10-50ms (depending on filters)
- Generate Plotly figures: ~100-200ms (JSON serialization)
- Render HTML: ~10-20ms
- **Total:** ~150-300ms per request

### Optimization Opportunities
- Cache aggregated data for common parameter combinations
- Pre-generate figures at startup
- Use WebSocket for real-time parameter updates (no page reload)

---

**Last Updated:** After implementing interactive drill-down feature
