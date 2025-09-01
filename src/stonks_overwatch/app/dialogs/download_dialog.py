import os
import subprocess
import sys
import threading

import toga
from toga.style import Pack

from stonks_overwatch.app.utils.dialog_utils import center_window_on_parent
from stonks_overwatch.services.utilities.google_drive_service import GoogleDriveService
from stonks_overwatch.utils.core.logger import StonksLogger


class DownloadDialog(toga.Window):
    def __init__(self, file_info: GoogleDriveService.FileInfo, main_window: toga.Window | None = None):
        super().__init__(
            title="Downloading Update",
            closable=False,
            minimizable=False,
            resizable=False,
            size=(400, 150),
            position=(100, 100),
        )

        self.logger = StonksLogger.get_logger("stonks_overwatch.app", "[DOWNLOAD_DIALOG]")

        self.file_name = file_info
        self._main_window = main_window

        self.label = toga.Label(f"Downloading: {file_info.name}")
        self.progress = toga.ProgressBar(max=None, value=0)
        self.download_info_label = toga.Label("Preparing download...", style=Pack(text_align="center"))
        self.cancel_button = toga.Button("Cancel", on_press=self.on_cancel)

        # Create a vertical box for label, progress bar, and download info
        content_box = toga.Box(
            children=[self.label, self.progress, self.download_info_label],
            style=Pack(direction="column", padding_bottom=20, align_items="center", flex=1),
        )
        # Place the cancel button in its own box at the bottom
        button_box = toga.Box(
            children=[self.cancel_button], style=Pack(direction="row", align_items="center", margin_top=10)
        )
        # Main box with content and button separated
        box = toga.Box(
            children=[content_box, button_box], style=Pack(direction="column", margin=10, align_items="center")
        )

        self.content = box
        self._closed = False
        self._download_thread = None

    def on_cancel(self, widget):
        self.logger.debug("Starting closing download dialog.")
        self._closed = True
        self.logger.debug("Stopping thread, if needed.")
        # No need to join the thread here; let it exit naturally using the _closed flag
        self.logger.debug("Closing download dialog.")
        self.app.loop.call_soon_threadsafe(self.close)

    def show(self):
        center_window_on_parent(self, self._main_window)
        super().show()
        self.start_download()

    def open_file_browser(self, folder_path: str):
        if sys.platform == "win32":
            subprocess.Popen(["explorer", folder_path])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder_path])
        elif sys.platform.startswith("linux"):
            subprocess.Popen(["xdg-open", folder_path])
        else:
            subprocess.Popen(["open", folder_path])

    def update_progress(
        self,
        percent: float | int,
        folder_path: str = None,
        file_path: str = None,
        downloaded_bytes: int = 0,
        total_bytes: int = 0,
    ):
        def _update():
            percent_int = int(percent)
            if percent_int != self.progress.value:
                if self.progress.max is None:
                    self.progress.max = 100
                self.progress.value = percent_int
                if percent_int % 10 == 0:
                    self.logger.debug(f"Progress: {percent_int}%")
                self.progress.refresh()

                # Update download info label with MB and percentage
                if total_bytes > 0:
                    downloaded_mb = downloaded_bytes / (1024 * 1024)
                    total_mb = total_bytes / (1024 * 1024)
                    self.download_info_label.text = f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB ({percent_int}%)"
                else:
                    # Try to estimate file size from current file if it exists
                    if file_path and os.path.exists(file_path):
                        current_size = os.path.getsize(file_path)
                        current_mb = current_size / (1024 * 1024)
                        self.download_info_label.text = f"{current_mb:.1f} MB ({percent_int}%)"
                    else:
                        self.download_info_label.text = f"Downloaded: {percent_int}%"

                self.download_info_label.refresh()

                if percent_int >= 100:
                    self.logger.debug("Reached 100% progress, showing install confirmation.")
                    if folder_path and file_path:
                        self.show_install_confirmation(file_path, folder_path)
                    else:
                        # Fallback to old behavior if file_path not provided
                        if folder_path:
                            self.open_file_browser(folder_path)
                        self.on_cancel(self.cancel_button)

        self.app.loop.call_soon_threadsafe(_update)

    def start_download(self):
        def get_downloads_folder():
            if sys.platform == "win32":
                from pathlib import Path

                return str(Path.home() / "Downloads")
            elif sys.platform == "darwin" or sys.platform.startswith("linux"):
                return os.path.expanduser("~/Downloads")
            else:
                return os.path.expanduser("~/Downloads")

        downloads_folder = get_downloads_folder()
        output_path = os.path.join(downloads_folder, self.file_name.name)

        def download():
            def progress_callback(percent, downloaded_bytes=0, total_bytes=0):
                if self._closed:
                    self.logger.info("Download cancelled by user.")
                    return
                self.update_progress(percent, downloads_folder, output_path, downloaded_bytes, total_bytes)

            try:
                GoogleDriveService.download_file(
                    self.file_name.id,
                    output_path,
                    progress_callback=progress_callback,
                    should_cancel=lambda: self._closed,
                )
            except Exception as e:
                self.logger.error(f"Download error: {e}")
            finally:
                self._download_thread = None

        self._download_thread = threading.Thread(target=download)
        self._download_thread.start()

    def install_update(self, file_path: str):
        """Execute the installer based on the platform and file type."""
        try:
            if sys.platform == "win32":
                # For Windows installers (.exe, .msi)
                subprocess.Popen([file_path])
            elif sys.platform == "darwin":
                # For macOS, handle different installer types
                if file_path.lower().endswith(".dmg"):
                    # Mount DMG file
                    subprocess.Popen(["open", file_path])
                elif file_path.lower().endswith(".pkg"):
                    # Install PKG file
                    subprocess.Popen(["open", file_path])
                else:
                    # Try to open with default application
                    subprocess.Popen(["open", file_path])
            elif sys.platform.startswith("linux"):
                # For Linux, handle different package types
                if file_path.lower().endswith((".deb", ".rpm", ".AppImage")):
                    if file_path.lower().endswith(".AppImage"):
                        # Make AppImage executable and run it
                        os.chmod(file_path, 0o755)
                        subprocess.Popen([file_path])
                    else:
                        # Open with default application (usually package manager)
                        subprocess.Popen(["xdg-open", file_path])
                else:
                    subprocess.Popen(["xdg-open", file_path])
            else:
                # Fallback for other platforms
                subprocess.Popen(["open", file_path])

            self.logger.info(f"Started installer for: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to start installer: {e}")

    def show_install_confirmation(self, file_path: str, folder_path: str):
        """Show confirmation dialog asking if user wants to install the update now."""

        async def ask_install():
            # Create and show confirmation dialog using toga.ConfirmDialog
            dialog = toga.ConfirmDialog(
                title="Install Update", message="Download completed! Do you want to install the update now?"
            )
            result = await self.app.main_window.dialog(dialog)

            if result:
                self.logger.debug("User chose to install the update.")
                self.install_update(file_path)
            else:
                self.logger.debug("User chose not to install, opening file browser.")
                self.open_file_browser(folder_path)

            # Close the download dialog
            self.on_cancel(self.cancel_button)

        # Schedule the async function to run
        self.app.loop.call_soon_threadsafe(lambda: self.app.loop.create_task(ask_install()))
