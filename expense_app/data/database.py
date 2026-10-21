"""Database connection, schema management, and seeding.

Provides SQLite initialization with foreign keys enabled, table definitions
for categories, category_rules, expenses, and budgets, and idempotent seeding
of initial default categories and rules.
"""

from __future__ import annotations

import os
import sqlite3
from typing import Optional

from expense_app.config import DEFAULT_CATEGORIES, DEFAULT_RULES, FALLBACK_CATEGORY


def get_database_path(custom_path: Optional[str] = None) -> str:
    """Return the absolute path to the SQLite database file.

    Priority:
    1. Explicit custom_path if provided.
    2. EXPENSE_TRACKER_DB_PATH environment variable if set.
    3. Kivy App user_data_dir if running inside Kivy.
    4. Local project/app fallback directory.
    """
    if custom_path:
        return custom_path

    env_path = os.environ.get("EXPENSE_TRACKER_DB_PATH")
    if env_path:
        return env_path

    # Check if running within a Kivy app context
    try:
        from kivy.app import App

        app = App.get_running_app()
        if app and getattr(app, "user_data_dir", None):
            data_dir = app.user_data_dir
            os.makedirs(data_dir, exist_ok=True)
            return os.path.join(data_dir, "expenses.db")
    except Exception:
        pass

    # Default fallback: data directory in project root or current working dir
    default_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    )
    return os.path.join(default_dir, "expenses.db")


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Open and return a SQLite connection with foreign keys enabled."""
    path = get_database_path(db_path)
    if path != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
    color TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    is_default INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS category_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern TEXT NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    priority INTEGER NOT NULL,
    match_mode TEXT NOT NULL DEFAULT 'substring' CHECK (match_mode IN ('substring', 'whole_word')),
    is_enabled INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount_centavos INTEGER NOT NULL CHECK (amount_centavos > 0),
    description TEXT NOT NULL,
    occurred_on TEXT NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    category_source TEXT NOT NULL CHECK (category_source IN ('automatic', 'manual')),
    matched_pattern TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    period_month TEXT NOT NULL,
    limit_centavos INTEGER NOT NULL CHECK (limit_centavos > 0),
    UNIQUE(category_id, period_month)
);

CREATE INDEX IF NOT EXISTS idx_expenses_occurred_on ON expenses(occurred_on);
CREATE INDEX IF NOT EXISTS idx_expenses_category_id ON expenses(category_id);
CREATE INDEX IF NOT EXISTS idx_budgets_period_month ON budgets(period_month);
"""


def init_database(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Initialize tables and seed default categories and rules idempotently."""
    conn = get_connection(db_path)
    with conn:
        conn.executescript(SCHEMA_SQL)
        seed_defaults(conn)
    return conn


def seed_defaults(conn: sqlite3.Connection) -> None:
    """Seed default categories and keyword rules if categories table is empty."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM categories;")
    count = cursor.fetchone()[0]

    if count > 0:
        return

    # Insert default categories
    category_map: dict[str, int] = {}
    for cat_name in DEFAULT_CATEGORIES:
        is_default = 1 if cat_name.lower() == FALLBACK_CATEGORY.lower() else 0
        cursor.execute(
            """
            INSERT INTO categories (name, is_active, is_default)
            VALUES (?, 1, ?);
            """,
            (cat_name, is_default),
        )
        category_map[cat_name.lower()] = cursor.lastrowid

    # Insert starter rules
    for pattern, cat_name, priority, match_mode in DEFAULT_RULES:
        cat_id = category_map.get(cat_name.lower())
        if cat_id is not None:
            cursor.execute(
                """
                INSERT INTO category_rules (pattern, category_id, priority, match_mode, is_enabled)
                VALUES (?, ?, ?, ?, 1);
                """,
                (pattern, cat_id, priority, match_mode),
            )

