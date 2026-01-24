import asyncio
import hashlib
import os
import platform
import shutil
import sys
from pathlib import Path
from threading import Thread

import django
import toga
from asgiref.sync import sync_to_async
from django.core.handlers.wsgi import WSGIHandler
from django.core.management import call_command
from django.core.servers.basehttp import WSGIRequestHandler
from toga.command import Separator

from stonks_overwatch.app.dialogs.dialogs import DialogManager
from stonks_overwatch.app.ui.menu import MenuManager
from stonks_overwatch.app.webserver import StaticFilesMiddleware, ThreadedWSGIServer
from stonks_overwatch.utils.core.demo_mode import is_demo_mode
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.platform_utils import get_flatpak_paths, is_flatpak


class StonksOverwatchApp(toga.App):
    def __init__(self, *args, **kwargs):
        # CRITICAL: Set environment variables BEFORE super().__init__() to ensure
        # Django's settings.py uses correct paths when it's first imported
        os.environ["STONKS_OVERWATCH_APP"] = "1"
        os.environ["DJANGO_SETTINGS_MODULE"] = "stonks_overwatch.settings"

        # Determine platform and get appropriate paths
        in_flatpak = is_flatpak()
        paths_to_create = None

        if in_flatpak:
            # For Flatpak, set paths BEFORE super().__init__() since we don't need self.paths
            paths_to_create = get_flatpak_paths()
            self._set_environment_from_paths(paths_to_create)

        # Initialize parent class (this may trigger settings.py import)
        super().__init__(*args, **kwargs)

        # Set version after super().__init__() when self.version is available
        version = str(self.version) if self.version is not None else "Unknown Version"
        os.environ["STONKS_OVERWATCH_VERSION"] = version

        # For non-Flatpak, set paths AFTER super().__init__() when self.paths is available
        if not in_flatpak:
            paths_to_create = {
                "data": self.paths.data,
                "config": self.paths.config,
                "logs": self.paths.logs,
                "cache": self.paths.cache,
            }
            self._set_environment_from_paths(paths_to_create)

        # Ensure all directories exist (works for both Flatpak and non-Flatpak)
        self._ensure_directories_exist(paths_to_create)

        # NOW it's safe to create loggers since environment variables are set
        # and directories exist
        self.logger = StonksLogger.get_logger("stonks_overwatch.app", "[APP]")

        self.main_window = None
        self.on_exit = None
        self.server_thread = None
        self.web_view = None
        self._httpd = None
        self.server_exists = None
        self.host = None
        self.port = None
        self.menu_manager = MenuManager(self)
        self.dialog_manager = DialogManager(self)

        # Track if we've shown the license dialog
        self._license_dialog_shown = False

    def _set_environment_from_paths(self, paths: dict) -> None:
        """Set environment variables from path dictionary.

        Args:
            paths: Dictionary mapping path types ('data', 'config', 'logs', 'cache')
                   to Path objects
        """
        env_mapping = {
            "data": "STONKS_OVERWATCH_DATA_DIR",
            "config": "STONKS_OVERWATCH_CONFIG_DIR",
            "logs": "STONKS_OVERWATCH_LOGS_DIR",
            "cache": "STONKS_OVERWATCH_CACHE_DIR",
        }

        for key, env_var in env_mapping.items():
            if key in paths:
                path_str = paths[key].as_posix() if hasattr(paths[key], "as_posix") else str(paths[key])
                os.environ[env_var] = path_str

    def _ensure_directories_exist(self, paths: dict) -> None:
        """Ensure all required directories exist.

        Creates directories with proper permissions and warns if creation fails.
        The application will continue even if directory creation fails, but may
        fail later with a clearer error message.

        Args:
            paths: Dictionary mapping path types to Path objects
        """
        import warnings

        for path_type, path in paths.items():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                # Warn but continue - application will fail later with clearer error
                warning_msg = f"Failed to create {path_type} directory {path}: {e}. Application may fail to start."
                warnings.warn(warning_msg, RuntimeWarning, stacklevel=2)
                # Also print to stderr for immediate visibility
                print(f"WARNING: {warning_msg}", file=sys.stderr)

    def web_server(self):
        self.logger.info("Configuring settings...")

        # Environment variables are already set in __init__
        # Import settings and ensure directories exist
        from stonks_overwatch.settings import ensure_data_directories

        ensure_data_directories()

        django.setup(set_prefix=False)

        self.logger.debug(f"STONKS_OVERWATCH_DATA_DIR= {os.environ['STONKS_OVERWATCH_DATA_DIR']}")
        self.logger.debug(f"STONKS_OVERWATCH_CONFIG_DIR= {os.environ['STONKS_OVERWATCH_CONFIG_DIR']}")
        self.logger.debug(f"STONKS_OVERWATCH_LOGS_DIR= {os.environ['STONKS_OVERWATCH_LOGS_DIR']}")
        self.logger.debug(f"STONKS_OVERWATCH_CACHE_DIR= {os.environ['STONKS_OVERWATCH_CACHE_DIR']}")

        self.logger.info("Applying database migrations...")
        call_command("migrate")

        # toga.Widget.DEBUG_LAYOUT_ENABLED = True

        self.logger.info("Starting server...")
        # Use port 0 to let the server select an available port.
        self._httpd = ThreadedWSGIServer(("127.0.0.1", 0), WSGIRequestHandler)
        self._httpd.daemon_threads = True

        wsgi_handler = WSGIHandler()

        # If the import is not done locally, the settings.py file is loaded too early,
        # ignoring the necessary configuration
        from stonks_overwatch.settings import STATIC_ROOT

        static_middleware = StaticFilesMiddleware(wsgi_handler, static_url="/static/", static_root=STATIC_ROOT)
        self._httpd.set_app(static_middleware)

        # The server is now listening, but connections will block until
        # serve_forever is run.
        self.loop.call_soon_threadsafe(self.server_exists.set_result, "ready")
        self._httpd.serve_forever()

    async def exit_handler(self, app):
        # Return True if app should close, and False if it should remain open
        if await self.dialog(toga.ConfirmDialog("Confirm Exit", "Are you sure you want to exit?")):
            self.logger.info("Shutting down...")
            self._httpd.shutdown()
            return True
        else:
            return False

    def startup(self):
        self.server_exists = asyncio.Future()
        self.web_view = toga.WebView()
        self.server_thread = Thread(target=self.web_server)
        self.server_thread.start()
        self.on_exit = self.exit_handler
        self.main_window = toga.MainWindow()
        self.main_window.size = (1440, 900)
        self.main_window.content = self.web_view
        self.menu_manager.setup_main_menu()
        self.menu_manager.setup_debug_menu()
        self.menu_manager.setup_help_menu()
        for command in self.commands:
            if isinstance(command, Separator):
                continue
            if command.group.text == "File" and command.text == "Close All":
                self.commands.remove(command)

    async def on_running(self):
        await self.server_exists
        self.host, self.port = self._httpd.socket.getsockname()
        self.logger.debug("Using server at %s:%s", self.host, self.port)

        # Offer demo mode BEFORE setting initial URL if portfolio is empty
        # If user accepts, demo mode will be active when initial URL is set
        await self.check_demo_mode()

        # Set the initial URL - go directly to dashboard if demo mode is active
        if is_demo_mode():
            self.logger.info("Demo mode active - setting initial URL to dashboard")
            self.web_view.url = f"http://{self.host}:{self.port}/dashboard"
        else:
            self.logger.info("Normal mode - setting initial URL to root (will show broker selector if needed)")
            self.web_view.url = f"http://{self.host}:{self.port}"

        self.main_window.show()

        # Force layout refresh workaround for Windows
        if platform.system() == "Windows":
            # If refresh is not available, resize the window slightly
            w, h = self.main_window.size
            self.main_window.size = (w + 1, h)
            self.main_window.size = (w, h)

        # Check for updates
        await self.check_update()

    async def check_update(self):
        """Check the update status and show download dialog if needed."""
        await self.dialog_manager.check_for_updates(False)

    def _copy_demo_database_if_needed(self, bundled_demo_db, user_demo_db):
        """
        Copy demo database from bundle to user data directory if needed.

        Compares file hashes to determine if an update is required.
        Creates a backup of existing database before updating.

        Args:
            bundled_demo_db: Path to bundled demo database template
            user_demo_db: Path to user's demo database

        Returns:
            bool: True if database was copied/updated, False otherwise
        """

        def get_file_hash(path):
            """Calculate SHA256 hash of a file."""
            sha256 = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()

        # Check if we need to copy/update the demo database
        should_copy = False

        if not user_demo_db.exists():
            self.logger.info("Demo database not found in user data directory")
            should_copy = True
        else:
            # Compare file hashes to detect changes
            bundled_hash = get_file_hash(bundled_demo_db)
            user_hash = get_file_hash(user_demo_db)

            if bundled_hash != user_hash:
                self.logger.info(
                    f"Demo database has been updated (bundled hash: {bundled_hash[:16]}..., "
                    f"user hash: {user_hash[:16]}...)"
                )
                # Backup existing demo database
                backup_path = user_demo_db.with_suffix(".sqlite3.backup")
                self.logger.info(f"Backing up existing demo database to {backup_path}")

                shutil.copy2(user_demo_db, backup_path)
                should_copy = True
            else:
                self.logger.info("Demo database is up to date, no copy needed")

        if should_copy:
            self.logger.info(f"Copying demo database from {bundled_demo_db} to {user_demo_db}")
            shutil.copy2(bundled_demo_db, user_demo_db)
            return True

        return False

    async def switch_to_demo_mode(self, refresh_ui=True):
        """
        Switch to demo mode by setting the DEMO_MODE environment variable.

        The database router will automatically handle switching to the demo database
        without requiring a server restart.

        Args:
            refresh_ui: If True, navigates to dashboard after switching. Set to False
                       when called during startup before initial URL is set.
        """
        self.logger.info("Switching to demo mode...")

        # Import async utilities

        from asgiref.sync import sync_to_async
        from django.core.management import call_command

        from stonks_overwatch.core.registry_setup import reload_broker_configurations
        from stonks_overwatch.settings import STONKS_OVERWATCH_DATA_DIR

        # Locate demo database files
        bundled_demo_db = Path(__file__).parent.parent / "fixtures" / "demo_db.sqlite3"
        user_demo_db = Path(STONKS_OVERWATCH_DATA_DIR) / "demo_db.sqlite3"

        # Verify bundled demo database exists
        if not bundled_demo_db.exists():
            self.logger.error(f"Bundled demo database not found at {bundled_demo_db}")
            await self.main_window.dialog(
                toga.ErrorDialog("Demo Mode Error", "Demo database template not found in application bundle.")
            )
            return

        # Copy or update demo database if needed
        await sync_to_async(self._copy_demo_database_if_needed)(bundled_demo_db, user_demo_db)

        # Set demo mode environment variable
        os.environ["DEMO_MODE"] = "True"

        # Clear demo mode cache to ensure the change is detected immediately
        from stonks_overwatch.utils.core.demo_mode import is_demo_mode

        is_demo_mode.cache_clear()

        # Stop Jobs Scheduled. No updates while in Demo Mode
        from stonks_overwatch.jobs.jobs_scheduler import JobsScheduler

        JobsScheduler.stop()

        # Reload broker configurations to pick up demo mode changes
        await sync_to_async(reload_broker_configurations)()

        # Apply migrations to the demo database to ensure it's up to date
        await sync_to_async(call_command)("migrate", database="demo")

        self.logger.info("Demo mode activated - using demo database")

        # Refresh UI if requested (when switching from menu, not during startup)
        if refresh_ui:
            # Navigate to dashboard to show demo data
            # The middleware will detect offline_mode (active in demo mode) and allow access
            dashboard_url = f"http://{self.host}:{self.port}/"
            self.web_view.url = dashboard_url
            self.logger.info(f"Navigating to dashboard: {dashboard_url}")

    async def check_demo_mode(self):
        """Check if portfolio is empty and offer to load demo data."""
        try:
            from stonks_overwatch.services.aggregators.portfolio_aggregator import PortfolioAggregatorService
            from stonks_overwatch.services.models import PortfolioId

            portfolio = PortfolioAggregatorService()
            portfolio_entries = await sync_to_async(portfolio.get_portfolio)(PortfolioId.ALL)

            if len(portfolio_entries) == 0:
                demo_dialog = toga.QuestionDialog(
                    "Demo Mode", "No portfolio entries found. Do you want to load demo data?"
                )

                # Display the dialog and get the user's response
                if await self.main_window.dialog(demo_dialog):
                    self.logger.info("User accepted demo mode offer")
                    # Switch to demo mode - don't refresh UI during startup
                    # (initial URL will be set by on_running after this returns)
                    await self.switch_to_demo_mode(refresh_ui=False)
                else:
                    self.logger.info("User declined demo mode offer")
        except Exception as e:
            self.logger.error(f"Failed to check demo mode status: {str(e)}")
