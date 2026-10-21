"""Reusable UI components for the Expense Categorizer.

Provides touch-friendly, mobile-optimized widgets including headers,
cards, stat cards, styled buttons, form inputs, and empty states.
"""

from __future__ import annotations

from typing import Callable, Optional

from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput


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
        self.label.text = text
        self.opacity = 1
        self.height = 44

    def hide(self):
        self.label.text = ""
        self.opacity = 0
        self.height = 0
