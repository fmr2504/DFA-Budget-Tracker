"""Reusable UI components for the Expense Categorizer.

Provides touch-friendly, mobile-optimized widgets including headers,
cards, stat cards, styled buttons, form inputs, empty states, transaction cards,
and confirmation / editing dialogs.
"""

from __future__ import annotations

from typing import Callable, Optional

from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

from expense_app.logic.money import format_amount


# ---------------------------------------------------------------------------
# Styling constants
# ---------------------------------------------------------------------------

COLOR_PRIMARY = (0.13, 0.59, 0.95, 1)      # Vibrant blue
COLOR_SUCCESS = (0.18, 0.80, 0.44, 1)      # Emerald green
COLOR_WARNING = (0.95, 0.61, 0.07, 1)      # Warm amber
COLOR_DANGER = (0.91, 0.30, 0.24, 1)       # Coral red
COLOR_SURFACE = (0.16, 0.20, 0.28, 1)      # Card dark slate
COLOR_SURFACE_LIGHT = (0.22, 0.27, 0.38, 1)
COLOR_TEXT_PRIMARY = (0.96, 0.97, 0.98, 1)
COLOR_TEXT_MUTED = (0.65, 0.70, 0.78, 1)


# ---------------------------------------------------------------------------
# Card container
# ---------------------------------------------------------------------------

class Card(BoxLayout):
    """A styled container with rounded background."""

    def __init__(
        self,
        bg_color: tuple[float, float, float, float] = COLOR_SURFACE,
        radius: float = 12.0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.padding = kwargs.get("padding", [16, 16, 16, 16])
        self.spacing = kwargs.get("spacing", 10)

        with self.canvas.before:
            self._bg_color_instruction = Color(*bg_color)
            self._bg_rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[radius]
            )
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size


# ---------------------------------------------------------------------------
# Header bar
# ---------------------------------------------------------------------------

class HeaderBar(BoxLayout):
    """Top navigation and title bar."""

    def __init__(
        self,
        title: str,
        subtitle: Optional[str] = None,
        on_back: Optional[Callable] = None,
        **kwargs,
    ):
        super().__init__(orientation="horizontal", size_hint_y=None, height=60, **kwargs)
        self.padding = [12, 8, 12, 8]
        self.spacing = 10

        if on_back:
            back_btn = Button(
                text="<",
                size_hint=(None, 1),
                width=44,
                font_size="20sp",
                background_color=(0.25, 0.30, 0.40, 1),
            )
            back_btn.bind(on_release=on_back)
            self.add_widget(back_btn)

        title_box = BoxLayout(orientation="vertical", spacing=2)
        title_label = Label(
            text=title,
            font_size="18sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            halign="left",
            valign="middle",
        )
        title_label.bind(size=title_label.setter("text_size"))
        title_box.add_widget(title_label)

        if subtitle:
            sub_label = Label(
                text=subtitle,
                font_size="12sp",
                color=COLOR_TEXT_MUTED,
                halign="left",
                valign="middle",
            )
            sub_label.bind(size=sub_label.setter("text_size"))
            title_box.add_widget(sub_label)

        self.add_widget(title_box)


# ---------------------------------------------------------------------------
# Stat Card
# ---------------------------------------------------------------------------

class StatCard(Card):
    """A card displaying a prominent metric and label."""

    def __init__(
        self,
        title: str,
        value: str,
        subtitle: Optional[str] = None,
        value_color: tuple[float, float, float, float] = COLOR_PRIMARY,
        **kwargs,
    ):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            height=100,
            **kwargs,
        )

        title_lbl = Label(
            text=title.upper(),
            font_size="12sp",
            bold=True,
            color=COLOR_TEXT_MUTED,
            size_hint_y=None,
            height=20,
            halign="left",
        )
        title_lbl.bind(size=title_lbl.setter("text_size"))
        self.add_widget(title_lbl)

        self.value_label = Label(
            text=value,
            font_size="24sp",
            bold=True,
            color=value_color,
            size_hint_y=None,
            height=36,
            halign="left",
        )
        self.value_label.bind(size=self.value_label.setter("text_size"))
        self.add_widget(self.value_label)

        if subtitle:
            sub_lbl = Label(
                text=subtitle,
                font_size="11sp",
                color=COLOR_TEXT_MUTED,
                size_hint_y=None,
                height=18,
                halign="left",
            )
            sub_lbl.bind(size=sub_lbl.setter("text_size"))
            self.add_widget(sub_lbl)


