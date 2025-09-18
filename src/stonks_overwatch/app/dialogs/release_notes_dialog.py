import toga

from stonks_overwatch.app.utils.dialog_utils import center_window_on_parent
from stonks_overwatch.utils.core.logger import StonksLogger


class ReleaseNotesDialog(toga.Window):
    def __init__(self, title: str, base_url: str, app: toga.App | None = None):
        super().__init__(title=title, minimizable=False, closable=True, size=(600, 500))
        self._app = app
        self._main_window = app.main_window

        self.logger = StonksLogger.get_logger("stonks_overwatch.app", "[RELEASE_NOTES]")

        is_dark_mode = getattr(self._app, "dark_mode", True) is True

        self.content = toga.WebView()
        self.content.url = f"{base_url}/release_notes?dark_mode={is_dark_mode}"

    def show(self):
        center_window_on_parent(self, self._main_window)
        super().show()
