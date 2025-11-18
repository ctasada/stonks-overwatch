"""
Tests for the DialogManager class.

This module tests the dialog management functionality of the Toga app,
including database export, cache clearing, license info, preferences, and update checking.
"""

from ..toga_test_utils import conditional_import, skip_if_toga_unavailable

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Skip all tests in this module if toga is not available
pytestmark = skip_if_toga_unavailable

# Conditionally import DialogManager only if toga is available
DialogManager = conditional_import("DialogManager", "stonks_overwatch.app.dialogs.dialogs")


class TestDialogManager:
    """Test cases for the DialogManager class."""

    @pytest.fixture
    def mock_app(self):
        """Create a mock Toga app."""
        app = MagicMock()
        app.main_window = MagicMock()
        # Create a fresh AsyncMock for each test to ensure isolation
        app.main_window.dialog = AsyncMock()
        app.main_window.dialog.reset_mock()  # Ensure clean state
        app.paths = MagicMock()
        app.paths.data = "/test/data"
        app.paths.cache = "/test/cache"
        app.version = "1.0.0"
        return app

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        with (
            patch("stonks_overwatch.app.dialogs.dialogs.StonksLogger") as mock_logger,
            patch("stonks_overwatch.app.dialogs.dialogs.ConfirmDialog") as mock_confirm,
            patch("stonks_overwatch.app.dialogs.dialogs.ErrorDialog") as mock_error,
            patch("stonks_overwatch.app.dialogs.dialogs.InfoDialog") as mock_info,
            patch("stonks_overwatch.app.dialogs.dialogs.SaveFileDialog") as mock_save,
            patch("stonks_overwatch.app.dialogs.dialogs.PreferencesDialog") as mock_prefs,
            patch("stonks_overwatch.app.dialogs.dialogs.DownloadDialog") as mock_download,
            patch("stonks_overwatch.app.dialogs.dialogs.GoogleDriveService") as mock_drive,
            patch("stonks_overwatch.app.dialogs.dialogs.sync_to_async") as mock_sync,  # Use Mock, not AsyncMock
            patch("stonks_overwatch.app.dialogs.dialogs.dump_database") as mock_dump,
        ):
            mock_logger.get_logger.return_value = MagicMock()

            yield {
                "StonksLogger": mock_logger,
                "ConfirmDialog": mock_confirm,
                "ErrorDialog": mock_error,
                "InfoDialog": mock_info,
                "SaveFileDialog": mock_save,
                "PreferencesDialog": mock_prefs,
                "DownloadDialog": mock_download,
                "GoogleDriveService": mock_drive,
                "sync_to_async": mock_sync,
                "dump_database": mock_dump,
            }

    @pytest.fixture
    def dialog_manager(self, mock_app, mock_dependencies):
        """Create a DialogManager instance with mocked dependencies."""
        mock_dependencies["StonksLogger"].get_logger.return_value = MagicMock()
        return DialogManager(mock_app)

    def test_initialization(self, mock_app, mock_dependencies):
        """Test DialogManager initialization."""
        manager = DialogManager(mock_app)

        assert manager.app == mock_app
        mock_dependencies["StonksLogger"].get_logger.assert_called_with("stonks_overwatch.app", "[DIALOG_MANAGER]")

    @pytest.mark.asyncio
    async def test_download_database_success(self, dialog_manager, mock_dependencies):
        """Test successful database download flow."""
        # Mock dialog responses
        dialog_manager.app.main_window.dialog.side_effect = [
            True,  # Confirm dialog
            "/path/to/save.zip",  # Save file dialog
            None,  # Info dialog (success)
        ]

        # Mock export_database
        dialog_manager.export_database = AsyncMock()

        await dialog_manager.download_database()

        # Verify dialogs were shown
        assert dialog_manager.app.main_window.dialog.call_count == 3

        # Verify export was called
        dialog_manager.export_database.assert_called_once_with("/path/to/save.zip")

    @pytest.mark.asyncio
    async def test_download_database_user_cancels_confirm(self, dialog_manager):
        """Test database download when user cancels confirmation."""
        # Mock dialog to return False (user cancels)
        dialog_manager.app.main_window.dialog.return_value = False

        # Mock export_database to ensure it's not called
        dialog_manager.export_database = AsyncMock()

        await dialog_manager.download_database()

        # Verify only confirmation dialog was shown
        dialog_manager.app.main_window.dialog.assert_called_once()

        # Verify export was not called
        dialog_manager.export_database.assert_not_called()

    @pytest.mark.asyncio
    async def test_download_database_user_cancels_save(self, dialog_manager):
        """Test database download when user cancels save dialog."""
        # Mock dialog responses
        dialog_manager.app.main_window.dialog.side_effect = [
            True,  # Confirm dialog
            None,  # Save file dialog (user cancels)
        ]

        # Mock export_database to ensure it's not called
        dialog_manager.export_database = AsyncMock()

        await dialog_manager.download_database()

        # Verify both dialogs were shown
        assert dialog_manager.app.main_window.dialog.call_count == 2

        # Verify export was not called
        dialog_manager.export_database.assert_not_called()

    @pytest.mark.asyncio
    async def test_download_database_exception(self, dialog_manager, mock_dependencies):
        """Test database download with exception handling."""
        # Mock dialog responses
        dialog_manager.app.main_window.dialog.side_effect = [
            True,  # Confirm dialog
            "/path/to/save.zip",  # Save file dialog
            None,  # Error dialog
        ]

        # Mock export_database to raise exception
        dialog_manager.export_database = AsyncMock(side_effect=Exception("Test error"))

        await dialog_manager.download_database()

        # Verify error was logged
        dialog_manager.logger.error.assert_called_once()

        # Verify error dialog was shown
        mock_dependencies["ErrorDialog"].assert_called_with("Export Failed", "Failed to export database: Test error")

    @pytest.mark.asyncio
    async def test_export_database_success(self, dialog_manager, mock_dependencies):
        """Test successful database export."""
        destination_path = "/path/to/save.zip"

        # Properly mock sync_to_async to return a callable async function
        async def fake_async_callable(*args, **kwargs):
            return None

        def fake_sync_to_async(fn):
            return fake_async_callable

        mock_dependencies["sync_to_async"].side_effect = fake_sync_to_async

        # Mock database file exists
        with patch("stonks_overwatch.app.dialogs.dialogs.os.path.exists", return_value=True):
            await dialog_manager.export_database(destination_path)

        # Verify sync_to_async was called with dump_database
        mock_dependencies["sync_to_async"].assert_called_once_with(mock_dependencies["dump_database"])

    @pytest.mark.asyncio
    async def test_clear_cache_cancelled(self, dialog_manager):
        """Test cache clearing when user cancels."""
        # Mock confirmation dialog to return False
        dialog_manager.app.main_window.dialog.return_value = False

        with (
            patch("stonks_overwatch.app.dialogs.dialogs.os.listdir") as mock_listdir,
            patch("stonks_overwatch.app.dialogs.dialogs.os.remove") as mock_remove,
        ):
            await dialog_manager.clear_cache()

        # Verify no files were processed
        mock_listdir.assert_not_called()
        mock_remove.assert_not_called()

        # Verify only confirmation dialog was shown
        dialog_manager.app.main_window.dialog.assert_called_once()

    @pytest.mark.asyncio
    async def test_preferences_new_dialog(self, dialog_manager, mock_dependencies):
        """Test preferences dialog creation when no dialog exists."""
        # Ensure no existing dialog
        DialogManager._preferences_dialog_instance = None

        # Mock PreferencesDialog
        mock_dialog = MagicMock()
        mock_dialog.async_init = AsyncMock()
        mock_dependencies["PreferencesDialog"].return_value = mock_dialog

        await dialog_manager.preferences()

        # Verify PreferencesDialog was created
        mock_dependencies["PreferencesDialog"].assert_called_once_with(title="Preferences", app=dialog_manager.app)

        # Verify async_init was called
        mock_dialog.async_init.assert_called_once()

        # Verify dialog was shown
        mock_dialog.show.assert_called_once()

    @pytest.mark.asyncio
    async def test_preferences_existing_dialog_open(self, dialog_manager):
        """Test preferences when dialog already exists and is open."""
        # Mock existing dialog that's not closed
        existing_dialog = MagicMock()
        existing_dialog._closed = False
        DialogManager._preferences_dialog_instance = existing_dialog

        await dialog_manager.preferences()

        # Verify existing dialog was shown
        existing_dialog.show.assert_called_once()

    @pytest.mark.asyncio
    async def test_preferences_existing_dialog_closed(self, dialog_manager, mock_dependencies):
        """Test preferences when existing dialog is closed."""
        # Mock existing dialog that's closed
        existing_dialog = MagicMock()
        existing_dialog._closed = True
        DialogManager._preferences_dialog_instance = existing_dialog

        # Mock new dialog
        mock_dialog = MagicMock()
        mock_dialog.async_init = AsyncMock()
        mock_dependencies["PreferencesDialog"].return_value = mock_dialog

        await dialog_manager.preferences()

        # Verify new dialog was created
        mock_dependencies["PreferencesDialog"].assert_called_once()

    @pytest.mark.asyncio
    async def test_check_for_updates_update_available_confirmed(self, dialog_manager, mock_dependencies):
        """Test check for updates when update is available and user confirms."""
        # Mock GoogleDriveService responses
        mock_file = MagicMock()
        mock_file.version = "2.0.0"

        mock_dependencies["GoogleDriveService"].list_files.return_value = [mock_file]
        mock_dependencies["GoogleDriveService"].get_platform_for_os.return_value = "test_platform"
        mock_dependencies["GoogleDriveService"].get_latest_for_platform.return_value = mock_file
        mock_dependencies["GoogleDriveService"].is_file_newer_than_version.return_value = True

        # Mock confirmation dialog to return True
        dialog_manager.app.main_window.dialog.return_value = True

        # Mock DownloadDialog
        mock_download_dialog = MagicMock()
        mock_dependencies["DownloadDialog"].return_value = mock_download_dialog

        await dialog_manager.check_for_updates()

        # Verify DownloadDialog was created and shown
        mock_dependencies["DownloadDialog"].assert_called_once_with(
            mock_file, main_window=dialog_manager.app.main_window
        )
        mock_download_dialog.show.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_for_updates_update_available_declined(self, dialog_manager, mock_dependencies):
        """Test check for updates when update is available but user declines."""
        # Mock GoogleDriveService responses
        mock_file = MagicMock()
        mock_file.version = "2.0.0"

        mock_dependencies["GoogleDriveService"].list_files.return_value = [mock_file]
        mock_dependencies["GoogleDriveService"].get_platform_for_os.return_value = "test_platform"
        mock_dependencies["GoogleDriveService"].get_latest_for_platform.return_value = mock_file
        mock_dependencies["GoogleDriveService"].is_file_newer_than_version.return_value = True

        # Mock confirmation dialog to return False
        dialog_manager.app.main_window.dialog.return_value = False

        await dialog_manager.check_for_updates()

        # Verify DownloadDialog was not created
        mock_dependencies["DownloadDialog"].assert_not_called()

    @pytest.mark.asyncio
    async def test_check_for_updates_no_update_available_show_message(self, dialog_manager, mock_dependencies):
        """Test check for updates when no update is available and should show message."""
        # Ensure no existing dialog
        DialogManager._check_for_updates_dialog_instance = None

        # Mock GoogleDriveService responses for no update
        mock_dependencies["GoogleDriveService"].list_files.return_value = []

        await dialog_manager.check_for_updates(show_no_updates=True)

        # Verify info dialog was created and shown
        dialog_manager.app.main_window.dialog.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_for_updates_no_update_available_no_message(self, dialog_manager, mock_dependencies):
        """Test check for updates when no update is available and should not show message."""
        # Mock GoogleDriveService responses for no update
        mock_dependencies["GoogleDriveService"].list_files.return_value = []

        await dialog_manager.check_for_updates(show_no_updates=False)

        # Verify no dialogs were shown
        mock_dependencies["InfoDialog"].assert_not_called()
        dialog_manager.app.main_window.dialog.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_for_updates_existing_dialog_open(self, dialog_manager, mock_dependencies):
        """Test check for updates when update dialog already exists and is open."""
        # Mock existing dialog that's not closed
        existing_dialog = MagicMock()
        existing_dialog._closed = False
        DialogManager._check_for_updates_dialog_instance = existing_dialog

        await dialog_manager.check_for_updates()

        # Verify GoogleDriveService was not called (early return)
        mock_dependencies["GoogleDriveService"].list_files.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_for_updates_existing_dialog_closed(self, dialog_manager, mock_dependencies):
        """Test check for updates when existing dialog is closed."""
        # Mock existing dialog that's closed
        existing_dialog = MagicMock()
        existing_dialog._closed = True
        DialogManager._check_for_updates_dialog_instance = existing_dialog

        # Mock GoogleDriveService responses for no update
        mock_dependencies["GoogleDriveService"].list_files.return_value = []

        await dialog_manager.check_for_updates(show_no_updates=False)

        # Verify GoogleDriveService was called (dialog was reset)
        mock_dependencies["GoogleDriveService"].list_files.assert_called_once()

    @pytest.mark.asyncio
    async def test_all_dialog_instances_are_class_variables(self, dialog_manager):
        """Test that dialog instances are stored as class variables for singleton behavior."""
        # Reset all dialog instances
        DialogManager._expired_dialog_instance = None
        DialogManager._preferences_dialog_instance = None
        DialogManager._check_for_updates_dialog_instance = None

        # Verify all dialog instance variables exist as class variables
        assert hasattr(DialogManager, "_expired_dialog_instance")
        assert hasattr(DialogManager, "_preferences_dialog_instance")
        assert hasattr(DialogManager, "_check_for_updates_dialog_instance")

        # Verify they start as None
        assert DialogManager._expired_dialog_instance is None
        assert DialogManager._preferences_dialog_instance is None
        assert DialogManager._check_for_updates_dialog_instance is None
