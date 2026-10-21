"""Add Expense screen — record a new expense with auto-categorization.

Placeholder for Phase 5.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label


class AddExpenseScreen(Screen):
    """Screen for entering a new expense."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Label(text="Add Expense\n(Phase 5)"))

