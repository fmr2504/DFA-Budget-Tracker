"""Tests for money parsing, validation, and formatting (expense_app.logic.money)."""

import pytest

from expense_app.logic.money import format_amount, parse_amount


class TestParseAmount:
    def test_standard_decimal(self):
        assert parse_amount("125.50") == 12550

    def test_integer_string(self):
        assert parse_amount("100") == 10000

    def test_centavos_only(self):
        assert parse_amount("0.75") == 75

    def test_with_peso_symbol(self):
        assert parse_amount("₱150.00") == 15000
        assert parse_amount("₱ 250.50") == 25050

    def test_with_commas(self):
        assert parse_amount("1,000.00") == 100000
        assert parse_amount("₱1,250,500.50") == 125050050

    def test_surrounding_whitespace(self):
        assert parse_amount("  50.25  ") == 5025

    def test_rounding_half_up(self):
        # 125.505 quantizes to 125.51 -> 12551
        assert parse_amount("125.505") == 12551

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="empty"):
            parse_amount("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="empty"):
            parse_amount("   ")

    def test_non_numeric_raises(self):
        with pytest.raises(ValueError, match="Invalid amount"):
            parse_amount("abc")

    def test_multiple_decimals_raises(self):
        with pytest.raises(ValueError, match="Invalid amount"):
            parse_amount("12.34.56")

    def test_zero_amount_raises(self):
        with pytest.raises(ValueError, match="greater than zero"):
            parse_amount("0")
        with pytest.raises(ValueError, match="greater than zero"):
            parse_amount("0.00")

    def test_negative_amount_raises(self):
        with pytest.raises(ValueError, match="greater than zero"):
            parse_amount("-50")
        with pytest.raises(ValueError, match="greater than zero"):
            parse_amount("-0.01")


class TestFormatAmount:
    def test_standard_amount(self):
        assert format_amount(12550) == "₱125.50"

    def test_thousands_separator(self):
        assert format_amount(100000) == "₱1,000.00"
        assert format_amount(125050050) == "₱1,250,500.50"

    def test_zero(self):
        assert format_amount(0) == "₱0.00"

    def test_small_centavos(self):
        assert format_amount(5) == "₱0.05"
        assert format_amount(50) == "₱0.50"

    def test_negative_display(self):
        assert format_amount(-5000) == "₱-50.00"


class TestRoundTrip:
    @pytest.mark.parametrize(
        "centavos",
        [1, 50, 100, 12550, 99999, 1000000],
    )
    def test_parse_format_roundtrip(self, centavos):
        formatted = format_amount(centavos)
        parsed = parse_amount(formatted)
        assert parsed == centavos

