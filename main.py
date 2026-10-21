"""Entry point for the Expense Categorizer application.

Run with:
    python main.py
"""

from expense_app.app import ExpenseCategorizerApp


def main():
    ExpenseCategorizerApp().run()


if __name__ == "__main__":
    main()

