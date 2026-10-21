"""Shared pytest fixtures for the Expense Categorizer test suite."""

import os
import sys
import sqlite3
import pytest

# Ensure the project root is on sys.path so ``import expense_app`` works
# regardless of the directory pytest is invoked from.
_project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir)
)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from expense_app.data.database import init_database


@pytest.fixture
def db_conn(tmp_path):
    """Provide a fresh SQLite connection with initialized schema and seed data."""
    db_file = str(tmp_path / "test_expenses.db")
    conn = init_database(db_file)
    yield conn
    conn.close()