# ---------------------------------------------------------------------------
# Form Input
# ---------------------------------------------------------------------------

class FormInput(BoxLayout):
    """Labeled text input with mobile-friendly touch height."""

    def __init__(
        self,
        label: str,
        hint_text: str = "",
        input_filter: Optional[str] = None,
        multiline: bool = False,
        initial_text: str = "",
        **kwargs,
    ):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            height=76 if not multiline else 110,
            spacing=4,
            **kwargs,
        )

        lbl = Label(
            text=label,
            font_size="13sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            size_hint_y=None,
            height=22,
            halign="left",
        )
        lbl.bind(size=lbl.setter("text_size"))
        self.add_widget(lbl)

        self.input = TextInput(
            text=initial_text,
            hint_text=hint_text,
            input_filter=input_filter,
            multiline=multiline,
            size_hint_y=None,
            height=46 if not multiline else 80,
            font_size="16sp",
            padding=[12, 12, 12, 12],
            background_color=COLOR_SURFACE_LIGHT,
            foreground_color=COLOR_TEXT_PRIMARY,
            hint_text_color=COLOR_TEXT_MUTED,
            cursor_color=COLOR_PRIMARY,
        )
        self.add_widget(self.input)

    @property
    def text(self) -> str:
        return self.input.text

    @text.setter
    def text(self, val: str) -> None:
        self.input.text = val


# ---------------------------------------------------------------------------
# Styled App Button
# ---------------------------------------------------------------------------

class AppButton(Button):
    """Styled touch button with minimum 48dp height."""

    def __init__(
        self,
        text: str,
        variant: str = "primary",
        **kwargs,
    ):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", 48)
        kwargs.setdefault("font_size", "15sp")
        kwargs.setdefault("bold", True)
        super().__init__(text=text, **kwargs)

        if variant == "primary":
            self.background_color = COLOR_PRIMARY
        elif variant == "success":
            self.background_color = COLOR_SUCCESS
        elif variant == "danger":
            self.background_color = COLOR_DANGER
        elif variant == "warning":
            self.background_color = COLOR_WARNING
        else:
            self.background_color = (0.28, 0.33, 0.44, 1)


# ---------------------------------------------------------------------------
# Empty State Widget
# ---------------------------------------------------------------------------

class EmptyState(BoxLayout):
    """Friendly empty state display."""

    def __init__(
        self,
        title: str,
        message: str = "",
        action_text: Optional[str] = None,
        on_action: Optional[Callable] = None,
        **kwargs,
    ):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            height=160,
            spacing=8,
            padding=[20, 20, 20, 20],
            **kwargs,
        )

        title_lbl = Label(
            text=title,
            font_size="16sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            halign="center",
        )
        self.add_widget(title_lbl)

        if message:
            msg_lbl = Label(
                text=message,
                font_size="13sp",
                color=COLOR_TEXT_MUTED,
                halign="center",
            )
            self.add_widget(msg_lbl)

        if action_text and on_action:
            act_btn = AppButton(
                text=action_text,
                size_hint=(None, None),
                width=180,
                height=42,
                pos_hint={"center_x": 0.5},
            )
            act_btn.bind(on_release=on_action)
            self.add_widget(act_btn)


# ---------------------------------------------------------------------------
# Message Banner
# ---------------------------------------------------------------------------

class MessageBanner(Card):
    """Feedback and validation banner."""

    def __init__(
        self,
        text: str = "",
        variant: str = "info",
        **kwargs,
    ):
        bg = COLOR_SURFACE_LIGHT
        if variant == "error":
            bg = (0.45, 0.15, 0.15, 1)
        elif variant == "success":
            bg = (0.12, 0.40, 0.22, 1)

        super().__init__(
            bg_color=bg,
            orientation="horizontal",
            size_hint_y=None,
            height=44,
            padding=[12, 8, 12, 8],
            **kwargs,
        )

        self.label = Label(
            text=text,
            font_size="13sp",
            color=COLOR_TEXT_PRIMARY,
            halign="left",
            valign="middle",
        )
        self.label.bind(size=self.label.setter("text_size"))
        self.add_widget(self.label)

    def show(self, text: str, variant: str = "info"):
        if variant == "error":
            self._bg_color_instruction.rgba = (0.45, 0.15, 0.15, 1)
        elif variant == "success":
            self._bg_color_instruction.rgba = (0.12, 0.40, 0.22, 1)
        else:
            self._bg_color_instruction.rgba = COLOR_SURFACE_LIGHT

        self.label.text = text
        self.opacity = 1
        self.height = 44

    def hide(self):
        self.label.text = ""
        self.opacity = 0
        self.height = 0


