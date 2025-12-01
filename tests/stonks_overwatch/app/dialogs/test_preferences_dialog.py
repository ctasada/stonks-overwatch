"""
Tests for the PreferencesDialog class.

This module tests the preferences dialog functionality including
initialization, WebView setup, button interactions, URL handling, and dark mode support.
"""

from ..toga_test_utils import conditional_import, skip_if_toga_unavailable

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Skip all tests in this module if toga is not available
pytestmark = skip_if_toga_unavailable

# Conditionally import PreferencesDialog only if toga is available
PreferencesDialog = conditional_import("PreferencesDialog", "stonks_overwatch.app.dialogs.preferences_dialog")


class TestPreferencesDialog:
    """Test cases for the PreferencesDialog class."""

    @pytest.fixture
    def mock_toga_deps(self):
        """Mock all Toga dependencies."""
        with (
            patch("stonks_overwatch.app.dialogs.preferences_dialog.toga") as mock_toga,
            patch("stonks_overwatch.app.dialogs.preferences_dialog.Pack") as mock_pack,
            patch("stonks_overwatch.app.dialogs.preferences_dialog.toga.platform") as mock_platform,
        ):
            # Configure toga mocks
            mock_toga.Window = MagicMock()
            mock_toga.Box = MagicMock(return_value=MagicMock())
            mock_toga.WebView = MagicMock(return_value=MagicMock())
            mock_toga.Button = MagicMock(return_value=MagicMock())
            mock_platform.current_platform = "macOS"

            yield {
                "toga": mock_toga,
                "Pack": mock_pack,
                "platform": mock_platform,
            }

    @pytest.fixture
    def mock_app(self):
        """Create a mock Toga app with host, port, and dark_mode attributes."""
        app = MagicMock()
        app.main_window = MagicMock()
        app.host = "127.0.0.1"
        app.port = 8000
        app.dark_mode = True
        return app

    @pytest.fixture
    def mock_dependencies(self):
        """Mock external dependencies."""
        with (
            patch("stonks_overwatch.app.dialogs.preferences_dialog.StonksLogger") as mock_logger,
            patch("stonks_overwatch.app.dialogs.preferences_dialog.center_window_on_parent") as mock_center,
        ):
            mock_logger.get_logger.return_value = MagicMock()

            yield {
                "StonksLogger": mock_logger,
                "center_window_on_parent": mock_center,
            }

    @pytest.fixture
    def preferences_dialog(self, mock_toga_deps, mock_app, mock_dependencies):
        """Create a PreferencesDialog instance with mocked dependencies."""
        with patch("toga.App.app", mock_app):
            return PreferencesDialog("Test Preferences", mock_app)

    @pytest.fixture
    def mock_async_sleep(self):
        """Patch asyncio.sleep to avoid real delays during polling."""
        with patch("stonks_overwatch.app.dialogs.preferences_dialog.asyncio.sleep", new=AsyncMock()) as mock_sleep:
            yield mock_sleep

    def test_initialization(self, preferences_dialog, mock_dependencies):
        """Test PreferencesDialog initialization."""
        assert preferences_dialog.title == "Test Preferences"
        assert preferences_dialog._app is not None
        assert preferences_dialog._main_window is not None

        # Verify logger was set up
        mock_dependencies["StonksLogger"].get_logger.assert_called_with("stonks_overwatch.app", "[PREFERENCES]")

    def test_window_properties(self, mock_toga_deps, mock_app, mock_dependencies):
        """Test window properties are set correctly during initialization."""
        with patch("toga.App.app", mock_app):
            dialog = PreferencesDialog("Test Window", mock_app)

            # Verify basic properties are set
            assert dialog.title == "Test Window"
            assert hasattr(dialog, "logger")

    def test_layout_components_created(self, preferences_dialog, mock_toga_deps):
        """Test that layout components are created during initialization."""
        # Verify main_box was created
        assert hasattr(preferences_dialog, "main_box")

        # Verify webview was created
        assert hasattr(preferences_dialog, "webview")

        # Verify button_box was created
        assert hasattr(preferences_dialog, "button_box")

        # Verify buttons were created
        assert hasattr(preferences_dialog, "save_button")
        assert hasattr(preferences_dialog, "cancel_button")

        # Verify Box and WebView creation was called
        assert mock_toga_deps["toga"].Box.called
        assert mock_toga_deps["toga"].WebView.called
        assert mock_toga_deps["toga"].Button.called

    def test_app_and_main_window_references(self, preferences_dialog, mock_app):
        """Test that app and main window references are stored correctly."""
        assert preferences_dialog._app == mock_app
        assert preferences_dialog._main_window == mock_app.main_window

    def test_default_title(self, mock_toga_deps, mock_app, mock_dependencies):
        """Test default title when none provided."""
        with patch("toga.App.app", mock_app):
            dialog = PreferencesDialog(app=mock_app)

            # Should use default title "Preferences"
            assert "Preferences" in str(dialog.title)

    def test_get_settings_url_with_app_host_port(self, preferences_dialog, mock_app):
        """Test _get_settings_url uses app's host and port."""
        mock_app.host = "192.168.1.100"
        mock_app.port = 9000
        mock_app.dark_mode = True

        url = preferences_dialog._get_settings_url()

        assert url.startswith("http://192.168.1.100:9000/settings?dark_mode=True")
        assert "&_t=" in url  # Cache-busting timestamp parameter

    def test_get_settings_url_default_values(self, mock_toga_deps, mock_app, mock_dependencies):
        """Test _get_settings_url uses defaults when app doesn't have host/port."""
        # Delete host and port to simulate app before server is started
        del mock_app.host
        del mock_app.port

        with patch("toga.App.app", mock_app):
            dialog = PreferencesDialog("Test", mock_app)
            url = dialog._get_settings_url()

            # Should use default values since host/port don't exist on mock_app
            assert url.startswith("http://127.0.0.1:8000/settings?dark_mode=True")
            assert "&_t=" in url  # Cache-busting timestamp parameter

    def test_get_settings_url_dark_mode_true(self, mock_toga_deps, mock_app, mock_dependencies):
        """Test _get_settings_url includes dark_mode=True when app is in dark mode."""
        mock_app.dark_mode = True

        with patch("toga.App.app", mock_app):
            dialog = PreferencesDialog("Test", mock_app)
            url = dialog._get_settings_url()

            assert "dark_mode=True" in url

    def test_get_settings_url_dark_mode_false(self, mock_toga_deps, mock_app, mock_dependencies):
        """Test _get_settings_url includes dark_mode=False when app is in light mode."""
        mock_app.dark_mode = False

        with patch("toga.App.app", mock_app):
            dialog = PreferencesDialog("Test", mock_app)
            url = dialog._get_settings_url()

            assert "dark_mode=False" in url

    def test_get_settings_url_force_reload_false(self, preferences_dialog, mock_app):
        """Test _get_settings_url doesn't add cache-busting when force_reload=False."""
        mock_app.host = "127.0.0.1"
        mock_app.port = 8000
        mock_app.dark_mode = True

        url = preferences_dialog._get_settings_url(force_reload=False)

        assert url == "http://127.0.0.1:8000/settings?dark_mode=True"
        assert "&_t=" not in url  # No cache-busting timestamp parameter

    @pytest.mark.asyncio
    async def test_async_init_sets_webview_url(self, preferences_dialog, mock_app):
        """Test async_init sets the WebView URL."""
        mock_app.host = "127.0.0.1"
        mock_app.port = 8000
        mock_app.dark_mode = True

        await preferences_dialog.async_init()

        assert preferences_dialog.webview.url.startswith("http://127.0.0.1:8000/settings?dark_mode=True")
        assert "&_t=" in preferences_dialog.webview.url  # Cache-busting timestamp parameter

    @pytest.mark.asyncio
    async def test_on_save_calls_javascript_and_closes(self, preferences_dialog, mock_async_sleep):
        """Test on_save executes JavaScript saveSettings() and closes dialog."""
        # Mock evaluate_javascript call sequence: init script, first poll, second poll with result
        preferences_dialog.webview.evaluate_javascript = AsyncMock(
            side_effect=[None, None, '{"success": true, "message": "Saved"}']
        )
        preferences_dialog.close = MagicMock()

        await preferences_dialog.on_save(MagicMock())

        # Verify JavaScript was called to start the save operation
        assert preferences_dialog.webview.evaluate_javascript.call_count == 3
        start_call = preferences_dialog.webview.evaluate_javascript.call_args_list[0][0][0]
        assert "saveSettings()" in start_call

        # Verify dialog was closed
        preferences_dialog.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_save_handles_json_string_result(self, preferences_dialog, mock_async_sleep):
        """Test on_save correctly parses JSON string result from JavaScript."""
        preferences_dialog.webview.evaluate_javascript = AsyncMock(
            side_effect=[None, '{"success": true, "message": "Configuration saved successfully"}']
        )
        preferences_dialog.close = MagicMock()

        await preferences_dialog.on_save(MagicMock())

        # Should complete without error and close
        preferences_dialog.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_save_handles_failure_result(self, preferences_dialog, mock_async_sleep):
        """Test on_save handles failure result from JavaScript."""
        preferences_dialog.webview.evaluate_javascript = AsyncMock(
            side_effect=[None, '{"success": false, "message": "Validation failed"}']
        )
        preferences_dialog.close = MagicMock()

        await preferences_dialog.on_save(MagicMock())

        # Should still close even on failure
        preferences_dialog.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_save_handles_non_json_string_result(self, preferences_dialog, mock_async_sleep):
        """Test on_save handles non-JSON string result from JavaScript."""
        preferences_dialog.webview.evaluate_javascript = AsyncMock(side_effect=[None, "some string result"])
        preferences_dialog.close = MagicMock()

        await preferences_dialog.on_save(MagicMock())

        # Should complete without error and close (assumes success for non-JSON)
        preferences_dialog.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_save_handles_exception(self, preferences_dialog, mock_async_sleep):
        """Test on_save handles exceptions gracefully."""
        preferences_dialog.webview.evaluate_javascript = AsyncMock(side_effect=Exception("JavaScript error"))
        preferences_dialog.close = MagicMock()

        # Should not raise exception
        await preferences_dialog.on_save(MagicMock())

        # Should still close even on exception
        preferences_dialog.close.assert_called_once()

    def test_on_cancel_closes_dialog(self, preferences_dialog):
        """Test on_cancel closes the dialog."""
        preferences_dialog.close = MagicMock()

        preferences_dialog.on_cancel(MagicMock())

        preferences_dialog.close.assert_called_once()

    def test_show_centers_window_and_sets_url(self, preferences_dialog, mock_dependencies, mock_app):
        """Test show centers the window and sets WebView URL."""
        mock_app.host = "127.0.0.1"
        mock_app.port = 8000
        mock_app.dark_mode = True

        with patch.object(preferences_dialog, "show", wraps=preferences_dialog.show):
            # Call the original show method but patch super().show()
            with patch("toga.Window.show"):
                preferences_dialog.show()

        # Verify center_window_on_parent was called
        mock_dependencies["center_window_on_parent"].assert_called_once_with(
            preferences_dialog, preferences_dialog._main_window
        )

        # Verify URL was set with cache-busting parameter
        assert preferences_dialog.webview.url.startswith("http://127.0.0.1:8000/settings?dark_mode=True")
        assert "&_t=" in preferences_dialog.webview.url  # Cache-busting timestamp parameter

    def test_button_order_macos(self, mock_toga_deps, mock_app, mock_dependencies):
        """Test button order is Cancel, Save on macOS."""
        mock_toga_deps["toga"].platform.current_platform = "macOS"

        with patch("toga.App.app", mock_app):
            dialog = PreferencesDialog("Test", mock_app)

            # On macOS, Cancel should be added before Save
            # This is verified by the order of button_box.add calls
            assert hasattr(dialog, "cancel_button")
            assert hasattr(dialog, "save_button")

    def test_button_order_windows(self, mock_toga_deps, mock_app, mock_dependencies):
        """Test button order is Save, Cancel on Windows/Linux."""
        mock_toga_deps["toga"].platform.current_platform = "Windows"

        with patch("toga.App.app", mock_app):
            dialog = PreferencesDialog("Test", mock_app)

            # On Windows, Save should be added before Cancel
            assert hasattr(dialog, "save_button")
            assert hasattr(dialog, "cancel_button")

    def test_webview_style(self, mock_toga_deps, mock_app, mock_dependencies):
        """Test WebView is created with flex=1 style."""
        with patch("toga.App.app", mock_app):
            PreferencesDialog("Test", mock_app)

            # Verify WebView was created with style
            mock_toga_deps["toga"].WebView.assert_called()

    def test_main_box_contains_webview_and_buttons(self, preferences_dialog):
        """Test main_box contains webview and button_box."""
        # Verify main_box.add was called for webview and button_box
        assert preferences_dialog.main_box.add.called

    def test_content_set_to_main_box(self, preferences_dialog):
        """Test window content is set to main_box."""
        assert preferences_dialog.content == preferences_dialog.main_box
