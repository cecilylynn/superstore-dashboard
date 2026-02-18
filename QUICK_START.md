# Quick Start: Interactive Dashboard with Drill-Down

## Running the Dashboard

```bash
cd /Users/cecilysantiago/Documents/Claude\ Code\ Playground/.claude/worktrees/compassionate-shaw
python3 preview_charts.py
```

Expected output:
```
✅ Interactive preview running at http://localhost:8765
   Change settings in the sidebar — the page will reload with new data.
   Press Ctrl+C to stop.

   Period: Jan–June 2023  |  Comparison: vs Goal
   All                    actual=$831.7K  Goal=$852.3K  ▼ 2.4%
   Furniture              actual=$174.7K  Goal=$175.8K  ▼ 0.6%
   Office Supplies        actual=$283.8K  Goal=$289.7K  ▼ 2.0%
   Technology            actual=$373.2K  Goal=$386.8K  ▼ 3.5%
```

Browser will open automatically at `http://localhost:8765`

## Dashboard Features

### Overview (Default View)

Shows all three product categories side-by-side:

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│ Left Panel (Settings)          Main Panel (Charts)          │
│ ───────────────────            ──────────────────            │
│                                                              │
│ ⚙ Settings                     Sales Dashboard              │
│                                Period: Jan-June | vs Goal    │
│ Year:                                                        │
│ [2023 ▼]                       ┌────────┐ ┌─────────────┐   │
│                                │KPI     │ │Monthly Sales│   │
│ Through Month:                 │Card    │ │Chart (All)  │   │
│ [June ▼]                       └────────┘ └─────────────┘   │
│                                                              │
│ Time Range:                    ┌────────┬────────┬────────┐ │
│ ○ Year-to-Date                 │Furn    │Office  │Tech    │ │
│ ○ Month Only                   ├────────┼────────┼────────┤ │
│                                │KPI     │KPI     │KPI     │ │
│ Compare To:                    ├────────┼────────┼────────┤ │
│ ○ vs Goal                      │Monthly │Monthly │Monthly │ │
│ ○ vs Prior Year                │Chart   │Chart   │Chart   │ │
│                                │        │        │        │ │
│                                │[CLICK] │[CLICK] │[CLICK] │ │
│                                └────────┴────────┴────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**To drill down:** Click any category card

### Drill-Down Mode (After Clicking Category)

Shows one category with sub-category breakdown:

