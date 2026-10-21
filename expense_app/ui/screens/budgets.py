"""Budgets screen — manage per-category monthly spending limits and track progress.

Allows creating and reviewing category budgets, displaying visual progress bars,
remaining balances, and over-budget notices.
"""

from __future__ import annotations

from datetime import date

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner

from expense_app.config import DEFAULT_CATEGORIES
from expense_app.ui.components import (
    COLOR_SURFACE_LIGHT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    AppButton,
    Card,
    EmptyState,
    FormInput,
    HeaderBar,
    MessageBanner,
)


class BudgetsScreen(Screen):
    """Screen for creating and managing monthly category budgets."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        today = date.today()
        self.current_month_str = today.strftime("%Y-%m")

        root = BoxLayout(orientation="vertical")
        root.add_widget(
            HeaderBar(
                title="Budgets",
                subtitle="Monthly Limits & Progress",
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

        # Message Banner
        self.banner = MessageBanner()
        self.banner.hide()
        content.add_widget(self.banner)

        # Month Selector Bar
        month_bar = Card(
            orientation="horizontal",
            size_hint_y=None,
            height=54,
            padding=[8, 6, 8, 6],
            spacing=10,
        )
        self.prev_btn = Button(
            text="<",
            size_hint=(None, 1),
            width=46,
            font_size="18sp",
            bold=True,
            background_color=COLOR_SURFACE_LIGHT,
        )
        self.month_lbl = Label(
            text=self.current_month_str,
            font_size="16sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            halign="center",
        )
        self.next_btn = Button(
            text=">",
            size_hint=(None, 1),
            width=46,
            font_size="18sp",
            bold=True,
            background_color=COLOR_SURFACE_LIGHT,
        )
        month_bar.add_widget(self.prev_btn)
        month_bar.add_widget(self.month_lbl)
        month_bar.add_widget(self.next_btn)
        content.add_widget(month_bar)

        # Set Budget Form Card
        form_card = Card(orientation="vertical", size_hint_y=None, spacing=10)
        form_card.bind(minimum_height=form_card.setter("height"))

        form_hdr = Label(
            text="SET OR UPDATE BUDGET",
            font_size="12sp",
            bold=True,
            color=COLOR_TEXT_MUTED,
            size_hint_y=None,
            height=20,
            halign="left",
        )
        form_hdr.bind(size=form_hdr.setter("text_size"))
        form_card.add_widget(form_hdr)

        # Category Picker
        self.category_spinner = Spinner(
            text="Select Category",
            values=DEFAULT_CATEGORIES,
            size_hint_y=None,
            height=46,
            background_color=COLOR_SURFACE_LIGHT,
            color=COLOR_TEXT_PRIMARY,
            font_size="15sp",
        )
        form_card.add_widget(self.category_spinner)

        # Limit input
        self.limit_input = FormInput(
            label="Monthly Limit (PHP ₱)",
            hint_text="e.g. 5000.00",
        )
        form_card.add_widget(self.limit_input)

        self.save_budget_btn = AppButton(
            text="Save Budget Limit",
            variant="primary",
        )
        form_card.add_widget(self.save_budget_btn)
        content.add_widget(form_card)

        # Active Budgets List Card
        self.budgets_card = Card(orientation="vertical", size_hint_y=None)
        self.budgets_card.bind(minimum_height=self.budgets_card.setter("height"))

        budgets_hdr = Label(
            text="ACTIVE BUDGETS",
            font_size="12sp",
            bold=True,
            color=COLOR_TEXT_MUTED,
            size_hint_y=None,
            height=24,
            halign="left",
        )
        budgets_hdr.bind(size=budgets_hdr.setter("text_size"))
        self.budgets_card.add_widget(budgets_hdr)

        self.empty_budgets = EmptyState(
            title="No Budgets Set",
            message=f"No spending limits set for {self.current_month_str}.\nUse the form above to set a category budget.",
        )
        self.budgets_card.add_widget(self.empty_budgets)
        content.add_widget(self.budgets_card)

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def _nav_to_dashboard(self, *args):
        app = App.get_running_app()
        if app and hasattr(app, "screen_manager"):
            app.screen_manager.current = "dashboard"
