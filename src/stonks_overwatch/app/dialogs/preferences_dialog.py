import asyncio
import json
import time

import toga
import toga.platform
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from stonks_overwatch.app.utils.dialog_utils import center_window_on_parent
from stonks_overwatch.utils.core.logger import StonksLogger


class PreferencesDialog(toga.Window):
    """Preferences dialog that displays broker configuration using a WebView."""

    def __init__(self, title: str = "Preferences", app: toga.App | None = None) -> None:
        """
        Initialize the PreferencesDialog window with a WebView.

        Args:
            title (str): The window title.
            app (toga.App | None): The Toga application instance.
        """
        super().__init__(
            title=title,
            minimizable=False,
            resizable=True,
            closable=True,
            size=(800, 600),
        )
        self.logger = StonksLogger.get_logger("stonks_overwatch.app", "[PREFERENCES]")

        self._app = app
        self._main_window = app.main_window

        # Main container
        self.main_box = toga.Box(style=Pack(direction=COLUMN, flex=1))

        # WebView to display settings
        self.webview = toga.WebView(style=Pack(flex=1))
        self.main_box.add(self.webview)

        # Buttons at the bottom
        self.button_box = toga.Box(style=Pack(direction=ROW, margin=10))
        self.save_button = toga.Button("Save", on_press=self.on_save, style=Pack(width=100, margin_right=10))
        self.cancel_button = toga.Button("Cancel", on_press=self.on_cancel, style=Pack(width=100, margin_right=10))

        platform = toga.platform.current_platform
        self.button_box.add(toga.Box(style=Pack(flex=1)))

        if platform == "macOS":
            # macOS: Cancel (left), Save (right), right-aligned
            self.button_box.add(self.cancel_button)
            self.button_box.add(self.save_button)
        else:
            # Windows/Linux: Save (left), Cancel (right), right-aligned
            self.button_box.add(self.save_button)
            self.button_box.add(self.cancel_button)

        self.main_box.add(self.button_box)
        self.content = self.main_box

    def _get_settings_url(self, force_reload: bool = True) -> str:
        """
        Get the settings URL using the app's host and port, with dark_mode support.

        Args:
            force_reload: If True, add a cache-busting timestamp parameter to force fresh content.

        Returns:
            The settings URL with query parameters.
        """
        # Use the app's running server host and port (set in main.py on_running)
        host = getattr(self._app, "host", "127.0.0.1")
        port = getattr(self._app, "port", 8000)

        # Check if app is in dark mode (similar to ReleaseNotesDialog)
        is_dark_mode = getattr(self._app, "dark_mode", True) is True

        url = f"http://{host}:{port}/settings?dark_mode={is_dark_mode}"

        # Add cache-busting parameter to force reload
        if force_reload:
            timestamp = int(time.time())  # seconds precision is sufficient as dialog opens are infrequent
            url += f"&_t={timestamp}"

        return url

    async def async_init(self):
        """Initialize the dialog by loading the settings page."""
        settings_url = self._get_settings_url()
        self.logger.debug(f"async_init: Loading settings from: {settings_url}")
        self.webview.url = settings_url

    def _get_bridge_init_script(self) -> str:
        """Return the JavaScript code to initialize the native bridge and trigger save."""
        return """
            (function () {
                if (!window.stonksNativeBridge) {
                    window.stonksNativeBridge = {};
                }
                window.stonksNativeBridge.saveResult = null;
                window.stonksNativeBridge.saveError = null;
                try {
                    const runSave = async () => {
                        try {
                            const result = await saveSettings();
                            if (typeof result === "string") {
                                window.stonksNativeBridge.saveResult = result;
                            } else if (result && typeof result === "object") {
                                window.stonksNativeBridge.saveResult = JSON.stringify(result);
                            } else {
                                window.stonksNativeBridge.saveResult = JSON.stringify({
                                    success: true,
                                    message: String(result || "Settings saved"),
                                });
                            }
                        } catch (error) {
                            window.stonksNativeBridge.saveResult = JSON.stringify({
                                success: false,
                                message: error && error.toString ? error.toString() : "Unknown error",
                            });
                        }
                    };
                    runSave();
                } catch (error) {
                    window.stonksNativeBridge.saveResult = JSON.stringify({
                        success: false,
                        message: error && error.toString ? error.toString() : "Unknown error",
                    });
                }
            })();
        """

    async def _poll_for_result(self, max_attempts: int = 50, interval: float = 0.1) -> str | None:
        """Poll the WebView for the save result."""
        poll_script = (
            "window.stonksNativeBridge && window.stonksNativeBridge.saveResult "
            "? window.stonksNativeBridge.saveResult : null"
        )

        for _ in range(max_attempts):
            result = await self.webview.evaluate_javascript(poll_script)
            if result:
                return result
            await asyncio.sleep(interval)
        return None

    def _handle_save_result(self, result: str) -> None:
        """Parse and log the save result."""
        success = False
        message = "Unknown error"

        if isinstance(result, str):
            try:
                parsed = json.loads(result)
                success = parsed.get("success", False)
                message = parsed.get("message", "")
            except json.JSONDecodeError:
                # If it's not valid JSON, assume success if we got any result
                success = True
                message = result
        else:
            success = True
            message = str(result) if result else "Settings saved"

        if success:
            self.logger.info(f"Settings saved successfully: {message}")
        else:
            self.logger.warning(f"Settings save reported failure: {message}")

    async def on_save(self, widget: toga.Widget) -> None:
        """Save settings by calling the saveSettings() JavaScript function in the WebView."""
        self.logger.debug("Save button pressed, executing saveSettings() in WebView")
        try:
            # Initialize bridge and start save
            await self.webview.evaluate_javascript(self._get_bridge_init_script())

            # Poll for result
            result = await self._poll_for_result()

            if result is None:
                self.logger.error("Timed out waiting for saveSettings() result")
            else:
                self.logger.debug(f"saveSettings() returned: {result}")
                self._handle_save_result(result)

        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}", exc_info=True)

        self.close()

    def on_cancel(self, widget: toga.Widget) -> None:
        """Close the dialog without saving."""
        self.logger.debug("Cancel button pressed")
        self.close()

    def show(self):
        """Show the preferences dialog centered on the parent window."""
        center_window_on_parent(self, self._main_window)
        super().show()
        # Set URL after window is shown
        settings_url = self._get_settings_url()
        self.logger.debug(f"show: Setting WebView URL to: {settings_url}")
        self.webview.url = settings_url
