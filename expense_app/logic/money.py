"""Money parsing, validation, and formatting helpers.

All monetary values are stored as **integer centavos** throughout
the application.  This module provides the boundary layer that
converts between user-visible Philippine-peso strings and internal
centavo integers.

The conversion pipeline:

    User input  →  parse_amount()  →  int centavos  →  SQLite
    SQLite      →  int centavos    →  format_amount() →  display
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

_CENTAVO_QUANTIZE = Decimal("0.01")


def parse_amount(text: str) -> int:
    """Parse a user-entered amount string into integer centavos.

    Strips ``₱`` signs, commas, and surrounding whitespace before
    parsing.  Uses :class:`~decimal.Decimal` to avoid floating-point
    rounding errors.

    Returns:
        Integer centavos (e.g. ``"125.50"`` → ``12550``).

    Raises:
        ValueError: If the text is blank, non-numeric, zero,
                    or negative.

    Examples:
        >>> parse_amount("125.50")
        12550
        >>> parse_amount("₱1,000")
        100000
    """
    cleaned = text.strip().replace("₱", "").replace(",", "").strip()
    if not cleaned:
        raise ValueError("Amount must not be empty.")

    try:
        amount = Decimal(cleaned)
    except InvalidOperation:
        raise ValueError(f"Invalid amount: {text!r}")

    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    # Quantize to two decimal places, then convert to centavos.
    centavos = int(
        amount.quantize(_CENTAVO_QUANTIZE, rounding=ROUND_HALF_UP) * 100
    )
    return centavos


def format_amount(centavos: int) -> str:
    """Format integer centavos as a Philippine-peso display string.

    Examples:
        >>> format_amount(12550)
        '₱125.50'
        >>> format_amount(100050)
        '₱1,000.50'
        >>> format_amount(0)
        '₱0.00'
    """
    pesos = Decimal(centavos) / 100
    return f"₱{pesos:,.2f}"

