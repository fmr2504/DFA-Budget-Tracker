"""Dashboard screen — monthly spending overview and quick navigation.

Displays high-level monthly metrics, quick action shortcuts, and recent
expense highlights in a touch-friendly, scrollable mobile layout.
"""

from __future__ import annotations

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from expense_app.ui.components import (
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_TEXT_PRIMARY,
    AppButton,
    Card,
    EmptyState,
    HeaderBar,
    StatCard,
)


class DashboardScreen(Screen):
    """Home screen providing high-level spending summary and quick actions."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(orientation="vertical")
        root.add_widget(HeaderBar(title="Dashboard", subtitle="Personal Expense Overview"))

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=[16, 16, 16, 24],
            spacing=16,
        )
        content.bind(minimum_height=content.setter("height"))

        # Stat cards row
        stats_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=100,
            spacing=12,
        )
        self.total_spent_card = StatCard(
            title="Spent This Month",
            value="₱0.00",
            subtitle="Current cycle",
            value_color=COLOR_PRIMARY,
        )
        self.active_budgets_card = StatCard(
            title="Budget Status",
            value="On Track",
            subtitle="0 active budgets",
            value_color=COLOR_SUCCESS,
        )
        stats_row.add_widget(self.total_spent_card)
        stats_row.add_widget(self.active_budgets_card)
        content.add_widget(stats_row)

        # Quick Actions Card
        actions_card = Card(orientation="vertical", size_hint_y=None, height=120)
        actions_lbl = Label(
            text="QUICK ACTIONS",
            font_size="12sp",
            bold=True,
            color=(0.65, 0.70, 0.78, 1),
            size_hint_y=None,
            height=20,
            halign="left",
        )
        actions_lbl.bind(size=actions_lbl.setter("text_size"))
        actions_card.add_widget(actions_lbl)

        btn_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=48,
            spacing=12,
        )
        add_btn = AppButton(
            text="+ Add Expense",
            variant="primary",
            on_release=self._nav_to_add_expense,
        )
        view_reports_btn = AppButton(
            text="View Reports",
            variant="secondary",
            on_release=self._nav_to_reports,
        )
        btn_row.add_widget(add_btn)
        btn_row.add_widget(view_reports_btn)
        actions_card.add_widget(btn_row)
        content.add_widget(actions_card)

        # Recent Transactions Section
        recent_card = Card(orientation="vertical", size_hint_y=None)
        recent_card.bind(minimum_height=recent_card.setter("height"))

        recent_hdr = Label(
            text="RECENT TRANSACTIONS",
            font_size="12sp",
            bold=True,
            color=(0.65, 0.70, 0.78, 1),
            size_hint_y=None,
            height=24,
            halign="left",
        )
        recent_hdr.bind(size=recent_hdr.setter("text_size"))
        recent_card.add_widget(recent_hdr)

        self.empty_transactions = EmptyState(
            title="No Transactions Yet",
            message="Your recorded expenses will appear here.\nTap '+ Add Expense' to record your first purchase.",
            action_text="+ Add Expense",
            on_action=self._nav_to_add_expense,
        )
        recent_card.add_widget(self.empty_transactions)
        content.add_widget(recent_card)

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def _nav_to_add_expense(self, *args):
        app = App.get_running_app()
        if app and hasattr(app, "screen_manager"):
            app.screen_manager.current = "add_expense"

    def _nav_to_reports(self, *args):
        app = App.get_running_app()
        if app and hasattr(app, "screen_manager"):
            app.screen_manager.current = "reports"