```
┌──────────────────────────────────────────────────────────────┐
│ [← Back] Viewing: Furniture                                  │
│                                                              │
│ ┌────────┐ ┌──────────────────────────────────────────────┐ │
│ │KPI     │ │Sub-Categories (Horizontal Bars)              │ │
│ │Card    │ │  Desks      ║─────────────────── (Blue)     │ │
│ │        │ │             ║────────────── (Gray)           │ │
│ │        │ │  Chairs     ║───────────────── (Blue)      │ │
│ │        │ │             ║──────────────────── (Gray)    │ │
│ │        │ │  Cabinets   ║────────── (Blue)             │ │
│ │        │ │             ║──────────────────── (Gray)    │ │
│ │        │ │  Bookcase   ║────── (Blue)                 │ │
│ │        │ │             ║──────────────────── (Gray)    │ │
│ │        │ │  Tables     ║── (Blue) [maybe red box]    │ │
│ │        │ │             ║──────────────────── (Gray)    │ │
│ └────────┘ └──────────────────────────────────────────────┘ │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐  │
│ │Furniture KPI Card                                      │  │
│ ├────────────────────────────────────────────────────────┤  │
│ │Monthly Sales for Furniture (All 12 Months Shown)       │  │
│ │ Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec        │  │
│ │  ██  ██  ██  ██  ██  ██  ░░  ░░  ░░  ░░  ░░  ░░       │  │
│ │  ▓▓  ▓▓  ▓▓  ▓▓  ▓▓  ▓▓  ░░  ░░  ░░  ░░  ░░  ░░       │  │
│ │                                                        │  │
│ │  (Blue = actual Jun, Gray = goal, ░ = unselected)    │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**To return:** Click "← Back to Overview" button or adjust settings

## Settings Panel

### Year
- Select: 2020, 2021, 2022, or 2023
- Updates all charts with that year's data
- Default: 2023

### Through Month
- Select: January through December
- "Through Month" means "through and including" when YTD selected
- Default: December

### Time Range
- **Year-to-Date:** Shows data from Jan through selected month
  - Example: June selected = Jan-June data
- **Month Only:** Shows data for just the selected month
  - Example: June selected = June only data
- Default: Year-to-Date

### Compare To
- **vs Goal:** Compare actual sales to sales goals (from generated dataset)
  - Gray bars show full-year goals (all 12 months)
- **vs Prior Year:** Compare to same period in prior year
  - Gray bars show prior-year sales (full 12 months)
  - Edge case: 2020 shows no prior-year data (first year)
- Default: vs Goal

## Key Behaviors

### Drill-Down Interaction
1. **Overview:** Three categories shown
2. **Click:** Any category card (KPI or chart)
3. **Drill-down:** URL adds `&category=CategoryName`
4. **Chart changes:** Row 1 right chart becomes sub-category breakdown
5. **Back:** Click "← Back to Overview" or adjust any setting
6. **URL clears:** category parameter removed, returns to three-column view

### Chart Types

| Location | Chart Type | Mode | Details |
|----------|-----------|------|---------|
| Row 1 Left | KPI Card | Always | Large total sales number with comparison |
| Row 1 Right | Monthly Bar | Overview | Vertical bars, 12 months, all categories |
| Row 1 Right | Sub-Category Bar | Drill-down | Horizontal bars, sub-categories, blue/gray |
| Row 2 Left/Middle/Right | KPI Cards | Overview | Small KPI cards for each category |
| Row 2 Left/Middle/Right | Monthly Bar | Overview | Vertical bars for each category |
| Row 2 Full | KPI Card | Drill-down | Category-specific KPI |
| Row 2 Full | Monthly Bar | Drill-down | Vertical bars for drill-down category |

### Color Coding

| Color | Meaning |
|-------|---------|
| Cornflower Blue (#6495ED) | Actual sales for selected period |
| Pale Blue (#B0C4DE) | Unselected months (future months) |
| Light Gray (#D3D3D3) | Full-year comparison (goal or prior year) |
| Green Arrow (▲) | Performance above goal/comparison |
| Red Arrow (▼) | Performance below goal/comparison |

### Number Formatting

**On labels:**
```
$260M  (for $260,000,000)
$26.5M (for $26,500,000)
$2.6M  (for $2,600,000)
$260K  (for $260,000)
$26.5K (for $26,500)
$2.6K  (for $2,600)
$260   (for amounts less than $1,000)
```

**In tooltips (hover):**
```
$260,279.42 (always exact with 2 decimal places)
```

## Common Tasks

### Task: Check if Technology is meeting Q2 goals

1. Set **Year:** 2023
2. Set **Through Month:** June
3. Set **Time Range:** Year-to-Date
4. Set **Compare To:** vs Goal
5. **Click** Technology card to drill down
6. **Look at** sub-category chart - which items are below gray bar?
7. **Check** monthly chart - June (blue) vs full-year goal (gray)

### Task: Compare June sales to June last year

1. Set **Year:** 2023
2. Set **Through Month:** June
3. Set **Time Range:** Month Only
4. Set **Compare To:** vs Prior Year
5. See blue bars (June 2023) vs gray bars (June 2022 full year)

### Task: Which Furniture sub-category lost money?

1. Set any year/month/settings
2. **Click** Furniture category
3. **Look for** sub-categories with very short blue bars or negative (loss)
4. **Compare** blue (actual) vs gray (goal/prior year)

## Troubleshooting

### Dashboard doesn't load
```bash
# Check if server is running
lsof -i :8765

# If not running, start it
python3 preview_charts.py
```

### Charts look squeezed or overflow
- Try refreshing the page (Cmd+R or Ctrl+R)
- Close and reopen the browser
- Check viewport width (assumes 1440px)

### Numbers look wrong
- Verify URL parameters in address bar
- Hover over abbreviated numbers to see exact values
- Check settings panel matches your expectations

### Can't return from drill-down
- Click "← Back to Overview" button at top
- Or navigate directly: `http://localhost:8765/`
- Or adjust any setting (like Month selector)

### Sub-category chart shows no data
- Normal if selecting a category with no sub-categories (shouldn't happen)
- Verify category name is spelled correctly in URL
- Check year has transactions for that category

## Next Steps

After running:
1. **Explore overview:** Click through each category
2. **Test settings:** Change year, month, comparison mode
3. **Check tooltips:** Hover over all bars to see exact values
4. **Bookmark states:** Save URL for interesting views
5. **Provide feedback:** What visualizations to add next?

---

**Questions?** See:
- `DRILL_DOWN_USAGE_GUIDE.md` - Detailed feature walkthrough
- `IMPLEMENTATION_SUMMARY.md` - Technical implementation details
- `ARCHITECTURE.md` - System design and data flow
