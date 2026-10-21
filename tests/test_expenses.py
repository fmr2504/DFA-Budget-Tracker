"""Tests for expense persistence and category rules (expense_app.data.repositories)."""

import sqlite3
import pytest

from expense_app.data.repositories import (
    create_expense,
    create_rule,
    delete_expense,
    delete_rule,
    get_expense_by_id,
    get_expenses,
    get_rules,
    load_categorizer_rules,
    update_expense,
    update_rule,
)


class TestExpenseCRUD:
    def test_create_automatic_expense(self, db_conn):
        exp_id = create_expense(
            db_conn,
            amount_centavos=15000,
            description="Jollibee lunch",
            occurred_on="2026-10-21",
            category_id=1,
            category_source="automatic",
            matched_pattern="jollibee",
        )
        assert exp_id > 0
        exp = get_expense_by_id(db_conn, exp_id)
        assert exp["amount_centavos"] == 15000
        assert exp["description"] == "Jollibee lunch"
        assert exp["occurred_on"] == "2026-10-21"
        assert exp["category_source"] == "automatic"
        assert exp["matched_pattern"] == "jollibee"
        assert exp["created_at"] is not None
        assert exp["updated_at"] is None

    def test_create_manual_expense(self, db_conn):
        exp_id = create_expense(
            db_conn,
            amount_centavos=25000,
            description="Special gift",
            occurred_on="2026-10-21",
            category_id=1,
            category_source="manual",
        )
        exp = get_expense_by_id(db_conn, exp_id)
        assert exp["category_source"] == "manual"
        assert exp["matched_pattern"] is None

    def test_zero_amount_rejected(self, db_conn):
        with pytest.raises(ValueError, match="greater than zero"):
            create_expense(
                db_conn,
                amount_centavos=0,
                description="Zero item",
                occurred_on="2026-10-21",
                category_id=1,
            )

    def test_negative_amount_rejected(self, db_conn):
        with pytest.raises(ValueError, match="greater than zero"):
            create_expense(
                db_conn,
                amount_centavos=-500,
                description="Negative item",
                occurred_on="2026-10-21",
                category_id=1,
            )

    def test_empty_description_rejected(self, db_conn):
        with pytest.raises(ValueError, match="empty"):
            create_expense(
                db_conn,
                amount_centavos=1000,
                description="   ",
                occurred_on="2026-10-21",
                category_id=1,
            )

    def test_invalid_category_source_rejected(self, db_conn):
        with pytest.raises(ValueError, match="Invalid category_source"):
            create_expense(
                db_conn,
                amount_centavos=1000,
                description="Coffee",
                occurred_on="2026-10-21",
                category_id=1,
                category_source="invalid",
            )

    def test_nonexistent_category_id_rejected(self, db_conn):
        with pytest.raises(sqlite3.IntegrityError):
            create_expense(
                db_conn,
                amount_centavos=1000,
                description="Test",
                occurred_on="2026-10-21",
                category_id=9999,
            )

    def test_update_expense_fields(self, db_conn):
        exp_id = create_expense(
            db_conn,
            amount_centavos=10000,
            description="Lunch",
            occurred_on="2026-10-20",
            category_id=1,
            category_source="manual",
        )
        update_expense(
            db_conn,
            expense_id=exp_id,
            amount_centavos=12500,
            description="Lunch with drinks",
        )
        updated = get_expense_by_id(db_conn, exp_id)
        assert updated["amount_centavos"] == 12500
        assert updated["description"] == "Lunch with drinks"
        # Manual category preserved
        assert updated["category_source"] == "manual"
        assert updated["updated_at"] is not None

    def test_delete_expense(self, db_conn):
        exp_id = create_expense(
            db_conn,
            amount_centavos=10000,
            description="Lunch",
            occurred_on="2026-10-20",
            category_id=1,
        )
        assert delete_expense(db_conn, exp_id) is True
        assert get_expense_by_id(db_conn, exp_id) is None
        assert delete_expense(db_conn, exp_id) is False


class TestExpenseQueries:
    def test_filter_by_date_and_category(self, db_conn):
        # Category 1 = Food, Category 2 = Transportation (seeded)
        create_expense(db_conn, 1000, "Food Sept", "2026-09-30", category_id=1)
        create_expense(db_conn, 2000, "Food Oct 1", "2026-10-01", category_id=1)
        create_expense(db_conn, 3000, "Food Oct 15", "2026-10-15", category_id=1)
        create_expense(db_conn, 4000, "Transport Oct", "2026-10-10", category_id=2)
        create_expense(db_conn, 5000, "Food Nov", "2026-11-01", category_id=1)

        # Filter for October 2026 only
        oct_expenses = get_expenses(
            db_conn,
            start_date="2026-10-01",
            end_date_exclusive="2026-11-01",
        )
        assert len(oct_expenses) == 3
        # Sorted descending by date
        assert [e["amount_centavos"] for e in oct_expenses] == [3000, 4000, 2000]

        # Filter October + Food only
        oct_food = get_expenses(
            db_conn,
            start_date="2026-10-01",
            end_date_exclusive="2026-11-01",
            category_id=1,
        )
        assert len(oct_food) == 2
        assert [e["amount_centavos"] for e in oct_food] == [3000, 2000]

    def test_pagination(self, db_conn):
        for i in range(10):
            create_expense(
                db_conn,
                1000 + i,
                f"Item {i}",
                f"2026-10-{i+1:02d}",
                category_id=1,
            )
        page1 = get_expenses(db_conn, limit=3, offset=0)
        assert len(page1) == 3
        assert page1[0]["description"] == "Item 9"

        page2 = get_expenses(db_conn, limit=3, offset=3)
        assert len(page2) == 3
        assert page2[0]["description"] == "Item 6"


class TestCategoryRulesRepository:
    def test_load_categorizer_rules(self, db_conn):
        rules = load_categorizer_rules(db_conn)
        assert len(rules) > 0
        patterns = {r.pattern for r in rules}
        assert "jollibee" in patterns
        assert "grab" in patterns

    def test_create_and_update_rule(self, db_conn):
        rule_id = create_rule(
            db_conn,
            pattern="angkas",
            category_id=2,  # Transportation
            priority=15,
            match_mode="whole_word",
        )
        assert rule_id > 0

        update_rule(db_conn, rule_id, priority=25)
        rules = get_rules(db_conn, enabled_only=False)
        angkas = next(r for r in rules if r["id"] == rule_id)
        assert angkas["priority"] == 25
        assert angkas["pattern"] == "angkas"

    def test_delete_rule(self, db_conn):
        rule_id = create_rule(db_conn, "testpattern", 1)
        delete_rule(db_conn, rule_id)
        rules = get_rules(db_conn, enabled_only=False)
        assert not any(r["id"] == rule_id for r in rules)

