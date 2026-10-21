# Automatic Expense Categorizer

An offline-first, mobile personal expense tracking application for Android
built with **Python, Kivy, DFA pattern matching, and SQLite**.

The application automatically categorizes expenses as you type transaction descriptions
using a deterministic finite automaton (DFA) keyword-matching algorithm, persists
data in a local SQLite database, and provides monthly spending breakdowns and category budgets.

---

## Features

- **DFA-Powered Real-time Categorization**:
  - Live category suggestions as you type expense descriptions (e.g., `"Jollibee lunch"` $\rightarrow$ `Food`, `"Jeepney fare"` $\rightarrow$ `Transportation`).
  - Strict whole-word boundary matching (e.g. `"gas"` matches `"gas station"` but not `"gasoline"`).
  - Explicit manual overrides tracked and permanently preserved.
- **Accurate Money Handling**:
  - All monetary values are stored as **integer centavos** (e.g. ₱125.50 $\rightarrow$ `12550`) to eliminate floating-point rounding errors.
  - Formatted with Philippine Peso (`₱`) currency symbols.
- **Transaction Ledger**:
  - Chronological transaction history sorted newest-first.
  - Category filtering, transaction editing, and safe deletion with confirmation dialogs.
- **Monthly Analytics & Reports**:
  - Monthly spending totals, transaction counts, and category percentage breakdown bars.
  - Previous/next month navigation with automatic year roll-over (`YYYY-MM`).
- **Category Budgets**:
  - Set per-category monthly spending limits.
  - Live progress tracking with visual progress bars strictly clamped to `[0, 1]`.
  - Color-coded three-tier status alerts: **On Track** ($< 80\%$), **Near Limit** ($80\% - 100\%$), and **Over Budget** ($> 100\%$).
- **Offline-First & Private**:
  - Zero cloud dependencies, zero network requests, and zero analytics.
  - Data is saved in the platform-appropriate app storage directory (`App.user_data_dir` on Android / desktop).

---

## Architecture Overview

```
DFA_Budget_Tracker/
├── main.py                          # App entry point
├── buildozer.spec                   # Android Buildozer packaging configuration
├── substring_dfa.py                 # Original binary DFA reference (preserved)
│
├── expense_app/
│   ├── app.py                       # Kivy App, ScreenManager, & Bottom Navigation
│   ├── config.py                    # Default categories, starter rules, constants
│   │
│   ├── logic/                       # Pure business logic (Zero Kivy/SQLite dependencies)
│   │   ├── dfa.py                   # Generalized text DFA (construction & simulation)
│   │   ├── categorizer.py           # Multi-rule matching & priority conflict resolution
│   │   ├── money.py                 # Centavo integer parsing & peso formatting
│   │   └── reporting.py             # Pure report analytics & budget progress calculations
│   │
│   ├── data/                        # Persistence Layer
│   │   ├── database.py              # SQLite connection, schema, & idempotent seeding
│   │   └── repositories.py          # Parameterized CRUD operations for records
│   │
│   └── ui/                          # Presentation Layer (Kivy)
│       ├── components.py            # Reusable mobile widgets (Cards, Dialogs, Inputs, Buttons)
│       └── screens/
│           ├── dashboard.py         # Summary metrics, recent transactions, & quick shortcuts
│           ├── add_expense.py       # Live DFA expense recording form
│           ├── transactions.py      # Expense ledger with filtering, edit, & delete
│           ├── reports.py           # Monthly spending analytics & visual breakdown bars
│           └── budgets.py           # Category budget limits & progress tracking
│
└── tests/                           # Comprehensive automated test suite
    ├── conftest.py                  # Pytest fixtures (temporary SQLite DB)
    ├── test_dfa.py                  # DFA engine tests (55 tests)
    ├── test_categorizer.py          # Categorizer & rule matching tests (45 tests)
    ├── test_money.py                # Centavo parsing and formatting tests (20 tests)
    ├── test_database.py             # Schema, foreign keys, & seeding tests (11 tests)
    ├── test_expenses.py             # Repository CRUD & pagination tests (14 tests)
    ├── test_reporting.py            # Month range & date validation tests (14 tests)
    ├── test_reports.py              # Report math & database integration tests (14 tests)
    ├── test_budgets.py              # Budget limits, upsert, & progress tests (16 tests)
    ├── test_ui.py                   # Widget trees & navigation tests (13 tests)
    ├── test_smoke.py                # Package imports & config checks (3 tests)
    └── test_integration_scenario.py # Full 10-step guide acceptance scenario (1 test)
```

