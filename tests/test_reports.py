"""Unit and integration tests for monthly spending reports (expense_app.logic.reporting)."""

import pytest

from expense_app.data.repositories import (
    create_expense,
    delete_expense,
    get_category_by_name,
    get_expenses,
    update_expense,
)
from expense_app.logic.reporting import (
    generate_monthly_report,
    month_range,
    shift_month,
)


class TestShiftMonth:
    def test_forward_one_month(self):
        assert shift_month("2026-10", 1) == "2026-11"

    def test_backward_one_month(self):
        assert shift_month("2026-10", -1) == "2026-09"

    def test_year_boundary_forward(self):
        assert shift_month("2026-12", 1) == "2027-01"

    def test_year_boundary_backward(self):
        assert shift_month("2026-01", -1) == "2025-12"

    def test_multiple_months_shift(self):
        assert shift_month("2026-10", 3) == "2027-01"
        assert shift_month("2026-02", -3) == "2025-11"

    def test_zero_shift(self):
        assert shift_month("2026-10", 0) == "2026-10"

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            shift_month("2026/10", 1)
        with pytest.raises(ValueError):
            shift_month("2026-13", 1)


class TestGenerateMonthlyReportPure:
    def test_empty_month_no_expenses(self):
        report = generate_monthly_report([], "2026-10")
        assert report.period_month == "2026-10"
        assert report.total_centavos == 0
        assert report.transaction_count == 0
        assert report.categories == []

    def test_single_category_report(self):
        expenses = [
            {"amount_centavos": 15000, "category_name": "Food", "occurred_on": "2026-10-05"},
            {"amount_centavos": 25000, "category_name": "Food", "occurred_on": "2026-10-12"},
        ]
        report = generate_monthly_report(expenses, "2026-10")
        assert report.total_centavos == 40000
        assert report.transaction_count == 2
        assert len(report.categories) == 1
        assert report.categories[0].category_name == "Food"
        assert report.categories[0].amount_centavos == 40000
        assert report.categories[0].percentage == 100.0

    def test_multiple_categories_sorted_descending(self):
        expenses = [
            {"amount_centavos": 20000, "category_name": "Food", "occurred_on": "2026-10-02"},
            {"amount_centavos": 50000, "category_name": "Bills", "occurred_on": "2026-10-10"},
            {"amount_centavos": 30000, "category_name": "Transportation", "occurred_on": "2026-10-15"},
        ]
        report = generate_monthly_report(expenses, "2026-10")
        assert report.total_centavos == 100000
        assert report.transaction_count == 3
        assert len(report.categories) == 3

        # Sorted by amount descending: Bills (50k) > Transportation (30k) > Food (20k)
        names = [c.category_name for c in report.categories]
        assert names == ["Bills", "Transportation", "Food"]

        # Percentages
        pcts = [c.percentage for c in report.categories]
        assert pcts == [50.0, 30.0, 20.0]

    def test_month_isolation_filters_adjacent_dates(self):
        expenses = [
            {"amount_centavos": 1000, "category_name": "Food", "occurred_on": "2026-09-30"},  # Prev month
            {"amount_centavos": 2000, "category_name": "Food", "occurred_on": "2026-10-01"},  # Included
            {"amount_centavos": 3000, "category_name": "Food", "occurred_on": "2026-10-31"},  # Included
            {"amount_centavos": 4000, "category_name": "Food", "occurred_on": "2026-11-01"},  # Next month
        ]
        report = generate_monthly_report(expenses, "2026-10")
        assert report.total_centavos == 5000
        assert report.transaction_count == 2


class TestReportDatabaseIntegration:
    def test_report_reflects_saved_expenses(self, db_conn):
        cat_food = get_category_by_name(db_conn, "Food")
        cat_trans = get_category_by_name(db_conn, "Transportation")

        create_expense(db_conn, 15000, "Jollibee", "2026-10-05", cat_food["id"])
        create_expense(db_conn, 8500, "Grab", "2026-10-10", cat_trans["id"])

        start, end = month_range("2026-10")
        db_expenses = get_expenses(db_conn, start_date=start, end_date_exclusive=end)
        report = generate_monthly_report(db_expenses, "2026-10")

        assert report.total_centavos == 23500
        assert report.transaction_count == 2
        assert len(report.categories) == 2

    def test_editing_expense_updates_report(self, db_conn):
        cat_food = get_category_by_name(db_conn, "Food")
        exp_id = create_expense(db_conn, 10000, "Lunch", "2026-10-05", cat_food["id"])

        # Update expense amount
        update_expense(db_conn, exp_id, amount_centavos=18000)

        start, end = month_range("2026-10")
        report = generate_monthly_report(get_expenses(db_conn, start_date=start, end_date_exclusive=end), "2026-10")
        assert report.total_centavos == 18000
        assert report.categories[0].amount_centavos == 18000

    def test_deleting_expense_updates_report(self, db_conn):
        cat_food = get_category_by_name(db_conn, "Food")
        exp_id = create_expense(db_conn, 10000, "Lunch", "2026-10-05", cat_food["id"])

        delete_expense(db_conn, exp_id)

        start, end = month_range("2026-10")
        report = generate_monthly_report(get_expenses(db_conn, start_date=start, end_date_exclusive=end), "2026-10")
        assert report.total_centavos == 0
        assert report.transaction_count == 0
        assert report.categories == []

