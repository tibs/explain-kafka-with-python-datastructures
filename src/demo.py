#!/usr/bin/env python3

"""Working out some ideas for Textual UI.
"""

from textual.app import App, ComposeResult
from textual.widgets import Static
from textual.color import Color

BACKGROUND = Color.parse('lemonchiffon')
TEXT_COLOR = BACKGROUND.get_contrast_text()


TEXT = """\
Some text.
Nothing much.
"""


class BorderedApp(App[None]):
    """A text area with a solid border.
    """

    CSS_PATH = 'demo.css'

    BINDINGS = [
        ('q', "quit", 'Quit'),
    ]

    def compose(self) -> ComposeResult:
        self.widget = Static(TEXT)
        yield self.widget

    def on_mount(self) -> None:
        #self.widget.styles.background = BACKGROUND
        #self.widget.styles.color = TEXT_COLOR
        #self.widget.styles.border = ('solid', 'grey')
        self.widget.styles.width = '1fr'
        self.widget.border_title = 'This is a title'
        self.widget.border_title_align = 'left'


if __name__ == '__main__':
    app = BorderedApp()
    app.run()
