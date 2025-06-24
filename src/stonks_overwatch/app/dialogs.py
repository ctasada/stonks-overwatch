import os

from asgiref.sync import sync_to_async
from toga.dialogs import ConfirmDialog, ErrorDialog, InfoDialog, SaveFileDialog

from stonks_overwatch.utils.database.db_utils import dump_database


class DialogManager:
    def __init__(self, app):
        self.app = app

    async def download_database(self, widget):
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
            await self.app.main_window.dialog(ErrorDialog("Export Failed", f"Failed to export database: {str(e)}"))

    async def export_database(self, destination_path):
        source_db_path = os.path.join(self.app.paths.data, "db.sqlite3")
        if not os.path.exists(source_db_path):
            raise FileNotFoundError(f"Database not found at {source_db_path}")
        return await sync_to_async(dump_database)(destination_path)

    async def clear_cache(self, widget):
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
