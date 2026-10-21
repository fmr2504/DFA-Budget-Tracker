"""Application constants and default configuration.

This module defines seed categories, default rules, and app-wide
constants.  It has no Kivy or SQLite imports so it can be used
freely by the logic and data layers.
"""

# Application metadata
APP_NAME = "Expense Categorizer"
APP_VERSION = "0.1.0"

# Default expense categories seeded on first database initialization.
DEFAULT_CATEGORIES = [
    "Food",
    "Transportation",
    "Bills",
    "Shopping",
    "Education",
    "Health",
    "Household",
    "Entertainment",
    "Other",
]

# Starter categorization rules seeded on first initialization.
# Each tuple is (pattern, category_name, priority, match_mode).
# Higher priority value wins when rules from different categories match.
# match_mode: "substring" matches anywhere; "whole_word" requires word boundaries.
DEFAULT_RULES = [
    # Food
    ("jollibee", "Food", 10, "substring"),
    ("restaurant", "Food", 10, "substring"),
    ("lunch", "Food", 10, "whole_word"),
    ("dinner", "Food", 10, "whole_word"),
    ("coffee", "Food", 10, "substring"),
    # Transportation
    ("grab", "Transportation", 10, "whole_word"),
    ("jeepney", "Transportation", 10, "substring"),
    ("bus", "Transportation", 10, "whole_word"),
    ("train", "Transportation", 10, "whole_word"),
    ("gas", "Transportation", 10, "whole_word"),
    ("parking", "Transportation", 10, "substring"),
    # Bills
    ("electricity", "Bills", 10, "substring"),
    ("water bill", "Bills", 10, "substring"),
    ("internet", "Bills", 10, "substring"),
    ("mobile load", "Bills", 10, "substring"),
    # Shopping
    ("lazada", "Shopping", 10, "substring"),
    ("shopee", "Shopping", 10, "substring"),
    ("clothing", "Shopping", 10, "substring"),
    # Education
    ("tuition", "Education", 10, "substring"),
    ("textbook", "Education", 10, "substring"),
    ("school supplies", "Education", 10, "substring"),
    # Health
    ("pharmacy", "Health", 10, "substring"),
    ("clinic", "Health", 10, "substring"),
    ("medicine", "Health", 10, "substring"),
]

# The fallback category when no rule matches a description.
FALLBACK_CATEGORY = "Other"

