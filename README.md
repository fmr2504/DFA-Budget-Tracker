# Automatic Expense Categorizer

Offline-first personal expense tracking application for Android,
built with Python and Kivy.  Uses a DFA-based keyword matcher to
automatically suggest expense categories from transaction descriptions.

## Features (planned)

- Add, edit, and delete expenses with Philippine peso amounts (₱).
- DFA-powered automatic category suggestions from descriptions.
- Monthly spending reports with per-category breakdowns.
- Per-category monthly budgets with progress tracking.
- Fully offline — no cloud, bank, or network access required.

## Prerequisites

- Python 3.11 or later
- A virtual environment is recommended

## Setup

```bash
# Create and activate a virtual environment (if not already done)
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt
```

## Run the App

```bash
python main.py
```

The app launches a Kivy window with placeholder screens.  Navigation
buttons at the bottom switch between Dashboard, Add Expense,
Transactions, Reports, and Budgets.

## Run Tests

```bash
python -m pytest -v
```

## Project Structure

```
DFA_Budget_Tracker/
├── main.py                  # App entry point
├── substring_dfa.py         # Original binary DFA (preserved)
├── expense_app/
│   ├── app.py               # Kivy App class and screen setup
│   ├── config.py            # Default categories, rules, constants
│   ├── logic/               # Business logic (DFA, categorizer, money)
│   ├── data/                # SQLite database and repositories
│   └── ui/                  # Kivy screens and components
│       └── screens/
└── tests/                   # pytest test suite
```

## Technology Stack

| Component     | Technology          |
|---------------|---------------------|
| Language      | Python              |
| UI framework  | Kivy                |
| Database      | SQLite (sqlite3)    |
| Testing       | pytest              |
| Android build | Buildozer (planned) |

## Currency

All monetary values are stored as **integer centavos** internally
(e.g., ₱125.50 → 12550) to avoid floating-point rounding errors.
Amounts are displayed with the `₱` symbol and two decimal places.

## License

Private project — not currently published.

