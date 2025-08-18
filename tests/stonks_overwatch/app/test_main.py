"""
Tests for the main StonksOverwatchApp class.

This module tests the Toga application initialization, startup sequence,
web server management, and license checking functionality.
"""

import asyncio
import os
import warnings
from threading import Thread

from stonks_overwatch.app.main import StonksOverwatchApp

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.django_db
class TestStonksOverwatchApp:
    """Test cases for the StonksOverwatchApp class."""

    @pytest.fixture
    def mock_toga_deps(self):
        """Mock all Toga and Django dependencies."""
        with (
            patch("stonks_overwatch.app.main.toga") as mock_toga,
            patch("stonks_overwatch.app.main.django") as mock_django,
            patch("stonks_overwatch.app.main.call_command") as mock_call,
            patch("stonks_overwatch.app.main.WSGIHandler") as mock_handler,
            patch("stonks_overwatch.app.main.WSGIRequestHandler") as mock_req,
            patch("stonks_overwatch.app.main.StaticFilesMiddleware") as mock_static,
            patch("stonks_overwatch.app.main.ThreadedWSGIServer") as mock_server,
        ):
            # Configure specific mocks
            mock_toga.App = MagicMock
            mock_toga.MainWindow = MagicMock
            mock_toga.WebView = MagicMock
            mock_toga.ConfirmDialog = MagicMock

            yield {
                "toga": mock_toga,
                "django": mock_django,
                "call_command": mock_call,
                "WSGIHandler": mock_handler,
                "WSGIRequestHandler": mock_req,
                "StaticFilesMiddleware": mock_static,
                "ThreadedWSGIServer": mock_server,
            }

    @pytest.fixture
    def mock_managers(self):
        """Mock the manager classes."""
        with (
            patch("stonks_overwatch.app.main.MenuManager") as mock_menu,
            patch("stonks_overwatch.app.main.DialogManager") as mock_dialog,
            patch("stonks_overwatch.app.main.LicenseManager") as mock_license,
            patch("stonks_overwatch.app.main.StonksLogger") as mock_logger,
        ):
            mock_logger.get_logger.return_value = MagicMock()

            yield {
                "MenuManager": mock_menu,
                "DialogManager": mock_dialog,
                "LicenseManager": mock_license,
                "StonksLogger": mock_logger,
            }

    @pytest.fixture
    def app_instance(self, mock_toga_deps, mock_managers):
        """Create a StonksOverwatchApp instance with mocked dependencies."""
        # Mock the logger
        mock_managers["StonksLogger"].get_logger.return_value = MagicMock()

        app = StonksOverwatchApp("Test App", "com.test.app")
        return app

    def test_initialization(self, app_instance, mock_managers):
        """Test that the app initializes correctly with all required components."""
        # Verify logger is set up
        mock_managers["StonksLogger"].get_logger.assert_called_with("stonks_overwatch.app", "[APP]")

        # Verify managers are initialized
        mock_managers["LicenseManager"].assert_called_once()
        mock_managers["MenuManager"].assert_called_once_with(app_instance)
        mock_managers["DialogManager"].assert_called_once_with(app_instance)

        # Verify instance variables are initialized
        assert app_instance.main_window is None
        assert app_instance.on_exit is None
        assert app_instance.server_thread is None
        assert app_instance.web_view is None
        assert app_instance._httpd is None
        assert app_instance.server_exists is None
        assert app_instance.host is None
        assert app_instance.port is None
        assert app_instance._license_dialog_shown is False

    def test_web_server_environment_setup(self, app_instance, mock_toga_deps):
        """Test that web_server method sets up environment variables correctly."""
        # Use context manager for os.environ patching to ensure proper cleanup
        with patch.dict(os.environ, {}, clear=True):
            # Mock paths using property override
            mock_paths = MagicMock()
            mock_paths.data.as_posix.return_value = "/test/data"
            mock_paths.config.as_posix.return_value = "/test/config"
            mock_paths.logs.as_posix.return_value = "/test/logs"
            mock_paths.cache.as_posix.return_value = "/test/cache"

            with patch.object(type(app_instance), "paths", new_callable=lambda: mock_paths):
                # Mock the server components
                mock_server = MagicMock()
                mock_toga_deps["ThreadedWSGIServer"].return_value = mock_server
                with patch.object(type(app_instance), "loop", new_callable=lambda: MagicMock()):
                    app_instance.server_exists = MagicMock()

                    # Mock STATIC_ROOT import
                    with patch("stonks_overwatch.settings.STATIC_ROOT", "/test/static"):
                        app_instance.web_server()

            # Verify environment variables are set
            assert os.environ["STONKS_OVERWATCH_APP"] == "1"
            assert os.environ["DJANGO_SETTINGS_MODULE"] == "stonks_overwatch.settings"
            assert os.environ["STONKS_OVERWATCH_DATA_DIR"] == "/test/data"
            assert os.environ["STONKS_OVERWATCH_CONFIG_DIR"] == "/test/config"
            assert os.environ["STONKS_OVERWATCH_LOGS_DIR"] == "/test/logs"
            assert os.environ["STONKS_OVERWATCH_CACHE_DIR"] == "/test/cache"

        # Verify Django setup is called
        mock_toga_deps["django"].setup.assert_called_once_with(set_prefix=False)

        # Verify database migration is called
        mock_toga_deps["call_command"].assert_called_once_with("migrate")

        # Verify server is set up
        mock_toga_deps["ThreadedWSGIServer"].assert_called_once_with(
            ("127.0.0.1", 0), mock_toga_deps["WSGIRequestHandler"]
        )
        assert mock_server.daemon_threads is True

    def test_startup_sequence(self, app_instance, mock_toga_deps):
        """Test the startup method initializes components in the correct order."""
        # Mock MainWindow to avoid property setter issues
        mock_main_window = MagicMock()
        mock_toga_deps["toga"].MainWindow.return_value = mock_main_window

        # Mock the main_window property to avoid Toga validation
        with patch.object(type(app_instance), "main_window", new_callable=lambda: mock_main_window):
            # Suppress the deprecation warning about no event loop for this test
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                app_instance.startup()

        # Verify components are initialized
        assert isinstance(app_instance.server_exists, asyncio.Future)
        # Verify WebView and MainWindow were called
        assert mock_toga_deps["toga"].WebView.called
        assert mock_toga_deps["toga"].MainWindow.called

        # Verify server thread is started
        assert isinstance(app_instance.server_thread, Thread)
        # Thread uses _target attribute (not target)
        assert app_instance.server_thread._target == app_instance.web_server

        # Verify main window configuration was attempted (size assignment)
        # We can just verify the content attribute was set since that's what happens next
        assert mock_main_window.content is not None
        # Note: web_view is set via property, so we check it was created
        # We can verify the mock was used
        assert mock_toga_deps["toga"].WebView.called

        # Verify exit handler is set
        assert app_instance.on_exit == app_instance.exit_handler

        # Verify menu setup is called
        app_instance.menu_manager.setup_main_menu.assert_called_once()
        app_instance.menu_manager.setup_debug_menu.assert_called_once()
        app_instance.menu_manager.setup_help_menu.assert_called_once()

    @pytest.mark.asyncio
    async def test_exit_handler_confirm_exit(self, app_instance):
        """Test exit handler when user confirms exit."""
        # Mock the dialog to return True (user confirms exit)
        app_instance.dialog = AsyncMock(return_value=True)
        app_instance._httpd = MagicMock()

        result = await app_instance.exit_handler(app_instance)

        # Verify dialog was shown
        app_instance.dialog.assert_called_once()

        # Verify server shutdown was called
        app_instance._httpd.shutdown.assert_called_once()

        # Verify function returns True (should exit)
        assert result is True

    @pytest.mark.asyncio
    async def test_exit_handler_cancel_exit(self, app_instance):
        """Test exit handler when user cancels exit."""
        # Mock the dialog to return False (user cancels exit)
        app_instance.dialog = AsyncMock(return_value=False)
        app_instance._httpd = MagicMock()

        result = await app_instance.exit_handler(app_instance)

        # Verify dialog was shown
        app_instance.dialog.assert_called_once()

        # Verify server shutdown was NOT called
        app_instance._httpd.shutdown.assert_not_called()

        # Verify function returns False (should not exit)
        assert result is False

    @pytest.mark.asyncio
    async def test_check_license_no_dialog_shown_high_days(self, app_instance):
        """Test license check when many days remaining (no dialog)."""
        app_instance.license_manager.get_license_info.return_value = {"days_remaining": 30}
        app_instance.dialog_manager.license_info = AsyncMock()

        await app_instance.check_license()

        # Verify license info was retrieved
        app_instance.license_manager.get_license_info.assert_called_once()

        # Verify no dialog was shown (days > 15)
        app_instance.dialog_manager.license_info.assert_not_called()

        # Verify dialog flag is still False
        assert app_instance._license_dialog_shown is False

    @pytest.mark.asyncio
    async def test_check_license_shows_dialog_for_threshold_days(self, app_instance):
        """Test license check shows dialog for threshold days."""
        # Test each threshold day
        threshold_days = [15, 10, 5, 2, 1]

        for days in threshold_days:
            # Reset the dialog flag for each test
            app_instance._license_dialog_shown = False
            app_instance.license_manager.get_license_info.return_value = {"days_remaining": days}
            app_instance.dialog_manager.license_info = AsyncMock()
            app_instance.web_view = MagicMock()
            app_instance.web_view.url = "http://test.url"

            await app_instance.check_license()

            # Verify dialog was shown
            app_instance.dialog_manager.license_info.assert_called_with("http://test.url")

            # Verify dialog flag is set
            assert app_instance._license_dialog_shown is True

    @pytest.mark.asyncio
    async def test_check_license_no_dialog_for_non_threshold_days(self, app_instance):
        """Test license check doesn't show dialog for non-threshold days."""
        # Test days that shouldn't trigger dialog
        non_threshold_days = [14, 9, 4, 3, 0]

        for days in non_threshold_days:
            # Reset the dialog flag for each test
            app_instance._license_dialog_shown = False
            app_instance.license_manager.get_license_info.return_value = {"days_remaining": days}
            app_instance.dialog_manager.license_info = AsyncMock()

            await app_instance.check_license()

            # Verify no dialog was shown for non-threshold days
            app_instance.dialog_manager.license_info.assert_not_called()

            # Verify dialog flag is still False
            assert app_instance._license_dialog_shown is False

    @pytest.mark.asyncio
    async def test_check_license_dialog_already_shown(self, app_instance):
        """Test license check when dialog was already shown."""
        # Reset the license manager mock to clear previous calls
        app_instance.license_manager.get_license_info.reset_mock()

        app_instance._license_dialog_shown = True
        app_instance.license_manager.get_license_info.return_value = {"days_remaining": 5}
        app_instance.dialog_manager.license_info = AsyncMock()

        await app_instance.check_license()

        # Verify license info was not retrieved (early return)
        app_instance.license_manager.get_license_info.assert_not_called()

        # Verify no dialog was shown
        app_instance.dialog_manager.license_info.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_license_handles_exception(self, app_instance):
        """Test license check handles exceptions gracefully."""
        app_instance.license_manager.get_license_info.side_effect = Exception("Test error")
        app_instance.logger = MagicMock()

        await app_instance.check_license()

        # Verify error was logged
        app_instance.logger.error.assert_called_once()
        assert "Failed to check license status" in app_instance.logger.error.call_args[0][0]

    @pytest.mark.asyncio
    async def test_check_update(self, app_instance):
        """Test check_update method calls dialog manager."""
        app_instance.dialog_manager.check_for_updates = AsyncMock()

        await app_instance.check_update()

        # Verify dialog manager check_for_updates is called with False
        app_instance.dialog_manager.check_for_updates.assert_called_once_with(False)

    def test_command_removal_in_startup(self, app_instance, mock_toga_deps):
        """Test that 'Close All' command is removed during startup."""
        # Create mock commands
        close_all_command = MagicMock()
        close_all_command.group.text = "File"
        close_all_command.text = "Close All"

        other_command = MagicMock()
        other_command.group.text = "File"
        other_command.text = "New"

        # Create a mock commands list with remove method
        mock_commands = [close_all_command, other_command]
        mock_commands_collection = MagicMock()
        mock_commands_collection.__iter__ = lambda x: iter(mock_commands)
        mock_commands_collection.remove = lambda x: mock_commands.remove(x)

        # Mock MainWindow to avoid property setter issues
        mock_main_window = MagicMock()
        mock_toga_deps["toga"].MainWindow.return_value = mock_main_window

        # Use property patch for commands and main_window
        with (
            patch.object(type(app_instance), "commands", new_callable=lambda: mock_commands_collection),
            patch.object(type(app_instance), "main_window", new_callable=lambda: mock_main_window),
        ):
            # Suppress the deprecation warning about no event loop for this test
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                app_instance.startup()

            # Verify 'Close All' command was removed
            assert close_all_command not in mock_commands
            assert other_command in mock_commands
