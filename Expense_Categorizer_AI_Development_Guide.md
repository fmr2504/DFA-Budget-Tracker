**Automatic Expense Categorizer for Android with Python, Kivy, DFA, and SQLite**

**Purpose:** A practical, phase-by-phase guide for using an AI coding assistant to build a mobile expense-tracking app from the existing Python DFA pattern detector through **expense entry, automatic categorization, transaction history, monthly reports, and budgets**.

**Target:** Android-first, offline-first, single user, manual expense entry, Philippine pesos (PHP / ₱). The guide favors a working and testable MVP over advanced features.

### Guide roadmap

1. Define the app behavior, categories, stack, and project structure.
2. Give your coding assistant persistent instructions and build in small phases.
3. Refactor the current binary DFA for text pattern detection.
4. Add money helpers, SQLite persistence, and the Kivy screens.
5. Complete expense entry and transaction management.
6. Build monthly reports and per-category budgets.
7. Test end-to-end and package a debug APK for Android.

---

## 1. Product goal and scope

Build a mobile application that lets a user record an expense, receive a category suggestion from a DFA-powered keyword matcher, correct the suggestion, and see spending totals and budget progress.

### Included by the end of this guide

1. Project structure and development environment.
2. Text-capable DFA matching engine adapted from `substring_dfa.py`.
3. Configurable keyword-to-category rules.
4. Local SQLite storage for categories, expenses, rules, and monthly budgets.
5. Kivy screen navigation and a usable layout.
6. Add, view, edit, and delete expense flows.
7. Monthly reports with category breakdowns.
8. Per-category monthly budgets and in-app budget status.
9. Unit tests, manual acceptance tests, and an Android debug APK workflow.

### Deliberately out of scope for the first release

- Automatic bank/SMS scraping or bank account connections.
- Cloud accounts, syncing, and online storage.
- AI/LLM-based classification.
- Recurring transactions, multiple currencies, income accounting, debt tracking, and investments.
- Push notifications, shared budgets, and encrypted cloud backup.

Keep the first version local and understandable. Add these later only if the working MVP is stable.

## 2. Product behavior and rules

### Expense flow

1. The user opens **Add Expense**.
2. Enters an amount, description, and date; the date defaults to today.
3. The app runs the categorizer against the description and suggests a category.
4. The user accepts the suggestion or manually chooses another category.
5. The app saves the expense to SQLite and confirms the save.
6. Dashboard totals, reports, and budget progress update from saved data.

### Initial categories

Seed these editable categories: **Food, Transportation, Bills, Shopping, Education, Health, Household, Entertainment, and Other**. Users should be able to change a category assignment. Do not permanently delete a category that is used by existing expenses; deactivate it or prevent deletion with a clear explanation.

### Starter categorization rules

| Pattern examples | Suggested category |
|---|---|
| `jollibee`, `restaurant`, `lunch`, `dinner`, `coffee` | Food |
| `grab`, `jeepney`, `bus`, `train`, `gas`, `parking` | Transportation |
| `electricity`, `water bill`, `internet`, `mobile load` | Bills |
| `lazada`, `shopee`, `clothing` | Shopping |
| `tuition`, `textbook`, `school supplies` | Education |
| `pharmacy`, `clinic`, `medicine` | Health |

These are examples, not universal truths. A merchant name can represent different kinds of purchases. Always allow a manual override. Be careful with short keywords: for example, substring `gas` could produce a false match inside another word. Where feasible, apply whole-word boundaries to single-word rules.

### Ambiguous or unmatched descriptions

- If exactly one enabled rule matches, suggest its category.
- If no rule matches, suggest **Other** and tell the user it is a fallback suggestion.
- If rules from different categories match, resolve with an explicit, deterministic rule-priority policy. Prefer asking the user to choose when equally ranked rules disagree rather than silently making an arbitrary choice.
- Store whether the final category came from an automatic suggestion or a manual correction. Do not overwrite a user's manual choice just because the description matches another rule later.

## 3. Recommended stack and development constraints

