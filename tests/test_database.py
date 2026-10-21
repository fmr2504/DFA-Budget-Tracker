"""Tests for SQLite database schema, seeding, and path resolution (expense_app.data.database)."""

import os
import sqlite3
import pytest

from expense_app.config import DEFAULT_CATEGORIES, DEFAULT_RULES, FALLBACK_CATEGORY
from expense_app.data.database import (
    get_connection,
    get_database_path,
    init_database,
    seed_defaults,
)
from expense_app.data.repositories import (
    create_category,
    create_expense,
    deactivate_category,
    delete_category,
    get_categories,
    get_category_by_id,
    get_category_by_name,
    update_category,
)


class TestDatabasePath:
    def test_custom_path_override(self, tmp_path):
        custom = str(tmp_path / "custom.db")
        assert get_database_path(custom) == custom

    def test_env_var_override(self, monkeypatch, tmp_path):
        env_file = str(tmp_path / "env_expenses.db")
        monkeypatch.setenv("EXPENSE_TRACKER_DB_PATH", env_file)
        assert get_database_path() == env_file

    def test_default_path_is_absolute(self, monkeypatch):
        monkeypatch.delenv("EXPENSE_TRACKER_DB_PATH", raising=False)
        path = get_database_path()
        assert os.path.isabs(path)
        assert path.endswith(".db")


class TestDatabaseInitAndSchema:
    def test_tables_created(self, db_conn):
        cursor = db_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        assert {"categories", "category_rules", "expenses", "budgets"}.issubset(tables)

    def test_foreign_keys_pragma_enabled(self, db_conn):
        cursor = db_conn.cursor()
        cursor.execute("PRAGMA foreign_keys;")
        assert cursor.fetchone()[0] == 1


class TestDatabaseSeeding:
    def test_default_categories_seeded(self, db_conn):
        cats = get_categories(db_conn, active_only=False)
        cat_names = {c["name"].lower() for c in cats}
        expected = {c.lower() for c in DEFAULT_CATEGORIES}
        assert expected == cat_names

    def test_fallback_category_is_default(self, db_conn):
        cat = get_category_by_name(db_conn, FALLBACK_CATEGORY)
        assert cat is not None
        assert cat["is_default"] == 1

    def test_default_rules_seeded(self, db_conn):
        cursor = db_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM category_rules;")
        count = cursor.fetchone()[0]
        assert count == len(DEFAULT_RULES)

    def test_seeding_is_idempotent(self, db_conn, tmp_path):
        # Call seed_defaults again on existing db
        seed_defaults(db_conn)
        cursor = db_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM categories;")
        assert cursor.fetchone()[0] == len(DEFAULT_CATEGORIES)
        cursor.execute("SELECT COUNT(*) FROM category_rules;")
        assert cursor.fetchone()[0] == len(DEFAULT_RULES)


class TestCategoryConstraintsAndRepository:
    def test_duplicate_category_name_raises(self, db_conn):
        with pytest.raises(sqlite3.IntegrityError):
            create_category(db_conn, "Food")

    def test_empty_category_name_raises(self, db_conn):
        with pytest.raises(ValueError, match="empty"):
            create_category(db_conn, "   ")

    def test_create_and_get_category(self, db_conn):
        cat_id = create_category(db_conn, "Investment", color="#FF5733")
        cat = get_category_by_id(db_conn, cat_id)
        assert cat["name"] == "Investment"
        assert cat["color"] == "#FF5733"
        assert cat["is_active"] == 1

    def test_update_category(self, db_conn):
        cat = get_category_by_name(db_conn, "Shopping")
        update_category(db_conn, cat["id"], name="Online Shopping", color="#123456")
        updated = get_category_by_id(db_conn, cat["id"])
        assert updated["name"] == "Online Shopping"
        assert updated["color"] == "#123456"

    def test_deactivate_category(self, db_conn):
        cat = get_category_by_name(db_conn, "Entertainment")
        deactivate_category(db_conn, cat["id"])
        active_cats = {c["name"] for c in get_categories(db_conn, active_only=True)}
        assert "Entertainment" not in active_cats
        all_cats = {c["name"] for c in get_categories(db_conn, active_only=False)}
        assert "Entertainment" in all_cats

    def test_foreign_key_restricts_category_delete_with_expenses(self, db_conn):
        cat = get_category_by_name(db_conn, "Food")
        create_expense(
            db_conn,
            amount_centavos=15000,
            description="Jollibee",
            occurred_on="2026-10-21",
            category_id=cat["id"],
        )
        with pytest.raises(sqlite3.IntegrityError):
            delete_category(db_conn, cat["id"])

    def test_foreign_key_restricts_category_delete_with_rules(self, db_conn):
        cat = get_category_by_name(db_conn, "Transportation")
        with pytest.raises(sqlite3.IntegrityError):
            delete_category(db_conn, cat["id"])

