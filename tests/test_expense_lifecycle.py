"""End-to-end service and lifecycle tests for expense creation, categorization, and ledger management."""

from datetime import date
import pytest

from expense_app.data.repositories import (
    create_expense,
    delete_expense,
    get_category_by_name,
    get_expense_by_id,
    get_expenses,
    load_categorizer_rules,
    update_expense,
)
from expense_app.logic.categorizer import Categorizer
from expense_app.logic.money import format_amount, parse_amount
from expense_app.logic.reporting import month_range, validate_date


@pytest.fixture
def categorizer(db_conn):
    rules = load_categorizer_rules(db_conn)
    return Categorizer(rules, fallback_category="Other")


class TestExpenseLifecycle:
    def test_automatic_categorization_and_save(self, db_conn, categorizer):
        # User types "Jollibee chicken dinner"
        description = "Jollibee chicken dinner"
        result = categorizer.categorize(description)

        assert result.suggested_category == "Food"
        assert not result.is_fallback
        assert result.matches[0].rule.pattern == "jollibee"

        cat_row = get_category_by_name(db_conn, result.suggested_category)
        assert cat_row is not None

        exp_id = create_expense(
            conn=db_conn,
            amount_centavos=parse_amount("250.00"),
            description=description,
            occurred_on="2026-10-21",
            category_id=cat_row["id"],
            category_source="automatic",
            matched_pattern=result.matches[0].rule.pattern,
        )

        saved = get_expense_by_id(db_conn, exp_id)
        assert saved["amount_centavos"] == 25000
        assert saved["category_name"] == "Food"
        assert saved["category_source"] == "automatic"
        assert saved["matched_pattern"] == "jollibee"

    def test_manual_override_persists(self, db_conn, categorizer):
        # Description "Grab ride to office" matches Transportation rule "grab"
        description = "Grab ride to office"
        result = categorizer.categorize(description)
        assert result.suggested_category == "Transportation"

        # User chooses to override category to "Bills"
        override_cat = get_category_by_name(db_conn, "Bills")
        exp_id = create_expense(
            conn=db_conn,
            amount_centavos=parse_amount("180.50"),
            description=description,
            occurred_on="2026-10-21",
            category_id=override_cat["id"],
            category_source="manual",
            matched_pattern=None,
        )

        saved = get_expense_by_id(db_conn, exp_id)
        assert saved["category_name"] == "Bills"
        assert saved["category_source"] == "manual"
        assert saved["matched_pattern"] is None

    def test_edit_does_not_revert_manual_category(self, db_conn):
        cat = get_category_by_name(db_conn, "Shopping")
        exp_id = create_expense(
            conn=db_conn,
            amount_centavos=10000,
            description="Item from market",
            occurred_on="2026-10-21",
            category_id=cat["id"],
            category_source="manual",
        )

        # Edit description and amount only
        update_expense(
            conn=db_conn,
            expense_id=exp_id,
            amount_centavos=15000,
            description="New description",
        )

        updated = get_expense_by_id(db_conn, exp_id)
        assert updated["amount_centavos"] == 15000
        assert updated["description"] == "New description"
        assert updated["category_source"] == "manual"
        assert updated["category_name"] == "Shopping"

    def test_delete_removes_transaction(self, db_conn):
        cat = get_category_by_name(db_conn, "Food")
        exp1 = create_expense(db_conn, 5000, "Breakfast", "2026-10-21", cat["id"])
        exp2 = create_expense(db_conn, 8000, "Lunch", "2026-10-21", cat["id"])

        assert delete_expense(db_conn, exp1) is True
        assert get_expense_by_id(db_conn, exp1) is None
        assert get_expense_by_id(db_conn, exp2) is not None

    def test_transactions_ledger_sorting_and_filtering(self, db_conn):
        cat_food = get_category_by_name(db_conn, "Food")
        cat_trans = get_category_by_name(db_conn, "Transportation")

        create_expense(db_conn, 1000, "Coffee", "2026-10-01", cat_food["id"])
        create_expense(db_conn, 2000, "Jeep", "2026-10-15", cat_trans["id"])
        create_expense(db_conn, 3000, "Dinner", "2026-10-20", cat_food["id"])

        # Fetch all: newest first
        all_exp = get_expenses(db_conn)
        assert len(all_exp) == 3
        assert [e["description"] for e in all_exp] == ["Dinner", "Jeep", "Coffee"]

        # Filter by Food only
        food_exp = get_expenses(db_conn, category_id=cat_food["id"])
        assert len(food_exp) == 2
        assert [e["description"] for e in food_exp] == ["Dinner", "Coffee"]

    def test_validation_helpers_prevent_bad_data(self):
        # Invalid amounts
        with pytest.raises(ValueError):
            parse_amount("")
        with pytest.raises(ValueError):
            parse_amount("0")
        with pytest.raises(ValueError):
            parse_amount("-10")
        with pytest.raises(ValueError):
            parse_amount("invalid")

        # Invalid dates
        assert validate_date("2026-13-01") is False
        assert validate_date("not-a-date") is False
        assert validate_date("2026-10-21") is True