# ---------------------------------------------------------------------------
# Transaction Card Widget
# ---------------------------------------------------------------------------

class TransactionCard(Card):
    """Card displaying a single recorded expense with edit/delete actions."""

    def __init__(
        self,
        expense: dict,
        on_edit: Optional[Callable[[dict], None]] = None,
        on_delete: Optional[Callable[[dict], None]] = None,
        show_actions: bool = True,
        **kwargs,
    ):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            height=96 if show_actions else 72,
            padding=[14, 10, 14, 10],
            spacing=4,
            **kwargs,
        )
        self.expense = expense

        # Top row: Description and Amount
        top_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=28)
        desc_lbl = Label(
            text=expense.get("description", ""),
            font_size="15sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            halign="left",
            valign="middle",
        )
        desc_lbl.bind(size=desc_lbl.setter("text_size"))
        top_row.add_widget(desc_lbl)

        amount_str = format_amount(expense.get("amount_centavos", 0))
        amt_lbl = Label(
            text=amount_str,
            font_size="16sp",
            bold=True,
            color=COLOR_SUCCESS,
            size_hint=(None, 1),
            width=120,
            halign="right",
            valign="middle",
        )
        amt_lbl.bind(size=amt_lbl.setter("text_size"))
        top_row.add_widget(amt_lbl)
        self.add_widget(top_row)

        # Bottom row: Date, Category badge, Source, and Actions
        bottom_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=32, spacing=8)
        cat_name = expense.get("category_name", "Other")
        date_str = expense.get("occurred_on", "")
        source_tag = "[Auto]" if expense.get("category_source") == "automatic" else "[Manual]"
        meta_text = f"{date_str}  •  {cat_name} {source_tag}"

        meta_lbl = Label(
            text=meta_text,
            font_size="12sp",
            color=COLOR_TEXT_MUTED,
            halign="left",
            valign="middle",
        )
        meta_lbl.bind(size=meta_lbl.setter("text_size"))
        bottom_row.add_widget(meta_lbl)

        if show_actions:
            if on_edit:
                edit_btn = AppButton(
                    text="Edit",
                    variant="secondary",
                    size_hint=(None, None),
                    width=54,
                    height=32,
                    font_size="12sp",
                )
                edit_btn.bind(on_release=lambda _inst: on_edit(expense))
                bottom_row.add_widget(edit_btn)

            if on_delete:
                del_btn = AppButton(
                    text="Del",
                    variant="danger",
                    size_hint=(None, None),
                    width=50,
                    height=32,
                    font_size="12sp",
                )
                del_btn.bind(on_release=lambda _inst: on_delete(expense))
                bottom_row.add_widget(del_btn)

        self.add_widget(bottom_row)


# ---------------------------------------------------------------------------
# Confirmation Dialog
# ---------------------------------------------------------------------------

class ConfirmDialog(Popup):
    """Modal dialog for confirming destructive operations."""

    def __init__(
        self,
        title: str,
        message: str,
        on_confirm: Callable[[], None],
        **kwargs,
    ):
        super().__init__(
            title=title,
            size_hint=(0.85, None),
            height=200,
            auto_dismiss=False,
            **kwargs,
        )

        layout = BoxLayout(orientation="vertical", padding=14, spacing=12)

        msg_lbl = Label(
            text=message,
            font_size="14sp",
            color=COLOR_TEXT_PRIMARY,
            halign="center",
            valign="middle",
        )
        msg_lbl.bind(size=msg_lbl.setter("text_size"))
        layout.add_widget(msg_lbl)

        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=44, spacing=10)
        cancel_btn = AppButton(
            text="Cancel",
            variant="secondary",
            on_release=lambda _inst: self.dismiss(),
        )
        confirm_btn = AppButton(
            text="Delete",
            variant="danger",
            on_release=lambda _inst: (self.dismiss(), on_confirm()),
        )
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(confirm_btn)
        layout.add_widget(btn_row)

        self.content = layout


# ---------------------------------------------------------------------------
# Edit Expense Dialog
# ---------------------------------------------------------------------------

