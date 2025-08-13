import asyncio
import os

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW


class LogStreamWindow(toga.Window):
    def __init__(self, title, log_path):
        super().__init__(title=title, size=(800, 500))
        self.log_path = log_path
        self.last_position = 0
        self.search_term = ""
        self.all_log_lines = []

        # Search input
        self.search_input = toga.TextInput(
            placeholder="Search logs...", on_change=self._update_filter, style=Pack(flex=1, margin=(0, 5, 10, 0))
        )

        # Text box to display logs
        self.log_display = toga.MultilineTextInput(
            readonly=True, style=Pack(flex=1, margin=10, font_family="monospace", font_size=10)
        )

        # Layout
        self.content = toga.Box(
            children=[toga.Box(children=[self.search_input], style=Pack(direction=ROW)), self.log_display],
            style=Pack(direction=COLUMN, margin=10),
        )

        # Register the on_close handler
        self.on_close = self._handle_close

        # Start the background logs streaming task
        asyncio.create_task(self.stream_logs())

    def _handle_close(self, widget):
        # Cleanup reference in app
        self.app.log_window = None

        return True

    async def stream_logs(self):
        while True:
            await asyncio.sleep(1)

            if not os.path.exists(self.log_path):
                continue

            with open(self.log_path, "r", encoding="utf-8") as f:
                f.seek(self.last_position)
                new_data = f.read()
                self.last_position = f.tell()

            if new_data:
                # Append new lines to internal buffer
                new_lines = new_data.splitlines(keepends=True)
                self.all_log_lines.extend(new_lines)

                self._refresh_display()

    def _refresh_display(self):
        """Update log_display with current filter."""
        if self.search_term:
            filtered = [line for line in self.all_log_lines if self.search_term.lower() in line.lower()]
        else:
            filtered = self.all_log_lines

        self.log_display.value = "".join(filtered)

        self.log_display.scroll_to_bottom()

    def _update_filter(self, widget):
        self.search_term = widget.value
        self._refresh_display()
