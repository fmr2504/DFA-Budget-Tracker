"""Data repositories for categories, rules, expenses, and budgets.

Provides parameterized CRUD operations and queries for all database tables.
All functions take a sqlite3.Connection with foreign keys enabled.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any, Optional

from expense_app.logic.categorizer import CategoryRule


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[dict[str, Any]]:
    return dict(row) if row is not None else None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Category Operations
# ---------------------------------------------------------------------------

def get_categories(
    conn: sqlite3.Connection, active_only: bool = True
) -> list[dict[str, Any]]:
    """Retrieve all categories, optionally filtering by active status."""
    cursor = conn.cursor()
    if active_only:
        cursor.execute(
            "SELECT * FROM categories WHERE is_active = 1 ORDER BY name ASC;"
        )
    else:
        cursor.execute("SELECT * FROM categories ORDER BY name ASC;")
    return [dict(row) for row in cursor.fetchall()]


def get_category_by_id(
    conn: sqlite3.Connection, category_id: int
) -> Optional[dict[str, Any]]:
    """Retrieve a single category by its ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE id = ?;", (category_id,))
    return _row_to_dict(cursor.fetchone())


def get_category_by_name(
    conn: sqlite3.Connection, name: str
) -> Optional[dict[str, Any]]:
    """Retrieve a single category by its name (case-insensitive)."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE name = ? COLLATE NOCASE;", (name,))
    return _row_to_dict(cursor.fetchone())


def create_category(
    conn: sqlite3.Connection,
    name: str,
    color: Optional[str] = None,
    is_active: bool = True,
    is_default: bool = False,
) -> int:
    """Insert a new category and return its ID."""
    name_clean = name.strip()
    if not name_clean:
        raise ValueError("Category name cannot be empty.")
    cursor = conn.cursor()
    with conn:
        cursor.execute(
            """
            INSERT INTO categories (name, color, is_active, is_default)
            VALUES (?, ?, ?, ?);
            """,
            (name_clean, color, 1 if is_active else 0, 1 if is_default else 0),
        )
    return cursor.lastrowid


def update_category(
    conn: sqlite3.Connection,
    category_id: int,
    name: Optional[str] = None,
    color: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_default: Optional[bool] = None,
) -> None:
    """Update an existing category's properties."""
    current = get_category_by_id(conn, category_id)
    if not current:
        raise ValueError(f"Category with id {category_id} not found.")

    new_name = name.strip() if name is not None else current["name"]
    if not new_name:
        raise ValueError("Category name cannot be empty.")

    new_color = color if color is not None else current["color"]
    new_active = (1 if is_active else 0) if is_active is not None else current["is_active"]
    new_default = (1 if is_default else 0) if is_default is not None else current["is_default"]

    with conn:
        conn.execute(
            """
            UPDATE categories
            SET name = ?, color = ?, is_active = ?, is_default = ?
            WHERE id = ?;
            """,
            (new_name, new_color, new_active, new_default, category_id),
        )


def deactivate_category(conn: sqlite3.Connection, category_id: int) -> None:
    """Deactivate a category instead of deleting it to preserve history."""
    update_category(conn, category_id, is_active=False)


def delete_category(conn: sqlite3.Connection, category_id: int) -> None:
    """Delete a category.

    Raises sqlite3.IntegrityError if expenses or rules still reference it.
    """
    with conn:
        conn.execute("DELETE FROM categories WHERE id = ?;", (category_id,))


# ---------------------------------------------------------------------------
# Category Rules Operations
# ---------------------------------------------------------------------------

def get_rules(
    conn: sqlite3.Connection, enabled_only: bool = True
) -> list[dict[str, Any]]:
    """Retrieve keyword rules joined with the category name."""
    cursor = conn.cursor()
    query = """
        SELECT r.id, r.pattern, r.category_id, c.name AS category_name,
               r.priority, r.match_mode, r.is_enabled
        FROM category_rules r
        JOIN categories c ON r.category_id = c.id
    """
    if enabled_only:
        query += " WHERE r.is_enabled = 1 AND c.is_active = 1"
    query += " ORDER BY r.priority DESC, r.id ASC;"

    cursor.execute(query)
    return [dict(row) for row in cursor.fetchall()]


def load_categorizer_rules(conn: sqlite3.Connection) -> list[CategoryRule]:
    """Load active rules from the database as CategoryRule objects."""
    rules_data = get_rules(conn, enabled_only=True)
    return [
        CategoryRule(
            pattern=row["pattern"],
            category=row["category_name"],
            priority=row["priority"],
            match_mode=row["match_mode"],
            is_enabled=bool(row["is_enabled"]),
        )
        for row in rules_data
    ]


