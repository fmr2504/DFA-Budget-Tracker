"""Kivy application class and screen manager setup.

This module creates the App subclass, registers all screens with a
ScreenManager, and provides the root widget with a mobile-optimized
bottom navigation bar.
"""

from __future__ import annotations

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import FadeTransition, ScreenManager

from expense_app.config import APP_NAME
from expense_app.ui.components import COLOR_PRIMARY, COLOR_SURFACE_LIGHT
from expense_app.ui.screens.add_expense import AddExpenseScreen
from expense_app.ui.screens.budgets import BudgetsScreen
from expense_app.ui.screens.dashboard import DashboardScreen
from expense_app.ui.screens.reports import ReportsScreen
from expense_app.ui.screens.transactions import TransactionsScreen

# Set modern background color for the application window
Window.clearcolor = (0.08, 0.10, 0.15, 1)


class ExpenseCategorizerApp(App):
    """Main Kivy application for the Expense Categorizer."""

    title = APP_NAME

    def build(self):
        """Build the root widget with navigation and a screen manager."""
        root = BoxLayout(orientation="vertical")

        # --- Screen manager ---
        self.screen_manager = ScreenManager(transition=FadeTransition(duration=0.15))
        self.screen_manager.add_widget(DashboardScreen(name="dashboard"))
        self.screen_manager.add_widget(AddExpenseScreen(name="add_expense"))
        self.screen_manager.add_widget(TransactionsScreen(name="transactions"))
        self.screen_manager.add_widget(ReportsScreen(name="reports"))
        self.screen_manager.add_widget(BudgetsScreen(name="budgets"))

        root.add_widget(self.screen_manager)

        # --- Bottom navigation bar ---
        self.nav_buttons: dict[str, Button] = {}
        nav_bar = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=54,
            spacing=4,
            padding=[4, 4, 4, 4],
        )

        nav_items = [
            ("Home", "dashboard"),
            ("+ Add", "add_expense"),
            ("History", "transactions"),
            ("Reports", "reports"),
            ("Budgets", "budgets"),
        ]

        for label, screen_name in nav_items:
            btn = Button(
                text=label,
                font_size="13sp",
                bold=True,
                background_color=COLOR_PRIMARY if screen_name == "dashboard" else COLOR_SURFACE_LIGHT,
            )
            btn.bind(on_release=self._make_nav_callback(screen_name))
            self.nav_buttons[screen_name] = btn
            nav_bar.add_widget(btn)

        root.add_widget(nav_bar)
        return root

    def _make_nav_callback(self, screen_name: str):
        """Return a callback that navigates to *screen_name* and updates tab styles."""

        def callback(_instance):
            self.screen_manager.current = screen_name
            for name, btn in self.nav_buttons.items():
                if name == screen_name:
                    btn.background_color = COLOR_PRIMARY
                else:
                    btn.background_color = COLOR_SURFACE_LIGHT

        return callback
