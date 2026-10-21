"""Transactions screen — list, filter, and inspect recorded expenses.

Provides a mobile-friendly transaction ledger with month/category filters,
touch targets for reviewing expenses, and clear empty states.
"""

from __future__ import annotations

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner

from expense_app.config import DEFAULT_CATEGORIES
from expense_app.ui.components import (
    COLOR_SURFACE_LIGHT,
    COLOR_TEXT_PRIMARY,
    Card,
    EmptyState,
    HeaderBar,
)


class TransactionsScreen(Screen):
    """Screen displaying historical expenses with filtering capabilities."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(orientation="vertical")
        root.add_widget(
            HeaderBar(
                title="Transactions",
                subtitle="Expense History",
                on_back=self._nav_to_dashboard,
            )
        )

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=[16, 16, 16, 24],
            spacing=14,
        )
        content.bind(minimum_height=content.setter("height"))

        # Filter card
        filter_card = Card(
            orientation="horizontal",
            size_hint_y=None,
            height=66,
            padding=[12, 10, 12, 10],
            spacing=10,
        )
        filter_lbl = Label(
            text="Filter:",
            font_size="14sp",
            bold=True,
            size_hint=(None, 1),
            width=50,
            color=COLOR_TEXT_PRIMARY,
        )
        filter_card.add_widget(filter_lbl)

        all_cats = ["All Categories"] + DEFAULT_CATEGORIES
        self.category_filter = Spinner(
            text="All Categories",
            values=all_cats,
            size_hint=(1, 1),
            background_color=COLOR_SURFACE_LIGHT,
            color=COLOR_TEXT_PRIMARY,
            font_size="14sp",
        )
        filter_card.add_widget(self.category_filter)
        content.add_widget(filter_card)

        # Transactions list container
        self.list_container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=10,
        )
        self.list_container.bind(minimum_height=self.list_container.setter("height"))

        # Default empty state
        self.empty_state = EmptyState(
            title="No Transactions Found",
            message="No recorded expenses match the current filter.\nAdd a new expense to see it in your ledger.",
            action_text="+ Add Expense",
            on_action=self._nav_to_add_expense,
        )
        self.list_container.add_widget(self.empty_state)
        content.add_widget(self.list_container)

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def _nav_to_dashboard(self, *args):
        app = App.get_running_app()
        if app and hasattr(app, "screen_manager"):
            app.screen_manager.current = "dashboard"

    def _nav_to_add_expense(self, *args):
        app = App.get_running_app()
        if app and hasattr(app, "screen_manager"):
            app.screen_manager.current = "add_expense"