def create_rule(
    conn: sqlite3.Connection,
    pattern: str,
    category_id: int,
    priority: int = 10,
    match_mode: str = "substring",
    is_enabled: bool = True,
) -> int:
    """Insert a new categorization rule."""
    clean_pat = pattern.strip()
    if not clean_pat:
        raise ValueError("Pattern cannot be empty.")
    if match_mode not in ("substring", "whole_word"):
        raise ValueError(f"Invalid match_mode: {match_mode}")

    cursor = conn.cursor()
    with conn:
        cursor.execute(
            """
            INSERT INTO category_rules (pattern, category_id, priority, match_mode, is_enabled)
            VALUES (?, ?, ?, ?, ?);
            """,
            (clean_pat, category_id, priority, match_mode, 1 if is_enabled else 0),
        )
    return cursor.lastrowid


def update_rule(
    conn: sqlite3.Connection,
    rule_id: int,
    pattern: Optional[str] = None,
    category_id: Optional[int] = None,
    priority: Optional[int] = None,
    match_mode: Optional[str] = None,
    is_enabled: Optional[bool] = None,
) -> None:
    """Update an existing rule."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM category_rules WHERE id = ?;", (rule_id,))
    current = cursor.fetchone()
    if not current:
        raise ValueError(f"Rule with id {rule_id} not found.")

    new_pattern = pattern.strip() if pattern is not None else current["pattern"]
    if not new_pattern:
        raise ValueError("Pattern cannot be empty.")

    new_cat_id = category_id if category_id is not None else current["category_id"]
    new_priority = priority if priority is not None else current["priority"]
    new_mode = match_mode if match_mode is not None else current["match_mode"]
    if new_mode not in ("substring", "whole_word"):
        raise ValueError(f"Invalid match_mode: {new_mode}")

    new_enabled = (1 if is_enabled else 0) if is_enabled is not None else current["is_enabled"]

    with conn:
        conn.execute(
            """
            UPDATE category_rules
            SET pattern = ?, category_id = ?, priority = ?, match_mode = ?, is_enabled = ?
            WHERE id = ?;
            """,
            (new_pattern, new_cat_id, new_priority, new_mode, new_enabled, rule_id),
        )


def delete_rule(conn: sqlite3.Connection, rule_id: int) -> None:
    """Delete a categorization rule."""
    with conn:
        conn.execute("DELETE FROM category_rules WHERE id = ?;", (rule_id,))


# ---------------------------------------------------------------------------
# Expense Operations
# ---------------------------------------------------------------------------

def create_expense(
    conn: sqlite3.Connection,
    amount_centavos: int,
    description: str,
    occurred_on: str,
    category_id: int,
    category_source: str = "automatic",
    matched_pattern: Optional[str] = None,
) -> int:
    """Insert a new expense record."""
    if amount_centavos <= 0:
        raise ValueError("Amount must be greater than zero.")
    clean_desc = description.strip()
    if not clean_desc:
        raise ValueError("Description cannot be empty.")
    if category_source not in ("automatic", "manual"):
        raise ValueError(f"Invalid category_source: {category_source}")

    created_at = _now_iso()
    cursor = conn.cursor()
    with conn:
        cursor.execute(
            """
            INSERT INTO expenses (
                amount_centavos, description, occurred_on, category_id,
                category_source, matched_pattern, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, NULL);
            """,
            (
                amount_centavos,
                clean_desc,
                occurred_on,
                category_id,
                category_source,
                matched_pattern,
                created_at,
            ),
        )
    return cursor.lastrowid


def get_expense_by_id(
    conn: sqlite3.Connection, expense_id: int
) -> Optional[dict[str, Any]]:
    """Retrieve an expense by ID, including category name."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT e.*, c.name AS category_name
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.id = ?;
        """,
        (expense_id,),
    )
    return _row_to_dict(cursor.fetchone())


def get_expenses(
    conn: sqlite3.Connection,
    start_date: Optional[str] = None,
    end_date_exclusive: Optional[str] = None,
    category_id: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> list[dict[str, Any]]:
    """Query expenses with optional date range and category filtering."""
    query = """
        SELECT e.*, c.name AS category_name
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE 1=1
    """
    params: list[Any] = []

    if start_date:
        query += " AND e.occurred_on >= ?"
        params.append(start_date)
    if end_date_exclusive:
        query += " AND e.occurred_on < ?"
        params.append(end_date_exclusive)
    if category_id is not None:
        query += " AND e.category_id = ?"
        params.append(category_id)

    query += " ORDER BY e.occurred_on DESC, e.id DESC"

    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)

    cursor = conn.cursor()
    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def update_expense(
    conn: sqlite3.Connection,
    expense_id: int,
    amount_centavos: Optional[int] = None,
    description: Optional[str] = None,
    occurred_on: Optional[str] = None,
    category_id: Optional[int] = None,
    category_source: Optional[str] = None,
    matched_pattern: Optional[str] = None,
) -> None:
    """Update an expense record."""
    current = get_expense_by_id(conn, expense_id)
    if not current:
        raise ValueError(f"Expense with id {expense_id} not found.")

    new_amount = amount_centavos if amount_centavos is not None else current["amount_centavos"]
    if new_amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    new_desc = description.strip() if description is not None else current["description"]
    if not new_desc:
        raise ValueError("Description cannot be empty.")

    new_date = occurred_on if occurred_on is not None else current["occurred_on"]
    new_cat_id = category_id if category_id is not None else current["category_id"]

    new_source = category_source if category_source is not None else current["category_source"]
    if new_source not in ("automatic", "manual"):
        raise ValueError(f"Invalid category_source: {new_source}")

    new_pattern = matched_pattern if matched_pattern is not None else current["matched_pattern"]
    updated_at = _now_iso()

    with conn:
        conn.execute(
            """
            UPDATE expenses
            SET amount_centavos = ?, description = ?, occurred_on = ?,
                category_id = ?, category_source = ?, matched_pattern = ?,
                updated_at = ?
            WHERE id = ?;
            """,
            (
                new_amount,
                new_desc,
                new_date,
                new_cat_id,
                new_source,
                new_pattern,
                updated_at,
                expense_id,
            ),
        )


def delete_expense(conn: sqlite3.Connection, expense_id: int) -> bool:
    """Delete an expense record by ID."""
    with conn:
        cursor = conn.execute("DELETE FROM expenses WHERE id = ?;", (expense_id,))
    return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# Budget Operations
# ---------------------------------------------------------------------------

def get_budget(
    conn: sqlite3.Connection, category_id: int, period_month: str
) -> Optional[dict[str, Any]]:
    """Retrieve a budget limit for a specific category and month."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT b.*, c.name AS category_name
        FROM budgets b
        JOIN categories c ON b.category_id = c.id
        WHERE b.category_id = ? AND b.period_month = ?;
        """,
        (category_id, period_month),
    )
    return _row_to_dict(cursor.fetchone())


def get_budgets_for_month(
    conn: sqlite3.Connection, period_month: str
) -> list[dict[str, Any]]:
    """Retrieve all budget limits set for a given month."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT b.*, c.name AS category_name
        FROM budgets b
        JOIN categories c ON b.category_id = c.id
        WHERE b.period_month = ?
        ORDER BY c.name ASC;
        """,
        (period_month,),
    )
    return [dict(row) for row in cursor.fetchall()]


def set_budget(
    conn: sqlite3.Connection,
    category_id: int,
    period_month: str,
    limit_centavos: int,
) -> int:
    """Create or update (upsert) a budget limit for a category and month."""
    if limit_centavos <= 0:
        raise ValueError("Budget limit must be greater than zero.")

    cursor = conn.cursor()
    with conn:
        cursor.execute(
            """
            INSERT INTO budgets (category_id, period_month, limit_centavos)
            VALUES (?, ?, ?)
            ON CONFLICT(category_id, period_month)
            DO UPDATE SET limit_centavos = excluded.limit_centavos;
            """,
            (category_id, period_month, limit_centavos),
        )
    return cursor.lastrowid


def delete_budget(conn: sqlite3.Connection, budget_id: int) -> bool:
    """Delete a budget by its primary key ID."""
    with conn:
        cursor = conn.execute("DELETE FROM budgets WHERE id = ?;", (budget_id,))
    return cursor.rowcount > 0


def delete_budget_for_category(
    conn: sqlite3.Connection, category_id: int, period_month: str
) -> bool:
    """Delete a budget for a given category and month."""
    with conn:
        cursor = conn.execute(
            "DELETE FROM budgets WHERE category_id = ? AND period_month = ?;",
            (category_id, period_month),
        )
    return cursor.rowcount > 0
