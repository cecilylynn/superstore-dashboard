"""
data_processing.py — All Data Loading, Filtering, and Calculations

This file contains EVERY calculation used in the dashboard.
If you need to change how a number is computed, look here.

No UI code lives here — just pure data logic.
"""

import pandas as pd
from typing import Optional


# ── FILE PATHS ───────────────────────────────────────────────────────────────
# These point to the raw data files. Change these if you move the data files.
ORDERS_PATH = '/Users/cecilysantiago/Documents/Claude Code Playground/Datasources/Sample - Superstore.xls'
GOALS_PATH  = '/Users/cecilysantiago/Documents/Claude Code Playground/Datasources/subcategory_monthly_goals.csv'


# ── CONSTANTS ────────────────────────────────────────────────────────────────
# The three product categories in the Superstore dataset
CATEGORIES = ['Furniture', 'Office Supplies', 'Technology']

# Short month names used as bar chart labels (Jan, Feb, ... Dec)
MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# Maps full month name → month number (January → 1, February → 2, etc.)
MONTH_MAP = {
    'January': 1, 'February': 2, 'March': 3, 'April': 4,
    'May': 5, 'June': 6, 'July': 7, 'August': 8,
    'September': 9, 'October': 10, 'November': 11, 'December': 12
}

# Reverse lookup: month number → full month name (1 → 'January', etc.)
MONTH_NUM_TO_NAME = {v: k for k, v in MONTH_MAP.items()}


# ── DATA LOADING ─────────────────────────────────────────────────────────────

