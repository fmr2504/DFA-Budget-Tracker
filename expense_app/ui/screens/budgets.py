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
from expense_app.data.repositories import (
    delete_budget_for_category,
    get_budgets_for_month,
    get_categories,
    get_category_by_id,
    get_category_by_name,
    get_expenses,
    set_budget,
)
from expense_app.logic.money import parse_amount
from expense_app.logic.reporting import calculate_budget_progress, month_range, shift_month
from expense_app.ui.components import (
    COLOR_SURFACE_LIGHT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    AppButton,
    BudgetCard,
    Card,
    ConfirmDialog,
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
            on_release=lambda _inst: self._navigate_month(-1),
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
            on_release=lambda _inst: self._navigate_month(1),
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
            on_release=self._handle_save_budget,
        )
        form_card.add_widget(self.save_budget_btn)
        content.add_widget(form_card)

        # Active Budgets List Card
        self.budgets_card = Card(orientation="vertical", size_hint_y=None, spacing=10)
        self.budgets_card.bind(minimum_height=self.budgets_card.setter("height"))

        self.budgets_hdr = Label(
            text="ACTIVE BUDGETS",
            font_size="12sp",
            bold=True,
            color=COLOR_TEXT_MUTED,
            size_hint_y=None,
            height=24,
            halign="left",
        )
        self.budgets_hdr.bind(size=self.budgets_hdr.setter("text_size"))
        self.budgets_card.add_widget(self.budgets_hdr)

        self.budgets_container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=10,
        )
        self.budgets_container.bind(minimum_height=self.budgets_container.setter("height"))

        self.empty_budgets = EmptyState(
            title="No Budgets Set",
            message=f"No spending limits set for {self.current_month_str}.\nUse the form above to set a category budget.",
        )
        self.budgets_container.add_widget(self.empty_budgets)
        self.budgets_card.add_widget(self.budgets_container)
        content.add_widget(self.budgets_card)

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_pre_enter(self, *args):
        """Refresh budget limits and spending progress when screen becomes active."""
        self.refresh_budgets()

    def _navigate_month(self, offset: int):
        self.current_month_str = shift_month(self.current_month_str, offset)
        self.month_lbl.text = self.current_month_str
        self.refresh_budgets()

    def refresh_budgets(self):
        """Query SQLite database and render budget cards with current progress."""
        app = App.get_running_app()
        conn = getattr(app, "conn", None)
        if not conn:
            return

        # Update category spinner options from active categories
        active_cats = [c["name"] for c in get_categories(conn, active_only=True)]
        if active_cats:
            self.category_spinner.values = active_cats

        start_date, end_date = month_range(self.current_month_str)
        month_expenses = get_expenses(conn, start_date=start_date, end_date_exclusive=end_date)
        budgets = get_budgets_for_month(conn, self.current_month_str)

        self.budgets_container.clear_widgets()

        if not budgets:
            self.empty_budgets.message = (
                f"No spending limits set for {self.current_month_str}.\n"
                "Use the form above to set a category budget."
            )
            self.budgets_container.add_widget(self.empty_budgets)
            return

        for b in budgets:
            status = calculate_budget_progress(b, month_expenses)
            card = BudgetCard(
                status=status,
                on_delete=self._open_delete_budget_dialog,
            )
            self.budgets_container.add_widget(card)

    def _handle_save_budget(self, *args):
        cat_name = self.category_spinner.text
        if cat_name == "Select Category":
            self.banner.show("Please select a category.", variant="error")
            return

        try:
            limit_centavos = parse_amount(self.limit_input.text)
        except ValueError as e:
            self.banner.show(str(e), variant="error")
            return

        app = App.get_running_app()
        conn = getattr(app, "conn", None)
        if not conn:
            self.banner.show("Database not available.", variant="error")
            return

        cat_row = get_category_by_name(conn, cat_name)
        if not cat_row:
            self.banner.show(f"Category '{cat_name}' not found.", variant="error")
            return

        try:
            set_budget(conn, cat_row["id"], self.current_month_str, limit_centavos)
        except Exception as e:
            self.banner.show(f"Save failed: {e}", variant="error")
            return

        self.limit_input.text = ""
        self.banner.show(f"Budget limit saved for {cat_name}!", variant="success")
        self.refresh_budgets()

    def _open_delete_budget_dialog(self, category_id: int):
        app = App.get_running_app()
        conn = getattr(app, "conn", None)
        cat_row = get_category_by_id(conn, category_id) if conn else None
        cat_name = cat_row["name"] if cat_row else "this category"

        def handle_confirm():
            if conn:
                delete_budget_for_category(conn, category_id, self.current_month_str)
                self.banner.show(f"Budget for {cat_name} removed.", variant="info")
                self.refresh_budgets()

        dialog = ConfirmDialog(
            title="Remove Budget",
            message=f"Remove the {self.current_month_str} budget limit\nfor {cat_name}?",
            on_confirm=handle_confirm,
        )
        dialog.open()

    def _nav_to_dashboard(self, *args):
        self.banner.hide()
        app = App.get_running_app()
        if app and hasattr(app, "screen_manager"):
            app.screen_manager.current = "dashboard"
