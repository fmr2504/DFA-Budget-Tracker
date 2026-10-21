"""Pure calculation helpers for reports and budgets.

Functions in this module have no side effects and no Kivy or SQLite
dependencies, so they can be tested in isolation.

Both the Reports screen (Phase 6) and the Budgets screen (Phase 7)
share the :func:`month_range` helper so they always compute the same
date boundaries.
"""

from __future__ import annotations


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

