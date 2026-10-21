"""Reports screen — monthly spending breakdowns and category analysis.

Presents category-wise distributions, monthly totals, and previous/next
month navigation with mobile-friendly visuals.
"""

from __future__ import annotations

from datetime import date

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from expense_app.ui.components import (
    COLOR_PRIMARY,
    COLOR_SURFACE_LIGHT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    Card,
    EmptyState,
    HeaderBar,
    StatCard,
)


class ReportsScreen(Screen):
    """Screen for viewing monthly spending analytics and category distribution."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        today = date.today()
        self.current_month_str = today.strftime("%Y-%m")

        root = BoxLayout(orientation="vertical")
        root.add_widget(
            HeaderBar(
                title="Reports",
                subtitle="Monthly Spending Analytics",
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

        # Overview Stats
        stats_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=100,
            spacing=12,
        )
        self.total_card = StatCard(
            title="Total Spending",
            value="₱0.00",
            subtitle=f"{self.current_month_str} Total",
            value_color=COLOR_PRIMARY,
        )
        self.count_card = StatCard(
            title="Transactions",
            value="0",
            subtitle="Recorded entries",
            value_color=COLOR_TEXT_PRIMARY,
        )
        stats_row.add_widget(self.total_card)
        stats_row.add_widget(self.count_card)
        content.add_widget(stats_row)

        # Category Breakdown Card
        self.breakdown_card = Card(orientation="vertical", size_hint_y=None)
        self.breakdown_card.bind(minimum_height=self.breakdown_card.setter("height"))

        breakdown_hdr = Label(
            text="CATEGORY BREAKDOWN",
            font_size="12sp",
            bold=True,
            color=COLOR_TEXT_MUTED,
            size_hint_y=None,
            height=24,
            halign="left",
        )
        breakdown_hdr.bind(size=breakdown_hdr.setter("text_size"))
        self.breakdown_card.add_widget(breakdown_hdr)

        self.empty_reports = EmptyState(
            title="No Data for this Month",
            message=f"No expenses were recorded for {self.current_month_str}.",
        )
        self.breakdown_card.add_widget(self.empty_reports)
        content.add_widget(self.breakdown_card)

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def _nav_to_dashboard(self, *args):
        app = App.get_running_app()
        if app and hasattr(app, "screen_manager"):
            app.screen_manager.current = "dashboard"
