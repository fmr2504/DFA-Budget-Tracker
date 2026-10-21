"""Dashboard screen — monthly spending summary and quick actions.

Placeholder for Phase 4.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label


class DashboardScreen(Screen):
    """Home screen showing total spent this month and quick actions."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        layout.add_widget(
            Label(
                text="Dashboard",
                font_size="24sp",
                size_hint_y=None,
                height=50,
            )
        )
        layout.add_widget(
            Label(
                text="Welcome to Expense Categorizer!\n\n"
                "Screens will be wired in Phase 4.",
                halign="center",
            )
        )
        self.add_widget(layout)

