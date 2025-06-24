import asyncio
import os
from threading import Thread

import django
import toga
from django.core.handlers.wsgi import WSGIHandler
from django.core.management import call_command
from django.core.servers.basehttp import WSGIRequestHandler

from stonks_overwatch.app.dialogs import DialogManager
from stonks_overwatch.app.menu import MenuManager
from stonks_overwatch.app.webserver import StaticFilesMiddleware, ThreadedWSGIServer
from stonks_overwatch.utils.core.logger import StonksLogger


class StonksOverwatchApp(toga.App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.stonks_overwatch_logger = StonksLogger.get_logger("stonks_overwatch.app", "[APP]")

        self.main_window = None
        self.on_exit = None
        self.server_thread = None
        self.web_view = None
        self._httpd = None
        self.server_exists = None
        self.menu_manager = MenuManager(self)
        self.dialog_manager = DialogManager(self)

    def web_server(self):
        self.stonks_overwatch_logger.info("Configuring settings...")
        os.environ["DJANGO_SETTINGS_MODULE"] = "stonks_overwatch.settings"
        os.environ["STONKS_OVERWATCH_DATA_DIR"] = self.paths.data.as_posix()
        os.environ["STONKS_OVERWATCH_CONFIG_DIR"] = self.paths.config.as_posix()
        os.environ["STONKS_OVERWATCH_LOGS_DIR"] = self.paths.logs.as_posix()
        os.environ["STONKS_OVERWATCH_CACHE_DIR"] = self.paths.cache.as_posix()
        django.setup(set_prefix=False)

        self.stonks_overwatch_logger.info("Applying database migrations...")
        call_command("migrate")

        self.stonks_overwatch_logger.info("Starting server...")
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
            self.stonks_overwatch_logger.info("Shutting down...")
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
        self.main_window.size = (1024, 768)
        self.main_window.content = self.web_view
        self.menu_manager.setup_debug_menu()
        self.menu_manager.setup_help_menu()
        for command in self.commands:
            if command.group.text == "File" and command.text == "Close All":
                self.commands.remove(command)

    async def on_running(self):
        await self.server_exists
        host, port = self._httpd.socket.getsockname()
        self.web_view.url = f"http://{host}:{port}"
        self.main_window.show()