---

## Development Setup

### Prerequisites
- Python 3.11 or later
- Virtual environment (`venv`)

### Installation
```bash
# 1. Clone repository and navigate to root
cd DFA_Budget_Tracker

# 2. Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements-dev.txt
```

---

## Running the Application (Desktop)

```bash
python main.py
```

The application opens in a desktop window optimized for mobile touch targets and navigation.

---

## Running Automated Tests

Run the full pytest suite:

```bash
python -m pytest -v
```

Bytecode verification:
```bash
python -m compileall main.py expense_app -q
```

---

## Android Packaging with Buildozer

Buildozer packages the Python and Kivy code into an Android `.apk` file using `python-for-android`.

### Requirements
- Linux or macOS (On Windows, use **WSL2**).
- OpenJDK 17, Android SDK tools, Git, and system build libraries (`libffi-dev`, `libssl-dev`, `zlib1g-dev`, `build-essential`).

### Build Steps (Inside Linux / WSL2)
```bash
# 1. Install buildozer
pip install --user buildozer

# 2. Build debug APK
buildozer -v android debug
```

The output debug APK will be created in the `bin/` directory:
```
bin/expensecategorizer-0.1.0-arm64-v8a-debug.apk
```

Install and test on an Android device via USB debugging:
```bash
adb install -r bin/expensecategorizer-0.1.0-arm64-v8a-debug.apk
```

---

## Keyword Library & Categorization Rules

The application uses an extensive seed keyword library in `expense_app/config.py` (`DEFAULT_RULES`) containing over 600 rules across 9 categories (`Food`, `Transportation`, `Bills`, `Shopping`, `Education`, `Health`, `Household`, `Entertainment`, and `Other`), with tailored support for Philippine everyday expenses and Taglish terminology.

### How to Add or Update Keywords

1. Open `expense_app/config.py`.
2. Locate the appropriate category under `DEFAULT_RULES`.
3. Add a 4-tuple: `(pattern, category_name, priority, match_mode)`:
   - `pattern`: Lowercase search phrase or word (e.g. `"pandesal"`, `"meralco"`).
   - `category_name`: One of the categories defined in `DEFAULT_CATEGORIES`.
   - `priority`: Integer priority (default `10`; higher values take precedence during conflicts).
   - `match_mode`:
     - `"whole_word"`: Recommended for single words and short terms to prevent accidental substring collisions (e.g., `"fare"` vs `"farewell"`).
     - `"substring"`: Recommended for unique multiword phrases or distinct brand names (e.g., `"water bill"`, `"mercury drug"`).
4. Run automated tests to verify matching:
   ```bash
   python -m pytest tests/test_categorizer.py
   ```
5. **Database Updates**: `init_database` and `seed_defaults` idempotently seed newly added default rules into existing SQLite databases without overwriting user customizations or duplicating existing rules.

---

## Offline-First Guarantee & Privacy

- **No Network Access**: The app requests no internet permissions in `buildozer.spec`.
- **Local Storage**: All categories, keyword rules, expenses, and monthly budgets are stored in a local SQLite file (`expenses.db`) in the application's private data sandbox.
- **Zero Third-party Services**: No bank APIs, advertising SDKs, cloud logins, or telemetry tracking.
