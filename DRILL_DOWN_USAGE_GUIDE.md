# Interactive Category Drill-Down Usage Guide

## Overview

The dashboard now supports two viewing modes:

1. **Overview Mode** - See all three categories side-by-side
2. **Drill-Down Mode** - Focus on one category with sub-category breakdown

## How to Use

### From Overview to Drill-Down

In the overview (initial load):
```
Row 2 shows three clickable cards:
┌─────────────┬─────────────┬─────────────┐
│ Furniture   │ Office Sup. │ Technology  │
├─────────────┼─────────────┼─────────────┤
│ [Monthly    │ [Monthly    │ [Monthly    │
│  chart]     │  chart]     │  chart]     │
└─────────────┴─────────────┴─────────────┘
```

**To drill down:** Click on any category card (either KPI card or bar chart)

```
1. Click "Furniture" card
2. Page navigates to drill-down view
3. URL changes: ?category=Furniture
4. Dashboard reorganizes to show Furniture details
```

### In Drill-Down Mode

Once you've clicked a category:

```
Header shows:
  [← Back to Overview] Viewing: Furniture

Row 1:
  ┌─────────┬──────────────────────────┐
  │  KPI    │  Sub-Category Chart      │
  │  Card   │  (Desks, Tables, etc.)   │
  └─────────┴──────────────────────────┘

Row 2 (full width):
  ┌─────────────────────────────────────┐
  │  Furniture Category KPI Card         │
  ├─────────────────────────────────────┤
  │  Monthly Sales Trend (all 12 months) │
  └─────────────────────────────────────┘
```

### Sub-Category Chart Features

The new horizontal bar chart shows:

```
          Bookcase  ║─────────── [GRAY BAR - Full Year Goal/Prior Year]
                    ║──────── [BLUE BAR - Actual for Selected Period]

          Cabinets  ║──────────── [GRAY]
                    ║────────── [BLUE]

          Chairs    ║────────────── [GRAY]
                    ║──────────── [BLUE]

          Desks     ║──── [GRAY - shorter]
                    ║────────────── [BLUE - longer]

          Tables    ║────────────────────── [GRAY]
                    ║─ [BLUE - much shorter, maybe loss]
```

**What it means:**
- **Blue bar length:** How much actual sales in your selected period
- **Gray bar length:** Full-year goal or prior-year sales
- **Comparison:** If blue > gray, you're beating full-year pace

**Example:**
- Viewing: June 2023, Year-to-Date (Jan-Jun)
- Desks: Actual $50K (blue), Full-Year Goal $300K (gray)
- Tooltip: "75% of full-year goal pace"

### Return to Overview

Two ways to go back:

1. **Click "Back to Overview" button** at the top
   - Clears category parameter
   - Returns to three-column view

2. **Click "← Back to Overview" link**
   - Same effect

URL becomes: `?year=2023&month=6&...` (no category parameter)

## Parameter Interactions

### How Settings Affect Sub-Category Chart

| Parameter | Effect |
|-----------|--------|
| **Year selector** | Changes which year's data shown in both blue and gray bars |
| **Month selector** | Changes period shown in blue bar (actual) |
| **Time Range (YTD/Month Only)** | Determines if blue bar shows Jan-Month or just selected month |
| **Comparison Mode (vs Goal/vs Prior Year)** | Switches gray bars from sales goals to prior-year sales |

### Important: Full-Year Comparison

The gray bar ALWAYS shows full year data:
- If you select "June, YTD": Blue shows Jan-Jun, Gray shows Jan-Dec
- If you select "June, Month Only": Blue shows June only, Gray shows full year
- This lets you see "am I on pace?" even for single months

## Real-World Examples

### Example 1: Is Furniture on track for Q2?
```
Settings:
- Year: 2023
- Month: June
- Time Range: Year-to-Date
- Comparison: vs Goal

Drill down to: Furniture

Result:
- Blue bars: Jan-Jun actual sales
- Gray bars: Full-year 2023 goal (all 12 months)
- Tells you: "Desks are at 75% of goal pace"
```

### Example 2: How did Furniture perform vs last year (June)?
```
Settings:
- Year: 2023
- Month: June
- Time Range: Month Only
- Comparison: vs Prior Year

Drill down to: Furniture

Result:
- Blue bars: June 2023 actual sales only
- Gray bars: Full-year 2022 goal (all 12 months)
- Shows seasonal comparison: June vs annual average
```

### Example 3: Sub-category deep dive
```
Goal: Find which furniture sub-category is hurting profitability

Steps:
1. Overview: See all categories
2. Click Furniture (drill down)
3. Look at sub-category chart - see which items are underperforming
4. Check monthly bar chart - see trends over time
5. Use settings to compare vs goals or prior year
```

## URL Examples (for bookmarking)

### Overview Mode
```
http://localhost:8765/?year=2023&month=6&time_range=YTD&comparison=vs Goal
```

### Drill-Down Mode (Furniture)
```
http://localhost:8765/?year=2023&month=6&time_range=YTD&comparison=vs Goal&category=Furniture
```

### Drill-Down Mode (Technology, Month Only, Prior Year)
```
http://localhost:8765/?year=2023&month=6&time_range=Month Only&comparison=vs Prior Year&category=Technology
```

## Tips & Tricks

1. **Hover for exact numbers** - Abbreviated format ($50K) on labels, exact amounts in tooltips
2. **Look for widest gaps** - Big difference between blue and gray suggests underperformance
3. **Compare across categories** - Go back to overview to see which category needs attention
4. **Check seasonality** - Use prior-year comparison to spot seasonal patterns
5. **Monitor progress** - Use YTD view with goals to track quarterly performance

## Visual Indicators

### Color Meanings
- **Cornflower Blue (#6495ED):** Actual sales for selected period
- **Light Gray (#D3D3D3):** Full-year comparison (goal or prior year)
- **Green arrow (▲):** Performance above comparison
- **Red arrow (▼):** Performance below comparison

### Hover States
- Category cards: Cursor changes to pointer, shadow increases
- Sub-category bars: Tooltip shows exact values and calculations

---

**Questions?** Check the implementation summary for technical details.