- **Python:** Application logic and tests.
- **Kivy:** UI, touch controls, layout, and screen navigation.
- **KivyMD:** Optional. Add only after the basic Kivy screens run. UI library versions can change, so pin and test the chosen version rather than following a development branch blindly.
- **SQLite (`sqlite3`):** Local database; no separate database server is required.
- **Buildozer + python-for-android:** Build an Android debug APK. Buildozer runs on Linux/macOS; on Windows, use WSL2 and keep the project inside the Linux filesystem for builds.
- **pytest:** Automated tests for the DFA, categorizer, database/repositories, reporting, and budgets.
- **Git:** Version control. Commit after each successful phase.

Start by getting **Kivy alone** running; add KivyMD only if it makes the UI easier. Keep the first dependency set small to reduce Android packaging issues. Use a stable, mutually compatible Python/Kivy/toolchain combination and record it in the project README and dependency files. Verify current compatibility in the official documentation linked at the end.

### Money and dates

- Store money as **integer centavos** (for example, ₱125.50 is `12550`) rather than floating-point values. Parse user input with `decimal.Decimal`, validate it, and convert to centavos at the application boundary.
- Display amounts with two decimal places and the `₱` symbol.
- For this offline MVP, store expense occurrence date as ISO date text `YYYY-MM-DD`. Store creation timestamp separately. Use a consistent local-date policy and do not silently shift a user's expense to a different day through UTC conversion.
- Store budget months as `YYYY-MM`.

## 4. Suggested project layout

Ask the coding agent to adapt this structure to any existing files rather than blindly deleting or rewriting the current source.

```text
expense-categorizer/
├── main.py
├── README.md
├── requirements-dev.txt
├── buildozer.spec                 # Add when Android packaging starts
├── expense_app/
│   ├── __init__.py
│   ├── app.py                     # App class and screen setup
│   ├── config.py                  # App constants/default categories
│   ├── logic/
│   │   ├── __init__.py
│   │   ├── dfa.py                 # Generalized DFA implementation
│   │   ├── categorizer.py         # Rule matching and conflict policy
│   │   ├── money.py               # Amount parse/format helpers
│   │   └── reporting.py           # Pure report calculations
│   ├── data/
│   │   ├── __init__.py
│   │   ├── database.py            # Connection, schema, migrations, seeding
│   │   └── repositories.py        # Queries and persistence operations
│   └── ui/
│       ├── __init__.py
│       ├── components.py          # Reusable buttons, cards, rows
│       └── screens/
│           ├── dashboard.py
│           ├── add_expense.py
│           ├── transactions.py
│           ├── reports.py
│           └── budgets.py
└── tests/
    ├── test_dfa.py
    ├── test_categorizer.py
    ├── test_money.py
    ├── test_database.py
    ├── test_expenses.py
    ├── test_reports.py
    └── test_budgets.py
```

**Architecture rule:** UI screens collect input and render results. They should call logic/services and repositories; they should not contain SQL statements or reimplement categorization/report calculations. Keep the DFA engine independent of Kivy so it can be tested without opening a window.

## 5. How to work with an AI coding assistant

Use the coding assistant in your editor or repository-aware environment. Provide it access to the current files, especially `substring_dfa.py`. Give it **one phase prompt at a time**. Run the tests and inspect the changes before asking it to continue.

### Persistent project instructions (`AGENTS.md` or equivalent)

Create a root-level `AGENTS.md` and give the coding assistant these rules:

```text
Project: Offline-first Android expense categorizer in Python/Kivy.

Working rules:
1. Inspect existing code before editing. Preserve working behavior unless a change is required and covered by tests.
2. Implement only the current requested phase. Do not build later phases early.
3. Keep core logic independent of Kivy. Do not place SQL or DFA logic inside UI screens.
4. Store money as integer centavos in SQLite; never use binary float for persisted money calculations.
5. Use parameterized SQL, foreign-key constraints, and explicit transactions where needed.
6. Validate all user input. Show friendly validation messages; never crash on a blank form.
7. No network calls, analytics, ads, bank integration, or cloud storage in the MVP.
8. Add or update automated tests for every behavior change. Run the full test suite before finishing.
9. Do not claim a test or build passed unless you actually ran it and saw it pass.
10. Do not add dependencies without explaining why and updating dependency documentation.
11. Keep changes small. Do not silently rewrite unrelated files or remove tests.
12. When finished, report: files changed, design decisions, test commands/results, known limitations, and the next safe step.
```

### A standard prompt footer

Append this to phase prompts when needed:

