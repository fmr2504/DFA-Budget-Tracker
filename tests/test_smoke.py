"""Smoke tests — verify project structure and imports."""


def test_expense_app_package_imports():
    """The expense_app package and its sub-packages are importable."""
    import expense_app
    import expense_app.logic
    import expense_app.data
    import expense_app.config


def test_config_defaults_populated():
    """config.py exposes non-empty default categories and rules."""
    from expense_app.config import (
        DEFAULT_CATEGORIES,
        DEFAULT_RULES,
        FALLBACK_CATEGORY,
        APP_NAME,
    )

    assert len(DEFAULT_CATEGORIES) > 0
    assert len(DEFAULT_RULES) > 0
    assert FALLBACK_CATEGORY in DEFAULT_CATEGORIES
    assert isinstance(APP_NAME, str) and len(APP_NAME) > 0


def test_default_rules_reference_valid_categories():
    """Every rule's category must appear in DEFAULT_CATEGORIES."""
    from expense_app.config import DEFAULT_CATEGORIES, DEFAULT_RULES

    category_set = set(DEFAULT_CATEGORIES)
    for pattern, category, priority, match_mode in DEFAULT_RULES:
        assert category in category_set, (
            f"Rule pattern '{pattern}' references unknown "
            f"category '{category}'"
        )
        assert isinstance(priority, int) and priority > 0
        assert match_mode in ("substring", "whole_word")

