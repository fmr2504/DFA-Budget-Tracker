"""Budgets screen — per-category monthly budget limits and progress.

Placeholder for Phase 7.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label


class BudgetsScreen(Screen):
    """Screen showing budget limits and spending progress."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Label(text="Budgets\n(Phase 7)"))