```text
Before editing, inspect the relevant files and summarize your plan briefly.
Make the smallest coherent change for this phase. Add tests. Run the tests you can run.
If a test fails, investigate and fix the cause instead of suppressing the test.
Do not mark unfinished behavior as complete. Summarize changed files, commands run,
results, and any manual test I should perform. Stop after this phase.
```

## 6. Phase 0 — Inspect the existing DFA and establish a baseline

**Goal:** Understand the current code before the app is built around it.

The supplied `substring_dfa.py` currently accepts a binary alphabet (`0` and `1`). Its simulator reports whether a pattern occurs by checking the final state. The expense app needs text descriptions, multiple category patterns, and match metadata. Do not simply connect the unchanged binary-only program to the UI.

### Prompt to paste

```text
Inspect the existing repository and the current substring_dfa.py file. Do not modify files yet.
Explain how build_dfa(), display_transition_table(), and simulate_dfa() work;
identify the binary-only assumptions and the behavior of the accepting state.
Propose the smallest refactor that supports case-insensitive text pattern detection
for expense descriptions, multiple independent patterns, and detection of match positions.
List existing tests (if any), risks, and a minimal test plan. Do not implement the app UI yet.
```

### Gate to pass before continuing

- You understand which functions are reusable and which need changes.
- The original file has been committed or copied into version control.
- A list of expected DFA behaviors exists before the refactor.

## 7. Phase 1 — Create the project skeleton and run a minimal Kivy app

**Goal:** Confirm that Python, Kivy, and the selected environment work before adding business logic.

### Prompt to paste

```text
Set up the project skeleton described in this guide, adapting to existing files.
Create a minimal main.py that launches a Kivy app with a title and a simple home screen.
Add dependency/setup instructions to README.md, a requirements-dev.txt for development
packages, and a basic pytest configuration if needed. Do not add SQLite, reports, or budgets yet.
Keep the initial runtime dependencies minimal. Run pytest and launch the app if the environment
supports it. Explain any commands that I must run locally.
```

### Acceptance checklist

- [ ] The app opens on the development computer without an exception.
- [ ] Project imports work from the repository root.
- [ ] `pytest` runs and reports the current test status.
- [ ] Setup steps are written down and reproducible.
- [ ] Git commit created: `chore: initialize Kivy app structure`.

## 8. Phase 2 — Refactor DFA and build the categorizer

**Goal:** Produce a testable engine that suggests a category from a transaction description.

### Design requirements

- Normalize descriptions and rules consistently (at minimum, trim and case-fold text and normalize repeated whitespace).
- Support alphabetic text, digits, punctuation, and spaces in the input description. An input character not present in a particular pattern must not crash the scanner.
- Search multiple patterns without requiring a separate app launch per pattern.
- Report which pattern matched and where it matched, when available.
- Correctly handle patterns at the start/end of text, missing patterns, repeated matches, and overlapping matches.
- Empty patterns are invalid and must be rejected.
- Keep any binary-mode regression tests required for the original DFA demonstration, or document why a behavior intentionally changed.
- Use deterministic conflict handling: rule priority first; if multiple different categories match equally, return an ambiguity that the UI can ask the user to resolve.
- Do not trust pattern matches as final truth: users can always override them.

A straightforward first implementation may run one pattern DFA per enabled rule. Optimize later only if tests or real usage show that it is necessary.

### Prompt to paste

```text
Implement the text-capable DFA engine and expense categorizer in expense_app/logic/dfa.py
and expense_app/logic/categorizer.py. First inspect substring_dfa.py and reuse its core idea,
but remove the fixed '0'/'1' alphabet assumption. The categorizer must accept a description
and a collection of enabled rules (pattern, category, priority, match mode if implemented).
Return a structured result containing the suggested category, matching patterns, and whether
the result is unmatched or ambiguous. Support case-insensitive matching consistently.
Add pytest coverage for empty/invalid patterns, absent matches, matches at boundaries, repeated
and overlapping occurrences, different categories matching, equal-priority conflicts, and normal
expense descriptions. Keep this code independent of Kivy and SQLite. Run the tests and explain
how to invoke the categorizer from a small Python example.
```

### Acceptance checklist

