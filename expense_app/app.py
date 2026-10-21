"""Kivy application class and screen manager setup.

This module creates the App subclass, registers all screens with a
ScreenManager, and provides the root widget.  Business logic and
database access are deliberately excluded — screens call into the
logic and data layers as needed.
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from expense_app.config import APP_NAME
from expense_app.ui.screens.dashboard import DashboardScreen
from expense_app.ui.screens.add_expense import AddExpenseScreen
from expense_app.ui.screens.transactions import TransactionsScreen
from expense_app.ui.screens.reports import ReportsScreen
from expense_app.ui.screens.budgets import BudgetsScreen


class ExpenseCategorizerApp(App):
    """Main Kivy application for the Expense Categorizer."""

    title = APP_NAME

    def build(self):
        """Build the root widget with navigation and a screen manager."""
        root = BoxLayout(orientation="vertical")

        # --- Screen manager ---
        self.screen_manager = ScreenManager(transition=FadeTransition())
        self.screen_manager.add_widget(DashboardScreen(name="dashboard"))
        self.screen_manager.add_widget(AddExpenseScreen(name="add_expense"))
        self.screen_manager.add_widget(
            TransactionsScreen(name="transactions")
        )
        self.screen_manager.add_widget(ReportsScreen(name="reports"))
        self.screen_manager.add_widget(BudgetsScreen(name="budgets"))

        root.add_widget(self.screen_manager)

        # --- Bottom navigation bar ---
        nav_bar = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=50,
            spacing=2,
        )

        nav_items = [
            ("Home", "dashboard"),
            ("Add", "add_expense"),
            ("History", "transactions"),
            ("Reports", "reports"),
            ("Budgets", "budgets"),
        ]

        for label, screen_name in nav_items:
            btn = Button(text=label, font_size="14sp")
            btn.bind(
                on_release=self._make_nav_callback(screen_name)
            )
            nav_bar.add_widget(btn)

        root.add_widget(nav_bar)
        return root

    def _make_nav_callback(self, screen_name):
        """Return a callback that navigates to *screen_name*."""

        def callback(_instance):
            self.screen_manager.current = screen_name

        return callback

