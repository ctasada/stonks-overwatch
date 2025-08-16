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
        self.progress = toga.ProgressBar(max=100, value=0)
        self.cancel_button = toga.Button("Cancel", on_press=self.on_cancel)

        # Create a vertical box for label and progress bar
        content_box = toga.Box(
            children=[self.label, self.progress],
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

    def update_progress(self, percent: float | int, folder_path: str = None):
        def _update():
            percent_int = int(percent)
            if percent_int != self.progress.value:
                self.progress.value = percent_int
                if percent_int % 10 == 0:
                    self.logger.debug(f"Progress: {percent_int}%")
                self.progress.refresh()
                if percent_int >= 100:
                    self.logger.debug("Reached 100% progress, closing dialog.")
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
            def progress_callback(percent):
                if self._closed:
                    self.logger.info("Download cancelled by user.")
                    return
                self.update_progress(percent, downloads_folder)

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
