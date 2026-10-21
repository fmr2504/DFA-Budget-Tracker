"""Tests for UI screens and reusable components (expense_app.ui)."""

import pytest

from expense_app.app import ExpenseCategorizerApp
from expense_app.ui.components import (
    AppButton,
    Card,
    EmptyState,
    FormInput,
    HeaderBar,
    MessageBanner,
    StatCard,
)
from expense_app.ui.screens.add_expense import AddExpenseScreen
from expense_app.ui.screens.budgets import BudgetsScreen
from expense_app.ui.screens.dashboard import DashboardScreen
from expense_app.ui.screens.reports import ReportsScreen
from expense_app.ui.screens.transactions import TransactionsScreen


class TestReusableComponents:
    def test_card_instantiation(self):
        card = Card()
        assert card.padding == [16, 16, 16, 16]

    def test_header_bar(self):
        header = HeaderBar(title="Test Header", subtitle="Test Sub")
        assert header.height == 60

    def test_stat_card(self):
        stat = StatCard(title="Spent", value="₱100.00", subtitle="October")
        assert stat.value_label.text == "₱100.00"

    def test_form_input(self):
        inp = FormInput(label="Amount", initial_text="150.00")
        assert inp.text == "150.00"
        inp.text = "200.00"
        assert inp.text == "200.00"

    def test_app_button(self):
        btn = AppButton(text="Save", variant="success")
        assert btn.text == "Save"
        assert btn.height == 48

    def test_empty_state(self):
        empty = EmptyState(title="No Items", message="Add some items.")
        assert empty.height == 160

    def test_message_banner(self):
        banner = MessageBanner()
        banner.show("Invalid input", variant="error")
        assert banner.label.text == "Invalid input"
        assert banner.opacity == 1
        banner.hide()
        assert banner.label.text == ""
        assert banner.opacity == 0


class TestScreensFoundation:
    def test_dashboard_screen(self):
        screen = DashboardScreen(name="dashboard")
        assert screen.name == "dashboard"
        assert hasattr(screen, "total_spent_card")
        assert hasattr(screen, "active_budgets_card")

    def test_add_expense_screen(self):
        screen = AddExpenseScreen(name="add_expense")
        assert screen.name == "add_expense"
        assert hasattr(screen, "amount_input")
        assert hasattr(screen, "desc_input")
        assert hasattr(screen, "date_input")
        assert hasattr(screen, "category_spinner")

    def test_transactions_screen(self):
        screen = TransactionsScreen(name="transactions")
        assert screen.name == "transactions"
        assert hasattr(screen, "category_filter")
        assert hasattr(screen, "list_container")

    def test_reports_screen(self):
        screen = ReportsScreen(name="reports")
        assert screen.name == "reports"
        assert hasattr(screen, "month_lbl")
        assert hasattr(screen, "total_card")
        assert hasattr(screen, "count_card")

    def test_budgets_screen(self):
        screen = BudgetsScreen(name="budgets")
        assert screen.name == "budgets"
        assert hasattr(screen, "category_spinner")
        assert hasattr(screen, "limit_input")
        assert hasattr(screen, "save_budget_btn")


class TestAppScreenManager:
    def test_app_builds_all_screens(self):
        app = ExpenseCategorizerApp()
        root = app.build()
        assert root is not None
        assert app.screen_manager is not None

        screen_names = app.screen_manager.screen_names
        expected_screens = ["dashboard", "add_expense", "transactions", "reports", "budgets"]
        for expected in expected_screens:
            assert expected in screen_names

        # Verify initial screen is dashboard
        assert app.screen_manager.current == "dashboard"

        # Verify bottom nav bar contains 5 buttons
        assert len(app.nav_buttons) == 5
