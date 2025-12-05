import asyncio
import hashlib
import os
import platform
import shutil
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
from stonks_overwatch.utils.core.logger import StonksLogger


class StonksOverwatchApp(toga.App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

    def web_server(self):
        self.logger.info("Configuring settings...")
        os.environ["STONKS_OVERWATCH_APP"] = "1"
        # Convert version to string, handling None case
        version = str(self.version) if self.version is not None else "Unknown Version"
        os.environ["STONKS_OVERWATCH_VERSION"] = version
        os.environ["DJANGO_SETTINGS_MODULE"] = "stonks_overwatch.settings"
        os.environ["STONKS_OVERWATCH_DATA_DIR"] = self.paths.data.as_posix()
        os.environ["STONKS_OVERWATCH_CONFIG_DIR"] = self.paths.config.as_posix()
        os.environ["STONKS_OVERWATCH_LOGS_DIR"] = self.paths.logs.as_posix()
        os.environ["STONKS_OVERWATCH_CACHE_DIR"] = self.paths.cache.as_posix()
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

        # Set the initial URL (will be dashboard if demo mode, login otherwise)
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
        from pathlib import Path

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
