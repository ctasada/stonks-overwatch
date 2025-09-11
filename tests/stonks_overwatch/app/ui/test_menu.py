"""
Tests for the MenuManager class.

This module tests the menu management functionality of the Toga app,
including main menu, debug menu, and help menu setup and interactions.
"""

import os
from datetime import datetime, timezone

from ..toga_test_utils import conditional_import, skip_if_toga_unavailable

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Skip all tests in this module if toga is not available
pytestmark = skip_if_toga_unavailable

# Conditionally import MenuManager only if toga is available
MenuManager = conditional_import("MenuManager", "stonks_overwatch.app.ui.menu")


class TestMenuManager:
    """Test cases for the MenuManager class."""

    @pytest.fixture
    def mock_app(self):
        """Create a mock Toga app."""
        app = MagicMock()
        app.commands = MagicMock()
        app.windows = MagicMock()
        app.dialog_manager = MagicMock()
        # Mock web_view.url to return a valid URL string for license info tests
        app.web_view.url = "https://example.com/app"
        return app

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        with (
            patch("stonks_overwatch.app.ui.menu.LicenseManager") as mock_license,
            patch("stonks_overwatch.app.ui.menu.LogStreamWindow") as mock_log,
            patch("stonks_overwatch.app.ui.menu.webbrowser") as mock_browser,
            patch("stonks_overwatch.app.ui.menu.Command") as mock_command,
            patch("stonks_overwatch.app.ui.menu.Group") as mock_group,
        ):
            # Configure Group mock
            mock_group.APP = "APP"
            mock_group.COMMANDS = "COMMANDS"
            mock_group.HELP = "HELP"

            # Configure Command mock
            mock_command.PREFERENCES = "PREFERENCES"
            mock_command.standard = MagicMock()

            yield {
                "LicenseManager": mock_license,
                "LogStreamWindow": mock_log,
                "webbrowser": mock_browser,
                "Command": mock_command,
                "Group": mock_group,
            }

    @pytest.fixture
    def menu_manager(self, mock_app, mock_dependencies):
        """Create a MenuManager instance with mocked dependencies."""
        return MenuManager(mock_app)

    def test_initialization(self, mock_app, mock_dependencies):
        """Test MenuManager initialization."""
        manager = MenuManager(mock_app)

        assert manager.app == mock_app
        assert manager.log_window is None
        mock_dependencies["LicenseManager"].assert_called_once()

    def test_setup_main_menu(self, menu_manager, mock_dependencies):
        """Test main menu setup creates correct commands."""
        menu_manager.setup_main_menu()

        # Verify Command creation for check updates
        mock_dependencies["Command"].assert_called()

        # Verify Command.standard creation for preferences
        mock_dependencies["Command"].standard.assert_called_with(
            menu_manager.app,
            "PREFERENCES",
            action=menu_manager._preferences_dialog,
        )

        # Verify commands were added to app
        #  There should be 3 commands: Check for Updates, Release Notes, Preferences
        assert menu_manager.app.commands.add.call_count == 3

    def test_setup_debug_menu(self, menu_manager, mock_dependencies):
        """Test debug menu setup creates correct commands."""
        menu_manager.setup_debug_menu()

        # Verify Command was called multiple times for debug commands
        assert mock_dependencies["Command"].call_count >= 3

        # Verify commands were added to app
        assert menu_manager.app.commands.add.call_count == 3

    def test_setup_help_menu(self, menu_manager, mock_dependencies):
        """Test help menu setup creates correct commands."""
        # Mock license manager to return not expired
        menu_manager.license_manager.is_license_expired.return_value = False

        with patch.object(menu_manager, "_MenuManager__license_label", return_value="Test License"):
            menu_manager.setup_help_menu()

        # Verify commands were added to app
        assert menu_manager.app.commands.add.call_count == 2

    def test_license_label_expired(self, menu_manager):
        """Test license label when license is expired."""
        expired_date = "2020-01-01T00:00:00+00:00"

        with patch("stonks_overwatch.build_config.EXPIRATION_DATE", expired_date):
            result = menu_manager._MenuManager__license_label()

        assert result == "License Expired"

    def test_license_label_expires_today(self, menu_manager):
        """Test license label when license expires today."""
        # Use a specific time that will definitely be "today"
        from datetime import timedelta

        # Add a few seconds to ensure we're definitely in "today" range
        today = (datetime.now(timezone.utc) + timedelta(seconds=5)).isoformat()

        with patch("stonks_overwatch.build_config.EXPIRATION_DATE", today):
            result = menu_manager._MenuManager__license_label()

        assert result == "License Expires Today"

    def test_license_label_expires_tomorrow(self, menu_manager):
        """Test license label when license expires tomorrow."""
        from datetime import timedelta

        # Add one day and a few seconds to ensure we're definitely in "tomorrow" range
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1, seconds=5)).isoformat()

        with patch("stonks_overwatch.build_config.EXPIRATION_DATE", tomorrow):
            result = menu_manager._MenuManager__license_label()

        assert result == "License Expires Tomorrow"

    def test_license_label_expires_in_days(self, menu_manager):
        """Test license label when license expires in a few days."""
        from datetime import timedelta

        # Add 5 days and a few seconds to ensure we're definitely in the 5-day range
        future_date = (datetime.now(timezone.utc) + timedelta(days=5, seconds=5)).isoformat()

        with patch("stonks_overwatch.build_config.EXPIRATION_DATE", future_date):
            result = menu_manager._MenuManager__license_label()

        assert result == "License Expires in 5 days"

    def test_license_label_expires_in_months(self, menu_manager):
        """Test license label when license expires in more than 30 days."""
        from datetime import timedelta

        future_date = (datetime.now(timezone.utc) + timedelta(days=60)).isoformat()

        with patch("stonks_overwatch.build_config.EXPIRATION_DATE", future_date):
            result = menu_manager._MenuManager__license_label()

        # Should show formatted date
        expected_date = (datetime.now(timezone.utc) + timedelta(days=60)).strftime("%Y-%m-%d")
        assert result == f"License Expires: {expected_date}"

    def test_open_bug_report(self, menu_manager, mock_dependencies):
        """Test opening bug report URL."""
        support_url = "https://test.com/support"

        with patch("stonks_overwatch.settings.STONKS_OVERWATCH_SUPPORT_URL", support_url):
            menu_manager.open_bug_report(None)

        mock_dependencies["webbrowser"].open_new_tab.assert_called_once_with(support_url)

    @pytest.mark.asyncio
    async def test_preferences_dialog(self, menu_manager):
        """Test preferences dialog method."""
        menu_manager.app.dialog_manager.preferences = AsyncMock()

        await menu_manager._preferences_dialog(None)

        menu_manager.app.dialog_manager.preferences.assert_called_once()

    @pytest.mark.asyncio
    async def test_open_license_info(self, menu_manager):
        """Test open license info method."""
        menu_manager.app.dialog_manager.license_info = AsyncMock()

        await menu_manager._open_license_info(None)

        menu_manager.app.dialog_manager.license_info.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_database(self, menu_manager):
        """Test download database method."""
        menu_manager.app.dialog_manager.download_database = AsyncMock()

        await menu_manager._download_database(None)

        menu_manager.app.dialog_manager.download_database.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_cache(self, menu_manager):
        """Test clear cache method."""
        menu_manager.app.dialog_manager.clear_cache = AsyncMock()

        await menu_manager._clear_cache(None)

        menu_manager.app.dialog_manager.clear_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_for_updates(self, menu_manager):
        """Test check for updates method."""
        menu_manager.app.dialog_manager.check_for_updates = AsyncMock()

        await menu_manager._check_for_updates(None)

        menu_manager.app.dialog_manager.check_for_updates.assert_called_once()

    def test_show_logs_creates_new_window(self, menu_manager, mock_dependencies):
        """Test show logs creates new window when none exists."""
        logs_dir = "/test/logs"
        logs_filename = "test.log"

        with (
            patch("stonks_overwatch.settings.STONKS_OVERWATCH_LOGS_DIR", logs_dir),
            patch("stonks_overwatch.settings.STONKS_OVERWATCH_LOGS_FILENAME", logs_filename),
        ):
            menu_manager._show_logs(None)
            # Reset the call count after construction to only count the explicit call
            menu_manager.log_window.show.reset_mock()
            menu_manager._show_logs(None)

        # Verify LogStreamWindow was created
        expected_path = os.path.join(logs_dir, logs_filename)
        mock_dependencies["LogStreamWindow"].assert_called_with("Live Logs", expected_path)

        # Verify window was added to app
        menu_manager.app.windows.add.assert_called()

        # Verify window was shown only once per explicit call
        assert menu_manager.log_window.show.call_count == 1

    def test_show_logs_reuses_existing_window(self, menu_manager, mock_dependencies):
        """Test show logs reuses existing window."""
        # Set up existing log window
        existing_window = MagicMock()
        menu_manager.log_window = existing_window

        menu_manager._show_logs(None)

        # Verify LogStreamWindow was NOT created again
        mock_dependencies["LogStreamWindow"].assert_not_called()

        # Verify window was NOT added to app again
        menu_manager.app.windows.add.assert_not_called()

        # Verify existing window was shown
        existing_window.show.assert_called_once()

    def test_help_menu_license_command_disabled_when_expired(self, menu_manager, mock_dependencies):
        """Test help menu license command is disabled when license is expired."""
        # Mock license manager to return expired
        menu_manager.license_manager.is_license_expired.return_value = True

        with patch.object(menu_manager, "_MenuManager__license_label", return_value="License Expired"):
            menu_manager.setup_help_menu()

        # Verify commands were created with enabled=False for license command
        # Check that Command was called with enabled=False
        call_args_list = mock_dependencies["Command"].call_args_list

        # Find the license command call (should have enabled=False)
        license_command_found = False
        for call_args in call_args_list:
            # Get both positional and keyword arguments
            args, kwargs = call_args
            # Check if this is the license command by looking for the license-related text
            # The text might be a MagicMock, so check for license info callback
            if "license_info" in str(args[0]) and kwargs.get("enabled") is False:
                license_command_found = True
                break

        assert license_command_found, f"License command with enabled=False not found. Calls: {call_args_list}"

    def test_help_menu_license_command_enabled_when_not_expired(self, menu_manager, mock_dependencies):
        """Test help menu license command is enabled when license is not expired."""
        # Mock license manager to return not expired
        menu_manager.license_manager.is_license_expired.return_value = False

        with patch.object(menu_manager, "_MenuManager__license_label", return_value="License Active"):
            menu_manager.setup_help_menu()

        # Find the license command call (should have enabled=True)
        call_args_list = mock_dependencies["Command"].call_args_list
        license_command_found = False
        for call_args in call_args_list:
            # Get both positional and keyword arguments
            args, kwargs = call_args
            # Check if this is the license command by looking for the license-related text
            # The text might be a MagicMock, so check for license info callback
            if "license_info" in str(args[0]) and kwargs.get("enabled") is True:
                license_command_found = True
                break

        assert license_command_found, f"License command with enabled=True not found. Calls: {call_args_list}"

    def test_menu_commands_have_correct_groups_and_sections(self, menu_manager, mock_dependencies):
        """Test that menu commands are created with correct groups and sections."""
        # Setup main menu
        menu_manager.setup_main_menu()

        # Check that commands were created with APP group
        main_menu_calls = mock_dependencies["Command"].call_args_list
        assert any(call[1].get("group") == "APP" for call in main_menu_calls)

        # Reset mock
        mock_dependencies["Command"].reset_mock()

        # Setup debug menu
        menu_manager.setup_debug_menu()

        # Check that commands were created with COMMANDS group
        debug_menu_calls = mock_dependencies["Command"].call_args_list
        assert any(call[1].get("group") == "COMMANDS" for call in debug_menu_calls)

        # Reset mock
        mock_dependencies["Command"].reset_mock()

        # Setup help menu
        menu_manager.license_manager.is_license_expired.return_value = False
        with patch.object(menu_manager, "_MenuManager__license_label", return_value="Test License"):
            menu_manager.setup_help_menu()

        # Check that commands were created with HELP group
        help_menu_calls = mock_dependencies["Command"].call_args_list
        assert any(call[1].get("group") == "HELP" for call in help_menu_calls)
