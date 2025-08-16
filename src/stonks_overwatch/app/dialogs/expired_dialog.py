import toga

from stonks_overwatch.app.utils.dialog_utils import center_window_on_parent


class ExpiredDialog(toga.Window):
    def __init__(self, title: str, base_url: str, main_window: toga.Window):
        super().__init__(
            title=title,
            minimizable=False,
            resizable=False,
            closable=True,
            size=(375, 550),
        )
        self._main_window = main_window

        # Set the content
        self.content = toga.WebView()
        self.content.url = f"{base_url}/expired?full=false"

    def show(self):
        center_window_on_parent(self, self._main_window)
        super().show()
