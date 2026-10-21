"""Tests for budget persistence and operations (expense_app.data.repositories)."""

import sqlite3
import pytest

from expense_app.data.repositories import (
    create_expense,
    delete_budget,
    delete_budget_for_category,
    get_budget,
    get_budgets_for_month,
    get_category_by_name,
    get_expenses,
    set_budget,
)
from expense_app.logic.reporting import calculate_budget_progress, month_range


class TestCalculateBudgetProgressPure:
    def test_no_expenses_under_budget(self):
        budget = {
            "category_id": 1,
            "category_name": "Food",
            "period_month": "2026-10",
            "limit_centavos": 100000,
        }
        status = calculate_budget_progress(budget, [])
        assert status.spent_centavos == 0
        assert status.remaining_centavos == 100000
        assert status.progress_ratio == 0.0
        assert status.visual_progress == 0.0
        assert status.status_level == "normal"

    def test_under_budget_normal(self):
        budget = {
            "category_id": 1,
            "category_name": "Food",
            "period_month": "2026-10",
            "limit_centavos": 100000,
        }
        expenses = [
            {"amount_centavos": 50000, "category_id": 1},
        ]
        status = calculate_budget_progress(budget, expenses)
        assert status.spent_centavos == 50000
        assert status.remaining_centavos == 50000
        assert status.progress_ratio == 0.5
        assert status.visual_progress == 0.5
        assert status.status_level == "normal"

    def test_warning_threshold_at_80_percent(self):
        budget = {
            "category_id": 1,
            "category_name": "Food",
            "period_month": "2026-10",
            "limit_centavos": 100000,
        }
        expenses = [
            {"amount_centavos": 80000, "category_id": 1},
        ]
        status = calculate_budget_progress(budget, expenses)
        assert status.spent_centavos == 80000
        assert status.remaining_centavos == 20000
        assert status.progress_ratio == 0.8
        assert status.visual_progress == 0.8
        assert status.status_level == "warning"

    def test_exact_limit_warning(self):
        budget = {
            "category_id": 1,
            "category_name": "Food",
            "period_month": "2026-10",
            "limit_centavos": 100000,
        }
        expenses = [
            {"amount_centavos": 100000, "category_id": 1},
        ]
        status = calculate_budget_progress(budget, expenses)
        assert status.spent_centavos == 100000
        assert status.remaining_centavos == 0
        assert status.progress_ratio == 1.0
        assert status.visual_progress == 1.0
        assert status.status_level == "warning"

    def test_over_budget_exceeded(self):
        budget = {
            "category_id": 1,
            "category_name": "Food",
            "period_month": "2026-10",
            "limit_centavos": 100000,
        }
        expenses = [
            {"amount_centavos": 140000, "category_id": 1},
        ]
        status = calculate_budget_progress(budget, expenses)
        assert status.spent_centavos == 140000
        # Negative remaining intact
        assert status.remaining_centavos == -40000
        assert status.progress_ratio == 1.4
        # Visual progress clamped to 1.0
        assert status.visual_progress == 1.0
        assert status.status_level == "exceeded"

    def test_multiple_categories_filtered(self):
        budget = {
            "category_id": 1,
            "category_name": "Food",
            "period_month": "2026-10",
            "limit_centavos": 100000,
        }
        expenses = [
            {"amount_centavos": 20000, "category_id": 1},  # Food
            {"amount_centavos": 50000, "category_id": 2},  # Transport
            {"amount_centavos": 30000, "category_id": 1},  # Food
        ]
        status = calculate_budget_progress(budget, expenses)
        assert status.spent_centavos == 50000
        assert status.remaining_centavos == 50000


