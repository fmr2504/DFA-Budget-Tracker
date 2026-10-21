"""Shared pytest fixtures for the Expense Categorizer test suite."""

import os
import sys

# Ensure the project root is on sys.path so ``import expense_app`` works
# regardless of the directory pytest is invoked from.
_project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir)
)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

