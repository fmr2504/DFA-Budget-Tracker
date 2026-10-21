"""Tests for pure reporting calculations and helpers (expense_app.logic.reporting)."""

import pytest

from expense_app.logic.reporting import month_range


class TestMonthRange:
    def test_standard_month(self):
        start, end = month_range("2026-10")
        assert start == "2026-10-01"
        assert end == "2026-11-01"

    def test_year_boundary_december(self):
        start, end = month_range("2026-12")
        assert start == "2026-12-01"
        assert end == "2027-01-01"

    def test_january(self):
        start, end = month_range("2026-01")
        assert start == "2026-01-01"
        assert end == "2026-02-01"

    def test_leap_year_february(self):
        start, end = month_range("2024-02")
        assert start == "2024-02-01"
        assert end == "2024-03-01"

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="YYYY-MM format"):
            month_range("2026/10")
        with pytest.raises(ValueError, match="YYYY-MM format"):
            month_range("2026-1")
        with pytest.raises(ValueError, match="YYYY-MM format"):
            month_range("invalid")
        with pytest.raises(ValueError, match="YYYY-MM format"):
            month_range("2026")

    def test_out_of_range_month_raises(self):
        with pytest.raises(ValueError, match="Month must be 1–12"):
            month_range("2026-00")
        with pytest.raises(ValueError, match="Month must be 1–12"):
            month_range("2026-13")