- [ ] Text descriptions work, not just `0`/`1` strings.
- [ ] Matching is case-insensitive.
- [ ] Unknown characters do not crash the matcher.
- [ ] Multiple rules can be evaluated in one categorization call.
- [ ] Conflicts are explicit and deterministic.
- [ ] Match positions and repeated/overlapping matches behave as documented.
- [ ] Unit tests pass.
- [ ] Git commit created: `feat: add text DFA expense categorizer`.

## 9. Phase 3 — Add money parsing, SQLite schema, and repositories

**Goal:** Persist categories, rules, expenses, and monthly budgets safely.

### Suggested tables

**`categories`**

- `id` integer primary key
- `name` text, required and unique (apply a consistent case policy)
- `color` text, optional UI color token/hex
- `is_active` integer boolean, default 1
- `is_default` integer boolean, default 0

**`category_rules`**

- `id` integer primary key
- `pattern` text, required and non-empty
- `category_id` foreign key to categories
- `priority` integer, required
- `match_mode` text, such as `substring` or `whole_word` if implemented
- `is_enabled` integer boolean, default 1

**`expenses`**

- `id` integer primary key
- `amount_centavos` integer, required and greater than zero
- `description` text, required and non-empty
- `occurred_on` text, required ISO date `YYYY-MM-DD`
- `category_id` foreign key to categories
- `category_source` text: `automatic` or `manual`
- `matched_pattern` text, nullable
- `created_at` text, required timestamp
- `updated_at` text, nullable

**`budgets`**

- `id` integer primary key
- `category_id` foreign key to categories
- `period_month` text, required `YYYY-MM`
- `limit_centavos` integer, required and greater than zero
- unique constraint on `(category_id, period_month)`

Enable SQLite foreign keys for every connection with `PRAGMA foreign_keys = ON`. Use parameterized SQL. Add database initialization/migration logic and seed starter categories/rules only when the database is first initialized; avoid duplicating seed rows on every app launch. Store the database in the platform-appropriate app data directory, not the source-code folder or a temporary working directory.

### Prompt to paste

```text
Implement money helpers and SQLite persistence. Store all monetary values as integer centavos;
parse and validate user-entered amounts with decimal.Decimal, reject zero/negative/invalid values,
and format amounts as Philippine pesos. Add database initialization and schema creation for
categories, category_rules, expenses, and budgets using the schema in the development guide.
Enable foreign keys, use parameterized SQL, and add repository methods for CRUD operations needed
by later screens. Seed default categories and keyword rules exactly once. Put database path selection
behind one function so it can use Kivy's app data directory in the packaged app and a local test
path in pytest. Add tests for initialization, seeding idempotence, invalid amounts, expense persistence,
foreign-key behavior, category changes, and budget uniqueness. Do not add screen code yet.
```

### Acceptance checklist

- [ ] Amounts round-trip without floating-point errors (e.g. ₱125.50 is 12550 centavos).
- [ ] Invalid, blank, zero, and negative amounts are rejected.
- [ ] Seed categories/rules are not duplicated at every startup.
- [ ] Expenses survive database close/reopen.
- [ ] Deletion of a category used by an expense is blocked or replaced by a documented deactivate workflow.
- [ ] Repositories can use a temporary database in tests.
- [ ] Git commit created: `feat: persist expenses and categorization rules`.

## 10. Phase 4 — Build screen navigation and UI foundation

**Goal:** Establish a mobile-friendly layout before implementing each feature.

Use Kivy `ScreenManager` or a similarly simple navigation design. Keep touch targets large, labels clear, and forms scrollable on smaller phone screens. Support device rotation only if it is straightforward; prioritize portrait mode for the first release. Add consistent spacing, typography, empty states, validation messages, and back navigation. Do not rely on hover-only interactions.

### Suggested screens

- **Dashboard:** total spent this month, quick actions, recent transactions, category summary.
- **Add Expense:** amount, description, date, suggested category, manual category selector, save/cancel.
- **Transactions:** list, filter by month/category, open expense for edit, delete with confirmation.
- **Reports:** month selector, monthly total, category totals, percentages/bars.
- **Budgets:** month selector, category limit forms, spent/remaining/progress.

### Prompt to paste

