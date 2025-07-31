import os
import webbrowser
from datetime import datetime

from toga.command import Command, Group

from stonks_overwatch.app.logs_window import LogStreamWindow
from stonks_overwatch.services.utilities.license_manager import LicenseManager


class MenuManager:
    def __init__(self, app):
        self.app = app
        # Track the log viewer window
        self.log_window = None
        self.license_manager = LicenseManager()

    def setup_preferences_menu(self):
        preferences_cmd = Command.standard(
            self.app,
            Command.PREFERENCES,
            action=self._preferences_dialog,
        )

        # Add commands to the app
        self.app.commands.add(preferences_cmd)

    def setup_debug_menu(self):
        tools_group = Group.COMMANDS
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
        license_cmd = Command(
            self._open_license_info,
            text=self.__license_label(),
            tooltip="License information",
            enabled=not self.license_manager.is_license_expired(),
            group=Group.HELP,
            section=1,
        )
        self.app.commands.add(bug_report_cmd)
        self.app.commands.add(license_cmd)

    def __license_label(self) -> str:
        """Generate the license expiration label."""
        from stonks_overwatch.build_config import EXPIRATION_DATE

        expiration = datetime.fromisoformat(EXPIRATION_DATE)
        now = datetime.now(expiration.tzinfo)
        delta = expiration - now
        if delta.days < 0:
            return "License Expired"
        elif delta.days == 0:
            return "License Expires Today"
        elif delta.days == 1:
            return "License Expires Tomorrow"
        elif delta.days < 30:
            return f"License Expires in {delta.days} days"
        else:
            return f"License Expires: {expiration.strftime('%Y-%m-%d')}"

    def open_bug_report(self, widget):
        from stonks_overwatch.settings import STONKS_OVERWATCH_SUPPORT_URL

        webbrowser.open_new_tab(STONKS_OVERWATCH_SUPPORT_URL)

    async def _preferences_dialog(self, widget):
        await self.app.dialog_manager.preferences(widget)

    async def _open_license_info(self, widget):
        await self.app.dialog_manager.license_info(widget)

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
