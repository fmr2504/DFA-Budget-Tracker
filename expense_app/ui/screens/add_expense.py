"""Add Expense screen — record a new expense with auto-categorization preview.

Provides a scrollable form with inputs for amount, description, date,
and automatic/manual category selection.
"""

from __future__ import annotations

from datetime import date

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner

from expense_app.config import DEFAULT_CATEGORIES
from expense_app.ui.components import (
    COLOR_PRIMARY,
    COLOR_SURFACE_LIGHT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    AppButton,
    Card,
    FormInput,
    HeaderBar,
    MessageBanner,
)


class AddExpenseScreen(Screen):
    """Screen for entering transaction details and reviewing category suggestions."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(orientation="vertical")
        root.add_widget(
            HeaderBar(
                title="Add Expense",
                subtitle="Record a transaction",
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

        # Message Banner (for validation warnings)
        self.banner = MessageBanner()
        self.banner.hide()
        content.add_widget(self.banner)

        # Form Card
        form_card = Card(orientation="vertical", size_hint_y=None, spacing=12)
        form_card.bind(minimum_height=form_card.setter("height"))

        # Amount Input
        self.amount_input = FormInput(
            label="Amount (PHP ₱)",
            hint_text="e.g. 150.00",
            input_filter=None,  # Handled cleanly by parse_amount in Phase 5
        )
        form_card.add_widget(self.amount_input)

        # Description Input
        self.desc_input = FormInput(
            label="Description",
            hint_text="e.g. Jollibee lunch, Jeepney fare",
        )
        form_card.add_widget(self.desc_input)

        # Date Input
        today_str = date.today().isoformat()
        self.date_input = FormInput(
            label="Date (YYYY-MM-DD)",
            initial_text=today_str,
            hint_text="YYYY-MM-DD",
        )
        form_card.add_widget(self.date_input)

        # Suggested Category Display
        sugg_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=54,
            spacing=4,
        )
        sugg_lbl = Label(
            text="SUGGESTED CATEGORY",
            font_size="12sp",
            bold=True,
            color=COLOR_TEXT_MUTED,
            size_hint_y=None,
            height=20,
            halign="left",
        )
        sugg_lbl.bind(size=sugg_lbl.setter("text_size"))
        sugg_box.add_widget(sugg_lbl)

        self.suggestion_badge = Label(
            text="Type a description to auto-suggest",
            font_size="14sp",
            color=COLOR_PRIMARY,
            size_hint_y=None,
            height=30,
            halign="left",
        )
        self.suggestion_badge.bind(size=self.suggestion_badge.setter("text_size"))
        sugg_box.add_widget(self.suggestion_badge)
        form_card.add_widget(sugg_box)

        # Category Selector (Spinner / Dropdown)
        cat_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=74,
            spacing=4,
        )
        cat_lbl = Label(
            text="CATEGORY (Override or Select)",
            font_size="12sp",
            bold=True,
            color=COLOR_TEXT_MUTED,
            size_hint_y=None,
            height=20,
            halign="left",
        )
        cat_lbl.bind(size=cat_lbl.setter("text_size"))
        cat_box.add_widget(cat_lbl)

        self.category_spinner = Spinner(
            text="Select Category",
            values=DEFAULT_CATEGORIES,
            size_hint_y=None,
            height=46,
            background_color=COLOR_SURFACE_LIGHT,
            color=COLOR_TEXT_PRIMARY,
            font_size="15sp",
        )
        cat_box.add_widget(self.category_spinner)
        form_card.add_widget(cat_box)

        content.add_widget(form_card)

        # Actions Row
        actions_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=48,
            spacing=12,
        )
        self.save_btn = AppButton(
            text="Save Expense",
            variant="primary",
        )
        self.cancel_btn = AppButton(
            text="Cancel",
            variant="secondary",
            on_release=self._nav_to_dashboard,
        )
        actions_row.add_widget(self.cancel_btn)
        actions_row.add_widget(self.save_btn)
        content.add_widget(actions_row)

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def _nav_to_dashboard(self, *args):
        app = App.get_running_app()
        if app and hasattr(app, "screen_manager"):
            app.screen_manager.current = "dashboard"
