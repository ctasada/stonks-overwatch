import os
import webbrowser

from toga.command import Command, Group

from stonks_overwatch.app.logs_window import LogStreamWindow


class MenuManager:
    def __init__(self, app):
        self.app = app
        # Track the log viewer window
        self.log_window = None

    def setup_debug_menu(self):
        tools_group = Group("Tools")
        download_db_cmd = Command(
            self._download_database,
            text="Export Internal Database...",
            tooltip="Download the internal database for debugging",
            group=tools_group,
            section=0,
        )
        clear_cache_cmd = Command(
            self._clear_cache,
            text="Clear Cache",
            tooltip="Clear application cache",
            group=tools_group,
            section=1,
        )
        show_logs_cmd = Command(
            self._show_logs,
            text="Show Logs",
            tooltip="View application logs",
            group=tools_group,
            section=1,  # Different section will be separated by divider
        )

        # Add commands to the app
        self.app.commands.add(download_db_cmd)
        self.app.commands.add(clear_cache_cmd)
        self.app.commands.add(show_logs_cmd)

    def setup_help_menu(self):
        bug_report_cmd = Command(
            self.open_bug_report,
            text="Bug Report / Feedback",
            tooltip="Report a bug or send feedback",
            group=Group.HELP,
            section=0,
        )
        self.app.commands.add(bug_report_cmd)

    def open_bug_report(self, widget):
        webbrowser.open_new_tab("https://forms.gle/djPWAtLSFfRYbDwV7")

    async def _download_database(self, widget):
        await self.app.dialog_manager.download_database(widget)

    async def _clear_cache(self, widget):
        await self.app.dialog_manager.clear_cache(widget)

    def _get_log_file_path(self):
        """Get the path to the log file."""
        from stonks_overwatch.settings import STONKS_OVERWATCH_LOGS_DIR, STONKS_OVERWATCH_LOGS_FILENAME

        return os.path.join(STONKS_OVERWATCH_LOGS_DIR, STONKS_OVERWATCH_LOGS_FILENAME)

    def _show_logs(self, widget):
        # If the log window does not exist, create it
        if self.log_window is None:
            log_path = self._get_log_file_path()
            self.log_window = LogStreamWindow("Live Logs", log_path)
            self.app.windows.add(self.log_window)

        self.log_window.show()