class TestBudgetDatabaseIntegration:
    def test_budget_reflects_actual_expenses(self, db_conn):
        cat_food = get_category_by_name(db_conn, "Food")
        set_budget(db_conn, cat_food["id"], "2026-10", 100000)

        create_expense(db_conn, 25000, "Lunch", "2026-10-05", cat_food["id"])
        create_expense(db_conn, 35000, "Dinner", "2026-10-12", cat_food["id"])

        start, end = month_range("2026-10")
        month_expenses = get_expenses(db_conn, start_date=start, end_date_exclusive=end)
        budget = get_budget(db_conn, cat_food["id"], "2026-10")

        status = calculate_budget_progress(budget, month_expenses)
        assert status.spent_centavos == 60000
        assert status.remaining_centavos == 40000
        assert status.progress_ratio == 0.6
        assert status.status_level == "normal"

    def test_removing_budget_preserves_expenses(self, db_conn):
        cat_food = get_category_by_name(db_conn, "Food")
        set_budget(db_conn, cat_food["id"], "2026-10", 100000)
        exp_id = create_expense(db_conn, 25000, "Lunch", "2026-10-05", cat_food["id"])

        # Delete budget
        delete_budget_for_category(db_conn, cat_food["id"], "2026-10")
        assert get_budget(db_conn, cat_food["id"], "2026-10") is None

        # Expense still exists
        expenses = get_expenses(db_conn)
        assert any(e["id"] == exp_id for e in expenses)


class TestBudgetsRepository:
    def test_set_and_get_budget(self, db_conn):
        b_id = set_budget(
            db_conn,
            category_id=1,  # Food
            period_month="2026-10",
            limit_centavos=100000,  # ₱1,000.00
        )
        assert b_id > 0
        budget = get_budget(db_conn, category_id=1, period_month="2026-10")
        assert budget is not None
        assert budget["limit_centavos"] == 100000
        assert budget["category_name"] == "Food"

    def test_upsert_existing_budget(self, db_conn):
        set_budget(db_conn, category_id=1, period_month="2026-10", limit_centavos=100000)
        # Update limit for the same month and category
        set_budget(db_conn, category_id=1, period_month="2026-10", limit_centavos=150000)

        budgets = get_budgets_for_month(db_conn, "2026-10")
        food_budgets = [b for b in budgets if b["category_id"] == 1]
        assert len(food_budgets) == 1
        assert food_budgets[0]["limit_centavos"] == 150000

    def test_zero_or_negative_limit_rejected(self, db_conn):
        with pytest.raises(ValueError, match="greater than zero"):
            set_budget(db_conn, category_id=1, period_month="2026-10", limit_centavos=0)

        with pytest.raises(ValueError, match="greater than zero"):
            set_budget(db_conn, category_id=1, period_month="2026-10", limit_centavos=-100)

    def test_invalid_category_id_raises_foreign_key_error(self, db_conn):
        with pytest.raises(sqlite3.IntegrityError):
            set_budget(db_conn, category_id=9999, period_month="2026-10", limit_centavos=50000)

    def test_budgets_isolated_across_months(self, db_conn):
        set_budget(db_conn, category_id=1, period_month="2026-10", limit_centavos=100000)
        set_budget(db_conn, category_id=1, period_month="2026-11", limit_centavos=120000)

        b_oct = get_budget(db_conn, category_id=1, period_month="2026-10")
        b_nov = get_budget(db_conn, category_id=1, period_month="2026-11")

        assert b_oct["limit_centavos"] == 100000
        assert b_nov["limit_centavos"] == 120000

    def test_get_budgets_for_month(self, db_conn):
        set_budget(db_conn, category_id=1, period_month="2026-10", limit_centavos=100000)
        set_budget(db_conn, category_id=2, period_month="2026-10", limit_centavos=50000)

        budgets = get_budgets_for_month(db_conn, "2026-10")
        assert len(budgets) == 2
        categories = {b["category_name"] for b in budgets}
        assert categories == {"Food", "Transportation"}

    def test_delete_budget(self, db_conn):
        b_id = set_budget(db_conn, category_id=1, period_month="2026-10", limit_centavos=100000)
        assert delete_budget(db_conn, b_id) is True
        assert get_budget(db_conn, category_id=1, period_month="2026-10") is None

    def test_delete_budget_for_category(self, db_conn):
        set_budget(db_conn, category_id=1, period_month="2026-10", limit_centavos=100000)
        assert delete_budget_for_category(db_conn, category_id=1, period_month="2026-10") is True
        assert get_budget(db_conn, category_id=1, period_month="2026-10") is None