class EditExpenseDialog(Popup):
    """Modal dialog for editing an existing expense."""

    def __init__(
        self,
        expense: dict,
        categories: list[str],
        on_save: Callable[[dict], None],
        **kwargs,
    ):
        super().__init__(
            title="Edit Expense",
            size_hint=(0.92, 0.8),
            auto_dismiss=False,
            **kwargs,
        )
        self.expense = expense
        self.on_save = on_save

        layout = BoxLayout(orientation="vertical", padding=14, spacing=8)

        # Message Banner for validation inside dialog
        self.banner = MessageBanner()
        self.banner.hide()
        layout.add_widget(self.banner)

        # Inputs
        centavos = expense.get("amount_centavos", 0)
        pesos_str = f"{centavos / 100:.2f}"
        self.amount_input = FormInput(label="Amount (PHP ₱)", initial_text=pesos_str)
        self.desc_input = FormInput(label="Description", initial_text=expense.get("description", ""))
        self.date_input = FormInput(label="Date (YYYY-MM-DD)", initial_text=expense.get("occurred_on", ""))

        layout.add_widget(self.amount_input)
        layout.add_widget(self.desc_input)
        layout.add_widget(self.date_input)

        # Category Spinner
        cat_box = BoxLayout(orientation="vertical", size_hint_y=None, height=64, spacing=2)
        cat_lbl = Label(text="Category", font_size="13sp", bold=True, size_hint_y=None, height=20, halign="left")
        cat_lbl.bind(size=cat_lbl.setter("text_size"))
        cat_box.add_widget(cat_lbl)

        current_cat = expense.get("category_name", categories[0] if categories else "Other")
        self.category_spinner = Spinner(
            text=current_cat,
            values=categories,
            size_hint_y=None,
            height=42,
            background_color=COLOR_SURFACE_LIGHT,
            color=COLOR_TEXT_PRIMARY,
            font_size="14sp",
        )
        cat_box.add_widget(self.category_spinner)
        layout.add_widget(cat_box)

        # Actions
        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=44, spacing=10)
        cancel_btn = AppButton(
            text="Cancel",
            variant="secondary",
            on_release=lambda _inst: self.dismiss(),
        )
        save_btn = AppButton(
            text="Save Changes",
            variant="primary",
            on_release=self._handle_save,
        )
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(save_btn)
        layout.add_widget(btn_row)

        self.content = layout

    def _handle_save(self, *args):
        from expense_app.logic.money import parse_amount
        from expense_app.logic.reporting import validate_date

        try:
            amount_centavos = parse_amount(self.amount_input.text)
        except ValueError as e:
            self.banner.show(str(e), variant="error")
            return

        desc = self.desc_input.text.strip()
        if not desc:
            self.banner.show("Description cannot be empty.", variant="error")
            return

        date_str = self.date_input.text.strip()
        if not validate_date(date_str):
            self.banner.show("Invalid date format (YYYY-MM-DD).", variant="error")
            return

        cat_name = self.category_spinner.text

        # If user changed category, category_source becomes manual
        orig_cat = self.expense.get("category_name")
        cat_source = "manual" if cat_name != orig_cat else self.expense.get("category_source", "manual")

        updated_data = {
            "id": self.expense["id"],
            "amount_centavos": amount_centavos,
            "description": desc,
            "occurred_on": date_str,
            "category_name": cat_name,
            "category_source": cat_source,
        }
        self.dismiss()
        self.on_save(updated_data)


# ---------------------------------------------------------------------------
# Category Report Bar
# ---------------------------------------------------------------------------

class CategoryReportBar(BoxLayout):
    """Bar visualizing spending in a category with proportion fill."""

    def __init__(
        self,
        category_name: str,
        amount_centavos: int,
        percentage: float,
        **kwargs,
    ):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            height=54,
            spacing=4,
            **kwargs,
        )

        # Header row: Category Name & Amount (Percentage%)
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=22)
        cat_lbl = Label(
            text=category_name,
            font_size="14sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            halign="left",
            valign="middle",
        )
        cat_lbl.bind(size=cat_lbl.setter("text_size"))
        row.add_widget(cat_lbl)

        amount_str = format_amount(amount_centavos)
        stat_lbl = Label(
            text=f"{amount_str}  ({percentage:.1f}%)",
            font_size="13sp",
            bold=True,
            color=COLOR_PRIMARY,
            halign="right",
            valign="middle",
        )
        stat_lbl.bind(size=stat_lbl.setter("text_size"))
        row.add_widget(stat_lbl)
        self.add_widget(row)

        # Progress bar container
        bar_container = BoxLayout(size_hint_y=None, height=10)
        with bar_container.canvas.before:
            Color(0.20, 0.25, 0.35, 1)  # Track background
            self._track_rect = RoundedRectangle(pos=bar_container.pos, size=bar_container.size, radius=[5])
            Color(*COLOR_PRIMARY)
            self._fill_rect = RoundedRectangle(pos=bar_container.pos, size=(0, bar_container.height), radius=[5])

        def update_bar(*args):
            self._track_rect.pos = bar_container.pos
            self._track_rect.size = bar_container.size
            self._fill_rect.pos = bar_container.pos
            fill_w = max(0.0, min(bar_container.width, bar_container.width * (percentage / 100.0)))
            self._fill_rect.size = (fill_w, bar_container.height)

        bar_container.bind(pos=update_bar, size=update_bar)
        self.add_widget(bar_container)