def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the two data sources and prepare them for analysis.

    Returns:
        orders: DataFrame with one row per order line item (10,194 rows).
                Has columns: Sales, Profit, Category, Sub-Category, Year, Month, etc.
        goals:  DataFrame with one row per sub-category per month (816 rows).
                Has columns: Year-Month, Sub-Category, Sales_Goal
    """
    # Read the main transaction data from the Excel file (sheet named "Orders")
    orders = pd.read_excel(ORDERS_PATH, sheet_name='Orders')

    # Read the sales goals CSV (generated earlier with ±10% variance from actuals)
    goals = pd.read_csv(GOALS_PATH)

    # Convert the Order Date column from text to a proper date type
    orders['Order Date'] = pd.to_datetime(orders['Order Date'])

    # Extract useful date parts so we can filter and group easily
    orders['Year']       = orders['Order Date'].dt.year        # e.g. 2023
    orders['Month']      = orders['Order Date'].dt.month       # e.g. 6 for June
    orders['Year-Month'] = orders['Order Date'].dt.strftime('%Y-%m')  # e.g. "2023-06"

    return orders, goals


# ── CURRENCY FORMATTING ──────────────────────────────────────────────────────

def fmt(value: float) -> str:
    """
    Format a dollar amount into an abbreviated string for dashboard labels.

    Makes big numbers easy to read at a glance:
        $2,600,000  →  "$2.6M"
        $260,000    →  "$260K"
        $26,500     →  "$26.5K"
        $260        →  "$260"

    Exact (unabbreviated) amounts are shown in hover tooltips instead.

    Args:
        value: The dollar amount to format.

    Returns:
        A string like "$260K" or "$2.6M".
    """
    a = abs(value)  # Use absolute value to pick the right abbreviation level

    # Millions range
    if a >= 100_000_000: return f"${value / 1_000_000:.0f}M"   # e.g. $260M
    if a >= 10_000_000:  return f"${value / 1_000_000:.1f}M"   # e.g. $26.5M
    if a >= 1_000_000:   return f"${value / 1_000_000:.1f}M"   # e.g. $2.6M

    # Thousands range
    if a >= 100_000:     return f"${value / 1_000:.0f}K"       # e.g. $260K
    if a >= 10_000:      return f"${value / 1_000:.1f}K"       # e.g. $26.5K
    if a >= 1_000:       return f"${value / 1_000:.1f}K"       # e.g. $2.6K

    # Small amounts: show as-is, no decimals
    return f"${value:.0f}"                                      # e.g. $260


# ── MONTHLY SALES DATA (powers the vertical bar charts) ──────────────────────

def get_monthly_actuals(
    orders: pd.DataFrame,
    year: int,
    category: Optional[str] = None
) -> pd.Series:
    """
    Get actual sales for each month (Jan–Dec) in a given year.

    This powers the BLUE BARS in the monthly bar charts.

    Args:
        orders:   The full orders DataFrame.
        year:     Which year to look at (e.g. 2023).
        category: If provided, only include this category (e.g. "Furniture").
                  If None, include all categories.

    Returns:
        A pandas Series with 12 values indexed 1–12 (one per month).
        Months with no sales show as 0.
    """
    # Start with all orders in the selected year
    d = orders[orders['Year'] == year].copy()

    # If a specific category was requested, keep only that category's rows
    if category:
        d = d[d['Category'] == category]

    # Group rows by month number, sum up the Sales column for each month.
    # reindex(range(1,13)) ensures we always get all 12 months even if some have $0.
    return d.groupby('Month')['Sales'].sum().reindex(range(1, 13), fill_value=0)


def get_monthly_comparison(
    orders: pd.DataFrame,
    goals: pd.DataFrame,
    year: int,
    comparison_mode: str,
    category: Optional[str] = None
) -> list[float]:
    """
    Get the comparison values (goal or prior year) for each of the 12 months.

    This powers the GRAY BARS behind the blue bars in the monthly charts.

    Args:
        orders:          The full orders DataFrame.
        goals:           The goals DataFrame.
        year:            The selected year (e.g. 2023).
        comparison_mode: Either "vs Goal" or "vs Prior Year".
        category:        Optional category filter.

    Returns:
        A list of 12 floats — one comparison value per month (Jan through Dec).
    """
    if comparison_mode == 'vs Goal':
        # --- GOAL COMPARISON ---
        # Goals are stored at the sub-category level, so if we're filtering by
        # category we need to know which sub-categories belong to that category
        subcats = (orders[orders['Category'] == category]['Sub-Category'].unique()
                   if category else None)

        result = []
        for m in range(1, 13):  # Loop through months 1 (Jan) to 12 (Dec)
            # Build the year-month key like "2023-01", "2023-02", etc.
            ym = f"{year}-{m:02d}"

            # Get all goal rows for this specific month
            g = goals[goals['Year-Month'] == ym]

            # If filtering by category, only keep goals for that category's sub-categories
            if subcats is not None:
                g = g[g['Sub-Category'].isin(subcats)]

            # Sum up all the goal values for this month and add to our list
            result.append(g['Sales_Goal'].sum())
        return result

    else:
        # --- PRIOR YEAR COMPARISON ---
        # Get actual sales from last year (e.g. if year=2023, look at 2022)
        prior = orders[orders['Year'] == year - 1].copy()

        # Apply category filter if needed
        if category:
            prior = prior[prior['Category'] == category]

        # Group by month, sum sales, ensure all 12 months present
        return prior.groupby('Month')['Sales'].sum().reindex(range(1, 13), fill_value=0).tolist()


# ── PERIOD TOTALS (powers the KPI cards) ─────────────────────────────────────

def get_period_totals(
    orders: pd.DataFrame,
    goals: pd.DataFrame,
    year: int,
    month: int,
    time_range: str,
    comparison_mode: str,
    category: Optional[str] = None
) -> tuple[float, float, float, str]:
    """
    Calculate the total sales and comparison value for the selected time period.

    This is used by the big KPI cards to show things like:
        "Total Sales: $831K   Goal: $852K   ▼ 2.4%"

    Args:
        orders:          The full orders DataFrame.
        goals:           The goals DataFrame.
        year:            Selected year (e.g. 2023).
        month:           Selected month number (e.g. 6 for June).
        time_range:      "YTD" means January through selected month.
                         "Month Only" means just that one month.
        comparison_mode: "vs Goal" or "vs Prior Year".
        category:        Optional category filter (None = all categories).

    Returns:
        A tuple of four values:
        - actual:  Total sales dollars for the selected period
        - comp:    The goal or prior-year total for the same period
        - pct:     Percent difference (positive = above, negative = below)
        - label:   Either "Goal" or the prior year number like "2022"
    """
    # Start with all orders in the selected year
    d = orders[orders['Year'] == year].copy()

    # Apply category filter if specified
    if category:
        d = d[d['Category'] == category]

    # Apply time range filter:
    #   YTD = all months from January through the selected month
    #   Month Only = just the one selected month
    if time_range == 'YTD':
        d = d[d['Month'] <= month]   # e.g. month=6 keeps Jan through Jun
    else:
        d = d[d['Month'] == month]   # e.g. month=6 keeps only June

    # Sum up actual sales for the filtered period
    actual = d['Sales'].sum()

    # --- Now calculate the comparison value ---
    if comparison_mode == 'vs Goal':
        # Build list of year-month keys for the period
        # e.g. YTD through June 2023 → ["2023-01", "2023-02", ..., "2023-06"]
        if time_range == 'YTD':
            ym_list = [f"{year}-{m:02d}" for m in range(1, month + 1)]
        else:
            ym_list = [f"{year}-{month:02d}"]

        # Get goal rows for those months
        g = goals[goals['Year-Month'].isin(ym_list)]

        # If filtering by category, only include that category's sub-categories
        if category:
            subcats = orders[orders['Category'] == category]['Sub-Category'].unique()
            g = g[g['Sub-Category'].isin(subcats)]

        comp = g['Sales_Goal'].sum()
        label = 'Goal'

    else:
        # Prior year: get sales from the same period last year
        prior = orders[orders['Year'] == year - 1].copy()

        if category:
            prior = prior[prior['Category'] == category]

        # Apply the same time range filter to the prior year data
        if time_range == 'YTD':
            prior = prior[prior['Month'] <= month]
        else:
            prior = prior[prior['Month'] == month]

        comp = prior['Sales'].sum()
        label = str(year - 1)  # e.g. "2022"

    # Calculate percentage difference: ((actual - comparison) / comparison) × 100
    # If comparison is 0, show 0% to avoid dividing by zero
    pct = ((actual - comp) / comp * 100) if comp > 0 else 0

    return actual, comp, pct, label


# ── SUB-CATEGORY DATA (powers the horizontal drill-down charts) ──────────────

def get_subcategory_actuals(
    orders: pd.DataFrame,
    year: int,
    month: int,
    time_range: str,
    category: str
) -> pd.Series:
    """
    Get actual sales by sub-category for the selected period.

    This powers the BLUE BARS in the horizontal sub-category drill-down chart.
    Results are sorted smallest-to-largest so the biggest sub-categories
    appear at the top of the horizontal chart (Plotly draws bottom-up).

    Args:
        orders:     The full orders DataFrame.
        year:       Selected year.
        month:      Selected month number.
        time_range: "YTD" or "Month Only".
        category:   Which category to drill into (e.g. "Furniture").

    Returns:
        A pandas Series indexed by sub-category name, values are total sales,
        sorted ascending (smallest first).
    """
    # Filter to the selected year and category
    d = orders[orders['Year'] == year].copy()
    d = d[d['Category'] == category]

    # Apply time range filter (same logic as get_period_totals)
    if time_range == 'YTD':
        d = d[d['Month'] <= month]
    else:
        d = d[d['Month'] == month]

    # Group by sub-category name, sum sales, sort smallest → largest
    return d.groupby('Sub-Category')['Sales'].sum().sort_values(ascending=True)


def get_subcategory_period_comparison(
    orders: pd.DataFrame,
    goals: pd.DataFrame,
    year: int,
    month: int,
    time_range: str,
    comparison_mode: str,
    category: str
) -> dict[str, float]:
    """
    Get comparison values by sub-category for the SELECTED PERIOD.

    This powers the GRAY BARS in the sub-category drill-down chart.
    These show the goal or prior-year sales for the same time window
    as the blue bars (e.g. Jan–June if YTD through June).

    Args:
        orders:          The full orders DataFrame.
        goals:           The goals DataFrame.
        year:            Selected year.
        month:           Selected month number.
        time_range:      "YTD" or "Month Only".
        comparison_mode: "vs Goal" or "vs Prior Year".
        category:        Which category (e.g. "Furniture").

    Returns:
        A dict mapping sub-category name → comparison value.
        Example: {"Bookcases": 12000, "Chairs": 45000, ...}
    """
    # Find all sub-categories that belong to this category
    subcats = orders[orders['Category'] == category]['Sub-Category'].unique()
    result = {}

    if comparison_mode == 'vs Goal':
        # Build year-month keys for the selected period
        if time_range == 'YTD':
            ym_list = [f"{year}-{m:02d}" for m in range(1, month + 1)]
        else:
            ym_list = [f"{year}-{month:02d}"]

        # Get goals for those months, filtered to this category's sub-categories
        g = goals[goals['Year-Month'].isin(ym_list)]
        g = g[g['Sub-Category'].isin(subcats)]

        # Sum goals for each sub-category individually
        for sc in subcats:
            result[sc] = g[g['Sub-Category'] == sc]['Sales_Goal'].sum()

    else:
        # Prior year: get actual sales from last year for the same period
        prior = orders[orders['Year'] == year - 1].copy()
        prior = prior[prior['Category'] == category]

        # Apply same time range filter to prior year data
        if time_range == 'YTD':
            prior = prior[prior['Month'] <= month]
        else:
            prior = prior[prior['Month'] == month]

        # Sum prior year sales for each sub-category
        for sc in subcats:
            result[sc] = prior[prior['Sub-Category'] == sc]['Sales'].sum()

    return result


def get_subcategory_full_year_comparison(
    orders: pd.DataFrame,
    goals: pd.DataFrame,
    year: int,
    comparison_mode: str,
    category: str
) -> dict[str, float]:
    """
    Get comparison values by sub-category for the FULL YEAR (all 12 months).

    This powers the DARK GRAY REFERENCE LINES in the sub-category chart.
    These lines show "where does this sub-category need to end up by December?"

    The gray bars show the period comparison (e.g. Jan–June goal),
    while these lines show the full-year total (e.g. full 2023 goal).
    Comparing blue bars to these lines tells you if you're on pace.

    Args:
        orders:          The full orders DataFrame.
        goals:           The goals DataFrame.
        year:            Selected year.
        comparison_mode: "vs Goal" or "vs Prior Year".
        category:        Which category (e.g. "Furniture").

    Returns:
        A dict mapping sub-category name → full-year comparison value.
    """
    # Find all sub-categories in this category
    subcats = orders[orders['Category'] == category]['Sub-Category'].unique()
    result = {}

    if comparison_mode == 'vs Goal':
        # Get goals for ALL 12 months of the selected year
        ym_list = [f"{year}-{m:02d}" for m in range(1, 13)]
        g = goals[goals['Year-Month'].isin(ym_list)]
        g = g[g['Sub-Category'].isin(subcats)]

        # Sum the full-year goal for each sub-category
        for sc in subcats:
            result[sc] = g[g['Sub-Category'] == sc]['Sales_Goal'].sum()

    else:
        # Get ALL actual sales from prior year (full 12 months)
        prior = orders[orders['Year'] == year - 1].copy()
        prior = prior[prior['Category'] == category]

        # Sum full prior year sales for each sub-category
        for sc in subcats:
            result[sc] = prior[prior['Sub-Category'] == sc]['Sales'].sum()

    return result
