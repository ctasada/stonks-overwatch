import os

import toga
from asgiref.sync import sync_to_async
from toga.dialogs import ConfirmDialog, ErrorDialog, InfoDialog, SaveFileDialog

from stonks_overwatch.app.dialogs.download_dialog import DownloadDialog
from stonks_overwatch.app.dialogs.expired_dialog import ExpiredDialog
from stonks_overwatch.app.dialogs.preferences_dialog import PreferencesDialog
from stonks_overwatch.services.utilities.google_drive_service import GoogleDriveService
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.database.db_utils import dump_database


class DialogManager:
    _expired_dialog_instance = None
    _preferences_dialog_instance = None
    _check_for_updates_dialog_instance = None

    def __init__(self, app: toga.App):
        self.app = app
        self.logger = StonksLogger.get_logger("stonks_overwatch.app", "[DIALOG_MANAGER]")

    async def download_database(self):
        try:
            confirmed = await self.app.main_window.dialog(
                ConfirmDialog(
                    "Export Database", "This will export the internal database for debugging purposes. Continue?"
                )
            )
            if not confirmed:
                return
            save_path = await self.app.main_window.dialog(
                SaveFileDialog("Save Database Export", suggested_filename="db_export.zip", file_types=["zip"])
            )
            if save_path:
                await self.export_database(save_path)
                await self.app.main_window.dialog(
                    InfoDialog("Export Complete", f"Database exported successfully to:\n{save_path}")
                )
        except Exception as e:
            self.logger.error(f"Failed to export database: {str(e)}")
            await self.app.main_window.dialog(ErrorDialog("Export Failed", f"Failed to export database: {str(e)}"))

    async def export_database(self, destination_path):
        source_db_path = os.path.join(self.app.paths.data, "db.sqlite3")
        if not os.path.exists(source_db_path):
            raise FileNotFoundError(f"Database not found at {source_db_path}")
        return await sync_to_async(dump_database)(destination_path)

    async def clear_cache(self):
        confirmed = await self.app.main_window.dialog(
            ConfirmDialog("Clear Cache", "This will clear all cached data. Continue?")
        )
        if confirmed:
            cache_dir = self.app.paths.cache
            files = os.listdir(cache_dir)
            for file in files:
                os.remove(os.path.join(cache_dir, file))
            await self.app.main_window.dialog(
                InfoDialog("Cache Cleared", "Application cache has been cleared successfully.")
            )

    async def license_info(self, base_url: str):
        """Show the license information dialog."""
        try:
            if DialogManager._expired_dialog_instance is not None:
                self.logger.debug("ExpiredDialog already open, focusing window.")
                DialogManager._expired_dialog_instance.show()
                return

            dialog = ExpiredDialog("License Information", base_url, main_window=self.app.main_window)
            DialogManager._expired_dialog_instance = dialog

            def on_close(widget):
                self.logger.debug("ExpiredDialog close handler called")
                DialogManager._expired_dialog_instance = None
                dialog.close()

            dialog.on_close = on_close
            dialog.show()

        except Exception as e:
            self.logger.error(f"Failed to retrieve license info: {str(e)}")
            await self.app.main_window.dialog(ErrorDialog("License", f"Failed to retrieve license info: {str(e)}"))

    async def preferences(self):
        # If a dialog is open and not closed, focus it
        if DialogManager._preferences_dialog_instance is not None:
            if not getattr(DialogManager._preferences_dialog_instance, "_closed", False):
                self.logger.debug("PreferencesDialog already open, focusing window.")
                DialogManager._preferences_dialog_instance.show()
                return
            else:
                # Previous instance is closed, reset
                DialogManager._preferences_dialog_instance = None

        dialog = PreferencesDialog(title="Preferences", app=self.app)
        await dialog.async_init()  # Initialize the dialog asynchronously
        dialog._closed = False  # Track closed state
        DialogManager._preferences_dialog_instance = dialog

        def on_close(widget):
            self.logger.debug("PreferencesDialog close handler called")
            dialog._closed = True
            DialogManager._preferences_dialog_instance = None
            dialog.close()

        dialog.on_close = on_close
        dialog.show()

    async def check_for_updates(self, show_no_updates: bool = True):
        # If a dialog is open and not closed, focus it
        if DialogManager._check_for_updates_dialog_instance is not None:
            if not getattr(DialogManager._check_for_updates_dialog_instance, "_closed", False):
                return
            else:
                # Previous instance is closed, reset
                DialogManager._check_for_updates_dialog_instance = None

        is_update_available = False
        newest_version_file = None

        # Get list of available updates
        update_files = GoogleDriveService.list_files()
        if update_files:
            platform = GoogleDriveService.get_platform_for_os()
            newest_version_file = GoogleDriveService.get_latest_for_platform(update_files, platform)
            is_update_available = GoogleDriveService.is_file_newer_than_version(newest_version_file, self.app.version)

        if is_update_available:
            confirmed = await self.app.main_window.dialog(
                ConfirmDialog(
                    "Update Available",
                    f"Update to version {newest_version_file.version} available. Do you want to download it?",
                )
            )
            if not confirmed:
                return

            dialog = DownloadDialog(newest_version_file, main_window=self.app.main_window)
            dialog._closed = False
            DialogManager._check_for_updates_dialog_instance = dialog

            def on_close(widget):
                self.logger.debug("DownloadDialog close handler called")
                dialog._closed = True
                DialogManager._check_for_updates_dialog_instance = None
                dialog.close()

            dialog.on_close = on_close
            dialog.show()
        elif show_no_updates:
            dialog = InfoDialog(
                "You're up-to-date!",
                f"Stonks Overwatch {self.app.version} is currently at the newest version available.",
            )
            DialogManager._check_for_updates_dialog_instance = dialog

            await self.app.main_window.dialog(dialog)

            DialogManager._check_for_updates_dialog_instance = None