# ---------------------------------------------------------------------------
# Budget Card
# ---------------------------------------------------------------------------

class BudgetCard(Card):
    """Card displaying a category budget, spending progress, and remaining balance."""

    def __init__(
        self,
        status: Any,
        on_delete: Optional[Callable[[int], None]] = None,
        **kwargs,
    ):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            height=110,
            padding=[14, 10, 14, 10],
            spacing=6,
            **kwargs,
        )
        self.status = status

        # Status badge color
        if status.status_level == "exceeded":
            badge_color = COLOR_DANGER
            badge_text = "OVER BUDGET"
            bar_color = COLOR_DANGER
        elif status.status_level == "warning":
            badge_color = COLOR_WARNING
            badge_text = f"WARNING ({status.progress_ratio * 100:.0f}%)"
            bar_color = COLOR_WARNING
        else:
            badge_color = COLOR_SUCCESS
            badge_text = "ON TRACK"
            bar_color = COLOR_SUCCESS

        # Row 1: Category Name and Status Badge + optional delete button
        top_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=26)
        cat_lbl = Label(
            text=status.category_name,
            font_size="15sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            halign="left",
            valign="middle",
        )
        cat_lbl.bind(size=cat_lbl.setter("text_size"))
        top_row.add_widget(cat_lbl)

        status_lbl = Label(
            text=badge_text,
            font_size="12sp",
            bold=True,
            color=badge_color,
            size_hint=(None, 1),
            width=110,
            halign="right",
            valign="middle",
        )
        status_lbl.bind(size=status_lbl.setter("text_size"))
        top_row.add_widget(status_lbl)

        if on_delete:
            del_btn = AppButton(
                text="X",
                variant="secondary",
                size_hint=(None, None),
                width=30,
                height=26,
                font_size="11sp",
            )
            del_btn.bind(on_release=lambda _inst: on_delete(status.category_id))
            top_row.add_widget(del_btn)

        self.add_widget(top_row)

        # Row 2: Spent / Limit and Remaining / Over
        spent_str = format_amount(status.spent_centavos)
        limit_str = format_amount(status.limit_centavos)
        figures_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=22)

        spent_lbl = Label(
            text=f"Spent: {spent_str} / {limit_str}",
            font_size="13sp",
            color=COLOR_TEXT_MUTED,
            halign="left",
            valign="middle",
        )
        spent_lbl.bind(size=spent_lbl.setter("text_size"))
        figures_row.add_widget(spent_lbl)

        if status.remaining_centavos >= 0:
            rem_text = f"Remaining: {format_amount(status.remaining_centavos)}"
            rem_color = COLOR_TEXT_PRIMARY
        else:
            rem_text = f"Over: {format_amount(abs(status.remaining_centavos))}"
            rem_color = COLOR_DANGER

        rem_lbl = Label(
            text=rem_text,
            font_size="13sp",
            bold=True,
            color=rem_color,
            halign="right",
            valign="middle",
        )
        rem_lbl.bind(size=rem_lbl.setter("text_size"))
        figures_row.add_widget(rem_lbl)
        self.add_widget(figures_row)

        # Row 3: Visual Progress Bar (clamped to 0..1)
        bar_box = BoxLayout(size_hint_y=None, height=10)
        with bar_box.canvas.before:
            Color(0.20, 0.25, 0.35, 1)  # Track
            self._track = RoundedRectangle(pos=bar_box.pos, size=bar_box.size, radius=[5])
            Color(*bar_color)
            self._fill = RoundedRectangle(pos=bar_box.pos, size=(0, bar_box.height), radius=[5])

        def update_bar(*args):
            self._track.pos = bar_box.pos
            self._track.size = bar_box.size
            self._fill.pos = bar_box.pos
            fill_w = max(0.0, min(bar_box.width, bar_box.width * status.visual_progress))
            self._fill.size = (fill_w, bar_box.height)

        bar_box.bind(pos=update_bar, size=update_bar)
        self.add_widget(bar_box)


