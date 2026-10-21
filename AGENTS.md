
# Project: Automatic Expense Categorizer

## Purpose
Build an offline-first personal expense tracking application
for Android using Python and Kivy.

## Technology
- Python
- Kivy for the mobile interface
- SQLite for local data storage
- pytest for automated tests
- Buildozer for Android packaging when the app is ready

## Core algorithm
- Preserve and extend the existing DFA pattern detection algorithm.
- Support text patterns instead of only binary strings.
- Use DFA-based keyword matching for expense categorization.
- Keep categorization logic separate from the UI and database.
- Support case-insensitive matching and avoid accidental
  matches inside unrelated words.
- Allow users to correct suggested categories.
- Define predictable behavior when multiple rules match.

## Money and data
- Store monetary values as integer centavos, not floats.
- Display amounts using Philippine peso formatting (₱).
- Store expenses and budgets locally in SQLite.
- Use Kivy's user_data_dir for the live database location
  so storage works on desktop and Android.
- Never require bank credentials or an online service.

## Code quality
- Make small, incremental changes.
- Keep UI, business logic, and database code separated.
- Add or update pytest tests for every core feature.
- Run relevant tests after making changes.
- Never claim tests passed unless you actually ran them.
- Do not delete existing files or replace working code
  without explaining the reason.
- Report modified files, commands executed, and test results.
- Ask before performing destructive operations.
