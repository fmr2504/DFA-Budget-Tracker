"""Transactions screen — list, filter, edit, and delete recorded expenses.

Provides a mobile ledger displaying dates, descriptions, categories,
Philippine peso amounts, category sources, and interactive edit / delete dialogs.
"""

from __future__ import annotations

from typing import Optional

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner

from expense_app.config import DEFAULT_CATEGORIES
from expense_app.data.repositories import (
    delete_expense,
    get_categories,
    get_category_by_name,
    get_expenses,
    update_expense,
)
from expense_app.ui.components import (
    COLOR_SURFACE_LIGHT,
    COLOR_TEXT_PRIMARY,
    Card,
    ConfirmDialog,
    EditExpenseDialog,
    EmptyState,
    HeaderBar,
    MessageBanner,
    TransactionCard,
)


class TransactionsScreen(Screen):
    """Screen displaying historical expenses with filtering, edit, and delete flows."""

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
            spacing=12,
        )
        content.bind(minimum_height=content.setter("height"))

        # Banner for status notices
        self.banner = MessageBanner()
        self.banner.hide()
        content.add_widget(self.banner)

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
        self.category_filter.bind(text=self._on_filter_changed)
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

    def on_pre_enter(self, *args):
        """Automatically refresh transaction records whenever screen is opened."""
        self.refresh_transactions()

    def _on_filter_changed(self, _instance, _text: str):
        self.refresh_transactions()

    def refresh_transactions(self):
        """Query SQLite database and render transaction rows."""
        app = App.get_running_app()
        conn = getattr(app, "conn", None)
        if not conn:
            return

        cat_filter = self.category_filter.text
        category_id: Optional[int] = None
        if cat_filter != "All Categories":
            cat_row = get_category_by_name(conn, cat_filter)
            if cat_row:
                category_id = cat_row["id"]

        expenses = get_expenses(conn, category_id=category_id)

        self.list_container.clear_widgets()

        if not expenses:
            self.list_container.add_widget(self.empty_state)
            return

        for exp in expenses:
            card = TransactionCard(
                expense=exp,
                on_edit=self._open_edit_dialog,
                on_delete=self._open_delete_dialog,
                show_actions=True,
            )
            self.list_container.add_widget(card)

    def _open_edit_dialog(self, expense: dict):
        app = App.get_running_app()
        conn = getattr(app, "conn", None)
        cats = [c["name"] for c in get_categories(conn, active_only=True)] if conn else DEFAULT_CATEGORIES

        dialog = EditExpenseDialog(
            expense=expense,
            categories=cats,
            on_save=self._save_edited_expense,
        )
        dialog.open()

    def _save_edited_expense(self, updated_data: dict):
        app = App.get_running_app()
        conn = getattr(app, "conn", None)
        if not conn:
            return

        cat_row = get_category_by_name(conn, updated_data["category_name"])
        cat_id = cat_row["id"] if cat_row else 1

        update_expense(
            conn=conn,
            expense_id=updated_data["id"],
            amount_centavos=updated_data["amount_centavos"],
            description=updated_data["description"],
            occurred_on=updated_data["occurred_on"],
            category_id=cat_id,
            category_source=updated_data["category_source"],
        )
        self.banner.show("Expense updated successfully!", variant="success")
        self.refresh_transactions()

    def _open_delete_dialog(self, expense: dict):
        desc = expense.get("description", "this expense")

        def handle_confirm():
            app = App.get_running_app()
            conn = getattr(app, "conn", None)
            if conn:
                delete_expense(conn, expense["id"])
                self.banner.show("Expense deleted.", variant="info")
                self.refresh_transactions()

        dialog = ConfirmDialog(
            title="Delete Expense",
            message=f"Are you sure you want to delete\n'{desc}'?",
            on_confirm=handle_confirm,
        )
        dialog.open()

    def _nav_to_dashboard(self, *args):
        self.banner.hide()
        app = App.get_running_app()
        if app and hasattr(app, "screen_manager"):
            app.screen_manager.current = "dashboard"

    def _nav_to_add_expense(self, *args):
        self.banner.hide()
        app = App.get_running_app()
        if app and hasattr(app, "screen_manager"):
            app.screen_manager.current = "add_expense"
