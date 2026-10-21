"""Tests for budget persistence and operations (expense_app.data.repositories)."""

import sqlite3
import pytest

from expense_app.data.repositories import (
    delete_budget,
    delete_budget_for_category,
    get_budget,
    get_budgets_for_month,
    set_budget,
)


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

