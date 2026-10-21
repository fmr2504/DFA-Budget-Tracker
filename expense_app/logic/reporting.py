"""Pure calculation helpers for reports and budgets.

Functions in this module have no side effects and no Kivy or SQLite
dependencies, so they can be tested in isolation.

Both the Reports screen (Phase 6) and the Budgets screen (Phase 7)
share the :func:`month_range` and :func:`shift_month` helpers so they
always compute the same date boundaries and navigation states.
"""

from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CategoryBreakdown:
    """Spending breakdown for a single category within a reporting month."""

    category_name: str
    amount_centavos: int
    percentage: float


@dataclass(frozen=True)
class MonthlyReport:
    """Aggregated spending summary for a calendar month."""

    period_month: str
    total_centavos: int
    transaction_count: int
    categories: list[CategoryBreakdown]


@dataclass(frozen=True)
class BudgetStatus:
    """Calculated spending progress against a category budget limit."""

    category_id: int
    category_name: str
    period_month: str
    limit_centavos: int
    spent_centavos: int
    remaining_centavos: int
    progress_ratio: float
    visual_progress: float
    status_level: str  # "normal", "warning", "exceeded"


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def month_range(period_month: str) -> tuple[str, str]:
    """Return ``(start_date, end_date_exclusive)`` for a ``YYYY-MM`` period.

    The range is suitable for a SQL clause like::

        WHERE occurred_on >= ? AND occurred_on < ?

    which selects every date within the calendar month.

    Examples:
        >>> month_range("2026-10")
        ('2026-10-01', '2026-11-01')
        >>> month_range("2026-12")
        ('2026-12-01', '2027-01-01')

    Raises:
        ValueError: If *period_month* is not in ``YYYY-MM`` format or
                    the month is out of range.
    """
    parts = period_month.split("-")
    if len(parts) != 2 or len(parts[0]) != 4 or len(parts[1]) != 2:
        raise ValueError(
            f"Expected YYYY-MM format, got {period_month!r}"
        )

    try:
        year = int(parts[0])
        month = int(parts[1])
    except ValueError:
        raise ValueError(
            f"Expected YYYY-MM format, got {period_month!r}"
        )

    if not 1 <= month <= 12:
        raise ValueError(f"Month must be 1–12, got {month}")

    start = f"{year:04d}-{month:02d}-01"

    if month == 12:
        end = f"{year + 1:04d}-01-01"
    else:
        end = f"{year:04d}-{month + 1:02d}-01"

    return start, end


def shift_month(period_month: str, offset: int) -> str:
    """Add *offset* calendar months to *period_month* (e.g. -1 for prev, +1 for next).

    Examples:
        >>> shift_month("2026-10", 1)
        '2026-11'
        >>> shift_month("2026-12", 1)
        '2027-01'
        >>> shift_month("2026-01", -1)
        '2025-12'
    """
    parts = period_month.split("-")
    if len(parts) != 2 or len(parts[0]) != 4 or len(parts[1]) != 2:
        raise ValueError(
            f"Expected YYYY-MM format, got {period_month!r}"
        )

    try:
        year = int(parts[0])
        month = int(parts[1])
    except ValueError:
        raise ValueError(
            f"Expected YYYY-MM format, got {period_month!r}"
        )

    if not 1 <= month <= 12:
        raise ValueError(f"Month must be 1–12, got {month}")

    total_months = year * 12 + (month - 1) + offset
    new_year = total_months // 12
    new_month = (total_months % 12) + 1
    return f"{new_year:04d}-{new_month:02d}"


def validate_date(date_str: str) -> bool:
    """Return True if date_str is a valid ISO date in YYYY-MM-DD format."""
    clean = date_str.strip()
    parts = clean.split("-")
    if len(parts) != 3 or len(parts[0]) != 4 or len(parts[1]) != 2 or len(parts[2]) != 2:
        return False
    try:
        from datetime import datetime

        datetime.strptime(clean, "%Y-%m-%d")
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_monthly_report(
    expenses: list[dict], period_month: str
) -> MonthlyReport:
    """Generate a spending summary grouped by category for *period_month*.

    Computes total spending, transaction count, category totals, and percentage
    shares sorted descending by expense amount. Filters out any expense records
    whose occurred_on date falls outside the selected calendar month.
    """
    start_date, end_date = month_range(period_month)
    valid_expenses = [
        e for e in expenses
        if start_date <= e.get("occurred_on", "") < end_date
    ]

    total_centavos = sum(e.get("amount_centavos", 0) for e in valid_expenses)
    transaction_count = len(valid_expenses)

    if total_centavos == 0:
        return MonthlyReport(
            period_month=period_month,
            total_centavos=0,
            transaction_count=transaction_count,
            categories=[],
        )

    # Group totals by category name
    cat_totals: dict[str, int] = {}
    for exp in valid_expenses:
        cat = exp.get("category_name", "Other")
        cat_totals[cat] = cat_totals.get(cat, 0) + exp.get("amount_centavos", 0)

    # Calculate percentages and sort descending by amount, then alphabetically
    breakdowns: list[CategoryBreakdown] = []
    for cat_name, amt in cat_totals.items():
        pct = (amt / total_centavos) * 100.0
        breakdowns.append(
            CategoryBreakdown(
                category_name=cat_name,
                amount_centavos=amt,
                percentage=round(pct, 2),
            )
        )

    breakdowns.sort(key=lambda b: (-b.amount_centavos, b.category_name))

    return MonthlyReport(
        period_month=period_month,
        total_centavos=total_centavos,
        transaction_count=transaction_count,
        categories=breakdowns,
    )


# ---------------------------------------------------------------------------
# Budget progress calculation
# ---------------------------------------------------------------------------

def calculate_budget_progress(
    budget: dict, month_expenses: list[dict]
) -> BudgetStatus:
    """Compute spending progress, remaining balance, and status for a budget limit.

    Formulas:
    - spent = sum(expense amounts for matching category within the month)
    - remaining = limit - spent (negative if over budget)
    - progress_ratio = spent / limit
    - visual_progress = clamped to [0.0, 1.0]

    Status levels:
    - "exceeded": progress_ratio > 1.0
    - "warning": progress_ratio >= 0.8
    - "normal": progress_ratio < 0.8
    """
    category_id = budget["category_id"]
    category_name = budget.get("category_name", "Category")
    period_month = budget["period_month"]
    limit_centavos = budget["limit_centavos"]

    # Filter expenses for this category
    spent_centavos = sum(
        e.get("amount_centavos", 0)
        for e in month_expenses
        if e.get("category_id") == category_id
    )

    remaining_centavos = limit_centavos - spent_centavos
    progress_ratio = spent_centavos / limit_centavos if limit_centavos > 0 else 0.0
    visual_progress = max(0.0, min(1.0, progress_ratio))

    if progress_ratio > 1.0:
        status_level = "exceeded"
    elif progress_ratio >= 0.8:
        status_level = "warning"
    else:
        status_level = "normal"

    return BudgetStatus(
        category_id=category_id,
        category_name=category_name,
        period_month=period_month,
        limit_centavos=limit_centavos,
        spent_centavos=spent_centavos,
        remaining_centavos=remaining_centavos,
        progress_ratio=progress_ratio,
        visual_progress=visual_progress,
        status_level=status_level,
    )

