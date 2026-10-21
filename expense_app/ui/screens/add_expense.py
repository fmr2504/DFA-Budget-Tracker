"""Add Expense screen — record a new expense with real-time DFA categorization.

Provides a mobile-friendly form with live keyword matching, manual override,
and input validation with helpful error banners.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner

from expense_app.config import DEFAULT_CATEGORIES
from expense_app.data.repositories import create_expense, get_category_by_name
from expense_app.logic.money import parse_amount
from expense_app.logic.reporting import validate_date
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

        self.category_source = "automatic"
        self.matched_pattern: Optional[str] = None
        self.manual_override = False
        self._setting_spinner_programmatically = False

        root = BoxLayout(orientation="vertical")
        root.add_widget(
            HeaderBar(
                title="Add Expense",
                subtitle="Record a transaction",
                on_back=self._handle_cancel,
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

        # Message Banner (for validation warnings and success notices)
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
        )
        form_card.add_widget(self.amount_input)

        # Description Input
        self.desc_input = FormInput(
            label="Description",
            hint_text="e.g. Jollibee lunch, Jeepney fare",
        )
        self.desc_input.input.bind(text=self._on_description_changed)
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
            text="CATEGORY (Auto-selected or Override)",
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
        self.category_spinner.bind(text=self._on_category_selected)
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
        self.cancel_btn = AppButton(
            text="Cancel",
            variant="secondary",
            on_release=self._handle_cancel,
        )
        self.save_btn = AppButton(
            text="Save Expense",
            variant="primary",
            on_release=self._handle_save,
        )
        actions_row.add_widget(self.cancel_btn)
        actions_row.add_widget(self.save_btn)
        content.add_widget(actions_row)

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def _on_description_changed(self, _instance, text: str):
        """Run DFA categorizer as user types description."""
        app = App.get_running_app()
        categorizer = getattr(app, "categorizer", None)
        if not categorizer:
            return

        clean = text.strip()
        if not clean:
            self.suggestion_badge.text = "Type a description to auto-suggest"
            self.suggestion_badge.color = COLOR_PRIMARY
            if not self.manual_override:
                self._set_spinner_text("Select Category")
                self.category_source = "automatic"
                self.matched_pattern = None
            return

        result = categorizer.categorize(clean)

        if result.is_fallback:
            self.suggestion_badge.text = f"Suggested: {result.suggested_category} (Fallback)"
            self.suggestion_badge.color = COLOR_TEXT_MUTED
            self.matched_pattern = None
        elif result.is_ambiguous:
            cats = ", ".join(result.tied_categories)
            self.suggestion_badge.text = f"Suggested: {result.suggested_category} (Ambiguous: {cats})"
            self.suggestion_badge.color = (0.95, 0.61, 0.07, 1)  # Warning amber
            self.matched_pattern = result.matches[0].rule.pattern if result.matches else None
        else:
            pat = result.matches[0].rule.pattern if result.matches else ""
            self.suggestion_badge.text = f"Suggested: {result.suggested_category} (Matched '{pat}')"
            self.suggestion_badge.color = (0.18, 0.80, 0.44, 1)  # Success emerald
            self.matched_pattern = pat

        if not self.manual_override:
            self._set_spinner_text(result.suggested_category)
            self.category_source = "automatic"

    def _set_spinner_text(self, text: str):
        self._setting_spinner_programmatically = True
        self.category_spinner.text = text
        self._setting_spinner_programmatically = False

    def _on_category_selected(self, _instance, text: str):
        """Track user manual overrides of category."""
        if self._setting_spinner_programmatically:
            return
        if text != "Select Category":
            self.manual_override = True
            self.category_source = "manual"

    def _handle_save(self, *args):
        """Validate and persist the expense record."""
        # 1. Validate Amount
        try:
            amount_centavos = parse_amount(self.amount_input.text)
        except ValueError as e:
            self.banner.show(str(e), variant="error")
            return

        # 2. Validate Description
        desc = self.desc_input.text.strip()
        if not desc:
            self.banner.show("Please enter an expense description.", variant="error")
            return

        # 3. Validate Date
        occurred_on = self.date_input.text.strip()
        if not validate_date(occurred_on):
            self.banner.show("Date must be in YYYY-MM-DD format.", variant="error")
            return

        # 4. Validate Category
        cat_name = self.category_spinner.text
        if cat_name == "Select Category":
            cat_name = "Other"

        app = App.get_running_app()
        conn = getattr(app, "conn", None)
        if not conn:
            self.banner.show("Database not available.", variant="error")
            return

        cat_row = get_category_by_name(conn, cat_name)
        if not cat_row:
            self.banner.show(f"Category '{cat_name}' not found.", variant="error")
            return

        category_id = cat_row["id"]

        try:
            create_expense(
                conn=conn,
                amount_centavos=amount_centavos,
                description=desc,
                occurred_on=occurred_on,
                category_id=category_id,
                category_source=self.category_source,
                matched_pattern=self.matched_pattern,
            )
        except Exception as e:
            self.banner.show(f"Save failed: {e}", variant="error")
            return

        # Reset form fields
        self.amount_input.text = ""
        self.desc_input.text = ""
        self.date_input.text = date.today().isoformat()
        self.suggestion_badge.text = "Type a description to auto-suggest"
        self.suggestion_badge.color = COLOR_PRIMARY
        self.manual_override = False
        self._set_spinner_text("Select Category")
        self.category_source = "automatic"
        self.matched_pattern = None

        self.banner.show("Expense recorded successfully!", variant="success")

    def _handle_cancel(self, *args):
        self.banner.hide()
        app = App.get_running_app()
        if app and hasattr(app, "screen_manager"):
            app.screen_manager.current = "dashboard"