```text
Implement the Kivy screen/navigation foundation for Dashboard, Add Expense, Transactions,
Reports, and Budgets. Use placeholder state/data only for now; do not fake completed database
behavior. Create reusable UI components where helpful and keep screen files focused. Make forms
scrollable and touch-friendly. Include loading/empty/error states and a consistent way to show
validation messages. Keep imports and application startup stable. Add tests only where practical
for non-visual logic and provide a manual smoke-test checklist. Do not add new dependencies unless
necessary and explained.
```

### Acceptance checklist

- [ ] App launches to Dashboard.
- [ ] Navigation to each planned screen and back works.
- [ ] Layout remains usable on a narrow window.
- [ ] No business logic or SQL has been embedded in screen classes.
- [ ] Git commit created: `feat: add mobile navigation and screen layouts`.

## 11. Phase 5 — Complete Add Expense and Transactions

**Goal:** Deliver the complete record lifecycle using real SQLite data.

### Add Expense behavior

- Amount: required, numeric, positive, and formatted as PHP.
- Description: required after trimming whitespace.
- Date: required, defaults to today, and validated.
- Category: automatically suggested when a rule matches; user can change it before saving.
- Save: insert once, show clear success feedback, and refresh dashboard/transactions.
- Cancel: return without writing a row.
- Error handling: invalid input or database errors show a helpful message; do not silently swallow errors.

### Transactions behavior

- Show newest expense dates first (with a deterministic secondary sort by ID or timestamp).
- Display date, description, category, and amount.
- Allow view/edit of description, amount, date, and category.
- Allow delete only after a confirmation dialog.
- Manual category override must be saved and marked `manual`; subsequent screen refreshes must not automatically replace it.
- Keep list queries paged or reasonably bounded if needed; do not load an unbounded database into widgets by default.

### Prompt to paste

```text
Connect Add Expense and Transactions screens to the real categorizer and repositories.
Implement validated create, list, edit, and delete flows. Auto-suggest the category based on the
current description, but allow the user to override it; persist category_source as automatic or
manual. Re-categorize only when appropriate and never overwrite a saved manual choice on a normal
refresh. Dates default to today. Use integer-centavo helpers throughout. Add service/repository tests
for create/update/delete and category-source behavior, and provide a manual test checklist for the
Kivy screens. Run the full test suite and fix failures.
```

### Acceptance checklist

- [ ] Add Expense saves a transaction that appears in Transactions after navigation.
- [ ] App restart preserves saved data.
- [ ] User can change an automatic category suggestion.
- [ ] Editing description does not silently overwrite a manually selected category.
- [ ] Delete requires confirmation and updates totals/lists.
- [ ] Missing description, invalid date, or bad amount produces an understandable message.
- [ ] Git commit created: `feat: add and manage expense transactions`.

## 12. Phase 6 — Reports

**Goal:** Summarize expense data for the selected calendar month.

### Required report features

- Previous-month and next-month navigation; the initial month is the current local month.
- Monthly total expense amount and transaction count.
- Category totals, ordered from highest spending to lowest.
- Percentage of monthly spending per category, using safe handling when the total is zero.
- A simple visual breakdown using Kivy labels, progress bars, or canvas drawing. Avoid a heavy chart dependency until needed.
- Empty state if no expenses exist in the selected month.
- Reports must use recorded expense dates, not created timestamps.
- Editing/deleting an expense must update report totals when the screen refreshes.

### Report calculation rules

For the chosen month, use a date range from the first day of the month inclusive to the first day of the next month exclusive. Group expenses by category and sum `amount_centavos`. Compute percentages from integer totals (convert to decimals only for display). Do not include expenses from adjacent months. Make report calculations pure functions in `reporting.py`, with a repository query that returns the required data.

### Prompt to paste

```text
Implement the Reports screen with real database data. Add a month selector starting at the current
local month and allowing previous/next month navigation. Show the month total, transaction count,
and category totals sorted descending, including each category's percentage of the total. Show a
clear empty state for months with no expenses. Draw simple category bars with existing Kivy widgets;
avoid adding a chart library unless there is a strong documented reason. Filter by occurred_on using
[start-of-month, start-of-next-month) so adjacent months are not mixed. Keep calculations in pure
functions in expense_app/logic/reporting.py, and test totals, sorting, percentages, zero-total behavior,
empty months, month boundaries, edited expenses, and deleted expenses. Then connect the screen and
run the full suite.
```

### Acceptance checklist

