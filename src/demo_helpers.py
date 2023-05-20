#!/usr/bin/env python3

"""Helpers and common code for the demo programs.
"""

import asyncio
import random

from collections import deque

from rich.panel import Panel
from textual.widget import Widget


class DemoWidgetMixin(Widget):
    """Provide common functionality for our demo widgets

    Subclass, and then make multuple instances of the subclass, which will share
    the same `lines` dictionary.
    """

    # Maximum number of lines to keep for a widget display
    MAX_LINES = 40

    def __init__(self, instance_number: int, name: str | None = None) -> None:

        if name is None:
            name = f'{self.__class__.__name__}_{instance_number}'

        self.name = name
        self.instance_number = instance_number
        self.lines = deque(maxlen=self.MAX_LINES)
        super().__init__(name)

    def add_line(self, text):
        """Add a line of text to our scrolling display"""
        self.lines.append(text)
        self.refresh()
        self.app.refresh()

    def change_last_line(self, text):
        """Change the last line of text to our scrolling display"""
        self.lines[-1] = text
        self.refresh()
        self.app.refresh()

    def make_text(self, height):
        lines = list(self.lines)
        # The value of 2 seems unnecessarily magical
        # I assume it's the widget height - the panel border
        return '\n'.join(lines[-(height-2):])

    def render(self):
        text = self.make_text(self.size.height)
        return Panel(text, title=self.name)
