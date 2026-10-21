"""Reports screen — monthly spending breakdown by category.

Placeholder for Phase 6.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label


class ReportsScreen(Screen):
    """Screen showing monthly spending reports."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Label(text="Reports\n(Phase 6)"))