- [ ] Current month is selected on first entry.
- [ ] Previous/next month navigation changes all report values.
- [ ] Total and per-category sums match the transactions shown for that month.
- [ ] Percentages sum to approximately 100% when total spending is nonzero (minor display rounding is acceptable).
- [ ] Empty months do not divide by zero or display misleading values.
- [ ] No expense outside the chosen month is included.
- [ ] Editing or deleting transactions updates the results after refresh.
- [ ] Git commit created: `feat: add monthly spending reports`.

## 13. Phase 7 — Budgets

**Goal:** Let users set a monthly spending limit for a category and monitor progress against it.

### Required budget features

- Select a month; initial selection is the current local month.
- Create or update one budget per category per month.
- Show category, limit, spent amount, amount remaining/over, and a progress bar.
- Budget spending is the sum of expenses for that category and month, based on `occurred_on`.
- Show a clear state for budgets not yet used, nearly reached, and exceeded.
- Do not let an invalid zero/negative budget be saved.
- Removing a budget must not remove expenses. Confirm removal if a delete option is offered.
- A budget for one month must not change a different month's budget.

### Budget formulas

- `spent = sum(expenses.amount_centavos for the category and month)`
- `remaining = limit_centavos - spent` (may be negative when exceeded)
- `progress_ratio = spent / limit_centavos`
- Clamp only the **visual progress bar** to the range 0..1. Keep the real spent and remaining values intact so an over-budget amount remains visible.
- Optional initial warning threshold: 80% of the limit. Show it in the app as a status only; do not imply background notifications are implemented.

### Prompt to paste

```text
Implement the Budgets screen backed by the budgets repository and actual expense totals.
Allow the user to select a month and create/update a positive monthly limit per active category.
Show limit, spent, remaining (including a negative value when exceeded), and a progress indicator.
Calculate spent using expense occurred_on dates within the selected month. Clamp only the graphical
progress value, not the displayed figures. Prevent duplicate budget rows for the same category and
month. Support editing an existing limit and make budget deletion optional but safe. Add unit tests for
no expenses, exact limit, under budget, 80% warning threshold if used, over budget, multiple months,
and a category with a budget but no spending. Ensure reports and budgets use the same month-boundary
helper. Connect the Kivy screen, run all tests, and document manual test steps.
```

### Acceptance checklist

- [ ] User can create a monthly category budget and see it after screen navigation or app restart.
- [ ] Editing a budget changes the existing row rather than creating a duplicate.
- [ ] Spent totals match Reports for the same category and month.
- [ ] Remaining amount can be negative and is displayed clearly when over budget.
- [ ] The progress bar never exceeds its visual maximum, even when overspent.
- [ ] Budgets are independent between months.
- [ ] Adding/editing/deleting an expense updates budget progress after refresh.
- [ ] Git commit created: `feat: add monthly category budgets`.

## 14. Phase 8 — Integration, quality checks, and Android debug APK

**Goal:** Confirm the whole MVP works together before attempting wider distribution.

### Integrated manual test scenario

Use a fresh test database and try these steps:

1. Add `₱150.00` with description `Jollibee lunch` and accept Food.
2. Add `₱80.00` with description `Jeepney fare` and accept Transportation.
3. Add `₱200.00` with an unmatched description; confirm the fallback and manually choose a category.
4. Edit one expense and verify that the reports and budgets update.
5. Set a Food budget of `₱1,000.00` for the current month.
6. Confirm Food spent is `₱150.00`, remaining is `₱850.00`, and progress is 15% (assuming no other Food expenses exist in the test database).
7. Add enough Food expenses to exceed the limit, then confirm the exceeded amount is visible and the visual bar stays capped.
8. Navigate to a different month and confirm the report and budget values are isolated to that month.
9. Restart the app and verify that the saved expenses and budgets remain.
10. Try blank/invalid amounts and delete cancellation; the app should remain responsive and data should remain unchanged.

### Automated preflight

Run commands appropriate for the environment, for example:

```bash
python -m pytest -q
python -m compileall main.py expense_app
```

Also manually launch the Kivy desktop app. Automated unit tests do not validate the visual experience; tap through every screen.

### Android packaging workflow

Use the current official Buildozer instructions for package installation and system prerequisites. On Windows, use WSL2; keep the project in the WSL Linux filesystem rather than building directly from `/mnt/c/...`.

