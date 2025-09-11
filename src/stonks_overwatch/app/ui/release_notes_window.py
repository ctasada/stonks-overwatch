import os.path
import sys
from pathlib import Path

import markdown
import toga
from toga.style import Pack
from toga.style.pack import COLUMN

from stonks_overwatch.app.utils.dialog_utils import center_window_on_parent
from stonks_overwatch.utils.core.logger import StonksLogger


class ReleaseNotesDialog(toga.Window):
    def __init__(self, title="Release Notes", app: toga.App | None = None):
        super().__init__(title=title, size=(600, 500))
        self._main_window = app.main_window

        self.logger = StonksLogger.get_logger("stonks_overwatch.app", "[RELEASE_NOTES]")

        self.web_view = toga.WebView(style=Pack(flex=1))
        self.web_view.content = self._convert_md_to_html()

        box = toga.Box(children=[self.web_view], style=Pack(direction=COLUMN, margin=5))

        self.content = box

    def _convert_md_to_html(self) -> str:
        """Convert markdown file to HTML."""
        input_file = os.path.join(Path(sys.executable).parent.parent, "Resources", "app", "CHANGELOG.md")

        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file {input_file} not found")

        # Read and convert
        with open(input_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Replace CHANGELOG starting lines with "Release Notes" header
        start_idx = next((i for i, line in enumerate(lines) if line.strip().startswith("##")), 0)
        markdown_content = "# Release Notes\n" + "".join(lines[start_idx:])

        return markdown.markdown(markdown_content)

    def show(self):
        center_window_on_parent(self, self._main_window)
        super().show()
