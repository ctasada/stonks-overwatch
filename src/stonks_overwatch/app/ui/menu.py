import os
import platform
import webbrowser
from urllib.parse import urlparse

from toga.command import Command, Group

from stonks_overwatch.app.ui.logs_window import LogStreamWindow


class MenuManager:
    def __init__(self, app):
        self.app = app
        # Track the log viewer window
        self.log_window = None

    def setup_main_menu(self):
        app_group = Group.APP

        if platform.system() == "Darwin":
            # On macOS, the "Check for Updates" command is added to the app menu,
            #    but other OSes will have it in the Help menu
            check_update_cmd = Command(
                self._check_for_updates,
                text="Check for Updates...",
                group=app_group,
                section=0,
                order=1,
            )
            self.app.commands.add(check_update_cmd)

            release_notes_info_cmd = Command(
                self._release_notes_info,
                text="Release Notes",
                tooltip="View the latest release notes",
                group=app_group,
                section=0,
            )
            self.app.commands.add(release_notes_info_cmd)

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
        help_group = Group.HELP

        bug_report_cmd = Command(
            self.open_bug_report,
            text="Bug Report / Feedback",
            tooltip="Report a bug or send feedback",
            group=help_group,
            section=0,
        )
        self.app.commands.add(bug_report_cmd)

        if platform.system() != "Darwin":
            # On non-macOS systems, the "Check for Updates" command is added to the Help menu
            check_update_cmd = Command(
                self._check_for_updates,
                text="Check for Updates...",
                group=help_group,
                section=1,
            )
            self.app.commands.add(check_update_cmd)

            release_notes_info_cmd = Command(
                self._release_notes_info,
                text="Release Notes",
                tooltip="View the latest release notes",
                group=help_group,
                section=1,
            )
            self.app.commands.add(release_notes_info_cmd)

    def open_bug_report(self, widget):
        from stonks_overwatch.settings import STONKS_OVERWATCH_SUPPORT_URL

        webbrowser.open_new_tab(STONKS_OVERWATCH_SUPPORT_URL)

    async def _preferences_dialog(self, widget):
        await self.app.dialog_manager.preferences()

    async def _download_database(self, widget):
        await self.app.dialog_manager.download_database()

    async def _clear_cache(self, widget):
        await self.app.dialog_manager.clear_cache()

    async def _check_for_updates(self, widget):
        await self.app.dialog_manager.check_for_updates()

    async def _release_notes_info(self, widget):
        parsed_url = urlparse(self.app.web_view.url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        await self.app.dialog_manager.release_notes(base_url)

    def _show_logs(self, widget):
        # If the log window does not exist, create it
        if self.log_window is None:
            from stonks_overwatch.settings import STONKS_OVERWATCH_LOGS_DIR, STONKS_OVERWATCH_LOGS_FILENAME

            log_path = os.path.join(STONKS_OVERWATCH_LOGS_DIR, STONKS_OVERWATCH_LOGS_FILENAME)

            self.log_window = LogStreamWindow("Live Logs", log_path)
            self.app.windows.add(self.log_window)

        self.log_window.show()