Typical project steps after installing Buildozer:

```bash
buildozer init
# Edit buildozer.spec: title, package.name, package.domain, source.include_exts,
# requirements, orientation, and Android settings as needed.
buildozer -v android debug
```

The first Android build downloads toolchain components and can take a while. If a build fails, give the coding assistant the complete error log, your OS, Python/Kivy versions, and `buildozer.spec`; ask it to diagnose the actual error rather than changing random versions. The debug APK is normally written to `bin/` when packaging succeeds. Install and test it on a real Android device as well as the desktop app. Check app-data path, text input, scrolling, and screen sizing on device.

### Prompt to paste

```text
Run an integration review of the completed MVP: DFA categorization, Add Expense, Transactions,
Reports, and Budgets. Check for inconsistent month/date calculations, float-based money operations,
SQL embedded in screens, missing input validation, swallowed exceptions, duplicate writes, and
manual categories being overwritten. Run the full test suite and compileall, fix genuine defects,
and add regression tests. Provide a manual test checklist. Inspect buildozer.spec and identify what
is required for an Android debug build; do not claim an APK was built unless you actually ran the build.
Do not add unrelated features.
```

### Release gate

- [ ] All automated tests pass.
- [ ] App starts without an exception.
- [ ] Core flows work by hand from Dashboard through Add Expense, Transactions, Reports, and Budgets.
- [ ] Data persists after restart.
- [ ] Invalid input does not crash the app.
- [ ] No network permission or external service is required for MVP functionality unless explicitly justified.
- [ ] Debug APK opens on an Android device and can save/read local data.
- [ ] README explains setup, tests, database location policy, build command, and limitations.
- [ ] Final git commit/tag created only after the release gate passes.

## 15. Common pitfalls and how to avoid them

1. **Keeping the DFA binary-only:** The supplied prototype accepts only `0` and `1`; text support is a real refactor, not just a UI change.
2. **Only checking final acceptance:** A simple contains-pattern simulator may report whether a match occurred but not all match positions. Specify repeated/overlapping-match behavior in tests.
3. **False category matches:** Substrings can match inside unrelated words. Use sensible patterns, whole-word checks where appropriate, priorities, ambiguity handling, and manual overrides.
4. **Storing money as floats:** Use integer centavos all the way through storage and aggregation.
5. **Mixing date boundaries:** Reports and budgets must share the same tested month-range helper.
6. **Putting SQL in widgets:** Keep persistence in repositories so logic can be tested on desktop.
7. **Using the wrong database path on Android:** Resolve the file path via the app's writable data directory.
8. **Coding too many screens at once:** Finish one phase, run tests, commit, then continue.
9. **Adding KivyMD or chart dependencies too early:** Keep the initial stack small; add dependencies only when the basic app and Android build are stable.
10. **Assuming desktop success means Android success:** Package early enough to expose mobile-only issues, and test the APK on a device.

## 16. Future enhancements after this guide

Only after the MVP passes its release gate, consider CSV export/backup, editable categorization rules, category management UI, recurring expenses, budget reminders, and optional encrypted backup. For CSV export, let users choose the destination and avoid automatic uploads. If encryption or device backup is added, document threat assumptions and recovery behavior rather than claiming the local database is encrypted by default.

## 17. Official references

Use official docs as the source of truth because package versions and Android toolchain requirements change.

- Kivy documentation: https://kivy.org/doc/stable/
- Kivy Android packaging guide: https://kivy.org/doc/stable/guide/packaging-android.html
- Buildozer documentation and installation: https://buildozer.readthedocs.io/en/stable/ and https://buildozer.readthedocs.io/en/latest/installation/
- KivyMD documentation: https://kivymd.readthedocs.io/
- Python `sqlite3` reference: https://docs.python.org/3/library/sqlite3.html
- Python `decimal` reference: https://docs.python.org/3/library/decimal.html
- pytest documentation: https://docs.pytest.org/

---

**Definition of done:** A user can add, edit, categorize, and delete expenses; the app stores records locally; monthly reports sum the right expenses; a user can create per-category monthly budgets; and budget progress stays consistent with reports after transactions change. The app has automated tests and has been manually exercised on Android. No later-phase feature should be started until these behaviors work reliably.
