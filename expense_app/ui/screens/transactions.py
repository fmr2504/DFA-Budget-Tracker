"""Transactions screen — list, filter, edit, and delete expenses.

Placeholder for Phase 5.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label


class TransactionsScreen(Screen):
    """Screen showing the expense transaction list."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Label(text="Transactions\n(Phase 5)"))

