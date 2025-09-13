import os.path
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
        self._app = app
        self._main_window = app.main_window

        self.logger = StonksLogger.get_logger("stonks_overwatch.app", "[RELEASE_NOTES]")

        self.web_view = toga.WebView(style=Pack(flex=1))
        self.web_view.content = self._convert_md_to_html()

        box = toga.Box(children=[self.web_view], style=Pack(direction=COLUMN, margin=5))

        self.content = box

    def _convert_md_to_html(self) -> str:
        """Convert markdown file to HTML."""
        input_file = os.path.join(Path(self._app.paths.app).parent.parent, "CHANGELOG.md")

        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file {input_file} not found")

        # Read and convert
        with open(input_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Replace CHANGELOG starting lines with "Release Notes" header
        start_idx = next((i for i, line in enumerate(lines) if line.strip().startswith("##")), 0)
        markdown_content = "# Release Notes\n" + "".join(lines[start_idx:])

        html_fragment = markdown.markdown(
            markdown_content,
            extensions=[
                "fenced_code",
            ],
            output_format="html",
        )

        # Theme colors via CSS variables
        is_dark_mode = getattr(self._app, "dark_mode", True) is True
        if is_dark_mode:
            bg_color = "#3B3B3B"
            text_color = "#FFFFFF"
            code_bg = "#696969"
            blockquote_bg = "#101010"
        else:
            bg_color = "#FFFFFF"
            text_color = "#000000"
            code_bg = "#F5F5F5"
            blockquote_bg = "#F0F0F0"

        styled_html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\" />
<title>Release Notes</title>
<meta name=\"color-scheme\" content=\"dark light\" />
<style>
    :root {{
        --bg-color: {bg_color};
        --text-color: {text_color};
        --code-bg: {code_bg};
        --blockquote-bg: {blockquote_bg};
    }}
    body {{
        background:var(--bg-color); color:var(--text-color);
        font-family:-apple-system, system-ui, Segoe UI, Roboto, Oxygen, Ubuntu, Cantarell,
            'Open Sans', 'Helvetica Neue', sans-serif;
        line-height:1.5; padding:1rem 1.25rem 2rem; font-size:15px;
    }}
    h1,h2,h3,h4,h5,h6 {{
        color:var(--text-color);
        font-weight:600; line-height:1.25; margin-top:1.6em; margin-bottom:0.6em;
    }}
    h1 {{ font-size:1.9em; }} h2 {{ font-size:1.5em; }} h3 {{ font-size:1.25em; }}
    p {{ margin:0.6em 0 0.9em; }}
    a {{ color:#4ea3ff; text-decoration:none; }} a:hover {{ text-decoration:underline; }}
    hr {{ border:0; border-top:1px solid #333; margin:1.8em 0; }}
    ul,ol {{ padding-left:1.3rem; margin:0.4em 0 1em; }} li {{ margin:0.25em 0; }}
    code {{
        background:var(--code-bg); color:var(--text-color); padding:0.15em 0.4em; border-radius:4px; font-size:0.95em;
    }}
    pre code {{ padding:0; background:transparent; }}
    pre {{
        background:var(--code-bg); padding:0.85rem 1rem; border-radius:6px; overflow-x:auto;
        font-size:0.9em; line-height:1.4; border:1px solid #222;
    }}
    blockquote {{
        margin:0.9rem 0; padding:0.55rem 0.9rem; border-left:4px solid #444; background:var(--blockquote-bg);
        color:#ccc; border-radius:4px;
    }}
    img {{ max-width:100%; display:block; margin:0.75rem auto; }}
    strong {{ color:var(--text-color); }} em {{ color:#ddd; }}
</style>
</head>
<body>
{html_fragment}
</body>
</html>"""
        return styled_html

    def show(self):
        center_window_on_parent(self, self._main_window)
        super().show()
